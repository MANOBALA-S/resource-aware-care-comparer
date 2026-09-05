"""Pydantic data models and enumerations for follow-up tracking and escalation.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from src.models.config_models import UrgencyLevel


class FollowUpStatus(str, Enum):
    """Execution lifecycle status of an operational follow-up task."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    ESCALATED = "ESCALATED"


class EscalationStatus(str, Enum):
    """Escalation condition of a follow-up task."""
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    ESCALATED = "ESCALATED"
    ESCALATION_FAILED = "ESCALATION_FAILED"


class EventType(str, Enum):
    """Audit trail event types for follow-up milestones and escalations."""
    FOLLOW_UP_CREATED = "FOLLOW_UP_CREATED"
    FOLLOW_UP_OVERDUE = "FOLLOW_UP_OVERDUE"
    ESCALATION_TRIGGERED = "ESCALATION_TRIGGERED"
    ESCALATION_FAILED = "ESCALATION_FAILED"
    FOLLOW_UP_COMPLETED = "FOLLOW_UP_COMPLETED"
    FOLLOW_UP_UPDATED = "FOLLOW_UP_UPDATED"


class FollowUpCreate(BaseModel):
    """Request payload for creating a new follow-up task."""
    case_id: str = Field(..., description="Synthetic patient case ID (e.g. 'SYNTH-CASE-001')")
    protocol_id: str = Field(..., description="Applicable protocol ID (e.g. 'PROTO-001')")
    task_type: str = Field(..., description="Type of follow-up (e.g. 'vitals_check', 'medication_refill', 'wound_review')")
    description: str = Field(..., description="Clear clinical/operational instructions for the task owner")
    urgency: UrgencyLevel = Field(..., description="Clinical urgency tier ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')")
    owner: str = Field(..., description="Named role or individual responsible (e.g. 'Local Health Worker', 'ASHA Nirmala')")
    due_at: Optional[str] = Field(None, description="ISO timestamp when task is due; calculated from SLA if omitted")
    escalation_due_at: Optional[str] = Field(None, description="ISO timestamp when escalation triggers if task is overdue")
    escalation_path: Optional[List[str]] = Field(None, description="Ordered escalation ladder")
    escalation_reason: Optional[str] = Field(None, description="Initial escalation context or trigger reason")


class FollowUpUpdate(BaseModel):
    """Payload for updating an existing follow-up task."""
    status: Optional[FollowUpStatus] = Field(None, description="New follow-up status")
    owner: Optional[str] = Field(None, description="Reassign task owner")
    description: Optional[str] = Field(None, description="Update task description or progress notes")
    notes: Optional[str] = Field(None, description="Operational notes or rationale for update")


class FollowUp(BaseModel):
    """Persistent entity model for an operational follow-up task."""
    follow_up_id: str = Field(..., description="Unique follow-up ID (e.g. 'FUP-2026-0001')")
    case_id: str = Field(..., description="Synthetic patient case ID")
    protocol_id: str = Field(..., description="Clinical protocol ID")
    task_type: str = Field(..., description="Category of task")
    description: str = Field(..., description="Detailed instructions")
    urgency: UrgencyLevel = Field(..., description="Urgency classification")
    owner: str = Field(..., description="Assigned human owner")
    due_at: str = Field(..., description="ISO timestamp of deadline")
    escalation_due_at: str = Field(..., description="ISO timestamp of escalation SLA deadline")
    escalation_path: List[str] = Field(default_factory=list, description="Ordered roles for escalation")
    status: FollowUpStatus = Field(default=FollowUpStatus.PENDING, description="Current task status")
    escalation_status: EscalationStatus = Field(default=EscalationStatus.NOT_REQUIRED, description="Escalation status")
    created_at: str = Field(..., description="ISO creation timestamp")
    updated_at: str = Field(..., description="ISO last modified timestamp")
    completed_at: Optional[str] = Field(None, description="ISO completion timestamp")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation")
    governance_notice: str = Field(
        default="Decision-support prototype — clinician sign-off required.",
        description="Mandatory clinical sign-off disclaimer"
    )
    synthetic_data_notice: str = Field(
        default="Synthetic data only — no real patient data.",
        description="Mandatory synthetic data declaration"
    )


class EscalationEvent(BaseModel):
    """Immutable audit trail record of a milestone, overdue breach, or escalation action."""
    event_id: str = Field(..., description="Unique event ID (e.g. 'EVT-2026-0001')")
    follow_up_id: str = Field(..., description="Associated follow-up ID")
    event_type: EventType = Field(..., description="Category of event")
    event_timestamp: str = Field(..., description="ISO timestamp when event occurred")
    previous_status: Optional[str] = Field(None, description="Task status prior to event")
    new_status: str = Field(..., description="Task status resulting from event")
    reason: str = Field(..., description="Explanatory context or trigger reason")
    owner: str = Field(..., description="Task owner at time of event")
    escalation_target: Optional[str] = Field(None, description="Role or individual escalated to")
