"""Tests for hierarchical escalation paths and milestone transitions.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from src.followup.models import (
    EscalationStatus,
    EventType,
    FollowUpCreate,
    FollowUpStatus,
)
from src.followup.repository import (
    complete_follow_up,
    create_follow_up,
    get_escalation_events,
    get_follow_up,
)
from src.followup.scheduler import check_overdue_followups
from src.models.config_models import UrgencyLevel


def test_escalation_to_next_tier(test_db: Path) -> None:
    """Test that breaching escalation SLA reassigns task to next tier in ladder."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    due_time = base_time + timedelta(hours=1)
    esc_due_time = base_time + timedelta(hours=2)

    payload = FollowUpCreate(
        case_id="SYNTH-CASE-020",
        protocol_id="PROTO-001",
        task_type="emergency_escalation",
        description="Patient in critical state, monitor transfer",
        urgency=UrgencyLevel.CRITICAL,
        owner="Local Health Worker",
        due_at=due_time.isoformat(),
        escalation_due_at=esc_due_time.isoformat(),
        escalation_path=[
            "Local Health Worker",
            "Site Coordinator",
            "Regional Clinical Supervisor",
            "Emergency / Human Clinical Escalation",
        ],
    )
    fup = create_follow_up(payload, db_path=test_db)

    # Evaluate at 2 hours and 30 minutes (past escalation_due_at)
    eval_time = base_time + timedelta(hours=2, minutes=30)
    summary = check_overdue_followups(now=eval_time, db_path=test_db)

    assert summary["overdue_count"] == 1
    assert summary["escalated_count"] == 1

    reloaded = get_follow_up(fup.follow_up_id, db_path=test_db)
    assert reloaded is not None
    assert reloaded.status == FollowUpStatus.ESCALATED
    assert reloaded.escalation_status == EscalationStatus.ESCALATED
    assert reloaded.owner == "Site Coordinator"
    assert "Site Coordinator" in (reloaded.escalation_reason or "")

    # Check audit events: created -> overdue -> escalation triggered
    events = get_escalation_events(fup.follow_up_id, db_path=test_db)
    assert len(events) == 3
    assert events[0].event_type == EventType.FOLLOW_UP_CREATED
    assert events[1].event_type == EventType.FOLLOW_UP_OVERDUE
    assert events[2].event_type == EventType.ESCALATION_TRIGGERED
    assert events[2].escalation_target == "Site Coordinator"


def test_completion_of_escalated_task(test_db: Path) -> None:
    """Test that completing an escalated task transitions to COMPLETED with audit event."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    payload = FollowUpCreate(
        case_id="SYNTH-CASE-021",
        protocol_id="PROTO-001",
        task_type="vitals_check",
        description="Escalated vitals check",
        urgency=UrgencyLevel.HIGH,
        owner="Site Coordinator",
        due_at=(base_time - timedelta(hours=5)).isoformat(),
        escalation_due_at=(base_time - timedelta(hours=1)).isoformat(),
        escalation_path=["Site Coordinator", "Regional Clinical Supervisor"],
    )
    fup = create_follow_up(payload, db_path=test_db)

    # Trigger escalation
    check_overdue_followups(now=base_time, db_path=test_db)

    # Now complete it
    completed = complete_follow_up(fup.follow_up_id, db_path=test_db, now=base_time)
    assert completed is not None
    assert completed.status == FollowUpStatus.COMPLETED
    assert completed.completed_at is not None

    events = get_escalation_events(fup.follow_up_id, db_path=test_db)
    comp_events = [e for e in events if e.event_type == EventType.FOLLOW_UP_COMPLETED]
    assert len(comp_events) == 1
