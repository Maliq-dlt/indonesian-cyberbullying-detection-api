import html
import logging
import os
import re
import unicodedata

import pandas as pd

logger = logging.getLogger("bullyguard")

# Global Slang Map (diisi melalui fungsi init_slang_map)
SLANG_MAP = {}
ABUSIVE_WORDS_SET = set()
FORMAL_WORDS_SET = set()
ABUSIVE_TRIE = None


class AbusiveTrie:
    def __init__(self):
        self.root = {}

    def insert(self, word: str):
        node = self.root
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        node["$"] = word

    def search_edit_distance_one(self, word: str) -> str | None:
        n = len(word)
        results = []

        def dfs(node, i, edit_count):
            if edit_count > 1:
                return
            if i == n:
                if "$" in node and edit_count == 1:
                    results.append(node["$"])
                if edit_count == 0:
                    for char in node:
                        if char != "$":
                            dfs(node[char], i, 1)
                return

            char = word[i]
            if char in node:
                dfs(node[char], i + 1, edit_count)

            if edit_count == 0:
                for next_char in node:
                    if next_char != "$" and next_char != char:
                        dfs(node[next_char], i + 1, 1)
                dfs(node, i + 1, 1)
                for next_char in node:
                    if next_char != "$":
                        dfs(node[next_char], i, 1)

        dfs(self.root, 0, 0)
        return results[0] if results else None


# Set kata hubung, kata ganti, dan kata kerja/sifat umum bahasa Indonesia untuk mencegah salah koreksi
INDONESIAN_COMMON_WORDS = {
    "sampai",
    "kamu",
    "sekali",
    "untuk",
    "dengan",
    "dalam",
    "akan",
    "bisa",
    "dapat",
    "oleh",
    "atau",
    "pada",
    "juga",
    "dari",
    "telah",
    "tapi",
    "tetapi",
    "bagi",
    "serta",
    "yaitu",
    "yakni",
    "kami",
    "kita",
    "dia",
    "mereka",
    "saya",
    "aku",
    "anda",
    "ingin",
    "harus",
    "bukan",
    "tidak",
    "belum",
    "sangat",
    "lebih",
    "paling",
    "hanya",
    "saja",
    "baru",
    "lama",
    "banyak",
    "sedikit",
    "semua",
    "setiap",
    "adalah",
    "ialah",
    "merupakan",
    "bahwa",
    "seperti",
    "bagai",
    "bagaikan",
    "maka",
    "wah",
    "nilai",
    "ujian",
    "ujianmu",
}

LEET_MAP = {
    "0": "o",
    "1": "i",
    "!": "i",
    "|": "i",
    "¡": "i",
    "3": "e",
    "4": "a",
    "@": "a",
    "5": "s",
    "$": "s",
    "7": "t",
    "+": "t",
    "8": "b",
    "9": "g",
    "6": "g",
}

ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
MULTISPACE_RE = re.compile(r"\s+")
REPEATED_CHAR_RE = re.compile(r"(.)\1{2,}")
REPEATED_CHAR_ANY_RE = re.compile(r"(.)\1+")


def edit_distance_one(s1: str, s2: str) -> bool:
    """Mengembalikan True jika jarak edit Levenshtein antara s1 dan s2 tepat 1."""
    len1, len2 = len(s1), len(s2)
    if abs(len1 - len2) > 1:
        return False

    if len1 == len2:
        # Substitusi tunggal
        diffs = 0
        for c1, c2 in zip(s1, s2, strict=False):
            if c1 != c2:
                diffs += 1
                if diffs > 1:
                    return False
        return diffs == 1
    else:
        # Insersi / Delesi tunggal
        if len1 > len2:
            s1, s2 = s2, s1  # s2 selalu lebih panjang
        i = 0
        j = 0
        diffs = 0
        while i < len(s1) and j < len(s2):
            if s1[i] != s2[j]:
                diffs += 1
                if diffs > 1:
                    return False
                j += 1
            else:
                i += 1
                j += 1
        return True


def get_close_match_abusive(word: str) -> str | None:
    """Mencari apakah kata memiliki kedekatan jarak edit 1 dengan entri abusive leksikon."""
    if not ABUSIVE_WORDS_SET or len(word) < 4:
        return None
    # Jika kata merupakan kata formal yang valid/umum, atau ada di slang map, jangan diganti!
    if word in FORMAL_WORDS_SET or word in SLANG_MAP:
        return None
    if ABUSIVE_TRIE is not None:
        return ABUSIVE_TRIE.search_edit_distance_one(word)
    for ab_w in ABUSIVE_WORDS_SET:
        if abs(len(word) - len(ab_w)) > 1:
            continue
        if edit_distance_one(word, ab_w):
            return ab_w
    return None


def init_slang_map(alay_path: str, singkatan_path: str) -> dict[str, str]:
    """Memuat peta slang dari CSV dan memperbarui dictionary global SLANG_MAP."""
    global SLANG_MAP, ABUSIVE_WORDS_SET, FORMAL_WORDS_SET
    alay_map = {}
    singkatan_map = {}

    try:
        if alay_path and os.path.exists(alay_path):
            alay_df = pd.read_csv(alay_path, header=None, names=["slang", "formal"], encoding="latin-1")
            alay_map = dict(zip(alay_df["slang"], alay_df["formal"], strict=False))
    except Exception as e:
        logger.warning(f"Gagal memuat new_kamusalay.csv di normalizer: {e}")

    try:
        if singkatan_path and os.path.exists(singkatan_path):
            singkatan_df = pd.read_csv(singkatan_path)
            singkatan_df = singkatan_df.dropna(subset=["singkatan", "asli"])
            singkatan_map = dict(zip(singkatan_df["singkatan"], singkatan_df["asli"], strict=False))
    except Exception as e:
        logger.warning(f"Gagal memuat kamus_singkatan.csv di normalizer: {e}")

    # Muat juga kata abusive untuk fuzzy spell correction
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        abusive_path = os.path.join(base_dir, "..", "dataset", "ds_1", "abusive.csv")
        if os.path.exists(abusive_path):
            df_abusive = pd.read_csv(abusive_path)
            ABUSIVE_WORDS_SET = set(df_abusive["ABUSIVE"].dropna().str.strip().str.lower().unique())
            global ABUSIVE_TRIE
            ABUSIVE_TRIE = AbusiveTrie()
            for ab_w in ABUSIVE_WORDS_SET:
                ABUSIVE_TRIE.insert(ab_w)
            logger.info(f"Berhasil memuat {len(ABUSIVE_WORDS_SET)} kata abusive untuk spell correction.")
            try:
                from monitoring import TRIE_WORDS_COUNT

                TRIE_WORDS_COUNT.set(len(ABUSIVE_WORDS_SET))
            except Exception as prometheus_err:
                logger.warning(f"Gagal menyimpan metrik Trie words: {prometheus_err}")
    except Exception as e:
        logger.warning(f"Gagal memuat abusive.csv di normalizer: {e}")

    SLANG_MAP = {**singkatan_map, **alay_map}

    # Populasi set kata formal bahasa Indonesia
    FORMAL_WORDS_SET = (
        set(alay_map.values()) | set(singkatan_map.values()) | set(alay_map.keys()) | set(singkatan_map.keys())
    )
    FORMAL_WORDS_SET.update(INDONESIAN_COMMON_WORDS)

    return SLANG_MAP


def replace_leet(text: str) -> str:
    """Mengganti karakter angka/simbol yang menyerupai huruf (leetspeak)."""
    return "".join(LEET_MAP.get(ch, ch) for ch in text)


def reduce_repeated_chars(text: str, max_repeat: int = 2) -> str:
    """Mereduksi karakter berulang yang berlebihan (misal: begoooo -> bego)."""
    if max_repeat < 1:
        return text
    if max_repeat == 1:
        return REPEATED_CHAR_ANY_RE.sub(lambda m: m.group(1), text)
    return REPEATED_CHAR_RE.sub(lambda m: m.group(1) * max_repeat, text)


def normalize_text(text: str, reduce_repeats: bool = True) -> dict[str, str]:
    """Melakukan normalisasi teks lengkap (leetspeak, slang, singkatan, huruf berulang)."""
    raw = html.unescape(text)
    raw = unicodedata.normalize("NFKC", raw)
    raw = ZERO_WIDTH_RE.sub("", raw)
    raw = raw.lower()
    leet_replaced = replace_leet(raw)
    spaced = NON_ALNUM_RE.sub(" ", leet_replaced)
    spaced = MULTISPACE_RE.sub(" ", spaced).strip()

    # Slang mapping & spell correction untuk kata kasar
    if SLANG_MAP:
        words = spaced.split()
        normalized_words = []
        for w in words:
            formal = SLANG_MAP.get(w)
            if formal:
                normalized_words.append(formal)
            else:
                # Cek kedekatan typo ke kata kasar formal
                abusive_match = get_close_match_abusive(w)
                if abusive_match:
                    normalized_words.append(abusive_match)
                else:
                    normalized_words.append(w)
        spaced = " ".join(normalized_words)

    compact_raw = NON_ALNUM_RE.sub("", leet_replaced)
    if reduce_repeats:
        spaced = reduce_repeated_chars(spaced, max_repeat=2)
        compact = reduce_repeated_chars(compact_raw, max_repeat=2)
        compact_strict = reduce_repeated_chars(compact_raw, max_repeat=1)
    else:
        compact = compact_raw
        compact_strict = compact_raw

    return {
        "raw": text,
        "spaced": spaced,
        "compact": compact,
        "compact_strict": compact_strict,
    }


def prepare_lexicon(lexicon: list[dict[str, str]]) -> list[dict[str, str]]:
    """Menormalisasi frasa kamus leksikon agar sesuai dengan teks komentar."""
    prepared = []
    for item in lexicon:
        norm = normalize_text(item["phrase"], reduce_repeats=False)
        prepared.append(
            {
                **item,
                "norm_spaced": norm["spaced"],
                "norm_compact": norm["compact"],
                "word_count": len(norm["spaced"].split()),
            }
        )
    return prepared


def contains_word_or_phrase(spaced_text: str, spaced_pattern: str) -> bool:
    """Mengecek apakah kata/frasa tertentu ada di teks secara terpisah."""
    if not spaced_pattern:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(spaced_pattern) + r"(?![a-z0-9])"
    return re.search(pattern, spaced_text) is not None


def fuzzy_contains(compact_text: str, compact_pattern: str, threshold: float = 0.92, max_delta: int = 2) -> bool:
    """Mencocokkan kata berdasar kesamaan difflib (fuzzy matching) untuk kata tersamar secara efisien."""
    if not compact_text or not compact_pattern:
        return False

    # Batasi panjang teks untuk menghindari CPU exhaustion
    if len(compact_text) > 200:
        compact_text = compact_text[:200]

    n = len(compact_pattern)
    if n < 5 or len(compact_text) < max(3, n - max_delta):
        return False

    min_len = max(3, n - max_delta)
    max_len = n + max_delta

    import math
    from collections import Counter
    from difflib import SequenceMatcher

    p_counts = Counter(compact_pattern)

    for size in range(min_len, max_len + 1):
        if size > len(compact_text):
            continue

        min_overlap = math.ceil(threshold * (size + n) / 2)

        # O(1) sliding window count
        s_counts = Counter(compact_text[:size])
        overlap = sum(min(s_counts[c], p_counts.get(c, 0)) for c in s_counts)

        if overlap >= min_overlap:
            segment = compact_text[0:size]
            if SequenceMatcher(None, segment, compact_pattern).ratio() >= threshold:
                return True

        for i in range(1, len(compact_text) - size + 1):
            char_out = compact_text[i - 1]
            char_in = compact_text[i + size - 1]

            if s_counts[char_out] <= p_counts.get(char_out, 0):
                overlap -= 1
            s_counts[char_out] -= 1

            s_counts[char_in] = s_counts.get(char_in, 0) + 1
            if s_counts[char_in] <= p_counts.get(char_in, 0):
                overlap += 1

            if overlap >= min_overlap:
                segment = compact_text[i : i + size]
                if SequenceMatcher(None, segment, compact_pattern).ratio() >= threshold:
                    return True

    return False


def detect_sentiment_contrast(spaced_text: str) -> bool:
    """Mendeteksi kontras sentimen sederhana (pujian + indikator kegagalan/ejekan) untuk menyaring sarkasme awal."""
    text_lower = spaced_text.lower()

    pos_words = [
        "pintar",
        "pinter",
        "hebat",
        "ganteng",
        "cantik",
        "indah",
        "cakep",
        "rajin",
        "cepat",
        "cepet",
        "suci",
        "sopan",
        "baik",
        "mulia",
    ]
    neg_words = [
        "nol",
        "0",
        "salah",
        "gagal",
        "spakbor",
        "badut",
        "monyet",
        "panci",
        "gosong",
        "sirkus",
        "siang",
        "sore",
        "deadline",
        "menit",
        "tahun",
        "minus",
        "kasar",
        "bayaran",
        "belakang",
    ]

    has_pos = any(w in text_lower for w in pos_words)
    has_neg = any(w in text_lower for w in neg_words)

    return has_pos and has_neg


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
    # Body Shaming
    {"phrase": "gendut", "category": "body shaming", "severity": "sedang"},
    {"phrase": "gendutan", "category": "body shaming", "severity": "sedang"},
    {"phrase": "jadi bola", "category": "body shaming", "severity": "sedang"},
    {"phrase": "kayak tong", "category": "body shaming", "severity": "sedang"},
    {"phrase": "kayak babi", "category": "body shaming", "severity": "tinggi"},
    {"phrase": "ceking", "category": "body shaming", "severity": "sedang"},
    {"phrase": "kerempeng", "category": "body shaming", "severity": "sedang"},
    {"phrase": "pesek", "category": "body shaming", "severity": "rendah"},
    {"phrase": "buluk", "category": "body shaming", "severity": "rendah"},
    {"phrase": "dekil", "category": "body shaming", "severity": "rendah"},
    {"phrase": "item", "category": "body shaming", "severity": "rendah"},
    {"phrase": "jelek", "category": "body shaming", "severity": "sedang"},
    {"phrase": "pendek", "category": "body shaming", "severity": "rendah"},
    {"phrase": "bantet", "category": "body shaming", "severity": "sedang"},
    {"phrase": "burik", "category": "body shaming", "severity": "sedang"},
]
