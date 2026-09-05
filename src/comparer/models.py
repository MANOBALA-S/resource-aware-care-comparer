"""Pydantic models for Baseline vs Resource-Aware care option comparison.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CaseComparisonResult(BaseModel):
    """Structured per-case comparison between textbook baseline and resource-aware engine.

    Satisfies Phase 7 comparison contract:
    - case_id
    - condition
    - site_id
    - urgency
    - baseline_recommendation
    - resource_aware_recommendation
    - baseline_feasible
    - resource_aware_feasible
    - baseline_follow_up
    - resource_aware_follow_up
    - baseline_language_checked
    - resource_aware_language_checked
    - baseline_reason
    - resource_aware_reason
    - changed_recommendation
    """
    case_id: str = Field(..., description="Unique synthetic case identifier")
    condition: str = Field(..., description="Clinical condition under evaluation")
    site_id: str = Field(..., description="Healthcare facility site identifier")
    urgency: str = Field(..., description="Case clinical urgency level")
    
    # Recommendations
    baseline_recommendation: str = Field(
        ..., description="Textbook gold-standard recommendation from baseline engine"
    )
    resource_aware_recommendation: str = Field(
        ..., description="Adapted or escalated recommendation from resource-aware engine"
    )
    
    # Feasibility
    baseline_feasible: bool = Field(
        ..., description="Whether the baseline recommendation is actually feasible at local site"
    )
    resource_aware_feasible: bool = Field(
        ..., description="Whether the resource-aware system selected a feasible local care option"
    )
    
    # Follow-up
    baseline_follow_up: Optional[str] = Field(
        None, description="Follow-up disposition from baseline (untracked/unassigned)"
    )
    resource_aware_follow_up: Optional[str] = Field(
        None, description="Tracked follow-up task with named owner, due date, and escalation path"
    )
    
    # Language Safety Checks
    baseline_language_checked: bool = Field(
        default=False, description="Whether baseline verified patient-clinician language compatibility"
    )
    resource_aware_language_checked: bool = Field(
        default=True, description="Whether resource-aware engine verified patient language compatibility"
    )
    
    # Reason Trails
    baseline_reason: str = Field(
        ..., description="Explanation of baseline recommendation rationale"
    )
    resource_aware_reason: str = Field(
        ..., description="Explanation of resource-aware selection or escalation rationale"
    )
    
    # Core Comparative Divergence
    changed_recommendation: bool = Field(
        ..., description="Whether resource-aware recommendation diverged from textbook baseline"
    )
    
    # Detailed Audit & Metric Flags
    baseline_ladder_level: str = Field(
        default="preferred", description="Baseline always attempts the preferred textbook rung"
    )
    resource_aware_ladder_level: Optional[str] = Field(
        default=None, description="Ladder tier selected by resource-aware engine"
    )
    language_mismatch: bool = Field(
        default=False, description="True if patient language required interpreter or language escalation"
    )
    immediate_escalation: bool = Field(
        default=False, description="True if resource-aware triggered immediate clinical escalation"
    )
    high_priority: bool = Field(
        default=False, description="True if case urgency is HIGH or CRITICAL"
    )
    has_named_owner: bool = Field(
        default=False, description="True if follow-up task has an assigned named owner"
    )
    has_due_date: bool = Field(
        default=False, description="True if follow-up task has a deterministic calculated due date"
    )
    has_escalation_path: bool = Field(
        default=False, description="True if follow-up task has a defined escalation hierarchy"
    )
    
    governance_notice: str = Field(
        default="Decision-support prototype — clinician sign-off required.",
        description="Clinical governance disclaimer",
    )
    synthetic_data_notice: str = Field(
        default="Synthetic data only — no real patient data.",
        description="Mandatory data notice",
    )


class ComparisonSummaryMetrics(BaseModel):
    """Aggregated evaluation metrics comparing baseline vs resource-aware systems across all cases."""
    total_cases_evaluated: int = Field(..., description="Total synthetic cases evaluated")
    
    # Metric 1: Feasibility given site resources
    metric_1_baseline_feasible_pct: float = Field(
        ..., description="Percentage of baseline recommendations feasible given site resources"
    )
    metric_1_resource_aware_feasible_pct: float = Field(
        ..., description="Percentage of resource-aware recommendations feasible given site resources"
    )
    metric_1_baseline_feasible_count: int = Field(
        ..., description="Count of baseline recommendations feasible given site resources"
    )
    metric_1_resource_aware_feasible_count: int = Field(
        ..., description="Count of resource-aware recommendations feasible given site resources"
    )
    
    # Metric 2: High-priority follow-up accountability
    metric_2_total_high_priority_cases: int = Field(
        ..., description="Total count of HIGH and CRITICAL urgency cases"
    )
    metric_2_baseline_high_priority_tracked_pct: float = Field(
        ..., description="Percentage of baseline high-priority cases with owner, due date, escalation path (0%)"
    )
    metric_2_resource_aware_high_priority_tracked_pct: float = Field(
        ..., description="Percentage of resource-aware high-priority cases with owner, due date, escalation path (100%)"
    )
    
    # Metric 3: Recommendations changed because of constraints
    metric_3_recommendations_changed_count: int = Field(
        ..., description="Number of recommendations changed due to local resource constraints"
    )
    metric_3_recommendations_changed_pct: float = Field(
        ..., description="Percentage of recommendations changed due to constraints"
    )
    
    # Metric 4: Language mismatches detected
    metric_4_language_mismatches_detected_count: int = Field(
        ..., description="Number of language mismatches safely identified"
    )
    metric_4_language_mismatches_pct: float = Field(
        ..., description="Percentage of cases with language mismatch identified"
    )
    
    # Metric 5: Immediate escalations
    metric_5_immediate_escalations_count: int = Field(
        ..., description="Number of immediate clinical escalations triggered"
    )
    metric_5_immediate_escalations_pct: float = Field(
        ..., description="Percentage of cases triggering immediate clinical escalation"
    )
    
    # Breakdown statistics
    breakdown_by_ladder_level: Dict[str, int] = Field(
        default_factory=dict, description="Distribution of selected resource-aware ladder tiers"
    )
    breakdown_by_site: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Feasibility and changed recommendations by site"
    )
    breakdown_by_condition: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Feasibility and changed recommendations by condition"
    )
    
    governance_notice: str = Field(
        default="Decision-support prototype — clinician sign-off required.",
        description="Clinical governance disclaimer",
    )
    synthetic_data_notice: str = Field(
        default="Synthetic data only — no real patient data.",
        description="Mandatory data notice",
    )


class ComparisonRunResult(BaseModel):
    """Complete container for a full comparative evaluation run."""
    run_timestamp: str = Field(..., description="ISO timestamp of comparison execution")
    engine_version: str = Field(default="1.0.0", description="Comparative engine version")
    cases_evaluated: int = Field(..., description="Number of cases evaluated")
    metrics: ComparisonSummaryMetrics = Field(..., description="Summary metrics")
    results: List[CaseComparisonResult] = Field(..., description="Per-case comparative records")
