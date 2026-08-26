"""Direct-plan mutable fixed string storage and raw-address lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.ownership import (
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    ObjectKind,
    OwnershipOwner,
    PythonBarrierAction,
    StorageMode,
    TransferMode,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    ArgumentHandoffMode,
    BridgeDataAction,
    RAW_STRING_ADDRESS_COPY_REASON,
    STRING_STORAGE_COPY_REASON,
)
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _string_address_module():
    module = parse_pyi_text(
        """
def storage(label: String[8][()]) -> None: ...
def raw(label: Addr(String[8])) -> None: ...
""",
        module_name="fixed_string_addresses",
    )
    complete_semantic_policies(module)
    return module


def _string_address_plan():
    return WrapperPlanner().build(_string_address_module())


def _functions(plan):
    return {function.binding.python_name: function for function in plan.namespaces[0].functions}


def test_string_address_plans_keep_completed_ownership_length_and_copy_facts():
    module = _string_address_module()
    functions = _functions(WrapperPlanner().build(module))
    storage = functions["storage"].arguments[0]
    raw = functions["raw"].arguments[0]
    for argument in (storage, raw):
        assert argument.character_length == 8
        assert argument.object_kind is ObjectKind.STRING
        assert argument.ownership_owner is OwnershipOwner.CALLER
        assert argument.transfer_mode is TransferMode.IN_PLACE
        assert argument.destruction_policy is DestructionPolicy.CALLER
        assert argument.binding.codegen_action is CodegenAction.IN_PLACE_ARGUMENT
        assert argument.bridge.codegen_action is CodegenAction.IN_PLACE_ARGUMENT
        assert argument.entrypoint.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
        assert argument.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION
        assert argument.entrypoint.length_handoff_role is None
        assert argument.mutates_native is True
        assert argument.projects_result is False

    assert storage.binding.python_action is PythonBarrierAction.STRING_STORAGE
    assert storage.bridge.native_action is NativeBarrierAction.PASS_STORAGE_ADDRESS
    assert storage.storage_mode is StorageMode.ALIAS
    assert storage.boundary_storage_mode is StorageMode.ALIAS
    assert storage.bridge.copy_reason == STRING_STORAGE_COPY_REASON
    assert raw.binding.python_action is PythonBarrierAction.RAW_ADDRESS
    assert raw.bridge.native_action is NativeBarrierAction.PASS_RAW_ADDRESS
    assert raw.storage_mode is StorageMode.STACK
    assert raw.boundary_storage_mode is StorageMode.STACK
    assert raw.bridge.copy_reason == RAW_STRING_ADDRESS_COPY_REASON


def test_string_addresses_dispatch_to_named_binding_and_bridge_lowering():
    artifacts = WrapperGenerator().generate(_string_address_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    # NumPy-backed storage reports the caller's itemsize beside the address; a
    # raw address has no Python object to measure, so it carries only the width
    # the contract declared.
    assert "void bind_c_storage(void * label, int64_t label_length);" in c_source
    assert "PyArray_TYPE((PyArrayObject *)bound_label_obj) != NPY_STRING" in c_source
    assert "PyArray_NDIM((PyArrayObject *)bound_label_obj) != 0" in c_source
    assert "PyArray_ITEMSIZE((PyArrayObject *)bound_label_obj) != 8" in c_source
    assert "PyArray_ISNOTSWAPPED((PyArrayObject *)bound_label_obj)" in c_source
    assert "PyArray_ISALIGNED((PyArrayObject *)bound_label_obj)" in c_source
    assert "PyArray_ISWRITEABLE((PyArrayObject *)bound_label_obj)" in c_source
    assert "bound_label = PyArray_DATA((PyArrayObject *)bound_label_obj);" in c_source
    assert "void bind_c_raw(void * label);" in c_source
    assert "if (!PyLong_Check(bound_label_obj))" in c_source
    assert "bound_label = PyLong_AsVoidPtr(bound_label_obj);" in c_source
    assert "prik_malloc" not in c_source

    assert 'subroutine bind_c_storage(bound_label, label_length) bind(c, name="bind_c_storage")' in bridge_source
    assert 'subroutine bind_c_raw(bound_label) bind(c, name="bind_c_raw")' in bridge_source
    assert bridge_source.count("type(c_ptr), value :: bound_label") == 2
    assert "integer(c_int64_t), value :: label_length" in bridge_source
    assert "character(kind=c_char, len=label_length) :: label" in bridge_source
    assert "call c_f_pointer(bound_label, label_bytes, [label_length])" in bridge_source
    assert "label_bytes(1:label_length) = transfer(label, label_bytes(1:label_length))" in bridge_source
    assert bridge_source.count("character(kind=c_char, len=8) :: label") == 1
    assert bridge_source.count("call c_f_pointer(bound_label, label_bytes, [8])") == 1
    assert bridge_source.count("label = transfer(label_bytes, label)") == 2
    assert "call native_storage(label)" in bridge_source
    assert "call native_raw(label)" in bridge_source
    assert bridge_source.count("label_bytes(1:8) = transfer(label, label_bytes(1:8))") == 1
    assert "c_null_char" not in "\n".join(line for line in bridge_source.splitlines() if "label_bytes" in line)


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("missing-raw-length", "invalid-string-raw-address-length"),
        ("wrong-owner", "invalid-string-storage-owner"),
        ("runtime-length-role", "unexpected-string-storage-length-handoff"),
        ("wrong-copy-reason", "invalid-string-storage-copy-reason"),
        ("missing-mutation", "string-storage-without-mutation"),
        ("raw-alias-storage", "invalid-string-raw-address-storage"),
        ("raw-projection", "string-raw-address-projects-result"),
    ],
)
def test_string_address_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _string_address_plan()
    functions = _functions(plan)
    storage = functions["storage"].arguments[0]
    raw = functions["raw"].arguments[0]
    if edit == "missing-raw-length":
        # Only a raw address still needs the declared width: NumPy-backed
        # storage may leave it assumed and report the itemsize instead.
        raw.character_length = None
        raw.projected_call_slot.character_length = None
    elif edit == "wrong-owner":
        storage.ownership_owner = OwnershipOwner.NATIVE
    elif edit == "runtime-length-role":
        role = f"{storage.owner_path}:length"
        storage.entrypoint.length_handoff_role = role
    elif edit == "wrong-copy-reason":
        storage.bridge.copy_reason = "an edited reason"
        storage.projected_call_slot.adapter.bridge_copy_reason = "an edited reason"
    elif edit == "missing-mutation":
        storage.mutates_native = False
        storage.binding.writable = False
    elif edit == "raw-alias-storage":
        raw.storage_mode = StorageMode.ALIAS
    else:
        raw.projects_result = True
        raw.result_position = 0

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)
