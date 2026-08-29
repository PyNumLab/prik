"""Semantic meaning of edited methods, overloads, and constructors."""

import pytest
import re
from dataclasses import asdict
from prik.printers import emit_module
from prik.semantics.metadata import (
    BIND_TARGET_METADATA,
    SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA,
    USER_PRIVATE_METADATA,
)
from tests.fortran._support.pyi_conversion import parse_pyi_text


def test_private_method_preserves_pass_projection_and_native_target():
    module = parse_pyi_text(
        """
class particle:
    @private
    @native_call([Pass()])
    def reset(self) -> Int32: ...
""",
        module_name="edited",
    )

    method = module.classes[0].methods[0]
    assert method.name == method.native_name == "reset"
    assert method.visibility == "private"
    assert method.origin.metadata[USER_PRIVATE_METADATA] is True
    assert [arg.name for arg in method.arguments] == ["self"]
    assert asdict(method.projection[0]) == {
        "python_name": "self",
        "native_name": "self",
        "native_position": 0,
        "python_position": 0,
        "result_position": None,
        "value_kind": None,
        "value": None,
        "value_cast": None,
        "native_c_identity": None,
    }
    emitted = emit_module(module)
    assert "    @private\n    def reset(self) -> Int32: ..." in emitted
    reparsed = parse_pyi_text(emitted, module_name="edited")
    assert reparsed.classes[0].methods[0].visibility == "private"
    assert reparsed.classes[0].methods[0].origin.metadata[USER_PRIVATE_METADATA] is True
    assert emit_module(reparsed) == emitted


@pytest.mark.parametrize("native_language", ["fortran", "c"])
def test_destroy_is_language_neutral_lifecycle_metadata(native_language: str):
    module = parse_pyi_text(
        """
class owned_buffer:
    @destroy
    def release_owned_buffer(self) -> None: ...

    @destroy
    @bind("release_owned_buffer_array")
    def release_array(self) -> None: ...
""",
        module_name="edited",
        native_language=native_language,
    )

    cls = module.classes[0]
    assert cls.methods == []
    assert [(item.name, item.native_name) for item in cls.destructors] == [
        ("release_owned_buffer", "release_owned_buffer"),
        ("release_array", "release_owned_buffer_array"),
    ]
    emitted = emit_module(module)
    assert "    @destroy\n    def release_owned_buffer(self) -> None: ..." in emitted
    assert (
        '    @destroy\n    @bind("release_owned_buffer_array")\n    def release_array(self) -> None: ...'
    ) in emitted
    assert (
        parse_pyi_text(
            emitted,
            module_name="edited",
            native_language=native_language,
        )
        == module
    )


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            """
@destroy
def release_owned_buffer(self) -> None: ...
""",
            "destroy is only valid on a class-body declaration",
        ),
        (
            """
class owned_buffer:
    @destroy()
    def release_owned_buffer(self) -> None: ...
""",
            "destroy does not accept arguments",
        ),
        (
            """
class owned_buffer:
    @private
    @destroy
    def release_owned_buffer(self) -> None: ...
""",
            "destroy can only be combined with bind",
        ),
        (
            """
class owned_buffer:
    @destroy
    def release_owned_buffer(self, status: Int32) -> None: ...
""",
            "destroy declaration must have the form",
        ),
        (
            """
class owned_buffer:
    @destroy
    def release_owned_buffer(self) -> Int32: ...
""",
            "destroy declaration must have the form",
        ),
    ],
)
def test_invalid_destroy_contracts_are_rejected(source: str, message: str):
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_pyi_text(source, module_name="edited")


def test_generated_and_linked_constructors_remain_distinct():
    generated = parse_pyi_text(
        """
class state:
    def __init__(self, *, id: Int32 = 7) -> None: ...

    id: Int32 = 7
""",
        module_name="generated",
    )
    assert generated.classes[0].methods == []

    linked = parse_pyi_text(
        """
@private
@native_call([Arg(0), Addr(Arg(1))])
def init_state(self: state, seed: Int32) -> None: ...

class state:
    def __init__(self, *, id: Int32 = 7) -> None: ...

    @overload("init_state")
    def __init__(self, seed: Int32) -> None: ...

    id: Int32 = 7
""",
        module_name="edited",
    )

    cls = linked.classes[0]
    assert cls.methods == []
    assert [overload.name for overload in cls.overload_sets] == ["__init__"]
    init = cls.overload_sets[0].procedures[0]
    assert init.metadata["overload_kind"] == "constructor"
    assert init.metadata["python_bound_position"] == 0
    assert [arg.name for arg in init.arguments] == ["self", "seed"]
    assert parse_pyi_text(emit_module(linked), module_name="edited") == linked


def test_removing_constructor_suppresses_generated_keyword_initialization():
    module = parse_pyi_text(
        """
class state:
    id: Int32 = 7
    scale: Float64 = 2.5
""",
        module_name="edited",
    )

    cls = module.classes[0]
    assert cls.origin.metadata[SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA] is True
    assert "def __init__" not in emit_module(module)


def test_bound_constructor_uses_explicit_pass_position_and_native_target():
    module = parse_pyi_text(
        """
class state:
    @bind("init_state")
    @native_call([Arg(0), Pass(), Arg(1)])
    def __init__(self, left: state, right: state) -> None: ...
""",
        module_name="edited",
    )

    cls = module.classes[0]
    assert cls.origin.metadata[SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA] is True
    init = cls.methods[0]
    assert init.native_name == "init_state"
    assert init.metadata[BIND_TARGET_METADATA] == "init_state"
    assert [arg.name for arg in init.arguments] == ["left", "self", "right"]
    assert init.passed_object_position == 1
    assert [(item.native_position, item.python_position) for item in init.projection] == [
        (0, 0),
        (1, 1),
        (2, 2),
    ]
    assert parse_pyi_text(emit_module(module), module_name="edited") == module


def test_bound_constructor_can_reuse_public_module_procedure():
    module = parse_pyi_text(
        """
def init_state(owner: state, seed: Int32) -> None: ...

class state:
    @bind("init_state")
    @native_call([Pass(), Addr(Arg(0))])
    def __init__(self, seed: Int32) -> None: ...
""",
        module_name="edited",
    )

    init = module.classes[0].methods[0]
    assert init.native_name == module.functions[0].native_name == "init_state"
    emitted = emit_module(module)
    assert "def init_state(" in emitted
    assert '    @bind("init_state")\n    @native_call([Pass(), Addr(Arg(0))])' in emitted


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            """
class state:
    def __init__(self, seed: Int32) -> None: ...
""",
            'Non-generated __init__ declarations must use @bind("specific_name")',
        ),
        (
            """
class state:
    def __init__(self, *, id: Int32 = 7) -> None: ...

    @bind("init_state")
    @native_call([Pass(), Addr(Arg(0))])
    def __init__(self, seed: Int32) -> None: ...
""",
            "Direct constructor bindings replace the generated field constructor",
        ),
        (
            """
class state:
    @bind("init_state")
    @native_call([Addr(Arg(0))])
    def __init__(self, seed: Int32) -> None: ...
""",
            "Bound constructor native_call requires exactly one Pass() entry",
        ),
        (
            """
class state:
    @bind("init_state")
    @native_call([Pass(), Pass(), Addr(Arg(0))])
    def __init__(self, seed: Int32) -> None: ...
""",
            "Bound constructor native_call requires exactly one Pass() entry",
        ),
    ],
)
def test_contradictory_constructor_declarations_are_rejected(source: str, message: str):
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_pyi_text(source, module_name="edited")


def test_bind_selects_module_method_and_constructor_overload_targets():
    module = parse_pyi_text(
        """
def convert_integer(value: Int32) -> Int32: ...

@bind("convert")
@overload("convert_integer")
def convert_number(value: Int32) -> Int32: ...

def set_integer(self: item, value: Int32) -> None: ...

class item:
    @bind("set")
    @overload("set_integer")
    def set(self, value: Int32) -> None: ...

def init_integer(self: state, value: Int32) -> None: ...

class state:
    @bind("initialize")
    @overload("init_integer")
    def __init__(self, value: Int32) -> None: ...
""",
        module_name="edited",
    )

    candidates = (
        module.overload_sets[0].procedures[0],
        module.classes[0].overload_sets[0].procedures[0],
        module.classes[1].overload_sets[0].procedures[0],
    )
    assert [candidate.native_name for candidate in candidates] == ["convert", "set", "initialize"]
    assert [candidate.metadata[BIND_TARGET_METADATA] for candidate in candidates] == [
        "convert",
        "set",
        "initialize",
    ]


def test_method_and_module_declarations_keep_native_targets_independent():
    module = parse_pyi_text(
        """
class vector:
    @native_call([Pass(), Arg(0)])
    def scale(self, factor: Addr(Float64)) -> None: ...

    @bind("shift_vector")
    @native_call([Arg(0), Pass(), Arg(1)])
    def shift(self, dx: Addr(Float64), dy: Addr(Float64)) -> None: ...

def scale(self: vector, factor: Addr(Float64)) -> None: ...

def shift_vector(dx: Addr(Float64), owner: vector, dy: Addr(Float64)) -> None: ...
""",
        module_name="edited",
    )
    functions = {func.name: func for func in module.functions}
    methods = {method.name: method for method in module.classes[0].methods}

    assert methods["scale"].native_name == "scale"
    assert methods["shift"].native_name == "shift_vector"
    assert "fortran_type_bound_target" not in functions["scale"].metadata
    assert "fortran_type_bound_target" not in functions["shift_vector"].metadata
    emitted = emit_module(module)
    reparsed = parse_pyi_text(emitted, module_name="edited")
    assert all("fortran_type_bound_target" not in function.metadata for function in reparsed.functions)
    assert emit_module(reparsed) == emitted
