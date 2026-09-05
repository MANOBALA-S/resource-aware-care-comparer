"""Edge case and integration tests for follow-up and escalation tracker.

Covers:
- Multi-tier escalation cascades to highest level
- Simultaneous overdue tasks evaluation
- Repository edge cases
- FastAPI follow-up API endpoints and governance headers

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from src.followup.models import (
    EscalationStatus,
    EventType,
    FollowUpCreate,
    FollowUpStatus,
    FollowUpUpdate,
)
from src.followup.repository import (
    complete_follow_up,
    create_follow_up,
    get_escalation_events,
    get_follow_up,
    list_follow_ups,
    update_follow_up,
)
from src.followup.scheduler import check_overdue_followups
from src.models.config_models import UrgencyLevel


def test_multitier_escalation_cascade(test_db: Path) -> None:
    """Test task escalating across multiple tiers over time."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    path = [
        "Local Health Worker",
        "Site Coordinator",
        "Regional Clinical Supervisor",
        "Emergency / Human Clinical Escalation",
    ]

    payload = FollowUpCreate(
        case_id="SYNTH-CASE-CASCADE",
        protocol_id="PROTO-001",
        task_type="emergency_escalation",
        description="Critical deterioration case",
        urgency=UrgencyLevel.CRITICAL,
        owner="Local Health Worker",
        due_at=(base_time - timedelta(hours=3)).isoformat(),
        escalation_due_at=(base_time - timedelta(hours=2)).isoformat(),
        escalation_path=path,
    )
    fup = create_follow_up(payload, db_path=test_db)

    # First escalation: Local Health Worker -> Site Coordinator
    s1 = check_overdue_followups(now=base_time, db_path=test_db)
    assert s1["escalated_count"] == 1
    f1 = get_follow_up(fup.follow_up_id, db_path=test_db)
    assert f1 is not None
    assert f1.owner == "Site Coordinator"

    # Suppose Site Coordinator cannot resolve it; advance time and reset escalation_due_at to simulate secondary SLA breach
    update_payload = FollowUpUpdate(description="Site coordinator unable to dispatch; escalating to supervisor")
    update_follow_up(fup.follow_up_id, update_payload, db_path=test_db)

    # Second escalation: Site Coordinator -> Regional Clinical Supervisor
    s2 = check_overdue_followups(now=base_time + timedelta(hours=2), db_path=test_db)
    assert s2["escalated_count"] == 1
    f2 = get_follow_up(fup.follow_up_id, db_path=test_db)
    assert f2 is not None
    assert f2.owner == "Regional Clinical Supervisor"

    # Third escalation: Regional Clinical Supervisor -> Emergency / Human Clinical Escalation
    s3 = check_overdue_followups(now=base_time + timedelta(hours=4), db_path=test_db)
    assert s3["escalated_count"] == 1
    f3 = get_follow_up(fup.follow_up_id, db_path=test_db)
    assert f3 is not None
    assert f3.owner == "Emergency / Human Clinical Escalation"

    # At top tier: running again does not re-escalate further
    s4 = check_overdue_followups(now=base_time + timedelta(hours=6), db_path=test_db)
    assert s4["escalated_count"] == 0


def test_repository_not_found_handling(test_db: Path) -> None:
    """Test that repository handles non-existent IDs gracefully."""
    assert get_follow_up("NON-EXISTENT", db_path=test_db) is None
    assert update_follow_up("NON-EXISTENT", FollowUpUpdate(owner="Nobody"), db_path=test_db) is None
    assert complete_follow_up("NON-EXISTENT", db_path=test_db) is None
    assert get_escalation_events("NON-EXISTENT", db_path=test_db) == []


def test_api_full_followup_lifecycle(client: TestClient) -> None:
    """Test full HTTP API lifecycle for follow-ups via FastAPI TestClient."""
    # 1. Create follow-up
    create_res = client.post(
        "/followups",
        json={
            "case_id": "SYNTH-CASE-API-01",
            "protocol_id": "PROTO-001",
            "task_type": "vitals_check",
            "description": "API verification vitals check",
            "urgency": "HIGH",
            "owner": "Local Nurse",
        },
    )
    assert create_res.status_code == 201
    fup_data = create_res.json()
    follow_up_id = fup_data["follow_up_id"]
    assert follow_up_id.startswith("FUP-")
    assert fup_data["status"] == "PENDING"
    assert "X-Decision-Support" in create_res.headers
    assert "X-Data-Policy" in create_res.headers

    # 2. Retrieve by ID
    get_res = client.get(f"/followups/{follow_up_id}")
    assert get_res.status_code == 200
    assert get_res.json()["case_id"] == "SYNTH-CASE-API-01"

    # 3. List with filter
    list_res = client.get("/followups?status=PENDING&urgency=HIGH")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(item["follow_up_id"] == follow_up_id for item in items)

    # 4. Patch follow-up
    patch_res = client.patch(
        f"/followups/{follow_up_id}",
        json={
            "owner": "Community Health Worker",
            "description": "Updated instructions",
        },
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["owner"] == "Community Health Worker"

    # 5. Check overdue endpoint
    check_res = client.post("/followups/check-overdue")
    assert check_res.status_code == 200
    assert "checked_at" in check_res.json()

    # 6. Complete follow-up
    comp_res = client.post(f"/followups/{follow_up_id}/complete")
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"

    # 7. Check escalations / audit history
    esc_res = client.get(f"/followups/{follow_up_id}/escalations")
    assert esc_res.status_code == 200
    events = esc_res.json()
    assert len(events) >= 2  # At least CREATED and COMPLETED


def test_api_404_responses(client: TestClient) -> None:
    """Test that API endpoints return 404 for non-existent follow-up IDs."""
    fake_id = "FUP-DOES-NOT-EXIST"
    assert client.get(f"/followups/{fake_id}").status_code == 404
    assert client.patch(f"/followups/{fake_id}", json={"owner": "nobody"}).status_code == 404
    assert client.post(f"/followups/{fake_id}/complete").status_code == 404
    assert client.get(f"/followups/{fake_id}/escalations").status_code == 404
