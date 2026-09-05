"""Tests for input fairness and case immutability in the comparative evaluation pipeline.

Guarantees:
- Exactly 40 cases are evaluated.
- Same synthetic case + same condition + same site + same urgency is used for both systems.
- Neither baseline nor resource-aware engine mutates the input case entity.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import copy
from pathlib import Path
import pytest

from baseline.baseline_engine import TextbookBaselineEngine
from src.comparer.comparison import compare_single_case
from src.comparer.runner import ComparisonRunner
from src.protocol_engine.protocol_engine import ProtocolEngine


def test_exactly_40_cases_loaded(tmp_path: Path):
    """Verify that the comparison runner loads exactly 40 synthetic patient cases."""
    runner = ComparisonRunner(db_path=tmp_path / "test_comparer.db")
    assert len(runner.cases) == 40
    assert len(runner.sites) == 6


def test_same_input_case_immutability(tmp_path: Path):
    """Verify that case data is 100% identical before and after baseline & resource-aware evaluation."""
    runner = ComparisonRunner(db_path=tmp_path / "test_immutability.db")
    protocol_engine = ProtocolEngine()
    baseline_engine = TextbookBaselineEngine(protocol_engine)

    for case in runner.cases:
        site = runner.sites[case.site_id]
        protocol = protocol_engine.get_protocol(case.condition)
        assert protocol is not None

        # Take deep snapshot before comparison
        case_snapshot_before = copy.deepcopy(case.model_dump())

        # Execute single comparison
        result = compare_single_case(
            case=case,
            site=site,
            protocol=protocol,
            baseline_engine=baseline_engine,
            clinician_languages=["en"],
            db_path=tmp_path / "test_immutability.db",
        )

        # Take snapshot after comparison
        case_snapshot_after = case.model_dump()

        # Input fairness verification
        assert case_snapshot_before == case_snapshot_after, (
            f"Case '{case.case_id}' was mutated during comparative evaluation!"
        )
        assert result.case_id == case.case_id
        assert result.condition == case.condition
        assert result.site_id == case.site_id
        assert result.urgency == case.urgency.value


def test_full_run_evaluates_exactly_40_cases(tmp_path: Path):
    """Verify that a complete comparison run produces exactly 40 results matching case IDs."""
    runner = ComparisonRunner(db_path=tmp_path / "test_40_cases.db")
    run_result = runner.run_all()

    assert run_result.cases_evaluated == 40
    assert len(run_result.results) == 40
    assert run_result.metrics.total_cases_evaluated == 40

    case_ids = [r.case_id for r in run_result.results]
    assert len(set(case_ids)) == 40
    assert case_ids[0] == "SYNTH-CASE-001"
    assert case_ids[-1] == "SYNTH-CASE-040"
