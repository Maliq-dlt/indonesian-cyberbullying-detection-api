# 🎯 Acceptance Criteria — BullyGuard ID

Proyek ini dianggap berhasil menyelesaikan tahapan peningkatan keamanan awal (*initial hardening*) jika seluruh kriteria penerimaan (*acceptance criteria*) berikut terpenuhi secara lengkap.

---

## 🟢 1. Kriteria Penerimaan Minimum (Minimum Acceptable State)

Sistem wajib memenuhi kondisi operasional dasar berikut sebelum diserahkan ke pengguna:
- [x] **Dokumentasi Realistis**: Berkas `README.md` telah dibersihkan dari klaim berlebihan (*overclaim*).
- [x] **Panduan Setup**: Panduan setup lokal (`docs/LOCAL_SETUP.md`) dapat dipahami dan dijalankan dengan mudah oleh penguji.
- [x] **Integritas Variabel Lingkungan**: File `.env.example` lengkap dengan instruksi rahasia tanpa membocorkan token asli.
- [x] **Kestabilan Backend**: Server backend FastAPI dapat dijalankan di lokal dengan normal.
- [x] **Kestabilan Frontend**: Frontend React + Vite sukses dibuild tanpa error linter.
- [x] **Orkestrasi Docker**: Seluruh stack (API, database, Redis, Celery, UI) dapat dihidupkan melalui `docker compose up`.
- [x] **Proteksi API**: Endpoint terproteksi menolak request yang tidak menyertakan API Key yang valid (mengembalikan status `401 Unauthorized`).
- [x] **Unit Testing Lolos**: Semua unit test backend (termasuk modul evaluasi confidence) lulus dengan sukses.
- [x] **Integrasi UI & API**: Form input deteksi pada antarmuka web sukses menampilkan hasil prediksi dari backend.

---

## ⚠️ 2. Kriteria Penerimaan Produksi (Production Claim Policy)

> [!WARNING]
> Proyek **tidak boleh** diposisikan sebagai platform produksi skala perusahaan (*Enterprise-Grade*) selama poin-poin berikut belum diselesaikan:

- [ ] **Laporan Pengujian Model**: Mengisi laporan benchmarking model secara lengkap dengan metrik yang valid di berkas `MODEL_EVALUATION.md`.
- [ ] **Studi Kasus Kesalahan**: Menyertakan tabel contoh *False Positive* dan *False Negative* yang dianonimkan.
- [ ] **Pengujian Beban (Load Test)**: Memiliki hasil uji latensi dan kapasitas beban request simultan (menggunakan K6 atau Locust).
- [ ] **Sistem Logging Terpusat**: Implementasi monitoring log performa, pelacakan error, dan monitoring kesehatan server Redis/Database.
- [ ] **Prosedur Pemulihan**: Memiliki panduan backup database PostgreSQL dan skema rollback model AI yang aman.

---

## 🏷️ 3. Rekomendasi Label Penamaan Proyek

> [!TIP]
> **Gunakan Penamaan Ini:**  
> *"Advanced MVP for Indonesian Cyberbullying Detection with Hybrid AI and Active Learning."*

> [!CAUTION]
> **Hindari Penamaan Ini (Hingga Bukti Skala Besar Tersedia):**  
> *"Enterprise-ready production-grade automated moderation platform."*

