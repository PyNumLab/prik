"""Reviewed public libm surface and its explicit test mapping."""

from __future__ import annotations

ROUTINE_GROUPS: dict[str, tuple[str, ...]] = {
    "Trigonometric": ("sin", "cos", "tan", "asin", "acos", "atan", "atan2"),
    "Hyperbolic": ("sinh", "cosh", "tanh", "asinh", "acosh", "atanh"),
    "Exponential and logarithmic": ("exp", "exp2", "expm1", "log", "log2", "log10", "log1p"),
    "Power and roots": ("pow", "sqrt", "cbrt", "hypot"),
    "Rounding, truncation, and remainder": (
        "ceil",
        "floor",
        "trunc",
        "round",
        "nearbyint",
        "rint",
        "lrint",
        "llrint",
        "lround",
        "llround",
        "fmod",
        "remainder",
    ),
    "Floating-point manipulation": (
        "copysign",
        "fabs",
        "fdim",
        "fmax",
        "fmin",
        "fma",
        "ldexp",
        "scalbn",
        "scalbln",
        "nextafter",
        "nexttoward",
        "logb",
        "ilogb",
    ),
    "Error and gamma functions": ("erf", "erfc", "tgamma", "lgamma"),
    "Single and extended precision": ("sinf", "cosf", "expf", "logf", "sqrtf", "sinl", "sqrtl"),
}

ALL_ROUTINES = tuple(routine for group in ROUTINE_GROUPS.values() for routine in group)
PRIK_TESTED_ROUTINES = frozenset(ALL_ROUTINES)
UNSUPPORTED_ROUTINES: dict[str, str] = {}
EXPLICIT_TEST_NAMES = {routine: f"test_{routine}" for routine in ALL_ROUTINES}
