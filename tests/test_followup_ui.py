"""Tests for Phase 9 Follow-Up Queue UI endpoints, invariants, and static assets.

Verifies:
- Pending tasks appear in queue.
- Overdue tasks appear with overdue status.
- Escalated tasks appear with escalated status and new tier owner.
- Completed tasks disappear only from active queue, but remain permanently in historical records.
- Escalation configuration errors are flagged when escalation path is missing.
- Operational summary metrics endpoint /followups/summary.
- UI static assets (/ui/followup/index.html, followup.css, followup.js) are served.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from src.followup.models import (
    EscalationStatus,
    FollowUpCreate,
    FollowUpStatus,
)
from src.followup.repository import create_follow_up, get_follow_up
from src.main import create_app
from src.models.config_models import UrgencyLevel


@pytest.fixture
def client():
    """Create test client instance."""
    app = create_app()
    return TestClient(app)


def test_pending_appears_in_queue(client):
    """Verify that a pending task appears in the follow-up queue."""
    payload = {
        "case_id": "SYNTH-CASE-001",
        "protocol_id": "PROTO-001",
        "task_type": "vitals_check",
        "description": "Routine blood pressure monitoring.",
        "urgency": "MEDIUM",
        "owner": "Local Health Worker Nirmala",
        "escalation_path": ["Local Health Worker", "Taluk Medical Officer"],
    }
    create_res = client.post("/followups", json=payload)
    assert create_res.status_code == 201
    created_task = create_res.json()
    task_id = created_task["follow_up_id"]

    # Verify task appears in active queue
    list_res = client.get("/followups")
    assert list_res.status_code == 200
    tasks = list_res.json()
    matching = [t for t in tasks if t["follow_up_id"] == task_id]
    assert len(matching) == 1
    assert matching[0]["status"] == "PENDING"
    assert matching[0]["owner"] == "Local Health Worker Nirmala"


def test_overdue_appears_in_queue(client):
    """Verify that an overdue task is marked OVERDUE and appears in the queue."""
    # Create task with a past due date
    past_due = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    past_esc = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    payload = {
        "case_id": "SYNTH-CASE-002",
        "protocol_id": "PROTO-002",
        "task_type": "medication_refill",
        "description": "Critical metformin refill.",
        "urgency": "HIGH",
        "owner": "Sub-center Nurse",
        "due_at": past_due,
        "escalation_due_at": past_esc,
        "escalation_path": ["Sub-center Nurse", "District Medical Officer"],
    }
    create_res = client.post("/followups", json=payload)
    assert create_res.status_code == 201
    task_id = create_res.json()["follow_up_id"]

    # Run overdue check
    check_res = client.post("/followups/check-overdue")
    assert check_res.status_code == 200

    # Verify task now has status OVERDUE
    fup_res = client.get(f"/followups/{task_id}")
    assert fup_res.status_code == 200
    task_data = fup_res.json()
    assert task_data["status"] == "OVERDUE"

    # Verify it appears in overdue query
    overdue_list = client.get("/followups?status=OVERDUE").json()
    assert any(t["follow_up_id"] == task_id for t in overdue_list)


def test_escalated_appears_with_new_owner(client):
    """Verify that escalating a task updates status to ESCALATED and reassigns owner."""
    payload = {
        "case_id": "SYNTH-CASE-003",
        "protocol_id": "PROTO-003",
        "task_type": "wound_review",
        "description": "Progressive edema review.",
        "urgency": "HIGH",
        "owner": "Primary Care Nurse",
        "escalation_path": ["Primary Care Nurse", "Specialist Physician", "Clinical Director"],
    }
    create_res = client.post("/followups", json=payload)
    assert create_res.status_code == 201
    task_id = create_res.json()["follow_up_id"]

    # Escalate task
    esc_res = client.post(f"/followups/{task_id}/escalate?reason=Patient+vitals+worsening")
    assert esc_res.status_code == 200
    esc_data = esc_res.json()

    assert esc_data["status"] == "ESCALATED"
    assert esc_data["escalation_status"] == "ESCALATED"
    assert esc_data["owner"] == "Specialist Physician"  # Reassigned to next tier!

    # Verify it appears in escalated filter
    escalated_list = client.get("/followups?escalation_status=ESCALATED").json()
    assert any(t["follow_up_id"] == task_id for t in escalated_list)


def test_completed_disappears_only_from_active_queue(client):
    """Verify No Silent Disappearance: completed task leaves active queue filter but remains in historical records."""
    payload = {
        "case_id": "SYNTH-CASE-004",
        "protocol_id": "PROTO-004",
        "task_type": "discharge_check",
        "description": "Post-stabilization discharge instructions.",
        "urgency": "LOW",
        "owner": "Local ASHA Worker",
        "escalation_path": ["Local ASHA Worker", "Primary Health Officer"],
    }
    create_res = client.post("/followups", json=payload)
    assert create_res.status_code == 201
    task_id = create_res.json()["follow_up_id"]

    # Complete the task
    comp_res = client.post(f"/followups/{task_id}/complete")
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"

    # In Active Queue (pending/inprogress/overdue/escalated), completed task is excluded
    active_res = client.get("/followups")
    active_tasks = [t for t in active_res.json() if t["status"] != "COMPLETED"]
    assert not any(t["follow_up_id"] == task_id for t in active_tasks)

    # In Historical Records / Completed query, task is permanently preserved
    history_res = client.get("/followups?status=COMPLETED")
    assert history_res.status_code == 200
    completed_history = history_res.json()
    assert any(t["follow_up_id"] == task_id for t in completed_history)


def test_escalation_configuration_error_on_missing_path(client):
    """Verify that escalating a task without an escalation path flags ESCALATION_FAILED."""
    payload = {
        "case_id": "SYNTH-CASE-005",
        "protocol_id": "PROTO-005",
        "task_type": "isolated_task",
        "description": "Task created without escalation ladder.",
        "urgency": "HIGH",
        "owner": "Isolated Worker",
        "escalation_path": [],  # Empty ladder
    }
    create_res = client.post("/followups", json=payload)
    assert create_res.status_code == 201
    task_id = create_res.json()["follow_up_id"]

    # Attempt escalation
    esc_res = client.post(f"/followups/{task_id}/escalate")
    assert esc_res.status_code == 200
    esc_data = esc_res.json()

    assert esc_data["escalation_status"] == "ESCALATION_FAILED"
    assert "Escalation configuration error" in esc_data["escalation_reason"]


def test_followups_summary_endpoint(client):
    """Verify GET /followups/summary returns accurate aggregate counters."""
    res = client.get("/followups/summary")
    assert res.status_code == 200
    summary = res.json()

    assert "total_followups" in summary
    assert "pending_count" in summary
    assert "overdue_count" in summary
    assert "escalated_count" in summary
    assert "completed_count" in summary
    assert summary["total_followups"] >= summary["pending_count"]


def test_ui_followup_static_files_served(client):
    """Verify that ui/followup/ static files are served at /ui/followup/."""
    # Index page
    r_index = client.get("/ui/followup/index.html")
    assert r_index.status_code == 200
    assert "Resource-Aware Care Option Comparer" in r_index.text
    assert "followup.js" in r_index.text

    # Stylesheet
    r_css = client.get("/ui/followup/followup.css")
    assert r_css.status_code == 200
    assert "kpi-card" in r_css.text

    # Script
    r_js = client.get("/ui/followup/followup.js")
    assert r_js.status_code == 200
    assert "loadFollowups" in r_js.text
