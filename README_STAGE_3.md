# BullyGuard ID — Stage 3 Package

This package improves ML confidence handling without replacing the whole predictor file.

## Install

Copy these folders/files into the repository root:

```text
cyberbullying_api/
docs/
tests/
snippets/
.env.example.additions
STAGE_3_PATCH_NOTES.md
README_STAGE_3.md
```

Then manually apply:

```text
snippets/PREDICTOR_PATCH.md
```

## Why manual patch?

`predictor.py` is central to the app and contains multiple runtime paths: normal hybrid prediction, streaming prediction, cache retrieval, LLM fallback, lexicon fallback, and embedding memory. Replacing the whole file without running the full project is unnecessarily risky.

## Recommended next step

After applying this stage, create a small validation CSV:

```csv
text,toxic,bully
"contoh kalimat aman",0,0
"contoh kalimat toxic",1,0
"contoh kalimat bullying",1,1
```

Then run:

```bash
python -m cyberbullying_api.classifier.evaluate_thresholds --csv dataset/eval.csv
```
