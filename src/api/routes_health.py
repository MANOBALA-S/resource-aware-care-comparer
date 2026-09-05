"""Health check endpoints.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from typing import Any, Dict
from fastapi import APIRouter

from src.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> Dict[str, str]:
    """Basic service health check endpoint.

    Returns:
        JSON response with {"status": "ok"}.
    """
    return {"status": "ok"}


@router.get("/health/detail")
def health_check_detail() -> Dict[str, Any]:
    """Detailed health check and system configuration summary.

    Returns:
        System status, application metadata, governance banners, and supported languages.
    """
    settings = get_settings()

    return {
        "status": "ok",
        "app": {
            "name": settings.app.name,
            "version": settings.app.version,
            "environment": settings.app.environment,
        },
        "governance": {
            "prototype_disclaimer": settings.governance.prototype_disclaimer,
            "synthetic_data_policy": settings.governance.synthetic_data_policy,
            "clinician_signoff_mandatory": settings.governance.clinician_signoff_mandatory,
        },
        "languages": [lang.code for lang in settings.languages if lang.enabled],
        "urgency_levels": list(settings.urgency_levels.keys()),
        "escalation_levels": list(settings.escalation_levels.keys()),
    }
