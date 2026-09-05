"""Tests for follow-up task creation and initialization.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timezone
from pathlib import Path
import pytest

from src.constraint_engine.models import ConstraintEngineResult, LanguageStatus
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
    list_follow_ups,
)
from src.followup.tracker import create_followup_from_evaluation
from src.models.config_models import UrgencyLevel


def test_create_followup_basic(test_db: Path) -> None:
    """Test standard creation of a follow-up task."""
    payload = FollowUpCreate(
        case_id="SYNTH-CASE-001",
        protocol_id="PROTO-001",
        task_type="vitals_check",
        description="Verify blood pressure and heart rate post-consultation",
        urgency=UrgencyLevel.HIGH,
        owner="Local Health Worker",
    )
    fup = create_follow_up(payload, db_path=test_db)

    assert fup.follow_up_id.startswith("FUP-")
    assert fup.case_id == "SYNTH-CASE-001"
    assert fup.protocol_id == "PROTO-001"
    assert fup.task_type == "vitals_check"
    assert fup.urgency == UrgencyLevel.HIGH
    assert fup.owner == "Local Health Worker"
    assert fup.status == FollowUpStatus.PENDING
    assert fup.escalation_status == EscalationStatus.NOT_REQUIRED
    assert fup.governance_notice == "Decision-support prototype — clinician sign-off required."
    assert fup.synthetic_data_notice == "Synthetic data only — no real patient data."

    # Verify audit event was logged
    events = get_escalation_events(fup.follow_up_id, db_path=test_db)
    assert len(events) == 1
    assert events[0].event_type == EventType.FOLLOW_UP_CREATED
    assert events[0].new_status == FollowUpStatus.PENDING.value
    assert events[0].owner == "Local Health Worker"


def test_create_followup_custom_deadlines(test_db: Path) -> None:
    """Test creating a follow-up task with explicit custom deadlines and escalation path."""
    custom_due = "2026-09-10T12:00:00+00:00"
    custom_esc_due = "2026-09-10T16:00:00+00:00"
    custom_path = ["Local Nurse", "Senior Medical Officer"]

    payload = FollowUpCreate(
        case_id="SYNTH-CASE-002",
        protocol_id="PROTO-002",
        task_type="medication_refill",
        description="Dispense emergency maintenance medications",
        urgency=UrgencyLevel.MEDIUM,
        owner="Local Nurse",
        due_at=custom_due,
        escalation_due_at=custom_esc_due,
        escalation_path=custom_path,
    )
    fup = create_follow_up(payload, db_path=test_db)

    assert fup.due_at == custom_due
    assert fup.escalation_due_at == custom_esc_due
    assert fup.escalation_path == custom_path


def test_create_followup_from_evaluation_feasible(test_db: Path) -> None:
    """Test generating a follow-up directly from a feasible constraint engine result."""
    result = ConstraintEngineResult(
        case_id="SYNTH-CASE-003",
        protocol_id="PROTO-003",
        selected_option="Oral rehydration + zinc under community health supervision",
        selected_ladder_level="resource_adapted_alternative",
        feasible=True,
        decision="SELECT_OPTION",
        language_status=LanguageStatus.SUPPORTED,
    )
    case_mock = {"case_id": "SYNTH-CASE-003"}
    proto_mock = {
        "protocol_id": "PROTO-003",
        "title": "Pediatric Dehydration Protocol",
        "urgency": UrgencyLevel.MEDIUM,
    }

    fup = create_followup_from_evaluation(
        result=result,
        case=case_mock,
        protocol=proto_mock,
        owner="Community Health Worker Nirmala",
        db_path=test_db,
    )

    assert fup.case_id == "SYNTH-CASE-003"
    assert fup.protocol_id == "PROTO-003"
    assert fup.urgency == UrgencyLevel.MEDIUM
    assert fup.owner == "Community Health Worker Nirmala"
    assert "Pediatric Dehydration Protocol" in fup.description
    assert "resource_adapted_alternative" in fup.description


def test_create_followup_from_evaluation_immediate_escalation(test_db: Path) -> None:
    """Test generating a follow-up when the constraint engine decides immediate escalation."""
    result = ConstraintEngineResult(
        case_id="SYNTH-CASE-004",
        protocol_id="PROTO-004",
        selected_option=None,
        selected_ladder_level=None,
        feasible=False,
        decision="ESCALATE_IMMEDIATELY",
        escalation_required=True,
        escalation_reason="Severe respiratory distress with oxygen saturation < 88% and no supplemental O2",
        fallback_owner_required=True,
        language_status=LanguageStatus.SUPPORTED,
    )
    case_mock = {"case_id": "SYNTH-CASE-004"}
    proto_mock = {
        "protocol_id": "PROTO-004",
        "title": "Severe Respiratory Distress Protocol",
        "urgency": UrgencyLevel.HIGH,  # Note: Engine should elevate to CRITICAL
    }

    fup = create_followup_from_evaluation(
        result=result,
        case=case_mock,
        protocol=proto_mock,
        owner="Clinic Duty Officer",
        db_path=test_db,
    )

    assert fup.urgency == UrgencyLevel.CRITICAL
    assert fup.task_type == "emergency_escalation"
    assert "URGENT" in fup.description
    assert "Severe respiratory distress" in fup.description
