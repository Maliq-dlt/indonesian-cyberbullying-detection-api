import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertTriangle, Check, CheckCircle, Activity, Search, RefreshCw, HelpCircle, X, Info
} from 'lucide-react';
import { toast } from 'sonner';
import { XAIHighlightText } from './XAIHighlightText';
import type { WordImportance } from './XAIHighlightText';

interface NormalizationStep {
  name: string;
  value: string;
}

interface PredictionResult {
  text: string;
  is_toxic: boolean;
  is_bully: boolean;
  probability_toxic: number;
  probability_bully: number;
  category: string;
  decision_source: string;
  reason: string;
  normalization_steps?: NormalizationStep[];
  word_importances?: WordImportance[];
  execution_time?: number;
}

interface DetectorProps {
  apiUrl: string;
  apiKey: string;
}

export default function Detector({ apiUrl, apiKey }: DetectorProps) {
  const [detectorText, setDetectorText] = useState('');
  const [selectedModel, setSelectedModel] = useState<'hybrid' | 'lexicon' | 'ml' | 'transformers' | 'ensemble' | 'comparison'>('hybrid');
  const [useFuzzy, setUseFuzzy] = useState(false);
  const [detectorLoading, setDetectorLoading] = useState(false);
  const [detectorResult, setDetectorResult] = useState<PredictionResult | null>(null);

  // Comparison results state
  const [comparisonResults, setComparisonResults] = useState<any[] | null>(null);

  // XAI Side Drawer State
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleAnalyzeComparison = async () => {
    if (detectorText.trim().length === 0) {
      toast.error('Masukkan teks terlebih dahulu!');
      return;
    }
    if (detectorText.length > 500) {
      toast.error('Teks tidak boleh melebihi 500 karakter!');
      return;
    }
    setDetectorLoading(true);
    setComparisonResults(null);
    setDetectorResult(null);
    setIsDrawerOpen(false);

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    const endpoints = [
      { name: 'Hybrid AI', path: '/predict/hybrid' },
      { name: 'Lexicon', path: '/predict/lexicon', payload: { use_fuzzy: useFuzzy } },
      { name: 'Machine Learning', path: '/predict/ml' },
      { name: 'Transformer (DL)', path: '/predict/transformers' },
      { name: 'Ensemble', path: '/predict/ensemble' },
    ];

    try {
      const promises = endpoints.map(async (ep) => {
        try {
          const body: any = { text: detectorText };
          if (ep.payload) {
            Object.assign(body, ep.payload);
          }
          const start = performance.now();
          const response = await fetch(`${apiUrl}${ep.path}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(body)
          });
          const elapsed = performance.now() - start;
          if (!response.ok) throw new Error('Offline');
          const data = await response.json();
          return {
            name: ep.name,
            is_toxic: data.is_toxic !== undefined ? data.is_toxic : data.is_cyberbullying,
            is_bully: data.is_bully !== undefined ? data.is_bully : data.is_cyberbullying,
            probability_toxic: data.probability_toxic || (data.score ? data.score / 10 : 0.1),
            probability_bully: data.probability_bully || (data.score ? data.score / 10 : 0.1),
            category: data.category || (data.risk_label ? `Risiko ${data.risk_label}` : 'Aman'),
            decision_source: data.decision_source || ep.name,
            reason: data.reason || 'Selesai dianalisis.',
            word_importances: data.word_importances || [],
            status: 'ONLINE',
            execution_time: data.execution_time || parseFloat(elapsed.toFixed(2))
          };
        } catch (err) {
          return {
            name: ep.name,
            status: 'OFFLINE',
            is_toxic: false,
            is_bully: false,
            probability_toxic: 0,
            probability_bully: 0,
            category: '-',
            reason: 'Model sedang dinonaktifkan di backend.',
            word_importances: [],
            execution_time: 0
          };
        }
      });

      const results = await Promise.all(promises);
      setComparisonResults(results);
      
      const defaultRes = results.find(r => r.name === 'Hybrid AI' && r.status === 'ONLINE') || results.find(r => r.status === 'ONLINE');
      if (defaultRes) {
        setDetectorResult({
          text: detectorText,
          is_toxic: defaultRes.is_toxic,
          is_bully: defaultRes.is_bully,
          probability_toxic: defaultRes.probability_toxic,
          probability_bully: defaultRes.probability_bully,
          category: defaultRes.category,
          decision_source: defaultRes.decision_source,
          reason: defaultRes.reason,
          word_importances: defaultRes.word_importances
        });
      } else {
        toast.error('Semua model di server offline.');
      }
      toast.success('Analisis perbandingan selesai!');
    } catch (err) {
      console.error(err);
      toast.error('Gagal melakukan analisis perbandingan.');
    } finally {
      setDetectorLoading(false);
    }
  };

  const handleAnalyzeSingle = async () => {
    if (detectorText.trim().length === 0) {
      toast.error('Masukkan teks terlebih dahulu!');
      return;
    }
    if (detectorText.length > 500) {
      toast.error('Teks tidak boleh melebihi 500 karakter!');
      return;
    }
    setDetectorLoading(true);
    setDetectorResult(null);
    setIsDrawerOpen(false);

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    let endpoint = '/predict/hybrid';
    if (selectedModel === 'lexicon') endpoint = '/predict/lexicon';
    else if (selectedModel === 'ml') endpoint = '/predict/ml';
    else if (selectedModel === 'transformers') endpoint = '/predict/transformers';
    else if (selectedModel === 'ensemble') endpoint = '/predict/ensemble';

    try {
      const payload: any = { text: detectorText };
      if (selectedModel === 'lexicon') {
        payload.use_fuzzy = useFuzzy;
      }

      const startTime = performance.now();
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });
      const elapsed = performance.now() - startTime;

      if (!response.ok) throw new Error(`Error: ${response.statusText}`);
      const data = await response.json();
      
      const result: PredictionResult = {
        text: detectorText,
        is_toxic: data.is_toxic !== undefined ? data.is_toxic : data.is_cyberbullying,
        is_bully: data.is_bully !== undefined ? data.is_bully : data.is_cyberbullying,
        probability_toxic: data.probability_toxic || (data.score ? data.score / 10 : 0.1),
        probability_bully: data.probability_bully || (data.score ? data.score / 10 : 0.1),
        category: data.category || (data.risk_label ? `Risiko ${data.risk_label}` : 'Aman'),
        decision_source: data.decision_source || (selectedModel === 'lexicon' ? 'Lexicon Model' : 'Model Core'),
        reason: data.reason || (data.matches && data.matches.length > 0 ? `Ditemukan kata ofensif: ${data.matches.map((m: any) => m.matched_phrase).join(', ')}` : 'Tidak ditemukan pola penyerangan atau toksisitas.'),
        word_importances: data.word_importances || [],
        execution_time: data.execution_time || parseFloat(elapsed.toFixed(2))
      };

      const cleanText = data.normalized_spaced || detectorText.toLowerCase();
      result.normalization_steps = [
        { name: 'Input Mentah', value: `"${detectorText}"` },
        { name: 'Pembersihan & Lowercase', value: `"${detectorText.toLowerCase()}"` },
        { name: 'Normalisasi Slang / Alay', value: `"${cleanText}"` },
        { name: 'Final Tokens', value: JSON.stringify(cleanText.split(' ')) }
      ];

      setDetectorResult(result);
      toast.success('Analisis teks selesai!');
      setDetectorLoading(false);
    } catch (err: any) {
      console.error(err);
      toast.error('Gagal analisis. Menjalankan simulasi sandbox offline.');
      
      // Local fallback simulation
      setTimeout(() => {
        const text = detectorText.toLowerCase();
        let isToxic = false;
        let isBully = false;
        let reason = 'Teks dianalisis bersih dari indikasi cyberbullying atau toksisitas.';
        let category = 'Non-Toxic & Non-Bully (Aman)';

        if (text.includes('anjing') || text.includes('goblok') || text.includes('tolol') || text.includes('bego')) {
          isToxic = true;
          reason = 'Terdeteksi kata kasar/abusive language.';
          category = 'Toxic but Non-Bully (Casual Slang / Swearing)';
        }
        if (text.includes('dasar') || text.includes('jelek') || text.includes('mati aja')) {
          isBully = true;
          reason = 'Mengandung indikasi intimidasi atau serangan pribadi langsung.';
          if (isToxic) {
            category = 'Toxic & Bully (Serangan Langsung)';
          } else {
            category = 'Non-Toxic but Bully (Sarcasm / Insult)';
          }
        }

        // Generate mockup word importances for offline sandbox
        const words = text.split(/\s+/);
        const importances: WordImportance[] = words.map(w => {
          let wt = 0.02;
          let wb = 0.01;
          if (w.includes('anjing') || w.includes('goblok') || w.includes('tolol') || w.includes('bego')) {
            wt = 0.85;
            wb = 0.35;
          } else if (w.includes('dasar') || w.includes('jelek') || w.includes('mati')) {
            wt = 0.22;
            wb = 0.78;
          }
          return { word: w, weight_toxic: wt, weight_bully: wb };
        });

        setDetectorResult({
          text: detectorText,
          is_toxic: isToxic,
          is_bully: isBully,
          probability_toxic: isToxic ? 0.88 : 0.08,
          probability_bully: isBully ? 0.79 : 0.12,
          category,
          decision_source: 'Sandbox Offline Fallback',
          reason,
          word_importances: importances,
          normalization_steps: [
            { name: 'Input Mentah', value: `"${detectorText}"` },
            { name: 'Lowercase', value: `"${text}"` },
            { name: 'Normalisasi Kata', value: `"${text}"` },
            { name: 'Final Tokens', value: JSON.stringify(text.split(' ')) }
          ]
        });
        setDetectorLoading(false);
      }, 800);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.3 }}
      className="py-6 flex flex-col gap-6"
    >
      <header className="mb-2">
        <h1 className="text-3xl font-black text-gray-900 mb-1">Detektor Teks Tunggal</h1>
        <p className="text-gray-500 text-sm">Uji dan analisis kalimat untuk mendeteksi cyberbullying, toksisitas, dan profanity secara detail.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Input Form Column */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <div className="premium-card p-6 flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <label className="text-sm font-bold text-gray-900">Masukkan Kalimat / Komentar</label>
              <span className="text-xxs font-semibold bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Bahasa Indonesia</span>
            </div>
            
            <div className="relative border border-gray-200 bg-gray-50/50 rounded-xl focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100 transition-all">
              <textarea 
                value={detectorText}
                onChange={(e) => setDetectorText(e.target.value)}
                placeholder="Contoh: 'Semangat belajarnya ya!' atau 'kamu tolol banget sih goblok'"
                className="w-full h-36 p-4 bg-transparent border-none outline-none text-sm text-gray-800 resize-none font-medium placeholder:text-gray-400"
                maxLength={500}
              />
            </div>

            <div className="flex justify-between items-center text-xs text-gray-400">
              <span className="font-semibold">{detectorText.length} / 500 karakter</span>
              {detectorText.length > 500 && (
                <span className="text-rose-500 font-semibold">Melebihi batas maksimal</span>
              )}
            </div>
          </div>

          {/* Model Configuration */}
          <div className="premium-card p-6 flex flex-col gap-4">
            <div>
              <h3 className="text-sm font-bold text-gray-900 mb-2.5">Pilih Model Pendeteksian</h3>
              <div className="flex flex-wrap gap-2">
                {[
                  { id: 'hybrid', label: 'Hybrid AI', badge: 'Rekomendasi' },
                  { id: 'lexicon', label: 'Lexicon' },
                  { id: 'ml', label: 'Machine Learning' },
                  { id: 'transformers', label: 'Transformer (DL)' },
                  { id: 'ensemble', label: 'Ensemble' },
                  { id: 'comparison', label: 'Audit Multi-Model 🧪', badge: 'New' }
                ].map(model => (
                  <button
                    key={model.id}
                    onClick={() => setSelectedModel(model.id as any)}
                    className={`px-3.5 py-2 rounded-full text-xs font-semibold border transition-all duration-200 cursor-pointer ${
                      selectedModel === model.id
                        ? "bg-blue-50 border-blue-200 text-blue-600 shadow-sm"
                        : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"
                    }`}
                  >
                    {model.label}
                    {model.badge && (
                      <span className="ml-1 bg-blue-600 text-white font-bold px-1.5 py-0.5 rounded-full text-[9px] uppercase tracking-wider">{model.badge}</span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Lexicon Specific Toggle */}
            {(selectedModel === 'lexicon' || selectedModel === 'comparison') && (
              <div className="bg-gray-50 border border-gray-100 p-3 rounded-lg flex items-center justify-between transition-all animate-fade-in">
                <div className="flex items-center gap-2 text-xs text-gray-600 font-medium">
                  <CheckCircle className="w-4 h-4 text-gray-400" />
                  Gunakan Fuzzy Matching untuk Model Lexicon
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={useFuzzy}
                    onChange={(e) => setUseFuzzy(e.target.checked)}
                    className="sr-only peer" 
                  />
                  <div className="w-9 h-5 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600" />
                </label>
              </div>
            )}

            <button
              onClick={selectedModel === 'comparison' ? handleAnalyzeComparison : handleAnalyzeSingle}
              disabled={detectorLoading || detectorText.trim().length === 0 || detectorText.length > 500}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-xl text-sm font-bold hover:shadow-lg hover:shadow-blue-500/20 active:scale-98 transition-all disabled:opacity-50 cursor-pointer border-none flex items-center justify-center gap-2"
            >
              {detectorLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Menganalisis...
                </>
              ) : (
                <>
                  <Activity className="w-4 h-4" /> Analisis Sekarang
                </>
              )}
            </button>
          </div>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-5 h-full">
          {!detectorResult && !comparisonResults ? (
            <div className="premium-card p-8 flex flex-col items-center justify-center text-center min-h-[400px]">
              <div className="w-24 h-24 rounded-full bg-gray-50 flex items-center justify-center border border-gray-100 mb-4 text-gray-400">
                <Search className="w-10 h-10" />
              </div>
              <h3 className="text-sm font-bold text-gray-800 mb-1">Menunggu Input Analisis</h3>
              <p className="text-xs text-gray-400 max-w-xs leading-relaxed">Masukkan kalimat atau teks di panel kiri, pilih model dan klik tombol Analisis Sekarang.</p>
            </div>
          ) : selectedModel === 'comparison' && comparisonResults ? (
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="premium-card p-5 flex flex-col gap-4 border border-gray-150"
            >
              <div className="border-b border-gray-100 dark:border-gray-800/60 pb-3 flex justify-between items-start">
                <div>
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Hasil Perbandingan Multi-Model</span>
                  <h3 className="text-sm font-bold text-gray-900 dark:text-gray-200 leading-tight">Auditing Diagnosis AI</h3>
                </div>
                {detectorResult && detectorResult.word_importances && detectorResult.word_importances.length > 0 && (
                  <button
                    onClick={() => setIsDrawerOpen(true)}
                    className="text-[10px] font-bold text-blue-600 dark:text-indigo-400 hover:underline flex items-center gap-1 cursor-pointer bg-transparent border-none p-0"
                  >
                    Detail XAI &rarr;
                  </button>
                )}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="text-[10px] font-black text-gray-400 uppercase border-b border-gray-100 dark:border-gray-800/60">
                      <th className="pb-2">Model</th>
                      <th className="pb-2 text-center">Status</th>
                      <th className="pb-2 text-center">Verdict</th>
                      <th className="pb-2 text-right">Toxic</th>
                      <th className="pb-2 text-right">Bully</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100/50 dark:divide-gray-800/40">
                    {comparisonResults.map((res, i) => {
                      const isDanger = res.is_toxic || res.is_bully;
                      const isResCacheHit = res.status === 'ONLINE' && (
                        (res.execution_time !== undefined && res.execution_time <= 3.0) ||
                        /cache|database|semantic/i.test(res.decision_source || '')
                      );
                      return (
                        <tr key={i} className="hover:bg-gray-50/50 dark:hover:bg-slate-900/40 transition-colors">
                          <td className="py-2.5 font-bold text-gray-850 dark:text-gray-200">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span>{res.name}</span>
                              {isResCacheHit && (
                                <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-tighter bg-gradient-to-r from-blue-500/10 to-indigo-500/10 text-blue-600 dark:text-indigo-400 border border-blue-400/20 shadow-xxs animate-pulse" title="Semantic Cache Bypass (Resource Saved)">
                                  🚀 Cache Hit
                                </span>
                              )}
                            </div>
                            {res.status === 'ONLINE' && res.execution_time !== undefined && (
                              <div className="text-[9px] text-gray-400 dark:text-gray-500 font-mono font-normal">⏱️ {res.execution_time}ms</div>
                            )}
                          </td>
                          <td className="py-2.5 text-center">
                            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                              res.status === 'ONLINE' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30' : 'bg-gray-100 text-gray-400 dark:bg-slate-800'
                            }`}>
                              {res.status}
                            </span>
                          </td>
                          <td className="py-2.5 text-center">
                            {res.status === 'OFFLINE' ? (
                              <span className="text-gray-400">-</span>
                            ) : (
                              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                                isDanger ? 'bg-rose-50 text-rose-600 dark:bg-rose-950/30' : 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30'
                              }`}>
                                {isDanger ? 'Bahaya' : 'Aman'}
                              </span>
                            )}
                          </td>
                          <td className="py-2.5 text-right font-mono font-bold text-gray-650 dark:text-gray-300">
                            {res.status === 'OFFLINE' ? '-' : `${Math.round(res.probability_toxic * 100)}%`}
                          </td>
                          <td className="py-2.5 text-right font-mono font-bold text-gray-650 dark:text-gray-300">
                            {res.status === 'OFFLINE' ? '-' : `${Math.round(res.probability_bully * 100)}%`}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="flex flex-col gap-2 mt-2">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Hasil Analisis &amp; Penjelasan</span>
                <div className="flex flex-col gap-2">
                  {comparisonResults.map((res, i) => {
                    if (res.status === 'OFFLINE') return null;
                    return (
                      <div key={i} className="bg-gray-50/50 dark:bg-slate-950/20 border border-gray-100 dark:border-gray-800/40 p-2.5 rounded-lg text-[10px] leading-relaxed">
                        <strong className="text-gray-800 dark:text-gray-300">{res.name}:</strong>{' '}
                        <span className="text-gray-500 dark:text-gray-400">{res.reason}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          ) : detectorResult ? (
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className={`premium-card overflow-hidden transition-all duration-300 border border-solid ${
                detectorResult.is_toxic || detectorResult.is_bully
                  ? "border-rose-100"
                  : "border-emerald-100"
              }`}
            >
              {/* Header */}
              <div className={`p-5 border-b flex justify-between items-start ${
                detectorResult.is_toxic || detectorResult.is_bully
                  ? "bg-rose-50/60 border-rose-100 text-rose-800"
                  : "bg-emerald-50/60 border-emerald-100 text-emerald-800"
              }`}>
                <div>
                  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xxs font-bold uppercase tracking-wider mb-2 ${
                    detectorResult.is_toxic || detectorResult.is_bully
                      ? "bg-rose-100 text-rose-700"
                      : "bg-emerald-100 text-emerald-700"
                  }`}>
                    {detectorResult.is_toxic || detectorResult.is_bully ? (
                      <><AlertTriangle className="w-3 h-3" /> Berbahaya</>
                    ) : (
                      <><Check className="w-3 h-3" /> Aman</>
                    )}
                  </span>
                  <h3 className="text-sm font-bold leading-tight">
                    {detectorResult.is_toxic || detectorResult.is_bully ? 'Terdeteksi Risiko Toksisitas' : 'Teks Aman'}
                  </h3>
                  <p className="text-xxs opacity-75 mt-1 font-medium flex items-center gap-1.5 flex-wrap">
                    <span>Source: {detectorResult.decision_source}</span>
                    {detectorResult.execution_time !== undefined && (
                      <>
                        <span className="opacity-50">•</span>
                        <span>⏱️ {detectorResult.execution_time}ms</span>
                      </>
                    )}
                  </p>
                  {detectorResult && (
                    ((detectorResult.execution_time !== undefined && detectorResult.execution_time <= 3.0) || 
                     /cache|database|semantic/i.test(detectorResult.decision_source || ''))
                  ) && (
                    <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-gradient-to-r from-blue-500/15 to-indigo-500/15 text-blue-600 dark:text-indigo-400 border border-blue-200/30 dark:border-indigo-500/30 shadow-[0_0_12px_rgba(99,102,241,0.25)] animate-pulse">
                      🚀 Semantic Cache Bypass (Resource Saved)
                    </div>
                  )}
                </div>
                
                {/* Circle score */}
                <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center font-bold text-sm border shadow-sm text-gray-900">
                  {Math.round(Math.max(detectorResult.probability_toxic, detectorResult.probability_bully) * 100)}%
                </div>
              </div>

              <div className="p-5 flex flex-col gap-5">
                {/* Visualisasi XAI */}
                <div className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm flex flex-col gap-2">
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Hasil Sorotan Kata Pemicu (Explainable AI)</span>
                  <div className="text-sm font-medium text-gray-800 leading-relaxed">
                    <XAIHighlightText text={detectorResult.text} wordImportances={detectorResult.word_importances} />
                  </div>
                  {detectorResult.word_importances && detectorResult.word_importances.length > 0 && (
                    <button
                      onClick={() => setIsDrawerOpen(true)}
                      className="mt-2 text-[10px] font-bold text-blue-600 hover:text-blue-700 dark:text-indigo-400 hover:underline flex items-center gap-1 cursor-pointer bg-transparent border-none p-0 align-left self-start"
                    >
                      Lihat Analisis Detail XAI &rarr;
                    </button>
                  )}
                </div>

                {/* Category Label */}
                <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 flex justify-between items-center">
                  <span className="text-xs font-semibold text-gray-500">Klasifikasi Kategori:</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                    detectorResult.is_toxic || detectorResult.is_bully
                      ? "bg-rose-100 text-rose-700"
                      : "bg-emerald-100 text-emerald-700"
                  }`}>
                    {detectorResult.category}
                  </span>
                </div>

                {/* Meters */}
                <div className="flex flex-col gap-3">
                  <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Probabilitas Penilaian</h4>
                  
                  <div>
                    <div className="flex justify-between text-xs text-gray-600 mb-1 font-medium">
                      <span>Toxicity (Toksisitas)</span>
                      <span className="font-bold">{Math.round(detectorResult.probability_toxic * 100)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-1000 ${detectorResult.is_toxic ? "bg-rose-500" : "bg-emerald-500"}`}
                        style={{ width: `${detectorResult.probability_toxic * 100}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs text-gray-600 mb-1 font-medium">
                      <span>Bullying (Intimidasi/Ejekan)</span>
                      <span className="font-bold">{Math.round(detectorResult.probability_bully * 100)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-1000 ${detectorResult.is_bully ? "bg-rose-400" : "bg-emerald-400"}`}
                        style={{ width: `${detectorResult.probability_bully * 100}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Explanation */}
                <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 text-xs leading-relaxed">
                  <h4 className="font-bold text-gray-700 mb-1 flex items-center gap-1"><HelpCircle className="w-3.5 h-3.5 text-blue-500" /> Hasil Penjelasan</h4>
                  <p className="text-gray-600 font-medium">{detectorResult.reason}</p>
                </div>

                {/* Expandable Process */}
                {detectorResult.normalization_steps && (
                  <details className="group border border-gray-100 rounded-lg overflow-hidden bg-white">
                    <summary className="flex justify-between items-center text-xs font-semibold cursor-pointer list-none p-3 bg-gray-50/50 hover:bg-gray-50 transition-colors text-gray-700">
                      <span>Alur Normalisasi Teks</span>
                      <span className="transition group-open:rotate-180 text-gray-400">▼</span>
                    </summary>
                    <div className="p-4 border-t border-gray-100 bg-gray-50/20 text-xxs font-mono flex flex-col gap-3">
                      {detectorResult.normalization_steps.map((step, idx) => (
                        <div key={idx} className="flex flex-col gap-0.5 border-l-2 border-blue-200 pl-2">
                          <span className="font-bold text-gray-800">{step.name}</span>
                          <span className="text-gray-500 break-all">{step.value}</span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            </motion.div>
          ) : null}
        </div>
      </div>

      {/* XAI Side Drawer Panel */}
      <AnimatePresence>
        {isDrawerOpen && detectorResult && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsDrawerOpen(false)}
              className="fixed inset-0 bg-black z-50 cursor-pointer"
            />
            {/* Drawer */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 26, stiffness: 220 }}
              className="fixed top-0 right-0 h-full w-full sm:w-[480px] bg-white dark:bg-slate-900 border-l border-gray-200 dark:border-gray-800 shadow-2xl z-50 p-6 overflow-y-auto flex flex-col gap-6"
            >
              {/* Header */}
              <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-800 pb-4">
                <div>
                  <h2 className="text-lg font-black text-gray-900 dark:text-gray-100">Detail Analisis XAI</h2>
                  <p className="text-xxs text-gray-400">Kontribusi bobot penting tiap kata dalam kalimat.</p>
                </div>
                <button 
                  onClick={() => setIsDrawerOpen(false)}
                  className="p-1.5 rounded-lg bg-gray-50 dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 text-gray-400 dark:text-gray-300 transition-colors border-none cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Analyzed Text */}
              <div className="bg-gray-50/50 dark:bg-slate-950/20 border border-gray-150 p-4 rounded-xl flex flex-col gap-2">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Teks Analisis</span>
                <div className="text-sm font-medium text-gray-850 dark:text-gray-200 leading-relaxed">
                  <XAIHighlightText text={detectorResult.text} wordImportances={detectorResult.word_importances} />
                </div>
              </div>

              {/* Horizontal Bar Chart SVG */}
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Grafik Kontribusi Kata (SHAP Weights)</span>
                  <div className="flex gap-3 text-[9px] font-bold">
                    <span className="text-rose-500">■ Toxic</span>
                    <span className="text-purple-500">■ Bullying</span>
                  </div>
                </div>
                
                {/* SVG Horizontal Bar Chart */}
                {(() => {
                  const importances = (detectorResult.word_importances || []).filter(item => item.word.trim().length > 0);
                  if (importances.length === 0) {
                    return (
                      <div className="text-center py-8 text-xs text-gray-400 font-semibold italic">
                        Tidak ada bobot penting kata yang terdeteksi.
                      </div>
                    );
                  }

                  const barHeight = 8;
                  const rowSpacing = 36;
                  const textColWidth = 100;
                  const chartAreaWidth = 320;
                  const svgWidth = textColWidth + chartAreaWidth;
                  const svgHeight = importances.length * rowSpacing + 10;

                  // Find maximum weight to scale the bars
                  const maxWeight = Math.max(
                    0.01,
                    ...importances.map(w => Math.max(Math.abs(w.weight_toxic), Math.abs(w.weight_bully)))
                  );

                  return (
                    <div className="w-full overflow-hidden bg-gray-50/20 dark:bg-slate-950/10 border border-gray-100 dark:border-gray-800/40 rounded-xl p-3">
                      <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto overflow-visible select-none">
                        {importances.map((item, idx) => {
                          const y = idx * rowSpacing + 5;
                          const toxicWidth = (Math.abs(item.weight_toxic) / maxWeight) * (chartAreaWidth - 50);
                          const bullyWidth = (Math.abs(item.weight_bully) / maxWeight) * (chartAreaWidth - 50);

                          return (
                            <g key={idx}>
                              {/* Word Label */}
                              <text
                                x={textColWidth - 8}
                                y={y + 15}
                                textAnchor="end"
                                className="text-[11px] font-bold fill-gray-800 dark:fill-gray-200"
                              >
                                {item.word}
                              </text>

                              {/* Toxicity Bar Track */}
                              <rect
                                x={textColWidth}
                                y={y + 2}
                                width={chartAreaWidth}
                                height={barHeight}
                                rx="2"
                                fill="currentColor"
                                className="text-gray-100/50 dark:text-slate-800/30"
                              />
                              {/* Toxicity Active Bar */}
                              <rect
                                x={textColWidth}
                                y={y + 2}
                                width={toxicWidth}
                                height={barHeight}
                                rx="2"
                                fill="#f43f5e"
                                className="transition-all duration-500"
                              >
                                <title>{`Toxicity Weight: ${item.weight_toxic.toFixed(4)}`}</title>
                              </rect>
                              {/* Toxicity Value Text */}
                              {item.weight_toxic > 0 && (
                                <text
                                  x={textColWidth + toxicWidth + 5}
                                  y={y + 9}
                                  className="text-[8px] font-bold font-mono fill-rose-650 dark:fill-rose-450"
                                >
                                  +{item.weight_toxic.toFixed(4)}
                                </text>
                              )}

                              {/* Bullying Bar Track */}
                              <rect
                                x={textColWidth}
                                y={y + 14}
                                width={chartAreaWidth}
                                height={barHeight}
                                rx="2"
                                fill="currentColor"
                                className="text-gray-100/50 dark:text-slate-800/30"
                              />
                              {/* Bullying Active Bar */}
                              <rect
                                x={textColWidth}
                                y={y + 14}
                                width={bullyWidth}
                                height={barHeight}
                                rx="2"
                                fill="#a855f7"
                                className="transition-all duration-500"
                              >
                                <title>{`Bullying Weight: ${item.weight_bully.toFixed(4)}`}</title>
                              </rect>
                              {/* Bullying Value Text */}
                              {item.weight_bully > 0 && (
                                <text
                                  x={textColWidth + bullyWidth + 5}
                                  y={y + 21}
                                  className="text-[8px] font-bold font-mono fill-purple-650 dark:fill-purple-450"
                                >
                                  +{item.weight_bully.toFixed(4)}
                                </text>
                              )}

                              {/* Row Divider */}
                              {idx < importances.length - 1 && (
                                <line
                                  x1="0"
                                  y1={y + rowSpacing}
                                  x2={svgWidth}
                                  y2={y + rowSpacing}
                                  stroke="currentColor"
                                  strokeWidth="0.5"
                                  className="text-gray-100 dark:text-slate-800/40"
                                  strokeDasharray="2 2"
                                />
                              )}
                            </g>
                          );
                        })}
                      </svg>
                    </div>
                  );
                })()}
              </div>

              {/* Info Footnote */}
              <div className="bg-blue-50/30 dark:bg-slate-950/20 border border-blue-100/40 p-3 rounded-lg flex items-start gap-2.5 mt-auto">
                <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                <p className="text-[10px] text-gray-500 dark:text-gray-400 leading-normal">
                  Bobot kontribusi penting tiap token menunjukkan seberapa kuat kata tersebut memicu model untuk menentukan klasifikasi bahaya (Toxic / Bullying). Nilai dihitung menggunakan pendekatan model interpretasi lokal.
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
