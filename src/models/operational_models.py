"""Pydantic models for synthetic healthcare sites, travel constraints, language profiles, and patient cases.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from src.models.config_models import UrgencyLevel


class PopulationGroup(str, Enum):
    """Demographic and geographic population group context."""
    RURAL = "rural"
    URBAN = "urban"


class ConnectivityQuality(str, Enum):
    """Field connectivity reliability classifications."""
    POOR = "POOR"
    MODERATE = "MODERATE"
    GOOD = "GOOD"
    EXCELLENT = "EXCELLENT"


class ServiceSite(BaseModel):
    """Synthetic healthcare facility site specification."""
    site_id: str = Field(..., description="Unique site identifier (e.g. 'SITE-001')")
    region: str = Field(..., description="Geographic region of the site")
    site_name: str = Field(..., description="Display name of the clinic/hospital")
    clinic_tier: str = Field(..., description="Facility tier level (e.g., Sub-Center, CHC, Tertiary)")
    equipment: List[str] = Field(default_factory=list, description="Diagnostic and monitoring hardware available")
    medication_stock: List[str] = Field(default_factory=list, description="Currently verified pharmaceutical items in stock")
    cold_chain_available: bool = Field(..., description="Whether functional cold-chain refrigeration exists on site")
    specialists: List[str] = Field(default_factory=list, description="Specialist cadres available physically on site")
    specialist_availability_hours: str = Field(..., description="Working hours or schedule for specialist access")
    transport_available: bool = Field(..., description="Whether dedicated transfer or ambulance vehicles are available")
    teleconsult_bandwidth: str = Field(..., description="Description and speed of teleconsultation network connection")
    supported_languages: List[str] = Field(..., description="Languages spoken fluently by on-site staff")
    interpreter_languages: List[str] = Field(default_factory=list, description="Languages accessible via dedicated translators")
    operating_hours: str = Field(..., description="Operating schedule of the facility")
    registry_timestamp: str = Field(..., description="ISO timestamp of registry update")
    registry_version: str = Field(default="1.0.0", description="Semantic version of the registry schema")


class TravelConstraints(BaseModel):
    """Logistical travel and transit constraints between a patient's site and referral tiers."""
    next_tier_site: str = Field(..., description="Identifier of the nearest next-tier referral facility")
    travel_distance_km: float = Field(..., ge=0.0, description="Road distance to the next-tier site in kilometers")
    travel_time_minutes: int = Field(..., ge=0, description="Estimated transit time in minutes under typical conditions")
    transport_available: bool = Field(..., description="Whether safe transit conveyance is realistically available to patient")
    connectivity_quality: ConnectivityQuality = Field(..., description="Cellular/network connection stability at patient base")
    follow_up_teleconsult_possible: bool = Field(..., description="Whether remote virtual review is logistically feasible")
    patient_language: str = Field(..., description="Language primarily spoken and understood by patient")
    preferred_language: str = Field(..., description="Preferred language for written/spoken care instructions")
    interpreter_required: bool = Field(..., description="Whether patient requires an interpreter for clinical consultation")


class LanguageProfile(BaseModel):
    """Detailed linguistic and communication preferences for the patient."""
    primary_language: str = Field(..., description="Primary mother tongue (e.g., 'en', 'ta')")
    preferred_language: str = Field(..., description="Preferred language for care instructions")
    literacy_level: str = Field(default="functional", description="Literacy level: functional, low, high")
    interpreter_required: bool = Field(default=False, description="Whether translation is required for remote clinician")
    preferred_modality: str = Field(default="vernacular_text", description="Instruction modality: vernacular_text, audio, pictorial")


class PatientCase(BaseModel):
    """Synthetic patient case profile for teleconsultation decision-support evaluation."""
    case_id: str = Field(..., description="Unique synthetic case identifier (e.g. 'SYNTH-CASE-001')")
    condition: str = Field(..., description="Primary clinical condition code (e.g. 'condition_alpha')")
    age_band: str = Field(..., description="Patient age category (e.g. '18-35', '36-50', '51-65', '65+')")
    population_group: PopulationGroup = Field(..., description="Geographic context ('rural' or 'urban')")
    site_id: str = Field(..., description="Healthcare site where patient presented")
    patient_language: str = Field(..., description="Primary patient language ('en', 'ta')")
    urgency: UrgencyLevel = Field(..., description="Clinical urgency tier ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')")
    travel_constraints: TravelConstraints = Field(..., description="Physical travel and connectivity constraints")
    connectivity: str = Field(..., description="Human-readable network connectivity summary at presentation")
    language_profile: Optional[LanguageProfile] = None
    synthetic: bool = Field(default=True, description="Strict synthetic data flag: must always be True")
    governance_notice: str = Field(
        default="Decision-support prototype — clinician sign-off required.",
        description="Mandatory clinical sign-off disclaimer"
    )
    synthetic_data_notice: str = Field(
        default="Synthetic data only — no real patient data.",
        description="Mandatory synthetic data declaration"
    )

    @field_validator("synthetic")
    @classmethod
    def validate_synthetic(cls, v: bool) -> bool:
        if not v:
            raise ValueError("All patient cases MUST be synthetic. Real patient data is strictly prohibited.")
        return v
