"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

from tests._shared.pyi_conversion_support import (
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
    complete_semantic_policies,
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
    re,
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


def test_convert_pyi_to_ir_rejects_immutable_writable_borrowed_view_argument():
    with pytest.raises(ValueError, match="Immutable values cannot request"):
        parse_pyi_text(
            """
def normalize(
    values: Annotated[Float64[:], Immutable, Transfer("borrowed_view")]
) -> None: ...
""",
            module_name="invalid_immutable_view",
        )


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


def test_convert_pyi_to_ir_accepts_mutable_module_literal_defaults():
    source = """counter: Int32 = 41
scale: Float64 = 2.5
label: String[8] = "ready"
"""

    module = parse_pyi_text(source, module_name="runtime_state")

    assert [variable.default_value for variable in module.variables[:2]] == ["41", "2.5"]
    assert ast.literal_eval(module.variables[2].default_value) == "ready"


@pytest.mark.parametrize(
    "source",
    [
        "counter: Int32 = f(42)\n",
        "counter: Int32 = x + 1\n",
        "counter: Int32 = SOME_NAME\n",
    ],
)
def test_convert_pyi_to_ir_rejects_mutable_module_expression_defaults(source):
    with pytest.raises(ValueError, match="Mutable defaults must be literal values"):
        parse_pyi_text(source, module_name="runtime_state")


def test_convert_pyi_to_ir_round_trips_enum_like_integer_constants():
    source = """STATUS_OK: Final[Int] = 0
STATUS_NEXT: Final[Int] = STATUS_OK + 1

def set_status(
    value: Int
) -> None: ...
"""

    module = parse_pyi_text(source, module_name="status_api")

    assert module.classes == []
    assert [item.name for item in module.variables] == ["STATUS_OK", "STATUS_NEXT"]
    assert module.variables[1].default_value == "STATUS_OK + 1"
    assert module.functions[0].arguments[0].semantic_type.name == "Int"
    emitted = emit_module(module)
    assert "STATUS_NEXT: Final[Int] = STATUS_OK + 1" in emitted
    assert parse_pyi_text(emitted, module_name="status_api") == module


def test_convert_pyi_to_ir_uses_value_default_and_explicit_reference_callbacks():
    module = parse_pyi_text(
        """
class particle:
    mass: Float64

@prototype
def callback_shape(
    value: Int32,
    scalar_ref: Addr(Float64),
    values: Float64[:],
    scalar_storage: Float64[()],
    scalar_value: Float64,
    count_ref: Addr(Int32),
    derived_value: Value(particle),
    output: Float64[:],
    result_storage: Float64[()],
) -> None: ...

def register(
    callback: callback_shape
) -> None: ...
""",
        module_name="callbacks",
    )

    callback_type = module.functions[0].arguments[0].semantic_type
    callback_arguments = callback_type.metadata["callback_arguments"]

    assert [arg.origin.metadata["value"] for arg in callback_arguments] == [
        True,
        False,
        False,
        False,
        True,
        False,
        True,
        False,
        False,
    ]
    assert callback_arguments[0].semantic_type.storage is None
    assert callback_arguments[1].semantic_type.storage.kind == "reference"
    assert callback_arguments[2].semantic_type.storage.kind == "array"
    assert callback_arguments[3].semantic_type.storage.kind == "array"
    assert callback_arguments[4].semantic_type.storage is None
    assert callback_arguments[5].semantic_type.storage.kind == "reference"
    assert callback_arguments[6].semantic_type.storage is None
    assert callback_arguments[7].semantic_type.storage.mutable is True
    assert callback_arguments[8].semantic_type.storage.mutable is True


@pytest.mark.parametrize(
    "annotation",
    [
        "String[8]",
        "String[8][()]",
    ],
)
def test_callback_string_storage_contracts_complete(annotation: str):
    module = parse_pyi_text(
        f"""
@prototype
def string_callback(value: {annotation}) -> None: ...

def register(callback: string_callback) -> None: ...
""",
        module_name="callbacks",
    )

    complete_semantic_policies(module)
    callback_type = module.functions[0].arguments[0].semantic_type
    callback_argument = callback_type.metadata["callback_arguments"][0]
    assert callback_argument.semantic_type.name == "String"


def test_convert_pyi_to_ir_preserves_prototype_argument_names_and_dimensions():
    module = parse_pyi_text(
        """
@prototype
def transform_callback(
    count: Int32,
    values: Float64[count],
) -> Float64[count]: ...

def apply_transform(
    callback: transform_callback
) -> None: ...
""",
        module_name="callbacks",
    )

    callback_type = module.functions[0].arguments[0].semantic_type
    callback_arguments = callback_type.metadata["callback_arguments"]
    assert [arg.name for arg in callback_arguments] == ["count", "values"]
    assert callback_type.metadata["return"].shape == ["count"]
    assert callback_type.metadata["prototype_ref"]["name"] == "transform_callback"


def test_imported_prototype_resolves_as_module_interface_definition(tmp_path):
    from x2py.pipeline.pyi import pyi_paths_to_semantic_modules
    from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner

    (tmp_path / "callback_shapes.pyi").write_text(
        """from x2py.contracts import Float64, Int32, prototype

@prototype
def transform(count: Int32, values: Float64[count]) -> Float64[count]: ...
""",
        encoding="utf-8",
    )
    (tmp_path / "api.pyi").write_text(
        """from x2py.contracts import Float64, Int32
from .callback_shapes import transform

def apply(callback: transform, count: Int32, values: Float64[count]) -> None: ...
""",
        encoding="utf-8",
    )

    modules = {module.name: module for module in pyi_paths_to_semantic_modules(tmp_path)}
    api = modules["api"]
    callback_type = api.functions[0].arguments[0].semantic_type
    assert callback_type.metadata["prototype_ref"] == {
        "name": "transform",
        "local_name": "transform",
        "origin_module": "callback_shapes",
    }

    complete_semantic_policies(api)
    artifacts = WrapperCodeGenerator().generate(WrapperPlanner().build(api))
    bridge = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")
    assert "use callback_shapes, only:" in bridge
    assert "_prototype => transform" in bridge
    assert "procedure(x2py_callback_adapter_callback_" in bridge


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


def test_rank_zero_string_storage_round_trips_as_empty_tuple_array():
    module = parse_pyi_text(
        """
def rewrite_label(label: String[8][()]) -> None: ...
""",
        module_name="string_storage",
    )

    label_type = module.functions[0].arguments[0].semantic_type

    assert label_type.name == "String"
    assert label_type.rank == 0
    assert label_type.shape == []
    assert label_type.metadata["fortran_character_length"] == "8"
    assert label_type.storage.kind == "array"
    assert label_type.storage.array.category == "scalar_storage"

    emitted = emit_module(module)
    assert "label: String[8][()]" in emitted
    assert parse_pyi_text(emitted, module_name="string_storage") == module


def test_string_length_and_shape_axes_round_trip():
    module = parse_pyi_text(
        """
def scalar_unknown(value: String) -> None: ...
def scalar_fixed(value: String[8]) -> None: ...
def array_unknown(values: String[:][:]) -> None: ...
def array_fixed(values: String[8][:]) -> None: ...
def scalar_storage(value: String[8][()]) -> None: ...
""",
        module_name="string_axes",
    )

    scalar_unknown, scalar_fixed, array_unknown, array_fixed, scalar_storage = module.functions

    assert "fortran_character_length" not in scalar_unknown.arguments[0].semantic_type.metadata
    assert scalar_fixed.arguments[0].semantic_type.metadata["fortran_character_length"] == "8"

    array_unknown_type = array_unknown.arguments[0].semantic_type
    assert array_unknown_type.metadata["fortran_character_length"] == ":"
    assert array_unknown_type.rank == 1
    assert array_unknown_type.shape == [":"]
    assert array_unknown_type.storage.kind == "array"

    array_fixed_type = array_fixed.arguments[0].semantic_type
    assert array_fixed_type.metadata["fortran_character_length"] == "8"
    assert array_fixed_type.rank == 1
    assert array_fixed_type.shape == [":"]

    scalar_storage_type = scalar_storage.arguments[0].semantic_type
    assert scalar_storage_type.metadata["fortran_character_length"] == "8"
    assert scalar_storage_type.storage.array.category == "scalar_storage"

    emitted = emit_module(module)
    assert "value: String" in emitted
    assert "value: String[8]" in emitted
    assert "values: String[:][:]" in emitted
    assert "values: String[8][:]" in emitted
    assert "value: String[8][()]" in emitted
    assert parse_pyi_text(emitted, module_name="string_axes") == module


def test_bare_string_slice_is_rejected_as_ambiguous():
    with pytest.raises(ValueError, match=r"String\[:\] is ambiguous.*String\[:\]\[:\].*String\[n\]"):
        parse_pyi_text(
            """
def invalid(value: String[:]) -> None: ...
""",
            module_name="string_axes",
        )


@pytest.mark.parametrize(
    "annotation",
    [
        "Addr(Float64[n])",
        "Addr[2](Float64)",
        "Addr(String[8])",
        "Addr(particle)",
        "Addr(Allocatable[Float64])",
        "Addr(Pointer[Float64])",
    ],
)
def test_convert_pyi_to_ir_rejects_invalid_prototype_address_wrappers(annotation: str):
    with pytest.raises(ValueError, match=r"Addr.*prototype"):
        parse_pyi_text(
            f"class particle:\n    mass: Float64\n\n@prototype\ndef callback(value: {annotation}) -> None: ...",
            module_name="callbacks",
        )


@pytest.mark.parametrize(
    "annotation",
    [
        "Value(Float64)",
        "Value(Int32)",
        "Value(String[8])",
        "Value(Allocatable[Float64])",
        "Value(Pointer[Float64])",
    ],
)
def test_convert_pyi_to_ir_rejects_redundant_or_invalid_prototype_value_wrappers(annotation: str):
    with pytest.raises(ValueError, match=r"Value.*callback"):
        parse_pyi_text(
            f"@prototype\ndef callback(value: {annotation}) -> None: ...",
            module_name="callbacks",
        )


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


def test_convert_pyi_to_ir_uses_the_selected_native_language_array_default():
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
    c = parse_pyi_text(
        """
def consume(
    a: Float64[:, :],
    f: Annotated[Float64[:, :], ORDER_F],
    any_order: Annotated[Float64[:, :], ORDER_ANY]
) -> None: ...
""",
        module_name="c_contract",
        native_language="c",
    )

    fortran_arrays = [arg.semantic_type.storage.array for arg in fortran.functions[0].arguments]
    c_arrays = [arg.semantic_type.storage.array for arg in c.functions[0].arguments]
    assert [array.order for array in fortran_arrays] == ["ORDER_F", "ORDER_C", "ORDER_ANY"]
    assert [array.order for array in c_arrays] == ["ORDER_C", "ORDER_F", "ORDER_ANY"]
    assert fortran_arrays[0].category is None
    assert c_arrays[1].source_shape == []
    assert all(not arg.semantic_type.constraints for arg in fortran.functions[0].arguments)


@pytest.mark.parametrize(
    ("native_language", "order"),
    [("fortran", "ORDER_F"), ("c", "ORDER_C")],
)
def test_convert_pyi_to_ir_rejects_redundant_default_array_order(native_language: str, order: str):
    with pytest.raises(ValueError, match=rf"{order} is implicit for {native_language}"):
        parse_pyi_text(
            f"value: Annotated[Float64[:, :], {order}]\n",
            module_name="redundant_order",
            native_language=native_language,
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


def test_convert_pyi_to_ir_accepts_defaulted_scalar_descriptor_optional_dummies():
    module = parse_pyi_text(
        """
@native_call([Allocatable(Arg(0)), Pointer(Arg(1))])
def update(scale: Float64 | None = ..., current: Float64 | None = ...) -> None: ...
""",
        module_name="optional_scalar_descriptors",
    )

    scale, current = module.functions[0].arguments
    assert scale.optional is True
    assert scale.semantic_type.metadata["fortran_allocatable"] is True
    assert current.optional is True
    assert current.semantic_type.metadata["fortran_pointer"] is True
    assert native_array_descriptor_kind(scale.semantic_type) is None
    assert native_array_descriptor_kind(current.semantic_type) is None


@pytest.mark.parametrize(
    ("annotation", "message"),
    [
        ("Annotated[Float64[:], Allocatable]", "use Allocatable"),
        ("Annotated[Float64[:], Pointer]", "use Pointer"),
    ],
)
def test_convert_pyi_to_ir_rejects_legacy_array_descriptor_metadata(annotation, message):
    with pytest.raises(ValueError, match=message):
        parse_pyi_text(
            f"""
values: {annotation}
""",
            module_name="legacy_array_descriptors",
        )


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            "values: Allocatable[Float64[:]] | None = ...\n",
            "only valid for optional callable arguments",
        ),
        (
            "def make_values() -> Allocatable[Float64[:]] | None: ...\n",
            "only valid for optional callable arguments",
        ),
        (
            "def consume(values: Allocatable[Float64[:]] | None) -> None: ...\n",
            "must use '= ...' or '= None'",
        ),
        (
            "def consume(values: Pointer[Float64[:]] = ...) -> None: ...\n",
            "must use Pointer[T[...]] | None = ...",
        ),
    ],
)
def test_convert_pyi_to_ir_rejects_misplaced_optional_array_handle_none(source, message):
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_pyi_text(source, module_name="invalid_optional_array_handle")


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
        ("value: Addr(Int32, Float64)\n", "Addr type expects one argument: 'Addr(Int32, Float64)'"),
        ("value: Addr[1](Int32)\n", "Addr[1](...) is invalid; use Addr(...)"),
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
