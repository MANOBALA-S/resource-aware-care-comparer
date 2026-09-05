"""Synthetic data generation package.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
from src.data_generation.case_generator import (
    DEFAULT_SEED,
    generate_and_save_cases,
    generate_synthetic_cases,
)

__all__ = [
    "DEFAULT_SEED",
    "generate_and_save_cases",
    "generate_synthetic_cases",
]
