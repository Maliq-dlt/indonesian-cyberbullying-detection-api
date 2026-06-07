# 📋 Release Notes Template — BullyGuard ID

Dokumen ini adalah template pencatatan rilis untuk mendokumentasikan pembaruan fitur, perbaikan keamanan, dan perubahan arsitektur pada setiap versi rilis sistem BullyGuard ID.

---

## 🏷️ Versi Rilis: `v0.2.0-hardening-release`

### 📝 Ringkasan Rilis
Rilis ini berfokus pada **Security Hardening (Peningkatan Keamanan)**, **ML Confidence Calibration (Kalibrasi Keyakinan Model)**, **Frontend Modularization (Pemecahan Komponen UI)**, serta penyediaan skrip **Integration Testing** otomatis. Seluruh dokumentasi juga diperbarui agar memposisikan proyek secara realistis sebagai **Advanced MVP** yang kredibel.

---

## 🚀 Fitur Baru & Perubahan

### ➕ 1. Ditambahkan (Added)
- **Modul Kalibrasi**: File `confidence.py` untuk penanganan probabilitas ML yang lebih halus dan adaptif.
- **Skrip Threshold Evaluator**: File `evaluate_thresholds.py` untuk mencari batas threshold optimal secara otomatis menggunakan dataset CSV.
- **Skrip Pengujian Otomatis**: Skrip bash dan powershell (`smoke_test_api.ps1`/`smoke_test_api.sh` dan `verify_patch_files.sh`) untuk smoke testing endpoint API.
- **Dokumentasi Panduan Baru**: Laporan evaluasi model (`MODEL_EVALUATION.md`), security hardening (`SECURITY_HARDENING.md`), dan analisis kesalahan (`ERROR_ANALYSIS_GUIDE.md`).

### 🔄 2. Diubah (Changed)
- **Positioning Proyek**: Kredibilitas proyek diubah menjadi *Advanced MVP/Prototype* agar selaras dengan kemampuan teknis saat ini.
- **Restrukturisasi Frontend**: Komponen raksasa `Detector.tsx` dipecah menjadi komponen-komponen kecil dalam folder `Detector/` (InputPanel, ResultCard, XaiDrawer, dsb.) guna kemudahan pemeliharaan kode.
- **Optimasi Docker Compose**: Mengimplementasikan *image re-use* untuk Celery worker guna menghemat RAM dan memotong durasi build server.

### 🔒 3. Peningkatan Keamanan (Security Hardening)
- **Constant-Time Verification**: API Key menggunakan fungsi komparasi konstan untuk mencegah *timing attacks*.
- **Fail-Closed Redis**: Rate limiter di production akan memblokir request jika database cache Redis mati demi keamanan dari spamming.
- **Webhook SSRF Protection**: Validasi ketat alamat IP tujuan webhook untuk mencegah serangan pemindaian port internal (SSRF).

---

## ⚠️ Batasan Sistem Saat Ini (Known Limitations)
- Akurasi model biner masih memerlukan pembuktian menggunakan dataset validasi riil dari pengguna.
- Belum tersedia load testing terarah untuk memantau performa latensi concurrent requests tingkat tinggi.
- Skema autentikasi admin panel saat ini masih menggunakan konfigurasi API Key tunggal.

---

## 🛠️ Catatan Migrasi / Peningkatan (Upgrade Notes)
1. Salin ulang berkas `.env.example` ke `.env` Anda dan isi parameter rahasia yang baru.
2. Jalankan perintah `pytest` dari root direktori untuk memverifikasi fungsionalitas backend.
3. Jalankan `npm run build` pada folder `frontend` untuk memvalidasi build produksi.
4. Nyalakan sistem menggunakan `docker compose up -d --build` dan jalankan skrip `smoke_test_api.ps1`.
