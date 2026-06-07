# 🔄 Rencana Pemulihan (Rollback Plan) — BullyGuard ID

Penyusunan rencana pemulihan (*rollback plan*) sangat penting karena implementasi dari Stage 2 hingga Stage 5 menyentuh berkas runtime aplikasi di backend dan frontend.

---

## 🛠️ 1. Pemulihan di Tingkat Git (Git Rollback)

### 🌿 A. Menghapus Cabang Perbaikan (Sebelum di-merge)
Jika terdeteksi kegagalan fitur saat pengujian di branch perbaikan sebelum digabungkan ke cabang utama:
```bash
# Kembali ke cabang utama
git checkout main

# Menghapus branch lokal yang bermasalah secara paksa
git branch -D improvement/apply-stage-1-to-5
```

### ⏪ B. Membatalkan Komit Terakhir (Setelah di-merge)
Jika perubahan sudah terlanjur di-merge ke branch `main` dan menimbulkan masalah di server:
```bash
# Membuat komit pembatalan (revert) secara aman
git revert HEAD
```

> [!CAUTION]
> Hindari menggunakan perintah `git reset --hard` pada branch utama yang telah dipush ke repositori bersama (GitHub/GitLab) karena akan merusak riwayat komit developer lain.

---

## 🔒 2. Pemulihan Masalah Keamanan & API (Stage 2)

### 🚨 Gejala Masalah
- Request API mengembalikan status `401 Unauthorized`.
- Frontend ditolak menghubungi API karena error CORS.
- Server API crash saat startup akibat kegagalan koneksi Redis.

### 🛠️ Langkah Penanganan Cepat
1. **Cek Konfigurasi `.env`**: Pastikan nilai `API_KEY` di backend selaras dengan header yang dikirim oleh client/frontend.
2. **Cek CORS**: Periksa isi variabel `ALLOWED_ORIGINS` di `.env` dan pastikan domain frontend terdaftar lengkap dengan skema (`http://` atau `https://`).
3. **Kesehatan Redis**: Pastikan kontainer Redis aktif dan status kata sandi sinkron dengan compose.
4. **Bypass Dev**: Di lokal, Anda dapat menyetel `ALLOW_MISSING_API_KEY_IN_DEV=true` sementara untuk mendiagnosis masalah.

---

## 🧠 3. Pemulihan Masalah Model & Kalibrasi (Stage 3)

### 🚨 Gejala Masalah
- Python menampilkan `ImportError: cannot import name 'confidence'`.
- Error klasifikasi pada endpoint `/predict/hybrid` akibat salah mem-patch berkas `predictor.py`.
- Evaluator gagal memuat konfigurasi `thresholds.json`.

### 🛠️ Langkah Penanganan Cepat
1. **Verifikasi Unit Test**: Jalankan `pytest tests/test_confidence.py` untuk mengisolasi error perhitungan probabilitas.
2. **Cek Modifikasi Predictor**: Bandingkan berkas `cyberbullying_api/classifier/predictor.py` saat ini dengan riwayat Git (`git diff`) untuk memastikan tidak ada logika orisinal model statistik yang terhapus secara tidak sengaja.
3. **Gunakan Nilai Default**: Jika `thresholds.json` rusak, kembalikan nilai default biner `0.5` pada konfigurasi.

---

## 🎨 4. Pemulihan Masalah Frontend (Stage 4)

### 🚨 Gejala Masalah
- Perintah `npm run build` gagal akibat kesalahan tipe TypeScript.
- Layar antarmuka modul analisis (Detector) menjadi blank putih.
- Error impor file karena salah path folder.

### 🛠️ Langkah Penanganan Cepat
1. **Periksa File Wrapper**: Pastikan file `frontend/src/components/Detector.tsx` berfungsi secara benar mengekspor ulang folder Detector internal.
2. **Kembalikan Berkas Tunggal**: Jika modul baru dalam folder `Detector/` rusak parah dan Anda butuh memulihkan UI orisinal secara cepat, jalankan:
   ```bash
   # Restore file Detector.tsx lama dari Git
   git checkout main -- frontend/src/components/Detector.tsx
   
   # Hapus folder modular yang bermasalah
   rm -rf frontend/src/components/Detector/
   ```

---

## 🐳 5. Pemulihan Konfigurasi Docker

Jika kontainer Docker gagal melakukan build atau crash berulang kali (*crash loop*):
```bash
# Matikan seluruh kontainer beserta volume cache yang mungkin rusak
docker compose down -v

# Jalankan ulang build bersih tanpa cache lama
docker compose up -d --build
```

