"""Scalar function optional, descriptor, and writeback lowering tests."""

from __future__ import annotations

from dataclasses import replace
from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import WritebackPhase
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _artifacts(module):
    complete_semantic_policies(module)
    return WrapperGenerator().generate(WrapperPlanner().build(module))


def _source(artifacts, suffix: str) -> str:
    return next(item.text for item in artifacts.sources if item.path.name.endswith(suffix))


def _replace_root_function(plan, function):
    root = plan.namespaces[0]
    return replace(plan, namespaces=(replace(root, functions=(function,)), *plan.namespaces[1:]))


def test_scalar_writeback_is_an_explicit_binding_lifecycle_result():
    module = parse_pyi_text(
        'def bump(value: Annotated[Int32, Immutable]) -> Returns["value", Int32]: ...',
        module_name="scalar_writeback",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    actions = plan.namespaces[0].functions[0].writeback_actions

    assert tuple(action.phase for action in actions) == tuple(WritebackPhase)
    assert actions[0].binding is not None
    assert actions[1].bridge is not None
    assert actions[2].binding.python_result_role == "scalar_writeback.bump.value:python-result"
    assert actions[3].binding is not None

    artifacts = WrapperGenerator().generate(plan)
    c_source = _source(artifacts, ".c")
    fortran_source = _source(artifacts, ".f90")

    assert "void bind_c_bump(int32_t * value);" in c_source
    assert "bind_c_bump(&bound_value);" in c_source
    assert "PyObject * result_obj = NULL;" in c_source
    assert "result_obj = prik_int32_to_python(&bound_value);" in c_source
    assert "subroutine bind_c_bump(value)" in fortran_source
    assert "call native_bump(value)" in fortran_source
