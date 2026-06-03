import os
import re
import json
import joblib
import torch
import numpy as np
import pandas as pd
import asyncio
import subprocess
import sys
from typing import List, Dict, Any

from transformers import AutoTokenizer, AutoModelForSequenceClassification
try:
    import onnxruntime as ort
except ImportError:
    ort = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from models import *
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
from classifier.llm import query_ollama_async, OLLAMA_URL
import classifier.llm as llm_module

# Tentukan direktori dasar dinamis untuk pathing absolut (parent dari classifier/ yaitu cyberbullying_api/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Global variables for models and prepared lexicon
PREPARED_LEXICON = []
ML_MODEL = None
ML_VECTORIZER = None
TRANSFORMER_SESSION = None
TRANSFORMER_TOKENIZER = None
TRANSFORMER_MODEL = None
EMBEDDING_MODEL = None

THRESHOLDS = {
    "threshold_toxic": 0.5,
    "threshold_bully": 0.5
}

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

def init_models():
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
    
    if not os.path.exists(onnx_path):
        print(f"{onnx_filename} tidak ditemukan. Menjalankan ekspor otomatis...")
        try:
            export_script = os.path.join(BASE_DIR, "export_onnx.py")
            subprocess.run([sys.executable, export_script], check=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            # export_onnx.py hardcode ke model_quantized.onnx, kita pindahkan ke path spesifik model
            legacy_onnx = os.path.join(BASE_DIR, "models", "model_quantized.onnx")
            if os.path.exists(legacy_onnx):
                import shutil
                shutil.move(legacy_onnx, onnx_path)
        except Exception as e:
            print("Gagal ekspor ONNX otomatis, fallback ke PyTorch:", e)

    if os.path.exists(onnx_path) and ort is not None:
        try:
            TRANSFORMER_SESSION = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
            print("Model ONNX terkuantisasi INT8 berhasil dimuat!")
        except Exception as e:
            print("Warning: Gagal memuat session ONNX runtime, fallback ke PyTorch:", e)
            TRANSFORMER_SESSION = None

    if TRANSFORMER_SESSION is None:
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

    if TRANSFORMER_MODEL is not None:
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

    return LexiconResponse(
        text=text,
        normalized_spaced=spaced_text,
        normalized_compact=compact_text,
        is_cyberbullying=bool(matches),
        risk_label=risk_label,
        score=score,
        matches=matches
    )

def predict_ml(text: str) -> MLResponse:
    if ML_MODEL is None or ML_VECTORIZER is None:
        return MLResponse(text=text, is_toxic=False, is_bully=False, probability_toxic=0.0, probability_bully=0.0, category="Model ML belum termuat.")
    
    norm = normalize_text(text)["spaced"]
    tfidf_text = ML_VECTORIZER.transform([norm])
    
    pred_probs = ML_MODEL.predict_proba(tfidf_text)
    prob_toxic = float(pred_probs[0][0][1])
    prob_bully = float(pred_probs[1][0][1])
    
    is_toxic = prob_toxic >= THRESHOLDS.get("threshold_toxic", 0.5)
    is_bully = prob_bully >= THRESHOLDS.get("threshold_bully", 0.5)
    
    return MLResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=prob_toxic,
        probability_bully=prob_bully,
        category=determine_category(is_toxic, is_bully)
    )

def predict_transformers(text: str) -> TransformerResponse:
    res = predict_transformer_raw(text)
    prob_toxic = res["toxic_prob"]
    prob_bully = res["bully_prob"]
    
    is_toxic = prob_toxic >= THRESHOLDS.get("threshold_toxic", 0.5)
    is_bully = prob_bully >= THRESHOLDS.get("threshold_bully", 0.5)
    
    return TransformerResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=prob_toxic,
        probability_bully=prob_bully,
        category=determine_category(is_toxic, is_bully)
    )

def predict_ensemble(text: str) -> EnsembleResponse:
    ml_res = predict_ml(text)
    ml_toxic = ml_res.probability_toxic
    ml_bully = ml_res.probability_bully
    
    res_tr = predict_transformer_raw(text)
    tr_toxic = res_tr["toxic_prob"]
    tr_bully = res_tr["bully_prob"]
            
    final_toxic = 0.5 * ml_toxic + 0.5 * tr_toxic if tr_toxic > 0.0 else ml_toxic
    final_bully = 0.65 * ml_bully + 0.35 * tr_bully if tr_bully > 0.0 else ml_bully
    
    lex_res = predict_lexicon(text, use_fuzzy=False)
    if lex_res.is_cyberbullying:
        final_toxic = max(final_toxic, 0.90)
        
    is_toxic = final_toxic >= THRESHOLDS.get("threshold_toxic", 0.5)
    is_bully = final_bully >= THRESHOLDS.get("threshold_bully", 0.5)
    
    return EnsembleResponse(
        text=text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=final_toxic,
        probability_bully=final_bully,
        category=determine_category(is_toxic, is_bully)
    )

async def _predict_hybrid_internal(text: str) -> HybridResponse:
    if ML_MODEL is None or ML_VECTORIZER is None:
        return HybridResponse(text=text, is_toxic=False, is_bully=False, probability_toxic=0.0, probability_bully=0.0, category="Aman", decision_source="Fallback", reason="Model ML belum termuat.")

    # 0. Pra-penyaringan Kontras Sentimen (Bypass langsung ke Tier 3 jika terindikasi sarkasme kuat dan Ollama terkonfigurasi)
    is_sarcasm_candidate = detect_sentiment_contrast(text)
    if is_sarcasm_candidate and OLLAMA_URL:
        print(f"Pola kontras sentimen terdeteksi. Bypass ke Tier 3 (Ollama LLM) untuk: '{text}'")
        ollama_res = await query_ollama_async(text)
        if ollama_res["success"]:
            is_toxic = ollama_res["is_toxic"]
            is_bully = ollama_res["is_bully"]
            return HybridResponse(
                text=text,
                is_toxic=is_toxic,
                is_bully=is_bully,
                probability_toxic=1.0 if is_toxic else 0.0,
                probability_bully=1.0 if is_bully else 0.0,
                category=determine_category(is_toxic, is_bully),
                decision_source="Tier 3 (Ollama Qwen LLM - Sarcasm Bypass)",
                reason=f"[Sarcasm Bypass] {ollama_res['reason']}"
            )

    # 1. Jalankan ML (Tier 1)
    norm = normalize_text(text)["spaced"]
    tfidf_text = ML_VECTORIZER.transform([norm])
    pred_probs_ml = ML_MODEL.predict_proba(tfidf_text)
    ml_toxic = float(pred_probs_ml[0][0][1])
    ml_bully = float(pred_probs_ml[1][0][1])

    t_t = THRESHOLDS.get("threshold_toxic", 0.5)
    t_b = THRESHOLDS.get("threshold_bully", 0.5)

    # Jika ML sangat yakin (di luar rentang T - 0.25 s/d T + 0.25)
    if (abs(ml_toxic - t_t) >= 0.25) and (abs(ml_bully - t_b) >= 0.25):
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
            reason="Klasifikasi konfiden tinggi berdasarkan bobot kata kunci model statistik."
        )

    # 2. Ragu-ragu -> Jalankan Transformer (Tier 2 ONNX / Fallback PyTorch)
    res_tr = await asyncio.to_thread(predict_transformer_raw, text)
    tr_toxic = res_tr["toxic_prob"]
    tr_bully = res_tr["bully_prob"]

    ens_toxic = 0.5 * ml_toxic + 0.5 * tr_toxic if tr_toxic > 0.0 else ml_toxic
    ens_bully = 0.65 * ml_bully + 0.35 * tr_bully if tr_bully > 0.0 else ml_bully

    if (abs(ens_toxic - t_t) >= 0.25) and (abs(ens_bully - t_b) >= 0.25):
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
            reason="Klasifikasi berbasis gabungan model statistik dan semantik Transformer."
        )

    # 3. Sangat ragu-ragu -> Panggil Ollama (Tier 3 jika terkonfigurasi)
    if OLLAMA_URL:
        print(f"Kasus kompleks terdeteksi, meneruskan ke Tier 3 (Ollama LLM) untuk: '{text}'")
        ollama_res = await query_ollama_async(text)
        if ollama_res["success"]:
            is_toxic = ollama_res["is_toxic"]
            is_bully = ollama_res["is_bully"]
            return HybridResponse(
                text=text,
                is_toxic=is_toxic,
                is_bully=is_bully,
                probability_toxic=1.0 if is_toxic else 0.0,
                probability_bully=1.0 if is_bully else 0.0,
                category=determine_category(is_toxic, is_bully),
                decision_source="Tier 3 (Ollama Qwen LLM)",
                reason=ollama_res["reason"]
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
        reason="Ollama lokal tidak merespons, menggunakan keputusan cadangan dari model lokal."
    )

async def predict_hybrid(text: str) -> HybridResponse:
    # 1. Cek memori klasifikasi historis terlebih dahulu
    cached_memory = await get_classification_memory(text)
    if cached_memory:
        print(f"[MEMORY HIT] Mengambil keputusan klasifikasi historis (Redis/PostgreSQL) untuk: '{text}'")
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

async def predict_hybrid_stream(text: str):
    # 1. Cek memori klasifikasi historis terlebih dahulu
    cached_memory = await get_classification_memory(text)
    if cached_memory:
        print(f"[MEMORY HIT] Mengambil keputusan klasifikasi historis (Redis/PostgreSQL) untuk: '{text}'")
        yield {"chunk": cached_memory.reason, "done": True, "final_data": cached_memory}
        return

    if ML_MODEL is None or ML_VECTORIZER is None:
        res = HybridResponse(text=text, is_toxic=False, is_bully=False, probability_toxic=0.0, probability_bully=0.0, category="Aman", decision_source="Fallback", reason="Model ML belum termuat.")
        yield {"chunk": res.reason, "done": True, "final_data": res}
        return
    
    # 0. Pra-penyaringan Kontras Sentimen
    is_sarcasm_candidate = detect_sentiment_contrast(text)
    if is_sarcasm_candidate and OLLAMA_URL:
        print(f"Pola kontras sentimen terdeteksi. Bypass ke Tier 3 (Ollama LLM) untuk: '{text}'")
        async for state in query_ollama_stream_async(text):
            if state["done"]:
                ollama_res = state["final_data"]
                if ollama_res["success"]:
                    is_toxic = ollama_res["is_toxic"]
                    is_bully = ollama_res["is_bully"]
                    final_res = HybridResponse(
                        text=text,
                        is_toxic=is_toxic,
                        is_bully=is_bully,
                        probability_toxic=1.0 if is_toxic else 0.0,
                        probability_bully=1.0 if is_bully else 0.0,
                        category=determine_category(is_toxic, is_bully),
                        decision_source="Tier 3 (Ollama Qwen LLM - Sarcasm Bypass)",
                        reason=f"[Sarcasm Bypass] {ollama_res['reason']}"
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
                        reason=ollama_res["reason"]
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
    norm = normalize_text(text)["spaced"]
    tfidf_text = ML_VECTORIZER.transform([norm])
    pred_probs_ml = ML_MODEL.predict_proba(tfidf_text)
    ml_toxic = float(pred_probs_ml[0][0][1])
    ml_bully = float(pred_probs_ml[1][0][1])
    
    t_t = THRESHOLDS.get("threshold_toxic", 0.5)
    t_b = THRESHOLDS.get("threshold_bully", 0.5)
    
    # Jika ML sangat yakin
    if (abs(ml_toxic - t_t) >= 0.25) and (abs(ml_bully - t_b) >= 0.25):
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
            reason="Klasifikasi konfiden tinggi berdasarkan bobot kata kunci model statistik."
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
    
    ens_toxic = 0.5 * ml_toxic + 0.5 * tr_toxic if tr_toxic > 0.0 else ml_toxic
    ens_bully = 0.65 * ml_bully + 0.35 * tr_bully if tr_bully > 0.0 else ml_bully
    
    if (abs(ens_toxic - t_t) >= 0.25) and (abs(ens_bully - t_b) >= 0.25):
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
            reason="Klasifikasi berbasis gabungan model statistik dan semantik Transformer."
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
            
    # 3. Sangat ragu-ragu -> Panggil Ollama (Tier 3 jika terkonfigurasi)
    if OLLAMA_URL:
        print(f"Kasus kompleks terdeteksi, meneruskan ke Tier 3 (Ollama LLM) untuk: '{text}'")
        async for state in query_ollama_stream_async(text):
            if state["done"]:
                ollama_res = state["final_data"]
                if ollama_res["success"]:
                    is_toxic = ollama_res["is_toxic"]
                    is_bully = ollama_res["is_bully"]
                    final_res = HybridResponse(
                        text=text,
                        is_toxic=is_toxic,
                        is_bully=is_bully,
                        probability_toxic=1.0 if is_toxic else 0.0,
                        probability_bully=1.0 if is_bully else 0.0,
                        category=determine_category(is_toxic, is_bully),
                        decision_source="Tier 3 (Ollama Qwen LLM)",
                        reason=ollama_res["reason"]
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
                        reason="Ollama lokal gagal merespons, menggunakan keputusan cadangan dari model lokal."
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
        
    # Fallback jika Ollama tidak terkonfigurasi
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
        reason="Ollama lokal tidak dikonfigurasi, menggunakan keputusan cadangan dari model lokal."
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
