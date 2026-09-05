"""Unit and integration tests for Phase 13: Simulated Clinician Validation.

Verifies:
1. Reviewer persona definitions (5 personas with distinct clinical lenses)
2. Curated validation cases file format and validity (10 diverse synthetic cases)
3. Simulated evaluation execution (50 reviews across 7 criteria)
4. Score bounds (all 1–5 scale, valid mean calculations)
5. Artifact generation (eval/validation_results.json, eval/clinician_validation.md)
6. Mandatory disclaimers ("These are simulated reviewer personas, not real clinical validation")
7. Absence of false claims of clinical approval or regulatory clearance

No real patient data is used. Decision-support prototype — clinician sign-off required.
"""
from pathlib import Path
import json
import pytest

from eval.run_validation import (
    SIMULATED_PERSONAS,
    CaseReviewRecord,
    CriterionScores,
    ReviewerPersona,
    ValidationSummary,
    run_clinician_validation,
    save_validation_results,
    generate_clinician_validation_md,
)
from src.config import PROJECT_ROOT


@pytest.fixture(scope="module")
def validation_execution():
    """Run simulated clinician validation once for the test module."""
    summary, reviews = run_clinician_validation()
    return summary, reviews


def test_simulated_personas_count_and_profile():
    """Verify exactly 5 specialized reviewer personas are defined with unique focuses."""
    assert len(SIMULATED_PERSONAS) == 5
    
    persona_ids = [p.persona_id for p in SIMULATED_PERSONAS]
    assert len(set(persona_ids)) == 5
    assert "reviewer_primary_care" in persona_ids
    assert "reviewer_rural_health" in persona_ids
    assert "reviewer_teleconsult" in persona_ids
    assert "reviewer_patient_safety" in persona_ids
    assert "reviewer_language_access" in persona_ids

    for p in SIMULATED_PERSONAS:
        assert p.name
        assert p.clinical_role
        assert p.practice_setting
        assert p.primary_focus
        assert "simulated" in p.name.lower() or "simulated" in p.governance_notice.lower()


def test_validation_cases_cohort():
    """Verify curated validation cases file exists and has 10 valid synthetic cases."""
    v_path = PROJECT_ROOT / "eval" / "validation_cases.json"
    assert v_path.is_file(), f"Validation cases file missing at {v_path}"

    with open(v_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert data["metadata"]["total_cases"] == 10
    assert "cases" in data
    assert len(data["cases"]) == 10

    # Verify diversity across conditions, tiers, and languages
    conditions = set(c["condition"] for c in data["cases"])
    sites = set(c["site_id"] for c in data["cases"])
    urgencies = set(c["urgency"] for c in data["cases"])
    languages = set(c["patient_language"] for c in data["cases"])

    assert len(conditions) >= 4
    assert len(sites) >= 4
    assert "HIGH" in urgencies or "CRITICAL" in urgencies
    assert "ta" in languages and "en" in languages


def test_simulation_execution(validation_execution):
    """Verify that validation completes with 50 total reviews across 10 cases."""
    summary, reviews = validation_execution
    assert summary.total_cases_reviewed == 10
    assert summary.total_reviews_completed == 50
    assert len(reviews) == 50
    assert summary.overall_mean_score >= 1.0
    assert summary.overall_mean_score <= 5.0


def test_criterion_score_boundaries(validation_execution):
    """Verify all 7 criteria are scored within [1, 5] for every review."""
    _, reviews = validation_execution
    for r in reviews:
        scores = r.scores
        assert 1 <= scores.clarity <= 5
        assert 1 <= scores.feasibility <= 5
        assert 1 <= scores.reason_trail_usefulness <= 5
        assert 1 <= scores.follow_up_visibility <= 5
        assert 1 <= scores.escalation_safety <= 5
        assert 1 <= scores.language_handling <= 5
        assert 1 <= scores.usability <= 5
        assert 1.0 <= scores.average_score <= 5.0


def test_persona_averages_computed(validation_execution):
    """Verify per-persona averages are computed and conform to expectation."""
    summary, _ = validation_execution
    assert len(summary.persona_mean_scores) == 5
    for p_id, score in summary.persona_mean_scores.items():
        assert 1.0 <= score <= 5.0


def test_criterion_averages_computed(validation_execution):
    """Verify per-criterion averages exist for all seven criteria."""
    summary, _ = validation_execution
    expected_criteria = [
        "clarity",
        "feasibility",
        "reason_trail_usefulness",
        "follow_up_visibility",
        "escalation_safety",
        "language_handling",
        "usability",
    ]
    for c in expected_criteria:
        assert c in summary.criterion_mean_scores
        assert 1.0 <= summary.criterion_mean_scores[c] <= 5.0


def test_validation_results_json_artifact():
    """Verify eval/validation_results.json exists, parses, and contains required keys."""
    json_path = PROJECT_ROOT / "eval" / "validation_results.json"
    assert json_path.is_file(), f"JSON file missing at {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "summary" in data
    assert "reviews" in data
    assert data["summary"]["total_reviews_completed"] == 50
    assert "These are simulated reviewer personas, not real clinical validation." in data["summary"]["disclaimer"]


def test_clinician_validation_md_sections():
    """Verify eval/clinician_validation.md contains all required sections and tables."""
    report_path = PROJECT_ROOT / "eval" / "clinician_validation.md"
    assert report_path.is_file(), f"Report file missing at {report_path}"

    content = report_path.read_text(encoding="utf-8")

    required_sections = [
        "## 1. Methodology",
        "## 2. Reviewer Personas",
        "## 3. Cases Reviewed",
        "## 4. Evaluation Scores",
        "## 5. Persona Criticisms",
        "## 6. Suggested Improvements",
        "## 7. Limitations of Simulated Validation",
    ]
    for section in required_sections:
        assert section in content, f"Missing section: '{section}'"

    # Mandatory disclaimers
    assert "These are simulated reviewer personas, not real clinical validation." in content
    assert "claim clinical approval" in content.lower()
    assert "Decision-support prototype — clinician sign-off required." in content or "clinician sign-off is strictly required" in content.lower()
    assert "Synthetic data only — no real patient data" in content


def test_custom_output_directory(tmp_path: Path, validation_execution):
    """Verify artifact generators write to arbitrary destination paths."""
    summary, reviews = validation_execution
    custom_json = tmp_path / "custom_results.json"
    custom_md = tmp_path / "custom_report.md"

    save_validation_results(summary, reviews, custom_json)
    generate_clinician_validation_md(summary, reviews, custom_md)

    assert custom_json.is_file()
    assert custom_md.is_file()
