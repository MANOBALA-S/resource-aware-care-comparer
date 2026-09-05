"""FastAPI routes for the Care Option Comparison Screen (Phase 10).

Provides dedicated endpoints for side-by-side comparison between Textbook Baseline and
Resource-Aware decision support for the SAME synthetic patient case.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from baseline.baseline_engine import TextbookBaselineEngine
from src.comparer.comparison import compare_single_case
from src.comparer.models import CaseComparisonResult, ComparisonSummaryMetrics
from src.comparer.runner import ComparisonRunner
from src.config import PROJECT_ROOT
from src.constraint_engine.feasibility import (
    evaluate_case_constraints,
    evaluate_option_feasibility,
)
from src.followup.tracker import create_followup_from_evaluation
from src.language.models import LanguageStatus
from src.language.resolver import resolve_language
from src.models.operational_models import PatientCase, ServiceSite
from src.protocol_engine.protocol_engine import get_protocol_engine

router = APIRouter(prefix="/comparer", tags=["Care Option Comparer"])

CASES_FILE = PROJECT_ROOT / "data" / "cases" / "synthetic_cases.json"
SERVICES_FILE = PROJECT_ROOT / "data" / "services" / "service_registry.json"
SUMMARY_FILE = PROJECT_ROOT / "data" / "generated" / "comparison_summary.json"


class BaselinePanelData(BaseModel):
    """Structured Left-Panel data for Textbook / Baseline Method."""
    label: str = Field(default="TEXTBOOK / BASELINE METHOD")
    recommendation: str = Field(..., description="Textbook gold-standard recommendation")
    resources_ignored: List[str] = Field(..., description="Operational constraints ignored by baseline")
    follow_up: str = Field(..., description="Untracked follow-up disposition")
    language: str = Field(..., description="Language safety status (unverified)")
    feasibility: bool = Field(..., description="Whether feasible at local facility")
    feasibility_status: str = Field(..., description="'FEASIBLE' or 'NOT FEASIBLE'")
    feasibility_reason: str = Field(..., description="Rationale for local feasibility outcome")


class ResourceAwarePanelData(BaseModel):
    """Structured Right-Panel data for Resource-Aware Method."""
    label: str = Field(default="RESOURCE-AWARE METHOD")
    selected_option: str = Field(..., description="Selected care option")
    ladder_level: str = Field(..., description="Ladder rung selected")
    feasibility: bool = Field(..., description="Whether feasible locally")
    feasibility_status: str = Field(..., description="'FEASIBLE' or 'ESCALATE IMMEDIATELY'")
    feasibility_details: str = Field(..., description="Local facility resource verification summary")
    reason_trail: List[str] = Field(..., description="Chronological decision trail")
    blocked_options: Dict[str, List[str]] = Field(..., description="Higher tiers blocked and reasons")
    follow_up: str = Field(..., description="Tracked follow-up task with SLA")
    follow_up_details: Dict[str, Any] = Field(..., description="Structured follow-up attributes")
    escalation: str = Field(..., description="Escalation status or hierarchy")
    escalation_required: bool = Field(..., description="Whether immediate clinical escalation was triggered")
    language_status: str = Field(..., description="Language resolution status")
    language_details: str = Field(..., description="Language compatibility summary")


class WhatChangedAndWhy(BaseModel):
    """Structured divergence summary between Baseline and Resource-Aware methods."""
    changed: bool = Field(..., description="Whether resource-aware diverged from textbook baseline")
    baseline_rec: str = Field(..., description="Textbook baseline recommendation")
    resource_aware_rec: str = Field(..., description="Resource-aware selected care option")
    reason_summary: str = Field(..., description="Readable explanation of change or equivalence")
    constraint_factors: List[str] = Field(..., description="Specific constraint causes")


class DetailedCaseComparisonResponse(BaseModel):
    """Full side-by-side comparison payload for the SAME case."""
    case_id: str = Field(..., description="Unique synthetic case identifier")
    condition: str = Field(..., description="Clinical condition")
    site_id: str = Field(..., description="Facility identifier")
    site_name: str = Field(..., description="Facility display name")
    urgency: str = Field(..., description="Clinical urgency level")
    patient_language: str = Field(..., description="Patient primary language")
    baseline: BaselinePanelData
    resource_aware: ResourceAwarePanelData
    what_changed_and_why: WhatChangedAndWhy
    governance_notice: str = Field(
        default="Decision-support prototype — clinician sign-off required.",
        description="Clinical governance disclaimer",
    )
    synthetic_data_notice: str = Field(
        default="Synthetic data only — no real patient data.",
        description="Data policy notice",
    )


class CaseListItem(BaseModel):
    """Brief metadata for case selector bar."""
    case_id: str
    condition: str
    site_id: str
    site_name: str
    urgency: str
    patient_language: str
    changed: bool
    baseline_feasible: bool
    resource_aware_ladder_level: str


def _get_cases_and_sites():
    """Load synthetic cases and service registry sites."""
    if not CASES_FILE.is_file():
        raise HTTPException(status_code=500, detail="Synthetic cases data file missing.")
    if not SERVICES_FILE.is_file():
        raise HTTPException(status_code=500, detail="Service registry data file missing.")

    with open(CASES_FILE, "r", encoding="utf-8") as f:
        cases = [PatientCase(**c) for c in json.load(f).get("cases", [])]
    with open(SERVICES_FILE, "r", encoding="utf-8") as f:
        sites = {s["site_id"]: ServiceSite(**s) for s in json.load(f).get("sites", [])}

    return cases, sites


@router.get("/summary", response_model=ComparisonSummaryMetrics)
def get_comparison_summary() -> ComparisonSummaryMetrics:
    """Return aggregated evaluation metrics comparing baseline vs resource-aware across all 40 cases.

    Returns:
    - Baseline feasibility %
    - Resource-aware feasibility %
    - High-priority follow-up coverage %
    - Language mismatch detection count and %
    - Immediate clinical escalation count and %
    """
    if SUMMARY_FILE.is_file():
        try:
            with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ComparisonSummaryMetrics(**data)
        except Exception:
            pass

    # Fallback to dynamic computation
    runner = ComparisonRunner()
    run_result = runner.run_all()
    return run_result.metrics


@router.get("/cases", response_model=List[CaseListItem])
def list_comparison_cases() -> List[CaseListItem]:
    """Return all 40 synthetic cases with comparison flags for the UI case selector."""
    cases, sites = _get_cases_and_sites()
    protocol_engine = get_protocol_engine()
    baseline_engine = TextbookBaselineEngine(protocol_engine)

    items: List[CaseListItem] = []
    for c in cases:
        site = sites.get(c.site_id)
        site_name = site.site_name if site else c.site_id
        protocol = protocol_engine.get_protocol(c.condition)
        if not protocol:
            continue

        comp = compare_single_case(
            case=c,
            site=site,
            protocol=protocol,
            baseline_engine=baseline_engine,
            clinician_languages=["en"],
        )

        items.append(
            CaseListItem(
                case_id=c.case_id,
                condition=c.condition,
                site_id=c.site_id,
                site_name=site_name,
                urgency=c.urgency.upper() if isinstance(c.urgency, str) else c.urgency.value.upper(),
                patient_language=c.patient_language,
                changed=comp.changed_recommendation,
                baseline_feasible=comp.baseline_feasible,
                resource_aware_ladder_level=comp.resource_aware_ladder_level or "preferred",
            )
        )

    return items


@router.get("/compare/{case_id}", response_model=DetailedCaseComparisonResponse)
def get_case_comparison(case_id: str) -> DetailedCaseComparisonResponse:
    """Return full side-by-side comparison payload for the SAME synthetic case.

    Guarantees:
    - Left Panel (Baseline) and Right Panel (Resource-Aware) evaluate the exact same case.
    - Full breakdown of resources ignored, follow-up, language, and feasibility.
    - Bottom 'What changed and why?' comparison.
    """
    cases, sites = _get_cases_and_sites()
    case = next((c for c in cases if c.case_id == case_id), None)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found in synthetic case dataset.",
        )

    site = sites.get(case.site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site '{case.site_id}' for case '{case_id}' not found in service registry.",
        )

    protocol_engine = get_protocol_engine()
    protocol = protocol_engine.get_protocol(case.condition)
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clinical protocol for condition '{case.condition}' not found.",
        )

    clin_langs = ["en"]
    baseline_engine = TextbookBaselineEngine(protocol_engine)

    # 1. Evaluate baseline
    baseline_output = baseline_engine.generate_recommendation(case.model_dump())
    baseline_rec = baseline_output.get("recommendation", protocol.textbook_recommendation)
    eval_pref = evaluate_option_feasibility(
        ladder_level="preferred",
        option=protocol.recommendation_ladder.preferred,
        site=site,
        travel_constraints=case.travel_constraints,
    )
    baseline_feasible = eval_pref.feasible

    # Baseline resources ignored list
    resources_ignored = [
        "Local equipment stock (e.g. ECG, Doppler, Glucometer, Point-of-care lab analyzers)",
        "Specialist physician coverage & physical onsite availability",
        "Medication inventory & cold-chain refrigerated storage requirements",
        "Road infrastructure & emergency transport ambulance availability",
        "Teleconsultation data bandwidth & digital connectivity stability",
        "Patient language compatibility & trained interpreter availability",
        "Follow-up task ownership assignment, SLA due date & escalation path",
    ]

    baseline_followup_str = (
        f"Untracked disposition (routine interval: {protocol.follow_up_interval or 'unspecified'}; "
        "no named human owner assigned, no deterministic due date calculated, no escalation path defined)"
    )

    baseline_language_str = (
        f"Ignored (Patient language '{case.patient_language}' not validated against clinician language '{clin_langs[0]}'; "
        "interpreter needs completely bypassed)"
    )

    if baseline_feasible:
        baseline_feasibility_reason = (
            f"The textbook recommendation happens to be feasible at {site.site_name} because all required "
            "equipment, medications, and specialist staff exist at this facility tier."
        )
    else:
        blocked_reasons = eval_pref.blocking_reasons if eval_pref.blocking_reasons else ["facility resource deficit"]
        baseline_feasibility_reason = (
            f"Textbook recommendation is NOT feasible at {site.site_name}. Deficits: {'; '.join(blocked_reasons)}."
        )

    # 2. Evaluate Resource-Aware
    ra_result = evaluate_case_constraints(
        case=case,
        protocol=protocol,
        site=site,
        clinician_languages=clin_langs,
    )
    selected_option = ra_result.selected_option or protocol.recommendation_ladder.escalate_only.option
    ladder_level = ra_result.selected_ladder_level or "escalate_only"

    # Follow-up
    followup_task = create_followup_from_evaluation(
        result=ra_result,
        case=case,
        protocol=protocol,
    )
    escalation_path_str = " -> ".join(followup_task.escalation_path) if followup_task.escalation_path else "None"
    ra_followup_str = (
        f"Tracked task (Owner: {followup_task.owner}, SLA Due: {followup_task.due_at}, "
        f"Escalation Path: {escalation_path_str})"
    )

    # Language
    lang_profile = resolve_language(
        patient_language=case.patient_language,
        clinician_languages=clin_langs,
        interpreter_languages=site.interpreter_languages,
        interpreter_available=bool(site.interpreter_languages),
        preferred_language=case.language_profile.preferred_language if case.language_profile else None,
    )
    lang_status_str = lang_profile.language_status.value

    if lang_profile.language_status == LanguageStatus.SUPPORTED:
        lang_details = f"Direct communication supported ({lang_profile.selected_language or case.patient_language})."
    elif lang_profile.language_status == LanguageStatus.REQUIRES_INTERPRETER:
        lang_details = (
            f"Interpreter required: Patient speaks {lang_profile.patient_language}, clinician speaks "
            f"{clin_langs[0]}. Verified interpreter available at facility."
        )
    else:
        lang_details = (
            f"Language escalation required: Patient speaks {lang_profile.patient_language}, no interpreter "
            "available locally."
        )

    if ra_result.decision == "ESCALATE_IMMEDIATELY":
        ra_feasibility_details = (
            "All local care options blocked due to critical equipment/specialist deficits. "
            "Immediate operational escalation triggered."
        )
        ra_status = "ESCALATE IMMEDIATELY"
    else:
        ra_feasibility_details = (
            f"Care option verified 100% feasible against {site.site_name} verified equipment, "
            "medications, and staff capabilities."
        )
        ra_status = "FEASIBLE"

    # 3. Construct "What changed and why?"
    changed = (ladder_level != "preferred") or (not ra_result.feasible)
    constraint_factors: List[str] = []

    if changed:
        # Collect blocked reasons from higher rungs
        preferred_blocks = ra_result.blocked_options.get("preferred", [])
        for pb in preferred_blocks:
            constraint_factors.append(pb)
        
        alt_blocks = ra_result.blocked_options.get("resource_adapted_alternative", [])
        for ab in alt_blocks:
            constraint_factors.append(ab)

        if not constraint_factors:
            constraint_factors.append("Facility constraint deficit forced adaptation")

        reason_summary = " + ".join(constraint_factors)
    else:
        reason_summary = (
            "No change required: All textbook guideline requirements (equipment, medications, "
            "specialist coverage, cold chain) are confirmed available at this facility."
        )

    return DetailedCaseComparisonResponse(
        case_id=case.case_id,
        condition=case.condition,
        site_id=case.site_id,
        site_name=site.site_name,
        urgency=case.urgency.upper() if isinstance(case.urgency, str) else case.urgency.value.upper(),
        patient_language=case.patient_language,
        baseline=BaselinePanelData(
            label="TEXTBOOK / BASELINE METHOD",
            recommendation=baseline_rec,
            resources_ignored=resources_ignored,
            follow_up=baseline_followup_str,
            language=baseline_language_str,
            feasibility=baseline_feasible,
            feasibility_status="FEASIBLE" if baseline_feasible else "NOT FEASIBLE",
            feasibility_reason=baseline_feasibility_reason,
        ),
        resource_aware=ResourceAwarePanelData(
            label="RESOURCE-AWARE METHOD",
            selected_option=selected_option,
            ladder_level=ladder_level,
            feasibility=ra_result.feasible,
            feasibility_status=ra_status,
            feasibility_details=ra_feasibility_details,
            reason_trail=ra_result.reason_trail,
            blocked_options=ra_result.blocked_options,
            follow_up=ra_followup_str,
            follow_up_details={
                "follow_up_id": followup_task.follow_up_id,
                "owner": followup_task.owner,
                "due_at": followup_task.due_at,
                "escalation_path": followup_task.escalation_path,
                "urgency": followup_task.urgency,
            },
            escalation="Immediate clinical escalation required" if ra_result.escalation_required else "Standard SLA path",
            escalation_required=ra_result.escalation_required,
            language_status=lang_status_str,
            language_details=lang_details,
        ),
        what_changed_and_why=WhatChangedAndWhy(
            changed=changed,
            baseline_rec=baseline_rec,
            resource_aware_rec=selected_option,
            reason_summary=reason_summary,
            constraint_factors=constraint_factors,
        ),
        governance_notice="Decision-support prototype — clinician sign-off required.",
        synthetic_data_notice="Synthetic data only — no real patient data.",
    )
