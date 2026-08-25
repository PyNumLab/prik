"""Fail-closed public-surface and every-entrypoint runtime audits."""

from __future__ import annotations

import ast
import os
from pathlib import Path

import numpy as np
import pytest

from ..api_inventory import (
    DOUBLE_INDICATOR_COUNT,
    DOUBLE_INDICATOR_FUNCTIONS,
    EXCLUDED_PUBLIC_FUNCTIONS,
    FLOAT_INDICATOR_COUNT,
    FLOAT_INDICATOR_FUNCTIONS,
    INDICATOR_FUNCTIONS,
    LIFECYCLE_FUNCTIONS,
    LOOKBACK_FUNCTIONS,
    PUBLIC_FUNCTION_COUNT,
    SETTING_FUNCTIONS,
    WRAPPED_FUNCTION_COUNT,
    WRAPPED_FUNCTIONS,
)


pytestmark = pytest.mark.real_library
_ARRAY_DTYPES = {
    "Float32": np.float32,
    "Float64": np.float64,
    "Int": np.intc,
}
_SCALAR_VALUES = {
    "Float32": np.float32(0.5),
    "Float64": np.float64(0.5),
    "Int": np.intc(2),
}


def _contract_functions(contract: Path) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(contract.read_text(encoding="utf-8"), filename=str(contract))
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("TA_")}


def _annotation_name(annotation: ast.expr | None) -> str:
    if isinstance(annotation, ast.Name):
        return annotation.id
    if isinstance(annotation, ast.Subscript) and isinstance(annotation.value, ast.Name):
        return annotation.value.id
    raise AssertionError(f"unexpected TA-Lib annotation: {ast.dump(annotation)}")


def _argument_value(argument: ast.arg, *, invalid_start: bool = False):
    if invalid_start and argument.arg == "startIdx":
        return np.intc(-1)
    annotation = argument.annotation
    type_name = _annotation_name(annotation)
    if isinstance(annotation, ast.Subscript):
        return np.zeros(1, dtype=_ARRAY_DTYPES[type_name])
    return _SCALAR_VALUES[type_name]


def test_reviewed_surface_accounts_for_every_pinned_public_function(talib):
    build_root = Path(os.environ["TA_LIB_BUILD_ROOT"])
    public = set(_contract_functions(build_root / "prik/contract/ta_lib_public_api.pyi"))
    authored = set(_contract_functions(Path(os.environ["PRIK_TALIB_CONTRACT"])))
    built = {name for name in dir(talib) if not name.startswith("_")}
    reviewed = set(WRAPPED_FUNCTIONS)
    excluded = set(EXCLUDED_PUBLIC_FUNCTIONS)

    assert len(public) == PUBLIC_FUNCTION_COUNT
    assert len(reviewed) == WRAPPED_FUNCTION_COUNT
    assert public == reviewed | excluded
    assert reviewed.isdisjoint(excluded)
    assert authored == reviewed
    assert built == reviewed


def test_reviewed_categories_have_the_pinned_complete_counts():
    assert len(DOUBLE_INDICATOR_FUNCTIONS) == DOUBLE_INDICATOR_COUNT
    assert len(FLOAT_INDICATOR_FUNCTIONS) == FLOAT_INDICATOR_COUNT
    assert len(LOOKBACK_FUNCTIONS) == DOUBLE_INDICATOR_COUNT
    assert len(INDICATOR_FUNCTIONS) == DOUBLE_INDICATOR_COUNT + FLOAT_INDICATOR_COUNT
    assert len(WRAPPED_FUNCTIONS) == WRAPPED_FUNCTION_COUNT
    assert len(LIFECYCLE_FUNCTIONS) == 2
    assert len(SETTING_FUNCTIONS) == 6


def test_every_indicator_entrypoint_crosses_the_generated_wrapper(talib):
    functions = _contract_functions(Path(os.environ["PRIK_TALIB_CONTRACT"]))

    for name in INDICATOR_FUNCTIONS:
        arguments = [_argument_value(argument, invalid_start=True) for argument in functions[name].args.args]
        result = getattr(talib, name)(*arguments)
        assert isinstance(result, tuple), name
        assert int(result[0]) == 12, name  # TA_OUT_OF_RANGE_START_INDEX
