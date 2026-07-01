import React, { useState } from 'react';
import { m } from 'framer-motion';

export interface HistoryDataPoint {
  id?: number;
  timestamp: string;
  f1_toxic: number;
  f1_bully: number;
  threshold_toxic?: number;
  threshold_bully?: number;
  active_version: string;
}

const mockHistory: HistoryDataPoint[] = [
  { id: 1, timestamp: '2026-06-01', f1_toxic: 0.81, f1_bully: 0.78, threshold_toxic: 0.5, threshold_bully: 0.5, active_version: 'v1.0.0-mock' },
  { id: 2, timestamp: '2026-06-02', f1_toxic: 0.83, f1_bully: 0.81, threshold_toxic: 0.5, threshold_bully: 0.5, active_version: 'v1.0.1-mock' },
  { id: 3, timestamp: '2026-06-03', f1_toxic: 0.85, f1_bully: 0.83, threshold_toxic: 0.5, threshold_bully: 0.5, active_version: 'v1.1.0-mock' },
  { id: 4, timestamp: '2026-06-04', f1_toxic: 0.88, f1_bully: 0.86, threshold_toxic: 0.5, threshold_bully: 0.5, active_version: 'v1.2.0-mock' },
  { id: 5, timestamp: '2026-06-05', f1_toxic: 0.91, f1_bully: 0.89, threshold_toxic: 0.5, threshold_bully: 0.5, active_version: 'v2.0.0-mock' },
];

interface DashboardHistoryChartProps {
  historyData: HistoryDataPoint[];
}

export default function DashboardHistoryChart({ historyData }: DashboardHistoryChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const isMock = historyData.length === 0;
  const chartData = isMock ? mockHistory : historyData;

  const width = 600;
  const height = 240;
  const padLeft = 45;
  const padRight = 20;
  const padTop = 30;
  const padBottom = 35;

  const chartWidth = width - padLeft - padRight;
  const chartHeight = height - padTop - padBottom;

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

  const yTicks = [0.6, 0.7, 0.8, 0.9, 1.0].filter(t => t >= minF1);

  return (
    <div className="flex flex-col lg:flex-row gap-8 w-full">
      {/* Left Side: Interactive Line Chart */}
      <div className="flex-1 flex flex-col gap-4 relative">
        <div className="flex justify-between items-center">
          <div className="flex gap-4 text-xxs font-bold uppercase tracking-wider">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-1 bg-rose-500 rounded-full inline-block"></span>
              <span className="text-gray-600 dark:text-gray-300">F1 Toxicity</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-1 bg-indigo-500 rounded-full inline-block"></span>
              <span className="text-gray-600 dark:text-gray-300">F1 Bullying</span>
            </div>
          </div>
          {isMock && (
            <span className="text-[9px] font-black uppercase tracking-wider text-amber-600 bg-amber-50 dark:bg-amber-950/40 px-2.5 py-0.5 rounded-full border border-amber-200/50">
              Visualisasi Simulasi
            </span>
          )}
        </div>

        <div className="w-full overflow-hidden bg-gray-50/20 dark:bg-slate-950/20 border border-gray-100 dark:border-gray-800/40 rounded-2xl p-4 relative">
          <svg 
            viewBox={`0 0 ${width} ${height}`} 
            className="w-full h-auto overflow-visible select-none"
            onMouseLeave={() => setHoveredIdx(null)}
          >
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

            {/* Animated Path for F1 Toxicity */}
            <m.path 
              d={toxicPath} 
              fill="none" 
              stroke="#f43f5e" 
              strokeWidth="3" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="drop-shadow-[0_4px_8px_rgba(244,63,94,0.2)]"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1.5, ease: "easeInOut" }}
            />

            {/* Animated Path for F1 Bullying */}
            <m.path 
              d={bullyPath} 
              fill="none" 
              stroke="#6366f1" 
              strokeWidth="3" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="drop-shadow-[0_4px_8px_rgba(99,102,241,0.2)]"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1.5, ease: "easeInOut" }}
            />

            {/* Interactive Hover Hitboxes */}
            {chartData.map((d, idx) => {
              const x = getX(idx);
              return (
                <rect
                  key={`hitbox-${idx}`}
                  x={x - (chartWidth / (chartData.length * 2))}
                  y={padTop}
                  width={chartWidth / chartData.length}
                  height={chartHeight}
                  fill="transparent"
                  className="cursor-pointer"
                  onMouseEnter={() => setHoveredIdx(idx)}
                />
              );
            })}

            {/* Toxic Points */}
            {chartData.map((d, idx) => {
              const x = getX(idx);
              const y = getY(d.f1_toxic);
              const isHovered = hoveredIdx === idx;
              return (
                <circle 
                  key={`toxic-pt-${idx}`} 
                  cx={x} 
                  cy={y} 
                  r={isHovered ? "6" : "4.5"} 
                  fill="#ffffff" 
                  stroke="#f43f5e" 
                  strokeWidth={isHovered ? "3.5" : "2.5"} 
                  className="transition-all duration-150"
                />
              );
            })}

            {/* Bully Points */}
            {chartData.map((d, idx) => {
              const x = getX(idx);
              const y = getY(d.f1_bully);
              const isHovered = hoveredIdx === idx;
              return (
                <circle 
                  key={`bully-pt-${idx}`} 
                  cx={x} 
                  cy={y} 
                  r={isHovered ? "6" : "4.5"} 
                  fill="#ffffff" 
                  stroke="#6366f1" 
                  strokeWidth={isHovered ? "3.5" : "2.5"} 
                  className="transition-all duration-150"
                />
              );
            })}

            {/* Vertical Guide Line on Hover */}
            {hoveredIdx !== null && (
              <line
                x1={getX(hoveredIdx)}
                y1={padTop}
                x2={getX(hoveredIdx)}
                y2={height - padBottom}
                stroke="#3b82f6"
                strokeWidth="1.5"
                strokeDasharray="3 3"
                className="opacity-65 pointer-events-none"
              />
            )}

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

          {/* Custom Interactive Tooltip Card */}
          {hoveredIdx !== null && (
            <m.div
              initial={{ opacity: 0, scale: 0.95, y: -8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              className="absolute bg-slate-955/95 dark:bg-slate-900/95 text-white p-3.5 rounded-2xl border border-slate-800 shadow-2xl pointer-events-none text-xxs flex flex-col gap-1.5 z-40 font-semibold"
              style={{
                left: `${(getX(hoveredIdx) / width) * 100}%`,
                top: `${(getY(Math.max(chartData[hoveredIdx].f1_toxic, chartData[hoveredIdx].f1_bully)) / height) * 100 - 32}%`,
                transform: 'translateX(-50%) translateY(-100%)',
              }}
            >
              <div className="font-bold border-b border-slate-800 pb-1.5 text-slate-300">
                Versi: {chartData[hoveredIdx].active_version}
              </div>
              <div className="flex justify-between gap-6">
                <span className="text-gray-400">F1 Toxicity:</span>
                <span className="text-rose-400 font-bold">{chartData[hoveredIdx].f1_toxic.toFixed(4)}</span>
              </div>
              <div className="flex justify-between gap-6">
                <span className="text-gray-400">F1 Bullying:</span>
                <span className="text-indigo-400 font-bold">{chartData[hoveredIdx].f1_bully.toFixed(4)}</span>
              </div>
              <div className="text-[8px] text-gray-500 font-medium">
                Tanggal: {chartData[hoveredIdx].timestamp.split('T')[0] || chartData[hoveredIdx].timestamp}
              </div>
            </m.div>
          )}
        </div>
      </div>

      {/* Right Side: Training Stats Summary & Table */}
      <div className="w-full lg:w-72 flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Metrik Performa Puncak</span>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-rose-50/30 dark:bg-rose-950/10 border border-rose-100 dark:border-rose-900/20 p-3 rounded-xl flex flex-col gap-0.5">
              <span className="text-[9px] font-bold text-rose-500 dark:text-rose-400 uppercase">Tox F1 Peak</span>
              <span className="text-lg font-black text-rose-700 dark:text-rose-400">
                {Math.max(...chartData.map(d => d.f1_toxic)).toFixed(2)}
              </span>
            </div>
            <div className="bg-indigo-50/30 dark:bg-indigo-950/10 border border-indigo-100 dark:border-indigo-900/20 p-3 rounded-xl flex flex-col gap-0.5">
              <span className="text-[9px] font-bold text-indigo-500 dark:text-indigo-400 uppercase">Bully F1 Peak</span>
              <span className="text-lg font-black text-indigo-700 dark:text-indigo-400">
                {Math.max(...chartData.map(d => d.f1_bully)).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Riwayat Siklus Terakhir</span>
          <div className="flex flex-col gap-2 bg-gray-50/40 dark:bg-slate-950/15 border border-gray-100 dark:border-gray-800/40 rounded-2xl p-2.5 max-h-36 overflow-y-auto custom-scrollbar">
            {chartData.slice(-3).reverse().map((run, idx) => (
              <div key={idx} className="flex justify-between items-center text-[10px] border-b border-gray-100 dark:border-gray-800/30 pb-2 last:border-b-0 last:pb-0">
                <div className="flex flex-col">
                  <span className="font-bold text-gray-800 dark:text-gray-200 truncate max-w-28">{run.active_version}</span>
                  <span className="text-[8px] text-gray-400 font-semibold">{run.timestamp.split('T')[0] || run.timestamp}</span>
                </div>
                <div className="flex gap-2 font-mono font-bold">
                  <span className="text-rose-500">T:{run.f1_toxic.toFixed(2)}</span>
                  <span className="text-indigo-500">B:{run.f1_bully.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
