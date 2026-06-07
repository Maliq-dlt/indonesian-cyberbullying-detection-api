# 🧠 Panduan Kalibrasi Confidence & Threshold (Stage 3) — BullyGuard ID

Panduan ini menjelaskan perubahan logika perhitungan nilai probabilitas (*confidence scoring*), integrasi threshold, serta cara melakukan penyesuaian parameter klasifikasi pada sistem BullyGuard ID.

---

## ⚠️ 1. Masalah yang Diselesaikan pada Stage 3

Sebelum Stage 3 diterapkan, logika klasifikasi mencampuradukkan tiga konsep yang berbeda secara keliru:
1. **Probabilitas Model**: Nilai numerik mentah dari Logistic Regression atau Transformer.
2. **Keputusan Klasifikasi (Decision)**: Status biner (`true`/`false`) jika probabilitas melewati ambang batas (*threshold*).
3. **Routing Confidence (Ambang Ragu-Ragu)**: Menentukan apakah tingkat keyakinan AI cukup kuat untuk berhenti di Tier 1/2, atau wajib naik (*escalate*) ke Tier 3 (LLM).

Hal ini membuat sistem memberikan skor yang tidak realistis (seperti nilai biner `1.0` atau `0.0` dari LLM, atau pemaksaan nilai flat `0.90` jika mendeteksi kecocokan kata kasar pada Lexicon).

---

## 🛠️ 2. Perubahan Logika Utama

### 🤖 A. Keputusan LLM Tidak Lagi Ditulis sebagai Probabilitas Biner (1.0 / 0.0)
- **Sebelumnya**: `probability_toxic = 1.0` jika LLM memprediksi toxic, dan `0.0` jika aman.
- **Sekarang**: Probabilitas dipetakan secara realistis ke dalam rentang sekitar threshold:
  ```python
  probability_toxic = llm_decision_to_probability(is_toxic, threshold_toxic)
  ```
- **Alasan**: LLM menghasilkan keputusan klasifikasi linguistik, bukan probabilitas statistik yang terkalibrasi. Memaksa nilai `1.0` akan merusak akumulasi statistik riwayat.

### 📖 B. Lexicon Matching Tidak Lagi Memaksa Skor Menjadi 0.90 secara Buta
- **Sebelumnya**: Jika kata kasar cocok dengan lexicon, probabilitas langsung dipaksa `0.90`.
- **Sekarang**: Lexicon digunakan sebagai penambah bobot (*boost*) probabilitas model statistik secara adaptif:
  ```python
  final_toxic = apply_lexicon_evidence(final_toxic, lex_res)
  ```
- **Alasan**: Umpatan kasar bisa muncul dalam kutipan laporan korban, candaan, atau pembelajaran. Lexicon menaikkan risiko (*risk factor*), bukan mendikte hasil akhir secara buta.

### ⚖️ C. Normalisasi Bobot Model Ensemble
- Memastikan jumlah total bobot model ensemble bernilai tepat `1.0` sebelum menghitung probabilitas tertimbang (*weighted average*). Hal ini mencegah skor probabilitas melampaui rentang `[0, 1]`.

---

## 🔑 3. Konfigurasi Variabel Lingkungan Baru (.env)

Tambahkan variabel ini pada berkas `.env` Anda untuk mengatur margin toleransi keraguan AI:

```env
# Jarak batas keraguan di sekitar threshold. 
# Jika threshold=0.5 dan margin=0.2, maka area ragu-ragu adalah 0.3 - 0.7.
# Nilai yang lebih besar akan menaikkan lebih banyak kasus ke Tier 2 & 3.
CONFIDENCE_MARGIN=0.20

# Parameter penambah bobot dari kecocokan kamus lexicon
LEXICON_BOOST_LOW=0.05
LEXICON_BOOST_MEDIUM=0.12
LEXICON_BOOST_HIGH=0.20
LEXICON_PROBABILITY_CAP=0.85
```

---

## 🎛️ 4. Cara Melakukan Tuning Threshold

Untuk melatih dan mencari angka threshold klasifikasi terbaik berdasarkan data validasi riil Anda, jalankan skrip evaluator:

```bash
# Menjalankan evaluasi threshold otomatis
python -m cyberbullying_api.classifier.evaluate_thresholds --csv dataset/eval.csv
```

Penyaring evaluator akan membuat rekomendasi nilai threshold optimal. Salin isi berkas output rekomendasi:
`reports/threshold_eval/recommended_thresholds.json`

Dan gantikan nilai parameter pada berkas konfigurasi aktif:
`cyberbullying_api/models/thresholds.json`

**Contoh isi berkas `thresholds.json`:**
```json
{
  "threshold_toxic": 0.48,
  "threshold_bully": 0.52
}
```

---

## 🏁 5. Rekomendasi Narasi (Menghindari Overclaim)

> [!WARNING]
> Sebelum Anda memiliki kurva kalibrasi probabilitas (*Reliability Diagrams*) dan hasil pengujian bias, hindari klaim berikut:
> - *"Skor keyakinan AI telah terkalibrasi sempurna."*
> - *"Model dijamin bebas dari bias kelas sosial / slang daerah."*
> - *"Akurasi deteksi tingkat industri tanpa False Positive."*

