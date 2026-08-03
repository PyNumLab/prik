"""Import fixtures for the wrappers produced by ``build_all.sh``."""

import importlib

import pytest


@pytest.fixture(scope="session")
def prik_blas():
    """Return the already-built PRIK BLAS module."""
    return importlib.import_module("prik_reference_blas")


@pytest.fixture(scope="session")
def f2py_blas():
    """Return the already-built f2py BLAS module."""
    return importlib.import_module("f2py_reference_blas")
