"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from pathlib import Path

from tests.fortran._support.semantic_conversion import (
    FortranToIRConverter,
    fortran_module_to_semantic_module,
    parse_fortran_source,
    pytest,
)

OPERATOR_F90_SOURCE = Path(__file__).parents[1] / "end_to_end" / "fixtures" / "foperators_f90.f90"


def test_converter_preserves_module_and_type_bound_generic_overload_sets():
    source = """
module generic_mod
  private
  public :: box, convert
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
    module = FortranToIRConverter().visit(parse_fortran_source(source).modules[0])

    assert [(item.name, [proc.name for proc in item.procedures]) for item in module.overload_sets] == [
        ("convert", ["convert_integer", "convert_real"])
    ]
    assert all(proc.visibility == "public" for proc in module.overload_sets[0].procedures)
    box = module.classes[0]
    assert [(item.name, [proc.name for proc in item.procedures]) for item in box.overload_sets] == [
        ("set", ["set_integer", "set_real"])
    ]
    assert all(proc.visibility == "public" for proc in box.overload_sets[0].procedures)


def test_converter_rejects_generic_constructor_interfaces_during_semantic_conversion():
    source = """
module constructor_generic_mod
  type :: item
    integer :: value
  end type item
  interface item
    module procedure make_item
  end interface item
contains
  type(item) function make_item(value) result(instance)
    integer, intent(in) :: value
    instance%value = value
  end function make_item
end module constructor_generic_mod
"""

    with pytest.raises(ValueError, match="cannot represent generic constructor") as exc_info:
        fortran_module_to_semantic_module(parse_fortran_source(source))

    assert "constructor_generic_mod.item" in str(exc_info.value)


def test_converter_preserves_defined_operators_assignment_and_type_bound_operators():
    module = FortranToIRConverter().visit(
        parse_fortran_source(
            OPERATOR_F90_SOURCE.read_text(),
            filename=str(OPERATOR_F90_SOURCE),
        ).modules[0]
    )

    assert [(item.name, len(item.procedures)) for item in module.overload_sets] == [("convert", 2)]
    classes = {cls.name: cls for cls in module.classes}
    vector_sets = {item.name: item for item in classes["vector"].overload_sets}
    assert set(vector_sets) == {
        "__add__",
        "__pos__",
        "__sub__",
        "__neg__",
        "__mul__",
        "__truediv__",
        "__pow__",
        "__eq__",
        "__ne__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
        "__and__",
        "__or__",
        "__invert__",
        "operator_dot",
        "r_operator_shift",
        "assign",
    }
    assert [procedure.name for procedure in vector_sets["__add__"].procedures] == [
        "add_vectors",
        "add_vector_integer",
        "add_vector_real",
        "add_real_vector",
        "add_vector_array",
        "add_vector_offset",
    ]
    reflected = next(
        procedure for procedure in vector_sets["__add__"].procedures if procedure.name == "add_real_vector"
    )
    assert reflected.metadata["python_method_name"] == "__radd__"
    assert reflected.metadata["python_bound_position"] == 1
    assert reflected.metadata["fortran_generic_name"] == "operator(+)"
    assert vector_sets["assign"].procedures[0].metadata["fortran_generic_name"] == "assignment(=)"
    assert vector_sets["operator_dot"].procedures[0].metadata["python_method_name"] == "operator_dot"
    assert vector_sets["r_operator_shift"].procedures[0].metadata["python_method_name"] == "r_operator_shift"

    assert [
        (item.name, [procedure.name for procedure in item.procedures]) for item in classes["counter"].overload_sets
    ] == [("__add__", ["counter_add_integer"])]
