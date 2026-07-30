"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

from tests.fortran._support.parser_procedures import (
    FortranUseMapping,
    FortranVariable,
    collect_project_procedure_signatures,
    collect_signature_shape_symbols,
    evaluate_signature_shapes,
    parse_fortran_file,
)


def test_compile_time_shape_eval_with_local_and_imported_params():
    files = {
        "kinds.f90": """
module k
  integer, parameter :: n = 8
end module k
""",
        "solver.f90": """
subroutine step(x)
  use k, only: n
  integer, parameter :: m = n + 2
  real, intent(inout) :: x(m*2)
end subroutine step
""",
    }
    sig = collect_project_procedure_signatures(files)[0]
    assert sig.arguments[0].shape == ["m*2"]


def test_assumed_shape_with_explicit_lower_bounds_is_preserved():
    code = """
subroutine fill_grid(x)
  integer, intent(inout) :: x(0:,0:)
end subroutine fill_grid
"""
    sig = parse_fortran_file(code).procedures[0]
    arg = sig.arguments[0]
    assert arg.base_type == "integer"
    assert arg.rank == 2
    assert arg.shape == ["0:", "0:"]


def test_dimension_attribute_with_mixed_bounds_is_parsed():
    code = """
subroutine update_plane(x)
  real, intent(inout), dimension(0:, 1:n) :: x
end subroutine update_plane
"""
    sig = parse_fortran_file(code).procedures[0]
    arg = sig.arguments[0]
    assert arg.rank == 2
    assert arg.shape == ["0:", "1:n"]
    assert arg.lower_bounds == ["0", "1"]
    assert arg.upper_bounds == [None, "n"]
    assert arg.lbound == ["0", "1"]
    assert arg.ubound == [None, "n"]
    assert arg.shape_info == [
        {"raw": "0:", "lower": "0", "upper": None},
        {"raw": "1:n", "lower": "1", "upper": "n"},
    ]


def test_shape_info_for_explicit_extent_dimension():
    code = """
subroutine resize(x)
  real, intent(inout) :: x(n)
end subroutine resize
"""
    sig = parse_fortran_file(code).procedures[0]
    arg = sig.arguments[0]
    assert arg.shape_info == [
        {"raw": "n", "lower": "1", "upper": "n"},
    ]
    assert arg.lower_bounds == ["1"]
    assert arg.upper_bounds == ["n"]
    assert arg.lbound == ["1"]
    assert arg.ubound == ["n"]


def test_structured_shape_handles_empty_dimensions_and_use_mapping_equality():
    from x2py.parsers.fortran.type_resolver import extract_kind_from_type_spec

    var = FortranVariable(name="empty", shape=[""])
    assert var.shape_info == [{"raw": "", "lower": None, "upper": None}]
    shape = var.structured_shape
    assert shape.raw == [""]
    assert shape.dimensions == [None]
    assert extract_kind_from_type_spec("real", "()") is None
    assert extract_kind_from_type_spec("real", "(len=5)") is None

    renamed = FortranUseMapping(source="delete_input_list", target="delete_input")
    assert renamed == "delete_input"
    assert renamed == FortranUseMapping(source="delete_input_list", target="delete_input")
    assert renamed != FortranUseMapping(source="delete_input_list")
    assert renamed != object()


def test_compile_time_parameter_expressions_are_evaluated_in_shapes():
    files = {
        "dims.f90": """
module dims_mod
  integer, parameter :: n0 = 4
  integer, parameter :: n1 = n0 + 2
contains
  subroutine use_expr(x, y)
    integer, intent(inout) :: x(0:n1-1)
    real, intent(inout), dimension(1:n0*2) :: y
  end subroutine use_expr
end module dims_mod
"""
    }
    sig = collect_project_procedure_signatures(files)[0]
    assert sig.arguments[0].shape == ["0:n1-1"]
    assert sig.arguments[1].shape == ["1:n0*2"]


def test_symbolic_shape_symbols_can_be_collected_and_later_evaluated():
    code = """
subroutine s(a)
  real, intent(inout) :: a(0:nx-1, 1:ny*2)
end subroutine s
"""
    sig = parse_fortran_file(code).procedures[0]
    assert collect_signature_shape_symbols(sig) == {"nx", "ny"}

    evaluated = evaluate_signature_shapes(sig, {"nx": 6, "ny": 4})
    assert evaluated.arguments[0].shape == ["0:6-1", "1:4*2"]
