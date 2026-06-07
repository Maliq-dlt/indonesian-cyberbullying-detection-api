# 🤝 Panduan Integrasi Akhir (Final Integration Guide) — BullyGuard ID

Panduan ini digunakan setelah seluruh patch Stage 1 hingga Stage 4 disiapkan untuk diverifikasi dan digabungkan (*merge*) secara aman ke cabang utama (*main*).

---

## 📐 1. Prinsip Dasar Integrasi

1. **Bertahap**: Jangan menggabungkan seluruh perubahan sekaligus. Terapkan dan uji per tahap.
2. **Pengujian Berkelanjutan**: Jalankan uji coba fungsionalitas dan keamanan setelah setiap tahap selesai digabungkan.
3. **Pencatatan Versi**: Gunakan tag rilis Git untuk mencatat setiap tahapan rilis penting.
4. **Pencegahan Overclaim**: Pastikan dokumentasi diposisikan secara realistis sebagai **Advanced MVP**.

---

## 💻 2. Persiapan Repositori Lokal

Pastikan working tree repositori lokal Anda bersih sebelum memulai integrasi:

```bash
# Memeriksa status repositori
git status

# Memastikan tidak ada file sisa yang tidak terkomit
git status --short
```

> [!TIP]
> Jika Anda memiliki perubahan lokal yang belum sempat disimpan, buat komit cadangan terlebih dahulu:
> ```bash
> git add .
> git commit -m "backup: save local changes before integration"
> ```

---

## 🔑 3. Konfigurasi Lingkungan (Environment)

Salin konfigurasi default dari berkas `.env.example` ke `.env`:

```bash
cp .env.example .env
```

Pastikan variabel-variabel sensitif ini diatur dengan benar (jangan gunakan nilai default untuk deployment rilis):
```env
ENV=development
API_KEY=rahasia_api_key_yang_sangat_panjang_dan_aman_123
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## 🐍 4. Pengujian Backend API

Jalankan pengujian backend menggunakan pytest untuk memverifikasi logika klasifikasi, routing, dan confidence:

**Bagi Pengguna Linux / macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cyberbullying_api/requirements.txt
pytest -q
```

**Bagi Pengguna Windows (PowerShell):**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r cyberbullying_api\requirements.txt
pytest -q
```

---

## 🎨 5. Pengujian Frontend Web

Pastikan kompilasi aset produksi frontend berjalan tanpa error TypeScript:

```bash
cd frontend
npm install
npm run lint
npm run build
```

---

## 🐳 6. Pengujian Docker Compose (Simulasi Production)

### ⚙️ Mode Development (Local Dev Server)
Jalankan docker compose standar dev untuk verifikasi reloading:
```bash
docker compose up -d --build
curl http://localhost:8000/health
```

### 🔒 Mode Production-Like (Hardened State)
Jalankan docker compose gabungan dengan file override produksi:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
curl http://localhost:8000/health
```

### 🔑 Pengujian Akses Terproteksi
Pastikan endpoint status menolak jika API Key kosong dan menerima jika menyertakan key yang valid:
```bash
# Menolak request (401 Unauthorized)
curl -I http://localhost:8000/models/status

# Diterima (200 OK)
curl -H "X-API-Key: rahasia_api_key_yang_sangat_panjang_dan_aman_123" http://localhost:8000/models/status
```

---

## 🚀 7. Pengujian Smoke Test Otomatis

Gunakan skrip pengujian bawaan untuk mengirim request prediksi uji coba ke server API:

**Bagi Pengguna Linux / macOS / Git Bash:**
```bash
bash scripts/smoke_test_api.sh
```

**Bagi Pengguna Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_api.ps1
```

---

## 🏁 8. Rilis dan Git Tagging

Setelah seluruh pengujian di atas sukses, gabungkan cabang integrasi ke branch utama (`main`), lalu buat tag rilis internal:

```bash
# Pindah ke branch utama dan gabungkan cabang perbaikan
git checkout main
git merge improvement/apply-stage-1-to-5

# Membuat tag rilis
git tag v0.2.0-hardening-release
git push origin v0.2.0-hardening-release
```

