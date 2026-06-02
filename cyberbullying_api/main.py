from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import os
import json
import httpx
import joblib
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Impor skema dan utilitas yang sudah dipisahkan (modular)
from models import *
from normalizer import (
    normalize_text,
    prepare_lexicon,
    contains_word_or_phrase,
    fuzzy_contains,
    init_slang_map
)

app = FastAPI(
    title="Cyberbullying & Hate Speech Detection API",
    description="API untuk mendeteksi cyberbullying bahasa Indonesia menggunakan pendekatan Leksikon, Machine Learning, dan Deep Learning Transformers.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models and prepared lexicon
PREPARED_LEXICON = []
ML_MODEL = None
ML_VECTORIZER = None
TRANSFORMER_MODEL = None
TRANSFORMER_TOKENIZER = None

# Base 24 cyberbullying words
BASE_CYBERBULLYING_LEXICON = [
    {"phrase": "mati lu", "category": "ancaman/serangan personal", "severity": "tinggi"},
    {"phrase": "mati lo", "category": "ancaman/serangan personal", "severity": "tinggi"},
    {"phrase": "mati loe", "category": "ancaman/serangan personal", "severity": "tinggi"},
    {"phrase": "mati kamu", "category": "ancaman/serangan personal", "severity": "tinggi"},
    {"phrase": "mending mati", "category": "dorongan menyakiti diri", "severity": "tinggi"},
    {"phrase": "bunuh diri", "category": "dorongan menyakiti diri", "severity": "tinggi"},
    {"phrase": "ga usah hidup", "category": "dorongan menyakiti diri", "severity": "tinggi"},
    {"phrase": "nggak usah hidup", "category": "dorongan menyakiti diri", "severity": "tinggi"},
    {"phrase": "dasar bodoh", "category": "hinaan", "severity": "sedang"},
    {"phrase": "dasar goblok", "category": "hinaan", "severity": "sedang"},
    {"phrase": "dasar tolol", "category": "hinaan", "severity": "sedang"},
    {"phrase": "dasar bego", "category": "hinaan", "severity": "sedang"},
    {"phrase": "dasar sampah", "category": "hinaan", "severity": "sedang"},
    {"phrase": "otak kosong", "category": "hinaan", "severity": "sedang"},
    {"phrase": "goblok", "category": "kata kasar", "severity": "sedang"},
    {"phrase": "tolol", "category": "kata kasar", "severity": "sedang"},
    {"phrase": "bodoh", "category": "kata kasar", "severity": "rendah"},
    {"phrase": "bego", "category": "kata kasar", "severity": "rendah"},
    {"phrase": "idiot", "category": "kata kasar", "severity": "sedang"},
    {"phrase": "sampah", "category": "kata kasar", "severity": "sedang"},
    {"phrase": "anjing", "category": "kata kasar", "severity": "sedang"},
    {"phrase": "bangsat", "category": "kata kasar", "severity": "sedang"},
    {"phrase": "babi", "category": "kata kasar", "severity": "sedang"},
    {"phrase": "kampret", "category": "kata kasar", "severity": "rendah"},
]

@app.on_event("startup")
def startup_event():
    global PREPARED_LEXICON, ML_MODEL, ML_VECTORIZER, TRANSFORMER_MODEL, TRANSFORMER_TOKENIZER
    
    print("=== Memulai Startup API Server ===")
    
    # 1. Load Slang Mapping (menggunakan normalizer)
    print("Memuat kamus slang alay & singkatan...")
    alay_path = os.path.join("..", "dataset 1", "new_kamusalay.csv")
    singkatan_path = os.path.join("..", "dataset 2", "kamus_singkatan.csv")
    slang_map = init_slang_map(alay_path, singkatan_path)
    print(f"Berhasil memuat {len(slang_map)} pemetaan slang/singkatan di normalizer.")

    # 2. Load and Prepare Lexicon (Base + Abusive Wordlist)
    print("Memuat kata kasar dari abusive.csv...")
    try:
        abusive_path = os.path.join("..", "dataset 1", "abusive.csv")
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
        print("Warning: Gagal memuat abusive.csv, menggunakan baseline lexicon:", e)
        import pandas as pd # fallback import if needed
        full_lexicon = BASE_CYBERBULLYING_LEXICON

    PREPARED_LEXICON = prepare_lexicon(full_lexicon)
    print(f"Leksikon siap: total {len(PREPARED_LEXICON)} kata/frasa cyberbullying.")

    # 3. Load Machine Learning Models
    print("Memuat model Machine Learning (Logistic Regression & TF-IDF)...")
    try:
        ML_MODEL = joblib.load("model_lr.joblib")
        ML_VECTORIZER = joblib.load("vectorizer.joblib")
        print("Model ML berhasil dimuat!")
    except Exception as e:
        print("Error: Gagal memuat model Machine Learning. Pastikan Anda menjalankan train_and_export.py dahulu:", e)

    # 4. Load Deep Learning Transformers
    print("Memuat model Deep Learning Transformers XLM-RoBERTa (sekitar 1.1 GB)...")
    try:
        model_name = "nahiar/hatespeech-abusive-xlm-roberta-v1"
        TRANSFORMER_TOKENIZER = AutoTokenizer.from_pretrained(model_name)
        TRANSFORMER_MODEL = AutoModelForSequenceClassification.from_pretrained(model_name)
        print("Model Transformer berhasil dimuat!")
    except Exception as e:
        print("Warning: Gagal memuat model Transformer:", e)

    print("=== API Server Siap Menerima Request! ===")

# Helper: check imports
import pandas as pd

# ----------------------------------------------------
# 2. API Endpoints
# ----------------------------------------------------

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Cyberbullying & Hate Speech Detection API is running.",
        "models_loaded": {
            "lexicon": len(PREPARED_LEXICON) > 0,
            "machine_learning": ML_MODEL is not None,
            "transformers": TRANSFORMER_MODEL is not None
        }
    }

@app.post("/predict/lexicon", response_model=LexiconResponse)
def predict_lexicon(req: TextRequest):
    norm = normalize_text(req.text)
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
        elif req.use_fuzzy and len(norm_compact) >= 6:
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
        text=req.text,
        normalized_spaced=spaced_text,
        normalized_compact=compact_text,
        is_cyberbullying=bool(matches),
        risk_label=risk_label,
        score=score,
        matches=matches
    )

def predict_transformer_raw(text: str) -> Dict[str, float]:
    if TRANSFORMER_MODEL is None or TRANSFORMER_TOKENIZER is None:
        return {"toxic_prob": 0.0, "bully_prob": 0.0}
    inputs = TRANSFORMER_TOKENIZER(text, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        logits = TRANSFORMER_MODEL(**inputs).logits[0]
    probs = torch.sigmoid(logits).tolist()
    return {
        "bully_prob": probs[0],
        "toxic_prob": probs[1]
    }

@app.post("/predict/ml", response_model=MLResponse)
def predict_ml(req: TextRequest):
    if ML_MODEL is None or ML_VECTORIZER is None:
        raise HTTPException(status_code=503, detail="Model ML belum termuat.")
    
    norm = normalize_text(req.text)["spaced"]
    tfidf_text = ML_VECTORIZER.transform([norm])
    
    pred_probs = ML_MODEL.predict_proba(tfidf_text)
    prob_toxic = float(pred_probs[0][0][1])
    prob_bully = float(pred_probs[1][0][1])
    
    pred_l = ML_MODEL.predict(tfidf_text)[0]
    is_toxic = bool(pred_l[0])
    is_bully = bool(pred_l[1])
    
    return MLResponse(
        text=req.text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=prob_toxic,
        probability_bully=prob_bully,
        category=determine_category(is_toxic, is_bully)
    )

@app.post("/predict/transformers", response_model=TransformerResponse)
def predict_transformers(req: TextRequest):
    if TRANSFORMER_MODEL is None or TRANSFORMER_TOKENIZER is None:
        raise HTTPException(status_code=503, detail="Model Transformer belum termuat.")
    
    try:
        res = predict_transformer_raw(req.text)
        prob_toxic = res["toxic_prob"]
        prob_bully = res["bully_prob"]
        
        is_toxic = prob_toxic >= 0.5
        is_bully = prob_bully >= 0.5
        
        return TransformerResponse(
            text=req.text,
            is_toxic=is_toxic,
            is_bully=is_bully,
            probability_toxic=prob_toxic,
            probability_bully=prob_bully,
            category=determine_category(is_toxic, is_bully)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/ensemble", response_model=EnsembleResponse)
def predict_ensemble(req: TextRequest):
    if ML_MODEL is None or ML_VECTORIZER is None:
        raise HTTPException(status_code=503, detail="Model ML belum termuat.")
    
    norm = normalize_text(req.text)["spaced"]
    tfidf_text = ML_VECTORIZER.transform([norm])
    
    pred_probs_ml = ML_MODEL.predict_proba(tfidf_text)
    ml_toxic = float(pred_probs_ml[0][0][1])
    ml_bully = float(pred_probs_ml[1][0][1])
    
    tr_toxic = 0.0
    tr_bully = 0.0
    if TRANSFORMER_MODEL is not None and TRANSFORMER_TOKENIZER is not None:
        try:
            res_tr = predict_transformer_raw(req.text)
            tr_toxic = res_tr["toxic_prob"]
            tr_bully = res_tr["bully_prob"]
        except Exception as e:
            print("Warning: Gagal memproses Transformer di Ensemble:", e)
            
    final_toxic = 0.5 * ml_toxic + 0.5 * tr_toxic if tr_toxic > 0.0 else ml_toxic
    final_bully = 0.65 * ml_bully + 0.35 * tr_bully if tr_bully > 0.0 else ml_bully
    
    lex_res = predict_lexicon(req)
    if lex_res.is_cyberbullying:
        final_toxic = max(final_toxic, 0.90)
        
    is_toxic = final_toxic >= 0.5
    is_bully = final_bully >= 0.5
    
    return EnsembleResponse(
        text=req.text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=final_toxic,
        probability_bully=final_bully,
        category=determine_category(is_toxic, is_bully)
    )

def query_ollama(text: str, model_name: str = "qwen2.5-coder:7b") -> Dict[str, Any]:
    url = "http://localhost:11434/api/generate"
    prompt = f"""
    Analisis teks Bahasa Indonesia di bawah ini untuk mendeteksi dua parameter:
    1. "is_toxic": Apakah teks menggunakan kata kasar, kotor, atau umpatan gaul secara eksplisit? (true/false)
    2. "is_bully": Apakah teks berniat untuk menghina, merendahkan, mencemooh, atau merundung seseorang secara personal (termasuk sarkasme/sindiran halus)? (true/false)

    Format output wajib JSON valid seperti ini tanpa penjelasan lain:
    {{
        "is_toxic": true,
        "is_bully": false,
        "reason": "alasan singkat dalam bahasa Indonesia"
    }}

    Teks yang dianalisis:
    "{text}"
    """
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        with httpx.Client(timeout=6.0) as client:
            response = client.post(url, json=payload)
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
        print("Warning: Gagal menghubungi Ollama lokal:", e)
        
    return {
        "is_toxic": False,
        "is_bully": False,
        "reason": "Gagal terhubung ke Ollama lokal (pastikan Ollama berjalan di port 11434).",
        "success": False
    }

@app.post("/predict/hybrid", response_model=HybridResponse)
def predict_hybrid(req: TextRequest):
    if ML_MODEL is None or ML_VECTORIZER is None:
        raise HTTPException(status_code=503, detail="Model ML belum termuat.")
    
    # 1. Jalankan ML (Tier 1)
    norm = normalize_text(req.text)["spaced"]
    tfidf_text = ML_VECTORIZER.transform([norm])
    pred_probs_ml = ML_MODEL.predict_proba(tfidf_text)
    ml_toxic = float(pred_probs_ml[0][0][1])
    ml_bully = float(pred_probs_ml[1][0][1])
    
    # Jika ML sangat yakin (di luar rentang 0.25 - 0.75 untuk kedua label)
    if (ml_toxic > 0.75 or ml_toxic < 0.25) and (ml_bully > 0.75 or ml_bully < 0.25):
        is_toxic = ml_toxic >= 0.5
        is_bully = ml_bully >= 0.5
        return HybridResponse(
            text=req.text,
            is_toxic=is_toxic,
            is_bully=is_bully,
            probability_toxic=ml_toxic,
            probability_bully=ml_bully,
            category=determine_category(is_toxic, is_bully),
            decision_source="Tier 1 (ML Klasik)",
            reason="Klasifikasi konfiden tinggi berdasarkan bobot kata kunci model statistik."
        )
        
    # 2. Ragu-ragu -> Jalankan Transformer XLM-RoBERTa (Tier 2)
    tr_toxic = 0.0
    tr_bully = 0.0
    tr_loaded = TRANSFORMER_MODEL is not None and TRANSFORMER_TOKENIZER is not None
    if tr_loaded:
        try:
            res_tr = predict_transformer_raw(req.text)
            tr_toxic = res_tr["toxic_prob"]
            tr_bully = res_tr["bully_prob"]
            
            ens_toxic = 0.5 * ml_toxic + 0.5 * tr_toxic
            ens_bully = 0.65 * ml_bully + 0.35 * tr_bully
            
            if (ens_toxic > 0.75 or ens_toxic < 0.25) and (ens_bully > 0.75 or ens_bully < 0.25):
                is_toxic = ens_toxic >= 0.5
                is_bully = ens_bully >= 0.5
                return HybridResponse(
                    text=req.text,
                    is_toxic=is_toxic,
                    is_bully=is_bully,
                    probability_toxic=ens_toxic,
                    probability_bully=ens_bully,
                    category=determine_category(is_toxic, is_bully),
                    decision_source="Tier 2 (Ensemble ML & Transformer)",
                    reason="Klasifikasi berbasis gabungan model statistik dan semantik Transformer."
                )
        except Exception as e:
            print("Warning: Gagal memproses Tier 2 di Hybrid:", e)
            
    # 3. Sangat ragu-ragu -> Panggil Ollama (Tier 3)
    print(f"Kasus kompleks terdeteksi, meneruskan ke Tier 3 (Ollama LLM) untuk: '{req.text}'")
    ollama_res = query_ollama(req.text)
    if ollama_res["success"]:
        is_toxic = ollama_res["is_toxic"]
        is_bully = ollama_res["is_bully"]
        return HybridResponse(
            text=req.text,
            is_toxic=is_toxic,
            is_bully=is_bully,
            probability_toxic=1.0 if is_toxic else 0.0,
            probability_bully=1.0 if is_bully else 0.0,
            category=determine_category(is_toxic, is_bully),
            decision_source="Tier 3 (Ollama Qwen LLM)",
            reason=ollama_res["reason"]
        )
        
    # Jika Ollama gagal/mati, gunakan fallback hasil ensemble/ML
    fallback_toxic = 0.5 * ml_toxic + 0.5 * tr_toxic if tr_loaded else ml_toxic
    fallback_bully = 0.65 * ml_bully + 0.35 * tr_bully if tr_loaded else ml_bully
    
    lex_res = predict_lexicon(req)
    if lex_res.is_cyberbullying:
        fallback_toxic = max(fallback_toxic, 0.90)
        
    is_toxic = fallback_toxic >= 0.5
    is_bully = fallback_bully >= 0.5
    
    return HybridResponse(
        text=req.text,
        is_toxic=is_toxic,
        is_bully=is_bully,
        probability_toxic=fallback_toxic,
        probability_bully=fallback_bully,
        category=determine_category(is_toxic, is_bully),
        decision_source="Fallback (Ensemble Terbatas)",
        reason="Ollama lokal tidak merespons, menggunakan keputusan cadangan dari model lokal."
    )

@app.post("/predict/batch", response_model=BatchResponse)
def predict_batch(req: BatchTextRequest):
    results = []
    for text in req.texts:
        pred = predict_hybrid(TextRequest(text=text))
        results.append(BatchItemResponse(
            text=pred.text,
            is_toxic=pred.is_toxic,
            is_bully=pred.is_bully,
            probability_toxic=pred.probability_toxic,
            probability_bully=pred.probability_bully,
            category=pred.category,
            decision_source=pred.decision_source,
            reason=pred.reason
        ))
    return BatchResponse(results=results)
