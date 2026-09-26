"""Internal ordered wrapper-generation contracts."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.ownership import CodegenAction, NativeBarrierAction, ObjectKind
from prik.policy.models import ArgumentHandoffMode, BridgeDataAction
from prik.utilities.stage_values import FrozenStageRecordError
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import NamespacePlan, WrapperPlanner


def _rendered_source(generated_wrapper, suffix: str) -> str:
    return next(source.text for source in generated_wrapper.sources if source.path.name.endswith(suffix))


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


def _scalar_boundary_plan():
    module = parse_pyi_text(
        """
def storage(x: Float64[()]) -> None: ...
def raw(x: Addr(Float64)) -> None: ...
def direct_storage_result() -> Float64[()]: ...
@native_call([Return("out", 0)])
def hidden_storage_result() -> Float64[()]: ...
""",
        module_name="scalar_boundaries",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_public_generator_directly_returns_one_complete_generated_wrapper():
    plan = _plan(
        """
@nogil
@bind("SWAP_ARGS")
@standalone
@native_call([Addr(Arg(1)), Addr(Arg(0))])
def swap_args(x: Float64, y: Float64) -> Float64: ...
""",
        module_name="render_demo",
    )

    generated_wrapper = WrapperGenerator().generate(plan)
    c_source = _rendered_source(generated_wrapper, ".c")
    c_header = _rendered_source(generated_wrapper, ".h")
    fortran_source = _rendered_source(generated_wrapper, ".f90")

    assert generated_wrapper.module_name == "render_demo"
    assert generated_wrapper.source_paths == (
        Path("bind_c_render_demo_wrapper.f90"),
        Path("render_demo_wrapper.c"),
        Path("render_demo_wrapper.h"),
    )
    # The handoff names what the build compiles; headers are generated but never compiled.
    assert generated_wrapper.compile_sources == (Path("bind_c_render_demo_wrapper.f90"), Path("render_demo_wrapper.c"))
    assert generated_wrapper.generated_files == generated_wrapper.source_paths
    assert generated_wrapper.extension_init_name == "PyInit_render_demo"
    assert "double bind_c_swap_args(double * y, double * x);" in c_source
    assert 'static char * kwlist[] = {"x", "y", NULL};' in c_source
    assert 'PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist, &bound_x_obj, &bound_y_obj)' in c_source
    assert "prik_float64_or_storage(bound_x_obj, NPY_FLOAT64, " in c_source
    assert "result = bind_c_swap_args(bound_y_storage, bound_x_storage);" in c_source
    assert "PyObject * result_obj = prik_float64_to_numpy(&result);" in c_source
    assert "PyMODINIT_FUNC PyInit_render_demo(void)" in c_source
    assert "static PyObject * wrap_swap_args" in c_header
    assert "module bind_c_render_demo_wrapper" in fortran_source
    assert 'function bind_c_swap_args(y, x) result(result) bind(c, name="bind_c_swap_args")' in fortran_source
    assert "real(c_double), external :: SWAP_ARGS" in fortran_source
    assert "function SWAP_ARGS(" not in fortran_source
    assert "result = SWAP_ARGS(y, x)" in fortran_source


def test_procedure_only_binding_stays_one_compile_unit_at_any_size():
    declarations = "\n".join(f"def value_{index:03d}(x: Float64) -> Float64: ..." for index in range(128))

    generated_wrapper = WrapperGenerator().generate(_plan(declarations, module_name="large_binding"))
    binding_source = next(
        source for source in generated_wrapper.sources if source.path.name == "large_binding_wrapper.c"
    )
    header_source = next(
        source for source in generated_wrapper.sources if source.path.name == "large_binding_wrapper.h"
    )

    assert generated_wrapper.binding_sources == (Path("large_binding_wrapper.c"),)
    assert "#define PRIK_BINDING_IMPORT_ARRAY 1" in binding_source.text
    assert "PyMODINIT_FUNC PyInit_large_binding(void)" in binding_source.text
    assert binding_source.text.count("static PyObject * wrap_value_") == 128
    assert "static PyObject * wrap_value_000(PyObject * self, PyObject * args, PyObject * kwargs);" in (
        header_source.text
    )


def test_direct_plan_edits_change_binding_and_bridge_generation_then_freeze_plan():
    plan = _plan(
        """
@bind("ADD_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def calculate(x: Float64, y: Float64) -> Float64: ...
""",
        module_name="editable_plan",
    )
    function = plan.namespaces[0].functions[0]
    function.binding.python_name = "subtract"
    function.owner_path = "editable_plan.subtract"
    function.bridge.native_name = "SUB_R8"
    plan.native_generated_code_groups[0].member_keys = (function.owner_path,)

    generated_wrapper = WrapperGenerator().generate(plan)

    assert '"subtract", (PyCFunction)wrap_calculate' in _rendered_source(generated_wrapper, ".c")
    assert "result = SUB_R8(x, y)" in _rendered_source(generated_wrapper, ".f90")
    with pytest.raises(FrozenStageRecordError):
        function.bridge.native_name = "ADD_R8"


def test_bridge_only_native_target_edit_cannot_change_c_binding():
    source = """
@bind("ADD_R8")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def calculate(x: Float64, y: Float64) -> Float64: ...
"""
    original = _plan(source, module_name="bridge_only_edit")
    edited = _plan(source, module_name="bridge_only_edit")
    edited.namespaces[0].functions[0].bridge.native_name = "SUB_R8"

    original_wrapper = WrapperGenerator().generate(original)
    edited_wrapper = WrapperGenerator().generate(edited)

    assert _rendered_source(edited_wrapper, ".c") == _rendered_source(original_wrapper, ".c")
    assert "result = ADD_R8(x, y)" in _rendered_source(original_wrapper, ".f90")
    assert "result = SUB_R8(x, y)" in _rendered_source(edited_wrapper, ".f90")


def test_entrypoint_symbol_edit_changes_both_sides_of_shared_c_abi():
    plan = _plan("def scale(x: Float64) -> Float64: ...", module_name="entrypoint_edit")
    function = plan.namespaces[0].functions[0]
    function.entrypoint.symbol_name = "custom_scale_entrypoint"

    generated = WrapperGenerator().generate(plan)
    c_source = _rendered_source(generated, ".c")
    fortran_source = _rendered_source(generated, ".f90")

    assert "custom_scale_entrypoint(bound_x)" in c_source
    assert "bind_c_scale(bound_x)" not in c_source
    assert "function custom_scale_entrypoint(x) result(result)" in fortran_source
    assert 'bind(c, name="custom_scale_entrypoint")' in fortran_source


def _unregistered_optional_mode(plan):
    function = plan.namespaces[0].functions[0]
    argument = function.arguments[0]
    invalid_argument = replace(
        argument,
        binding=replace(argument.binding, optional_mode="x"),
        entrypoint=replace(argument.entrypoint, optional_mode="x"),
    )
    return _edit_first_function(plan, lambda item: replace(item, arguments=(invalid_argument, *item.arguments[1:])))


def _hidden_result_native_action(plan):
    result = plan.namespaces[0].functions[0].results[0]
    replacement = (
        NativeBarrierAction.PASS_VALUE
        if result.bridge.native_action is not NativeBarrierAction.PASS_VALUE
        else NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    )
    edited = replace(result, bridge=replace(result.bridge, native_action=replacement))
    return _edit_first_function(plan, lambda item: replace(item, results=(edited,)))


def _hidden_result_slot_codegen_action(plan):
    function = plan.namespaces[0].functions[0]
    result = function.results[0]
    original_slot = result.projected_call_slot
    edited_slot = replace(original_slot, adapter=replace(original_slot.adapter, codegen_action=CodegenAction.COPY_OUT))
    projected_slots = tuple(
        edited_slot if slot is original_slot else slot for slot in function.entrypoint.projected_slots
    )
    return _edit_first_function(
        plan,
        lambda item: replace(
            item,
            results=(replace(result, projected_call_slot=edited_slot),),
            entrypoint=replace(item.entrypoint, projected_slots=projected_slots),
        ),
    )


def _argument_object_kind(plan):
    plan.namespaces[0].functions[0].arguments[0].projected_call_slot.object_kind = ObjectKind.STRING
    return plan


def _result_object_kind(plan):
    plan.namespaces[0].functions[0].results[0].projected_call_slot.object_kind = ObjectKind.STRING
    return plan


def _invented_role(plan):
    return _edit_first_function(
        plan, lambda function: replace(function, available_roles=(*function.available_roles, "invented:role"))
    )


def _duplicate_python_export(plan):
    root = plan.namespaces[0]
    function = root.functions[0]
    duplicate = replace(function, symbol_name="other_symbol")
    return replace(plan, namespaces=(replace(root, functions=(function, duplicate)),))


def _duplicate_generated_symbol(plan):
    root = plan.namespaces[0]
    function = root.functions[0]
    duplicate = replace(
        function, owner_path="runtime_policy.other", binding=replace(function.binding, python_name="other")
    )
    return replace(plan, namespaces=(replace(root, functions=(function, duplicate)),))


def _colliding_namespace(plan):
    return replace(
        plan,
        namespaces=(*plan.namespaces, NamespacePlan(owner_path="runtime_policy.root", python_path=("root",))),
    )


def _foreign_binding_owner(plan):
    return replace(plan, binding=replace(plan.binding, owner_path="other"))


def _edit_first_argument(plan, edit):
    return _edit_first_function(
        plan, lambda function: replace(function, arguments=(edit(function.arguments[0]), *function.arguments[1:]))
    )


def _out_of_range_python_position(plan):
    return _edit_first_argument(plan, lambda argument: replace(argument, python_position=99))


def _inconsistent_native_handoff(plan):
    return _edit_first_argument(
        plan, lambda argument: replace(argument, entrypoint=replace(argument.entrypoint, handoff_role="other:role"))
    )


@pytest.mark.parametrize(
    ("plan_factory", "edit", "diagnostic"),
    [
        pytest.param(
            _scalar_plan, _unregistered_optional_mode, "Unsupported C argument optional mode", id="optional-mode"
        ),
        pytest.param(
            _hidden_result_plan,
            _hidden_result_native_action,
            "inconsistent-result-native-action",
            id="result-native-action",
        ),
        pytest.param(
            _hidden_result_plan,
            _hidden_result_slot_codegen_action,
            "inconsistent-result-slot-codegen-action",
            id="result-slot-codegen-action",
        ),
        pytest.param(
            _scalar_plan, _argument_object_kind, "inconsistent-argument-object-kind", id="argument-object-kind"
        ),
        pytest.param(
            _hidden_result_plan, _result_object_kind, "inconsistent-result-object-kind", id="result-object-kind"
        ),
        pytest.param(_scalar_plan, _invented_role, "inconsistent-available-roles", id="role-without-producer"),
        pytest.param(_scalar_plan, _duplicate_python_export, "duplicate-python-export", id="duplicate-python-export"),
        pytest.param(_scalar_plan, _duplicate_generated_symbol, "duplicate-generated-symbol", id="duplicate-symbol"),
        pytest.param(
            _scalar_plan, _colliding_namespace, "duplicate-generated-namespace-symbol", id="colliding-namespace-symbol"
        ),
        pytest.param(_scalar_plan, _foreign_binding_owner, "binding-module-owner", id="binding-module-owner"),
        pytest.param(_scalar_plan, _out_of_range_python_position, "out-of-range-python-position", id="python-position"),
        pytest.param(_scalar_plan, _inconsistent_native_handoff, "inconsistent-native-handoff", id="native-handoff"),
    ],
)
def test_generator_revalidates_edited_plans_before_lowering(plan_factory, edit, diagnostic):
    """A plan stays editable until generation, so every cross-stage agreement is checked again there."""
    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(edit(plan_factory()))


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("native_action", "invalid-scalar-storage-native-action"),
        ("handoff", "invalid-scalar-storage-handoff-mode"),
        ("data_action", "invalid-scalar-storage-data-action"),
        ("codegen", "invalid-scalar-storage-codegen-action"),
        ("array", "invalid-scalar-storage-array"),
    ],
)
def test_scalar_address_handoff_plan_edits_fail_before_lowering(edit, diagnostic):
    plan = _scalar_boundary_plan()
    storage = plan.namespaces[0].functions[0].arguments[0]
    if edit == "native_action":
        storage.bridge.native_action = NativeBarrierAction.PASS_VALUE
    elif edit == "handoff":
        storage.entrypoint.handoff_mode = ArgumentHandoffMode.VALUE
    elif edit == "data_action":
        storage.bridge.data_action = BridgeDataAction.COPY_REPRESENTATION
        storage.bridge.copy_reason = "edited scalar-storage copy"
        storage.projected_call_slot.adapter.bridge_data_action = BridgeDataAction.COPY_REPRESENTATION
        storage.projected_call_slot.adapter.bridge_copy_reason = "edited scalar-storage copy"
    elif edit == "codegen":
        storage.binding.codegen_action = CodegenAction.SNAPSHOT_COPY
    else:
        storage.array.rank = 1

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)


@pytest.mark.parametrize(
    ("action", "reason", "diagnostic"),
    [
        (BridgeDataAction.COPY_REPRESENTATION, None, "missing-bridge-copy-reason"),
        (BridgeDataAction.ASSOCIATE_VIEW, "unnecessary second copy", "unexpected-bridge-copy-reason"),
        (BridgeDataAction.BLOCKED, None, "blocked-bridge-data-action"),
    ],
)
def test_bridge_data_action_invariant_rejects_unjustified_or_blocked_plans(action, reason, diagnostic):
    plan = _scalar_boundary_plan()
    function = plan.namespaces[0].functions[0]
    storage = function.arguments[0]
    storage.bridge.data_action = action
    storage.bridge.copy_reason = reason
    storage.projected_call_slot.adapter.bridge_data_action = action
    storage.projected_call_slot.adapter.bridge_copy_reason = reason
    assert function.entrypoint.projected_slots[storage.native_position] is storage.projected_call_slot

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)


def test_scalar_copy_in_out_reuses_one_binding_local_without_bridge_copy():
    module = parse_pyi_text(
        'def bump(value: Annotated[Int32, Immutable]) -> Returns["value", Int32]: ...',
        module_name="one_copy",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    value = plan.namespaces[0].functions[0].arguments[0]
    assert value.bridge.data_action is BridgeDataAction.DIRECT_TRANSFER
    assert value.bridge.copy_reason is None

    generated_wrapper = WrapperGenerator().generate(plan)
    c_source = next(source.text for source in generated_wrapper.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in generated_wrapper.sources if source.path.suffix == ".f90")

    assert c_source.count("int32_t bound_value;") == 1
    assert "prik_int32_or_storage(bound_value_obj, NPY_INT32, " in c_source
    assert "integer(c_int32_t) :: value" in bridge_source
    assert "call native_bump(value)" in bridge_source
    assert "value =" not in bridge_source
    assert "value_input" not in bridge_source
