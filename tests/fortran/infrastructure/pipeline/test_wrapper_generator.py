"""Internal ordered wrapper-generation contracts."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.ownership import CodegenAction, NativeBarrierAction, ObjectKind
from prik.policy.models import ArgumentHandoffMode, BridgeDataAction
from prik.stage_values import FrozenStageRecordError
from prik.codegen import (
    CBindingGenerator,
    FortranBridgeGenerator,
)
from prik.codegen.docstrings import WrapperDocstringBuilder
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import NamespacePlan, WrapperPlanner
from prik.printers import CSourcePrinter, FortranSourcePrinter


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
    assert generated_wrapper.extension_init_name == "PyInit_render_demo"
    assert "double bind_c_swap_args(double * y, double * x);" in c_source
    assert 'static char * kwlist[] = {"x", "y", NULL};' in c_source
    assert 'PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist, &bound_x_obj, &bound_y_obj)' in c_source
    assert "prik_float64_unpack_exact(bound_x_obj, &bound_x)" in c_source
    assert "result = bind_c_swap_args(&bound_y, &bound_x);" in c_source
    assert "PyObject * result_obj = prik_float64_to_python(&result);" in c_source
    assert "PyMODINIT_FUNC PyInit_render_demo(void)" in c_source
    assert "static PyObject * wrap_swap_args" in c_header
    assert "module bind_c_render_demo_wrapper" in fortran_source
    assert 'function bind_c_swap_args(y, x) result(result) bind(c, name="bind_c_swap_args")' in fortran_source
    assert "real(c_double), external :: SWAP_ARGS" in fortran_source
    assert "function SWAP_ARGS(" not in fortran_source
    assert "result = SWAP_ARGS(y, x)" in fortran_source


def test_public_generator_reports_each_rendering_operation_in_execution_order():
    plan = _plan("def value(x: Float64) -> Float64: ...", module_name="render_progress")
    progress = []

    WrapperGenerator().generate(plan, progress=lambda label, elapsed: progress.append((label, elapsed)))

    assert [label for label, _ in progress] == [
        "Generate binding source",
        "Generate binding source",
        "Generate bridge source",
        "Generate bridge source",
        "Generate binding header",
        "Generate binding header",
    ]
    assert [elapsed is None for _, elapsed in progress] == [True, False, True, False, True, False]
    assert all(elapsed >= 0.0 for _, elapsed in progress if elapsed is not None)


def test_large_procedure_only_binding_is_split_into_balanced_compile_units():
    declarations = "\n".join(f"def value_{index:03d}(x: Float64) -> Float64: ..." for index in range(128))
    generated_wrapper = WrapperGenerator().generate(_plan(declarations, module_name="large_binding"))
    binding_sources = [
        source for source in generated_wrapper.sources if source.path.name.startswith("large_binding_wrapper")
    ]
    main_source, *worker_sources, header_source = binding_sources

    assert generated_wrapper.binding_sources == (
        Path("large_binding_wrapper.c"),
        Path("large_binding_wrapper_001.c"),
        Path("large_binding_wrapper_002.c"),
        Path("large_binding_wrapper_003.c"),
        Path("large_binding_wrapper_004.c"),
    )
    assert "#define PRIK_BINDING_IMPORT_ARRAY 1" in main_source.text
    assert "PyMODINIT_FUNC PyInit_large_binding(void)" in main_source.text
    assert "PyObject * wrap_value_000(" not in main_source.text
    assert all("PRIK_BINDING_IMPORT_ARRAY" not in source.text for source in worker_sources)
    assert all("PyInit_large_binding" not in source.text for source in worker_sources)
    assert sum(source.text.count("PyObject * wrap_value_") for source in worker_sources) == 128
    assert "static PyObject * wrap_value_000" not in header_source.text
    assert "PyObject * wrap_value_000(PyObject * self, PyObject * args, PyObject * kwargs);" in header_source.text


def test_procedure_only_binding_below_sharding_threshold_keeps_one_compile_unit():
    declarations = "\n".join(f"def value_{index:03d}(x: Float64) -> Float64: ..." for index in range(127))

    generated_wrapper = WrapperGenerator().generate(_plan(declarations, module_name="unsharded_binding"))

    assert generated_wrapper.binding_sources == (Path("unsharded_binding_wrapper.c"),)


@pytest.mark.parametrize(
    ("source", "c_fragment", "fortran_fragment"),
    [
        (
            "def required_value(x: Float64) -> Float64: ...",
            "PyObject * bound_x_obj;",
            "result = native_required_value(x)",
        ),
        (
            "def optional_value(x: Int32 = ...) -> Int32: ...",
            "PyObject * bound_x_obj = Py_None;",
            "if (c_associated(bound_x)) then",
        ),
        (
            """
@native_call([Allocatable(Arg(0))])
def descriptor_value(value: Annotated[Float64, Immutable] | None = ...) -> Int32: ...
""",
            "PyObject * bound_value_obj = NULL;",
            "type(c_ptr), value :: bound_value_present",
        ),
        (
            """
@native_call([Addr(Arg(0)), Return("result", 0)])
def hidden_value(x: Float64) -> Float64: ...
""",
            "void bind_c_hidden_value(double * x, double * result);",
            "subroutine bind_c_hidden_value(x, result)",
        ),
    ],
)
def test_supported_function_actions_select_their_backend_behavior(source, c_fragment, fortran_fragment):
    generated_wrapper = WrapperGenerator().generate(_plan(source, module_name="action_dispatch"))

    assert c_fragment in _rendered_source(generated_wrapper, ".c")
    assert fortran_fragment in _rendered_source(generated_wrapper, ".f90")


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

    generated_wrapper = WrapperGenerator().generate(plan)

    assert '"subtract", (PyCFunction)wrap_calculate' in _rendered_source(generated_wrapper, ".c")
    assert "result = SUB_R8(x, y)" in _rendered_source(generated_wrapper, ".f90")
    with pytest.raises(FrozenStageRecordError):
        function.bridge.native_name = "ADD_R8"


def test_backend_visitors_return_complete_nodes_and_printers_freeze_them():
    plan = _plan(
        """
@bind("SCALE")
@native_call([Int32(1), Arg(0), Bool(False)])
def scale(x: Float64) -> Float64: ...
""",
        module_name="backend_nodes",
    )
    c_generator = CBindingGenerator()
    fortran_generator = FortranBridgeGenerator()
    WrapperDocstringBuilder().render(plan)
    c_generator.require_supported(plan)
    fortran_generator.require_supported(plan)

    c_module, c_header = c_generator.visit(plan)
    fortran_module = fortran_generator.visit(plan)

    assert [function.name for function in c_module.functions] == ["wrap_scale", "PyInit_backend_nodes"]
    assert [prototype.name for prototype in c_header.prototypes] == ["wrap_scale"]
    assert [procedure.name for procedure in fortran_module.procedures] == ["bind_c_scale"]
    assert "result = native_scale(1, x, .false.)" in FortranSourcePrinter().doprint(fortran_module)
    CSourcePrinter().doprint(c_module)
    with pytest.raises(FrozenStageRecordError):
        c_module.name = "later"
    with pytest.raises(FrozenStageRecordError):
        fortran_module.name = "later"


def test_generator_rejects_unregistered_typed_lowering_combination():
    plan = _plan(
        """
def scale(x: Float64) -> Float64: ...
""",
        module_name="unsupported_lowering",
    )
    function = plan.namespaces[0].functions[0]
    invalid_argument = replace(
        function.arguments[0],
        binding=replace(function.arguments[0].binding, optional_mode="x"),
        bridge=replace(function.arguments[0].bridge, optional_mode="x"),
    )
    root = plan.namespaces[0]
    invalid = replace(
        plan,
        namespaces=(replace(root, functions=(replace(function, arguments=(invalid_argument,)),)),),
    )

    with pytest.raises(ValueError, match="Unsupported C argument optional mode"):
        WrapperGenerator().generate(invalid)


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
        WrapperGenerator().generate(invalid)


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
        WrapperGenerator().generate(invalid)


def test_generator_rejects_argument_native_slot_object_kind_disagreement():
    plan = _scalar_plan()
    argument = plan.namespaces[0].functions[0].arguments[0]
    argument.native_call_slot.object_kind = ObjectKind.STRING

    with pytest.raises(ValueError, match="inconsistent-argument-object-kind"):
        WrapperGenerator().generate(plan)


def test_generator_rejects_result_native_slot_object_kind_disagreement():
    plan = _hidden_result_plan()
    result = plan.namespaces[0].functions[0].results[0]
    result.native_call_slot.object_kind = ObjectKind.STRING

    with pytest.raises(ValueError, match="inconsistent-result-object-kind"):
        WrapperGenerator().generate(plan)


def test_generator_rejects_advertised_role_without_a_plan_producer():
    invalid = _edit_first_function(
        _scalar_plan(),
        lambda function: replace(function, available_roles=(*function.available_roles, "invented:role")),
    )

    with pytest.raises(ValueError, match="inconsistent-available-roles"):
        WrapperGenerator().generate(invalid)


def test_generator_rejects_duplicate_python_exports_before_lowering():
    plan = _scalar_plan()
    root = plan.namespaces[0]
    function = root.functions[0]
    duplicate = replace(function, symbol_name="other_symbol")
    invalid = replace(plan, namespaces=(replace(root, functions=(function, duplicate)),))

    with pytest.raises(ValueError, match="duplicate-python-export"):
        WrapperGenerator().generate(invalid)


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
        WrapperGenerator().generate(invalid)


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
        WrapperGenerator().generate(invalid)


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
        WrapperGenerator().generate(invalid)


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
        storage.bridge.handoff_mode = ArgumentHandoffMode.VALUE
    elif edit == "data_action":
        storage.bridge.data_action = BridgeDataAction.COPY_REPRESENTATION
        storage.bridge.copy_reason = "edited scalar-storage copy"
        storage.native_call_slot.bridge_data_action = BridgeDataAction.COPY_REPRESENTATION
        storage.native_call_slot.bridge_copy_reason = "edited scalar-storage copy"
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
    storage.native_call_slot.bridge_data_action = action
    storage.native_call_slot.bridge_copy_reason = reason
    assert function.native_call_slots[storage.native_position] is storage.native_call_slot

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
    assert "prik_int32_unpack_exact(bound_value_obj, &bound_value)" in c_source
    assert "bind_c_bump(&bound_value);" in c_source
    assert "PyObject * result_obj = NULL;" in c_source
    assert "result_obj = prik_int32_to_python(&bound_value);" in c_source
    assert "integer(c_int32_t) :: value" in bridge_source
    assert "call native_bump(value)" in bridge_source
    assert "value =" not in bridge_source
    assert "value_input" not in bridge_source
