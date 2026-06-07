# Rollback Plan

Rollback penting karena Stage 2-4 menyentuh file runtime.

## Rollback per branch

Jika patch belum merge ke main:

```bash
git checkout main
git branch -D <nama-branch-bermasalah>
```

## Rollback commit terakhir

Jika commit terakhir bermasalah:

```bash
git revert HEAD
```

Jangan gunakan `git reset --hard` jika commit sudah dipush dan dipakai orang lain.

## Rollback Stage 2 security

Gejala umum:

- Endpoint tiba-tiba 401.
- Frontend tidak bisa akses backend.
- CORS error.
- Redis error membuat API gagal.

Langkah cepat:

1. Cek `.env`.
2. Pastikan `API_KEY` sama antara frontend/backend atau curl test.
3. Pastikan `ALLOWED_ORIGINS` sesuai URL frontend.
4. Pastikan Redis container aktif.
5. Jika masih rusak, revert commit Stage 2.

## Rollback Stage 3 ML confidence

Gejala umum:

- Import error `confidence.py`.
- Prediction error karena patch `predictor.py` salah tempel.
- Threshold tidak terbaca.

Langkah cepat:

1. Jalankan `pytest tests/test_confidence.py -q`.
2. Cek import di `predictor.py`.
3. Bandingkan perubahan manual dengan `snippets/PREDICTOR_PATCH.md`.
4. Jika masih rusak, revert hanya patch manual `predictor.py`, bukan seluruh Stage 3.

## Rollback Stage 4 frontend

Gejala umum:

- Build gagal.
- Import path salah.
- UI detector blank.

Langkah cepat:

1. Jalankan `npm run build`.
2. Pastikan `frontend/src/components/Detector.tsx` berisi wrapper default export.
3. Pastikan folder `frontend/src/components/Detector/` ada.
4. Jika masih rusak, restore file lama `Detector.tsx` dari Git.

```bash
git checkout main -- frontend/src/components/Detector.tsx
rm -rf frontend/src/components/Detector
```

## Rollback Docker config

Jika Docker gagal setelah Stage 2:

```bash
docker compose down -v
docker compose up -d --build
```

Jika masih gagal, cek `.env` dan port conflict.
