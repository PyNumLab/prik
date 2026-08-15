"""Fixed-shape direct and hidden ordinary array result lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.ownership import CodegenAction, NativeBarrierAction, ObjectKind, OwnershipOwner, TransferMode
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import BridgeDataAction, ORDINARY_ARRAY_RESULT_COPY_REASON
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _result_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Float64, Int32, Return, native_call

def direct(n: Int32) -> Float64[n]: ...

@native_call([Return("out", 0)])
def hidden() -> Float64[3]: ...
""",
        module_name="ordinary_array_results",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _array_property_result_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Float64

def vector(values: Float64[:]) -> Float64[values.size]: ...
def flattened(values: Float64[:, :]) -> Float64[values.size]: ...
def columns(values: Float64[:, :]) -> Float64[values.shape[1]]: ...
""",
        module_name="size_intrinsic_results",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_array_results_record_producer_shape_copy_ownership_and_shared_hidden_slot():
    direct_function, hidden_function = _result_plan().namespaces[0].functions
    direct = direct_function.results[0]
    hidden = hidden_function.results[0]

    for result in (direct, hidden):
        assert result.object_kind is ObjectKind.NUMPY_ARRAY
        assert result.ownership_owner is OwnershipOwner.PYTHON
        assert result.transfer_mode is TransferMode.COPY_RETURN
        assert result.array is not None
        assert result.array.rank == 1
        assert result.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION
        assert result.bridge.copy_reason == ORDINARY_ARRAY_RESULT_COPY_REASON
    assert direct.source_kind == "direct_return"
    assert direct.binding.codegen_action is CodegenAction.COPY_OUT
    assert direct.bridge.native_action is NativeBarrierAction.NONE
    assert direct.projected_call_slot is None
    assert hidden.source_kind == "hidden_output"
    assert hidden.binding.codegen_action is CodegenAction.COPY_OUT
    assert hidden.bridge.native_action is NativeBarrierAction.PASS_ARRAY_BUFFER
    assert hidden.array is hidden.projected_call_slot.array
    assert hidden.projected_call_slot.object_kind is ObjectKind.NUMPY_ARRAY


def test_array_result_lowering_transfers_bridge_copy_to_capsule_owned_numpy_storage():
    artifacts = WrapperGenerator().generate(_result_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "void * bind_c_direct(int32_t n);" in c_source
    assert (
        "PyArray_New(&PyArray_Type, 1, result_obj_dims, NPY_FLOAT64, NULL, result, 0, "
        "NPY_ARRAY_C_CONTIGUOUS | NPY_ARRAY_WRITEABLE, NULL)" in c_source
    )
    assert "PyCapsule_New(result, NULL, prik_release_owned_memory)" in c_source
    assert "PyArray_SetBaseObject((PyArrayObject *)result_obj, result_obj_base)" in c_source
    assert "memcpy(PyArray_DATA((PyArrayObject *)result_obj), result" not in c_source
    base_failure = c_source.split(
        "if (PyArray_SetBaseObject((PyArrayObject *)result_obj, result_obj_base) < 0)",
        maxsplit=1,
    )[1].split("}", maxsplit=1)[0]
    assert "Py_DECREF(result_obj_base)" not in base_failure
    assert "free(result)" not in base_failure
    assert "void bind_c_hidden(void ** out);" in c_source
    assert "PyCapsule_New(out, NULL, prik_release_owned_memory)" in c_source
    assert "real(c_double), dimension(n) :: result_value" in bridge_source
    assert "result = c_malloc(" in bridge_source
    assert "size(result_value," in bridge_source
    assert "storage_size(result_value," in bridge_source
    assert "result_copy = reshape(result_value, [size(result_value)])" in bridge_source
    assert "real(c_double), dimension(3) :: out_value" in bridge_source
    assert "call native_hidden(out_value)" in bridge_source


def test_array_property_results_reuse_input_array_extent_roles_in_both_backends():
    plan = _array_property_result_plan()
    vector, flattened, columns = plan.namespaces[0].functions

    assert vector.results[0].array.shape == ("__prik_extent_values_0",)
    assert vector.results[0].array.extent_reference_tokens == (("__prik_extent_values_0",),)
    assert vector.results[0].array.extent_reference_roles == (("size_intrinsic_results.vector.values:extent:0",),)
    assert flattened.results[0].array.shape == ("__prik_extent_values_0 * __prik_extent_values_1",)
    assert columns.results[0].array.shape == ("__prik_extent_values_1",)

    artifacts = WrapperGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "npy_intp result_obj_dims[] = {bound_values_extent_0};" in c_source
    assert "npy_intp result_obj_dims[] = {bound_values_extent_0 * bound_values_extent_1};" in c_source
    assert "real(c_double), dimension(values_extent_0) :: result_value" in bridge_source
    assert "dimension(values_extent_0 * values_extent_1) :: result_value" in bridge_source
    assert "real(c_double), dimension(values_extent_1) :: result_value" in bridge_source


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("rank", "invalid-array-result-rank"),
        ("order", "invalid-array-result-order"),
        ("copy", "invalid-array-result-copy-reason"),
        ("slot", "inconsistent-result-array-handoff"),
    ],
)
def test_array_result_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _result_plan()
    direct = plan.namespaces[0].functions[0].results[0]
    hidden = plan.namespaces[0].functions[1].results[0]
    if edit == "rank":
        direct.array.rank = None
    elif edit == "order":
        direct.array.order = "ORDER_C"
        direct.array.rank = 2
        direct.array.shape = ("2", "2")
        direct.array.extent_roles = ("edited:extent:0", "edited:extent:1")
        direct.array.extent_reference_roles = ((), ())
    elif edit == "copy":
        direct.bridge.copy_reason = "edited"
    else:
        hidden.projected_call_slot.array = direct.array

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)
