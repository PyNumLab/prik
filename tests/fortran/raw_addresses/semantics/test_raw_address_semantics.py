"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

import pytest
from prik.codegen.printers import emit_module
from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_RAW,
)
from prik.semantics.policy_completion import complete_semantic_policies
from tests.fortran._support.pyi_conversion import parse_pyi_text


def test_public_raw_address_contract_round_trips():
    module = parse_pyi_text(
        """
def update_raw(value: Addr(Float64)) -> None: ...
def inspect_raw(value: Addr(Float64)) -> None: ...
def raw_values(n: Int32, values: Addr(Float64[n])) -> None: ...
def raw_label(label: Addr(String[8])) -> None: ...
""",
        module_name="raw_address",
    )

    update, inspect, raw_values, raw_label = module.functions
    update_storage = update.arguments[0].semantic_type.storage
    inspect_storage = inspect.arguments[0].semantic_type.storage
    values_type = raw_values.arguments[1].semantic_type
    label_type = raw_label.arguments[0].semantic_type

    assert update_storage.kind == "address"
    assert update_storage.metadata[ADDRESS_ROLE_METADATA] == ADDRESS_ROLE_RAW
    assert inspect_storage.read_only is False
    assert inspect_storage.mutable is True
    assert values_type.rank == 1
    assert values_type.shape == ["n"]
    assert values_type.storage.kind == "address"
    assert values_type.storage.metadata[ADDRESS_ROLE_METADATA] == ADDRESS_ROLE_RAW
    assert label_type.name == "String"
    assert label_type.metadata["fortran_character_length"] == "8"
    assert label_type.storage.kind == "address"
    assert label_type.storage.metadata[ADDRESS_ROLE_METADATA] == ADDRESS_ROLE_RAW

    emitted = emit_module(module)
    assert "value: Addr(Float64)" in emitted
    assert "value: Addr(Float64)" in emitted
    assert "values: Addr(Float64[n])" in emitted
    assert "label: Addr(String[8])" in emitted
    assert parse_pyi_text(emitted, module_name="raw_address") == module


def test_wrapped_type_raw_address_is_rejected_during_policy_completion():
    module = parse_pyi_text(
        """
class particle:
    value: Float64

def move(value: Addr(particle)) -> None: ...
""",
        module_name="wrapped_address",
    )

    storage = module.functions[0].arguments[0].semantic_type.storage
    assert storage.kind == "address"
    assert storage.metadata[ADDRESS_ROLE_METADATA] == ADDRESS_ROLE_RAW
    assert (
        emit_module(module)
        .strip()
        .endswith("class particle:\n    value: Float64\n\ndef move(\n    value: Addr(particle)\n) -> None: ...")
    )
    with pytest.raises(ValueError, match=r"Addr\(WrappedType\) is not allowed"):
        complete_semantic_policies(module)


def test_raw_address_policy_accepts_only_complete_primitive_layouts():
    module = parse_pyi_text(
        """
def raw_access(
    n: Int32,
    scalar: Addr(Float64),
    label: Addr(String[8]),
    values: Addr(Float64[n])
) -> Addr(Int32): ...

def raw_access_with_storage_extent(
    n: Int32[()],
    values: Addr(Float64[n])
) -> None: ...
""",
        module_name="raw_addresses",
    )

    complete_semantic_policies(module)

    assert module.metadata["policy_completion_prepared"] is True


@pytest.mark.parametrize(
    ("annotation", "message"),
    [
        ("Addr(particle)", r"Addr\(WrappedType\) is not allowed"),
        ("Addr(String)", "raw strings require a fixed length"),
        ("Addr(Float64[:])", "raw arrays require a fully resolved rank and shape"),
        ("Addr(Float64[missing])", "raw arrays require a fully resolved rank and shape"),
        ("Addr[2](Float64)", r"callable Addr\(T\) supports depth one only"),
    ],
)
def test_raw_address_policy_rejects_incomplete_or_wrapped_pointees(annotation: str, message: str):
    module = parse_pyi_text(
        f"""
class particle:
    value: Float64

def invalid(n: Int32, value: {annotation}) -> None: ...
""",
        module_name="invalid_raw_address",
    )

    with pytest.raises(ValueError, match=message):
        complete_semantic_policies(module)


@pytest.mark.parametrize(
    "annotation",
    [
        "String[8]",
        "Float64[()]",
        "Float64[:]",
        "particle",
        "Addr(Float64)",
    ],
)
def test_native_call_addr_arg_rejects_non_primitive_scalar_values(annotation: str):
    module = parse_pyi_text(
        f"""
class particle:
    value: Float64

@native_call([Addr(Arg(0))])
def invalid(value: {annotation}) -> None: ...
""",
        module_name="edited",
    )

    with pytest.raises(ValueError, match="only valid for primitive scalar values"):
        complete_semantic_policies(module)


@pytest.mark.parametrize(
    ("projection", "return_type"),
    [
        ("Addr(Return(0))", "Float64"),
        ('Addr(Work("scratch"))', "None"),
    ],
)
def test_native_call_address_projection_rejects_non_argument_storage(projection: str, return_type: str):
    module = parse_pyi_text(
        f"""
@native_call([{projection}])
def invalid() -> {return_type}: ...
""",
        module_name="edited",
    )

    with pytest.raises(ValueError, match=r"only Addr\(Arg\(i\)\) is supported"):
        complete_semantic_policies(module)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("value: Addr(Int32, Float64)\n", "Addr type expects one argument: 'Addr(Int32, Float64)'"),
        ("value: Addr[1](Int32)\n", "Addr[1](...) is invalid; use Addr(...)"),
    ],
)
def test_raw_address_syntax_rejects_multiple_pointees_and_explicit_depth_one(source: str, message: str):
    with pytest.raises(ValueError) as error:
        parse_pyi_text(source, module_name="invalid_raw_address_syntax")
    assert str(error.value) == message
