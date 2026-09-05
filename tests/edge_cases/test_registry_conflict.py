"""Edge case test: Contradictory service registry records handled with safety-first principle.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import pytest

from src.constraint_engine.feasibility import evaluate_case_constraints
from src.constraint_engine.models import ResourceStatus
from src.constraint_engine.resource_filter import (
    check_registry_conflicts,
    evaluate_resource_availability,
    resolve_registry_pair_conflict,
)
from src.models.operational_models import (
    ConnectivityQuality,
    PatientCase,
    PopulationGroup,
    ServiceSite,
    TravelConstraints,
)
from src.protocol_engine.protocol_engine import get_protocol_engine


def test_disparate_registry_a_vs_b_conflict() -> None:
    """Test Edge Case 2: Registry A reports specialist available, Registry B reports unavailable.

    Expected:
    - Status: REGISTRY_CONFLICT
    - Safer assumption: resource unavailable (available = False)
    - No averaging or guessing.
    """
    registry_a = {
        "site_id": "SITE-001",
        "specialist_available": True,
        "specialists": ["endocrinologist", "cardiologist"],
    }
    registry_b = {
        "site_id": "SITE-001",
        "specialist_available": False,
        "specialists": [],
    }

    status_code, available, reason = resolve_registry_pair_conflict(
        registry_a=registry_a,
        registry_b=registry_b,
        resource="specialist",
    )

    assert status_code == "REGISTRY_CONFLICT"
    assert available is False
    assert "REGISTRY_CONFLICT" in reason
    assert "Safer clinical assumption applied" in reason
    assert "No averaging or guessing" in reason


def test_direct_conflict_detection_treats_resource_as_unavailable() -> None:
    """Test 5A: Conflicting boolean flags trigger CONFLICT_RESOLVED_BLOCKED."""
    base_site = ServiceSite(
        site_id="SITE-CONFLICT",
        region="Test Region",
        site_name="Conflicted Clinic",
        clinic_tier="Community Health Center",
        equipment=["digital_xray"],
        medication_stock=["oral_antibiotics", "co_amoxiclav"],
        cold_chain_available=True,
        specialists=["vascular_surgeon"],
        specialist_availability_hours="24/7",
        transport_available=True,
        teleconsult_bandwidth="10 Mbps",
        supported_languages=["en"],
        interpreter_languages=[],
        operating_hours="24/7",
        registry_timestamp="2026-09-01T00:00:00Z",
    )

    # Inject contradictory record into raw dictionary
    conflicted_dict = base_site.model_dump()
    conflicted_dict["specialist_available"] = True
    conflicted_dict["specialist_unavailable"] = True  # Contradiction

    # Check resource evaluation directly
    eval_res = evaluate_resource_availability(
        resource="specialist_48h",
        site=base_site,
        raw_site_dict=conflicted_dict,
    )

    # Invariant: Safe assumption applied
    assert eval_res.available is False
    assert eval_res.status == ResourceStatus.CONFLICT_RESOLVED_BLOCKED
    assert "conflicting specialist availability records" in eval_res.reason.lower()
    assert "safer assumption applied" in eval_res.reason.lower()


def test_registry_conflict_prevents_unsafe_preferred_option() -> None:
    """Test 5B: When specialist data is in conflict, engine must not prescribe the specialist option."""
    protocol_engine = get_protocol_engine()
    protocol = protocol_engine.get_protocol("condition_alpha")
    assert protocol is not None

    base_site = ServiceSite(
        site_id="SITE-CONFLICT-2",
        region="Coastal South",
        site_name="Conflicted Referral Hospital",
        clinic_tier="Tertiary Hospital",
        equipment=["doppler_ultrasound", "digital_xray"],
        medication_stock=["oral_antibiotics", "co_amoxiclav", "iv_cephalosporins"],
        cold_chain_available=True,
        specialists=["vascular_surgeon"],
        specialist_availability_hours="24/7",
        transport_available=True,
        teleconsult_bandwidth="50 Mbps",
        supported_languages=["en", "ta"],
        interpreter_languages=[],
        operating_hours="24/7",
        registry_timestamp="2026-09-01T00:00:00Z",
    )

    # Simulate conflict in imaging availability
    conflicted_dict = base_site.model_dump()
    conflicted_dict["conflicts"] = {
        "same_day_imaging": "Inventory says ultrasound online, but maintenance log reports probe failure"
    }

    tc = TravelConstraints(
        next_tier_site="SITE-001",
        travel_distance_km=0.0,
        travel_time_minutes=0,
        transport_available=True,
        connectivity_quality=ConnectivityQuality.EXCELLENT,
        follow_up_teleconsult_possible=True,
        patient_language="ta",
        preferred_language="ta",
        interpreter_required=False,
    )

    case = PatientCase(
        case_id="TEST-CASE-CONFLICT",
        condition="condition_alpha",
        age_band="36-50",
        population_group=PopulationGroup.URBAN,
        site_id="SITE-CONFLICT-2",
        patient_language="ta",
        urgency=protocol.urgency,
        travel_constraints=tc,
        connectivity="50 Mbps fiber",
        synthetic=True,
    )

    result = evaluate_case_constraints(
        case=case,
        protocol=protocol,
        site=base_site,
        raw_site_dict=conflicted_dict,
    )

    # Preferred option (which requires same_day_imaging) must be BLOCKED due to conflict
    assert "preferred" in result.blocked_options
    assert any("conflicting" in r.lower() for r in result.blocked_options["preferred"])
    # Engine falls back to resource-adapted alternative
    assert result.selected_ladder_level == "resource_adapted_alternative"
    assert any("Conflicting same_day_imaging records detected" in step for step in result.reason_trail)
