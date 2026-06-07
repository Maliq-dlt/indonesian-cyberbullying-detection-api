import { Activity, CheckCircle, RefreshCw } from 'lucide-react';
import { MAX_TEXT_LENGTH, MODEL_OPTIONS } from './constants';
import type { ModelId } from './types';

interface InputPanelProps {
  text: string;
  selectedModel: ModelId;
  useFuzzy: boolean;
  loading: boolean;
  onTextChange: (value: string) => void;
  onModelChange: (value: ModelId) => void;
  onUseFuzzyChange: (value: boolean) => void;
  onAnalyze: () => void;
}

export function InputPanel(props: InputPanelProps) {
  const {
    text,
    selectedModel,
    useFuzzy,
    loading,
    onTextChange,
    onModelChange,
    onUseFuzzyChange,
    onAnalyze,
  } = props;

  const isAnalyzeDisabled = loading || text.trim().length === 0 || text.length > MAX_TEXT_LENGTH;
  const showFuzzyToggle = selectedModel === 'lexicon' || selectedModel === 'comparison';

  return (
    <div className="lg:col-span-7 flex flex-col gap-5">
      <div className="premium-card p-5 flex flex-col gap-3">
        <label htmlFor="detector-text" className="text-sm font-bold text-gray-900">
          Masukkan Kalimat / Komentar Bahasa Indonesia
        </label>

        <div className="rounded-xl border border-gray-100 bg-white overflow-hidden shadow-sm">
          <textarea
            id="detector-text"
            value={text}
            onChange={(event) => onTextChange(event.target.value)}
            placeholder="Contoh: 'Semangat belajarnya ya!' atau 'kamu tolol banget sih goblok'"
            className="w-full h-36 p-4 bg-transparent border-none outline-none text-sm text-gray-800 resize-none font-medium placeholder:text-gray-400"
            maxLength={MAX_TEXT_LENGTH}
          />
        </div>

        <div className="flex justify-between items-center text-xs text-gray-400">
          <span className="font-semibold">
            {text.length} / {MAX_TEXT_LENGTH} karakter
          </span>
          {text.length > MAX_TEXT_LENGTH && (
            <span className="text-rose-500 font-semibold">Melebihi batas maksimal</span>
          )}
        </div>
      </div>

      <div className="premium-card p-6 flex flex-col gap-4">
        <div>
          <h3 className="text-sm font-bold text-gray-900 mb-2.5">Pilih Model Pendeteksian</h3>
          <div className="flex flex-wrap gap-2">
            {MODEL_OPTIONS.map((model) => (
              <button
                key={model.id}
                type="button"
                onClick={() => onModelChange(model.id)}
                className={`px-3.5 py-2 rounded-full text-xs font-semibold border transition-all duration-200 cursor-pointer ${
                  selectedModel === model.id
                    ? 'bg-blue-50 border-blue-200 text-blue-600 shadow-sm'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                {model.label}
                {model.badge && (
                  <span className="ml-1 bg-blue-600 text-white font-bold px-1.5 py-0.5 rounded-full text-[9px] uppercase tracking-wider">
                    {model.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {showFuzzyToggle && (
          <div className="bg-gray-50 border border-gray-100 p-3 rounded-lg flex items-center justify-between transition-all animate-fade-in">
            <div className="flex items-center gap-2 text-xs text-gray-600 font-medium">
              <CheckCircle className="w-4 h-4 text-gray-400" />
              Gunakan Fuzzy Matching untuk Model Lexicon
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={useFuzzy}
                onChange={(event) => onUseFuzzyChange(event.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600" />
            </label>
          </div>
        )}

        <button
          type="button"
          onClick={onAnalyze}
          disabled={isAnalyzeDisabled}
          className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-xl text-sm font-bold hover:shadow-lg hover:shadow-blue-500/20 active:scale-98 transition-all disabled:opacity-50 cursor-pointer border-none flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Menganalisis...
            </>
          ) : (
            <>
              <Activity className="w-4 h-4" />
              Analisis Sekarang
            </>
          )}
        </button>
      </div>
    </div>
  );
}
