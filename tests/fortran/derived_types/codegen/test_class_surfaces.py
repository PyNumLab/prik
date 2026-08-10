"""Completed inheritance and polymorphism class surfaces."""

from pathlib import Path

import pytest

from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.semantics.policy_completion import complete_semantic_policies
from prik.codegen import WrapperCodeGenerator, WrapperPlanner

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"
INHERITANCE = FIXTURES / "contracts" / "finheritance_f90" / "finheritance_f90.pyi"


def _plan(contract: Path):
    module = pyi_file_to_semantic_module(contract, module_name=contract.stem)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _surface(plan, name: str):
    return next(
        surface for namespace in plan.namespaces for surface in namespace.classes if name in surface.python_names
    )


def test_inheritance_and_polymorphism_are_completed_before_planning():
    plan = _plan(INHERITANCE)
    base = _surface(plan, "base_shape")
    circle = _surface(plan, "circle")
    derived = next(
        item
        for namespace in plan.namespaces
        for item in namespace.derived_types
        if item.type_identity == circle.type_identity
    )
    describe = next(
        function
        for namespace in plan.namespaces
        for function in namespace.functions
        if function.binding.python_name == "describe_shape"
    )

    assert circle.base_identities == (base.type_identity,)
    assert [field.name for field in derived.fields] == ["size", "radius"]
    assert tuple(variant.python_name for variant in describe.arguments[0].polymorphic.variants) == (
        "box",
        "circle",
        "base_shape",
    )


def test_invalid_class_graph_fails_before_emission():
    plan = _plan(INHERITANCE)
    _surface(plan, "circle").base_identities = (("missing", "base"),)

    with pytest.raises(ValueError, match="missing-or-late-class-base"):
        WrapperCodeGenerator().generate(plan)
