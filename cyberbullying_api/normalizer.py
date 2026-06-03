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
    
    from collections import Counter
    from difflib import SequenceMatcher
    import math
    
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
                segment = compact_text[i:i + size]
                if SequenceMatcher(None, segment, compact_pattern).ratio() >= threshold:
                    return True
                    
    return False


def detect_sentiment_contrast(spaced_text: str) -> bool:
    """Mendeteksi kontras sentimen sederhana (pujian + indikator kegagalan/ejekan) untuk menyaring sarkasme awal."""
    text_lower = spaced_text.lower()
    
    pos_words = ["pintar", "pinter", "hebat", "ganteng", "cantik", "indah", "cakep", "rajin", "cepat", "cepet", "suci", "sopan", "baik", "mulia"]
    neg_words = ["nol", "0", "salah", "gagal", "spakbor", "badut", "monyet", "panci", "gosong", "sirkus", "siang", "sore", "deadline", "menit", "tahun", "minus", "kasar", "bayaran", "belakang"]
    
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
]

