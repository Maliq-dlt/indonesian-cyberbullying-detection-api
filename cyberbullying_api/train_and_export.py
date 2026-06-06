import pandas as pd
import numpy as np
import re
import html
import unicodedata
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import classification_report, accuracy_score
import os
import joblib
from normalizer import init_slang_map, normalize_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("--- Memulai Proses Pelatihan Model Multi-Label ---")

# ----------------------------------------------------
# 1. Definisi Normalisasi Teks (Sama dengan API main.py)
# ----------------------------------------------------

# Inisialisasi peta slang secara global di normalizer
alay_path = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "new_kamusalay.csv")
singkatan_path = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "kamus_singkatan.csv")
init_slang_map(alay_path, singkatan_path)

def clean_and_normalize(text: str) -> str:
    return normalize_text(text)["spaced"]

# Load Abusive Words List for Rule-Based Toxicity Labeling in other datasets
abusive_path = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "abusive.csv")
df_abusive = pd.read_csv(abusive_path)
abusive_words = set(df_abusive['ABUSIVE'].dropna().str.strip().str.lower().unique().tolist())

def check_toxic_by_lexicon(norm_text: str) -> bool:
    words = set(norm_text.split())
    return any(w in abusive_words for w in words)

# ----------------------------------------------------
# 2. Loading Datasets
# ----------------------------------------------------

# Dataset 1 (Twitter)
print("Memuat dataset Twitter...")
df_twitter = pd.read_csv(os.path.join(BASE_DIR, "..", "dataset", "ds_1", "data.csv"), encoding='latin-1')
df_twitter = df_twitter.dropna(subset=['Tweet'])
df_twitter['text_clean'] = df_twitter['Tweet'].apply(clean_and_normalize)
df_twitter['is_toxic'] = df_twitter['Abusive'] == 1
df_twitter['is_bully'] = df_twitter['HS'] == 1

# Dataset Instagram (kairaamilanii)
df_kaira = None
instagram_path = os.path.join(BASE_DIR, "..", "dataset", "ds_instagram", "DATASET CYBERBULLYING INSTAGRAM - FINAL.xlsx")
if os.path.exists(instagram_path):
    print("Memuat dataset Instagram...")
    try:
        df_kaira = pd.read_excel(instagram_path)
        df_kaira = df_kaira.dropna(subset=['Komentar', 'Kategori'])
        df_kaira['text_clean'] = df_kaira['Komentar'].apply(clean_and_normalize)
        df_kaira['is_bully'] = df_kaira['Kategori'].map({'Bullying': True, 'Non-bullying': False})
        df_kaira['is_toxic'] = df_kaira['text_clean'].apply(check_toxic_by_lexicon)
    except Exception as e:
        print(f"Warning: Gagal memuat dataset Instagram: {e}")
else:
    print(f"Informasi: Dataset Instagram tidak ditemukan di {instagram_path}, dilewati.")

# Dataset Kompilasi (dataset 2)
print("Memuat dataset kompilasi...")
df_combined = pd.read_csv(os.path.join(BASE_DIR, "..", "dataset", "ds_2", "combined_dataset.csv"))
df_combined = df_combined.dropna(subset=['String', 'Label'])
df_combined['text_clean'] = df_combined['String'].apply(clean_and_normalize)
df_combined['is_bully'] = df_combined['Label'].isin(['Bullying', 'negatif', 'negative'])
if 'is_toxic' in df_combined.columns:
    df_combined['is_toxic'] = df_combined['is_toxic'].astype(bool)
else:
    df_combined['is_toxic'] = df_combined['text_clean'].apply(check_toxic_by_lexicon)

# ----------------------------------------------------
# 3. Augmentasi Data (Sarkasme & Slang Pujian)
# ----------------------------------------------------
print("Menyusun data augmentasi untuk sarkasme dan slang...")

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
    "jago banget bangsat main gitarnya",
    "gokil parah lu bro, respect anjing",
    "gila desain lu keren banget asu",
    "anjing suaranya merdu banget",
    "gila jagoan banget lu bangsat",
    "goblok lu pinter banget bikin presentasi"
]

augmented_records = []
# Melakukan duplikasi agar dataset seimbang pengaruhnya untuk pola ini
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
print(f"Data augmentasi siap: {len(df_aug)} baris.")

# 1. Gabungkan dataset dasar asli yang berhasil dimuat
dfs_to_concat = [df_twitter[['text_clean', 'is_toxic', 'is_bully']]]
if df_kaira is not None:
    dfs_to_concat.append(df_kaira[['text_clean', 'is_toxic', 'is_bully']])
dfs_to_concat.append(df_combined[['text_clean', 'is_toxic', 'is_bully']])

base_df = pd.concat(dfs_to_concat, ignore_index=True)

base_df = base_df.dropna()
base_df = base_df[base_df['text_clean'] != ""]
print(f"Total data dasar asli: {len(base_df)} baris.")

# 2. Stratified train_test_split berdasarkan kombinasi label joint
stratify_key = base_df['is_toxic'].astype(str) + "_" + base_df['is_bully'].astype(str)
min_class_count = stratify_key.value_counts().min()

if min_class_count >= 2:
    train_df, test_df = train_test_split(
        base_df, test_size=0.15, random_state=42, stratify=stratify_key
    )
    print("Menggunakan stratified train_test_split berbasis kombinasi label joint.")
else:
    train_df, test_df = train_test_split(
        base_df, test_size=0.15, random_state=42
    )
    print("Fallback ke standard train_test_split.")

# 3. Tambahkan data augmentasi HANYA ke train set
final_train_df = pd.concat([train_df, df_aug], ignore_index=True)
final_train_df = final_train_df.dropna()
final_train_df = final_train_df[final_train_df['text_clean'] != ""]

print(f"Train Set Asli: {len(train_df)} -> Setelah Augmentasi: {len(final_train_df)} | Test Set Bersih: {len(test_df)}")

X_train = final_train_df['text_clean']
y_train = final_train_df[['is_toxic', 'is_bully']].astype(int)

X_test = test_df['text_clean']
y_test = test_df[['is_toxic', 'is_bully']].astype(int)

# ----------------------------------------------------
# 4. Vectorization
# ----------------------------------------------------
# Vectorizer (Unigram + Bigram)
vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), min_df=2)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# ----------------------------------------------------
# 5. Training Multi-Label Classifier
# ----------------------------------------------------
print("Melatih Multi-Label Classifier (TF-IDF + Logistic Regression)...")
base_lr = LogisticRegression(max_iter=1500, class_weight='balanced', C=1.5, random_state=42)
clf = MultiOutputClassifier(base_lr)
clf.fit(X_train_tfidf, y_train)

# ----------------------------------------------------
# 6. Evaluation
# ----------------------------------------------------
preds = np.asarray(clf.predict(X_test_tfidf))

print("\n=== EVALUASI MODEL LATIH (TEST SET) ===")
print("1. Target: TOXICITY (is_toxic)")
print(classification_report(y_test['is_toxic'], preds[:, 0]))

print("2. Target: BULLYING (is_bully)")
print(classification_report(y_test['is_bully'], preds[:, 1]))

# Custom Test Verification
print("\n=== PENGUJIAN DENGAN SENTENCE UJI USER ===")
test_sentences = [
    "Kamu bodoh banget sih, dasar tolol!",
    "Semangat belajarnya ya, jangan menyerah!",
    "Wah pintar sekali kamu ya, sampai nilai ujianmu nol.",
    "kamu hebat banget sih anjing",
    "ganteng banget mukalu kaya spakbor mio"
]

for s in test_sentences:
    norm = clean_and_normalize(s)
    feats = vectorizer.transform([norm])
    pred_probs = clf.predict_proba(feats)
    pred_l = np.asarray(clf.predict(feats))[0]
    
    # Extract probabilities
    prob_toxic = pred_probs[0][0][1]
    prob_bully = pred_probs[1][0][1]
    
    print(f"\nTeks: '{s}'")
    print(f"  Normalized: '{norm}'")
    print(f"  Prediksi: Toxic={bool(pred_l[0])} (Prob: {prob_toxic:.4f}) | Bully={bool(pred_l[1])} (Prob: {prob_bully:.4f})")

# ----------------------------------------------------
# 7. Saving Models
# ----------------------------------------------------
print("\nMenyimpan model & vectorizer ke disk...")
joblib.dump(clf, os.path.join(BASE_DIR, "models", "model_lr.joblib"))
joblib.dump(vectorizer, os.path.join(BASE_DIR, "models", "vectorizer.joblib"))
print("Semua berkas model berhasil diperbarui dan disimpan!")
