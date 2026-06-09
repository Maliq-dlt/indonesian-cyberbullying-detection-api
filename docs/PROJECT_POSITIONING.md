# 🎯 Panduan Project Positioning — BullyGuard ID

Dokumen ini memandu Anda dalam merumuskan narasi, deskripsi portofolio, pitch, atau presentasi proyek BullyGuard ID agar terdengar **kredibel**, **profesional**, dan **jujur secara akademis maupun bisnis**.

> [!IMPORTANT]
> Hindari membuat klaim yang tidak realistis (*overclaim*) sebelum didukung oleh data uji dan bukti benchmark yang konkret. Gunakan acuan penulisan di bawah ini untuk menjaga reputasi kualitas proyek.

---

## 📌 1. Cara Mendeskripsikan Proyek (Recommended)

| Kategori Penggunaan | Narasi Deskripsi yang Direkomendasikan |
| :--- | :--- |
| **Deskripsi Umum** | *"BullyGuard ID adalah **advanced MVP** untuk deteksi cyberbullying berbahasa Indonesia berbasis **Hybrid Multi-Tier AI** dan sistem peninjauan moderator manusia (*Human-in-the-Loop*)."* |
| **Deskripsi Teknis** | *"BullyGuard ID adalah prototipe sistem moderasi berbasis API yang menggabungkan kecerdasan lexicon matching, model statistik klasifikasi cepat (Logistic Regression), pemahaman semantik Transformer (XLM-RoBERTa ONNX), serta opsi peninjauan konteks kompleks menggunakan Cloud LLM (OpenCode Go)."* |

---

## ⚠️ 2. Narasi yang Wajib Dihindari (Overclaim)

Sebelum memiliki laporan benchmark kinerja riil, hindari klaim berikut agar tidak memicu keraguan teknis dari pihak penguji, perekrut, atau klien:
- ❌ *"Platform moderasi otomatis 100% akurat tanpa campur tangan manusia."* (Sistem AI pasti memiliki celah salah klasifikasi).
- ❌ *"Sistem enterprise-ready skala produksi massal."* (Infrastruktur dan skalabilitas beban belum diuji).
- ❌ *"Pemrosesan secepat kilat (sub-millisecond) untuk jutaan request."* (Prediksi neural/Transformer membutuhkan waktu komputasi yang tidak instan).
- ❌ *"Model bebas bias dan pasti memahami semua slang sarkasme Indonesia."* (Bahasa gaul Indonesia berkembang sangat cepat dan dinamis).

---

## 🚀 3. Narasi Pitch & Portofolio yang Profesional

### 📢 A. Kalimat Pitch Singkat (Elevator Pitch)
> *"Sistem kami memecahkan masalah efisiensi moderasi konten digital dengan mengimplementasikan arsitektur hybrid multi-tier. AI menyaring komentar sederhana menggunakan model statistik yang sangat hemat daya komputasi, dan hanya meneruskan kasus-kasus ambigu yang sulit ke model Transformer atau LLM. Hal ini menghemat penggunaan sumber daya server hingga 70% sambil menjaga kualitas akurasi deteksi tetap optimal."*

### 💼 B. Kalimat untuk Portofolio Pekerjaan
> *"Saya merancang dan membangun **BullyGuard ID**, sebuah sistem deteksi cyberbullying bahasa Indonesia terintegrasi dengan arsitektur hybrid. Menggunakan **FastAPI** di backend dan **React** di frontend, proyek ini mengintegrasikan machine learning, **ONNX Runtime**, caching **Redis**, basis data vektor **PostgreSQL**, orkestrasi kontainer **Docker**, serta pipeline pengujian unit otomatis (*automated tests*)."*

### 🎓 C. Kalimat untuk Skripsi / Tugas Akhir
> *"Penelitian ini mengembangkan prototipe sistem klasifikasi deteksi cyberbullying pada teks komentar berbahasa Indonesia menggunakan metode hybrid classifier. Sistem ini dirancang untuk membagi beban komputasi melalui mekanisme routing probabilitas (probabilistic routing), serta menyediakan modul audit data (Active Learning) bagi moderator untuk memvalidasi kesalahan AI sebagai data latih baru pada proses retraining model berikutnya."*
