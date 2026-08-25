"""Import the FFTPACK extension built by ``build_all.sh``."""

import importlib

import pytest


@pytest.fixture(scope="session")
def fftpack():
    """Return the public high-level FFTPACK module namespace."""
    return importlib.import_module("prik_reference_fftpack").fftpack
