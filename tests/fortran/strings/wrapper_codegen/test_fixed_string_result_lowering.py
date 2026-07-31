"""Direct-plan fixed string result and hidden-output lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.models import RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA
from x2py.semantics.ownership import (
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    ObjectKind,
    OwnershipOwner,
    PythonBarrierAction,
    StorageMode,
    TransferMode,
)
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import BridgeDataAction
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner
from x2py.wrapper_codegen.plan import DatatypeFamily


_COPY_REASON = "copy fixed-length Fortran character output into C-owned null-terminated storage"


def _fixed_string_module():
    module = parse_pyi_text(
        """
def direct_label() -> String[8]: ...

@native_call([Return("label", 0)])
def hidden_label() -> String[8]: ...
""",
        module_name="fixed_string_results",
    )
    complete_semantic_policies(module)
    return module


def _fixed_string_plan():
    return WrapperPlanner().build(_fixed_string_module())


def test_fixed_strings_reuse_ordered_result_plans_with_completed_length_and_copy_facts():
    module = _fixed_string_module()
    plan = WrapperPlanner().build(module)
    functions = {function.binding.python_name: function for function in plan.namespaces[0].functions}
    direct = functions["direct_label"].results[0]
    hidden = functions["hidden_label"].results[0]

    for result in (direct, hidden):
        assert result.datatype_family is DatatypeFamily.STRING
        assert result.character_length == 8
        assert result.object_kind is ObjectKind.STRING
        assert result.ownership_owner is OwnershipOwner.PYTHON
        assert result.transfer_mode is TransferMode.COPY_RETURN
        assert result.destruction_policy is DestructionPolicy.PYTHON_REFCOUNT
        assert result.storage_mode is StorageMode.STACK
        assert result.boundary_storage_mode is StorageMode.STACK
        assert result.nullable is False
        assert result.binding.python_action is PythonBarrierAction.NONE
        assert result.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION
        assert result.bridge.copy_reason == _COPY_REASON

    assert direct.source_kind == "direct_return"
    assert direct.binding.codegen_action is CodegenAction.COPY_OUT
    assert direct.bridge.native_action is NativeBarrierAction.NONE
    assert direct.native_call_slot is None

    assert hidden.source_kind == "hidden_output"
    assert hidden.binding.codegen_action is CodegenAction.COPY_OUT
    assert hidden.bridge.native_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert hidden.native_call_slot is functions["hidden_label"].native_call_slots[0]
    assert hidden.native_call_slot.object_kind is ObjectKind.STRING
    assert hidden.native_call_slot.character_length == hidden.character_length


def test_fixed_string_results_dispatch_to_named_binding_and_bridge_copy_lowering():
    artifacts = WrapperCodeGenerator().generate(_fixed_string_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "void * bind_c_direct_label(void);" in c_source
    assert "void * result = NULL;" in c_source
    assert "result = bind_c_direct_label();" in c_source
    assert "if (result == NULL)" in c_source
    assert 'Py_BuildValue("s", (const char *)result)' in c_source
    assert "free(result);" in c_source
    assert "void bind_c_hidden_label(void ** label);" in c_source
    assert "bind_c_hidden_label(&label);" in c_source
    assert 'Py_BuildValue("s", (const char *)label)' in c_source
    assert "free(label);" in c_source

    assert 'function bind_c_direct_label() result(result) bind(c, name="bind_c_direct_label")' in bridge_source
    assert "type(c_ptr) :: result" in bridge_source
    assert "character(kind=c_char, len=8) :: result_value" in bridge_source
    assert "result_value = native_direct_label()" in bridge_source
    assert "result = c_malloc(9_c_size_t)" in bridge_source
    assert "result_copy(1:8) = transfer(result_value, result_copy(1:8))" in bridge_source
    assert "result_copy(9) = c_null_char" in bridge_source
    assert 'subroutine bind_c_hidden_label(label) bind(c, name="bind_c_hidden_label")' in bridge_source
    assert "character(kind=c_char, len=8) :: label_value" in bridge_source
    assert "call native_hidden_label(label_value)" in bridge_source
    assert "label = c_malloc(9_c_size_t)" in bridge_source


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("missing-length", "invalid-result-character-length"),
        ("wrong-copy", "invalid-string-result-data-action"),
        ("wrong-copy-reason", "invalid-string-result-copy-reason"),
        ("wrong-object-kind", "invalid-scalar-result-datatype-family"),
        ("wrong-owner", "invalid-string-result-owner"),
        ("wrong-transfer", "invalid-string-result-transfer"),
        ("wrong-destruction", "invalid-string-result-destruction"),
        ("wrong-storage", "invalid-string-result-storage"),
        ("wrong-boundary-storage", "invalid-string-result-boundary-storage"),
        ("nullable", "nullable-fixed-string-result"),
        ("slot-length-drift", "inconsistent-result-character-length"),
    ],
)
def test_fixed_string_result_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _fixed_string_plan()
    direct, hidden = (
        plan.namespaces[0].functions[0].results[0],
        plan.namespaces[0].functions[1].results[0],
    )
    if edit == "missing-length":
        direct.character_length = None
    elif edit == "wrong-copy":
        direct.bridge.data_action = BridgeDataAction.DIRECT_TRANSFER
        direct.bridge.copy_reason = None
    elif edit == "wrong-copy-reason":
        direct.bridge.copy_reason = "an edited reason"
    elif edit == "wrong-object-kind":
        direct.object_kind = ObjectKind.SCALAR
    elif edit == "wrong-owner":
        direct.ownership_owner = OwnershipOwner.NATIVE
    elif edit == "wrong-transfer":
        direct.transfer_mode = TransferMode.BORROWED_VIEW
    elif edit == "wrong-destruction":
        direct.destruction_policy = DestructionPolicy.NATIVE_OWNER
    elif edit == "wrong-storage":
        direct.storage_mode = StorageMode.HEAP
    elif edit == "wrong-boundary-storage":
        direct.boundary_storage_mode = StorageMode.HEAP
    elif edit == "nullable":
        direct.nullable = True
    else:
        hidden.native_call_slot.character_length = 7

    with pytest.raises(ValueError, match=diagnostic):
        WrapperCodeGenerator().generate(plan)


def test_fixed_string_result_policy_uses_ordered_mixed_result_cleanup():
    module = parse_pyi_text(
        """
@native_call([Return("status", 1)])
def mixed() -> tuple[String[8], Int32]: ...
""",
        module_name="mixed_string_results",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is True
    assert policy.blockers == ()
    assert policy.results[0].ownership.kind is ObjectKind.STRING
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    assert tuple(result.result_position for result in function.results) == (0, 1)

    c_source = next(
        source.text for source in WrapperCodeGenerator().generate(plan).sources if source.path.suffix == ".c"
    )
    assert "free(result);" in c_source
    assert "PyTuple_New(2)" in c_source
    assert "Py_DECREF(result_0_obj);" in c_source


def test_fixed_string_result_policy_blocks_status_error_until_failure_release_is_planned():
    module = parse_pyi_text(
        """
@raises(status="status", success=0)
@native_call([Return("label", 0), Return("status", 1)])
def label() -> tuple[String[8], Int32]: ...
""",
        module_name="string_result_with_status",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert "fixed string result with native status error requires planned failure-path release" in policy.blockers
    assert len(policy.results) == 1
    assert policy.results[0].ownership.kind is ObjectKind.STRING
