# Final Integration Guide

Panduan ini dipakai setelah patch Stage 1 sampai Stage 4 disiapkan.

## Prinsip integrasi

1. Jangan langsung overwrite seluruh repository.
2. Apply patch per tahap.
3. Test setelah setiap tahap.
4. Commit kecil dan jelas.
5. Jangan klaim production-ready sebelum acceptance criteria terpenuhi.

## Persiapan lokal

```bash
git clone https://github.com/<username>/<repo>.git
cd <repo>
git status
```

Pastikan working tree bersih:

```bash
git status --short
```

Jika ada perubahan lokal penting:

```bash
git add .
git commit -m "backup: save local changes before integration"
```

## Environment

Buat `.env` dari `.env.example`.

```bash
cp .env.example .env
```

Minimal pastikan variabel ini ada:

```env
ENV=development
API_KEY=change_this_to_a_long_random_secret
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

Untuk production, jangan pakai nilai default.

## Backend test

Dari root repo:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cyberbullying_api/requirements.txt
pytest -q
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r cyberbullying_api\requirements.txt
pytest -q
```

## Frontend test

```bash
cd frontend
npm install
npm run lint
npm run build
npm run dev
```

## Docker test

Development:

```bash
docker compose up -d --build
docker compose ps
curl http://localhost:8000/health
```

Production-like:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
curl http://localhost:8000/health
```

Protected endpoint:

```bash
curl -H "X-API-Key: change_this_to_a_long_random_secret" http://localhost:8000/models/status
```

## Smoke test prediction

Gunakan script:

Linux/macOS/Git Bash:

```bash
bash scripts/smoke_test_api.sh
```

PowerShell:

```powershell
.\scripts\smoke_test_api.ps1
```

## Manual UI test

Cek fitur berikut:

- Input teks pendek.
- Input teks panjang mendekati limit.
- Hybrid AI mode.
- Lexicon/fuzzy mode.
- Machine learning mode.
- Transformer mode.
- Ensemble mode.
- Audit multi-model mode.
- Backend offline fallback.
- XAI drawer.
- Error message saat API key salah.

## Setelah semua aman

```bash
git status
git log --oneline -5
```

Buat tag release internal:

```bash
git tag v0.2.0-hardening-preview
git push origin v0.2.0-hardening-preview
```
