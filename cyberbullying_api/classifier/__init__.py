import classifier.database as _database
import classifier.llm as _llm
import classifier.predictor as _predictor
import classifier.predictor_base as _predictor_base

# Expose functions directly (their references do not change)
from classifier.database import (
    get_pg_pool, get_redis, init_cache_db,
    get_cached_response, save_cached_response,
    save_classification_memory, get_classification_memory,
    get_unvalidated_memory, update_validation_status,
    get_categorized_memory
)
from classifier.llm import (
    retrieve_relevant_examples, query_cloud_llm_async, query_cloud_llm_stream_async
)
from classifier.predictor import (
    load_thresholds, init_models, sigmoid, predict_transformer_raw,
    predict_lexicon, predict_ml, predict_transformers,
    predict_ensemble, predict_hybrid, predict_hybrid_stream
)

# Use __getattr__ to dynamically look up global variables from their defining modules
def __getattr__(name):
    if name in ("GEMINI_BASE_URL", "GEMINI_MODEL", "ABUSIVE_WORDS_SET", "RAG_POOL_TEXTS", "RAG_POOL_VECTORS", "RAG_POOL_LABELS"):
        return getattr(_llm, name)
    if name in ("BASE_DIR", "PREPARED_LEXICON", "ML_MODEL", "ML_VECTORIZER", "TRANSFORMER_SESSION", "TRANSFORMER_TOKENIZER", "TRANSFORMER_MODEL", "THRESHOLDS"):
        return getattr(_predictor_base, name)
    if name in ("PG_POOL", "REDIS_CLIENT"):
        return getattr(_database, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
