"""Data models and enumerations for the Resource Constraint Engine.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ResourceStatus(str, Enum):
    """Evaluation status of a specific required clinical or operational resource."""
    AVAILABLE = "AVAILABLE"
    BLOCKED = "BLOCKED"
    CONFLICT_RESOLVED_BLOCKED = "CONFLICT_RESOLVED_BLOCKED"


class LanguageStatus(str, Enum):
    """Clinical communication and translation safety status."""
    SUPPORTED = "SUPPORTED"
    REQUIRES_INTERPRETER = "REQUIRES_INTERPRETER"
    LANGUAGE_ESCALATION_REQUIRED = "LANGUAGE_ESCALATION_REQUIRED"


class ResourceEvaluation(BaseModel):
    """Detailed evaluation result for a single required resource."""
    resource: str = Field(..., description="Resource identifier, e.g. 'same_day_imaging'")
    required: bool = Field(..., description="Whether this resource is demanded by the evaluated option")
    available: bool = Field(..., description="Whether the resource is confirmed available at the point of care")
    status: ResourceStatus = Field(..., description="Availability classification (AVAILABLE, BLOCKED, CONFLICT_RESOLVED_BLOCKED)")
    reason: str = Field(..., description="Explanatory clinical or logistical rationale")


class OptionEvaluation(BaseModel):
    """Evaluation of an individual rung in the protocol recommendation ladder."""
    ladder_level: str = Field(..., description="Rung level: 'preferred', 'resource_adapted_alternative', 'minimum_safe_fallback', 'escalate_only'")
    option_text: str = Field(..., description="Text of the clinical/operational recommendation")
    feasible: bool = Field(..., description="Whether all required resources and constraints are satisfied")
    resource_evaluations: List[ResourceEvaluation] = Field(default_factory=list, description="Breakdown of each resource check")
    blocking_reasons: List[str] = Field(default_factory=list, description="Specific deficits that render this option infeasible")


class LanguageEvaluation(BaseModel):
    """Linguistic compatibility assessment for the teleconsultation."""
    patient_language: str
    status: LanguageStatus
    interpreter_available: bool
    explanation: str


class ConstraintEngineResult(BaseModel):
    """Comprehensive output emitted by the Resource Constraint Engine."""
    case_id: str
    protocol_id: str
    selected_option: Optional[str] = Field(None, description="The highest feasible clinical recommendation option")
    selected_ladder_level: Optional[str] = Field(None, description="The ladder tier selected: preferred, resource_adapted_alternative, minimum_safe_fallback, or escalate_only")
    feasible: bool = Field(..., description="Whether a safe local care recommendation was successfully selected")
    decision: str = Field(..., description="'SELECT_OPTION' if a ladder tier is feasible; 'ESCALATE_IMMEDIATELY' if all local tiers are blocked")
    reason_trail: List[str] = Field(default_factory=list, description="Step-by-step chronological audit log of evaluation decisions")
    blocked_options: Dict[str, List[str]] = Field(default_factory=dict, description="Dictionary mapping blocked ladder levels to their blocking reasons")
    escalation_required: bool = Field(default=False, description="Whether immediate clinical or operational escalation is triggered")
    escalation_reason: Optional[str] = Field(None, description="Clinical/logistical reason necessitating escalation")
    fallback_owner_required: bool = Field(default=False, description="Whether an accountable human owner must be assigned immediately to resolve block")
    language_status: LanguageStatus = Field(..., description="Language communication status (SUPPORTED, REQUIRES_INTERPRETER, LANGUAGE_ESCALATION_REQUIRED)")
    resource_status: Dict[str, ResourceEvaluation] = Field(default_factory=dict, description="Consolidated resource availability map across all evaluated requirements")
    governance_notice: str = Field(
        default="Decision-support prototype — clinician sign-off required.",
        description="Mandatory clinical sign-off disclaimer"
    )
    synthetic_data_notice: str = Field(
        default="Synthetic data only — no real patient data.",
        description="Mandatory synthetic data declaration"
    )
