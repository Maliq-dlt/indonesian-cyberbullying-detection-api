---
name: cyberbullying-detector
description: AI hybrid system for cyberbullying and hate speech detection in Indonesian text using Lexicon, Machine Learning (TF-IDF + Logistic Regression/Naive Bayes), and Deep Learning (XLM-RoBERTa ONNX) with Active Learning.
---

# Cyberbullying Detector Skill

This skill allows agents to analyze, moderates, and classify Indonesian text for cyberbullying, toxic language, and hate speech. It utilizes a hybrid approach combining Lexicon matching, TF-IDF + Logistic Regression, and quantized XLM-RoBERTa models, backed by an active learning pipeline.

## When to Use

Use this skill when you need to:
1. Moderate or classify Indonesian comments/text for cyberbullying or toxicity.
2. Clean, normalize, or preprocess Indonesian internet slang, abbreviations, or obfuscated leetspeak (e.g., `m4ti lu`, `gblk`).
3. Bulk process comments scraped from social media (TikTok or X/Twitter).
4. Run active learning tasks, including re-labelling/validating datasets, starting model training, and verifying training metrics.

## API Endpoints Reference

The FastAPI server runs by default on `http://localhost:8000`.

### 1. Classification & Prediction
* **`POST /predict/lexicon`**: Matches normalized text against the cyberbullying lexicon dictionary.
  - Request: `{"text": "string", "use_fuzzy": boolean}`
  - Returns lexicon match data, category, and severity score.
* **`POST /predict/ml`**: Uses the TF-IDF + Logistic Regression classifier.
  - Request: `{"text": "string"}`
  - Returns classification probability and verdict.
* **`POST /predict/transformers`**: Runs the XLM-RoBERTa ONNX model.
  - Request: `{"text": "string"}`
  - Returns deep learning prediction.
* **`POST /predict/hybrid`**: Standard pipeline combining all classifiers with an LLM fallback for reasoning.
  - Request: `{"text": "string"}`
  - Returns final consolidated judgment with categories: `Aman`, `Toxic (Non-Bullying)`, `Bullying (Non-Toxic)`, or `Bullying & Toxic`.
* **`POST /predict/batch`**: Bulk prediction on a list of texts (maximum 500 characters per item).
  - Request: `{"texts": ["string"]}`

### 2. Social Media Scraping (Moderation Tool)
* **`POST /api/scrape/tiktok`**: Scrape comments from a TikTok video URL.
  - Request: `{"url": "string", "max_comments": integer}`
* **`POST /api/scrape/x`**: Scrape replies from an X/Twitter post URL.
  - Request: `{"url": "string", "max_tweets": integer}`

### 3. Active Learning & Admin
* **`GET /api/data/categorized`**: Retrieve categorized classification memory from the database.
  - Parameters: `limit`, `confidence_min`, `confidence_max`, `decision_source`, `search`
* **`POST /api/data/reallocate`**: Manually correct a classification verdict (Active Learning label injection).
  - Request: `{"text": "string", "new_is_toxic": 0|1, "new_is_bully": 0|1}`
* **`POST /api/train/start`**: Trigger model retraining pipeline (uses Celery if available, else local background process).
* **`GET /api/train/status`**: Check retraining progress, metrics, and logs.

---

## Instructions for Agents

### 1. Text Normalization Pipeline
When performing manual analysis, always normalize Indonesian slang using the following sequential steps:
1. **Leetspeak Replacement**:
   Replace digit-to-letter lookalikes:
   - `0` $\rightarrow$ `o`
   - `1` / `!` / `|` $\rightarrow$ `i`
   - `3` $\rightarrow$ `e`
   - `4` / `@` $\rightarrow$ `a`
   - `5` / `$` $\rightarrow$ `s`
   - `7` / `+` $\rightarrow$ `t`
   - `8` $\rightarrow$ `b`
   - `9` / `6` $\rightarrow$ `g`
2. **Repeated Character Reduction**:
   Reduce letters repeated more than twice (e.g. `goblloookkk` $\rightarrow$ `goblok`).
3. **Slang Dictionary Expansion**:
   Convert abbreviations to formal equivalent Indonesian words:
   - `gblk` $\rightarrow$ `goblok`
   - `anjg` $\rightarrow$ `anjing`
   - `bgsd` $\rightarrow$ `bangsat`
   - `lu` $\rightarrow$ `kamu`
   - `yg` $\rightarrow$ `yang`

### 2. Hybrid Decision Matrix
To understand how the hybrid classifier works under the hood:
- **High-Severity Lexicon Hit**: Instantly flags content if severe keywords are matched.
- **Logistic Regression Model**: Evaluates semantic structures with statistical confidence.
- **XLM-RoBERTa ONNX**: Provides contextual and sentiment-based evaluation (reducing false positives on ambiguous sarcasm).
- **RAG + LLM Reasoning**: If confidence drops below `0.55` (toxic) or `0.50` (bully), LLM leverages vector similarity search over historical samples to resolve the verdict with detailed Chain-of-Thought explanation.

### 3. Training & Validation Workflow
To retrain the classification models:
1. Post corrections using `/api/data/reallocate` to build a validated feedback loop.
2. Run `POST /api/train/start` to begin the background training run.
3. Monitor training progress via `GET /api/train/status` until status shows `completed`.
4. Ensure the new F1-Score does not drop by more than 8%, or the system will trigger an auto-rollback to keep models stable.
