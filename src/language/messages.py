"""Message catalog loader and localization service for English and Tamil.

Loads pre-compiled human-curated message dictionaries without external translation APIs.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import PROJECT_ROOT

DATA_LANGUAGES_DIR = PROJECT_ROOT / "data" / "languages"

_CATALOG_CACHE: Dict[str, Dict[str, Any]] = {}


def _load_catalog(lang_code: str) -> Dict[str, Any]:
    """Load JSON message catalog from disk with caching."""
    code = lang_code.strip().lower()
    if code in _CATALOG_CACHE:
        return _CATALOG_CACHE[code]

    target_path = DATA_LANGUAGES_DIR / f"{code}.json"
    if not target_path.is_file():
        # Fallback to English if target not found
        fallback_path = DATA_LANGUAGES_DIR / "en.json"
        if fallback_path.is_file():
            with open(fallback_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _CATALOG_CACHE[code] = data
                return data
        return {"messages": {}}

    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        _CATALOG_CACHE[code] = data
        return data


def get_message(key: str, lang: str = "en", **kwargs: Any) -> str:
    """Retrieve localized message string by key, with parameter formatting.

    Args:
        key: Message key in dictionary (e.g. 'recommendation', 'prototype_disclaimer')
        lang: Target language code ('en' or 'ta')
        **kwargs: Dynamic values to interpolate into message string

    Returns:
        Formatted localized message string, falling back to English or key itself if missing.
    """
    catalog = _load_catalog(lang)
    messages = catalog.get("messages", {})

    if key in messages:
        raw = messages[key]
        if kwargs:
            try:
                return raw.format(**kwargs)
            except Exception:
                return raw
        return raw

    # Fallback to English catalog if key not present in chosen language
    if lang.lower() != "en":
        en_catalog = _load_catalog("en")
        en_messages = en_catalog.get("messages", {})
        if key in en_messages:
            raw = en_messages[key]
            if kwargs:
                try:
                    return raw.format(**kwargs)
                except Exception:
                    return raw
            return raw

    return key


def get_all_messages(lang: str = "en") -> Dict[str, str]:
    """Retrieve full flat dictionary of messages for a given language."""
    catalog = _load_catalog(lang)
    return dict(catalog.get("messages", {}))


def list_supported_languages() -> List[Dict[str, Any]]:
    """Return list of supported languages with code, name, native name, and metadata."""
    supported = [
        {
            "code": "en",
            "name": "English",
            "native_name": "English",
            "direction": "ltr",
            "locale": "en_US",
            "is_default": True,
        },
        {
            "code": "ta",
            "name": "Tamil",
            "native_name": "தமிழ்",
            "direction": "ltr",
            "locale": "ta_IN",
            "is_default": False,
        },
    ]
    return supported
