import React, { useState } from 'react';
import { m, AnimatePresence } from 'framer-motion';
import { ArrowRight, UploadCloud, Download } from 'lucide-react';

interface FeaturesShowcaseProps {
  setActiveTab: (tab: any) => void;
}

export default function FeaturesShowcase({ setActiveTab }: FeaturesShowcaseProps) {
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
