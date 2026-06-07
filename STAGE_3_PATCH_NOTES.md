# Stage 3 Patch Notes — ML Confidence, Thresholds, and Error Analysis

## Goal

Make the prediction pipeline more honest and safer by separating:

- model probability,
- final classification decision,
- routing confidence,
- symbolic LLM decision.

## Files added

```text
cyberbullying_api/classifier/confidence.py
cyberbullying_api/classifier/evaluate_thresholds.py
tests/test_confidence.py
docs/ML_CONFIDENCE_GUIDE.md
docs/ERROR_ANALYSIS_GUIDE.md
snippets/PREDICTOR_PATCH.md
.env.example.additions
```

## Main fixes

### 1. LLM no longer returns fake 1.0/0.0 probabilities

LLM output is treated as a classification decision with conservative pseudo-probability.

### 2. Lexicon no longer forces toxic score to 0.90

Lexicon matches now add bounded evidence depending on risk level.

### 3. Ensemble weights are normalized

This prevents accidental over-weighting when the sum of weights is not exactly 1.0.

### 4. Confidence margin is configurable

`CONFIDENCE_MARGIN` can be adjusted without editing code.

### 5. Threshold evaluation script added

`evaluate_thresholds.py` generates:

```text
reports/threshold_eval/threshold_sweep.csv
reports/threshold_eval/threshold_report.json
reports/threshold_eval/recommended_thresholds.json
```

## Apply order

1. Copy the new files into the repo.
2. Append `.env.example.additions` into your existing `.env.example`.
3. Follow `snippets/PREDICTOR_PATCH.md` to patch `predictor.py`.
4. Run tests.
5. Run threshold evaluation on a labeled validation CSV.

## Commands

```bash
git checkout -b ml/stage-3-confidence-thresholds

# after copying files
git add cyberbullying_api/classifier/confidence.py \
        cyberbullying_api/classifier/evaluate_thresholds.py \
        tests/test_confidence.py \
        docs/ML_CONFIDENCE_GUIDE.md \
        docs/ERROR_ANALYSIS_GUIDE.md \
        snippets/PREDICTOR_PATCH.md \
        .env.example.additions \
        STAGE_3_PATCH_NOTES.md

git commit -m "ml: improve confidence handling and threshold evaluation"
```

Run tests:

```bash
pytest tests/test_confidence.py -q
```

Run threshold sweep:

```bash
python -m cyberbullying_api.classifier.evaluate_thresholds --csv dataset/eval.csv
```

## Important limitation

This stage does not magically make the model accurate. It makes the system more honest and measurable. Real improvement still depends on labeled validation data and error analysis.
