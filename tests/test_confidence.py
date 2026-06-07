from cyberbullying_api.classifier.confidence import (
    apply_lexicon_evidence,
    combine_probabilities,
    is_confident_pair,
    llm_decision_to_probability,
    normalize_weights,
)


class DummyLexicon:
    def __init__(self, is_cyberbullying=True, risk_label="tinggi"):
        self.is_cyberbullying = is_cyberbullying
        self.risk_label = risk_label


def test_normalize_weights():
    assert normalize_weights(2, 2) == (0.5, 0.5)
    assert normalize_weights(0, 0) == (0.5, 0.5)
    assert normalize_weights(3, 1) == (0.75, 0.25)


def test_combine_probabilities_normalizes_weights():
    value = combine_probabilities(0.8, 0.2, 3, 1, min_second_signal=0.0)
    assert round(value, 3) == 0.65


def test_is_confident_pair_requires_both_outputs_to_be_outside_margin():
    confident = is_confident_pair(0.90, 0.10, 0.50, 0.50, margin=0.25)
    borderline = is_confident_pair(0.90, 0.49, 0.50, 0.50, margin=0.25)
    assert confident.is_confident is True
    assert borderline.is_confident is False


def test_llm_probability_is_not_extreme():
    assert llm_decision_to_probability(True, 0.5) < 1.0
    assert llm_decision_to_probability(False, 0.5) > 0.0


def test_lexicon_evidence_boosts_but_caps():
    boosted = apply_lexicon_evidence(0.78, DummyLexicon(True, "tinggi"))
    assert boosted <= 0.85
    assert boosted > 0.78


def test_lexicon_no_match_does_not_change_probability():
    value = apply_lexicon_evidence(0.42, DummyLexicon(False, "tinggi"))
    assert value == 0.42
