"""Phase 10 callback policy, typed-plan, validation, and artifact coverage."""

from pathlib import Path

import pytest

from x2py.pipeline.pyi import pyi_file_to_semantic_module
from x2py.semantics import models
from x2py.semantics.ownership import PythonBarrierAction
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import (
    CallbackABIKind,
    CallbackGILAction,
    CallbackLifecycleAction,
    CallbackResultAction,
    CallbackThreadAction,
    CallbackTransferAction,
    ExternalDeclarationMode,
)
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner
from x2py.wrapper_codegen.plan import DatatypeFamily

CONTRACT = (
    Path(__file__).parents[1]
    / "wrapper"
    / "fortran"
    / "callbacks"
    / "contracts"
    / "fcallback_all_f90"
    / "fcallback_all_f90.pyi"
)
ARRAY_CONTRACT = CONTRACT.parents[1] / "fcallback_array_f90" / "fcallback_array_f90.pyi"


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
    artifacts = WrapperCodeGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")
    return c_source, bridge


def test_callback_policy_completes_value_default_and_explicit_reference_before_planning():
    module = _module()
    policies = {
        function.name: function.metadata[models.RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
        for function in module.functions
    }

    scalar = policies["apply_scalar_storage_callback"].arguments[0].callback
    assert scalar.lifecycle == tuple(CallbackLifecycleAction)
    assert scalar.thread_action is CallbackThreadAction.REQUIRE_ENTERING_THREAD
    assert scalar.gil_actions == (CallbackGILAction.ACQUIRE_GIL, CallbackGILAction.RELEASE_GIL)
    assert tuple(transfer.abi for transfer in scalar.arguments) == (CallbackABIKind.REFERENCE,) * 3
    assert tuple(transfer.adapter_action for transfer in scalar.arguments) == (CallbackTransferAction.COPY_IN,) * 3
    assert tuple(transfer.python_action for transfer in scalar.arguments) == (PythonBarrierAction.SCALAR_VALUE,) * 3

    array = policies["apply_array_storage_callback"].arguments[0].callback
    assert array.arguments[0].abi is CallbackABIKind.REFERENCE
    assert array.arguments[0].adapter_action is CallbackTransferAction.COPY_IN
    assert array.arguments[0].python_action is PythonBarrierAction.SCALAR_VALUE
    assert array.arguments[1].abi is CallbackABIKind.DATA_AND_SHAPE
    assert array.arguments[1].array.shape == ("count",)

    string = policies["apply_string_storage_callback"].arguments[0].callback
    assert all(transfer.abi is CallbackABIKind.DATA_AND_LENGTH for transfer in string.arguments)
    assert tuple(transfer.character_length for transfer in string.arguments) == (8, 8, 8)

    derived = policies["apply_point_callback"].arguments[0].callback
    assert derived.arguments[0].derived_type_identity == ("fcallback_all_f90", "point_t")
    assert derived.result.action is CallbackResultAction.RETURN_DERIVED_ADDRESS


def test_callback_plan_projects_one_explicit_site_and_stable_roles_per_argument():
    plan = _plan()
    callbacks = [
        argument.callback
        for namespace in plan.namespaces
        for function in namespace.functions
        for argument in function.arguments
        if argument.callback is not None
    ]

    assert all(
        _callback_argument(plan, function).datatype_family is DatatypeFamily.CALLBACK
        for function in (
            "apply_value_callback",
            "apply_scalar_storage_callback",
            "apply_array_storage_callback",
            "apply_string_storage_callback",
            "apply_point_callback",
        )
    )
    assert all(
        _function(plan, function).binding.hold_gil
        for function in (
            "apply_value_callback",
            "apply_scalar_storage_callback",
            "apply_array_storage_callback",
            "apply_string_storage_callback",
            "apply_point_callback",
        )
    )
    assert len({callback.context_current_symbol for callback in callbacks}) == len(callbacks)
    assert len({callback.adapter_symbol for callback in callbacks}) == len(callbacks)
    assert len({callback.trampoline_symbol for callback in callbacks}) == len(callbacks)


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    (
        ("lifecycle", "unbalanced-callback-lifecycle"),
        ("array_roles", "incomplete-callback-array-roles"),
        ("scalar_projection", "inconsistent-callback-scalar-value-projection"),
        ("result", "callback-void-has-transfer"),
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
        callback.arguments[0].python_action = PythonBarrierAction.SCALAR_STORAGE
    elif edit == "result":
        callback = _callback_argument(plan, "apply_value_callback").callback
        callback.result.action = CallbackResultAction.RETURN_VOID
    else:
        callback = _callback_argument(plan, "apply_value_callback").callback
        callback.trampoline_symbol = callback.adapter_symbol

    with pytest.raises(ValueError, match=diagnostic):
        WrapperCodeGenerator().generate(plan)


def test_callback_artifacts_use_linear_context_adapter_and_trampoline_paths():
    c_source, bridge = _sources(_plan())

    assert "static _Thread_local" in c_source
    assert "PyThread_get_thread_ident()" in c_source
    assert "PyGILState_Ensure()" in c_source
    assert "PyGILState_Release(" in c_source
    assert "PyErr_PrintEx(0);" in c_source
    assert "abort();" in c_source
    assert "Py_BEGIN_ALLOW_THREADS" not in c_source
    assert "Py_END_ALLOW_THREADS" not in c_source

    assert "integer(c_int32_t), value :: value" in bridge
    assert "integer(c_int32_t) :: count" in bridge
    assert "external :: x2py_callback_adapter" in bridge
    assert 'bind(c, name="x2py_callback_trampoline' in bridge
    assert "size(values_callback_storage, dim=1, kind=c_int64_t)" in bridge
    assert "int(len(read_label_callback_storage), kind=c_int64_t)" in bridge
    assert "x2py_scalar_to_numpy(NPY_INT32, &value)" in c_source
    assert "x2py_scalar_to_numpy(NPY_INT32, count_data)" in c_source
    assert bridge.count("call native_apply_array_storage_callback(") == 1
    assert "call callback(" not in bridge
    assert max(map(len, bridge.splitlines())) <= 132


def test_callback_declaration_uses_external_unless_prototype_requires_explicit_interface():
    module = pyi_file_to_semantic_module(ARRAY_CONTRACT, module_name="fcallback_array_f90")
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)

    reduce = _callback_argument(plan, "apply_reduce").callback
    transform = _callback_argument(plan, "apply_transform").callback
    assert reduce.declaration_mode is ExternalDeclarationMode.IMPLICIT_EXTERNAL
    assert transform.declaration_mode is ExternalDeclarationMode.EXPLICIT_INTERFACE

    _, bridge = _sources(plan)
    assert f"real(c_double), external :: {reduce.adapter_symbol}" in bridge
    assert f"procedure({transform.adapter_symbol}_prototype) :: {transform.adapter_symbol}" in bridge
    assert f"{transform.adapter_symbol}_prototype => transform_callback" in bridge


def test_optional_callback_retains_one_exact_policy_blocker():
    module = pyi_file_to_semantic_module(CONTRACT, module_name="fcallback_all_f90")
    function = next(item for item in module.functions if item.name == "apply_value_callback")
    function.arguments[0].optional = True
    complete_semantic_policies(module)

    with pytest.raises(ValueError, match="unsupported optional callback"):
        WrapperPlanner().build(module)
