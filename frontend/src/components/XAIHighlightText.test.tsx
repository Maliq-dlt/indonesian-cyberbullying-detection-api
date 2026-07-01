import { describe, test, expect } from 'vitest';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { XAIHighlightText } from './XAIHighlightText';
import type { WordImportance } from './XAIHighlightText';

describe('XAIHighlightText Component', () => {
  test('should render simple text when no wordImportances are provided', () => {
    const html = renderToString(<XAIHighlightText text="halo apa kabar" />);
    expect(html).toContain('halo apa kabar');
  });

  test('should render text when wordImportances is empty array', () => {
    const html = renderToString(<XAIHighlightText text="halo apa kabar" wordImportances={[]} />);
    expect(html).toContain('halo apa kabar');
  });

  test('should highlight toxic word with red styling', () => {
    const importances: WordImportance[] = [
      { word: 'anjing', weight_toxic: 0.8, weight_bully: 0.1 }
    ];
    const html = renderToString(
      <XAIHighlightText text="kamu anjing" wordImportances={importances} />
    );
    expect(html).toContain('kamu');
    expect(html).toContain('anjing');
    expect(html).toContain('text-rose-800'); // Toxic style class
    expect(html).toContain('font-semibold');
  });

  test('should highlight bully word with purple styling', () => {
    const importances: WordImportance[] = [
      { word: 'dasar', weight_toxic: 0.1, weight_bully: 0.9 }
    ];
    const html = renderToString(
      <XAIHighlightText text="dasar tidak berguna" wordImportances={importances} />
    );
    expect(html).toContain('text-purple-800'); // Bully style class
  });

  test('should not highlight words with very low weights', () => {
    const importances: WordImportance[] = [
      { word: 'halo', weight_toxic: 0.005, weight_bully: 0.005 }
    ];
    const html = renderToString(
      <XAIHighlightText text="halo apa kabar" wordImportances={importances} />
    );
    // Should NOT have highlighting classes since weight is below 0.01 threshold
    expect(html).not.toContain('text-rose-800');
    expect(html).not.toContain('text-purple-800');
  });

  test('should render tooltip with weight information', () => {
    const importances: WordImportance[] = [
      { word: 'goblok', weight_toxic: 0.85, weight_bully: 0.35 }
    ];
    const html = renderToString(
      <XAIHighlightText text="kamu goblok" wordImportances={importances} />
    );
    expect(html).toContain('Bobot Kontribusi');
    expect(html).toContain('goblok');
    expect(html).toContain('Toxicity');
    expect(html).toContain('Bullying');
  });

  test('should handle multiple highlighted words', () => {
    const importances: WordImportance[] = [
      { word: 'anjing', weight_toxic: 0.8, weight_bully: 0.1 },
      { word: 'goblok', weight_toxic: 0.7, weight_bully: 0.5 }
    ];
    const html = renderToString(
      <XAIHighlightText text="anjing goblok" wordImportances={importances} />
    );
    // Both words should be highlighted
    const toxicMatches = html.match(/text-rose-800/g);
    expect(toxicMatches).not.toBeNull();
    expect(toxicMatches!.length).toBeGreaterThanOrEqual(2);
  });

  test('should be case-insensitive for word matching', () => {
    const importances: WordImportance[] = [
      { word: 'Anjing', weight_toxic: 0.8, weight_bully: 0.1 }
    ];
    const html = renderToString(
      <XAIHighlightText text="kamu ANJING" wordImportances={importances} />
    );
    // Should still match despite case difference
    expect(html).toContain('text-rose-800');
  });

  test('should render with leading-relaxed wrapper', () => {
    const importances: WordImportance[] = [
      { word: 'test', weight_toxic: 0.5, weight_bully: 0.1 }
    ];
    const html = renderToString(
      <XAIHighlightText text="test kata" wordImportances={importances} />
    );
    expect(html).toContain('leading-relaxed');
  });
});
