"""FastAPI routes for multilingual language catalogs, messages, and localized evaluations.

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
from src.language.messages import get_all_messages, get_message, list_supported_languages
from src.language.models import LanguageProfile, LanguageStatus
from src.language.resolver import resolve_language
from src.language.translator import translate_reason_trail
from src.models.operational_models import PatientCase, ServiceSite
from src.protocol_engine.protocol_engine import ProtocolEngine

router = APIRouter(tags=["Multilingual Language Layer"])

CASES_FILE = PROJECT_ROOT / "data" / "cases" / "synthetic_cases.json"
SERVICES_FILE = PROJECT_ROOT / "data" / "services" / "service_registry.json"


class EvaluationRequest(BaseModel):
    """Payload to evaluate care options with language localization."""
    case_id: str = Field(..., description="Synthetic patient case ID (e.g. 'SYNTH-CASE-001')")
    protocol_id: Optional[str] = Field(None, description="Optional protocol ID; inferred from condition if omitted")
    lang: str = Field(default="en", description="Display language code ('en' or 'ta')")
    clinician_languages: Optional[List[str]] = Field(
        default=None,
        description="Languages directly spoken by treating clinician (default: ['en'])"
    )


class LocalizedEvaluationResponse(BaseModel):
    """Localized evaluation output with safety communication alerts."""
    case_id: str
    protocol_id: str
    lang: str
    selected_option: Optional[str]
    selected_ladder_level: Optional[str]
    feasible: bool
    decision: str
    reason_trail: List[str]
    blocked_options: Dict[str, List[str]]
    escalation_required: bool
    escalation_reason: Optional[str]
    fallback_owner_required: bool
    language_status: LanguageStatus
    communication_supported: bool
    communication_warning: Optional[str]
    governance_notice: str
    synthetic_data_notice: str


@router.get(
    "/languages",
    response_model=List[Dict[str, Any]],
    summary="List all supported system languages",
)
def get_supported_languages() -> List[Dict[str, Any]]:
    """Return catalog of supported languages (English 'en' and Tamil 'ta')."""
    return list_supported_languages()


@router.get(
    "/languages/{language_code}/messages",
    response_model=Dict[str, str],
    summary="Retrieve localized message dictionary for a language",
)
def get_language_messages(language_code: str) -> Dict[str, str]:
    """Retrieve the flat message catalog for UI and system localization.

    Supported codes: 'en', 'ta'. Returns 404 for unsupported language codes.
    """
    code = language_code.strip().lower()
    if code not in ("en", "ta"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language '{language_code}' is not supported. Supported codes are 'en' and 'ta'.",
        )
    return get_all_messages(code)


@router.get(
    "/cases",
    response_model=List[Dict[str, Any]],
    summary="Retrieve all synthetic patient cases for evaluation",
)
def get_synthetic_cases() -> List[Dict[str, Any]]:
    """Return all 40 generated synthetic patient cases."""
    if not CASES_FILE.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthetic cases file not found.",
        )
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("cases", [])


@router.post(
    "/evaluate",
    response_model=LocalizedEvaluationResponse,
    summary="Evaluate care options with language localization and safety overlay",
)
def evaluate_case_localized(payload: EvaluationRequest) -> LocalizedEvaluationResponse:
    """Evaluate patient case against protocol with English or Tamil reason trails.

    Safety Guarantee: If communication cannot be safely supported (clinician and interpreter
    fail to support patient language), the recommendation is NEVER silently presented as valid.
    Instead, language_status = 'LANGUAGE_ESCALATION_REQUIRED' with explicit safety warning.
    """
    target_lang = payload.lang.strip().lower()
    if target_lang not in ("en", "ta"):
        target_lang = "en"

    # 1. Load patient case
    if not CASES_FILE.is_file():
        raise HTTPException(status_code=500, detail="Synthetic cases data missing.")
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        cases_data = json.load(f).get("cases", [])

    matched_case = next((c for c in cases_data if c["case_id"] == payload.case_id), None)
    if not matched_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{payload.case_id}' not found.",
        )
    case_obj = PatientCase(**matched_case)

    # 2. Load facility site
    if not SERVICES_FILE.is_file():
        raise HTTPException(status_code=500, detail="Service registry data missing.")
    with open(SERVICES_FILE, "r", encoding="utf-8") as f:
        sites_data = json.load(f).get("sites", [])

    matched_site = next((s for s in sites_data if s["site_id"] == case_obj.site_id), None)
    if not matched_site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility site '{case_obj.site_id}' not found.",
        )
    site_obj = ServiceSite(**matched_site)

    # 3. Load protocol
    proto_engine = ProtocolEngine()
    if payload.protocol_id:
        protocol_obj = proto_engine.get_protocol_by_id(payload.protocol_id)
        if not protocol_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Protocol '{payload.protocol_id}' not found.",
            )
    else:
        protocol_obj = proto_engine.get_protocol(case_obj.condition)
        if not protocol_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No protocol found for condition '{case_obj.condition}'.",
            )

    # 4. Clinician languages
    clin_langs = payload.clinician_languages or ["en"]

    # 5. Evaluate options through constraint engine
    result: ConstraintEngineResult = evaluate_case_constraints(
        case=case_obj,
        protocol=protocol_obj,
        site=site_obj,
        clinician_languages=clin_langs,
    )

    # 6. Safety check: Language communication safety
    comm_supported = result.language_status in (
        LanguageStatus.SUPPORTED,
        LanguageStatus.REQUIRES_INTERPRETER,
    )
    comm_warning = None
    if not comm_supported:
        comm_warning = get_message("communication_unsupported", lang=target_lang)

    # 7. Localize reason trail
    localized_trail = translate_reason_trail(result.reason_trail, lang=target_lang)

    return LocalizedEvaluationResponse(
        case_id=result.case_id,
        protocol_id=result.protocol_id,
        lang=target_lang,
        selected_option=result.selected_option,
        selected_ladder_level=result.selected_ladder_level,
        feasible=result.feasible,
        decision=result.decision,
        reason_trail=localized_trail,
        blocked_options=result.blocked_options,
        escalation_required=result.escalation_required,
        escalation_reason=result.escalation_reason,
        fallback_owner_required=result.fallback_owner_required,
        language_status=result.language_status,
        communication_supported=comm_supported,
        communication_warning=comm_warning,
        governance_notice=get_message("prototype_disclaimer", lang=target_lang),
        synthetic_data_notice=get_message("synthetic_data_policy", lang=target_lang),
    )
