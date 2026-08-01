"""Direct-plan required dense rank-one primitive-array input lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.ownership import (
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    ObjectKind,
    OwnershipOwner,
    PythonBarrierAction,
    StorageMode,
    TransferMode,
)
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import ArgumentHandoffMode, BridgeDataAction
from x2py.wrapper_codegen import ArrayHandoffPlan, WrapperCodeGenerator, WrapperPlanner
from x2py.wrapper_codegen.plan import DatatypeFamily


def _array_module():
    module = parse_pyi_text(
        "def sum_values(values: Float64[:]) -> Float64: ...\n",
        module_name="array_buffers",
    )
    complete_semantic_policies(module)
    return module


def _array_plan():
    return WrapperPlanner().build(_array_module())


def test_required_array_buffer_has_one_printable_editable_handoff_plan():
    function = _array_plan().namespaces[0].functions[0]
    argument = function.arguments[0]

    assert argument.object_kind is ObjectKind.NUMPY_ARRAY
    assert argument.ownership_owner is OwnershipOwner.CALLER
    assert argument.transfer_mode is TransferMode.IN_PLACE
    assert argument.destruction_policy is DestructionPolicy.CALLER
    assert argument.storage_mode is StorageMode.STACK
    assert argument.boundary_storage_mode is StorageMode.STACK
    assert argument.datatype_family is DatatypeFamily.REAL
    assert argument.binding.python_action is PythonBarrierAction.ARRAY_STORAGE
    assert argument.binding.codegen_action is CodegenAction.IN_PLACE_ARGUMENT
    assert argument.bridge.native_action is NativeBarrierAction.PASS_ARRAY_BUFFER
    assert argument.bridge.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER
    assert argument.bridge.data_action is BridgeDataAction.ASSOCIATE_VIEW

    assert isinstance(argument.array, ArrayHandoffPlan)
    assert argument.array is argument.native_call_slot.array
    assert argument.native_call_slot.object_kind is ObjectKind.NUMPY_ARRAY
    assert argument.array.rank == 1
    assert argument.array.shape == (":",)
    assert argument.array.axes == ("dense",)
    assert argument.array.contiguous is True
    assert argument.array.flatten_python_storage is False
    assert argument.array.flat_axis is None
    assert argument.array.data_role == argument.binding.handoff_role
    assert argument.array.extent_roles == (f"{argument.owner_path}:extent:0",)
    assert argument.array.upper_bound_roles == ()
    assert argument.array.stride_roles == ()
    assert argument.array.dense_actual_role is None


def test_required_array_buffer_dispatches_through_named_binding_and_bridge_methods():
    artifacts = WrapperCodeGenerator().generate(_array_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "double bind_c_sum_values(void * values, int64_t values_extent_0);" in c_source
    assert '"_native_array_actual_argument_for_binding_positional"' in c_source
    assert (
        'PyObject_CallFunction(bound_values_helper, "OsiOOiiiiiiiii", bound_values_obj, "float64", 1, '
        "bound_values_shape, bound_values_layout, 1, 1, 1, 0, 0, 0, 1, 0, -1)"
    ) in c_source
    assert "bound_values = PyLong_AsVoidPtr(PyTuple_GetItem(bound_values_packed, 0));" in c_source
    assert "bound_values_extent_0 = (int64_t)PyLong_AsLongLong(PyTuple_GetItem(bound_values_packed, 1));" in c_source
    assert "if (PyArray_Check(bound_values_obj)) {" in c_source
    assert "PyArray_TYPE((PyArrayObject *)bound_values_obj) != NPY_FLOAT64" in c_source
    assert "bound_values = PyArray_DATA((PyArrayObject *)bound_values_obj);" in c_source
    assert "result = bind_c_sum_values(bound_values, bound_values_extent_0);" in c_source

    assert "type(c_ptr), value :: bound_values" in bridge_source
    assert "integer(c_int64_t), value :: values_extent_0" in bridge_source
    assert "real(c_double), pointer, contiguous, dimension(:) :: values" in bridge_source
    assert "call c_f_pointer(bound_values, values, [values_extent_0])" in bridge_source
    assert "result = native_sum_values(values)" in bridge_source


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("rank", "inconsistent-array-rank"),
        ("axis", "invalid-array-axis-modes"),
        ("role", "inconsistent-array-data-role"),
        ("action", "invalid-array-data-action"),
    ],
)
def test_array_handoff_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _array_plan()
    argument = plan.namespaces[0].functions[0].arguments[0]
    if edit == "rank":
        argument.array.rank = 2
    elif edit == "axis":
        argument.array.axes = ("strided",)
    elif edit == "role":
        argument.array.data_role = "edited:data-role"
    else:
        argument.bridge.data_action = BridgeDataAction.DIRECT_TRANSFER

    with pytest.raises(ValueError, match=diagnostic):
        WrapperCodeGenerator().generate(plan)
