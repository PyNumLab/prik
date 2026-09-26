"""Completed inheritance and polymorphism class surfaces."""

from pathlib import Path

import pytest

from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner

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


def test_invalid_class_graph_fails_before_emission():
    plan = _plan(INHERITANCE)
    _surface(plan, "Circle").base_identities = (("missing", "base"),)

    with pytest.raises(ValueError, match="missing-or-late-class-base"):
        WrapperGenerator().generate(plan)


def test_a_type_defined_in_two_namespaces_fails_before_emission():
    """Generated code reaches a type in the one namespace defining it."""
    plan = _plan(INHERITANCE)
    namespace = next(item for item in plan.namespaces if item.derived_types)
    namespace.derived_types = (*namespace.derived_types, namespace.derived_types[0])

    with pytest.raises(ValueError, match="duplicate-derived-type-identity"):
        WrapperGenerator().generate(plan)
