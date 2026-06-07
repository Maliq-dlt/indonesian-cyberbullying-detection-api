import type { WordImportance } from '../XAIHighlightText';

export type ModelId =
  | 'hybrid'
  | 'lexicon'
  | 'ml'
  | 'transformers'
  | 'ensemble'
  | 'comparison';

export interface DetectorProps {
  apiUrl: string;
  apiKey: string;
}

export interface NormalizationStep {
  name: string;
  value: string;
}

export interface PredictionResult {
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

export interface ComparisonResult extends PredictionResult {
  name: string;
  status: 'ONLINE' | 'OFFLINE';
}

export interface ModelOption {
  id: ModelId;
  label: string;
  badge?: string;
}

export interface DetectorState {
  text: string;
  selectedModel: ModelId;
  useFuzzy: boolean;
  loading: boolean;
  result: PredictionResult | null;
  comparisonResults: ComparisonResult[] | null;
  isDrawerOpen: boolean;
}
