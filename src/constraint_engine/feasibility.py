"""Feasibility evaluator implementing deterministic option ladder traversal and safety rules.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from typing import Any, Dict, List, Optional

from src.constraint_engine.models import (
    ConstraintEngineResult,
    LanguageEvaluation,
    LanguageStatus,
    OptionEvaluation,
    ResourceEvaluation,
    ResourceStatus,
)
from src.constraint_engine.reason_trail import ReasonTrailBuilder
from src.constraint_engine.resource_filter import evaluate_resource_availability
from src.models.operational_models import (
    ConnectivityQuality,
    PatientCase,
    ServiceSite,
    TravelConstraints,
)
from src.protocol_engine.models import ProtocolDefinition, RecommendationOption


def evaluate_language_safety(
    patient_language: str,
    site: ServiceSite,
    clinician_languages: Optional[List[str]] = None,
) -> LanguageEvaluation:
    """Evaluate patient language against clinician and site interpreter capabilities.

    Safety rule: If neither clinician, site staff, nor interpreter can communicate in
    the patient's language, DO NOT silently proceed. Trigger LANGUAGE_ESCALATION_REQUIRED.

    Args:
        patient_language: ISO language code (e.g., 'en', 'ta')
        site: ServiceSite profile of the facility.
        clinician_languages: List of languages spoken by remote clinicians (default: ['en']).

    Returns:
        LanguageEvaluation model.
    """
    clin_langs = [l.strip().lower() for l in (clinician_languages or ["en"])]
    p_lang = patient_language.strip().lower()
    site_langs = [l.strip().lower() for l in site.supported_languages]
    interpreter_langs = [l.strip().lower() for l in site.interpreter_languages]

    # Case 1: Directly supported by clinician or site staff
    if p_lang in clin_langs or p_lang in site_langs:
        return LanguageEvaluation(
            patient_language=patient_language,
            status=LanguageStatus.SUPPORTED,
            interpreter_available=False,
            explanation=f"Patient language '{patient_language}' is directly supported by available healthcare staff.",
        )

    # Case 2: Supported via available interpreter
    if p_lang in interpreter_langs:
        return LanguageEvaluation(
            patient_language=patient_language,
            status=LanguageStatus.REQUIRES_INTERPRETER,
            interpreter_available=True,
            explanation=f"Patient language '{patient_language}' requires translation; certified interpreter is available.",
        )

    # Case 3: Unsupported - Safety trigger
    return LanguageEvaluation(
        patient_language=patient_language,
        status=LanguageStatus.LANGUAGE_ESCALATION_REQUIRED,
        interpreter_available=False,
        explanation=(
            f"Patient language '{patient_language}' is NOT supported by current clinicians, "
            f"on-site staff, or available interpreters. Immediate language escalation is mandatory."
        ),
    )


def evaluate_option_feasibility(
    ladder_level: str,
    option: RecommendationOption,
    site: ServiceSite,
    travel_constraints: TravelConstraints,
    raw_site_dict: Optional[Dict[str, Any]] = None,
) -> OptionEvaluation:
    """Evaluate whether a specific ladder tier option is feasible at the site.

    Checks:
    1. Resource requirements (equipment, medications, cold chain, staffing, transport)
    2. Travel feasibility (if transfer/referral required, transport must be available)
    3. Connectivity feasibility (if teleconsultation/remote monitoring required)

    Args:
        ladder_level: Ladder tier name ('preferred', 'resource_adapted_alternative', 'minimum_safe_fallback', 'escalate_only')
        option: RecommendationOption containing option text and required_resources.
        site: ServiceSite facility profile.
        travel_constraints: TravelConstraints of the patient case.
        raw_site_dict: Optional raw dictionary to detect conflicts.

    Returns:
        OptionEvaluation containing boolean feasibility and list of blocking reasons.
    """
    resource_evaluations: List[ResourceEvaluation] = []
    blocking_reasons: List[str] = []

    # 1. Evaluate each declared required resource
    for res in option.required_resources:
        eval_res = evaluate_resource_availability(
            resource=res,
            site=site,
            travel_constraints=travel_constraints,
            raw_site_dict=raw_site_dict,
        )
        resource_evaluations.append(eval_res)
        if not eval_res.available:
            blocking_reasons.append(f"{res}: {eval_res.reason}")

    opt_text_lower = option.option.lower()

    # 2. Check travel feasibility if option requires transfer/referral/ambulance
    requires_transfer = any(
        kw in opt_text_lower
        for kw in ("transfer", "ambulance", "referral", "transport to", "tertiary center")
    )
    if requires_transfer:
        if not travel_constraints.transport_available and not site.transport_available:
            reason = "Transfer required, but neither facility ambulance nor patient transport is available."
            if reason not in blocking_reasons:
                blocking_reasons.append(reason)

    # 3. Check connectivity feasibility if option requires remote/tele-review
    requires_remote = any(
        kw in opt_text_lower
        for kw in ("teleconsult", "tele-review", "tele-pulmonology", "remote neurologist", "video guidance", "digital wound margin")
    )
    if requires_remote:
        if (
            travel_constraints.connectivity_quality == ConnectivityQuality.POOR
            or not travel_constraints.follow_up_teleconsult_possible
        ):
            reason = "Remote review or teleconsultation is infeasible due to insufficient connectivity (POOR quality or high loss)."
            if reason not in blocking_reasons:
                blocking_reasons.append(reason)

    is_feasible = len(blocking_reasons) == 0

    return OptionEvaluation(
        ladder_level=ladder_level,
        option_text=option.option,
        feasible=is_feasible,
        resource_evaluations=resource_evaluations,
        blocking_reasons=blocking_reasons,
    )


def evaluate_case_constraints(
    case: PatientCase,
    protocol: ProtocolDefinition,
    site: ServiceSite,
    raw_site_dict: Optional[Dict[str, Any]] = None,
    clinician_languages: Optional[List[str]] = None,
) -> ConstraintEngineResult:
    """Execute complete deterministic evaluation of a patient case against a clinical protocol.

    Follows the strict decision order:
    1. preferred
    2. resource_adapted_alternative
    3. minimum_safe_fallback
    4. escalate_only (if all preceding are blocked)

    Args:
        case: PatientCase containing condition, travel constraints, and language.
        protocol: ProtocolDefinition containing the 4-tier recommendation ladder.
        site: ServiceSite containing facility equipment, medication stock, and telemetry.
        raw_site_dict: Optional raw dictionary for metadata conflict checks.
        clinician_languages: Optional list of languages spoken by remote clinicians.

    Returns:
        ConstraintEngineResult with selected option, reason trail, and escalation status.
    """
    reason_builder = ReasonTrailBuilder()
    reason_builder.add_step(
        f"Initiating evaluation for Case '{case.case_id}' (Condition: '{case.condition}', Site: '{case.site_id}')."
    )

    # 1. Language Safety Assessment
    lang_eval = evaluate_language_safety(
        patient_language=case.patient_language,
        site=site,
        clinician_languages=clinician_languages,
    )
    reason_builder.log_language_evaluation(lang_eval)

    # 2. Evaluate Recommendation Ladder Tiers in Strict Hierarchy
    ladder = protocol.recommendation_ladder
    rungs = [
        ("preferred", ladder.preferred),
        ("resource_adapted_alternative", ladder.resource_adapted_alternative),
        ("minimum_safe_fallback", ladder.minimum_safe_fallback),
    ]

    selected_level: Optional[str] = None
    selected_option_text: Optional[str] = None
    blocked_options_map: Dict[str, List[str]] = {}
    all_resource_status: Dict[str, ResourceEvaluation] = {}

    for rung_name, rung_option in rungs:
        eval_result = evaluate_option_feasibility(
            ladder_level=rung_name,
            option=rung_option,
            site=site,
            travel_constraints=case.travel_constraints,
            raw_site_dict=raw_site_dict,
        )

        # Store resource evaluations
        for r_eval in eval_result.resource_evaluations:
            all_resource_status[r_eval.resource] = r_eval

        reason_builder.log_option_evaluation(eval_result)

        if eval_result.feasible:
            selected_level = rung_name
            selected_option_text = rung_option.option
            break
        else:
            blocked_options_map[rung_name] = eval_result.blocking_reasons

    # 3. Decision Synthesis & Exhaustion Handling
    escalation_required = False
    escalation_reason: Optional[str] = None
    fallback_owner_required = False
    decision_type = "SELECT_OPTION"
    is_feasible = True

    if selected_level is not None:
        # A local tier (preferred, adapted, or fallback) is feasible
        is_feasible = True
        decision_type = "SELECT_OPTION"
    else:
        # ALL 3 LOCAL TIERS ARE INFEASIBLE: Trigger immediate safe escalation
        is_feasible = False
        decision_type = "ESCALATE_IMMEDIATELY"
        selected_level = "escalate_only"
        selected_option_text = ladder.escalate_only.option
        escalation_required = True
        fallback_owner_required = True
        escalation_reason = (
            "All local care pathways (preferred, resource-adapted alternative, and minimum-safe fallback) "
            "are blocked due to critical site resource deficits. Immediate clinical and operational escalation is required."
        )

    # 4. Language Safety Overlay
    if lang_eval.status == LanguageStatus.LANGUAGE_ESCALATION_REQUIRED:
        escalation_required = True
        lang_msg = f"Language escalation: Patient language '{case.patient_language}' is unsupported."
        if escalation_reason:
            escalation_reason = f"{escalation_reason}; {lang_msg}"
        else:
            escalation_reason = lang_msg

    reason_builder.log_final_decision(
        decision=decision_type,
        selected_level=selected_level,
        escalation_required=escalation_required,
        escalation_reason=escalation_reason,
    )

    return ConstraintEngineResult(
        case_id=case.case_id,
        protocol_id=protocol.protocol_id,
        selected_option=selected_option_text,
        selected_ladder_level=selected_level,
        feasible=is_feasible,
        decision=decision_type,
        reason_trail=reason_builder.build(),
        blocked_options=blocked_options_map,
        escalation_required=escalation_required,
        escalation_reason=escalation_reason,
        fallback_owner_required=fallback_owner_required,
        language_status=lang_eval.status,
        resource_status=all_resource_status,
        governance_notice="Decision-support prototype — clinician sign-off required.",
        synthetic_data_notice="Synthetic data only — no real patient data.",
    )
