import { ComparisonResultCard } from './ComparisonResultCard';
import { EmptyState } from './EmptyState';
import { InputPanel } from './InputPanel';
import { ResultCard } from './ResultCard';
import type { DetectorProps } from './types';
import { useDetector } from './useDetector';
import { XaiDrawer } from './XaiDrawer';

export default function Detector({ apiUrl, apiKey }: DetectorProps) {
  const detector = useDetector(apiUrl, apiKey);
  const hasXaiDetail = Boolean(detector.result?.word_importances?.length);

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-lg font-black text-gray-900 dark:text-gray-100">Detektor Teks Tunggal</h2>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Uji dan analisis kalimat untuk mendeteksi cyberbullying, toksisitas, dan profanity secara detail.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <InputPanel
          text={detector.text}
          selectedModel={detector.selectedModel}
          useFuzzy={detector.useFuzzy}
          loading={detector.loading}
          onTextChange={detector.setText}
          onModelChange={detector.setSelectedModel}
          onUseFuzzyChange={detector.setUseFuzzy}
          onAnalyze={detector.analyze}
        />

        <div className="lg:col-span-5 h-full">
          {!detector.result && !detector.comparisonResults ? (
            <EmptyState />
          ) : detector.selectedModel === 'comparison' && detector.comparisonResults ? (
            <ComparisonResultCard
              results={detector.comparisonResults}
              hasXaiDetail={hasXaiDetail}
              onOpenXai={() => detector.setIsDrawerOpen(true)}
            />
          ) : detector.result ? (
            <ResultCard result={detector.result} onOpenXai={() => detector.setIsDrawerOpen(true)} />
          ) : null}
        </div>
      </div>

      <XaiDrawer
        isOpen={detector.isDrawerOpen}
        result={detector.result}
        onClose={() => detector.setIsDrawerOpen(false)}
      />
    </div>
  );
}
