"""Cross-feature wrapper-plan projection and structural validation tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.models import PYTHON_EXPORTS_METADATA
from prik.semantics.ownership import CodegenAction, NativeBarrierAction, ObjectKind
from prik.semantics.policy_completion import complete_semantic_policies
from prik.codegen import (
    NamespacePlan,
    WrapperCodeGenerator,
    WrapperPlanner,
)


def _plan(source: str, *, module_name: str = "fmath"):
    module = parse_pyi_text(source, module_name=module_name)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _scalar_plan():
    return _plan(
        """
@nogil
@bind("SWAP_ARGS")
@standalone
@native_call([Addr(Arg(1)), Addr(Arg(0))])
def swap_args(x: Float64, y: Float64) -> Float64: ...
""",
        module_name="runtime_policy",
    )


def _hidden_result_plan():
    return _plan(
        """
@native_call([Int32(1), Arg(0), Bool(False), Return("result", 0)])
def scale(x: Float64) -> Float64: ...
""",
        module_name="hidden_values",
    )


def _edit_first_function(plan, edit):
    root = plan.namespaces[0]
    functions = (edit(root.functions[0]), *root.functions[1:])
    return replace(plan, namespaces=(replace(root, functions=functions), *plan.namespaces[1:]))


def test_generator_rejects_hidden_result_native_action_disagreement():
    plan = _hidden_result_plan()
    function = plan.namespaces[0].functions[0]
    result = function.results[0]
    replacement = (
        NativeBarrierAction.PASS_VALUE
        if result.bridge.native_action is not NativeBarrierAction.PASS_VALUE
        else NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    )
    invalid = _edit_first_function(
        plan,
        lambda item: replace(
            item,
            results=(replace(result, bridge=replace(result.bridge, native_action=replacement)),),
        ),
    )

    with pytest.raises(ValueError, match="inconsistent-result-native-action"):
        WrapperCodeGenerator().generate(invalid)


def test_generator_rejects_hidden_result_slot_codegen_action_disagreement():
    plan = _hidden_result_plan()
    function = plan.namespaces[0].functions[0]
    result = function.results[0]
    edited_slot = replace(result.native_call_slot, codegen_action=CodegenAction.COPY_OUT)
    invalid = _edit_first_function(
        plan,
        lambda item: replace(
            item,
            results=(replace(result, native_call_slot=edited_slot),),
            native_call_slots=tuple(
                edited_slot if slot.native_position == edited_slot.native_position else slot
                for slot in item.native_call_slots
            ),
        ),
    )

    with pytest.raises(ValueError, match="inconsistent-result-slot-codegen-action"):
        WrapperCodeGenerator().generate(invalid)


def test_generator_rejects_argument_native_slot_object_kind_disagreement():
    plan = _scalar_plan()
    argument = plan.namespaces[0].functions[0].arguments[0]
    argument.native_call_slot.object_kind = ObjectKind.STRING

    with pytest.raises(ValueError, match="inconsistent-argument-object-kind"):
        WrapperCodeGenerator().generate(plan)


def test_generator_rejects_result_native_slot_object_kind_disagreement():
    plan = _hidden_result_plan()
    result = plan.namespaces[0].functions[0].results[0]
    result.native_call_slot.object_kind = ObjectKind.STRING

    with pytest.raises(ValueError, match="inconsistent-result-object-kind"):
        WrapperCodeGenerator().generate(plan)


def test_generator_rejects_advertised_role_without_a_plan_producer():
    invalid = _edit_first_function(
        _scalar_plan(),
        lambda function: replace(function, available_roles=(*function.available_roles, "invented:role")),
    )

    with pytest.raises(ValueError, match="inconsistent-available-roles"):
        WrapperCodeGenerator().generate(invalid)


def test_planner_groups_completed_exports_into_explicit_namespace_nodes():
    module = parse_pyi_text(
        """
def left_value(x: Int32) -> Int32: ...
def right_value(x: Int32) -> Int32: ...
""",
        module_name="namespaced",
    )
    module.functions[0].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": ("left",), "name": "shared_value"}]
    module.functions[1].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": ("right",), "name": "shared_value"}]
    complete_semantic_policies(module)

    plan = WrapperPlanner().build(module)

    assert [namespace.python_path for namespace in plan.namespaces] == [(), ("left",), ("right",)]
    assert plan.namespaces[0].functions == ()
    assert [function.binding.python_name for function in plan.namespaces[1].functions] == ["shared_value"]
    assert [function.binding.python_name for function in plan.namespaces[2].functions] == ["shared_value"]
    assert plan.namespaces[1].functions[0].symbol_name == "left_shared_value"
    assert plan.namespaces[2].functions[0].symbol_name == "right_shared_value"


def test_binding_registers_child_namespaces_as_importable_submodules():
    module = parse_pyi_text(
        """
def left_value(x: Int32) -> Int32: ...
def right_value(x: Int32) -> Int32: ...
""",
        module_name="namespaced",
    )
    module.functions[0].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": ("left",), "name": "shared_value"}]
    module.functions[1].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": ("right",), "name": "shared_value"}]
    complete_semantic_policies(module)
    artifacts = WrapperCodeGenerator().generate(WrapperPlanner().build(module))
    c_source = next(source.text for source in artifacts.sources if source.path.name.endswith(".c"))

    assert "PyModule_Create(&namespaced_left_module)" in c_source
    assert "PyModule_Create(&namespaced_right_module)" in c_source
    left_registration = 'PyDict_SetItemString(PyImport_GetModuleDict(), "namespaced.left", namespace_left) < 0'
    assert left_registration in c_source
    assert 'PyDict_SetItemString(PyImport_GetModuleDict(), "namespaced.right", namespace_right) < 0' in c_source
    assert c_source.index(left_registration) > c_source.index("PyModule_Create(&namespaced_left_module)")


def test_post_ir_export_policy_fixes_names_within_each_namespace():
    module = parse_pyi_text(
        """
def first(x: Int32) -> Int32: ...
def second(x: Int32) -> Int32: ...
""",
        module_name="namespaced_fixes",
    )
    module.functions[0].name = "lambda"
    module.functions[0].native_name = "first"
    module.functions[0].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": ("child",), "name": None}]
    module.functions[1].name = "lambda_"
    module.functions[1].native_name = "second"
    module.functions[1].metadata[PYTHON_EXPORTS_METADATA] = [{"namespace": ("child",), "name": None}]

    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    child = next(namespace for namespace in plan.namespaces if namespace.python_path == ("child",))

    assert [function.binding.python_name for function in child.functions] == ["lambda_", "lambda__2"]


def test_planner_omits_private_functions_from_public_namespaces():
    module = parse_pyi_text(
        """
def visible(x: Int32) -> Int32: ...
def hidden(x: Int32) -> Int32: ...
""",
        module_name="visibility",
    )
    module.functions[1].visibility = "private"
    complete_semantic_policies(module)

    plan = WrapperPlanner().build(module)

    assert [function.binding.python_name for function in plan.namespaces[0].functions] == ["visible"]


def test_planner_projects_required_array_buffer_policy():
    module = parse_pyi_text(
        """
def sum_values(values: Float64[:]) -> Float64: ...
""",
        module_name="array_argument",
    )
    complete_semantic_policies(module)

    assert WrapperPlanner().build(module).namespaces[0].functions[0].arguments[0].array is not None


def test_planner_fails_when_post_ir_policy_has_not_completed():
    module = parse_pyi_text(
        """
def add(x: Float64, y: Float64) -> Float64: ...
""",
        module_name="missing_policy",
    )

    with pytest.raises(ValueError, match="missing completed wrapper policy"):
        WrapperPlanner().build(module)


def test_planner_rejects_a_module_without_public_wrapper_exports():
    module = parse_pyi_text("", module_name="empty_api")
    complete_semantic_policies(module)

    with pytest.raises(ValueError, match="Semantic module 'empty_api' has no public wrapper exports"):
        WrapperPlanner().build(module)


def test_completed_function_policy_rejects_unimplemented_runtime_constraints():
    module = parse_pyi_text(
        "def solve(value: Annotated[Int32, Bounded(1, 8), Finite]) -> Int32: ...\n",
        module_name="constrained",
    )
    complete_semantic_policies(module)

    with pytest.raises(ValueError, match="no runtime validators for semantic constraints"):
        WrapperPlanner().build(module)


def test_planner_reports_an_unsupported_completed_module_policy_at_its_owner_path():
    module = parse_pyi_text(
        """
label: String = "ready"
""",
        module_name="labels",
    )
    complete_semantic_policies(module)

    with pytest.raises(
        ValueError,
        match=r"Semantic variable 'labels\.label'.*module variable initializer requires a write-through native setter",
    ):
        WrapperPlanner().build(module)


def test_generator_rejects_duplicate_python_exports_before_lowering():
    plan = _scalar_plan()
    root = plan.namespaces[0]
    function = root.functions[0]
    duplicate = replace(function, symbol_name="other_symbol")
    invalid = replace(plan, namespaces=(replace(root, functions=(function, duplicate)),))

    with pytest.raises(ValueError, match="duplicate-python-export"):
        WrapperCodeGenerator().generate(invalid)


def test_generator_rejects_duplicate_generated_symbols_before_lowering():
    plan = _scalar_plan()
    root = plan.namespaces[0]
    function = root.functions[0]
    duplicate = replace(
        function,
        owner_path="runtime_policy.other",
        binding=replace(function.binding, python_name="other"),
    )
    invalid = replace(plan, namespaces=(replace(root, functions=(function, duplicate)),))

    with pytest.raises(ValueError, match="duplicate-generated-symbol"):
        WrapperCodeGenerator().generate(invalid)


def test_generator_rejects_colliding_generated_namespace_symbols():
    plan = _scalar_plan()
    invalid = replace(
        plan,
        namespaces=(
            *plan.namespaces,
            NamespacePlan(owner_path="runtime_policy.root", python_path=("root",)),
        ),
    )

    with pytest.raises(ValueError, match="duplicate-generated-namespace-symbol"):
        WrapperCodeGenerator().generate(invalid)


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (
            lambda plan: replace(
                plan,
                binding=replace(plan.binding, owner_path="other"),
            ),
            "binding-module-owner",
        ),
        (
            lambda plan: _edit_first_function(
                plan,
                lambda function: replace(
                    function,
                    arguments=(
                        replace(function.arguments[0], python_position=99),
                        function.arguments[1],
                    ),
                ),
            ),
            "out-of-range-python-position",
        ),
        (
            lambda plan: _edit_first_function(
                plan,
                lambda function: replace(
                    function,
                    arguments=(
                        replace(
                            function.arguments[0],
                            bridge=replace(
                                function.arguments[0].bridge,
                                handoff_role="other:role",
                            ),
                        ),
                        function.arguments[1],
                    ),
                ),
            ),
            "inconsistent-bridge-handoff",
        ),
    ],
)
def test_generator_revalidates_direct_plan_edits(mutate, expected_code):
    invalid = mutate(_scalar_plan())

    with pytest.raises(ValueError, match=expected_code):
        WrapperCodeGenerator().generate(invalid)
