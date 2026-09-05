"""Tests for missing escalation contact / configuration failure handling.

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
    create_follow_up,
    get_escalation_events,
    get_follow_up,
)
from src.followup.scheduler import check_overdue_followups
from src.models.config_models import UrgencyLevel


def test_missing_escalation_contact_triggers_failed_status(test_db: Path) -> None:
    """Test that empty escalation path triggers ESCALATION_FAILED and requires fallback owner."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    due_time = base_time - timedelta(hours=2)
    esc_due_time = base_time - timedelta(hours=1)

    payload = FollowUpCreate(
        case_id="SYNTH-CASE-040",
        protocol_id="PROTO-001",
        task_type="unassigned_check",
        description="Missing contact test case",
        urgency=UrgencyLevel.HIGH,
        owner="Local Health Worker",
        due_at=due_time.isoformat(),
        escalation_due_at=esc_due_time.isoformat(),
        escalation_path=[],  # Intentionally empty!
    )
    fup = create_follow_up(payload, db_path=test_db)

    # Trigger scheduler
    summary = check_overdue_followups(now=base_time, db_path=test_db)
    assert summary["overdue_count"] == 1
    assert summary["failed_count"] == 1
    assert summary["escalated_count"] == 0

    # Verify action flagged fallback_owner_required
    failed_actions = [a for a in summary["actions"] if a["action"] == "ESCALATION_FAILED"]
    assert len(failed_actions) == 1
    assert failed_actions[0].get("fallback_owner_required") is True

    # Verify database record
    reloaded = get_follow_up(fup.follow_up_id, db_path=test_db)
    assert reloaded is not None
    assert reloaded.status == FollowUpStatus.ESCALATED
    assert reloaded.escalation_status == EscalationStatus.ESCALATION_FAILED
    assert "Configuration failure" in (reloaded.escalation_reason or "")

    # Verify audit event
    events = get_escalation_events(fup.follow_up_id, db_path=test_db)
    fail_events = [e for e in events if e.event_type == EventType.ESCALATION_FAILED]
    assert len(fail_events) == 1
    assert fail_events[0].new_status == FollowUpStatus.ESCALATED.value


def test_missing_contact_scheduler_idempotency(test_db: Path) -> None:
    """Test that missing contact failures are not duplicated across multiple scheduler runs."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    payload = FollowUpCreate(
        case_id="SYNTH-CASE-041",
        protocol_id="PROTO-001",
        task_type="unassigned_check",
        description="Idempotency missing contact test case",
        urgency=UrgencyLevel.CRITICAL,
        owner="Local Health Worker",
        due_at=(base_time - timedelta(hours=2)).isoformat(),
        escalation_due_at=(base_time - timedelta(hours=1)).isoformat(),
        escalation_path=[],
    )
    fup = create_follow_up(payload, db_path=test_db)

    # First run
    summary1 = check_overdue_followups(now=base_time, db_path=test_db)
    assert summary1["failed_count"] == 1

    # Runs 2 through 5
    for _ in range(4):
        summary = check_overdue_followups(now=base_time, db_path=test_db)
        assert summary["failed_count"] == 0

    events = get_escalation_events(fup.follow_up_id, db_path=test_db)
    fail_events = [e for e in events if e.event_type == EventType.ESCALATION_FAILED]
    assert len(fail_events) == 1
