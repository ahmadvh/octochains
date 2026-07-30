import json
from unittest.mock import MagicMock

import pytest

from octochains.aggregators.synthesizer import Synthesizer
from octochains.aggregators.weighted_synthesizer import WeightedSynthesizer
from octochains.schema import WeightedSynthesisResult


# ==========================================
# 1. Mock Data
# ==========================================
MOCK_SYNTH_JSON = json.dumps({
    "narrative": "The CTO's scalability concerns anchor the assessment; revenue and compliance are supporting.",
    "key_takeaways": ["Address the sharding bottleneck first", "Revenue integration is secondary", "GDPR posture is acceptable"],
    "confidence": 0.82,
    "citations": {
        "CTO": "The monolith will not shard cleanly.",
        "CRO": "Sales cycle is ~90 days.",
        "GDPR Auditor": "Transfers are covered by SCCs."
    }
})


@pytest.fixture
def sample_reports():
    return {
        "CTO": "The monolith will not shard cleanly; expect a 6-month refactor.",
        "CRO": "Sales cycle is ~90 days with strong mid-market synergy.",
        "GDPR Auditor": "Cross-border transfers are covered by SCCs.",
    }


@pytest.fixture
def mock_llm():
    m = MagicMock()
    m.return_value = MOCK_SYNTH_JSON
    return m


# ==========================================
# 2. Construction & weight resolution
# ==========================================
def test_returns_weighted_synthesis_result(mock_llm, sample_reports):
    agg = WeightedSynthesizer(llm_callable=mock_llm, weights={"CTO": 0.7, "CRO": 0.2, "GDPR Auditor": 0.1})
    result = agg.execute(sample_reports)
    assert isinstance(result, WeightedSynthesisResult)


def test_weights_are_normalized_to_sum_one(mock_llm, sample_reports):
    agg = WeightedSynthesizer(llm_callable=mock_llm, weights={"CTO": 7, "CRO": 2, "GDPR Auditor": 1})
    result = agg.execute(sample_reports)
    assert result.weights_applied["CTO"] == pytest.approx(0.7, abs=1e-3)
    assert sum(result.weights_applied.values()) == pytest.approx(1.0, abs=1e-3)


def test_missing_weight_defaults_to_equal_footing_not_dropped(mock_llm, sample_reports):
    # Only CTO is weighted; CRO and GDPR Auditor must fall back to default_weight (1.0), not vanish.
    agg = WeightedSynthesizer(llm_callable=mock_llm, weights={"CTO": 1.0})
    result = agg.execute(sample_reports)

    assert set(result.weights_applied.keys()) == set(sample_reports.keys())
    # With all effective weights equal to 1.0, each normalizes to ~1/3.
    for role in sample_reports:
        assert result.weights_applied[role] == pytest.approx(1 / 3, abs=1e-3)


def test_all_zero_weights_fall_back_to_equal_split(mock_llm, sample_reports):
    agg = WeightedSynthesizer(llm_callable=mock_llm, weights={"CTO": 0, "CRO": 0, "GDPR Auditor": 0})
    result = agg.execute(sample_reports)
    for role in sample_reports:
        assert result.weights_applied[role] == pytest.approx(1 / 3, abs=1e-3)


# ==========================================
# 3. Unbalanced weighting shifts emphasis
# ==========================================
def test_unbalanced_weighting_selects_dominant_and_annotates_prompt(mock_llm, sample_reports):
    agg = WeightedSynthesizer(llm_callable=mock_llm, weights={"CTO": 0.9, "CRO": 0.05, "GDPR Auditor": 0.05})
    result = agg.execute(sample_reports)

    # Dominant perspective is deterministic — the highest-weighted responding role.
    assert result.dominant_perspective == "CTO"
    assert result.weights_applied["CTO"] == pytest.approx(0.9, abs=1e-3)

    # The weighting must be encoded into the prompt so it actually shapes the blend.
    prompt = mock_llm.call_args[0][0]
    assert 'The dominant perspective is "CTO"' in prompt
    assert "CTO (emphasis weight: 90.0%)" in prompt
    assert "CRO (emphasis weight: 5.0%)" in prompt


# ==========================================
# 4. Degenerate case: equal weights == plain Synthesizer behavior
# ==========================================
def test_equal_weights_equivalent_to_plain_synthesizer(sample_reports):
    # Same mock output feeds both aggregators.
    weighted = WeightedSynthesizer(
        llm_callable=lambda p: MOCK_SYNTH_JSON,
        weights={"CTO": 1.0, "CRO": 1.0, "GDPR Auditor": 1.0},
    )
    plain = Synthesizer(llm_callable=lambda p: MOCK_SYNTH_JSON)

    w_result = weighted.execute(sample_reports)
    p_result = plain.execute(sample_reports)

    # The synthesized content is structurally identical to the unweighted Synthesizer.
    assert w_result.narrative == p_result.narrative
    assert w_result.key_takeaways == p_result.key_takeaways
    assert w_result.confidence == p_result.confidence
    assert w_result.citations == p_result.citations

    # And every perspective carries identical weight.
    weights = list(w_result.weights_applied.values())
    assert all(w == pytest.approx(weights[0], abs=1e-3) for w in weights)


# ==========================================
# 5. Edge cases: empty input & malformed output
# ==========================================
def test_empty_reports_aborts_cleanly_without_calling_llm(mock_llm):
    agg = WeightedSynthesizer(llm_callable=mock_llm, weights={"CTO": 0.7})
    result = agg.execute({})

    mock_llm.assert_not_called()
    assert result.confidence == 0.0
    assert "Synthesis Aborted" in result.narrative
    assert result.weights_applied == {}
    assert result.dominant_perspective == ""


def test_malformed_llm_output_handled_gracefully(sample_reports):
    def bad_llm(prompt):
        return "I'm afraid I can't do that right now."

    agg = WeightedSynthesizer(llm_callable=bad_llm, weights={"CTO": 0.9, "CRO": 0.05, "GDPR Auditor": 0.05})
    result = agg.execute(sample_reports)

    # Safe fallback object — never raises.
    assert isinstance(result, WeightedSynthesisResult)
    assert result.confidence == 0.0
    assert "System Error" in result.narrative
    # Audit fields are still populated from the deterministic weight resolution.
    assert result.dominant_perspective == "CTO"
    assert result.weights_applied["CTO"] == pytest.approx(0.9, abs=1e-3)


def test_llm_exception_handled_gracefully(sample_reports):
    def exploding_llm(prompt):
        raise RuntimeError("Simulated API timeout")

    agg = WeightedSynthesizer(llm_callable=exploding_llm, weights={"CTO": 0.9})
    result = agg.execute(sample_reports)

    assert isinstance(result, WeightedSynthesisResult)
    assert result.confidence == 0.0
    assert "Simulated API timeout" in result.narrative
