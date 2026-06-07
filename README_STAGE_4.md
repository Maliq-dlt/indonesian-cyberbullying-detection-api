# Stage 4 — Frontend Refactor Package

This package refactors the detector frontend module into smaller, maintainable React + TypeScript files.

## Main goal

Reduce the maintenance risk of a very large `Detector.tsx` component.

The previous file mixed API logic, state management, fallback simulation, result rendering, comparison rendering, and XAI drawer rendering in one component. That makes future changes risky because a small edit in one area can accidentally break another part.

## How to apply

Copy these files into your repository root:

```text
frontend/src/components/Detector.tsx
frontend/src/components/Detector/
docs/FRONTEND_REFACTOR_GUIDE.md
STAGE_4_PATCH_NOTES.md
README_STAGE_4.md
```

The replacement is designed so the old import should still work:

```ts
import Detector from './components/Detector';
```

## Validation commands

Run these commands inside the `frontend` folder:

```bash
npm install
npm run lint
npm run build
npm run dev
```

If your existing project already has dependencies installed, `npm run build` is the most important validation.

## Important warning

This refactor is designed based on the current public repository structure. If you already changed `Detector.tsx` locally after pushing to GitHub, compare before replacing.

Recommended workflow:

```bash
git checkout -b frontend/stage-4-detector-refactor
cp -r <this-package>/* <your-repo>/
npm run build
```
