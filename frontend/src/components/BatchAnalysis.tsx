import React, { useState } from 'react';
import { m } from 'framer-motion';
import { FileText, Download, Trash2, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { XAIHighlightText } from './XAIHighlightText';
import type { WordImportance } from './XAIHighlightText';

interface PredictionResult {
  text: string;
  is_toxic: boolean;
  is_bully: boolean;
  probability_toxic: number;
  probability_bully: number;
  category: string;
  decision_source: string;
  reason: string;
  word_importances?: WordImportance[];
}

interface BatchAnalysisProps {
  apiUrl: string;
  apiKey: string;
  handleExportCSV: (data: any[]) => void;
}

export default function BatchAnalysis({ apiUrl, apiKey, handleExportCSV }: BatchAnalysisProps) {
  const [batchTexts, setBatchTexts] = useState('');
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResults, setBatchResults] = useState<PredictionResult[]>([]);

  // Hitung frekuensi kata toksik terpopuler
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

  const handleBatchAnalyze = async () => {
    if (!batchTexts.trim()) {
      toast.warning('Silakan masukkan beberapa teks!');
      return;
    }
    const lines = batchTexts.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    if (lines.length === 0) {
      toast.warning('Teks tidak valid!');
      return;
    }

    setBatchLoading(true);
    setBatchResults([]);

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    try {
      const response = await fetch(`${apiUrl}/predict/batch`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ texts: lines.slice(0, 50) }) // Max 50 lines
      });

      if (!response.ok) throw new Error('Batch failed');
      const data = await response.json();
      setBatchResults(data.results || []);
      toast.success(`Berhasil menganalisis ${(data.results || []).length} teks.`);
      setBatchLoading(false);
    } catch (err: any) {
      console.error(err);
      toast.error('Gagal analisis batch. Menjalankan simulasi sandbox offline.');
      
      setTimeout(() => {
        const sim = lines.map(t => {
          const isToxic = t.includes('anjing') || t.includes('goblok') || t.includes('tolol') || t.includes('bangsat');
          const isBully = t.includes('jelek') || t.includes('dasar') || t.includes('bodoh');
          return {
            text: t,
            is_toxic: isToxic,
            is_bully: isBully,
            probability_toxic: isToxic ? 0.95 : 0.02,
            probability_bully: isBully ? 0.88 : 0.05,
            category: isToxic && isBully ? 'Toxic & Bully' : (isToxic ? 'Toxic' : (isBully ? 'Bully' : 'Aman')),
            decision_source: 'Sandbox Batch Fallback',
            reason: 'Hasil simulasi batch local.'
          };
        });
        setBatchResults(sim);
        setBatchLoading(false);
      }, 1000);
    }
  };

  const toxicWords = getToxicWordFrequencies(batchResults);
  const toxicPercentage = batchResults.length > 0 ? Math.round((batchResults.filter(r => r.is_toxic).length / batchResults.length) * 100) : 0;
  const bullyPercentage = batchResults.length > 0 ? Math.round((batchResults.filter(r => r.is_bully).length / batchResults.length) * 100) : 0;

  return (
    <m.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.3 }}
      className="py-6 flex flex-col gap-6"
    >
      <header className="mb-2">
        <h1 className="text-3xl font-black text-gray-900 mb-1">Batch Analisis Teks</h1>
        <p className="text-gray-500 text-sm">Masukkan satu komentar per baris (maksimal 50 baris) untuk deteksi massal cepat.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-6 flex flex-col gap-4">
          <div className="premium-card p-6 flex flex-col gap-4">
            <label className="text-sm font-bold text-gray-950">Daftar Komentar (Satu per baris)</label>
            
            <textarea
              value={batchTexts}
              onChange={(e) => setBatchTexts(e.target.value)}
              placeholder="Contoh:&#10;Keren banget bro!&#10;Dasar cowok bodoh tolol&#10;Gila hebat asu nilaimu naik"
              className="w-full h-72 p-4 bg-gray-50/50 border border-gray-200 rounded-xl outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all text-xs font-mono leading-relaxed resize-none"
            />

            <button
              onClick={handleBatchAnalyze}
              disabled={batchLoading}
              className="w-full bg-blue-600 text-white py-3 rounded-xl text-sm font-bold hover:bg-blue-700 disabled:opacity-50 transition-all cursor-pointer border-none flex items-center justify-center gap-2"
            >
              {batchLoading ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> Memproses...</>
              ) : (
                <>Analisis Batch sekarang</>
              )}
            </button>
          </div>
        </div>

        <div className="lg:col-span-6 flex flex-col gap-4">
          {batchResults.length === 0 ? (
            <div className="premium-card p-8 flex flex-col items-center justify-center text-center min-h-[360px]">
              <div className="w-20 h-20 rounded-full bg-gray-50 flex items-center justify-center border border-gray-100 mb-4 text-gray-400">
                <FileText className="w-9 h-9" />
              </div>
              <h3 className="text-sm font-bold text-gray-800 mb-1">Hasil Batch Teks</h3>
              <p className="text-xs text-gray-400 max-w-xs leading-relaxed">Hasil pemrosesan baris massal teks Anda akan terdaftar di sini.</p>
            </div>
          ) : (
            <m.div 
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col gap-4"
            >
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold text-gray-800">Hasil Pemrosesan ({batchResults.length})</h3>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleExportCSV(batchResults)}
                    className="bg-white border border-gray-200 text-gray-700 text-xs font-semibold px-2.5 py-1.5 rounded-lg hover:bg-gray-50 flex items-center gap-1 cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5 text-blue-500" /> CSV
                  </button>
                  <button
                    onClick={() => setBatchResults([])}
                    className="bg-white border border-gray-200 text-rose-600 text-xs font-semibold px-2.5 py-1.5 rounded-lg hover:bg-rose-50 flex items-center gap-1 cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Hapus
                  </button>
                </div>
              </div>

              {/* Stats Widgets */}
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
              {toxicWords.length > 0 && (
                <div className="premium-card p-4 flex flex-col gap-3">
                  <span className="text-xxs font-bold text-gray-900 uppercase tracking-wider">Kata Kasar Paling Sering Muncul</span>
                  <div className="flex flex-col gap-2.5">
                    {toxicWords.map((item, idx) => {
                      const maxCount = toxicWords[0].count;
                      const widthPercent = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
                      return (
                        <div key={idx} className="flex flex-col gap-1 text-[11px]">
                          <div className="flex justify-between font-bold text-gray-700">
                            <span className="capitalize">{item.word}</span>
                            <span className="text-gray-400">{item.count}x</span>
                          </div>
                          <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-1.5 overflow-hidden">
                            <m.div 
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
              )}

              <div className="premium-card max-h-[220px] overflow-y-auto custom-scrollbar p-3 flex flex-col gap-2 bg-gray-50/30">
                {batchResults.map((item, index) => {
                  const isProblematic = item.is_toxic || item.is_bully;
                  return (
                    <div 
                      key={index} 
                      className={`p-3 rounded-lg border text-xs flex justify-between items-start gap-4 transition-all bg-white dark:bg-zinc-900/50 ${
                        isProblematic ? "border-rose-100 bg-rose-50/10" : "border-emerald-100 bg-emerald-50/10"
                      }`}
                    >
                      <div className="flex-grow text-gray-800 dark:text-gray-200">
                        <p className="font-semibold break-words leading-relaxed">
                          "<XAIHighlightText text={item.text} wordImportances={item.word_importances} />"
                        </p>
                        <p className="text-xxs text-gray-400 mt-1 font-mono">Source: {item.decision_source}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider shrink-0 ${
                        isProblematic ? "bg-rose-100 text-rose-700" : "bg-emerald-100 text-emerald-700"
                      }`}>
                        {item.category.replace(' (Serangan Langsung)', '')}
                      </span>
                    </div>
                  );
                })}
              </div>
            </m.div>
          )}
        </div>
      </div>
    </m.div>
  );
}
