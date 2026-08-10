"""Tests split by stable ownership concept from `test_imports_and_packages.py`."""

import pytest
from prik import parse_fortran_file as parse_fortran_source
from prik.codegen.printers import (
    PyiPrinter,
    emit_module,
    emit_module_stubs,
)
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.semantics.models import (
    ProjectionMapping,
    SemanticArgument,
    SemanticClass,
    SemanticFunction,
    SemanticMethod,
    SemanticModule,
    SemanticType,
)
from tests.fortran._support.printer_models import (
    OPERATOR_F90_SOURCE,
    generate_pyi,
    generate_wrapper_artifacts,
    normalize,
    parse_pyi_text,
    rendered_source,
)


def test_emit_class():
    source = """
module sparse_mod

type :: sparse_matrix

    integer :: nrows
    integer :: ncols

end type

end module
"""

    code = generate_pyi(source)

    assert "class sparse_matrix" in code


def test_emit_inheritance():
    source = """
module inheritance_mod

type :: base_matrix
end type

type, extends(base_matrix) :: sparse_matrix
end type

end module
"""

    code = generate_pyi(source)

    assert "class sparse_matrix(base_matrix)" in code


def test_printer_class_entrypoint():
    source = """
module class_print_mod

contains

subroutine touch(x)

    integer, intent(inout) :: x

end subroutine

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    code = PyiPrinter().emit(smod)

    assert "def touch(" in code
    assert "@native_call([Addr(Arg(0))])" in code
    assert "x: Int32" in code


def test_emit_class_method_keeps_method_indentation():
    module = SemanticModule(
        name="method_mod",
        classes=[
            SemanticClass(
                name="thing",
                methods=[SemanticMethod(name="reset")],
            )
        ],
    )

    code = emit_module(module)

    assert "class thing:\n    def reset(self) -> None: ..." in code


def test_emit_type_bound_procedure_as_python_method_without_duplicate_self():
    source = """
module vector_mod
  private
  public :: vector

  type :: vector
    real(8), allocatable :: values(:)
  contains
    procedure :: scale
  end type vector

contains
  subroutine scale(self, alpha)
    type(vector), intent(inout) :: self
    real(8), intent(in) :: alpha
  end subroutine scale
end module vector_mod
"""

    code = generate_pyi(source)

    assert "class vector:" in code
    assert "values: Allocatable[Float64[:]]" in code
    assert "    @native_call([Pass(), Addr(Arg(0))])" in code
    assert "    def scale(\n        self,\n        alpha: Float64\n    ) -> None: ..." in code
    assert "        self: vector" not in code


def test_emit_fortran_type_default_constructor_and_field_values():
    source = """
module constructor_mod
  type :: state
    integer :: id = 7
    real(8) :: scale = 2.5
    logical :: enabled = .true.
  end type state
end module constructor_mod
"""

    code = generate_pyi(source)

    assert normalize(
        """
class state:
    def __init__(
        self,
        *,
        id: Int32 = 7,
        scale: Float64 = 2.5,
        enabled: Bool = True
    ) -> None: ...
"""
    ) in normalize(code)
    assert "    id: Int32 = 7" in code
    assert "    scale: Float64 = 2.5" in code
    assert "    enabled: Bool = True" in code


def test_emit_explicit_pass_name_and_nopass_methods():
    source = """
module pass_mod
  type :: vector
  contains
    procedure, pass(owner) :: shift => shift_vector
    procedure, nopass :: make => make_vector
  end type vector
contains
  subroutine shift_vector(dx, owner, dy)
    real(8), intent(in) :: dx
    class(vector), intent(inout) :: owner
    real(8), intent(in) :: dy
  end subroutine shift_vector
  function make_vector(value) result(created)
    real(8), intent(in) :: value
    type(vector) :: created
  end function make_vector
end module pass_mod
"""

    code = generate_pyi(source)

    assert "    def shift(\n        self,\n        dx: Float64,\n        dy: Float64" in code
    assert "        owner: Addr(vector)" not in code
    assert "@native_call([Addr(Arg(0)), Pass(), Addr(Arg(1))])" in code
    assert "owner: Annotated[vector, Polymorphic]" in code
    assert '    @staticmethod\n    @bind("make_vector")' in code
    assert "value: Float64" in code
    assert "-> vector: ..." in code


def test_emit_and_load_module_and_type_bound_overload_sets():
    source = """
module generic_mod
  interface convert
    module procedure convert_integer, convert_real
  end interface convert
  type :: box
  contains
    procedure, private :: set_integer
    procedure, private :: set_real
    generic, public :: set => set_integer, set_real
  end type box
contains
  integer function convert_integer(value)
    integer :: value
    convert_integer = value
  end function convert_integer
  real function convert_real(value)
    real :: value
    convert_real = value
  end function convert_real
  subroutine set_integer(self, value)
    class(box) :: self
    integer :: value
  end subroutine set_integer
  subroutine set_real(self, value)
    class(box) :: self
    real :: value
  end subroutine set_real
end module generic_mod
"""
    code = generate_pyi(source)

    assert "from typing import overload" not in code
    assert code.count('@overload("convert_integer")\ndef convert(') == 1
    assert code.count('@overload("convert_real")\ndef convert(') == 1
    assert code.count('    @bind("set")\n    @overload("set_integer")\n    def set(') == 1
    assert code.count('    @bind("set")\n    @overload("set_real")\n    def set(') == 1
    assert '@overload("convert_integer")\n@native_call' not in code
    assert '    @overload("set_integer")\n    @native_call' not in code

    loaded = parse_pyi_text(code, module_name="generic_mod")
    assert [(item.name, len(item.procedures)) for item in loaded.overload_sets] == [("convert", 2)]
    assert [procedure.name for procedure in loaded.overload_sets[0].procedures] == [
        "convert_integer",
        "convert_real",
    ]
    assert loaded.imports == []
    assert [(item.name, len(item.procedures)) for item in loaded.classes[0].overload_sets] == [("set", 2)]
    assert [procedure.name for procedure in loaded.classes[0].overload_sets[0].procedures] == [
        "set_integer",
        "set_real",
    ]
    assert {procedure.native_name for procedure in loaded.classes[0].overload_sets[0].procedures} == {"set"}


def test_private_module_generic_specifics_bind_overload_candidates_to_public_generic():
    source = """
module generic_mod
  implicit none
  private
  public :: convert
  interface convert
    module procedure convert_integer, convert_real
  end interface convert
contains
  integer function convert_integer(value)
    integer :: value
    convert_integer = value
  end function convert_integer
  real function convert_real(value)
    real :: value
    convert_real = value
  end function convert_real
end module generic_mod
"""

    code = generate_pyi(source)

    assert code.count('@bind("convert")\n@overload("convert_integer")') == 1
    assert code.count('@bind("convert")\n@overload("convert_real")') == 1
    loaded = parse_pyi_text(code, module_name="generic_mod")
    assert [procedure.native_name for procedure in loaded.overload_sets[0].procedures] == [
        "convert",
        "convert",
    ]
    assert emit_module(loaded) == code


def test_public_type_bound_generic_specifics_do_not_emit_bind():
    source = """
module generic_mod
  type :: box
  contains
    procedure :: set_integer
    procedure :: set_real
    generic :: set => set_integer, set_real
  end type box
contains
  subroutine set_integer(self, value)
    class(box) :: self
    integer :: value
  end subroutine set_integer
  subroutine set_real(self, value)
    class(box) :: self
    real :: value
  end subroutine set_real
end module generic_mod
"""

    code = generate_pyi(source)

    assert '    @bind("set")' not in code
    assert code.count('    @overload("set_integer")\n    def set(') == 1
    assert code.count('    @overload("set_real")\n    def set(') == 1
    loaded = parse_pyi_text(code, module_name="generic_mod")
    assert [procedure.native_name for procedure in loaded.classes[0].overload_sets[0].procedures] == [
        "set_integer",
        "set_real",
    ]


def test_emit_and_load_aliased_derived_module_variable_declaration():
    source = """
module derived_module_state
  type :: box
    real(8), allocatable :: values(:)
  end type box
  type(box), target :: current
end module derived_module_state
"""
    code = generate_pyi(source)

    assert "current: Annotated[box, Aliased]" in code

    loaded = parse_pyi_text(code, module_name="derived_module_state")
    assert [variable.name for variable in loaded.variables] == ["current"]
    assert loaded.variables[0].semantic_type.name == "box"
    assert loaded.variables[0].semantic_type.metadata["aliased"] is True


def test_emit_module_stubs_print_plain_derived_module_variable_as_live_object():
    source = """
module derived_module_snapshot
  type :: box
    real(8) :: value
  end type box
  type(box) :: current
end module derived_module_snapshot
"""
    parsed = parse_fortran_source(source)
    semantic_module = fortran_module_to_semantic_module(parsed)

    code = emit_module_stubs(semantic_module)["derived_module_snapshot"]

    assert "current: box" in code
    loaded = parse_pyi_text(code, module_name="derived_module_snapshot")
    assert loaded.variables[0].semantic_type.name == "box"


def test_defined_operator_pyi_round_trip_preserves_native_links_without_fortran_source():
    semantic_module = fortran_module_to_semantic_module(
        parse_fortran_source(OPERATOR_F90_SOURCE.read_text(), filename=str(OPERATOR_F90_SOURCE))
    )
    code = emit_module(semantic_module)

    assert '@overload("add_real_vector")' in code
    assert "def __radd__(" in code
    assert '@overload("assign_vector_real")' in code
    assert "def assign(" in code
    assert "left: Annotated[Addr(vector)" not in code
    assert "left: vector" in code
    assert '-> Returns["left", vector]: ...' in code
    assert "right: Float64\n    ) -> vector: ..." in code
    assert '@overload("dot_vectors")' in code
    assert "def operator_dot(" in code
    assert '@overload("equivalent_vector_offset", generic="operator(.eqv.)")' in code
    assert '@overload("not_equivalent_vector_integer", generic="operator(.neqv.)")' in code
    assert "from typing import overload" not in code

    loaded = parse_pyi_text(code, module_name=semantic_module.name)
    assert emit_module(loaded) == code


def test_defined_operator_pyi_generates_wrapper_sources_without_fortran_source():
    semantic_module = fortran_module_to_semantic_module(
        parse_fortran_source(OPERATOR_F90_SOURCE.read_text(), filename=str(OPERATOR_F90_SOURCE))
    )
    pyi = emit_module(semantic_module)
    loaded = parse_pyi_text(pyi, module_name=semantic_module.name)
    generated = generate_wrapper_artifacts(loaded)

    assert [path.name for path in generated.source_paths] == [
        "bind_c_foperators_f90_wrapper.f90",
        "foperators_f90_wrapper.c",
        "foperators_f90_wrapper.h",
    ]
    fortran_wrapper = rendered_source(generated, ".f90")
    c_wrapper = rendered_source(generated, ".c")
    assert "left + right" in fortran_wrapper
    assert "left = right" in fortran_wrapper
    assert "left .eqv. right" in fortran_wrapper
    assert " .neqv. " in fortran_wrapper
    assert "def __add__(self, *args, **kwargs):" in c_wrapper
    assert "def __ne__(self, *args, **kwargs):" in c_wrapper


def test_emit_module_variables_with_visibility():
    source = """
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
    code = generate_pyi(source)
    assert "answer:" not in code
    assert "counter: Int32" in code
    assert "hidden_scale" not in code
    assert "ping" not in code


def test_emit_omits_fortran_source_private_methods_and_fields():
    source = """
module private_method_mod
  implicit none
  private
  public :: box
  type :: box
    private
    integer, public :: id
    integer, private :: secret
  contains
    procedure, private :: hidden => hidden_impl
    procedure, public :: visible => visible_impl
  end type box
contains
  subroutine hidden_impl(self)
    class(box) :: self
  end subroutine hidden_impl
  subroutine visible_impl(self)
    class(box) :: self
  end subroutine visible_impl
end module
"""

    code = generate_pyi(source)

    assert "class box:" in code
    assert "    id: Int32" in code
    assert "secret" not in code
    assert "hidden" not in code
    assert "hidden_impl" not in code
    assert '@bind("visible_impl")' in code
    assert "    def visible(self) -> None: ..." in code


def test_printer_rejects_each_unresolved_semantic_type_field():
    printer = PyiPrinter()
    message = "Cannot emit .pyi with unresolved semantic type 'Unknown'"

    with pytest.raises(ValueError) as unknown_name:
        printer.emit(SemanticType("Unknown", dtype="Int32"))
    with pytest.raises(ValueError) as unknown_dtype:
        printer.emit(SemanticType("Int32", dtype="Unknown"))

    assert str(unknown_name.value) == message
    assert str(unknown_dtype.value) == message


def test_printer_preserves_structured_class_and_decorator_layout():
    printer = PyiPrinter()
    decorated_method = SemanticMethod(
        name="lookup",
        return_type=SemanticType("Float64"),
        visibility="private",
        projection=[ProjectionMapping(native_position=0, result_position=0)],
    )
    cls = SemanticClass(
        name="thing",
        base_classes=["Opaque", "Protocol"],
        fields=[SemanticArgument("value", SemanticType("Int32"))],
        methods=[decorated_method, SemanticMethod(name="reset")],
    )
    decorated_function = SemanticFunction(
        name="wrapper",
        visibility="private",
        projection=[ProjectionMapping(native_position=0, result_position=0)],
    )

    assert (
        printer.emit(cls)
        == """class thing(Opaque, Protocol):
    value: Int32

    @private
    @native_call([Return(0)])
    def lookup(self) -> Float64: ...

    def reset(self) -> None: ..."""
    )
    assert (
        printer.emit(decorated_function)
        == """@private
@native_call([Return(0)])
def wrapper() -> None: ..."""
    )
