import { describe, test, expect } from 'vitest';
import {
  clampProbability,
  percent,
  isDangerous,
  isCacheHit,
  buildNormalizationSteps,
  getErrorMessage,
} from './utils';

describe('clampProbability', () => {
  test('should clamp value between 0 and 1', () => {
    expect(clampProbability(0.5)).toBe(0.5);
    expect(clampProbability(-0.5)).toBe(0);
    expect(clampProbability(1.5)).toBe(1);
    expect(clampProbability(0)).toBe(0);
    expect(clampProbability(1)).toBe(1);
  });

  test('should return fallback for NaN or non-number', () => {
    expect(clampProbability(NaN)).toBe(0.1);
    expect(clampProbability(undefined)).toBe(0.1);
    expect(clampProbability('hello')).toBe(0.1);
    expect(clampProbability(null)).toBe(0.1);
  });

  test('should use custom fallback value', () => {
    expect(clampProbability(NaN, 0.25)).toBe(0.25);
    expect(clampProbability('abc', 0)).toBe(0);
  });
});

describe('percent', () => {
  test('should format probability as percentage string', () => {
    expect(percent(0.85)).toBe('85%');
    expect(percent(0)).toBe('0%');
    expect(percent(1)).toBe('100%');
    expect(percent(0.5)).toBe('50%');
  });

  test('should handle edge cases', () => {
    expect(percent(NaN)).toBe('0%');
    expect(percent(-0.3)).toBe('0%');
    expect(percent(1.2)).toBe('100%');
  });
});

describe('isDangerous', () => {
  test('should return true when is_toxic is true', () => {
    expect(isDangerous({ is_toxic: true, is_bully: false })).toBe(true);
  });

  test('should return true when is_bully is true', () => {
    expect(isDangerous({ is_toxic: false, is_bully: true })).toBe(true);
  });

  test('should return true when both are true', () => {
    expect(isDangerous({ is_toxic: true, is_bully: true })).toBe(true);
  });

  test('should return false when both are false', () => {
    expect(isDangerous({ is_toxic: false, is_bully: false })).toBe(false);
  });
});

describe('isCacheHit', () => {
  test('should detect cache by fast execution time', () => {
    expect(isCacheHit({ execution_time: 1.5, decision_source: 'Tier 1' })).toBe(true);
    expect(isCacheHit({ execution_time: 3.0, decision_source: 'Tier 1' })).toBe(true);
  });

  test('should detect cache by decision_source containing cache keywords', () => {
    expect(isCacheHit({ execution_time: 100, decision_source: 'Redis Cache' })).toBe(true);
    expect(isCacheHit({ execution_time: 100, decision_source: 'Semantic Match' })).toBe(true);
    expect(isCacheHit({ execution_time: 100, decision_source: 'Database Hit' })).toBe(true);
  });

  test('should return false for slow non-cache responses', () => {
    expect(isCacheHit({ execution_time: 50, decision_source: 'Tier 3 (Cloud LLM)' })).toBe(false);
  });
});

describe('buildNormalizationSteps', () => {
  test('should build 4 normalization steps', () => {
    const steps = buildNormalizationSteps('Halo Apa Kabar', 'halo apa kabar');
    expect(steps).toHaveLength(4);
    expect(steps[0].name).toBe('Input Mentah');
    expect(steps[0].value).toBe('"Halo Apa Kabar"');
    expect(steps[1].name).toBe('Pembersihan & Lowercase');
    expect(steps[2].name).toBe('Normalisasi Slang / Alay');
    expect(steps[2].value).toBe('"halo apa kabar"');
    expect(steps[3].name).toBe('Final Tokens');
  });

  test('should produce valid JSON tokens', () => {
    const steps = buildNormalizationSteps('test input', 'test input');
    const tokens = JSON.parse(steps[3].value);
    expect(tokens).toEqual(['test', 'input']);
  });
});

describe('getErrorMessage', () => {
  test('should extract message from Error object', () => {
    expect(getErrorMessage(new Error('test error'))).toBe('test error');
  });

  test('should return fallback for non-Error values', () => {
    expect(getErrorMessage('string error')).toBe('Terjadi kesalahan tidak diketahui.');
    expect(getErrorMessage(42)).toBe('Terjadi kesalahan tidak diketahui.');
    expect(getErrorMessage(null)).toBe('Terjadi kesalahan tidak diketahui.');
  });
});
