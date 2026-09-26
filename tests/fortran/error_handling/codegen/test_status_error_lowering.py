"""Status-error plan validation before lowering."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import DatatypeFamily, WrapperPlanner


RUNTIME_POLICY_CONTRACT = (
    Path(__file__).resolve().parents[1]
    / "end_to_end"
    / "fixtures"
    / "edited_contracts"
    / "runtime_policy"
    / "fruntime_policy_f90.pyi"
)


def _runtime_plan():
    module = pyi_file_to_semantic_module(RUNTIME_POLICY_CONTRACT, module_name="fruntime_policy_f90")
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _drop_message_copy_reason(function):
    return replace(
        function,
        entrypoint=replace(
            function.entrypoint,
            projected_slots=tuple(
                replace(slot, adapter=replace(slot.adapter, bridge_copy_reason=None))
                if slot.datatype_family is DatatypeFamily.STRING
                else slot
                for slot in function.entrypoint.projected_slots
            ),
        ),
    )


def _drop_status_role(function):
    return replace(
        function,
        binding=replace(
            function.binding,
            status_error=replace(function.binding.status_error, status_role="missing:status"),
        ),
    )


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        (_drop_message_copy_reason, "missing-bridge-copy-reason"),
        (_drop_status_role, "missing-status-result-role"),
    ],
    ids=["message-copy-without-reason", "status-error-without-status-result"],
)
def test_status_error_plan_edits_fail_before_backend_lowering(edit, diagnostic):
    """A status error must name a produced status and a completed message copy.

    Runtime status projection, message text, and GIL placement are proved in
    ``end_to_end/test_status_projection.py``.
    """
    plan = _runtime_plan()
    root = plan.namespaces[0]
    functions = tuple(
        edit(function) if function.binding.python_name == "solve" else function for function in root.functions
    )
    invalid = replace(plan, namespaces=(replace(root, functions=functions), *plan.namespaces[1:]))

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(invalid)
