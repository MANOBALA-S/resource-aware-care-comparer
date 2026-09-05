"""Presentation-layer translation for clinical reason trails and decision-support rationale.

Translates internal English reason trail lines into natural, human-readable Tamil
while preserving underlying machine-readable codes and telemetry.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import re
from typing import List, Optional

# Tier mapping for Tamil presentation
TIER_TRANSLATIONS = {
    "preferred": "விருப்பமான சிகிச்சைத் தேர்வு",
    "Preferred": "விருப்பமான சிகிச்சைத் தேர்வு",
    "resource_adapted_alternative": "வள-தழுவிய மாற்று சிகிச்சை",
    "Resource Adapted Alternative": "வள-தழுவிய மாற்று சிகிச்சை",
    "minimum_safe_fallback": "குறைந்தபட்ச பாதுகாப்பான வழி",
    "Minimum Safe Fallback": "குறைந்தபட்ச பாதுகாப்பான வழி",
    "escalate_only": "அவசர மேலனுப்பல்",
    "Escalate Only": "அவசர மேலனுப்பல்",
}

# Common phrase and blocking rationale patterns in Tamil
BLOCKING_PATTERNS = [
    (
        r"preferred option blocked because specialist is unavailable\.?",
        "நிபுணர் கிடைக்காததால் விருப்பமான சிகிச்சைத் தேர்வு பயன்படுத்த முடியாது.",
    ),
    (
        r"resource-adapted alternative blocked because transport is unavailable\.?",
        "போக்குவரத்து வசதி இல்லாததால் வள-தழுவிய மாற்று சிகிச்சை பயன்படுத்த முடியாது.",
    ),
    (
        r"specialist.*unavailable within.*timeframe",
        "மருத்துவ காலக்கெடுவிற்குள் சிறப்பு மருத்துவர் கிடைக்கவில்லை",
    ),
    (
        r"specialist cadre .* unavailable at site",
        "சிகிச்சை மையத்தில் தேவையான சிறப்பு மருத்துவர் இல்லை",
    ),
    (
        r"safe transport unavailable.*",
        "பாதுகாப்பான நோயாளி போக்குவரத்து வசதி இல்லை",
    ),
    (
        r"cold chain required but unavailable.*",
        "தேவையான குளிர்பதன வசதி சிகிச்சை மையத்தில் இல்லை",
    ),
    (
        r"required medication '([^']+)' out of stock",
        r"தேவையான மருந்து '\1' கையிருப்பில் இல்லை",
    ),
    (
        r"connectivity insufficient.*",
        "இணைய இணைப்பு வேகம் தொலைநிலை கண்காணிப்புக்கு போதுமானதாக இல்லை",
    ),
    (
        r"direct conflict: site equipment .* verified operational",
        "நேரடி முரண்பாடு: கருவி ஆய்வக பதிவுகளில் செயல்பாட்டில் இல்லை என உள்ளது (பாதுகாப்பு முதன்மை விதி)",
    ),
]


def _translate_blocking_reasons_ta(reasons_str: str) -> str:
    """Translate semicolon-separated or comma-separated blocking reasons to Tamil."""
    parts = [p.strip() for p in reasons_str.split(";")]
    translated_parts = []
    for part in parts:
        matched = False
        for pattern, replacement in BLOCKING_PATTERNS:
            if re.search(pattern, part, re.IGNORECASE):
                translated_parts.append(re.sub(pattern, replacement, part, flags=re.IGNORECASE))
                matched = True
                break
        if not matched:
            translated_parts.append(part)
    return "; ".join(translated_parts)


def translate_reason_line(line: str, lang: str = "en") -> str:
    """Translate a single reason trail line to the requested display language."""
    if lang.strip().lower() != "ta":
        return line

    cleaned = line.strip()

    # Direct exact matches
    for pattern, replacement in BLOCKING_PATTERNS:
        if re.fullmatch(pattern, cleaned, re.IGNORECASE):
            return replacement

    # 1. Language Safety evaluations
    m_lang_sup = re.match(
        r"Language Safety: Patient language '([^']+)' is directly supported without translation barriers\.",
        cleaned,
        re.IGNORECASE,
    )
    if m_lang_sup:
        return f"மொழி பாதுகாப்பு: நோயாளியின் மொழி '{m_lang_sup.group(1)}' மொழிபெயர்ப்பு தடைகள் இன்றி நேரடியாக ஆதரிக்கப்படுகிறது."

    m_lang_interp = re.match(
        r"Language Safety: Patient language '([^']+)' requires an interpreter; translator is confirmed available\.",
        cleaned,
        re.IGNORECASE,
    )
    if m_lang_interp:
        return f"மொழி பாதுகாப்பு: நோயாளியின் மொழி '{m_lang_interp.group(1)}' மொழிபெயர்ப்பாளர் தேவைப்படுகிறது; மொழிபெயர்ப்பாளர் இருப்பது உறுதி செய்யப்பட்டது."

    m_lang_alert = re.match(
        r"Language Safety ALERT: Patient language '([^']+)' is unsupported by available clinicians and interpreters\. Language escalation triggered\.",
        cleaned,
        re.IGNORECASE,
    )
    if m_lang_alert:
        return f"மொழி பாதுகாப்பு எச்சரிக்கை: நோயாளியின் மொழி '{m_lang_alert.group(1)}' மருத்துவர் அல்லது மொழிபெயர்ப்பாளரால் ஆதரிக்கப்படவில்லை. மொழி அதிகரிப்பு தொடங்கப்பட்டது."

    # 2. Option evaluation: FEASIBLE
    m_opt_feas = re.match(
        r"Evaluated '([^']+)': FEASIBLE\. All required resources and constraints are satisfied\.",
        cleaned,
        re.IGNORECASE,
    )
    if m_opt_feas:
        tier = m_opt_feas.group(1)
        ta_tier = TIER_TRANSLATIONS.get(tier, tier)
        return f"மதிப்பீடு '{ta_tier}': சாத்தியமானது. தேவையான அனைத்து வளங்களும் நிபந்தனைகளும் பூர்த்தி செய்யப்பட்டுள்ளன."

    # 3. Option evaluation: BLOCKED
    m_opt_block = re.match(
        r"Evaluated '([^']+)': BLOCKED\. Constraints not met: (.*)\.",
        cleaned,
        re.IGNORECASE,
    )
    if m_opt_block:
        tier = m_opt_block.group(1)
        reasons = m_opt_block.group(2)
        ta_tier = TIER_TRANSLATIONS.get(tier, tier)
        ta_reasons = _translate_blocking_reasons_ta(reasons)
        return f"மதிப்பீடு '{ta_tier}': தடுக்கப்பட்டது. பூர்த்தி செய்யப்படாத தடைகள்: {ta_reasons}."

    # 4. Final decision: ESCALATE_IMMEDIATELY
    m_dec_esc = re.match(
        r"FINAL DECISION: ESCALATE_IMMEDIATELY\. All local treatment rungs \(preferred, adapted, fallback\) are infeasible\. Reason: (.*)\.",
        cleaned,
        re.IGNORECASE,
    )
    if m_dec_esc:
        reason = m_dec_esc.group(1)
        ta_reason = _translate_blocking_reasons_ta(reason)
        return f"இறுதி முடிவு: உடனடியாக அவசர மேலனுப்பல் செய்க. உள்ளூர் சிகிச்சை முறைகள் எதுவும் சாத்தியமில்லை. காரணம்: {ta_reason}."

    # 5. Final decision: Selected tier
    m_dec_sel = re.match(
        r"FINAL DECISION: Selected '([^']+)' as the highest feasible care pathway for this patient's clinical and site constraints\.",
        cleaned,
        re.IGNORECASE,
    )
    if m_dec_sel:
        tier = m_dec_sel.group(1)
        ta_tier = TIER_TRANSLATIONS.get(tier, tier)
        return f"இறுதி முடிவு: நோயாளியின் மருத்துவ மற்றும் கள நிலைமைகளுக்கு ஏற்ப '{ta_tier}' சிறந்த சாத்தியமான சிகிச்சை முறையாக தேர்ந்தெடுக்கப்பட்டது."

    # Fallback to applying any regex phrases found in line
    result = cleaned
    for pattern, replacement in BLOCKING_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def translate_reason_trail(reason_trail: List[str], lang: str = "en") -> List[str]:
    """Translate an entire reason trail list into the designated display language.

    Args:
        reason_trail: List of chronological reason trail entries in English.
        lang: Target display language code ('en' or 'ta').

    Returns:
        Translated list of reason trail statements.
    """
    if lang.strip().lower() != "ta":
        return list(reason_trail)
    return [translate_reason_line(line, lang="ta") for line in reason_trail]
