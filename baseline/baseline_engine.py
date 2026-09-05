"""Textbook Baseline Recommendation Engine.

Acts as the unconstrained clinical benchmark comparator.
Accepts a synthetic patient case, identifies the relevant protocol, and returns
the gold-standard textbook recommendation without verifying local resource availability
or follow-up feasibility.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel

from src.protocol_engine.protocol_engine import ProtocolEngine, get_protocol_engine


class BaselineRecommendationResult(BaseModel):
    """Structured output from the textbook baseline engine."""
    method: str = "baseline"
    case_id: Optional[str] = None
    status: str
    protocol_id: Optional[str] = None
    condition: Optional[str] = None
    protocol_title: Optional[str] = None
    urgency: Optional[str] = None
    recommendation: str
    textbook_required_resources: list[str] = []
    follow_up_interval: Optional[str] = None
    resource_checked: bool = False
    follow_up_checked: bool = False
    governance_notice: str = "Decision-support prototype — clinician sign-off required."
    synthetic_data_notice: str = "Synthetic data only — no real patient data."


class TextbookBaselineEngine:
    """Baseline engine implementing direct, unconstrained textbook protocol lookup."""

    def __init__(self, protocol_engine: Optional[ProtocolEngine] = None) -> None:
        """Initialize with a protocol engine instance or standard default."""
        self._engine = protocol_engine or get_protocol_engine()

    def generate_recommendation(self, case_data: Dict[str, Any] | BaseModel) -> Dict[str, Any]:
        """Generate an unconstrained textbook recommendation for a synthetic patient case.

        IMPORTANT CONTRACTUAL INVARIANTS:
        - This engine MUST NOT check site resources.
        - This engine MUST NOT check medication stock.
        - This engine MUST NOT check specialists.
        - This engine MUST NOT check imaging.
        - This engine MUST NOT check transportation.
        - This engine MUST NOT check connectivity.
        - This engine MUST NOT check language support.
        - This engine MUST NOT check follow-up ownership or escalation feasibility.

        Args:
            case_data: Dictionary or Pydantic model representing a synthetic patient case.

        Returns:
            Dictionary matching the baseline comparison contract.
        """
        # Convert to dict if a Pydantic model is supplied
        data = case_data.model_dump() if isinstance(case_data, BaseModel) else dict(case_data)

        case_id = data.get("case_id") or data.get("id") or "SYNTH-CASE-UNKNOWN"
        condition = data.get("condition") or data.get("primary_condition") or ""

        if not condition:
            return BaselineRecommendationResult(
                case_id=case_id,
                status="error",
                protocol_id=None,
                condition=None,
                recommendation="Missing condition: Case does not specify a clinical condition.",
                resource_checked=False,
                follow_up_checked=False,
            ).model_dump()

        protocol = self._engine.get_protocol(str(condition))
        if protocol is None:
            return BaselineRecommendationResult(
                case_id=case_id,
                status="error",
                protocol_id=None,
                condition=str(condition),
                recommendation=(
                    f"Unknown condition: No approved textbook protocol for condition '{condition}'."
                ),
                resource_checked=False,
                follow_up_checked=False,
            ).model_dump()

        # Deliberately output the textbook recommendation without evaluating any site constraints
        return BaselineRecommendationResult(
            case_id=case_id,
            status="success",
            protocol_id=protocol.protocol_id,
            condition=protocol.condition,
            protocol_title=protocol.title,
            urgency=protocol.urgency.value,
            recommendation=protocol.textbook_recommendation,
            textbook_required_resources=list(protocol.required_resources),
            follow_up_interval=protocol.follow_up_interval,
            resource_checked=False,
            follow_up_checked=False,
        ).model_dump()
