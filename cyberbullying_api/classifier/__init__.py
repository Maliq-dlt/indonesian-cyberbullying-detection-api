import classifier.database as _database
import classifier.llm as _llm
import classifier.predictor_base as _predictor_base
from classifier.database import (
    get_cached_response as get_cached_response,
)
from classifier.database import (
    get_categorized_memory as get_categorized_memory,
)
from classifier.database import (
    get_classification_memory as get_classification_memory,
)

# Expose functions directly (their references do not change)
from classifier.database import (
    get_pg_pool as get_pg_pool,
)
from classifier.database import (
    get_redis as get_redis,
)
from classifier.database import (
    get_unvalidated_memory as get_unvalidated_memory,
)
from classifier.database import (
    init_cache_db as init_cache_db,
)
from classifier.database import (
    save_cached_response as save_cached_response,
)
from classifier.database import (
    save_classification_memory as save_classification_memory,
)
from classifier.database import (
    update_validation_status as update_validation_status,
)
from classifier.llm import (
    query_cloud_llm_async as query_cloud_llm_async,
)
from classifier.llm import (
    query_cloud_llm_stream_async as query_cloud_llm_stream_async,
)
from classifier.llm import (
    retrieve_relevant_examples as retrieve_relevant_examples,
)
from classifier.predictor import (
    init_models as init_models,
)
from classifier.predictor import (
    load_thresholds as load_thresholds,
)
from classifier.predictor import (
    predict_ensemble as predict_ensemble,
)
from classifier.predictor import (
    predict_hybrid as predict_hybrid,
)
from classifier.predictor import (
    predict_hybrid_stream as predict_hybrid_stream,
)
from classifier.predictor import (
    predict_lexicon as predict_lexicon,
)
from classifier.predictor import (
    predict_ml as predict_ml,
)
from classifier.predictor import (
    predict_transformer_raw as predict_transformer_raw,
)
from classifier.predictor import (
    predict_transformers as predict_transformers,
)
from classifier.predictor import (
    sigmoid as sigmoid,
)


# Use __getattr__ to dynamically look up global variables from their defining modules
def __getattr__(name):
    if name in (
        "GEMINI_BASE_URL",
        "GEMINI_MODEL",
        "ABUSIVE_WORDS_SET",
        "RAG_POOL_TEXTS",
        "RAG_POOL_VECTORS",
        "RAG_POOL_LABELS",
    ):
        return getattr(_llm, name)
    if name in (
        "BASE_DIR",
        "PREPARED_LEXICON",
        "ML_MODEL",
        "ML_VECTORIZER",
        "TRANSFORMER_SESSION",
        "TRANSFORMER_TOKENIZER",
        "TRANSFORMER_MODEL",
        "THRESHOLDS",
    ):
        return getattr(_predictor_base, name)
    if name in ("PG_POOL", "REDIS_CLIENT"):
        return getattr(_database, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
