"""Tests for SLA deadline calculation across all urgency tiers.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from src.followup.escalation import (
    calculate_deadlines,
    get_default_escalation_path,
    get_followup_rule,
    load_followup_rules,
)
from src.models.config_models import UrgencyLevel


def test_calculate_deadlines_critical() -> None:
    """Test CRITICAL SLA: 1 hour due, 1 hour escalation."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    due_at, esc_due_at = calculate_deadlines(UrgencyLevel.CRITICAL, start_time=base_time)

    assert due_at == base_time + timedelta(hours=1)
    assert esc_due_at == base_time + timedelta(hours=2)


def test_calculate_deadlines_high() -> None:
    """Test HIGH SLA: 24 hours due, 4 hours escalation."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    due_at, esc_due_at = calculate_deadlines(UrgencyLevel.HIGH, start_time=base_time)

    assert due_at == base_time + timedelta(hours=24)
    assert esc_due_at == base_time + timedelta(hours=28)


def test_calculate_deadlines_medium() -> None:
    """Test MEDIUM SLA: 72 hours due, 24 hours escalation."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    due_at, esc_due_at = calculate_deadlines(UrgencyLevel.MEDIUM, start_time=base_time)

    assert due_at == base_time + timedelta(hours=72)
    assert esc_due_at == base_time + timedelta(hours=96)


def test_calculate_deadlines_low() -> None:
    """Test LOW SLA: 168 hours due, 48 hours escalation."""
    base_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    due_at, esc_due_at = calculate_deadlines(UrgencyLevel.LOW, start_time=base_time)

    assert due_at == base_time + timedelta(hours=168)
    assert esc_due_at == base_time + timedelta(hours=216)


def test_fallback_when_rules_file_missing(tmp_path: Path) -> None:
    """Test safe fallback when custom rules file does not exist."""
    missing_file = tmp_path / "non_existent_rules.json"
    rules = load_followup_rules(missing_file)
    assert "CRITICAL" in rules
    assert rules["CRITICAL"]["due_hours"] == 1


def test_default_escalation_path_hierarchy() -> None:
    """Test default escalation hierarchy structure."""
    critical_path = get_default_escalation_path(UrgencyLevel.CRITICAL)
    assert len(critical_path) == 4
    assert critical_path[0] == "Local Health Worker"
    assert critical_path[-1] == "Emergency / Human Clinical Escalation"

    low_path = get_default_escalation_path(UrgencyLevel.LOW)
    assert len(low_path) == 2
    assert low_path[0] == "Local Health Worker"
    assert low_path[1] == "Site Coordinator"
