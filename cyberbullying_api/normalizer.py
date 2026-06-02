import re
import html
import os
import unicodedata
import pandas as pd
from typing import List, Dict, Any

# Global Slang Map (diisi melalui fungsi init_slang_map)
SLANG_MAP = {}

LEET_MAP = {
    "0": "o", "1": "i", "!": "i", "|": "i", "¡": "i", "3": "e", "4": "a",
    "@": "a", "5": "s", "$": "s", "7": "t", "+": "t", "8": "b", "9": "g", "6": "g"
}

ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
MULTISPACE_RE = re.compile(r"\s+")
REPEATED_CHAR_RE = re.compile(r"(.)\1{2,}")
REPEATED_CHAR_ANY_RE = re.compile(r"(.)\1+")

def init_slang_map(alay_path: str, singkatan_path: str) -> Dict[str, str]:
    """Memuat peta slang dari CSV dan memperbarui dictionary global SLANG_MAP."""
    global SLANG_MAP
    alay_map = {}
    singkatan_map = {}
    
    try:
        if alay_path and os.path.exists(alay_path):
            alay_df = pd.read_csv(alay_path, encoding='latin-1', header=None, names=['slang', 'formal'])
            alay_map = dict(zip(alay_df['slang'], alay_df['formal']))
    except Exception as e:
        print("Warning: Gagal memuat new_kamusalay.csv di normalizer:", e)

    try:
        if singkatan_path and os.path.exists(singkatan_path):
            singkatan_df = pd.read_csv(singkatan_path, encoding='latin-1')
            singkatan_df = singkatan_df.dropna(subset=['singkatan', 'asli'])
            singkatan_map = dict(zip(singkatan_df['singkatan'], singkatan_df['asli']))
    except Exception as e:
        print("Warning: Gagal memuat kamus_singkatan.csv di normalizer:", e)

    SLANG_MAP = {**singkatan_map, **alay_map}
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

def normalize_text(text: str, reduce_repeats: bool = True) -> Dict[str, str]:
    """Melakukan normalisasi teks lengkap (leetspeak, slang, singkatan, huruf berulang)."""
    raw = html.unescape(text)
    raw = unicodedata.normalize("NFKC", raw)
    raw = ZERO_WIDTH_RE.sub("", raw)
    raw = raw.lower()
    leet_replaced = replace_leet(raw)
    spaced = NON_ALNUM_RE.sub(" ", leet_replaced)
    spaced = MULTISPACE_RE.sub(" ", spaced).strip()
    
    # Slang mapping
    if SLANG_MAP:
        words = spaced.split()
        spaced = " ".join(SLANG_MAP.get(w, w) for w in words)
        
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

def prepare_lexicon(lexicon: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Menormalisasi frasa kamus leksikon agar sesuai dengan teks komentar."""
    prepared = []
    for item in lexicon:
        norm = normalize_text(item["phrase"], reduce_repeats=False)
        prepared.append({
            **item,
            "norm_spaced": norm["spaced"],
            "norm_compact": norm["compact"],
            "word_count": len(norm["spaced"].split()),
        })
    return prepared

def contains_word_or_phrase(spaced_text: str, spaced_pattern: str) -> bool:
    """Mengecek apakah kata/frasa tertentu ada di teks secara terpisah."""
    if not spaced_pattern:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(spaced_pattern) + r"(?![a-z0-9])"
    return re.search(pattern, spaced_text) is not None

def fuzzy_contains(compact_text: str, compact_pattern: str, threshold: float = 0.92, max_delta: int = 2) -> bool:
    """Mencocokkan kata berdasar kesamaan difflib (fuzzy matching) untuk kata tersamar."""
    if not compact_text or not compact_pattern:
        return False
    n = len(compact_pattern)
    if n < 5 or len(compact_text) < max(3, n - max_delta):
        return False
    min_len = max(3, n - max_delta)
    max_len = n + max_delta
    from difflib import SequenceMatcher
    for size in range(min_len, max_len + 1):
        if size > len(compact_text):
            continue
        for i in range(0, len(compact_text) - size + 1):
            segment = compact_text[i:i + size]
            ratio = SequenceMatcher(None, segment, compact_pattern).ratio()
            if ratio >= threshold:
                return True
    return False
