"""Pytest fixtures for API and configuration tests.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
import sys
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

# Ensure project root is available to pytest
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings
from src.main import app
from src.models.config_models import SystemSettings


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture for interacting with the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def settings() -> SystemSettings:
    """Settings fixture providing current system settings."""
    return get_settings()


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    """Provide a fresh, isolated temporary SQLite database path."""
    from src.followup.repository import init_db
    db_file = tmp_path / "test_followup.db"
    init_db(db_file)
    return db_file
