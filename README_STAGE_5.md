# Stage 5 — Final Integration and Testing

Tahap ini menggabungkan hasil Stage 1 sampai Stage 4 secara aman. Fokusnya bukan menambah fitur baru, tetapi memastikan patch dapat diterapkan, dites, dan jika perlu di-rollback tanpa merusak project utama.

## Tujuan

- Menentukan urutan apply patch yang aman.
- Menyediakan checklist integrasi backend, frontend, Docker, security, dan ML.
- Menyediakan smoke test sederhana untuk API.
- Menyediakan release notes dan pull request template.
- Mengurangi risiko conflict saat patch diterapkan ke repository asli.

## Isi paket

```text
bullyguard_stage5_integration/
├── README_STAGE_5.md
├── STAGE_5_PATCH_NOTES.md
├── docs/
│   ├── FINAL_INTEGRATION_GUIDE.md
│   ├── FINAL_TESTING_CHECKLIST.md
│   ├── APPLY_PATCH_ORDER.md
│   ├── ROLLBACK_PLAN.md
│   ├── RELEASE_NOTES_TEMPLATE.md
│   └── ACCEPTANCE_CRITERIA.md
└── scripts/
    ├── smoke_test_api.sh
    ├── smoke_test_api.ps1
    └── verify_patch_files.sh
```

## Cara pakai cepat

1. Terapkan Stage 1 sampai Stage 4 sesuai urutan.
2. Copy isi paket Stage 5 ke root repository.
3. Jalankan test backend, frontend, dan Docker.
4. Jalankan smoke test API.
5. Buat commit final.

```bash
git checkout -b integration/stage-5-final-testing

# Setelah semua file Stage 1-5 sudah dicopy
git status
git add .
git commit -m "chore: add final integration and testing workflow"
```

## Catatan

Stage 5 tidak mengganti logic aplikasi. File di tahap ini bersifat dokumentasi, checklist, dan script bantu. Jadi risiko merusak aplikasi relatif rendah.
