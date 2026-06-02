# Dokumentasi Sistem: Mekanisme dan Rangkuman Deteksi Cyberbullying Indonesia

Dokumen ini menjelaskan arsitektur, pipa normalisasi teks, mekanisme deteksi hibrida (Leksikon, Machine Learning, dan Deep Learning), serta hasil evaluasi performa pada proyek deteksi cyberbullying bahasa Indonesia.

---

## 1. Alur Kerja Sistem (Pipeline)

Sistem ini memproses komentar mentah dari media sosial melalui tahapan berikut untuk menentukan apakah komentar tersebut merupakan tindakan cyberbullying/hate speech:

```
[ Teks Mentah ]
       │
       ▼
┌──────────────────────────────────────────────┐
│  Pipa Normalisasi Teks (Preprocessing)       │
│  - Lowercase, HTML Decode, Unicode Normal    │
│  - Leetspeak Replacement (Angka -> Huruf)    │
│  - Normalisasi Slang & Kamus Singkatan       │
│  - Reduksi Huruf Berulang (Repeated Chars)   │
└──────────────────────────────────────────────┘
       │
       ├──────────────────────────────┬──────────────────────────────┐
       ▼                              ▼                              ▼
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│  Pendekatan  │              │  Pendekatan  │              │  Pendekatan  │
│  Leksikon    │              │  Machine     │              │  Deep        │
│  (Kamus Rule)│              │  Learning    │              │  Learning    │
└──────────────┘              └──────────────┘              └──────────────┘
  - Word Match                 - TF-IDF Feat.                - XLM-RoBERTa
  - Compact Match              - Naive Bayes                 - Self-Attention
  - Severity Weight            - Log Regression              - Contextual
       │                              │                              │
       ▼                              ▼                              ▼
 [ Prediksi Leksikon ]         [ Prediksi ML ]               [ Prediksi DL ]
```

---

## 2. Mekanisme Normalisasi Teks (Preprocessing)

Langkah ini krusial untuk menangani berbagai bentuk kata samaran (*obfuscation*) yang umum digunakan pelaku perundungan agar tidak terdeteksi oleh sistem sensor standar.

### A. Penggantian Leetspeak
Mengubah angka atau simbol yang mirip huruf latin kembali ke karakter aslinya.
* **Tabel Pemetaan Utama**:
  * `0 → o` | `1, !, |, ¡ → i` | `3 → e` | `4, @ → a`
  * `5, $ → s` | `7, + → t` | `8 → b` | `9, 6 → g`
* **Contoh**: `M4ti lu` $\rightarrow$ `mati lu`, `d4s4r` $\rightarrow$ `dasar`.

### B. Normalisasi Slang & Singkatan
Menggunakan pemetaan gabungan dari **15.578 aturan** yang bersumber dari kamus alay (`new_kamusalay.csv`) dan kamus singkatan (`kamus_singkatan.csv`).
* **Contoh Pemetaan**:
  * `gblk` $\rightarrow$ `goblok` | `anjg` $\rightarrow$ `anjing` | `bgsd` $\rightarrow$ `bangsat`
  * `lu` $\rightarrow$ `kamu` | `yg` $\rightarrow$ `yang` | `bgt` $\rightarrow$ `banget`

### C. Reduksi Karakter Berulang
Mengurangi huruf-huruf berulang yang sengaja diketik untuk memberikan penekanan emosi (misalnya: `loooove` $\rightarrow$ `loove` atau `love`).
* **Mekanisme**: Karakter yang berulang lebih dari 2 kali berturut-turut dipotong menjadi maksimal 2 karakter (untuk deteksi normal) atau 1 karakter (untuk pencocokan ketat).
* **Contoh**: `g0bllloook` $\rightarrow$ `goblok`, `b@@@nngs444t` $\rightarrow$ `bangsat`.

---

## 3. Mekanisme Deteksi Leksikon (Rule-Based)

Model leksikon bekerja dengan cara mencocokkan teks yang sudah dinormalisasi dengan kamus cyberbullying yang berisi **139 kata/frasa kasar**. Deteksi dilakukan melalui 3 lapis pencocokan:

1. **`word_or_phrase_match`**: Mencocokkan pola kata setelah dinormalisasi dengan spasi (menggunakan batas kata regex `\b` agar aman dari kesalahan potong kata).
2. **`compact_match`**: Menghapus seluruh spasi dan simbol, lalu mencari apakah kata kasar ada di dalam teks rapat (menangkap variasi seperti `m_a_t_i`).
3. **`compact_repeated_char_match`**: Sama seperti compact match, tetapi karakter berulang dipotong habis menjadi 1 huruf (menangkap variasi seperti `g___o___b___l___o___k`).

### Skor Keparahan & Klasifikasi Risiko:
Setiap kata dalam kamus memiliki bobot keparahan (`tinggi = 3`, `sedang = 2`, `rendah = 1`).
* **Risiko Tinggi**: Jika terdeteksi kata berbobot *tinggi* atau akumulasi skor total $\ge 4$.
* **Risiko Sedang**: Jika akumulasi skor total $\ge 2$.
* **Risiko Rendah**: Jika akumulasi skor total $= 1$.
* **Aman**: Jika tidak ada kata kasar yang cocok.

---

## 4. Mekanisme Machine Learning & Deep Learning

### A. Machine Learning Tradisional (TF-IDF + Classifier)
* **TF-IDF (Term Frequency-Inverse Document Frequency)**: Mengubah teks komentar menjadi matriks numerik berdasarkan frekuensi kata tunggal (unigram) dan pasangan kata (bigram) dengan membatasi maksimal 5.000 fitur terpenting.
* **Naive Bayes (MultinomialNB)**: Menggunakan teorema probabilitas Bayes untuk menghitung peluang suatu dokumen masuk kategori cyberbullying berdasarkan kata penyusunnya. Sangat cepat dan efisien.
* **Logistic Regression**: Menggunakan fungsi sigmoid untuk memodelkan probabilitas cyberbullying berdasarkan kombinasi linier dari bobot kata TF-IDF. Model ini sangat stabil dan mencatatkan hasil terbaik.

### B. Deep Learning (Transformers XLM-RoBERTa)
* **Arsitektur**: Menggunakan model Transformer *state-of-the-art* (`nahiar/hatespeech-abusive-xlm-roberta-v1`).
* **Kelebihan**: Menggunakan mekanisme *self-attention* untuk memetakan hubungan ketergantungan antar kata di dalam satu kalimat secara kontekstual. Mampu mengabaikan kalimat positif yang memiliki kata ambigu (bebas *false positive*), serta membedakan sarkasme murni jika dilatih secara spesifik.

---

## 5. Rangkuman Hasil Evaluasi Metrik Performa

Berikut adalah hasil perbandingan performa klasifikasi semua model saat diuji secara adil di **Test Set** (20% data dari Dataset Kompilasi):

| Model / Pendekatan | Accuracy | Precision | Recall | F1-Score | Karakteristik Utama |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Leksikon Baseline (24 kata)** | 66.43% | **91.11%** | 40.59% | 56.16% | Presisi sangat tinggi, namun Recall rendah (banyak kata kasar lolos). |
| **Leksikon Expanded (139 kata)** | 75.85% | 82.26% | 71.07% | 76.25% | Keseimbangan metrik membaik, deteksi kata kasar meningkat drastis. |
| **Naive Bayes (ML)** | 86.71% | 84.19% | **93.88%** | 88.75% | Sangat sensitif dalam mendeteksi cyberbullying, sangat cepat dilatih. |
| **Logistic Regression (ML)** | **87.92%** | 87.05% | 91.95% | **89.41%** | **Model terbaik secara keseluruhan** dengan tingkat akurasi dan F1 paling stabil. |

### Kesimpulan Metrik:
1. **Leksikon (Rule-Based)**: Sangat baik untuk penanganan instan teks kasar eksplisit. Presisi yang tinggi meminimalisir kesalahan blokir (aman dari memblokir pengguna tidak bersalah), namun recall yang rendah menunjukkan perlunya dukungan AI.
2. **Machine Learning (AI)**: Menawarkan lompatan performa yang masif (F1-score naik ke **89.41%**). Model ini mempelajari konteks kalimat secara statistik sehingga mampu mendeteksi sindiran atau kata toksik yang tidak terdaftar di kamus.
3. **Deep Learning (Transformer)**: Model XLM-RoBERTa sangat akurat dalam membedakan kalimat positif bernada semangat dari ujaran kebencian asli, meskipun sarkasme murni yang tidak menggunakan kata kasar literal masih membutuhkan fine-tuning lebih spesifik.
