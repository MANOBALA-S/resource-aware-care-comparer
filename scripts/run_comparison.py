"""CLI script to run paired comparison across all 40 synthetic patient cases.

Executes both Textbook Baseline and Resource-Aware decision engines on identical inputs,
calculates comparative metrics, and saves results and summary JSON artifacts.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.comparer.runner import ComparisonRunner


def main() -> None:
    """Run full evaluation across all 40 synthetic cases and print metrics."""
    print("=" * 80)
    print(" PHASE 7 — BASELINE VS RESOURCE-AWARE CARE OPTION COMPARER")
    print("=" * 80)
    print(" GOVERNANCE: Decision-support prototype — clinician sign-off required.")
    print(" DATA:       Synthetic data only — no real patient data.")
    print("-" * 80)

    runner = ComparisonRunner()
    print(f"Loaded {len(runner.cases)} synthetic cases across {len(runner.sites)} healthcare sites.")
    print("Executing paired comparative evaluation pipeline...")

    output_results = PROJECT_ROOT / "data" / "generated" / "comparison_results.json"
    output_summary = PROJECT_ROOT / "data" / "generated" / "comparison_summary.json"

    run_result = runner.run_and_save(
        output_results_path=output_results,
        output_summary_path=output_summary,
    )

    metrics = run_result.metrics

    print("\n" + "=" * 80)
    print(" COMPARATIVE EVALUATION SUMMARY METRICS")
    print("=" * 80)
    print(f" Total Cases Evaluated: {metrics.total_cases_evaluated}")
    print("-" * 80)
    print(" METRIC 1: % Recommendations Feasible Given Site Resources")
    print(f"   - Baseline (Textbook Gold-Standard): {metrics.metric_1_baseline_feasible_pct}% "
          f"({metrics.metric_1_baseline_feasible_count}/{metrics.total_cases_evaluated})")
    print(f"   - Resource-Aware System:             {metrics.metric_1_resource_aware_feasible_pct}% "
          f"({metrics.metric_1_resource_aware_feasible_count}/{metrics.total_cases_evaluated})")
    print("-" * 80)
    print(" METRIC 2: % High-Priority Follow-ups with Owner, Due Date & Escalation Path")
    print(f"   - Total High-Priority Cases (HIGH/CRITICAL): {metrics.metric_2_total_high_priority_cases}")
    print(f"   - Baseline System:                           {metrics.metric_2_baseline_high_priority_tracked_pct}% (0/{metrics.metric_2_total_high_priority_cases})")
    print(f"   - Resource-Aware System:                     {metrics.metric_2_resource_aware_high_priority_tracked_pct}% ({metrics.metric_2_total_high_priority_cases}/{metrics.metric_2_total_high_priority_cases})")
    print("-" * 80)
    print(" METRIC 3: Recommendations Changed Because of Constraints")
    print(f"   - Count: {metrics.metric_3_recommendations_changed_count} / {metrics.total_cases_evaluated} cases "
          f"({metrics.metric_3_recommendations_changed_pct}%)")
    print("-" * 80)
    print(" METRIC 4: Language Mismatches Detected")
    print(f"   - Count: {metrics.metric_4_language_mismatches_detected_count} / {metrics.total_cases_evaluated} cases "
          f"({metrics.metric_4_language_mismatches_pct}%)")
    print("-" * 80)
    print(" METRIC 5: Immediate Clinical Escalations Triggered")
    print(f"   - Count: {metrics.metric_5_immediate_escalations_count} / {metrics.total_cases_evaluated} cases "
          f"({metrics.metric_5_immediate_escalations_pct}%)")
    print("-" * 80)
    print(" RESOURCE-AWARE LADDER TIER DISTRIBUTION:")
    for level, count in sorted(metrics.breakdown_by_ladder_level.items()):
        print(f"   - {level:30s}: {count:2d} cases")
    print("-" * 80)
    print(" OUTPUT FILES GENERATED:")
    print(f"   - Results: {output_results}")
    print(f"   - Summary: {output_summary}")
    print("=" * 80)


if __name__ == "__main__":
    main()
