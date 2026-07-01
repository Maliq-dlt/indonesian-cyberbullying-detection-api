import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { analyzeSingle, analyzeComparison, createOfflineFallback } from './api';

// Mock global fetch
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('analyzeSingle', () => {
  test('should call correct endpoint for hybrid model', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        is_toxic: false,
        is_bully: false,
        probability_toxic: 0.1,
        probability_bully: 0.05,
        category: 'Aman',
        decision_source: 'Tier 1',
        reason: 'Aman',
      }),
    });

    const result = await analyzeSingle({
      apiUrl: 'http://localhost:8000',
      apiKey: 'test-key',
      text: 'halo apa kabar',
      selectedModel: 'hybrid',
      useFuzzy: false,
    });

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/predict/hybrid',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'x-api-key': 'test-key' }),
      }),
    );
    expect(result.text).toBe('halo apa kabar');
    expect(result.is_toxic).toBe(false);
    expect(result.category).toBe('Aman');
  });

  test('should call correct endpoint for ml model', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        is_toxic: true,
        is_bully: false,
        probability_toxic: 0.85,
        probability_bully: 0.2,
        category: 'Toxic',
        decision_source: 'Tier 1 (ML)',
        reason: 'Kata kasar terdeteksi',
      }),
    });

    await analyzeSingle({
      apiUrl: 'http://localhost:8000',
      apiKey: '',
      text: 'kamu goblok',
      selectedModel: 'ml',
      useFuzzy: false,
    });

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/predict/ml',
      expect.any(Object),
    );
  });

  test('should throw on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });

    await expect(
      analyzeSingle({
        apiUrl: 'http://localhost:8000',
        apiKey: 'key',
        text: 'test',
        selectedModel: 'hybrid',
        useFuzzy: false,
      }),
    ).rejects.toThrow('Backend mengembalikan status 500');
  });

  test('should send use_fuzzy for lexicon model', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        is_cyberbullying: false,
        score: 0,
        risk_label: 'aman',
        matches: [],
      }),
    });

    await analyzeSingle({
      apiUrl: 'http://localhost:8000',
      apiKey: 'key',
      text: 'halo',
      selectedModel: 'lexicon',
      useFuzzy: true,
    });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.use_fuzzy).toBe(true);
  });
});

describe('analyzeComparison', () => {
  test('should return results for all models', async () => {
    // Mock all 5 comparison endpoints
    for (let i = 0; i < 5; i++) {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          is_toxic: false,
          is_bully: false,
          probability_toxic: 0.1,
          probability_bully: 0.05,
          category: 'Aman',
          decision_source: 'Test',
          reason: 'OK',
        }),
      });
    }

    const results = await analyzeComparison({
      apiUrl: 'http://localhost:8000',
      apiKey: 'key',
      text: 'halo',
      useFuzzy: false,
    });

    expect(results).toHaveLength(5);
    expect(results[0].name).toBe('Hybrid AI');
    expect(results[0].status).toBe('ONLINE');
  });

  test('should mark offline models correctly', async () => {
    // All endpoints fail
    for (let i = 0; i < 5; i++) {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));
    }

    const results = await analyzeComparison({
      apiUrl: 'http://localhost:8000',
      apiKey: 'key',
      text: 'test',
      useFuzzy: false,
    });

    expect(results).toHaveLength(5);
    results.forEach((r) => {
      expect(r.status).toBe('OFFLINE');
    });
  });
});

describe('createOfflineFallback', () => {
  test('should detect toxic words', () => {
    const result = createOfflineFallback('kamu anjing banget');
    expect(result.is_toxic).toBe(true);
    expect(result.is_bully).toBe(false);
    expect(result.category).toContain('Toxic');
    expect(result.decision_source).toBe('Sandbox Offline Fallback');
  });

  test('should detect bully words', () => {
    const result = createOfflineFallback('dasar jelek');
    expect(result.is_bully).toBe(true);
    expect(result.category).toContain('Bully');
  });

  test('should detect both toxic and bully', () => {
    const result = createOfflineFallback('anjing dasar jelek');
    expect(result.is_toxic).toBe(true);
    expect(result.is_bully).toBe(true);
    expect(result.category).toContain('Toxic & Bully');
  });

  test('should return safe result for clean text', () => {
    const result = createOfflineFallback('halo apa kabar');
    expect(result.is_toxic).toBe(false);
    expect(result.is_bully).toBe(false);
    expect(result.category).toContain('Aman');
  });

  test('should include word importances', () => {
    const result = createOfflineFallback('kamu anjing');
    expect(result.word_importances).toBeDefined();
    expect(result.word_importances!.length).toBeGreaterThan(0);

    const anjingWord = result.word_importances!.find((w) => w.word === 'anjing');
    expect(anjingWord).toBeDefined();
    expect(anjingWord!.weight_toxic).toBeGreaterThan(0.5);
  });

  test('should include normalization steps', () => {
    const result = createOfflineFallback('Test Input');
    expect(result.normalization_steps).toBeDefined();
    expect(result.normalization_steps!.length).toBe(4);
  });
});
