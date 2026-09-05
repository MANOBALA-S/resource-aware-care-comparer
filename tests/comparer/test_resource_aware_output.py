"""Tests for Resource-Aware system output structure, ladder adaptation, and follow-up accountability.

Verifies:
- Resource-aware system adapts care options down the recommendation ladder when constraints block preferred care.
- All high-priority follow-up tasks have named owner, due date, and escalation path.
- Language compatibility is verified end-to-end.
- Reason trails provide inspectable clinical rationale.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from pathlib import Path
import pytest

from src.comparer.runner import ComparisonRunner


def test_resource_aware_selects_feasible_options(tmp_path: Path):
    """Verify that resource-aware engine selects feasible care options across all sites."""
    runner = ComparisonRunner(db_path=tmp_path / "test_ra_feasible.db")
    run_result = runner.run_all()

    for result in run_result.results:
        assert result.resource_aware_feasible is True
        assert result.resource_aware_ladder_level in (
            "preferred",
            "resource_adapted_alternative",
            "minimum_safe_fallback",
            "escalate_only",
        )
        assert len(result.resource_aware_recommendation) > 10
        assert len(result.resource_aware_reason) > 10


def test_resource_aware_follow_up_accountability(tmp_path: Path):
    """Verify that every resource-aware follow-up task has owner, due date, and escalation path."""
    runner = ComparisonRunner(db_path=tmp_path / "test_ra_followup.db")
    run_result = runner.run_all()

    for result in run_result.results:
        assert result.has_named_owner is True
        assert result.has_due_date is True
        assert result.has_escalation_path is True
        assert "Tracked (owner:" in result.resource_aware_follow_up
        assert "due:" in result.resource_aware_follow_up
        assert "path:" in result.resource_aware_follow_up


def test_resource_aware_language_checked(tmp_path: Path):
    """Verify that resource-aware system always checks language and flags mismatches."""
    runner = ComparisonRunner(db_path=tmp_path / "test_ra_lang.db")
    run_result = runner.run_all()

    for result in run_result.results:
        assert result.resource_aware_language_checked is True

    # At least some synthetic cases have Tamil patient with English clinician
    mismatch_cases = [r for r in run_result.results if r.language_mismatch]
    assert len(mismatch_cases) > 0


def test_resource_aware_adapts_when_site_constrained(tmp_path: Path):
    """Verify that when site constraints block preferred option, changed_recommendation is True."""
    runner = ComparisonRunner(db_path=tmp_path / "test_ra_adaptation.db")
    run_result = runner.run_all()

    adapted_results = [
        r for r in run_result.results
        if r.resource_aware_ladder_level in ("resource_adapted_alternative", "minimum_safe_fallback")
    ]
    assert len(adapted_results) == 14
    for r in adapted_results:
        assert r.changed_recommendation is True
        assert "Adapted to" in r.resource_aware_reason
