# ML Confidence Guide

## Problem fixed in Stage 3

The previous predictor logic mixed three different concepts:

1. **Model probability** — numeric output from Logistic Regression or Transformer.
2. **Decision** — whether probability crosses the toxic/bully threshold.
3. **Routing confidence** — whether the system is confident enough to stop at Tier 1/Tier 2 or escalate to LLM.

These must be separated. Otherwise, the API may look precise while actually producing misleading confidence.

## Key changes

### 1. LLM decision is no longer treated as true probability

Old behavior:

```python
probability_toxic = 1.0 if is_toxic else 0.0
```

New behavior:

```python
probability_toxic = llm_decision_to_probability(is_toxic, threshold_toxic)
```

Reason: an LLM can make a classification decision, but that does not mean it produced a calibrated probability.

### 2. Lexicon evidence no longer forces score to 0.90

Old behavior:

```python
final_toxic = max(final_toxic, 0.90)
```

New behavior:

```python
final_toxic = apply_lexicon_evidence(final_toxic, lex_res)
```

Reason: abusive words can appear in quotes, jokes, educational explanations, self-reporting, or non-targeted context. Lexicon evidence should boost risk, not dominate the model blindly.

### 3. Ensemble weights are normalized

Old behavior may accidentally overweight probabilities if weight totals are not exactly 1.0.

New behavior normalizes weights before calculating weighted probability.

### 4. Confidence margin is configurable

Set in `.env`:

```env
CONFIDENCE_MARGIN=0.25
```

A larger margin escalates more cases to stronger tiers. A smaller margin makes the API faster but riskier.

## Recommended `.env` additions

```env
CONFIDENCE_MARGIN=0.25
MIN_TRANSFORMER_SIGNAL=0.001
LLM_POSITIVE_PROBABILITY=0.80
LLM_NEGATIVE_PROBABILITY=0.20
LEXICON_BOOST_LOW=0.05
LEXICON_BOOST_MEDIUM=0.12
LEXICON_BOOST_HIGH=0.20
LEXICON_PROBABILITY_CAP=0.85
```

## How to tune thresholds

Run:

```bash
python -m cyberbullying_api.classifier.evaluate_thresholds --csv dataset/eval.csv
```

Then copy the generated values from:

```text
reports/threshold_eval/recommended_thresholds.json
```

into:

```text
cyberbullying_api/models/thresholds.json
```

Example:

```json
{
  "threshold_toxic": 0.45,
  "threshold_bully": 0.55
}
```

## What not to claim yet

Do not claim:

- "model confidence is calibrated"
- "production-grade moderation accuracy"
- "enterprise-level detection"
- "bias-free cyberbullying detection"

Unless you have calibration plots, benchmark datasets, and error analysis.
