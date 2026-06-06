# Expose all database modules for backward compatibility
from classifier.db_config import (
    get_pg_pool, get_redis, encrypt_text, decrypt_text, derived_key, key_source, CIPHER_SUITE,
    PG_URL, REDIS_URL, PG_POOL, REDIS_CLIENT, SQLITE_WRITE_LOCK, init_sqlite_db, init_cache_db
)
from classifier.db_cache import (
    get_cached_response, save_cached_response
)
from classifier.db_memory import (
    save_classification_memory, get_classification_memory, get_unvalidated_memory,
    get_categorized_memory, update_validation_status, save_retraining_history,
    get_retraining_history
)
