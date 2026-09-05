"""Unit and integration tests for Phase 12: Bias Evaluation and Disparity Analysis.

Verifies:
1. Demographic and geographic cohort segmentation (Rural/Urban, English/Tamil, Age Bands)
2. Metric computation correctness and absence of divide-by-zero errors
3. Empirical values and disparity deltas across cohorts
4. Elimination of the rural feasibility penalty by resource-aware adaptation
5. Report generation and mandatory structural sections
6. Clinical governance and synthetic data notices

No real patient data is used. Decision-support prototype — clinician sign-off required.
"""
from pathlib import Path
import json
import pytest

from eval.bias_eval import (
    BiasEvaluationSummary,
    CohortMetrics,
    DisparityDelta,
    calculate_cohort_metrics,
    calculate_disparity,
    evaluate_bias,
    generate_bias_report_md,
    generate_results_json,
    generate_results_md,
)
from src.comparer.runner import ComparisonRunner
from src.config import PROJECT_ROOT


@pytest.fixture(scope="module")
def bias_summary() -> BiasEvaluationSummary:
    """Run bias evaluation once for test module to verify all calculations."""
    return evaluate_bias()


def test_cohort_segmentation(bias_summary: BiasEvaluationSummary):
    """Verify all 40 cases are accounted for across all cohort partitions."""
    cohorts = bias_summary.cohorts
    assert bias_summary.total_cases_evaluated == 40
    
    # Geographic
    assert cohorts["rural"].total_cases == 20
    assert cohorts["urban"].total_cases == 20
    assert cohorts["rural"].total_cases + cohorts["urban"].total_cases == 40
    
    # Linguistic
    assert cohorts["english"].total_cases == 11
    assert cohorts["tamil"].total_cases == 29
    assert cohorts["english"].total_cases + cohorts["tamil"].total_cases == 40
    
    # Age Bands
    age_cases = (
        cohorts["age_18-35"].total_cases
        + cohorts["age_36-50"].total_cases
        + cohorts["age_51-65"].total_cases
        + cohorts["age_65+"].total_cases
    )
    assert age_cases == 40
    assert cohorts["age_18-35"].total_cases == 13
    assert cohorts["age_36-50"].total_cases == 7
    assert cohorts["age_51-65"].total_cases == 11
    assert cohorts["age_65+"].total_cases == 9
    
    # Overall
    assert cohorts["overall"].total_cases == 40


def test_rural_vs_urban_metrics(bias_summary: BiasEvaluationSummary):
    """Test empirical values and disparity gaps between Rural and Urban populations."""
    rural = bias_summary.cohorts["rural"]
    urban = bias_summary.cohorts["urban"]
    rvu = bias_summary.disparities["rural_vs_urban"]
    
    # Baseline feasibility deficit
    assert rural.baseline_feasible_pct == 55.0
    assert urban.baseline_feasible_pct == 75.0
    assert rvu.baseline_feasibility_gap_pct == -20.0
    
    # Resource-aware closed feasibility gap
    assert rural.resource_aware_feasible_pct == 100.0
    assert urban.resource_aware_feasible_pct == 100.0
    assert rvu.resource_aware_feasibility_gap_pct == 0.0
    
    # Immediate escalations (all cases found viable safe rungs)
    assert rural.immediate_escalation_pct == 0.0
    assert urban.immediate_escalation_pct == 0.0
    
    # Language escalation disparity due to unstaffed peripheral interpreters
    assert rural.language_escalation_pct == 55.0
    assert urban.language_escalation_pct == 5.0
    assert rvu.language_escalation_gap_pct == 50.0
    
    # High-priority follow-up coverage
    assert rural.baseline_high_priority_tracked_pct == 0.0
    assert urban.baseline_high_priority_tracked_pct == 0.0
    assert rural.resource_aware_high_priority_tracked_pct == 100.0
    assert urban.resource_aware_high_priority_tracked_pct == 100.0
    assert rural.high_priority_total == 4
    assert urban.high_priority_total == 12
    
    # Travel logistics disparity
    assert rural.avg_travel_distance_km == 23.70
    assert urban.avg_travel_distance_km == 11.22
    assert rvu.travel_distance_gap_km == 12.48
    
    assert rural.avg_travel_time_min == 94.60
    assert urban.avg_travel_time_min == 35.15
    assert rvu.travel_time_gap_min == 59.45


def test_english_vs_tamil_metrics(bias_summary: BiasEvaluationSummary):
    """Test empirical values and disparity gaps between English and Tamil speaking cohorts."""
    en = bias_summary.cohorts["english"]
    ta = bias_summary.cohorts["tamil"]
    tve = bias_summary.disparities["tamil_vs_english"]
    
    # Feasibility
    assert en.baseline_feasible_pct == pytest.approx(72.73, rel=1e-2)
    assert ta.baseline_feasible_pct == pytest.approx(62.07, rel=1e-2)
    assert en.resource_aware_feasible_pct == 100.0
    assert ta.resource_aware_feasible_pct == 100.0
    assert tve.resource_aware_feasibility_gap_pct == 0.0
    
    # Language escalation
    assert en.language_escalation_pct == 0.0
    assert ta.language_escalation_pct == pytest.approx(41.38, rel=1e-2)
    assert tve.language_escalation_gap_pct == pytest.approx(41.38, rel=1e-2)
    
    # High-priority follow-up
    assert en.resource_aware_high_priority_tracked_pct == 100.0
    assert ta.resource_aware_high_priority_tracked_pct == 100.0
    assert en.high_priority_total == 5
    assert ta.high_priority_total == 11


def test_age_band_metrics(bias_summary: BiasEvaluationSummary):
    """Verify age band distributions and metrics."""
    c = bias_summary.cohorts
    
    # Check that all age bands achieve 100% resource-aware feasibility
    for band in ["age_18-35", "age_36-50", "age_51-65", "age_65+"]:
        assert c[band].resource_aware_feasible_pct == 100.0
        assert c[band].resource_aware_high_priority_tracked_pct == 100.0
        assert c[band].baseline_high_priority_tracked_pct == 0.0
        assert c[band].avg_travel_distance_km > 0.0
        assert c[band].avg_travel_time_min > 0.0


def test_empty_cohort_handling():
    """Verify calculate_cohort_metrics handles an empty case list without ZeroDivisionError."""
    empty_metrics = calculate_cohort_metrics(
        cohort_name="EmptyCohort",
        cohort_type="test",
        cases=[],
        case_results={},
        sites={},
    )
    assert empty_metrics.total_cases == 0
    assert empty_metrics.baseline_feasible_pct == 0.0
    assert empty_metrics.resource_aware_feasible_pct == 0.0
    assert empty_metrics.language_escalation_pct == 0.0
    assert empty_metrics.avg_travel_distance_km == 0.0
    assert empty_metrics.avg_travel_time_min == 0.0


def test_artifact_generation(tmp_path: Path, bias_summary: BiasEvaluationSummary):
    """Test generating results.json, results.md, and bias_report.md into temporary directory."""
    json_path = tmp_path / "results.json"
    results_md_path = tmp_path / "results.md"
    bias_report_path = tmp_path / "bias_report.md"
    
    generate_results_json(bias_summary, json_path)
    generate_results_md(bias_summary, results_md_path)
    generate_bias_report_md(bias_summary, bias_report_path)
    
    assert json_path.is_file()
    assert results_md_path.is_file()
    assert bias_report_path.is_file()
    
    # Verify JSON content
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["total_cases_evaluated"] == 40
        assert "rural" in data["cohorts"]
        assert "urban" in data["cohorts"]
        assert "rural_vs_urban" in data["disparities"]


def test_bias_report_sections_present():
    """Verify that eval/bias_report.md includes all 9 required sections."""
    report_path = PROJECT_ROOT / "eval" / "bias_report.md"
    assert report_path.is_file()
    content = report_path.read_text(encoding="utf-8")
    
    required_sections = [
        "## 1. Purpose",
        "## 2. Synthetic Dataset",
        "## 3. Group Definitions",
        "## 4. Metrics",
        "## 5. Results",
        "## 6. Observed Differences",
        "## 7. Possible Causes",
        "## 8. Limitations of Synthetic Evaluation",
        "## 9. Mitigation Ideas",
    ]
    for section in required_sections:
        assert section in content, f"Missing section: '{section}' in bias_report.md"
        
    # Verify governance disclaimers
    assert "Synthetic data only — no real patient data." in content
    assert "Decision-support prototype — clinician sign-off required." in content


def test_results_md_sections_present():
    """Verify that eval/results.md includes all required sections."""
    results_path = PROJECT_ROOT / "eval" / "results.md"
    assert results_path.is_file()
    content = results_path.read_text(encoding="utf-8")
    
    required_sections = [
        "## 1. Baseline",
        "## 2. Target",
        "## 3. Measured",
        "## 4. Difference",
        "## 5. Error Analysis",
    ]
    for section in required_sections:
        assert section in content, f"Missing section: '{section}' in results.md"
        
    # Verify governance disclaimers
    assert "Synthetic data only — no real patient data." in content
    assert "Decision-support prototype — clinician sign-off required." in content
