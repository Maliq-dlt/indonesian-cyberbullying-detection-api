import streamlit as st
import pandas as pd
import numpy as np
import re
import html
import unicodedata
import matplotlib.pyplot as plt
import seaborn as sns
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Set page config
st.set_page_config(
    page_title="Cyberbullying & Hate Speech Detection Indonesia",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }
    
    /* Main container background */
    .stApp {
        background-color: #0d0f19;
        color: #e2e8f0;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        margin-bottom: 0.2rem;
        font-weight: 800;
        text-align: center;
    }
    
    .subheader-text {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Card design */
    .premium-card {
        background: rgba(19, 24, 44, 0.75);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 40px 0 rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
        margin-bottom: 24px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .premium-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    /* Preprocessing table styling */
    .norm-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
    }
    
    .norm-table th, .norm-table td {
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 12px;
        text-align: left;
    }
    
    .norm-table th {
        background-color: rgba(99, 102, 241, 0.15);
        color: #e2e8f0;
        font-weight: 600;
    }
    
    .norm-table td {
        background-color: rgba(255, 255, 255, 0.02);
    }
    
    /* Metric styling */
    .risk-badge {
        padding: 8px 20px;
        border-radius: 99px;
        font-weight: 700;
        text-align: center;
        display: inline-block;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
    }
    
    .risk-aman {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    
    .risk-rendah {
        background-color: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.4);
    }
    
    .risk-sedang {
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    
    .risk-tinggi {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Cache Resources (dictionaries and preprocessing utilities)
@st.cache_resource
def load_lexicon_and_maps():
    LEET_MAP = {
        "0": "o", "1": "i", "!": "i", "|": "i", "¡": "i", "3": "e", "4": "a",
        "@": "a", "5": "s", "$": "s", "7": "t", "+": "t", "8": "b", "9": "g", "6": "g"
    }
    
    ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")
    NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
    MULTISPACE_RE = re.compile(r"\s+")
    REPEATED_CHAR_RE = re.compile(r"(.)\1{2,}")
    REPEATED_CHAR_ANY_RE = re.compile(r"(.)\1+")
    
    # Load Slang / Abbreviation Dictionaries
    try:
        alay_df = pd.read_csv('dataset 1/new_kamusalay.csv', encoding='latin-1', header=None, names=['slang', 'formal'])
        alay_map = dict(zip(alay_df['slang'], alay_df['formal']))
    except Exception as e:
        alay_map = {}

    try:
        singkatan_df = pd.read_csv('dataset 2/kamus_singkatan.csv', encoding='latin-1')
        singkatan_df = singkatan_df.dropna(subset=['singkatan', 'asli'])
        singkatan_map = dict(zip(singkatan_df['singkatan'], singkatan_df['asli']))
    except Exception as e:
        singkatan_map = {}

    SLANG_MAP = {**singkatan_map, **alay_map}
    
    # Main Lexicon
    CYBERBULLYING_LEXICON = [
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
        {"phrase": "kampret", "category": "kata kasar", "severity": "rendah"}
    ]
    
    # Abusive lexicon expansion
    try:
        df_abusive_list = pd.read_csv('dataset 1/abusive.csv')
        abusive_words = df_abusive_list['ABUSIVE'].dropna().unique().tolist()
    except Exception as e:
        abusive_words = []
        
    new_terms = []
    existing_phrases = {item["phrase"].lower() for item in CYBERBULLYING_LEXICON}
    for word in abusive_words:
        word_lower = word.strip().lower()
        if word_lower not in existing_phrases:
            new_terms.append({
                "phrase": word_lower,
                "category": "kata kasar (abusive.csv)",
                "severity": "sedang"
            })
            existing_phrases.add(word_lower)
            
    EXPANDED_CYBERBULLYING_LEXICON = CYBERBULLYING_LEXICON + new_terms
    
    def prepare_lexicon(lexicon):
        prepared = []
        for item in lexicon:
            phr = str(item["phrase"]).lower()
            spaced = NON_ALNUM_RE.sub(" ", phr)
            spaced = MULTISPACE_RE.sub(" ", spaced).strip()
            compact = NON_ALNUM_RE.sub("", phr)
            prepared.append({
                **item,
                "norm_spaced": spaced,
                "norm_compact": compact,
                "word_count": len(spaced.split())
            })
        return prepared
        
    PREPARED_LEXICON = prepare_lexicon(CYBERBULLYING_LEXICON)
    EXPANDED_PREPARED_LEXICON = prepare_lexicon(EXPANDED_CYBERBULLYING_LEXICON)
    
    return LEET_MAP, ZERO_WIDTH_RE, NON_ALNUM_RE, MULTISPACE_RE, REPEATED_CHAR_RE, REPEATED_CHAR_ANY_RE, SLANG_MAP, PREPARED_LEXICON, EXPANDED_PREPARED_LEXICON

LEET_MAP, ZERO_WIDTH_RE, NON_ALNUM_RE, MULTISPACE_RE, REPEATED_CHAR_RE, REPEATED_CHAR_ANY_RE, SLANG_MAP, PREPARED_LEXICON, EXPANDED_PREPARED_LEXICON = load_lexicon_and_maps()

# Preprocessing helpers
def replace_leet(text: str) -> str:
    return "".join(LEET_MAP.get(ch, ch) for ch in text)

def reduce_repeated_chars(text: str, max_repeat: int = 2) -> str:
    if max_repeat < 1:
        return text
    if max_repeat == 1:
        return REPEATED_CHAR_ANY_RE.sub(lambda m: m.group(1), text)
    return REPEATED_CHAR_RE.sub(lambda m: m.group(1) * max_repeat, text)

def normalize_text(text, reduce_repeats=True):
    if pd.isna(text):
        text = ""
    text = str(text)
    raw = html.unescape(text)
    raw = unicodedata.normalize("NFKC", raw)
    raw = ZERO_WIDTH_RE.sub("", raw)
    raw = raw.lower()
    
    leet_replaced = replace_leet(raw)
    spaced = NON_ALNUM_RE.sub(" ", leet_replaced)
    spaced = MULTISPACE_RE.sub(" ", spaced).strip()
    
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

# Lexicon matching helpers
SEVERITY_SCORE = {"rendah": 1, "sedang": 2, "tinggi": 3}

def contains_word_or_phrase(spaced_text: str, spaced_pattern: str) -> bool:
    if not spaced_pattern:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(spaced_pattern) + r"(?![a-z0-9])"
    return re.search(pattern, spaced_text) is not None

def fuzzy_contains(compact_text: str, compact_pattern: str, threshold: float = 0.92, max_delta: int = 2) -> bool:
    if not compact_text or not compact_pattern:
        return False
    n = len(compact_pattern)
    if n < 5 or len(compact_text) < max(3, n - max_delta):
        return False
        
    min_len = max(3, n - max_delta)
    max_len = n + max_delta
    
    for size in range(min_len, max_len + 1):
        if size > len(compact_text):
            continue
        for i in range(0, len(compact_text) - size + 1):
            segment = compact_text[i:i + size]
            ratio = SequenceMatcher(None, segment, compact_pattern).ratio()
            if ratio >= threshold:
                return True
    return False

def detect_cyberbullying_text(text, lexicon=EXPANDED_PREPARED_LEXICON, use_fuzzy=True, fuzzy_threshold=0.92):
    norm = normalize_text(text)
    spaced_text = norm["spaced"]
    compact_text = norm["compact"]
    compact_strict_text = norm["compact_strict"]
    
    matches = []
    seen_phrases = set()
    
    for item in lexicon:
        phrase = item["phrase"]
        norm_spaced = item["norm_spaced"]
        norm_compact = item["norm_compact"]
        
        method = None
        if contains_word_or_phrase(spaced_text, norm_spaced):
            method = "word_or_phrase_match"
        elif norm_compact and norm_compact in compact_text:
            method = "compact_match"
        elif norm_compact and norm_compact in compact_strict_text:
            method = "compact_repeated_char_match"
        elif use_fuzzy and len(norm_compact) >= 6:
            if fuzzy_contains(compact_text, norm_compact, threshold=fuzzy_threshold) or fuzzy_contains(compact_strict_text, norm_compact, threshold=fuzzy_threshold):
                method = "fuzzy_compact_match"
                
        if method and phrase not in seen_phrases:
            matches.append({
                "matched_phrase": phrase,
                "category": item["category"],
                "severity": item["severity"],
                "method": method,
                "normalized_key": norm_compact,
            })
            seen_phrases.add(phrase)
            
    score = sum(SEVERITY_SCORE.get(m["severity"], 1) for m in matches)
    has_high = any(m["severity"] == "tinggi" for m in matches)
    
    if not matches:
        risk_label = "aman/tidak terdeteksi"
    elif has_high or score >= 4:
        risk_label = "tinggi"
    elif score >= 2:
        risk_label = "sedang"
    else:
        risk_label = "rendah"
        
    return {
        "text": str(text),
        "normalized_spaced": spaced_text,
        "normalized_compact": compact_text,
        "normalized_compact_strict": compact_strict_text,
        "is_cyberbullying": bool(matches),
        "risk_label": risk_label,
        "score": score,
        "matches": matches,
        "matched_phrases": ", ".join(sorted({m["matched_phrase"] for m in matches})),
        "matched_categories": ", ".join(sorted({m["category"] for m in matches})),
        "detection_methods": ", ".join(sorted({m["method"] for m in matches})),
    }

# Machine Learning resource caching (Trained on the compiled dataset)
@st.cache_resource
def train_ml_models():
    try:
        df_combined = pd.read_csv('dataset 2/combined_dataset.csv')
        df_combined['y_true'] = df_combined['Label'].isin(['Bullying', 'negatif', 'negative'])
        df_combined = df_combined.dropna(subset=['y_true', 'String'])
        
        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        X_tfidf = vectorizer.fit_transform(df_combined['String'])
        y = df_combined['y_true']
        
        nb_model = MultinomialNB()
        nb_model.fit(X_tfidf, y)
        
        lr_model = LogisticRegression(max_iter=1000)
        lr_model.fit(X_tfidf, y)
        return vectorizer, nb_model, lr_model
    except Exception as e:
        return None, None, None

vectorizer, nb_model, lr_model = train_ml_models()

# Deep Learning resource caching (Hugging Face XLM-RoBERTa Model)
@st.cache_resource
def load_transformer_pipeline():
    try:
        model_name = "nahiar/hatespeech-abusive-xlm-roberta-v1"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        nlp_transformer = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
        return nlp_transformer
    except Exception as e:
        return None

nlp_transformer = load_transformer_pipeline()

# Layout
st.markdown("<h1 class='main-header'>🛡️ INDONESIAN CYBERBULLYING DETECTOR</h1>", unsafe_allow_html=True)
st.markdown("<p class='subheader-text'>Sistem Hibrida Leksikon, Machine Learning, dan Deep Learning untuk Deteksi Cyberbullying & Hate Speech Indonesia</p>", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### ⚙️ Pengaturan Pendekatan")
use_expanded = st.sidebar.checkbox("Gunakan Leksikon Diperluas (139 kata)", value=True, help="Jika dinonaktifkan, kamus baseline hanya menggunakan 24 kata utama.")
use_fuzzy = st.sidebar.checkbox("Fuzzy Matching Fallback", value=True, help="Menangkap variasi salah ketik yang tidak terpetakan oleh leetspeak.")
fuzzy_threshold = st.sidebar.slider("Fuzzy Threshold", min_value=0.80, max_value=0.98, value=0.92, step=0.02)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Dataset Benchmark")
try:
    df_c = pd.read_csv('dataset 2/combined_dataset.csv')
    st.sidebar.metric("Dataset Kompilasi", f"{len(df_c)} Komentar")
    df_k = pd.read_excel('cyberbullying-indonesia/DATASET CYBERBULLYING INSTAGRAM - FINAL.xlsx')
    st.sidebar.metric("Dataset Instagram", f"{len(df_k)} Komentar")
    df_t = pd.read_csv('dataset 1/data.csv')
    st.sidebar.metric("Dataset Twitter", f"{len(df_t)} Tweets")
except:
    pass

# Main Tabs
tab_single, tab_batch = st.tabs(["🔍 Analisis Komentar Tunggal", "📁 Batch Scanner (CSV / Excel)"])

with tab_single:
    st.markdown("### Ketik atau Tempel Komentar")
    input_text = st.text_area("Masukkan teks di bawah ini:", placeholder="Tulis komentar media sosial di sini...", height=100)
    
    if st.button("Analisis Teks", type="primary") or input_text:
        if not input_text.strip():
            st.warning("Silakan masukkan teks terlebih dahulu.")
        else:
            # 1. PREPROCESSING
            norm_res = normalize_text(input_text)
            
            # 2. LEXICON APPROACH
            lex = EXPANDED_PREPARED_LEXICON if use_expanded else PREPARED_LEXICON
            lex_res = detect_cyberbullying_text(input_text, lexicon=lex, use_fuzzy=use_fuzzy, fuzzy_threshold=fuzzy_threshold)
            
            # Preprocessing Details
            st.markdown("#### 1. Tahapan Normalisasi Teks")
            st.markdown(f"""
            <table class='norm-table'>
                <tr><th>Bentuk Teks</th><th>Isi Teks</th><th>Keterangan</th></tr>
                <tr><td><b>Original Raw</b></td><td><code>{norm_res['raw']}</code></td><td>Teks asli yang diketik</td></tr>
                <tr><td><b>Spaced Spaced</b></td><td><code>{norm_res['spaced']}</code></td><td>Karakter non-alfanumerik dihapus & kamus alay diterjemahkan</td></tr>
                <tr><td><b>Compact</b></td><td><code>{norm_res['compact']}</code></td><td>Spasi dihilangkan untuk menangkap kamuflase / kata rapat</td></tr>
                <tr><td><b>Compact Strict</b></td><td><code>{norm_res['compact_strict']}</code></td><td>Karakter berulang dipangkas habis menjadi 1 huruf (e.g. gbbllk -> gblk)</td></tr>
            </table>
            """, unsafe_allow_html=True)
            
            # Predict Column Layout
            col_lex, col_ml, col_dl = st.columns(3)
            
            with col_lex:
                st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                st.markdown("### 🏷️ Rule-Based Lexicon")
                
                risk = lex_res["risk_label"]
                badge_class = f"risk-{risk.split('/')[0].strip()}"
                st.markdown(f"Status Risiko: <span class='risk-badge {badge_class}'>{risk.upper()}</span>", unsafe_allow_html=True)
                
                st.markdown(f"**Skor Keparahan:** {lex_res['score']}")
                
                if lex_res["matches"]:
                    st.markdown("**Kata Kasar Terdeteksi:**")
                    for m in lex_res["matches"]:
                        st.markdown(f"- **{m['matched_phrase']}** (`{m['category']}`, severity: `{m['severity']}`, metode: `{m['method']}`)")
                else:
                    st.markdown("Tidak ada kata kasar yang terdeteksi di kamus.")
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_ml:
                st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                st.markdown("### 🤖 Machine Learning")
                if vectorizer and nb_model and lr_model:
                    text_vec = vectorizer.transform([input_text])
                    prob_nb = nb_model.predict_proba(text_vec)[0][1]
                    prob_lr = lr_model.predict_proba(text_vec)[0][1]
                    
                    st.markdown("**Logistic Regression probability:**")
                    st.progress(float(prob_lr))
                    st.markdown(f"Tingkat Cyberbullying: **{prob_lr*100:.2f}%**")
                    
                    st.markdown("**Multinomial Naive Bayes probability:**")
                    st.progress(float(prob_nb))
                    st.markdown(f"Tingkat Cyberbullying: **{prob_nb*100:.2f}%**")
                else:
                    st.error("Model Machine Learning gagal dimuat.")
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_dl:
                st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
                st.markdown("### ⚡ Deep Learning (Transformer)")
                if nlp_transformer:
                    res = nlp_transformer([input_text])[0]
                    label_mapped = "TOXIC/CYBERBULLYING" if res['label'] == 'LABEL_1' else "AMAN/NON-TOXIC"
                    score = res['score']
                    
                    dl_badge = "risk-tinggi" if res['label'] == 'LABEL_1' else "risk-aman"
                    st.markdown(f"Klasifikasi XLM-R: <span class='risk-badge {dl_badge}'>{label_mapped}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Confidence Score:** {score*100:.2f}%")
                else:
                    st.warning("Model Transformer XLM-RoBERTa tidak tersedia atau gagal dimuat.")
                st.markdown("</div>", unsafe_allow_html=True)

with tab_batch:
    st.markdown("### Upload File untuk Batch Scanning")
    uploaded_file = st.file_uploader("Upload file CSV atau Excel:", type=["csv", "xlsx", "xls"])
    
    if uploaded_file:
        # Load File
        file_name = uploaded_file.name.lower()
        try:
            if file_name.endswith(".csv"):
                df_batch = pd.read_csv(uploaded_file)
            else:
                df_batch = pd.read_excel(uploaded_file)
                
            st.success(f"Berhasil mengunggah file! Ditemukan {len(df_batch)} baris.")
            
            # Select column
            columns = df_batch.columns.tolist()
            text_column = st.selectbox("Pilih kolom teks untuk dianalisis:", columns)
            
            if st.button("Mulai Batch Scan", type="primary"):
                with st.spinner("Memindai dokumen..."):
                    # Process
                    results = []
                    lex = EXPANDED_PREPARED_LEXICON if use_expanded else PREPARED_LEXICON
                    
                    for index, row in df_batch.iterrows():
                        txt = row[text_column]
                        res = detect_cyberbullying_text(txt, lexicon=lex, use_fuzzy=use_fuzzy, fuzzy_threshold=fuzzy_threshold)
                        
                        # Get ML predictions
                        if vectorizer and lr_model:
                            txt_vec = vectorizer.transform([str(txt)])
                            prob_lr = lr_model.predict_proba(txt_vec)[0][1]
                        else:
                            prob_lr = 0.0
                            
                        results.append({
                            "Teks Asli": str(txt),
                            "Normalized Spaced": res["normalized_spaced"],
                            "Terdeteksi Leksikon": "YA" if res["is_cyberbullying"] else "TIDAK",
                            "Tingkat Risiko Leksikon": res["risk_label"],
                            "Skor Keparahan": res["score"],
                            "Kata Kasar Cocok": res["matched_phrases"],
                            "Tingkat Toksisitas ML (%)": round(prob_lr * 100, 2)
                        })
                        
                    res_df = pd.DataFrame(results)
                    final_df = pd.concat([df_batch.reset_index(drop=True), res_df], axis=1)
                    
                    # Display metrics
                    st.markdown("### Hasil Batch Scan")
                    col_met1, col_met2, col_met3 = st.columns(3)
                    
                    total_rows = len(final_df)
                    bullying_count = (final_df["Terdeteksi Leksikon"] == "YA").sum()
                    bullying_rate = (bullying_count / total_rows) * 100
                    
                    col_met1.metric("Total Komentar", f"{total_rows}")
                    col_met2.metric("Terdeteksi Bullying", f"{bullying_count} baris")
                    col_met3.metric("Rasio Bullying (%)", f"{bullying_rate:.2f}%")
                    
                    # Graph
                    st.markdown("#### Grafik Pembagian Risiko")
                    fig, ax = plt.subplots(figsize=(8, 4))
                    sns.countplot(data=final_df, x="Tingkat Risiko Leksikon", hue="Tingkat Risiko Leksikon", 
                                  palette="coolwarm", legend=False, ax=ax)
                    ax.set_title("Distribusi Tingkat Risiko Cyberbullying")
                    ax.set_ylabel("Jumlah Komentar")
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Display Table
                    st.dataframe(final_df.head(100))
                    
                    # Download Link
                    csv_bytes = final_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Unduh Hasil Deteksi (.csv)",
                        data=csv_bytes,
                        file_name="hasil_deteksi_cyberbullying.csv",
                        mime="text/csv"
                    )
        except Exception as e:
            st.error(f"Gagal memproses file: {e}")
