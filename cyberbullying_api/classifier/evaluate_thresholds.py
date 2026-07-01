"""
Threshold evaluation script for the classical ML tier.

Usage examples:
    python -m cyberbullying_api.classifier.evaluate_thresholds --csv dataset/eval.csv
    python cyberbullying_api/classifier/evaluate_thresholds.py --csv dataset/eval.csv --text-col text --toxic-col toxic --bully-col bully

Expected CSV columns by default:
    text,toxic,bully

Accepted aliases:
    text: text, Text, String, comment, komentar
    toxic: toxic, Toxic, is_toxic
    bully: bully, Bully, is_bully

This script intentionally evaluates Tier 1 first. Transformer and hybrid routing
should be evaluated separately because their latency, costs, and failure modes
are different.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score

try:
    from normalizer import normalize_text
except Exception:
    # When executed as a module from repository root.
    from cyberbullying_api.normalizer import normalize_text  # type: ignore


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "model_lr.joblib"
DEFAULT_VECTORIZER_PATH = BASE_DIR / "models" / "vectorizer.joblib"


def _first_existing_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    columns = set(df.columns)
    for name in candidates:
        if name in columns:
            return name
    return None


def _resolve_columns(args: argparse.Namespace, df: pd.DataFrame) -> tuple[str, str, str]:
    text_col = args.text_col or _first_existing_column(df, ["text", "Text", "String", "comment", "komentar"])
    toxic_col = args.toxic_col or _first_existing_column(df, ["toxic", "Toxic", "is_toxic"])
    bully_col = args.bully_col or _first_existing_column(df, ["bully", "Bully", "is_bully"])

    missing = []
    if not text_col:
        missing.append("text column")
    if not toxic_col:
        missing.append("toxic label column")
    if not bully_col:
        missing.append("bully label column")
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing) + ". "
            "Pass --text-col, --toxic-col, and --bully-col explicitly."
        )
    return text_col, toxic_col, bully_col


def _to_binary(series: pd.Series) -> np.ndarray:
    positive_values = {
        1,
        "1",
        "true",
        "True",
        "TRUE",
        "yes",
        "Ya",
        "ya",
        "toxic",
        "bully",
        "Bullying",
        "negative",
        "negatif",
    }
    return series.fillna(0).map(lambda x: 1 if x in positive_values else 0).astype(int).to_numpy()


def _normalize_texts(texts: Iterable[str]) -> list[str]:
    normalized = []
    for text in texts:
        try:
            normalized.append(normalize_text(str(text))["spaced"])
        except Exception:
            normalized.append(str(text).lower().strip())
    return normalized


def _metric_row(label_name: str, threshold: float, y_true: np.ndarray, probs: np.ndarray) -> dict[str, float | str]:
    y_pred = (probs >= threshold).astype(int)
    return {
        "label": label_name,
        "threshold": round(float(threshold), 3),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 6),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 6),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 6),
    }


def evaluate(args: argparse.Namespace) -> dict:
    df = pd.read_csv(args.csv)
    text_col, toxic_col, bully_col = _resolve_columns(args, df)

    df = df.dropna(subset=[text_col]).copy()
    texts = _normalize_texts(df[text_col].astype(str).tolist())
    y_toxic = _to_binary(df[toxic_col])
    y_bully = _to_binary(df[bully_col])

    model_path = Path(args.model_path or DEFAULT_MODEL_PATH)
    vectorizer_path = Path(args.vectorizer_path or DEFAULT_VECTORIZER_PATH)

    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)
    x = vectorizer.transform(texts)
    pred_probs = model.predict_proba(x)

    toxic_probs = np.array([row[1] for row in pred_probs[0]])
    bully_probs = np.array([row[1] for row in pred_probs[1]])

    thresholds = np.arange(args.min_threshold, args.max_threshold + 0.0001, args.step)
    rows = []
    for threshold in thresholds:
        rows.append(_metric_row("toxic", threshold, y_toxic, toxic_probs))
        rows.append(_metric_row("bully", threshold, y_bully, bully_probs))

    metrics_df = pd.DataFrame(rows)
    best_toxic = metrics_df[metrics_df["label"] == "toxic"].sort_values("f1", ascending=False).iloc[0].to_dict()
    best_bully = metrics_df[metrics_df["label"] == "bully"].sort_values("f1", ascending=False).iloc[0].to_dict()

    final_toxic_threshold = float(best_toxic["threshold"])
    final_bully_threshold = float(best_bully["threshold"])
    toxic_pred = (toxic_probs >= final_toxic_threshold).astype(int)
    bully_pred = (bully_probs >= final_bully_threshold).astype(int)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_csv = output_dir / "threshold_sweep.csv"
    report_json = output_dir / "threshold_report.json"
    thresholds_json = output_dir / "recommended_thresholds.json"

    metrics_df.to_csv(metrics_csv, index=False)

    report = {
        "input_csv": str(args.csv),
        "rows_evaluated": int(len(df)),
        "columns": {"text": text_col, "toxic": toxic_col, "bully": bully_col},
        "best_thresholds": {
            "threshold_toxic": final_toxic_threshold,
            "threshold_bully": final_bully_threshold,
        },
        "best_metric_rows": {"toxic": best_toxic, "bully": best_bully},
        "classification_reports": {
            "toxic": classification_report(y_toxic, toxic_pred, zero_division=0, output_dict=True),
            "bully": classification_report(y_bully, bully_pred, zero_division=0, output_dict=True),
        },
        "confusion_matrices": {
            "toxic": confusion_matrix(y_toxic, toxic_pred).tolist(),
            "bully": confusion_matrix(y_bully, bully_pred).tolist(),
        },
        "artifacts": {
            "threshold_sweep_csv": str(metrics_csv),
            "threshold_report_json": str(report_json),
            "recommended_thresholds_json": str(thresholds_json),
        },
    }

    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    thresholds_json.write_text(
        json.dumps(report["best_thresholds"], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate ML thresholds for toxic and bully labels.")
    parser.add_argument("--csv", required=True, help="Evaluation CSV path.")
    parser.add_argument("--text-col", default=None, help="Text column name.")
    parser.add_argument("--toxic-col", default=None, help="Toxic label column name.")
    parser.add_argument("--bully-col", default=None, help="Bully label column name.")
    parser.add_argument("--model-path", default=str(DEFAULT_MODEL_PATH), help="Path to model_lr.joblib.")
    parser.add_argument("--vectorizer-path", default=str(DEFAULT_VECTORIZER_PATH), help="Path to vectorizer.joblib.")
    parser.add_argument("--output-dir", default="reports/threshold_eval", help="Output directory.")
    parser.add_argument("--min-threshold", type=float, default=0.10)
    parser.add_argument("--max-threshold", type=float, default=0.90)
    parser.add_argument("--step", type=float, default=0.05)
    return parser.parse_args()


if __name__ == "__main__":
    result = evaluate(parse_args())
    print(json.dumps(result["best_thresholds"], indent=2, ensure_ascii=False))
