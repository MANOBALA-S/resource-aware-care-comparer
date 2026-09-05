"""Per-case comparison logic running the identical case through Baseline and Resource-Aware engines.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
import copy

from baseline.baseline_engine import TextbookBaselineEngine
from src.comparer.models import CaseComparisonResult
from src.constraint_engine.feasibility import (
    evaluate_case_constraints,
    evaluate_option_feasibility,
)
from src.followup.tracker import create_followup_from_evaluation
from src.language.models import LanguageStatus
from src.language.resolver import resolve_language
from src.models.operational_models import PatientCase, ServiceSite
from src.protocol_engine.models import ProtocolDefinition


def compare_single_case(
    case: PatientCase,
    site: ServiceSite,
    protocol: ProtocolDefinition,
    baseline_engine: TextbookBaselineEngine,
    clinician_languages: Optional[List[str]] = None,
    db_path: Optional[Path] = None,
) -> CaseComparisonResult:
    """Run an identical synthetic case through Baseline and Resource-Aware systems.

    Safety & Fairness Guarantees:
    - The case object is NOT mutated between or during evaluations.
    - Same condition, same site, same urgency, same travel constraints.
    - Baseline evaluates unconstrained textbook protocol lookup.
    - Resource-aware evaluates actual site resources, travel, connectivity,
      follow-up accountability, and language safety.

    Args:
        case: Synthetic patient case.
        site: Facility profile from synthetic service registry.
        protocol: Clinical protocol definition from library.
        baseline_engine: Instance of TextbookBaselineEngine.
        clinician_languages: List of languages spoken by clinician (default: ['en']).
        db_path: Optional SQLite path for follow-up tracking repository.

    Returns:
        CaseComparisonResult containing parallel fields and divergence metrics.
    """
    clin_langs = clinician_languages or ["en"]

    # Deep snapshot to verify case immutability
    case_snapshot = copy.deepcopy(case.model_dump())

    # =========================================================================
    # 1. BASELINE EVALUATION (Phase 2 Textbook Lookup)
    # =========================================================================
    # Baseline deliberately ignores site resources, connectivity, language, and follow-ups.
    baseline_output = baseline_engine.generate_recommendation(case.model_dump())
    baseline_rec = baseline_output.get("recommendation", protocol.textbook_recommendation)

    # Determine if baseline's recommendation is actually feasible at this facility:
    # Baseline always prescribes the preferred textbook rung.
    eval_pref = evaluate_option_feasibility(
        ladder_level="preferred",
        option=protocol.recommendation_ladder.preferred,
        site=site,
        travel_constraints=case.travel_constraints,
    )
    baseline_feasible = eval_pref.feasible

    # Baseline follow-up is untracked (no assigned owner, no due date, no escalation path)
    baseline_follow_up = (
        f"Untracked (interval: {protocol.follow_up_interval or 'unspecified'}, "
        f"no named owner, no due date, no escalation path)"
    )
    baseline_reason = (
        "Standard textbook protocol lookup; site resources, equipment, medication stock, "
        "specialists, travel constraints, connectivity, language support, and follow-up feasibility not evaluated."
    )

    # =========================================================================
    # 2. RESOURCE-AWARE EVALUATION (Phase 4 + Phase 5 + Phase 6)
    # =========================================================================
    # Constraint Engine evaluation (Phase 4 + Phase 6 safety overlay)
    ra_result = evaluate_case_constraints(
        case=case,
        protocol=protocol,
        site=site,
        clinician_languages=clin_langs,
    )
    resource_aware_rec = ra_result.selected_option or protocol.recommendation_ladder.escalate_only.option
    resource_aware_feasible = ra_result.feasible

    # Follow-Up Tracking (Phase 5)
    followup_task = create_followup_from_evaluation(
        result=ra_result,
        case=case,
        protocol=protocol,
        db_path=db_path,
    )
    escalation_path_str = " -> ".join(followup_task.escalation_path) if followup_task.escalation_path else "None"
    resource_aware_follow_up = (
        f"Tracked (owner: {followup_task.owner}, due: {followup_task.due_at}, "
        f"path: {escalation_path_str})"
    )
    has_named_owner = bool(followup_task.owner)
    has_due_date = bool(followup_task.due_at)
    has_escalation_path = bool(followup_task.escalation_path and len(followup_task.escalation_path) > 0)

    # Language Resolution (Phase 6)
    lang_profile = resolve_language(
        patient_language=case.patient_language,
        clinician_languages=clin_langs,
        interpreter_languages=site.interpreter_languages,
        interpreter_available=bool(site.interpreter_languages),
        preferred_language=case.language_profile.preferred_language if case.language_profile else None,
    )
    language_mismatch = lang_profile.language_status in (
        LanguageStatus.REQUIRES_INTERPRETER,
        LanguageStatus.LANGUAGE_ESCALATION_REQUIRED,
    )

    # Resource-aware reason generation
    if ra_result.decision == "ESCALATE_IMMEDIATELY":
        resource_aware_reason = (
            ra_result.escalation_reason
            or "All local care options blocked; immediate clinical and operational escalation required."
        )
    elif ra_result.selected_ladder_level == "preferred":
        resource_aware_reason = (
            "Preferred textbook option verified: all required facility equipment, specialist coverage, "
            "medications, cold chain, and connectivity confirmed available."
        )
    else:
        blocked_reasons = ra_result.blocked_options.get("preferred", ["site resource deficits"])
        blocked_summary = "; ".join(blocked_reasons[:2])
        resource_aware_reason = (
            f"Adapted to [{ra_result.selected_ladder_level}]: Preferred tier blocked due to {blocked_summary}."
        )

    # Changed recommendation determination (diverged from preferred textbook care due to site constraints)
    changed_recommendation = (ra_result.selected_ladder_level != "preferred") or (not ra_result.feasible)

    # High priority indicator
    case_urgency_str = case.urgency.upper() if isinstance(case.urgency, str) else case.urgency.value.upper()
    is_high_priority = case_urgency_str in ("HIGH", "CRITICAL")
    is_immediate_escalation = (ra_result.decision == "ESCALATE_IMMEDIATELY" or ra_result.escalation_required)

    # Assert immutability: case data has not changed
    assert case.model_dump() == case_snapshot, f"Case {case.case_id} was mutated during comparison evaluation!"

    return CaseComparisonResult(
        case_id=case.case_id,
        condition=case.condition,
        site_id=case.site_id,
        urgency=case_urgency_str,
        baseline_recommendation=baseline_rec,
        resource_aware_recommendation=resource_aware_rec,
        baseline_feasible=baseline_feasible,
        resource_aware_feasible=resource_aware_feasible,
        baseline_follow_up=baseline_follow_up,
        resource_aware_follow_up=resource_aware_follow_up,
        baseline_language_checked=False,
        resource_aware_language_checked=True,
        baseline_reason=baseline_reason,
        resource_aware_reason=resource_aware_reason,
        changed_recommendation=changed_recommendation,
        baseline_ladder_level="preferred",
        resource_aware_ladder_level=ra_result.selected_ladder_level,
        language_mismatch=language_mismatch,
        immediate_escalation=is_immediate_escalation,
        high_priority=is_high_priority,
        has_named_owner=has_named_owner,
        has_due_date=has_due_date,
        has_escalation_path=has_escalation_path,
        governance_notice="Decision-support prototype — clinician sign-off required.",
        synthetic_data_notice="Synthetic data only — no real patient data.",
    )
