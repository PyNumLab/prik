"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

from tests.fortran._support.pyi_conversion import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_RAW,
    NATIVE_ARRAY_DESCRIPTOR_METADATA,
    OPTIONAL_ABSENT_HANDLE_METADATA,
    PYTHON_VALUE_IMMUTABLE,
    PYTHON_VALUE_MUTABILITY_METADATA,
    SemanticConstraint,
    SemanticField,
    SemanticVariable,
    USER_PRIVATE_METADATA,
    _node_text,
    ast,
    emit_module,
    fortran_file_to_semantic_modules,
    is_native_array_handle,
    native_array_data_type,
    native_array_descriptor_kind,
    native_array_handle_facts,
    native_contract_issues,
    parse_fortran_file,
    parse_pyi_text,
    pyi_text_to_semantic_module,
    pytest,
)


def test_convert_pyi_to_ir_dispatches_nested_and_qualified_semantic_types():
    module = parse_pyi_text(
        """
public_value: Int32
bounded: Final[Annotated[Int32, Bounded(1, 8)]]
pointer: Addr(Float64)
raw_pointer: Addr(Float64)
""",
        module_name="dispatch",
    )

    public_value, bounded, pointer, raw_pointer = module.variables
    assert isinstance(public_value, SemanticVariable)
    assert public_value.visibility == "public"
    assert bounded.semantic_type.constraints == [
        SemanticConstraint("Bounded", [1, 8]),
        SemanticConstraint("Constant"),
    ]
    assert pointer.semantic_type.storage.kind == "address"
    assert pointer.semantic_type.storage.metadata[ADDRESS_ROLE_METADATA] == ADDRESS_ROLE_RAW
    assert raw_pointer.semantic_type.storage.read_only is False


def test_value_projection_round_trips_as_argument_specific_native_transport():
    module = parse_pyi_text(
        """
from x2py.contracts import Arg, Float64, Value, native_call, native_type

@native_type(attributes=("bind(c)",))
class point:
    x: Float64

@native_call([Value(Arg(0))])
def score(value: point) -> Float64: ...
""",
        module_name="value_contract",
    )

    value = module.functions[0].arguments[0]
    assert value.metadata["native_by_value"] is True
    assert "@native_call([Value(Arg(0))])" in emit_module(module)
    assert "value: point" in emit_module(module)


def test_convert_pyi_to_ir_follows_arbitrary_contract_aliases():
    module = pyi_text_to_semantic_module(
        """
from x2py.contracts import Addr as AddressOf, Arg as PythonArg, Final as Frozen
from x2py.contracts import Flat as Layout, Float64 as F64, Int32 as I32, native_call as call

Flat: Frozen[I32] = 10

@call([AddressOf(PythonArg(0))])
def inspect(values: F64[Layout], dense: F64[Flat]) -> None: ...
""",
        module_name="aliases",
    )

    assert module.variables[0].name == "Flat"
    assert module.functions[0].arguments[0].semantic_type.storage.array.category == "assumed_size"
    assert module.functions[0].arguments[1].semantic_type.shape == ["Flat"]


def test_convert_pyi_to_ir_preserves_immutable_python_value_metadata():
    module = parse_pyi_text(
        """
def scale(
    values: Annotated[Float64[:], Immutable]
) -> Returns["values", Float64[:]]: ...
""",
        module_name="immutable_values",
    )

    values = module.functions[0].arguments[0].semantic_type
    assert values.metadata[PYTHON_VALUE_MUTABILITY_METADATA] == PYTHON_VALUE_IMMUTABLE

    emitted = emit_module(module)
    assert "Immutable" in emitted
    reparsed = parse_pyi_text(emitted, module_name="immutable_values")
    reparsed_values = reparsed.functions[0].arguments[0].semantic_type
    assert reparsed_values.metadata[PYTHON_VALUE_MUTABILITY_METADATA] == PYTHON_VALUE_IMMUTABLE


def test_convert_pyi_to_ir_allows_user_modified_stub():
    pyi = """
import iso_c_binding

class particle:
    id: Int32

scale: private[Float64]
answer: Final[Int32]
hidden_answer: private[Final[Int32]]
literal_answer: Final[Int32] = 42

def touch(
    p: particle
) -> Returns["p", particle]: ...
"""

    module = parse_pyi_text(pyi, module_name="edited")

    assert module.name == "edited"
    assert module.imports == ["iso_c_binding"]
    assert module.classes[0].name == "particle"
    assert isinstance(module.classes[0].fields[0], SemanticField)
    assert module.variables[0].name == "scale"
    assert module.variables[0].visibility == "private"
    assert module.variables[1].name == "answer"
    assert [c.name for c in module.variables[1].semantic_type.constraints] == ["Constant"]
    assert module.variables[2].name == "hidden_answer"
    assert module.variables[2].visibility == "private"
    assert [c.name for c in module.variables[2].semantic_type.constraints] == ["Constant"]
    assert module.variables[3].name == "literal_answer"
    assert module.variables[3].default_value == "42"


def test_convert_pyi_to_ir_forwards_filename_to_syntax_errors():
    with pytest.raises(SyntaxError) as error:
        parse_pyi_text("from broken import\n", filename="custom.pyi")
    assert error.value.filename == "custom.pyi"


def test_convert_pyi_to_ir_accepts_aliased_contract_wrapper_names():
    module = pyi_text_to_semantic_module(
        """
from x2py.contracts import Annotated as Metadata, Float64 as F64, SourceName as NativeName
from x2py.contracts import Returns as Gives

alias: Metadata[F64[1:n], NativeName("native_alias")]

def f() -> tuple[F64, Gives["y", F64]]: ...
""",
        module_name="edited",
    )

    assert module.variables[0].name == "native_alias"
    assert module.variables[0].semantic_type.shape == ["1:n"]
    assert module.functions[0].return_type is not None
    assert module.functions[0].return_type.name == "Float64"
    assert module.functions[0].arguments[0].name == "y"


def test_rank_zero_scalar_storage_round_trips_as_empty_tuple_array():
    module = parse_pyi_text(
        """
def update_storage(value: Float64[()]) -> None: ...
def inspect_storage(value: Int32[()]) -> None: ...
""",
        module_name="scalar_storage",
    )

    update, inspect = module.functions
    update_type = update.arguments[0].semantic_type
    inspect_type = inspect.arguments[0].semantic_type

    assert update_type.rank == 0
    assert update_type.storage.kind == "array"
    assert update_type.storage.array.category == "scalar_storage"
    assert inspect_type.storage.read_only is False
    assert inspect_type.storage.mutable is True

    emitted = emit_module(module)
    assert "value: Float64[()]" in emitted
    assert "value: Int32[()]" in emitted
    assert parse_pyi_text(emitted, module_name="scalar_storage") == module


def test_convert_pyi_to_ir_preserves_explicit_array_source_dimensions():
    module = parse_pyi_text(
        """
def apply(
    A: Float64[LDA, N],
    work: Float64[::],
    scratch: Float64[:]
) -> None: ...
""",
        module_name="explicit_dims",
    )

    args = {arg.name: arg.semantic_type.storage.array for arg in module.functions[0].arguments}
    assert args["A"].source_shape == ["LDA", "N"]
    assert args["A"].lower_bounds == [None, None]
    assert args["A"].upper_bounds == [None, None]
    assert args["work"].shape == ["::Strided"]
    assert args["work"].axes == ["strided"]
    assert args["work"].contiguous is False
    assert args["work"].source_shape == []
    assert args["scratch"].shape == [":"]
    assert args["scratch"].axes == ["dense"]
    assert args["scratch"].contiguous is True
    assert args["scratch"].source_shape == []


def test_convert_pyi_to_ir_accepts_explicit_strided_marker_for_edited_contracts():
    module = parse_pyi_text(
        """
current: Float64[::]
explicit: Float64[::Strided]
bounded: Float64[0:n:]
explicit_bounded: Float64[0:n:Strided]
""",
        module_name="strided_axes",
    )

    arrays = [variable.semantic_type.storage.array for variable in module.variables]
    assert [array.shape for array in arrays] == [["::Strided"], ["::Strided"], ["0:n:Strided"], ["0:n:Strided"]]
    assert [array.axes for array in arrays] == [["strided"], ["strided"], ["strided"], ["strided"]]
    assert [array.contiguous for array in arrays] == [False, False, False, False]


def test_convert_pyi_to_ir_uses_fortran_native_array_defaults():
    fortran = parse_pyi_text(
        """
def consume(
    a: Float64[:, :],
    c: Annotated[Float64[:, :], ORDER_C],
    any_order: Annotated[Float64[:, :], ORDER_ANY]
) -> None: ...
""",
        module_name="fortran_contract",
    )
    fortran_arrays = [arg.semantic_type.storage.array for arg in fortran.functions[0].arguments]
    assert [array.order for array in fortran_arrays] == ["ORDER_F", "ORDER_C", "ORDER_ANY"]
    assert fortran_arrays[0].category is None
    assert all(not arg.semantic_type.constraints for arg in fortran.functions[0].arguments)


def test_convert_pyi_to_ir_rejects_redundant_fortran_default_array_order():
    with pytest.raises(ValueError, match="ORDER_F is implicit for fortran"):
        parse_pyi_text(
            "value: Annotated[Float64[:, :], ORDER_F]\n",
            module_name="redundant_order",
            native_language="fortran",
        )


def test_convert_pyi_to_ir_records_explicit_c_to_fortran_copy_order():
    module = parse_pyi_text(
        """
def consume(values: Annotated[Float64[:, :], ORDER_C, COPY_F]) -> None: ...
""",
        module_name="copy_order",
    )

    array = module.functions[0].arguments[0].semantic_type.storage.array

    assert array.order == "ORDER_C"
    assert array.copy_order == "ORDER_F"
    assert array.rank == 2
    assert array.contiguous is True


def test_convert_pyi_to_ir_accepts_flat_array_dimension():
    module = parse_pyi_text(
        """
flat: Float64[Flat]
matrix: Float64[3, Flat]
tensor: Float64[3, 4, Flat]
c_matrix: Annotated[Float64[Flat, 3], ORDER_C]
c_tensor: Annotated[Float64[Flat, 3, 4], ORDER_C]
""",
        module_name="flat_arrays",
    )

    arrays = [variable.semantic_type.storage.array for variable in module.variables]
    assert [variable.semantic_type.shape for variable in module.variables] == [
        [":"],
        ["3", ":"],
        ["3", "4", ":"],
        [":", "3"],
        [":", "3", "4"],
    ]
    assert [array.category for array in arrays] == [
        "assumed_size",
        "assumed_size",
        "assumed_size",
        "assumed_size",
        "assumed_size",
    ]
    assert [array.source_shape for array in arrays] == [
        ["*"],
        ["3", "*"],
        ["3", "4", "*"],
        ["*", "3"],
        ["*", "3", "4"],
    ]
    assert [array.upper_bounds for array in arrays] == [
        ["*"],
        [None, "*"],
        [None, None, "*"],
        ["*", None],
        ["*", None, None],
    ]
    assert [array.order for array in arrays] == [None, "ORDER_F", "ORDER_F", "ORDER_C", "ORDER_C"]


def test_convert_pyi_to_ir_preserves_extended_array_metadata_and_nested_selector():
    module = parse_pyi_text(
        """
value: Annotated[Float64[:, :], Contiguous, ArrayCategory("deferred_shape")]
nested: Float64[:, :][rank, kind]
name: Annotated[String[16], FortranAllocatable]

def fill(x: Float64[:]) -> None: ...
""",
        module_name="metadata",
    )

    value_type = module.variables[0].semantic_type
    value = value_type.storage.array
    nested = module.variables[1].semantic_type
    name = module.variables[2].semantic_type
    assert value.order == "ORDER_F"
    assert value.allocatable is False
    assert value.pointer is False
    assert value.contiguous is True
    assert value.category == "deferred_shape"
    assert value.source_shape == []
    assert value.lower_bounds == []
    assert value.upper_bounds == []
    assert value_type.constraints == []
    assert nested.metadata["rank_selector"] == "rank, kind"
    assert nested.storage.array.metadata["rank_selector"] == "rank, kind"
    assert name.metadata["fortran_character_length"] == "16"
    assert name.metadata["fortran_allocatable"] is True


def test_convert_pyi_to_ir_accepts_array_descriptor_handle_wrappers():
    module = pyi_text_to_semantic_module(
        """
from x2py.contracts import Allocatable as A, Annotated, Float64 as F64, Pointer as P, SourceName, String as Str

values: A[F64[:]]
target: Annotated[P[F64[:, :]], SourceName("target_values")]
labels: P[Str[8][:]]
plain_values: F64[:]

def consume(values: A[F64[:]], target: P[F64[:]]) -> None: ...
def maybe_consume(values: A[F64[:]] | None = ..., target: P[F64[:]] | None = ...) -> None: ...
""",
        module_name="array_descriptors",
    )

    values, target, labels, plain_values = [variable.semantic_type for variable in module.variables]
    assert is_native_array_handle(values) is True
    assert native_array_descriptor_kind(values) == "allocatable"
    assert values.storage.array.allocatable is True
    assert values.storage.array.pointer is False
    assert values.metadata[NATIVE_ARRAY_DESCRIPTOR_METADATA] == "allocatable"
    assert values.rank == 1
    assert values.shape == [":"]
    values_data = native_array_data_type(values)
    assert values_data.storage.array.allocatable is False
    assert values_data.storage.array.pointer is False
    assert values_data.metadata.get(NATIVE_ARRAY_DESCRIPTOR_METADATA) is None
    assert values_data == plain_values
    assert is_native_array_handle(plain_values) is False

    assert target.storage.array.pointer is True
    assert native_array_descriptor_kind(target) == "pointer"
    assert target.metadata[NATIVE_ARRAY_DESCRIPTOR_METADATA] == "pointer"
    assert target.rank == 2
    target_data = native_array_data_type(target)
    assert target_data.storage.array.pointer is False
    assert target_data.rank == target.rank

    assert native_array_descriptor_kind(labels) == "pointer"
    assert labels.name == "String"
    assert labels.rank == 1
    assert labels.shape == [":"]
    assert labels.metadata["fortran_character_length"] == "8"
    assert labels.storage.array.pointer is True
    labels_data = native_array_data_type(labels)
    assert labels_data.metadata["fortran_character_length"] == "8"

    values_facts = native_array_handle_facts(values)
    assert values_facts.descriptor_kind == "allocatable"
    assert values_facts.data_type == plain_values
    assert values_facts.element_type.name == "Float64"
    assert values_facts.element_type.rank == 0
    assert values_facts.element_type.shape == []
    assert values_facts.dtype == "Float64"
    assert values_facts.rank == 1
    assert values_facts.shape == (":",)
    assert values_facts.fortran_character_length is None

    target_facts = native_array_handle_facts(target)
    assert target_facts.descriptor_kind == "pointer"
    assert target_facts.data_type.storage.array.pointer is False
    assert target_facts.rank == 2
    assert target_facts.shape == (":", ":")

    labels_facts = native_array_handle_facts(labels)
    assert labels_facts.descriptor_kind == "pointer"
    assert labels_facts.element_type.name == "String"
    assert labels_facts.element_type.rank == 0
    assert labels_facts.element_type.metadata["fortran_character_length"] == "8"
    assert labels_facts.data_type.storage.array.pointer is False
    assert labels_facts.dtype == "String"
    assert labels_facts.rank == 1
    assert labels_facts.shape == (":",)
    assert labels_facts.fortran_character_length == "8"

    with pytest.raises(ValueError, match="is not a native array handle"):
        native_array_handle_facts(plain_values)
    assert labels_data.storage.array.pointer is False

    consume_values, consume_target = [arg.semantic_type for arg in module.functions[0].arguments]
    assert consume_values.storage.array.allocatable is True
    assert consume_target.storage.array.pointer is True

    maybe_values, maybe_target = module.functions[1].arguments
    assert maybe_values.semantic_type.metadata[NATIVE_ARRAY_DESCRIPTOR_METADATA] == "allocatable"
    assert maybe_values.semantic_type.metadata[OPTIONAL_ABSENT_HANDLE_METADATA] is True
    assert maybe_values.optional is True
    assert maybe_target.semantic_type.metadata[NATIVE_ARRAY_DESCRIPTOR_METADATA] == "pointer"
    assert maybe_target.semantic_type.metadata[OPTIONAL_ABSENT_HANDLE_METADATA] is True
    assert maybe_target.optional is True


def test_convert_pyi_to_ir_preserves_user_private_bound_function_contract():
    module = parse_pyi_text(
        """
@private
@bind("native_helper")
def helper(value: Int32) -> None: ...
""",
        module_name="edited",
    )

    helper = module.functions[0]
    assert native_contract_issues(module) == []
    assert helper.visibility == "private"
    assert helper.origin.source_language == "fortran"
    assert helper.origin.metadata[USER_PRIVATE_METADATA] is True

    emitted = emit_module(module)
    assert '@private\n@bind("native_helper")\ndef helper(' in emitted
    assert "    value: Int32" in emitted
    assert parse_pyi_text(emitted, module_name="edited") == module


@pytest.mark.parametrize(
    "source, message",
    [
        (
            "value: Float64[ORDER_F]\n",
            "Non-dimensional type subscriptions are not supported; use Final[...] for constants and "
            "Annotated[...] for constraints or array metadata",
        ),
        (
            "value: Float64[3, Flat, 4]\n",
            "Flat must appear exactly once at the first or final concrete array dimension",
        ),
        (
            "value: Float64[3, Flat, Flat]\n",
            "Flat must appear exactly once at the first or final concrete array dimension",
        ),
        (
            "value: Annotated[Float64[Flat, 3], ORDER_F]\n",
            "ORDER_F conflicts with ORDER_C implied by Flat placement",
        ),
        (
            "value: Annotated[Float64[3, Flat], ORDER_C]\n",
            "ORDER_C conflicts with ORDER_F implied by Flat placement",
        ),
        (
            "value: Annotated[Float64[:, :], COPY_F]\n",
            "COPY_F requires a C-order Python array and targets Fortran order",
        ),
        (
            "value: Annotated[Float64[:], COPY_F]\n",
            "COPY_F requires a concrete multidimensional array rank",
        ),
        (
            "value: Annotated[Float64[::, ::], ORDER_C, COPY_F]\n",
            "COPY_F initially supports only dense concrete-shape arrays",
        ),
        (
            "value: Annotated[Int32, Bounded(lower=1)]\n",
            "Constraint metadata expects positional arguments only: 'Bounded(lower=1)'",
        ),
        ("value: Annotated[Int32, 'bad']\n", "Unsupported Annotated metadata: \"'bad'\""),
        ("value: Float64[:, foo.bar]\n", "Unsupported array dimension expression: 'foo.bar'"),
        (
            "@native_call([Arg(0).other[0]])\ndef f(x: Int32) -> None: ...\n",
            "native_call expects projection entry calls",
        ),
    ],
)
def test_convert_pyi_to_ir_rejects_additional_invalid_storage_forms(source: str, message: str):
    with pytest.raises(ValueError) as error:
        parse_pyi_text(source, module_name="invalid")
    assert str(error.value) == message


def test_node_text_falls_back_to_node_type_for_empty_unparse():
    assert _node_text(ast.Module(body=[], type_ignores=[])) == "Module"


def test_native_contract_structurally_accepts_declared_type_and_constraint_edits():
    parsed = parse_fortran_file(
        """
module solver_mod
contains
  function solve(value) result(result)
    real(8), intent(in) :: value
    real(8) :: result
  end function solve
end module solver_mod
"""
    )
    generated = emit_module(fortran_file_to_semantic_modules(parsed)[0])
    constrained = generated.replace(
        "from x2py.contracts import ",
        "from x2py.contracts import Annotated, Finite, ",
        1,
    ).replace("value: Float64", "value: Annotated[Float64, Finite]", 1)
    changed_abi = generated.replace(
        "from x2py.contracts import ",
        "from x2py.contracts import Int32, ",
        1,
    ).replace("value: Float64", "value: Int32", 1)

    assert native_contract_issues(parse_pyi_text(constrained, module_name="solver_mod")) == []
    assert native_contract_issues(parse_pyi_text(changed_abi, module_name="solver_mod")) == []
