# Predictor Patch Guide — Stage 3

This guide intentionally avoids replacing your entire `predictor.py`. Apply these small edits instead.

## 1. Add import near the existing imports

```python
from classifier.confidence import (
    apply_lexicon_evidence,
    combine_probabilities,
    decision_summary,
    get_threshold,
    is_confident_pair,
    llm_decision_to_probability,
)
```

## 2. Replace hard-coded threshold reads

Where you currently use:

```python
t_t = THRESHOLDS.get("threshold_toxic", 0.5)
t_b = THRESHOLDS.get("threshold_bully", 0.5)
```

Use:

```python
t_t = get_threshold(THRESHOLDS, "threshold_toxic", 0.5)
t_b = get_threshold(THRESHOLDS, "threshold_bully", 0.5)
```

## 3. Replace confidence margin checks

Where you currently use:

```python
if (abs(ml_toxic - t_t) >= 0.25) and (abs(ml_bully - t_b) >= 0.25):
```

Use:

```python
ml_confidence = is_confident_pair(ml_toxic, ml_bully, t_t, t_b)
if ml_confidence.is_confident:
```

For ensemble:

```python
ens_confidence = is_confident_pair(ens_toxic, ens_bully, t_t, t_b)
if ens_confidence.is_confident:
```

You may also append to the API `reason` string:

```python
reason="Klasifikasi konfiden tinggi berdasarkan model statistik. " + ml_confidence.reason
```

## 4. Replace ensemble probability combination

Where you currently use:

```python
final_toxic = w_ml_toxic * ml_toxic + w_tr_toxic * tr_toxic if tr_toxic > 0.0 else ml_toxic
final_bully = w_ml_bully * ml_bully + w_tr_bully * tr_bully if tr_bully > 0.0 else ml_bully
```

Use:

```python
final_toxic = combine_probabilities(ml_toxic, tr_toxic, w_ml_toxic, w_tr_toxic)
final_bully = combine_probabilities(ml_bully, tr_bully, w_ml_bully, w_tr_bully)
```

Do the same replacement for `ens_toxic` and `ens_bully` in hybrid mode.

## 5. Replace lexicon force-to-0.90 logic

Where you currently use:

```python
if lex_res.is_cyberbullying:
    final_toxic = max(final_toxic, 0.90)
```

Use:

```python
final_toxic = apply_lexicon_evidence(final_toxic, lex_res)
```

## 6. Replace LLM probability 1.0/0.0

Where you currently use:

```python
probability_toxic=1.0 if is_toxic else 0.0,
probability_bully=1.0 if is_bully else 0.0,
```

Use:

```python
probability_toxic=llm_decision_to_probability(is_toxic, t_t),
probability_bully=llm_decision_to_probability(is_bully, t_b),
```

If this is inside the sarcasm pre-filter before `t_t` and `t_b` exist, add before building the response:

```python
t_t = get_threshold(THRESHOLDS, "threshold_toxic", 0.5)
t_b = get_threshold(THRESHOLDS, "threshold_bully", 0.5)
```

## 7. Optional: improve reason string

Use this for logs or response reason text:

```python
reason=(
    "Klasifikasi berbasis gabungan ML dan Transformer. "
    + decision_summary("ensemble", ens_toxic, ens_bully, t_t, t_b, ens_confidence)
)
```

## Why this patch matters

- LLM outputs are decisions, not calibrated probabilities.
- Lexicon matches are evidence, not automatic proof of bullying.
- Ensemble weights should be normalized before combination.
- Routing confidence should be configurable, not hard-coded to 0.25.
