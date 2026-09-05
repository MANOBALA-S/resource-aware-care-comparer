"""Tests for interpreter requirement and availability handling.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
import pytest

from src.language.models import LanguageStatus
from src.language.resolver import resolve_language


def test_tamil_patient_with_english_clinician_requires_interpreter() -> None:
    """Test Tamil patient with English-only clinician triggers REQUIRES_INTERPRETER when interpreter available."""
    profile = resolve_language(
        patient_language="ta",
        clinician_languages=["en"],
        interpreter_languages=["ta"],
        interpreter_available=True,
    )
    assert profile.language_status == LanguageStatus.REQUIRES_INTERPRETER
    assert profile.selected_language == "ta"
    assert "interpreter is required and confirmed available" in (profile.explanation or "")


def test_unsupported_language_with_available_interpreter() -> None:
    """Test requirement: 'Unsupported language + interpreter -> REQUIRES_INTERPRETER'."""
    profile = resolve_language(
        patient_language="hi",  # Hindi
        clinician_languages=["en", "ta"],
        interpreter_languages=["hi", "te"],
        interpreter_available=True,
    )
    assert profile.language_status == LanguageStatus.REQUIRES_INTERPRETER
    assert profile.selected_language == "hi"


def test_interpreter_unavailable_when_needed_escalates() -> None:
    """Test that if interpreter speaks the language but is marked unavailable, it escalates."""
    profile = resolve_language(
        patient_language="ta",
        clinician_languages=["en"],
        interpreter_languages=["ta"],
        interpreter_available=False,
    )
    assert profile.language_status == LanguageStatus.LANGUAGE_ESCALATION_REQUIRED
    assert profile.selected_language is None
    assert "interpreter services are unavailable" in (profile.explanation or "")
