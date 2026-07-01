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

### 📂 Struktur Modul Baru (`frontend/src/`)

```text
frontend/src/
├── App.tsx                           # Thin orchestrator menggunakan Zustand store
├── store/
│   └── useAppStore.ts                # Zustand global state (theme, apiUrl, activeTab, dll)
├── components/
│   ├── Detector/                     # Komponen deteksi modular
│   │   ├── Detector.tsx              # Komposisi layout utama
│   │   ├── InputPanel.tsx            # Form input teks & selector model
│   │   ├── ResultCard.tsx            # Tampilan hasil analisis
│   │   ├── ComparisonResultCard.tsx  # Tabel perbandingan multi-model
│   │   ├── XaiDrawer.tsx             # Panel visualisasi SHAP
│   │   ├── EmptyState.tsx            # Tampilan kosong
│   │   ├── ProbabilityBar.tsx        # Bar probabilitas
│   │   ├── useDetector.ts            # Custom hook state & action
│   │   ├── api.ts                    # Fungsi API & normalisasi response
│   │   ├── constants.ts              # Konstanta UI
│   │   ├── types.ts                  # Interface TypeScript
│   │   ├── utils.ts                  # Helper formatting
│   │   └── index.ts                  # Export publik
│   ├── Home/                         # Sub-komponen halaman utama
│   │   ├── ChatSimulator.tsx         # Simulator chat deteksi
│   │   ├── FeaturesShowcase.tsx      # Showcase fitur tab interaktif
│   │   └── DashboardHistoryChart.tsx # Grafik riwayat deteksi
│   ├── Home.tsx                      # Thin orchestrator halaman utama
│   ├── ActiveLearning.tsx            # Dashboard active learning
│   ├── BatchAnalysis.tsx             # Analisis batch
│   ├── Settings.tsx                  # Pengaturan API & model
│   ├── SocialScraper.tsx             # Scraper media sosial
│   ├── Navbar.tsx                    # Navigation bar
│   ├── Sidebar.tsx                   # Sidebar navigasi
│   └── XAIHighlightText.tsx          # Highlight teks XAI
└── main.tsx                          # Entry point React
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
- [x] ~~Membuat shared API client~~ — API normalization layer sudah ada di `Detector/api.ts`.
- [x] ~~Menambahkan pengujian komponen otomatis menggunakan *Vitest*~~ — **Selesai**: 45 Vitest tests telah mencakup Detector, XAIHighlightText, API, constants, dan utils.
- [x] ~~Mengurangi prop drilling~~ — **Selesai**: Zustand store (`store/useAppStore.ts`) menggantikan seluruh prop drilling dari App.tsx.
- [x] ~~Memecah Home.tsx God Component~~ — **Selesai**: Diekstrak ke 3 sub-komponen (`ChatSimulator`, `FeaturesShowcase`, `DashboardHistoryChart`).
- [ ] Mengganti indikator loading teks sederhana menggunakan skeleton loading modern agar UI terasa lebih premium.
