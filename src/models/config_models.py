"""Configuration models and enumerations for system settings, languages, urgency, and escalation.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class UrgencyLevel(str, Enum):
    """Standard clinical urgency classifications."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EscalationTier(str, Enum):
    """Operational escalation tiers for follow-up checkpoints."""
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class ActorType(str, Enum):
    """Core stakeholders defined in the teleconsultation operating procedure."""
    PATIENT = "Patient"
    REMOTE_CLINICIAN = "Remote clinician"
    LOCAL_HEALTH_WORKER = "Local health worker"
    CARE_COORDINATOR = "Care coordinator"


class LanguageConfig(BaseModel):
    """Configuration definition for a supported language."""
    code: str = Field(..., description="ISO 639-1 two-letter language code (e.g., 'en', 'ta')")
    name: str = Field(..., description="English display name of the language")
    native_name: str = Field(..., description="Endonym / native name of the language")
    direction: str = Field(default="ltr", description="Text direction ('ltr' or 'rtl')")
    is_default: bool = Field(default=False, description="Whether this is the fallback language")
    enabled: bool = Field(default=True, description="Whether the language is currently active in the UI/API")
    locale: str = Field(..., description="BCP 47 / standard locale code (e.g., 'en_US', 'ta_IN')")
    description: Optional[str] = Field(default=None, description="Operational purpose of this language")

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if v not in ("ltr", "rtl"):
            raise ValueError("Direction must be 'ltr' or 'rtl'")
        return v


class UrgencyDetail(BaseModel):
    """Detail and operational parameters for a specific urgency level."""
    code: UrgencyLevel
    label: str
    description: str
    default_followup_hours: int = Field(..., gt=0, description="Default follow-up window in hours")
    max_escalation_tier: EscalationTier = Field(..., description="Maximum escalation tier before auto-dispatch")


class EscalationDetail(BaseModel):
    """Detail and timeout constraints for an escalation tier."""
    tier: EscalationTier
    title: str
    responsible_actor: str
    ack_timeout_minutes: int = Field(..., gt=0, description="Acknowledgment timeout in minutes")
    description: str


class AppConfig(BaseModel):
    """Application runtime configuration."""
    name: str = "Resource-Aware Care Option Comparer"
    version: str = "0.1.0"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    database_url: str = "sqlite:///data/care_comparer.db"


class GovernanceConfig(BaseModel):
    """Mandatory clinical governance and synthetic data policy configuration."""
    prototype_disclaimer: str = "Decision-support prototype — clinician sign-off required."
    synthetic_data_policy: str = "Synthetic data only — no real patient data."
    clinician_signoff_mandatory: bool = True


class SystemSettings(BaseModel):
    """Composite system settings combining app, governance, urgency, escalation, and languages."""
    app: AppConfig = Field(default_factory=AppConfig)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    urgency_levels: Dict[str, UrgencyDetail] = Field(default_factory=dict)
    escalation_levels: Dict[str, EscalationDetail] = Field(default_factory=dict)
    languages: List[LanguageConfig] = Field(default_factory=list)
    default_language: str = "en"
