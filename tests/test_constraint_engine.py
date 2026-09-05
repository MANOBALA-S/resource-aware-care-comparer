"""Tests for the Resource Constraint Engine feasibility evaluation and ladder traversal.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from typing import Dict
import pytest

from src.constraint_engine.feasibility import (
    evaluate_case_constraints,
    evaluate_language_safety,
    evaluate_option_feasibility,
)
from src.constraint_engine.models import (
    LanguageStatus,
    ResourceStatus,
)
from src.data_generation.case_generator import load_service_registry_sites
from src.models.operational_models import (
    ConnectivityQuality,
    PatientCase,
    PopulationGroup,
    ServiceSite,
    TravelConstraints,
)
from src.protocol_engine.protocol_engine import get_protocol_engine


@pytest.fixture
def sites() -> Dict[str, ServiceSite]:
    """Loaded dictionary of ServiceSite models."""
    raw_sites = load_service_registry_sites()
    return {sid: ServiceSite.model_validate(data) for sid, data in raw_sites.items()}


@pytest.fixture
def protocol_engine():
    """Default protocol engine instance."""
    return get_protocol_engine()


def test_preferred_option_feasible_at_tertiary_center(sites, protocol_engine) -> None:
    """Test 1: Preferred option is feasible when site possesses all required resources."""
    tertiary_site = sites["SITE-001"]
    protocol = protocol_engine.get_protocol("condition_alpha")
    assert protocol is not None

    tc = TravelConstraints(
        next_tier_site="SITE-001",
        travel_distance_km=0.0,
        travel_time_minutes=0,
        transport_available=True,
        connectivity_quality=ConnectivityQuality.EXCELLENT,
        follow_up_teleconsult_possible=True,
        patient_language="en",
        preferred_language="en",
        interpreter_required=False,
    )

    case = PatientCase(
        case_id="TEST-CASE-TERTIARY",
        condition="condition_alpha",
        age_band="36-50",
        population_group=PopulationGroup.URBAN,
        site_id="SITE-001",
        patient_language="en",
        urgency=protocol.urgency,
        travel_constraints=tc,
        connectivity="100 Mbps fiber",
        synthetic=True,
    )

    result = evaluate_case_constraints(case=case, protocol=protocol, site=tertiary_site)

    assert result.decision == "SELECT_OPTION"
    assert result.feasible is True
    assert result.selected_ladder_level == "preferred"
    assert result.selected_option == protocol.recommendation_ladder.preferred.option
    assert result.escalation_required is False
    assert len(result.reason_trail) > 0
    assert any("Preferred': FEASIBLE" in step for step in result.reason_trail)


def test_preferred_unavailable_and_adapted_option_feasible(sites, protocol_engine) -> None:
    """Test 2: Preferred option is blocked (no imaging/cold chain), adapted option is selected."""
    # SITE-003 has basic lab and oral stock, but no Doppler US and no cold-chain
    chc_site = sites["SITE-003"]
    protocol = protocol_engine.get_protocol("condition_alpha")
    assert protocol is not None

    tc = TravelConstraints(
        next_tier_site="SITE-005",
        travel_distance_km=24.0,
        travel_time_minutes=50,
        transport_available=True,
        connectivity_quality=ConnectivityQuality.GOOD,
        follow_up_teleconsult_possible=True,
        patient_language="ta",
        preferred_language="ta",
        interpreter_required=False,
    )

    case = PatientCase(
        case_id="TEST-CASE-ADAPTED",
        condition="condition_alpha",
        age_band="51-65",
        population_group=PopulationGroup.RURAL,
        site_id="SITE-003",
        patient_language="ta",
        urgency=protocol.urgency,
        travel_constraints=tc,
        connectivity="4G mobile broadband",
        synthetic=True,
    )

    result = evaluate_case_constraints(case=case, protocol=protocol, site=chc_site)

    assert result.decision == "SELECT_OPTION"
    assert result.feasible is True
    # Preferred must be blocked due to cold chain / same day imaging
    assert "preferred" in result.blocked_options
    # Resource adapted alternative must be selected
    assert result.selected_ladder_level == "resource_adapted_alternative"
    assert result.selected_option == protocol.recommendation_ladder.resource_adapted_alternative.option
    assert any("Preferred': BLOCKED" in step for step in result.reason_trail)
    assert any("Resource Adapted Alternative': FEASIBLE" in step for step in result.reason_trail)


def test_preferred_and_adapted_blocked_fallback_feasible(sites, protocol_engine) -> None:
    """Test 3: Preferred and adapted blocked (no imaging, no cold chain, 2G connectivity), fallback selected."""
    # SITE-002 has no imaging, no cold-chain, and intermittent 2G (blocks adapted option's teleconsultation)
    subcenter_site = sites["SITE-002"]
    protocol = protocol_engine.get_protocol("condition_alpha")
    assert protocol is not None

    tc = TravelConstraints(
        next_tier_site="SITE-005",
        travel_distance_km=18.5,
        travel_time_minutes=80,
        transport_available=False,
        connectivity_quality=ConnectivityQuality.POOR,
        follow_up_teleconsult_possible=False,
        patient_language="ta",
        preferred_language="ta",
        interpreter_required=False,
    )

    case = PatientCase(
        case_id="TEST-CASE-FALLBACK",
        condition="condition_alpha",
        age_band="65+",
        population_group=PopulationGroup.RURAL,
        site_id="SITE-002",
        patient_language="ta",
        urgency=protocol.urgency,
        travel_constraints=tc,
        connectivity="Intermittent 2G cellular link",
        synthetic=True,
    )

    result = evaluate_case_constraints(case=case, protocol=protocol, site=subcenter_site)

    assert result.decision == "SELECT_OPTION"
    assert result.feasible is True
    assert "preferred" in result.blocked_options
    assert "resource_adapted_alternative" in result.blocked_options
    assert result.selected_ladder_level == "minimum_safe_fallback"
    assert result.selected_option == protocol.recommendation_ladder.minimum_safe_fallback.option


def test_transport_unavailable_blocks_transfer(sites, protocol_engine) -> None:
    """Test 7: Lack of transport explicitly blocks referral/transfer option."""
    subcenter_site = sites["SITE-002"]  # transport_available = False
    protocol = protocol_engine.get_protocol("condition_gamma")
    assert protocol is not None

    tc = TravelConstraints(
        next_tier_site="SITE-005",
        travel_distance_km=30.0,
        travel_time_minutes=90,
        transport_available=False,  # Patient also has no transport
        connectivity_quality=ConnectivityQuality.POOR,
        follow_up_teleconsult_possible=False,
        patient_language="ta",
        preferred_language="ta",
        interpreter_required=False,
    )

    # Evaluate option that requires transport
    eval_res = evaluate_option_feasibility(
        ladder_level="preferred",
        option=protocol.recommendation_ladder.preferred,
        site=subcenter_site,
        travel_constraints=tc,
    )

    assert eval_res.feasible is False
    assert any("transport" in r.lower() for r in eval_res.blocking_reasons)


def test_connectivity_unavailable_blocks_remote_monitoring(sites, protocol_engine) -> None:
    """Test 8: Poor connectivity blocks options requiring remote review or teleconsultation."""
    subcenter_site = sites["SITE-002"]  # 128 kbps
    protocol = protocol_engine.get_protocol("condition_epsilon")
    assert protocol is not None

    tc = TravelConstraints(
        next_tier_site="SITE-005",
        travel_distance_km=18.0,
        travel_time_minutes=40,
        transport_available=True,
        connectivity_quality=ConnectivityQuality.POOR,
        follow_up_teleconsult_possible=False,
        patient_language="ta",
        preferred_language="ta",
        interpreter_required=False,
    )

    eval_res = evaluate_option_feasibility(
        ladder_level="preferred",
        option=protocol.recommendation_ladder.preferred,
        site=subcenter_site,
        travel_constraints=tc,
    )

    assert eval_res.feasible is False
    assert any("connectivity" in r.lower() for r in eval_res.blocking_reasons)


def test_required_medication_unavailable(sites, protocol_engine) -> None:
    """Test 9: Medication stockout at the site blocks options requiring pharmaceutical stocks."""
    # Create an austere site with empty medication stock
    austere_site = ServiceSite(
        site_id="SITE-AUSTERE",
        region="Test Region",
        site_name="Austere Test Clinic",
        clinic_tier="Sub-Center",
        equipment=[],
        medication_stock=[],  # Stockout
        cold_chain_available=False,
        specialists=[],
        specialist_availability_hours="None",
        transport_available=False,
        teleconsult_bandwidth="128 kbps",
        supported_languages=["ta"],
        interpreter_languages=[],
        operating_hours="Mon-Fri",
        registry_timestamp="2026-09-01T00:00:00Z",
    )

    protocol = protocol_engine.get_protocol("condition_beta")
    assert protocol is not None

    tc = TravelConstraints(
        next_tier_site="SITE-001",
        travel_distance_km=50.0,
        travel_time_minutes=120,
        transport_available=False,
        connectivity_quality=ConnectivityQuality.POOR,
        follow_up_teleconsult_possible=False,
        patient_language="ta",
        preferred_language="ta",
        interpreter_required=False,
    )

    # Minimum safe fallback requires medication_stock
    eval_res = evaluate_option_feasibility(
        ladder_level="minimum_safe_fallback",
        option=protocol.recommendation_ladder.minimum_safe_fallback,
        site=austere_site,
        travel_constraints=tc,
    )

    assert eval_res.feasible is False
    assert any("medication" in r.lower() for r in eval_res.blocking_reasons)


def test_specialist_unavailable_within_timeframe(sites, protocol_engine) -> None:
    """Test 10: Lack of on-site or teleconsultation specialist blocks specialist-dependent options."""
    kiosk_site = sites["SITE-006"]  # Urban kiosk: no local specialists
    protocol = protocol_engine.get_protocol("condition_alpha")
    assert protocol is not None

    tc = TravelConstraints(
        next_tier_site="SITE-001",
        travel_distance_km=8.0,
        travel_time_minutes=20,
        transport_available=True,
        connectivity_quality=ConnectivityQuality.EXCELLENT,
        follow_up_teleconsult_possible=True,
        patient_language="en",
        preferred_language="en",
        interpreter_required=False,
    )

    eval_res = evaluate_option_feasibility(
        ladder_level="preferred",
        option=protocol.recommendation_ladder.preferred,
        site=kiosk_site,
        travel_constraints=tc,
    )

    assert eval_res.feasible is False
    assert any("specialist" in r.lower() for r in eval_res.blocking_reasons)
