"""Tests for language escalation safety triggers and API endpoints.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from fastapi.testclient import TestClient
import pytest

from src.language.models import LanguageStatus
from src.language.resolver import resolve_language


def test_unsupported_language_and_no_interpreter_triggers_escalation() -> None:
    """Test requirement: 'Unsupported language + no interpreter -> LANGUAGE_ESCALATION_REQUIRED'."""
    profile = resolve_language(
        patient_language="kn",  # Kannada
        clinician_languages=["en"],
        interpreter_languages=["ta"],  # Only Tamil interpreter available
        interpreter_available=True,
    )
    assert profile.language_status == LanguageStatus.LANGUAGE_ESCALATION_REQUIRED
    assert profile.selected_language is None
    assert "unsupported by available interpreters" in (profile.explanation or "")


def test_unsupported_language_and_interpreter_false_triggers_escalation() -> None:
    """Test safety invariant: patient language unsupported and interpreter unavailable."""
    profile = resolve_language(
        patient_language="te",  # Telugu
        clinician_languages=["en"],
        interpreter_languages=[],
        interpreter_available=False,
    )
    assert profile.language_status == LanguageStatus.LANGUAGE_ESCALATION_REQUIRED
    assert profile.selected_language is None


def test_api_languages_endpoint(client: TestClient) -> None:
    """Test GET /languages returns supported languages metadata."""
    res = client.get("/languages")
    assert res.status_code == 200
    langs = res.json()
    assert len(langs) >= 2
    codes = [l["code"] for l in langs]
    assert "en" in codes
    assert "ta" in codes


def test_api_language_messages_endpoint(client: TestClient) -> None:
    """Test GET /languages/{code}/messages returns valid message dictionary."""
    res_en = client.get("/languages/en/messages")
    assert res_en.status_code == 200
    msgs_en = res_en.json()
    assert msgs_en["recommendation"] == "Recommendation"

    res_ta = client.get("/languages/ta/messages")
    assert res_ta.status_code == 200
    msgs_ta = res_ta.json()
    assert msgs_ta["recommendation"] == "பரிந்துரை"


def test_api_unsupported_language_messages_returns_404(client: TestClient) -> None:
    """Test GET /languages/{code}/messages returns 404 for unsupported language."""
    res = client.get("/languages/fr/messages")
    assert res.status_code == 404


def test_api_evaluate_endpoint_localized(client: TestClient) -> None:
    """Test POST /evaluate returns localized reason trail in Tamil when requested."""
    res = client.post(
        "/evaluate",
        json={
            "case_id": "SYNTH-CASE-001",
            "lang": "ta",
            "clinician_languages": ["en"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "SYNTH-CASE-001"
    assert data["lang"] == "ta"
    assert len(data["reason_trail"]) > 0
    # Reason trail must contain Tamil script for safety/decision steps
    has_tamil = any("மொழி" in step or "முடிவு" in step or "மதிப்பீடு" in step for step in data["reason_trail"])
    assert has_tamil, f"Expected Tamil script in reason trail: {data['reason_trail']}"
