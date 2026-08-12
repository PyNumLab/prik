"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from prik.parsers.fortran.models import (
    FortranArgument,
    FortranModule,
)
from prik.semantics.fortran2ir import (
    FortranToIRConverter,
    _requirement_unit_name,
    _resolve_compile_time_text,
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
)
from tests.fortran._support.semantic_conversion import (
    array_contract,
    get_class,
    get_function,
    has_constraint,
)
from prik.parsers.fortran import parse_fortran_project
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


def test_converter_normalizes_wrapped_types_and_resolves_wildcard_imports():
    converter = FortranToIRConverter(wrapped_derived_types={("types_mod", "state_t")})
    module = FortranModule(name="consumer", uses={"OTHER_MOD": [], "TYPES_MOD": []})
    context = converter._module_derived_type_context(module)

    state = converter.visit(
        FortranArgument(name="state", base_type="derived", kind="state_t"),
        derived_type_context=context,
    ).semantic_type
    opaque_context = converter._module_derived_type_context(FortranModule(name="consumer", uses={"OPAQUE_MOD": []}))
    opaque = converter.visit(
        FortranArgument(name="opaque", base_type="derived", kind="opaque_t"),
        derived_type_context=opaque_context,
    ).semantic_type
    merged = FortranToIRConverter()._with_additional_wrapped_types({("TYPES_MOD", "State_T")})

    assert state.metadata["external_type_ref"] == {
        "name": "state_t",
        "local_name": "state_t",
        "origin_module": "TYPES_MOD",
        "wrapped": True,
        "representation": "wrapped",
    }
    assert opaque.metadata["external_type_ref"] == {
        "name": "opaque_t",
        "local_name": "opaque_t",
        "origin_module": "OPAQUE_MOD",
        "wrapped": False,
        "representation": "opaque",
    }
    assert merged.wrapped_derived_types == {("types_mod", "state_t")}
    custom_type_map = {("integer", None): "CustomInt"}
    configured = FortranToIRConverter(type_map=custom_type_map, compile_time_values={"rk": 8})
    configured = configured._with_additional_wrapped_types({("types_mod", "state_t")})
    assert configured.type_map is custom_type_map
    assert configured.compile_time_values == {"rk": "8"}
    assert FortranToIRConverter(compile_time_values={" ": 4, " RK ": 8}).compile_time_values == {"rk": "8"}
    assert _resolve_compile_time_text("n + missing", {"n": "4"}) == "4 + missing"
    assert _resolve_compile_time_text("N + missing", {"n": "4"}) == "4 + missing"
    assert _requirement_unit_name(module="m") == "m"
    assert _requirement_unit_name(unit_name="step") == "step"
    assert _requirement_unit_name() == "<source>"


def test_iso_c_module_variable_kinds_map_to_semantic_types():
    source = """
module constants_mod
  use iso_c_binding, only: c_int, c_double
  integer(kind=c_int), parameter :: nmax = 100
  real(kind=c_double), dimension(3) :: origin
end module constants_mod
"""

    parsed = parse_fortran_source(source)
    module = fortran_module_to_semantic_module(parsed)
    variables = {var.name: var.semantic_type for var in module.variables}

    assert variables["nmax"].name == "Int32"
    assert has_constraint(variables["nmax"], "Constant")
    assert variables["origin"].name == "Float64"
    assert variables["origin"].shape == ["3"]


def test_parameter_array_is_retained_as_a_public_semantic_constant():
    source = """
module constants_mod
  real, parameter :: machine_values(3) = [1.0, 2.0, 3.0]
  integer, parameter :: count = 3
contains
  real function second_value() result(value)
    value = machine_values(2)
  end function second_value
end module constants_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))

    variables = {variable.name: variable.semantic_type for variable in module.variables}

    assert list(variables) == ["machine_values", "count"]
    assert variables["machine_values"].name == "Float32"
    assert variables["machine_values"].shape == ["3"]
    assert has_constraint(variables["machine_values"], "Constant")
    assert [function.name for function in module.functions] == ["second_value"]


def test_explicit_public_unnamed_interface_procedure_uses_the_declared_signature():
    source = """
module api
  private
  public :: scale
  interface
    subroutine scale(values)
      real(8), intent(inout) :: values(*)
    end subroutine scale
  end interface
end module api
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))

    assert [function.name for function in module.functions] == ["scale"]
    assert module.prototypes == []
    argument = module.functions[0].arguments[0]
    assert argument.semantic_type.name == "Float64"
    assert argument.semantic_type.rank == 1


def test_explicit_public_submodule_interface_is_callable_from_parent_contract():
    project = parse_fortran_project(
        {
            "api.f90": """
module api
  private
  public :: values
  interface
    module function values(n) result(output)
      integer, intent(in) :: n
      integer :: output(n)
    end function values
  end interface
end module api
""",
            "implementation.f90": """
submodule(api) implementation
contains
  module procedure values
    do n = 1, n
      output(n) = n
    end do
  end procedure values
end submodule implementation
""",
        }
    )

    module = next(item for item in fortran_project_to_semantic_modules(project) if item.name == "api")

    assert [function.name for function in module.functions] == ["values"]
    assert module.prototypes == []
    assert module.functions[0].return_type.shape == ["n"]


def test_complex_module():
    source = """
module fem_mod

type :: mesh

    integer :: nelements
    integer :: nnodes

end type

contains

subroutine assemble(K, coords, connectivity)

    real(8), intent(out) :: K(:, :)

    real(8), intent(in) :: coords(:, :)

    integer, intent(in) :: connectivity(:, :)

end subroutine

function compute_norm(x) result(r)

    real(8), intent(in) :: x(:)

    real(8) :: r

end function

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    # --------------------------------------------------------
    # Module structure
    # --------------------------------------------------------

    assert smod.name == "fem_mod"

    assert len(smod.functions) == 2

    assert len(smod.classes) == 1

    # --------------------------------------------------------
    # Class checks
    # --------------------------------------------------------

    mesh_cls = get_class(smod, "mesh")

    assert len(mesh_cls.fields) == 2

    # --------------------------------------------------------
    # Procedure checks
    # --------------------------------------------------------

    assemble = get_function(smod, "assemble")

    assert len(assemble.arguments) == 3

    K = next(arg for arg in assemble.arguments if arg.name == "K")

    assert K.semantic_type.rank == 2

    assert array_contract(K.semantic_type).order == "ORDER_F"

    connectivity = next(arg for arg in assemble.arguments if arg.name == "connectivity")

    assert connectivity.semantic_type.name == "Int32"

    # --------------------------------------------------------
    # Function return
    # --------------------------------------------------------

    norm = get_function(smod, "compute_norm")

    assert norm.return_type.name == "Float64"


def test_module_conversion_public_api_entrypoint():
    source = """
module class_mod

contains

subroutine touch(x)

    integer, intent(inout) :: x

end subroutine

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    assert smod.name == "class_mod"
    assert get_function(smod, "touch").arguments[0].semantic_type.name == "Int32"


def test_fortran_to_ir_preserves_module_semantics_from_inline_source():
    source = """
module m
  use iso_c_binding
  private
  public :: doit
  integer, parameter :: p = 2
  integer :: x(0:)
  type, extends(base) :: thing
    integer, allocatable :: vals(:)
  end type thing
contains
  subroutine doit(a)
    integer, allocatable, intent(inout) :: a(:)
  end subroutine doit
end module m
"""
    parsed = parse_fortran_source(source, filename="m.f90")
    semantic_module = fortran_module_to_semantic_module(parsed)
    semantic_file_modules = fortran_file_to_semantic_modules(parsed, standalone_module_name="standalone")
    semantic_var = semantic_module.variables[0]
    semantic_proc = get_function(semantic_module, "doit")
    semantic_arg = semantic_proc.arguments[0]
    semantic_dtype = get_class(semantic_module, "thing")

    assert semantic_var.semantic_type.name == "Int32"
    assert array_contract(semantic_arg.semantic_type).allocatable is True
    assert semantic_proc.projection[0].python_position == 0
    assert semantic_dtype.base_classes == ["base"]
    assert semantic_module.imports == ["iso_c_binding"]
    assert semantic_dtype.visibility == "private"
    assert semantic_proc.visibility == "public"
    assert semantic_file_modules[0].name == "m"


def test_declaration_level_private_module_constant_is_not_exported():
    parsed = parse_fortran_source(
        """
module constants
  real, parameter, private :: epsilon = 1.0
  real, parameter :: visible = 2.0
end module constants
""",
        filename="constants.f90",
    )

    semantic_module = fortran_module_to_semantic_module(parsed)

    assert [(variable.name, variable.visibility) for variable in semantic_module.variables] == [
        ("epsilon", "private"),
        ("visible", "public"),
    ]
