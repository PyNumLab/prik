"""Pytest configuration shipped with the copyable native-library examples."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register the repository's two example markers in a copied directory."""
    config.addinivalue_line("markers", "fortran_end_to_end: compiled and called Fortran example")
    config.addinivalue_line(
        "markers",
        "real_library: complete native-library example (BLAS, LAPACK, FFTPACK, MINPACK, BSPLINE-FORTRAN, or libm)",
    )
