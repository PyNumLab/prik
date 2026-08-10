"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

import pytest
from prik.codegen.printers import emit_module
from prik.parsers.fortran.models import (
    FortranArgument,
    FortranDerivedType,
    FortranFile,
    FortranProcedureSignature,
    FortranVariable,
)
from prik.semantics.fortran2ir import (
    FortranToIRConverter,
    fortran_module_to_semantic_module,
)
from prik.semantics.models import (
    SemanticArgument,
    SemanticConstraint,
    SemanticFunction,
    SemanticMethod,
    SemanticType,
)
from prik.semantics.native_contract import native_contract_issues
from tests.fortran._support.semantic_conversion import get_class
from prik import parse_fortran_file as parse_fortran_source
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text


def test_converter_rejects_unsupported_inputs_and_missing_derived_type_names():
    converter = FortranToIRConverter()

    with pytest.raises(TypeError) as error:
        converter.visit(object())
    assert str(error.value) == "Unsupported Fortran parse object: <class 'object'>"

    with pytest.raises(TypeError, match="Unsupported Fortran parse object"):
        converter.first_module(object())

    with pytest.raises(ValueError) as error:
        converter.first_module(FortranFile())
    assert str(error.value) == "Expected at least one Fortran module in parsed file"

    from_list = converter.first_module(
        [
            FortranProcedureSignature(
                name="inside",
                kind="subroutine",
                module="legacy_mod",
                in_interface=True,
            ),
            FortranProcedureSignature(name="outside", kind="subroutine"),
        ]
    )
    assert from_list.name == "legacy_mod"
    assert [proc.name for proc in from_list.procedures] == ["outside"]

    with pytest.raises(ValueError, match="missing concrete type name"):
        converter.visit(FortranVariable(name="state", base_type="derived"))

    with pytest.raises(ValueError, match="Unknown Fortran datatype"):
        converter.visit(FortranVariable(name="x", base_type="unknown"))

    with pytest.raises(ValueError) as error:
        converter.visit(FortranVariable(name="x", base_type="real", kind="selected_real_kind(33)"))
    assert str(error.value) == "Unsupported Fortran semantic type for variable 'x': real(kind=selected_real_kind(33))"


def test_converter_covers_derived_dispatch_methods_and_kind_edges():
    converter = FortranToIRConverter()
    callback = SemanticFunction(
        name="advance",
        native_name="advance_impl",
        arguments=[SemanticArgument("state", SemanticType("particle_t"))],
        return_type=SemanticType("Int32"),
        contracts=[SemanticConstraint("Pure")],
        visibility="private",
    )
    dtype = FortranDerivedType(
        name="particle_t",
        fields=[FortranArgument(name="id", base_type="integer")],
        methods=["missing_binding", "advance"],
    )

    semantic_class = converter.visit(dtype, procedure_lookup={"advance": callback})

    assert semantic_class.methods == [
        SemanticMethod(
            name="advance",
            native_name="advance_impl",
            arguments=callback.arguments,
            return_type=callback.return_type,
            contracts=callback.contracts,
            visibility="private",
            passed_object_name="state",
            passed_object_position=0,
        )
    ]
    assert converter.visit(FortranVariable(name="count", base_type="integer")).name == "Int32"


def test_derived_type_initializers_and_finalizers_reach_semantic_ir():
    source = """
module lifecycle_mod
  type :: state
    integer :: count = 7
  contains
    final :: cleanup
  end type state
contains
  subroutine cleanup(self)
    type(state), intent(inout) :: self
  end subroutine cleanup
end module lifecycle_mod
"""

    parsed = parse_fortran_source(source)
    module = fortran_module_to_semantic_module(parsed)
    state = module.classes[0]

    assert state.fields[0].default_value == "7"
    assert state.fields[0].metadata["fortran_initializer"] == "7"
    assert state.metadata["fortran_final_procedures"] == ["cleanup"]
    emitted = emit_module(module)
    assert "@native_type(finalizers=('cleanup',))" in emitted
    assert native_contract_issues(parse_pyi_text(emitted, module_name=module.name)) == []


def test_bind_c_and_sequence_types_preserve_accessor_layout_metadata():
    source = """
module layout_mod
  use iso_c_binding
  type, bind(C) :: point
    real(c_double) :: x
    integer(c_int) :: axis
  end type point
  type, bind(C) :: tagged_point
    type(point) :: position
    logical(c_bool) :: active
    complex(c_double_complex) :: weight
  end type tagged_point
  type :: ordered_pair
    sequence
    integer :: first
    integer :: second
  end type ordered_pair
end module layout_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))
    point, tagged, ordered = module.classes

    assert point.metadata["fortran_type_attributes"] == ["bind(c)"]
    assert "@native_type(attributes=('bind(c)',))" in emit_module(module)
    assert point.metadata["fortran_bind_c"] is True
    assert point.metadata["fortran_layout_policy"] == "accessors"
    assert point.metadata["fortran_direct_layout"] is False
    assert point.metadata["fortran_component_order"] == ["x", "axis"]
    assert point.metadata["fortran_component_facts"] == [
        {
            "name": "x",
            "source_type": "real(kind=c_double)",
            "kind": "c_double",
            "rank": 0,
            "shape": [],
            "allocatable": False,
            "pointer": False,
            "target": False,
        },
        {
            "name": "axis",
            "source_type": "integer(kind=c_int)",
            "kind": "c_int",
            "rank": 0,
            "shape": [],
            "allocatable": False,
            "pointer": False,
            "target": False,
        },
    ]
    assert [field.name for field in tagged.fields] == ["position", "active", "weight"]
    assert tagged.fields[0].origin.source_type == "type(point)"
    assert tagged.fields[1].origin.source_type == "logical(kind=c_bool)"
    assert tagged.fields[2].origin.source_type == "complex(kind=c_double_complex)"
    assert ordered.metadata["fortran_type_attributes"] == ["sequence"]
    assert "@native_type(attributes=('sequence',))" in emit_module(module)
    assert ordered.metadata["fortran_sequence"] is True
    assert ordered.metadata["fortran_layout_policy"] == "accessors"


def test_bind_c_derived_value_argument_is_accessor_routed():
    interoperable_source = """
module bind_c_value_mod
  use iso_c_binding
  type, bind(C) :: point
    real(c_double) :: x
  end type point
contains
  subroutine consume(value) bind(C)
    type(point), value :: value
  end subroutine consume
end module bind_c_value_mod
"""
    interoperable = fortran_module_to_semantic_module(parse_fortran_source(interoperable_source))
    assert interoperable.classes[0].name == "point"


def test_derived_type():
    source = """
module sparse_mod

type :: sparse_matrix
    integer :: nrows
    integer :: ncols
end type

contains

subroutine multiply(A, x, y)

    type(sparse_matrix), intent(in) :: A

    real(8), intent(in) :: x(:)

    real(8), intent(out) :: y(:)

end subroutine

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    cls = get_class(smod, "sparse_matrix")

    assert cls.name == "sparse_matrix"

    assert len(cls.fields) == 2

    field_names = {f.name for f in cls.fields}

    assert "nrows" in field_names
    assert "ncols" in field_names


def test_derived_type_inheritance():
    source = """
module inheritance_mod

type :: base_matrix
end type

type, extends(base_matrix) :: sparse_matrix
end type

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    cls = get_class(smod, "sparse_matrix")

    assert "base_matrix" in cls.base_classes


def test_class_declarations_preserve_polymorphic_source_fact():
    source = """
module polymorphic_source_mod
  type :: base
  contains
    procedure :: touch
  end type base
contains
  subroutine touch(self)
    class(base), intent(inout) :: self
  end subroutine touch
  subroutine accept(value)
    class(base), intent(in) :: value
  end subroutine accept
end module polymorphic_source_mod
"""

    module = FortranToIRConverter().visit(parse_fortran_source(source).modules[0])
    touch_self = module.functions[0].arguments[0].semantic_type
    accept_value = module.functions[1].arguments[0].semantic_type

    assert touch_self.origin.source_type == "class(base)"
    assert touch_self.metadata["fortran_polymorphic"] is True
    assert module.functions[0].metadata["fortran_type_bound_target"] is True
    assert module.functions[0].metadata["fortran_passed_object_name"] == "self"
    assert accept_value.origin.source_type == "class(base)"
    assert accept_value.metadata["fortran_polymorphic"] is True
