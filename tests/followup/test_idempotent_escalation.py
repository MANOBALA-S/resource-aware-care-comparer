"""Tests verifying strict idempotency of the escalation scheduler.

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


def test_idempotent_escalation_10_iterations(test_db: Path) -> None:
    """Test that running the scheduler 10 consecutive times does NOT create duplicate escalation events."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    due_time = base_time - timedelta(hours=3)
    esc_due_time = base_time - timedelta(hours=1)

    payload = FollowUpCreate(
        case_id="SYNTH-CASE-030",
        protocol_id="PROTO-001",
        task_type="vitals_check",
        description="Idempotency testing follow-up task",
        urgency=UrgencyLevel.HIGH,
        owner="Local Health Worker",
        due_at=due_time.isoformat(),
        escalation_due_at=esc_due_time.isoformat(),
        escalation_path=["Local Health Worker", "Site Coordinator", "Regional Clinical Supervisor"],
    )
    fup = create_follow_up(payload, db_path=test_db)

    # First run: should trigger 1 overdue + 1 escalation
    first_summary = check_overdue_followups(now=base_time, db_path=test_db)
    assert first_summary["overdue_count"] == 1
    assert first_summary["escalated_count"] == 1
    assert first_summary["failed_count"] == 0

    # Next 9 runs: should perform 0 actions (idempotent no-op)
    for i in range(2, 11):
        subsequent_summary = check_overdue_followups(now=base_time, db_path=test_db)
        assert subsequent_summary["overdue_count"] == 0, f"Run {i} triggered duplicate overdue!"
        assert subsequent_summary["escalated_count"] == 0, f"Run {i} triggered duplicate escalation!"
        assert subsequent_summary["failed_count"] == 0, f"Run {i} triggered duplicate failure!"

    # Verify database state
    reloaded = get_follow_up(fup.follow_up_id, db_path=test_db)
    assert reloaded is not None
    assert reloaded.status == FollowUpStatus.ESCALATED
    assert reloaded.escalation_status == EscalationStatus.ESCALATED
    assert reloaded.owner == "Site Coordinator"

    # Verify audit events: exactly 3 events total (1 CREATED, 1 OVERDUE, 1 ESCALATION_TRIGGERED)
    events = get_escalation_events(fup.follow_up_id, db_path=test_db)
    assert len(events) == 3

    esc_events = [e for e in events if e.event_type == EventType.ESCALATION_TRIGGERED]
    assert len(esc_events) == 1
    assert esc_events[0].escalation_target == "Site Coordinator"
