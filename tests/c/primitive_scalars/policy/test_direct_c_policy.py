"""Completed-policy evidence for the direct-only C primitive lane."""

import pytest

from prik.parsers.c import parse_c_file
from prik.policy.completion import complete_semantic_policies
from prik.semantics.c2ir import c_file_to_semantic_module
from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.semantics.native_contract import validate_pyi_native_contract


def _complete(source: str):
    module = c_file_to_semantic_module(parse_c_file(source, filename="api.c"))
    complete_semantic_policies(module)
    return module.functions[0].metadata["resolved_function_wrapper_policy"]


def test_supported_c_scalar_policy_selects_direct_c_abi_without_a_bridge_facet():
    policy = _complete("double add(double left, double right) { return left + right; }\n")

    assert policy.supported is True
    assert policy.entrypoint_action.value == "direct_c_abi"
    assert policy.direct_c_abi.result.source_spelling == "double"
    assert tuple(item.source_spelling for item in policy.direct_c_abi.parameters) == ("double", "double")


@pytest.mark.parametrize(
    ("source", "diagnostic"),
    [
        ("double *result(void);", "C_DIRECT_POINTER_RESULT"),
        ("void values(double input[3]);", "C_DIRECT_ARRAY_DECLARATOR:input"),
        ("void indirect(double **input);", "C_DIRECT_POINTER_DEPTH:input"),
        ("void callback(void (*action)(int));", "C_DIRECT_CALLBACK:action"),
        ("struct state { int value; }; void consume(struct state value);", "C_DIRECT_UNRESOLVED_PRIMITIVE_ABI:value"),
        ("int total(int first, ...);", "C_DIRECT_VARIADIC_FUNCTION"),
        ("static double hidden(double value);", "C_DIRECT_TRANSLATION_UNIT_LOCAL_SYMBOL"),
        ("void volatile_value(volatile double value);", "C_DIRECT_UNSUPPORTED_QUALIFIER:value"),
        ("void atomic_value(_Atomic(int) value);", "C_DIRECT_UNSUPPORTED_QUALIFIER:value"),
    ],
)
def test_ineligible_c_operations_fail_with_a_stable_preplanning_diagnostic(source: str, diagnostic: str):
    module = c_file_to_semantic_module(parse_c_file(source, filename="unsupported.c"))

    with pytest.raises(ValueError, match=diagnostic):
        complete_semantic_policies(module)


@pytest.mark.parametrize(
    ("annotation", "diagnostic"),
    [
        ("Addr(Float64)", "C_DIRECT_RAW_ADDRESS:value"),
        ("Float64 | None", "C_DIRECT_NULLABLE_POINTER:value"),
        ("Float64[:] | None", "C_DIRECT_NULLABLE_POINTER:value"),
        ("Float64[()] | None", "C_DIRECT_NULLABLE_POINTER:value"),
        ("Bool[:]", "C_DIRECT_BOOL_ARRAY:value"),
    ],
)
def test_out_of_scope_c_pointer_contracts_fail_before_planning(annotation: str, diagnostic: str):
    imports = "Addr, Bool, Float64" if "Addr" in annotation else "Bool, Float64"
    module = pyi_text_to_semantic_module(
        f"from prik.contracts import {imports}\ndef f(value: {annotation}) -> None: ...\n",
        module_name="unsupported_contract",
        native_language="c",
    )
    validate_pyi_native_contract([module])

    with pytest.raises(ValueError, match=diagnostic):
        complete_semantic_policies(module)
