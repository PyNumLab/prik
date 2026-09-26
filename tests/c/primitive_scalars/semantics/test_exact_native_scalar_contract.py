"""Semantic C contracts preserve exact native scalar identities at call sites."""

import pytest

from prik.parsers.c import parse_c_file
from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.printers.pyi import emit_module
from prik.semantics.c2ir import c_file_to_semantic_module


_LP64_FACTS = {
    "types": {
        "long": {"kind": "integer", "signed": True, "bits": 64, "underlying_c_type": "long"},
        "long long": {
            "kind": "integer",
            "signed": True,
            "bits": 64,
            "underlying_c_type": "long long",
        },
        "int64_t": {"kind": "integer", "signed": True, "bits": 64, "underlying_c_type": "long"},
    }
}

_LLP64_FACTS = {
    "types": {
        "long": {"kind": "integer", "signed": True, "bits": 32, "underlying_c_type": "long"},
        "int32_t": {"kind": "integer", "signed": True, "bits": 32, "underlying_c_type": "int"},
    }
}


def test_target_generation_emits_only_the_native_identity_lost_by_width_normalization():
    module = c_file_to_semantic_module(
        parse_c_file("long keep_long(long value); long long keep_ll(long long value);", filename="exact.h"),
        standard_type_report=_LP64_FACTS,
    )

    text = emit_module(module)

    assert "def keep_long(" in text
    assert "CLong(Arg(0))" not in text
    assert "@native_call([CLongLong(Arg(0))], result=CLongLong(Return(0)))" in text


def test_same_width_long_and_int32_t_still_keep_their_distinct_c_identities():
    module = c_file_to_semantic_module(
        parse_c_file("long convert(long value);", filename="exact.h"),
        standard_type_report=_LLP64_FACTS,
    )

    text = emit_module(module)

    assert "@native_call([CLong(Arg(0))], result=CLong(Return(0)))" in text
    assert "def convert(" in text
    assert "value: Int32" in text
    assert ") -> Int32" in text


@pytest.mark.parametrize(
    ("text", "rendered"),
    [
        pytest.param(
            """from prik.contracts import Arg, CLongLong, Int64, Return, native_call
@native_call([CLongLong(Arg(0))], result=CLongLong(Return(0)))
def convert(value: Int64) -> Int64: ...
""",
            ("@native_call([CLongLong(Arg(0))], result=CLongLong(Return(0)))", "value: Int64"),
            id="scalar-argument-and-result",
        ),
        pytest.param(
            """from prik.contracts import Arg, CLongLong, Int64, native_call
@native_call([CLongLong(Arg(0))])
def update(values: Int64[:]) -> None: ...
""",
            ("@native_call([CLongLong(Arg(0))])", "values: Int64[:]"),
            id="array-element-without-a-public-c-type",
        ),
    ],
)
def test_exact_native_identity_contract_round_trips(text, rendered):
    module = pyi_text_to_semantic_module(text, module_name="exact", native_language="c")

    assert module.functions[0].projection[0].native_c_identity == "CLongLong"
    if module.functions[0].return_type is not None:
        assert module.functions[0].return_type.metadata["native_c_scalar_identity"] == "CLongLong"
    emitted = emit_module(module)
    assert all(fragment in emitted for fragment in rendered)


def test_native_c_identity_requires_exactly_one_positional_reference():
    with pytest.raises(ValueError, match="CLongLong expects positional arguments only"):
        pyi_text_to_semantic_module(
            """from prik.contracts import Arg, CLongLong, Int64, native_call
@native_call([CLongLong(Arg(0), unexpected=True)])
def invalid(value: Int64) -> None: ...
""",
            module_name="invalid",
            native_language="c",
        )


@pytest.mark.parametrize("native_name", ["CChar", "CLongLong", "CLongDoubleComplex"])
def test_native_scalar_names_are_not_public_signature_types(native_name):
    with pytest.raises(ValueError, match="valid only inside @native_call"):
        pyi_text_to_semantic_module(
            f"from prik.contracts import {native_name}\ndef invalid(value: {native_name}) -> None: ...\n",
            module_name="invalid",
            native_language="c",
        )
