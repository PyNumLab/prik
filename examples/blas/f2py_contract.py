"""Reviewed f2py intent additions for Reference BLAS comparison calls."""

from __future__ import annotations


F2PY_INOUT_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "srotg": ("a", "b", "c", "s"),
    "drotg": ("a", "b", "c", "s"),
    "crotg": ("a", "c", "s"),
    "zrotg": ("a", "c", "s"),
    "srotmg": ("sd1", "sd2", "sx1", "sparam"),
    "drotmg": ("dd1", "dd2", "dx1", "dparam"),
}
