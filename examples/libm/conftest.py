"""Import fixture for the wrapper produced by ``build_all.sh``."""

import importlib

import pytest


@pytest.fixture(scope="session")
def libm():
    """Return the already-built PRIK libm module."""
    return importlib.import_module("prik_reference_libm")
