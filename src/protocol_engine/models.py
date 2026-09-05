"""Pydantic data models for synthetic clinical protocols and recommendation ladders.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

from src.models.config_models import UrgencyLevel


class RecommendationOption(BaseModel):
    """A single tier option within a protocol recommendation ladder."""
    option: str = Field(..., description="Actionable clinical or operational guidance text")
    required_resources: List[str] = Field(
        default_factory=list,
        description="Required site and infrastructure capabilities for this option"
    )
    rationale: str = Field(..., description="Justification and trade-off considerations for this option")


class RecommendationLadder(BaseModel):
    """Four-tier hierarchical recommendation ladder for a clinical condition."""
    preferred: RecommendationOption = Field(
        ...,
        description="Gold standard, unconstrained guideline recommendation"
    )
    resource_adapted_alternative: RecommendationOption = Field(
        ...,
        description="Safe adaptation when primary resources (imaging, cold-chain) are unavailable"
    )
    minimum_safe_fallback: RecommendationOption = Field(
        ...,
        description="Lowest-tier safe maintenance or stabilization option in austere settings"
    )
    escalate_only: RecommendationOption = Field(
        ...,
        description="Mandatory trigger for physical transfer or senior clinical escalation"
    )


class ProtocolDefinition(BaseModel):
    """Complete specification of a synthetic clinical protocol."""
    protocol_id: str = Field(..., description="Unique protocol identifier, e.g. 'PROTO-001'")
    protocol_version: str = Field(..., description="Semantic version string, e.g. '1.0.0'")
    condition: str = Field(..., description="Unique condition code, e.g. 'condition_alpha'")
    title: str = Field(..., description="Human-readable title of the protocol")
    urgency: UrgencyLevel = Field(..., description="Urgency classification (LOW, MEDIUM, HIGH, CRITICAL)")
    textbook_recommendation: str = Field(
        ...,
        description="Comprehensive standard-of-care recommendation assuming ideal resources"
    )
    required_resources: List[str] = Field(
        default_factory=list,
        description="List of resources required to execute the textbook recommendation"
    )
    follow_up_required: bool = Field(default=True, description="Whether scheduled follow-up is mandatory")
    follow_up_interval: str = Field(..., description="Target time interval for follow-up (e.g., '6h', '24h')")
    escalation_required: bool = Field(default=True, description="Whether an escalation pathway must be configured")
    recommendation_ladder: RecommendationLadder = Field(
        ...,
        description="Structured 4-tier recommendation ladder"
    )


class ProtocolLibraryMetadata(BaseModel):
    """Metadata header for the protocol library file."""
    title: str = "Synthetic Clinical Protocol Library"
    version: str = "1.0.0"
    synthetic_data_notice: str = "Synthetic data only — no real patient data."
    governance_notice: str = "Decision-support prototype — clinician sign-off required."
    description: Optional[str] = None


class ProtocolLibrary(BaseModel):
    """Top-level container for the protocol catalog."""
    metadata: ProtocolLibraryMetadata
    protocols: List[ProtocolDefinition]
