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
- [x] **API Key Wajib**: API menolak request jika `API_KEY` tidak disertakan saat dideploy di production.
- [x] **JWT Secret**: JWT secret menggunakan `secrets.token_hex(32)` di dev, wajib eksplisit di production.
- [x] **Security Headers**: HSTS, X-Frame-Options, X-Content-Type-Options, dll telah aktif.
- [x] **Request Size Limit**: Pembatasan 10MB body telah aktif.
- [x] **Fail-Closed Redis**: Rate limiting di production dikonfigurasi `RATE_LIMIT_FAIL_OPEN=false`.
- [x] **Akses Publik Dibatasi**: Endpoint dokumentasi Swagger dinonaktifkan di production.
- [x] **Bebas Kredensial Hardcoded**: Seluruh password database dan Redis di docker-compose menggunakan variabel lingkungan.

---

## 🧠 4. Pengujian ML Confidence & Routing
- [x] **Logika Confidence**: Perhitungan probabilitas di `confidence.py` bekerja normal.
- [x] **Unit Test Lolos**: Pengujian unit test backend (101 tests) lulus 100%.
- [x] **Routing Adaptif**: Kalibrasi probabilitas memastikan request ragu-ragu diteruskan ke tier di atasnya.
- [x] **Evaluator Threshold**: Skrip `evaluate_thresholds.py` sukses dijalankan pada dataset validasi.

---

## 🎨 5. Pengujian Antarmuka Frontend
- [x] **Wrapper Detector**: File wrapper `Detector.tsx` tetap mempertahankan kompatibilitas impor lama.
- [x] **Modul Komponen**: Komponen Detector telah dipecah ke dalam folder `Detector/` dengan rapi.
- [x] **Home Modular**: Home.tsx telah dipecah menjadi 3 sub-komponen (ChatSimulator, FeaturesShowcase, DashboardHistoryChart).
- [x] **Zustand Store**: State management menggunakan Zustand (`store/useAppStore.ts`) menggantikan prop drilling.
- [x] **Vitest Tests**: 45 frontend tests lulus (Detector, XAIHighlightText, API, constants, utils).
- [x] **Kompilasi Sukses**: Perintah `npm run lint` dan `npm run build` berhasil diselesaikan tanpa error.
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

