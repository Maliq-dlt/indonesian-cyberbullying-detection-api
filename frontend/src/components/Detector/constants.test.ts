import { describe, test, expect } from 'vitest';
import { MAX_TEXT_LENGTH, MODEL_OPTIONS, COMPARISON_ENDPOINTS } from './constants';

describe('constants', () => {
  test('MAX_TEXT_LENGTH should be a positive number', () => {
    expect(MAX_TEXT_LENGTH).toBeGreaterThan(0);
    expect(MAX_TEXT_LENGTH).toBe(500);
  });

  test('MODEL_OPTIONS should have at least 5 models', () => {
    expect(MODEL_OPTIONS.length).toBeGreaterThanOrEqual(5);
  });

  test('MODEL_OPTIONS should include hybrid model', () => {
    const hybrid = MODEL_OPTIONS.find((m) => m.id === 'hybrid');
    expect(hybrid).toBeDefined();
    expect(hybrid!.label).toBe('Hybrid AI');
    expect(hybrid!.badge).toBe('Rekomendasi');
  });

  test('MODEL_OPTIONS should include comparison model', () => {
    const comparison = MODEL_OPTIONS.find((m) => m.id === 'comparison');
    expect(comparison).toBeDefined();
    expect(comparison!.badge).toBe('New');
  });

  test('all MODEL_OPTIONS should have unique ids', () => {
    const ids = MODEL_OPTIONS.map((m) => m.id);
    const uniqueIds = new Set(ids);
    expect(uniqueIds.size).toBe(ids.length);
  });

  test('COMPARISON_ENDPOINTS should have 5 entries', () => {
    expect(COMPARISON_ENDPOINTS).toHaveLength(5);
  });

  test('COMPARISON_ENDPOINTS should have unique names', () => {
    const names = COMPARISON_ENDPOINTS.map((e) => e.name);
    const uniqueNames = new Set(names);
    expect(uniqueNames.size).toBe(names.length);
  });

  test('all COMPARISON_ENDPOINTS paths should start with /predict/', () => {
    COMPARISON_ENDPOINTS.forEach((endpoint) => {
      expect(endpoint.path).toMatch(/^\/predict\//);
    });
  });
});
