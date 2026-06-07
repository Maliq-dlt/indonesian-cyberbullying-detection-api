import type { ModelOption } from './types';

export const MAX_TEXT_LENGTH = 500;

export const MODEL_OPTIONS: ModelOption[] = [
  { id: 'hybrid', label: 'Hybrid AI', badge: 'Rekomendasi' },
  { id: 'lexicon', label: 'Lexicon' },
  { id: 'ml', label: 'Machine Learning' },
  { id: 'transformers', label: 'Transformer (DL)' },
  { id: 'ensemble', label: 'Ensemble' },
  { id: 'comparison', label: 'Audit Multi-Model', badge: 'New' },
];

export const COMPARISON_ENDPOINTS = [
  { name: 'Hybrid AI', path: '/predict/hybrid' },
  { name: 'Lexicon', path: '/predict/lexicon', payload: { use_fuzzy: true } },
  { name: 'Machine Learning', path: '/predict/ml' },
  { name: 'Transformer (DL)', path: '/predict/transformers' },
  { name: 'Ensemble', path: '/predict/ensemble' },
] as const;
