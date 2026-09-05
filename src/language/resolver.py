"""Deterministic language resolver for teleconsultation patient-clinician communication.

Ensures that language barriers cannot cause unsafe silent miscommunication.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from typing import List, Optional
from src.language.models import LanguageProfile, LanguageStatus

# Standard language code normalization dictionary
_LANG_SYNONYMS = {
    "en": "en",
    "english": "en",
    "eng": "en",
    "ta": "ta",
    "tamil": "ta",
    "tam": "ta",
    "தமிழ்": "ta",
}


def normalize_language_code(code: Optional[str]) -> Optional[str]:
    """Normalize language code or name to standard 2-letter ISO code where known."""
    if not code:
        return None
    cleaned = code.strip().lower()
    return _LANG_SYNONYMS.get(cleaned, cleaned)


def normalize_language_list(languages: List[str]) -> List[str]:
    """Normalize a list of language codes or names."""
    result: List[str] = []
    for lang in languages:
        norm = normalize_language_code(lang)
        if norm and norm not in result:
            result.append(norm)
    return result


def resolve_language(
    patient_language: str,
    clinician_languages: List[str],
    interpreter_languages: Optional[List[str]] = None,
    interpreter_available: bool = True,
    preferred_language: Optional[str] = None,
) -> LanguageProfile:
    """Evaluate patient language compatibility against available clinician and interpreter capabilities.

    Rules:
    1. If patient/preferred language is directly supported by clinician:
       -> SUPPORTED
    2. If clinician does not speak language, but interpreter is available and supports it:
       -> REQUIRES_INTERPRETER
    3. If neither clinician nor interpreter supports language (or interpreter is unavailable):
       -> LANGUAGE_ESCALATION_REQUIRED

    Safety invariant: Never silently proceed with care if language cannot be supported.

    Args:
        patient_language: Mother tongue or primary language of the patient.
        clinician_languages: Languages spoken by available healthcare provider(s).
        interpreter_languages: Languages covered by available translator services.
        interpreter_available: Whether interpreter is functionally on-duty/accessible.
        preferred_language: Optional preferred communication language.

    Returns:
        Structured LanguageProfile with deterministic LanguageStatus.
    """
    interp_langs = interpreter_languages or []

    norm_patient = normalize_language_code(patient_language) or patient_language.strip().lower()
    norm_preferred = normalize_language_code(preferred_language) if preferred_language else None
    target_lang = norm_preferred or norm_patient

    norm_clinician_langs = normalize_language_list(clinician_languages)
    norm_interp_langs = normalize_language_list(interp_langs)

    # Rule 1: Direct clinician communication
    if target_lang in norm_clinician_langs:
        return LanguageProfile(
            patient_language=patient_language,
            preferred_language=preferred_language,
            clinician_languages=clinician_languages,
            interpreter_languages=interp_langs,
            interpreter_available=interpreter_available,
            selected_language=target_lang,
            language_status=LanguageStatus.SUPPORTED,
            explanation=f"Patient language '{target_lang}' is directly supported by clinician.",
        )

    # Rule 2: Clinician does not speak language, but interpreter is available
    if interpreter_available and (target_lang in norm_interp_langs):
        return LanguageProfile(
            patient_language=patient_language,
            preferred_language=preferred_language,
            clinician_languages=clinician_languages,
            interpreter_languages=interp_langs,
            interpreter_available=interpreter_available,
            selected_language=target_lang,
            language_status=LanguageStatus.REQUIRES_INTERPRETER,
            explanation=(
                f"Clinician does not speak '{target_lang}'; interpreter is required and confirmed available."
            ),
        )

    # Rule 3: Communication cannot be safely supported -> Escalate
    reason = (
        f"Language escalation required: Patient language '{target_lang}' is unsupported by clinician "
        f"{norm_clinician_langs}"
    )
    if not interpreter_available:
        reason += " and interpreter services are unavailable."
    else:
        reason += f" and unsupported by available interpreters {norm_interp_langs}."

    return LanguageProfile(
        patient_language=patient_language,
        preferred_language=preferred_language,
        clinician_languages=clinician_languages,
        interpreter_languages=interp_langs,
        interpreter_available=interpreter_available,
        selected_language=None,
        language_status=LanguageStatus.LANGUAGE_ESCALATION_REQUIRED,
        explanation=reason,
    )
