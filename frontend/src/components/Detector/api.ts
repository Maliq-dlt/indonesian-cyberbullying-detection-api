import type { WordImportance } from '../XAIHighlightText';
import { COMPARISON_ENDPOINTS } from './constants';
import type { ComparisonResult, ModelId, PredictionResult } from './types';
import { buildNormalizationSteps, clampProbability } from './utils';

interface LexiconMatch {
  matched_phrase: string;
  category: string;
  severity: string;
  method: string;
}

interface ApiResponse {
  is_toxic?: boolean;
  is_cyberbullying?: boolean;
  is_bully?: boolean;
  normalized_spaced?: string;
  probability_toxic?: number;
  probability_bully?: number;
  score?: number;
  category?: string;
  decision_source?: string;
  reason?: string;
  matches?: LexiconMatch[];
  word_importances?: WordImportance[];
  execution_time?: number;
  risk_label?: string;
}

interface AnalyzeSingleParams {
  apiUrl: string;
  apiKey: string;
  text: string;
  selectedModel: ModelId;
  useFuzzy: boolean;
}

interface AnalyzeComparisonParams {
  apiUrl: string;
  apiKey: string;
  text: string;
  useFuzzy: boolean;
}

function buildHeaders(apiKey: string): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (apiKey) headers['x-api-key'] = apiKey;
  return headers;
}

function getEndpoint(model: ModelId): string {
  switch (model) {
    case 'lexicon':
      return '/predict/lexicon';
    case 'ml':
      return '/predict/ml';
    case 'transformers':
      return '/predict/transformers';
    case 'ensemble':
      return '/predict/ensemble';
    case 'hybrid':
    case 'comparison':
    default:
      return '/predict/hybrid';
  }
}

function normalizePredictionData(
  data: ApiResponse,
  text: string,
  fallbackSource: string,
  elapsedMs?: number,
): PredictionResult {
  const isToxic = data.is_toxic !== undefined ? Boolean(data.is_toxic) : Boolean(data.is_cyberbullying);
  const isBully = data.is_bully !== undefined ? Boolean(data.is_bully) : Boolean(data.is_cyberbullying);
  const cleanText = data.normalized_spaced || text.toLowerCase();

  return {
    text,
    is_toxic: isToxic,
    is_bully: isBully,
    probability_toxic: clampProbability(
      data.probability_toxic,
      data.score ? clampProbability(data.score / 10) : 0.1,
    ),
    probability_bully: clampProbability(
      data.probability_bully,
      data.score ? clampProbability(data.score / 10) : 0.1,
    ),
    category: data.category || (data.risk_label ? `Risiko ${data.risk_label}` : 'Aman'),
    decision_source: data.decision_source || fallbackSource,
    reason:
      data.reason ||
      (Array.isArray(data.matches) && data.matches.length > 0
        ? `Ditemukan kata ofensif: ${data.matches.map((m: LexiconMatch) => m.matched_phrase).join(', ')}`
        : 'Tidak ditemukan pola penyerangan atau toksisitas.'),
    normalization_steps: buildNormalizationSteps(text, cleanText),
    word_importances: Array.isArray(data.word_importances) ? data.word_importances : [],
    execution_time: data.execution_time ?? (elapsedMs !== undefined ? Number(elapsedMs.toFixed(2)) : undefined),
  };
}


export async function analyzeSingle(params: AnalyzeSingleParams): Promise<PredictionResult> {
  const { apiUrl, apiKey, text, selectedModel, useFuzzy } = params;
  const endpoint = getEndpoint(selectedModel);
  const payload: Record<string, unknown> = { text };

  if (selectedModel === 'lexicon') payload.use_fuzzy = useFuzzy;

  const startTime = performance.now();
  const response = await fetch(`${apiUrl}${endpoint}`, {
    method: 'POST',
    headers: buildHeaders(apiKey),
    body: JSON.stringify(payload),
  });
  const elapsed = performance.now() - startTime;

  if (!response.ok) {
    throw new Error(`Backend mengembalikan status ${response.status}: ${response.statusText}`);
  }

  const data = await response.json();
  return normalizePredictionData(
    data,
    text,
    selectedModel === 'lexicon' ? 'Lexicon Model' : 'Model Core',
    elapsed,
  );
}

export async function analyzeComparison(params: AnalyzeComparisonParams): Promise<ComparisonResult[]> {
  const { apiUrl, apiKey, text, useFuzzy } = params;
  const headers = buildHeaders(apiKey);

  const requests = COMPARISON_ENDPOINTS.map(async (endpoint) => {
    try {
      const payload: Record<string, unknown> = { text };
      if (endpoint.name === 'Lexicon') payload.use_fuzzy = useFuzzy;

      const startTime = performance.now();
      const response = await fetch(`${apiUrl}${endpoint.path}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });
      const elapsed = performance.now() - startTime;

      if (!response.ok) throw new Error('Offline');

      const data = await response.json();
      const normalized = normalizePredictionData(data, text, endpoint.name, elapsed);

      return {
        ...normalized,
        name: endpoint.name,
        status: 'ONLINE' as const,
      };
    } catch {
      return createOfflineResult(endpoint.name, text);
    }
  });

  return Promise.all(requests);
}

export function createOfflineFallback(text: string): PredictionResult {
  const lowerText = text.toLowerCase();
  let isToxic = false;
  let isBully = false;
  let reason = 'Teks dianalisis bersih dari indikasi cyberbullying atau toksisitas.';
  let category = 'Non-Toxic & Non-Bully (Aman)';

  if (/(anjing|goblok|tolol|bego)/i.test(lowerText)) {
    isToxic = true;
    reason = 'Terdeteksi kata kasar/abusive language.';
    category = 'Toxic but Non-Bully (Casual Slang / Swearing)';
  }

  if (/(dasar|jelek|mati aja)/i.test(lowerText)) {
    isBully = true;
    reason = 'Mengandung indikasi intimidasi atau serangan pribadi langsung.';
    category = isToxic ? 'Toxic & Bully (Serangan Langsung)' : 'Non-Toxic but Bully (Sarcasm / Insult)';
  }

  const word_importances: WordImportance[] = lowerText.split(/\s+/).filter(Boolean).map((word) => {
    if (/(anjing|goblok|tolol|bego)/i.test(word)) {
      return { word, weight_toxic: 0.85, weight_bully: 0.35 };
    }
    if (/(dasar|jelek|mati)/i.test(word)) {
      return { word, weight_toxic: 0.22, weight_bully: 0.78 };
    }
    return { word, weight_toxic: 0.02, weight_bully: 0.01 };
  });

  return {
    text,
    is_toxic: isToxic,
    is_bully: isBully,
    probability_toxic: isToxic ? 0.88 : 0.08,
    probability_bully: isBully ? 0.79 : 0.12,
    category,
    decision_source: 'Sandbox Offline Fallback',
    reason,
    word_importances,
    normalization_steps: buildNormalizationSteps(text, lowerText),
  };
}

function createOfflineResult(name: string, text: string): ComparisonResult {
  return {
    name,
    text,
    status: 'OFFLINE',
    is_toxic: false,
    is_bully: false,
    probability_toxic: 0,
    probability_bully: 0,
    category: '-',
    decision_source: name,
    reason: 'Model sedang dinonaktifkan di backend.',
    word_importances: [],
    execution_time: 0,
  };
}
