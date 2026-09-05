"""Textbook baseline comparator package.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from baseline.baseline_engine import (
    BaselineRecommendationResult,
    TextbookBaselineEngine,
)

__all__ = [
    "BaselineRecommendationResult",
    "TextbookBaselineEngine",
]
