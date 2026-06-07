# Frontend Refactor Guide — Detector Module

## Problem

The detector frontend component was too large and handled too many responsibilities at once.

A component like that becomes difficult to maintain because:

- API request logic is coupled with UI rendering.
- State transitions are scattered inside JSX-heavy code.
- Multi-model comparison logic is mixed with single-model prediction logic.
- XAI visualization is embedded in the same component.
- TypeScript types are harder to reuse.
- Future UI changes become risky.

## Refactor strategy

This refactor uses a conservative decomposition strategy.

The goal is not to redesign the product. The goal is to preserve behavior while making the code easier to reason about.

## New module structure

```text
frontend/src/components/Detector/
├── Detector.tsx              # High-level layout composition
├── InputPanel.tsx            # Text input, model selector, fuzzy toggle, submit button
├── ResultCard.tsx            # Single-model result UI
├── ComparisonResultCard.tsx  # Audit Multi-Model result table
├── XaiDrawer.tsx             # XAI side drawer and contribution chart
├── EmptyState.tsx            # Empty state before analysis
├── ProbabilityBar.tsx        # Reusable probability meter
├── useDetector.ts            # State and action orchestration
├── api.ts                    # API calls, normalization, fallback simulation
├── constants.ts              # Model options and shared constants
├── types.ts                  # Shared TypeScript interfaces
├── utils.ts                  # Formatting and helper functions
└── index.ts                  # Public exports
```

## Design decisions

### Keep old import compatibility

The file below still exists:

```text
frontend/src/components/Detector.tsx
```

It only re-exports the new module:

```ts
export { default } from './Detector/Detector';
```

That means code like this should continue working:

```ts
import Detector from './components/Detector';
```

### Keep API behavior similar

The refactor preserves the endpoint mapping:

| UI Mode | Endpoint |
|---|---|
| Hybrid AI | `/predict/hybrid` |
| Lexicon | `/predict/lexicon` |
| Machine Learning | `/predict/ml` |
| Transformer | `/predict/transformers` |
| Ensemble | `/predict/ensemble` |
| Audit Multi-Model | all major endpoints |

### Keep offline fallback

The offline fallback simulation remains available when a single-model request fails. This is useful for local demo mode, but should not be presented as a real model result.

## Manual QA checklist

After applying the patch, test these flows:

- [ ] Empty input should not submit.
- [ ] More than 500 characters should not submit.
- [ ] Hybrid mode should call `/predict/hybrid`.
- [ ] Lexicon mode should call `/predict/lexicon`.
- [ ] Fuzzy toggle should only appear for Lexicon and Audit Multi-Model.
- [ ] Audit Multi-Model should call all comparison endpoints.
- [ ] Offline backend should trigger sandbox fallback in single-model mode.
- [ ] Result card should show toxic/bully probability.
- [ ] XAI drawer should open when word importance data exists.
- [ ] XAI drawer should close on backdrop or close button.
- [ ] `npm run build` should pass.

## Next recommended frontend improvements

This stage only refactors the detector module. Later improvements should include:

1. Introduce a shared API client.
2. Move API URL/key handling into a config provider.
3. Add frontend tests with React Testing Library.
4. Add loading skeletons instead of only spinner text.
5. Add clearer user warning that offline fallback is not real prediction.
6. Add typed backend response schemas shared with the API docs.
