import os
import re
import json
import joblib
import numpy as np
import pandas as pd
import asyncio
import subprocess
import threading
import sys
from typing import List, Dict, Any, AsyncGenerator

from transformers import AutoTokenizer, AutoModelForSequenceClassification
try:
    import torch
except ImportError:
    torch = None

try:
    import onnxruntime as ort
except ImportError:
    ort = None

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:
    SentenceTransformer = None

from models import LexiconResponse, MLResponse, TransformerResponse, EnsembleResponse, HybridResponse, determine_category
from normalizer import (
    normalize_text,
    prepare_lexicon,
    contains_word_or_phrase,
    fuzzy_contains,
    init_slang_map,
    detect_sentiment_contrast,
    BASE_CYBERBULLYING_LEXICON
)
from classifier.database import init_cache_db, save_classification_memory, get_classification_memory
from classifier.llm import query_cloud_llm_async, query_cloud_llm_stream_async, GEMINI_API_KEY
import classifier.llm as llm_module
from classifier.confidence import (
    apply_lexicon_evidence,
    combine_probabilities,
    decision_summary,
    get_threshold,
    is_confident_pair,
    llm_decision_to_probability,
)

# Tentukan direktori dasar dinamis untuk pathing absolut (parent dari classifier/ yaitu cyberbullying_api/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Global variables for models and prepared lexicon
PREPARED_LEXICON = []
ML_MODEL: Any = None
ML_VECTORIZER: Any = None
TRANSFORMER_SESSION: Any = None
TRANSFORMER_TOKENIZER: Any = None
TRANSFORMER_MODEL: Any = None
EMBEDDING_MODEL: Any = None

THRESHOLDS = {
    "threshold_toxic": 0.5,
    "threshold_bully": 0.5
}

_MODEL_LOCK = threading.Lock()

def load_thresholds():
    global THRESHOLDS
    thresholds_path = os.path.join(BASE_DIR, "models", "thresholds.json")
    if os.path.exists(thresholds_path):
        try:
            with open(thresholds_path, "r") as f:
                THRESHOLDS = json.load(f)
            print(f"Ambang batas perutean dinamis dimuat: Toxic={THRESHOLDS['threshold_toxic']:.2f}, Bully={THRESHOLDS['threshold_bully']:.2f}")
        except Exception as e:
            print("Warning: Gagal memuat thresholds.json, menggunakan default 0.5:", e)

def get_calibrated_weights() -> dict:
    try:
        from classifier.settings_store import get_settings_sync
        settings = get_settings_sync()
        return settings.get("ensemble_weights", {
            "ml_toxic": 0.5,
            "tr_toxic": 0.5,
            "ml_bully": 0.65,
            "tr_bully": 0.35
        })
    except Exception:
        return {
            "ml_toxic": 0.5,
            "tr_toxic": 0.5,
            "ml_bully": 0.65,
            "tr_bully": 0.35
        }

def init_models():
    with _MODEL_LOCK:
        _init_models_inner()

def _init_models_inner():
    global PREPARED_LEXICON, ML_MODEL, ML_VECTORIZER, TRANSFORMER_SESSION, TRANSFORMER_TOKENIZER, TRANSFORMER_MODEL, EMBEDDING_MODEL
    
    print("=== Inisialisasi Model Klasifikasi ===")
    
    # 0. Inisialisasi Basis Data Caching LLM
    init_cache_db()
    
    # 1. Load Slang Mapping (menggunakan path absolut dinamis)
    print("Memuat kamus slang alay & singkatan...")
    alay_path = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "new_kamusalay.csv")
    singkatan_path = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "kamus_singkatan.csv")
    slang_map = init_slang_map(alay_path, singkatan_path)
    print(f"Berhasil memuat {len(slang_map)} pemetaan slang/singkatan.")

    # 2. Load and Prepare Lexicon
    print("Memuat kata kasar dari abusive.csv...")
    try:
        abusive_path = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "abusive.csv")
        df_abusive = pd.read_csv(abusive_path)
        abusive_words = df_abusive['ABUSIVE'].dropna().unique().tolist()
        
        existing_phrases = {item["phrase"].lower() for item in BASE_CYBERBULLYING_LEXICON}
        new_terms = []
        for word in abusive_words:
            word_lower = word.strip().lower()
            if word_lower not in existing_phrases:
                new_terms.append({
                    "phrase": word_lower,
                    "category": "kata kasar (abusive.csv)",
                    "severity": "sedang"
                })
                existing_phrases.add(word_lower)
        full_lexicon = BASE_CYBERBULLYING_LEXICON + new_terms
    except Exception as e:
        print("Warning: Gagal memuat abusive.csv, menggunakan baseline leksikon:", e)
        full_lexicon = BASE_CYBERBULLYING_LEXICON
        abusive_words = []

    llm_module.ABUSIVE_WORDS_SET = set(abusive_words)

    PREPARED_LEXICON = prepare_lexicon(full_lexicon)
    print(f"Leksikon siap: total {len(PREPARED_LEXICON)} kata/frasa.")

    # 3. Load Machine Learning Models
    print("Memuat model Machine Learning (Logistic Regression & TF-IDF)...")
    try:
        ML_MODEL = joblib.load(os.path.join(BASE_DIR, "models", "model_lr.joblib"))
        ML_VECTORIZER = joblib.load(os.path.join(BASE_DIR, "models", "vectorizer.joblib"))
        print("Model ML berhasil dimuat!")
    except Exception as e:
        print("Error: Gagal memuat model Machine Learning:", e)

    # 3.5. Load RAG Pool untuk Few-Shot LLM Dinamis
    print("Memuat dataset RAG pool untuk LLM...")
    try:
        combined_path = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "combined_dataset.csv")
        if os.path.exists(combined_path):
            df_combined = pd.read_csv(combined_path)
            df_combined = df_combined.dropna(subset=["String", "Label"])
            # Ambil sampel seimbang (150 bully, 150 non-bully) jika mencukupi
            df_bully_pool = df_combined[df_combined["Label"].isin(["Bullying", "negatif", "negative"])]
            df_nonbully_pool = df_combined[~df_combined["Label"].isin(["Bullying", "negatif", "negative"])]
            df_bully = df_bully_pool.sample(min(150, len(df_bully_pool)), random_state=42, replace=False)
            df_nonbully = df_nonbully_pool.sample(min(150, len(df_nonbully_pool)), random_state=42, replace=False)
            df_sampled = pd.concat([df_bully, df_nonbully], ignore_index=True)
            
            llm_module.RAG_POOL_TEXTS = df_sampled["String"].tolist()
            llm_module.RAG_POOL_LABELS = df_sampled["Label"].tolist()
            
            if ML_VECTORIZER is not None:
                llm_module.RAG_POOL_VECTORS = ML_VECTORIZER.transform(llm_module.RAG_POOL_TEXTS)
                print(f"RAG Pool siap dengan {len(llm_module.RAG_POOL_TEXTS)} sampel!")
        else:
            print("Warning: dataset combined tidak ditemukan untuk RAG pool, Few-Shot statis digunakan.")
    except Exception as e:
        print("Warning: Gagal memuat RAG pool:", e)

    # 4. Load thresholds.json
    load_thresholds()

    # 5. Load Deep Learning Transformers (ONNX / PyTorch)
    model_name = os.getenv("TRANSFORMER_MODEL_PATH", "nahiar/hatespeech-abusive-xlm-roberta-v1")
    print(f"Memuat model Deep Learning Transformers dari: {model_name}...")
    try:
        TRANSFORMER_TOKENIZER = AutoTokenizer.from_pretrained(model_name)
    except Exception as e:
        print("Warning: Gagal memuat tokenizer:", e)

    # Cek model quantized ONNX (Gunakan nama file spesifik model agar tidak tertukar jika ganti model)
    model_slug = model_name.replace("/", "_").replace("\\", "_").replace(".", "_")
    onnx_filename = f"model_{model_slug}_quantized.onnx"
    onnx_path = os.path.join(BASE_DIR, "models", onnx_filename)
    
    if not os.path.exists(onnx_path) and os.getenv("AUTO_EXPORT_ONNX", "false").lower() in {"1", "true", "yes"}:
        print(f"{onnx_filename} tidak ditemukan. Menjalankan ekspor otomatis...")
        try:
            export_script = os.path.join(BASE_DIR, "export_onnx.py")
            # Hapus berkas legacy_onnx lama jika ada untuk menghindari mismatch model lama jika ekspor saat ini gagal
            legacy_onnx = os.path.join(BASE_DIR, "models", "model_quantized.onnx")
            if os.path.exists(legacy_onnx):
                try:
                    os.remove(legacy_onnx)
                    print("Membersihkan model_quantized.onnx usang sebelum ekspor baru.")
                except Exception as del_err:
                    print(f"Warning: Gagal membersihkan model_quantized.onnx lama: {del_err}")

            subprocess.run([sys.executable, export_script], check=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            
            # export_onnx.py menulis ke model_quantized.onnx, pindahkan ke nama file spesifik model
            if os.path.exists(legacy_onnx):
                import shutil
                shutil.move(legacy_onnx, onnx_path)
                print(f"Sukses mengekspor model ONNX spesifik ke: {onnx_path}")
            else:
                raise FileNotFoundError("Berkas ekspor model_quantized.onnx tidak ditemukan setelah proses ekspor selesai.")
        except Exception as e:
            print("Gagal ekspor ONNX otomatis, fallback ke PyTorch:", e)
    elif not os.path.exists(onnx_path):
        print(f"{onnx_filename} tidak ditemukan. Auto-export ONNX dinonaktifkan.")

    if os.path.exists(onnx_path) and ort is not None:
        try:
            TRANSFORMER_SESSION = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
            print("Model ONNX terkuantisasi INT8 berhasil dimuat!")
        except Exception as e:
            print("Warning: Gagal memuat session ONNX runtime, fallback ke PyTorch:", e)
            TRANSFORMER_SESSION = None

    if TRANSFORMER_SESSION is None:
        if torch is None:
            print("Warning: PyTorch tidak terinstal. Fallback PyTorch dinonaktifkan.")
        else:
            try:
                TRANSFORMER_MODEL = AutoModelForSequenceClassification.from_pretrained(model_name)
                print("Model PyTorch berhasil dimuat (ONNX Fallback)!")
            except Exception as e:
                print("Warning: Gagal memuat model PyTorch:", e)

    # 6. Load Sentence Transformer for pgvector/RAG
    print("Memuat model sentence-transformer untuk vector embedding...")
    try:
        if SentenceTransformer is not None:
            EMBEDDING_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            print("Model sentence-transformer (all-MiniLM-L6-v2) berhasil dimuat!")
        else:
            print("Warning: sentence-transformers tidak terinstal. Vector search dinonaktifkan.")
    except Exception as e:
        print("Warning: Gagal memuat sentence-transformer model:", e)

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def explain_prediction(text: str) -> List[Any]:
    from models import WordImportance
    if ML_MODEL is None or ML_VECTORIZER is None:
        return []
        
    try:
        norm = normalize_text(text)["spaced"]
        
        # Ekstrak estimator individual dari MultiOutputClassifier
        toxic_estimator = ML_MODEL.estimators_[0]
        bully_estimator = ML_MODEL.estimators_[1]
        
        # Ekstrak koefisien masing-masing kelas secara aman
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
        
        feature_names = ML_VECTORIZER.get_feature_names_out()
        tfidf_matrix = ML_VECTORIZER.transform([norm])
        nonzero_indices = tfidf_matrix.nonzero()[1]
        
        impacts = []
        for idx in nonzero_indices:
            word = feature_names[idx]
            tfidf_val = tfidf_matrix[0, idx]
            
            w_toxic = float(toxic_coefs[idx] * tfidf_val) if toxic_coefs is not None and idx < len(toxic_coefs) else 0.0
            w_bully = float(bully_coefs[idx] * tfidf_val) if bully_coefs is not None and idx < len(bully_coefs) else 0.0
            
            if abs(w_toxic) > 1e-4 or abs(w_bully) > 1e-4:
                impacts.append({
                    "word": word,
                    "weight_toxic": w_toxic,
                    "weight_bully": w_bully
                })
                
        # Urutkan berdasarkan impak absolut tertinggi
        impacts.sort(key=lambda x: max(abs(x["weight_toxic"]), abs(x["weight_bully"])), reverse=True)
        return [
            WordImportance(word=imp["word"], weight_toxic=imp["weight_toxic"], weight_bully=imp["weight_bully"])
            for imp in impacts
        ]
    except Exception as e:
        print(f"Warning: Gagal menghitung XAI explain_prediction: {e}")
        return []

def predict_transformer_raw(text: str) -> Dict[str, float]:
    if TRANSFORMER_TOKENIZER is None:
        return {"toxic_prob": 0.0, "bully_prob": 0.0}
    
    if TRANSFORMER_SESSION is not None:
        try:
            inputs = TRANSFORMER_TOKENIZER(text, padding=True, truncation=True, return_tensors="np")
            ort_inputs = {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64)
            }
            ort_outputs: Any = TRANSFORMER_SESSION.run(None, ort_inputs)
            logits = ort_outputs[0][0]
            probs = sigmoid(logits)
            return {
                "bully_prob": float(probs[0]),
                "toxic_prob": float(probs[1])
            }
        except Exception as e:
            print("Warning: Gagal memproses menggunakan session ONNX, fallback ke PyTorch:", e)

    global TRANSFORMER_MODEL
    if TRANSFORMER_MODEL is None and torch is not None:
        try:
            model_name = os.getenv("TRANSFORMER_MODEL_PATH", "nahiar/hatespeech-abusive-xlm-roberta-v1")
            print(f"Memuat model PyTorch secara dinamis untuk fallback: {model_name}...")
            TRANSFORMER_MODEL = AutoModelForSequenceClassification.from_pretrained(model_name)
            print("Model PyTorch berhasil dimuat secara dinamis!")
        except Exception as load_err:
            print("Error: Gagal memuat model PyTorch secara dinamis:", load_err)

    if TRANSFORMER_MODEL is not None and torch is not None:
        inputs = TRANSFORMER_TOKENIZER(text, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            logits = TRANSFORMER_MODEL(**inputs).logits[0]
        probs = torch.sigmoid(logits).tolist()
        return {
            "bully_prob": probs[0],
            "toxic_prob": probs[1]
        }

    return {"toxic_prob": 0.0, "bully_prob": 0.0}

def predict_lexicon(text: str, use_fuzzy: bool = True) -> LexiconResponse:
    import time
    start_time = time.perf_counter()
    norm = normalize_text(text)
    spaced_text = norm["spaced"]
    compact_text = norm["compact"]
    compact_strict_text = norm["compact_strict"]

    matches = []
    seen_phrases = set()

    for item in PREPARED_LEXICON:
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
            matches.append({
                "matched_phrase": phrase,
                "category": item["category"],
                "severity": item["severity"],
                "method": method
            })
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
        execution_time=round(elapsed, 2)
    )

def predict_ml(text: str) -> MLResponse:
    import time
    start_time = time.perf_counter()
    if ML_MODEL is None or ML_VECTORIZER is None:
        return MLResponse(text=text, is_toxic=False, is_bully=False, probability_toxic=0.0, probability_bully=0.0, category="Model ML belum termuat.", word_importances=[], execution_time=0.0)
    
    norm = normalize_text(text)["spaced"]
    tfidf_text = ML_VECTORIZER.transform([norm])
    
    pred_probs = ML_MODEL.predict_proba(tfidf_text)
    prob_toxic = float(pred_probs[0][0][1])
    prob_bully = float(pred_probs[1][0][1])
    
    is_toxic = prob_toxic >= get_threshold(THRESHOLDS, "threshold_toxic", 0.5)
    is_bully = prob_bully >= get_threshold(THRESHOLDS, "threshold_bully", 0.5)
    
    elapsed = (time.perf_counter() - start_time) * 1000.0
    return MLResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=prob_toxic,
        probability_bully=prob_bully,
        category=determine_category(is_toxic, is_bully),
        word_importances=explain_prediction(text),
        execution_time=round(elapsed, 2)
    )

def predict_transformers(text: str) -> TransformerResponse:
    import time
    start_time = time.perf_counter()
    res = predict_transformer_raw(text)
    prob_toxic = res["toxic_prob"]
    prob_bully = res["bully_prob"]
    
    is_toxic = prob_toxic >= get_threshold(THRESHOLDS, "threshold_toxic", 0.5)
    is_bully = prob_bully >= get_threshold(THRESHOLDS, "threshold_bully", 0.5)
    
    elapsed = (time.perf_counter() - start_time) * 1000.0
    return TransformerResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=prob_toxic,
        probability_bully=prob_bully,
        category=determine_category(is_toxic, is_bully),
        word_importances=explain_prediction(text),
        execution_time=round(elapsed, 2)
    )

def predict_ensemble(text: str) -> EnsembleResponse:
    import time
    start_time = time.perf_counter()
    ml_res = predict_ml(text)
    ml_toxic = ml_res.probability_toxic
    ml_bully = ml_res.probability_bully
    
    res_tr = predict_transformer_raw(text)
    tr_toxic = res_tr["toxic_prob"]
    tr_bully = res_tr["bully_prob"]
            
    w = get_calibrated_weights()
    w_ml_toxic = w.get("ml_toxic", 0.5)
    w_tr_toxic = w.get("tr_toxic", 0.5)
    w_ml_bully = w.get("ml_bully", 0.65)
    w_tr_bully = w.get("tr_bully", 0.35)

    final_toxic = combine_probabilities(ml_toxic, tr_toxic, w_ml_toxic, w_tr_toxic)
    final_bully = combine_probabilities(ml_bully, tr_bully, w_ml_bully, w_tr_bully)
    
    lex_res = predict_lexicon(text, use_fuzzy=False)
    final_toxic = apply_lexicon_evidence(final_toxic, lex_res)
    final_bully = apply_lexicon_evidence(final_bully, lex_res)
        
    is_toxic = final_toxic >= get_threshold(THRESHOLDS, "threshold_toxic", 0.5)
    is_bully = final_bully >= get_threshold(THRESHOLDS, "threshold_bully", 0.5)
    
    elapsed = (time.perf_counter() - start_time) * 1000.0
    return EnsembleResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=final_toxic,
        probability_bully=final_bully,
        category=determine_category(is_toxic, is_bully),
        word_importances=explain_prediction(text),
        execution_time=round(elapsed, 2)
    )

def run_ml_inference_sync(text: str) -> tuple[float, float]:
    if ML_VECTORIZER is None or ML_MODEL is None:
        return 0.0, 0.0
    norm = normalize_text(text)["spaced"]
    tfidf_text = ML_VECTORIZER.transform([norm])
    pred_probs_ml = ML_MODEL.predict_proba(tfidf_text)
    ml_toxic = float(pred_probs_ml[0][0][1])
    ml_bully = float(pred_probs_ml[1][0][1])
    return ml_toxic, ml_bully

async def _predict_hybrid_internal(text: str) -> HybridResponse:
    if ML_MODEL is None or ML_VECTORIZER is None:
        return HybridResponse(text=text, is_toxic=False, is_bully=False, probability_toxic=0.0, probability_bully=0.0, category="Aman", decision_source="Fallback", reason="Model ML belum termuat.", word_importances=[])

    t_t = get_threshold(THRESHOLDS, "threshold_toxic", 0.5)
    t_b = get_threshold(THRESHOLDS, "threshold_bully", 0.5)

    # 0. Pra-penyaringan Kontras Sentimen (Bypass langsung ke Tier 3 jika terindikasi sarkasme kuat dan Cloud LLM terkonfigurasi)
    is_sarcasm_candidate = detect_sentiment_contrast(text)
    if is_sarcasm_candidate and GEMINI_API_KEY:
        print(f"Pola kontras sentimen terdeteksi. Bypass ke Tier 3 (Cloud LLM) untuk: '{text}'")
        llm_res = await query_cloud_llm_async(text)
        if llm_res["success"]:
            is_toxic = llm_res["is_toxic"]
            is_bully = llm_res["is_bully"]
            return HybridResponse(
                text=text,
                is_toxic=is_toxic,
                is_bully=is_bully,
                probability_toxic=llm_decision_to_probability(is_toxic, t_t),
                probability_bully=llm_decision_to_probability(is_bully, t_b),
                category=determine_category(is_toxic, is_bully),
                decision_source="Tier 3 (Cloud LLM - Sarcasm Bypass)",
                reason=f"[Sarcasm Bypass] {llm_res['reason']}",
                word_importances=explain_prediction(text)
            )

    # 0.5 Pra-penyaringan Lexicon (Bypass jika terdeteksi sangat kasar / masuk kamus blacklist)
    lex_res = predict_lexicon(text, use_fuzzy=True)
    if lex_res.is_cyberbullying and lex_res.risk_label in ["sedang", "tinggi"]:
        matched_words = [m.matched_phrase for m in lex_res.matches]
        return HybridResponse(
            text=text,
            is_toxic=True,
            is_bully=True,  # Asumsikan bully jika tertangkap kamus keras (body shaming dll)
            probability_toxic=0.85,
            probability_bully=0.85,
            category=determine_category(True, True),
            decision_source="Tier 1 (Lexicon Kamus)",
            reason=f"Terdeteksi kata kasar/larangan di dalam teks: {', '.join(matched_words)}",
            word_importances=explain_prediction(text)
        )

    # 1. Jalankan ML (Tier 1)
    ml_toxic, ml_bully = await asyncio.to_thread(run_ml_inference_sync, text)

    # Jika ML sangat yakin (di luar rentang T - margin s/d T + margin)
    ml_confidence = is_confident_pair(ml_toxic, ml_bully, t_t, t_b)
    if ml_confidence.is_confident:
        is_toxic = ml_toxic >= t_t
        is_bully = ml_bully >= t_b
        return HybridResponse(
            text=text,
            is_toxic=is_toxic,
            is_bully=is_bully,
            probability_toxic=ml_toxic,
            probability_bully=ml_bully,
            category=determine_category(is_toxic, is_bully),
            decision_source="Tier 1 (ML Klasik)",
            reason="Klasifikasi konfiden tinggi berdasarkan bobot kata kunci model statistik. " + ml_confidence.reason,
            word_importances=explain_prediction(text)
        )

    # 2. Ragu-ragu -> Jalankan Transformer (Tier 2 ONNX / Fallback PyTorch)
    res_tr = await asyncio.to_thread(predict_transformer_raw, text)
    tr_toxic = res_tr["toxic_prob"]
    tr_bully = res_tr["bully_prob"]

    w = get_calibrated_weights()
    w_ml_toxic = w.get("ml_toxic", 0.5)
    w_tr_toxic = w.get("tr_toxic", 0.5)
    w_ml_bully = w.get("ml_bully", 0.65)
    w_tr_bully = w.get("tr_bully", 0.35)

    ens_toxic = combine_probabilities(ml_toxic, tr_toxic, w_ml_toxic, w_tr_toxic)
    ens_bully = combine_probabilities(ml_bully, tr_bully, w_ml_bully, w_tr_bully)

    ens_confidence = is_confident_pair(ens_toxic, ens_bully, t_t, t_b)
    if ens_confidence.is_confident:
        is_toxic = ens_toxic >= t_t
        is_bully = ens_bully >= t_b
        return HybridResponse(
            text=text,
            is_toxic=is_toxic,
            is_bully=is_bully,
            probability_toxic=ens_toxic,
            probability_bully=ens_bully,
            category=determine_category(is_toxic, is_bully),
            decision_source="Tier 2 (Ensemble ML & Transformer)",
            reason="Klasifikasi berbasis gabungan model statistik dan semantik Transformer. " + ens_confidence.reason,
            word_importances=explain_prediction(text)
        )

    # 3. Sangat ragu-ragu -> Panggil Cloud LLM (Tier 3 jika terkonfigurasi)
    if GEMINI_API_KEY:
        print(f"Kasus kompleks terdeteksi, meneruskan ke Tier 3 (Cloud LLM) untuk: '{text}'")
        llm_res = await query_cloud_llm_async(text)
        if llm_res["success"]:
            is_toxic = llm_res["is_toxic"]
            is_bully = llm_res["is_bully"]
            return HybridResponse(
                text=text,
                is_toxic=is_toxic,
                is_bully=is_bully,
                probability_toxic=llm_decision_to_probability(is_toxic, t_t),
                probability_bully=llm_decision_to_probability(is_bully, t_b),
                category=determine_category(is_toxic, is_bully),
                decision_source="Tier 3 (Cloud LLM)",
                reason=llm_res["reason"],
                word_importances=explain_prediction(text)
            )

    # Fallback
    is_toxic = ens_toxic >= t_t
    is_bully = ens_bully >= t_b
    return HybridResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=ens_toxic,
        probability_bully=ens_bully,
        category=determine_category(is_toxic, is_bully),
        decision_source="Fallback (Ensemble Terbatas)",
        reason="Cloud LLM tidak merespons, menggunakan keputusan cadangan dari model lokal.",
        word_importances=explain_prediction(text)
    )

async def predict_hybrid(text: str) -> HybridResponse:
    # 1. Cek memori klasifikasi historis terlebih dahulu
    cached_memory = await get_classification_memory(text)
    if cached_memory:
        print(f"[MEMORY HIT] Mengambil keputusan klasifikasi historis (Redis/PostgreSQL) untuk: '{text}'")
        cached_memory.word_importances = explain_prediction(text)
        return cached_memory

    # Jalankan inferensi hybrid
    res = await _predict_hybrid_internal(text)

    # Simpan hasil analisis baru ke dalam memori database persistent
    embedding_json = None
    if EMBEDDING_MODEL is not None:
        try:
            emb = EMBEDDING_MODEL.encode([text])[0]
            embedding_json = str(emb.tolist())
        except Exception:
            pass
    await save_classification_memory(res, embedding_json)
    return res

# predict_hybrid_stream definition below handles streaming logic

async def predict_hybrid_stream(text: str) -> AsyncGenerator[Dict[str, Any], None]:
    # 1. Cek memori klasifikasi historis terlebih dahulu
    cached_memory = await get_classification_memory(text)
    if cached_memory:
        print(f"[MEMORY HIT] Mengambil keputusan klasifikasi historis (Redis/PostgreSQL) untuk: '{text}'")
        cached_memory.word_importances = explain_prediction(text)
        yield {"chunk": cached_memory.reason, "done": True, "final_data": cached_memory}
        return

    if ML_MODEL is None or ML_VECTORIZER is None:
        res = HybridResponse(text=text, is_toxic=False, is_bully=False, probability_toxic=0.0, probability_bully=0.0, category="Aman", decision_source="Fallback", reason="Model ML belum termuat.", word_importances=[])
        yield {"chunk": res.reason, "done": True, "final_data": res}
        return
    
    t_t = get_threshold(THRESHOLDS, "threshold_toxic", 0.5)
    t_b = get_threshold(THRESHOLDS, "threshold_bully", 0.5)

    # 0. Pra-penyaringan Kontras Sentimen
    is_sarcasm_candidate = detect_sentiment_contrast(text)
    if is_sarcasm_candidate and GEMINI_API_KEY:
        print(f"Pola kontras sentimen terdeteksi. Bypass ke Tier 3 (Cloud LLM) untuk: '{text}'")
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
                        word_importances=explain_prediction(text)
                    )
                    embedding_json = None
                    if EMBEDDING_MODEL is not None:
                        try:
                            emb = EMBEDDING_MODEL.encode([text])[0]
                            embedding_json = str(emb.tolist())
                        except Exception:
                            pass
                    await save_classification_memory(final_res, embedding_json)
                    yield {"chunk": state["chunk"], "done": True, "final_data": final_res}
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
                        word_importances=explain_prediction(text)
                    )
                    embedding_json = None
                    if EMBEDDING_MODEL is not None:
                        try:
                            emb = EMBEDDING_MODEL.encode([text])[0]
                            embedding_json = str(emb.tolist())
                        except Exception:
                            pass
                    await save_classification_memory(final_res, embedding_json)
                    yield {"chunk": state["chunk"], "done": True, "final_data": final_res}
            else:
                yield {"chunk": state["chunk"], "done": False, "final_data": None}
        return

    # 1. Jalankan ML (Tier 1)
    ml_toxic, ml_bully = await asyncio.to_thread(run_ml_inference_sync, text)
    
    # Jika ML sangat yakin
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
            reason="Klasifikasi konfiden tinggi berdasarkan bobot kata kunci model statistik. " + ml_confidence.reason,
            word_importances=explain_prediction(text)
        )
        embedding_json = None
        if EMBEDDING_MODEL is not None:
            try:
                emb = EMBEDDING_MODEL.encode([text])[0]
                embedding_json = str(emb.tolist())
            except Exception:
                pass
        await save_classification_memory(res, embedding_json)
        yield {"chunk": res.reason, "done": True, "final_data": res}
        return
        
    # 2. Ragu-ragu -> Jalankan Transformer (Tier 2 ONNX / Fallback PyTorch)
    res_tr = await asyncio.to_thread(predict_transformer_raw, text)
    tr_toxic = res_tr["toxic_prob"]
    tr_bully = res_tr["bully_prob"]
    
    w = get_calibrated_weights()
    w_ml_toxic = w.get("ml_toxic", 0.5)
    w_tr_toxic = w.get("tr_toxic", 0.5)
    w_ml_bully = w.get("ml_bully", 0.65)
    w_tr_bully = w.get("tr_bully", 0.35)

    ens_toxic = combine_probabilities(ml_toxic, tr_toxic, w_ml_toxic, w_tr_toxic)
    ens_bully = combine_probabilities(ml_bully, tr_bully, w_ml_bully, w_tr_bully)
    
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
            word_importances=explain_prediction(text)
        )
        embedding_json = None
        if EMBEDDING_MODEL is not None:
            try:
                emb = EMBEDDING_MODEL.encode([text])[0]
                embedding_json = str(emb.tolist())
            except Exception:
                pass
        await save_classification_memory(res, embedding_json)
        yield {"chunk": res.reason, "done": True, "final_data": res}
        return
            
    # 3. Sangat ragu-ragu -> Panggil Cloud LLM (Tier 3 jika terkonfigurasi)
    if GEMINI_API_KEY:
        print(f"Kasus kompleks terdeteksi, meneruskan ke Tier 3 (Cloud LLM) untuk: '{text}'")
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
                        word_importances=explain_prediction(text)
                    )
                    embedding_json = None
                    if EMBEDDING_MODEL is not None:
                        try:
                            emb = EMBEDDING_MODEL.encode([text])[0]
                            embedding_json = str(emb.tolist())
                        except Exception:
                            pass
                    await save_classification_memory(final_res, embedding_json)
                    yield {"chunk": state["chunk"], "done": True, "final_data": final_res}
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
                        word_importances=explain_prediction(text)
                    )
                    embedding_json = None
                    if EMBEDDING_MODEL is not None:
                        try:
                            emb = EMBEDDING_MODEL.encode([text])[0]
                            embedding_json = str(emb.tolist())
                        except Exception:
                            pass
                    await save_classification_memory(final_res, embedding_json)
                    yield {"chunk": state["chunk"], "done": True, "final_data": final_res}
            else:
                yield {"chunk": state["chunk"], "done": False, "final_data": None}
        return
        
    # Fallback jika Cloud LLM tidak terkonfigurasi
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
        word_importances=explain_prediction(text)
    )
    embedding_json = None
    if EMBEDDING_MODEL is not None:
        try:
            emb = EMBEDDING_MODEL.encode([text])[0]
            embedding_json = str(emb.tolist())
        except Exception:
            pass
    await save_classification_memory(res, embedding_json)
    yield {"chunk": res.reason, "done": True, "final_data": res}
