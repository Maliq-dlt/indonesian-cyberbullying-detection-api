# Apply Patch Order

Gunakan urutan ini agar risiko conflict rendah.

## Urutan aman

### 1. Stage 1 — Documentation and Credibility

Apply dulu karena hampir tidak menyentuh runtime.

File utama:

- `README.md`
- `.env.example`
- `MODEL_EVALUATION.md`
- `docs/LOCAL_SETUP.md`
- `docs/PRODUCTION_CHECKLIST.md`
- `docs/PROJECT_POSITIONING.md`

Commit:

```bash
git checkout -b docs/stage-1-credibility-cleanup
git add README.md .env.example MODEL_EVALUATION.md docs STAGE_1_PATCH_NOTES.md
git commit -m "docs: improve project positioning and evaluation documentation"
```

### 2. Stage 2 — Backend Security

Apply setelah Stage 1 karena memakai `.env.example` yang lebih rapi.

File utama:

- `cyberbullying_api/routes/deps.py`
- `cyberbullying_api/main.py`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `docs/SECURITY_HARDENING.md`

Commit:

```bash
git checkout -b security/stage-2-hardening
git add cyberbullying_api/routes/deps.py cyberbullying_api/main.py docker-compose.yml docker-compose.prod.yml .env.example docs STAGE_2_PATCH_NOTES.md
git commit -m "security: harden API key, rate limiting, CORS, and compose config"
```

### 3. Stage 3 — ML Confidence and Thresholds

Apply setelah security karena beberapa setting threshold masuk ke `.env.example`.

File utama:

- `cyberbullying_api/classifier/confidence.py`
- `cyberbullying_api/classifier/evaluate_thresholds.py`
- `tests/test_confidence.py`
- `docs/ML_CONFIDENCE_GUIDE.md`
- `docs/ERROR_ANALYSIS_GUIDE.md`
- `snippets/PREDICTOR_PATCH.md`

Commit:

```bash
git checkout -b ml/stage-3-confidence-thresholds
git add cyberbullying_api/classifier/confidence.py cyberbullying_api/classifier/evaluate_thresholds.py tests/test_confidence.py docs snippets .env.example.additions STAGE_3_PATCH_NOTES.md README_STAGE_3.md
git commit -m "ml: improve confidence handling and threshold evaluation"
```

Catatan: `PREDICTOR_PATCH.md` harus diterapkan manual ke `predictor.py`. Jangan overwrite seluruh `predictor.py` tanpa review.

### 4. Stage 4 — Frontend Refactor

Apply setelah backend dan ML karena frontend butuh bentuk response API yang stabil.

File utama:

- `frontend/src/components/Detector.tsx`
- `frontend/src/components/Detector/*`
- `docs/FRONTEND_REFACTOR_GUIDE.md`

Commit:

```bash
git checkout -b frontend/stage-4-detector-refactor
git add frontend/src/components/Detector.tsx frontend/src/components/Detector docs/FRONTEND_REFACTOR_GUIDE.md STAGE_4_PATCH_NOTES.md README_STAGE_4.md
git commit -m "frontend: refactor detector component into smaller modules"
```

### 5. Stage 5 — Final Integration

Apply terakhir.

Commit:

```bash
git checkout -b integration/stage-5-final-testing
git add docs scripts README_STAGE_5.md STAGE_5_PATCH_NOTES.md
git commit -m "chore: add final integration and testing workflow"
```

## Strategi merge ke main

Pilihan paling aman:

```bash
git checkout main
git merge docs/stage-1-credibility-cleanup
git merge security/stage-2-hardening
git merge ml/stage-3-confidence-thresholds
git merge frontend/stage-4-detector-refactor
git merge integration/stage-5-final-testing
```

Jika terjadi conflict, selesaikan per tahap. Jangan merge semua sekaligus.
