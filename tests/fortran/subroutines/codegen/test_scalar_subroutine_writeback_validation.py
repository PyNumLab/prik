"""Scalar writeback plans are validated before lowering."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import WritebackPhase
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _drop_cleanup(actions):
    return actions[:-1]


def _drop_python_target(actions):
    return tuple(
        replace(action, binding=replace(action.binding, python_result_role=None))
        if action.phase is WritebackPhase.COPY_OUT
        else action
        for action in actions
    )


def _unavailable_source(actions):
    return tuple(
        replace(
            action,
            source_role="missing:value",
            binding=(replace(action.binding, source_role="missing:value") if action.binding is not None else None),
            bridge=(replace(action.bridge, source_role="missing:value") if action.bridge is not None else None),
        )
        for action in actions
    )


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        (_drop_cleanup, "missing-writeback-phase"),
        (_drop_python_target, "missing-python-writeback-target"),
        (_unavailable_source, r"unavailable-.*-role"),
    ],
    ids=["incomplete-phase-group", "no-python-result-target", "unavailable-handoff"],
)
def test_generator_rejects_incomplete_scalar_writeback_plans(edit, diagnostic):
    module = parse_pyi_text(
        'def bump(value: Annotated[Int32, Immutable]) -> Returns["value", Int32]: ...',
        module_name="invalid_writeback",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    root = plan.namespaces[0]
    invalid_function = replace(function, writeback_actions=edit(function.writeback_actions))
    invalid = replace(plan, namespaces=(replace(root, functions=(invalid_function,)), *plan.namespaces[1:]))

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(invalid)
