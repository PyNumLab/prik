"""Import the BSPLINE-FORTRAN extension built by ``build_all.sh``."""

import importlib

import pytest


@pytest.fixture(scope="session")
def bspline_oo():
    """Return the object-oriented B-spline namespace."""
    return importlib.import_module("prik_bspline").bspline_oo_module


@pytest.fixture(scope="session")
def bspline_sub():
    """Return the procedural B-spline namespace."""
    return importlib.import_module("prik_bspline").bspline_sub_module
