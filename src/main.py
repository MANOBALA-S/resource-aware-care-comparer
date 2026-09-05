"""FastAPI application factory and main entry point.

RESOURCE-AWARE CARE OPTION COMPARER
Multilingual Teleconsultation Service Prototype

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from contextlib import asynccontextmanager
import logging
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.routes_clinician import router as clinician_router
from src.api.routes_comparer import router as comparer_router
from src.api.routes_followup import router as followup_router
from src.api.routes_health import router as health_router
from src.api.routes_language import router as language_router
from src.config import PROJECT_ROOT, get_settings
from src.followup.repository import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("care_comparer")


def _to_header_safe(text: str) -> str:
    """Sanitize non-Latin-1 characters (such as em-dashes) for HTTP header transmission."""
    return text.replace("—", "-").replace("–", "-")


class GovernanceHeadersMiddleware(BaseHTTPMiddleware):
    """Ensure all outgoing HTTP responses include mandatory clinical governance headers."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        settings = get_settings()
        response.headers["X-Decision-Support"] = _to_header_safe(settings.governance.prototype_disclaimer)
        response.headers["X-Data-Policy"] = _to_header_safe(settings.governance.synthetic_data_policy)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for application startup and shutdown hooks."""
    settings = get_settings()
    logger.info("Starting up %s v%s", settings.app.name, settings.app.version)
    logger.info("Governance: %s", settings.governance.prototype_disclaimer)
    logger.info("Data Policy: %s", settings.governance.synthetic_data_policy)
    logger.info("Loaded active languages: %s", [l.code for l in settings.languages if l.enabled])
    logger.info("Loaded urgency tiers: %s", list(settings.urgency_levels.keys()))
    logger.info("Loaded escalation levels: %s", list(settings.escalation_levels.keys()))
    init_db()
    logger.info("Follow-up SQLite database initialized")
    yield
    logger.info("Shutting down %s", settings.app.name)


def create_app() -> FastAPI:
    """Application factory for Resource-Aware Care Option Comparer."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        description=(
            "Multilingual teleconsultation decision-support prototype comparing textbook "
            "clinical guidelines against resource-aware recommendations.\n\n"
            "**IMPORTANT DISCLAIMERS:**\n"
            "- *Decision-support prototype — clinician sign-off required.*\n"
            "- *Synthetic data only — no real patient data.*"
        ),
        lifespan=lifespan,
    )

    # Middleware
    application.add_middleware(GovernanceHeadersMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    application.include_router(health_router)
    application.include_router(followup_router)
    application.include_router(language_router)
    application.include_router(clinician_router)
    application.include_router(comparer_router)

    # Mount UI static files
    ui_dir = PROJECT_ROOT / "ui"
    if ui_dir.is_dir():
        application.mount("/ui", StaticFiles(directory=str(ui_dir), html=True), name="ui")

    @application.get("/", tags=["Root"])
    def root() -> Dict[str, Any]:
        """Root status and documentation landing metadata."""
        return {
            "name": settings.app.name,
            "version": settings.app.version,
            "environment": settings.app.environment,
            "notice": settings.governance.prototype_disclaimer,
            "data_policy": settings.governance.synthetic_data_policy,
            "endpoints": {
                "health": "/health",
                "health_detail": "/health/detail",
                "followups": "/followups",
                "languages": "/languages",
                "cases": "/cases",
                "comparer_summary": "/comparer/summary",
                "comparer_cases": "/comparer/cases",
                "comparer_compare": "/comparer/compare/{case_id}",
                "evaluate": "/evaluate",
                "ui": "/ui",
                "openapi_docs": "/docs",
                "redoc": "/redoc",
            },
        }

    return application


# Global application instance
app = create_app()
