"""Tests for the Textbook Baseline engine.

Verifies that the baseline functions as an unconstrained control comparator,
returning gold-standard textbook recommendations while strictly ignoring local site constraints.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
import pytest
from baseline.baseline_engine import TextbookBaselineEngine


@pytest.fixture
def baseline_engine() -> TextbookBaselineEngine:
    """Fixture providing a fresh TextbookBaselineEngine instance."""
    return TextbookBaselineEngine()


def test_baseline_recommendation_standard_case(baseline_engine: TextbookBaselineEngine) -> None:
    """Verify standard baseline recommendation output structure."""
    case = {
        "case_id": "SYNTH-CASE-101",
        "condition": "condition_alpha",
        "patient_age": 45,
        "site_id": "SITE-RURAL-01",
    }

    result = baseline_engine.generate_recommendation(case)

    assert result["method"] == "baseline"
    assert result["case_id"] == "SYNTH-CASE-101"
    assert result["status"] == "success"
    assert result["protocol_id"] == "PROTO-001"
    assert result["condition"] == "condition_alpha"
    assert "parenteral broad-spectrum" in result["recommendation"].lower()
    assert result["resource_checked"] is False
    assert result["follow_up_checked"] is False
    assert "clinician sign-off required" in result["governance_notice"].lower()
    assert "synthetic data only" in result["synthetic_data_notice"].lower()


def test_baseline_deliberately_ignores_severe_resource_constraints(
    baseline_engine: TextbookBaselineEngine
) -> None:
    """CRITICAL TEST: Verify that the baseline completely ignores severe site deficits.

    Even when the case metadata explicitly specifies total absence of imaging, cold-chain,
    medication stock, and transport, the baseline engine MUST NOT adapt or downgrade
    the recommendation. It must return the textbook recommendation and report
    resource_checked=False.
    """
    austere_case = {
        "case_id": "SYNTH-CASE-AUSTERE-999",
        "condition": "condition_alpha",
        # Explicit severe resource deficits at patient site:
        "site_resources": {
            "same_day_imaging": False,
            "cold_chain": False,
            "medication_stock": False,
            "transport": False,
            "specialist_48h": False,
            "stable_connectivity": False,
        },
        "patient_travel_hours": 8,
        "language": "ta",
    }

    result = baseline_engine.generate_recommendation(austere_case)

    # Must succeed with standard textbook recommendation despite zero resources
    assert result["status"] == "success"
    assert result["protocol_id"] == "PROTO-001"
    assert "parenteral broad-spectrum" in result["recommendation"].lower()
    # Invariant: resource_checked MUST remain False
    assert result["resource_checked"] is False
    assert result["follow_up_checked"] is False


def test_baseline_across_all_synthetic_conditions(baseline_engine: TextbookBaselineEngine) -> None:
    """Verify that the baseline correctly processes all five synthetic conditions."""
    conditions = [
        ("condition_alpha", "PROTO-001", "HIGH"),
        ("condition_beta", "PROTO-002", "MEDIUM"),
        ("condition_gamma", "PROTO-003", "CRITICAL"),
        ("condition_delta", "PROTO-004", "LOW"),
        ("condition_epsilon", "PROTO-005", "MEDIUM"),
    ]

    for cond, expected_proto, expected_urgency in conditions:
        case = {"case_id": f"TEST-{cond}", "condition": cond}
        result = baseline_engine.generate_recommendation(case)
        assert result["status"] == "success"
        assert result["protocol_id"] == expected_proto
        assert result["urgency"] == expected_urgency
        assert len(result["recommendation"]) > 0
        assert result["resource_checked"] is False
        assert result["follow_up_checked"] is False


def test_baseline_unknown_condition(baseline_engine: TextbookBaselineEngine) -> None:
    """Verify graceful error reporting when case specifies an unknown condition."""
    case = {"case_id": "SYNTH-UNKNOWN", "condition": "condition_unknown_xyz"}
    result = baseline_engine.generate_recommendation(case)

    assert result["status"] == "error"
    assert result["protocol_id"] is None
    assert "unknown condition" in result["recommendation"].lower()
    assert result["resource_checked"] is False


def test_baseline_missing_condition(baseline_engine: TextbookBaselineEngine) -> None:
    """Verify graceful error reporting when case is missing condition field."""
    case = {"case_id": "SYNTH-EMPTY"}
    result = baseline_engine.generate_recommendation(case)

    assert result["status"] == "error"
    assert result["protocol_id"] is None
    assert "missing condition" in result["recommendation"].lower()
    assert result["resource_checked"] is False
