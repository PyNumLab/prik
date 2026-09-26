"""Declaration forms, compile-time kind and shape resolution, and type definitions."""

from prik.parsers.fortran import parse_fortran_file, parse_fortran_project
from prik.parsers.fortran.scope import ScopeUses


def test_legacy_star_kind_and_declarations_without_double_colon_are_resolved():
    code = """
      subroutine legacy_decl(x, z, p, c, f)
      real*8 x
      complex*16 z
      type(point) p
      class(point) c
      procedure(cb) f
      end
"""

    sig = parse_fortran_file(code, filename="legacy_decl.f").procedures[0]
    args = {arg.name: (arg.base_type, arg.kind) for arg in sig.arguments}

    assert args == {
        "x": ("real", "8"),
        "z": ("complex", "16"),
        "p": ("derived", "point"),
        "c": ("derived", "point"),
        "f": ("procedure", "cb"),
    }


def test_bind_c_and_dummy_argument_attributes_from_inline_fortran():
    code = """
subroutine c_step(n, x, y, work, cb) bind(c, name="c_step")
  integer, value, intent(in) :: n
  real, optional, intent(inout) :: x(:)
  real, pointer, intent(out) :: y(:)
  real, allocatable, intent(inout) :: work(:)
  real, external :: cb
end subroutine c_step
"""

    sig = parse_fortran_file(code).procedures[0]
    args = {arg.name: arg for arg in sig.arguments}

    assert "bind(c)" in sig.attributes
    assert args["n"].intent == "in"
    assert args["n"].pass_by_value is True
    assert args["x"].intent == "inout"
    assert args["x"].optional is True
    assert args["y"].intent == "out"
    assert args["y"].pointer is True
    assert args["work"].intent == "inout"
    assert args["work"].allocatable is True
    assert args["cb"].intent is None
    assert args["cb"].base_type == "real"


def test_module_specification_keeps_variables_and_skips_other_statements():
    """Statements that declare no variable are skipped; every declared entity is kept once."""
    parsed = parse_fortran_file(
        """
module spec_mod
  public ::
  private ::
  import :: external_symbol
  implicit none
  save
  module procedure :: ignored_impl
  integer, parameter :: rk = 8, n = 3
  real(kind=rk), parameter, private, dimension(0:n) :: weights = 1.0_rk
  logical, parameter :: flag = .true.
  integer, parameter :: pair(2) = (/ 1, 2 /)
  integer kept, , also_kept
  real values(2)
  real*8 :: wide
  character(len=default_len) :: label*(name_len), other
  type :: state
    sequence
    private
    real :: x, , y
  end type state
contains
  subroutine worker()
  end subroutine worker
end module spec_mod

program type_stmt_program
  type :: local_state
    integer :: marker
  end type local_state
  integer :: kept
end program type_stmt_program
""",
        filename="module_spec.f90",
    )
    module = parsed.modules[0]
    variables = {var.name: var for var in module.variables}

    assert module.default_visibility == "private"
    assert list(variables) == [
        "rk",
        "n",
        "weights",
        "flag",
        "pair",
        "kept",
        "also_kept",
        "values",
        "wide",
        "label",
        "other",
    ]
    weights = variables["weights"]
    assert (weights.kind, weights.shape, weights.lbound, weights.ubound) == ("8", ["0:3"], ["0"], ["3"])
    assert (weights.is_parameter, weights.value, weights.symbolic_value) == (True, "1", "1.0_rk")
    assert [(variables[name].value, variables[name].symbolic_value) for name in ("flag", "pair")] == [
        ("1", ".true."),
        ("(/ 1, 2 /)", "(/ 1, 2 /)"),
    ]
    assert module.private_symbols == ["weights"]
    assert (variables["kept"].base_type, variables["values"].shape) == ("integer", ["2"])
    assert (variables["wide"].base_type, variables["wide"].kind) == ("real", "8")
    # An entity's own character length does not leak into the next entity.
    assert (variables["other"].kind, variables["other"].shape) == ("len=default_len", [])
    dtype = module.derived_types[0]
    assert [field.name for field in dtype.fields] == ["x", "y"]
    assert dtype.attributes == ["sequence"]
    assert [var.name for var in parsed.programs[0].variables] == ["kept"]


def test_use_rename_intrinsic_and_empty_only_items_are_recorded():
    code = """
module use_forms
  use list_input, delete_input => delete_input_list
  use, intrinsic :: iso_c_binding, only: c_int, c_double
  use constants_mod, only: rk, , ik
end module use_forms
"""

    scope = ScopeUses(parse_fortran_file(code).modules[0].uses)

    # A rename without `only` binds the new name and still imports the rest.
    assert scope.imports_all("list_input") is True
    assert [(item.source, item.target) for item in scope.mappings("list_input")] == [
        ("delete_input_list", "delete_input")
    ]
    assert scope.imports_all("iso_c_binding") is False
    assert [(item.source, item.target) for item in scope.mappings("iso_c_binding")] == [
        ("c_int", None),
        ("c_double", None),
    ]
    assert [item.local_name for item in scope.mappings("constants_mod")] == ["rk", "ik"]


def test_declaration_and_execution_edge_branches_from_inline_fortran():
    code = """
subroutine declaration_edges(i, x, y)
  integer ( kind = 4 ) i
  double precision y
  real x
  go to 10
10 continue
end subroutine declaration_edges
"""

    sig = parse_fortran_file(code, filename="declaration_edges.f90").procedures[0]
    args = {arg.name: arg for arg in sig.arguments}

    assert args["i"].base_type == "integer"
    assert args["i"].kind == "4"
    assert args["x"].base_type == "real"
    assert args["y"].base_type == "real"
    assert args["y"].target_kind_expression == "kind(1.0d0)"


def test_cross_file_kind_resolution_for_arguments_results_and_local_parameters():
    project = parse_fortran_project(
        {
            "kinds.f90": """
module kinds_mod
  integer, parameter :: base = 4
  integer, parameter :: offset = base
  integer, parameter :: rk = base + offset
end module kinds_mod
""",
            "solver.f90": """
module solver_mod
  use kinds_mod
contains
  function make_value() result(value)
    real(kind=rk) :: value
  end function make_value

  subroutine use_local(x)
    integer, parameter :: n = 4
    real, intent(inout) :: x(1:n)
  end subroutine use_local
end module solver_mod
""",
        }
    )

    assert project.procedures["solver_mod.make_value"].result.kind == "8"
    assert project.procedures["solver_mod.use_local"].arguments[0].shape == ["1:4"]


def test_local_parameter_chains_resolve_kinds_and_shapes():
    modern = parse_fortran_file(
        """
subroutine consume(x, y)
  integer, parameter :: word = 4
  integer, parameter :: twice = 2
  integer, parameter :: rk = word * twice
  integer, parameter :: ck = rk * twice
  real(kind=rk), intent(in) :: x
  complex(kind=ck), intent(out) :: y
end subroutine consume
""",
        filename="local_kind_chain.f90",
    ).procedures[0]
    dependent = parse_fortran_file(
        """
subroutine sized(c, d, x)
  character(len=4) :: c*(8), d
  integer, parameter :: m = 3, k = m + 1
  real :: x(k)
end subroutine sized
""",
        filename="dependent_parameters.f90",
    ).procedures[0]
    legacy = parse_fortran_file(
        "      subroutine loose(x, y)\n      parameter (ival = 2, alpha = 1.0)\n      real x(ival), y(ival+1)\n      end\n",
        filename="loose.f",
    ).procedures[0]

    assert [arg.kind for arg in modern.arguments] == ["8", "16"]
    assert [arg.shape for arg in legacy.arguments] == [["2"], ["3"]]
    # A parameter defined through another resolves; an entity length stays on its entity.
    assert [(arg.kind, arg.shape) for arg in dependent.arguments] == [("len=4", ["8"]), ("len=4", []), ("", ["4"])]


def test_local_compile_time_arithmetic_is_folded_for_shapes_and_parameters():
    code = """
subroutine arithmetic_shapes(a, b, c, d, e, f)
  integer, parameter :: n = 8
  integer, parameter :: m = 3
  integer, parameter :: one = 1.0d+0
  real, intent(inout) :: a(1:n-m)
  real, intent(inout) :: b(1:n*m)
  real, intent(inout) :: c(1:n/m)
  real, intent(inout) :: d(1:m**2)
  real, intent(inout) :: e(1:+n-one)
  real, intent(inout) :: f(1:+n)
end subroutine arithmetic_shapes
"""

    sig = parse_fortran_file(code).procedures[0]

    assert [arg.shape[0] for arg in sig.arguments] == [
        "1:5",
        "1:24",
        "1:(8)/(3)",
        "1:9",
        "1:7",
        "1:8",
    ]


def test_local_parameters_of_one_procedure_do_not_leak_into_a_sibling():
    project = parse_fortran_project(
        {
            "dims.f90": """
module dims_mod
  integer, parameter :: n = 3
contains
  subroutine a()
    integer, parameter :: n = 9
  end subroutine a

  subroutine b(x)
    real, intent(inout) :: x(1:n)
  end subroutine b
end module dims_mod
"""
        }
    )

    assert project.procedures["dims_mod.b"].arguments[0].shape[0] in {"1:n", "1:3"}


def test_type_bound_bindings_and_final_procedures_are_recorded():
    dtype = (
        parse_fortran_file(
            """
module type_contains_valid_mod
  type :: parent
  end type parent
  type, extends(parent), public :: state
  contains
    procedure, pass(self), public :: update, reset
    generic, public :: assignment(=) => assign_child, assign_other
    FINAL :: cleanup, destroy
  end type state
end module type_contains_valid_mod
""",
            filename="type_contains_valid.f90",
        )
        .modules[0]
        .derived_types[1]
    )

    assert dtype.extends.name == "parent"
    assert dtype.attributes == ["public"]
    assert dtype.methods == ["update", "reset"]
    assert dtype.procedure_bindings == [
        {"name": "update", "attrs": ["pass(self)", "public"], "visibility": "public"},
        {"name": "reset", "attrs": ["pass(self)", "public"], "visibility": "public"},
    ]
    assert dtype.generic_bindings == [
        {
            "name": "assignment(=)",
            "targets": ["assign_child", "assign_other"],
            "attrs": ["public"],
            "visibility": "public",
        }
    ]
    assert dtype.final_procedures == ["cleanup", "destroy"]


def test_type_accessibility_statements_set_component_and_binding_defaults():
    """A type's `private` statement is a default, not an unsupported declaration.

    The statement before `contains` sets component accessibility; the statement
    after it sets type-bound accessibility. Each declaration that states its own
    accessibility keeps it.
    """
    module = parse_fortran_file(
        """
module access_mod
  implicit none
  type,public :: t
    private
    integer :: hidden = 0
    integer,public :: shown = 0
  contains
    private
    procedure :: internal_step
    procedure,public :: step => internal_step
  end type t
contains
  subroutine internal_step(self)
    class(t),intent(inout) :: self
  end subroutine internal_step
end module access_mod
"""
    ).modules[0]

    dtype = module.derived_types[0]
    assert dtype.component_visibility == "private"
    assert dtype.binding_visibility == "private"
    assert {field.name: field.visibility for field in dtype.fields} == {
        "hidden": "private",
        "shown": "public",
    }
    assert [(binding["name"], binding["visibility"]) for binding in dtype.procedure_bindings] == [
        ("internal_step", "private"),
        ("step => internal_step", "public"),
    ]


def test_deferred_type_bound_binding_records_its_declaring_interface():
    """A deferred binding parses; whether it can be wrapped belongs to policy."""
    module = parse_fortran_file(
        """
module deferred_mod
  implicit none
  type,public,abstract :: base
  contains
    procedure(size_func),deferred,public :: size_of
  end type base
  abstract interface
    pure function size_func(self) result(s)
      import :: base
      class(base),intent(in) :: self
      integer :: s
    end function size_func
  end interface
end module deferred_mod
"""
    ).modules[0]

    binding = module.derived_types[0].procedure_bindings[0]
    assert binding["name"] == "size_of"
    assert binding["interface"] == "size_func"
    assert "deferred" in binding["attrs"]


def test_nested_interface_procedure_without_matching_dummy_stays_publicly_parseable():
    sig = parse_fortran_file(
        """
subroutine caller()
  interface
    subroutine helper(x)
      integer, intent(in) :: x
    end subroutine helper
  end interface
end subroutine caller
"""
    ).procedures[0]

    assert sig.name == "caller"
    assert sig.arguments == []
