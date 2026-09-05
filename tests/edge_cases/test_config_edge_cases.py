"""Edge case tests for configuration validation, missing resources, and invalid inputs.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from pathlib import Path
import pytest
from pydantic import ValidationError

from src.config import (
    _load_yaml_file,
    build_default_settings,
    get_escalation_detail,
    get_language,
    get_urgency_detail,
)
from src.models.config_models import (
    EscalationDetail,
    EscalationTier,
    LanguageConfig,
    UrgencyDetail,
    UrgencyLevel,
)


def test_unknown_language_lookup() -> None:
    """Verify lookup for an unconfigured language code returns None without error."""
    assert get_language("fr") is None
    assert get_language("") is None
    assert get_language("123") is None


def test_case_insensitive_language_lookup() -> None:
    """Verify language code lookup is case-insensitive."""
    en_lower = get_language("en")
    en_upper = get_language("EN")
    assert en_lower is not None
    assert en_upper is not None
    assert en_lower.code == en_upper.code

    ta_mixed = get_language("Ta")
    assert ta_mixed is not None
    assert ta_mixed.code == "ta"


def test_unknown_urgency_and_escalation() -> None:
    """Verify requesting undefined urgency or escalation tiers gracefully returns None."""
    assert get_urgency_detail("EXTREME") is None
    assert get_urgency_detail("") is None
    assert get_escalation_detail("L99") is None
    assert get_escalation_detail("ALPHA") is None


def test_invalid_urgency_enum() -> None:
    """Verify constructing an invalid urgency enum raises ValueError."""
    with pytest.raises(ValueError):
        UrgencyLevel("NON_EXISTENT")


def test_invalid_escalation_tier() -> None:
    """Verify constructing an invalid escalation tier raises ValueError."""
    with pytest.raises(ValueError):
        EscalationTier("L4")


def test_invalid_language_direction_validation() -> None:
    """Verify that unsupported text direction triggers Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        LanguageConfig(
            code="test",
            name="Test",
            native_name="Test",
            direction="diagonal",  # Invalid; only 'ltr' or 'rtl' allowed
            locale="te_ST",
        )


def test_negative_timeout_validation() -> None:
    """Verify that negative timeouts are rejected by Pydantic models."""
    with pytest.raises(ValidationError):
        EscalationDetail(
            tier=EscalationTier.L0,
            title="Invalid Timeout",
            responsible_actor="Coordinator",
            ack_timeout_minutes=-15,
            description="Testing negative boundary",
        )


def test_nonexistent_yaml_file_handling(tmp_path: Path) -> None:
    """Verify that attempting to load a non-existent YAML file safely returns empty dict."""
    non_existent = tmp_path / "does_not_exist.yaml"
    result = _load_yaml_file(non_existent)
    assert result == {}


def test_build_settings_with_missing_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify build_default_settings safely falls back to defaults when configs are missing."""
    empty_dir = tmp_path / "empty_config"
    empty_dir.mkdir()
    monkeypatch.setattr("src.config.CONFIG_DIR", empty_dir)

    settings = build_default_settings()
    assert settings.app.name == "Resource-Aware Care Option Comparer"
    assert "LOW" in settings.urgency_levels
    assert "CRITICAL" in settings.urgency_levels
    assert "L0" in settings.escalation_levels
    assert len(settings.languages) >= 2
