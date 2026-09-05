"""Tests for Tamil message catalog, translations, and reason trail localization.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
import pytest

from src.language.messages import get_all_messages, get_message, list_supported_languages
from src.language.translator import translate_reason_line, translate_reason_trail


def test_tamil_catalog_contains_all_required_keys() -> None:
    """Verify that data/languages/ta.json contains all required clinical and operational keys."""
    ta_messages = get_all_messages("ta")
    en_messages = get_all_messages("en")

    for key in en_messages.keys():
        assert key in ta_messages, f"Key '{key}' in en.json is missing from ta.json"
        assert len(ta_messages[key].strip()) > 0, f"Key '{key}' is empty in ta.json"


def test_tamil_specific_translations() -> None:
    """Verify exact Tamil phrases specified in requirements."""
    assert get_message("recommendation", lang="ta") == "பரிந்துரை"
    assert get_message("follow_up_required", lang="ta") == "பின்தொடர்தல் தேவை"
    assert get_message("escalation_required", lang="ta") == "அவசர மேலனுப்பல் தேவை"
    assert get_message("resource_unavailable", lang="ta") == "வளம் கிடைக்கவில்லை"
    assert get_message("interpreter_required", lang="ta") == "மொழிபெயர்ப்பாளர் தேவை"
    assert get_message("language_mismatch", lang="ta") == "மொழி பொருந்தவில்லை"
    assert get_message("no_feasible_option", lang="ta") == "சாத்தியமான சிகிச்சைத் தேர்வு இல்லை"
    assert get_message("prototype_disclaimer", lang="ta") == "முடிவு ஆதரவு முன்மாதிரி — மருத்துவர் ஒப்புதல் தேவை."
    assert get_message("language_escalation_required", lang="ta") == "மொழி அதிகரிப்பு தேவை"


def test_reason_trail_translation_example_from_spec() -> None:
    """Verify the exact prompt reason trail translation requirement:
    English: 'Preferred option blocked because specialist is unavailable.'
    Tamil: 'நிபுணர் கிடைக்காததால் விருப்பமான சிகிச்சைத் தேர்வு பயன்படுத்த முடியாது.'
    """
    en_line = "Preferred option blocked because specialist is unavailable."
    ta_line = translate_reason_line(en_line, lang="ta")
    assert ta_line == "நிபுணர் கிடைக்காததால் விருப்பமான சிகிச்சைத் தேர்வு பயன்படுத்த முடியாது."


def test_reason_trail_list_translation() -> None:
    """Verify translating a multi-line reason trail from English to Tamil."""
    trail_en = [
        "Language Safety: Patient language 'ta' is directly supported without translation barriers.",
        "Evaluated 'Preferred': FEASIBLE. All required resources and constraints are satisfied.",
        "FINAL DECISION: Selected 'Preferred' as the highest feasible care pathway for this patient's clinical and site constraints.",
    ]
    trail_ta = translate_reason_trail(trail_en, lang="ta")

    assert len(trail_ta) == 3
    assert "மொழி பாதுகாப்பு" in trail_ta[0]
    assert "சாத்தியமானது" in trail_ta[1]
    assert "இறுதி முடிவு" in trail_ta[2]


def test_english_trail_unchanged() -> None:
    """Verify that translate_reason_trail with lang='en' leaves strings unchanged."""
    trail_en = ["Preferred option blocked because specialist is unavailable."]
    res = translate_reason_trail(trail_en, lang="en")
    assert res == trail_en


def test_list_supported_languages_contains_tamil() -> None:
    """Verify list_supported_languages includes Tamil with proper native_name."""
    languages = list_supported_languages()
    ta_entry = next((l for l in languages if l["code"] == "ta"), None)
    assert ta_entry is not None
    assert ta_entry["name"] == "Tamil"
    assert ta_entry["native_name"] == "தமிழ்"
    assert ta_entry["locale"] == "ta_IN"
