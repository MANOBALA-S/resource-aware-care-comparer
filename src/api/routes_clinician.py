"""FastAPI routes for the Clinician / Teleconsult Screen.

Provides dedicated endpoints for reviewing synthetic patient cases, inspecting local facility
resources, receiving resource-aware care recommendations, reason trails, and follow-up tracking.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.config import PROJECT_ROOT
from src.constraint_engine.feasibility import evaluate_case_constraints
from src.constraint_engine.models import ConstraintEngineResult
from src.followup.tracker import create_followup_from_evaluation
from src.language.messages import get_message
from src.language.models import LanguageStatus
from src.language.resolver import resolve_language
from src.language.translator import translate_reason_line, translate_reason_trail
from src.models.operational_models import PatientCase, ServiceSite
from src.protocol_engine.protocol_engine import ProtocolEngine

router = APIRouter(tags=["Clinician Screen"])

CASES_FILE = PROJECT_ROOT / "data" / "cases" / "synthetic_cases.json"
SERVICES_FILE = PROJECT_ROOT / "data" / "services" / "service_registry.json"


class SiteResourcesSummary(BaseModel):
    """Structured facility resource capabilities for UI display."""
    site_id: str
    site_name: str
    region: str
    clinic_tier: str
    equipment: List[str]
    medication_stock: List[str]
    specialists: List[str]
    transport_available: bool
    connectivity: str
    cold_chain_available: bool
    supported_languages: List[str]
    interpreter_languages: List[str]


class PatientCaseDetailsResponse(BaseModel):
    """Patient case profile combined with local facility resources."""
    case_id: str
    condition: str
    age_band: str
    population_group: str
    urgency: str
    patient_language: str
    site_id: str
    site_name: str
    connectivity: str
    site_resources: SiteResourcesSummary
    governance_notice: str
    synthetic_data_notice: str


class ReasonStepItem(BaseModel):
    """Individual transparent reason step with status indicator symbol."""
    status: str = Field(..., description="'available', 'unavailable', 'blocked', or 'selected'")
    symbol: str = Field(..., description="'✓', '✗', or '★'")
    text: str = Field(..., description="Human-readable decision step")
    category: str = Field(..., description="'equipment', 'medication', 'specialist', 'transport', 'connectivity', 'decision'")


class FollowUpSummary(BaseModel):
    """Follow-up task disposition and SLA tracking."""
    follow_up_id: str
    owner: str
    due_at: str
    escalation_path: List[str]
    status: str
    urgency: str
    description: str


class ClinicianRecommendationResponse(BaseModel):
    """Complete clinician teleconsult screen evaluation payload."""
    case_id: str
    condition: str
    urgency: str
    site_id: str
    site_name: str
    lang: str

    # Patient Section Data
    patient_summary: Dict[str, Any]

    # Resource Section Data
    site_resources: SiteResourcesSummary

    # Recommendation Section Data
    selected_care_option: str
    ladder_level: str
    feasible: bool
    decision: str
    reason_trail: List[str]
    reason_steps: List[ReasonStepItem]
    blocked_options: Dict[str, List[str]]
    escalation_required: bool
    escalation_reason: Optional[str]

    # Follow-Up Section Data
    follow_up: FollowUpSummary

    # Safety Alerts
    escalate_immediately: bool
    language_escalation_required: bool
    requires_interpreter: bool
    safety_banner_type: Optional[str] = Field(
        None, description="'ESCALATE_IMMEDIATELY', 'LANGUAGE_ESCALATION_REQUIRED', or None"
    )
    safety_banner_message: Optional[str] = None

    # Governance Disclaimers
    governance_notice: str
    synthetic_data_notice: str


def _load_case(case_id: str) -> PatientCase:
    """Helper to locate and deserialize a synthetic patient case."""
    if not CASES_FILE.is_file():
        raise HTTPException(status_code=500, detail="Synthetic cases data file missing.")
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        cases_raw = json.load(f).get("cases", [])
    matched = next((c for c in cases_raw if c["case_id"] == case_id), None)
    if not matched:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found.")
    return PatientCase(**matched)


def _load_site(site_id: str) -> ServiceSite:
    """Helper to locate and deserialize a service facility profile."""
    if not SERVICES_FILE.is_file():
        raise HTTPException(status_code=500, detail="Service registry data file missing.")
    with open(SERVICES_FILE, "r", encoding="utf-8") as f:
        sites_raw = json.load(f).get("sites", [])
    matched = next((s for s in sites_raw if s["site_id"] == site_id), None)
    if not matched:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Site '{site_id}' not found.")
    return ServiceSite(**matched)


def _build_site_summary(site: ServiceSite) -> SiteResourcesSummary:
    """Construct structured SiteResourcesSummary."""
    return SiteResourcesSummary(
        site_id=site.site_id,
        site_name=site.site_name,
        region=site.region,
        clinic_tier=site.clinic_tier.value if hasattr(site.clinic_tier, "value") else str(site.clinic_tier),
        equipment=list(site.equipment),
        medication_stock=list(site.medication_stock),
        specialists=list(site.specialists),
        transport_available=site.transport_available,
        connectivity=site.teleconsult_bandwidth or "Standard teleconsult connection",
        cold_chain_available=site.cold_chain_available,
        supported_languages=list(site.supported_languages),
        interpreter_languages=list(site.interpreter_languages),
    )


@router.get(
    "/cases/{case_id}",
    response_model=PatientCaseDetailsResponse,
    summary="Retrieve synthetic patient case and local facility resources",
)
def get_case_details(case_id: str) -> PatientCaseDetailsResponse:
    """Retrieve complete patient case profile paired with local site capabilities."""
    case = _load_case(case_id)
    site = _load_site(case.site_id)
    site_summary = _build_site_summary(site)

    return PatientCaseDetailsResponse(
        case_id=case.case_id,
        condition=case.condition,
        age_band=case.age_band,
        population_group=case.population_group.value if hasattr(case.population_group, "value") else str(case.population_group),
        urgency=case.urgency.value if hasattr(case.urgency, "value") else str(case.urgency),
        patient_language=case.patient_language,
        site_id=case.site_id,
        site_name=site.site_name,
        connectivity=case.connectivity,
        site_resources=site_summary,
        governance_notice="Decision-support prototype — clinician sign-off required.",
        synthetic_data_notice="Synthetic data only — no real patient data.",
    )


@router.post(
    "/recommendations/{case_id}",
    response_model=ClinicianRecommendationResponse,
    summary="Generate resource-aware recommendation for clinician review",
)
def generate_recommendation_for_clinician(
    case_id: str,
    lang: str = Query(default="en", description="Display language ('en' or 'ta')"),
    clinician_languages: Optional[List[str]] = Query(
        default=None, description="Languages spoken by remote clinician (default: ['en'])"
    ),
    simulate_exhaustion: bool = Query(
        default=False, description="Simulate option exhaustion for testing immediate escalation alert"
    ),
) -> ClinicianRecommendationResponse:
    """Evaluate patient case and return transparent recommendation, reason trail, and follow-up.

    Supports dynamic language switching between English and Tamil with explicit safety alerts:
    - ESCALATE IMMEDIATELY when all local tiers are blocked.
    - LANGUAGE ESCALATION REQUIRED when patient language cannot be safely communicated.
    """
    target_lang = lang.strip().lower()
    if target_lang not in ("en", "ta"):
        target_lang = "en"

    case = _load_case(case_id)
    site = _load_site(case.site_id)
    clin_langs = clinician_languages or ["en"]

    proto_engine = ProtocolEngine()
    protocol = proto_engine.get_protocol(case.condition)
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No protocol found for condition '{case.condition}'.",
        )

    # Constraint engine evaluation
    result: ConstraintEngineResult = evaluate_case_constraints(
        case=case,
        protocol=protocol,
        site=site,
        clinician_languages=clin_langs,
    )

    # Optional testing override for option exhaustion
    if simulate_exhaustion:
        result.feasible = False
        result.decision = "ESCALATE_IMMEDIATELY"
        result.selected_ladder_level = "escalate_only"
        result.selected_option = protocol.recommendation_ladder.escalate_only.option
        result.escalation_required = True
        result.escalation_reason = (
            "Simulated exhaustion: All local care pathways blocked. Immediate clinical and operational escalation required."
        )

    # Follow-up task creation
    followup_task = create_followup_from_evaluation(
        result=result,
        case=case,
        protocol=protocol,
    )

    # Language resolution
    lang_profile = resolve_language(
        patient_language=case.patient_language,
        clinician_languages=clin_langs,
        interpreter_languages=site.interpreter_languages,
        interpreter_available=bool(site.interpreter_languages),
        preferred_language=case.language_profile.preferred_language if case.language_profile else None,
    )

    # Build transparent reason steps with ✓ / ✗ symbols
    reason_steps: List[ReasonStepItem] = []
    
    # 1. Clinician / Local Staffing
    reason_steps.append(
        ReasonStepItem(
            status="available",
            symbol="✓",
            text="Local clinician available" if target_lang == "en" else "உள்ளூர் மருத்துவர் கிடைக்கிறார்",
            category="staff",
        )
    )

    # 2. Specialist availability
    has_specialist = len(site.specialists) > 0
    if has_specialist:
        spec_text = f"Specialist coverage available ({', '.join(site.specialists[:2])})" if target_lang == "en" else f"நிபுணர் சேவை உள்ளது ({', '.join(site.specialists[:2])})"
        reason_steps.append(ReasonStepItem(status="available", symbol="✓", text=spec_text, category="specialist"))
    else:
        spec_text = "Specialist unavailable locally" if target_lang == "en" else "உள்ளூரில் நிபுணர் கிடைக்கவில்லை"
        reason_steps.append(ReasonStepItem(status="unavailable", symbol="✗", text=spec_text, category="specialist"))

    # 3. Transport availability
    if site.transport_available or case.travel_constraints.transport_available:
        trans_text = "Patient / facility transport available" if target_lang == "en" else "நோயாளி / மருத்துவமனை போக்குவரத்து வசதி உள்ளது"
        reason_steps.append(ReasonStepItem(status="available", symbol="✓", text=trans_text, category="transport"))
    else:
        trans_text = "Transport unavailable locally" if target_lang == "en" else "போக்குவரத்து வசதி கிடைக்கவில்லை"
        reason_steps.append(ReasonStepItem(status="unavailable", symbol="✗", text=trans_text, category="transport"))

    # 4. Connectivity
    has_stable_conn = case.travel_constraints.follow_up_teleconsult_possible
    if has_stable_conn:
        conn_text = "Stable connectivity verified" if target_lang == "en" else "நிலையான இணைய இணைப்பு உறுதிசெய்யப்பட்டது"
        reason_steps.append(ReasonStepItem(status="available", symbol="✓", text=conn_text, category="connectivity"))
    else:
        conn_text = "Connectivity limited or unstable" if target_lang == "en" else "இணைய இணைப்பு குறைவாக அல்லது நிலையற்றதாக உள்ளது"
        reason_steps.append(ReasonStepItem(status="unavailable", symbol="✗", text=conn_text, category="connectivity"))

    # 5. Cold chain
    if site.cold_chain_available:
        cc_text = "Cold chain refrigeration operational" if target_lang == "en" else "குளிர்பதன வசதி இயங்குகிறது"
        reason_steps.append(ReasonStepItem(status="available", symbol="✓", text=cc_text, category="equipment"))
    else:
        cc_text = "Cold chain refrigeration unavailable" if target_lang == "en" else "குளிர்பதன வசதி கிடைக்கவில்லை"
        reason_steps.append(ReasonStepItem(status="unavailable", symbol="✗", text=cc_text, category="equipment"))

    # 6. Selected tier
    selected_tier_name = result.selected_ladder_level or "escalate_only"
    if target_lang == "en":
        tier_label_map = {
            "preferred": "Preferred (Textbook Gold-Standard)",
            "resource_adapted_alternative": "Resource-Adapted Alternative",
            "minimum_safe_fallback": "Minimum-Safe Fallback",
            "escalate_only": "Immediate Emergency Escalation",
        }
        sel_text = f"Selected: {tier_label_map.get(selected_tier_name, selected_tier_name)}"
    else:
        tier_label_map_ta = {
            "preferred": "விருப்பமான சிகிச்சைத் தேர்வு (நிலையான நெறிமுறை)",
            "resource_adapted_alternative": "வளத்திற்கு ஏற்ற மாற்று வழி",
            "minimum_safe_fallback": "குறைந்தபட்ச பாதுகாப்பான வழி",
            "escalate_only": "உடனடி தீவிர மேலனுப்பல்",
        }
        sel_text = f"தேர்ந்தெடுக்கப்பட்டது: {tier_label_map_ta.get(selected_tier_name, selected_tier_name)}"
    
    reason_steps.append(
        ReasonStepItem(
            status="selected",
            symbol="★",
            text=sel_text,
            category="decision",
        )
    )

    # Localized reason trail
    localized_reason_trail = translate_reason_trail(result.reason_trail, lang=target_lang)

    # Safety alert states
    escalate_imm = (result.decision == "ESCALATE_IMMEDIATELY" or not result.feasible)
    lang_esc_req = (lang_profile.language_status == LanguageStatus.LANGUAGE_ESCALATION_REQUIRED)
    req_interpreter = (lang_profile.language_status == LanguageStatus.REQUIRES_INTERPRETER)

    safety_banner_type = None
    safety_banner_msg = None

    if escalate_imm:
        safety_banner_type = "ESCALATE_IMMEDIATELY"
        safety_banner_msg = (
            "ESCALATE IMMEDIATELY: All local care pathways blocked. Immediate transfer and specialist escalation required."
            if target_lang == "en"
            else "உடனடி தீவிர மேலனுப்பல் தேவை: அனைத்து உள்ளூர் சிகிச்சை வழிகளும் தடைபட்டுள்ளன. உடனடி இடமாற்றம் மற்றும் நிபுணர் மேலனுப்பல் தேவை."
        )
    elif lang_esc_req:
        safety_banner_type = "LANGUAGE_ESCALATION_REQUIRED"
        safety_banner_msg = (
            f"LANGUAGE ESCALATION REQUIRED: Patient language '{case.patient_language}' is unsupported by available clinicians and interpreters."
            if target_lang == "en"
            else f"மொழி அதிகரிப்பு தேவை: நோயாளியின் மொழி '{case.patient_language}' கிடைக்கக்கூடிய மருத்துவர்கள் மற்றும் மொழிபெயர்ப்பாளர்களால் ஆதரிக்கப்படவில்லை."
        )

    # Follow-up representation
    follow_up_summary = FollowUpSummary(
        follow_up_id=followup_task.follow_up_id,
        owner=followup_task.owner,
        due_at=followup_task.due_at,
        escalation_path=followup_task.escalation_path,
        status=followup_task.status.value,
        urgency=followup_task.urgency.value,
        description=followup_task.description,
    )

    patient_summary = {
        "case_id": case.case_id,
        "age_band": case.age_band,
        "population_group": case.population_group.value if hasattr(case.population_group, "value") else str(case.population_group),
        "condition": case.condition,
        "urgency": case.urgency.value if hasattr(case.urgency, "value") else str(case.urgency),
        "patient_language": case.patient_language,
        "site_id": case.site_id,
        "site_name": site.site_name,
    }

    return ClinicianRecommendationResponse(
        case_id=case.case_id,
        condition=case.condition,
        urgency=case.urgency.value if hasattr(case.urgency, "value") else str(case.urgency),
        site_id=case.site_id,
        site_name=site.site_name,
        lang=target_lang,
        patient_summary=patient_summary,
        site_resources=_build_site_summary(site),
        selected_care_option=result.selected_option or protocol.recommendation_ladder.escalate_only.option,
        ladder_level=selected_tier_name,
        feasible=result.feasible,
        decision=result.decision,
        reason_trail=localized_reason_trail,
        reason_steps=reason_steps,
        blocked_options=result.blocked_options,
        escalation_required=result.escalation_required,
        escalation_reason=result.escalation_reason,
        follow_up=follow_up_summary,
        escalate_immediately=escalate_imm,
        language_escalation_required=lang_esc_req,
        requires_interpreter=req_interpreter,
        safety_banner_type=safety_banner_type,
        safety_banner_message=safety_banner_msg,
        governance_notice=get_message("prototype_disclaimer", lang=target_lang),
        synthetic_data_notice=get_message("synthetic_data_policy", lang=target_lang),
    )
