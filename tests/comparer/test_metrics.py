"""Tests for Phase 7 evaluation metric calculations and aggregations.

Verifies:
- Metric 1: % recommendations feasible given site resources.
- Metric 2: % high-priority follow-ups with named owner, due date, escalation path.
- Metric 3: Number of recommendations changed because of constraints.
- Metric 4: Number of language mismatches detected.
- Metric 5: Number of immediate escalations.
- Exactly 40 cases evaluated.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from pathlib import Path
import pytest

from src.comparer.metrics import calculate_comparison_metrics
from src.comparer.runner import ComparisonRunner


def test_metric_1_feasibility_percentages(tmp_path: Path):
    """Verify Metric 1: Site resource feasibility between baseline and resource-aware."""
    runner = ComparisonRunner(db_path=tmp_path / "test_metrics_1.db")
    run_result = runner.run_all()
    metrics = run_result.metrics

    assert metrics.total_cases_evaluated == 40
    assert metrics.metric_1_baseline_feasible_pct == 65.0
    assert metrics.metric_1_baseline_feasible_count == 26
    assert metrics.metric_1_resource_aware_feasible_pct == 100.0
    assert metrics.metric_1_resource_aware_feasible_count == 40


def test_metric_2_high_priority_accountability(tmp_path: Path):
    """Verify Metric 2: 0% baseline vs 100% resource-aware for high-priority follow-up tracking."""
    runner = ComparisonRunner(db_path=tmp_path / "test_metrics_2.db")
    run_result = runner.run_all()
    metrics = run_result.metrics

    assert metrics.metric_2_total_high_priority_cases == 16
    assert metrics.metric_2_baseline_high_priority_tracked_pct == 0.0
    assert metrics.metric_2_resource_aware_high_priority_tracked_pct == 100.0


def test_metric_3_recommendations_changed_due_to_constraints(tmp_path: Path):
    """Verify Metric 3: 14 of 40 cases (35.0%) changed recommendation due to site constraints."""
    runner = ComparisonRunner(db_path=tmp_path / "test_metrics_3.db")
    run_result = runner.run_all()
    metrics = run_result.metrics

    assert metrics.metric_3_recommendations_changed_count == 14
    assert metrics.metric_3_recommendations_changed_pct == 35.0


def test_metric_4_language_mismatches_detected(tmp_path: Path):
    """Verify Metric 4: Safe detection of 29 language mismatches (72.5%)."""
    runner = ComparisonRunner(db_path=tmp_path / "test_metrics_4.db")
    run_result = runner.run_all()
    metrics = run_result.metrics

    assert metrics.metric_4_language_mismatches_detected_count == 29
    assert metrics.metric_4_language_mismatches_pct == 72.5


def test_metric_5_immediate_escalations(tmp_path: Path):
    """Verify Metric 5: Number of immediate clinical escalations."""
    runner = ComparisonRunner(db_path=tmp_path / "test_metrics_5.db")
    run_result = runner.run_all()
    metrics = run_result.metrics

    assert metrics.metric_5_immediate_escalations_count == 0
    assert metrics.metric_5_immediate_escalations_pct == 0.0


def test_empty_results_metric_calculation():
    """Verify calculate_comparison_metrics gracefully handles an empty list."""
    metrics = calculate_comparison_metrics([])
    assert metrics.total_cases_evaluated == 0
    assert metrics.metric_1_baseline_feasible_pct == 0.0
    assert metrics.metric_1_resource_aware_feasible_pct == 0.0
    assert metrics.metric_2_total_high_priority_cases == 0
    assert metrics.metric_2_baseline_high_priority_tracked_pct == 0.0
    assert metrics.metric_2_resource_aware_high_priority_tracked_pct == 0.0
    assert metrics.metric_3_recommendations_changed_count == 0
    assert metrics.metric_4_language_mismatches_detected_count == 0
    assert metrics.metric_5_immediate_escalations_count == 0
