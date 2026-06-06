import React, { useState, useEffect } from 'react';
import { m, AnimatePresence } from 'framer-motion';
import { 
  Shield, CheckCircle, Activity, ArrowRight, PlayCircle, 
  Check, MessageSquare, Globe, UploadCloud, Workflow, 
  Settings, Download, Moon, Sun, ArrowUpRight
} from 'lucide-react';

interface HomeProps {
  setActiveTab: (tab: any) => void;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  apiStatus: 'unchecked' | 'online' | 'offline';
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

const simulatedComments = [
  {
    author: "user_anon88",
    avatar: "A",
    text: "Terima kasih atas bantuannya hari ini, sangat terbantu sekali! Sukses selalu.",
    verdict: "Aman / Bersih",
    confidence: 0.99,
    details: "Teks dianalisis aman dari indikasi cyberbullying, ujaran kebencian, atau pelecehan.",
    type: "aman",
    segments: [
      { text: "Terima kasih atas bantuannya hari ini, sangat terbantu sekali! Sukses selalu." }
    ]
  },
  {
    author: "hater_detect32",
    avatar: "H",
    text: "eh lu bego banget sih kerja ginian aja ga becus wkwk mental lemah",
    verdict: "Toxic & Bullying",
    confidence: 0.95,
    details: "Mengandung makian personal kasar dan ejekan merendahkan kapasitas mental seseorang.",
    type: "toxic-bully",
    segments: [
      { text: "eh lu " },
      { text: "bego", type: "toxic", weight: 0.85 },
      { text: " banget sih kerja ginian aja " },
      { text: "ga becus", type: "toxic", weight: 0.75 },
      { text: " wkwk " },
      { text: "mental lemah", type: "bully", weight: 0.90 }
    ]
  },
  {
    author: "gamer_id90",
    avatar: "G",
    text: "anjing kaget gua kirain musuhnya udah mati ternyata masih hidup kampret",
    verdict: "Toxic but Non-Bully",
    confidence: 0.88,
    details: "Mengandung kata kasar/umpatan mengekspresikan emosi kekagetan, bukan serangan personal.",
    type: "toxic-nonbully",
    segments: [
      { text: "anjing", type: "toxic", weight: 0.88 },
      { text: " kaget gua kirain musuhnya udah mati ternyata masih hidup " },
      { text: "kampret", type: "toxic", weight: 0.70 }
    ]
  },
  {
    author: "sarcasm_king",
    avatar: "S",
    text: "pinter banget sih kamu ya, sampe-sampe nilai ujiannya dapet nol terus",
    verdict: "Non-Toxic but Bully",
    confidence: 0.84,
    details: "Sarkasme halus meremehkan inteligensi orang lain secara pasif-agresif.",
    type: "nontoxic-bully",
    segments: [
      { text: "pinter banget sih", type: "bully", weight: 0.65 },
      { text: " kamu ya, sampe-sampe " },
      { text: "nilai ujiannya dapet nol terus", type: "bully", weight: 0.82 }
    ]
  }
];

function ChatSimulator() {
  const [index, setIndex] = useState(0);
  const [textToShow, setTextToShow] = useState('');
  const [stage, setStage] = useState<'typing' | 'scanning' | 'revealing' | 'idle'>('typing');
  const [typedLength, setTypedLength] = useState(0);
  
  const currentComment = simulatedComments[index];
  const fullText = currentComment.text;

  // Typing effect
  useEffect(() => {
    if (stage !== 'typing') return;
    
    if (typedLength < fullText.length) {
      const timer = setTimeout(() => {
        setTypedLength(prev => prev + 1);
        setTextToShow(fullText.slice(0, typedLength + 1));
      }, 35 + Math.random() * 25);
      return () => clearTimeout(timer);
    } else {
      const timer = setTimeout(() => {
        setStage('scanning');
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [stage, typedLength, fullText]);

  // Scanning effect
  useEffect(() => {
    if (stage !== 'scanning') return;
    
    const timer = setTimeout(() => {
      setStage('revealing');
    }, 1800);
    return () => clearTimeout(timer);
  }, [stage]);

  // Revealing & Idle cycle
  useEffect(() => {
    if (stage !== 'revealing') return;
    
    const timer = setTimeout(() => {
      setStage('idle');
    }, 1000);
    return () => clearTimeout(timer);
  }, [stage]);

  useEffect(() => {
    if (stage !== 'idle') return;
    
    const timer = setTimeout(() => {
      setStage('typing');
      setTypedLength(0);
      setTextToShow('');
      setIndex(prev => (prev + 1) % simulatedComments.length);
    }, 4000);
    return () => clearTimeout(timer);
  }, [stage]);

  const config = {
    aman: {
      badgeClass: "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-100 dark:border-emerald-500/20",
      progressClass: "bg-emerald-500",
      textClass: "text-emerald-800 dark:text-emerald-400"
    },
    'toxic-bully': {
      badgeClass: "bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-105 dark:border-rose-500/20",
      progressClass: "bg-rose-600",
      textClass: "text-rose-800 dark:text-rose-400"
    },
    'toxic-nonbully': {
      badgeClass: "bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-100 dark:border-amber-500/20",
      progressClass: "bg-amber-500",
      textClass: "text-amber-800 dark:text-amber-400"
    },
    'nontoxic-bully': {
      badgeClass: "bg-purple-50 dark:bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-100 dark:border-purple-500/20",
      progressClass: "bg-purple-600",
      textClass: "text-purple-800 dark:text-purple-400"
    }
  }[currentComment.type as 'aman' | 'toxic-bully' | 'toxic-nonbully' | 'nontoxic-bully'] || {
    badgeClass: "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-100 dark:border-emerald-500/20",
    progressClass: "bg-emerald-500",
    textClass: "text-emerald-800 dark:text-emerald-400"
  };

  return (
    <div className="relative glass-card rounded-2xl p-6 border border-white/60 dark:border-white/10 shadow-xl overflow-hidden min-h-[300px] flex flex-col justify-between">
      {/* Laser Scanner Bar */}
      {stage === 'scanning' && (
        <m.div
          initial={{ top: '0%' }}
          animate={{ top: '100%' }}
          transition={{ repeat: Infinity, repeatType: "reverse", duration: 0.9, ease: "linear" }}
          className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-blue-500/80 to-transparent pointer-events-none shadow-[0_0_10px_rgba(59,130,246,0.8)] z-20"
        />
      )}

      {/* Header bar of mock */}
      <div className="flex justify-between items-center mb-4 border-b border-gray-150 dark:border-gray-800/60 pb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
            <Shield className="w-4.5 h-4.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-gray-900 dark:text-[#faf8ff] leading-none">Analisis Real-Time</h3>
            <span className="text-[9px] text-gray-400 font-bold uppercase tracking-wider mt-0.5 block leading-none">AI Hybrid Scanner</span>
          </div>
        </div>
        <span className="bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 border border-emerald-100 dark:border-emerald-500/20 leading-none">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Active
        </span>
      </div>

      {/* Comment Body */}
      <div className="bg-gray-50/50 dark:bg-black/10 rounded-xl p-4 border border-gray-150 dark:border-gray-800/60 mb-4 flex-grow flex flex-col justify-center min-h-[90px] relative">
        {stage === 'scanning' && (
          <div className="absolute inset-0 bg-blue-500/3 dark:bg-blue-500/5 animate-pulse pointer-events-none" />
        )}
        <div className="flex gap-2.5 mb-2.5 items-center">
          <div className="w-6.5 h-6.5 rounded-full bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-100 dark:border-indigo-500/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-xs shrink-0 select-none">
            {currentComment.avatar}
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-gray-850 dark:text-gray-200 leading-none">{currentComment.author}</span>
            <span className="text-[9px] text-gray-400 font-semibold leading-none mt-1">Baru saja</span>
          </div>
        </div>
        <p className="text-xs text-gray-700 dark:text-gray-300 italic font-medium leading-relaxed">
          "
          {stage === 'typing' || stage === 'scanning' ? (
            textToShow
          ) : (
            currentComment.segments.map((seg, idx) => {
              if (seg.type === 'toxic') {
                return (
                  <span 
                    key={idx} 
                    className="bg-rose-500/15 text-rose-700 dark:bg-rose-500/25 dark:text-rose-300 font-bold px-1.5 py-0.5 rounded border-b-2 border-rose-400/60 transition-colors"
                  >
                    {seg.text}
                  </span>
                );
              } else if (seg.type === 'bully') {
                return (
                  <span 
                    key={idx} 
                    className="bg-purple-500/15 text-purple-700 dark:bg-purple-500/25 dark:text-purple-300 font-bold px-1.5 py-0.5 rounded border-b-2 border-purple-400/60 transition-colors"
                  >
                    {seg.text}
                  </span>
                );
              } else {
                return <span key={idx}>{seg.text}</span>;
              }
            })
          )}
          "
        </p>
      </div>

      {/* AI Diagnosis Verdict Box */}
      <div className="min-h-[72px] flex items-center justify-center">
        <AnimatePresence mode="wait">
          {(stage === 'revealing' || stage === 'idle') ? (
            <m.div
              key={index}
              initial={{ opacity: 0, y: 15, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.98 }}
              transition={{ type: "spring", stiffness: 350, damping: 25 }}
              className={`w-full border rounded-xl p-3.5 flex items-start gap-3 shadow-xxs ${config.badgeClass}`}
            >
              <div className="flex-grow">
                <div className="flex items-center justify-between mb-1">
                  <h4 className={`text-xs font-black leading-none ${config.textClass}`}>{currentComment.verdict}</h4>
                  <span className="text-[9px] font-black bg-white/90 dark:bg-black/20 border border-current px-1.5 py-0.5 rounded leading-none shrink-0">
                    {Math.round(currentComment.confidence * 100)}% Confidence
                  </span>
                </div>
                <p className="text-[10px] text-gray-500 dark:text-gray-400 font-medium leading-normal">
                  {currentComment.details}
                </p>
                <div className="mt-2.5 w-full bg-white/60 dark:bg-black/20 h-1 rounded-full overflow-hidden border border-black/5">
                  <m.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${currentComment.confidence * 100}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className={`h-full rounded-full ${config.progressClass}`} 
                  />
                </div>
              </div>
            </m.div>
          ) : stage === 'scanning' ? (
            <m.div
              key="scanning-state"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-3 flex flex-col items-center gap-1.5"
            >
              <Activity className="w-5 h-5 text-blue-500 animate-pulse" />
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest animate-pulse">Memindai Konten Teks...</span>
            </m.div>
          ) : (
            <m.div
              key="idle-state"
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              className="text-center py-4 text-[10px] font-bold text-gray-400 uppercase tracking-wider"
            >
              Menunggu input komentar...
            </m.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function FeaturesShowcase({ setActiveTab }: { setActiveTab: (tab: any) => void }) {
  const [activeIdx, setActiveIdx] = useState(0);

  const features = [
    {
      title: "Detektor AI & Bobot XAI",
      shortDesc: "Analisis instan dengan visualisasi kontribusi kata kunci.",
      fullDesc: "Uji teks secara instan menggunakan model hibrida. XAI (Explainable AI) menyorot kata toxic (merah) dan bully (ungu) lengkap dengan tooltip kontribusi kontributor numerik.",
      tabId: "detector",
      indexLabel: "01"
    },
    {
      title: "TikTok & X Comment Scraper",
      shortDesc: "Ambil data komentar media sosial secara otomatis.",
      fullDesc: "Masukkan link video TikTok atau tweet X untuk mengunduh puluhan komentar secara langsung. Lakukan moderasi instan berbasis cookie platform dan proxy rotasi aman.",
      tabId: "social",
      indexLabel: "02"
    },
    {
      title: "Batch Analisis CSV",
      shortDesc: "Pemrosesan dokumen massal secara sinkron.",
      fullDesc: "Unggah dokumen file CSV yang berisi ribuan baris komentar teks. Unduh laporan klasifikasi terperinci yang mencakup diagnosis label dan tingkat kepercayaan model.",
      tabId: "batch",
      indexLabel: "03"
    },
    {
      title: "Active Learning Loop",
      shortDesc: "Latih ulang model berbasis koreksi manusia.",
      fullDesc: "Gunakan moderasi drag-and-drop antar kuadran untuk mengoreksi kesalahan prediksi kecerdasan buatan. Jalankan retrain model secara asinkron dengan sekali klik.",
      tabId: "active-learning",
      indexLabel: "04"
    },
    {
      title: "Manajemen Platform & Cookie",
      shortDesc: "Kelola sesi dan status server secara terintegrasi.",
      fullDesc: "Ubah base URL FastAPI, unggah cookie JSON untuk TikTok/X, dan pantau status pemuatan model transformers serta penyerapan memori cache di satu panel kontrol.",
      tabId: "settings",
      indexLabel: "05"
    }
  ];

  return (
    <div className="w-full flex flex-col gap-8 mt-16 border-t border-gray-150 dark:border-gray-800/60 pt-16">
      <div className="max-w-2xl mx-auto text-center flex flex-col gap-3">
        <h2 className="text-3xl font-black text-gray-900 dark:text-[#faf8ff] tracking-tight">Eksplorasi Fitur Dashboard</h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          Sistem deteksi cyberbullying komprehensif yang dirancang untuk mendukung ekosistem moderasi konten etis bahasa Indonesia.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch mt-6">
        {/* Left Side: Navigation Tabs */}
        <div className="lg:col-span-5 flex flex-col gap-2">
          {features.map((feat, idx) => {
            const isActive = activeIdx === idx;
            return (
              <div
                key={idx}
                onMouseEnter={() => setActiveIdx(idx)}
                onClick={() => setActiveIdx(idx)}
                className={`p-4 rounded-xl border text-left cursor-pointer transition-all flex items-start gap-4 select-none ${
                  isActive
                    ? 'bg-white dark:bg-[#151726] border-blue-500/30 dark:border-blue-500/20 shadow-xs'
                    : 'bg-transparent border-transparent opacity-60 hover:opacity-90'
                }`}
              >
                <span className={`text-xs font-black px-2 py-1 rounded-md shrink-0 ${
                  isActive ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400' : 'bg-gray-100 dark:bg-white/5 text-gray-400'
                }`}>
                  {feat.indexLabel}
                </span>
                <div className="flex flex-col gap-1">
                  <h3 className={`text-xs font-bold ${isActive ? 'text-gray-900 dark:text-[#faf8ff]' : 'text-gray-650 dark:text-gray-400'}`}>
                    {feat.title}
                  </h3>
                  <p className="text-[10px] text-gray-450 dark:text-gray-400 font-medium">
                    {feat.shortDesc}
                  </p>
                  {isActive && (
                    <m.p 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="text-[10px] text-gray-500 dark:text-gray-450 font-normal leading-relaxed mt-2"
                    >
                      {feat.fullDesc}
                    </m.p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Side: Mock UI Visual Showcase */}
        <div className="lg:col-span-7 flex flex-col">
          <div className="glass-card rounded-2xl p-6 border border-white/60 dark:border-white/10 flex-grow flex flex-col justify-between shadow-lg min-h-[350px] relative overflow-hidden">
            <AnimatePresence mode="wait">
              <m.div
                key={activeIdx}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
                className="flex-grow flex flex-col justify-between h-full"
              >
                {/* Mock Header (Browser Bar) */}
                <div className="flex items-center gap-2 mb-4 border-b border-gray-150 dark:border-gray-800/60 pb-3">
                  <div className="flex gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
                    <span className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
                    <span className="w-2.5 h-2.5 rounded-full bg-green-400" />
                  </div>
                  <div className="bg-gray-100 dark:bg-black/20 text-[9px] text-gray-400 font-bold px-3 py-1 rounded-md flex-grow text-center select-none truncate">
                    BullyGuard ID Dashboard — {features[activeIdx].title}
                  </div>
                </div>

                {/* Mock Screen Content depending on activeIdx */}
                <div className="flex-grow flex items-center justify-center p-4">
                  {activeIdx === 0 && (
                    /* Mock 0: Detector */
                    <div className="w-full flex flex-col gap-3 max-w-sm bg-white dark:bg-[#1c1b1c]/35 p-4 rounded-xl border border-gray-150 dark:border-gray-850 shadow-xxs">
                      <div className="text-[10px] font-bold text-gray-400 uppercase leading-none mb-1">Hasil Deteksi &amp; XAI Highlight</div>
                      <div className="border border-blue-150 bg-blue-50/10 dark:border-blue-950/40 p-3 rounded-lg text-xs leading-relaxed font-semibold text-gray-800 dark:text-gray-200">
                        "kamu <span className="bg-rose-500/20 text-rose-700 dark:bg-rose-500/30 dark:text-rose-300 px-1 py-0.5 rounded border-b border-rose-400">bego banget</span> sih kerja ginian aja <span className="bg-rose-500/20 text-rose-700 dark:bg-rose-500/30 dark:text-rose-300 px-1 py-0.5 rounded border-b border-rose-400">ga becus</span>"
                      </div>
                      <div className="flex flex-wrap gap-2 mt-1">
                        <span className="bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-500/20 px-2 py-0.5 rounded text-[9px] font-bold">Toxic &amp; Bullying (95%)</span>
                        <span className="bg-gray-100 dark:bg-white/5 text-gray-500 dark:text-gray-400 px-2 py-0.5 rounded text-[9px] font-medium">Hybrid Engine</span>
                      </div>
                    </div>
                  )}

                  {activeIdx === 1 && (
                    /* Mock 1: Scraper */
                    <div className="w-full flex flex-col gap-3 max-w-sm">
                      <div className="bg-white dark:bg-[#1c1b1c]/35 p-2 border border-gray-150 dark:border-gray-850 rounded-lg flex items-center justify-between text-[10px] font-mono text-gray-450 dark:text-gray-400">
                        <span className="truncate">https://tiktok.com/@user/video/72381203</span>
                        <span className="text-[8px] bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 px-1 rounded uppercase tracking-wider font-sans font-bold ml-2">Tiktok Scraped</span>
                      </div>
                      <div className="flex flex-col gap-2">
                        <div className="bg-rose-50/50 dark:bg-rose-950/5 border border-rose-100 dark:border-rose-900/30 p-2.5 rounded-lg flex items-center justify-between text-[10px]">
                          <span className="font-semibold text-gray-800 dark:text-gray-200 truncate">"mukamu jelek mending mati aja"</span>
                          <span className="bg-rose-600 text-white font-bold px-1.5 py-0.5 rounded text-[8px] uppercase tracking-wider">Bully</span>
                        </div>
                        <div className="bg-emerald-50/50 dark:bg-emerald-950/5 border border-emerald-100 dark:border-emerald-900/30 p-2.5 rounded-lg flex items-center justify-between text-[10px]">
                          <span className="font-semibold text-gray-800 dark:text-gray-200 truncate">"sukses terus ya programnya kak"</span>
                          <span className="bg-emerald-600 text-white font-bold px-1.5 py-0.5 rounded text-[8px] uppercase tracking-wider">Aman</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeIdx === 2 && (
                    /* Mock 2: Batch Analysis */
                    <div className="w-full flex flex-col items-center justify-center gap-4 max-w-sm bg-white dark:bg-[#1c1b1c]/35 p-5 rounded-xl border border-gray-150 dark:border-gray-850 shadow-xxs">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-500/10 border border-blue-150 dark:border-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                          <UploadCloud className="w-5 h-5" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-[11px] font-bold text-gray-800 dark:text-gray-200 leading-none">comments_database.csv</span>
                          <span className="text-[9px] text-gray-400 font-medium mt-1 leading-none">2.4 MB • 350 Baris Komentar</span>
                        </div>
                      </div>
                      <div className="w-full flex flex-col gap-1">
                        <div className="flex justify-between text-[9px] font-bold text-gray-400">
                          <span>MENGANALISIS DATASET...</span>
                          <span className="text-blue-500">100% Selesai</span>
                        </div>
                        <div className="w-full bg-gray-100 dark:bg-gray-800/60 h-1 rounded-full overflow-hidden">
                          <div className="bg-blue-500 h-full rounded-full w-full" />
                        </div>
                      </div>
                      <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2 rounded-lg text-[10px] border-none cursor-pointer flex items-center gap-1.5 w-full justify-center transition-colors">
                        <Download className="w-3.5 h-3.5" /> Unduh Laporan CSV
                      </button>
                    </div>
                  )}

                  {activeIdx === 3 && (
                    /* Mock 3: Active Learning */
                    <div className="w-full grid grid-cols-2 gap-3 max-w-sm">
                      <div className="border border-purple-200 dark:border-purple-900/30 bg-purple-50/10 p-3 rounded-xl flex flex-col gap-2">
                        <div className="text-[9px] font-bold text-purple-700 dark:text-purple-400 flex items-center justify-between">
                          <span>TOXIC (BULLEY)</span>
                          <span className="bg-purple-100 dark:bg-purple-500/20 px-1 py-0.2 rounded font-sans">1 item</span>
                        </div>
                        <div className="bg-white dark:bg-[#1c1b1c] p-2 rounded-lg border border-purple-100 dark:border-purple-900/40 text-[9px] font-semibold text-gray-700 dark:text-gray-300 shadow-xxs cursor-grab select-none">
                          "pinter amat ujian nol"
                        </div>
                      </div>
                      <div className="border border-emerald-200 dark:border-emerald-900/30 bg-emerald-50/10 p-3 rounded-xl flex flex-col gap-2">
                        <div className="text-[9px] font-bold text-emerald-700 dark:text-emerald-400 flex items-center justify-between">
                          <span>AMAN</span>
                          <span className="bg-emerald-100 dark:bg-emerald-500/20 px-1 py-0.2 rounded font-sans">10 item</span>
                        </div>
                        <div className="border border-dashed border-emerald-300 bg-emerald-50/50 p-3.5 rounded-lg flex items-center justify-center text-[8px] text-emerald-600 font-bold select-none">
                          Tarik ke Sini
                        </div>
                      </div>
                    </div>
                  )}

                  {activeIdx === 4 && (
                    /* Mock 4: Settings */
                    <div className="w-full flex flex-col gap-3.5 max-w-sm bg-white dark:bg-[#1c1b1c]/35 p-4 rounded-xl border border-gray-150 dark:border-gray-850 shadow-xxs">
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] font-bold text-gray-400">FASTAPI SERVER URL</label>
                        <div className="bg-gray-100 dark:bg-white/5 border border-gray-150 dark:border-gray-850 px-2.5 py-1.5 rounded-lg text-[10px] font-medium text-gray-700 dark:text-gray-350 select-none">
                          http://localhost:8000
                        </div>
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] font-bold text-gray-400">TIKTOK SCRAPER SESSION COOKIE</label>
                        <div className="bg-gray-100 dark:bg-white/5 border border-gray-150 dark:border-gray-850 px-2.5 py-1.5 rounded-lg text-[9px] font-mono text-gray-400 select-none">
                          {"[ { \"name\": \"sessionid\", \"value\": \"********\" } ]"}
                        </div>
                      </div>
                      <div className="flex justify-between items-center border-t border-gray-150 dark:border-gray-800/60 pt-2.5">
                        <span className="text-[9px] text-gray-450 dark:text-gray-400 font-bold">STATUS KONEKSI ENGINE:</span>
                        <span className="inline-flex items-center gap-1 text-[9px] font-bold text-emerald-500 uppercase">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Online
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Open in Dashboard Trigger */}
                <button
                  onClick={() => setActiveTab(features[activeIdx].tabId)}
                  className="bg-gray-100 dark:bg-white/5 hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-blue-500/10 dark:hover:text-blue-400 text-gray-600 dark:text-gray-400 font-bold py-2.5 rounded-xl text-[10px] border-none cursor-pointer flex items-center justify-center gap-1 shrink-0 mt-4 transition-colors active-press"
                >
                  Buka Modul Dashboard
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </m.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Home({ setActiveTab, theme, toggleTheme, apiStatus }: HomeProps) {
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
        </m.div>

        {/* Grid panel for Word Cloud and Confidence Density Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-4">
          
          {/* Sebaran Kata Toksik Terpopuler (Interactive Word Cloud) (lg:col-span-7) */}
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
              {/* Responsive SVG Word Cloud */}
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
              * Arahkan kursor ke atas slang kata untuk melacak rincian kategori tingkat keparahan (*severity*).
            </p>
          </m.div>

          {/* Grafik Distribusi Densitas Keyakinan (Confidence Density Chart) (lg:col-span-5) */}
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

                {/* Highlight active learning zone (0.4 - 0.7) */}
                <rect x="176" y="20" width="102" height="140" fill="#fef3c7" className="opacity-25 dark:opacity-[0.06]" />
                <line x1="176" y1="20" x2="176" y2="160" stroke="#f59e0b" strokeDasharray="3 3" strokeWidth="1" className="opacity-60" />
                <line x1="278" y1="20" x2="278" y2="160" stroke="#f59e0b" strokeDasharray="3 3" strokeWidth="1" className="opacity-60" />
                <text x="227" y="15" textAnchor="middle" className="text-[8px] font-bold fill-amber-600 dark:fill-amber-500 uppercase tracking-wider">Zona Ragu (Active Learning)</text>

                {/* Grid Lines */}
                {[40, 80, 120, 160].map(y => (
                  <line key={y} x1="40" y1={y} x2="380" y2={y} stroke="var(--card-border)" strokeWidth="0.5" strokeDasharray="2 2" className="opacity-50" />
                ))}

                {/* Area path for density spline */}
                <path 
                  d="M 40 160 C 80 40, 120 40, 160 110 C 200 150, 240 150, 280 110 C 320 60, 350 65, 380 160 L 380 160 L 40 160 Z" 
                  fill="url(#densityGrad)" 
                />

                {/* Stroke path for density spline */}
                <path 
                  d="M 40 160 C 80 40, 120 40, 160 110 C 200 150, 240 150, 280 110 C 320 60, 350 65, 380 160" 
                  fill="none" 
                  stroke="var(--primary-color)" 
                  strokeWidth="2.5" 
                  strokeLinecap="round" 
                />

                {/* Grid axes */}
                <line x1="40" y1="160" x2="380" y2="160" stroke="var(--card-border)" strokeWidth="1.5" />
                <line x1="40" y1="20" x2="40" y2="160" stroke="var(--card-border)" strokeWidth="1.5" />

                {/* X-axis labels */}
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

                {/* X-axis title */}
                <text x="210" y="192" textAnchor="middle" className="text-[8px] font-bold" fill="var(--text-muted)">Model Confidence Score</text>

                {/* Y-axis title */}
                <text x="15" y="90" textAnchor="middle" transform="rotate(-90 15 90)" className="text-[8px] font-bold" fill="var(--text-muted)">Kerapatan (Density)</text>

                {/* Peak highlights */}
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
