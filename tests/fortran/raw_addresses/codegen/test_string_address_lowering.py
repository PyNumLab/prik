"""Fixed-string storage and raw-address plans fail closed when edited."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.ownership import (
    OwnershipOwner,
    StorageMode,
)
from prik.policy.completion import complete_semantic_policies
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
