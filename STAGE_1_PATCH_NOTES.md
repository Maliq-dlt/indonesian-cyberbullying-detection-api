# Stage 1 Patch Notes — Documentation & Credibility Cleanup

## File yang ditambahkan / diganti

1. `README.md`
   - Menurunkan klaim dari production-grade menjadi advanced MVP / research-oriented prototype.
   - Memperbaiki struktur dokumentasi.
   - Memperbaiki command virtualenv Windows.
   - Menambahkan batasan sistem, keamanan, roadmap, dan disclaimer.

2. `.env.example`
   - Menyediakan contoh konfigurasi environment.
   - Membantu menghindari hard-code credential di masa depan.

3. `MODEL_EVALUATION.md`
   - Template laporan evaluasi model.
   - Memaksa pembuktian kualitas model dengan metrik lengkap.

4. `docs/LOCAL_SETUP.md`
   - Panduan setup lokal lebih rinci.

5. `docs/PRODUCTION_CHECKLIST.md`
   - Checklist sebelum project diklaim production-ready.

6. `docs/PROJECT_POSITIONING.md`
   - Panduan narasi project agar lebih kredibel.

## Command commit yang disarankan

```bash
git checkout -b docs/stage-1-credibility-cleanup

# salin file dari paket ini ke root repository Anda

git add README.md .env.example MODEL_EVALUATION.md docs/LOCAL_SETUP.md docs/PRODUCTION_CHECKLIST.md docs/PROJECT_POSITIONING.md
git commit -m "docs: improve project positioning and evaluation documentation"
git push origin docs/stage-1-credibility-cleanup
```

## Catatan

Tahap 1 tidak mengubah logic backend, frontend, model, atau Docker Compose. Fokusnya adalah memperbaiki kredibilitas dokumentasi dan menyiapkan fondasi untuk evaluasi model.
