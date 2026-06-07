# Error Analysis Guide

A cyberbullying model should not be judged by F1-score alone. Moderation has asymmetric risk:

- False positive: harmless speech is incorrectly flagged.
- False negative: harmful speech is missed.

Both matter.

## Minimum manual review table

Create a CSV or spreadsheet with these columns:

```text
id,text,true_toxic,true_bully,pred_toxic,pred_bully,prob_toxic,prob_bully,error_type,notes
```

## Error categories

Use these categories:

| Category | Meaning |
|---|---|
| direct_insult | Direct insult toward a person/group |
| profanity_no_target | Harsh word without clear target |
| sarcasm | Meaning depends on irony/context |
| quote_or_report | User quotes abuse or reports being abused |
| slang_or_alay | Creative spelling, slang, abbreviation |
| identity_attack | Attack on protected/social identity |
| threat | Threat/intimidation |
| ambiguous | Human reviewers may disagree |
| non_bullying_negative | Negative sentiment but not bullying |

## False positive checklist

Inspect flagged safe texts and ask:

1. Is the harsh word targeted at someone?
2. Is the text quoting someone else?
3. Is it educational/news/reporting context?
4. Is it self-directed expression?
5. Is it banter between close friends?

## False negative checklist

Inspect missed harmful texts and ask:

1. Is the insult written with obfuscation?
2. Is the message sarcastic?
3. Does it use local slang or Indonesian-English mix?
4. Is bullying implied rather than explicit?
5. Is identity-based hate present without common abusive words?

## Recommended report structure

Add this section into `MODEL_EVALUATION.md` after you run threshold evaluation:

```md
## Error Analysis

### False Positives

| Text | Expected | Predicted | Likely cause | Fix |
|---|---|---|---|---|
| ... | safe | toxic | quoted abusive word | add quote/reporting examples |

### False Negatives

| Text | Expected | Predicted | Likely cause | Fix |
|---|---|---|---|---|
| ... | bully | safe | slang/obfuscation | add slang examples |
```

## Stronger evaluation rule

Evaluate at least 100 manually reviewed samples after every retraining. If possible, use 300–500 samples.
