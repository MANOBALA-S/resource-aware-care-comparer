"""Tests for overdue detection logic in follow-up scheduler.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from src.followup.models import (
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


def test_task_not_overdue_before_deadline(test_db: Path) -> None:
    """Test that task due in future remains PENDING."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    payload = FollowUpCreate(
        case_id="SYNTH-CASE-010",
        protocol_id="PROTO-001",
        task_type="vitals_check",
        description="Routine check",
        urgency=UrgencyLevel.HIGH,
        owner="Local Health Worker",
        due_at=(base_time + timedelta(hours=24)).isoformat(),
        escalation_due_at=(base_time + timedelta(hours=28)).isoformat(),
    )
    fup = create_follow_up(payload, db_path=test_db)

    # Check 5 hours into the 24 hour window
    summary = check_overdue_followups(now=base_time + timedelta(hours=5), db_path=test_db)
    assert summary["overdue_count"] == 0
    assert summary["escalated_count"] == 0

    reloaded = get_follow_up(fup.follow_up_id, db_path=test_db)
    assert reloaded is not None
    assert reloaded.status == FollowUpStatus.PENDING


def test_task_marked_overdue_after_deadline(test_db: Path) -> None:
    """Test that task is marked OVERDUE once due_at is passed."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    due_time = base_time + timedelta(hours=24)
    esc_due_time = base_time + timedelta(hours=28)

    payload = FollowUpCreate(
        case_id="SYNTH-CASE-011",
        protocol_id="PROTO-001",
        task_type="vitals_check",
        description="High urgency vitals check",
        urgency=UrgencyLevel.HIGH,
        owner="Local Health Worker",
        due_at=due_time.isoformat(),
        escalation_due_at=esc_due_time.isoformat(),
    )
    fup = create_follow_up(payload, db_path=test_db)

    # Advance time past due_at (25 hours) but before escalation_due_at (28 hours)
    eval_time = base_time + timedelta(hours=25)
    summary = check_overdue_followups(now=eval_time, db_path=test_db)

    assert summary["overdue_count"] == 1
    assert summary["escalated_count"] == 0

    reloaded = get_follow_up(fup.follow_up_id, db_path=test_db)
    assert reloaded is not None
    assert reloaded.status == FollowUpStatus.OVERDUE

    # Verify audit event
    events = get_escalation_events(fup.follow_up_id, db_path=test_db)
    overdue_events = [e for e in events if e.event_type == EventType.FOLLOW_UP_OVERDUE]
    assert len(overdue_events) == 1
    assert overdue_events[0].previous_status == FollowUpStatus.PENDING.value
    assert overdue_events[0].new_status == FollowUpStatus.OVERDUE.value


def test_completed_task_not_marked_overdue(test_db: Path) -> None:
    """Test that completed tasks are ignored and never marked OVERDUE."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    due_time = base_time + timedelta(hours=1)

    payload = FollowUpCreate(
        case_id="SYNTH-CASE-012",
        protocol_id="PROTO-001",
        task_type="vitals_check",
        description="Quick check",
        urgency=UrgencyLevel.CRITICAL,
        owner="Local Health Worker",
        due_at=due_time.isoformat(),
        escalation_due_at=(due_time + timedelta(hours=1)).isoformat(),
    )
    fup = create_follow_up(payload, db_path=test_db)

    # Complete before deadline
    complete_follow_up(fup.follow_up_id, db_path=test_db, now=base_time + timedelta(minutes=30))

    # Evaluate 10 hours later
    summary = check_overdue_followups(now=base_time + timedelta(hours=10), db_path=test_db)
    assert summary["overdue_count"] == 0
    assert summary["escalated_count"] == 0

    reloaded = get_follow_up(fup.follow_up_id, db_path=test_db)
    assert reloaded is not None
    assert reloaded.status == FollowUpStatus.COMPLETED
