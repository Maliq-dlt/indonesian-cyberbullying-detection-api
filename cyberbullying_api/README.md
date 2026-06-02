# Cyberbullying & Hate Speech Detection API

Proyek ini mendemonstrasikan bagaimana memigrasikan model deteksi cyberbullying bahasa Indonesia (metode Leksikon, Machine Learning, dan Deep Learning) ke sebuah API siap produksi menggunakan **FastAPI**, **Uvicorn**, dan **Docker** sesuai dengan arsitektur microservices.

---

## 🚀 Fitur Utama
1. **Leksikon & Normalisasi Teks** (`POST /predict/lexicon`):
   - Deteksi cepat berbasis aturan menggunakan **139 kata kasar**.
   - Normalisasi penyamaran leetspeak dan perulangan kata.
   - Normalisasi kata slang alay & singkatan menggunakan kamus dengan **15.000+ pemetaan**.
2. **Machine Learning Classifier** (`POST /predict/ml`):
   - Deteksi cerdas berbasis statistik menggunakan **Logistic Regression** dan **TF-IDF Vectorizer**.
   - Kecepatan inferensi tinggi dengan F1-Score **~89.4%**.
3. **Deep Learning Transformer** (`POST /predict/transformers`):
   - Deteksi konteks mendalam menggunakan arsitektur **XLM-RoBERTa** (`nahiar/hatespeech-abusive-xlm-roberta-v1`).
   - Mampu menangani ambiguitas konteks kalimat secara lebih akurat.

---

## 🛠️ Cara Menjalankan Secara Lokal (Tanpa Docker)

### 1. Prasyarat
Pastikan Anda menggunakan Python 3.10 ke atas dan instal semua library yang diperlukan:
```bash
pip install -r requirements.txt
```

### 2. Ekspor Model
Jalankan skrip pelatihan untuk membuat file model Logistic Regression:
```bash
python train_and_export.py
```
Skrip ini akan melatih model di dataset kompilasi dan menyimpan file biner `model_lr.joblib` dan `vectorizer.joblib` ke dalam folder.

### 3. Jalankan Server API
Jalankan Uvicorn server:
```bash
uvicorn main:app --reload
```
Aplikasi Anda akan berjalan di `http://127.0.0.1:8000`.

*   **Dokumentasi Swagger API**: Buka browser ke `http://127.0.0.1:8000/docs` untuk melakukan uji coba secara langsung menggunakan GUI interaktif.

---

## 🐳 Cara Menjalankan Menggunakan Docker

Kami telah menyediakan `Dockerfile` yang telah dioptimasi dengan instalasi **PyTorch CPU-only** untuk memperkecil ukuran image Docker Anda secara masif (menghemat space server Anda).

### 1. Bangun Image Docker
Jalankan perintah ini di direktori root proyek (`/Cyber`):
```bash
docker build -f cyberbullying_api/Dockerfile -t cyberbullying-api .
```

### 2. Jalankan Kontainer Docker
```bash
docker run -d -p 8000:8000 --name cyberbullying-container cyberbullying-api
```
Aplikasi sekarang berjalan di kontainer terisolasi dan dapat diakses di `http://localhost:8000`.

---

## ☁️ Panduan Deployment ke Cloud (Railway / Render / Render)

Anda dapat dengan mudah mendeploy kontainer Docker ini ke platform cloud modern seperti **Railway** atau **Render**:

### Langkah-langkah:
1. Push kode proyek ini ke repositori **GitHub** pribadi Anda.
2. Buat akun di **Railway.app** atau **Render.com**.
3. Pilih opsi **Deploy dari GitHub**.
4. Railway/Render akan mendeteksi keberadaan `Dockerfile` di folder `cyberbullying_api` dan membangun kontainernya secara otomatis.
5. Selesai! Platform cloud akan memberikan Anda sebuah URL HTTPS publik (contoh: `https://cyberbullying-api.up.railway.app`) yang siap diintegrasikan ke frontend Android/iOS/Web Anda.
