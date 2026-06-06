import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Download, Trash2, RefreshCw, Globe } from 'lucide-react';
import { toast } from 'sonner';
import { SkeletonTableRow, SkeletonStatsWidget, SkeletonFreqWidget } from './SkeletonLoader';

interface PredictionResult {
  text: string;
  is_toxic: boolean;
  is_bully: boolean;
  probability_toxic: number;
  probability_bully: number;
  category: string;
  decision_source: string;
  reason: string;
}

interface SocialScraperProps {
  apiUrl: string;
  apiKey: string;
  handleExportCSV: (data: any[]) => void;
}

export default function SocialScraper({ apiUrl, apiKey, handleExportCSV }: SocialScraperProps) {
  const [socialUrl, setSocialUrl] = useState('');
  const [maxComments, setMaxComments] = useState<number | ''>(15);
  const [scrapingLoading, setScrapingLoading] = useState(false);
  const [scrapedResults, setScrapedResults] = useState<PredictionResult[]>([]);
  const [detectedPlatform, setDetectedPlatform] = useState<'tiktok' | 'x' | null>(null);

  // Hitung frekuensi kata kasar terpopuler
  const getToxicWordFrequencies = (results: PredictionResult[]) => {
    const listWords = ["anjing", "goblok", "tolol", "bego", "sampah", "idiot", "mati", "kasar", "bangsat", "gila", "bodoh", "perek", "cabul", "memek", "kontol", "bajingan"];
    const counts: Record<string, number> = {};
    
    results.forEach(item => {
      if (item.is_toxic || item.is_bully) {
        const normalizedText = item.text.toLowerCase();
        listWords.forEach(word => {
          if (normalizedText.includes(word)) {
            counts[word] = (counts[word] || 0) + 1;
          }
        });
      }
    });

    return Object.entries(counts)
      .map(([word, count]) => ({ word, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  };

  useEffect(() => {
    const trimmed = socialUrl.trim();
    if (trimmed.includes('tiktok.com')) {
      setDetectedPlatform('tiktok');
    } else if (trimmed.includes('x.com') || trimmed.includes('twitter.com') || trimmed.includes('/status/')) {
      setDetectedPlatform('x');
    } else {
      setDetectedPlatform(null);
    }
  }, [socialUrl]);

  const handleScrapeAndAnalyze = async () => {
    if (!socialUrl.trim()) {
      toast.warning('Tautan tidak boleh kosong!');
      return;
    }
    if (!detectedPlatform) {
      toast.warning('Tautan harus berupa tautan TikTok atau X (Twitter) yang valid.');
      return;
    }

    setScrapingLoading(true);
    setScrapedResults([]);

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    const endpoint = detectedPlatform === 'tiktok' ? '/api/scrape/tiktok' : '/api/scrape/x';
    const payload = detectedPlatform === 'tiktok' 
      ? { url: socialUrl, max_comments: maxComments || 15 }
      : { url: socialUrl, max_tweets: maxComments || 15 };

    try {
      toast.info(`Menghubungi scraper untuk menarik data dari ${detectedPlatform.toUpperCase()}...`);
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Scraping failed');
      const data = await response.json();
      
      const scrapedTexts: string[] = data.data || [];
      if (scrapedTexts.length === 0) {
        toast.info('Scraper berhasil dijalankan, namun tidak ada komentar baru yang ditemukan.');
        setScrapingLoading(false);
        return;
      }

      toast.info(`Berhasil menarik ${scrapedTexts.length} data. Melakukan analisis batch...`);
      
      const batchRes = await fetch(`${apiUrl}/predict/batch`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ texts: scrapedTexts })
      });

      if (!batchRes.ok) throw new Error('Batch analysis failed');
      const batchData = await batchRes.json();
      setScrapedResults(batchData.results || []);
      toast.success(`Berhasil memuat dan menganalisis ${(batchData.results || []).length} komentar!`);
      setScrapingLoading(false);
    } catch (err: any) {
      console.error(err);
      toast.error('Gagal scraping otomatis. Menjalankan simulasi data media sosial.');
      
      // Local simulated comments fallback
      setTimeout(() => {
        const mockComments = detectedPlatform === 'tiktok' ? [
          'Keren banget videonya kak! menginspirasi',
          'dasar cewek matre, pamer harta terus goblok',
          'cantik banget kak, sehat selalu yaaa',
          'jujur ini konten paling aneh sih, ga mutu banget',
          'hebat banget anjing, ga nyangka bisa gini!'
        ] : [
          'Info penting nih, makasih ya min',
          'akun sampah, sebar hoax terus kerjanya bego banget',
          'semoga sukses terus usahanya!',
          'wah pinter banget ya lo, ampe nilai nol bangga spakbor mio',
          'gila keren abis aksinya!'
        ];

        const mockAnalyses = mockComments.map(t => {
          const lower = t.toLowerCase();
          const isToxic = lower.includes('goblok') || lower.includes('anjing') || lower.includes('bego') || lower.includes('sampah');
          const isBully = lower.includes('matre') || lower.includes('bejo') || lower.includes('mio') || lower.includes('hoax') || lower.includes('sampah');
          let category = 'Non-Toxic & Non-Bully (Aman)';
          if (isToxic && isBully) category = 'Toxic & Bully (Serangan Langsung)';
          else if (isToxic) category = 'Toxic but Non-Bully (Casual Slang / Swearing)';
          else if (isBully) category = 'Non-Toxic but Bully (Sarcasm / Insult)';

          return {
            text: t,
            is_toxic: isToxic,
            is_bully: isBully,
            probability_toxic: isToxic ? 0.9 : 0.05,
            probability_bully: isBully ? 0.85 : 0.1,
            category,
            decision_source: 'Sandbox Scraper Fallback',
            reason: isToxic || isBully ? 'Terdeteksi unsur kata kasar/bully bermasalah.' : 'Komentar aman.'
          };
        });

        setScrapedResults(mockAnalyses);
        toast.success(`Simulasi: Memuat ${mockAnalyses.length} komentar dari ${detectedPlatform.toUpperCase()}.`);
        setScrapingLoading(false);
      }, 1500);
    }
  };

  const handleReallocate = async (text: string, newIsToxic: boolean, newIsBully: boolean) => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    try {
      const response = await fetch(`${apiUrl}/api/data/reallocate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          text,
          new_is_toxic: newIsToxic,
          new_is_bully: newIsBully
        })
      });

      if (!response.ok) throw new Error('Reallocate failed');
      const data = await response.json();
      if (data.success) {
        toast.success('Kategori data berhasil diubah & divalidasi!');
        // Update local state directly
        setScrapedResults(prev => prev.map(item => {
          if (item.text === text) {
            let cat = 'Non-Toxic & Non-Bully (Aman)';
            if (newIsToxic && newIsBully) cat = 'Toxic & Bully (Serangan Langsung)';
            else if (newIsToxic) cat = 'Toxic but Non-Bully (Casual Slang / Swearing)';
            else if (newIsBully) cat = 'Non-Toxic but Bully (Sarcasm / Insult)';
            return {
              ...item,
              is_toxic: newIsToxic,
              is_bully: newIsBully,
              category: cat
            };
          }
          return item;
        }));
      } else {
        toast.error(data.message || 'Gagal mengubah kategori.');
      }
    } catch (err: any) {
      console.error(err);
      toast.success('Simulasi: Sukses mengubah label data di sandbox lokal.');
      setScrapedResults(prev => prev.map(item => {
        if (item.text === text) {
          let cat = 'Non-Toxic & Non-Bully (Aman)';
          if (newIsToxic && newIsBully) cat = 'Toxic & Bully (Serangan Langsung)';
          else if (newIsToxic) cat = 'Toxic but Non-Bully (Casual Slang / Swearing)';
          else if (newIsBully) cat = 'Non-Toxic but Bully (Sarcasm / Insult)';
          return {
            ...item,
            is_toxic: newIsToxic,
            is_bully: newIsBully,
            category: cat
          };
        }
        return item;
      }));
    }
  };

  const toxicWords = getToxicWordFrequencies(scrapedResults);
  const toxicPercentage = scrapedResults.length > 0 ? Math.round((scrapedResults.filter(r => r.is_toxic).length / scrapedResults.length) * 100) : 0;
  const bullyPercentage = scrapedResults.length > 0 ? Math.round((scrapedResults.filter(r => r.is_bully).length / scrapedResults.length) * 100) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.3 }}
      className="py-6 flex flex-col gap-6"
    >
      <header className="mb-2">
        <h1 className="text-3xl font-black text-gray-900 mb-1">Scraper &amp; Analisis Tautan Sosmed</h1>
        <p className="text-gray-500 text-sm">Tempel tautan video TikTok atau tweet X (Twitter) untuk mengikis komentar dan menganalisisnya secara massal.</p>
      </header>

      {/* Input URL card */}
      <div className="premium-card p-6 flex flex-col md:flex-row gap-4 items-center">
        <div className="flex-grow w-full relative">
          <input
            type="text"
            value={socialUrl}
            onChange={(e) => setSocialUrl(e.target.value)}
            placeholder="Tempel tautan TikTok (video) atau X (tweet status) di sini..."
            className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 outline-none text-sm text-gray-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all font-medium"
          />
          <div className="absolute left-3.5 top-3.5 text-gray-400">
            <Search className="w-4.5 h-4.5" />
          </div>
        </div>
        
        <div className="flex items-center gap-3 w-full md:w-auto">
          {/* Max comment input */}
          <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-1.5 shrink-0">
            <span className="text-xxs text-gray-400 font-bold uppercase">Limit:</span>
            <input
              type="number"
              min="1"
              max="100"
              value={maxComments === '' ? '' : maxComments}
              onChange={(e) => {
                const val = e.target.value;
                if (val === '') {
                  setMaxComments('');
                } else {
                  const num = parseInt(val, 10);
                  if (!isNaN(num)) {
                    setMaxComments(Math.max(1, Math.min(100, num)));
                  }
                }
              }}
              className="w-10 bg-transparent border-none outline-none text-sm font-bold text-gray-700"
            />
          </div>

          <button
            onClick={handleScrapeAndAnalyze}
            disabled={scrapingLoading || !detectedPlatform}
            className="flex-grow md:flex-grow-0 bg-blue-600 text-white px-6 py-3 rounded-xl text-sm font-bold hover:bg-blue-700 active-press disabled:opacity-50 transition-all cursor-pointer border-none flex items-center justify-center gap-2 whitespace-nowrap"
          >
            {scrapingLoading ? (
              <><RefreshCw className="w-4 h-4 animate-spin" /> Scraping...</>
            ) : (
              <>Tarik &amp; Analisis</>
            )}
          </button>
        </div>
      </div>

      {/* Platform indicator badge */}
      {socialUrl.trim().length > 0 && (
        <div className="flex items-center gap-2 mt-[-12px] px-2">
          {detectedPlatform === 'tiktok' ? (
            <span className="text-xxs bg-emerald-50 text-emerald-700 border border-emerald-100 rounded px-2 py-0.5 font-bold uppercase tracking-wider flex items-center gap-1 animate-fade-in">
              ✓ Video TikTok Terdeteksi (Spesifik Postingan Video)
            </span>
          ) : detectedPlatform === 'x' ? (
            <span className="text-xxs bg-indigo-50 text-indigo-700 border border-indigo-100 rounded px-2 py-0.5 font-bold uppercase tracking-wider flex items-center gap-1 animate-fade-in">
              ✓ Tweet X Terdeteksi (Scrape Balasan/Replies Spesifik)
            </span>
          ) : (
            <span className="text-xxs bg-rose-50 text-rose-700 border border-rose-100 rounded px-2 py-0.5 font-bold uppercase tracking-wider flex items-center gap-1">
              ✗ Tautan Tidak Dikenali (Gunakan Video TikTok / Tweet Status)
            </span>
          )}
        </div>
      )}

      {/* Placeholder saat belum ada hasil — menjaga tinggi halaman konsisten */}
      {scrapedResults.length === 0 && !scrapingLoading && (
        <div className="premium-card p-10 flex flex-col items-center justify-center text-center min-h-[350px]">
          <div className="w-20 h-20 rounded-full bg-gray-50 dark:bg-white/5 flex items-center justify-center border border-gray-100 mb-4">
            <Globe className="w-9 h-9 text-gray-300" />
          </div>
          <h3 className="text-sm font-bold text-gray-800 mb-1">Belum Ada Data Scraping</h3>
          <p className="text-xs text-gray-400 max-w-sm leading-relaxed">
            Tempel tautan video TikTok atau tweet X/Twitter di atas, lalu klik <strong>"Tarik & Analisis"</strong> untuk mengikis dan mengklasifikasikan komentar secara otomatis.
          </p>
        </div>
      )}

      {/* Loading Skeletons */}
      {scrapingLoading && (
        <div className="flex flex-col gap-4 animate-fade-in">
          <h3 className="text-sm font-bold text-gray-850 dark:text-gray-200 flex items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
            Sedang Menarik &amp; Menganalisis Komentar...
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="grid grid-cols-2 gap-4">
              <SkeletonStatsWidget />
              <SkeletonStatsWidget />
            </div>
            <SkeletonFreqWidget />
          </div>
          <div className="premium-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-xs text-gray-500">
                <thead className="bg-gray-50 dark:bg-gray-850 text-xxs font-bold text-gray-400 uppercase border-b border-gray-100 dark:border-gray-800">
                  <tr>
                    <th className="px-6 py-3">Komentar / Teks</th>
                    <th className="px-6 py-3">Klasifikasi</th>
                    <th className="px-6 py-3">Toxic %</th>
                    <th className="px-6 py-3">Bully %</th>
                    <th className="px-6 py-3 text-right">Aksi HITL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <SkeletonTableRow key={n} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Results list */}
      {scrapedResults.length > 0 && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-4"
        >
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-bold text-gray-800">
              Hasil Scraping &amp; Klasifikasi ({scrapedResults.length} komentar)
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => handleExportCSV(scrapedResults)}
                className="bg-white border border-gray-200 text-gray-700 text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-gray-50 flex items-center gap-1.5 cursor-pointer"
              >
                <Download className="w-3.5 h-3.5 text-blue-500" /> Ekspor CSV
              </button>
              <button
                onClick={() => setScrapedResults([])}
                className="bg-white border border-gray-200 text-rose-600 text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-rose-50 flex items-center gap-1.5 cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" /> Hapus Hasil
              </button>
            </div>
          </div>

          {/* Stats Widgets & Analytics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="premium-card p-4 flex flex-col justify-center items-center text-center bg-rose-50/5 border border-rose-100/10">
                <span className="text-xxs font-bold text-gray-400 uppercase tracking-wider">Kepadatan Toksisitas</span>
                <span className="text-2xl font-black text-rose-500 mt-1">{toxicPercentage}%</span>
              </div>
              <div className="premium-card p-4 flex flex-col justify-center items-center text-center bg-indigo-50/5 border border-indigo-100/10">
                <span className="text-xxs font-bold text-gray-400 uppercase tracking-wider">Rasio Bullying</span>
                <span className="text-2xl font-black text-indigo-500 mt-1">{bullyPercentage}%</span>
              </div>
            </div>

            {/* Word Frequency Bar Chart */}
            {toxicWords.length > 0 ? (
              <div className="premium-card p-4 flex flex-col gap-3">
                <span className="text-xxs font-bold text-gray-900 uppercase tracking-wider">Kata Kasar Paling Sering Muncul</span>
                <div className="flex flex-col gap-2">
                  {toxicWords.map((item, idx) => {
                    const maxCount = toxicWords[0].count;
                    const widthPercent = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
                    return (
                      <div key={idx} className="flex flex-col gap-0.5 text-[11px]">
                        <div className="flex justify-between font-bold text-gray-700">
                          <span className="capitalize">{item.word}</span>
                          <span className="text-gray-400">{item.count}x</span>
                        </div>
                        <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-1 overflow-hidden">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${widthPercent}%` }}
                            transition={{ duration: 0.6, delay: idx * 0.08 }}
                            className="bg-gradient-to-r from-rose-500 to-indigo-500 h-full rounded-full"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="premium-card p-4 flex items-center justify-center text-center text-xs text-gray-400 font-medium">
                Tidak terdeteksi kata kasar yang signifikan dari konten media sosial ini.
              </div>
            )}
          </div>

          <div className="premium-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-xs text-gray-500">
                <thead className="bg-gray-50 text-xxs font-bold text-gray-400 uppercase border-b border-gray-100">
                  <tr>
                    <th className="px-6 py-3">Komentar / Teks</th>
                    <th className="px-6 py-3">Klasifikasi</th>
                    <th className="px-6 py-3">Toxic %</th>
                    <th className="px-6 py-3">Bully %</th>
                    <th className="px-6 py-3 text-right">Aksi HITL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {scrapedResults.map((item, index) => {
                    const isProblematic = item.is_toxic || item.is_bully;
                    return (
                      <tr key={index} className="hover:bg-gray-50/50">
                        <td className="px-6 py-4 font-medium text-gray-800 max-w-sm truncate" title={item.text}>
                          {item.text}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            isProblematic ? "bg-rose-100 text-rose-700" : "bg-emerald-100 text-emerald-700"
                          }`}>
                            {item.category.replace(' (Serangan Langsung)', '').replace(' (Casual Slang / Swearing)', '')}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-bold text-gray-700">
                          {Math.round(item.probability_toxic * 100)}%
                        </td>
                        <td className="px-6 py-4 font-bold text-gray-700">
                          {Math.round(item.probability_bully * 100)}%
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex justify-end gap-1.5">
                            <button
                              onClick={() => handleReallocate(item.text, true, true)}
                              title="Koreksi ke: Toxic & Bully"
                              className="px-2 py-1 hover:bg-rose-50 text-rose-500 text-[10px] font-bold rounded border border-gray-200 cursor-pointer"
                            >
                              T&amp;B
                            </button>
                            <button
                              onClick={() => handleReallocate(item.text, true, false)}
                              title="Koreksi ke: Toxic Non-Bully"
                              className="px-2 py-1 hover:bg-amber-50 text-amber-600 text-[10px] font-bold rounded border border-gray-200 cursor-pointer"
                            >
                              T&amp;NB
                            </button>
                            <button
                              onClick={() => handleReallocate(item.text, false, true)}
                              title="Koreksi ke: Non-Toxic but Bully"
                              className="px-2 py-1 hover:bg-purple-50 text-purple-600 text-[10px] font-bold rounded border border-gray-200 cursor-pointer"
                            >
                              NT&amp;B
                            </button>
                            <button
                              onClick={() => handleReallocate(item.text, false, false)}
                              title="Koreksi ke: Non-Toxic (Aman)"
                              className="px-2 py-1 hover:bg-emerald-50 text-emerald-600 text-[10px] font-bold rounded border border-gray-200 cursor-pointer"
                            >
                              Aman
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
