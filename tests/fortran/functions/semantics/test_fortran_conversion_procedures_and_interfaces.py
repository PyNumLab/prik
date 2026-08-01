"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from tests.fortran._support.semantic_conversion import (
    FortranProcedureSignature,
    FortranToIRConverter,
    ProjectionMapping,
    SemanticArgument,
    SemanticFunction,
    SemanticMethod,
    SemanticType,
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
    get_function,
    parse_fortran_source,
    semantic_models,
)


def test_bind_c_name_and_value_calling_convention_reach_semantic_ir():
    parsed = parse_fortran_source(
        """
module c_api
  use iso_c_binding
contains
  integer(c_int) function renamed(n) bind(C, name="prik_renamed") result(res)
    integer(c_int), value, intent(in) :: n
    res = n
  end function renamed
end module c_api
"""
    )

    module = fortran_module_to_semantic_module(parsed.modules[0])
    renamed = get_function(module, "renamed")

    assert renamed.metadata["fortran_bind_c"] is True
    assert renamed.metadata["fortran_bind_c_name"] == "prik_renamed"
    assert renamed.arguments[0].origin.metadata["value"] is True
    assert renamed.arguments[0].semantic_type.storage is None


def test_converter_preserves_abstract_and_deferred_type_facts_for_policy_completion():
    source = """
module abstract_mod
  type, abstract :: shape
  contains
    procedure, deferred :: area
  end type shape
end module abstract_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))

    assert module.classes[0].metadata["fortran_type_attributes"] == ["abstract"]
    assert module.classes[0].metadata["fortran_deferred_bindings"] == ["area"]


def test_semantic_model_helpers_cover_projection_and_canonical_edge_cases():
    converter = FortranToIRConverter()
    assert (
        converter.first_module([FortranProcedureSignature(name="hidden", kind="subroutine", in_interface=True)]).name
        == ""
    )
    assert FortranToIRConverter._literal_kind_key("kind(1.0q0)") == "16"
    assert FortranToIRConverter._literal_kind_key("kind(1)") is None
    assert SemanticFunction("f") != SemanticMethod("f")
    assert semantic_models._semantic_type_key(None, {}) is None
    assert semantic_models._canonical_expression(
        ["n", ("m",), {"extent": "n + m"}],
        {"n": "$0", "m": "$1"},
    ) == ["$0", ("$1",), {"extent": "$0 + $1"}]

    projection = [
        ProjectionMapping(native_position=0, python_position=1),
        ProjectionMapping(native_position=1, python_position=None),
        ProjectionMapping(native_position=2, result_position=0),
        ProjectionMapping(native_position=3, python_position=None),
        ProjectionMapping(
            native_position=4,
            value_kind="shape",
            value={"value": ["n", ("m",)], "dim": {"extent": "n + m"}},
        ),
    ]

    key = semantic_models._projection_key(projection, {"n": "$0", "m": "$1"})

    assert len(key) == len(projection)
    assert key[-1][4] == (("dim", (("extent", "$0 + $1"),)), ("value", ("$0", ("$1",))))


def test_scalar_descriptors_record_native_projection_kind():
    source = """
module scalar_descriptor_mod
contains
subroutine update_allocatable(value)
    real(8), allocatable, intent(inout) :: value
end subroutine update_allocatable

subroutine create_pointer(value)
    real(8), pointer, intent(out) :: value
end subroutine create_pointer
end module scalar_descriptor_mod
"""

    smod = fortran_module_to_semantic_module(parse_fortran_source(source))
    update = get_function(smod, "update_allocatable")
    create = get_function(smod, "create_pointer")

    assert update.projection == [
        ProjectionMapping(
            python_name="value",
            native_name="value",
            native_position=0,
            python_position=0,
            result_position=0,
            value_kind="allocatable",
            value={"kind": "arg", "position": 0},
        )
    ]
    assert create.projection == [
        ProjectionMapping(
            python_name="value",
            native_name="value",
            native_position=0,
            python_position=None,
            result_position=0,
            value_kind="pointer",
            value={"kind": "return", "name": "value", "position": 0},
        )
    ]


def test_fortran_file_to_semantic_modules_keeps_standalone_procedures_from_inline_source():
    source = """
subroutine scale(n, x)
  integer, intent(in) :: n
  real(8), intent(inout) :: x(n)
end subroutine scale
"""

    parsed = parse_fortran_source(source)
    modules = fortran_file_to_semantic_modules(parsed)

    assert len(modules) == 1
    assert modules[0].name == "standalone"
    func = get_function(modules[0], "scale")
    assert [arg.name for arg in func.arguments] == ["n", "x"]
    assert func.projection[0].python_position == 0
    assert func.projection[1].python_position == 1
    assert func.projection[1].result_position is None


def test_semantic_function_projection_equality_and_placeholders():
    left = SemanticFunction(
        name="f",
        native_name="f",
        arguments=[
            SemanticArgument("x", SemanticType("Int32", dtype="Int32")),
            SemanticArgument("y", SemanticType("Float64", dtype="Float64")),
        ],
        projection=[ProjectionMapping(native_position=1, result_position=0)],
    )
    right = SemanticFunction(
        name="f",
        native_name="f",
        arguments=[
            SemanticArgument("a", SemanticType("Int32", dtype="Int32")),
            SemanticArgument("b", SemanticType("Float64", dtype="Float64")),
        ],
        projection=[ProjectionMapping(native_position=1, result_position=0)],
    )

    assert left == right
