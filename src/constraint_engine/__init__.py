"""Resource constraint engine package providing deterministic feasibility evaluation and reason trails.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from src.constraint_engine.feasibility import (
    evaluate_case_constraints,
    evaluate_language_safety,
    evaluate_option_feasibility,
)
from src.constraint_engine.models import (
    ConstraintEngineResult,
    LanguageEvaluation,
    LanguageStatus,
    OptionEvaluation,
    ResourceEvaluation,
    ResourceStatus,
)
from src.constraint_engine.reason_trail import ReasonTrailBuilder
from src.constraint_engine.resource_filter import (
    check_registry_conflicts,
    evaluate_resource_availability,
)

__all__ = [
    "ConstraintEngineResult",
    "LanguageEvaluation",
    "LanguageStatus",
    "OptionEvaluation",
    "ReasonTrailBuilder",
    "ResourceEvaluation",
    "ResourceStatus",
    "check_registry_conflicts",
    "evaluate_case_constraints",
    "evaluate_language_safety",
    "evaluate_option_feasibility",
    "evaluate_resource_availability",
]
