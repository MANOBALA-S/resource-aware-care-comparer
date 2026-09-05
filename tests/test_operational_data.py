"""Tests for synthetic operational environment, service registry, and patient cases.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import json
from pathlib import Path
import pytest

from src.config import PROJECT_ROOT
from src.data_generation.case_generator import (
    DEFAULT_SEED,
    generate_synthetic_cases,
    load_service_registry_sites,
)
from src.models.operational_models import PatientCase, ServiceSite


@pytest.fixture
def cases_file_path() -> Path:
    """Path to the generated synthetic cases JSON file."""
    return PROJECT_ROOT / "data" / "cases" / "synthetic_cases.json"


@pytest.fixture
def service_registry_path() -> Path:
    """Path to the service registry JSON file."""
    return PROJECT_ROOT / "data" / "services" / "service_registry.json"


@pytest.fixture
def raw_cases_data(cases_file_path: Path) -> dict:
    """Load raw synthetic cases data from JSON."""
    assert cases_file_path.is_file(), f"File not found: {cases_file_path}"
    with open(cases_file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def raw_service_registry(service_registry_path: Path) -> dict:
    """Load raw service registry data from JSON."""
    assert service_registry_path.is_file(), f"File not found: {service_registry_path}"
    with open(service_registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_service_registry_site_count_and_validation(raw_service_registry: dict) -> None:
    """Verify service registry has at least 6 sites and all pass ServiceSite Pydantic validation."""
    sites_list = raw_service_registry.get("sites", [])
    assert len(sites_list) >= 6, "Service registry must contain at least 6 sites."

    validated_sites = [ServiceSite.model_validate(s) for s in sites_list]
    site_ids = [s.site_id for s in validated_sites]

    # Verify key site IDs are present
    assert "SITE-001" in site_ids
    assert "SITE-002" in site_ids

    # Verify site variations
    site_001 = next(s for s in validated_sites if s.site_id == "SITE-001")
    assert site_001.cold_chain_available is True
    assert site_001.transport_available is True
    assert "doppler_ultrasound" in site_001.equipment

    site_002 = next(s for s in validated_sites if s.site_id == "SITE-002")
    assert site_002.cold_chain_available is False
    assert site_002.transport_available is False
    assert len(site_002.specialists) == 0


def test_exact_40_cases_generated(raw_cases_data: dict) -> None:
    """Verify that exactly 40 synthetic patient cases are generated and present."""
    cases = raw_cases_data.get("cases", [])
    assert len(cases) == 40, f"Expected exactly 40 cases, got {len(cases)}"


def test_all_cases_are_synthetic(raw_cases_data: dict) -> None:
    """Verify every single patient case declares synthetic=true and contains synthetic disclaimers."""
    cases = raw_cases_data.get("cases", [])
    for case in cases:
        assert case.get("synthetic") is True, f"Case {case.get('case_id')} synthetic flag is not True"
        assert "synthetic data only" in case.get("synthetic_data_notice", "").lower()
        assert "clinician sign-off required" in case.get("governance_notice", "").lower()


def test_all_required_fields_exist(raw_cases_data: dict) -> None:
    """Verify every case contains all mandatory top-level and travel_constraints fields."""
    required_top_level = [
        "case_id",
        "condition",
        "age_band",
        "population_group",
        "site_id",
        "patient_language",
        "urgency",
        "travel_constraints",
        "connectivity",
        "synthetic",
    ]

    required_travel = [
        "next_tier_site",
        "travel_distance_km",
        "travel_time_minutes",
        "transport_available",
        "connectivity_quality",
        "follow_up_teleconsult_possible",
        "patient_language",
        "preferred_language",
        "interpreter_required",
    ]

    for case in raw_cases_data.get("cases", []):
        for field in required_top_level:
            assert field in case, f"Missing required field '{field}' in case {case.get('case_id')}"

        tc = case["travel_constraints"]
        for field in required_travel:
            assert field in tc, f"Missing required travel field '{field}' in case {case.get('case_id')}"

        # Pydantic validation check
        validated_case = PatientCase.model_validate(case)
        assert validated_case.case_id == case["case_id"]


def test_languages_variation(raw_cases_data: dict) -> None:
    """Verify both English ('en') and Tamil ('ta') exist in the dataset."""
    languages = {c["patient_language"] for c in raw_cases_data.get("cases", [])}
    assert "en" in languages, "English ('en') must be present in the cases."
    assert "ta" in languages, "Tamil ('ta') must be present in the cases."


def test_population_group_variation(raw_cases_data: dict) -> None:
    """Verify both 'rural' and 'urban' population contexts exist in the dataset."""
    groups = {c["population_group"] for c in raw_cases_data.get("cases", [])}
    assert "rural" in groups, "Rural population context must be represented."
    assert "urban" in groups, "Urban population context must be represented."


def test_urgency_levels_variation(raw_cases_data: dict) -> None:
    """Verify all four clinical urgency levels are represented in the dataset."""
    urgencies = {c["urgency"] for c in raw_cases_data.get("cases", [])}
    assert "LOW" in urgencies
    assert "MEDIUM" in urgencies
    assert "HIGH" in urgencies
    assert "CRITICAL" in urgencies


def test_multiple_sites_variation(raw_cases_data: dict) -> None:
    """Verify multiple distinct healthcare sites are represented."""
    sites = {c["site_id"] for c in raw_cases_data.get("cases", [])}
    assert len(sites) >= 4, f"Expected at least 4 sites represented, got {len(sites)}"
    # Verify both rural sub-center and tertiary hospital are present
    assert "SITE-001" in sites
    assert "SITE-002" in sites


def test_multiple_conditions_variation(raw_cases_data: dict) -> None:
    """Verify all five synthetic conditions are represented."""
    conditions = {c["condition"] for c in raw_cases_data.get("cases", [])}
    assert "condition_alpha" in conditions
    assert "condition_beta" in conditions
    assert "condition_gamma" in conditions
    assert "condition_delta" in conditions
    assert "condition_epsilon" in conditions


def test_deterministic_reproducibility() -> None:
    """Verify that running generation with the same seed produces identical case outputs."""
    run1 = generate_synthetic_cases(total_cases=40, seed=DEFAULT_SEED)
    run2 = generate_synthetic_cases(total_cases=40, seed=DEFAULT_SEED)

    assert len(run1) == len(run2) == 40
    for c1, c2 in zip(run1, run2):
        assert c1.case_id == c2.case_id
        assert c1.condition == c2.condition
        assert c1.patient_language == c2.patient_language
        assert c1.urgency == c2.urgency
        assert c1.travel_constraints.travel_time_minutes == c2.travel_constraints.travel_time_minutes


def test_data_quality_logical_coherence(raw_cases_data: dict) -> None:
    """Verify that travel constraints and resource parameters are logically coherent."""
    for case in raw_cases_data.get("cases", []):
        tc = case["travel_constraints"]
        # If distance is zero (tertiary hospital self-referral), travel time should be 0
        if tc["travel_distance_km"] == 0.0:
            assert tc["travel_time_minutes"] == 0
        else:
            # Positive distance should require positive transit time
            assert tc["travel_time_minutes"] > 0

        # If transport is not available, transit time should not be suspiciously trivial for non-zero distance
        if not tc["transport_available"] and tc["travel_distance_km"] > 10.0:
            assert tc["travel_time_minutes"] >= 30
