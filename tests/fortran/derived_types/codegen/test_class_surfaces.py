"""Completed inheritance and polymorphism class surfaces."""

from pathlib import Path

import pytest

from prik.parsers.fortran import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
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


def test_inheritance_and_polymorphism_are_completed_before_planning():
    plan = _plan(INHERITANCE)
    base = _surface(plan, "Base_Shape")
    circle = _surface(plan, "Circle")
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
    assert tuple(variant.type_identity for variant in describe.arguments[0].polymorphic.variants) == (
        _surface(plan, "Box").type_identity,
        circle.type_identity,
        base.type_identity,
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


EXTENDING_ANOTHER_MODULE = """\
module zeta_base
  implicit none
  type :: shape
    integer :: sides = 0
  end type shape
end module zeta_base

module alpha_child
  use zeta_base, only: shape
  implicit none
  type, extends(shape) :: square
    integer :: edge = 1
  end type square
end module alpha_child
"""


def test_a_namespace_is_planned_after_the_one_defining_its_base(tmp_path: Path):
    """A class extending another namespace's type is created once its base exists.

    Path order would put `alpha_child` first; inheritance overrides it only
    where it has to.
    """
    (tmp_path / "project.f90").write_text(EXTENDING_ANOTHER_MODULE, encoding="utf-8")
    modules = fortran_project_to_semantic_modules(parse_fortran_project(str(tmp_path)))
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="package")
    complete_semantic_policies(module)

    plan = WrapperPlanner().build(module)

    assert [namespace.python_path for namespace in plan.namespaces] == [(), ("zeta_base",), ("alpha_child",)]
