"""Protocol Engine providing lookup, validation, and ladder retrieval for clinical conditions.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from functools import lru_cache
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.protocol_engine.models import (
    ProtocolDefinition,
    ProtocolLibrary,
    RecommendationLadder,
)
from src.protocol_engine.protocol_loader import load_protocol_library

logger = logging.getLogger("care_comparer.protocol_engine")


class ProtocolEngine:
    """Core engine for retrieving and querying synthetic clinical protocols."""

    def __init__(
        self,
        library: Optional[ProtocolLibrary] = None,
        protocols_path: Optional[Path] = None,
    ) -> None:
        """Initialize protocol engine from an existing library or from disk.

        Args:
            library: Pre-loaded ProtocolLibrary instance.
            protocols_path: Optional path to JSON file if loading from disk.
        """
        if library is not None:
            self._library = library
        else:
            self._library = load_protocol_library(protocols_path)

        self._condition_index: Dict[str, ProtocolDefinition] = {}
        self._id_index: Dict[str, ProtocolDefinition] = {}
        self._index_protocols()

    def _index_protocols(self) -> None:
        """Build fast lookup indices for condition codes and protocol IDs."""
        self._condition_index.clear()
        self._id_index.clear()
        for proto in self._library.protocols:
            cond_key = proto.condition.strip().lower()
            self._condition_index[cond_key] = proto
            self._id_index[proto.protocol_id.strip().upper()] = proto

    def get_protocol(self, condition: str) -> Optional[ProtocolDefinition]:
        """Lookup a protocol definition by condition code.

        Args:
            condition: Condition identifier, e.g. 'condition_alpha' (case-insensitive).

        Returns:
            ProtocolDefinition if found, or None.
        """
        if not condition:
            return None
        return self._condition_index.get(condition.strip().lower())

    def get_protocol_by_id(self, protocol_id: str) -> Optional[ProtocolDefinition]:
        """Lookup a protocol definition by protocol ID.

        Args:
            protocol_id: Protocol identifier, e.g. 'PROTO-001' (case-insensitive).

        Returns:
            ProtocolDefinition if found, or None.
        """
        if not protocol_id:
            return None
        return self._id_index.get(protocol_id.strip().upper())

    def get_recommendation_ladder(self, condition: str) -> Optional[RecommendationLadder]:
        """Retrieve the 4-tier recommendation ladder for a given condition.

        Args:
            condition: Condition identifier, e.g. 'condition_alpha'.

        Returns:
            RecommendationLadder with preferred, alternative, fallback, and escalate tiers, or None.
        """
        protocol = self.get_protocol(condition)
        if protocol is None:
            return None
        return protocol.recommendation_ladder

    def list_supported_conditions(self) -> List[str]:
        """Return a sorted list of all supported condition identifiers."""
        return sorted(list(self._condition_index.keys()))

    def list_protocols(self) -> List[ProtocolDefinition]:
        """Return all loaded protocol definitions."""
        return list(self._library.protocols)

    def validate_protocols(self) -> bool:
        """Perform deep structural and semantic verification on loaded protocols.

        Returns:
            True if all protocols are structurally valid and complete.

        Raises:
            ValueError: If an inconsistency or missing mandatory field is found.
        """
        if not self._library.protocols:
            raise ValueError("Protocol library contains no protocols.")

        for proto in self._library.protocols:
            ladder = proto.recommendation_ladder
            if not ladder.preferred or not ladder.preferred.option:
                raise ValueError(f"Protocol {proto.protocol_id} missing preferred option.")
            if not ladder.resource_adapted_alternative or not ladder.resource_adapted_alternative.option:
                raise ValueError(f"Protocol {proto.protocol_id} missing resource-adapted alternative.")
            if not ladder.minimum_safe_fallback or not ladder.minimum_safe_fallback.option:
                raise ValueError(f"Protocol {proto.protocol_id} missing minimum safe fallback.")
            if not ladder.escalate_only or not ladder.escalate_only.option:
                raise ValueError(f"Protocol {proto.protocol_id} missing escalate-only option.")
            if not proto.textbook_recommendation:
                raise ValueError(f"Protocol {proto.protocol_id} missing textbook recommendation.")

        return True


@lru_cache()
def get_protocol_engine(protocols_path: Optional[str] = None) -> ProtocolEngine:
    """Cached singleton provider for the default ProtocolEngine."""
    path = Path(protocols_path) if protocols_path else None
    return ProtocolEngine(protocols_path=path)
