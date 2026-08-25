"""Reviewed TA-Lib v0.7.1 public C surface and explicit exclusions."""

from __future__ import annotations

import ast
from pathlib import Path


PUBLIC_FUNCTION_COUNT = 522
WRAPPED_FUNCTION_COUNT = 324
DOUBLE_INDICATOR_COUNT = 161
FLOAT_INDICATOR_COUNT = 161
LIFECYCLE_FUNCTIONS = ("TA_Initialize", "TA_Shutdown")
SETTING_FUNCTIONS = (
    "TA_SetUnstablePeriod",
    "TA_GetUnstablePeriod",
    "TA_SetCompatibility",
    "TA_GetCompatibility",
    "TA_SetCandleSettings",
    "TA_RestoreCandleDefaultSettings",
)
POINTER_RESULT_FUNCTIONS = (
    "TA_GetVersionString",
    "TA_GetVersionMajor",
    "TA_GetVersionMinor",
    "TA_GetVersionPatch",
    "TA_GetVersionDate",
    "TA_GetVersionTime",
    "TA_GetVersionBuild",
    "TA_GetVersionExtra",
)
RECORD_METADATA_FUNCTIONS = ("TA_SetRetCodeInfo",)
ABSTRACTION_FUNCTIONS = (
    "TA_GroupTableAlloc",
    "TA_GroupTableFree",
    "TA_FuncTableAlloc",
    "TA_FuncTableFree",
    "TA_GetFuncHandle",
    "TA_GetFuncInfo",
    "TA_ForEachFunc",
    "TA_GetInputParameterInfo",
    "TA_GetOptInputParameterInfo",
    "TA_GetOutputParameterInfo",
    "TA_ParamHolderAlloc",
    "TA_ParamHolderFree",
    "TA_SetInputParamIntegerPtr",
    "TA_SetInputParamRealPtr",
    "TA_SetInputParamPricePtr",
    "TA_SetOptInputParamInteger",
    "TA_SetOptInputParamReal",
    "TA_SetOutputParamIntegerPtr",
    "TA_SetOutputParamRealPtr",
    "TA_GetLookback",
    "TA_CallFunc",
    "TA_FunctionDescriptionXML",
)


def _contract_functions() -> tuple[str, ...]:
    """Read the ordered functions from the reviewed semantic contract."""
    contract = Path(__file__).with_name("ta_lib_api.pyi")
    module = ast.parse(contract.read_text(encoding="utf-8"), filename=str(contract))
    names = tuple(node.name for node in module.body if isinstance(node, ast.FunctionDef))
    if len(names) != len(set(names)):
        raise ValueError("TA-Lib semantic contract contains duplicate functions")
    return names


WRAPPED_FUNCTIONS = _contract_functions()
FLOAT_INDICATOR_FUNCTIONS = tuple(name for name in WRAPPED_FUNCTIONS if name.startswith("TA_S_"))
DOUBLE_INDICATOR_FUNCTIONS = tuple(
    name for name in WRAPPED_FUNCTIONS if name not in LIFECYCLE_FUNCTIONS and not name.startswith("TA_S_")
)
INDICATOR_FUNCTIONS = (*DOUBLE_INDICATOR_FUNCTIONS, *FLOAT_INDICATOR_FUNCTIONS)
LOOKBACK_FUNCTIONS = tuple(f"{name}_Lookback" for name in DOUBLE_INDICATOR_FUNCTIONS)
EXCLUDED_PUBLIC_FUNCTIONS = {
    **dict.fromkeys(LOOKBACK_FUNCTIONS, "lookback replaced by returned beginning and count"),
    **dict.fromkeys(SETTING_FUNCTIONS, "example uses TA-Lib default global settings"),
    **dict.fromkeys(POINTER_RESULT_FUNCTIONS, "library-owned pointer result"),
    **dict.fromkeys(RECORD_METADATA_FUNCTIONS, "record output"),
    **dict.fromkeys(
        ABSTRACTION_FUNCTIONS,
        "optional abstraction API uses records, callbacks, multi-level pointers, or pointer results",
    ),
}
