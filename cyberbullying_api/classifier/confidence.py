"""
Confidence utilities for BullyGuard ID.

Purpose:
- Keep model probability, routing confidence, and LLM decisions separate.
- Avoid hard-coded 1.0/0.0 probabilities from LLM decisions.
- Avoid forcing lexicon matches to an extreme probability such as 0.90.
- Normalize ensemble weights before combining model outputs.

This module is intentionally dependency-light so it is safe to import from
predictor.py and easy to unit test.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping


DEFAULT_THRESHOLD = 0.5


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def clamp01(value: float) -> float:
    """Clamp a numeric value into the [0, 1] interval."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


@dataclass(frozen=True)
class ConfidenceDecision:
    """Human-readable explanation for confidence/routing decisions."""

    is_confident: bool
    toxic_distance: float
    bully_distance: float
    margin: float
    reason: str


def get_threshold(thresholds: Mapping[str, Any], key: str, default: float = DEFAULT_THRESHOLD) -> float:
    """Read threshold safely from a dict-like object."""
    try:
        return clamp01(float(thresholds.get(key, default)))
    except Exception:
        return default


def get_confidence_margin() -> float:
    """
    Minimum absolute distance from threshold needed before a local model is
    treated as confident enough to stop routing.

    Default 0.25 matches the previous project behavior, but is now configurable.
    """
    return clamp01(_env_float("CONFIDENCE_MARGIN", 0.25))


def is_confident_pair(
    toxic_prob: float,
    bully_prob: float,
    toxic_threshold: float = DEFAULT_THRESHOLD,
    bully_threshold: float = DEFAULT_THRESHOLD,
    margin: float | None = None,
) -> ConfidenceDecision:
    """
    Return whether both outputs are sufficiently far from their thresholds.

    Why both? In a multi-output moderation task, one confident label and one
    borderline label should still be escalated to a stronger tier.
    """
    if margin is None:
        margin = get_confidence_margin()

    toxic_distance = abs(clamp01(toxic_prob) - clamp01(toxic_threshold))
    bully_distance = abs(clamp01(bully_prob) - clamp01(bully_threshold))
    confident = toxic_distance >= margin and bully_distance >= margin

    if confident:
        reason = (
            f"Both labels are at least {margin:.2f} away from their thresholds "
            f"(toxic distance={toxic_distance:.3f}, bully distance={bully_distance:.3f})."
        )
    else:
        reason = (
            f"At least one label is within the uncertainty band of {margin:.2f} "
            f"(toxic distance={toxic_distance:.3f}, bully distance={bully_distance:.3f})."
        )

    return ConfidenceDecision(
        is_confident=confident,
        toxic_distance=round(toxic_distance, 6),
        bully_distance=round(bully_distance, 6),
        margin=round(margin, 6),
        reason=reason,
    )


def normalize_weights(first_weight: float, second_weight: float) -> tuple[float, float]:
    """Normalize two non-negative weights. Falls back to 0.5/0.5 if invalid."""
    a = max(float(first_weight or 0.0), 0.0)
    b = max(float(second_weight or 0.0), 0.0)
    total = a + b
    if total <= 0.0:
        return 0.5, 0.5
    return a / total, b / total


def combine_probabilities(
    first_prob: float,
    second_prob: float | None,
    first_weight: float = 0.5,
    second_weight: float = 0.5,
    min_second_signal: float | None = None,
) -> float:
    """
    Weighted ensemble probability with safer behavior when Tier 2 is unavailable.

    The previous code treated transformer probability 0.0 as unavailable. That
    is practical, but it can also hide a genuine strong negative prediction.
    To preserve backward compatibility, use MIN_TRANSFORMER_SIGNAL with a tiny
    default. Set it to 0.0 if you want to treat 0.0 as a valid signal.
    """
    if min_second_signal is None:
        min_second_signal = _env_float("MIN_TRANSFORMER_SIGNAL", 0.001)

    p1 = clamp01(float(first_prob or 0.0))

    if second_prob is None:
        return p1

    p2 = clamp01(float(second_prob))
    if p2 <= min_second_signal:
        return p1

    w1, w2 = normalize_weights(first_weight, second_weight)
    return clamp01((w1 * p1) + (w2 * p2))


def llm_decision_to_probability(is_positive: bool, threshold: float = DEFAULT_THRESHOLD) -> float:
    """
    Convert a symbolic LLM decision into a non-extreme pseudo-probability.

    Important: LLM output should not be interpreted as calibrated probability.
    Returning 1.0/0.0 makes downstream confidence misleading. Defaults are
    intentionally conservative and configurable through environment variables.
    """
    threshold = clamp01(threshold)
    if is_positive:
        return clamp01(_env_float("LLM_POSITIVE_PROBABILITY", max(0.70, threshold + 0.20)))
    return clamp01(_env_float("LLM_NEGATIVE_PROBABILITY", min(0.30, threshold - 0.20)))


def lexicon_boost_for_risk(risk_label: str | None) -> float:
    """Map lexicon severity/risk label to a conservative probability boost."""
    label = (risk_label or "").lower().strip()
    if label == "tinggi":
        return _env_float("LEXICON_BOOST_HIGH", 0.20)
    if label == "sedang":
        return _env_float("LEXICON_BOOST_MEDIUM", 0.12)
    if label == "rendah":
        return _env_float("LEXICON_BOOST_LOW", 0.05)
    return 0.0


def apply_lexicon_evidence(base_probability: float, lexicon_response: Any) -> float:
    """
    Add lexicon evidence without forcing the score to an extreme value.

    Previous behavior used max(probability, 0.90). That creates false-positive
    risk when a harsh word appears in a quotation, educational explanation,
    or casual non-targeted context.
    """
    base = clamp01(base_probability)

    try:
        is_match = bool(getattr(lexicon_response, "is_cyberbullying", False))
        risk_label = getattr(lexicon_response, "risk_label", None)
    except Exception:
        return base

    if not is_match:
        return base

    cap = clamp01(_env_float("LEXICON_PROBABILITY_CAP", 0.85))
    boosted = base + lexicon_boost_for_risk(risk_label)
    return min(clamp01(boosted), cap)


def decision_summary(
    source: str,
    toxic_prob: float,
    bully_prob: float,
    toxic_threshold: float,
    bully_threshold: float,
    confidence: ConfidenceDecision | None = None,
) -> str:
    """Compact text explanation suitable for logs or API reason strings."""
    pieces = [
        f"source={source}",
        f"toxic_prob={clamp01(toxic_prob):.3f}/threshold={clamp01(toxic_threshold):.3f}",
        f"bully_prob={clamp01(bully_prob):.3f}/threshold={clamp01(bully_threshold):.3f}",
    ]
    if confidence is not None:
        pieces.append(f"confidence_margin={confidence.margin:.3f}")
        pieces.append("confident=yes" if confidence.is_confident else "confident=no")
    return "; ".join(pieces)
