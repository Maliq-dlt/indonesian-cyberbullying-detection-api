# Acceptance Criteria

Project boleh dianggap selesai pada tahap hardening awal jika seluruh kriteria berikut terpenuhi.

## Minimum acceptable state

- README sudah tidak overclaim.
- Setup lokal bisa dijalankan oleh developer baru.
- `.env.example` lengkap dan tidak mengandung secret asli.
- Backend bisa start lokal.
- Frontend bisa build.
- Docker Compose bisa jalan.
- API key bekerja untuk protected endpoint.
- Health endpoint bisa diakses tanpa API key.
- Unit test confidence lolos.
- Detector UI tetap bisa melakukan prediksi.

## Not yet acceptable for production claim

Project belum boleh diklaim production-grade jika salah satu hal ini belum tersedia:

- Laporan evaluasi model dengan dataset jelas.
- Confusion matrix dan error analysis.
- Load test atau latency benchmark.
- Security review untuk deployment publik.
- Secret management yang benar.
- Logging dan monitoring production.
- Backup/restore database.
- Policy handling untuk false positive/false negative.

## Suggested final label

Gunakan label ini:

> Advanced MVP for Indonesian cyberbullying detection with hybrid AI and active learning.

Hindari label ini sampai bukti lengkap tersedia:

> Enterprise-ready production-grade moderation platform.
