import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, f1_score
import joblib
import os

print("--- Memulai Proses Pelatihan Model ---")

# Path ke dataset (berada di folder parent)
dataset_path = os.path.join("..", "dataset 2", "combined_dataset.csv")

if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"Dataset tidak ditemukan di path: {os.path.abspath(dataset_path)}")

# 1. Memuat dataset
print(f"Memuat dataset dari {dataset_path}...")
df = pd.read_csv(dataset_path)
df['y_true'] = df['Label'].isin(['Bullying', 'negatif', 'negative'])
df = df.dropna(subset=['y_true', 'String'])

# 2. Split data menjadi Train Set (80%) dan Test Set (20%)
X_train, X_test, y_train, y_test = train_test_split(
    df['String'], df['y_true'], test_size=0.2, random_state=42, stratify=df['y_true']
)
print(f"Jumlah Data Latih (Train): {len(X_train)} | Jumlah Data Uji (Test): {len(X_test)}")

# 3. Ekstraksi fitur menggunakan TF-IDF (Unigram + Bigram)
print("Mengekstrak fitur menggunakan TF-IDF...")
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# 4. Melatih model Logistic Regression
print("Melatih model Logistic Regression...")
lr_model = LogisticRegression(max_iter=1000)
lr_model.fit(X_train_tfidf, y_train)

# 5. Evaluasi Hasil
preds = lr_model.predict(X_test_tfidf)
print("\n=== Hasil Evaluasi Model di Test Set ===")
print("Accuracy :", accuracy_score(y_test, preds))
print("F1-Score :", f1_score(y_test, preds))
print("\nLaporan Klasifikasi:")
print(classification_report(y_test, preds))

# 6. Menyimpan model & vectorizer ke disk (joblib)
print("Menyimpan model ke model_lr.joblib...")
joblib.dump(lr_model, "model_lr.joblib")

print("Menyimpan vectorizer ke vectorizer.joblib...")
joblib.dump(vectorizer, "vectorizer.joblib")

print("\n--- Model Berhasil Diekspor! ---")
