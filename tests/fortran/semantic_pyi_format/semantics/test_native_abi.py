import pytest

from prik.planning import WrapperPlanner
from prik.policy import complete_semantic_policies
from prik.policy.models import NativeEntrypointAction
from prik.printers import emit_module
from tests.fortran._support.pyi_conversion import parse_pyi_text


def test_native_abi_keeps_fortran_identity_symbol_and_route_neutral_projection():
    module = parse_pyi_text(
        """
@native_abi("c")
@bind("scaled_value")
@native_call([Arg(0), Int32(4), Return("result", 0)])
def scale(value: Float64) -> Float64: ...
""",
        module_name="native_api",
    )

    function = module.functions[0]
    assert function.native_name == "scale"
    assert function.origin.source_language == "fortran"
    assert function.origin.native_name == "scale"
    assert function.origin.native_scope == "native_api"
    assert function.origin.native_abi == "c"
    assert function.origin.native_symbol == "scaled_value"
    assert [item.value_kind for item in function.projection] == ["", "literal", ""]
    assert [item.native_position for item in function.projection] == [0, 1, 2]
    assert function.projection[2].result_position == 0


def test_native_abi_composes_with_standalone_method_overload_and_prototype():
    module = parse_pyi_text(
        """
@native_abi("c")
@standalone
def external(value: Float64) -> Float64: ...

@private
@native_abi("c")
def specific(value: Float64) -> Float64: ...

@native_abi("c")
@bind("generic_label")
@overload("specific")
def generic(value: Float64) -> Float64: ...

@native_abi("c")
@bind("callback_label")
@prototype
def callback(value: Float64) -> Float64: ...

class State:
    @native_abi("c")
    @staticmethod
    def reset(value: Float64) -> None: ...
""",
        module_name="compositions",
    )

    assert module.functions[0].origin.native_scope is None
    candidate = module.overload_sets[0].procedures[0]
    assert candidate.origin.native_abi == "c"
    assert candidate.origin.native_symbol == "generic_label"
    assert module.prototypes[0].origin.native_abi == "c"
    assert module.prototypes[0].origin.native_symbol == "callback_label"
    assert module.classes[0].methods[0].origin.native_abi == "c"


@pytest.mark.parametrize(
    ("source", "native_language", "message"),
    [
        ('@native_abi("fortran")\ndef bad() -> None: ...', "fortran", 'accepts only "c"'),
        ('@native_abi("c")\n@native_abi("c")\ndef bad() -> None: ...', "fortran", "Duplicate"),
        ('@native_abi("c")\nclass Bad:\n    pass', "fortran", "Unsupported class decorator"),
        ('@native_abi("c")\ndef bad() -> None: ...', "c", "only valid for Fortran"),
    ],
)
def test_native_abi_rejects_contradictory_or_misplaced_annotations(
    source: str,
    native_language: str,
    message: str,
):
    with pytest.raises(ValueError, match=message):
        parse_pyi_text(source, module_name="invalid_native_abi", native_language=native_language)


def test_native_abi_round_trip_keeps_marker_symbol_and_projection():
    original = parse_pyi_text(
        """
@native_abi("c")
@bind("renamed_entry")
@native_call([Addr(Arg(0)), Arg(0).shape[0], Return("result", 0)])
def transform(values: Float64[:]) -> Float64: ...
""",
        module_name="round_trip_native_abi",
    )

    rendered = emit_module(original)
    loaded = parse_pyi_text(rendered, module_name=original.name)
    function = loaded.functions[0]

    assert '@native_abi("c")' in rendered
    assert '@bind("renamed_entry")' in rendered
    assert function.origin.native_abi == "c"
    assert function.origin.native_symbol == "renamed_entry"
    assert function.origin.source_language == "fortran"
    assert function.projection == original.functions[0].projection


def test_source_free_native_abi_selects_the_preserved_symbol_and_direct_route():
    module = parse_pyi_text(
        """
@native_abi("c")
@bind("edited_native_symbol")
def transform(value: Int32) -> Int32: ...
""",
        module_name="source_free_native_abi",
    )

    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]

    assert function.entrypoint.action is NativeEntrypointAction.DIRECT_C_ABI
    assert function.entrypoint.symbol_name == "edited_native_symbol"
    assert function.bridge is None
    assert plan.native_generated_code_groups == ()


def test_native_abi_round_trip_preserves_scalar_c_character_value_transport():
    original = parse_pyi_text(
        """
@native_abi("c")
@native_call([Value(Arg(0))])
def char_code(ch: String[1]) -> Int32: ...
""",
        module_name="c_character_value",
    )

    rendered = emit_module(original)
    loaded = parse_pyi_text(rendered, module_name=original.name)

    assert "@native_call([Value(Arg(0))])" in rendered
    assert loaded.functions[0].arguments[0].metadata["native_by_value"] is True


def test_native_abi_source_free_concrete_array_retains_explicit_shape_mechanism():
    module = parse_pyi_text(
        """
@native_abi("c")
def total(n: Int32, values: Float64[n]) -> Float64: ...
""",
        module_name="explicit_shape_native_abi",
    )

    array = module.functions[0].arguments[1].semantic_type.storage.array
    assert array.category == "explicit_shape"


def test_native_abi_rejects_value_transport_for_longer_character_buffer():
    with pytest.raises(ValueError, match=r"String\[1\]"):
        parse_pyi_text(
            """
@native_abi("c")
@native_call([Value(Arg(0))])
def invalid(label: String[8]) -> Int32: ...
""",
            module_name="invalid_c_character_value",
        )
