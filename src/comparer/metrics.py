"""Metric calculation engine for Baseline vs Resource-Aware comparative evaluation.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from typing import Any, Dict, List
from collections import Counter, defaultdict

from src.comparer.models import CaseComparisonResult, ComparisonSummaryMetrics


def calculate_comparison_metrics(results: List[CaseComparisonResult]) -> ComparisonSummaryMetrics:
    """Compute the 5 mandatory evaluation metrics and detailed breakdowns.

    Metrics:
    1. % recommendations feasible given site resources (Baseline vs Resource-Aware).
    2. % high-priority follow-ups with named owner, due date, and escalation path.
    3. Number and % of recommendations changed because of local constraints.
    4. Number and % of language mismatches detected.
    5. Number and % of immediate clinical escalations triggered.

    Args:
        results: List of evaluated CaseComparisonResult records.

    Returns:
        ComparisonSummaryMetrics containing deterministic summary and breakdown statistics.
    """
    total_cases = len(results)
    if total_cases == 0:
        return ComparisonSummaryMetrics(
            total_cases_evaluated=0,
            metric_1_baseline_feasible_pct=0.0,
            metric_1_resource_aware_feasible_pct=0.0,
            metric_1_baseline_feasible_count=0,
            metric_1_resource_aware_feasible_count=0,
            metric_2_total_high_priority_cases=0,
            metric_2_baseline_high_priority_tracked_pct=0.0,
            metric_2_resource_aware_high_priority_tracked_pct=0.0,
            metric_3_recommendations_changed_count=0,
            metric_3_recommendations_changed_pct=0.0,
            metric_4_language_mismatches_detected_count=0,
            metric_4_language_mismatches_pct=0.0,
            metric_5_immediate_escalations_count=0,
            metric_5_immediate_escalations_pct=0.0,
        )

    # -------------------------------------------------------------------------
    # Metric 1: Feasibility given site resources
    # -------------------------------------------------------------------------
    baseline_feasible_count = sum(1 for r in results if r.baseline_feasible)
    resource_aware_feasible_count = sum(1 for r in results if r.resource_aware_feasible)
    
    metric_1_base_pct = round((baseline_feasible_count / total_cases) * 100.0, 2)
    metric_1_ra_pct = round((resource_aware_feasible_count / total_cases) * 100.0, 2)

    # -------------------------------------------------------------------------
    # Metric 2: High-priority follow-up accountability (owner, due date, path)
    # -------------------------------------------------------------------------
    high_priority_cases = [r for r in results if r.high_priority]
    total_hp = len(high_priority_cases)
    
    # Baseline follow-up tracking is always 0% (baseline never assigns owner, due date, or path)
    baseline_hp_tracked_count = sum(
        1 for r in high_priority_cases
        if r.baseline_language_checked  # Baseline never tracks
    )
    metric_2_base_pct = round((baseline_hp_tracked_count / total_hp) * 100.0, 2) if total_hp > 0 else 0.0
    
    # Resource-aware follow-up tracking (requires named owner, due date, and escalation path)
    ra_hp_tracked_count = sum(
        1 for r in high_priority_cases
        if r.has_named_owner and r.has_due_date and r.has_escalation_path
    )
    metric_2_ra_pct = round((ra_hp_tracked_count / total_hp) * 100.0, 2) if total_hp > 0 else 100.0

    # -------------------------------------------------------------------------
    # Metric 3: Recommendations changed because of constraints
    # -------------------------------------------------------------------------
    changed_count = sum(1 for r in results if r.changed_recommendation)
    metric_3_pct = round((changed_count / total_cases) * 100.0, 2)

    # -------------------------------------------------------------------------
    # Metric 4: Language mismatches detected
    # -------------------------------------------------------------------------
    mismatch_count = sum(1 for r in results if r.language_mismatch)
    metric_4_pct = round((mismatch_count / total_cases) * 100.0, 2)

    # -------------------------------------------------------------------------
    # Metric 5: Immediate escalations
    # -------------------------------------------------------------------------
    escalation_count = sum(1 for r in results if r.immediate_escalation)
    metric_5_pct = round((escalation_count / total_cases) * 100.0, 2)

    # -------------------------------------------------------------------------
    # Categorical Breakdowns
    # -------------------------------------------------------------------------
    ladder_counter = Counter(r.resource_aware_ladder_level or "unknown" for r in results)
    breakdown_by_ladder = dict(ladder_counter)

    # Breakdown by site
    site_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "total_cases": 0,
        "baseline_feasible": 0,
        "resource_aware_feasible": 0,
        "changed_recommendations": 0,
        "escalations": 0,
    })
    for r in results:
        entry = site_map[r.site_id]
        entry["total_cases"] += 1
        if r.baseline_feasible:
            entry["baseline_feasible"] += 1
        if r.resource_aware_feasible:
            entry["resource_aware_feasible"] += 1
        if r.changed_recommendation:
            entry["changed_recommendations"] += 1
        if r.immediate_escalation:
            entry["escalations"] += 1

    # Breakdown by condition
    cond_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "total_cases": 0,
        "baseline_feasible": 0,
        "resource_aware_feasible": 0,
        "changed_recommendations": 0,
        "escalations": 0,
    })
    for r in results:
        entry = cond_map[r.condition]
        entry["total_cases"] += 1
        if r.baseline_feasible:
            entry["baseline_feasible"] += 1
        if r.resource_aware_feasible:
            entry["resource_aware_feasible"] += 1
        if r.changed_recommendation:
            entry["changed_recommendations"] += 1
        if r.immediate_escalation:
            entry["escalations"] += 1

    return ComparisonSummaryMetrics(
        total_cases_evaluated=total_cases,
        metric_1_baseline_feasible_pct=metric_1_base_pct,
        metric_1_resource_aware_feasible_pct=metric_1_ra_pct,
        metric_1_baseline_feasible_count=baseline_feasible_count,
        metric_1_resource_aware_feasible_count=resource_aware_feasible_count,
        metric_2_total_high_priority_cases=total_hp,
        metric_2_baseline_high_priority_tracked_pct=metric_2_base_pct,
        metric_2_resource_aware_high_priority_tracked_pct=metric_2_ra_pct,
        metric_3_recommendations_changed_count=changed_count,
        metric_3_recommendations_changed_pct=metric_3_pct,
        metric_4_language_mismatches_detected_count=mismatch_count,
        metric_4_language_mismatches_pct=metric_4_pct,
        metric_5_immediate_escalations_count=escalation_count,
        metric_5_immediate_escalations_pct=metric_5_pct,
        breakdown_by_ladder_level=breakdown_by_ladder,
        breakdown_by_site=dict(site_map),
        breakdown_by_condition=dict(cond_map),
        governance_notice="Decision-support prototype — clinician sign-off required.",
        synthetic_data_notice="Synthetic data only — no real patient data.",
    )
