import { motion } from 'framer-motion';
import type { ComparisonResult } from './types';
import { isCacheHit, isDangerous, percent } from './utils';

interface ComparisonResultCardProps {
  results: ComparisonResult[];
  hasXaiDetail: boolean;
  onOpenXai: () => void;
}

export function ComparisonResultCard({ results, hasXaiDetail, onOpenXai }: ComparisonResultCardProps) {
  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="premium-card p-5 flex flex-col gap-4 border border-gray-150"
    >
      <div className="border-b border-gray-100 dark:border-gray-800/60 pb-3 flex justify-between items-start">
        <div>
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            Hasil Perbandingan Multi-Model
          </span>
          <h3 className="text-sm font-bold text-gray-900 dark:text-gray-200 leading-tight">Auditing Diagnosis AI</h3>
        </div>

        {hasXaiDetail && (
          <button
            type="button"
            onClick={onOpenXai}
            className="text-[10px] font-bold text-blue-600 dark:text-indigo-400 hover:underline flex items-center gap-1 cursor-pointer bg-transparent border-none p-0"
          >
            Detail XAI →
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
            {results.map((result) => (
              <ComparisonRow key={result.name} result={result} />
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col gap-2 mt-2">
        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Hasil Analisis & Penjelasan</span>
        <div className="flex flex-col gap-2">
          {results
            .filter((result) => result.status === 'ONLINE')
            .map((result) => (
              <div
                key={`${result.name}-reason`}
                className="bg-gray-50/50 dark:bg-slate-950/20 border border-gray-100 dark:border-gray-800/40 p-2.5 rounded-lg text-[10px] leading-relaxed"
              >
                <strong className="text-gray-800 dark:text-gray-300">{result.name}:</strong>{' '}
                <span className="text-gray-500 dark:text-gray-400">{result.reason}</span>
              </div>
            ))}
        </div>
      </div>
    </motion.div>
  );
}

function ComparisonRow({ result }: { result: ComparisonResult }) {
  const dangerous = isDangerous(result);
  const cacheHit = result.status === 'ONLINE' && isCacheHit(result);

  return (
    <tr className="hover:bg-gray-50/50 dark:hover:bg-slate-900/40 transition-colors">
      <td className="py-2.5 font-bold text-gray-850 dark:text-gray-200">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span>{result.name}</span>
          {cacheHit && (
            <span
              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-tighter bg-gradient-to-r from-blue-500/10 to-indigo-500/10 text-blue-600 dark:text-indigo-400 border border-blue-400/20 shadow-xxs animate-pulse"
              title="Semantic Cache Bypass (Resource Saved)"
            >
              Cache Hit
            </span>
          )}
        </div>

        {result.status === 'ONLINE' && result.execution_time !== undefined && (
          <div className="text-[9px] text-gray-400 dark:text-gray-500 font-mono font-normal">
            ⏱️ {result.execution_time}ms
          </div>
        )}
      </td>

      <td className="py-2.5 text-center">
        <span
          className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
            result.status === 'ONLINE'
              ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30'
              : 'bg-gray-100 text-gray-400 dark:bg-slate-800'
          }`}
        >
          {result.status}
        </span>
      </td>

      <td className="py-2.5 text-center">
        {result.status === 'OFFLINE' ? (
          <span className="text-gray-400">-</span>
        ) : (
          <span
            className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
              dangerous ? 'bg-rose-50 text-rose-600 dark:bg-rose-950/30' : 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30'
            }`}
          >
            {dangerous ? 'Bahaya' : 'Aman'}
          </span>
        )}
      </td>

      <td className="py-2.5 text-right font-mono font-bold text-gray-650 dark:text-gray-300">
        {result.status === 'OFFLINE' ? '-' : percent(result.probability_toxic)}
      </td>
      <td className="py-2.5 text-right font-mono font-bold text-gray-650 dark:text-gray-300">
        {result.status === 'OFFLINE' ? '-' : percent(result.probability_bully)}
      </td>
    </tr>
  );
}
