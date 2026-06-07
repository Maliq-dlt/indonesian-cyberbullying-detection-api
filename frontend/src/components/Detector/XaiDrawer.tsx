import { AnimatePresence, motion } from 'framer-motion';
import { Info, X } from 'lucide-react';
import { XAIHighlightText } from '../XAIHighlightText';
import type { PredictionResult } from './types';

interface XaiDrawerProps {
  isOpen: boolean;
  result: PredictionResult | null;
  onClose: () => void;
}

export function XaiDrawer({ isOpen, result, onClose }: XaiDrawerProps) {
  return (
    <AnimatePresence>
      {isOpen && result && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.4 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black z-50 cursor-pointer"
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 26, stiffness: 220 }}
            className="fixed top-0 right-0 h-full w-full sm:w-[480px] bg-white dark:bg-slate-900 border-l border-gray-200 dark:border-gray-800 shadow-2xl z-50 p-6 overflow-y-auto flex flex-col gap-6"
          >
            <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-800 pb-4">
              <div>
                <h2 className="text-lg font-black text-gray-900 dark:text-gray-100">Detail Analisis XAI</h2>
                <p className="text-xxs text-gray-400">Kontribusi bobot penting tiap kata dalam kalimat.</p>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="p-1.5 rounded-lg bg-gray-50 dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 text-gray-400 dark:text-gray-300 transition-colors border-none cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-gray-50/50 dark:bg-slate-950/20 border border-gray-150 p-4 rounded-xl flex flex-col gap-2">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Teks Analisis</span>
              <div className="text-sm font-medium text-gray-850 dark:text-gray-200 leading-relaxed">
                <XAIHighlightText text={result.text} wordImportances={result.word_importances} />
              </div>
            </div>

            <XaiBarChart result={result} />

            <div className="bg-blue-50/30 dark:bg-slate-950/20 border border-blue-100/40 p-3 rounded-lg flex items-start gap-2.5 mt-auto">
              <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
              <p className="text-[10px] text-gray-500 dark:text-gray-400 leading-normal">
                Bobot kontribusi penting tiap token menunjukkan seberapa kuat kata tersebut memicu model untuk menentukan
                klasifikasi bahaya. Nilai ini adalah alat bantu interpretasi, bukan bukti mutlak bahwa satu kata selalu
                bermakna toxic atau bullying di semua konteks.
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function XaiBarChart({ result }: { result: PredictionResult }) {
  const importances = (result.word_importances || []).filter((item) => item.word.trim().length > 0);

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
  const maxWeight = Math.max(
    0.01,
    ...importances.map((item) => Math.max(Math.abs(item.weight_toxic), Math.abs(item.weight_bully))),
  );

  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-between items-center">
        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
          Grafik Kontribusi Kata (SHAP Weights)
        </span>
        <div className="flex gap-3 text-[9px] font-bold">
          <span className="text-rose-500">■ Toxic</span>
          <span className="text-purple-500">■ Bullying</span>
        </div>
      </div>

      <div className="w-full overflow-hidden bg-gray-50/20 dark:bg-slate-950/10 border border-gray-100 dark:border-gray-800/40 rounded-xl p-3">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto overflow-visible select-none">
          {importances.map((item, index) => {
            const y = index * rowSpacing + 5;
            const toxicWidth = (Math.abs(item.weight_toxic) / maxWeight) * (chartAreaWidth - 50);
            const bullyWidth = (Math.abs(item.weight_bully) / maxWeight) * (chartAreaWidth - 50);

            return (
              <g key={`${item.word}-${index}`}>
                <text
                  x={textColWidth - 8}
                  y={y + 15}
                  textAnchor="end"
                  className="text-[11px] font-bold fill-gray-800 dark:fill-gray-200"
                >
                  {item.word}
                </text>

                <rect
                  x={textColWidth}
                  y={y + 2}
                  width={chartAreaWidth}
                  height={barHeight}
                  rx="2"
                  fill="currentColor"
                  className="text-gray-100/50 dark:text-slate-800/30"
                />
                <rect x={textColWidth} y={y + 2} width={toxicWidth} height={barHeight} rx="2" fill="#f43f5e">
                  <title>{`Toxicity Weight: ${item.weight_toxic.toFixed(4)}`}</title>
                </rect>
                {item.weight_toxic > 0 && (
                  <text
                    x={textColWidth + toxicWidth + 5}
                    y={y + 9}
                    className="text-[8px] font-bold font-mono fill-rose-650 dark:fill-rose-450"
                  >
                    +{item.weight_toxic.toFixed(4)}
                  </text>
                )}

                <rect
                  x={textColWidth}
                  y={y + 14}
                  width={chartAreaWidth}
                  height={barHeight}
                  rx="2"
                  fill="currentColor"
                  className="text-gray-100/50 dark:text-slate-800/30"
                />
                <rect x={textColWidth} y={y + 14} width={bullyWidth} height={barHeight} rx="2" fill="#a855f7">
                  <title>{`Bullying Weight: ${item.weight_bully.toFixed(4)}`}</title>
                </rect>
                {item.weight_bully > 0 && (
                  <text
                    x={textColWidth + bullyWidth + 5}
                    y={y + 21}
                    className="text-[8px] font-bold font-mono fill-purple-650 dark:fill-purple-450"
                  >
                    +{item.weight_bully.toFixed(4)}
                  </text>
                )}

                {index < importances.length - 1 && (
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
    </div>
  );
}
