"""High-level tracker and integration bridge for follow-up and escalation workflows.

Bridges the Resource Constraint Engine evaluations to persistent follow-up tasks.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.constraint_engine.models import ConstraintEngineResult
from src.followup.escalation import calculate_deadlines, get_default_escalation_path
from src.followup.models import (
    EscalationStatus,
    FollowUp,
    FollowUpCreate,
    FollowUpStatus,
)
from src.followup.repository import create_follow_up
from src.models.config_models import UrgencyLevel
from src.models.operational_models import PatientCase
from src.protocol_engine.models import ProtocolDefinition


def create_followup_from_evaluation(
    result: ConstraintEngineResult,
    case: Union[PatientCase, Dict[str, Any]],
    protocol: Union[ProtocolDefinition, Dict[str, Any]],
    owner: Optional[str] = None,
    task_type: Optional[str] = None,
    custom_escalation_path: Optional[List[str]] = None,
    db_path: Optional[Path] = None,
) -> FollowUp:
    """Create a tracked follow-up task directly from a constraint engine evaluation result.

    Ensures that high-priority clinical or operational recommendations cannot silently vanish.
    If the constraint engine triggers an immediate escalation, urgency is automatically
    elevated to CRITICAL with an appropriate emergency task type and escalation ladder.

    Args:
        result: Evaluated result from the Resource Constraint Engine.
        case: Synthetic patient case entity or dictionary.
        protocol: Clinical protocol definition entity or dictionary.
        owner: Named role or clinician responsible for follow-up (defaults to 'Local Health Worker').
        task_type: Category of follow-up task.
        custom_escalation_path: Optional override for escalation hierarchy.
        db_path: Optional path to SQLite database.

    Returns:
        Persisted FollowUp instance with deterministic SLAs and audit trail initialized.
    """
    case_id = case.case_id if isinstance(case, PatientCase) else case.get("case_id", result.case_id)
    protocol_id = protocol.protocol_id if isinstance(protocol, ProtocolDefinition) else protocol.get("protocol_id", result.protocol_id)
    protocol_title = protocol.title if isinstance(protocol, ProtocolDefinition) else protocol.get("title", protocol_id)

    # Determine urgency: if escalation was triggered by engine, escalate to CRITICAL
    if result.decision == "ESCALATE_IMMEDIATELY" or result.escalation_required:
        urgency = UrgencyLevel.CRITICAL
        resolved_task_type = task_type or "emergency_escalation"
        reason = result.escalation_reason or "All local recommendation tiers blocked; immediate human clinical escalation required."
        description = f"URGENT: {reason} Case {case_id} under {protocol_title}."
    else:
        proto_urgency = protocol.urgency if isinstance(protocol, ProtocolDefinition) else protocol.get("urgency", UrgencyLevel.MEDIUM)
        urgency = UrgencyLevel(proto_urgency) if isinstance(proto_urgency, str) else proto_urgency
        resolved_task_type = task_type or "protocol_followup"
        selected_text = result.selected_option or "Standard clinical protocol regimen"
        ladder_level = result.selected_ladder_level or "active"
        description = (
            f"Follow-up verification for {protocol_title} ({case_id}): "
            f"Monitor response under [{ladder_level}] plan: {selected_text}"
        )
        reason = None

    assigned_owner = owner or "Local Health Worker"
    escalation_path = custom_escalation_path or get_default_escalation_path(urgency)

    create_payload = FollowUpCreate(
        case_id=case_id,
        protocol_id=protocol_id,
        task_type=resolved_task_type,
        description=description,
        urgency=urgency,
        owner=assigned_owner,
        escalation_path=escalation_path,
        escalation_reason=reason,
    )

    return create_follow_up(create_payload, db_path=db_path)
