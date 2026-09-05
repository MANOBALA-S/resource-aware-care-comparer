"""Test runner script for Resource-Aware Care Option Comparer.

Synthetic data only — no real patient data.
Decision-support prototype — clinician sign-off required.
"""
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    """Run pytest suite with verbose reporting."""
    tests_dir = PROJECT_ROOT / "tests"
    args = [str(tests_dir), "-v", "--durations=5"] + sys.argv[1:]
    sys.exit(pytest.main(args))


if __name__ == "__main__":
    main()
