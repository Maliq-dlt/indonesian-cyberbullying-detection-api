import { motion } from 'framer-motion';
import { AlertTriangle, Check, HelpCircle } from 'lucide-react';
import { XAIHighlightText } from '../XAIHighlightText';
import { ProbabilityBar } from './ProbabilityBar';
import type { PredictionResult } from './types';
import { isCacheHit, isDangerous, percent } from './utils';

interface ResultCardProps {
  result: PredictionResult;
  onOpenXai: () => void;
}

export function ResultCard({ result, onOpenXai }: ResultCardProps) {
  const dangerous = isDangerous(result);
  const hasWordImportances = Boolean(result.word_importances?.length);

  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`premium-card overflow-hidden transition-all duration-300 border border-solid ${
        dangerous ? 'border-rose-100' : 'border-emerald-100'
      }`}
    >
      <div
        className={`p-5 border-b flex justify-between items-start ${
          dangerous 
            ? 'bg-rose-50/60 border-rose-100 text-rose-800 dark:bg-rose-900/30 dark:border-rose-800/50 dark:text-rose-200' 
            : 'bg-emerald-50/60 border-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:border-emerald-800/50 dark:text-emerald-200'
        }`}
      >
        <div>
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xxs font-bold uppercase tracking-wider mb-2 ${
              dangerous 
                ? 'bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-300' 
                : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300'
            }`}
          >
            {dangerous ? (
              <>
                <AlertTriangle className="w-3 h-3" /> Berbahaya
              </>
            ) : (
              <>
                <Check className="w-3 h-3" /> Aman
              </>
            )}
          </span>

          <h3 className="text-sm font-bold leading-tight">
            {dangerous ? 'Terdeteksi Risiko Toksisitas' : 'Teks Aman'}
          </h3>

          <p className="text-xxs opacity-75 mt-1 font-medium flex items-center gap-1.5 flex-wrap">
            <span>Source: {result.decision_source}</span>
            {result.execution_time !== undefined && (
              <>
                <span className="opacity-50">•</span>
                <span>⏱️ {result.execution_time}ms</span>
              </>
            )}
          </p>

          {isCacheHit(result) && (
            <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-gradient-to-r from-blue-500/15 to-indigo-500/15 text-blue-600 dark:text-indigo-400 border border-blue-200/30 dark:border-indigo-500/30 shadow-[0_0_12px_rgba(99,102,241,0.25)] animate-pulse">
              Semantic Cache Bypass (Resource Saved)
            </div>
          )}
        </div>

        <div className="w-12 h-12 rounded-full bg-white dark:bg-gray-800 flex items-center justify-center font-bold text-sm border dark:border-gray-700 shadow-sm text-gray-900 dark:text-white">
          {percent(Math.max(result.probability_toxic, result.probability_bully))}
        </div>
      </div>

      <div className="p-5 flex flex-col gap-5">
        <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl p-4 shadow-sm flex flex-col gap-2">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            Hasil Sorotan Kata Pemicu (Explainable AI)
          </span>
          <div className="text-sm font-medium text-gray-800 dark:text-gray-200 leading-relaxed">
            <XAIHighlightText text={result.text} wordImportances={result.word_importances} />
          </div>
          {hasWordImportances && (
            <button
              type="button"
              onClick={onOpenXai}
              className="mt-2 text-[10px] font-bold text-blue-600 hover:text-blue-700 dark:text-indigo-400 hover:underline flex items-center gap-1 cursor-pointer bg-transparent border-none p-0 align-left self-start"
            >
              Lihat Analisis Detail XAI →
            </button>
          )}
        </div>

        <div className="bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-800 rounded-lg p-3 flex justify-between items-center gap-3">
          <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">Klasifikasi Kategori:</span>
          <span
            className={`text-xs font-bold px-2 py-0.5 rounded text-right ${
              dangerous 
                ? 'bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-300' 
                : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300'
            }`}
          >
            {result.category}
          </span>
        </div>

        <div className="flex flex-col gap-3">
          <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Probabilitas Penilaian</h4>
          <ProbabilityBar
            label="Toxicity (Toksisitas)"
            value={result.probability_toxic}
            active={result.is_toxic}
            activeClassName="bg-rose-500"
            inactiveClassName="bg-emerald-500"
          />
          <ProbabilityBar
            label="Bullying (Intimidasi/Ejekan)"
            value={result.probability_bully}
            active={result.is_bully}
            activeClassName="bg-rose-400"
            inactiveClassName="bg-emerald-400"
          />
        </div>

        <div className="bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-800 rounded-lg p-3 text-xs leading-relaxed">
          <h4 className="font-bold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5 text-blue-500" /> Hasil Penjelasan
          </h4>
          <p className="text-gray-600 dark:text-gray-400 font-medium">{result.reason}</p>
        </div>

        {result.normalization_steps && (
          <details className="group border border-gray-100 dark:border-gray-800 rounded-lg overflow-hidden bg-white dark:bg-gray-800">
            <summary className="flex justify-between items-center text-xs font-semibold cursor-pointer list-none p-3 bg-gray-50/50 dark:bg-gray-900/50 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-gray-700 dark:text-gray-300">
              <span>Alur Normalisasi Teks</span>
              <span className="transition group-open:rotate-180 text-gray-400">▼</span>
            </summary>
            <div className="p-4 border-t border-gray-100 dark:border-gray-800 bg-gray-50/20 dark:bg-gray-900/20 text-xxs font-mono flex flex-col gap-3">
              {result.normalization_steps.map((step, index) => (
                <div key={`${step.name}-${index}`} className="flex flex-col gap-0.5 border-l-2 border-blue-200 dark:border-indigo-500/50 pl-2">
                  <span className="font-bold text-gray-800 dark:text-gray-200">{step.name}</span>
                  <span className="text-gray-500 dark:text-gray-400 break-all">{step.value}</span>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </motion.div>
  );
}
