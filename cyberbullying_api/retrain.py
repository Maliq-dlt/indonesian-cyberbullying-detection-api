import os
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
from normalizer import init_slang_map, normalize_text

from training import (
    augment_text_with_llm, perturb_text,
    sarcasm_raw, slang_praise_raw, OLLAMA_URL,
    load_twitter_dataset, load_instagram_dataset,
    load_combined_dataset, ingest_scraped_csv, ingest_database_memory
)

print("=== Memulai Skrip Pelatihan Ulang Otomatis (Active Learning + Perturbasi + Kalibrasi) ===")

# Tentukan direktori dasar dinamis untuk pathing absolut
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Konfigurasi Path dan Kamus Slang
ALAY_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "new_kamusalay.csv")
SINGKATAN_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "kamus_singkatan.csv")
ABUSIVE_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "abusive.csv")

DATASET_TWITTER_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "data.csv")
DATASET_INSTAGRAM_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_instagram", "DATASET CYBERBULLYING INSTAGRAM - FINAL.xlsx")
DATASET_COMBINED_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "combined_dataset.csv")

# Inisialisasi kamus slang di normalizer secara global
init_slang_map(ALAY_PATH, SINGKATAN_PATH)

def clean_and_normalize(text: str) -> str:
    return normalize_text(text)["spaced"]

# Muat Leksikon Abusive
df_abusive = pd.read_csv(ABUSIVE_PATH)
abusive_words = set(df_abusive['ABUSIVE'].dropna().str.strip().str.lower().unique().tolist())

def check_toxic_by_lexicon(norm_text: str) -> bool:
    words = set(norm_text.split())
    return any(w in abusive_words for w in words)

# 2. Ingest Data Baru dari Hasil Scraping & Database Memori
new_records = []

# Ingest data scraper
scraped_records, new_files = ingest_scraped_csv(BASE_DIR)
new_records.extend(scraped_records)

# Ingest database memory (PostgreSQL / SQLite)
db_records = ingest_database_memory(BASE_DIR)
new_records.extend(db_records)

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
                is_bully = rec["Label"] == "Bullying"
                encoded_l = 0.0 if is_bully else 1.0
                
                new_row = {
                    "Label": rec["Label"],
                    "clean_text": clean_t,
                    "String": rec["String"],
                    "encoded_label": encoded_l
                }
                appended_list.append(new_row)
                existing_strings.add(normalized_check)
                added_count += 1
                
                # Opsi 4: LLM-based Data Augmentation
                if OLLAMA_URL:
                    print(f"  -> Menghasilkan augmentasi LLM untuk teks: '{rec['String']}'")
                    variations = augment_text_with_llm(rec["String"], is_bully)
                    for var in variations:
                        var_norm = var.strip().lower()
                        if var_norm not in existing_strings:
                            var_clean = clean_and_normalize(var)
                            appended_list.append({
                                "Label": rec["Label"],
                                "clean_text": var_clean,
                                "String": var,
                                "encoded_label": encoded_l
                            })
                            existing_strings.add(var_norm)
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
datasets_loaded = []

# Load Twitter Dataset
df_twitter = load_twitter_dataset(DATASET_TWITTER_PATH, clean_and_normalize)
if df_twitter is not None:
    datasets_loaded.append(df_twitter)
    print("Berhasil memuat dataset Twitter.")

# Load Instagram Dataset
df_instagram = load_instagram_dataset(DATASET_INSTAGRAM_PATH, clean_and_normalize, check_toxic_by_lexicon)
if df_instagram is not None:
    datasets_loaded.append(df_instagram)
    print("Berhasil memuat dataset Instagram.")

# Load Combined Dataset
df_combined_loaded = load_combined_dataset(DATASET_COMBINED_PATH, clean_and_normalize, check_toxic_by_lexicon)
if df_combined_loaded is not None:
    datasets_loaded.append(df_combined_loaded)
    print("Berhasil memuat dataset kombinasi.")

if not datasets_loaded:
    print("Critical Error: Tidak ada dataset utama yang berhasil dimuat untuk retraining.")
    exit(1)

# 5. Data Augmentasi (Sarkasme & Slang Pujian) untuk penyeimbangan pola spesifik
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

# 1. Gabungkan dataset dasar asli yang berhasil dimuat
base_df = pd.concat(datasets_loaded, ignore_index=True)

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

# 3. Terapkan Perturbasi Slang/Typo acak HANYA pada train set yang mengandung unsur toxic
print("Melakukan augmentasi perturbasi teks (typo/leet) secara dinamis pada train set...")
perturbed_records = []
for idx, row in train_df.iterrows():
    if row['is_toxic'] and random.random() < 0.3:
        perturbed_text = perturb_text(row['text_clean'], abusive_words)
        if perturbed_text and perturbed_text != row['text_clean']:
            perturbed_records.append({
                'text_clean': perturbed_text,
                'is_toxic': True,
                'is_bully': row['is_bully']
            })

df_perturbed = pd.DataFrame(perturbed_records)
print(f"Ditambahkan {len(df_perturbed)} baris data hasil perturbasi teks pada train set.")

# 4. Gabungkan train set dengan augmented dan perturbed data
final_train_df = pd.concat([
    train_df,
    df_aug,
    df_perturbed
], ignore_index=True)

final_train_df = final_train_df.dropna()
final_train_df = final_train_df[final_train_df['text_clean'] != ""]
print(f"Total baris data retraining train set (+ augmented & perturbed): {len(final_train_df)} baris.")
print(f"Total baris data test set (bersih): {len(test_df)} baris.")

# 5. Siapkan X dan y
X_train = final_train_df['text_clean']
y_train = final_train_df[['is_toxic', 'is_bully']].astype(int)

X_test = test_df['text_clean']
y_test = test_df[['is_toxic', 'is_bully']].astype(int)

# 6. Vectorization
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
thresholds_path = os.path.join(BASE_DIR, "models", "thresholds.json")
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
joblib.dump(clf, os.path.join(BASE_DIR, "models", "model_lr.joblib"))
joblib.dump(vectorizer, os.path.join(BASE_DIR, "models", "vectorizer.joblib"))
print("Proses retraining sukses! Model 'model_lr.joblib' dan 'vectorizer.joblib' telah diperbarui.")
