"""Edge case test: Language barrier and translation safety triggers mandatory escalation.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import pytest

from src.constraint_engine.feasibility import (
    evaluate_case_constraints,
    evaluate_language_safety,
)
from src.constraint_engine.models import LanguageStatus
from src.models.operational_models import (
    ConnectivityQuality,
    PatientCase,
    PopulationGroup,
    ServiceSite,
    TravelConstraints,
)
from src.protocol_engine.protocol_engine import get_protocol_engine


def test_unsupported_language_triggers_language_escalation() -> None:
    """Test 6A: Patient speaking an unsupported language with no interpreter available

    MUST trigger LANGUAGE_ESCALATION_REQUIRED and escalation_required=True.
    The engine must NOT silently proceed.
    """
    protocol_engine = get_protocol_engine()
    protocol = protocol_engine.get_protocol("condition_delta")
    assert protocol is not None

    # Clinic supports only English and Tamil
    site = ServiceSite(
        site_id="SITE-ENGLISH-TAMIL",
        region="South",
        site_name="Standard Bilingual Clinic",
        clinic_tier="Primary Health Center",
        equipment=["manual_bp_cuff"],
        medication_stock=["oral_amlodipine"],
        cold_chain_available=False,
        specialists=[],
        specialist_availability_hours="None",
        transport_available=True,
        teleconsult_bandwidth="10 Mbps",
        supported_languages=["en", "ta"],
        interpreter_languages=["en", "ta"],
        operating_hours="Mon-Fri",
        registry_timestamp="2026-09-01T00:00:00Z",
    )

    tc = TravelConstraints(
        next_tier_site="SITE-001",
        travel_distance_km=15.0,
        travel_time_minutes=30,
        transport_available=True,
        connectivity_quality=ConnectivityQuality.GOOD,
        follow_up_teleconsult_possible=True,
        patient_language="bn",  # Bengali - unsupported by site & interpreter
        preferred_language="bn",
        interpreter_required=True,
    )

    case = PatientCase(
        case_id="TEST-CASE-LANG-MISMATCH",
        condition="condition_delta",
        age_band="51-65",
        population_group=PopulationGroup.RURAL,
        site_id="SITE-ENGLISH-TAMIL",
        patient_language="bn",
        urgency=protocol.urgency,
        travel_constraints=tc,
        connectivity="4G mobile broadband",
        synthetic=True,
    )

    # Clinician speaks English only
    result = evaluate_case_constraints(
        case=case,
        protocol=protocol,
        site=site,
        clinician_languages=["en"],
    )

    # Invariants for language safety:
    assert result.language_status == LanguageStatus.LANGUAGE_ESCALATION_REQUIRED
    assert result.escalation_required is True
    assert result.escalation_reason is not None
    assert "language escalation" in result.escalation_reason.lower()
    assert any("Language Safety ALERT" in step for step in result.reason_trail)
    assert any("is unsupported" in step for step in result.reason_trail)


def test_supported_interpreter_flags_requires_interpreter() -> None:
    """Test 6B: When patient language is not spoken directly by clinician but interpreter is available,

    engine returns REQUIRES_INTERPRETER without failing the consultation.
    """
    site_with_interpreters = ServiceSite(
        site_id="SITE-MULTILINGUAL",
        region="Metropolitan",
        site_name="Multilingual Hub Hospital",
        clinic_tier="Tertiary Hospital",
        equipment=["manual_bp_cuff"],
        medication_stock=["oral_amlodipine"],
        cold_chain_available=True,
        specialists=["cardiologist"],
        specialist_availability_hours="24/7",
        transport_available=True,
        teleconsult_bandwidth="100 Mbps",
        supported_languages=["en"],  # Staff only English
        interpreter_languages=["en", "ta", "hi", "ml"],  # Tamil interpreter available
        operating_hours="24/7",
        registry_timestamp="2026-09-01T00:00:00Z",
    )

    # Patient speaks Tamil, remote clinician speaks English only
    lang_eval = evaluate_language_safety(
        patient_language="ta",
        site=site_with_interpreters,
        clinician_languages=["en"],
    )

    assert lang_eval.status == LanguageStatus.REQUIRES_INTERPRETER
    assert lang_eval.interpreter_available is True
    assert "certified interpreter is available" in lang_eval.explanation.lower()
