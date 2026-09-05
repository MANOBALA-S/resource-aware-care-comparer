"""Tests for synthetic protocol library loading, validation, and protocol engine lookups.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from pathlib import Path
import pytest

from src.protocol_engine.models import ProtocolDefinition, RecommendationLadder
from src.protocol_engine.protocol_engine import ProtocolEngine, get_protocol_engine
from src.protocol_engine.protocol_loader import ProtocolLoadError, load_protocol_library


def test_protocol_library_loading() -> None:
    """Verify loading the approved synthetic protocol library loads at least 5 protocols."""
    library = load_protocol_library()
    assert len(library.protocols) >= 5
    assert "synthetic" in library.metadata.synthetic_data_notice.lower()


def test_valid_condition_lookup() -> None:
    """Verify lookup for all five synthetic conditions produces valid ProtocolDefinitions."""
    engine = get_protocol_engine()
    expected_conditions = [
        "condition_alpha",
        "condition_beta",
        "condition_gamma",
        "condition_delta",
        "condition_epsilon",
    ]

    for cond in expected_conditions:
        protocol = engine.get_protocol(cond)
        assert protocol is not None
        assert isinstance(protocol, ProtocolDefinition)
        assert protocol.condition == cond
        assert protocol.protocol_id.startswith("PROTO-")
        assert len(protocol.textbook_recommendation) > 0
        assert len(protocol.required_resources) > 0


def test_case_insensitive_condition_lookup() -> None:
    """Verify that condition lookup is case-insensitive and trims whitespace."""
    engine = get_protocol_engine()
    proto_lower = engine.get_protocol("condition_alpha")
    proto_upper = engine.get_protocol("CONDITION_ALPHA")
    proto_spaced = engine.get_protocol("  condition_alpha  ")

    assert proto_lower is not None
    assert proto_upper is not None
    assert proto_spaced is not None
    assert proto_lower.protocol_id == proto_upper.protocol_id == proto_spaced.protocol_id


def test_protocol_lookup_by_id() -> None:
    """Verify protocol lookup by protocol_id."""
    engine = get_protocol_engine()
    proto = engine.get_protocol_by_id("PROTO-001")
    assert proto is not None
    assert proto.condition == "condition_alpha"

    # Lookup non-existent ID
    assert engine.get_protocol_by_id("PROTO-999") is None
    assert engine.get_protocol_by_id("") is None


def test_invalid_condition_handling() -> None:
    """Verify that invalid, unknown, or empty conditions return None without raising exceptions."""
    engine = get_protocol_engine()
    assert engine.get_protocol("condition_zeta") is None
    assert engine.get_protocol("unknown_disease") is None
    assert engine.get_protocol("") is None


def test_recommendation_ladder_retrieval() -> None:
    """Verify 4-tier recommendation ladder structure for condition_alpha."""
    engine = get_protocol_engine()
    ladder = engine.get_recommendation_ladder("condition_alpha")
    assert ladder is not None
    assert isinstance(ladder, RecommendationLadder)

    # 1. Preferred
    assert ladder.preferred.option is not None
    assert len(ladder.preferred.required_resources) > 0
    assert len(ladder.preferred.rationale) > 0

    # 2. Resource Adapted Alternative
    assert ladder.resource_adapted_alternative.option is not None
    assert len(ladder.resource_adapted_alternative.rationale) > 0

    # 3. Minimum Safe Fallback
    assert ladder.minimum_safe_fallback.option is not None
    assert len(ladder.minimum_safe_fallback.rationale) > 0

    # 4. Escalate Only
    assert ladder.escalate_only.option is not None
    assert len(ladder.escalate_only.rationale) > 0


def test_recommendation_ladder_invalid_condition() -> None:
    """Verify recommendation ladder retrieval for an invalid condition returns None."""
    engine = get_protocol_engine()
    assert engine.get_recommendation_ladder("invalid_condition") is None


def test_validate_protocols() -> None:
    """Verify structural and semantic integrity verification of all loaded protocols."""
    engine = get_protocol_engine()
    assert engine.validate_protocols() is True


def test_missing_protocols_file_raises_error(tmp_path: Path) -> None:
    """Verify attempting to load protocols from a non-existent file raises ProtocolLoadError."""
    fake_path = tmp_path / "nonexistent_protocols.json"
    with pytest.raises(ProtocolLoadError) as exc_info:
        load_protocol_library(fake_path)
    assert "not found" in str(exc_info.value).lower()


def test_invalid_json_protocols_raises_error(tmp_path: Path) -> None:
    """Verify malformed JSON raises ProtocolLoadError."""
    corrupt_file = tmp_path / "corrupt_protocols.json"
    corrupt_file.write_text("{ unclosed json", encoding="utf-8")

    with pytest.raises(ProtocolLoadError) as exc_info:
        load_protocol_library(corrupt_file)
    assert "failed to parse" in str(exc_info.value).lower()
