"""Base module for predictor — globals, thresholds, model initialization.

This module holds all shared mutable state and initialization logic so that
other predictor sub-modules can import from here without circular imports.
"""

import json
import logging
import os
import subprocess
import sys
import threading
from typing import Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger("bullyguard")

from transformers import AutoModelForSequenceClassification, AutoTokenizer

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

from normalizer import BASE_CYBERBULLYING_LEXICON, init_slang_map, prepare_lexicon

import classifier.llm as llm_module
from classifier.database import init_cache_db

# ── Path ──────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Global mutable state (shared by all predictor sub-modules) ────────────────

PREPARED_LEXICON: list = []
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

# ── Thresholds ────────────────────────────────────────────────────────────────

def load_thresholds():
    global THRESHOLDS
    thresholds_path = os.path.join(BASE_DIR, "models", "thresholds.json")
    if os.path.exists(thresholds_path):
        try:
            with open(thresholds_path) as f:
                THRESHOLDS = json.load(f)
            logger.info("Thresholds loaded", extra={"toxic": THRESHOLDS['threshold_toxic'], "bully": THRESHOLDS['threshold_bully']})
        except Exception as e:
            logger.warning("Failed to load thresholds.json, using default 0.5", extra={"error": str(e)})


def get_calibrated_weights() -> dict:
    try:
        from classifier.settings_store import get_settings_sync
        settings = get_settings_sync()
        return settings.get("ensemble_weights", {
            "ml_toxic": 0.5, "tr_toxic": 0.5, "ml_bully": 0.65, "tr_bully": 0.35
        })
    except Exception:
        return {"ml_toxic": 0.5, "tr_toxic": 0.5, "ml_bully": 0.65, "tr_bully": 0.35}


# ── Model Initialization ─────────────────────────────────────────────────────

def init_models():
    with _MODEL_LOCK:
        _init_models_inner()


def _init_models_inner():
    global PREPARED_LEXICON, ML_MODEL, ML_VECTORIZER, TRANSFORMER_SESSION
    global TRANSFORMER_TOKENIZER, TRANSFORMER_MODEL, EMBEDDING_MODEL

    logger.info("=== Classification model initialization ===")

    init_cache_db()

    # 1. Slang Mapping
    logger.info("Loading slang dictionary (alay & abbreviations)...")
    alay_path = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "new_kamusalay.csv")
    singkatan_path = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "kamus_singkatan.csv")
    slang_map = init_slang_map(alay_path, singkatan_path)
    logger.info("Slang mappings loaded", extra={"count": len(slang_map)})

    # 2. Lexicon
    logger.info("Loading abusive words from abusive.csv...")
    try:
        abusive_path = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "abusive.csv")
        df_abusive = pd.read_csv(abusive_path)
        abusive_words = df_abusive['ABUSIVE'].dropna().unique().tolist()

        existing_phrases = {item["phrase"].lower() for item in BASE_CYBERBULLYING_LEXICON}
        new_terms = []
        for word in abusive_words:
            word_lower = word.strip().lower()
            if word_lower not in existing_phrases:
                new_terms.append({"phrase": word_lower, "category": "kata kasar (abusive.csv)", "severity": "sedang"})
                existing_phrases.add(word_lower)
        full_lexicon = BASE_CYBERBULLYING_LEXICON + new_terms
    except Exception as e:
        logger.warning("Failed to load abusive.csv, using baseline lexicon", extra={"error": str(e)})
        full_lexicon = BASE_CYBERBULLYING_LEXICON
        abusive_words = []

    llm_module.ABUSIVE_WORDS_SET = set(abusive_words)
    PREPARED_LEXICON = prepare_lexicon(full_lexicon)
    logger.info("Lexicon ready", extra={"total_phrases": len(PREPARED_LEXICON)})

    # 3. ML Model
    logger.info("Loading ML model (Logistic Regression & TF-IDF)...")
    try:
        ML_MODEL = joblib.load(os.path.join(BASE_DIR, "models", "model_lr.joblib"))
        ML_VECTORIZER = joblib.load(os.path.join(BASE_DIR, "models", "vectorizer.joblib"))
        logger.info("ML model loaded successfully")
    except Exception as e:
        logger.error("Failed to load ML model", extra={"error": str(e)})

    # 3.5 RAG Pool
    logger.info("Loading RAG pool dataset for LLM...")
    try:
        combined_path = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "combined_dataset.csv")
        if os.path.exists(combined_path):
            df_combined = pd.read_csv(combined_path)
            df_combined = df_combined.dropna(subset=["String", "Label"])
            df_bully_pool = df_combined[df_combined["Label"].isin(["Bullying", "negatif", "negative"])]
            df_nonbully_pool = df_combined[~df_combined["Label"].isin(["Bullying", "negatif", "negative"])]
            df_bully = df_bully_pool.sample(min(150, len(df_bully_pool)), random_state=42, replace=False)
            df_nonbully = df_nonbully_pool.sample(min(150, len(df_nonbully_pool)), random_state=42, replace=False)
            df_sampled = pd.concat([df_bully, df_nonbully], ignore_index=True)

            llm_module.RAG_POOL_TEXTS = df_sampled["String"].tolist()
            llm_module.RAG_POOL_LABELS = df_sampled["Label"].tolist()

            if ML_VECTORIZER is not None:
                llm_module.RAG_POOL_VECTORS = ML_VECTORIZER.transform(llm_module.RAG_POOL_TEXTS)
                logger.info("RAG pool ready", extra={"samples": len(llm_module.RAG_POOL_TEXTS)})
        else:
            logger.warning("Combined dataset not found for RAG pool, using static Few-Shot")
    except Exception as e:
        logger.warning("Failed to load RAG pool", extra={"error": str(e)})

    # 4. Thresholds
    load_thresholds()

    # 5. Transformer (ONNX / PyTorch)
    model_name = os.getenv("TRANSFORMER_MODEL_PATH", "nahiar/hatespeech-abusive-xlm-roberta-v1")
    logger.info("Loading Deep Learning Transformers", extra={"model": model_name})
    try:
        TRANSFORMER_TOKENIZER = AutoTokenizer.from_pretrained(model_name)
    except Exception as e:
        logger.warning("Failed to load tokenizer", extra={"error": str(e)})

    model_slug = model_name.replace("/", "_").replace("\\", "_").replace(".", "_")
    onnx_filename = f"model_{model_slug}_quantized.onnx"
    onnx_path = os.path.join(BASE_DIR, "models", onnx_filename)

    if not os.path.exists(onnx_path) and os.getenv("AUTO_EXPORT_ONNX", "false").lower() in {"1", "true", "yes"}:
        logger.info("ONNX file not found, running auto-export", extra={"filename": onnx_filename})
        try:
            export_script = os.path.join(BASE_DIR, "export_onnx.py")
            legacy_onnx = os.path.join(BASE_DIR, "models", "model_quantized.onnx")
            if os.path.exists(legacy_onnx):
                try:
                    os.remove(legacy_onnx)
                    logger.info("Cleaning legacy model_quantized.onnx before new export")
                except Exception as del_err:
                    logger.warning("Failed to clean legacy model_quantized.onnx", extra={"error": str(del_err)})

            subprocess.run([sys.executable, export_script], check=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})

            if os.path.exists(legacy_onnx):
                import shutil
                shutil.move(legacy_onnx, onnx_path)
                logger.info("ONNX model exported successfully", extra={"path": onnx_path})
            else:
                raise FileNotFoundError("Berkas ekspor model_quantized.onnx tidak ditemukan setelah proses ekspor selesai.")
        except Exception as e:
            logger.error("Auto ONNX export failed, falling back to PyTorch", extra={"error": str(e)})
    elif not os.path.exists(onnx_path):
        logger.info("ONNX file not found, auto-export disabled", extra={"filename": onnx_filename})

    if os.path.exists(onnx_path) and ort is not None:
        try:
            available_providers = ort.get_available_providers()
            providers_to_use = []
            if "TensorrtExecutionProvider" in available_providers:
                providers_to_use.append("TensorrtExecutionProvider")
            if "CUDAExecutionProvider" in available_providers:
                providers_to_use.append("CUDAExecutionProvider")
            providers_to_use.append("CPUExecutionProvider")

            TRANSFORMER_SESSION = ort.InferenceSession(onnx_path, providers=providers_to_use)
            logger.info("ONNX INT8 quantized model loaded", extra={"providers": TRANSFORMER_SESSION.get_providers()})
        except Exception as e:
            logger.warning("Failed to load ONNX session, falling back to PyTorch", extra={"error": str(e)})
            TRANSFORMER_SESSION = None

    if TRANSFORMER_SESSION is None:
        if torch is None:
            logger.warning("PyTorch not installed, PyTorch fallback disabled")
        else:
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                TRANSFORMER_MODEL = AutoModelForSequenceClassification.from_pretrained(model_name).to(device)
                logger.info("PyTorch model loaded (ONNX fallback)", extra={"device": device})
            except Exception as e:
                logger.warning("Failed to load PyTorch model", extra={"error": str(e)})

    # 6. Sentence Transformer
    logger.info("Loading sentence-transformer for vector embedding...")
    try:
        if SentenceTransformer is not None:
            EMBEDDING_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("Sentence-transformer loaded (all-MiniLM-L6-v2)")
        else:
            logger.warning("sentence-transformers not installed, vector search disabled")
    except Exception as e:
        logger.warning("Failed to load sentence-transformer model", extra={"error": str(e)})


# ── Utility ───────────────────────────────────────────────────────────────────

def sigmoid(x):
    return 1 / (1 + np.exp(-x))
