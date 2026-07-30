"""Lowering selected by completed call and result plans."""

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.ownership import CodegenAction, NativeBarrierAction, ObjectKind
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import WritebackPhase
from x2py.wrapper_codegen import DatatypeFamily, WrapperCodeGenerator, WrapperPlanner


def _plan(source: str, *, module_name: str):
    module = parse_pyi_text(source, module_name=module_name)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _rendered_c(plan) -> str:
    artifacts = WrapperCodeGenerator().generate(plan)
    return next(source.text for source in artifacts.sources if source.path.suffix == ".c")


def test_plan_records_reordered_arguments_gil_behavior_and_hidden_result_slots():
    reordered = (
        _plan(
            """
@hold_gil
@bind("SWAP_ARGS")
@external
@native_call([Addr(Arg(1)), Addr(Arg(0))])
def swap_args(x: Float64, y: Float64) -> Float64: ...
""",
            module_name="runtime_policy",
        )
        .namespaces[0]
        .functions[0]
    )

    assert reordered.binding.hold_gil is True
    assert reordered.bridge.native_name == "SWAP_ARGS"
    assert reordered.bridge.external is True
    assert [argument.native_position for argument in reordered.arguments] == [1, 0]
    assert [argument.datatype_family for argument in reordered.arguments] == [
        DatatypeFamily.REAL,
        DatatypeFamily.REAL,
    ]
    assert reordered.arguments[0].native_call_slot.codegen_action is CodegenAction.CALL_LOCAL_INPUT

    hidden = (
        _plan(
            """
@native_call([Int32(1), Arg(0), Bool(False), Return("result", 0)])
def scale(x: Float64) -> Float64: ...
""",
            module_name="hidden_values",
        )
        .namespaces[0]
        .functions[0]
    )
    assert [(slot.source_kind, slot.literal_type, slot.literal_value) for slot in hidden.native_call_slots] == [
        ("literal", "Int32", 1),
        ("projection", None, None),
        ("literal", "Bool", False),
        ("result", None, None),
    ]
    assert hidden.results[0].source_kind == "hidden_output"
    assert hidden.results[0].bridge.abi_position == 3
    assert hidden.results[0].bridge.native_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert hidden.results[0].native_call_slot.object_kind is ObjectKind.SCALAR


@pytest.mark.parametrize(
    "codegen_action",
    (CodegenAction.COPY_IN_OUT, CodegenAction.IN_PLACE_ARGUMENT),
)
def test_replacement_writeback_dispatches_selected_scalar_result_behavior(codegen_action):
    plan = _plan(
        'def bump(value: Annotated[Int32, Immutable]) -> Returns["value", Int32]: ...',
        module_name="writeback_dispatch",
    )
    function = plan.namespaces[0].functions[0]
    actions = tuple(
        replace(
            action,
            codegen_action=codegen_action,
            binding=replace(action.binding, codegen_action=codegen_action),
        )
        if action.phase is WritebackPhase.COPY_OUT
        else action
        for action in function.writeback_actions
    )
    root = plan.namespaces[0]
    edited = replace(
        plan,
        namespaces=(replace(root, functions=(replace(function, writeback_actions=actions),)),),
    )

    c_source = _rendered_c(edited)

    assert "bind_c_bump(&bound_value);" in c_source
    if codegen_action is CodegenAction.COPY_IN_OUT:
        assert "result_obj = x2py_scalar_to_python(NPY_INT32, &bound_value);" in c_source
    else:
        assert "PyObject * result_obj = bound_value_obj;" in c_source
        assert "Py_INCREF(result_obj);" in c_source
