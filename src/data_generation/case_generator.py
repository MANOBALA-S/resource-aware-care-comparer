"""Deterministic synthetic patient case generator for teleconsultation decision-support.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import PROJECT_ROOT
from src.models.config_models import UrgencyLevel
from src.models.operational_models import (
    ConnectivityQuality,
    LanguageProfile,
    PatientCase,
    PopulationGroup,
    TravelConstraints,
)

DEFAULT_SEED = 42
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "cases" / "synthetic_cases.json"
SERVICE_REGISTRY_PATH = PROJECT_ROOT / "data" / "services" / "service_registry.json"


def load_service_registry_sites() -> Dict[str, Dict[str, Any]]:
    """Load sites from the service registry into a lookup dictionary."""
    if not SERVICE_REGISTRY_PATH.is_file():
        raise FileNotFoundError(f"Service registry not found at {SERVICE_REGISTRY_PATH}")
    with open(SERVICE_REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {site["site_id"]: site for site in data.get("sites", [])}


# Condition catalog with baseline urgencies
CONDITIONS = [
    ("condition_alpha", UrgencyLevel.HIGH),
    ("condition_beta", UrgencyLevel.MEDIUM),
    ("condition_gamma", UrgencyLevel.CRITICAL),
    ("condition_delta", UrgencyLevel.LOW),
    ("condition_epsilon", UrgencyLevel.MEDIUM),
]

AGE_BANDS = ["18-35", "36-50", "51-65", "65+"]


def generate_synthetic_cases(
    total_cases: int = 40,
    seed: int = DEFAULT_SEED,
) -> List[PatientCase]:
    """Deterministically generate exactly total_cases synthetic patient cases with coherent constraints.

    Args:
        total_cases: Number of synthetic cases to generate (default 40).
        seed: Random seed for 100% deterministic reproducibility.

    Returns:
        List of validated PatientCase models.
    """
    rng = random.Random(seed)
    sites_lookup = load_service_registry_sites()
    site_ids = sorted(list(sites_lookup.keys()))

    cases: List[PatientCase] = []

    # Referral distances and baseline transit minutes from sites to their next-tier facility
    referral_map = {
        "SITE-001": ("SITE-001", 0.0, 0, True),  # Tertiary is top tier
        "SITE-002": ("SITE-005", 18.5, 40, False),  # Rural sub-center to Taluk
        "SITE-003": ("SITE-005", 24.0, 50, True),   # CHC to Taluk
        "SITE-004": ("SITE-003", 32.0, 85, False),  # Remote PHC to CHC
        "SITE-005": ("SITE-001", 21.0, 35, True),   # Taluk to Tertiary
        "SITE-006": ("SITE-001", 8.5, 20, True),    # Urban Kiosk to Tertiary
    }

    for i in range(1, total_cases + 1):
        case_id = f"SYNTH-CASE-{i:03d}"

        # Deterministic round-robin / seeded selection to guarantee balanced diversity
        condition_item = CONDITIONS[(i - 1) % len(CONDITIONS)]
        base_condition, base_urgency = condition_item

        # Allow controlled severity nuance (e.g. 10% chance of escalating or de-escalating urgency)
        urgency = base_urgency
        nuance_roll = rng.random()
        if nuance_roll < 0.10 and urgency != UrgencyLevel.LOW:
            # Slightly lower urgency presentation
            if urgency == UrgencyLevel.CRITICAL:
                urgency = UrgencyLevel.HIGH
            elif urgency == UrgencyLevel.HIGH:
                urgency = UrgencyLevel.MEDIUM
        elif nuance_roll > 0.90 and urgency != UrgencyLevel.CRITICAL:
            # Acute presentation of a sub-acute condition
            if urgency == UrgencyLevel.MEDIUM:
                urgency = UrgencyLevel.HIGH
            elif urgency == UrgencyLevel.LOW:
                urgency = UrgencyLevel.MEDIUM

        # Select site with balanced distribution
        site_id = site_ids[(i - 1) % len(site_ids)]
        site_data = sites_lookup[site_id]

        # Demographic context coherent with site tier
        if site_id in ("SITE-002", "SITE-003", "SITE-004"):
            # Rural bias
            pop_group = PopulationGroup.RURAL if rng.random() < 0.85 else PopulationGroup.URBAN
        else:
            # Urban bias
            pop_group = PopulationGroup.URBAN if rng.random() < 0.85 else PopulationGroup.RURAL

        age_band = rng.choice(AGE_BANDS)

        # Language profile:
        # Rural sites have higher Tamil prevalence; urban sites have balanced mix
        if pop_group == PopulationGroup.RURAL or site_id in ("SITE-002", "SITE-004"):
            patient_lang = "ta" if rng.random() < 0.80 else "en"
        else:
            patient_lang = "ta" if rng.random() < 0.45 else "en"

        # Coherent travel constraints
        ref_site, base_dist, base_time, default_transport = referral_map[site_id]

        # In remote or rural sub-center settings, transport availability depends on personal access or village vehicle
        if not default_transport:
            transport_avail = rng.random() < 0.25  # Only 25% have private transport
        else:
            transport_avail = rng.random() < 0.85  # 85% have access when site provides/urban

        # Transit time scales upward if transport is unavailable (e.g. waiting for public bus or walking)
        if not transport_avail and base_dist > 0:
            travel_time = int(base_time * rng.uniform(1.8, 2.5))
        else:
            travel_time = int(base_time * rng.uniform(0.9, 1.2))

        # Connectivity quality coherent with site bandwidth
        if "128 kbps" in site_data["teleconsult_bandwidth"]:
            conn_quality = rng.choice([ConnectivityQuality.POOR, ConnectivityQuality.MODERATE])
            conn_summary = "Intermittent 2G cellular link; high packet loss"
            teleconsult_possible = rng.random() < 0.35  # Often too slow for video
        elif "10 Mbps" in site_data["teleconsult_bandwidth"]:
            conn_quality = rng.choice([ConnectivityQuality.MODERATE, ConnectivityQuality.GOOD])
            conn_summary = "4G mobile broadband; adequate for video with occasional jitter"
            teleconsult_possible = True
        elif "Satellite" in site_data["teleconsult_bandwidth"] or "satellite" in site_data["teleconsult_bandwidth"]:
            conn_quality = ConnectivityQuality.MODERATE
            conn_summary = "Satellite broadband link; stable throughput with noticeable propagation latency"
            teleconsult_possible = True
        else:
            conn_quality = ConnectivityQuality.EXCELLENT
            conn_summary = "High-speed fiber/VDSL connection; full HD video supported"
            teleconsult_possible = True

        # Interpreter logic: If patient speaks Tamil only and remote clinician speaks English only,
        # an interpreter is required.
        interpreter_needed = True if (patient_lang == "ta" and rng.random() < 0.70) else False

        travel_constraints = TravelConstraints(
            next_tier_site=ref_site,
            travel_distance_km=round(base_dist, 1),
            travel_time_minutes=travel_time,
            transport_available=transport_avail,
            connectivity_quality=conn_quality,
            follow_up_teleconsult_possible=teleconsult_possible,
            patient_language=patient_lang,
            preferred_language=patient_lang,
            interpreter_required=interpreter_needed,
        )

        language_profile = LanguageProfile(
            primary_language=patient_lang,
            preferred_language=patient_lang,
            literacy_level=rng.choice(["functional", "low", "high"]),
            interpreter_required=interpreter_needed,
            preferred_modality="vernacular_text" if patient_lang == "ta" else "text",
        )

        case = PatientCase(
            case_id=case_id,
            condition=base_condition,
            age_band=age_band,
            population_group=pop_group,
            site_id=site_id,
            patient_language=patient_lang,
            urgency=urgency,
            travel_constraints=travel_constraints,
            connectivity=conn_summary,
            language_profile=language_profile,
            synthetic=True,
            governance_notice="Decision-support prototype — clinician sign-off required.",
            synthetic_data_notice="Synthetic data only — no real patient data.",
        )
        cases.append(case)

    return cases


def generate_and_save_cases(
    output_path: Optional[Path] = None,
    total_cases: int = 40,
    seed: int = DEFAULT_SEED,
) -> Path:
    """Generate 40 synthetic patient cases and write to JSON file.

    Args:
        output_path: Path where synthetic_cases.json should be saved.
        total_cases: Exact count of cases (40).
        seed: Random seed for deterministic reproducibility.

    Returns:
        Path to the saved JSON file.
    """
    target_path = output_path or DEFAULT_OUTPUT_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    cases = generate_synthetic_cases(total_cases=total_cases, seed=seed)

    payload = {
        "metadata": {
            "title": "Synthetic Patient Cases for Teleconsultation Evaluation",
            "version": "1.0.0",
            "total_cases": len(cases),
            "random_seed": seed,
            "synthetic_data_notice": "Synthetic data only — no real patient data.",
            "governance_notice": "Decision-support prototype — clinician sign-off required.",
            "description": "Cohort of 40 diverse, logical synthetic patient cases spanning rural/urban, multiple age bands, urgency levels, conditions, and resource realities."
        },
        "cases": [case.model_dump() for case in cases],
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return target_path
