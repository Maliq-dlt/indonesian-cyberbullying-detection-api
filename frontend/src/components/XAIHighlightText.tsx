import React from 'react';

export interface WordImportance {
  word: string;
  weight_toxic: number;
  weight_bully: number;
}

interface XAIHighlightTextProps {
  text: string;
  wordImportances?: WordImportance[];
}

export function XAIHighlightText({ text, wordImportances }: XAIHighlightTextProps) {
  if (!wordImportances || wordImportances.length === 0) {
    return <span>{text}</span>;
  }

  // Create a map for fast lookup
  const impMap = new Map<string, WordImportance>();
  wordImportances.forEach(imp => {
    impMap.set(imp.word.toLowerCase(), imp);
  });

  // Split text by word boundaries or punctuation, keeping separators
  const tokens = text.split(/(\s+|[.,/#!$%^&*;:{}=\-_`~()??"'“”[\]{}<>\\|]+)/g);

  return (
    <span className="leading-relaxed">
      {tokens.map((token, idx) => {
        const cleanToken = token.trim().toLowerCase();
        const imp = impMap.get(cleanToken);

        if (imp && (imp.weight_toxic > 0.01 || imp.weight_bully > 0.01)) {
          const isToxicDominant = imp.weight_toxic > imp.weight_bully;
          const maxWeight = Math.max(imp.weight_toxic, imp.weight_bully);
          
          // Calculate opacity: map weight (typically 0.1 to 1.5+) to opacity range (0.15 to 0.5)
          const opacity = Math.min(0.15 + (maxWeight * 0.15), 0.5);
          
          // Base color classes
          const bgStyle = isToxicDominant
            ? { backgroundColor: `rgba(239, 68, 68, ${opacity})` } // Red (toxic)
            : { backgroundColor: `rgba(168, 85, 247, ${opacity})` }; // Purple (bully)

          const textClass = isToxicDominant
            ? 'text-rose-800 font-semibold'
            : 'text-purple-800 font-semibold';

          return (
            <span
              key={idx}
              className={`relative inline-block px-1 rounded cursor-help group/xai ${textClass}`}
              style={bgStyle}
            >
              {token}
              {/* Tooltip */}
              <span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-48 -translate-x-1/2 scale-0 rounded-lg bg-gray-900 p-2 text-xxs leading-normal text-white shadow-xl transition-all duration-150 group-hover/xai:scale-100 font-sans font-normal border border-gray-800">
                <span className="block font-bold mb-1 border-b border-gray-800 pb-0.5 text-center text-[10px] text-gray-200">
                  Bobot Kontribusi: "{imp.word}"
                </span>
                <span className="flex justify-between items-center mb-0.5 text-gray-300">
                  <span>Toxicity:</span>
                  <span className={`font-bold ${imp.weight_toxic > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {imp.weight_toxic > 0 ? '+' : ''}{imp.weight_toxic.toFixed(4)}
                  </span>
                </span>
                <span className="flex justify-between items-center text-gray-300">
                  <span>Bullying:</span>
                  <span className={`font-bold ${imp.weight_bully > 0 ? 'text-purple-400' : 'text-emerald-400'}`}>
                    {imp.weight_bully > 0 ? '+' : ''}{imp.weight_bully.toFixed(4)}
                  </span>
                </span>
                {/* Arrow */}
                <span className="absolute top-full left-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1 rotate-45 bg-gray-900" />
              </span>
            </span>
          );
        }

        return <span key={idx}>{token}</span>;
      })}
    </span>
  );
}
