# Model Evaluation Report — BullyGuard ID

Dokumen ini digunakan untuk membuktikan kualitas model secara transparan. Jangan hanya menampilkan angka F1 tunggal. Untuk sistem deteksi cyberbullying, yang penting adalah performa per kelas, jenis kesalahan, dan batasan model.

> Status: template awal. Isi angka dan hasil aktual setelah evaluasi dilakukan ulang pada dataset yang jelas.

---

## 1. Ringkasan Model

| Item | Keterangan |
|---|---|
| Nama sistem | BullyGuard ID |
| Bahasa utama | Indonesia |
| Tugas | Deteksi toxic / cyberbullying / hate speech |
| Model Tier 1 | TF-IDF + Logistic Regression + Lexicon |
| Model Tier 2 | Transformer / XLM-RoBERTa / ONNX, jika tersedia |
| Model Tier 3 | LLM lokal + RAG few-shot, opsional |
| Tanggal evaluasi | TODO |
| Evaluator | TODO |
| Versi commit | TODO |

---

## 2. Dataset

| Item | Nilai |
|---|---:|
| Total data | TODO |
| Data train | TODO |
| Data validation | TODO |
| Data test | TODO |
| Jumlah label toxic | TODO |
| Jumlah label non-toxic | TODO |
| Jumlah label bully | TODO |
| Jumlah label non-bully | TODO |
| Sumber dataset | TODO |
| Tanggal pengambilan dataset | TODO |

### Catatan sumber data

Jelaskan sumber dataset secara jujur:

- Apakah berasal dari dataset publik?
- Apakah hasil scraping?
- Apakah sudah dianonimkan?
- Apakah ada data pribadi?
- Apakah ada proses deduplikasi?
- Apakah ada data yang berpotensi sensitif?

---

## 3. Definisi Label

### Toxic

Tuliskan definisi operasional toxic.

Contoh:

> Komentar toxic adalah komentar yang mengandung penghinaan, kata kasar agresif, ancaman, pelecehan, atau ekspresi merendahkan yang berpotensi mengganggu keamanan percakapan.

### Cyberbullying

Tuliskan definisi operasional cyberbullying.

Contoh:

> Cyberbullying adalah komentar yang menyerang, mempermalukan, mengintimidasi, mengancam, atau melecehkan target tertentu secara personal atau kelompok.

### Non-toxic

Tuliskan definisi komentar aman.

### Ambiguous / butuh validasi

Tuliskan kriteria kasus ambigu, misalnya:

- sarkasme,
- candaan antar teman,
- kutipan kata kasar,
- komentar edukatif yang membahas kata kasar,
- komentar tanpa konteks percakapan.

---

## 4. Metode Eksperimen

| Komponen | Keterangan |
|---|---|
| Split method | TODO: random stratified / time-based / manual split |
| Preprocessing | TODO |
| Vectorizer | TODO |
| Model baseline | TODO |
| Model final | TODO |
| Threshold | TODO |
| Calibration method | TODO |
| Random seed | TODO |

### Catatan penting

Jika data berasal dari scraping berurutan, pertimbangkan split berbasis waktu. Random split bisa membuat hasil terlihat terlalu bagus jika komentar yang mirip muncul di train dan test.

---

## 5. Hasil Evaluasi Utama

### Toxic classification

| Metric | Nilai |
|---|---:|
| Accuracy | TODO |
| Precision toxic | TODO |
| Recall toxic | TODO |
| F1 toxic | TODO |
| Precision non-toxic | TODO |
| Recall non-toxic | TODO |
| F1 non-toxic | TODO |
| Macro F1 | TODO |
| Weighted F1 | TODO |

### Bully classification

| Metric | Nilai |
|---|---:|
| Accuracy | TODO |
| Precision bully | TODO |
| Recall bully | TODO |
| F1 bully | TODO |
| Precision non-bully | TODO |
| Recall non-bully | TODO |
| F1 non-bully | TODO |
| Macro F1 | TODO |
| Weighted F1 | TODO |

---

## 6. Confusion Matrix

### Toxic classification

| Actual \ Predicted | Non-toxic | Toxic |
|---|---:|---:|
| Non-toxic | TODO | TODO |
| Toxic | TODO | TODO |

### Bully classification

| Actual \ Predicted | Non-bully | Bully |
|---|---:|---:|
| Non-bully | TODO | TODO |
| Bully | TODO | TODO |

---

## 7. Threshold Analysis

Jelaskan bagaimana threshold dipilih.

| Threshold | Precision | Recall | F1 | Catatan |
|---:|---:|---:|---:|---|
| 0.30 | TODO | TODO | TODO | TODO |
| 0.40 | TODO | TODO | TODO | TODO |
| 0.50 | TODO | TODO | TODO | TODO |
| 0.60 | TODO | TODO | TODO | TODO |
| 0.70 | TODO | TODO | TODO | TODO |

Catatan:

- Jika recall terlalu rendah, banyak komentar berbahaya lolos.
- Jika precision terlalu rendah, banyak komentar aman ditandai berbahaya.
- Untuk moderasi, threshold bisa berbeda antara screening awal dan tindakan final.

---

## 8. Error Analysis

Jangan tampilkan data pribadi. Anonimkan nama, username, nomor, dan informasi sensitif.

### False Positive

Komentar aman yang salah dianggap toxic/bully.

| No | Contoh anonim | Prediksi | Label benar | Dugaan penyebab |
|---:|---|---|---|---|
| 1 | TODO | TODO | TODO | TODO |
| 2 | TODO | TODO | TODO | TODO |
| 3 | TODO | TODO | TODO | TODO |

### False Negative

Komentar toxic/bully yang lolos sebagai aman.

| No | Contoh anonim | Prediksi | Label benar | Dugaan penyebab |
|---:|---|---|---|---|
| 1 | TODO | TODO | TODO | TODO |
| 2 | TODO | TODO | TODO | TODO |
| 3 | TODO | TODO | TODO | TODO |

---

## 9. Analisis Kasus Khusus Bahasa Indonesia

Isi hasil pengamatan untuk kategori berikut:

| Kategori | Performa | Catatan |
|---|---|---|
| Slang / alay | TODO | TODO |
| Bahasa daerah | TODO | TODO |
| Sarkasme | TODO | TODO |
| Kata kasar dalam candaan | TODO | TODO |
| Kutipan kata kasar | TODO | TODO |
| Kritik keras tapi valid | TODO | TODO |
| Ancaman implisit | TODO | TODO |
| Body shaming | TODO | TODO |
| Hate speech identitas | TODO | TODO |

---

## 10. Evaluasi Hybrid Routing

| Tier | Jumlah sampel | Akurasi | Avg latency | Catatan |
|---|---:|---:|---:|---|
| Tier 1: ML + Lexicon | TODO | TODO | TODO | TODO |
| Tier 2: Transformer | TODO | TODO | TODO | TODO |
| Tier 3: LLM | TODO | TODO | TODO | TODO |

Pertanyaan yang harus dijawab:

- Berapa persen komentar selesai di Tier 1?
- Berapa persen naik ke Transformer?
- Berapa persen naik ke LLM?
- Apakah Tier 2/3 benar-benar memperbaiki hasil atau hanya menambah latency?
- Apakah confidence antar-tier sudah dikalibrasi?

---

## 11. Latency dan Resource

| Skenario | Avg latency | P95 latency | Memory | Catatan |
|---|---:|---:|---:|---|
| Single prediction Tier 1 | TODO | TODO | TODO | TODO |
| Single prediction Transformer | TODO | TODO | TODO | TODO |
| Single prediction LLM | TODO | TODO | TODO | TODO |
| Batch prediction 10 teks | TODO | TODO | TODO | TODO |
| Batch prediction 100 teks | TODO | TODO | TODO | TODO |

---

## 12. Kesimpulan Evaluasi

Tuliskan kesimpulan dengan jujur.

Contoh format:

> Berdasarkan evaluasi pada test set berjumlah TODO data, model menunjukkan performa yang cukup baik untuk screening awal, tetapi belum layak digunakan sebagai satu-satunya dasar moderasi otomatis. Kesalahan paling sering terjadi pada TODO. Untuk deployment production, diperlukan TODO.

---

## 13. Rekomendasi Lanjutan

- [ ] Tambahkan dataset lebih seimbang.
- [ ] Buat test set yang tidak ikut active learning.
- [ ] Kalibrasi probabilitas model.
- [ ] Pisahkan threshold untuk toxic dan bully.
- [ ] Tambahkan evaluasi bahasa daerah/slang.
- [ ] Tambahkan manual review untuk confidence rendah.
- [ ] Tambahkan fairness dan bias review.
- [ ] Tambahkan benchmark latency.
