"""Unit and integration tests for Phase 14: Ethics & Deployment Documentation.

Verifies:
1. docs/03_ethics_note.md existence, mandatory sections, and all 14 ethical topics
2. docs/04_deployment_checklist.md existence, all 7 checklist categories, and sub-items
3. Mandatory disclaimers and non-production declarations present in both documents
4. Strict compliance with "not production-ready healthcare software"

No real patient data is used. Decision-support prototype — clinician sign-off required.
"""
from pathlib import Path
import pytest

from src.config import PROJECT_ROOT

MANDATORY_DISCLAIMER_PHRASE = (
    "This prototype is intended for demonstration and evaluation and requires "
    "clinical, regulatory, security, and operational validation before real-world deployment."
)


def test_ethics_note_exists_and_contains_mandatory_disclaimer():
    """Verify docs/03_ethics_note.md exists and contains the required disclaimers."""
    ethics_path = PROJECT_ROOT / "docs" / "03_ethics_note.md"
    assert ethics_path.is_file(), f"Ethics note missing at {ethics_path}"

    content = ethics_path.read_text(encoding="utf-8")
    assert MANDATORY_DISCLAIMER_PHRASE.lower() in content.lower()
    assert "synthetic data" in content.lower()
    assert "clinician sign-off required" in content.lower()


def test_ethics_note_covers_all_fourteen_topics():
    """Verify docs/03_ethics_note.md covers all 14 required ethical topics."""
    ethics_path = PROJECT_ROOT / "docs" / "03_ethics_note.md"
    content = ethics_path.read_text(encoding="utf-8").lower()

    required_topics = [
        "synthetic data only",
        "no real patient data",
        "decision-support only",
        "clinician sign-off required",
        "explainability",
        "resource-aware decision making",
        "language accessibility",
        "escalation safety",
        "registry freshness",
        "human override",
        "auditability",
        "bias evaluation",
        "limitations",
        "no autonomous diagnosis",
    ]

    for topic in required_topics:
        assert topic in content, f"Topic '{topic}' missing from docs/03_ethics_note.md"


def test_deployment_checklist_exists_and_contains_mandatory_disclaimer():
    """Verify docs/04_deployment_checklist.md exists and contains the required disclaimers."""
    checklist_path = PROJECT_ROOT / "docs" / "04_deployment_checklist.md"
    assert checklist_path.is_file(), f"Deployment checklist missing at {checklist_path}"

    content = checklist_path.read_text(encoding="utf-8")
    assert MANDATORY_DISCLAIMER_PHRASE.lower() in content.lower()
    assert "do not claim this is production-ready healthcare software" in content.lower()


def test_deployment_checklist_covers_all_categories_and_items():
    """Verify docs/04_deployment_checklist.md contains all 7 categories and their specific sub-items."""
    checklist_path = PROJECT_ROOT / "docs" / "04_deployment_checklist.md"
    content = checklist_path.read_text(encoding="utf-8").lower()

    # Category 1: DATA
    assert "synthetic data confirmed" in content
    assert "privacy" in content
    assert "access controls" in content

    # Category 2: CLINICAL
    assert "protocol approval" in content
    assert "clinician sign-off" in content
    assert "escalation policy" in content

    # Category 3: TECHNICAL
    assert "database backups" in content
    assert "logging" in content
    assert "monitoring" in content
    assert "authentication" in content
    assert "api" in content and "validation" in content
    assert "error handling" in content

    # Category 4: RESOURCE REGISTRY
    assert "registry" in content and "versioning" in content
    assert "freshness timestamp" in content
    assert "conflict" in content and "detection" in content

    # Category 5: LANGUAGE
    assert "translation validation" in content
    assert "interpreter availability" in content

    # Category 6: SAFETY
    assert "no feasible option escalation" in content
    assert "language mismatch escalation" in content
    assert "follow-up breach escalation" in content
    assert "fallback" in content and "owner" in content

    # Category 7: TESTING
    assert "unit tests" in content
    assert "edge-case" in content and "tests" in content
    assert "integration tests" in content
    assert "regression tests" in content
