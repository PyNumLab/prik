"""Pytest import setup for in-place repository runs."""

import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register repository-wide options before pytest parses its command line.

    The Fortran test hooks consume these options from ``tests/fortran``.  They
    must be registered here because nested conftests are discovered too late
    when pytest collects the complete repository suite.
    """
    group = parser.getgroup("prik Fortran")
    group.addoption(
        "--prik-fortran-compiler",
        action="store",
        default=os.environ.get("PRIK_TEST_FORTRAN_COMPILER", "gfortran"),
        metavar="EXECUTABLE",
        help="Fortran compiler executable used by compiled Fortran tests.",
    )
    group.addoption(
        "--require-toolchain-smoke",
        action="store_true",
        help="Require a nonempty, skip-free selection containing only toolchain smoke nodes.",
    )


try:
    from hypothesis import HealthCheck, settings
except ImportError:  # pragma: no cover - base test installs can omit QA extras.
    pass
else:
    settings.register_profile(
        "dev",
        max_examples=75,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    settings.register_profile(
        "ci",
        max_examples=250,
        deadline=None,
        derandomize=True,
        suppress_health_check=[HealthCheck.too_slow],
    )
    settings.register_profile(
        "fuzz",
        max_examples=1000,
        deadline=None,
        suppress_health_check=[
            HealthCheck.filter_too_much,
            HealthCheck.too_slow,
        ],
    )
    settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
