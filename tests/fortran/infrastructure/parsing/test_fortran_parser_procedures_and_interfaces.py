"""Procedure headers, dummy procedures, source forms, and program units."""

import pytest

from prik.parsers.fortran import parse_fortran_file
from prik.parsers.fortran.models import FortranFunctionCall, FortranSlice
from prik.parsers.fortran.scope import ScopeUses


def test_fixed_form_and_interface_detection():
    code = """
      subroutine saxpy(n,x,y)
      integer, intent(in) :: n
      real, dimension(n), intent(in) :: x
      real, dimension(n), intent(inout) :: y
      end
      interface
        subroutine cb(i)
          integer, intent(in) :: i
        end subroutine cb
      end interface
"""
    for filename, source_form in (("legacy.f", "fixed"), ("legacy.f77", "fixed"), ("legacy.f90", "free")):
        parsed = parse_fortran_file(code, filename=filename)
        assert parsed.format == source_form
        assert [procedure.name for procedure in parsed.procedures] == ["saxpy"]
        assert parsed.procedures[0].arguments[1].shape == ["n"]
        assert len(parsed.interfaces) == 1
        assert parsed.interfaces[0].procedures[0].in_interface is True


@pytest.mark.parametrize(
    ("declarations", "expected"),
    [
        pytest.param("  implicit none\n  external :: arg\n", ("procedure", ""), id="external-statement-only"),
        pytest.param("  implicit none\n  external arg\n  real arg\n", ("real", ""), id="external-then-type"),
        pytest.param("  implicit none\n  real, external :: arg\n", ("real", ""), id="typed-external-attribute"),
        pytest.param("  implicit none\n  real :: arg\n  external :: arg\n", ("real", ""), id="type-then-external"),
        pytest.param("  procedure(local_cb) :: arg\n", ("procedure", "local_cb"), id="procedure-interface"),
        pytest.param(
            "  procedure(callback_iface), external :: arg\n",
            ("procedure", "callback_iface"),
            id="procedure-interface-external",
        ),
        pytest.param(
            "  import :: ext_cb\n  procedure(ext_cb) :: arg\n",
            ("procedure", ""),
            id="imported-interface-stays-unresolved",
        ),
    ],
)
def test_dummy_procedure_declarations_record_type_and_interface(declarations, expected):
    """EXTERNAL and PROCEDURE() declarations in either order never conflict with a type."""
    sig = parse_fortran_file(f"subroutine caller(arg)\n{declarations}end subroutine caller\n").procedures[0]

    assert [(arg.name, arg.base_type, arg.kind) for arg in sig.arguments] == [("arg", *expected)]


def test_procedure_prefixes_result_keyword_variants_and_local_use():
    code = """
recursive function fact(n) results(res)
  integer, intent(in) :: n
  integer :: res
end function fact

pure subroutine axpy(a, x)
  use iso_c_binding, only: c_double
  real(kind=c_double), intent(in) :: a
  real(kind=c_double), intent(in), dimension(:) :: x
end subroutine axpy
"""
    fact, axpy = parse_fortran_file(code).procedures
    assert "recursive" in fact.attributes
    assert fact.result is not None
    assert fact.result.name == "res"
    assert "pure" in axpy.attributes
    assert list(ScopeUses(axpy.uses).mappings("iso_c_binding")) == ["c_double"]
    assert [(arg.base_type, arg.shape) for arg in axpy.arguments] == [("real", []), ("real", [":"])]


def test_structured_shape_preserves_slices_and_function_calls():
    code = """
subroutine derived_shape(src, x, y)
  real, intent(in) :: src(:,:)
  real, intent(inout), dimension(0:size(src, 1)-1, lbound(src, 2):ubound(src, 2)) :: x
  real, intent(inout) :: y(1:n:2)
end subroutine derived_shape
"""
    sig = parse_fortran_file(code).procedures[0]
    args = {arg.name: arg for arg in sig.arguments}

    assert args["x"].shape == ["0:size(src, 1)-1", "lbound(src, 2):ubound(src, 2)"]
    shape = args["x"].structured_shape
    assert shape.raw == args["x"].shape
    assert isinstance(shape.dimensions[0], FortranSlice)
    assert shape.dimensions[0].lower == "0"
    assert shape.dimensions[0].upper == "size(src, 1)-1"
    assert isinstance(shape.dimensions[1], FortranSlice)
    assert isinstance(shape.dimensions[1].lower, FortranFunctionCall)
    assert shape.dimensions[1].lower.name == "lbound"
    assert shape.dimensions[1].lower.arguments == ["src", "2"]
    assert isinstance(shape.dimensions[1].upper, FortranFunctionCall)
    assert shape.dimensions[1].upper.name == "ubound"

    y_dim = args["y"].structured_shape.dimensions[0]
    assert isinstance(y_dim, FortranSlice)
    assert (y_dim.lower, y_dim.upper, y_dim.stride) == ("1", "n", "2")


def test_submodule_module_procedure_stub_and_additional_program_units():
    code = """
submodule (ancestor_mod:parent_impl) child_impl
  use iso_c_binding, only: c_int
  integer(kind=c_int) :: counter
contains
  module procedure reset_counter
  end procedure reset_counter
end submodule child_impl

program driver
  use ancestor_mod
  integer :: ierr
end program driver

block data init_data
  integer :: seed
end block data init_data
"""
    parsed = parse_fortran_file(code)
    (submodule,) = parsed.submodules
    assert submodule.parent == "parent_impl"
    assert submodule.ancestor == "ancestor_mod"
    assert list(ScopeUses(submodule.uses).mappings("iso_c_binding")) == ["c_int"]
    assert [v.name for v in submodule.variables] == ["counter"]
    assert [(p.name, p.kind) for p in submodule.procedures] == [("reset_counter", "module procedure")]

    (program,) = parsed.programs
    assert program.name == "driver"
    assert ScopeUses(program.uses).imports_all("ancestor_mod") is True
    assert [v.name for v in program.variables] == ["ierr"]

    (block_data,) = parsed.block_data_units
    assert block_data.name == "init_data"
    assert [v.name for v in block_data.variables] == ["seed"]
