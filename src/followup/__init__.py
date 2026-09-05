"""Follow-Up & Escalation Tracker package for teleconsultation service workflows.

Ensures that high-priority clinical and operational follow-ups cannot silently disappear.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from src.followup.escalation import (
    calculate_deadlines,
    get_default_escalation_path,
    get_followup_rule,
    load_followup_rules,
    resolve_next_escalation_target,
)
from src.followup.models import (
    EscalationEvent,
    EscalationStatus,
    EventType,
    FollowUp,
    FollowUpCreate,
    FollowUpStatus,
    FollowUpUpdate,
)
from src.followup.repository import (
    DEFAULT_DB_PATH,
    complete_follow_up,
    create_follow_up,
    escalate_follow_up,
    get_escalation_events,
    get_follow_up,
    has_escalation_event_for_target,
    init_db,
    list_follow_ups,
    mark_overdue,
    record_event,
    update_follow_up,
)
from src.followup.scheduler import check_overdue_followups
from src.followup.tracker import create_followup_from_evaluation

__all__ = [
    "DEFAULT_DB_PATH",
    "EscalationEvent",
    "EscalationStatus",
    "EventType",
    "FollowUp",
    "FollowUpCreate",
    "FollowUpStatus",
    "FollowUpUpdate",
    "calculate_deadlines",
    "check_overdue_followups",
    "complete_follow_up",
    "create_follow_up",
    "create_followup_from_evaluation",
    "escalate_follow_up",
    "get_default_escalation_path",
    "get_escalation_events",
    "get_follow_up",
    "get_followup_rule",
    "has_escalation_event_for_target",
    "init_db",
    "list_follow_ups",
    "load_followup_rules",
    "mark_overdue",
    "record_event",
    "resolve_next_escalation_target",
    "update_follow_up",
]
