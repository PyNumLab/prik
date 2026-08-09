"""Derived policy, typed-plan, validation, and artifact coverage."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.models import RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy import (
    BridgeDataAction,
    DerivedNativeHandoff,
    DerivedObjectOrigin,
    DerivedOwnerRetention,
    DerivedRelease,
    LifecycleOperation,
)
from prik.codegen import WrapperCodeGenerator, WrapperPlanner


def _value_module(*, attributes: tuple[str, ...] = ()):
    decorator = f"@native_type(attributes={attributes!r})" if attributes else ""
    module = parse_pyi_text(
        f"""
from prik.contracts import Arg, Float64, Value, native_call, native_type

{decorator}
class point:
    x: Float64

@native_call([Value(Arg(0))])
def score(value: point) -> Float64: ...
""",
        module_name="derived_value",
    )
    complete_semantic_policies(module)
    return module


def _value_plan():
    return WrapperPlanner().build(_value_module())


def _sources(plan):
    artifacts = WrapperCodeGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")
    return c_source, bridge_source


@pytest.mark.parametrize("attributes", [(), ("sequence",), ("bind(c)",)])
def test_exact_typed_value_policy_projects_shared_canonical_derived_handoff(attributes):
    module = _value_module(attributes=attributes)
    function_policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    policy = function_policy.arguments[0]
    plan = WrapperPlanner().build(module)
    argument = plan.namespaces[0].functions[0].arguments[0]

    assert policy.derived.type_identity == ("derived_value", "point")
    assert policy.derived.native_handoff is DerivedNativeHandoff.TYPED_VALUE
    assert policy.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert argument.derived is argument.native_call_slot.derived
    assert argument.derived.type_identity == ("derived_value", "point")
    assert argument.derived.native_handoff is DerivedNativeHandoff.TYPED_VALUE
    assert "type_identity=('derived_value', 'point')" in str(plan)


def test_exact_typed_value_lowering_uses_fortran_value_semantics_and_opaque_binding():
    c_source, bridge_source = _sources(_value_plan())

    assert "struct point" not in c_source
    assert "PyCapsule_GetPointer" in c_source
    assert "type(prik_type_point), pointer :: value" in bridge_source
    assert "native_score(value)" in bridge_source


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    (
        ("identity", "inconsistent-derived-type-identity"),
        ("mechanism", "invalid-derived-native-handoff"),
        ("retention", "invalid-derived-owner-retention"),
        ("release", "invalid-derived-release"),
        ("data_action", "invalid-bridge-data-action"),
    ),
)
def test_derived_plan_edits_fail_central_validation(edit: str, diagnostic: str):
    plan = _value_plan()
    argument = plan.namespaces[0].functions[0].arguments[0]
    if edit == "identity":
        argument.derived.type_identity = ("other", "point")
    elif edit == "mechanism":
        argument.derived.native_handoff = DerivedNativeHandoff.REFERENCE
    elif edit == "retention":
        argument.derived.owner_retention = DerivedOwnerRetention.NATIVE_MODULE
    elif edit == "release":
        argument.derived.release = DerivedRelease.NATIVE_OWNER
    else:
        argument.bridge = replace(argument.bridge, data_action=BridgeDataAction.ASSOCIATE_VIEW)

    with pytest.raises(ValueError, match=diagnostic):
        WrapperCodeGenerator().generate(plan)


def test_owned_derived_result_has_explicit_failure_and_release_lifecycle():
    module = parse_pyi_text(
        """
from prik.contracts import Float64

class point:
    x: Float64

def make_point() -> point: ...
""",
        module_name="owned_derived_result",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]

    assert [action.operation for action in function.cleanup_actions] == [LifecycleOperation.DESTROY_ON_FAILURE]
    assert [action.operation for action in function.release_actions] == [LifecycleOperation.TRANSFER_TO_WRAPPER]
    assert function.cleanup_actions[0].source_role == function.results[0].bridge.native_result_role
    assert function.release_actions[0].source_role == function.results[0].bridge.native_result_role

    function.release_actions = ()
    with pytest.raises(ValueError, match="derived-wrapper-release-count"):
        WrapperCodeGenerator().generate(plan)


def test_hidden_returns_derived_output_reuses_owned_result_storage_and_lifecycle():
    module = parse_pyi_text(
        """
from prik.contracts import Float64, Return, Returns, native_call

class point:
    x: Float64

@native_call([Return("value", 0)])
def make_point() -> Returns["value", point]: ...
""",
        module_name="hidden_derived_returns",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    result = function.results[0]

    assert result.source_kind == "hidden_output"
    assert result.derived is result.native_call_slot.derived
    assert result.derived.origin is DerivedObjectOrigin.WRAPPER_RESULT
    assert result.derived.release is DerivedRelease.WRAPPER_DESTROY
    assert function.cleanup_actions[0].source_role == result.bridge.native_result_role
    assert function.release_actions[0].source_role == result.bridge.native_result_role

    c_source, bridge_source = _sources(plan)
    assert "PyCapsule_New(value" in c_source
    assert "allocate(value_value, stat=prik_allocation_status)" in bridge_source


def test_projected_derived_argument_returns_the_exact_caller_wrapper_without_release():
    module = parse_pyi_text(
        """
from prik.contracts import Float64, Returns

class point:
    x: Float64

def update(value: point) -> Returns["value", point]: ...
""",
        module_name="derived_writeback",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    argument = function.arguments[0]

    assert argument.derived is argument.native_call_slot.derived
    assert argument.derived.origin is DerivedObjectOrigin.CALLER_WRAPPER
    assert argument.derived.owner_retention is DerivedOwnerRetention.CALLER_WRAPPER
    assert argument.derived.release is DerivedRelease.NONE
    assert function.writeback_actions[2].binding.python_result_role.endswith(":python-result")

    c_source, _ = _sources(plan)
    assert "PyObject * result_obj = bound_value_obj;" in c_source
    assert "Py_INCREF(result_obj);" in c_source
    assert "point_to_" not in c_source


def test_derived_module_handoff_edit_fails_central_validation():
    module = parse_pyi_text(
        """
from prik.contracts import Aliased, Annotated, Float64

class point:
    x: Float64

current: Annotated[point, Aliased]
""",
        module_name="derived_module_validation",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    variable = plan.namespaces[0].variables[0]

    assert variable.derived.handoff.origin is DerivedObjectOrigin.NATIVE_MODULE
    assert variable.derived.handoff.release is DerivedRelease.NATIVE_OWNER
    variable.derived.handoff.release = DerivedRelease.WRAPPER_DESTROY

    with pytest.raises(ValueError, match="invalid-derived-module-release"):
        WrapperCodeGenerator().generate(plan)


@pytest.mark.parametrize(
    ("contract", "diagnostic"),
    (
        (
            """
from prik.contracts import Float64, Pointer

class point:
    x: Float64

class holder:
    child: Pointer[point]
""",
            "unsupported descriptor-backed scalar derived value",
        ),
        (
            """
from prik.contracts import Float64

class point:
    x: Float64

def consume(value: point[:]) -> None: ...
""",
            "unsupported array of derived values",
        ),
        (
            """
from prik.contracts import Float64

class point:
    x: Float64

def make() -> point[:]: ...
""",
            "unsupported array of derived values",
        ),
        (
            """
from elsewhere import point

def consume(value: point) -> None: ...
""",
            "no completed wrapper type definition for ('elsewhere', 'point')",
        ),
        (
            """
class node:
    next: node
""",
            "forms a recursive value edge without descriptor policy",
        ),
    ),
)
def test_unsupported_derived_shapes_fail_on_exact_completed_policy_blockers(
    contract: str,
    diagnostic: str,
):
    module = parse_pyi_text(contract, module_name="blocked_derived")
    complete_semantic_policies(module)

    with pytest.raises(ValueError, match=diagnostic.replace("(", r"\(").replace(")", r"\)")):
        WrapperPlanner().build(module)


def test_native_result_and_derived_writeback_share_ordered_output_aggregation():
    module = parse_pyi_text(
        """
from prik.contracts import Float64, Returns

class point:
    x: Float64

def update(value: point) -> tuple[Float64, Returns["value", point]]: ...
""",
        module_name="mixed_derived_writeback",
    )
    complete_semantic_policies(module)

    plan = WrapperPlanner().build(module)
    function = plan.namespaces[0].functions[0]
    assert function.results[0].result_position == 0
    assert function.writeback_actions[2].result_position == 1

    c_source = next(
        source.text for source in WrapperCodeGenerator().generate(plan).sources if source.path.suffix == ".c"
    )
    assert "PyTuple_New(2)" in c_source
    assert "Py_DECREF(result_0_obj);" in c_source


def test_mixed_derived_results_check_allocation_and_own_every_failure_path_before_scalar_conversion():
    module = parse_pyi_text(
        """
from prik.contracts import Int32, Return, native_call

class point:
    x: Int32

@native_call([Return("status", 0), Return("left", 1), Return("right", 2)])
def make_pair() -> tuple[Int32, point, point]: ...
""",
        module_name="mixed_derived_results",
    )
    complete_semantic_policies(module)
    c_source, bridge_source = _sources(WrapperPlanner().build(module))

    assert "left = c_null_ptr" in bridge_source
    assert "right = c_null_ptr" in bridge_source
    assert "allocate(left_value, stat=prik_allocation_status)" in bridge_source
    assert "allocate(right_value, stat=prik_allocation_status)" in bridge_source
    assert "deallocate(left_value)" in bridge_source
    allocation_check = c_source.index("if (left == NULL || right == NULL)")
    first_wrapper = c_source.index("PyCapsule_New(left")
    scalar_conversion = c_source.index("prik_int32_to_python(&status)")
    assert allocation_check < first_wrapper < scalar_conversion
    assert "if (right != NULL) { bind_c_prik_destroy_point(right); right = NULL; }" in c_source
