"""API routes package for Resource-Aware Care Option Comparer.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from src.api.routes_health import router as health_router

__all__ = ["health_router"]
