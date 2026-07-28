"""Phase 9 policy, plan, and pre-emission class validation."""

from pathlib import Path

import pytest

from x2py import pyi_text_to_semantic_module
from x2py.pipeline.pyi import pyi_file_to_semantic_module
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import ClassInvocationKind, OverloadMatchKind
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner

ROOT = Path(__file__).parents[1] / "wrapper" / "fortran"
INHERITANCE = ROOT / "derived_types" / "contracts" / "finheritance_f90" / "finheritance_f90.pyi"
OVERLOADS = ROOT / "naming" / "contracts" / "fconstructor_overloads_phase9" / "foverloads_f90.pyi"
BOUND_CONSTRUCTOR = ROOT / "derived_types" / "contracts" / "fbound_constructor_phase9" / "fclasses_f90.pyi"


def _plan(contract: Path):
    module = pyi_file_to_semantic_module(contract, module_name=contract.stem)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _plan_text(source: str):
    module = pyi_text_to_semantic_module(source, module_name="constructor_api")
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


def test_class_overloads_project_exact_typed_matches_and_bound_generic_calls():
    plan = _plan(OVERLOADS)
    surface = _surface(plan, "accumulator")
    method = next(overload for overload in surface.overloads if overload.python_name == "add")
    constructor = surface.constructor.overload

    assert constructor is not None
    for overload in (method, constructor):
        assert tuple(matches[0].kind for matches in overload.candidate_matches) == (
            OverloadMatchKind.NUMPY_SCALAR,
            OverloadMatchKind.NUMPY_SCALAR,
        )
        assert tuple(matches[0].semantic_type_name for matches in overload.candidate_matches) == (
            "Int32",
            "Float64",
        )
        assert all(
            candidate.class_call.invocation is ClassInvocationKind.TYPE_BOUND for candidate in overload.candidates
        )
        assert {candidate.class_call.type_bound_name for candidate in overload.candidates} == {"add"}
        assert {candidate.bridge.native_name for candidate in overload.candidates} == {"add"}


def test_same_named_module_procedure_and_method_are_both_public_without_bind():
    plan = _plan_text(
        """
from x2py.contracts import Addr, Arg, Float64, Pass, native_call

class point:
    @native_call([Pass(), Addr(Arg(0))])
    def move_point(self, dx: Float64) -> None: ...

@native_call([Arg(0), Addr(Arg(1))])
def move_point(item: point, dx: Float64) -> None: ...
"""
    )
    surface = _surface(plan, "point")
    method = next(item for item in surface.methods if item.python_name == "move_point")
    module_function = next(
        function for function in plan.namespaces[0].functions if function.binding.python_name == "move_point"
    )

    assert method.function.class_call is not None
    assert method.function.class_call.invocation is ClassInvocationKind.MODULE_PROCEDURE
    assert method.function.class_call.passed_object_position == 0
    assert method.function.bridge.native_name == "move_point"
    assert module_function.bridge.native_name == "move_point"
    assert module_function.binding.public is True
    assert ".__method__.move_point." in method.function.arguments[0].owner_path
    assert ".__method__." not in module_function.arguments[0].owner_path
    WrapperCodeGenerator().generate(plan)


def test_private_module_projection_hides_only_the_module_surface():
    plan = _plan_text(
        """
from x2py.contracts import Addr, Arg, Float64, Pass, native_call, private

class point:
    @native_call([Pass(), Addr(Arg(0))])
    def move_point(self, dx: Float64) -> None: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def move_point(item: point, dx: Float64) -> None: ...
"""
    )
    surface = _surface(plan, "point")
    method = next(item for item in surface.methods if item.python_name == "move_point")

    assert method.function.class_call is not None
    assert method.function.class_call.invocation is ClassInvocationKind.MODULE_PROCEDURE
    assert all(function.binding.python_name != "move_point" for function in plan.namespaces[0].functions)
    WrapperCodeGenerator().generate(plan)


def test_bound_constructor_uses_its_completed_direct_function_plan():
    plan = _plan(BOUND_CONSTRUCTOR)
    surface = _surface(plan, "vector")
    target = surface.constructor.target
    namespace = plan.namespaces[0]

    assert target is not None
    assert surface.methods == ()
    assert surface.constructor.target_owner_path == "fclasses_f90.vector.__init__"
    assert target.owner_path.endswith("._x2py_class_vector___init__")
    assert target.class_call is not None
    assert target.class_call.passed_object_position == 1
    assert target.class_call.invocation is ClassInvocationKind.MODULE_PROCEDURE
    assert [argument.binding.python_name for argument in target.arguments] == ["dx", "self", "dy"]
    assert target.binding.python_name.startswith("_x2py_class_")
    assert target.binding.public is False
    assert target in namespace.functions
    module_initializer = next(
        function for function in namespace.functions if function.binding.python_name == "shift_vector"
    )
    assert module_initializer.binding.public is True
    assert module_initializer is not target
    assert "_x2py_class_" not in namespace.docstring


def test_bound_constructor_pass_disambiguates_same_type_arguments_and_keeps_module_export():
    plan = _plan_text(
        """
from x2py.contracts import Arg, Pass, bind, native_call

class point:
    @bind("initialize_point")
    @native_call([Arg(0), Pass(), Arg(1)])
    def __init__(self, left: point, right: point) -> None: ...

def initialize_point(left: point, owner: point, right: point) -> None: ...
"""
    )
    surface = _surface(plan, "point")
    target = surface.constructor.target
    namespace = plan.namespaces[0]

    assert target is not None
    assert target.class_call is not None
    assert target.class_call.passed_object_position == 1
    assert [argument.binding.python_name for argument in target.arguments] == ["left", "self", "right"]
    module_initializer = next(
        function for function in namespace.functions if function.binding.python_name == "initialize_point"
    )
    assert module_initializer.binding.public is True
    assert module_initializer is not target
    WrapperCodeGenerator().generate(plan)


def test_class_docstrings_describe_only_the_public_surface():
    plan = _plan(BOUND_CONSTRUCTOR)
    surface = _surface(plan, "vector")

    assert "Constructor\n-----------\nvector(dx, dy) -> vector" in surface.docstring
    assert "Fields\n------\nx : float64\ny : float64" in surface.docstring
    assert "vector(dx, dy) -> vector" in surface.constructor.docstring
    assert "dx : float64" in surface.constructor.docstring
    assert "_x2py_class_" not in surface.docstring


def test_overload_docstrings_distinguish_candidates_by_public_types():
    plan = _plan(OVERLOADS)
    surface = _surface(plan, "accumulator")
    method = next(overload for overload in surface.overloads if overload.python_name == "add")

    assert "add(value: int32) -> None" in method.docstring
    assert "add(value: float64) -> None" in method.docstring
    assert "Dispatches to a native operation on the wrapped instance." in method.docstring
    assert "accumulator(value: int32) -> accumulator" in surface.constructor.docstring
    assert "accumulator(value: float64) -> accumulator" in surface.constructor.docstring
    assert "_x2py_class_" not in method.docstring
    assert "accumulator_add_" not in method.docstring


def test_invalid_class_graph_and_overload_edits_fail_before_emission():
    inheritance = _plan(INHERITANCE)
    _surface(inheritance, "circle").base_identities = (("missing", "base"),)
    with pytest.raises(ValueError, match="missing-or-late-class-base"):
        WrapperCodeGenerator().generate(inheritance)

    overloads = _plan(OVERLOADS)
    overload = next(item for item in _surface(overloads, "accumulator").overloads if item.python_name == "add")
    overload.candidate_matches = (overload.candidate_matches[0], overload.candidate_matches[0])
    with pytest.raises(ValueError, match="ambiguous-overload"):
        WrapperCodeGenerator().generate(overloads)
