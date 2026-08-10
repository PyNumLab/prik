"""Completed policy for edited method, constructor, and overload surfaces."""

from pathlib import Path

import pytest

from prik import pyi_text_to_semantic_module
from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy import ClassInvocationKind, OverloadMatchKind
from prik.codegen import WrapperCodeGenerator, WrapperPlanner

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures" / "edited_contracts"
METHOD_AND_CONSTRUCTOR = FIXTURES / "method_and_constructor" / "fclasses_f90.pyi"
OVERLOADED_API = FIXTURES / "overloaded_api" / "foverloads_f90.pyi"


def _plan(contract: Path):
    module = pyi_file_to_semantic_module(contract, module_name=contract.stem)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _plan_text(source: str):
    module = pyi_text_to_semantic_module(source, module_name="edited")
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _surface(plan, name: str):
    return next(
        surface for namespace in plan.namespaces for surface in namespace.classes if name in surface.python_names
    )


def test_module_procedure_method_visibility_is_completed_independently():
    public_plan = _plan_text(
        """
from prik.contracts import Addr, Arg, Float64, Pass, native_call

class point:
    @native_call([Pass(), Addr(Arg(0))])
    def move(self, dx: Float64) -> None: ...

@native_call([Arg(0), Addr(Arg(1))])
def move(item: point, dx: Float64) -> None: ...
"""
    )
    public_method = _surface(public_plan, "point").methods[0].function
    public_function = public_plan.namespaces[0].functions[0]

    assert public_method.class_call is not None
    assert public_method.class_call.invocation is ClassInvocationKind.MODULE_PROCEDURE
    assert public_method.class_call.passed_object_position == 0
    assert public_method.bridge.native_name == public_function.bridge.native_name == "move"
    assert public_function.binding.public is True

    private_plan = _plan_text(
        """
from prik.contracts import Addr, Arg, Float64, Pass, native_call, private

class point:
    @native_call([Pass(), Addr(Arg(0))])
    def move(self, dx: Float64) -> None: ...

@private
@native_call([Arg(0), Addr(Arg(1))])
def move(item: point, dx: Float64) -> None: ...
"""
    )
    private_method = _surface(private_plan, "point").methods[0].function
    assert private_method.class_call is not None
    assert private_method.class_call.invocation is ClassInvocationKind.MODULE_PROCEDURE
    assert all(function.binding.python_name != "move" for function in private_plan.namespaces[0].functions)
    WrapperCodeGenerator().generate(public_plan)
    WrapperCodeGenerator().generate(private_plan)


def test_bound_constructor_and_method_reuse_completed_direct_function_plans():
    plan = _plan(METHOD_AND_CONSTRUCTOR)
    surface = _surface(plan, "vector")
    constructor = surface.constructor.target
    method = next(item.function for item in surface.methods if item.python_name == "shift")

    assert constructor is not None
    assert constructor.class_call is not None
    assert constructor.class_call.passed_object_position == 1
    assert constructor.class_call.invocation is ClassInvocationKind.MODULE_PROCEDURE
    assert [argument.binding.python_name for argument in constructor.arguments] == ["dx", "self", "dy"]
    assert constructor.binding.public is False

    assert method.class_call is not None
    assert method.class_call.passed_object_position == 1
    assert method.class_call.invocation is ClassInvocationKind.MODULE_PROCEDURE
    assert constructor.bridge.native_name == method.bridge.native_name == "shift_vector"
    assert "Constructor\n-----------\nvector(dx, dy) -> vector" in surface.docstring
    assert "shift(dx, dy) -> None" in surface.methods[0].docstring


def test_bound_constructor_pass_disambiguates_same_type_arguments_and_keeps_module_export():
    plan = _plan_text(
        """
from prik.contracts import Arg, Pass, bind, native_call

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


def test_edited_overloads_complete_exact_dispatch_and_reject_ambiguous_plan():
    plan = _plan(OVERLOADED_API)
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
        assert {candidate.bridge.native_name for candidate in overload.candidates} == {"add"}

    assert "add(value: int32) -> None" in method.docstring
    assert "add(value: float64) -> None" in method.docstring
    assert "accumulator(value: int32) -> accumulator" in surface.constructor.docstring
    assert "accumulator(value: float64) -> accumulator" in surface.constructor.docstring

    method.candidate_matches = (method.candidate_matches[0], method.candidate_matches[0])
    with pytest.raises(ValueError, match="ambiguous-overload"):
        WrapperCodeGenerator().generate(plan)
