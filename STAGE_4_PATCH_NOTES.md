# Stage 4 Patch Notes — Frontend Detector Refactor

## Scope

This stage refactors the original `frontend/src/components/Detector.tsx` component into smaller, focused files.

The old component mixed these concerns in one place:

- UI rendering
- API calls
- request payload construction
- fallback simulation
- comparison mode logic
- XAI drawer rendering
- probability formatting
- model option configuration

The new structure separates those concerns without intentionally changing the user-facing behavior.

## Files added or replaced

```text
frontend/src/components/Detector.tsx
frontend/src/components/Detector/
├── Detector.tsx
├── index.ts
├── api.ts
├── constants.ts
├── types.ts
├── utils.ts
├── useDetector.ts
├── InputPanel.tsx
├── EmptyState.tsx
├── ProbabilityBar.tsx
├── ResultCard.tsx
├── ComparisonResultCard.tsx
└── XaiDrawer.tsx
```

## Why `frontend/src/components/Detector.tsx` still exists

The original app likely imports the component like this:

```ts
import Detector from './components/Detector';
```

To avoid breaking that import, `Detector.tsx` is kept as a small wrapper:

```ts
export { default } from './Detector/Detector';
```

This makes the refactor a safer drop-in replacement.

## What changed

### Before

One large component handled everything.

### After

- `Detector.tsx`: page-level composition only.
- `useDetector.ts`: state and action orchestration.
- `api.ts`: API calls, response normalization, offline fallback.
- `InputPanel.tsx`: textarea, model selector, fuzzy toggle, analyze button.
- `ResultCard.tsx`: single prediction result UI.
- `ComparisonResultCard.tsx`: multi-model audit table.
- `XaiDrawer.tsx`: XAI side drawer and local contribution chart.
- `types.ts`: shared TypeScript interfaces.
- `utils.ts`: formatting and small pure helpers.
- `constants.ts`: model options and character limit.

## Compatibility notes

This patch expects the existing component `XAIHighlightText` to remain here:

```text
frontend/src/components/XAIHighlightText.tsx
```

If your actual file path is different, adjust these imports:

```ts
import { XAIHighlightText } from '../XAIHighlightText';
import type { WordImportance } from '../XAIHighlightText';
```

## Recommended validation

From the `frontend` folder:

```bash
npm install
npm run lint
npm run build
npm run dev
```

Then test manually:

1. Hybrid AI mode
2. Lexicon mode with fuzzy on/off
3. Machine Learning mode
4. Transformer mode
5. Ensemble mode
6. Audit Multi-Model mode
7. Backend offline fallback
8. XAI drawer open/close
9. 500-character limit

## Commit message

```bash
git checkout -b frontend/stage-4-detector-refactor

git add frontend/src/components/Detector.tsx \
        frontend/src/components/Detector \
        docs/FRONTEND_REFACTOR_GUIDE.md \
        STAGE_4_PATCH_NOTES.md \
        README_STAGE_4.md

git commit -m "frontend: refactor detector component into smaller modules"
```
