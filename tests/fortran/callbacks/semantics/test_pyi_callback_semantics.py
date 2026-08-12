"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

import pytest
from prik.policy.completion import complete_semantic_policies
from tests.fortran._support.pyi_conversion import parse_pyi_text


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


def test_prototype_is_one_exact_nonexported_signature_declaration():
    module = parse_pyi_text(
        """
@pure
@prototype
def extent_for(n: In(Addr(Int32))) -> Int32: ...

def values(n: Int32) -> Float64[extent_for(n)]: ...
""",
        module_name="prototype_signature",
    )

    prototype = module.prototypes[0]
    assert prototype.pure is True
    assert prototype.origin.native_scope == "prototype_signature"
    assert prototype.arguments[0].origin.metadata == {"value": False, "prototype_intent": "in"}
    assert [function.name for function in module.functions] == ["values"]


@pytest.mark.parametrize(
    ("decorators", "message"),
    [
        ("@pure", "pure requires prototype"),
        ("@standalone\n@prototype", "prototype cannot be combined with standalone"),
    ],
)
def test_exact_interface_decorators_reject_ambiguous_combinations(decorators: str, message: str):
    with pytest.raises(ValueError, match=message):
        parse_pyi_text(
            f"""
{decorators}
def declared(value: Int32) -> Int32: ...
""",
            module_name="invalid_prototype_decorators",
        )


def test_imported_prototype_resolves_as_module_interface_definition(tmp_path):
    from prik.pipeline.pyi import pyi_paths_to_semantic_modules
    from prik.pipeline.wrapper import WrapperGenerator
    from prik.planning import WrapperPlanner

    (tmp_path / "callback_shapes.pyi").write_text(
        """from prik.contracts import Float64, Int32, prototype

@prototype
def transform(count: Int32, values: Float64[count]) -> Float64[count]: ...
""",
        encoding="utf-8",
    )
    (tmp_path / "api.pyi").write_text(
        """from prik.contracts import Float64, Int32
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
    artifacts = WrapperGenerator().generate(WrapperPlanner().build(api))
    bridge = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")
    assert "abstract interface" in bridge
    assert "function prik_transform_" in bridge
    assert "procedure(prik_transform_" in bridge
    assert "use callback_shapes, only:" not in bridge


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
