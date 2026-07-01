# BullyGuard ID — Frontend Dashboard

Dashboard web untuk sistem deteksi cyberbullying BullyGuard ID, dibangun dengan **React 19**, **Vite 8**, **TypeScript 6**, **TailwindCSS 4**, dan **Zustand** untuk state management.

---

## 🚀 Getting Started

### Prasyarat
- **Node.js 20+** dan **npm**

### Instalasi
```bash
npm install
```

### Development Server
```bash
npm run dev
```
Buka `http://localhost:5173` di browser Anda.

---

## 🧪 Testing

Proyek ini memiliki **45 unit tests** menggunakan Vitest:
```bash
npx vitest run
```

### Test Coverage
- **Detector components**: InputPanel, ResultCard, ComparisonResultCard, EmptyState, ProbabilityBar
- **API normalization**: Response parsing, fallback handling, error mapping
- **Utilities**: Percentage formatting, text truncation
- **Constants**: Model option validation
- **XAIHighlightText**: Word importance highlighting

---

## 📂 Struktur Komponen

```text
src/
├── App.tsx                  # Thin orchestrator (menggunakan Zustand store)
├── store/
│   └── useAppStore.ts       # Zustand global state management
├── components/
│   ├── Detector/            # Modul deteksi (7 sub-komponen + hooks + API)
│   ├── Home/                # Sub-komponen halaman utama
│   │   ├── ChatSimulator.tsx
│   │   ├── FeaturesShowcase.tsx
│   │   └── DashboardHistoryChart.tsx
│   ├── ActiveLearning.tsx   # Dashboard active learning & retraining
│   ├── BatchAnalysis.tsx    # Analisis batch multi-teks
│   ├── Settings.tsx         # Pengaturan API & model
│   ├── SocialScraper.tsx    # Scraper media sosial (TikTok, X)
│   ├── Navbar.tsx           # Navigation bar
│   ├── Sidebar.tsx          # Sidebar navigasi
│   └── XAIHighlightText.tsx # Highlight teks XAI
└── main.tsx                 # Entry point
```

---

## 🔧 Konfigurasi

URL backend API dibaca dari environment variable Vite:
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 📦 Build Produksi
```bash
npm run build
```
Output akan berada di folder `dist/`.

### Linting
```bash
npm run lint
```

---

## 🔌 Koneksi Backend

Frontend berkomunikasi dengan backend FastAPI melalui:
- **REST API**: `POST /predict/hybrid`, `/predict/lexicon`, `/predict/ml`, `/predict/transformers`, `/predict/ensemble`
- **Versioned Routes**: `/api/v1/predict/*` (recommended)
- **Authentication**: Header `X-API-Key` atau `Authorization: Bearer <token>`
- **Offline Fallback**: Mode simulasi lokal saat backend tidak terjangkau
