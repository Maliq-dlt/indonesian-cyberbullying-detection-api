import React from 'react';
import { Search, RefreshCw, Download } from 'lucide-react';

interface FilterBarProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  decisionSourceFilter: string;
  setDecisionSourceFilter: (source: string) => void;
  confidenceFilter: string;
  setConfidenceFilter: (conf: string) => void;
  onRefresh: () => void;
  onExport: (format: 'csv' | 'json') => void;
  isLoading: boolean;
}

export default function FilterBar({
  searchQuery,
  setSearchQuery,
  decisionSourceFilter,
  setDecisionSourceFilter,
  confidenceFilter,
  setConfidenceFilter,
  onRefresh,
  onExport,
  isLoading
}: FilterBarProps) {
  return (
    <div className="bg-white border border-gray-150 p-4 rounded-xl shadow-xxs flex flex-wrap gap-4 items-center justify-between">
      <div className="flex flex-wrap gap-4 items-center flex-1">
        <div className="flex-1 min-w-[220px] relative">
          <label className="text-[10px] font-bold text-gray-400 block mb-1">CARI TEKS</label>
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Cari teks komentar..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg pl-8 pr-3 py-1.5 text-xs text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500"
            />
          </div>
        </div>
        
        <div className="min-w-[160px]">
          <label className="text-[10px] font-bold text-gray-400 block mb-1">SUMBER KEPUTUSAN</label>
          <select
            value={decisionSourceFilter}
            onChange={(e) => setDecisionSourceFilter(e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 cursor-pointer"
          >
            <option value="">Semua Sumber</option>
            <option value="Model Core">Model Core</option>
            <option value="Lexicon Match">Lexicon Match</option>
            <option value="Transformers">Transformers</option>
            <option value="Koreksi Manusia">Koreksi Manusia</option>
          </select>
        </div>

        <div className="min-w-[180px]">
          <label className="text-[10px] font-bold text-gray-400 block mb-1">TINGKAT KEYAKINAN (CONFIDENCE)</label>
          <select
            value={confidenceFilter}
            onChange={(e) => setConfidenceFilter(e.target.value)}
            className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 cursor-pointer"
          >
            <option value="">Semua Tingkat</option>
            <option value="uncertain">Ragu-ragu (0.4 - 0.7)</option>
            <option value="certain">Yakin (&gt; 0.8)</option>
          </select>
        </div>
      </div>

      <div className="flex gap-2 items-center">
        <div className="relative group">
          <button
            className="bg-indigo-650 hover:bg-indigo-750 text-white text-xs font-bold px-3 py-2 rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 border-none shadow-sm dark:bg-indigo-600 dark:hover:bg-indigo-700"
          >
            <Download className="w-3.5 h-3.5" /> Ekspor Dataset
          </button>
          <div className="absolute right-0 top-full mt-1 bg-white dark:bg-slate-800 border border-gray-150 dark:border-gray-800 rounded-xl shadow-xl w-32 hidden group-hover:block hover:block z-50 overflow-hidden text-xs">
            <button
              onClick={() => onExport('csv')}
              className="w-full text-left px-4 py-2.5 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-slate-700 border-none bg-transparent cursor-pointer font-bold"
            >
              Format CSV
            </button>
            <button
              onClick={() => onExport('json')}
              className="w-full text-left px-4 py-2.5 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-slate-700 border-none bg-transparent cursor-pointer font-bold border-t border-gray-100 dark:border-gray-850"
            >
              Format JSON
            </button>
          </div>
        </div>

        <button
          onClick={onRefresh}
          className="bg-gray-50 dark:bg-slate-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 border border-gray-200 dark:border-gray-700 p-2 rounded-lg transition-colors cursor-pointer flex items-center justify-center"
          title="Refresh Data"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </div>
  );
}
