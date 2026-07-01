"""Predictor module — inference functions for all classification tiers.

State (globals, init) lives in classifier.predictor_base.
This module re-exports everything for backward compatibility so that
``from classifier.predictor import init_models, predict_hybrid`` still works.
"""

import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from typing import Any

import numpy as np
from models import (
    EnsembleResponse,
    HybridResponse,
    LexiconResponse,
    MLResponse,
    TransformerResponse,
    WordImportance,
    determine_category,
)
from monitoring import INFERENCE_LATENCY
from normalizer import (
    contains_word_or_phrase,
    detect_sentiment_contrast,
    fuzzy_contains,
    normalize_text,
)

import classifier.predictor_base as _base
from classifier.confidence import (
    apply_lexicon_evidence,
    combine_probabilities,
    get_threshold,
    is_confident_pair,
    llm_decision_to_probability,
)
from classifier.database import get_classification_memory, save_classification_memory
from classifier.llm import GEMINI_API_KEY, query_cloud_llm_async, query_cloud_llm_stream_async

# Re-export state from base (single source of truth)
from classifier.predictor_base import (  # noqa: F401
    BASE_DIR,
    EMBEDDING_MODEL,
    ML_MODEL,
    ML_VECTORIZER,
    PREPARED_LEXICON,
    THRESHOLDS,
    TRANSFORMER_MODEL,
    TRANSFORMER_SESSION,
    TRANSFORMER_TOKENIZER,
    get_calibrated_weights,
    init_models,
    load_thresholds,
    sigmoid,
)

logger = logging.getLogger("bullyguard")

try:
    import torch
except ImportError:
    torch = None

try:
    from transformers import AutoModelForSequenceClassification
except ImportError:
    AutoModelForSequenceClassification = None


# ── XAI Explainability ───────────────────────────────────────────────────────


def explain_prediction(text: str) -> list[Any]:
    ml_model = _base.ML_MODEL
    ml_vectorizer = _base.ML_VECTORIZER
    if ml_model is None or ml_vectorizer is None:
        return []

    try:
        norm = normalize_text(text)["spaced"]

        toxic_estimator = ml_model.estimators_[0]
        bully_estimator = ml_model.estimators_[1]

        def get_coefs(est):
            if hasattr(est, "coef_"):
                return est.coef_[0]
            if hasattr(est, "calibrated_classifiers_") and len(est.calibrated_classifiers_) > 0:
                coefs_list = []
                for cal in est.calibrated_classifiers_:
                    sub_est = getattr(cal, "estimator", getattr(cal, "base_estimator", None))
                    if sub_est is not None and hasattr(sub_est, "coef_"):
                        coefs_list.append(sub_est.coef_[0])
                if coefs_list:
                    return np.mean(coefs_list, axis=0)
            return None

        toxic_coefs = get_coefs(toxic_estimator)
        bully_coefs = get_coefs(bully_estimator)

        feature_names = ml_vectorizer.get_feature_names_out()
        tfidf_matrix = ml_vectorizer.transform([norm])
        nonzero_indices = tfidf_matrix.nonzero()[1]

        impacts = []
        for idx in nonzero_indices:
            word = feature_names[idx]
            tfidf_val = tfidf_matrix[0, idx]
            w_toxic = float(toxic_coefs[idx] * tfidf_val) if toxic_coefs is not None and idx < len(toxic_coefs) else 0.0
            w_bully = float(bully_coefs[idx] * tfidf_val) if bully_coefs is not None and idx < len(bully_coefs) else 0.0
            if abs(w_toxic) > 1e-4 or abs(w_bully) > 1e-4:
                impacts.append({"word": word, "weight_toxic": w_toxic, "weight_bully": w_bully})

        impacts.sort(key=lambda x: max(abs(x["weight_toxic"]), abs(x["weight_bully"])), reverse=True)
        return [
            WordImportance(word=imp["word"], weight_toxic=imp["weight_toxic"], weight_bully=imp["weight_bully"])
            for imp in impacts
        ]
    except Exception as e:
        logger.warning("Failed to compute XAI explain_prediction", extra={"error": str(e)})
        return []


# ── Transformer Inference ────────────────────────────────────────────────────


def predict_transformer_raw(text: str) -> dict[str, float]:
    transformer_tokenizer = _base.TRANSFORMER_TOKENIZER
    transformer_session = _base.TRANSFORMER_SESSION
    if transformer_tokenizer is None:
        return {"toxic_prob": 0.0, "bully_prob": 0.0}

    if transformer_session is not None:
        try:
            inputs = transformer_tokenizer(text, padding=True, truncation=True, return_tensors="np")
            ort_inputs = {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64),
            }
            ort_outputs: Any = transformer_session.run(None, ort_inputs)
            logits = ort_outputs[0][0]
            probs = sigmoid(logits)
            return {"bully_prob": float(probs[0]), "toxic_prob": float(probs[1])}
        except Exception as e:
            logger.warning("Failed to process ONNX session, falling back to PyTorch", extra={"error": str(e)})

    transformer_model = _base.TRANSFORMER_MODEL
    if transformer_model is None and torch is not None:
        try:
            model_name = os.getenv("TRANSFORMER_MODEL_PATH", "nahiar/hatespeech-abusive-xlm-roberta-v1")
            logger.info("Loading PyTorch model dynamically for fallback", extra={"model": model_name})
            device = "cuda" if torch.cuda.is_available() else "cpu"
            _base.TRANSFORMER_MODEL = AutoModelForSequenceClassification.from_pretrained(model_name).to(device)
            transformer_model = _base.TRANSFORMER_MODEL
        except Exception as load_err:
            logger.error("Failed to load PyTorch model dynamically", extra={"error": str(load_err)})

    if transformer_model is not None and torch is not None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        inputs = transformer_tokenizer(text, padding=True, truncation=True, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            logits = transformer_model(**inputs).logits[0]
        probs = torch.sigmoid(logits).tolist()
        return {"bully_prob": probs[0], "toxic_prob": probs[1]}

    return {"toxic_prob": 0.0, "bully_prob": 0.0}


# ── Lexicon Prediction ───────────────────────────────────────────────────────


def predict_lexicon(text: str, use_fuzzy: bool = True) -> LexiconResponse:
    start_time = time.perf_counter()
    norm = normalize_text(text)
    spaced_text = norm["spaced"]
    compact_text = norm["compact"]
    compact_strict_text = norm["compact_strict"]

    matches = []
    seen_phrases = set()

    for item in _base.PREPARED_LEXICON:
        phrase = item["phrase"]
        norm_spaced = item["norm_spaced"]
        norm_compact = item["norm_compact"]
        method = None

        if contains_word_or_phrase(spaced_text, norm_spaced):
            method = "word_or_phrase_match"
        elif norm_compact and norm_compact in compact_text:
            method = "compact_match"
        elif norm_compact and norm_compact in compact_strict_text:
            method = "compact_repeated_char_match"
        elif use_fuzzy and len(norm_compact) >= 6:
            if fuzzy_contains(compact_text, norm_compact) or fuzzy_contains(compact_strict_text, norm_compact):
                method = "fuzzy_compact_match"

        if method and phrase not in seen_phrases:
            matches.append(
                {"matched_phrase": phrase, "category": item["category"], "severity": item["severity"], "method": method}
            )
            seen_phrases.add(phrase)

    severity_score = {"rendah": 1, "sedang": 2, "tinggi": 3}
    score = sum(severity_score.get(m["severity"], 1) for m in matches)
    has_high = any(m["severity"] == "tinggi" for m in matches)

    if not matches:
        risk_label = "aman/tidak terdeteksi"
    elif has_high or score >= 4:
        risk_label = "tinggi"
    elif score >= 2:
        risk_label = "sedang"
    else:
        risk_label = "rendah"

    elapsed = (time.perf_counter() - start_time) * 1000.0
    return LexiconResponse(
        text=text,
        normalized_spaced=spaced_text,
        normalized_compact=compact_text,
        is_cyberbullying=bool(matches),
        risk_label=risk_label,
        score=score,
        matches=matches,
        execution_time=round(elapsed, 2),
    )


# ── ML Prediction ────────────────────────────────────────────────────────────


def predict_ml(text: str) -> MLResponse:
    start_time = time.perf_counter()
    ml_model = _base.ML_MODEL
    ml_vectorizer = _base.ML_VECTORIZER
    if ml_model is None or ml_vectorizer is None:
        return MLResponse(
            text=text,
            is_toxic=False,
            is_bully=False,
            probability_toxic=0.0,
            probability_bully=0.0,
            category="Model ML belum termuat.",
            word_importances=[],
            execution_time=0.0,
        )

    norm = normalize_text(text)["spaced"]
    tfidf_text = ml_vectorizer.transform([norm])
    pred_probs = ml_model.predict_proba(tfidf_text)
    prob_toxic = float(pred_probs[0][0][1])
    prob_bully = float(pred_probs[1][0][1])

    is_toxic = prob_toxic >= get_threshold(_base.THRESHOLDS, "threshold_toxic", 0.5)
    is_bully = prob_bully >= get_threshold(_base.THRESHOLDS, "threshold_bully", 0.5)

    elapsed = (time.perf_counter() - start_time) * 1000.0
    return MLResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=prob_toxic,
        probability_bully=prob_bully,
        category=determine_category(is_toxic, is_bully),
        word_importances=explain_prediction(text),
        execution_time=round(elapsed, 2),
    )


# ── Transformer Prediction ───────────────────────────────────────────────────


def predict_transformers(text: str) -> TransformerResponse:
    start_time = time.perf_counter()
    res = predict_transformer_raw(text)
    prob_toxic = res["toxic_prob"]
    prob_bully = res["bully_prob"]

    is_toxic = prob_toxic >= get_threshold(_base.THRESHOLDS, "threshold_toxic", 0.5)
    is_bully = prob_bully >= get_threshold(_base.THRESHOLDS, "threshold_bully", 0.5)

    elapsed = (time.perf_counter() - start_time) * 1000.0
    return TransformerResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=prob_toxic,
        probability_bully=prob_bully,
        category=determine_category(is_toxic, is_bully),
        word_importances=explain_prediction(text),
        execution_time=round(elapsed, 2),
    )


# ── Ensemble Prediction ──────────────────────────────────────────────────────


def predict_ensemble(text: str) -> EnsembleResponse:
    start_time = time.perf_counter()
    ml_res = predict_ml(text)
    ml_toxic = ml_res.probability_toxic
    ml_bully = ml_res.probability_bully

    res_tr = predict_transformer_raw(text)
    tr_toxic = res_tr["toxic_prob"]
    tr_bully = res_tr["bully_prob"]

    w = get_calibrated_weights()
    final_toxic = combine_probabilities(ml_toxic, tr_toxic, w.get("ml_toxic", 0.5), w.get("tr_toxic", 0.5))
    final_bully = combine_probabilities(ml_bully, tr_bully, w.get("ml_bully", 0.65), w.get("tr_bully", 0.35))

    lex_res = predict_lexicon(text, use_fuzzy=False)
    final_toxic = apply_lexicon_evidence(final_toxic, lex_res)
    final_bully = apply_lexicon_evidence(final_bully, lex_res)

    is_toxic = final_toxic >= get_threshold(_base.THRESHOLDS, "threshold_toxic", 0.5)
    is_bully = final_bully >= get_threshold(_base.THRESHOLDS, "threshold_bully", 0.5)

    elapsed = (time.perf_counter() - start_time) * 1000.0
    return EnsembleResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=final_toxic,
        probability_bully=final_bully,
        category=determine_category(is_toxic, is_bully),
        word_importances=explain_prediction(text),
        execution_time=round(elapsed, 2),
    )


# ── ML Inference Helper ──────────────────────────────────────────────────────


def run_ml_inference_sync(text: str) -> tuple[float, float]:
    if _base.ML_VECTORIZER is None or _base.ML_MODEL is None:
        return 0.0, 0.0
    norm = normalize_text(text)["spaced"]
    tfidf_text = _base.ML_VECTORIZER.transform([norm])
    pred_probs_ml = _base.ML_MODEL.predict_proba(tfidf_text)
    return float(pred_probs_ml[0][0][1]), float(pred_probs_ml[1][0][1])


# ── Ensemble Helper (async) ──────────────────────────────────────────────────


async def run_ensemble_inference_async(text: str, ml_toxic: float, ml_bully: float) -> tuple[float, float]:
    """Run transformer inference in a thread and combine with ML probabilities."""
    res_tr = await asyncio.to_thread(predict_transformer_raw, text)
    tr_toxic = res_tr["toxic_prob"]
    tr_bully = res_tr["bully_prob"]

    w = get_calibrated_weights()
    ens_toxic = combine_probabilities(ml_toxic, tr_toxic, w.get("ml_toxic", 0.5), w.get("tr_toxic", 0.5))
    ens_bully = combine_probabilities(ml_bully, tr_bully, w.get("ml_bully", 0.65), w.get("tr_bully", 0.35))
    return ens_toxic, ens_bully


# ── Hybrid Prediction ────────────────────────────────────────────────────────


async def _predict_hybrid_internal(text: str) -> HybridResponse:
    start_time = time.perf_counter()
    if _base.ML_MODEL is None or _base.ML_VECTORIZER is None:
        elapsed = time.perf_counter() - start_time
        INFERENCE_LATENCY.labels(tier="fallback").observe(elapsed)
        return HybridResponse(
            text=text,
            is_toxic=False,
            is_bully=False,
            probability_toxic=0.0,
            probability_bully=0.0,
            category="Aman",
            decision_source="Fallback",
            reason="Model ML belum termuat.",
            word_importances=[],
        )

    t_t = get_threshold(_base.THRESHOLDS, "threshold_toxic", 0.5)
    t_b = get_threshold(_base.THRESHOLDS, "threshold_bully", 0.5)

    # Sarcasm bypass
    is_sarcasm_candidate = detect_sentiment_contrast(text)
    if is_sarcasm_candidate and GEMINI_API_KEY:
        logger.info("Sentiment contrast pattern detected, bypassing to Tier 3", extra={"text": text[:80]})
        llm_res = await query_cloud_llm_async(text)
        if llm_res["success"]:
            is_toxic = llm_res["is_toxic"]
            is_bully = llm_res["is_bully"]
            elapsed = time.perf_counter() - start_time
            INFERENCE_LATENCY.labels(tier="sarcasm_bypass").observe(elapsed)
            return HybridResponse(
                text=text,
                is_toxic=is_toxic,
                is_bully=is_bully,
                probability_toxic=llm_decision_to_probability(is_toxic, t_t),
                probability_bully=llm_decision_to_probability(is_bully, t_b),
                category=determine_category(is_toxic, is_bully),
                decision_source="Tier 3 (Cloud LLM - Sarcasm Bypass)",
                reason=f"[Sarcasm Bypass] {llm_res['reason']}",
                word_importances=explain_prediction(text),
            )

    # Lexicon bypass
    lex_res = predict_lexicon(text, use_fuzzy=True)
    if lex_res.is_cyberbullying and lex_res.risk_label in ["sedang", "tinggi"]:
        matched_words = [m.matched_phrase for m in lex_res.matches]
        elapsed = time.perf_counter() - start_time
        INFERENCE_LATENCY.labels(tier="lexicon").observe(elapsed)
        return HybridResponse(
            text=text,
            is_toxic=True,
            is_bully=True,
            probability_toxic=0.85,
            probability_bully=0.85,
            category=determine_category(True, True),
            decision_source="Tier 1 (Lexicon Kamus)",
            reason=f"Terdeteksi kata kasar/larangan di dalam teks: {', '.join(matched_words)}",
            word_importances=explain_prediction(text),
        )

    # Tier 1: ML
    ml_toxic, ml_bully = await asyncio.to_thread(run_ml_inference_sync, text)
    ml_confidence = is_confident_pair(ml_toxic, ml_bully, t_t, t_b)
    if ml_confidence.is_confident:
        is_toxic = ml_toxic >= t_t
        is_bully = ml_bully >= t_b
        elapsed = time.perf_counter() - start_time
        INFERENCE_LATENCY.labels(tier="ml").observe(elapsed)
        return HybridResponse(
            text=text,
            is_toxic=is_toxic,
            is_bully=is_bully,
            probability_toxic=ml_toxic,
            probability_bully=ml_bully,
            category=determine_category(is_toxic, is_bully),
            decision_source="Tier 1 (ML Klasik)",
            reason="Klasifikasi konfiden tinggi berdasarkan bobot kata kunci model statistik. " + ml_confidence.reason,
            word_importances=explain_prediction(text),
        )

    # Tier 2: Ensemble
    ens_toxic, ens_bully = await run_ensemble_inference_async(text, ml_toxic, ml_bully)
    ens_confidence = is_confident_pair(ens_toxic, ens_bully, t_t, t_b)
    if ens_confidence.is_confident:
        is_toxic = ens_toxic >= t_t
        is_bully = ens_bully >= t_b
        elapsed = time.perf_counter() - start_time
        INFERENCE_LATENCY.labels(tier="ensemble").observe(elapsed)
        return HybridResponse(
            text=text,
            is_toxic=is_toxic,
            is_bully=is_bully,
            probability_toxic=ens_toxic,
            probability_bully=ens_bully,
            category=determine_category(is_toxic, is_bully),
            decision_source="Tier 2 (Ensemble ML & Transformer)",
            reason="Klasifikasi berbasis gabungan model statistik dan semantik Transformer. " + ens_confidence.reason,
            word_importances=explain_prediction(text),
        )

    # Tier 3: Cloud LLM
    if GEMINI_API_KEY:
        logger.info("Complex case detected, forwarding to Tier 3", extra={"text": text[:80]})
        llm_res = await query_cloud_llm_async(text)
        if llm_res["success"]:
            is_toxic = llm_res["is_toxic"]
            is_bully = llm_res["is_bully"]
            elapsed = time.perf_counter() - start_time
            INFERENCE_LATENCY.labels(tier="cloud_llm").observe(elapsed)
            return HybridResponse(
                text=text,
                is_toxic=is_toxic,
                is_bully=is_bully,
                probability_toxic=llm_decision_to_probability(is_toxic, t_t),
                probability_bully=llm_decision_to_probability(is_bully, t_b),
                category=determine_category(is_toxic, is_bully),
                decision_source="Tier 3 (Cloud LLM)",
                reason=llm_res["reason"],
                word_importances=explain_prediction(text),
            )

    # Fallback
    is_toxic = ens_toxic >= t_t
    is_bully = ens_bully >= t_b
    elapsed = time.perf_counter() - start_time
    INFERENCE_LATENCY.labels(tier="fallback").observe(elapsed)
    return HybridResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=ens_toxic,
        probability_bully=ens_bully,
        category=determine_category(is_toxic, is_bully),
        decision_source="Fallback (Ensemble Terbatas)",
        reason="Cloud LLM tidak merespons, menggunakan keputusan cadangan dari model lokal.",
        word_importances=explain_prediction(text),
    )


async def predict_hybrid(text: str) -> HybridResponse:
    cached_memory = await get_classification_memory(text)
    if cached_memory:
        logger.info("Memory hit: returning cached classification", extra={"text": text[:80]})
        cached_memory.word_importances = explain_prediction(text)
        return cached_memory

    res = await _predict_hybrid_internal(text)

    embedding_json = None
    embedding_model = _base.EMBEDDING_MODEL
    if embedding_model is not None:
        try:
            emb = embedding_model.encode([text])[0]
            embedding_json = str(emb.tolist())
        except Exception:
            pass
    await save_classification_memory(res, embedding_json)
    return res


# ── Streaming Hybrid Prediction ──────────────────────────────────────────────


async def predict_hybrid_stream(text: str) -> AsyncGenerator[dict[str, Any], None]:
    ml_model = _base.ML_MODEL
    ml_vectorizer = _base.ML_VECTORIZER
    embedding_model = _base.EMBEDDING_MODEL

    cached_memory = await get_classification_memory(text)
    if cached_memory:
        logger.info("Memory hit: returning cached classification (stream)", extra={"text": text[:80]})
        cached_memory.word_importances = explain_prediction(text)
        yield {"chunk": cached_memory.reason, "done": True, "final_data": cached_memory}
        return

    if ml_model is None or ml_vectorizer is None:
        res = HybridResponse(
            text=text,
            is_toxic=False,
            is_bully=False,
            probability_toxic=0.0,
            probability_bully=0.0,
            category="Aman",
            decision_source="Fallback",
            reason="Model ML belum termuat.",
            word_importances=[],
        )
        yield {"chunk": res.reason, "done": True, "final_data": res}
        return

    t_t = get_threshold(_base.THRESHOLDS, "threshold_toxic", 0.5)
    t_b = get_threshold(_base.THRESHOLDS, "threshold_bully", 0.5)

    # Lexicon bypass
    lex_res = predict_lexicon(text, use_fuzzy=True)
    if lex_res.is_cyberbullying and lex_res.risk_label in ["sedang", "tinggi"]:
        matched_words = [m.matched_phrase for m in lex_res.matches]
        final_res = HybridResponse(
            text=text,
            is_toxic=True,
            is_bully=True,
            probability_toxic=0.85,
            probability_bully=0.85,
            category=determine_category(True, True),
            decision_source="Tier 1 (Lexicon Kamus)",
            reason=f"Terdeteksi kata kasar/larangan di dalam teks: {', '.join(matched_words)}",
            word_importances=explain_prediction(text),
        )
        embedding_json = None
        if embedding_model is not None:
            try:
                emb = embedding_model.encode([text])[0]
                embedding_json = str(emb.tolist())
            except Exception:
                pass
        await save_classification_memory(final_res, embedding_json)
        yield {"chunk": final_res.reason, "done": True, "final_data": final_res}
        return

    # Sarcasm bypass (stream)
    is_sarcasm_candidate = detect_sentiment_contrast(text)
    if is_sarcasm_candidate and GEMINI_API_KEY:
        logger.info("Sentiment contrast detected, bypassing to Tier 3 (stream)", extra={"text": text[:80]})
        async for state in query_cloud_llm_stream_async(text):
            if state["done"]:
                llm_res = state["final_data"]
                if llm_res["success"]:
                    is_toxic = llm_res["is_toxic"]
                    is_bully = llm_res["is_bully"]
                    final_res = HybridResponse(
                        text=text,
                        is_toxic=is_toxic,
                        is_bully=is_bully,
                        probability_toxic=llm_decision_to_probability(is_toxic, t_t),
                        probability_bully=llm_decision_to_probability(is_bully, t_b),
                        category=determine_category(is_toxic, is_bully),
                        decision_source="Tier 3 (Cloud LLM - Sarcasm Bypass)",
                        reason=f"[Sarcasm Bypass] {llm_res['reason']}",
                        word_importances=explain_prediction(text),
                    )
                else:
                    final_res = HybridResponse(
                        text=text,
                        is_toxic=False,
                        is_bully=False,
                        probability_toxic=0.0,
                        probability_bully=0.0,
                        category="Aman",
                        decision_source="Fallback",
                        reason=llm_res["reason"],
                        word_importances=explain_prediction(text),
                    )
                embedding_json = None
                if embedding_model is not None:
                    try:
                        emb = embedding_model.encode([text])[0]
                        embedding_json = str(emb.tolist())
                    except Exception:
                        pass
                await save_classification_memory(final_res, embedding_json)
                yield {"chunk": state["chunk"], "done": True, "final_data": final_res}
            else:
                yield {"chunk": state["chunk"], "done": False, "final_data": None}
        return

    # Tier 1: ML
    ml_toxic, ml_bully = await asyncio.to_thread(run_ml_inference_sync, text)
    ml_confidence = is_confident_pair(ml_toxic, ml_bully, t_t, t_b)
    if ml_confidence.is_confident:
        is_toxic = ml_toxic >= t_t
        is_bully = ml_bully >= t_b
        res = HybridResponse(
            text=text,
            is_toxic=is_toxic,
            is_bully=is_bully,
            probability_toxic=ml_toxic,
            probability_bully=ml_bully,
            category=determine_category(is_toxic, is_bully),
            decision_source="Tier 1 (ML Klasik)",
            reason="Klasifikasi berbasis ambang batas probabilitas model statistik. " + ml_confidence.reason,
            word_importances=explain_prediction(text),
        )
        embedding_json = None
        if embedding_model is not None:
            try:
                emb = embedding_model.encode([text])[0]
                embedding_json = str(emb.tolist())
            except Exception:
                pass
        await save_classification_memory(res, embedding_json)
        yield {"chunk": res.reason, "done": True, "final_data": res}
        return

    # Tier 2: Ensemble
    ens_toxic, ens_bully = await run_ensemble_inference_async(text, ml_toxic, ml_bully)
    ens_confidence = is_confident_pair(ens_toxic, ens_bully, t_t, t_b)
    if ens_confidence.is_confident:
        is_toxic = ens_toxic >= t_t
        is_bully = ens_bully >= t_b
        res = HybridResponse(
            text=text,
            is_toxic=is_toxic,
            is_bully=is_bully,
            probability_toxic=ens_toxic,
            probability_bully=ens_bully,
            category=determine_category(is_toxic, is_bully),
            decision_source="Tier 2 (Ensemble ML & Transformer)",
            reason="Klasifikasi berbasis gabungan model statistik dan semantik Transformer. " + ens_confidence.reason,
            word_importances=explain_prediction(text),
        )
        embedding_json = None
        if embedding_model is not None:
            try:
                emb = embedding_model.encode([text])[0]
                embedding_json = str(emb.tolist())
            except Exception:
                pass
        await save_classification_memory(res, embedding_json)
        yield {"chunk": res.reason, "done": True, "final_data": res}
        return

    # Tier 3: Cloud LLM (stream)
    if GEMINI_API_KEY:
        logger.info("Complex case detected, forwarding to Tier 3 (stream)", extra={"text": text[:80]})
        async for state in query_cloud_llm_stream_async(text):
            if state["done"]:
                llm_res = state["final_data"]
                if llm_res["success"]:
                    is_toxic = llm_res["is_toxic"]
                    is_bully = llm_res["is_bully"]
                    final_res = HybridResponse(
                        text=text,
                        is_toxic=is_toxic,
                        is_bully=is_bully,
                        probability_toxic=llm_decision_to_probability(is_toxic, t_t),
                        probability_bully=llm_decision_to_probability(is_bully, t_b),
                        category=determine_category(is_toxic, is_bully),
                        decision_source="Tier 3 (Cloud LLM)",
                        reason=llm_res["reason"],
                        word_importances=explain_prediction(text),
                    )
                else:
                    is_toxic = ens_toxic >= t_t
                    is_bully = ens_bully >= t_b
                    final_res = HybridResponse(
                        text=text,
                        is_toxic=is_toxic,
                        is_bully=is_bully,
                        probability_toxic=ens_toxic,
                        probability_bully=ens_bully,
                        category=determine_category(is_toxic, is_bully),
                        decision_source="Fallback (Ensemble Terbatas)",
                        reason="Cloud LLM gagal merespons, menggunakan keputusan cadangan dari model lokal.",
                        word_importances=explain_prediction(text),
                    )
                embedding_json = None
                if embedding_model is not None:
                    try:
                        emb = embedding_model.encode([text])[0]
                        embedding_json = str(emb.tolist())
                    except Exception:
                        pass
                await save_classification_memory(final_res, embedding_json)
                yield {"chunk": state["chunk"], "done": True, "final_data": final_res}
            else:
                yield {"chunk": state["chunk"], "done": False, "final_data": None}
        return

    # Fallback
    is_toxic = ens_toxic >= t_t
    is_bully = ens_bully >= t_b
    res = HybridResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=ens_toxic,
        probability_bully=ens_bully,
        category=determine_category(is_toxic, is_bully),
        decision_source="Fallback (Ensemble Terbatas)",
        reason="Cloud LLM tidak dikonfigurasi, menggunakan keputusan cadangan dari model lokal.",
        word_importances=explain_prediction(text),
    )
    embedding_json = None
    if embedding_model is not None:
        try:
            emb = embedding_model.encode([text])[0]
            embedding_json = str(emb.tolist())
        except Exception:
            pass
    await save_classification_memory(res, embedding_json)
    yield {"chunk": res.reason, "done": True, "final_data": res}
