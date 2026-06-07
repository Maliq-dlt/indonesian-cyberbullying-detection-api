import type { NormalizationStep, PredictionResult } from './types';

export function clampProbability(value: unknown, fallback = 0.1): number {
  if (typeof value !== 'number' || Number.isNaN(value)) return fallback;
  return Math.max(0, Math.min(1, value));
}

export function percent(value: number): string {
  return `${Math.round(clampProbability(value, 0) * 100)}%`;
}

export function isDangerous(result: Pick<PredictionResult, 'is_toxic' | 'is_bully'>): boolean {
  return Boolean(result.is_toxic || result.is_bully);
}

export function isCacheHit(result: Pick<PredictionResult, 'execution_time' | 'decision_source'>): boolean {
  return Boolean(
    (result.execution_time !== undefined && result.execution_time <= 3.0) ||
      /cache|database|semantic/i.test(result.decision_source || ''),
  );
}

export function buildNormalizationSteps(rawText: string, cleanText: string): NormalizationStep[] {
  return [
    { name: 'Input Mentah', value: `"${rawText}"` },
    { name: 'Pembersihan & Lowercase', value: `"${rawText.toLowerCase()}"` },
    { name: 'Normalisasi Slang / Alay', value: `"${cleanText}"` },
    { name: 'Final Tokens', value: JSON.stringify(cleanText.split(/\s+/).filter(Boolean)) },
  ];
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return 'Terjadi kesalahan tidak diketahui.';
}
