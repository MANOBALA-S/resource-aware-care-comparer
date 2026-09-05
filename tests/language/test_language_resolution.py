"""Tests for deterministic language resolution rules.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
import pytest

from src.language.models import LanguageStatus
from src.language.resolver import normalize_language_code, resolve_language


def test_english_directly_supported() -> None:
    """Test English patient language directly supported by English-speaking clinician."""
    profile = resolve_language(
        patient_language="en",
        clinician_languages=["en"],
        interpreter_languages=[],
        interpreter_available=False,
    )
    assert profile.language_status == LanguageStatus.SUPPORTED
    assert profile.selected_language == "en"
    assert "directly supported" in (profile.explanation or "")


def test_tamil_directly_supported() -> None:
    """Test Tamil patient language directly supported by Tamil-speaking clinician."""
    profile = resolve_language(
        patient_language="ta",
        clinician_languages=["en", "ta"],
        interpreter_languages=[],
        interpreter_available=False,
    )
    assert profile.language_status == LanguageStatus.SUPPORTED
    assert profile.selected_language == "ta"
    assert "directly supported" in (profile.explanation or "")


def test_normalization_and_case_insensitivity() -> None:
    """Test that language strings like 'Tamil', 'EN', 'தமிழ்' are normalized properly."""
    assert normalize_language_code("TAMIL") == "ta"
    assert normalize_language_code("English") == "en"
    assert normalize_language_code("தமிழ்") == "ta"

    profile = resolve_language(
        patient_language="TAMIL",
        clinician_languages=["ENGLISH", "Tamil"],
    )
    assert profile.language_status == LanguageStatus.SUPPORTED
    assert profile.selected_language == "ta"


def test_preferred_language_override() -> None:
    """Test that preferred_language takes precedence when supported."""
    profile = resolve_language(
        patient_language="ta",
        preferred_language="en",
        clinician_languages=["en"],
    )
    assert profile.language_status == LanguageStatus.SUPPORTED
    assert profile.selected_language == "en"
