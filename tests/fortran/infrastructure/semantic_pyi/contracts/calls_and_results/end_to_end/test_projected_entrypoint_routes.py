"""Compiled binding-owned projection sequences for direct and adapted targets."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_inline_pyi_contract_module

pytestmark = pytest.mark.fortran_end_to_end


def _projection_source(module_name: str, *, bind_c: bool) -> str:
    binding = ' bind(C, name="projected_native")' if bind_c else ""
    output_binding = ' bind(C, name="projected_output_native")' if bind_c else ""
    return f"""
module {module_name}
  use iso_c_binding
contains
  integer(c_int) function projected(right, left, bias){binding} result(output)
    integer(c_int), value, intent(in) :: right
    integer(c_int), intent(in) :: left
    integer(c_int), value, intent(in) :: bias
    output = 100_c_int * right + 10_c_int * left + bias
  end function projected

  subroutine projected_output(right, left, bias, output){output_binding}
    integer(c_int), value, intent(in) :: right
    integer(c_int), intent(in) :: left
    integer(c_int), value, intent(in) :: bias
    integer(c_int), intent(out) :: output
    output = 100_c_int * right + 10_c_int * left + bias
  end subroutine projected_output
end module {module_name}
"""


def _projection_contract(*, direct: bool) -> str:
    marker = '@native_abi("c")\n' if direct else ""
    native_name = "projected_native" if direct else "projected"
    output_native_name = "projected_output_native" if direct else "projected_output"
    return f"""
from prik.contracts import Addr, Arg, Int32, Return, Value, bind, native_abi, native_call

{marker}@bind("{native_name}")
@native_call([Value(Arg(1)), Addr(Arg(0)), Int32(5)])
def projected(left: Int32, right: Int32) -> Int32: ...

{marker}@bind("{output_native_name}")
@native_call([Value(Arg(1)), Addr(Arg(0)), Int32(5), Return("output", 0)])
def projected_output(left: Int32, right: Int32) -> Int32: ...
"""


def test_direct_projection_reorders_value_and_address_actuals_and_materializes_literal(tmp_path: Path):
    module, result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="direct_projection_runtime",
        source_text=_projection_source("direct_projection_runtime", bind_c=True),
        contract_text=_projection_contract(direct=True),
    )

    assert module.projected(np.int32(2), np.int32(3)) == np.int32(325)
    assert module.projected_output(np.int32(2), np.int32(3)) == np.int32(325)
    assert {path.name for path in result.generated_sources} == {
        "direct_projection_runtime_wrapper.c",
        "direct_projection_runtime_wrapper.h",
    }
    binding = (result.output_dir / "direct_projection_runtime_wrapper.c").read_text(encoding="utf-8")
    assert "int32_t projected_native(int32_t right, int32_t * left, int32_t literal_2);" in binding
    assert "result = projected_native(bound_right, &bound_left, 5);" in binding
    assert (
        "void projected_output_native(int32_t right, int32_t * left, int32_t literal_2, int32_t * output);" in binding
    )
    assert "projected_output_native(bound_right, &bound_left, 5, &output);" in binding


def test_adapted_projection_uses_the_same_binding_owned_actual_sequence(tmp_path: Path):
    module, result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="adapted_projection_runtime",
        source_text=_projection_source("adapted_projection_runtime", bind_c=False),
        contract_text=_projection_contract(direct=False),
    )

    assert module.projected(np.int32(2), np.int32(3)) == np.int32(325)
    assert module.projected_output(np.int32(2), np.int32(3)) == np.int32(325)
    assert {path.name for path in result.generated_sources} == {
        "adapted_projection_runtime_wrapper.c",
        "adapted_projection_runtime_wrapper.h",
        "bind_c_adapted_projection_runtime_wrapper.f90",
    }
    binding = (result.output_dir / "adapted_projection_runtime_wrapper.c").read_text(encoding="utf-8")
    bridge = (result.output_dir / "bind_c_adapted_projection_runtime_wrapper.f90").read_text(encoding="utf-8")
    assert "bind_c_projected(bound_right, &bound_left, 5)" in binding
    assert "bind_c_projected_output(bound_right, &bound_left, 5, &output)" in binding
    assert "function bind_c_projected(right, left, literal_2)" in bridge
    assert "native_projected(right, left, literal_2)" in bridge
    assert "subroutine bind_c_projected_output(right, left, literal_2, output)" in bridge
    assert "native_projected_output(right, left, literal_2, output)" in bridge


def test_matching_fortran_contract_name_uses_the_native_procedure_without_bind(tmp_path: Path):
    """A Fortran contract needs ``@bind`` only when the names differ."""
    module, result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="matching_fortran_name",
        source_text="""
module matching_fortran_name
contains
  subroutine increment(value)
    integer, intent(inout) :: value
    value = value + 1
  end subroutine increment
end module matching_fortran_name
""",
        contract_text="""
from prik.contracts import Addr, Arg, Int32, Returns, native_call

@native_call([Addr(Arg(0))])
def increment(value: Int32) -> Returns[\"value\", Int32]: ...
""",
    )

    assert module.increment(np.int32(4)) == np.int32(5)
    bridge = (result.output_dir / "bind_c_matching_fortran_name_wrapper.f90").read_text(encoding="utf-8")
    assert "call native_increment(value)" in bridge
