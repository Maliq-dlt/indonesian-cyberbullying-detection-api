# 📈 Model Evaluation Report — BullyGuard ID

Dokumen ini berfungsi sebagai laporan resmi pengujian dan pembuktian kualitas model secara transparan. Untuk sistem deteksi cyberbullying berbahasa Indonesia, performa detail per kelas, tipe kesalahan (*error analysis*), serta batasan operasional model jauh lebih penting daripada sekadar angka F1-score rata-rata.

> [!NOTE]
> **Status Dokumen**: `Template Evaluasi / Draf Awal`  
> Isi metrik, jumlah dataset, dan hasil tabel di bawah ini harus diperbarui setelah Anda menjalankan skrip pengujian model pada dataset validasi utama Anda.

---

## 🔍 1. Ringkasan Model

Tabel di bawah ini merangkum spesifikasi umum dari sistem klasifikasi hybrid yang diuji:

| Parameter / Item | Keterangan Teknis |
| :--- | :--- |
| **Nama Sistem** | BullyGuard ID |
| **Bahasa Utama** | Bahasa Indonesia (termasuk gaul, slang, alay) |
| **Tugas Utama** | Multi-label klasifikasi (Toxic, Cyberbullying, Aman) |
| **Model Tier 1** | TF-IDF + Logistic Regression + Lexicon Matcher |
| **Model Tier 2** | Deep Learning XLM-RoBERTa (Format ONNX Runtime) |
| **Model Tier 3** | Large Language Model (Cloud LLM) (OpenCode Go API) |
| **Tanggal Evaluasi** | *Belum Ditentukan (TODO)* |
| **Petugas Evaluator** | *Belum Ditentukan (TODO)* |
| **Versi Commit Git** | *Belum Ditentukan (TODO)* |

---

## 📊 2. Dataset Pengujian

Statistik dataset yang digunakan untuk melatih dan mengevaluasi performa model:

| Jenis Data / Label | Jumlah Sampel | Persentase | Sumber / Catatan |
| :--- | :---: | :---: | :--- |
| **Total Data** | *TODO* | 100% | Gabungan dataset publik & scraping |
| **Data Train (Latih)** | *TODO* | *TODO*% | Digunakan untuk pelatihan model statistik/ML |
| **Data Validation** | *TODO* | *TODO*% | Digunakan untuk tuning threshold |
| **Data Test (Uji)** | *TODO* | *TODO*% | Evaluasi akhir performa *out-of-sample* |
| **Label Toxic** | *TODO* | *TODO*% | Kalimat mengandung kata kasar/abusive |
| **Label Cyberbullying** | *TODO* | *TODO*% | Kalimat pelecehan verbal personal/grup |
| **Label Aman (Clean)** | *TODO* | *TODO*% | Kalimat percakapan netral/positif |

### 📝 Catatan Integritas Sumber Data
- **Scraping & Publik**: Apakah data bersumber dari media sosial publik (Twitter/X, Instagram, TikTok)?
- **Anonimisasi**: Semua data uji wajib disamarkan (menghapus nama akun asli, nomor HP, email) sebelum didokumentasikan.
- **Deduplikasi**: Pastikan data duplikat hasil repost/retweet telah dibersihkan agar tidak mendistorsi hasil akurasi.

---

## 🏷️ 3. Definisi Operasional Label

Untuk menyamakan persepsi pelabelan manusia (*human annotators*) dengan model AI:

### 🔴 A. Toxic
Komentar yang mengekspresikan kekasaran, kata-kata kotor/abusive (*profanity*), makian umum, atau sarkasme tajam yang berpotensi menurunkan kualitas kesopanan komunikasi, meskipun tidak diarahkan untuk mengintimidasi individu tertentu.
> **Contoh**: *"Aduh bego banget sih nih server lemot terus!"*

### ❌ B. Cyberbullying
Tindakan pelecehan verbal terarah yang menyerang, mengintimidasi, merendahkan, melakukan *body shaming*, atau mengancam secara berulang/personal terhadap individu atau kelompok tertentu.
> **Contoh**: *"Muka lu jelek banget, gak layak hidup lu mending hilang aja!"*

### 🟢 C. Aman (Non-Toxic & Non-Bullying)
Kalimat opini, kritik yang membangun, komentar informatif, atau ekspresi santun yang tidak mengandung unsur kekerasan verbal.
> **Contoh**: *"Mohon maaf, sistem ini sepertinya masih memiliki bug di bagian login."*

### ⚠️ D. Kasus Ambigu (Butuh Tinjauan Moderator)
Kalimat-kalimat abu-abu seperti sarkasme halus, kutipan (*quoting*) kata kasar untuk tujuan edukasi, atau istilah kasar yang digunakan sebagai keakraban antar teman (*casual banter/swearing*).

---

## 🧪 4. Metode Eksperimen & Validasi

| Komponen Eksperimen | Metode yang Digunakan |
| :--- | :--- |
| **Metode Split** | `Stratified K-Fold` / `Time-based Split` (Disarankan jika data berurutan) |
| **Tahapan Preprocessing** | Case folding, cleansing (non-alphanumeric), formalisasi slang/alay |
| **Model Baseline** | Naive Bayes / TF-IDF + Logistic Regression |
| **Parameter Threshold** | Diatur dinamis melalui file `thresholds.json` |
| **Metode Kalibrasi** | Platt Scaling / CalibratedClassifierCV |

> [!TIP]
> **Penting untuk Pengujian**:  
> Selalu pisahkan dataset uji secara ketat. Jika model Anda sering dilatih ulang dengan *Active Learning*, simpan sebuah test set statis yang **tidak pernah** dilihat oleh model untuk memantau terjadinya degradasi performa (*model drift*).

---

## 📈 5. Hasil Evaluasi Utama

### 1. Klasifikasi Toxic (Biner/Multi-class)

| Metrik Evaluasi | Kelas: Aman | Kelas: Toxic | Macro Avg | Weighted Avg |
| :--- | :---: | :---: | :---: | :---: |
| **Precision** | *TODO* | *TODO* | *TODO* | *TODO* |
| **Recall** | *TODO* | *TODO* | *TODO* | *TODO* |
| **F1-Score** | *TODO* | *TODO* | *TODO* | *TODO* |
| **Akurasi Keseluruhan** | | | **TODO** | |

### 2. Klasifikasi Cyberbullying

| Metrik Evaluasi | Kelas: Aman | Kelas: Bully | Macro Avg | Weighted Avg |
| :--- | :---: | :---: | :---: | :---: |
| **Precision** | *TODO* | *TODO* | *TODO* | *TODO* |
| **Recall** | *TODO* | *TODO* | *TODO* | *TODO* |
| **F1-Score** | *TODO* | *TODO* | *TODO* | *TODO* |
| **Akurasi Keseluruhan** | | | **TODO** | |

---

## 🔀 6. Confusion Matrix

Membantu melihat kelas mana yang sering tertukar oleh model.

### Matrix: Deteksi Toxic
| Aktual \ Prediksi | Aman (Non-Toxic) | Terdeteksi Toxic |
| :--- | :---: | :---: |
| **Aman (Non-Toxic)** | *TODO (True Negative)* | *TODO (False Positive)* |
| **Toxic** | *TODO (False Negative)* | *TODO (True Positive)* |

### Matrix: Deteksi Cyberbullying
| Aktual \ Prediksi | Aman (Non-Bully) | Terdeteksi Bully |
| :--- | :---: | :---: |
| **Aman (Non-Bully)** | *TODO (True Negative)* | *TODO (False Positive)* |
| **Bully** | *TODO (False Negative)* | *TODO (True Positive)* |

---

## 🎛️ 7. Analisis Threshold & Kalibrasi

Penentuan *threshold* (ambang batas) probabilitas untuk menentukan label biner sangat krusial dalam sistem moderasi.

| Nilai Threshold | Precision (Toxic) | Recall (Toxic) | F1-Score | Dampak Operasional / Tindakan |
| :---: | :---: | :---: | :---: | :--- |
| **0.30** | *TODO* | *TODO* | *TODO* | Sangat sensitif, banyak *false alarm*, menyaring ketat. |
| **0.50** | *TODO* | *TODO* | *TODO* | Standar default, seimbang. |
| **0.70** | *TODO* | *TODO* | *TODO* | Konservatif, meloloskan komentar jika AI kurang yakin. |

> [!WARNING]
> Menurunkan threshold meningkatkan **Recall** (sedikit konten lolos) namun menurunkan **Precision** (banyak komentar bersih terblokir). Pilihlah threshold yang sesuai dengan kebijakan moderasi platform Anda.

---

## 🔀 8. Analisis Kesalahan (Error Analysis)

Studi kasus mendalam terhadap sampel data uji yang gagal diklasifikasikan dengan benar oleh model:

### 🔴 False Positive (Salah Blokir)
*Komentar bersih/aman yang dideteksi sebagai toxic/bullying.*

| No | Teks Sampel (Disamarkan) | Prediksi AI | Label Asli | Analisis Penyebab Kesalahan |
| :---: | :--- | :---: | :---: | :--- |
| 1 | *"Buku ini mengajarkan kita untuk tidak bego menghadapi penipu."* | Toxic | Aman | AI mendeteksi kata "bego" tanpa memahami konteks edukasi kalimat. |
| 2 | *TODO* | *TODO* | *TODO* | *TODO* |

### 🔵 False Negative (Kebocoran Konten)
*Komentar berbahaya/cyberbullying yang lolos sebagai aman.*

| No | Teks Sampel (Disamarkan) | Prediksi AI | Label Asli | Analisis Penyebab Kesalahan |
| :---: | :--- | :---: | :---: | :--- |
| 1 | *"Semoga karirmu hancur ya, dasar orang ga berguna."* | Aman | Bully | Sarkasme halus tanpa kata umpatan eksplisit gagal dideteksi ML klasik. |
| 2 | *TODO* | *TODO* | *TODO* | *TODO* |

---

## 🇮🇩 9. Analisis Kasus Spesifik Bahasa Indonesia

| Karakteristik Linguistik | Performa Model | Catatan / Strategi Perbaikan |
| :--- | :---: | :--- |
| **Bahasa Gaul / Slang / Singkatan** | Cukup Baik | Perlu terus memperbarui kamus slang `dataset/colloquial-indonesian-lexicon.csv` |
| **Bahasa Daerah (Jawa, Sunda, dll.)** | Kurang | Model saat ini didominasi bahasa Indonesia formal & gaul Jakarta |
| **Sarkasme & Ironi** | Lemah | Memerlukan Tier 3 (LLM) untuk memahami konteks implisit secara utuh |
| **Plesetan Kata Kasar (Obfuscation)**| Sedang | Dibantu modul *fuzzy matching* pada lexicon |

---

## 🔀 10. Evaluasi Efisiensi Hybrid Routing

Menghitung performa dan penghematan biaya/waktu berkat mekanisme Multi-Tier Routing:

| Lapisan Klasifikasi (Tier) | Volume Request | Rata-rata Latensi | Akurasi Mandiri |
| :--- | :---: | :---: | :---: |
| **Tier 1: ML Statistik & Lexicon** | *TODO* % | ~2-5 ms | *TODO*% |
| **Tier 2: Transformer ONNX (CPU)** | *TODO* % | ~50-120 ms | *TODO*% |
| **Tier 3: Cloud LLM (OpenCode Go API)** | *TODO* % | ~800-2500 ms | *TODO*% |

*Pertanyaan Kunci:*
- Berapa persen trafik request yang berhasil diselesaikan langsung pada **Tier 1** tanpa naik ke **Tier 2**? (Target: >70%)
- Berapa banyak latensi rata-rata yang berhasil dihemat melalui skema ini?

---

## ⚡ 11. Latensi & Konsumsi Sumber Daya

| Skenario Pengujian | Rata-rata Latensi (ms) | Latensi P95 (ms) | RAM / Memory |
| :--- | :---: | :---: | :---: |
| **Prediksi Tunggal (Tier 1)** | *TODO* | *TODO* | *TODO* |
| **Prediksi Tunggal (Tier 2)** | *TODO* | *TODO* | *TODO* |
| **Prediksi Tunggal (Tier 3)** | *TODO* | *TODO* | *TODO* |
| **Batch 10 Kalimat Sekaligus** | *TODO* | *TODO* | *TODO* |

---

## 🏁 12. Kesimpulan Evaluasi

> [!IMPORTANT]
> **Kesimpulan Akhir**: *[Isi dengan narasi ringkas]*  
> Berdasarkan hasil uji coba pada dataset sebanyak **TODO** sampel, BullyGuard ID versi MVP ini menunjukkan performa akurasi **TODO%** untuk deteksi toxic umum. Namun, untuk kasus pelecehan terarah dan sarkasme, sistem masih memerlukan pengawasan manusia (*Human-in-the-Loop*).

---

## 🛠️ 13. Rekomendasi Pengembangan Model
- [ ] Meningkatkan variasi dataset latih dengan memasukkan kata-kata makian daerah.
- [ ] Melakukan kalibrasi probabilitas Logistic Regression menggunakan *Platt Scaling* agar skor confidence lebih akurat.
- [ ] Mengaktifkan *Active Learning retraining pipeline* secara berkala setelah audit komentar terkumpul >500 entri.
- [ ] Memisahkan ambang batas (*threshold*) klasifikasi untuk label `toxic` dan `bully` demi fleksibilitas aturan moderasi.
