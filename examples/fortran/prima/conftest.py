"""Import the PRIMA extension built by ``build_all.sh``."""

import importlib

import pytest


@pytest.fixture(scope="session")
def prima():
    """Return the extension containing PRIMA's five public solver modules."""
    return importlib.import_module("prik_prima")
