"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

from tests._shared.pyi_conversion_support import (
    BIND_TARGET_METADATA,
    PROJECTED_OUTPUT_METADATA,
    SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA,
    USER_PRIVATE_METADATA,
    asdict,
    emit_module,
    parse_pyi_text,
    pytest,
    re,
)


def test_convert_pyi_to_ir_rejects_enum_classes():
    source = """class status(Enum[Int]):
    pass
"""

    with pytest.raises(ValueError, match=r"Enum declarations are not supported"):
        parse_pyi_text(source, module_name="status_api")


def test_convert_pyi_to_ir_class_body_visibility_and_native_call():
    module = parse_pyi_text(
        """
class wrapper:
    pass

class particle:
    @private
    @native_call([Pass()])
    def reset(self) -> Int32: ...
""",
        module_name="edited",
    )

    empty_cls, particle_cls = module.classes
    assert empty_cls.name == "wrapper"
    assert particle_cls.methods[0].name == "reset"
    assert particle_cls.methods[0].native_name == "reset"
    assert particle_cls.methods[0].visibility == "private"
    assert particle_cls.methods[0].origin.metadata[USER_PRIVATE_METADATA] is True
    assert [arg.name for arg in particle_cls.methods[0].arguments] == ["self"]
    assert particle_cls.methods[0].return_type.name == "Int32"
    assert asdict(particle_cls.methods[0].projection[0]) == {
        "python_name": "self",
        "native_name": "self",
        "native_position": 0,
        "python_position": 0,
        "result_position": None,
        "value_kind": None,
        "value": None,
    }
    emitted = emit_module(module)
    assert "    @private\n    def reset(self) -> Int32: ..." in emitted
    reparsed = parse_pyi_text(emitted, module_name="edited")
    assert reparsed.classes[1].methods[0].visibility == "private"
    assert reparsed.classes[1].methods[0].origin.metadata[USER_PRIVATE_METADATA] is True
    assert emit_module(reparsed) == emitted


def test_convert_pyi_to_ir_distinguishes_generated_and_linked_constructors():
    generated = parse_pyi_text(
        """
class state:
    def __init__(
        self,
        *,
        id: Int32 = 7,
        scale: Float64 = 2.5
    ) -> None: ...

    id: Int32 = 7
    scale: Float64 = 2.5
""",
        module_name="generated",
    )

    generated_cls = generated.classes[0]
    assert generated_cls.origin.source_language == "fortran"
    assert generated_cls.methods == []

    linked = parse_pyi_text(
        """
@private
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def init_state(
    self: state,
    seed: Int32,
    scale: Float64 = ...
) -> None: ...

class state:
    def __init__(
        self,
        *,
        id: Int32 = 7,
        scale: Float64 = 2.5
    ) -> None: ...

    @overload("init_state")
    def __init__(
        self,
        seed: Int32,
        scale: Float64 = ...
    ) -> None: ...

    id: Int32 = 7
    scale: Float64 = 2.5
""",
        module_name="edited",
    )

    linked_cls = linked.classes[0]
    assert linked_cls.origin.source_language == "fortran"
    assert linked_cls.methods == []
    assert [overload.name for overload in linked_cls.overload_sets] == ["__init__"]
    init = linked_cls.overload_sets[0].procedures[0]
    assert init.name == "init_state"
    assert init.metadata["overload_target"] == "init_state"
    assert init.metadata["overload_kind"] == "constructor"
    assert init.metadata["python_method_name"] == "__init__"
    assert init.metadata["python_bound_position"] == 0
    assert [arg.name for arg in init.arguments] == ["self", "seed", "scale"]
    assert [arg.optional for arg in init.arguments] == [False, False, True]

    emitted = emit_module(linked)
    assert "def __init__(\n        self,\n        *,\n        id: Int32 = 7," in emitted
    assert '    @overload("init_state")\n    def __init__(' in emitted
    assert '    @overload("init_state")\n    @native_call' not in emitted
    assert parse_pyi_text(emitted, module_name="edited") == linked


def test_convert_pyi_to_ir_removed_constructor_suppresses_keyword_initializer():
    module = parse_pyi_text(
        """
class state:
    id: Int32 = 7
    scale: Float64 = 2.5
""",
        module_name="edited",
    )

    cls = module.classes[0]
    assert cls.origin.source_language is None
    assert cls.origin.metadata[SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA] is True
    assert "def __init__" not in emit_module(module)


def test_convert_pyi_to_ir_self_only_generated_constructor_keeps_default_initializer():
    module = parse_pyi_text(
        """
class state:
    def __init__(self) -> None: ...

    values: Allocatable[Float64[:]]
""",
        module_name="edited",
    )

    cls = module.classes[0]
    assert cls.origin.source_language == "fortran"
    assert SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA not in cls.origin.metadata
    assert cls.methods == []
    assert "    def __init__(self) -> None: ..." in emit_module(module)


def test_convert_pyi_to_ir_bound_constructor_uses_explicit_pass_position():
    module = parse_pyi_text(
        """
class state:
    @bind("init_state")
    @native_call([Arg(0), Pass(), Arg(1)])
    def __init__(
        self,
        left: state,
        right: state
    ) -> None: ...

    id: Int32 = 7
    scale: Float64 = 2.5
""",
        module_name="edited",
    )

    cls = module.classes[0]
    assert cls.origin.metadata[SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA] is True
    assert [method.name for method in cls.methods] == ["__init__"]
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

    emitted = emit_module(module)
    assert '    @bind("init_state")\n    @native_call([Arg(0), Pass(), Arg(1)])\n    def __init__(' in emitted
    assert "def __init__(\n        self,\n        *," not in emitted
    assert parse_pyi_text(emitted, module_name="edited") == module


def test_convert_pyi_to_ir_bound_constructor_does_not_require_class_method_target():
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

    cls = module.classes[0]
    assert [method.name for method in cls.methods] == ["__init__"]
    assert cls.methods[0].native_name == module.functions[0].native_name == "init_state"
    emitted = emit_module(module)
    assert "def init_state(" in emitted
    assert '    @bind("init_state")\n    @native_call([Pass(), Addr(Arg(0))])\n    def __init__(' in emitted


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
def test_convert_pyi_to_ir_rejects_ambiguous_constructor_declarations(source: str, message: str):
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_pyi_text(source, module_name="edited")


def test_convert_pyi_to_ir_applies_decorators_after_native_call():
    module = parse_pyi_text(
        """
@native_call([])
@private
def hidden() -> None: ...
""",
        module_name="edited",
    )

    assert module.functions[0].visibility == "private"


def test_convert_pyi_to_ir_resolves_x2py_overload_by_explicit_specific_name():
    module = parse_pyi_text(
        """
@bind("convert_integer_native")
def convert_integer(value: Int32) -> Int32: ...

@overload("convert_integer")
def convert(value: Int32) -> Int32: ...
""",
        module_name="generic_mod",
    )

    assert [function.name for function in module.functions] == ["convert_integer"]
    assert [(item.name, [procedure.name for procedure in item.procedures]) for item in module.overload_sets] == [
        ("convert", ["convert_integer"])
    ]
    assert module.overload_sets[0].procedures[0].metadata["overload_target"] == "convert_integer"
    assert module.overload_sets[0].procedures[0].native_name == "convert_integer_native"


def test_convert_pyi_to_ir_applies_module_overload_bind_and_round_trips_native_name():
    module = parse_pyi_text(
        """
def convert_integer(value: Int32) -> Int32: ...

@bind("convert")
@overload("convert_integer")
def convert_number(value: Int32) -> Int32: ...
""",
        module_name="generic_mod",
    )

    overload = module.overload_sets[0]
    assert overload.name == "convert_number"
    assert overload.procedures[0].native_name == "convert"
    assert overload.procedures[0].metadata[BIND_TARGET_METADATA] == "convert"
    emitted = emit_module(module)
    assert '@bind("convert")\n@overload("convert_integer")' in emitted


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            "@overload\ndef convert(value: Int32) -> Int32: ...\n",
            "overload expects one specific procedure name",
        ),
        (
            "from typing import overload\n",
            "typing.overload is not supported",
        ),
        (
            """
def convert_integer(value: Int32) -> Int32: ...

@overload("convert_integer", generic="convert")
def convert_number(value: Int32) -> Int32: ...
""",
            "generic is only valid for class overloads; use bind on a module overload",
        ),
        (
            """
def compare(left: item, right: item) -> Bool: ...
class item:
    @overload("compare", generic="operator(.eqv.)")
    def __add__(self, right: item) -> Bool: ...
""",
            "generic 'operator\\(\\.eqv\\.\\)' is incompatible with method '__add__'",
        ),
        (
            '@overload("missing")\ndef convert(value: Int32) -> Int32: ...\n',
            "missing specific procedure 'missing'",
        ),
        (
            """
def convert_integer(value: Int32) -> Int32: ...
def convert_integer(value: Int32) -> Int32: ...
@overload("convert_integer")
def convert(value: Int32) -> Int32: ...
""",
            "target 'convert_integer' is ambiguous",
        ),
        (
            """
def convert_integer(value: Int32) -> Int32: ...
@overload("convert_integer")
def convert(value: Float64) -> Int32: ...
""",
            "declaration 'convert' is incompatible",
        ),
        (
            """
def convert_integer(value: Int32) -> Int32: ...
@overload("convert_integer")
def convert(value: Int32) -> Int32: ...
@overload("convert_integer")
def convert(value: Int32) -> Int32: ...
""",
            "references specific procedure 'convert_integer' more than once",
        ),
        (
            """
def convert_integer(value: Int32) -> Int32: ...
@overload("convert_integer")
@native_call([Addr(Arg(0))])
def convert(value: Int32) -> Int32: ...
""",
            "overload cannot be combined with native_call",
        ),
        (
            """
def set_integer(self: item, value: Int32) -> None: ...
class item:
    @overload("set_integer")
    @native_call([Pass(), Addr(Arg(0))])
    def set(self, value: Int32) -> None: ...
""",
            "overload cannot be combined with native_call",
        ),
    ],
)
def test_convert_pyi_to_ir_rejects_invalid_x2py_overload_links(source: str, message: str):
    with pytest.raises(ValueError, match=message):
        parse_pyi_text(source, module_name="generic_mod")


def test_identity_returns_reconstruct_native_projection_without_decorator():
    source = """
def fill(values: Float64[3]) -> Returns["values", Float64[3]]: ...
"""
    module = parse_pyi_text(source, module_name="identity_returns")
    function = module.functions[0]

    assert len(function.projection) == 1
    assert function.projection[0].native_position == 0
    assert function.projection[0].python_position == 0
    assert function.projection[0].result_position == 0
    assert (
        emit_module(module)
        .strip()
        .endswith('def fill(\n    values: Float64[3]\n) -> Returns["values", Float64[3]]: ...')
    )


def test_compact_assignment_overload_projects_visible_destination_without_direction_label():
    from_pyi = parse_pyi_text(
        """
class vector:
    value: Float64

    @overload("assign_vector_real")
    def assign(
        self,
        right: Float64
    ) -> vector: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def assign_vector_real(
    left: vector,
    right: Float64
) -> Returns["left", vector]: ...
""",
        module_name="edited",
    )
    func = from_pyi.functions[0]

    assert func.arguments[0].metadata[PROJECTED_OUTPUT_METADATA] is True
    assert func.projection[0].result_position == 0
    assert from_pyi.classes[0].overload_sets[0].procedures[0].metadata["overload_kind"] == "assignment"


def test_method_declarations_keep_module_procedure_targets_independent():
    from_pyi = parse_pyi_text(
        """
class vector:
    @native_call([Pass(), Arg(0)])
    def scale(
        self,
        factor: Addr(Float64)
    ) -> None: ...

    @bind("shift_vector")
    @native_call([Arg(0), Pass(), Arg(1)])
    def shift(
        self,
        dx: Addr(Float64),
        dy: Addr(Float64)
    ) -> None: ...

def scale(
    self: vector,
    factor: Addr(Float64)
) -> None: ...

def shift_vector(
    dx: Addr(Float64),
    owner: vector,
    dy: Addr(Float64)
) -> None: ...

def inspect(value: Annotated[vector, Polymorphic]) -> None: ...
""",
        module_name="edited",
    )
    functions = {func.name: func for func in from_pyi.functions}
    methods = {method.name: method for method in from_pyi.classes[0].methods}

    assert methods["scale"].native_name == "scale"
    assert methods["shift"].native_name == "shift_vector"
    assert "fortran_type_bound_target" not in functions["scale"].metadata
    assert "fortran_type_bound_target" not in functions["shift_vector"].metadata

    emitted = emit_module(from_pyi)
    assert "self: vector" in emitted
    assert "owner: vector" in emitted
    assert "value: Annotated[vector, Polymorphic]" in emitted
    reparsed = parse_pyi_text(emitted, module_name="edited")
    assert "fortran_type_bound_target" not in reparsed.functions[0].metadata
    assert emit_module(reparsed) == emitted


def test_pyi_keyword_normalized_type_bound_method_keeps_native_binding_name():
    module = parse_pyi_text(
        """
class visible_t:
    @bind("visible_from")
    def from_(self) -> Int32: ...
""",
        module_name="fnaming_f90",
    )

    method = module.classes[0].methods[0]

    assert method.name == "from_"
    assert method.native_name == "visible_from"


def test_method_equality_treats_argument_names_as_placeholders():
    left = parse_pyi_text(
        """
class vector:
    def scale(
        self,
        n: Int32,
        x: Float64[1:n]
    ) -> None: ...
""",
        module_name="edited",
    )
    right = parse_pyi_text(
        """
class vector:
    def scale(
        self,
        extent: Int32,
        values: Float64[1:extent]
    ) -> None: ...
""",
        module_name="edited",
    )

    assert left == right


def test_convert_pyi_to_ir_accepts_multiline_native_call_decorator():
    module = parse_pyi_text(
        """
@native_call([
    Arg(0),
    Return(0),
])
def wrapper(
    x: Int32
) -> Float64: ...
""",
        module_name="edited",
    )

    func = module.functions[0]
    assert func.name == "wrapper"
    assert func.projection[0].python_position == 0
    assert func.projection[1].result_position == 0
