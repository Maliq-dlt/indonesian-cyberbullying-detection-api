import React, { useEffect, useRef, useState } from 'react';
import { TrendingUp, Terminal as TermIcon, RefreshCw } from 'lucide-react';

interface RetrainTerminalProps {
  onStartTraining: (modelType: string) => void;
  isTraining: boolean;
  trainingLogs: string[];
  onClearLogs: () => void;
}

export default function RetrainTerminal({
  onStartTraining,
  isTraining,
  trainingLogs,
  onClearLogs
}: RetrainTerminalProps) {
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const [modelType, setModelType] = useState<string>('both');

  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [trainingLogs]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-4 items-start">
      
      {/* Retrain triggering card */}
      <div className="lg:col-span-4 flex flex-col gap-4">
        <div className="premium-card p-6 flex flex-col gap-4">
          <h3 className="text-sm font-bold text-gray-900 flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-blue-500" /> Siklus Latih Ulang Model
          </h3>
          <p className="text-xs text-gray-500 leading-relaxed">
            Setelah Anda memindahkan dan menyeimbangkan label di kuadran, klik tombol di bawah untuk memicu pelatihan ulang di server backend. Perubahan bobot akan segera diterapkan.
          </p>
          
          <div className="flex flex-col gap-1.5 mt-1">
            <label className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Tipe Pelatihan Model</label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              disabled={isTraining}
              className="w-full bg-white border border-gray-200 text-gray-700 px-3 py-2.5 rounded-xl text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500 transition cursor-pointer"
            >
              <option value="both">Latih Keduanya (ML & Transformer)</option>
              <option value="ml">Machine Learning (Logistic Regression) Saja</option>
              <option value="transformer">Transformer (XLM-RoBERTa ONNX) Saja</option>
            </select>
          </div>

          <button
            onClick={() => onStartTraining(modelType)}
            disabled={isTraining}
            className="w-full bg-blue-600 text-white py-3 rounded-xl text-sm font-bold hover:bg-blue-700 disabled:bg-gray-100 disabled:text-gray-400 transition-all cursor-pointer border-none flex items-center justify-center gap-2 mt-2"
          >
            {isTraining ? (
              <><RefreshCw className="w-4 h-4 animate-spin" /> Sedang Melatih...</>
            ) : (
              <>Jalankan Pelatihan Ulang</>
            )}
          </button>
        </div>
      </div>

      {/* Console log output Terminal */}
      <div className="lg:col-span-8 flex flex-col gap-3">
        <div className="flex justify-between items-center">
          <span className="text-xs font-bold text-gray-800 flex items-center gap-1">
            <TermIcon className="w-4 h-4 text-gray-500" /> Log Pelatihan Server (Terminal)
          </span>
          <div className="flex gap-2">
            {isTraining && (
              <span className="text-xxs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-bold animate-pulse">Running</span>
            )}
            <button
              onClick={onClearLogs}
              className="bg-white border border-gray-200 text-gray-500 text-xs px-2.5 py-1 rounded hover:bg-gray-50 cursor-pointer"
            >
              Clear Logs
            </button>
          </div>
        </div>

        <div className="premium-card bg-gray-950 text-emerald-400 p-4 font-mono text-xxs h-64 overflow-y-auto custom-scrollbar flex flex-col gap-1 border-none shadow-lg">
          {trainingLogs.length === 0 ? (
            <p className="text-gray-600 italic">Terminal siap. Mulai pelatihan ulang untuk mendengarkan log stream...</p>
          ) : (
            trainingLogs.map((log, idx) => (
              <div key={idx} className="break-all whitespace-pre-wrap leading-relaxed">
                <span className="text-gray-600 mr-2">&gt;</span>{log}
              </div>
            ))
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>

    </div>
  );
}
