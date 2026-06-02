import os
import json
import httpx
import joblib
import torch
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from transformers import AutoTokenizer, AutoModelForSequenceClassification
try:
    import onnxruntime as ort
except ImportError:
    ort = None

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

# Tentukan direktori dasar dinamis untuk pathing absolut
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Global variables for models and prepared lexicon
PREPARED_LEXICON = []
ML_MODEL = None
ML_VECTORIZER = None
TRANSFORMER_SESSION = None
TRANSFORMER_TOKENIZER = None
TRANSFORMER_MODEL = None

THRESHOLDS = {
    "threshold_toxic": 0.5,
    "threshold_bully": 0.5
}

def load_thresholds():
    global THRESHOLDS
    thresholds_path = os.path.join(BASE_DIR, "thresholds.json")
    if os.path.exists(thresholds_path):
        try:
            with open(thresholds_path, "r") as f:
                THRESHOLDS = json.load(f)
            print(f"Ambang batas perutean dinamis dimuat: Toxic={THRESHOLDS['threshold_toxic']:.2f}, Bully={THRESHOLDS['threshold_bully']:.2f}")
        except Exception as e:
            print("Warning: Gagal memuat thresholds.json, menggunakan default 0.5:", e)

def init_models():
    global PREPARED_LEXICON, ML_MODEL, ML_VECTORIZER, TRANSFORMER_SESSION, TRANSFORMER_TOKENIZER, TRANSFORMER_MODEL
    
    print("=== Inisialisasi Model Klasifikasi ===")
    
    # 1. Load Slang Mapping (menggunakan path absolut dinamis)
    print("Memuat kamus slang alay & singkatan...")
    alay_path = os.path.join(BASE_DIR, "..", "dataset 1", "new_kamusalay.csv")
    singkatan_path = os.path.join(BASE_DIR, "..", "dataset 2", "kamus_singkatan.csv")
    slang_map = init_slang_map(alay_path, singkatan_path)
    print(f"Berhasil memuat {len(slang_map)} pemetaan slang/singkatan.")

    # 2. Load and Prepare Lexicon
    print("Memuat kata kasar dari abusive.csv...")
    try:
        abusive_path = os.path.join(BASE_DIR, "..", "dataset 1", "abusive.csv")
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

    PREPARED_LEXICON = prepare_lexicon(full_lexicon)
    print(f"Leksikon siap: total {len(PREPARED_LEXICON)} kata/frasa.")

    # 3. Load Machine Learning Models
    print("Memuat model Machine Learning (Logistic Regression & TF-IDF)...")
    try:
        ML_MODEL = joblib.load(os.path.join(BASE_DIR, "model_lr.joblib"))
        ML_VECTORIZER = joblib.load(os.path.join(BASE_DIR, "vectorizer.joblib"))
        print("Model ML berhasil dimuat!")
    except Exception as e:
        print("Error: Gagal memuat model Machine Learning:", e)

    # 4. Load thresholds.json
    load_thresholds()

    # 5. Load Deep Learning Transformers (ONNX / PyTorch)
    print("Memuat model Deep Learning Transformers XLM-RoBERTa...")
    model_name = "nahiar/hatespeech-abusive-xlm-roberta-v1"
    try:
        TRANSFORMER_TOKENIZER = AutoTokenizer.from_pretrained(model_name)
    except Exception as e:
        print("Warning: Gagal memuat tokenizer:", e)

    # Cek model quantized ONNX
    onnx_path = os.path.join(BASE_DIR, "model_quantized.onnx")
    if not os.path.exists(onnx_path):
        print("model_quantized.onnx tidak ditemukan. Menjalankan ekspor otomatis...")
        try:
            import subprocess
            import sys
            export_script = os.path.join(BASE_DIR, "export_onnx.py")
            subprocess.run([sys.executable, export_script], check=True)
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
            ort_outputs = TRANSFORMER_SESSION.run(None, ort_inputs)
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

async def query_ollama_async(text: str, model_name: str = None) -> Dict[str, Any]:
    url = "http://localhost:11434/api/generate"
    
    if not model_name:
        model_name = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    
    # Skema output terstruktur yang formal
    schema = {
        "type": "object",
        "properties": {
            "is_toxic": {"type": "boolean"},
            "is_bully": {"type": "boolean"},
            "reason": {"type": "string"}
        },
        "required": ["is_toxic", "is_bully", "reason"]
    }
    
    # System prompt linguistik Indonesia yang mendalam (mengakomodasi casual slang vs bullying & sindiran/sarkasme)
    system_instruction = (
        "Sistem: Anda adalah ahli sosiolinguistik bahasa Indonesia yang spesifik mendeteksi cyberbullying, hate speech, dan sarkasme.\n"
        "Tugas: Analisis teks secara objektif dan klasifikasikan ke parameter 'is_toxic' dan 'is_bully'.\n"
        "Panduan Nuansa Bahasa Gaul Indonesia:\n"
        "- Bedakan penggunaan kata kasar seperti 'anjing', 'bangsat', 'bego', 'goblok' jika digunakan sebagai pujian/casual slang (is_toxic=true, is_bully=false) seperti 'anjing keren banget lu bang'.\n"
        "- Deteksi sarkasme / ejekan halus sebagai intimidasi personal (is_toxic=false, is_bully=true) seperti 'ganteng banget mukalu kaya spakbor mio' atau 'pintar sekali kamu, nilai ujianmu nol'.\n"
        "- Serangan verbal kasar langsung dinilai sebagai keduanya (is_toxic=true, is_bully=true)."
    )
    
    prompt = f"""
    {system_instruction}

    Gunakan format JSON yang valid mengikuti skema ini secara ketat:
    {json.dumps(schema, indent=2)}

    Teks yang dianalisis:
    "{text}"
    """
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": schema
    }
    
    try:
        # Peningkatan timeout menjadi 15.0 detik untuk keandalan loading VRAM
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                res_json = response.json()
                content = json.loads(res_json["response"])
                return {
                    "is_toxic": bool(content.get("is_toxic", False)),
                    "is_bully": bool(content.get("is_bully", False)),
                    "reason": str(content.get("reason", "Analisis Ollama selesai.")),
                    "success": True
                }
    except Exception as e:
        print("Warning: Gagal menghubungi Ollama dengan skema JSON:", e)
        
    return {
        "is_toxic": False,
        "is_bully": False,
        "reason": "Gagal terhubung ke Ollama lokal dengan format skema.",
        "success": False
    }

async def predict_hybrid(text: str) -> HybridResponse:
    if ML_MODEL is None or ML_VECTORIZER is None:
        return HybridResponse(text=text, is_toxic=False, is_bully=False, probability_toxic=0.0, probability_bully=0.0, category="Aman", decision_source="Fallback", reason="Model ML belum termuat.")
    
    # 0. Pra-penyaringan Kontras Sentimen (Bypass langsung ke Tier 3 jika terindikasi sarkasme kuat)
    is_sarcasm_candidate = detect_sentiment_contrast(text)
    if is_sarcasm_candidate:
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
    res_tr = predict_transformer_raw(text)
    tr_toxic = res_tr["toxic_prob"]
    tr_bully = res_tr["bully_prob"]
    
    ens_toxic = 0.5 * ml_toxic + 0.5 * tr_toxic
    ens_bully = 0.65 * ml_bully + 0.35 * tr_bully
    
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
            
    # 3. Sangat ragu-ragu -> Panggil Ollama (Tier 3)
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
