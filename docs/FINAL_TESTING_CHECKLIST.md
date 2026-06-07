# Final Testing Checklist

Gunakan checklist ini sebelum merge ke branch utama.

## 1. Repository hygiene

- [ ] Working tree bersih sebelum apply patch.
- [ ] Setiap tahap punya branch sendiri.
- [ ] Setiap tahap punya commit sendiri.
- [ ] Tidak ada secret asli masuk ke Git.
- [ ] `.env` tidak ikut commit.
- [ ] `.env.example` tidak berisi secret production.

## 2. Documentation

- [ ] README tidak overclaim production-grade.
- [ ] README menjelaskan status project sebagai MVP/prototype advanced.
- [ ] Setup lokal bisa diikuti dari awal.
- [ ] Production checklist tersedia.
- [ ] Model evaluation template tersedia.
- [ ] Project positioning jelas.

## 3. Backend security

- [ ] Production/staging wajib `API_KEY`.
- [ ] Protected endpoint menolak request tanpa `X-API-Key`.
- [ ] `/health` tetap public.
- [ ] CORS tidak memakai wildcard di production.
- [ ] Rate limit aktif dengan Redis.
- [ ] Redis failure di production tidak fail-open.
- [ ] Webhook hanya menerima HTTPS di production.
- [ ] Credential database/Redis tidak hard-code untuk production.

## 4. ML confidence

- [ ] `confidence.py` sudah masuk.
- [ ] Unit test confidence lolos.
- [ ] LLM output tidak lagi diberi confidence absolut 1.0/0.0.
- [ ] Lexicon tidak memaksa probability langsung menjadi 0.90.
- [ ] Threshold bisa diatur dari config/env.
- [ ] Script threshold evaluation bisa dijalankan.
- [ ] Error analysis guide tersedia.

## 5. Frontend

- [ ] `Detector.tsx` wrapper tetap menjaga import lama.
- [ ] Folder `Detector/` berisi komponen kecil.
- [ ] `npm run lint` lolos.
- [ ] `npm run build` lolos.
- [ ] Semua mode detector tetap tampil.
- [ ] Fallback saat backend offline tetap bekerja.
- [ ] XAI drawer tetap bekerja.

## 6. Docker

- [ ] `docker compose up -d --build` berhasil.
- [ ] Backend container healthy.
- [ ] Frontend dapat mengakses backend.
- [ ] PostgreSQL dapat connect.
- [ ] Redis dapat connect.
- [ ] Production override dapat berjalan.

## 7. API smoke test

- [ ] `GET /health` return 200.
- [ ] Protected endpoint tanpa API key return 401/403.
- [ ] Protected endpoint dengan API key valid return 200.
- [ ] Prediction endpoint menerima input valid.
- [ ] Prediction endpoint menolak input kosong.
- [ ] Batch endpoint tidak error untuk payload kecil.

## 8. Acceptance

- [ ] Tidak ada crash saat local dev.
- [ ] Tidak ada secret bocor.
- [ ] Dokumentasi cukup untuk user baru menjalankan project.
- [ ] Klaim model belum berlebihan.
- [ ] Risiko utama sudah ditulis jujur di dokumentasi.
