"""Reviewed public MINPACK surface and its explicit test mapping."""

from __future__ import annotations

ROUTINE_GROUPS: dict[str, tuple[str, ...]] = {
    "Diagnostics and finite differences": ("chkder", "enorm", "fdjac1", "fdjac2"),
    "Hybrid nonlinear solvers": ("hybrd", "hybrd1", "hybrj", "hybrj1"),
    "Levenberg-Marquardt solvers": ("lmder", "lmder1", "lmdif", "lmdif1", "lmstr", "lmstr1"),
    "Factorization and update helpers": ("dogleg", "lmpar", "qform", "qrfac", "qrsolv", "r1mpyq", "r1updt", "rwupdt"),
}

ALL_ROUTINES = tuple(routine for group in ROUTINE_GROUPS.values() for routine in group)
PRIK_TESTED_ROUTINES = frozenset(ALL_ROUTINES)
UNSUPPORTED_ROUTINES: dict[str, str] = {}
EXPLICIT_TEST_NAMES = {routine: f"test_{routine}" for routine in ALL_ROUTINES}
