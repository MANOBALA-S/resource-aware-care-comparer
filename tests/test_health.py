"""Tests for the health check and root endpoints.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from fastapi.testclient import TestClient


def test_health_check_status(client: TestClient) -> None:
    """Verify that GET /health returns HTTP 200 and {'status': 'ok'}."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


def test_health_check_governance_headers(client: TestClient) -> None:
    """Verify that GET /health attaches mandatory governance disclaimers in headers."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Decision-Support" in response.headers
    assert "clinician sign-off required" in response.headers["X-Decision-Support"].lower()
    assert "X-Data-Policy" in response.headers
    assert "synthetic data only" in response.headers["X-Data-Policy"].lower()


def test_health_check_detail(client: TestClient) -> None:
    """Verify that GET /health/detail provides complete system introspection."""
    response = client.get("/health/detail")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert data["app"]["version"] == "0.1.0"
    assert "en" in data["languages"]
    assert "ta" in data["languages"]
    assert "CRITICAL" in data["urgency_levels"]
    assert "L3" in data["escalation_levels"]


def test_root_endpoint(client: TestClient) -> None:
    """Verify that GET / returns the landing metadata and disclaimers."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Resource-Aware Care Option Comparer" in data["name"]
    assert "endpoints" in data
    assert data["endpoints"]["health"] == "/health"
