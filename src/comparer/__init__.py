"""Phase 7: Baseline vs Resource-Aware Care Option Comparer.

Provides paired comparative execution of synthetic cases through the textbook baseline
and the resource-aware decision engine, calculating feasibility, follow-up accountability,
recommendation divergence, language detection, and escalation metrics.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from src.comparer.comparison import compare_single_case
from src.comparer.metrics import calculate_comparison_metrics
from src.comparer.models import (
    CaseComparisonResult,
    ComparisonRunResult,
    ComparisonSummaryMetrics,
)
from src.comparer.runner import ComparisonRunner, run_all_comparisons

__all__ = [
    "CaseComparisonResult",
    "ComparisonSummaryMetrics",
    "ComparisonRunResult",
    "ComparisonRunner",
    "compare_single_case",
    "calculate_comparison_metrics",
    "run_all_comparisons",
]
