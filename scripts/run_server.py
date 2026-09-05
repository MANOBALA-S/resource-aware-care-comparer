"""Run script to start the FastAPI server for Resource-Aware Care Option Comparer.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from src.config import get_settings


def main() -> None:
    """Start uvicorn server using configured application parameters."""
    settings = get_settings()

    print("=" * 70)
    print(f" {settings.app.name.upper()} v{settings.app.version}")
    print("=" * 70)
    print(f" NOTICE: {settings.governance.prototype_disclaimer}")
    print(f" DATA:   {settings.governance.synthetic_data_policy}")
    print(f" HOST:   http://{settings.app.host}:{settings.app.port}")
    print(f" HEALTH: http://{settings.app.host}:{settings.app.port}/health")
    print(f" DOCS:   http://{settings.app.host}:{settings.app.port}/docs")
    print("=" * 70)

    uvicorn.run(
        "src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )


if __name__ == "__main__":
    main()
