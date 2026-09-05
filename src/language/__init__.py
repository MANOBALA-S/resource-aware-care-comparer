"""Multilingual Language Layer package supporting English and Tamil end-to-end.

Prevents silent communication failures in teleconsultations.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from src.language.messages import (
    get_all_messages,
    get_message,
    list_supported_languages,
)
from src.language.models import LanguageProfile, LanguageStatus
from src.language.resolver import normalize_language_code, resolve_language
from src.language.translator import translate_reason_line, translate_reason_trail

__all__ = [
    "LanguageProfile",
    "LanguageStatus",
    "get_all_messages",
    "get_message",
    "list_supported_languages",
    "normalize_language_code",
    "resolve_language",
    "translate_reason_line",
    "translate_reason_trail",
]
