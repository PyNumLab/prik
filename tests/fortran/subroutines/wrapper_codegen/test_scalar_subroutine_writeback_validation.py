"""Scalar subroutine optional, descriptor, and writeback lowering tests."""

from __future__ import annotations

from dataclasses import replace
import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy import WritebackPhase
from prik.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


def _artifacts(module):
    complete_semantic_policies(module)
    return WrapperCodeGenerator().generate(WrapperPlanner().build(module))


def _source(artifacts, suffix: str) -> str:
    return next(item.text for item in artifacts.sources if item.path.name.endswith(suffix))


def _replace_root_function(plan, function):
    root = plan.namespaces[0]
    return replace(plan, namespaces=(replace(root, functions=(function,)), *plan.namespaces[1:]))


def test_generator_rejects_incomplete_writeback_phase_group():
    module = parse_pyi_text(
        'def bump(value: Annotated[Int32, Immutable]) -> Returns["value", Int32]: ...',
        module_name="invalid_writeback",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    invalid = _replace_root_function(
        plan,
        replace(function, writeback_actions=function.writeback_actions[:-1]),
    )

    with pytest.raises(ValueError, match="missing-writeback-phase"):
        WrapperCodeGenerator().generate(invalid)


def test_generator_rejects_writeback_without_python_result_target():
    module = parse_pyi_text(
        'def bump(value: Annotated[Int32, Immutable]) -> Returns["value", Int32]: ...',
        module_name="invalid_writeback_target",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    actions = tuple(
        replace(action, binding=replace(action.binding, python_result_role=None))
        if action.phase is WritebackPhase.COPY_OUT
        else action
        for action in function.writeback_actions
    )
    invalid = _replace_root_function(plan, replace(function, writeback_actions=actions))

    with pytest.raises(ValueError, match="missing-python-writeback-target"):
        WrapperCodeGenerator().generate(invalid)


def test_generator_rejects_writeback_from_an_unavailable_handoff():
    module = parse_pyi_text(
        'def bump(value: Annotated[Int32, Immutable]) -> Returns["value", Int32]: ...',
        module_name="invalid_writeback_source",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    actions = tuple(
        replace(
            action,
            source_role="missing:value",
            binding=(replace(action.binding, source_role="missing:value") if action.binding is not None else None),
            bridge=(replace(action.bridge, source_role="missing:value") if action.bridge is not None else None),
        )
        for action in function.writeback_actions
    )
    invalid = _replace_root_function(plan, replace(function, writeback_actions=actions))

    with pytest.raises(ValueError, match=r"unavailable-.*-role"):
        WrapperCodeGenerator().generate(invalid)
