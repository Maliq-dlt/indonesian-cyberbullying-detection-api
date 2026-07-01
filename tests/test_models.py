"""Unit tests untuk Pydantic models dan fungsi helper di models.py.

Mencakup validasi model, determine_category, dan check_ssrf_url.
"""

import pytest
from pydantic import ValidationError
from cyberbullying_api.models import (
    TextRequest,
    BatchTextRequest,
    ScrapeTikTokRequest,
    ScrapeXRequest,
    ReallocateRequest,
    BulkReallocateItem,
    BulkReallocateRequest,
    WordImportance,
    HybridResponse,
    BatchItemResponse,
    determine_category,
    check_ssrf_url,
)


# ── determine_category ────────────────────────────────────────────────────────

class TestDetermineCategory:
    def test_toxic_and_bully(self):
        assert determine_category(True, True) == "Bully-toxic(bully)"

    def test_non_toxic_bully_sarkasme(self):
        assert determine_category(False, True) == "non-Toxic Bully(Sarkasme)"

    def test_toxic_non_bully_slang(self):
        assert determine_category(True, False) == "Toxic non-bully(slang)"

    def test_non_toxic_non_bully_normal(self):
        assert determine_category(False, False) == "non-toxic non-bully(Normal)"


# ── TextRequest ───────────────────────────────────────────────────────────────

class TestTextRequest:
    def test_valid_text(self):
        req = TextRequest(text="halo dunia")
        assert req.text == "halo dunia"
        assert req.use_fuzzy is False

    def test_empty_text_rejected(self):
        with pytest.raises(ValidationError):
            TextRequest(text="")

    def test_text_too_long(self):
        with pytest.raises(ValidationError):
            TextRequest(text="a" * 501)

    def test_max_length_accepted(self):
        req = TextRequest(text="a" * 500)
        assert len(req.text) == 500

    def test_use_fuzzy_optional(self):
        req = TextRequest(text="coba", use_fuzzy=True)
        assert req.use_fuzzy is True


# ── BatchTextRequest ──────────────────────────────────────────────────────────

class TestBatchTextRequest:
    def test_valid_batch(self):
        req = BatchTextRequest(texts=["teks1", "teks2"])
        assert len(req.texts) == 2
        assert req.model_name == "llama3.2:3b"

    def test_empty_list_rejected(self):
        with pytest.raises(ValidationError):
            BatchTextRequest(texts=[])

    def test_over_50_items_rejected(self):
        with pytest.raises(ValidationError):
            BatchTextRequest(texts=["a"] * 51)

    def test_exactly_50_items_accepted(self):
        req = BatchTextRequest(texts=["a"] * 50)
        assert len(req.texts) == 50

    def test_single_item(self):
        req = BatchTextRequest(texts=["satu teks"])
        assert len(req.texts) == 1


# ── ReallocateRequest ─────────────────────────────────────────────────────────

class TestReallocateRequest:
    def test_valid_reallocate(self):
        req = ReallocateRequest(text="bodoh sekali", new_is_toxic=True, new_is_bully=False)
        assert req.text == "bodoh sekali"
        assert req.new_is_toxic is True
        assert req.new_is_bully is False

    def test_empty_text_rejected(self):
        with pytest.raises(ValidationError):
            ReallocateRequest(text="", new_is_toxic=True, new_is_bully=False)


# ── BulkReallocateRequest ─────────────────────────────────────────────────────

class TestBulkReallocateRequest:
    def test_valid_bulk(self):
        req = BulkReallocateRequest(items=[
            BulkReallocateItem(text="teks1", new_is_toxic=True, new_is_bully=False),
            BulkReallocateItem(text="teks2", new_is_toxic=False, new_is_bully=True),
        ])
        assert len(req.items) == 2


# ── Response Models ───────────────────────────────────────────────────────────

class TestResponseModels:
    def test_word_importance(self):
        wi = WordImportance(word="bodoh", weight_toxic=0.9, weight_bully=0.7)
        assert wi.word == "bodoh"

    def test_hybrid_response(self):
        resp = HybridResponse(
            text="coba",
            is_toxic=True,
            is_bully=False,
            probability_toxic=0.85,
            probability_bully=0.3,
            category="Toxic non-bully(slang)",
            decision_source="ml_ensemble",
            reason="confident",
        )
        assert resp.decision_source == "ml_ensemble"
        assert resp.word_importances == []

    def test_batch_item_response(self):
        item = BatchItemResponse(
            text="uji",
            is_toxic=False,
            is_bully=False,
            probability_toxic=0.1,
            probability_bully=0.05,
            category="non-toxic non-bully(Normal)",
            decision_source="lexicon",
            reason="aman",
        )
        assert item.category == "non-toxic non-bully(Normal)"


# ── check_ssrf_url ────────────────────────────────────────────────────────────

class TestCheckSsrfUrl:
    def test_reject_ftp_scheme(self):
        with pytest.raises(ValueError, match="http"):
            check_ssrf_url("ftp://evil.com", ["evil.com"])

    def test_reject_no_hostname(self):
        with pytest.raises(ValueError):
            check_ssrf_url("http://", ["example.com"])

    def test_reject_disallowed_domain(self):
        with pytest.raises(ValueError, match="Domain"):
            check_ssrf_url("https://evil.com/path", ["example.com"])

    def test_reject_localhost(self):
        with pytest.raises(ValueError, match="lokal"):
            check_ssrf_url("http://localhost/admin", ["localhost"])

    def test_reject_127_ip(self):
        with pytest.raises(ValueError, match="lokal"):
            check_ssrf_url("http://127.0.0.1/admin", ["127.0.0.1"])

    def test_allow_subdomain(self):
        result = check_ssrf_url("https://www.tiktok.com/video/123", ["tiktok.com"])
        assert result == "https://www.tiktok.com/video/123"

    def test_allow_exact_domain(self):
        result = check_ssrf_url("https://x.com/post", ["x.com", "twitter.com"])
        assert result == "https://x.com/post"


# ── ScrapeTikTokRequest ───────────────────────────────────────────────────────

class TestScrapeTikTokRequest:
    def test_valid_tiktok_url(self):
        req = ScrapeTikTokRequest(url="https://www.tiktok.com/@user/video/123")
        assert req.max_comments == 20

    def test_invalid_domain_rejected(self):
        with pytest.raises(ValidationError):
            ScrapeTikTokRequest(url="https://evil.com/fake")

    def test_max_comments_bounds(self):
        with pytest.raises(ValidationError):
            ScrapeTikTokRequest(url="https://www.tiktok.com/@u/video/1", max_comments=0)
        with pytest.raises(ValidationError):
            ScrapeTikTokRequest(url="https://www.tiktok.com/@u/video/1", max_comments=101)


# ── ScrapeXRequest ────────────────────────────────────────────────────────────

class TestScrapeXRequest:
    def test_valid_x_url(self):
        req = ScrapeXRequest(url="https://x.com/user/status/123")
        assert req.max_tweets == 20

    def test_valid_twitter_url(self):
        req = ScrapeXRequest(url="https://twitter.com/user/status/123")
        assert req.max_tweets == 20

    def test_invalid_domain_rejected(self):
        with pytest.raises(ValidationError):
            ScrapeXRequest(url="https://evil.com/fake")
