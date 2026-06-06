import React, { useState, useEffect } from 'react';
import { m } from 'framer-motion';
import { Activity, ShieldCheck, Bell, Link2, TrendingUp, Clock, Save, RefreshCw, Workflow } from 'lucide-react';
import { toast } from 'sonner';

interface SettingsProps {
  apiUrl: string;
  setApiUrl: (url: string) => void;
  apiKey: string;
  setApiKey: (key: string) => void;
  checkConnection: (silent: boolean) => Promise<boolean>;
  modelStatus: any;
}

interface TrainingHistoryItem {
  id: number;
  timestamp: string;
  f1_toxic: number;
  f1_bully: number;
  threshold_toxic: number;
  threshold_bully: number;
  active_version: string;
}

const mockHistory: TrainingHistoryItem[] = [
  { id: 1, timestamp: '2026-06-01', f1_toxic: 0.81, f1_bully: 0.78, threshold_toxic: 0.5, threshold_bully: 0.5, active_version: 'v1.0.0-mock' },
  { id: 2, timestamp: '2026-06-02', f1_toxic: 0.83, f1_bully: 0.81, threshold_toxic: 0.5, threshold_bully: 0.5, active_version: 'v1.0.1-mock' },
  { id: 3, timestamp: '2026-06-03', f1_toxic: 0.85, f1_bully: 0.83, threshold_toxic: 0.5, threshold_bully: 0.5, active_version: 'v1.1.0-mock' },
  { id: 4, timestamp: '2026-06-04', f1_toxic: 0.88, f1_bully: 0.86, threshold_toxic: 0.5, threshold_bully: 0.5, active_version: 'v1.2.0-mock' },
  { id: 5, timestamp: '2026-06-05', f1_toxic: 0.91, f1_bully: 0.89, threshold_toxic: 0.5, threshold_bully: 0.5, active_version: 'v2.0.0-mock' },
];

export default function Settings({ 
  apiUrl, setApiUrl, apiKey, setApiKey, checkConnection, modelStatus 
}: SettingsProps) {
  
  const [cookiePlatform, setCookiePlatform] = useState<'tiktok' | 'x'>('tiktok');
  const [cookieJson, setCookieJson] = useState('');
  const [cookieLoading, setCookieLoading] = useState(false);

  // Webhook states
  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookEnabled, setWebhookEnabled] = useState(false);
  const [webhookLoading, setWebhookLoading] = useState(false);

  // Retraining history states
  const [historyData, setHistoryData] = useState<TrainingHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  // Ensemble Weights states
  const [ensembleWeights, setEnsembleWeights] = useState<{
    ml_toxic: number;
    tr_toxic: number;
    ml_bully: number;
    tr_bully: number;
  }>({
    ml_toxic: 0.5,
    tr_toxic: 0.5,
    ml_bully: 0.65,
    tr_bully: 0.35
  });
  const [calibrationLoading, setCalibrationLoading] = useState(false);

  // Load webhook configurations, ensemble weights & training history from backend
  useEffect(() => {
    const fetchConfig = async () => {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (apiKey) headers['x-api-key'] = apiKey;

      // Fetch settings
      try {
        const response = await fetch(`${apiUrl}/api/settings`, { headers });
        if (response.ok) {
          const settings = await response.json();
          setWebhookUrl(settings.webhook_url || '');
          setWebhookEnabled(!!settings.webhook_enabled);
          if (settings.ensemble_weights) {
            setEnsembleWeights(settings.ensemble_weights);
          }
        }
      } catch (err) {
        console.error('Gagal mengambil pengaturan webhook:', err);
      }

      // Fetch training history
      try {
        setHistoryLoading(true);
        const response = await fetch(`${apiUrl}/api/train/history`, { headers });
        if (response.ok) {
          const history = await response.json();
          setHistoryData(history || []);
        }
      } catch (err) {
        console.error('Gagal mengambil riwayat retraining:', err);
      } finally {
        setHistoryLoading(false);
      }
    };

    fetchConfig();
  }, [apiUrl, apiKey]);

  const handleRecalibrate = async () => {
    setCalibrationLoading(true);
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    try {
      const response = await fetch(`${apiUrl}/api/settings/recalibrate`, {
        method: 'POST',
        headers
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Gagal melakukan kalibrasi bobot.');
      }

      if (data.weights) {
        setEnsembleWeights(data.weights);
      }

      if (data.calibrated) {
        toast.success(data.message || 'Kalibrasi bobot ensemble berhasil dilakukan!');
      } else {
        toast.warning(data.message || 'Data tervalidasi kurang dari 5, bobot disetel ke default.');
      }
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || 'Terjadi kesalahan saat menghubungi API Kalibrasi.');
    } finally {
      setCalibrationLoading(false);
    }
  };

  const handleSaveWebhook = async () => {
    setWebhookLoading(true);
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    try {
      const response = await fetch(`${apiUrl}/api/settings`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          webhook_url: webhookUrl,
          webhook_enabled: webhookEnabled
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Gagal menyimpan pengaturan webhook.');
      }
      
      toast.success('Pengaturan webhook berhasil disimpan!');
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || 'Gagal menyimpan pengaturan.');
    } finally {
      setWebhookLoading(false);
    }
  };

  const handleTestWebhook = async () => {
    if (!webhookUrl) return;
    setWebhookLoading(true);
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    try {
      const response = await fetch(`${apiUrl}/api/settings/test-webhook`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ webhook_url: webhookUrl })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Gagal terhubung dengan server webhook tujuan.');
      }
      
      toast.success(`Tes Webhook berhasil! Server tujuan merespon dengan HTTP ${data.status_code}.`);
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || 'Koneksi ke Webhook URL gagal.');
    } finally {
      setWebhookLoading(false);
    }
  };

  const handleUploadCookies = async () => {
    if (!cookieJson.trim()) {
      toast.warning('Silakan masukkan JSON cookies!');
      return;
    }
    
    let parsedCookies;
    try {
      parsedCookies = JSON.parse(cookieJson);
      if (!Array.isArray(parsedCookies)) {
        throw new Error('Cookies harus berupa array JSON');
      }
    } catch (err: any) {
      toast.error('Format JSON tidak valid! Pastikan format berupa array JSON yang valid.');
      return;
    }

    setCookieLoading(true);
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (apiKey) headers['x-api-key'] = apiKey;

    try {
      const response = await fetch(`${apiUrl}/api/settings/cookies`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          platform: cookiePlatform,
          cookies: parsedCookies
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Gagal unggah cookies.');
      }
      
      toast.success(`Cookie sesi ${cookiePlatform.toUpperCase()} berhasil diperbarui!`);
      setCookieJson('');
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || 'Gagal memperbarui cookie.');
    } finally {
      setCookieLoading(false);
    }
  };

  // Helper to render training history SVG line chart
  const renderHistoryChart = () => {
    const isMock = historyData.length === 0;
    const chartData = isMock ? mockHistory : historyData;

    const width = 500;
    const height = 220;
    const padLeft = 45;
    const padRight = 20;
    const padTop = 30;
    const padBottom = 35;

    const chartWidth = width - padLeft - padRight;
    const chartHeight = height - padTop - padBottom;

    // Find min and max F1
    const f1s = chartData.flatMap(d => [d.f1_toxic, d.f1_bully]);
    const minF1 = Math.max(0.0, Math.min(0.6, ...f1s) - 0.05);
    const maxF1 = 1.0;
    const f1Range = maxF1 - minF1;

    const getX = (idx: number) => {
      if (chartData.length <= 1) return padLeft + chartWidth / 2;
      return padLeft + (idx / (chartData.length - 1)) * chartWidth;
    };

    const getY = (val: number) => {
      const ratio = (val - minF1) / f1Range;
      return padTop + chartHeight - ratio * chartHeight;
    };

    // Construct SVG path lines
    let toxicPath = '';
    let bullyPath = '';

    chartData.forEach((d, idx) => {
      const x = getX(idx);
      const yToxic = getY(d.f1_toxic);
      const yBully = getY(d.f1_bully);

      if (idx === 0) {
        toxicPath = `M ${x} ${yToxic}`;
        bullyPath = `M ${x} ${yBully}`;
      } else {
        toxicPath += ` L ${x} ${yToxic}`;
        bullyPath += ` L ${x} ${yBully}`;
      }
    });

    // Helper for Y ticks
    const yTicks = [0.6, 0.7, 0.8, 0.9, 1.0].filter(t => t >= minF1);

    return (
      <div className="flex flex-col gap-3">
        <div className="flex justify-between items-center">
          <div className="flex gap-4 text-xxs font-bold">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-rose-500 rounded-full inline-block"></span>
              <span className="text-gray-600 dark:text-gray-300">F1 Toxicity</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-indigo-500 rounded-full inline-block"></span>
              <span className="text-gray-600 dark:text-gray-300">F1 Bullying</span>
            </div>
          </div>
          {isMock && (
            <span className="text-[9px] font-black uppercase tracking-wider text-amber-600 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded-full border border-amber-200/50">
              Visualisasi Simulasi
            </span>
          )}
        </div>

        <div className="w-full overflow-hidden bg-gray-50/40 dark:bg-slate-950/20 border border-gray-100 dark:border-gray-800/40 rounded-xl p-2.5">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible select-none">
            {/* Grid Lines */}
            {yTicks.map(tick => {
              const y = getY(tick);
              return (
                <g key={tick} className="opacity-40 dark:opacity-20">
                  <line 
                    x1={padLeft} 
                    y1={y} 
                    x2={width - padRight} 
                    y2={y} 
                    stroke="var(--text-muted)" 
                    strokeDasharray="4 4" 
                    strokeWidth="1" 
                  />
                  <text 
                    x={padLeft - 8} 
                    y={y + 3.5} 
                    textAnchor="end" 
                    className="text-[9px] font-mono font-bold" 
                    fill="var(--text-muted)"
                  >
                    {tick.toFixed(1)}
                  </text>
                </g>
              );
            })}

            {/* Toxic Line Path */}
            <path 
              d={toxicPath} 
              fill="none" 
              stroke="#f43f5e" 
              strokeWidth="2.5" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="drop-shadow-[0_2px_4px_rgba(244,63,94,0.15)]"
            />

            {/* Bully Line Path */}
            <path 
              d={bullyPath} 
              fill="none" 
              stroke="#6366f1" 
              strokeWidth="2.5" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="drop-shadow-[0_2px_4px_rgba(99,102,241,0.15)]"
            />

            {/* Toxic Points */}
            {chartData.map((d, idx) => {
              const x = getX(idx);
              const y = getY(d.f1_toxic);
              return (
                <circle 
                  key={`toxic-pt-${idx}`} 
                  cx={x} 
                  cy={y} 
                  r="4" 
                  fill="#ffffff" 
                  stroke="#f43f5e" 
                  strokeWidth="2" 
                  className="cursor-pointer hover:r-5 transition-all"
                >
                  <title>{`Versi: ${d.active_version}\nF1 Toxic: ${d.f1_toxic.toFixed(4)}\nTanggal: ${d.timestamp}`}</title>
                </circle>
              );
            })}

            {/* Bully Points */}
            {chartData.map((d, idx) => {
              const x = getX(idx);
              const y = getY(d.f1_bully);
              return (
                <circle 
                  key={`bully-pt-${idx}`} 
                  cx={x} 
                  cy={y} 
                  r="4" 
                  fill="#ffffff" 
                  stroke="#6366f1" 
                  strokeWidth="2" 
                  className="cursor-pointer hover:r-5 transition-all"
                >
                  <title>{`Versi: ${d.active_version}\nF1 Bullying: ${d.f1_bully.toFixed(4)}\nTanggal: ${d.timestamp}`}</title>
                </circle>
              );
            })}

            {/* X-axis Version Labels */}
            {chartData.map((d, idx) => {
              const x = getX(idx);
              return (
                <text 
                  key={`lbl-${idx}`} 
                  x={x} 
                  y={height - padBottom + 16} 
                  textAnchor="middle" 
                  className="text-[8px] font-bold font-mono tracking-tighter" 
                  fill="var(--text-muted)"
                >
                  {d.active_version.split('-')[0]}
                </text>
              );
            })}

            {/* X-axis line */}
            <line 
              x1={padLeft} 
              y1={height - padBottom} 
              x2={width - padRight} 
              y2={height - padBottom} 
              stroke="var(--card-border)" 
              strokeWidth="1.5" 
            />
          </svg>
        </div>
        <p className="text-[10px] text-gray-400 font-medium leading-normal italic">
          * Arahkan kursor ke titik grafik untuk melihat rincian presisi desimal dan timestamp pelatihan.
        </p>
      </div>
    );
  };

  const cn = (...classes: any[]) => classes.filter(Boolean).join(' ');

  return (
    <m.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.3 }}
      className="py-6 flex flex-col gap-6 max-w-2xl mx-auto"
    >
      <header className="mb-2">
        <h1 className="text-3xl font-black text-gray-900 mb-1">Pengaturan Konfigurasi</h1>
        <p className="text-gray-500 text-sm">Sesuaikan endpoint URL FastAPI backend, webhook notifikasi, dan monitor performa model.</p>
      </header>

      {/* Main Base Config */}
      <div className="premium-card p-6 flex flex-col gap-6">
        
        {/* API URL input */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold text-gray-800 uppercase tracking-wider">FastAPI Base URL</label>
          <input
            type="text"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            placeholder="Contoh: http://localhost:8000"
            className="w-full px-4 py-2.5 rounded-xl border border-gray-200 outline-none text-sm font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all text-gray-700"
          />
        </div>

        {/* API Key input */}
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <label className="text-xs font-bold text-gray-800 uppercase tracking-wider">API Authentication Key</label>
            <span className="text-[10px] text-gray-400 italic">Kosongkan jika backend berjalan di ENV=development</span>
          </div>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Kunci API Key rahasia Anda"
            className="w-full px-4 py-2.5 rounded-xl border border-gray-200 outline-none text-sm font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all text-gray-700"
          />
        </div>

        {/* Test Button */}
        <button
          onClick={() => checkConnection(false)}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl text-sm transition-all cursor-pointer border-none flex items-center justify-center gap-1.5 shadow-sm shadow-blue-500/10"
        >
          <Activity className="w-4.5 h-4.5" /> Uji &amp; Hubungkan Koneksi
        </button>
      </div>

      {/* Webhook System Configuration */}
      <div className="premium-card p-6 flex flex-col gap-5">
        <div className="flex items-center gap-2.5 border-b border-gray-100 dark:border-gray-800/60 pb-3">
          <Bell className="w-5 h-5 text-rose-500 animate-pulse" />
          <div>
            <h3 className="text-sm font-bold text-gray-900 dark:text-gray-200">Webhook Notifikasi Real-time</h3>
            <p className="text-xxs text-gray-400">Kirim event cyberbullying yang terdeteksi otomatis ke endpoint server eksternal.</p>
          </div>
        </div>

        <div className="bg-gray-50/50 dark:bg-slate-950/20 border border-gray-150 p-3.5 rounded-xl flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-bold text-gray-800 dark:text-gray-200">Aktifkan Pengiriman Webhook</span>
            <span className="text-[10px] text-gray-400">Kirim event deteksi positif (toxic/bullying) ke server tujuan.</span>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              checked={webhookEnabled}
              onChange={(e) => setWebhookEnabled(e.target.checked)}
              className="sr-only peer" 
            />
            <div className="w-9 h-5 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-rose-500" />
          </label>
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-1">
            <Link2 className="w-3.5 h-3.5 text-gray-400" />
            <label className="text-xs font-bold text-gray-800 dark:text-gray-300 uppercase tracking-wider">Webhook Endpoint URL</label>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              disabled={!webhookEnabled}
              placeholder="https://example.com/api/cyberbullying-alert"
              className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-850 dark:bg-slate-950/20 outline-none text-sm font-medium focus:border-rose-500 focus:ring-2 focus:ring-rose-100 transition-all text-gray-700 disabled:opacity-50 disabled:bg-gray-50"
            />
            <button
              onClick={handleTestWebhook}
              disabled={webhookLoading || !webhookEnabled || !webhookUrl}
              className="bg-gray-150 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-gray-200 text-xs font-bold px-4 rounded-xl transition cursor-pointer border-none flex items-center gap-1 disabled:opacity-50"
            >
              Uji Webhook
            </button>
          </div>
        </div>

        <button
          onClick={handleSaveWebhook}
          disabled={webhookLoading}
          className="w-full bg-gradient-to-r from-rose-500 to-red-500 hover:from-rose-600 hover:to-red-600 text-white font-bold py-3 rounded-xl text-sm transition-all cursor-pointer border-none flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-50"
        >
          {webhookLoading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Simpan Konfigurasi Webhook
        </button>
      </div>

      {/* Model Retraining History Performance Monitor */}
      <div className="premium-card p-6 flex flex-col gap-5">
        <div className="flex items-center gap-2.5 border-b border-gray-100 dark:border-gray-800/60 pb-3">
          <TrendingUp className="w-5 h-5 text-indigo-500" />
          <div>
            <h3 className="text-sm font-bold text-gray-900 dark:text-gray-200">Tracker Retraining &amp; Drift Model</h3>
            <p className="text-xxs text-gray-400">Pantau pergerakan kualitas F1-score model untuk melacak adanya model drift secara historis.</p>
          </div>
        </div>

        {historyLoading ? (
          <div className="flex flex-col items-center justify-center py-10 gap-2">
            <RefreshCw className="w-6 h-6 animate-spin text-indigo-500" />
            <span className="text-xxs text-gray-400 font-semibold">Mengambil data metrik training...</span>
          </div>
        ) : (
          renderHistoryChart()
        )}
      </div>

      {/* Ensemble Calibration Card */}
      <div className="premium-card p-6 flex flex-col gap-5">
        <div className="flex items-center gap-2.5 border-b border-gray-100 dark:border-gray-800/60 pb-3">
          <Workflow className="w-5 h-5 text-blue-500 animate-pulse" />
          <div>
            <h3 className="text-sm font-bold text-gray-900 dark:text-gray-200">Kalibrasi Bobot Ensemble AI</h3>
            <p className="text-xxs text-gray-400">Atur &amp; kalibrasikan kontribusi prediksi antara model Classical ML dan Transformer DL secara dinamis.</p>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          {/* Toxic Classifier Weights */}
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-gray-700 dark:text-gray-300">Klasifikasi Toksisitas (Toxic)</span>
              <span className="text-[10px] font-mono text-gray-400">ML: {Math.round(ensembleWeights.ml_toxic * 100)}% | Transformer: {Math.round(ensembleWeights.tr_toxic * 100)}%</span>
            </div>
            
            <div className="w-full h-3 bg-gray-100 dark:bg-slate-900 rounded-full overflow-hidden flex">
              <div 
                style={{ width: `${ensembleWeights.ml_toxic * 100}%` }} 
                className="bg-blue-500 h-full transition-all duration-500 relative group"
                title={`Classical ML: ${Math.round(ensembleWeights.ml_toxic * 100)}%`}
              />
              <div 
                style={{ width: `${ensembleWeights.tr_toxic * 100}%` }} 
                className="bg-indigo-500 h-full transition-all duration-500 relative group"
                title={`Transformer: ${Math.round(ensembleWeights.tr_toxic * 100)}%`}
              />
            </div>
            <div className="flex justify-between text-[10px] font-semibold text-gray-450">
              <span>Classical ML ({Math.round(ensembleWeights.ml_toxic * 100)}%)</span>
              <span>Transformer ({Math.round(ensembleWeights.tr_toxic * 100)}%)</span>
            </div>
          </div>

          {/* Bullying Classifier Weights */}
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-gray-700 dark:text-gray-300">Klasifikasi Perundungan (Bullying)</span>
              <span className="text-[10px] font-mono text-gray-400">ML: {Math.round(ensembleWeights.ml_bully * 100)}% | Transformer: {Math.round(ensembleWeights.tr_bully * 100)}%</span>
            </div>
            
            <div className="w-full h-3 bg-gray-100 dark:bg-slate-900 rounded-full overflow-hidden flex">
              <div 
                style={{ width: `${ensembleWeights.ml_bully * 100}%` }} 
                className="bg-blue-500 h-full transition-all duration-500 relative group"
                title={`Classical ML: ${Math.round(ensembleWeights.ml_bully * 100)}%`}
              />
              <div 
                style={{ width: `${ensembleWeights.tr_bully * 100}%` }} 
                className="bg-indigo-500 h-full transition-all duration-500 relative group"
                title={`Transformer: ${Math.round(ensembleWeights.tr_bully * 100)}%`}
              />
            </div>
            <div className="flex justify-between text-[10px] font-semibold text-gray-450">
              <span>Classical ML ({Math.round(ensembleWeights.ml_bully * 100)}%)</span>
              <span>Transformer ({Math.round(ensembleWeights.tr_bully * 100)}%)</span>
            </div>
          </div>
        </div>

        <div className="bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/30 p-3 rounded-xl text-xxs leading-normal text-blue-600 dark:text-blue-400">
          <strong>Bagaimana ini bekerja?</strong> Tombol di bawah akan mengeksekusi algoritma kalibrasi MSE (Mean Squared Error) optimasi grid search berbasis data memori tervalidasi (is_validated = 1). Memerlukan minimal 5 data tervalidasi agar bobot terkalibrasi secara optimal.
        </div>

        <button
          onClick={handleRecalibrate}
          disabled={calibrationLoading}
          className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-3 rounded-xl text-sm transition-all cursor-pointer border-none flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-50"
        >
          {calibrationLoading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          Kalibrasi Ulang Kontribusi Model Ensemble
        </button>
      </div>

      {/* Cookie Session Uploader Card */}
      <div className="premium-card p-6 flex flex-col gap-5">
        <div className="flex items-center gap-2.5 border-b border-gray-100 dark:border-gray-800/60 pb-3">
          <ShieldCheck className="w-5 h-5 text-indigo-500" />
          <div>
            <h3 className="text-sm font-bold text-gray-900 dark:text-gray-200">Manajemen Cookie Sesi Scraper</h3>
            <p className="text-xxs text-gray-400">Unggah cookie autentikasi untuk scraping komentar asli dari TikTok atau Twitter/X.</p>
          </div>
        </div>

        <div className="flex gap-4">
          <button
            onClick={() => setCookiePlatform('tiktok')}
            className={cn(
              "flex-1 py-2 rounded-xl text-xs font-bold transition-all border cursor-pointer",
              cookiePlatform === 'tiktok'
                ? "bg-rose-50 text-rose-700 border-rose-200"
                : "bg-white text-gray-500 border-gray-200 hover:bg-gray-50"
            )}
          >
            TikTok Cookie
          </button>
          <button
            onClick={() => setCookiePlatform('x')}
            className={cn(
              "flex-1 py-2 rounded-xl text-xs font-bold transition-all border cursor-pointer",
              cookiePlatform === 'x'
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-gray-500 border-gray-200 hover:bg-gray-50"
            )}
          >
            Twitter / X Cookie
          </button>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold text-gray-800 uppercase tracking-wider">Paste JSON Cookie Array</label>
          <textarea
            value={cookieJson}
            onChange={(e) => setCookieJson(e.target.value)}
            placeholder='Contoh:&#10;[&#10;  { "name": "sessionid", "value": "xyz...", "domain": ".tiktok.com" }&#10;]'
            className="w-full h-32 p-3 bg-gray-50/50 border border-gray-200 rounded-xl outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all text-[11px] font-mono leading-relaxed resize-none"
          />
        </div>

        <button
          onClick={handleUploadCookies}
          disabled={cookieLoading}
          className="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white font-bold py-3 rounded-xl text-sm transition-all cursor-pointer border-none flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-50"
        >
          {cookieLoading ? 'Mengunggah...' : `Unggah Cookie ${cookiePlatform.toUpperCase()}`}
        </button>
      </div>

      {/* Model load status details */}
      {modelStatus && (
        <div className="premium-card p-6 flex flex-col gap-4 animate-fade-in">
          <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider">Status Modul ML/DL di Server</h3>
          
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-gray-50 rounded-lg flex justify-between items-center border border-gray-100">
              <span className="font-semibold text-gray-600">Lexicon Engine</span>
              <span className={cn("font-bold px-1.5 py-0.5 rounded text-[10px]", modelStatus.models_loaded.lexicon ? "bg-emerald-50 text-emerald-600" : "bg-gray-100 text-gray-400")}>
                {modelStatus.models_loaded.lexicon ? 'LOADED' : 'OFFLINE'}
              </span>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg flex justify-between items-center border border-gray-100">
              <span className="font-semibold text-gray-600">Machine Learning</span>
              <span className={cn("font-bold px-1.5 py-0.5 rounded text-[10px]", modelStatus.models_loaded.machine_learning ? "bg-emerald-50 text-emerald-600" : "bg-gray-100 text-gray-400")}>
                {modelStatus.models_loaded.machine_learning ? 'LOADED' : 'OFFLINE'}
              </span>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg flex justify-between items-center border border-gray-100">
              <span className="font-semibold text-gray-600">Transformer ONNX</span>
              <span className={cn("font-bold px-1.5 py-0.5 rounded text-[10px]", modelStatus.models_loaded.transformers_onnx ? "bg-emerald-50 text-emerald-600" : "bg-gray-100 text-gray-400")}>
                {modelStatus.models_loaded.transformers_onnx ? 'LOADED' : 'OFFLINE'}
              </span>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg flex justify-between items-center border border-gray-100">
              <span className="font-semibold text-gray-600">Transformer PyTorch</span>
              <span className={cn("font-bold px-1.5 py-0.5 rounded text-[10px]", modelStatus.models_loaded.transformers_pytorch ? "bg-emerald-50 text-emerald-600" : "bg-gray-100 text-gray-400")}>
                {modelStatus.models_loaded.transformers_pytorch ? 'LOADED' : 'OFFLINE'}
              </span>
            </div>
          </div>

          <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 text-xxs font-mono flex flex-col gap-1.5">
            <span className="font-bold text-gray-700">Threshold Terkalibrasi Aktif:</span>
            <div className="flex gap-4">
              <span>Toxic: <strong className="text-gray-900">{modelStatus.thresholds?.threshold_toxic ?? 0.5}</strong></span>
              <span>Bully: <strong className="text-gray-900">{modelStatus.thresholds?.threshold_bully ?? 0.5}</strong></span>
            </div>
          </div>
        </div>
      )}
    </m.div>
  );
}
