"""Protocol loader for reading and validating synthetic clinical protocols.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import ValidationError

from src.config import PROJECT_ROOT
from src.protocol_engine.models import ProtocolDefinition, ProtocolLibrary

logger = logging.getLogger("care_comparer.protocol_loader")
DEFAULT_PROTOCOLS_PATH = PROJECT_ROOT / "data" / "protocols" / "protocols.json"


class ProtocolLoadError(Exception):
    """Raised when the protocol library file is unreadable, invalid JSON, or fails schema validation."""
    pass


def load_protocol_library(filepath: Optional[Path] = None) -> ProtocolLibrary:
    """Load and validate the synthetic protocol library from a JSON file.

    Args:
        filepath: Optional path to the protocols.json file. Defaults to data/protocols/protocols.json.

    Returns:
        Validated ProtocolLibrary object containing all protocol definitions.

    Raises:
        ProtocolLoadError: If file is missing, invalid JSON, or violates schema constraints.
    """
    target_path = filepath or DEFAULT_PROTOCOLS_PATH

    if not target_path.is_file():
        raise ProtocolLoadError(f"Protocols file not found at: {target_path}")

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ProtocolLoadError(f"Failed to parse protocols JSON at {target_path}: {exc}") from exc
    except Exception as exc:
        raise ProtocolLoadError(f"Unexpected error reading {target_path}: {exc}") from exc

    try:
        library = ProtocolLibrary.model_validate(raw_data)
    except ValidationError as exc:
        raise ProtocolLoadError(f"Protocol validation failed against schema: {exc}") from exc

    # Ensure uniqueness of protocol IDs and conditions
    seen_ids: Dict[str, str] = {}
    seen_conditions: Dict[str, str] = {}

    for proto in library.protocols:
        if proto.protocol_id in seen_ids:
            raise ProtocolLoadError(
                f"Duplicate protocol_id detected: '{proto.protocol_id}' in condition '{proto.condition}'"
            )
        seen_ids[proto.protocol_id] = proto.condition

        if proto.condition in seen_conditions:
            raise ProtocolLoadError(
                f"Duplicate condition detected: '{proto.condition}' in protocol '{proto.protocol_id}'"
            )
        seen_conditions[proto.condition] = proto.protocol_id

    logger.info("Successfully loaded %d synthetic protocols from %s", len(library.protocols), target_path)
    return library
