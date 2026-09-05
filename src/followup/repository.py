"""SQLite repository for persistent follow-up tasks and audit trail events.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from src.config import PROJECT_ROOT
from src.followup.escalation import get_followup_rule
from src.followup.models import (
    EscalationEvent,
    EscalationStatus,
    EventType,
    FollowUp,
    FollowUpCreate,
    FollowUpStatus,
    FollowUpUpdate,
)
from src.models.config_models import UrgencyLevel

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "app.db"


def _get_utc_now() -> datetime:
    """Return current timestamp in UTC."""
    return datetime.now(timezone.utc)


def _format_iso(dt: datetime) -> str:
    """Format datetime to ISO 8601 string."""
    return dt.isoformat()


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Obtain a SQLite database connection with row factory enabled."""
    target_path = db_path or DEFAULT_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Path] = None) -> Path:
    """Initialize database tables for follow-ups and escalation events if not already present."""
    target_path = db_path or DEFAULT_DB_PATH
    with get_connection(target_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS follow_ups (
                follow_up_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                protocol_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                description TEXT NOT NULL,
                urgency TEXT NOT NULL,
                owner TEXT NOT NULL,
                due_at TEXT NOT NULL,
                escalation_due_at TEXT NOT NULL,
                escalation_path TEXT NOT NULL,
                status TEXT NOT NULL,
                escalation_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                escalation_reason TEXT,
                governance_notice TEXT NOT NULL,
                synthetic_data_notice TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS escalation_events (
                event_id TEXT PRIMARY KEY,
                follow_up_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_timestamp TEXT NOT NULL,
                previous_status TEXT,
                new_status TEXT NOT NULL,
                reason TEXT NOT NULL,
                owner TEXT NOT NULL,
                escalation_target TEXT,
                FOREIGN KEY(follow_up_id) REFERENCES follow_ups(follow_up_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_followup_status ON follow_ups(status);
            CREATE INDEX IF NOT EXISTS idx_followup_case ON follow_ups(case_id);
            CREATE INDEX IF NOT EXISTS idx_events_followup ON escalation_events(follow_up_id);
            """
        )
    return target_path


def _row_to_follow_up(row: sqlite3.Row) -> FollowUp:
    """Convert a SQLite row to a validated FollowUp model."""
    d = dict(row)
    try:
        path_list = json.loads(d["escalation_path"]) if d["escalation_path"] else []
    except Exception:
        path_list = []
    d["escalation_path"] = path_list
    d["urgency"] = UrgencyLevel(d["urgency"])
    d["status"] = FollowUpStatus(d["status"])
    d["escalation_status"] = EscalationStatus(d["escalation_status"])
    return FollowUp(**d)


def _row_to_event(row: sqlite3.Row) -> EscalationEvent:
    """Convert a SQLite row to an EscalationEvent model."""
    d = dict(row)
    d["event_type"] = EventType(d["event_type"])
    return EscalationEvent(**d)


def record_event(
    follow_up_id: str,
    event_type: EventType,
    previous_status: Optional[str],
    new_status: str,
    reason: str,
    owner: str,
    escalation_target: Optional[str] = None,
    db_path: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> EscalationEvent:
    """Append an immutable audit record to escalation_events table."""
    timestamp = _format_iso(now or _get_utc_now())
    event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO escalation_events (
                event_id, follow_up_id, event_type, event_timestamp,
                previous_status, new_status, reason, owner, escalation_target
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                event_id,
                follow_up_id,
                event_type.value,
                timestamp,
                previous_status,
                new_status,
                reason,
                owner,
                escalation_target,
            ),
        )

    return EscalationEvent(
        event_id=event_id,
        follow_up_id=follow_up_id,
        event_type=event_type,
        event_timestamp=timestamp,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        owner=owner,
        escalation_target=escalation_target,
    )


def create_follow_up(
    data: FollowUpCreate,
    db_path: Optional[Path] = None,
    follow_up_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> FollowUp:
    """Persist a new follow-up task and record the FOLLOW_UP_CREATED audit event."""
    init_db(db_path)
    created_dt = now or _get_utc_now()
    created_str = _format_iso(created_dt)
    fup_id = follow_up_id or f"FUP-{created_dt.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Default deadlines if not supplied
    due_at = data.due_at or created_str
    escalation_due_at = data.escalation_due_at or created_str
    path_json = json.dumps(data.escalation_path or [])

    initial_status = FollowUpStatus.PENDING
    initial_esc_status = EscalationStatus.NOT_REQUIRED

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO follow_ups (
                follow_up_id, case_id, protocol_id, task_type, description,
                urgency, owner, due_at, escalation_due_at, escalation_path,
                status, escalation_status, created_at, updated_at, completed_at,
                escalation_reason, governance_notice, synthetic_data_notice
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?);
            """,
            (
                fup_id,
                data.case_id,
                data.protocol_id,
                data.task_type,
                data.description,
                data.urgency.value,
                data.owner,
                due_at,
                escalation_due_at,
                path_json,
                initial_status.value,
                initial_esc_status.value,
                created_str,
                created_str,
                data.escalation_reason,
                "Decision-support prototype — clinician sign-off required.",
                "Synthetic data only — no real patient data.",
            ),
        )

    record_event(
        follow_up_id=fup_id,
        event_type=EventType.FOLLOW_UP_CREATED,
        previous_status=None,
        new_status=initial_status.value,
        reason=f"Task created for owner: {data.owner}",
        owner=data.owner,
        escalation_target=None,
        db_path=db_path,
        now=created_dt,
    )

    fup = get_follow_up(fup_id, db_path=db_path)
    assert fup is not None
    return fup


def get_follow_up(follow_up_id: str, db_path: Optional[Path] = None) -> Optional[FollowUp]:
    """Retrieve a single follow-up task by ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT * FROM follow_ups WHERE follow_up_id = ?;", (follow_up_id,))
        row = cursor.fetchone()
        return _row_to_follow_up(row) if row else None


def list_follow_ups(
    status: Optional[Any] = None,
    urgency: Optional[Any] = None,
    owner: Optional[str] = None,
    case_id: Optional[str] = None,
    escalation_status: Optional[Any] = None,
    db_path: Optional[Path] = None,
) -> List[FollowUp]:
    """List all follow-up tasks with optional filtering."""
    init_db(db_path)
    query = "SELECT * FROM follow_ups WHERE 1=1"
    params: List[Any] = []

    if status:
        status_val = status.value if hasattr(status, "value") else str(status)
        query += " AND status = ?"
        params.append(status_val.upper())
    if urgency:
        urgency_val = urgency.value if hasattr(urgency, "value") else str(urgency)
        query += " AND urgency = ?"
        params.append(urgency_val.upper())
    if owner:
        query += " AND owner LIKE ?"
        params.append(f"%{owner}%")
    if case_id:
        query += " AND case_id = ?"
        params.append(case_id)
    if escalation_status:
        esc_val = escalation_status.value if hasattr(escalation_status, "value") else str(escalation_status)
        query += " AND escalation_status = ?"
        params.append(esc_val.upper())

    query += " ORDER BY created_at DESC;"

    with get_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        return [_row_to_follow_up(row) for row in cursor.fetchall()]


def update_follow_up(
    follow_up_id: str,
    updates: FollowUpUpdate,
    db_path: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> Optional[FollowUp]:
    """Update mutable fields of a follow-up task and record audit log."""
    fup = get_follow_up(follow_up_id, db_path=db_path)
    if not fup:
        return None

    updated_dt = now or _get_utc_now()
    updated_str = _format_iso(updated_dt)

    new_status = updates.status.value if updates.status else fup.status.value
    new_owner = updates.owner if updates.owner is not None else fup.owner
    new_desc = updates.description if updates.description is not None else fup.description

    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE follow_ups
            SET status = ?, owner = ?, description = ?, updated_at = ?
            WHERE follow_up_id = ?;
            """,
            (new_status, new_owner, new_desc, updated_str, follow_up_id),
        )

    record_event(
        follow_up_id=follow_up_id,
        event_type=EventType.FOLLOW_UP_UPDATED,
        previous_status=fup.status.value,
        new_status=new_status,
        reason=updates.notes or f"Updated fields (owner: {new_owner})",
        owner=new_owner,
        db_path=db_path,
        now=updated_dt,
    )

    return get_follow_up(follow_up_id, db_path=db_path)


def complete_follow_up(
    follow_up_id: str,
    completed_by: str = "Owner",
    notes: Optional[str] = None,
    db_path: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> Optional[FollowUp]:
    """Mark a follow-up task as COMPLETED."""
    fup = get_follow_up(follow_up_id, db_path=db_path)
    if not fup:
        return None

    completed_dt = now or _get_utc_now()
    completed_str = _format_iso(completed_dt)

    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE follow_ups
            SET status = ?, completed_at = ?, updated_at = ?
            WHERE follow_up_id = ?;
            """,
            (FollowUpStatus.COMPLETED.value, completed_str, completed_str, follow_up_id),
        )

    record_event(
        follow_up_id=follow_up_id,
        event_type=EventType.FOLLOW_UP_COMPLETED,
        previous_status=fup.status.value,
        new_status=FollowUpStatus.COMPLETED.value,
        reason=notes or f"Task marked completed by {completed_by}",
        owner=fup.owner,
        db_path=db_path,
        now=completed_dt,
    )

    return get_follow_up(follow_up_id, db_path=db_path)


def mark_overdue(
    follow_up_id: str,
    reason: str = "Deadline passed",
    db_path: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> Optional[FollowUp]:
    """Transition a pending/in-progress task to OVERDUE status."""
    fup = get_follow_up(follow_up_id, db_path=db_path)
    if not fup or fup.status in (FollowUpStatus.COMPLETED, FollowUpStatus.OVERDUE, FollowUpStatus.ESCALATED):
        return fup

    overdue_dt = now or _get_utc_now()
    overdue_str = _format_iso(overdue_dt)

    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE follow_ups
            SET status = ?, updated_at = ?
            WHERE follow_up_id = ?;
            """,
            (FollowUpStatus.OVERDUE.value, overdue_str, follow_up_id),
        )

    record_event(
        follow_up_id=follow_up_id,
        event_type=EventType.FOLLOW_UP_OVERDUE,
        previous_status=fup.status.value,
        new_status=FollowUpStatus.OVERDUE.value,
        reason=reason,
        owner=fup.owner,
        db_path=db_path,
        now=overdue_dt,
    )

    return get_follow_up(follow_up_id, db_path=db_path)


def escalate_follow_up(
    follow_up_id: str,
    target: Optional[str],
    reason: str,
    failed: bool = False,
    db_path: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> Optional[FollowUp]:
    """Escalate a task, updating escalation_status and owner, and appending to audit trail."""
    fup = get_follow_up(follow_up_id, db_path=db_path)
    if not fup:
        return None

    esc_dt = now or _get_utc_now()
    esc_str = _format_iso(esc_dt)

    if failed:
        new_esc_status = EscalationStatus.ESCALATION_FAILED
        new_task_status = FollowUpStatus.ESCALATED
        event_type = EventType.ESCALATION_FAILED
        new_owner = fup.owner  # Owner cannot be updated if target is unavailable
    else:
        new_esc_status = EscalationStatus.ESCALATED
        new_task_status = FollowUpStatus.ESCALATED
        event_type = EventType.ESCALATION_TRIGGERED
        new_owner = target if target else fup.owner

    rule = get_followup_rule(fup.urgency)
    esc_hours = rule.get("escalation_hours", 4)
    new_esc_due_str = _format_iso(esc_dt + timedelta(hours=esc_hours))

    with get_connection(db_path) as conn:
        conn.execute(
            """
            UPDATE follow_ups
            SET status = ?, escalation_status = ?, owner = ?, escalation_reason = ?, escalation_due_at = ?, updated_at = ?
            WHERE follow_up_id = ?;
            """,
            (new_task_status.value, new_esc_status.value, new_owner, reason, new_esc_due_str, esc_str, follow_up_id),
        )

    record_event(
        follow_up_id=follow_up_id,
        event_type=event_type,
        previous_status=fup.status.value,
        new_status=new_task_status.value,
        reason=reason,
        owner=new_owner,
        escalation_target=target,
        db_path=db_path,
        now=esc_dt,
    )

    return get_follow_up(follow_up_id, db_path=db_path)


def get_escalation_events(follow_up_id: str, db_path: Optional[Path] = None) -> List[EscalationEvent]:
    """Retrieve full chronological audit trail for a follow-up task."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM escalation_events WHERE follow_up_id = ? ORDER BY rowid ASC;",
            (follow_up_id,),
        )
        return [_row_to_event(row) for row in cursor.fetchall()]


def has_escalation_event_for_target(
    follow_up_id: str,
    event_type: EventType,
    escalation_target: Optional[str],
    db_path: Optional[Path] = None,
) -> bool:
    """Identity-based check to verify if an escalation event already exists for this target.

    Guarantees idempotency: running the watcher multiple times will not duplicate events.
    """
    init_db(db_path)
    with get_connection(db_path) as conn:
        if escalation_target is None:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM escalation_events
                WHERE follow_up_id = ? AND event_type = ? AND escalation_target IS NULL;
                """,
                (follow_up_id, event_type.value),
            )
        else:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM escalation_events
                WHERE follow_up_id = ? AND event_type = ? AND escalation_target = ?;
                """,
                (follow_up_id, event_type.value, escalation_target),
            )
        count = cursor.fetchone()[0]
        return count > 0
