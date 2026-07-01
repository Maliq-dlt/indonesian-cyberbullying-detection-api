from prometheus_client import Counter, Gauge, Histogram

REQUESTS_TOTAL = Counter(
    "cyberbullying_requests_total", "Total HTTP requests received", ["method", "endpoint", "status"]
)

REQUESTS_LATENCY = Histogram("cyberbullying_request_duration_seconds", "HTTP request latency in seconds", ["endpoint"])

PREDICTIONS_TOTAL = Counter(
    "cyberbullying_model_predictions_total", "Total model predictions made", ["decision_source", "category"]
)

CACHE_HITS_TOTAL = Counter("cyberbullying_cache_hits_total", "Total classification cache hits", ["cache_type"])

# Phase 3 additional metrics
INFERENCE_LATENCY = Histogram(
    "cyberbullying_inference_duration_seconds", "Inference latency in seconds by tier", ["tier"]
)

CACHE_LOOKUPS_TOTAL = Counter(
    "cyberbullying_cache_lookups_total",
    "Total classification cache lookups by cache type and status (hit/miss)",
    ["cache_type", "status"],
)

TRIE_WORDS_COUNT = Gauge("cyberbullying_trie_normalizer_words_total", "Total number of words loaded in Trie normalizer")

GEMINI_FAILURES_TOTAL = Counter("cyberbullying_gemini_failures_total", "Total failures of external Gemini LLM calls")
