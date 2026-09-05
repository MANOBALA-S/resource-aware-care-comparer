"""Tests for English message catalog and retrieval functions.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
import pytest

from src.language.messages import (
    get_all_messages,
    get_message,
    list_supported_languages,
)


REQUIRED_KEYS = [
    "recommendation",
    "follow_up_required",
    "escalation_required",
    "resource_unavailable",
    "interpreter_required",
    "language_mismatch",
    "no_feasible_option",
    "prototype_disclaimer",
    "synthetic_data_policy",
    "language_escalation_required",
]


def test_english_catalog_contains_all_required_keys() -> None:
    """Verify that data/languages/en.json contains all required clinical and operational keys."""
    en_messages = get_all_messages("en")
    for key in REQUIRED_KEYS:
        assert key in en_messages, f"Key '{key}' missing from en.json catalog"
        assert len(en_messages[key].strip()) > 0, f"Key '{key}' is empty in en.json"


def test_get_message_english_returns_exact_text() -> None:
    """Verify specific English translations."""
    assert get_message("recommendation", lang="en") == "Recommendation"
    assert get_message("follow_up_required", lang="en") == "Follow-up required"
    assert get_message("escalation_required", lang="en") == "Escalation required"
    assert get_message("resource_unavailable", lang="en") == "Resource unavailable"
    assert get_message("prototype_disclaimer", lang="en") == "Decision-support prototype — clinician sign-off required."
    assert get_message("synthetic_data_policy", lang="en") == "Synthetic data only — no real patient data."


def test_fallback_to_key_if_missing() -> None:
    """Verify graceful fallback when an undefined key is queried."""
    assert get_message("unknown_nonexistent_key", lang="en") == "unknown_nonexistent_key"


def test_list_supported_languages_contains_english() -> None:
    """Verify list_supported_languages returns English entry with correct metadata."""
    languages = list_supported_languages()
    en_entry = next((l for l in languages if l["code"] == "en"), None)
    assert en_entry is not None
    assert en_entry["name"] == "English"
    assert en_entry["is_default"] is True
