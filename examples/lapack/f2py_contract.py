"""Reviewed f2py intent additions for Reference LAPACK comparison calls."""

from __future__ import annotations


F2PY_INOUT_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "dlarfg": ("alpha", "tau"),
    "dlartg": ("c", "s", "r"),
    "dgbcon": ("rcond", "info"),
    "dgecon": ("rcond", "info"),
    "dgtcon": ("rcond", "info"),
    "dpocon": ("rcond", "info"),
    "dppcon": ("rcond", "info"),
    "dsycon": ("rcond", "info"),
    "dtrcon": ("rcond", "info"),
}
