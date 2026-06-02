import os
import glob
import re
import html
import unicodedata
import random
import json
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import classification_report, f1_score

print("=== Memulai Skrip Pelatihan Ulang Otomatis (Active Learning + Perturbasi + Kalibrasi) ===")

# Tentukan direktori dasar dinamis untuk pathing absolut
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Konfigurasi Path dan Kamus Slang
ALAY_PATH = os.path.join(BASE_DIR, "..", "dataset 1", "new_kamusalay.csv")
SINGKATAN_PATH = os.path.join(BASE_DIR, "..", "dataset 2", "kamus_singkatan.csv")
ABUSIVE_PATH = os.path.join(BASE_DIR, "..", "dataset 1", "abusive.csv")

DATASET_TWITTER_PATH = os.path.join(BASE_DIR, "..", "dataset 1", "data.csv")
DATASET_INSTAGRAM_PATH = os.path.join(BASE_DIR, "..", "cyberbullying-indonesia", "DATASET CYBERBULLYING INSTAGRAM - FINAL.xlsx")
DATASET_COMBINED_PATH = os.path.join(BASE_DIR, "..", "dataset 2", "combined_dataset.csv")

LEET_MAP = {
    "0": "o", "1": "i", "!": "i", "|": "i", "¡": "i", "3": "e", "4": "a",
    "@": "a", "5": "s", "$": "s", "7": "t", "+": "t", "8": "b", "9": "g", "6": "g"
}
ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
MULTISPACE_RE = re.compile(r"\s+")
REPEATED_CHAR_RE = re.compile(r"(.)\1{2,}")

PERTURB_LEET = {'a': '4', 'i': '1', 'e': '3', 'o': '0', 's': '5', 'g': '9'}

def replace_leet(text: str) -> str:
    return "".join(LEET_MAP.get(ch, ch) for ch in text)

def reduce_repeated_chars(text: str, max_repeat: int = 2) -> str:
    return REPEATED_CHAR_RE.sub(lambda m: m.group(1) * max_repeat, text)

# Muat Slang Map
alay_df = pd.read_csv(ALAY_PATH, encoding='latin-1', header=None, names=['slang', 'formal'])
alay_map = dict(zip(alay_df['slang'], alay_df['formal']))

singkatan_df = pd.read_csv(SINGKATAN_PATH, encoding='latin-1')
singkatan_df = singkatan_df.dropna(subset=['singkatan', 'asli'])
singkatan_map = dict(zip(singkatan_df['singkatan'], singkatan_df['asli']))

SLANG_MAP = {**singkatan_map, **alay_map}
print(f"Memuat {len(SLANG_MAP)} pemetaan slang/singkatan.")

def clean_and_normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    raw = html.unescape(text)
    raw = unicodedata.normalize("NFKC", raw)
    raw = ZERO_WIDTH_RE.sub("", raw)
    raw = raw.lower()
    leet_replaced = replace_leet(raw)
    spaced = NON_ALNUM_RE.sub(" ", leet_replaced)
    spaced = MULTISPACE_RE.sub(" ", spaced).strip()
    
    words = spaced.split()
    spaced = " ".join([SLANG_MAP.get(w, w) for w in words]) if SLANG_MAP else " ".join(words)
    spaced = reduce_repeated_chars(spaced, max_repeat=2)
    return spaced

# Muat Leksikon Abusive
df_abusive = pd.read_csv(ABUSIVE_PATH)
abusive_words = set(df_abusive['ABUSIVE'].dropna().str.strip().str.lower().unique().tolist())

def check_toxic_by_lexicon(norm_text: str) -> bool:
    words = set(norm_text.split())
    return any(w in abusive_words for w in words)

def perturb_text(text: str) -> str:
    """Melakukan perturbasi teks acak (leetspeak, sensor, typo) pada kata kasar untuk augmentasi."""
    if not text or not isinstance(text, str):
        return ""
    words = text.split()
    new_words = []
    for w in words:
        if w in abusive_words and random.random() < 0.6:
            p_type = random.choice(["leet", "censor", "repeat", "typo"])
            if p_type == "leet":
                w = "".join(PERTURB_LEET.get(c, c) for c in w)
            elif p_type == "censor":
                if len(w) > 2:
                    w = w[0] + "*" * (len(w) - 2) + w[-1]
            elif p_type == "repeat":
                w = w + w[-1] * random.randint(1, 3)
            elif p_type == "typo":
                if len(w) > 3:
                    idx = random.randint(1, len(w) - 2)
                    w_list = list(w)
                    w_list[idx], w_list[idx+1] = w_list[idx+1], w_list[idx]
                    w = "".join(w_list)
        new_words.append(w)
    return " ".join(new_words)

# 2. Ingest Data Baru dari Hasil Scraping (menggunakan path absolut dinamis)
print("Mencari berkas hasil klasifikasi scraper (classified_*_data.csv)...")
new_files = glob.glob(os.path.join(BASE_DIR, "classified_*_data.csv"))
new_records = []

if new_files:
    for file_path in new_files:
        print(f"Membaca data baru dari: {file_path}")
        try:
            df_new = pd.read_csv(file_path)
            if "Teks" in df_new.columns and "Is_Bully" in df_new.columns:
                df_valid = df_new[df_new["Is_Bully"] != "Error"].copy()
                for idx, row in df_valid.iterrows():
                    raw_text = str(row["Teks"]).strip()
                    is_bully = row["Is_Bully"] == "Ya"
                    label_str = "Bullying" if is_bully else "Non-bullying"
                    if raw_text:
                        new_records.append({
                            "String": raw_text,
                            "Label": label_str
                        })
            else:
                print(f"Warning: Kolom tidak cocok di {file_path}. Memerlukan 'Teks' dan 'Is_Bully'.")
        except Exception as e:
            print(f"Error membaca {file_path}: {e}")
else:
    print("Tidak ditemukan berkas data baru (*.csv hasil scraper).")

# 3. Gabungkan dan Perbarui Dataset Utama (Deduplikasi)
if new_records:
    print(f"Memproses {len(new_records)} baris data baru untuk digabung...")
    try:
        if os.path.exists(DATASET_COMBINED_PATH):
            df_combined = pd.read_csv(DATASET_COMBINED_PATH)
        else:
            df_combined = pd.DataFrame(columns=["Label", "clean_text", "String", "encoded_label"])
        
        existing_strings = set(df_combined["String"].dropna().str.strip().str.lower().unique())
        
        added_count = 0
        appended_list = []
        for rec in new_records:
            normalized_check = rec["String"].strip().lower()
            if normalized_check not in existing_strings:
                clean_t = clean_and_normalize(rec["String"])
                encoded_l = 0.0 if rec["Label"] == "Bullying" else 1.0
                
                new_row = {
                    "Label": rec["Label"],
                    "clean_text": clean_t,
                    "String": rec["String"],
                    "encoded_label": encoded_l
                }
                appended_list.append(new_row)
                existing_strings.add(normalized_check)
                added_count += 1
        
        if appended_list:
            df_to_append = pd.DataFrame(appended_list)
            df_combined = pd.concat([df_combined, df_to_append], ignore_index=True)
            df_combined.to_csv(DATASET_COMBINED_PATH, index=False)
            print(f"Sukses mengintegrasikan {added_count} sampel baru secara unik ke {DATASET_COMBINED_PATH}!")
        else:
            print("Seluruh sampel baru sudah ada dalam dataset (duplikat diabaikan).")
            
        # Pindahkan atau rename file scraper agar tidak diproses berulang kali
        for file_path in new_files:
            try:
                base_name = os.path.basename(file_path)
                backup_path = os.path.join(BASE_DIR, f"processed_{base_name}")
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(file_path, backup_path)
                print(f"Berkas lama diubah namanya menjadi: {backup_path}")
            except Exception as e:
                print(f"Warning: Gagal mengubah nama berkas {file_path}: {e}")
    except Exception as e:
        print(f"Error saat mengintegrasikan data baru: {e}")
else:
    print("Dataset kombinasi tetap menggunakan data baseline.")

# 4. Load & Gabungkan Semua Dataset untuk Retraining
print("Memuat seluruh dataset untuk pelatihan ulang...")
try:
    df_twitter = pd.read_csv(DATASET_TWITTER_PATH, encoding='latin-1')
    df_twitter = df_twitter.dropna(subset=['Tweet'])
    df_twitter['text_clean'] = df_twitter['Tweet'].apply(clean_and_normalize)
    df_twitter['is_toxic'] = df_twitter['Abusive'] == 1
    df_twitter['is_bully'] = df_twitter['HS'] == 1

    df_kaira = pd.read_excel(DATASET_INSTAGRAM_PATH)
    df_kaira = df_kaira.dropna(subset=['Komentar', 'Kategori'])
    df_kaira['text_clean'] = df_kaira['Komentar'].apply(clean_and_normalize)
    df_kaira['is_bully'] = df_kaira['Kategori'].map({'Bullying': True, 'Non-bullying': False})
    df_kaira['is_toxic'] = df_kaira['text_clean'].apply(check_toxic_by_lexicon)

    df_combined = pd.read_csv(DATASET_COMBINED_PATH)
    df_combined = df_combined.dropna(subset=['String', 'Label'])
    df_combined['text_clean'] = df_combined['String'].apply(clean_and_normalize)
    df_combined['is_bully'] = df_combined['Label'].isin(['Bullying', 'negatif', 'negative'])
    df_combined['is_toxic'] = df_combined['text_clean'].apply(check_toxic_by_lexicon)
except Exception as e:
    print(f"Critical Error: Gagal memuat dataset utama untuk retraining: {e}")
    exit(1)

# 5. Data Augmentasi (Sarkasme & Slang Pujian) untuk penyeimbangan pola spesifik
sarcasm_raw = [
    "Wah pintar sekali kamu ya, sampai nilai ujianmu nol.",
    "ganteng banget mukalu kaya spakbor mio",
    "rajin banget sih jam 12 siang baru bangun tidur",
    "bagus banget kerjaan lu, bikin rugi perusahaan aja",
    "wah hebat sekali, rancangan kamu sukses merusak sistem",
    "cantik banget sih mbak, dandanannya kayak badut ancol",
    "suaranya bagus sekali ya, sampai bikin telinga pecah",
    "bersih sekali kamarmu, sampai tikus pun betah di situ",
    "baik sekali kamu ya, suka membicarakan orang di belakang",
    "ganteng banget, mirip monyet kebanjiran",
    "pintar banget sih kamu, soal gampang begini aja salah semua",
    "wah wangi sekali badanmu, sampai semua orang pingsan",
    "cepat sekali kerjamu, proyek sebulan selesai setahun",
    "suci sekali kamu, padahal kelakuan minus semua",
    "sopan sekali bicaramu, seperti tidak pernah disekolahkan",
    "hebat sekali kau, selalu berhasil mengecewakan orang tua",
    "rajin sekali dia, tugas satu semester dikerjakan semenit sebelum deadline",
    "baik benar dirimu, menolong orang tapi minta bayaran ganda",
    "pemandangan indah sekali, penuh sampah berserakan di mana-mana",
    "ganteng banget mukamu, kayak panci gosong"
]

slang_praise_raw = [
    "kamu hebat banget sih anjing",
    "gila keren banget lu bajingan",
    "goblok lu lucu banget sumpah",
    "anjing ganteng banget cowok itu",
    "hebat banget sih monyet, jago mainnya",
    "gila mainnya jago banget bangsat",
    "kamu pintar banget sih bajingan",
    "gila ini makanan enak banget asu",
    "cantik banget kamu bangsat",
    "keren gila lu bro, mantap anjing",
    "gila lu bro, aseli keren banget anjing",
    "muka lu ganteng gila babi",
    "goblok lu kok bisa kepikiran ide sekeren ini",
    "anjing aseli ini film seru banget",
    "jago bangsat main gitarnya",
    "gokil parah lu bro, respect anjing",
    "gila desain lu keren banget asu",
    "anjing suaranya merdu banget",
    "gila jagoan banget lu bangsat",
    "goblok lu pinter banget bikin presentasi"
]

augmented_records = []
for _ in range(12):
    for s in sarcasm_raw:
        augmented_records.append({
            'text_clean': clean_and_normalize(s),
            'is_toxic': False,
            'is_bully': True
        })
    for s in slang_praise_raw:
        augmented_records.append({
            'text_clean': clean_and_normalize(s),
            'is_toxic': True,
            'is_bully': False
        })

df_aug = pd.DataFrame(augmented_records)

# Gabung dan terapkan Perturbasi Slang/Typo acak pada record yang mengandung unsur toxic
print("Melakukan augmentasi perturbasi teks (typo/leet) secara dinamis...")
perturbed_records = []
for idx, row in pd.concat([df_twitter, df_kaira, df_combined], ignore_index=True).iterrows():
    if row['is_toxic'] and random.random() < 0.3:
        perturbed_text = perturb_text(row['text_clean'])
        if perturbed_text and perturbed_text != row['text_clean']:
            perturbed_records.append({
                'text_clean': perturbed_text,
                'is_toxic': True,
                'is_bully': row['is_bully']
            })

df_perturbed = pd.DataFrame(perturbed_records)
print(f"Ditambahkan {len(df_perturbed)} baris data hasil perturbasi teks.")

# Gabung semuanya
final_df = pd.concat([
    df_twitter[['text_clean', 'is_toxic', 'is_bully']],
    df_kaira[['text_clean', 'is_toxic', 'is_bully']],
    df_combined[['text_clean', 'is_toxic', 'is_bully']],
    df_aug,
    df_perturbed
], ignore_index=True)

final_df = final_df.dropna()
final_df = final_df[final_df['text_clean'] != ""]
print(f"Total baris data retraining gabungan: {len(final_df)} baris.")

# 6. Splitting & Vectorization
X = final_df['text_clean']
y = final_df[['is_toxic', 'is_bully']].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42
)

vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), min_df=2)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# 7. Melatih Ulang Model
print("Melatih ulang Multi-Label Classifier...")
base_lr = LogisticRegression(max_iter=1500, class_weight='balanced', C=1.5, random_state=42)
clf = MultiOutputClassifier(base_lr)
clf.fit(X_train_tfidf, y_train)

# 8. Kalibrasi Threshold Dinamis
print("Mengevaluasi dan mengkalibrasi threshold optimal...")
test_probs = clf.predict_proba(X_test_tfidf)
probs_toxic = test_probs[0][:, 1]
probs_bully = test_probs[1][:, 1]

def calibrate_threshold(probs, y_true):
    best_thresh = 0.5
    best_f1 = 0.0
    for thresh in np.arange(0.1, 0.9, 0.05):
        y_pred = (probs >= thresh).astype(int)
        score = f1_score(y_true, y_pred, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_thresh = float(thresh)
    return best_thresh

best_thresh_toxic = calibrate_threshold(probs_toxic, y_test['is_toxic'])
best_thresh_bully = calibrate_threshold(probs_bully, y_test['is_bully'])
print(f"Threshold Terkalibrasi -> Toxic: {best_thresh_toxic:.2f} | Bully: {best_thresh_bully:.2f}")

# Simpan threshold ke file JSON menggunakan path absolut dinamis
thresholds_path = os.path.join(BASE_DIR, "thresholds.json")
thresholds_data = {
    "threshold_toxic": best_thresh_toxic,
    "threshold_bully": best_thresh_bully
}
with open(thresholds_path, "w") as f:
    json.dump(thresholds_data, f)
print(f"Berkas thresholds.json berhasil disimpan di: {thresholds_path}")

# 9. Evaluasi Akhir dengan Threshold Terkalibrasi
preds_toxic = (probs_toxic >= best_thresh_toxic).astype(int)
preds_bully = (probs_bully >= best_thresh_bully).astype(int)

print("\n=== HASIL EVALUASI RETRAINING DENGAN AMBANG BATAS TERKALIBRASI ===")
print("1. Target: TOXICITY (is_toxic)")
print(classification_report(y_test['is_toxic'], preds_toxic))
print("2. Target: BULLYING (is_bully)")
print(classification_report(y_test['is_bully'], preds_bully))

# 10. Simpan Model & Vectorizer yang Baru menggunakan path absolut dinamis
print("Menyimpan model & vectorizer terbaru...")
joblib.dump(clf, os.path.join(BASE_DIR, "model_lr.joblib"))
joblib.dump(vectorizer, os.path.join(BASE_DIR, "vectorizer.joblib"))
print("Proses retraining sukses! Model 'model_lr.joblib' dan 'vectorizer.joblib' telah diperbarui.")
