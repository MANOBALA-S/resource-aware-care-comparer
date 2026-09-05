"""Tests for configuration parsing, languages, urgency levels, and escalation rules.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from src.config import (
    get_escalation_detail,
    get_language,
    get_settings,
    get_supported_languages,
    get_urgency_detail,
)
from src.models.config_models import EscalationTier, SystemSettings, UrgencyLevel


def test_supported_languages(settings: SystemSettings) -> None:
    """Verify supported languages include English ('en') and Tamil ('ta')."""
    languages = get_supported_languages()
    lang_codes = [lang.code for lang in languages]
    assert "en" in lang_codes
    assert "ta" in lang_codes

    en_lang = get_language("en")
    assert en_lang is not None
    assert en_lang.name == "English"
    assert en_lang.direction == "ltr"
    assert en_lang.is_default is True

    ta_lang = get_language("ta")
    assert ta_lang is not None
    assert ta_lang.name == "Tamil"
    assert ta_lang.native_name == "தமிழ்"


def test_urgency_levels(settings: SystemSettings) -> None:
    """Verify that all four required urgency tiers exist with proper constraints."""
    required_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    for level in required_levels:
        detail = get_urgency_detail(level)
        assert detail is not None
        assert detail.code == UrgencyLevel(level)
        assert detail.default_followup_hours > 0
        assert isinstance(detail.max_escalation_tier, EscalationTier)

    # Validate relative time windows: CRITICAL should be faster than LOW
    critical_detail = get_urgency_detail(UrgencyLevel.CRITICAL)
    low_detail = get_urgency_detail(UrgencyLevel.LOW)
    assert critical_detail.default_followup_hours < low_detail.default_followup_hours


def test_escalation_levels(settings: SystemSettings) -> None:
    """Verify that escalation tiers L0-L3 are configured with responsibilities and timeouts."""
    tiers = ["L0", "L1", "L2", "L3"]
    for tier in tiers:
        detail = get_escalation_detail(tier)
        assert detail is not None
        assert detail.tier == EscalationTier(tier)
        assert detail.ack_timeout_minutes > 0
        assert len(detail.responsible_actor) > 0


def test_governance_disclaimers(settings: SystemSettings) -> None:
    """Verify that mandatory clinical governance strings are present."""
    gov = settings.governance
    assert "clinician sign-off required" in gov.prototype_disclaimer.lower()
    assert "synthetic data only" in gov.synthetic_data_policy.lower()
    assert gov.clinician_signoff_mandatory is True
