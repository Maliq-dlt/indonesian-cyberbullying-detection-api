# 🎨 Frontend Refactor Guide — Detector Module

Dokumen ini menjelaskan restrukturisasi arsitektur kode antarmuka (*refactoring*) pada modul utama **Detector.tsx** menjadi komponen modular yang lebih terkelola (*maintainable*).

---

## ⚠️ 1. Masalah pada Kode Awal
Sebelum Stage 4 diterapkan, komponen `Detector.tsx` merupakan berkas raksasa tunggal (>800 baris kode) yang memiliki terlalu banyak tanggung jawab:
- Pencampuran logika pemanggilan API dengan komponen rendering UI.
- Logika state loading, error, dan transisi perbandingan model tersebar acak di JSX.
- Logika XAI drawer dan grafik bobot SHAP tertanam langsung di induk komponen.
- Kode bertipe data `any` pada TypeScript yang rentan memicu *runtime bug*.

---

## 📐 2. Strategi Refaktorisasi

Tujuan refaktorisasi ini adalah memisahkan kode berdasarkan fungsinya (Separation of Concerns) tanpa mengubah visual asli atau perilaku aplikasi.

### 📂 Struktur Modul Baru (`frontend/src/components/Detector/`)

```text
Detector/
├── Detector.tsx              # Komposisi layout utama (Layout Orchestration)
├── InputPanel.tsx            # Form input teks, selector tipe model, tombol submit
├── ResultCard.tsx            # Tampilan hasil analisis model tunggal
├── ComparisonResultCard.tsx  # Tabel hasil audit perbandingan multi-model
├── XaiDrawer.tsx             # Panel laci samping grafik visualisasi SHAP (Word Importance)
├── EmptyState.tsx            # Tampilan kosong sebelum teks dianalisis
├── ProbabilityBar.tsx        # Bar persentase probabilitas toxic & bully
├── useDetector.ts            # Custom hook pengelola state dan action
├── api.ts                    # Fungsi API, normalisasi skema response, fallback lokal
├── constants.ts              # Daftar pilihan model dan konstanta UI
├── types.ts                  # Interface TypeScript (shared types)
├── utils.ts                  # Fungsi helper pemformatan teks & persentase
└── index.ts                  # Entrypoint export publik
```

---

## 🔑 3. Keputusan Desain Utama

### 🔌 Kompatibilitas Impor Lama
Untuk mencegah error pada berkas lain yang mengimpor detector, file wrapper `frontend/src/components/Detector.tsx` tetap dipertahankan dan hanya mengekspor ulang modul baru:
```typescript
export { default } from './Detector/Detector';
```
Sehingga pemanggilan impor di `App.tsx` tetap bekerja tanpa perubahan:
```typescript
import Detector from './components/Detector';
```

### 🔀 Pemetaan Endpoint API
Mekanisme routing pemanggilan endpoint backend didefinisikan secara rapi:

| Pilihan Mode Model | Endpoint API |
| :--- | :--- |
| **Hybrid AI** | `/predict/hybrid` |
| **Lexicon Only** | `/predict/lexicon` |
| **Machine Learning** | `/predict/ml` |
| **Transformer ONNX** | `/predict/transformers` |
| **Ensemble Model** | `/predict/ensemble` |
| **Audit Multi-Model** | Paralel call ke semua endpoint di atas |

### 🛠️ Mode Simulasi Sandbox (Offline Fallback)
Jika server API backend offline atau tidak terjangkau, sistem akan otomatis melakukan *fallback* lokal (simulasi) khusus di mode model tunggal agar antarmuka web demonstrasi tetap dapat ditunjukkan.

---

## 🧪 4. Daftar Verifikasi QA Manual (Checklist)

Setelah melakukan refaktorisasi, jalankan pengujian manual berikut pada browser:
- [ ] Teks input kosong tidak boleh memicu submit.
- [ ] Teks dengan panjang >500 karakter wajib menampilkan peringatan batas limit.
- [ ] Mode *Hybrid AI* memanggil endpoint `/predict/hybrid`.
- [ ] Mode *Lexicon* memanggil endpoint `/predict/lexicon`.
- [ ] Tombol opsi *Fuzzy Matching* hanya muncul pada pilihan model Lexicon dan Audit Multi-Model.
- [ ] Mode *Audit Multi-Model* memanggil seluruh endpoint model secara paralel dan menyajikannya dalam tabel perbandingan.
- [ ] Menguji backend dalam keadaan mati, pastikan form fallback lokal menyala di mode model tunggal.
- [ ] Panel XAI Drawer terbuka dengan benar saat baris kata penting diklik dan ditutup saat tombol silang atau backdrop diklik.
- [ ] Perintah `npm run build` berhasil tanpa memicu error kompilasi TypeScript.

---

## 📈 5. Rekomendasi Peningkatan Frontend Selanjutnya
- [ ] Membuat shared API client (menggunakan Axios atau instance Fetch) untuk pengelolaan header API Key terpusat.
- [ ] Menambahkan pengujian komponen otomatis menggunakan *Vitest* dan *React Testing Library*.
- [ ] Mengganti indikator loading teks sederhana menggunakan skeleton loading modern agar UI terasa lebih premium.
