"""An argument sized by a specification function is checked before anything else runs."""

from __future__ import annotations

from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.printer_models import generate_wrapper, rendered_source

CONTRACT = """
from prik.contracts import Addr, Annotated, Arg, COPY_F, Float64, Int32, ORDER_C, native_call, pure

@pure
@native_call([Addr(Arg(0))])
def extent_for(n: Int32) -> Int32: ...

@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def scaled(
    n: Int32,
    values: Float64[extent_for(n)],
    grid: Annotated[Float64[n, n], ORDER_C, COPY_F],
) -> Float64[extent_for(n)]: ...
"""


def _sources() -> tuple[str, str]:
    artifacts = generate_wrapper(parse_pyi_text(CONTRACT, module_name="extents"))
    return rendered_source(artifacts, ".f90"), rendered_source(artifacts, ".c")


def test_a_mismatched_actual_leaves_the_bridge_nothing_prepared_called_or_produced():
    """Only the declared extent is evaluated before the check; a mismatch yields a null result.

    Guarding the native call alone still converted the actuals, allocated the
    result, and copied storage the call never wrote into it.
    """
    bridge, _binding = _sources()
    body = bridge[bridge.index("function bind_c_scaled(") : bridge.index("end function bind_c_scaled")]
    statements = [
        line.strip()
        for line in body.splitlines()
        if line.strip() and "::" not in line and "&" not in line and "bind(c" not in line
    ]

    assert statements[0].startswith("values_declared_extent_0 = int(")
    assert statements[1] == "if (values_declared_extent_0 == values_extent_0) then"
    # Everything that prepares, calls, or produces sits inside that branch.
    assert statements[-3:] == ["else", "result = c_null_ptr", "end if"]


def test_the_binding_rejects_before_any_other_post_call_step():
    """The rejection is the first thing after the call, holding nothing the call produced.

    `grid` is copied through a Fortran-order temporary, whose copy-back is a
    post-call step; a rejected call must not reach it.
    """
    _bridge, binding = _sources()
    after_call = binding[binding.index("= bind_c_scaled(") :].splitlines()[1:]
    checks = [line.strip() for line in after_call if line.strip().startswith("if (")]

    assert checks[0] == "if (values_declared_extent_0 != bound_values_extent_0) {"
