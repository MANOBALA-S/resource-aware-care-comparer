# Follow-Up & Escalation Tracker Specification

> [!CAUTION]
> **GOVERNANCE & SYNTHETIC DATA NOTICE**
> - **Decision-support prototype — clinician sign-off required.**
> - **Synthetic data only — no real patient data.**
> - All cases, facility registries, protocols, and operational records described herein are synthetic.

---

## 1. Problem Statement: Why Follow-Ups Disappear

In distributed teleconsultation networks and resource-constrained health systems, critical clinical follow-ups routinely fail due to systemic operational blind spots:
1. **Unowned Directives**: Recommendations like *"Check vitals in 24 hours"* are recorded in notes without assigning an explicit, accountable human owner.
2. **Invisible Deadlines**: Tasks lack concrete Service Level Agreements (SLAs), meaning there is no clear distinction between an active task and an overdue breach.
3. **Absence of Escalation Paths**: When the primary assignee fails to act, there is no deterministic trigger to notify supervisors or emergency teams.
4. **Audit Blind Spots**: Without an immutable record of milestone changes and escalations, care teams cannot inspect why a critical action was delayed or missed.

The **Follow-Up & Escalation Tracker** (`src/followup/`) solves these failure modes by providing persistent SQLite task tracking, deterministic urgency SLAs, identity-based hierarchical escalations, and strict audit logging.

---

## 2. Architecture & Data Model

The module combines an asynchronous-ready SQLite repository with deterministic business logic:

```
┌──────────────────────────────────────┐     ┌────────────────────────────────────┐
│      CONSTRAINT ENGINE RESULT        │     │       MANUAL / API CREATION        │
│   (Option, Urgency, Escalation Req)  │     │       (Case, Task, Owner)          │
└──────────────────┬───────────────────┘     └─────────────────┬──────────────────┘
                   │                                           │
                   ▼                                           ▼
          ┌─────────────────────────────────────────────────────────────┐
          │             TRACKER INTEGRATION LAYER                       │
          │  - Resolves Urgency (Auto-elevates on Emergency)            │
          │  - Calculates Deterministic SLAs (due_at, escalation_due)   │
          │  - Attaches Standard Hierarchical Escalation Ladder         │
          └──────────────────────────────┬──────────────────────────────┘
                                         │
                                         ▼
          ┌─────────────────────────────────────────────────────────────┐
          │                 SQLITE REPOSITORY (data/app.db)             │
          │                                                             │
          │   TABLE follow_ups:                                         │
          │     - follow_up_id (PK)                                      │
          │     - case_id, protocol_id, task_type, description          │
          │     - urgency, owner, due_at, escalation_due_at             │
          │     - escalation_path (JSON), status, escalation_status     │
          │                                                             │
          │   TABLE escalation_events:                                  │
          │     - event_id (PK), follow_up_id (FK), event_type          │
          │     - event_timestamp, previous_status, new_status          │
          │     - reason, owner, escalation_target                      │
          └──────────────────────────────┬──────────────────────────────┘
                                         │
                                         ▼
          ┌─────────────────────────────────────────────────────────────┐
          │            DETERMINISTIC SCHEDULER / WATCHER                │
          │  - Evaluates active tasks against UTC deadlines             │
          │  - Transitions: PENDING -> OVERDUE -> ESCALATED             │
          │  - Guarantees Identity-Based Idempotency (No duplicate runs)│
          │  - Detects Missing Contacts -> ESCALATION_FAILED            │
          └─────────────────────────────────────────────────────────────┘
```

---

## 3. Task State Machine

### Follow-Up Status (`FollowUpStatus`)
```
                  [Create Task]
                        │
                        ▼
                   ┌─────────┐
         ┌─────────┤ PENDING ├─────────┐
         │         └────┬────┘         │
         │              │              │
         │ due_at       │ start work   │ mark completed
         │ breached     ▼              │
         │       ┌─────────────┐       │
         │       │ IN_PROGRESS │       │
         │       └──────┬──────┘       │
         │              │              │
         │              │ due_at       │
         │              │ breached     │
         ▼              ▼              │
        ┌────────────────┐             │
        │    OVERDUE     │             │
        └───────┬────────┘             │
                │                      │
                │ esc_due_at           │
                │ breached             │
                ▼                      │
        ┌────────────────┐             │
        │   ESCALATED    │             │
        └───────┬────────┘             │
                │                      │
                │ completed            │
                ▼                      ▼
        ┌────────────────────────────────┐
        │           COMPLETED            │
        └────────────────────────────────┘
```

### Escalation Status (`EscalationStatus`)
- `NOT_REQUIRED`: Default state when created or for low-priority non-escalatable tasks.
- `PENDING`: Escalation SLA is active and being monitored by the scheduler.
- `ESCALATED`: Escalation has been successfully triggered and reassigned to a higher-tier contact.
- `ESCALATION_FAILED`: Escalation was required, but the escalation path was missing or empty. Signals `fallback_owner_required = True`.

---

## 4. Configurable SLA Timers

SLAs are configured in [`config/followup_rules.json`](file:///c:/Users/amoha/OneDrive/Desktop/Teleconsultation%20Service%20Operating%20pro/resource-aware-care-comparer/config/followup_rules.json):

| Urgency Tier | Action SLA (`due_hours`) | Escalation Grace SLA (`escalation_hours`) | Default Escalation Ladder |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | **1 hour** | **1 hour** | Local Health Worker &rarr; Site Coordinator &rarr; Regional Clinical Supervisor &rarr; Emergency / Human Clinical Escalation |
| **HIGH** | **24 hours** | **4 hours** | Local Health Worker &rarr; Site Coordinator &rarr; Regional Clinical Supervisor &rarr; Emergency / Human Clinical Escalation |
| **MEDIUM** | **72 hours** | **24 hours** | Local Health Worker &rarr; Site Coordinator &rarr; Regional Clinical Supervisor |
| **LOW** | **168 hours** (7 days) | **48 hours** | Local Health Worker &rarr; Site Coordinator |

Deadlines are calculated deterministically:
$$\text{due\_at} = \text{base\_time} + \text{due\_hours}$$
$$\text{escalation\_due\_at} = \text{due\_at} + \text{escalation\_hours}$$

---

## 5. Deterministic Scheduler & Idempotency Guarantee

The watcher function `check_overdue_followups(now, db_path)` guarantees:

1. **Deterministic Evaluation**: Replaces wall-clock polling with explicit UTC comparisons against `due_at` and `escalation_due_at`.
2. **Identity-Based Idempotency**:
   - Before firing an escalation event, `has_escalation_event_for_target()` queries the audit table for `(follow_up_id, event_type, target)`.
   - Running the scheduler 10 times consecutively produces **exactly one** escalation event per tier.
   - When escalated, the task's `escalation_due_at` is extended by that urgency's `escalation_hours`, granting the new owner their full SLA window before subsequent escalation.

---

## 6. Failure Modes & Missing Contact Protection

If a task breaches its escalation SLA but its `escalation_path` is empty `[]` or unresolvable:
- `escalation_status` transitions to `ESCALATION_FAILED`.
- Task `status` transitions to `ESCALATED`.
- An audit event with `event_type = ESCALATION_FAILED` is recorded.
- Scheduler actions flag `fallback_owner_required = True`.
- Prevents tasks from getting stuck in limbo when administrative directories are incomplete.

---

## 7. REST API Endpoints

The API is exposed through FastAPI at prefix `/followups`:

| Method | Path | Summary |
| :--- | :--- | :--- |
| `POST` | `/followups` | Create a new tracked follow-up task |
| `GET` | `/followups` | List all tasks (filters: `status`, `urgency`, `owner`, `case_id`, `escalation_status`) |
| `GET` | `/followups/{id}` | Get complete details of a specific follow-up task |
| `PATCH` | `/followups/{id}` | Update task status, reassign owner, or modify instructions |
| `POST` | `/followups/{id}/complete` | Mark task as `COMPLETED` and record completion audit event |
| `POST` | `/followups/check-overdue` | Trigger scheduler evaluation of active tasks |
| `GET` | `/followups/{id}/escalations`| Retrieve chronological audit trail for a task |

Every HTTP response includes mandatory governance headers:
- `X-Decision-Support: Decision-support prototype - clinician sign-off required.`
- `X-Data-Policy: Synthetic data only - no real patient data.`

---

## 8. Verification & Test Coverage

Phase 5 includes 22 new targeted unit and integration tests (bringing the repository total to 77 passing tests):
- [`test_followup_creation.py`](file:///c:/Users/amoha/OneDrive/Desktop/Teleconsultation%20Service%20Operating%20pro/resource-aware-care-comparer/tests/followup/test_followup_creation.py): Field validation, SLA default assignment, engine integration.
- [`test_due_dates.py`](file:///c:/Users/amoha/OneDrive/Desktop/Teleconsultation%20Service%20Operating%20pro/resource-aware-care-comparer/tests/followup/test_due_dates.py): Mathematical verification across CRITICAL, HIGH, MEDIUM, LOW.
- [`test_overdue_detection.py`](file:///c:/Users/amoha/OneDrive/Desktop/Teleconsultation%20Service%20Operating%20pro/resource-aware-care-comparer/tests/followup/test_overdue_detection.py): Overdue transitions, ignoring completed tasks.
- [`test_escalation.py`](file:///c:/Users/amoha/OneDrive/Desktop/Teleconsultation%20Service%20Operating%20pro/resource-aware-care-comparer/tests/followup/test_escalation.py): Tier progression and audit logging.
- [`test_idempotent_escalation.py`](file:///c:/Users/amoha/OneDrive/Desktop/Teleconsultation%20Service%20Operating%20pro/resource-aware-care-comparer/tests/followup/test_idempotent_escalation.py): 10 consecutive scheduler runs produce exactly 1 escalation.
- [`test_missing_escalation_contact.py`](file:///c:/Users/amoha/OneDrive/Desktop/Teleconsultation%20Service%20Operating%20pro/resource-aware-care-comparer/tests/followup/test_missing_escalation_contact.py): Configuration failure handling.
- [`test_followup_breach.py`](file:///c:/Users/amoha/OneDrive/Desktop/Teleconsultation%20Service%20Operating%20pro/resource-aware-care-comparer/tests/edge_cases/test_followup_breach.py): Multi-tier cascade, 404 responses, and full API lifecycle.
