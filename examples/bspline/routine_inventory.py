"""Reviewed public BSPLINE-FORTRAN surface and its explicit test mapping."""

from __future__ import annotations

#: Object-oriented classes, most-derived first, over one abstract base.
CLASSES: tuple[str, ...] = (
    "bspline_1d",
    "bspline_2d",
    "bspline_3d",
    "bspline_4d",
    "bspline_5d",
    "bspline_6d",
)

ABSTRACT_BASE = "bspline_class"

#: Bindings the abstract base declares and every class answers.
DEFERRED_BINDINGS: tuple[str, ...] = ("destroy", "size_of")

#: Bindings the abstract base implements once for every extension.
INHERITED_BINDINGS: tuple[str, ...] = ("clear_flag", "status_message", "status_ok")

#: Public procedural routines, by dimension. The module keeps its knot,
#: interval, and band-solver helpers private, so they are not part of the
#: wrapped surface.
SUB_ROUTINE_GROUPS: dict[str, tuple[str, ...]] = {
    "Interpolation setup": ("db1ink", "db2ink", "db3ink", "db4ink", "db5ink", "db6ink"),
    "Evaluation": ("db1val", "db2val", "db3val", "db4val", "db5val", "db6val"),
    "Definite integrals": ("db1sqad", "db1fqad"),
    "Status reporting": ("get_status_message",),
}

ALL_SUB_ROUTINES = tuple(routine for group in SUB_ROUTINE_GROUPS.values() for routine in group)

#: Public spline-order constants copied into the module at import.
ORDER_CONSTANTS: dict[str, int] = {
    "bspline_order_linear": 2,
    "bspline_order_quadratic": 3,
    "bspline_order_cubic": 4,
    "bspline_order_quartic": 5,
    "bspline_order_quintic": 6,
    "bspline_order_hexic": 7,
    "bspline_order_heptic": 8,
    "bspline_order_octic": 9,
}

#: Upstream modules this example deliberately leaves out.
UNSUPPORTED: dict[str, str] = {
    "bspline_defc_module": "least-squares fitting; not required by the interpolation surface",
    "bspline_blas_module": "optional BLAS bridge used only by the least-squares module",
}
