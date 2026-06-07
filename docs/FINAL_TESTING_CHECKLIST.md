# 🧪 Daftar Periksa Pengujian Akhir (Final Testing Checklist) — BullyGuard ID

Gunakan daftar periksa (*checklist*) ini sebelum menggabungkan perbaikan (*merge*) ke branch utama (`main`) untuk menjamin kebersihan repositori, kualitas model, dan keamanan sistem.

---

## 📁 1. Kebersihan Repositori & Git (Git Hygiene)
- [ ] **Working Tree Bersih**: Tidak ada berkas sisa yang tidak terkomit sebelum pengujian dilakukan.
- [ ] **Struktur Percabangan**: Masing-masing tahap perubahan terdokumentasi dalam git commit yang teratur.
- [ ] **Tanpa Kebocoran Kredensial**: Tidak ada token asli, password, atau kunci API riil yang ter-commit ke repositori Git.
- [ ] **Gitignore Aktif**: File `.env` terdaftar secara benar dalam `.gitignore`.

---

## 📄 2. Kelengkapan Dokumentasi
- [ ] **README MVP**: Berkas `README.md` tidak membuat klaim *production-grade* tanpa bukti benchmark.
- [ ] **Panduan Setup**: Berkas `docs/LOCAL_SETUP.md` diuji ulang dan dapat diikuti tanpa kendala oleh developer baru.
- [ ] **Dokumen Evaluasi Model**: Berkas `MODEL_EVALUATION.md` disiapkan sebagai draf pencatatan metrik performa model.
- [ ] **Security & Error Guides**: Panduan hardening keamanan (`SECURITY_HARDENING.md`) dan analisis kesalahan (`ERROR_ANALYSIS_GUIDE.md`) lengkap.

---

## 🔒 3. Hardening Keamanan Backend
- [ ] **API Key Wajib**: API menolak request jika `API_KEY` tidak disertakan saat dideploy di production.
- [ ] **Fail-Closed Redis**: Rate limiting di production dikonfigurasi `RATE_LIMIT_FAIL_OPEN=false` agar memblokir request jika Redis mati.
- [ ] **Akses Publik Dibatasi**: Endpoint dokumentasi Swagger dinonaktifkan di production.
- [ ] **Bebas Kredensial Hardcoded**: Seluruh password database dan Redis di docker-compose menggunakan variabel lingkungan.

---

## 🧠 4. Pengujian ML Confidence & Routing
- [ ] **Logika Confidence**: Perhitungan probabilitas di `confidence.py` bekerja normal.
- [ ] **Unit Test Lolos**: Pengujian unit test (`pytest tests/test_confidence.py`) lulus 100%.
- [ ] **Routing Adaptif**: Kalibrasi probabilitas memastikan request ragu-ragu diteruskan ke tier di atasnya dan tidak diberi skor flat `1.0` atau `0.90`.
- [ ] **Evaluator Threshold**: Skrip `evaluate_thresholds.py` sukses dijalankan pada dataset validasi.

---

## 🎨 5. Pengujian Antarmuka Frontend
- [ ] **Wrapper Detector**: File wrapper `Detector.tsx` tetap mempertahankan kompatibilitas impor lama.
- [ ] **Modul Komponen**: Komponen Detector telah dipecah ke dalam folder `Detector/` dengan rapi.
- [ ] **Kompilasi Sukses**: Perintah `npm run lint` dan `npm run build` berhasil diselesaikan tanpa error.
- [ ] **Visual & XAI Drawer**: Panel XAI Drawer dan grafik visualisasi bobot kata penting berfungsi secara lancar.

---

## 🐳 6. Pengecekan Kontainer Docker
- [ ] **Build Sukses**: Perintah `docker compose up -d --build` berhasil diselesaikan tanpa masalah.
- [ ] **Pengecekan Status**: Kontainer API, PostgreSQL, Redis, dan worker Celery berstatus healthy/started.
- [ ] **Image Sharing**: Kontainer worker menggunakan image reuse dari API untuk menghemat RAM dan memotong waktu build.

---

## 🚀 7. Smoke Test Endpoint API
- [ ] **Health Check**: Endpoint `GET /health` mengembalikan status `200 OK`.
- [ ] **Akses Terproteksi**: Request ke `/models/status` ditolak dengan status `401 Unauthorized` jika API key tidak valid.
- [ ] **Prediksi Hybrid**: Endpoint `/predict/hybrid` memproses kalimat uji coba dengan respon JSON yang sesuai spesifikasi.
- [ ] **Input Limit**: Sistem menolak teks kosong atau teks yang melampaui batas karakter.

