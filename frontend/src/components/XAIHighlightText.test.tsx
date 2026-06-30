import { describe, test, expect } from 'vitest';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { XAIHighlightText } from './XAIHighlightText';

describe('XAIHighlightText Component', () => {
  test('should render simple text when no wordImportances are provided', () => {
    const html = renderToString(<XAIHighlightText text="halo apa kabar" />);
    expect(html).toContain('halo apa kabar');
  });

  test('should highlight toxic word', () => {
    const importances = [
      { word: 'anjing', weight_toxic: 0.8, weight_bully: 0.1 }
    ];
    const html = renderToString(
      <XAIHighlightText text="kamu anjing" wordImportances={importances} />
    );
    expect(html).toContain('kamu');
    expect(html).toContain('anjing');
    expect(html).toContain('text-rose-800'); // Toxic style class
  });
});
