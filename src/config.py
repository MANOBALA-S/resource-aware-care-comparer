"""Configuration loader and manager for Resource-Aware Care Option Comparer.

Loads declarative YAML configuration files with fallback defaults and environment overrides.
Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from functools import lru_cache
import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from src.models.config_models import (
    AppConfig,
    EscalationDetail,
    EscalationTier,
    GovernanceConfig,
    LanguageConfig,
    SystemSettings,
    UrgencyDetail,
    UrgencyLevel,
)

# Project base directory resolved relative to this source file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def _load_yaml_file(filepath: Path) -> dict:
    """Safely load and parse a YAML file if it exists, returning an empty dictionary on error."""
    if not filepath.is_file():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content if isinstance(content, dict) else {}
    except Exception:
        return {}


def build_default_settings() -> SystemSettings:
    """Build a complete SystemSettings instance using file configuration with built-in fallbacks."""
    default_config_path = CONFIG_DIR / "default_config.yaml"
    languages_config_path = CONFIG_DIR / "languages.yaml"

    raw_app = _load_yaml_file(default_config_path)
    raw_lang = _load_yaml_file(languages_config_path)

    # 1. App Configuration
    app_data = raw_app.get("app", {})
    app_config = AppConfig(
        name=str(os.getenv("APP_NAME", app_data.get("name", "Resource-Aware Care Option Comparer"))),
        version=str(os.getenv("APP_VERSION", app_data.get("version", "0.1.0"))),
        environment=str(os.getenv("APP_ENV", app_data.get("environment", "development"))),
        host=str(os.getenv("APP_HOST", app_data.get("host", "127.0.0.1"))),
        port=int(os.getenv("APP_PORT", app_data.get("port", 8000))),
        debug=bool(os.getenv("APP_DEBUG", app_data.get("debug", True))),
        database_url=str(os.getenv("DATABASE_URL", app_data.get("database_url", "sqlite:///data/care_comparer.db"))),
    )

    # 2. Governance
    gov_data = raw_app.get("governance", {})
    governance_config = GovernanceConfig(
        prototype_disclaimer=str(
            gov_data.get("prototype_disclaimer", "Decision-support prototype — clinician sign-off required.")
        ),
        synthetic_data_policy=str(
            gov_data.get("synthetic_data_policy", "Synthetic data only — no real patient data.")
        ),
        clinician_signoff_mandatory=bool(gov_data.get("clinician_signoff_mandatory", True)),
    )

    # 3. Urgency Levels
    urgency_raw = raw_app.get("urgency_levels", {})
    urgency_levels: Dict[str, UrgencyDetail] = {}
    fallback_urgencies = {
        "LOW": ("Low Urgency", "Stable chronic monitoring, routine triage", 72, "L1"),
        "MEDIUM": ("Medium Urgency", "Sub-acute conditions, elevated vitals", 24, "L2"),
        "HIGH": ("High Urgency", "Acute clinical risk, progressive symptoms", 6, "L3"),
        "CRITICAL": ("Critical Urgency", "Immediate life/limb threat, acute distress", 1, "L3"),
    }
    for level_key in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        if level_key in urgency_raw:
            item = urgency_raw[level_key]
            urgency_levels[level_key] = UrgencyDetail(
                code=UrgencyLevel(item.get("code", level_key)),
                label=item.get("label", level_key),
                description=item.get("description", ""),
                default_followup_hours=int(item.get("default_followup_hours", 24)),
                max_escalation_tier=EscalationTier(item.get("max_escalation_tier", "L3")),
            )
        else:
            fb = fallback_urgencies[level_key]
            urgency_levels[level_key] = UrgencyDetail(
                code=UrgencyLevel(level_key),
                label=fb[0],
                description=fb[1],
                default_followup_hours=fb[2],
                max_escalation_tier=EscalationTier(fb[3]),
            )

    # 4. Escalation Levels
    escalation_raw = raw_app.get("escalation_levels", {})
    escalation_levels: Dict[str, EscalationDetail] = {}
    fallback_escalations = {
        "L0": ("Local Health Worker Assessment", "Local health worker", 60, "Field acknowledgment"),
        "L1": ("Care Coordinator Intervention", "Care coordinator", 180, "Logistics orchestration"),
        "L2": ("Remote Clinician Re-evaluation", "Remote clinician", 360, "Physician teleconsultation review"),
        "L3": ("Emergency Facility Transfer", "Emergency transfer team", 30, "Immediate direct transfer"),
    }
    for tier_key in ("L0", "L1", "L2", "L3"):
        if tier_key in escalation_raw:
            item = escalation_raw[tier_key]
            escalation_levels[tier_key] = EscalationDetail(
                tier=EscalationTier(item.get("tier", tier_key)),
                title=item.get("title", tier_key),
                responsible_actor=item.get("responsible_actor", "Coordinator"),
                ack_timeout_minutes=int(item.get("ack_timeout_minutes", 60)),
                description=item.get("description", ""),
            )
        else:
            fb = fallback_escalations[tier_key]
            escalation_levels[tier_key] = EscalationDetail(
                tier=EscalationTier(tier_key),
                title=fb[0],
                responsible_actor=fb[1],
                ack_timeout_minutes=fb[2],
                description=fb[3],
            )

    # 5. Languages
    raw_lang_list = raw_lang.get("languages", [])
    languages: List[LanguageConfig] = []
    if raw_lang_list:
        for l_item in raw_lang_list:
            languages.append(
                LanguageConfig(
                    code=l_item["code"],
                    name=l_item["name"],
                    native_name=l_item["native_name"],
                    direction=l_item.get("direction", "ltr"),
                    is_default=l_item.get("is_default", False),
                    enabled=l_item.get("enabled", True),
                    locale=l_item.get("locale", f"{l_item['code']}_US"),
                    description=l_item.get("description"),
                )
            )
    else:
        languages = [
            LanguageConfig(
                code="en",
                name="English",
                native_name="English",
                direction="ltr",
                is_default=True,
                enabled=True,
                locale="en_US",
                description="Default administrative and clinical language",
            ),
            LanguageConfig(
                code="ta",
                name="Tamil",
                native_name="தமிழ்",
                direction="ltr",
                is_default=False,
                enabled=True,
                locale="ta_IN",
                description="Regional vernacular language",
            ),
        ]

    default_lang = raw_lang.get("default_language", "en")

    return SystemSettings(
        app=app_config,
        governance=governance_config,
        urgency_levels=urgency_levels,
        escalation_levels=escalation_levels,
        languages=languages,
        default_language=default_lang,
    )


@lru_cache()
def get_settings() -> SystemSettings:
    """Cached accessor for singleton system settings."""
    return build_default_settings()


def get_supported_languages() -> List[LanguageConfig]:
    """Return all active supported languages."""
    return [lang for lang in get_settings().languages if lang.enabled]


def get_language(code: str) -> Optional[LanguageConfig]:
    """Retrieve language metadata by ISO code."""
    for lang in get_settings().languages:
        if lang.code.lower() == code.lower():
            return lang
    return None


def get_urgency_detail(urgency: UrgencyLevel | str) -> Optional[UrgencyDetail]:
    """Retrieve operational details for an urgency level."""
    key = urgency.value if isinstance(urgency, UrgencyLevel) else str(urgency).upper()
    return get_settings().urgency_levels.get(key)


def get_escalation_detail(tier: EscalationTier | str) -> Optional[EscalationDetail]:
    """Retrieve operational details for an escalation tier."""
    key = tier.value if isinstance(tier, EscalationTier) else str(tier).upper()
    return get_settings().escalation_levels.get(key)
