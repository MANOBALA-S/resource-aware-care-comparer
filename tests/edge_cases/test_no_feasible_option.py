"""Edge case test: No feasible local option triggers immediate escalation.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import pytest

from src.constraint_engine.feasibility import evaluate_case_constraints
from src.models.operational_models import (
    ConnectivityQuality,
    PatientCase,
    PopulationGroup,
    ServiceSite,
    TravelConstraints,
)
from src.protocol_engine.protocol_engine import get_protocol_engine


def test_exhaustion_triggers_immediate_escalation() -> None:
    """Test 4: When preferred, adapted, and fallback tiers are all blocked,

    the engine MUST NOT return null, empty, or 'No recommendation'.
    It MUST return decision='ESCALATE_IMMEDIATELY', feasible=False,
    escalation_required=True, and fallback_owner_required=True.
    """
    protocol_engine = get_protocol_engine()
    protocol = protocol_engine.get_protocol("condition_alpha")
    assert protocol is not None

    # Completely depleted site: no equipment, no meds, no cold-chain, no specialists, 2G link
    depleted_site = ServiceSite(
        site_id="SITE-DEPLETED",
        region="Austere Border Outpost",
        site_name="Depleted Post-Disaster Aid Tent",
        clinic_tier="Sub-Center",
        equipment=[],  # Blocks preferred (no imaging)
        medication_stock=[],  # Blocks adapted & fallback (total drug stockout)
        cold_chain_available=False,  # Blocks preferred
        specialists=[],
        specialist_availability_hours="None",
        transport_available=False,
        teleconsult_bandwidth="128 kbps (2G link)",  # Blocks adapted remote photo transmission
        supported_languages=["ta"],
        interpreter_languages=[],
        operating_hours="Emergency only",
        registry_timestamp="2026-09-01T00:00:00Z",
    )

    tc = TravelConstraints(
        next_tier_site="SITE-001",
        travel_distance_km=70.0,
        travel_time_minutes=150,
        transport_available=False,
        connectivity_quality=ConnectivityQuality.POOR,
        follow_up_teleconsult_possible=False,
        patient_language="ta",
        preferred_language="ta",
        interpreter_required=False,
    )

    case = PatientCase(
        case_id="TEST-CASE-COLLAPSE",
        condition="condition_alpha",
        age_band="51-65",
        population_group=PopulationGroup.RURAL,
        site_id="SITE-DEPLETED",
        patient_language="ta",
        urgency=protocol.urgency,
        travel_constraints=tc,
        connectivity="128 kbps 2G link",
        synthetic=True,
    )

    result = evaluate_case_constraints(case=case, protocol=protocol, site=depleted_site)

    # Invariants for option exhaustion:
    assert result.decision == "ESCALATE_IMMEDIATELY"
    assert result.feasible is False
    assert result.escalation_required is True
    assert result.fallback_owner_required is True
    assert result.selected_ladder_level == "escalate_only"
    assert result.selected_option is not None
    assert len(result.selected_option) > 0
    assert result.selected_option != "No recommendation"
    assert result.selected_option != "null"

    # Verify that all 3 local tiers are documented in blocked_options
    assert "preferred" in result.blocked_options
    assert "resource_adapted_alternative" in result.blocked_options
    assert "minimum_safe_fallback" in result.blocked_options

    # Verify reason trail contains explicit explanation of total exhaustion
    assert any("FINAL DECISION: ESCALATE_IMMEDIATELY" in step for step in result.reason_trail)
    assert any("Minimum Safe Fallback': BLOCKED" in step for step in result.reason_trail)
