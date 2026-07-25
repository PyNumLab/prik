"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from tests.semantics.conversion.fortran._support import (
    FortranProcedureSignature,
    FortranToIRConverter,
    OPERATOR_F90_SOURCE,
    ProjectionMapping,
    SCALAR_STORAGE_CATEGORY,
    SemanticArgument,
    SemanticFunction,
    SemanticMethod,
    SemanticType,
    array_contract,
    emit_module,
    fortran_file_to_semantic_modules,
    fortran_module_to_semantic_module,
    get_function,
    native_contract_issues,
    parse_fortran_project,
    parse_fortran_source,
    parse_pyi_text,
    pytest,
    semantic_models,
)
from x2py.semantics.metadata import PROJECTED_OUTPUT_METADATA


def test_bind_c_name_and_value_calling_convention_reach_semantic_ir():
    parsed = parse_fortran_source(
        """
module c_api
  use iso_c_binding
contains
  integer(c_int) function renamed(n) bind(C, name="x2py_renamed") result(res)
    integer(c_int), value, intent(in) :: n
    res = n
  end function renamed
end module c_api
"""
    )

    module = fortran_module_to_semantic_module(parsed.modules[0])
    renamed = get_function(module, "renamed")

    assert renamed.metadata["fortran_bind_c"] is True
    assert renamed.metadata["fortran_bind_c_name"] == "x2py_renamed"
    assert renamed.arguments[0].origin.metadata["value"] is True
    assert renamed.arguments[0].semantic_type.storage is None


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


def test_converter_keeps_module_common_block_storage_internal():
    source = """
module common_mod
  public :: value, read_value
  real :: value
  common /shared/ value
contains
  real function read_value()
    read_value = value
  end function read_value
end module common_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))

    assert module.variables == []
    assert [function.name for function in module.functions] == ["read_value"]


def test_converter_allows_procedure_common_block_storage():
    source = """
module procedure_common_mod
contains
  subroutine work()
    real :: value
    common /shared/ value
  end subroutine work
end module procedure_common_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))

    assert [function.name for function in module.functions] == ["work"]


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


def test_optional_argument():
    source = """
module opt_mod

contains

subroutine solve(A, tol)

    real(8), intent(in) :: A(:, :)
    real(8), intent(in), optional :: tol

end subroutine

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    func = get_function(smod, "solve")

    tol = func.arguments[1]

    assert tol.optional is True


def test_optional_scalar_output_remains_visible_scalar_storage():
    source = """
module opt_out_mod
contains
subroutine maybe_status(status)
    integer(4), intent(out), optional :: status
end subroutine maybe_status
end module opt_out_mod
"""

    smod = fortran_module_to_semantic_module(parse_fortran_source(source))

    func = get_function(smod, "maybe_status")
    status = func.arguments[0]

    assert status.optional is True
    assert array_contract(status.semantic_type).category == SCALAR_STORAGE_CATEGORY
    assert func.projection == [
        ProjectionMapping(
            python_name="status",
            native_name="status",
            native_position=0,
            python_position=0,
            result_position=0,
        )
    ]


def test_optional_allocatable_output_remains_visible():
    source = """
module opt_alloc_out_mod
contains
subroutine maybe_values(values)
    real(8), allocatable, intent(out), optional :: values(:)
end subroutine maybe_values
end module opt_alloc_out_mod
"""

    smod = fortran_module_to_semantic_module(parse_fortran_source(source))

    func = get_function(smod, "maybe_values")
    values = func.arguments[0]

    assert values.optional is True
    assert array_contract(values.semantic_type).allocatable is True
    assert func.projection == [
        ProjectionMapping(
            python_name="values",
            native_name="values",
            native_position=0,
            python_position=0,
            result_position=0,
        )
    ]


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


def test_primitive_scalar_inout_stays_visible_and_projects_replacement_return():
    source = """
module outputs
contains
subroutine scale_in_place(value, factor)
    real(8), intent(inout) :: value
    real(8), intent(in) :: factor
    value = factor * value
end subroutine scale_in_place
end module outputs
"""

    smod = fortran_module_to_semantic_module(parse_fortran_source(source))
    scale = get_function(smod, "scale_in_place")

    assert scale.arguments[0].metadata[PROJECTED_OUTPUT_METADATA] is True
    assert scale.projection == [
        ProjectionMapping(
            python_name="value",
            native_name="value",
            native_position=0,
            python_position=0,
            result_position=0,
        ),
        ProjectionMapping(
            python_name="factor",
            native_name="factor",
            native_position=1,
            python_position=1,
        ),
    ]


def test_function_result():
    source = """
module func_mod

contains

function norm2(x) result(r)

    real(8), intent(in) :: x(:)

    real(8) :: r

end function

end module
"""

    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    func = get_function(smod, "norm2")

    assert func.return_type is not None

    assert func.return_type.name == "Float64"


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


def test_procedure_local_derived_type_rename_uses_origin_type_identity():
    parsed = parse_fortran_source(
        """
module physics
contains
  subroutine move(p)
    use a_types, only: local_state => state
    type(local_state), intent(inout) :: p
  end subroutine move
end module physics
"""
    )

    module = fortran_module_to_semantic_module(parsed)
    state = get_function(module, "move").arguments[0].semantic_type

    assert state.name == "a_types.state"
    assert state.metadata["external_type_ref"] == {
        "name": "state",
        "local_name": "a_types.state",
        "origin_module": "a_types",
        "wrapped": False,
        "representation": "opaque",
        "import_scope": "procedure",
    }


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


def test_dummy_procedure_interfaces_become_complete_callable_contracts():
    source = """
module callbacks
  type :: point_t
    real(8) :: x
  end type point_t
    abstract interface
      function transform_iface(count, values, point) result(output)
        import :: point_t
        integer, intent(in) :: count
        real(8), intent(in) :: values(count)
        type(point_t), intent(in) :: point
        real(8) :: output(count)
      end function transform_iface
      subroutine no_intent_iface(count, values)
        integer :: count
        real(8) :: values(count)
      end subroutine no_intent_iface
      subroutine value_iface(value, ref)
        integer, value, intent(in) :: value
        real(8) :: ref
      end subroutine value_iface
      subroutine notify_iface(value)
        integer, intent(in) :: value
      end subroutine notify_iface
      subroutine string_iface(read_label, write_label, update_label)
        character(len=8), intent(in) :: read_label
        character(len=8), intent(out) :: write_label
        character(len=8), intent(inout) :: update_label
      end subroutine string_iface
  end interface
contains
  subroutine abstract_case(callback)
    procedure(transform_iface) :: callback
  end subroutine abstract_case
  subroutine explicit_case(callback)
    interface
      integer function callback(value) result(output)
        integer, intent(in) :: value
      end function callback
    end interface
  end subroutine explicit_case
  subroutine notify_case(callback)
    procedure(notify_iface) :: callback
  end subroutine notify_case
  subroutine no_intent_case(callback)
    procedure(no_intent_iface) :: callback
  end subroutine no_intent_case
  subroutine value_case(callback)
    procedure(value_iface) :: callback
  end subroutine value_case
  subroutine string_case(callback)
    procedure(string_iface) :: callback
  end subroutine string_case
end module callbacks
"""
    module = FortranToIRConverter().visit(parse_fortran_source(source).modules[0])

    abstract_callback = get_function(module, "abstract_case").arguments[0].semantic_type
    assert abstract_callback.name == "transform_iface"
    assert [argument.name for argument in abstract_callback.metadata["callback_arguments"]] == [
        "count",
        "values",
        "point",
    ]
    assert [argument.name for argument in abstract_callback.metadata["arguments"]] == [
        "Int32",
        "Float64",
        "point_t",
    ]
    assert abstract_callback.metadata["arguments"][1].shape == ["count"]
    assert abstract_callback.metadata["return"].name == "Float64"
    assert abstract_callback.metadata["return"].shape == ["count"]
    assert abstract_callback.metadata["callback_lifetime"] == "call"
    assert abstract_callback.metadata["callback_thread"] == "entering_thread"
    assert abstract_callback.metadata["callback_exception"] == "print_traceback_and_abort"
    assert all(
        argument.semantic_type.storage is not None for argument in abstract_callback.metadata["callback_arguments"]
    )

    explicit_callback = get_function(module, "explicit_case").arguments[0].semantic_type
    assert explicit_callback.name == "callback"
    assert [argument.name for argument in explicit_callback.metadata["arguments"]] == ["Int32"]
    assert explicit_callback.metadata["return"].name == "Int32"

    notify_callback = get_function(module, "notify_case").arguments[0].semantic_type
    assert notify_callback.metadata["return"].name == "None"

    no_intent_callback = get_function(module, "no_intent_case").arguments[0].semantic_type
    assert all(argument.semantic_type.storage.mutable for argument in no_intent_callback.metadata["callback_arguments"])

    value_callback = get_function(module, "value_case").arguments[0].semantic_type
    assert [argument.name for argument in value_callback.metadata["callback_arguments"]] == ["value", "ref"]
    assert [argument.origin.metadata["value"] for argument in value_callback.metadata["callback_arguments"]] == [
        True,
        False,
    ]

    string_callback = get_function(module, "string_case").arguments[0].semantic_type
    assert all(
        argument.semantic_type.storage.array.category == "scalar_storage"
        for argument in string_callback.metadata["callback_arguments"]
    )

    emitted = emit_module(module)
    assert "@prototype\ndef transform_iface(" in emitted
    assert "callback: transform_iface" in emitted
    assert "@prototype\ndef value_iface(" in emitted
    assert "value: Int32" in emitted
    assert "ref: Addr(Float64)" in emitted
    assert "@prototype\ndef string_iface(" in emitted
    assert "read_label: String[8]" in emitted
    assert native_contract_issues(parse_pyi_text(emitted, module_name=module.name)) == []

    project = parse_fortran_project(
        {
            "callback_types.f90": """
module callback_types
  abstract interface
    integer function unary(value) result(output)
      integer, intent(in) :: value
    end function unary
  end interface
end module callback_types
""",
            "callback_user.f90": """
module callback_user
  use callback_types, only: renamed => unary
contains
  integer function apply(callback, value) result(output)
    procedure(renamed) :: callback
    integer, intent(in) :: value
    output = callback(value)
  end function apply
end module callback_user
""",
        }
    )
    modules = {item.name: item for item in FortranToIRConverter().visit(project)}
    imported_callback = get_function(modules["callback_user"], "apply").arguments[0].semantic_type
    assert imported_callback.name == "renamed"
    assert [argument.name for argument in imported_callback.metadata["arguments"]] == ["Int32"]
    assert imported_callback.metadata["return"].name == "Int32"

    standalone = parse_fortran_source(
        """
subroutine standalone_case(callback)
  interface
    integer function callback(value) result(output)
      integer, intent(in) :: value
    end function callback
  end interface
end subroutine standalone_case
"""
    )
    standalone_module = FortranToIRConverter().visit(standalone)[0]
    standalone_callback = get_function(standalone_module, "standalone_case").arguments[0].semantic_type
    assert standalone_callback.name == "callback"
    assert [argument.name for argument in standalone_callback.metadata["arguments"]] == ["Int32"]
    assert standalone_callback.metadata["return"].name == "Int32"
