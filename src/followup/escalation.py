"""Escalation rules, SLA calculations, and hierarchical path resolution.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.config import PROJECT_ROOT
from src.followup.models import FollowUp
from src.models.config_models import UrgencyLevel

RULES_PATH = PROJECT_ROOT / "config" / "followup_rules.json"

FALLBACK_RULES = {
    "CRITICAL": {
        "due_hours": 1,
        "escalation_hours": 1,
        "default_escalation_path": [
            "Local Health Worker",
            "Site Coordinator",
            "Regional Clinical Supervisor",
            "Emergency / Human Clinical Escalation",
        ],
    },
    "HIGH": {
        "due_hours": 24,
        "escalation_hours": 4,
        "default_escalation_path": [
            "Local Health Worker",
            "Site Coordinator",
            "Regional Clinical Supervisor",
            "Emergency / Human Clinical Escalation",
        ],
    },
    "MEDIUM": {
        "due_hours": 72,
        "escalation_hours": 24,
        "default_escalation_path": [
            "Local Health Worker",
            "Site Coordinator",
            "Regional Clinical Supervisor",
        ],
    },
    "LOW": {
        "due_hours": 168,
        "escalation_hours": 48,
        "default_escalation_path": [
            "Local Health Worker",
            "Site Coordinator",
        ],
    },
}


def load_followup_rules(rules_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configurable follow-up SLA rules from JSON file with built-in fallbacks."""
    target_path = rules_path or RULES_PATH
    if not target_path.is_file():
        return FALLBACK_RULES
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("rules", FALLBACK_RULES)
    except Exception:
        return FALLBACK_RULES


def get_followup_rule(urgency: UrgencyLevel | str, rules_path: Optional[Path] = None) -> Dict[str, Any]:
    """Retrieve SLA timing configuration for a specific clinical urgency."""
    rules = load_followup_rules(rules_path)
    key = urgency.value if isinstance(urgency, UrgencyLevel) else str(urgency).upper()
    return rules.get(key, FALLBACK_RULES.get(key, FALLBACK_RULES["MEDIUM"]))


def calculate_deadlines(
    urgency: UrgencyLevel | str,
    start_time: Optional[datetime] = None,
    rules_path: Optional[Path] = None,
) -> Tuple[datetime, datetime]:
    """Calculate due_at and escalation_due_at deadlines based on clinical urgency SLA.

    Args:
        urgency: Urgency tier (CRITICAL, HIGH, MEDIUM, LOW)
        start_time: Base reference datetime (defaults to current UTC time)
        rules_path: Optional override path for rules file

    Returns:
        Tuple of (due_at, escalation_due_at) datetime objects.
    """
    base_dt = start_time or datetime.now(timezone.utc)
    rule = get_followup_rule(urgency, rules_path)

    due_hours = rule.get("due_hours", 24)
    escalation_hours = rule.get("escalation_hours", 4)

    due_at = base_dt + timedelta(hours=due_hours)
    escalation_due_at = due_at + timedelta(hours=escalation_hours)

    return due_at, escalation_due_at


def get_default_escalation_path(
    urgency: UrgencyLevel | str,
    rules_path: Optional[Path] = None,
) -> List[str]:
    """Retrieve the standard hierarchical escalation path for an urgency level."""
    rule = get_followup_rule(urgency, rules_path)
    return list(rule.get("default_escalation_path", []))


def resolve_next_escalation_target(follow_up: FollowUp) -> Tuple[Optional[str], bool]:
    """Determine the next recipient in the escalation hierarchy.

    Safety rule: If escalation_path is empty or missing, returns (None, True)
    indicating a configuration failure state.

    Args:
        follow_up: FollowUp task model.

    Returns:
        Tuple of (next_target, is_missing_contact_failure):
            - next_target: The next role/individual string, or None.
            - is_missing_contact_failure: True if path was absent/empty or unresolvable.
    """
    path = follow_up.escalation_path
    if not path or len(path) == 0:
        return None, True

    current_owner = follow_up.owner.strip().lower()

    # Find position of current owner in the path
    matched_index: Optional[int] = None
    for idx, role in enumerate(path):
        if role.strip().lower() == current_owner or role.strip().lower() in current_owner:
            matched_index = idx
            break

    if matched_index is None:
        # Current owner is not in path; escalate to the first defined target in path
        return path[0], False

    if matched_index + 1 < len(path):
        # Escalate to next tier in the path
        return path[matched_index + 1], False

    # Already at the highest tier in the path
    return path[-1], False
