"""Array declaration shapes and bounds as the Fortran parser records them."""

import pytest

from prik.parsers.fortran import parse_fortran_file
from tests.fortran._support.parser_procedures import collect_project_procedure_signatures


@pytest.mark.parametrize(
    ("declaration", "shape", "lower_bounds", "upper_bounds"),
    [
        pytest.param(
            "integer, intent(inout) :: x(0:,0:)",
            ["0:", "0:"],
            ["0", "0"],
            [None, None],
            id="assumed-shape-lower-bounds",
        ),
        pytest.param(
            "real, intent(inout), dimension(0:, 1:n) :: x",
            ["0:", "1:n"],
            ["0", "1"],
            [None, "n"],
            id="dimension-attribute-mixed-bounds",
        ),
        pytest.param("real, intent(inout) :: x(n)", ["n"], ["1"], ["n"], id="explicit-extent-default-lower-bound"),
    ],
)
def test_array_bounds_split_into_lower_and_upper(declaration, shape, lower_bounds, upper_bounds):
    signature = parse_fortran_file(f"subroutine s(x)\n  {declaration}\nend subroutine s\n").procedures[0]
    argument = signature.arguments[0]

    assert argument.rank == len(shape)
    assert argument.shape == shape
    assert argument.lower_bounds == lower_bounds
    assert argument.upper_bounds == upper_bounds


def test_parameter_expressions_in_shapes_are_kept_across_local_and_imported_parameters():
    files = {
        "kinds.f90": """
module k
  integer, parameter :: n = 8
end module k
""",
        "dims.f90": """
module dims_mod
  use k, only: n
  integer, parameter :: m = n + 2
contains
  subroutine use_expr(x, y)
    integer, intent(inout) :: x(0:m-1)
    real, intent(inout), dimension(1:m*2) :: y
  end subroutine use_expr
end module dims_mod
""",
    }
    signature = collect_project_procedure_signatures(files)[0]

    assert signature.arguments[0].shape == ["0:m-1"]
    assert signature.arguments[1].shape == ["1:m*2"]


def test_balanced_extent_expressions_are_preserved_for_every_declaration_owner():
    code = """
module declaration_owners
  integer, parameter :: n = 3
  real, target :: module_values(max(2, n))
  type :: record
    real :: values(product([n, 1]))
  end type record
contains
  function transform(source, output) result(values)
    real, intent(in) :: source(0:, 2:)
    real, intent(out) :: output(size(source, dim=2, kind=8))
    real :: values(lbound(source, 1):ubound(source, 1))
  end function transform
end module declaration_owners
"""
    module = parse_fortran_file(code).modules[0]
    procedure = module.procedures[0]

    assert module.variables[-1].shape == ["3"]
    assert module.derived_types[0].fields[0].shape == ["3"]
    assert procedure.arguments[0].shape == ["0:", "2:"]
    assert procedure.arguments[1].shape == ["size(source, dim=2, kind=8)"]
    assert procedure.result.shape == ["lbound(source, 1):ubound(source, 1)"]
