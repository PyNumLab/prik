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


# Native builds keep their outputs in their own directories. A compiler run from
# the repository root leaves modules or objects here instead, and a stale
# ``m.mod`` then silently shadows another source's module in later builds.
_ROOT_ARTIFACT_SUFFIXES = frozenset(
    {".mod", ".smod", ".o", ".obj", ".so", ".a", ".dylib", ".dll", ".pyd", ".lib", ".exe"}
)


def _root_build_artifacts() -> list[str]:
    """Return native build artifacts sitting directly in the repository root."""
    return sorted(
        path.name
        for path in ROOT.iterdir()
        if path.is_file() and (path.suffix.casefold() in _ROOT_ARTIFACT_SUFFIXES or path.name == "a.out")
    )


def pytest_sessionstart(session: pytest.Session) -> None:
    """Refuse to run over stale root build artifacts that later builds could pick up."""
    if hasattr(session.config, "workerinput"):
        return
    stale = _root_build_artifacts()
    if stale:
        raise pytest.UsageError(
            f"Remove native build artifacts from the repository root before testing: {', '.join(stale)}"
        )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail a session whose tests left native build artifacts in the repository root."""
    if hasattr(session.config, "workerinput"):
        return
    leaked = _root_build_artifacts()
    if leaked:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter is not None:
            reporter.write_line(
                f"ERROR: tests left native build artifacts in the repository root: {', '.join(leaked)}",
                red=True,
            )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


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
