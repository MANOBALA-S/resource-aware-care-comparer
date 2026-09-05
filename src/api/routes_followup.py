"""FastAPI routes for Follow-Up & Escalation tracking workflows.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from src.followup.models import (
    EscalationEvent,
    EscalationStatus,
    FollowUp,
    FollowUpCreate,
    FollowUpStatus,
    FollowUpUpdate,
)
from src.followup.repository import (
    complete_follow_up,
    create_follow_up,
    escalate_follow_up,
    get_escalation_events,
    get_follow_up,
    list_follow_ups,
    update_follow_up,
)
from src.followup.scheduler import check_overdue_followups
from src.models.config_models import UrgencyLevel

router = APIRouter(prefix="/followups", tags=["Follow-Ups & Escalation"])


@router.post(
    "",
    response_model=FollowUp,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new operational follow-up task",
)
def create_new_followup(payload: FollowUpCreate) -> FollowUp:
    """Create a tracked follow-up task with deterministic deadlines and escalation ladder.

    - **case_id**: Synthetic case identifier
    - **protocol_id**: Synthetic protocol identifier
    - **task_type**: e.g., 'vitals_check', 'medication_refill', 'wound_review'
    - **urgency**: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    - **owner**: Responsible individual or clinical role
    """
    return create_follow_up(payload)


@router.get(
    "",
    response_model=List[FollowUp],
    summary="List all follow-up tasks with optional filtering",
)
def get_all_followups(
    status: Optional[FollowUpStatus] = Query(None, description="Filter by task status"),
    urgency: Optional[UrgencyLevel] = Query(None, description="Filter by urgency tier"),
    owner: Optional[str] = Query(None, description="Filter by assigned owner"),
    case_id: Optional[str] = Query(None, description="Filter by synthetic case ID"),
    escalation_status: Optional[EscalationStatus] = Query(None, description="Filter by escalation status"),
) -> List[FollowUp]:
    """Retrieve all tracked follow-ups with optional filters."""
    return list_follow_ups(
        status=status,
        urgency=urgency,
        owner=owner,
        case_id=case_id,
        escalation_status=escalation_status,
    )


@router.post(
    "/check-overdue",
    response_model=Dict[str, Any],
    summary="Evaluate active follow-up deadlines and trigger escalations",
)
def run_overdue_check() -> Dict[str, Any]:
    """Evaluate all active follow-ups against current UTC time.

    Marks breached tasks as OVERDUE, triggers idempotent hierarchical escalations,
    and flags configuration failures if an escalation path is missing.
    """
    return check_overdue_followups()


@router.get(
    "/summary",
    response_model=Dict[str, Any],
    summary="Retrieve operational summary counters for follow-up dashboard",
)
def get_followups_summary() -> Dict[str, Any]:
    """Return counts of total, pending, overdue, escalated, and completed tasks."""
    all_tasks = list_follow_ups()
    total = len(all_tasks)
    pending = sum(1 for t in all_tasks if t.status in (FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS))
    overdue = sum(1 for t in all_tasks if t.status == FollowUpStatus.OVERDUE)
    escalated = sum(1 for t in all_tasks if t.status == FollowUpStatus.ESCALATED or t.escalation_status == EscalationStatus.ESCALATED)
    completed = sum(1 for t in all_tasks if t.status == FollowUpStatus.COMPLETED)
    failed = sum(1 for t in all_tasks if t.escalation_status == EscalationStatus.ESCALATION_FAILED)

    return {
        "total_followups": total,
        "pending_count": pending,
        "overdue_count": overdue,
        "escalated_count": escalated,
        "completed_count": completed,
        "escalation_failed_count": failed,
    }


@router.get(
    "/{follow_up_id}",
    response_model=FollowUp,
    summary="Retrieve details of a single follow-up task",
)
def get_single_followup(follow_up_id: str) -> FollowUp:
    """Retrieve full details of a specific follow-up task by its ID."""
    fup = get_follow_up(follow_up_id)
    if not fup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Follow-up task '{follow_up_id}' not found.",
        )
    return fup


@router.patch(
    "/{follow_up_id}",
    response_model=FollowUp,
    summary="Update an existing follow-up task",
)
def patch_followup(follow_up_id: str, payload: FollowUpUpdate) -> FollowUp:
    """Update task status, reassign owner, or modify instructions."""
    updated = update_follow_up(follow_up_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Follow-up task '{follow_up_id}' not found.",
        )
    return updated


@router.post(
    "/{follow_up_id}/complete",
    response_model=FollowUp,
    summary="Mark a follow-up task as successfully completed",
)
def complete_single_followup(follow_up_id: str) -> FollowUp:
    """Mark follow-up task as COMPLETED and record audit event."""
    completed = complete_follow_up(follow_up_id)
    if not completed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Follow-up task '{follow_up_id}' not found.",
        )
    return completed


@router.post(
    "/{follow_up_id}/escalate",
    response_model=FollowUp,
    summary="Escalate a follow-up task along its escalation hierarchy",
)
def trigger_manual_escalation(
    follow_up_id: str,
    reason: Optional[str] = Query(default=None, description="Reason for escalation"),
) -> FollowUp:
    """Escalate task to next tier in escalation ladder or flag configuration failure."""
    fup = get_follow_up(follow_up_id)
    if not fup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Follow-up task '{follow_up_id}' not found.",
        )

    path = fup.escalation_path or []
    if not path:
        # Failure: no escalation path defined!
        escalated = escalate_follow_up(
            follow_up_id=follow_up_id,
            target=None,
            reason=reason or "Escalation configuration error: No escalation path configured.",
            failed=True,
        )
    else:
        current_owner = fup.owner
        target = None
        for idx, role in enumerate(path):
            if role == current_owner:
                if idx + 1 < len(path):
                    target = path[idx + 1]
                break
        if not target:
            target = path[0] if current_owner not in path else path[-1]

        escalated = escalate_follow_up(
            follow_up_id=follow_up_id,
            target=target,
            reason=reason or f"Manual clinical/operational escalation to {target}.",
            failed=False,
        )

    if not escalated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update escalation status in database.",
        )
    return escalated


@router.get(
    "/{follow_up_id}/escalations",
    response_model=List[EscalationEvent],
    summary="Retrieve full audit and escalation history for a follow-up",
)
def get_followup_audit_trail(follow_up_id: str) -> List[EscalationEvent]:
    """Retrieve the chronological audit log of milestones, breaches, and escalations."""
    fup = get_follow_up(follow_up_id)
    if not fup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Follow-up task '{follow_up_id}' not found.",
        )
    return get_escalation_events(follow_up_id)
