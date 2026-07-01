import React, { useState, useEffect } from 'react';
import { m } from 'framer-motion';
import { 
  Shield, CheckCircle, Activity, ArrowRight, PlayCircle, 
  Moon, Sun, ArrowUpRight, RefreshCw
} from 'lucide-react';

import ChatSimulator from './Home/ChatSimulator';
import FeaturesShowcase from './Home/FeaturesShowcase';
import DashboardHistoryChart from './Home/DashboardHistoryChart';
import type { HistoryDataPoint } from './Home/DashboardHistoryChart';

interface HomeProps {
  setActiveTab: (tab: any) => void;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  apiStatus: 'unchecked' | 'online' | 'offline';
  apiUrl: string;
  apiKey: string;
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.12,
      delayChildren: 0.15
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { 
    opacity: 1, 
    y: 0,
    transition: {
      type: "spring" as const,
      stiffness: 260,
      damping: 22
    }
  }
};

export default function Home({ setActiveTab, theme, toggleTheme, apiStatus, apiUrl, apiKey }: HomeProps) {
  const [historyData, setHistoryData] = useState<HistoryDataPoint[]>([]);
  const [historyLoading, setHistoryLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchHistory = async () => {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (apiKey) headers['x-api-key'] = apiKey;

      try {
        setHistoryLoading(true);
        const response = await fetch(`${apiUrl}/api/train/history`, { headers });
        if (response.ok) {
          const json = await response.json();
          // Support both paginated { data: [...] } and legacy flat array
          const history = Array.isArray(json) ? json : (json.data || []);
          setHistoryData(history);
        }
      } catch (err) {
        console.error('Gagal mengambil riwayat retraining di dashboard:', err);
      } finally {
        setHistoryLoading(false);
      }
    };

    fetchHistory();
  }, [apiUrl, apiKey]);

  return (
    <m.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.3 }}
      className="py-12 md:py-20 flex flex-col gap-12 relative"
    >
      {/* Floating Control Bar for Headerless Landing Page */}
      <div className="absolute top-0 right-0 z-50 flex items-center gap-3">
        <button
          onClick={() => setActiveTab('detector')}
          className="bg-white/80 dark:bg-white/5 backdrop-blur-md border border-gray-200 dark:border-gray-700 text-gray-750 dark:text-gray-300 px-4 py-2 rounded-xl text-xs font-bold hover:bg-gray-50 dark:hover:bg-white/10 active:scale-95 transition-all flex items-center gap-1.5 cursor-pointer shadow-xxs border-none active-press"
        >
          Masuk Dashboard
          <ArrowUpRight className="w-3.5 h-3.5 text-blue-500" />
        </button>

        <button
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Aktifkan Light Mode' : 'Aktifkan Dark Mode'}
          className="w-9 h-9 rounded-xl border border-gray-250 dark:border-gray-700 bg-white/80 dark:bg-white/5 backdrop-blur-md flex items-center justify-center cursor-pointer hover:bg-gray-100 dark:hover:bg-white/10 transition-all shadow-xxs border-none animate-colors"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-500" />}
        </button>
      </div>

      <div className="flex flex-col lg:flex-row items-center gap-12 mt-8">
        <div className="flex-grow flex-1 text-center lg:text-left flex flex-col gap-6">
          <div className="inline-flex items-center gap-2 bg-blue-50 dark:bg-blue-500/10 border border-blue-100 dark:border-blue-500/20 px-3 py-1 rounded-full text-blue-600 dark:text-blue-400 text-xs font-medium w-fit mx-auto lg:mx-0">
            <Activity className="w-3.5 h-3.5 text-blue-500 animate-pulse" />
            Versi 1.0 AI Engine Aktif
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-gray-900 dark:text-[#faf8ff] leading-tight tracking-tight">
            Deteksi Cyberbullying <br className="hidden md:block"/>
            Bahasa Indonesia dengan AI
          </h1>
          <p className="text-gray-500 dark:text-gray-400 text-base md:text-lg max-w-xl mx-auto lg:mx-0 leading-relaxed opacity-95">
            Analisis komentar, ujaran kebencian, dan bahasa toksik secara cepat menggunakan pendekatan Lexicon, Machine Learning, Transformer, dan Hybrid AI untuk perlindungan ruang digital yang etis dan aman.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center gap-3 mt-4 justify-center lg:justify-start">
            <button 
              onClick={() => setActiveTab('detector')}
              className="w-full sm:w-auto bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3.5 rounded-xl text-sm font-semibold hover:shadow-lg hover:shadow-blue-500/20 active-press flex items-center justify-center gap-2 border-none cursor-pointer"
            >
              Mulai Deteksi Teks
              <ArrowRight className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setActiveTab('social')}
              className="w-full sm:w-auto bg-white dark:bg-white/10 border border-gray-250 dark:border-gray-700 text-gray-755 dark:text-gray-300 px-8 py-3.5 rounded-xl text-sm font-semibold hover:bg-gray-50 dark:hover:bg-white/15 active-press flex items-center justify-center gap-2 cursor-pointer border-none"
            >
              Analisis Link Sosmed
              <PlayCircle className="w-4 h-4 text-blue-500" />
            </button>
          </div>

          <div className="flex items-center justify-center lg:justify-start gap-3 mt-8 text-gray-400">
            <div className="flex -space-x-1.5">
              <div className="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-900/40 border border-white dark:border-gray-800 flex items-center justify-center"><Shield className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 fill-blue-600/10" /></div>
              <div className="w-7 h-7 rounded-full bg-purple-100 dark:bg-purple-900/40 border border-white dark:border-gray-800 flex items-center justify-center"><CheckCircle className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" /></div>
              <div className="w-7 h-7 rounded-full bg-emerald-100 dark:bg-emerald-900/40 border border-white dark:border-gray-800 flex items-center justify-center"><Activity className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /></div>
            </div>
            <span className="text-xs font-medium text-gray-550 dark:text-gray-400">Mendukung perlindungan digital moderasi konten lokal</span>
          </div>
        </div>

        {/* Mockup Showcase */}
        <div className="flex-1 w-full max-w-lg relative mt-10 lg:mt-0">
          <div className="absolute inset-0 bg-gradient-to-tr from-blue-100/50 to-purple-100/50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-3xl blur-2xl transform rotate-3" />
          <ChatSimulator />
        </div>
      </div>

      {/* Feature Showcase Tabbed Showcase Section */}
      <FeaturesShowcase setActiveTab={setActiveTab} />

      {/* Visual Analytics Metrics Dashboard Section */}
      <div className="w-full flex flex-col gap-6 mt-6 border-t border-gray-150 dark:border-gray-800/60 pt-12">
        <header className="text-center lg:text-left">
          <h2 className="text-2xl font-black text-gray-900 dark:text-[#faf8ff]">Dashboard Metrik Moderasi AI</h2>
          <p className="text-gray-450 text-xs">Statistik performa deteksi dan pola toksisitas waktu-nyata.</p>
        </header>

        <m.div 
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {/* Card 1: Akurasi Multi-Model */}
          <m.div variants={itemVariants} className="premium-card p-5 flex flex-col gap-4">
            <span className="text-xxs font-bold text-gray-400 uppercase tracking-wider">Akurasi Performa Model</span>
            <div className="flex flex-col gap-3">
              <div className="flex flex-col gap-1">
                <div className="flex justify-between text-xs font-bold text-gray-700 dark:text-gray-300">
                  <span>ML Klasik (Logistic Regression)</span>
                  <span className="text-blue-500">87.4%</span>
                </div>
                <div className="w-full bg-gray-100 dark:bg-gray-800/60 rounded-full h-1.5 overflow-hidden">
                  <m.div 
                    initial={{ width: 0 }}
                    animate={{ width: '87.4%' }}
                    transition={{ duration: 1, ease: 'easeOut', delay: 0.5 }}
                    className="bg-blue-500 h-full rounded-full" 
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <div className="flex justify-between text-xs font-bold text-gray-700 dark:text-gray-300">
                  <span>Deep Learning (XLM-RoBERTa ONNX)</span>
                  <span className="text-purple-500">92.1%</span>
                </div>
                <div className="w-full bg-gray-100 dark:bg-gray-800/60 rounded-full h-1.5 overflow-hidden">
                  <m.div 
                    initial={{ width: 0 }}
                    animate={{ width: '92.1%' }}
                    transition={{ duration: 1, ease: 'easeOut', delay: 0.65 }}
                    className="bg-purple-500 h-full rounded-full" 
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <div className="flex justify-between text-xs font-bold text-gray-700 dark:text-gray-300">
                  <span>Hybrid Ensemble System (V1.0)</span>
                  <span className="text-emerald-500">94.8%</span>
                </div>
                <div className="w-full bg-gray-100 dark:bg-gray-800/60 rounded-full h-1.5 overflow-hidden">
                  <m.div 
                    initial={{ width: 0 }}
                    animate={{ width: '94.8%' }}
                    transition={{ duration: 1, ease: 'easeOut', delay: 0.8 }}
                    className="bg-emerald-500 h-full rounded-full" 
                  />
                </div>
              </div>
            </div>
          </m.div>

          {/* Card 2: Sebaran Kategori Toksisitas (SVG Donut Chart) */}
          <m.div variants={itemVariants} className="premium-card p-5 flex flex-col gap-2 items-center justify-between text-center">
            <span className="text-xxs font-bold text-gray-400 uppercase tracking-wider self-start">Distribusi Kategori Toksik</span>
            <div className="relative w-28 h-28 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                <path className="text-gray-100 dark:text-gray-800" strokeWidth="3" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <m.path 
                  className="text-rose-500" 
                  strokeDasharray="45, 100" 
                  strokeWidth="3" 
                  strokeLinecap="round" 
                  stroke="currentColor" 
                  fill="none" 
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1.2, ease: 'easeInOut', delay: 0.4 }}
                />
                <m.path 
                  className="text-indigo-500" 
                  strokeDasharray="30, 100" 
                  strokeDashoffset="-45" 
                  strokeWidth="3" 
                  strokeLinecap="round" 
                  stroke="currentColor" 
                  fill="none" 
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1.2, ease: 'easeInOut', delay: 0.65 }}
                />
                <m.path 
                  className="text-emerald-500" 
                  strokeDasharray="25, 100" 
                  strokeDashoffset="-75" 
                  strokeWidth="3" 
                  strokeLinecap="round" 
                  stroke="currentColor" 
                  fill="none" 
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1.2, ease: 'easeInOut', delay: 0.9 }}
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <m.span 
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.8, type: 'spring' }}
                  className="text-lg font-black text-gray-900 dark:text-white"
                >
                  15.8k
                </m.span>
                <span className="text-[9px] text-gray-400 font-bold uppercase tracking-wider">Teks Analisis</span>
              </div>
            </div>
            <div className="flex gap-3 text-[10px] font-bold text-gray-650 dark:text-gray-400 mt-2">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Bullying (45%)</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> Toxic (30%)</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Aman (25%)</span>
            </div>
          </m.div>

          {/* Card 3: Aktivitas Pemrosesan Deteksi */}
          <m.div variants={itemVariants} className="premium-card p-5 flex flex-col gap-3">
            <div className="flex justify-between items-center">
              <span className="text-xxs font-bold text-gray-400 uppercase tracking-wider">Aktivitas Pemrosesan API</span>
              <span className="text-[10px] text-emerald-500 font-bold bg-emerald-50 dark:bg-emerald-500/10 px-2 py-0.5 rounded">Realtime</span>
            </div>
            <div className="h-24 w-full mt-1">
              <svg className="w-full h-full" viewBox="0 0 100 30" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.3"/>
                    <stop offset="100%" stopColor="#4f46e5" stopOpacity="0"/>
                  </linearGradient>
                </defs>
                <m.path 
                  d="M 0 25 Q 15 15, 30 20 T 60 5 T 90 12 T 100 8 L 100 30 L 0 30 Z" 
                  fill="url(#areaGrad)" 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 1.2, delay: 0.8 }}
                />
                <m.path 
                  d="M 0 25 Q 15 15, 30 20 T 60 5 T 90 12 T 100 8" 
                  fill="none" 
                  stroke="var(--primary-color)" 
                  strokeWidth="1.5" 
                  strokeLinecap="round" 
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1.5, ease: 'easeInOut', delay: 0.4 }}
                />
                <circle cx="60" cy="5" r="1.5" fill="var(--primary-color)" className="animate-ping" style={{ transformOrigin: '60px 5px' }} />
                <circle cx="60" cy="5" r="1" fill="var(--primary-color)" />
              </svg>
            </div>
            <div className="flex justify-between text-[10px] text-gray-400 font-bold uppercase tracking-wider">
              <span>08:00</span>
              <span>12:00</span>
              <span>16:00</span>
              <span>Sekarang</span>
            </div>
          </m.div>

          {/* Card 4: Tren Riwayat Pelatihan & Drift Performa */}
          <m.div
            variants={itemVariants}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.85 }}
            className="premium-card p-6 flex flex-col gap-5 md:col-span-3 w-full relative"
          >
            <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-800/60 pb-3">
              <div className="flex flex-col">
                <span className="text-xxs font-bold text-gray-400 uppercase tracking-wider">Metrik Evaluasi Historis</span>
                <h3 className="text-sm font-bold text-gray-900 dark:text-gray-200">Tren Riwayat Pelatihan &amp; Drift Model</h3>
              </div>
              <span className="text-[10px] text-gray-400 font-bold">Interaktif</span>
            </div>

            {historyLoading ? (
              <div className="flex flex-col items-center justify-center py-12 gap-2">
                <RefreshCw className="w-6 h-6 animate-spin text-indigo-500" />
                <span className="text-xxs text-gray-400 font-semibold">Mengambil data metrik training...</span>
              </div>
            ) : (
              <DashboardHistoryChart historyData={historyData} />
            )}
          </m.div>
        </m.div>

        {/* Grid panel for Word Cloud and Confidence Density Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-4">
          
          {/* Sebaran Kata Toksik Terpopuler (Interactive Word Cloud) */}
          <m.div
            variants={itemVariants}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.95 }}
            className="premium-card p-6 flex flex-col gap-4 mt-2 lg:col-span-7"
          >
            <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-800/60 pb-3">
              <div className="flex flex-col">
                <span className="text-xxs font-bold text-gray-400 uppercase tracking-wider">Analisis Leksikal Ruang Siber</span>
                <h3 className="text-sm font-bold text-gray-900 dark:text-gray-200">Peta Slang &amp; Kata Toksik Terpopuler</h3>
              </div>
              <span className="text-[10px] text-gray-400 font-bold">Interaktif</span>
            </div>

            <div className="w-full overflow-hidden bg-gray-50/30 dark:bg-slate-950/20 border border-gray-100 dark:border-gray-800/40 rounded-2xl p-4 flex flex-col items-center justify-center min-h-[220px]">
              <svg viewBox="0 0 600 200" className="w-full h-auto max-w-2xl select-none overflow-visible">
                {(() => {
                  const wordPositions = [
                    { text: 'goblok', x: 300, y: 100, size: 28, color: '#f43f5e', category: 'Toxic (High Severity)' },
                    { text: 'anjing', x: 205, y: 80, size: 23, color: '#ef4444', category: 'Toxic (High Severity)' },
                    { text: 'tolol', x: 395, y: 120, size: 23, color: '#ef4444', category: 'Toxic (High Severity)' },
                    { text: 'mati aja', x: 310, y: 55, size: 20, color: '#a855f7', category: 'Bullying (High Severity)' },
                    { text: 'jelek', x: 130, y: 120, size: 19, color: '#c084fc', category: 'Bullying (Medium Severity)' },
                    { text: 'bego', x: 460, y: 70, size: 18, color: '#f87171', category: 'Toxic (Medium Severity)' },
                    { text: 'sampah', x: 250, y: 155, size: 18, color: '#f87171', category: 'Toxic (Medium Severity)' },
                    { text: 'bodoh', x: 375, y: 165, size: 16, color: '#fca5a5', category: 'Toxic (Medium Severity)' },
                    { text: 'cacat', x: 215, y: 135, size: 17, color: '#a855f7', category: 'Bullying (High Severity)' },
                    { text: 'banci', x: 130, y: 65, size: 16, color: '#a855f7', category: 'Bullying (High Severity)' },
                    { text: 'miskin', x: 490, y: 145, size: 15, color: '#c084fc', category: 'Bullying (Medium Severity)' },
                    { text: 'cupu', x: 275, y: 25, size: 14, color: '#e9d5ff', category: 'Bullying (Low Severity)' },
                    { text: 'kampret', x: 395, y: 30, size: 14, color: '#fecaca', category: 'Toxic (Low Severity)' },
                    { text: 'gila', x: 90, y: 95, size: 14, color: '#fecaca', category: 'Toxic (Low Severity)' },
                  ];

                  return wordPositions.map((word, index) => (
                    <g key={index} className="group/word cursor-help">
                      <text
                        x={word.x}
                        y={word.y}
                        textAnchor="middle"
                        style={{ 
                          fontSize: `${word.size}px`, 
                          fill: word.color, 
                          fontWeight: 900,
                          transformOrigin: `${word.x}px ${word.y}px`,
                        }}
                        className="transition-transform duration-200 group-hover/word:scale-115 font-display select-none"
                      >
                        {word.text}
                        <title>{`Kategori: ${word.category}\nFrekuensi Penggunaan: Tinggi`}</title>
                      </text>
                    </g>
                  ));
                })()}
              </svg>
            </div>
            <p className="text-[10px] text-gray-400 dark:text-gray-500 font-medium leading-normal italic text-center">
              *Arahkan kursor ke atas slang kata untuk melacak rincian kategori tingkat keparahan (*severity*).
            </p>
          </m.div>

          {/* Grafik Distribusi Densitas Keyakinan */}
          <m.div
            variants={itemVariants}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.95 }}
            className="premium-card p-6 flex flex-col gap-4 mt-2 lg:col-span-5"
          >
            <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-800/60 pb-3">
              <div className="flex flex-col">
                <span className="text-xxs font-bold text-gray-400 uppercase tracking-wider">Metrik Tingkat Keyakinan AI</span>
                <h3 className="text-sm font-bold text-gray-900 dark:text-gray-200">Distribusi Kerapatan (Density)</h3>
              </div>
              <span className="text-[10px] text-amber-600 dark:text-amber-500 font-bold bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded border border-amber-250/20">Bimodal</span>
            </div>

            <div className="w-full overflow-hidden bg-gray-50/30 dark:bg-slate-950/20 border border-gray-100 dark:border-gray-800/40 rounded-2xl p-4 flex flex-col items-center justify-center min-h-[220px]">
              <svg viewBox="0 0 400 200" className="w-full h-auto overflow-visible select-none">
                <defs>
                  <linearGradient id="densityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--primary-color)" stopOpacity="0.4"/>
                    <stop offset="100%" stopColor="var(--primary-color)" stopOpacity="0.01"/>
                  </linearGradient>
                </defs>

                <rect x="176" y="20" width="102" height="140" fill="#fef3c7" className="opacity-25 dark:opacity-[0.06]" />
                <line x1="176" y1="20" x2="176" y2="160" stroke="#f59e0b" strokeDasharray="3 3" strokeWidth="1" className="opacity-60" />
                <line x1="278" y1="20" x2="278" y2="160" stroke="#f59e0b" strokeDasharray="3 3" strokeWidth="1" className="opacity-60" />
                <text x="227" y="15" textAnchor="middle" className="text-[8px] font-bold fill-amber-600 dark:fill-amber-500 uppercase tracking-wider">Zona Ragu (Active Learning)</text>

                {[40, 80, 120, 160].map(y => (
                  <line key={y} x1="40" y1={y} x2="380" y2={y} stroke="var(--card-border)" strokeWidth="0.5" strokeDasharray="2 2" className="opacity-50" />
                ))}

                <path 
                  d="M 40 160 C 80 40, 120 40, 160 110 C 200 150, 240 150, 280 110 C 320 60, 350 65, 380 160 L 380 160 L 40 160 Z" 
                  fill="url(#densityGrad)" 
                />

                <path 
                  d="M 40 160 C 80 40, 120 40, 160 110 C 200 150, 240 150, 280 110 C 320 60, 350 65, 380 160" 
                  fill="none" 
                  stroke="var(--primary-color)" 
                  strokeWidth="2.5" 
                  strokeLinecap="round" 
                />

                <line x1="40" y1="160" x2="380" y2="160" stroke="var(--card-border)" strokeWidth="1.5" />
                <line x1="40" y1="20" x2="40" y2="160" stroke="var(--card-border)" strokeWidth="1.5" />

                {[
                  { val: '0.0', x: 40 },
                  { val: '0.2', x: 108 },
                  { val: '0.4', x: 176 },
                  { val: '0.6', x: 244 },
                  { val: '0.8', x: 312 },
                  { val: '1.0', x: 380 }
                ].map(tick => (
                  <text key={tick.val} x={tick.x} y="175" textAnchor="middle" className="text-[8px] font-mono font-bold" fill="var(--text-muted)">{tick.val}</text>
                ))}

                <text x="210" y="192" textAnchor="middle" className="text-[8px] font-bold" fill="var(--text-muted)">Model Confidence Score</text>
                <text x="15" y="90" textAnchor="middle" transform="rotate(-90 15 90)" className="text-[8px] font-bold" fill="var(--text-muted)">Kerapatan (Density)</text>

                <circle cx="100" cy="55" r="3.5" fill="#10b981" />
                <title>Peak Safe: AI sangat percaya diri mendiagnosis kalimat bersih.</title>
                <circle cx="335" cy="72" r="3.5" fill="#ef4444" />
                <title>Peak Toxic/Bully: AI mendeteksi penyerangan personal secara tegas.</title>
              </svg>
            </div>
            <p className="text-[10px] text-gray-400 dark:text-gray-500 font-medium leading-normal italic text-center">
              * Puncak kiri mewakili data aman; puncak kanan mewakili risiko terdeteksi; lembah tengah adalah target peninjauan active learning.
            </p>
          </m.div>

        </div>
      </div>
    </m.div>
  );
}
