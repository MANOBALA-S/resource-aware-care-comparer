"""CLI script to deterministically generate exactly 40 synthetic patient cases.

No real patient data is used. All cases, service registries, protocols, and operational records are synthetic.
Decision-support prototype — clinician sign-off required.
"""
import sys
from collections import Counter
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_generation.case_generator import (
    DEFAULT_SEED,
    generate_and_save_cases,
    generate_synthetic_cases,
)


def main() -> None:
    """Generate exactly 40 synthetic patient cases and print distribution metrics."""
    seed = DEFAULT_SEED
    total_cases = 40

    cases = generate_synthetic_cases(total_cases=total_cases, seed=seed)
    output_path = generate_and_save_cases(total_cases=total_cases, seed=seed)

    # Calculate distributions
    languages = Counter(case.patient_language for case in cases)
    pop_groups = Counter(case.population_group.value for case in cases)
    urgencies = Counter(case.urgency.value for case in cases)
    conditions = Counter(case.condition for case in cases)
    sites = Counter(case.site_id for case in cases)
    age_bands = Counter(case.age_band for case in cases)

    print("=" * 70)
    print(" SYNTHETIC PATIENT CASE GENERATION COMPLETE")
    print("=" * 70)
    print(" NOTICE: Decision-support prototype — clinician sign-off required.")
    print(" DATA:   Synthetic data only — no real patient data.")
    print(f" FILE:   {output_path}")
    print(f" TOTAL:  {len(cases)} cases (Seed: {seed})")
    print("-" * 70)
    print(f" Languages:         {dict(languages)}")
    print(f" Population Groups: {dict(pop_groups)}")
    print(f" Urgency Tiers:     {dict(urgencies)}")
    print(f" Conditions:        {dict(conditions)}")
    print(f" Sites:             {dict(sites)}")
    print(f" Age Bands:         {dict(age_bands)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
