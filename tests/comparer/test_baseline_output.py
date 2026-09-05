"""Tests for Baseline system output structure, semantics, and resource blindness.

Verifies:
- Baseline always generates textbook gold-standard recommendations.
- Baseline never checks site resources, connectivity, language, or follow-ups.
- Baseline follow-up is untracked with no named owner, due date, or escalation path.
- Baseline feasibility accurately reveals real-world facility deficits.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from pathlib import Path
import pytest

from src.comparer.runner import ComparisonRunner


def test_baseline_always_prescribes_textbook(tmp_path: Path):
    """Verify that baseline recommendations always match the protocol textbook recommendation."""
    runner = ComparisonRunner(db_path=tmp_path / "test_baseline.db")
    run_result = runner.run_all()

    for result in run_result.results:
        protocol = runner.protocol_engine.get_protocol(result.condition)
        assert protocol is not None
        assert result.baseline_recommendation == protocol.textbook_recommendation
        assert result.baseline_ladder_level == "preferred"


def test_baseline_language_and_followup_unchecked(tmp_path: Path):
    """Verify baseline leaves language unchecked and follow-up untracked."""
    runner = ComparisonRunner(db_path=tmp_path / "test_baseline_unchecked.db")
    run_result = runner.run_all()

    for result in run_result.results:
        assert result.baseline_language_checked is False
        assert "Untracked" in result.baseline_follow_up
        assert "no named owner" in result.baseline_follow_up
        assert "no due date" in result.baseline_follow_up
        assert "no escalation path" in result.baseline_follow_up


def test_baseline_feasibility_reveals_peripheral_deficits(tmp_path: Path):
    """Verify that baseline recommendations are flagged as infeasible at peripheral sites lacking resources."""
    runner = ComparisonRunner(db_path=tmp_path / "test_baseline_feasibility.db")
    run_result = runner.run_all()

    # At tertiary center SITE-001, baseline is 100% feasible
    site_001_results = [r for r in run_result.results if r.site_id == "SITE-001"]
    assert len(site_001_results) > 0
    assert all(r.baseline_feasible for r in site_001_results)

    # At remote primary clinic SITE-002 and tribal clinic SITE-006, baseline fails on most cases
    peripheral_results = [r for r in run_result.results if r.site_id in ("SITE-002", "SITE-006")]
    assert len(peripheral_results) > 0
    infeasible_count = sum(1 for r in peripheral_results if not r.baseline_feasible)
    assert infeasible_count >= 10  # 11 of 13 cases are infeasible under baseline
