import { useState } from 'react';
import { toast } from 'sonner';
import { analyzeComparison, analyzeSingle, createOfflineFallback } from './api';
import { MAX_TEXT_LENGTH } from './constants';
import type { ComparisonResult, ModelId, PredictionResult } from './types';
import { getErrorMessage } from './utils';

interface UseDetectorReturn {
  text: string;
  selectedModel: ModelId;
  useFuzzy: boolean;
  loading: boolean;
  result: PredictionResult | null;
  comparisonResults: ComparisonResult[] | null;
  isDrawerOpen: boolean;
  setText: (value: string) => void;
  setSelectedModel: (value: ModelId) => void;
  setUseFuzzy: (value: boolean) => void;
  setIsDrawerOpen: (value: boolean) => void;
  analyze: () => Promise<void>;
}

function validateText(text: string): boolean {
  if (text.trim().length === 0) {
    toast.error('Masukkan teks terlebih dahulu!');
    return false;
  }

  if (text.length > MAX_TEXT_LENGTH) {
    toast.error(`Teks tidak boleh melebihi ${MAX_TEXT_LENGTH} karakter!`);
    return false;
  }

  return true;
}

export function useDetector(apiUrl: string, apiKey: string): UseDetectorReturn {
  const [text, setText] = useState('');
  const [selectedModel, setSelectedModel] = useState<ModelId>('hybrid');
  const [useFuzzy, setUseFuzzy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [comparisonResults, setComparisonResults] = useState<ComparisonResult[] | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const resetOutput = () => {
    setResult(null);
    setComparisonResults(null);
    setIsDrawerOpen(false);
  };

  const analyze = async () => {
    if (!validateText(text)) return;

    setLoading(true);
    resetOutput();

    if (selectedModel === 'comparison') {
      try {
        const results = await analyzeComparison({ apiUrl, apiKey, text, useFuzzy });
        setComparisonResults(results);

        const defaultResult =
          results.find((item) => item.name === 'Hybrid AI' && item.status === 'ONLINE') ||
          results.find((item) => item.status === 'ONLINE');

        if (defaultResult) {
          setResult({ ...defaultResult });
          toast.success('Analisis perbandingan selesai!');
        } else {
          toast.error('Semua model di server offline.');
        }
      } catch (error) {
        console.error(error);
        toast.error(`Gagal melakukan analisis perbandingan: ${getErrorMessage(error)}`);
      } finally {
        setLoading(false);
      }

      return;
    }

    try {
      const prediction = await analyzeSingle({ apiUrl, apiKey, text, selectedModel, useFuzzy });
      setResult(prediction);
      toast.success('Analisis teks selesai!');
    } catch (error) {
      console.error(error);
      toast.error('Gagal analisis. Menjalankan simulasi sandbox offline.');

      window.setTimeout(() => {
        setResult(createOfflineFallback(text));
        setLoading(false);
      }, 800);

      return;
    }

    setLoading(false);
  };

  return {
    text,
    selectedModel,
    useFuzzy,
    loading,
    result,
    comparisonResults,
    isDrawerOpen,
    setText,
    setSelectedModel,
    setUseFuzzy,
    setIsDrawerOpen,
    analyze,
  };
}
