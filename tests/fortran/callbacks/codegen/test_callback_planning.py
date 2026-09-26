"""Completed callback policy, typed-plan validation, and artifact coverage."""

from pathlib import Path

import pytest

from prik.pipeline.pyi import pyi_file_to_semantic_module, pyi_text_to_semantic_module
from prik.policy.ownership import PythonBarrierAction
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    CallbackOptionalityAction,
    CallbackResultAction,
)
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner

CONTRACT_ROOT = Path(__file__).parents[1] / "end_to_end" / "fixtures" / "contracts"
CONTRACT = CONTRACT_ROOT / "fcallback_all_f90" / "fcallback_all_f90.pyi"


def _module():
    module = pyi_file_to_semantic_module(CONTRACT, module_name="fcallback_all_f90")
    complete_semantic_policies(module)
    return module


def _plan():
    return WrapperPlanner().build(_module())


def _function(plan, name: str):
    return next(
        function for namespace in plan.namespaces for function in namespace.functions if function.symbol_name == name
    )


def _callback_argument(plan, function_name: str):
    return next(argument for argument in _function(plan, function_name).arguments if argument.callback is not None)


def _sources(plan):
    artifacts = WrapperGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")
    return c_source, bridge


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    (
        ("lifecycle", "unbalanced-callback-lifecycle"),
        ("array_roles", "incomplete-callback-array-roles"),
        ("scalar_projection", "inconsistent-callback-scalar-value-projection"),
        ("result", "callback-void-has-transfer"),
        ("entrypoint_parameter", "inconsistent-callback-entrypoint-parameter"),
        ("prototype_optional", "inconsistent-callback-prototype-arguments"),
        ("native_fortran_type", "inconsistent-callback-prototype-arguments"),
        ("optional_value_abi", "invalid-callback-optionality"),
        ("blocked_optionality", "invalid-callback-optionality"),
        ("symbols", "invalid-callback-symbols"),
    ),
)
def test_callback_plan_edits_fail_central_validation_before_backend_emission(edit: str, diagnostic: str):
    plan = _plan()
    if edit == "lifecycle":
        callback = _callback_argument(plan, "apply_value_callback").callback
        callback.lifecycle = callback.lifecycle[:-1]
    elif edit == "array_roles":
        callback = _callback_argument(plan, "apply_array_storage_callback").callback
        callback.arguments[1].extent_roles = ()
    elif edit == "scalar_projection":
        callback = _callback_argument(plan, "apply_scalar_storage_callback").callback
        # A rank-zero storage transfer cannot claim the value projection: an
        # immutable value cannot deliver a write back to the native caller.
        callback.arguments[0].python_action = PythonBarrierAction.SCALAR_VALUE
    elif edit == "result":
        callback = _callback_argument(plan, "apply_value_callback").callback
        callback.result.action = CallbackResultAction.RETURN_VOID
    elif edit == "entrypoint_parameter":
        argument = _callback_argument(plan, "apply_value_callback")
        argument.entrypoint.pass_callback_parameter = True
    elif edit == "prototype_optional":
        callback = _callback_argument(plan, "apply_value_callback").callback
        callback.prototype.arguments[0].optional = True
    elif edit == "native_fortran_type":
        callback = _callback_argument(plan, "apply_value_callback").callback
        callback.prototype.arguments[0].native_fortran_type = "logical(kind=8)"
    elif edit == "optional_value_abi":
        callback = _callback_argument(plan, "apply_value_callback").callback
        callback.arguments[0].optionality = CallbackOptionalityAction.NULL_DATA_POINTER
    elif edit == "blocked_optionality":
        callback = _callback_argument(plan, "apply_value_callback").callback
        callback.arguments[0].optionality = CallbackOptionalityAction.BLOCKED
    else:
        callback = _callback_argument(plan, "apply_value_callback").callback
        callback.entrypoint.support_procedure.symbol_name = callback.bridge.adapter_symbol

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)


def test_nogil_callback_call_releases_outer_envelope_and_reacquires_in_trampoline():
    source = CONTRACT.read_text(encoding="utf-8")
    source = source.replace("native_call, prototype", "native_call, nogil, prototype", 1)
    source = source.replace(
        "@native_call([Arg(0), Addr(Arg(1))])\ndef apply_value_callback",
        "@nogil\n@native_call([Arg(0), Addr(Arg(1))])\ndef apply_value_callback",
        1,
    )
    module = pyi_text_to_semantic_module(source, module_name="fcallback_all_f90")
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)

    assert _function(plan, "apply_value_callback").binding.release_gil is True
    c_source, _ = _sources(plan)
    function_start = c_source.index("static PyObject * wrap_apply_value_callback")
    function_end = c_source.index("static PyObject * wrap_apply_scalar_storage_callback")
    function_source = c_source[function_start:function_end]
    assert "Py_BEGIN_ALLOW_THREADS" in function_source
    assert "Py_END_ALLOW_THREADS" in function_source
    assert "PyGILState_Ensure()" in c_source
    assert "PyGILState_Release(" in c_source


def test_callback_array_result_diagnostic_uses_the_contract_spelling():
    """A rejected shape is reported the way a contract would spell it.

    A function result has no caller descriptor to measure, so a runtime extent
    there is refused; the message names the extent the author wrote rather than
    the explicit step the IR stores.
    """
    module = pyi_text_to_semantic_module(
        """
from prik.contracts import Float64, In, prototype

@prototype
def strided_result(x: In(Float64)) -> Float64[::]: ...

def apply(callback: strided_result) -> None: ...
""",
        module_name="callback_strided_result",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)

    with pytest.raises(ValueError, match=r"runtime extents \['::'\]"):
        _sources(plan)
