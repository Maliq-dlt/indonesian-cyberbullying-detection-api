"""Unit tests tambahan untuk normalizer.py.

Mencakup fungsi-fungsi: edit_distance_one, reduce_repeated_chars,
replace_leet, fuzzy_contains, detect_sentiment_contrast, contains_word_or_phrase.
"""

import pytest
from cyberbullying_api.normalizer import (
    LEET_MAP,
    contains_word_or_phrase,
    detect_sentiment_contrast,
    edit_distance_one,
    fuzzy_contains,
    normalize_text,
    reduce_repeated_chars,
    replace_leet,
)


# ── edit_distance_one ─────────────────────────────────────────────────────────

class TestEditDistanceOne:
    def test_identical_strings(self):
        assert edit_distance_one("kata", "kata") is False

    def test_single_substitution(self):
        assert edit_distance_one("kutu", "kuta") is True

    def test_single_insertion(self):
        assert edit_distance_one("ktu", "katu") is True

    def test_single_deletion(self):
        assert edit_distance_one("katua", "kata") is True

    def test_two_differences(self):
        assert edit_distance_one("abc", "xyz") is False

    def test_length_diff_gt_1(self):
        assert edit_distance_one("a", "abc") is False

    def test_empty_vs_single(self):
        assert edit_distance_one("", "a") is True

    def test_empty_vs_empty(self):
        assert edit_distance_one("", "") is False


# ── reduce_repeated_chars ─────────────────────────────────────────────────────

class TestReduceRepeatedChars:
    def test_reduce_triple(self):
        assert reduce_repeated_chars("begooo", max_repeat=2) == "begoo"

    def test_reduce_quadruple(self):
        assert reduce_repeated_chars("hahaaaah", max_repeat=2) == "hahaah"

    def test_no_reduction_needed(self):
        assert reduce_repeated_chars("bego", max_repeat=2) == "bego"

    def test_max_repeat_1(self):
        assert reduce_repeated_chars("begooo", max_repeat=1) == "bego"

    def test_max_repeat_zero_returns_original(self):
        text = "begooo"
        assert reduce_repeated_chars(text, max_repeat=0) == text


# ── replace_leet ──────────────────────────────────────────────────────────────

class TestReplaceLeet:
    def test_basic_leet(self):
        assert replace_leet("g0bl0k") == "goblok"

    def test_symbols(self):
        assert replace_leet("b@ngs@t") == "bangsat"

    def test_mixed(self):
        assert replace_leet("m4t1") == "mati"

    def test_no_leet(self):
        assert replace_leet("halo") == "halo"

    def test_all_leet_chars_mapped(self):
        for digit, letter in LEET_MAP.items():
            assert replace_leet(digit) == letter


# ── fuzzy_contains ────────────────────────────────────────────────────────────

class TestFuzzyContains:
    def test_exact_match(self):
        assert fuzzy_contains("goblok", "goblok") is True

    def test_close_match(self):
        assert fuzzy_contains("goblokk", "goblok") is True

    def test_no_match(self):
        assert fuzzy_contains("halodunia", "goblok") is False

    def test_empty_text(self):
        assert fuzzy_contains("", "goblok") is False

    def test_empty_pattern(self):
        assert fuzzy_contains("goblok", "") is False

    def test_short_pattern_rejected(self):
        assert fuzzy_contains("halo", "go") is False


# ── detect_sentiment_contrast ─────────────────────────────────────────────────

class TestDetectSentimentContrast:
    def test_positive_and_negative(self):
        assert detect_sentiment_contrast("pintar tapi nol") is True

    def test_only_positive(self):
        assert detect_sentiment_contrast("pintar sekali") is False

    def test_only_negative(self):
        assert detect_sentiment_contrast("salah semua") is False

    def test_neither(self):
        assert detect_sentiment_contrast("halo dunia") is False

    def test_case_insensitive(self):
        assert detect_sentiment_contrast("PINTAR tapi GAGAL") is True


# ── contains_word_or_phrase ───────────────────────────────────────────────────

class TestContainsWordOrPhrase:
    def test_word_present(self):
        assert contains_word_or_phrase("dasar goblok", "goblok") is True

    def test_word_not_present(self):
        assert contains_word_or_phrase("halo dunia", "goblok") is False

    def test_empty_pattern(self):
        assert contains_word_or_phrase("halo", "") is False

    def test_partial_word_no_match(self):
        # "bodoh" should NOT match inside "bodohiya" because word boundary is enforced
        assert contains_word_or_phrase("bodohiya", "bodoh") is False

    def test_phrase_match(self):
        assert contains_word_or_phrase("dasar sampah masyarakat", "sampah") is True


# ── normalize_text ────────────────────────────────────────────────────────────

class TestNormalizeTextExtended:
    def test_zero_width_chars_removed(self):
        result = normalize_text("halo\u200Bdunia")
        assert "halodunia" in result["spaced"] or "halo dunia" in result["spaced"]

    def test_html_unescape(self):
        result = normalize_text("goblok &amp; bodoh")
        assert "goblok" in result["spaced"]
        assert "bodoh" in result["spaced"]

    def test_uppercase_normalized(self):
        result = normalize_text("GOBLOK")
        assert result["spaced"] == "goblok"

    def test_compact_no_spaces(self):
        result = normalize_text("mati lu")
        assert " " not in result["compact"]

    def test_reduce_repeats_false(self):
        result = normalize_text("begooo", reduce_repeats=False)
        assert "begooo" in result["spaced"] or "begooo" in result["compact"]
