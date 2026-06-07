# 🔍 Panduan Analisis Kesalahan (Error Analysis Guide) — BullyGuard ID

Model deteksi cyberbullying tidak boleh dinilai dari nilai rata-rata F1-score semata. Dalam sistem moderasi konten nyata, kesalahan memiliki risiko asimetris yang memerlukan penanganan yang berbeda:
- **False Positive (Salah Blokir)**: Kalimat aman ditandai sebagai toxic/bullying. Menyebabkan pengguna frustrasi karena disensor secara tidak adil.
- **False Negative (Kebocoran Konten)**: Kalimat kasar/bullying lolos dan tidak terdeteksi. Mengurangi rasa aman dalam platform digital.

---

## 📊 1. Struktur Pengumpulan Data Kesalahan

Untuk melakukan analisis secara sistematis, buat berkas spreadsheet atau CSV berisi data salah klasifikasi dengan struktur kolom berikut:

```csv
id,text,true_toxic,true_bully,pred_toxic,pred_bully,prob_toxic,prob_bully,error_type,notes
```

---

## 🏷️ 2. Kategorisasi Jenis Kesalahan

Kelompokkan kasus-kasus yang gagal diidentifikasi oleh AI ke dalam kategori linguistik berikut:

| Kategori | Definisi Linguistik | Contoh Kasus |
| :--- | :--- | :--- |
| **`direct_insult`** | Penghinaan langsung ke subjek/objek | *"Kamu bodoh sekali."* |
| **`profanity_no_target`** | Kata kotor yang dilemparkan tanpa target | *"Sialan, macet banget!"* |
| **`sarcasm`** | Arti sesungguhnya berlawanan dari kata yang ditulis | *"Wah, pintar sekali kamu sampai tidak lulus."* |
| **`quote_or_report`** | Pengguna mengutip hinaan orang lain / melaporkan kasus | *"Dia kemarin memanggil saya 'anjing'."* |
| **`slang_or_alay`** | Kata plesetan, singkatan gaul, atau variasi alay | *"L0 b3g0 b9t s1h"* |
| **`identity_attack`** | Serangan kebencian terhadap SARA/identitas sosial | Serangan rasial/agama tanpa kata umpatan kasar |
| **`threat`** | Intimidasi fisik, doxxing, atau ancaman kekerasan | *"Tunggu lu di rumah, gw habisin lu."* |
| **`non_bullying_negative`** | Kalimat sentimen negatif netral (bukan bullying) | *"Saya sangat kecewa dengan layanan Anda."* |

---

## 📋 3. Daftar Evaluasi Kesalahan (Checklist)

### 🔴 Pengujian False Positive (Aman dideteksi Kasar)
Saat menganalisis kasus di mana model menandai teks bersih sebagai berbahaya, ajukan pertanyaan-pertanyaan berikut:
1. **Apakah kata kasar tersebut diarahkan ke orang tertentu?** (Makian tanpa target tidak selalu bullying).
2. **Apakah pengguna sedang mengutip perkataan orang lain?** (Membahas bullying bukan tindakan melakukan bullying).
3. **Apakah teks tersebut memiliki konteks edukasi atau berita?** (Artikel ilmiah tentang umpatan).
4. **Apakah ini ekspresi kesal pada diri sendiri?** (*"Aduh saya bodoh banget"*).
5. **Apakah kalimat tersebut merupakan candaan santai antar-teman akrab?** (*"Woi kampret ke mana aja lu"*).

### 🔵 Pengujian False Negative (Kasar dideteksi Aman)
Saat menganalisis kasus di mana model meloloskan teks berbahaya sebagai aman, ajukan pertanyaan-pertanyaan berikut:
1. **Apakah ada modifikasi karakter huruf/angka?** (Modifikasi leet-speak untuk mengelabui filter).
2. **Apakah kalimat tersebut bernada sarkasme tertutup?** (Ujaran merendahkan yang dibungkus kata sopan).
3. **Apakah menggunakan percampuran bahasa gaul daerah atau bahasa Inggris?** (*"You are so stupid tapi pura-pura smart"*).
4. **Apakah pelecehan bersifat implisit/halus?** (*"Semoga kamu cepat dipanggil Yang Maha Kuasa ya"*).

---

## 📝 4. Rekomendasi Integrasi Laporan

Setiap kali Anda selesai melakukan *tuning threshold* atau *retraining model*, tambahkan tabel ringkasan analisis kesalahan pada berkas [`MODEL_EVALUATION.md`](../MODEL_EVALUATION.md):

```markdown
### Kasus False Positive Terpilih
| Teks Uji | Label Aktual | Prediksi AI | Penyebab | Solusi Perbaikan |
| :--- | :---: | :---: | :--- | :--- |
| *"Pelayanannya payah, saya kapok."* | Aman | Toxic | Sentimen negatif kuat | Tambahkan contoh review produk negatif yang aman |

### Kasus False Negative Terpilih
| Teks Uji | Label Aktual | Prediksi AI | Penyebab | Solusi Perbaikan |
| :--- | :---: | :---: | :--- | :--- |
| *"Muka pas-pasan ga usah sok gaya."* | Bully | Aman | Body shaming implisit | Tambahkan variasi ejekan fisik ke training set |
```

---

## 🛡️ 5. Standar Operasional Pengujian Ulang
> [!TIP]
> Lakukan analisis kesalahan secara manual minimal pada **100 data uji** (sangat direkomendasikan **300–500 data uji**) setiap siklus retraining selesai. Dokumentasikan pergeseran jenis kesalahan model untuk memastikan perbaikan data latih baru benar-benar tepat sasaran.

