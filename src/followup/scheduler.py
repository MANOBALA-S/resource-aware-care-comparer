"""Deterministic scheduler and watcher for monitoring follow-up deadlines and executing idempotent escalations.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.followup.escalation import resolve_next_escalation_target
from src.followup.models import (
    EscalationStatus,
    EventType,
    FollowUp,
    FollowUpStatus,
)
from src.followup.repository import (
    escalate_follow_up,
    get_follow_up,
    has_escalation_event_for_target,
    list_follow_ups,
    mark_overdue,
)

logger = logging.getLogger("care_comparer.followup_scheduler")


def _parse_iso(iso_str: str) -> datetime:
    """Parse ISO 8601 string into timezone-aware datetime."""
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def check_overdue_followups(
    now: Optional[datetime] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Inspect all active follow-up tasks, mark overdue, and trigger idempotent escalation.

    Guarantees:
    1. Deterministic evaluation: compares `now` with `due_at` and `escalation_due_at`.
    2. Identity-Based Idempotency: running the scheduler 10 times will not generate duplicate
       escalation events for the same target and breach tier.
    3. Failure-Safe Handling: if escalation is required but escalation_path is missing/empty,
       transitions to ESCALATION_FAILED with fallback_owner_required=True.

    Args:
        now: Reference datetime (defaults to current UTC time).
        db_path: Optional custom path to SQLite database.

    Returns:
        Summary dictionary of actions performed.
    """
    eval_now = now or datetime.now(timezone.utc)
    all_fups = list_follow_ups(db_path=db_path)

    # Consider tasks that are not yet marked COMPLETED
    active_fups = [f for f in all_fups if f.status != FollowUpStatus.COMPLETED]

    overdue_count = 0
    escalated_count = 0
    failed_count = 0
    actions: List[Dict[str, Any]] = []

    for fup in active_fups:
        due_at = _parse_iso(fup.due_at)
        esc_due_at = _parse_iso(fup.escalation_due_at)

        # 1. Check if due date has passed
        if eval_now >= due_at:
            if fup.status in (FollowUpStatus.PENDING, FollowUpStatus.IN_PROGRESS):
                updated = mark_overdue(
                    follow_up_id=fup.follow_up_id,
                    reason=f"SLA due date breached ({fup.due_at})",
                    db_path=db_path,
                    now=eval_now,
                )
                if updated:
                    fup = updated
                    overdue_count += 1
                    actions.append({
                        "follow_up_id": fup.follow_up_id,
                        "action": "MARKED_OVERDUE",
                    })

            # 2. Check if escalation SLA is breached
            if eval_now >= esc_due_at:
                target, is_missing_contact = resolve_next_escalation_target(fup)

                if is_missing_contact:
                    # Missing escalation contact / configuration failure
                    # Idempotency check: verify if ESCALATION_FAILED event already recorded
                    already_failed = has_escalation_event_for_target(
                        follow_up_id=fup.follow_up_id,
                        event_type=EventType.ESCALATION_FAILED,
                        escalation_target=None,
                        db_path=db_path,
                    )

                    if not already_failed:
                        escalate_follow_up(
                            follow_up_id=fup.follow_up_id,
                            target=None,
                            reason="Configuration failure: Escalation SLA breached but no escalation path/contact configured.",
                            failed=True,
                            db_path=db_path,
                            now=eval_now,
                        )
                        failed_count += 1
                        actions.append({
                            "follow_up_id": fup.follow_up_id,
                            "action": "ESCALATION_FAILED",
                            "fallback_owner_required": True,
                        })
                else:
                    # Escalation contact is available
                    # Idempotency check: verify if this task has already been escalated to this target
                    already_escalated = has_escalation_event_for_target(
                        follow_up_id=fup.follow_up_id,
                        event_type=EventType.ESCALATION_TRIGGERED,
                        escalation_target=target,
                        db_path=db_path,
                    )

                    if not already_escalated:
                        escalate_follow_up(
                            follow_up_id=fup.follow_up_id,
                            target=target,
                            reason=f"Escalation SLA breached ({fup.escalation_due_at}): Reassigned to {target}",
                            failed=False,
                            db_path=db_path,
                            now=eval_now,
                        )
                        escalated_count += 1
                        actions.append({
                            "follow_up_id": fup.follow_up_id,
                            "action": "ESCALATED",
                            "new_owner": target,
                        })

    logger.info(
        "Follow-up check completed at %s: %d inspected, %d marked overdue, %d escalated, %d failed",
        eval_now.isoformat(),
        len(active_fups),
        overdue_count,
        escalated_count,
        failed_count,
    )

    return {
        "status": "ok",
        "evaluated_at": eval_now.isoformat(),
        "checked_at": eval_now.isoformat(),
        "total_active": len(active_fups),
        "marked_overdue_count": overdue_count,
        "overdue_count": overdue_count,
        "escalated_count": escalated_count,
        "failed_count": failed_count,
        "actions": actions,
    }
