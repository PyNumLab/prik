"""Import fixtures for the wrappers produced by ``build_all.sh``."""

import importlib
import os
import sys

import pytest

from .routine_inventory import SCIPY_VERSION


@pytest.fixture(scope="session")
def prik_lapack():
    """Return the already-built PRIK LAPACK module."""
    old_flags = sys.getdlopenflags()
    sys.setdlopenflags(getattr(os, "RTLD_LAZY", old_flags) | getattr(os, "RTLD_GLOBAL", 0))
    try:
        return importlib.import_module("prik_reference_lapack_example")
    finally:
        sys.setdlopenflags(old_flags)


@pytest.fixture(scope="session")
def f2py_lapack():
    """Return the already-built f2py LAPACK module."""
    old_flags = sys.getdlopenflags()
    sys.setdlopenflags(getattr(os, "RTLD_LAZY", old_flags) | getattr(os, "RTLD_GLOBAL", 0))
    try:
        return importlib.import_module("f2py_reference_lapack_example")
    finally:
        sys.setdlopenflags(old_flags)


@pytest.fixture(scope="session")
def scipy_lapack():
    """Return the pinned SciPy low-level LAPACK module."""
    scipy = pytest.importorskip("scipy")
    if scipy.__version__ != SCIPY_VERSION:
        pytest.fail(f"expected SciPy {SCIPY_VERSION}, found {scipy.__version__}")
    return importlib.import_module("scipy.linalg.lapack")
