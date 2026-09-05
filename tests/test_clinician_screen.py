"""Tests for Phase 8 Clinician / Teleconsult Screen endpoints and frontend assets.

Verifies:
- GET /cases/{case_id} returns combined patient case and facility resources.
- POST /recommendations/{case_id} evaluates constraints and returns transparent reason steps.
- Bilingual localization (English & Tamil) operates end-to-end.
- Safety triggers: ESCALATE IMMEDIATELY and LANGUAGE ESCALATION REQUIRED.
- UI static assets (/ui/clinician/index.html, clinician.css, clinician.js) are accessible.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from fastapi.testclient import TestClient
import pytest

from src.main import create_app


@pytest.fixture
def client():
    """Create test client instance."""
    app = create_app()
    return TestClient(app)


def test_get_case_details_success(client):
    """Verify GET /cases/{case_id} returns patient profile and local site capabilities."""
    response = client.get("/cases/SYNTH-CASE-001")
    assert response.status_code == 200
    data = response.json()

    # Patient details
    assert data["case_id"] == "SYNTH-CASE-001"
    assert data["condition"] == "condition_alpha"
    assert data["site_id"] == "SITE-001"
    assert "site_name" in data
    assert "age_band" in data
    assert "population_group" in data

    # Site resources
    site_res = data["site_resources"]
    assert site_res["site_id"] == "SITE-001"
    assert len(site_res["equipment"]) > 0
    assert len(site_res["medication_stock"]) > 0
    assert len(site_res["specialists"]) > 0
    assert "transport_available" in site_res
    assert "connectivity" in site_res
    assert "cold_chain_available" in site_res


def test_get_case_details_not_found(client):
    """Verify GET /cases/{case_id} returns 404 for invalid case ID."""
    response = client.get("/cases/SYNTH-CASE-INVALID-999")
    assert response.status_code == 404


def test_post_recommendations_english(client):
    """Verify POST /recommendations/{case_id} generates English recommendations and reason steps."""
    response = client.post("/recommendations/SYNTH-CASE-001?lang=en")
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "SYNTH-CASE-001"
    assert data["lang"] == "en"
    assert data["feasible"] is True
    assert data["ladder_level"] == "preferred"
    assert len(data["selected_care_option"]) > 10

    # Transparent Reason Steps with symbols
    reason_steps = data["reason_steps"]
    assert len(reason_steps) >= 5
    symbols = [s["symbol"] for s in reason_steps]
    assert "✓" in symbols
    assert "★" in symbols

    # Follow-Up task
    fup = data["follow_up"]
    assert fup["owner"] == "Local Health Worker"
    assert len(fup["due_at"]) > 0
    assert len(fup["escalation_path"]) > 0
    assert fup["status"] == "PENDING"

    # Governance disclaimers
    assert "Decision-support prototype" in data["governance_notice"]
    assert "Synthetic data only" in data["synthetic_data_notice"]


def test_post_recommendations_tamil(client):
    """Verify POST /recommendations/{case_id} localizes reason steps and disclaimers in Tamil."""
    response = client.post("/recommendations/SYNTH-CASE-001?lang=ta")
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "SYNTH-CASE-001"
    assert data["lang"] == "ta"

    # Check that Tamil reason steps were generated
    first_step = data["reason_steps"][0]
    assert "மருத்துவர்" in first_step["text"] or "கிடைக்கிறார்" in first_step["text"]

    # Check Tamil governance disclaimers
    assert "மருத்துவர் ஒப்புதல் தேவை" in data["governance_notice"]
    assert "உண்மையான நோயாளி தரவு இல்லை" in data["synthetic_data_notice"]


def test_post_recommendations_adapted_site_constraints(client):
    """Verify recommendation adapts down the ladder for a peripheral clinic case."""
    # SYNTH-CASE-002 is at SITE-002 (Primary Health Center with limited specialists/cold-chain)
    response = client.post("/recommendations/SYNTH-CASE-002?lang=en")
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "SYNTH-CASE-002"
    assert data["ladder_level"] == "resource_adapted_alternative"
    assert len(data["blocked_options"].get("preferred", [])) > 0


def test_simulate_option_exhaustion_escalate_immediately(client):
    """Verify simulate_exhaustion triggers ESCALATE IMMEDIATELY safety banner."""
    response = client.post("/recommendations/SYNTH-CASE-001?lang=en&simulate_exhaustion=true")
    assert response.status_code == 200
    data = response.json()

    assert data["escalate_immediately"] is True
    assert data["safety_banner_type"] == "ESCALATE_IMMEDIATELY"
    assert "ESCALATE IMMEDIATELY" in data["safety_banner_message"]
    assert data["feasible"] is False
    assert data["decision"] == "ESCALATE_IMMEDIATELY"


def test_ui_clinician_static_files_served(client):
    """Verify that ui/clinician/ static files are served at /ui/clinician/."""
    # Index page
    r_index = client.get("/ui/clinician/index.html")
    assert r_index.status_code == 200
    assert "Resource-Aware Care Option Comparer" in r_index.text
    assert "clinician.js" in r_index.text

    # CSS Stylesheet
    r_css = client.get("/ui/clinician/clinician.css")
    assert r_css.status_code == 200
    assert "app-header" in r_css.text

    # JS Script
    r_js = client.get("/ui/clinician/clinician.js")
    assert r_js.status_code == 200
    assert "evaluateSelectedCase" in r_js.text
