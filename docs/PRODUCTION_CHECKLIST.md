# Production Readiness Checklist — BullyGuard ID

Project ini belum boleh diklaim production-ready penuh sebelum daftar berikut dipenuhi.

---

## 1. Keamanan

- [ ] API key wajib di production.
- [ ] Tidak ada credential default di Docker Compose production.
- [ ] `.env` tidak masuk Git.
- [ ] CORS dibatasi ke domain resmi.
- [ ] HTTPS aktif melalui reverse proxy.
- [ ] Endpoint admin dilindungi autentikasi yang lebih kuat.
- [ ] Webhook menggunakan allowlist domain atau signature verification.
- [ ] Rate limit tetap aman ketika Redis bermasalah.
- [ ] Log tidak menyimpan data sensitif mentah tanpa kebutuhan jelas.

---

## 2. Model dan Data

- [ ] Dataset terdokumentasi.
- [ ] Distribusi label jelas.
- [ ] Train/validation/test split jelas.
- [ ] Confusion matrix tersedia.
- [ ] Precision, recall, dan F1 per label tersedia.
- [ ] Error analysis tersedia.
- [ ] Threshold dipilih berdasarkan validation set.
- [ ] Test set tidak tercampur dengan data active learning.
- [ ] Ada prosedur rollback model.

---

## 3. Infrastruktur

- [ ] Database memakai backup otomatis.
- [ ] Redis memakai password kuat atau network internal.
- [ ] Health check tersedia untuk API, DB, Redis, dan worker.
- [ ] Structured logging aktif.
- [ ] Monitoring CPU, memory, latency, dan error rate aktif.
- [ ] Docker image dikunci versinya.
- [ ] Dependency dikunci dengan versi yang lebih deterministik.

---

## 4. Frontend

- [ ] URL API tidak hard-coded.
- [ ] Error message aman dan tidak membocorkan detail backend.
- [ ] Halaman admin tidak bisa diakses tanpa otorisasi.
- [ ] Build production sukses.
- [ ] UI menangani API timeout dan error.

---

## 5. Moderasi dan Etika

- [ ] Ada disclaimer bahwa prediksi bukan keputusan final.
- [ ] Ada manual review untuk kasus confidence rendah.
- [ ] Ada prosedur banding atau koreksi label.
- [ ] Data pribadi dianonimkan.
- [ ] Contoh komentar sensitif tidak ditampilkan sembarangan di demo publik.

---

## 6. Klaim yang Baru Aman Dipakai Setelah Terbukti

Jangan gunakan klaim berikut sebelum ada benchmark:

- production-grade,
- enterprise-ready,
- sub-millisecond,
- high accuracy tanpa angka evaluasi lengkap,
- fully automated moderation,
- real-time at scale.

Klaim yang lebih aman:

- advanced MVP,
- research-oriented prototype,
- hybrid AI-assisted moderation system,
- human-in-the-loop moderation support,
- Indonesian-language cyberbullying detection API.
