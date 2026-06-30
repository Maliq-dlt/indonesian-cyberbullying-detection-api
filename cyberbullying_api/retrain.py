import os
import sys
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
from dotenv import load_dotenv
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("../.env"):
    load_dotenv("../.env")
else:
    load_dotenv()

from normalizer import init_slang_map, normalize_text

from training import (
    augment_text_with_llm, perturb_text,
    sarcasm_raw, slang_praise_raw, GEMINI_API_KEY, GEMINI_BASE_URL,
    load_twitter_dataset, load_instagram_dataset,
    load_combined_dataset, ingest_scraped_csv, ingest_database_memory,
    load_mendeley_dataset, load_tiktok_rhiosutoyo_dataset
)

# Tentukan direktori dasar dinamis untuk pathing absolut
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(BASE_DIR, "cache")
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "training.log")



# 1. Konfigurasi Path dan Kamus Slang
ALAY_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "new_kamusalay.csv")
SINGKATAN_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "kamus_singkatan.csv")
ABUSIVE_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "abusive.csv")

DATASET_TWITTER_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "data.csv")
DATASET_INSTAGRAM_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_instagram", "DATASET CYBERBULLYING INSTAGRAM - FINAL.xlsx")
DATASET_COMBINED_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "combined_dataset.csv")
DATASET_MENDELEY_DIR = os.path.join(BASE_DIR, "..", "dataset", "ds_mendeley")
DATASET_TIKTOK_RHIOSUTOYO_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_tiktok_rhiosutoyo", "Dataset-Research.csv")

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
            if "is_toxic" not in df_combined.columns:
                print("Kolom 'is_toxic' tidak ditemukan pada dataset gabungan lama. Mengisi menggunakan leksikon...")
                df_combined["is_toxic"] = df_combined["clean_text"].apply(check_toxic_by_lexicon)
        else:
            df_combined = pd.DataFrame(columns=["Label", "clean_text", "String", "encoded_label", "is_toxic"])
        
        existing_strings = set(df_combined["String"].dropna().str.strip().str.lower().unique())
        
        added_count = 0
        appended_list = []
        for rec in new_records:
            normalized_check = rec["String"].strip().lower()
            if normalized_check not in existing_strings:
                clean_t = clean_and_normalize(rec["String"])
                is_bully = rec["Label"] == "Bullying"
                encoded_l = 0.0 if is_bully else 1.0
                
                # Gunakan is_toxic dari record jika tersedia, jika tidak gunakan leksikon
                if "is_toxic" in rec:
                    is_toxic = bool(rec["is_toxic"])
                else:
                    is_toxic = check_toxic_by_lexicon(clean_t)
                
                new_row = {
                    "Label": rec["Label"],
                    "clean_text": clean_t,
                    "String": rec["String"],
                    "encoded_label": encoded_l,
                    "is_toxic": is_toxic
                }
                appended_list.append(new_row)
                existing_strings.add(normalized_check)
                added_count += 1
                
                # Opsi 4: LLM-based Data Augmentation
                if GEMINI_API_KEY:
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
                                "encoded_label": encoded_l,
                                "is_toxic": is_toxic
                            })
                            existing_strings.add(var_norm)
                            added_count += 1
        
        if appended_list:
            df_to_append = pd.DataFrame(appended_list)
            df_combined = pd.concat([df_combined, df_to_append], ignore_index=True)
            df_combined.to_csv(DATASET_COMBINED_PATH, index=False, encoding="utf-8")
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

# Load Mendeley Dataset
df_mendeley = load_mendeley_dataset(DATASET_MENDELEY_DIR, clean_and_normalize, check_toxic_by_lexicon)
if df_mendeley is not None:
    datasets_loaded.append(df_mendeley)
    print("Berhasil memuat dataset Mendeley (Instagram, Twitter, Youtube).")

# Load TikTok Rhiosutoyo Dataset
df_tiktok_rhiosutoyo = load_tiktok_rhiosutoyo_dataset(DATASET_TIKTOK_RHIOSUTOYO_PATH, clean_and_normalize, check_toxic_by_lexicon)
if df_tiktok_rhiosutoyo is not None:
    datasets_loaded.append(df_tiktok_rhiosutoyo)
    print("Berhasil memuat dataset TikTok Rhiosutoyo.")

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

# Filter duplikat dari df_aug berdasarkan teks yang sudah ada di test_df sebelum menggabungkan untuk mencegah data leakage
test_texts = set(test_df['text_clean'].dropna().unique())
df_aug = df_aug[~df_aug['text_clean'].isin(test_texts)]
print(f"Jumlah data augmentasi setelah difilter untuk mencegah kebocoran: {len(df_aug)} baris.")

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

# 3.5. Ambil data tervalidasi dari database PostgreSQL / SQLite (Active Learning Oversampling)
validated_records = []
import asyncio
from classifier.database import get_pg_pool, decrypt_text
import sqlite3

def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop and loop.is_running():
        import threading
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(lambda: asyncio.run(coro)).result()
    else:
        return asyncio.run(coro)

async def fetch_validated_db():
    recs = []
    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT encrypted_text, is_toxic, is_bully FROM classification_memory WHERE is_validated = 1")
                for r in rows:
                    decrypted = decrypt_text(r['encrypted_text'])
                    recs.append({
                        'text_clean': clean_and_normalize(decrypted),
                        'is_toxic': bool(r['is_toxic']),
                        'is_bully': bool(r['is_bully'])
                    })
        except Exception as e:
            print("Warning: Gagal fetch validated dari PostgreSQL:", e)
    return recs

try:
    validated_records = run_async(fetch_validated_db())
except Exception as e:
    print("Warning: Gagal fetch validated dari PostgreSQL (event loop error):", e)

if not validated_records:
    try:
        db_path = os.path.join(BASE_DIR, "cache", "cloud_llm_cache.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT encrypted_text, is_toxic, is_bully FROM classification_memory WHERE is_validated = 1")
            rows = cursor.fetchall()
            for r in rows:
                decrypted = decrypt_text(r[0])
                validated_records.append({
                    'text_clean': clean_and_normalize(decrypted),
                    'is_toxic': bool(r[1]),
                    'is_bully': bool(r[2])
                })
            conn.close()
    except Exception as e:
        print("Warning: Gagal fetch validated dari SQLite:", e)

df_validated_oversampled = pd.DataFrame()
if validated_records:
    print(f"Ditemukan {len(validated_records)} sampel tervalidasi oleh manusia. Melakukan oversampling x5 untuk Active Learning...")
    oversampled = []
    for _ in range(5):
        oversampled.extend(validated_records)
    df_validated_oversampled = pd.DataFrame(oversampled)

df_perturbed = pd.DataFrame(perturbed_records)
print(f"Ditambahkan {len(df_perturbed)} baris data hasil perturbasi teks pada train set.")

# 4. Gabungkan train set dengan augmented, perturbed, dan oversampled validated data
concat_list = [train_df, df_aug, df_perturbed]
if not df_validated_oversampled.empty:
    concat_list.append(df_validated_oversampled)

final_train_df = pd.concat(concat_list, ignore_index=True)
final_train_df = final_train_df.dropna()
final_train_df = final_train_df[final_train_df['text_clean'] != ""]
print(f"Total baris data retraining train set (+ augmented & perturbed & validated): {len(final_train_df)} baris.")
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

# 7. Melatih Ulang Model Baru
print("Melatih ulang Multi-Label Classifier dengan Kalibrasi Probabilitas (Platt Scaling)...")
from sklearn.calibration import CalibratedClassifierCV
base_lr = LogisticRegression(max_iter=1500, class_weight='balanced', C=1.5, random_state=42)
# Gunakan CalibratedClassifierCV untuk melakukan kalibrasi probabilitas via 5-fold cross-validation
calibrated_lr = CalibratedClassifierCV(estimator=base_lr, method='sigmoid', cv=5)
clf = MultiOutputClassifier(calibrated_lr)
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

# Evaluasi model baru
preds_toxic = (probs_toxic >= best_thresh_toxic).astype(int)
preds_bully = (probs_bully >= best_thresh_bully).astype(int)
new_f1_toxic = f1_score(y_test['is_toxic'], preds_toxic, zero_division=0)
new_f1_bully = f1_score(y_test['is_bully'], preds_bully, zero_division=0)

# 9. Mekanisme Rollback Otomatis
old_model_path = os.path.join(BASE_DIR, "models", "model_lr.joblib")
old_vect_path = os.path.join(BASE_DIR, "models", "vectorizer.joblib")
old_f1_toxic = 0.0
old_f1_bully = 0.0

if os.path.exists(old_model_path) and os.path.exists(old_vect_path):
    try:
        old_clf = joblib.load(old_model_path)
        old_vect = joblib.load(old_vect_path)
        X_test_old_tfidf = old_vect.transform(X_test)
        
        old_thresholds = { "threshold_toxic": 0.5, "threshold_bully": 0.5 }
        old_thresholds_path = os.path.join(BASE_DIR, "models", "thresholds.json")
        if os.path.exists(old_thresholds_path):
            with open(old_thresholds_path, "r") as f:
                old_thresholds = json.load(f)
                
        old_probs = old_clf.predict_proba(X_test_old_tfidf)
        old_probs_toxic = old_probs[0][:, 1]
        old_probs_bully = old_probs[1][:, 1]
        
        old_preds_toxic = (old_probs_toxic >= old_thresholds.get("threshold_toxic", 0.5)).astype(int)
        old_preds_bully = (old_probs_bully >= old_thresholds.get("threshold_bully", 0.5)).astype(int)
        
        old_f1_toxic = f1_score(y_test['is_toxic'], old_preds_toxic, zero_division=0)
        old_f1_bully = f1_score(y_test['is_bully'], old_preds_bully, zero_division=0)
        print(f"Perbandingan F1-Score -> Model Lama Toxic: {old_f1_toxic:.4f} | Model Baru Toxic: {new_f1_toxic:.4f}")
        print(f"Perbandingan F1-Score -> Model Lama Bully: {old_f1_bully:.4f} | Model Baru Bully: {new_f1_bully:.4f}")
    except Exception as e:
        print("Warning: Gagal mengevaluasi model lama untuk perbandingan:", e)

# Jika model baru mengalami penurunan drastis (penurunan F1-Score > 0.08 pada salah satu label)
if old_f1_toxic > 0.0 and (old_f1_toxic - new_f1_toxic > 0.08 or old_f1_bully - new_f1_bully > 0.08):
    print("\n❌ [ROLLBACK] Model baru mengalami penurunan performa yang signifikan (> 8% F1-Score).")
    print("Membatalkan pembaruan model. Model lama tetap dipertahankan sebagai model aktif.")
    exit(0)

# 10. Menyimpan Model & Vectorizer dengan Versioning & Metadata
import datetime
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

versioned_model_name = f"model_lr_{timestamp}.joblib"
versioned_vect_name = f"vectorizer_{timestamp}.joblib"

models_dir = os.path.join(BASE_DIR, "models")
os.makedirs(models_dir, exist_ok=True)

versioned_model_path = os.path.join(models_dir, versioned_model_name)
versioned_vect_path = os.path.join(models_dir, versioned_vect_name)

print(f"Menyimpan model & vectorizer versi terbaru: {versioned_model_name}...")
joblib.dump(clf, versioned_model_path)
joblib.dump(vectorizer, versioned_vect_path)

# Simpan juga ke file default utama agar API langsung menggunakannya
joblib.dump(clf, os.path.join(models_dir, "model_lr.joblib"))
joblib.dump(vectorizer, os.path.join(models_dir, "vectorizer.joblib"))

# Simpan thresholds.json
thresholds_path = os.path.join(models_dir, "thresholds.json")
thresholds_data = {
    "threshold_toxic": best_thresh_toxic,
    "threshold_bully": best_thresh_bully
}
with open(thresholds_path, "w") as f:
    json.dump(thresholds_data, f)

# Simpan riwayat versi model aktif ke current_model_version.json
current_version_path = os.path.join(models_dir, "current_model_version.json")
version_metadata = {
    "active_version": timestamp,
    "model_file": versioned_model_name,
    "vectorizer_file": versioned_vect_name,
    "f1_toxic": float(new_f1_toxic),
    "f1_bully": float(new_f1_bully),
    "threshold_toxic": best_thresh_toxic,
    "threshold_bully": best_thresh_bully,
    "updated_at": str(datetime.datetime.now())
}
with open(current_version_path, "w") as f:
    json.dump(version_metadata, f, indent=4)

try:
    from classifier.database import save_retraining_history
    asyncio.run(save_retraining_history(
        f1_toxic=float(new_f1_toxic),
        f1_bully=float(new_f1_bully),
        threshold_toxic=float(best_thresh_toxic),
        threshold_bully=float(best_thresh_bully),
        active_version=timestamp
    ))
    print("[SUKSES] Berhasil menyimpan riwayat retraining ke database.")
except Exception as db_err:
    print(f"Warning: Gagal menyimpan riwayat retraining ke database: {str(db_err)}")

print("\n=== HASIL EVALUASI RETRAINING DENGAN AMBANG BATAS TERKALIBRASI ===")
from sklearn.metrics import classification_report
print("1. Target: TOXICITY (is_toxic)")
print(classification_report(y_test['is_toxic'], preds_toxic))
print("2. Target: BULLYING (is_bully)")
print(classification_report(y_test['is_bully'], preds_bully))
print(f"Proses retraining sukses! Berkas model terkompilasi dan metadata disimpan di: {current_version_path}")

# Tutup connection pool PostgreSQL & Redis secara bersih sebelum keluar
async def cleanup_resources():
    import classifier.database as db_mod
    if db_mod.PG_POOL is not None:
        try:
            await db_mod.PG_POOL.close()
            print("PostgreSQL connection pool berhasil ditutup secara bersih.")
        except Exception as e:
            print(f"Warning: Gagal menutup PostgreSQL connection pool: {e}")
            
    if db_mod.REDIS_CLIENT is not None:
        try:
            await db_mod.REDIS_CLIENT.close()
            print("Redis client connection berhasil ditutup secara bersih.")
        except Exception as e:
            print(f"Warning: Gagal menutup Redis client connection: {e}")

try:
    run_async(cleanup_resources())
except Exception as e:
    print("Warning: Gagal menjalankan cleanup_resources:", e)
