"""Modules a Fortran processor supplies without a source file.

Source discovery and semantic resolution both ask whether a ``use`` stating
no nature names a processor module, and they must give the same answer, so
the inventory lives here once.
"""

from __future__ import annotations

#: The standard intrinsic modules, and processor modules the common Fortran
#: toolchains supply for OpenMP and OpenACC. A ``use`` stating no nature names
#: one of these only when no parsed module of that name is accessible.
INTRINSIC_FORTRAN_MODULES = frozenset(
    {
        "iso_c_binding",
        "iso_fortran_env",
        "ieee_arithmetic",
        "ieee_exceptions",
        "ieee_features",
        "omp_lib",
        "omp_lib_kinds",
        "openacc",
    }
)
