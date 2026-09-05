"""Pydantic models and enumerations for the multilingual language layer.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class LanguageStatus(str, Enum):
    """Clinical communication and translation safety status."""
    SUPPORTED = "SUPPORTED"
    REQUIRES_INTERPRETER = "REQUIRES_INTERPRETER"
    LANGUAGE_ESCALATION_REQUIRED = "LANGUAGE_ESCALATION_REQUIRED"


class LanguageProfile(BaseModel):
    """Comprehensive linguistic profile for patient-clinician communication matching."""
    patient_language: str = Field(..., description="Primary language spoken by the patient (e.g. 'en', 'ta')")
    preferred_language: Optional[str] = Field(None, description="Preferred language for clinical communications if different")
    clinician_languages: List[str] = Field(
        default_factory=list,
        description="Languages directly spoken by the available clinician(s)"
    )
    interpreter_languages: List[str] = Field(
        default_factory=list,
        description="Languages available via dedicated interpretation services"
    )
    interpreter_available: bool = Field(
        default=True,
        description="Whether an interpreter is functionally accessible at time of consultation"
    )
    selected_language: Optional[str] = Field(
        None,
        description="The resolved language for the clinical interaction (None if escalation required)"
    )
    language_status: LanguageStatus = Field(
        ...,
        description="Status: SUPPORTED, REQUIRES_INTERPRETER, or LANGUAGE_ESCALATION_REQUIRED"
    )
    explanation: Optional[str] = Field(
        None,
        description="Human-readable clinical rationale for the language resolution status"
    )
    governance_notice: str = Field(
        default="Decision-support prototype — clinician sign-off required.",
        description="Mandatory clinical sign-off disclaimer"
    )
    synthetic_data_notice: str = Field(
        default="Synthetic data only — no real patient data.",
        description="Mandatory synthetic data declaration"
    )
