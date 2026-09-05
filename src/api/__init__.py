"""API routes package for Resource-Aware Care Option Comparer.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from src.api.routes_clinician import router as clinician_router
from src.api.routes_comparer import router as comparer_router
from src.api.routes_followup import router as followup_router
from src.api.routes_health import router as health_router
from src.api.routes_language import router as language_router

__all__ = [
    "clinician_router",
    "comparer_router",
    "followup_router",
    "health_router",
    "language_router",
]
