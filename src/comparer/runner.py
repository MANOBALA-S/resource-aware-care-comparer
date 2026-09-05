"""Batch comparison runner executing paired baseline vs resource-aware evaluations.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from baseline.baseline_engine import TextbookBaselineEngine
from src.comparer.comparison import compare_single_case
from src.comparer.metrics import calculate_comparison_metrics
from src.comparer.models import (
    CaseComparisonResult,
    ComparisonRunResult,
    ComparisonSummaryMetrics,
)
from src.config import PROJECT_ROOT
from src.models.operational_models import PatientCase, ServiceSite
from src.protocol_engine.protocol_engine import ProtocolEngine, get_protocol_engine

CASES_FILE_DEFAULT = PROJECT_ROOT / "data" / "cases" / "synthetic_cases.json"
SERVICES_FILE_DEFAULT = PROJECT_ROOT / "data" / "services" / "service_registry.json"
OUTPUT_RESULTS_DEFAULT = PROJECT_ROOT / "data" / "generated" / "comparison_results.json"
OUTPUT_SUMMARY_DEFAULT = PROJECT_ROOT / "data" / "generated" / "comparison_summary.json"


class ComparisonRunner:
    """Orchestrates paired execution across all synthetic patient cases."""

    def __init__(
        self,
        cases_path: Optional[Path] = None,
        services_path: Optional[Path] = None,
        protocol_engine: Optional[ProtocolEngine] = None,
        baseline_engine: Optional[TextbookBaselineEngine] = None,
        clinician_languages: Optional[List[str]] = None,
        db_path: Optional[Path] = None,
    ) -> None:
        self.cases_path = Path(cases_path) if cases_path else CASES_FILE_DEFAULT
        self.services_path = Path(services_path) if services_path else SERVICES_FILE_DEFAULT
        self.protocol_engine = protocol_engine or get_protocol_engine()
        self.baseline_engine = baseline_engine or TextbookBaselineEngine(self.protocol_engine)
        self.clinician_languages = clinician_languages or ["en"]
        self.db_path = db_path

        self._cases: List[PatientCase] = []
        self._sites: Dict[str, ServiceSite] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load and validate synthetic cases and service sites."""
        if not self.cases_path.is_file():
            raise FileNotFoundError(f"Synthetic cases file not found at '{self.cases_path}'")
        with open(self.cases_path, "r", encoding="utf-8") as f:
            cases_raw = json.load(f).get("cases", [])
            self._cases = [PatientCase(**c) for c in cases_raw]

        if not self.services_path.is_file():
            raise FileNotFoundError(f"Service registry file not found at '{self.services_path}'")
        with open(self.services_path, "r", encoding="utf-8") as f:
            sites_raw = json.load(f).get("sites", [])
            self._sites = {s["site_id"]: ServiceSite(**s) for s in sites_raw}

    @property
    def cases(self) -> List[PatientCase]:
        return self._cases

    @property
    def sites(self) -> Dict[str, ServiceSite]:
        return self._sites

    def run_all(self) -> ComparisonRunResult:
        """Run all loaded synthetic cases through the paired evaluation pipeline.

        Returns:
            ComparisonRunResult containing timestamp, metrics, and all 40 case comparison records.
        """
        results: List[CaseComparisonResult] = []

        for case in self._cases:
            site = self._sites.get(case.site_id)
            if not site:
                raise ValueError(f"Site '{case.site_id}' for case '{case.case_id}' not found in registry.")

            protocol = self.protocol_engine.get_protocol(case.condition)
            if not protocol:
                raise ValueError(f"No clinical protocol found for condition '{case.condition}'.")

            comparison_result = compare_single_case(
                case=case,
                site=site,
                protocol=protocol,
                baseline_engine=self.baseline_engine,
                clinician_languages=self.clinician_languages,
                db_path=self.db_path,
            )
            results.append(comparison_result)

        metrics = calculate_comparison_metrics(results)

        return ComparisonRunResult(
            run_timestamp=datetime.now(timezone.utc).isoformat(),
            engine_version="1.0.0",
            cases_evaluated=len(results),
            metrics=metrics,
            results=results,
        )

    def run_and_save(
        self,
        output_results_path: Optional[Path] = None,
        output_summary_path: Optional[Path] = None,
    ) -> ComparisonRunResult:
        """Execute the comparison across all cases and save the output JSON files."""
        run_result = self.run_all()

        results_path = Path(output_results_path) if output_results_path else OUTPUT_RESULTS_DEFAULT
        summary_path = Path(output_summary_path) if output_summary_path else OUTPUT_SUMMARY_DEFAULT

        results_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.parent.mkdir(parents=True, exist_ok=True)

        with open(results_path, "w", encoding="utf-8") as f:
            f.write(run_result.model_dump_json(indent=2))

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(run_result.metrics.model_dump_json(indent=2))

        return run_result


def run_all_comparisons(
    cases_path: Optional[Path] = None,
    services_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> ComparisonRunResult:
    """Convenience helper to run the complete comparison pipeline."""
    runner = ComparisonRunner(
        cases_path=cases_path,
        services_path=services_path,
        db_path=db_path,
    )
    return runner.run_all()
