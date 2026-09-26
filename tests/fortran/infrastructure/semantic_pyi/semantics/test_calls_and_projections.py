"""Semantic meaning of `@native_call` projections, returns, and callable shapes."""

import pytest
from prik.printers import emit_module
from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_PROJECTION,
    PROJECTED_OUTPUT_METADATA,
)
from prik.policy.completion import complete_semantic_policies
from tests.fortran._support.pyi_conversion import parse_pyi_text


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


def test_ir_equality_ignores_only_callable_argument_names():
    """Callable argument names are placeholders; declaration and field names are identity."""
    left = parse_pyi_text("def resize(\n    n: Int32,\n    x: Float64[1:n]\n) -> None: ...\n", module_name="edited")
    right = parse_pyi_text(
        "def resize(\n    extent: Int32,\n    values: Float64[1:extent]\n) -> None: ...\n", module_name="edited"
    )

    assert left == right
    assert left.functions[0].arguments[0] != right.functions[0].arguments[0]
    assert parse_pyi_text("value: Int32\n", module_name="edited") != parse_pyi_text(
        "other: Int32\n", module_name="edited"
    )
    assert parse_pyi_text("class vector:\n    x: Float64\n", module_name="edited") != parse_pyi_text(
        "class vector:\n    y: Float64\n", module_name="edited"
    )


@pytest.mark.parametrize(
    ("entry", "output_name"),
    [("Return(0)", "__return_0"), ('Return("c", 0)', "c")],
    ids=["unnamed-output", "named-output"],
)
def test_native_call_return_entry_keeps_the_native_output_slot(entry: str, output_name: str):
    function = parse_pyi_text(
        f"""
@native_call([Arg(0), Arg(1), {entry}])
def add(
    a: Float64,
    b: Float64
) -> Float64: ...
""",
        module_name="edited",
    ).functions[0]

    assert [arg.name for arg in function.arguments][:2] == ["a", "b"]
    assert function.projection[2].native_position == 2
    assert function.projection[2].result_position == 0
    if output_name == "c":
        assert function.arguments[2].name == "c"
        assert function.projection[2].native_name == function.projection[2].python_name == "c"


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

@native_call([Return(0), Len(Return(0)), Work("tmp").shape[0]])
def f() -> Float64: ...
""",
        module_name="edited",
    )

    wrapper, returned = module.functions
    assert [
        (item.native_position, item.python_position, item.value_kind, item.value) for item in wrapper.projection
    ] == [
        (0, 0, "", None),
        (1, None, "literal", {"type": "Int32", "value": 1}),
        (2, None, "literal", {"type": "Float64", "value": 0.5}),
        (3, None, "literal", {"type": "Bool", "value": False}),
        (4, None, "literal", {"type": "String[1]", "value": "N"}),
        (5, None, "len", {"kind": "arg", "position": 0}),
        (6, None, "shape", {"value": {"kind": "arg", "position": 0}, "dim": 0}),
        (7, None, "is_present", {"kind": "arg", "position": 1}),
        (8, None, "work", "tmp"),
    ]
    assert wrapper.arguments[1].optional
    assert returned.projection[1].value == {"kind": "return", "position": 0}
    assert returned.projection[2].value == {"value": {"kind": "work", "name": "tmp"}, "dim": 0}


def test_typed_projection_entries_record_producer_and_requested_type():
    """A typed wrapper around a size/shape/stride/length producer is a cast; around a literal, a constant."""
    module = parse_pyi_text(
        """
@native_call([
    Int32(Arg(0).shape[0]),
    Int64(Arg(0).strides[0]),
    Arg(0),
    Int32(Len(Arg(1))),
    Arg(1),
    Arg(0).size,
    Int32(Arg(0).size),
    Int32(1),
    Int32(-1),
    Float64(-0.5),
    Complex64(1+2j),
])
def scale(values: Float64[::], label: String[8]) -> None: ...
""",
        module_name="typed_projection",
    )

    arg0 = {"kind": "arg", "position": 0}
    assert [(item.value_kind, item.value, item.value_cast) for item in module.functions[0].projection] == [
        ("shape", {"value": arg0, "dim": 0}, "Int32"),
        ("stride", {"value": arg0, "dim": 0}, "Int64"),
        ("", None, None),
        ("len", {"kind": "arg", "position": 1}, "Int32"),
        ("", None, None),
        ("size", arg0, None),
        ("size", arg0, "Int32"),
        ("literal", {"type": "Int32", "value": 1}, None),
        ("literal", {"type": "Int32", "value": -1}, None),
        ("literal", {"type": "Float64", "value": -0.5}, None),
        ("literal", {"type": "Complex64", "value": 1 + 2j}, None),
    ]


def test_typed_scalar_constructor_rejects_a_visible_argument_reference():
    with pytest.raises(
        ValueError,
        match="Int32 accepts a literal value or a size, shape, stride, or length projection",
    ):
        parse_pyi_text(
            """from prik.contracts import Arg, Int32, native_call

@native_call([Int32(Arg(0))])
def scale(count: Int32) -> None: ...
""",
            module_name="rejected_typed_projection",
        )


def test_plain_tuple_return_types_parse_component_returns():
    func = parse_pyi_text(
        """
def split(
    x: Float64
) -> tuple[Float64, Int32, Logical]: ...
""",
        module_name="edited",
    ).functions[0]

    assert func.return_type.name == "Float64"
    assert [(arg.name, arg.semantic_type.name) for arg in func.arguments] == [
        ("x", "Float64"),
        ("__return_1", "Int32"),
        ("__return_2", "Logical"),
    ]
    assert [(item.native_position, item.result_position) for item in func.projection] == [(0, None), (1, 1), (2, 2)]


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
        ("@staticmethod\nclass C:\n    pass\n", "Unsupported class decorator: 'staticmethod'"),
        (
            '@overload("missing")\nclass C:\n    pass\n',
            "Unsupported class decorator: \"overload('missing')\"",
        ),
        (
            "@abstractmethod\ndef f() -> None: ...\n",
            "abstractmethod is only valid on a method declaration",
        ),
        (
            "class Outer:\n    @destroy\n    class Inner:\n        pass\n",
            "Unsupported class body decorator: 'destroy'",
        ),
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
            "Expected imported prik contract helper: 'Unknown'",
        ),
        (
            "def f(x: Int32) -> Returns['x']: ...\n",
            "Returns expects a name and type; use '| None' for nullable returns: \"Returns['x']\"",
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


def test_convert_pyi_to_ir_handles_pointer_and_array_storage_variants():
    module = parse_pyi_text(
        """
constant: Int32
deep: Addr[3](Float64)
rank_any: Float64[...]
strided: Float64[0:n:]
""",
        module_name="storage",
    )

    constant, deep, rank_any, strided = [var.semantic_type for var in module.variables]
    assert constant.storage is None
    assert deep.storage.kind == "pointer"
    assert deep.storage.pointer_depth == 3
    assert deep.storage.read_only is False
    assert deep.storage.mutable is True
    assert rank_any.storage.array.rank == 1
    assert rank_any.storage.array.category == "assumed_rank"
    assert rank_any.storage.array.source_shape == [".."]
    assert rank_any.rank == 1
    assert strided.shape == ["0:n:"]
    assert strided.storage.array.contiguous is False
