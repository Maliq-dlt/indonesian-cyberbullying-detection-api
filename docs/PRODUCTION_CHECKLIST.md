# 🚀 Production Readiness Checklist — BullyGuard ID

Dokumen ini berisi daftar persyaratan wajib (*checklist*) yang harus dipenuhi sebelum sistem BullyGuard ID dideploy ke lingkungan produksi (*production*).

> [!WARNING]
> Sistem ini **belum boleh** diklaim sebagai *Enterprise-Ready* atau *Production-Grade* sebelum seluruh poin checklist di bawah ini diverifikasi secara penuh oleh tim infrastruktur dan AI Anda.

---

## 🔒 1. Keamanan & Hardening API
- [ ] **API Key**: Wajib mengaktifkan autentikasi API Key di production (`ALLOW_MISSING_API_KEY_IN_DEV=false`).
- [ ] **Kredensial Unik**: Mengganti kata sandi bawaan untuk PostgreSQL dan Redis di berkas `docker-compose.prod.yml`.
- [ ] **Git Protection**: Memastikan berkas `.env` yang berisi token dan kunci asli sudah masuk ke `.gitignore` dan tidak di-commit.
- [ ] **CORS Policy**: Membatasi `ALLOWED_ORIGINS` hanya ke domain frontend resmi yang dipercaya (bukan wildcard `*`).
- [ ] **TLS/HTTPS**: Mengonfigurasi Nginx, Caddy, atau Cloudflare sebagai *reverse proxy* di atas Docker container untuk enkripsi TLS/HTTPS.
- [ ] **Proteksi SSRF Webhook**: Membatasi `WEBHOOK_ALLOWED_HOSTS` untuk mencegah serangan Server-Side Request Forgery.
- [ ] **Rate Limiting Fail-Closed**: Memastikan `RATE_LIMIT_FAIL_OPEN` bernilai `false` di production untuk memblokir request jika Redis mati.
- [ ] **Pencegahan Data Leak**: Mematikan debug mode dan memastikan stack trace error backend tidak dikembalikan ke pengguna luar.

---

## 📊 2. Kualitas Model & Integritas Data
- [ ] **Laporan Evaluasi**: Melengkapi metrik performa model di berkas [`MODEL_EVALUATION.md`](../MODEL_EVALUATION.md) menggunakan dataset riil.
- [ ] **Distribusi Label Seimbang**: Memastikan data latih memiliki representasi seimbang antara kelas toxic, cyberbullying, dan aman.
- [ ] **Threshold Tuning**: Memilih ambang batas klasifikasi (*decision thresholds*) berdasarkan hasil validasi empiris untuk meminimalisasi *False Positive*.
- [ ] **Isolasi Data Uji**: Memastikan data uji (*test set*) bersifat statis dan tidak tercampur dalam alur retraining active learning.
- [ ] **Prosedur Rollback**: Memiliki mekanisme cadangan untuk melakukan rollback ke model versi sebelumnya jika model baru berkinerja buruk.

---

## 🛠️ 3. Infrastruktur & Observabilitas
- [ ] **Pencadangan Data**: Mengaktifkan skrip backup otomatis berkala untuk database PostgreSQL.
- [ ] **Keamanan Redis**: Redis hanya dapat diakses melalui jaringan internal Docker dan diproteksi kata sandi yang kuat.
- [ ] **Health Checks**: Menambahkan instruksi healthcheck Docker untuk memantau kesehatan database, redis, backend, dan celery worker.
- [x] **Structured Logging**: JSON structured logging telah aktif di `main.py` dengan format kompatibel ELK/Loki.
- [x] **Metrics & Monitoring**: Prometheus metrics (`/metrics`) telah aktif dengan counter request dan histogram latency.
- [x] **Security Headers**: Middleware security headers (HSTS, X-Frame-Options, dll) telah aktif di seluruh response.
- [x] **Request Size Limit**: Middleware pembatasan ukuran body (10MB) telah aktif.
- [ ] **Version Lock**: Mengunci versi Docker base image (`python:3.11-slim` dan `node:20-alpine`) serta versi dependencies di `requirements.txt`.

---

## 🖥️ 4. Kehandalan Frontend
- [ ] **Dinamic Endpoint**: URL backend API tidak boleh *hard-coded*, melainkan dibaca melalui *Vite Environment Variable* (`VITE_API_BASE_URL`).
- [ ] **Error Handling**: Antarmuka web ramah pengguna saat API backend mengalami timeout atau offline.
- [ ] **Otorisasi Dashboard**: Halaman audit dan retrain terlindungi autentikasi admin yang aman.
- [ ] **Optimasi Bundle**: Frontend dibuild menggunakan mode produksi (`npm run build`) untuk meminimalkan ukuran berkas JavaScript.

---

## 👥 5. Etika & Alur Moderasi (Governance)
- [ ] **Disclaimer Penggunaan**: Menampilkan keterangan jelas di UI bahwa klasifikasi model adalah saran awal, bukan keputusan final.
- [ ] **Human-in-the-Loop**: Komentar yang berada pada *confidence margin* (ragu-ragu) wajib diteruskan ke antrean moderasi manusia.
- [ ] **Prosedur Banding**: Menyediakan fitur bagi pengguna untuk meminta peninjauan ulang jika komentar mereka salah ditandai oleh AI.
- [ ] **Anonimisasi**: Menghapus atau menyamarkan nama akun, nomor kontak, dan data sensitif sebelum dianalisis dalam log training model.

---

## ⚠️ 6. Aturan Klaim & Proyeksi Kapabilitas

> [!IMPORTANT]
> Jangan pernah mempromosikan kapabilitas sistem di luar batas bukti empiris yang ada. Gunakan terminologi klasifikasi yang realistis.

| ❌ Hindari Klaim Ini (Overclaim) | | 👍 Gunakan Klaim Ini (Akurat & Kredibel) |
| :--- | :---: | :--- |
| *Enterprise-ready / Production-grade* | ➡️ | Advanced MVP / Research-oriented Prototype |
| *Fully automated zero-human moderation* | ➡️ | Hybrid AI-assisted Human-in-the-loop Moderation |
| *Sub-millisecond real-time at scale* | ➡️ | Multi-Tier hybrid latency optimization (Tier 1-3) |
| *100% accurate toxic detection* | ➡️ | Calibrated statistical and neural classification |

