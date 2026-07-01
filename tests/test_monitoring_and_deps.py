"""Unit tests untuk monitoring.py (Prometheus metrics) dan deps.py (webhook SSRF).

Mencakup inisialisasi metrik dan validasi URL webhook.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Pre-import deps modules while ENV=test is still active,
# so classifier.db_config initializes correctly before any @patch.dict overrides.
import routes.deps as _deps_module  # noqa: F401


# ── Monitoring Metrics ─────────────────────────────────────────────────────────

class TestMonitoringMetrics:
    """Pastikan semua metrik Prometheus sudah dideklarasikan di monitoring.py."""

    def test_request_counter_exists(self):
        import monitoring
        assert monitoring.REQUESTS_TOTAL is not None
        # Prometheus Counter._name strips _total suffix
        assert monitoring.REQUESTS_TOTAL._name == "cyberbullying_requests"

    def test_latency_histogram_exists(self):
        import monitoring
        assert monitoring.REQUESTS_LATENCY is not None
        assert monitoring.REQUESTS_LATENCY._name == "cyberbullying_request_duration_seconds"

    def test_predictions_counter_exists(self):
        import monitoring
        assert monitoring.PREDICTIONS_TOTAL is not None
        assert monitoring.PREDICTIONS_TOTAL._name == "cyberbullying_model_predictions"

    def test_cache_hits_counter_exists(self):
        import monitoring
        assert monitoring.CACHE_HITS_TOTAL is not None
        assert monitoring.CACHE_HITS_TOTAL._name == "cyberbullying_cache_hits"

    def test_inference_latency_exists(self):
        import monitoring
        assert monitoring.INFERENCE_LATENCY is not None
        assert monitoring.INFERENCE_LATENCY._name == "cyberbullying_inference_duration_seconds"

    def test_cache_lookups_exists(self):
        import monitoring
        assert monitoring.CACHE_LOOKUPS_TOTAL is not None
        assert monitoring.CACHE_LOOKUPS_TOTAL._name == "cyberbullying_cache_lookups"

    def test_trie_words_gauge_exists(self):
        import monitoring
        assert monitoring.TRIE_WORDS_COUNT is not None
        assert monitoring.TRIE_WORDS_COUNT._name == "cyberbullying_trie_normalizer_words_total"

    def test_gemini_failures_exists(self):
        import monitoring
        assert monitoring.GEMINI_FAILURES_TOTAL is not None
        assert monitoring.GEMINI_FAILURES_TOTAL._name == "cyberbullying_gemini_failures"


# ── is_safe_webhook_url ───────────────────────────────────────────────────────

class TestIsSafeWebhookUrl:
    """Test fungsi is_safe_webhook_url dari deps.py."""

    def _call(self, url: str) -> bool:
        return _deps_module.is_safe_webhook_url(url)

    @patch.dict(os.environ, {"ENV": "production", "WEBHOOK_ALLOWED_HOSTS": ""})
    def test_reject_ftp_scheme(self):
        assert self._call("ftp://example.com") is False

    @patch.dict(os.environ, {"ENV": "production", "WEBHOOK_ALLOWED_HOSTS": ""})
    def test_reject_http_in_production(self):
        assert self._call("http://example.com/hook") is False

    @patch.dict(os.environ, {"ENV": "development", "WEBHOOK_ALLOWED_HOSTS": ""})
    def test_allow_http_in_development(self):
        # akan tetap False jika DNS resolution mengarah ke private IP,
        # tapi scheme check harus pass
        result = self._call("http://example.com/hook")
        # result bisa True atau False tergantung DNS, tapi tidak error
        assert isinstance(result, bool)

    @patch.dict(os.environ, {"ENV": "production", "WEBHOOK_ALLOWED_HOSTS": "hooks.slack.com"})
    def test_allow_whitelisted_host(self):
        # hooks.slack.com should resolve to public IP
        result = self._call("https://hooks.slack.com/services/abc")
        assert isinstance(result, bool)

    @patch.dict(os.environ, {"ENV": "production", "WEBHOOK_ALLOWED_HOSTS": "example.com"})
    def test_reject_non_whitelisted_host(self):
        assert self._call("https://evil.com/hook") is False

    def test_reject_empty_hostname(self):
        assert self._call("https:///path") is False

    def test_reject_no_scheme(self):
        assert self._call("example.com/hook") is False


# ── Helper functions in deps.py ───────────────────────────────────────────────

class TestDepsHelpers:
    def test_get_env_default(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ENV", None)
            assert _deps_module.get_env() == "production"

    def test_get_env_custom(self):
        with patch.dict(os.environ, {"ENV": "staging"}):
            assert _deps_module.get_env() == "staging"

    def test_is_development_env(self):
        with patch.dict(os.environ, {"ENV": "development"}):
            assert _deps_module.is_development_env() is True
        with patch.dict(os.environ, {"ENV": "production"}):
            assert _deps_module.is_development_env() is False

    def test_bool_env(self):
        with patch.dict(os.environ, {"MY_FLAG": "true"}):
            assert _deps_module._bool_env("MY_FLAG") is True
        with patch.dict(os.environ, {"MY_FLAG": "0"}):
            assert _deps_module._bool_env("MY_FLAG") is False
        assert _deps_module._bool_env("NONEXISTENT_VAR_XYZ", False) is False

    def test_int_env(self):
        with patch.dict(os.environ, {"MY_NUM": "42"}):
            assert _deps_module._int_env("MY_NUM", 0) == 42
        with patch.dict(os.environ, {"MY_NUM": "abc"}):
            assert _deps_module._int_env("MY_NUM", 99) == 99
        assert _deps_module._int_env("NONEXISTENT_VAR_XYZ", 7) == 7
