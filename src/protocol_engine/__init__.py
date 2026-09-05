"""Protocol engine package for synthetic clinical protocol management and retrieval.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
from src.protocol_engine.models import (
    ProtocolDefinition,
    ProtocolLibrary,
    ProtocolLibraryMetadata,
    RecommendationLadder,
    RecommendationOption,
)
from src.protocol_engine.protocol_engine import (
    ProtocolEngine,
    get_protocol_engine,
)
from src.protocol_engine.protocol_loader import (
    ProtocolLoadError,
    load_protocol_library,
)

__all__ = [
    "ProtocolDefinition",
    "ProtocolEngine",
    "ProtocolLibrary",
    "ProtocolLibraryMetadata",
    "ProtocolLoadError",
    "RecommendationLadder",
    "RecommendationOption",
    "get_protocol_engine",
    "load_protocol_library",
]
