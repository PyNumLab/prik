"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

from tests.fortran._support.pyi_conversion import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_PROJECTION,
    CONTRACT_SYMBOLS,
    PROJECTED_OUTPUT_METADATA,
    ProjectionMapping,
    SemanticArgument,
    SemanticConstraint,
    SemanticFunction,
    SemanticModule,
    SemanticType,
    _PyiAstParser,
    asdict,
    ast,
    complete_semantic_policies,
    emit_module,
    fortran_file_to_semantic_modules,
    parse_fortran_file,
    parse_pyi_text,
    pytest,
)


def test_convert_pyi_to_ir_accepts_ast_only_projection_value_refs():
    module = parse_pyi_text(
        """
@native_call([Return(0), Len(Return(0)), Work("tmp").shape[0]])
def f() -> Float64: ...
""",
        module_name="edited",
    )

    projection = module.functions[0].projection
    assert projection[1].value == {"kind": "return", "position": 0}
    assert projection[2].value == {"value": {"kind": "work", "name": "tmp"}, "dim": 0}


def test_convert_pyi_to_ir_accepts_plain_return_type():
    pyi = """
def make_value(
    x: Float64
) -> Float64: ...
"""

    module = parse_pyi_text(pyi, module_name="edited")

    func = module.functions[0]
    assert func.return_type is not None
    assert func.return_type.name == "Float64"


def test_native_call_address_argument_projection_records_native_address_storage():
    module = parse_pyi_text(
        """
@native_call([Addr(Arg(0))])
def add_one(value: Int32) -> Int32: ...
""",
        module_name="scalar_refs",
    )

    function = module.functions[0]
    value = function.arguments[0]

    assert value.semantic_type.name == "Int32"
    assert value.semantic_type.storage is None
    assert function.projection[0].value_kind == "addr"
    assert function.projection[0].value == {"kind": "arg", "position": 0}

    complete_semantic_policies(module)

    assert value.semantic_type.storage.kind == "address"
    assert value.semantic_type.storage.read_only is False
    assert value.semantic_type.storage.mutable is True
    assert value.semantic_type.storage.metadata[ADDRESS_ROLE_METADATA] == ADDRESS_ROLE_PROJECTION
    assert (
        emit_module(module)
        .strip()
        .endswith("@native_call([Addr(Arg(0))])\ndef add_one(\n    value: Int32\n) -> Int32: ...")
    )


def test_function_equality_treats_argument_names_as_placeholders():
    left = parse_pyi_text(
        """
def resize(
    n: Int32,
    x: Float64[1:n]
) -> None: ...
""",
        module_name="edited",
    )
    right = parse_pyi_text(
        """
def resize(
    extent: Int32,
    values: Float64[1:extent]
) -> None: ...
""",
        module_name="edited",
    )

    assert left == right
    assert left.functions[0].arguments[0] != right.functions[0].arguments[0]


def test_plain_return_type_represents_direct_return_not_output_argument():
    from_pyi = parse_pyi_text(
        """
def add(
    a: Float64,
    b: Float64
) -> Float64: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]
    assert func.return_type.name == "Float64"
    assert [arg.name for arg in func.arguments] == ["a", "b"]


def test_native_call_preserves_unnamed_output_argument_position():
    from_pyi = parse_pyi_text(
        """
@native_call([Arg(0), Arg(1), Return(0)])
def add(
    a: Float64,
    b: Float64
) -> Float64: ...
""",
        module_name="edited",
    )
    from_ir = SemanticModule(
        name="edited",
        functions=[
            SemanticFunction(
                name="add",
                native_name="add",
                arguments=[
                    SemanticArgument("a", SemanticType("Float64", dtype="Float64")),
                    SemanticArgument("b", SemanticType("Float64", dtype="Float64")),
                    SemanticArgument(
                        "c",
                        SemanticType("Float64", dtype="Float64"),
                    ),
                ],
                projection=[
                    ProjectionMapping(
                        native_name="c",
                        native_position=2,
                        result_position=0,
                    )
                ],
            )
        ],
    )

    assert from_pyi != from_ir
    assert from_pyi.functions[0].projection[2].native_position == 2


def test_native_call_return_entry_can_preserve_output_name():
    from_pyi = parse_pyi_text(
        """
@native_call([Arg(0), Arg(1), Return("c", 0)])
def add(
    a: Float64,
    b: Float64
) -> Float64: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]

    assert [arg.name for arg in func.arguments] == ["a", "b", "c"]
    assert func.projection[2].native_name == "c"
    assert func.projection[2].python_name == "c"
    assert func.projection[2].result_position == 0


def test_projected_replacement_without_native_call_keeps_writable_argument_storage():
    from_pyi = parse_pyi_text(
        """
def fixed_inout(
    name: String[8]
) -> Returns["name", String[8]]: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]

    assert func.arguments[0].metadata[PROJECTED_OUTPUT_METADATA] is True
    assert len(func.projection) == 1
    assert func.projection[0].native_position == 0
    assert func.projection[0].python_position == 0
    assert func.projection[0].result_position == 0


def test_native_call_projected_output_keeps_visible_storage_writable():
    from_pyi = parse_pyi_text(
        """
@native_call([Arg(0), Arg(1)])
def fill(
    n: Addr(Int32),
    values: Float64[n]
) -> Returns["values", Float64[n]]: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]

    assert func.projection[1].result_position == 0


def test_native_call_compact_array_output_marks_projection_without_direction_label():
    from_pyi = parse_pyi_text(
        """
@native_call([Arg(0), Arg(1)])
def fill(
    n: Addr(Int32),
    values: Float64[n]
) -> Returns["values", Float64[n]]: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]

    assert func.arguments[1].metadata[PROJECTED_OUTPUT_METADATA] is True
    assert func.projection[1].result_position == 0


def test_native_order_outputs_do_not_get_projected_without_native_call():
    from_pyi = parse_pyi_text(
        """
def solve(
    x: Addr(Float64),
    status: Addr(Int32)
) -> tuple[Float64, Returns["message", String]]: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]

    assert [arg.name for arg in func.arguments] == ["x", "status", "message"]
    assert PROJECTED_OUTPUT_METADATA not in func.arguments[1].metadata
    assert func.arguments[2].metadata[PROJECTED_OUTPUT_METADATA] is True


def test_native_call_return_entry_preserves_optional_pointer_return():
    from_pyi = parse_pyi_text(
        """
@native_call([Arg(0), Return("status", 0)])
def maybe_status(
    base: Addr(Int32)
) -> Addr(Int32) | None: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]
    returned = func.arguments[1]

    assert returned.name == "status"
    assert returned.optional is True
    assert returned.semantic_type.name == "Int32"
    assert returned.semantic_type.storage is not None
    assert returned.semantic_type.storage.kind == "address"
    assert func.projection[1].python_name == "status"


def test_native_call_later_return_entry_preserves_native_position_and_name():
    from_pyi = parse_pyi_text(
        """
@native_call([Arg(0), Return("status", 1), Arg(1)])
def fill(
    values: Float64[n],
    n: Addr(Int32)
) -> tuple[Returns["values", Float64[n]], Addr(Int32)]: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]

    assert [arg.name for arg in func.arguments] == ["values", "status", "n"]
    assert func.projection[1].python_name == "status"
    assert func.projection[1].native_name == "status"
    assert func.projection[1].result_position == 1


def test_native_call_accepts_hidden_native_values():
    module = parse_pyi_text(
        """
@native_call([
    Arg(0),
    Int32(1),
    Float64(0.5),
    Bool(False),
    String[1]("N"),
    Len(Arg(0)),
    Arg(0).shape[0],
    IsPresent(Arg(1)),
    Work("tmp"),
])
def wrapper(
    x: Float64[n],
    b: Vector | None = None
) -> None: ...
""",
        module_name="edited",
    )

    projection = module.functions[0].projection

    assert [asdict(mapping) for mapping in projection] == [
        {
            "python_name": "x",
            "native_name": "x",
            "native_position": 0,
            "python_position": 0,
            "result_position": None,
            "value_kind": "",
            "value": None,
        },
        {
            "python_name": None,
            "native_name": "",
            "native_position": 1,
            "python_position": None,
            "result_position": None,
            "value_kind": "literal",
            "value": {"type": "Int32", "value": 1},
        },
        {
            "python_name": None,
            "native_name": "",
            "native_position": 2,
            "python_position": None,
            "result_position": None,
            "value_kind": "literal",
            "value": {"type": "Float64", "value": 0.5},
        },
        {
            "python_name": None,
            "native_name": "",
            "native_position": 3,
            "python_position": None,
            "result_position": None,
            "value_kind": "literal",
            "value": {"type": "Bool", "value": False},
        },
        {
            "python_name": None,
            "native_name": "",
            "native_position": 4,
            "python_position": None,
            "result_position": None,
            "value_kind": "literal",
            "value": {"type": "String[1]", "value": "N"},
        },
        {
            "python_name": None,
            "native_name": "",
            "native_position": 5,
            "python_position": None,
            "result_position": None,
            "value_kind": "len",
            "value": {"kind": "arg", "position": 0},
        },
        {
            "python_name": None,
            "native_name": "",
            "native_position": 6,
            "python_position": None,
            "result_position": None,
            "value_kind": "shape",
            "value": {"value": {"kind": "arg", "position": 0}, "dim": 0},
        },
        {
            "python_name": None,
            "native_name": "",
            "native_position": 7,
            "python_position": None,
            "result_position": None,
            "value_kind": "is_present",
            "value": {"kind": "arg", "position": 1},
        },
        {
            "python_name": None,
            "native_name": "",
            "native_position": 8,
            "python_position": None,
            "result_position": None,
            "value_kind": "work",
            "value": "tmp",
        },
    ]
    assert projection[1].value_kind == "literal"
    assert projection[1].value == {"type": "Int32", "value": 1}
    assert projection[4].value == {"type": "String[1]", "value": "N"}
    assert projection[5].value_kind == "len"
    assert projection[5].value == {"kind": "arg", "position": 0}
    assert projection[6].value_kind == "shape"
    assert projection[6].value == {"value": {"kind": "arg", "position": 0}, "dim": 0}
    assert projection[7].value_kind == "is_present"
    assert projection[7].value == {"kind": "arg", "position": 1}
    assert projection[8].value_kind == "work"
    assert projection[8].value == "tmp"
    assert module.functions[0].arguments[1].optional


def test_emit_native_call_hidden_native_values():
    module = SemanticModule(
        name="edited",
        functions=[
            SemanticFunction(
                name="wrapper",
                native_name="wrapper",
                arguments=[
                    SemanticArgument("x", SemanticType("Float64", dtype="Float64")),
                    SemanticArgument("b", SemanticType("Vector", dtype="Vector"), optional=True),
                ],
                projection=[
                    ProjectionMapping(native_position=0, python_position=0),
                    ProjectionMapping(
                        native_position=1,
                        value_kind="literal",
                        value={"type": "Int32", "value": 1},
                    ),
                    ProjectionMapping(
                        native_position=2,
                        value_kind="len",
                        value={"kind": "arg", "position": 0},
                    ),
                    ProjectionMapping(
                        native_position=3,
                        value_kind="shape",
                        value={"value": {"kind": "arg", "position": 0}, "dim": 0},
                    ),
                    ProjectionMapping(
                        native_position=4,
                        value_kind="is_present",
                        value={"kind": "arg", "position": 1},
                    ),
                    ProjectionMapping(native_position=5, value_kind="work", value="tmp"),
                ],
            )
        ],
    )

    pyi = emit_module(module)

    assert "@native_call([Arg(0), Int32(1), Len(Arg(0)), Arg(0).shape[0], IsPresent(Arg(1)), Work('tmp')])" in pyi


def test_plain_return_without_native_call_does_not_preserve_native_output_position():
    from_pyi = parse_pyi_text(
        """
def add(
    a: Float64,
    b: Float64
) -> Float64: ...
""",
        module_name="edited",
    )
    with_native_call = SemanticModule(
        name="edited",
        functions=[
            SemanticFunction(
                name="add",
                native_name="add",
                arguments=[
                    SemanticArgument("a", SemanticType("Float64", dtype="Float64")),
                    SemanticArgument("b", SemanticType("Float64", dtype="Float64")),
                    SemanticArgument(
                        "c",
                        SemanticType("Float64", dtype="Float64"),
                    ),
                ],
                projection=[
                    ProjectionMapping(
                        native_name="c",
                        native_position=2,
                        result_position=0,
                    )
                ],
            )
        ],
    )

    assert from_pyi != with_native_call


def test_plain_tuple_return_types_parse_component_returns():
    from_pyi = parse_pyi_text(
        """
def split(
    x: Float64
) -> tuple[Float64, Int32]: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]
    assert func.return_type.name == "Float64"
    assert [arg.name for arg in func.arguments] == ["x", "__return_1"]


def test_return_projection_preserves_multiple_plain_output_components():
    parser = _PyiAstParser(module_name="internal")
    parser._contract_bindings.update({name: name for name in CONTRACT_SYMBOLS})

    return_type, returned = parser.return_projection(ast.parse("tuple[Float64, Int32, Logical]", mode="eval").body)

    assert return_type.name == "Float64"
    assert [asdict(arg) for arg in returned] == [
        asdict(
            SemanticArgument(
                "__return_1",
                SemanticType("Int32", dtype="Int32"),
                metadata={"return_position": 1},
            )
        ),
        asdict(
            SemanticArgument(
                "__return_2",
                SemanticType("Logical", dtype="Logical"),
                metadata={"return_position": 2},
            )
        ),
    ]


def test_non_callable_argument_names_remain_significant():
    assert parse_pyi_text("value: Int32\n", module_name="edited") != parse_pyi_text(
        "other: Int32\n",
        module_name="edited",
    )
    assert parse_pyi_text(
        """
class vector:
    x: Float64
""",
        module_name="edited",
    ) != parse_pyi_text(
        """
class vector:
    y: Float64
""",
        module_name="edited",
    )


@pytest.mark.parametrize(
    "source, message",
    [
        (
            "value: Int32[foo.bar]\n",
            "Non-dimensional type subscriptions are not supported; use Final[...] for constants and "
            "Annotated[...] for constraints or array metadata",
        ),
        ("foo.bar: Int32\n", "Unsupported annotation target: 'foo.bar'"),
        (
            "value: Annotated[Int32, SourceName('x', 'y')]\n",
            "SourceName metadata expects one argument: \"SourceName('x', 'y')\"",
        ),
        ("def f(x: Int32): ...\n", "Unsupported function header: 'def f(x: Int32):'"),
        ("def f(\n    x: Int32,\n): ...\n", "Unterminated callable starting at line 2"),
        ("def f(*x: Int32) -> None: ...\n", "Unsupported function header: 'def f(*x: Int32) -> None:'"),
        ("def f(*, x: Int32) -> None: ...\n", "Unsupported function header: 'def f(*, x: Int32) -> None:'"),
        ("def f(x: Int32, /) -> None: ...\n", "Unsupported function header: 'def f(x: Int32, /) -> None:'"),
        ("def f() -> None:\n    ...\n    ...\n", "Unsupported function header: 'def f() -> None:'"),
        ("def f() -> None: pass\n", "Unsupported function header: 'def f() -> None:'"),
        ("@native_call_bad([])\ndef f(x: Int32) -> None: ...\n", "Unsupported .pyi decorator: 'native_call_bad([])'"),
        ("@bad\nclass C:\n    pass\n", "Unsupported class decorator: 'bad'"),
        ("class C:\n    @bad\n    def f(self) -> None: ...\n", "Unsupported class body decorator: 'bad'"),
        ("@native_call([])\nclass C:\n    pass\n", "Unsupported class decorator: 'native_call([])'"),
        ("@native_call(Arg(0))\ndef f(x: Int32) -> None: ...\n", "native_call expects a list of projection entries"),
        (
            "@native_call([Arg(0)], foo=1)\ndef f(x: Int32) -> None: ...\n",
            "native_call accepts only the optional result keyword",
        ),
        (
            "@native_call([1])\ndef f(x: Int32) -> None: ...\n",
            'native_call hidden literals require typed calls such as Int32(1) or String[1]("N")',
        ),
        ("@native_call([Arg(1)])\ndef f(x: Int32) -> None: ...\n", "native_call argument position is out of range: 1"),
        ("@native_call([Arg()])\ndef f(x: Int32) -> None: ...\n", "Arg expects one positional index"),
        (
            "@native_call([Return()])\ndef f(x: Int32) -> None: ...\n",
            "Return expects one positional index or a name and index",
        ),
        (
            '@native_call([String("N")])\ndef f(x: Int32) -> None: ...\n',
            'native_call string literals require String[length](value), for example String[1]("N")',
        ),
        ("@native_call([Len()])\ndef f(x: Int32) -> None: ...\n", "Len expects one value reference"),
        ("@native_call([IsPresent()])\ndef f(x: Int32) -> None: ...\n", "IsPresent expects one value reference"),
        ("@native_call([Work()])\ndef f(x: Int32) -> None: ...\n", "Work expects one workspace name"),
        (
            "@native_call([Len(1)])\ndef f(x: Int32) -> None: ...\n",
            "Expected Arg(...), Return(...), or Work(...) value reference",
        ),
        (
            "@native_call([Len(Arg(0, 1))])\ndef f(x: Int32) -> None: ...\n",
            "Arg value reference expects one positional argument",
        ),
        (
            "@native_call([Len(Unknown(0))])\ndef f(x: Int32) -> None: ...\n",
            "Expected imported x2py contract helper: 'Unknown'",
        ),
        (
            "def f(x: Int32) -> Returns['x']: ...\n",
            "Returns expects a name and type; use '| None' for nullable returns: \"Returns['x']\"",
        ),
        (
            "def f(x: Int32) -> Returns['x', Int32, Optional]: ...\n",
            "Returns expects a name and type; use '| None' for nullable returns: \"Returns['x', Int32, Optional]\"",
        ),
        ("value: Final[Int32, Float64]\n", "Final expects exactly one type: 'Final[Int32, Float64]'"),
        ("value: Unknown\n", "Unknown semantic type is not allowed in .pyi annotations"),
        ("value: Annotated[()]\n", "Annotated type is empty: 'Annotated[()]'"),
    ],
)
def test_convert_pyi_to_ir_rejects_invalid_projection_and_type_forms(source: str, message: str):
    with pytest.raises(ValueError) as error:
        parse_pyi_text(source, module_name="edited")
    assert str(error.value) == message


def test_fortran_to_pyi_and_back_preserves_mixed_input_output_projection():
    source = """
module solver_mod
contains
  subroutine solve(a, x, b)
    real(8), intent(in) :: a
    real(8), intent(out) :: x
    real(8), intent(in) :: b
  end subroutine solve
end module solver_mod
"""

    parsed = parse_fortran_file(source)
    modules = fortran_file_to_semantic_modules(parsed)
    pyi = "\n\n".join(emit_module(module) for module in modules)
    reparsed = parse_pyi_text(pyi, module_name="solver_mod")

    assert "@native_call([Addr(Arg(0)), Return('x', 0), Addr(Arg(1))])" in pyi
    func = reparsed.functions[0]
    assert func.name == "solve"
    assert [arg.name for arg in func.arguments] == ["a", "x", "b"]


def test_convert_pyi_to_ir_accepts_scalar_descriptor_state_and_callable_projections():
    module = parse_pyi_text(
        """
scratch: Allocatable[Float64]
current: Pointer[Int32]
maybe_value: Float64 | None

@native_call(
    [Allocatable(Arg(0)), Pointer(Arg(1))],
    result=Pointer(Return(0)),
)
def combine(scale: Float64 | None, value: Int32 | None) -> Float64 | None: ...
""",
        module_name="scalar_descriptors",
    )

    scratch, current, maybe_value = [variable.semantic_type for variable in module.variables]
    assert scratch.name == "Float64"
    assert scratch.rank == 0
    assert scratch.storage is None
    assert scratch.metadata["fortran_allocatable"] is True

    assert current.name == "Int32"
    assert current.rank == 0
    assert current.metadata["fortran_pointer"] is True
    assert current.metadata["fortran_pointer_association"] == "runtime"
    assert current.storage.kind == "reference"
    assert current.storage.pointer_depth == 1

    assert maybe_value.name == "Float64 | None"
    assert maybe_value.metadata.get("fortran_allocatable") is None
    assert maybe_value.metadata.get("fortran_pointer") is None

    scale, value = [argument.semantic_type for argument in module.functions[0].arguments]
    result = module.functions[0].return_type
    assert scale.metadata["fortran_allocatable"] is True
    assert value.metadata["fortran_pointer"] is True
    assert result.metadata["fortran_pointer"] is True
    assert [mapping.value_kind for mapping in module.functions[0].projection] == ["allocatable", "pointer"]


def test_convert_pyi_to_ir_accepts_nullable_descriptor_output_and_inout_projections():
    module = parse_pyi_text(
        """
@native_call([
    Allocatable(Arg(0)),
    Pointer(Return("selected", 1)),
])
def update(
    value: Float64 | None,
) -> tuple[
    Returns["value", Float64] | None,
    Returns["selected", Float64] | None,
]: ...
""",
        module_name="descriptor_outputs",
    )

    value, selected = module.functions[0].arguments
    assert value.semantic_type.metadata["fortran_allocatable"] is True
    assert value.metadata[PROJECTED_OUTPUT_METADATA] is True
    assert selected.semantic_type.metadata["fortran_pointer"] is True
    assert selected.metadata[PROJECTED_OUTPUT_METADATA] is True
    assert value.optional is False
    assert selected.optional is False


def test_convert_pyi_to_ir_resolves_aliased_scalar_descriptor_projection_helpers():
    module = parse_pyi_text(
        """
from x2py.contracts import Allocatable as A, Arg as Input, Float64 as F64, Pointer as P, Return as Output, native_call as call

@call([A(Input(0))], result=P(Output(0)))
def convert(value: F64 | None) -> F64 | None: ...
""",
        module_name="aliased_descriptor_projection",
    )

    function = module.functions[0]
    assert function.projection[0].value_kind == "allocatable"
    assert function.arguments[0].semantic_type.metadata["fortran_allocatable"] is True
    assert function.return_type.metadata["fortran_pointer"] is True


def test_convert_pyi_to_ir_handles_pointer_and_array_storage_variants():
    module = parse_pyi_text(
        """
constant: Int32
deep: Addr[3](Float64)
rank_any: Float64[...]
strided: Float64[0:n:]
computed: Float64[size(xl)]
bounded_answer: Final[Annotated[Int32, Bounded(1, 8)]]
nested_answer: Final[Final[Int32]]
""",
        module_name="storage",
    )

    constant, deep, rank_any, strided, computed, bounded, nested = [var.semantic_type for var in module.variables]
    assert constant.storage is None
    assert deep.storage.kind == "pointer"
    assert deep.storage.pointer_depth == 3
    assert deep.storage.read_only is False
    assert deep.storage.mutable is True
    assert rank_any.storage.array.rank == 1
    assert rank_any.storage.array.category == "assumed_rank"
    assert rank_any.storage.array.source_shape == [".."]
    assert rank_any.rank == 1
    assert strided.shape == ["0:n:Strided"]
    assert strided.storage.array.contiguous is False
    assert computed.shape == ["size(xl)"]
    assert bounded.constraints == [
        SemanticConstraint("Bounded", [1, 8]),
        SemanticConstraint("Constant"),
    ]
    assert nested.constraints == [SemanticConstraint("Constant")]


def test_convert_pyi_to_ir_preserves_module_fields_and_private_function_arguments():
    module = parse_pyi_text(
        """
output: Float64[:] = ...

def consume(value: private[Int32]) -> None: ...
""",
        module_name="fields",
    )

    assert module.variables[0].optional is True
    assert module.functions[0].arguments[0].visibility == "private"
