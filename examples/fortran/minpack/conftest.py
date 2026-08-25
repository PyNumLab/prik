"""Import the MINPACK extension built by ``build_all.sh``."""

import importlib

import pytest


@pytest.fixture(scope="session")
def minpack():
    """Return the public MINPACK module namespace."""
    return importlib.import_module("prik_reference_minpack").minpack_module
