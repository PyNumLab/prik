"""Fortran declarations emit their `.pyi` spelling, and that contract reloads unchanged."""

from pathlib import Path

import pytest
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source
from prik.policy.contract_imports import complete_contract_imports
from prik.policy.exports import complete_python_export_policy
from prik.printers import emit_module
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from tests.fortran._support.printer_models import parse_pyi_text

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

SCALAR_ARGUMENTS_AND_RESULTS = """
module scalars
contains
subroutine add(a, b, c)
    real(8), intent(in) :: a
    real(8), intent(in) :: b
    real(8), intent(out) :: c
end subroutine
subroutine ping()
end subroutine
function norm2(x) result(r)
    real(8), intent(in) :: x(:)
    real(8) :: r
end function
subroutine solve(tol)
    real(8), intent(in), optional :: tol
end subroutine
subroutine maybe_status(status)
    integer(4), intent(out), optional :: status
end subroutine maybe_status
subroutine normalize(name)
    character(len=8), intent(inout) :: name
end subroutine
subroutine scale_in_place(value, factor)
    real(8), intent(inout) :: value
    real(8), intent(in) :: factor
end subroutine scale_in_place
end module
"""

ARRAY_SHAPES = """
module arrays
contains
subroutine matvec(A, x, y)
    real(8), intent(in) :: A(:, :)
    real(8), intent(in) :: x(:)
    real(8), intent(out) :: y(:)
end subroutine
subroutine scale(x)
    real(8), intent(inout) :: x(:)
end subroutine
subroutine explicit(n, fixed, default_bound, zero_bound, shifted_bound)
  integer, intent(in) :: n
  real(8), intent(in) :: fixed(10, 20)
  real(8), intent(inout) :: default_bound(1:n)
  real(8), intent(inout) :: zero_bound(0:n-1)
  real(8), intent(inout) :: shifted_bound(2:n+1)
end subroutine explicit
subroutine assumed_size(ldb, columns, flat, bounded)
  integer, intent(in) :: ldb
  real(8), intent(inout) :: columns(3, *)
  real(8), intent(inout) :: flat(0:*)
  real(8), intent(inout) :: bounded(0:ldb-1, 0:*)
end subroutine assumed_size
subroutine use_labels(labels)
  character(len=4), intent(in) :: labels(:)
end subroutine use_labels
subroutine replace_names(names)
  character(len=:), allocatable, intent(inout) :: names(:)
end subroutine replace_names
end module
"""

PARAMETERS_AND_VALUE_DUMMIES = """
module value_contract
  real, parameter :: c = cos(0.0)
  integer, parameter :: n = 3 + 4
  type :: item
    real(8) :: x
  end type item
contains
  function score(value) result(total)
    type(item), value :: value
    real(8) :: total
    total = value%x
  end function score
end module value_contract
"""

DERIVED_TYPES_AND_METHODS = """
module shapes
  type :: base_matrix
  end type
  type, extends(base_matrix) :: sparse_matrix
    integer :: nrows
  end type
  type :: state
    integer :: id = 7
    real(8) :: scale = 2.5
    logical :: enabled = .true.
  end type state
  type :: vector
    real(8), allocatable :: values(:)
  contains
    procedure :: scale
    procedure, pass(owner) :: shift => shift_vector
    procedure, nopass :: make => make_vector
  end type vector
  type(vector), target :: current
  type(state) :: snapshot
contains
  subroutine scale(self, alpha)
    class(vector), intent(inout) :: self
    real(8), intent(in) :: alpha
  end subroutine scale
  subroutine shift_vector(dx, owner, dy)
    real(8), intent(in) :: dx
    class(vector), intent(inout) :: owner
    real(8), intent(in) :: dy
  end subroutine shift_vector
  function make_vector(value) result(created)
    real(8), intent(in) :: value
    type(vector) :: created
  end function make_vector
end module shapes
"""

DEFAULT_PRIVATE_MODULE = """
module state_mod
  implicit none
  private
  public :: counter
  integer, parameter :: answer = 42
  integer :: counter
  real(8) :: hidden_scale
contains
  subroutine ping(x)
    integer, intent(in) :: x
  end subroutine
end module
"""


def _fixture(name: str) -> str:
    return (NATIVE_FIXTURES / name).read_text(encoding="utf-8")


DECLARATION_CASES = {
    "scalar-arguments-and-results": (
        SCALAR_ARGUMENTS_AND_RESULTS,
        [
            "@native_call([Addr(Arg(0)), Addr(Arg(1)), Return('c', 0)])\n"
            "def add(\n    a: Float64,\n    b: Float64\n) -> Float64: ...",
            "def ping() -> None: ...",
            "def norm2(\n    x: Float64[::]\n) -> Float64: ...",
            "tol: Float64 = ...",
            'status: Int32[()] = ...\n) -> Returns["status", Int32[()]] | None: ...',
            'def normalize(\n    name: String[8]\n) -> Returns["name", String[8]]: ...',
            "@native_call([Addr(Arg(0)), Addr(Arg(1))])\ndef scale_in_place(\n"
            '    value: Float64,\n    factor: Float64\n) -> Returns["value", Float64]: ...',
        ],
        ['Returns["c"', "c: Addr(Float64)", "Return('status'"],
    ),
    "array-shapes": (
        ARRAY_SHAPES,
        [
            "def matvec(\n    A: Float64[::, ::],\n    x: Float64[::],\n    y: Float64[::]\n) -> None: ...",
            "def scale(\n    x: Float64[::]\n) -> None: ...",
            "fixed: Float64[10, 20]",
            "default_bound: Float64[n]",
            "zero_bound: Float64[n]",
            "shifted_bound: Float64[n]",
            "columns: Float64[3, Flat]",
            "flat: Float64[Flat]",
            "bounded: Float64[ldb, Flat]",
            "labels: String[4][::]",
            "names: Allocatable[String[:][:]]",
        ],
        ["Shape", "Annotated[Float64"],
    ),
    "parameters-and-value-dummies": (
        PARAMETERS_AND_VALUE_DUMMIES,
        [
            "c: Final[Float32]\n",
            "n: Final[Int32] = 7",
            "@native_call([Value(Arg(0))])\ndef score(\n    value: item\n) -> Float64: ...",
        ],
        ["cos(0.0)"],
    ),
    "derived-types-and-methods": (
        DERIVED_TYPES_AND_METHODS,
        [
            "class sparse_matrix(base_matrix):",
            "class state:\n    def __init__(\n        self,\n        *,\n        id: Int32 = 7,\n"
            "        scale: Float64 = 2.5,\n        enabled: Bool = True\n    ) -> None: ...\n\n"
            "    id: Int32[()] = 7\n    scale: Float64[()] = 2.5\n    enabled: Bool[()] = True\n",
            "    values: Allocatable[Float64[:]]",
            "    @native_call([Pass(), Addr(Arg(0))])\n    def scale(\n        self,\n        alpha: Float64\n"
            "    ) -> None: ...",
            '    @bind("shift_vector")\n    @native_call([Addr(Arg(0)), Pass(), Addr(Arg(1))])\n    def shift(\n'
            "        self,\n        dx: Float64,\n        dy: Float64\n    ) -> None: ...",
            '    @staticmethod\n    @bind("make_vector")',
            "owner: Annotated[vector, Polymorphic]",
            "current: Annotated[vector, Aliased]",
            "snapshot: state\n",
        ],
        ["        self: vector", "owner: Addr(vector)"],
    ),
    "default-private-module": (
        DEFAULT_PRIVATE_MODULE,
        ["counter: Int32"],
        ["answer", "hidden_scale", "ping"],
    ),
    "public-private-markers": (
        _fixture("pyi_visibility_private_public_markers.f90"),
        ["a: Int32", "b: Int32", "def pub_proc("],
        ["class hidden_t:", "def hidden_proc("],
    ),
    "private-type-members": (
        _fixture("emit_omits_fortran_source_private_methods_and_fields.f90"),
        ["class box:", "    id: Int32", '@bind("visible_impl")', "    def visible(self) -> None: ..."],
        ["secret", "hidden"],
    ),
}


@pytest.mark.parametrize(
    ("source", "expected", "absent"),
    list(DECLARATION_CASES.values()),
    ids=list(DECLARATION_CASES),
)
def test_fortran_declarations_emit_contract_spelling_that_reloads(source: str, expected: list, absent: list):
    module = fortran_module_to_semantic_module(parse_fortran_source(source, filename="declarations.f90"))
    complete_python_export_policy(module)
    complete_contract_imports([module])
    code = emit_module(module)

    assert [fragment for fragment in expected if fragment not in code] == []
    assert [fragment for fragment in absent if fragment in code] == []
    assert emit_module(parse_pyi_text(code, module_name=module.name)) == code
