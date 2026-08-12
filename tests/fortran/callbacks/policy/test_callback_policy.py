from pathlib import Path

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from prik.pipeline.preprocessing import PreprocessingConfig
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    CallbackABIKind,
    CallbackTransferAction,
    FunctionWrapperPolicy,
)
from prik.policy.construction import completed_function_wrapper_policy

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"


def _source_semantic_module(filename: str, *, module_name: str):
    source = FIXTURES / filename
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


def test_source_callback_value_default_and_explicit_reference_are_completed():
    module = _source_semantic_module("fcallback_all_f90.f90", module_name="fcallback_all_f90")
    function = next(item for item in module.functions if item.name == "apply_value_callback")
    policy = completed_function_wrapper_policy(function)
    transfer = policy.arguments[0].callback.arguments[0]

    assert transfer.abi is CallbackABIKind.VALUE
    assert transfer.passed_by_value is True
    assert transfer.adapter_action is CallbackTransferAction.COPY_IN

    array_function = next(item for item in module.functions if item.name == "apply_array_storage_callback")
    array_policy = completed_function_wrapper_policy(array_function)
    extent = array_policy.arguments[0].callback.arguments[0]
    assert extent.abi is CallbackABIKind.REFERENCE
    assert extent.passed_by_value is False
    assert extent.adapter_action is CallbackTransferAction.COPY_IN


@pytest.mark.parametrize(
    ("prototype", "blocker"),
    [
        (
            "def callback_shape(value: Allocatable[Float64]) -> None: ...",
            "callback argument 'value' uses unsupported allocatable, pointer, polymorphic, or assumed-type storage",
        ),
        (
            "def callback_shape(value: Float64 = ...) -> None: ...",
            "callback argument 'value' cannot be optional",
        ),
        (
            "def callback_shape() -> Pointer[Float64]: ...",
            "callback result uses unsupported allocatable, pointer, polymorphic, or assumed-type storage",
        ),
    ],
)
def test_callback_descriptor_and_optional_forms_are_blocked_before_codegen(prototype: str, blocker: str):
    module = parse_pyi_text(
        f"""
@prototype
{prototype}

def apply(callback: callback_shape) -> None: ...
""",
        module_name="unsupported_callback_shape",
    )

    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is False
    assert blocker in policy.blockers
