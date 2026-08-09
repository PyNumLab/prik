"""Projected ordinary outputs preserve their original Python array identity."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.ownership import CodegenAction, ObjectKind, OwnershipOwner, TransferMode
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy import ArrayWritebackABI
from prik.codegen import WrapperCodeGenerator, WrapperPlanner
from prik.codegen.plan import WritebackPhase


def _output_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Float64, Int32, Returns

def fill(n: Int32, values: Float64[n]) -> Returns["values", Float64[n]]: ...
def fill_two(
    n: Int32,
    left: Float64[n],
    right: Float64[n],
) -> tuple[Returns["left", Float64[n]], Returns["right", Float64[n]]]: ...
""",
        module_name="array_output_identity",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _logical_output_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Bool, Int32

def invert_flags(n: Int32, values: Bool[n], out: Bool[n]) -> None: ...
""",
        module_name="logical_arrays",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _high_rank_logical_output_plan():
    shape = ", ".join(":" for _ in range(15))
    module = parse_pyi_text(
        f"""
from prik.contracts import Bool

def normalize(values: Bool[{shape}]) -> None: ...
""",
        module_name="high_rank_logical_array",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_projected_array_identity_uses_one_completed_in_place_copy_out_action():
    function = _output_plan().namespaces[0].functions[0]
    argument = function.arguments[-1]
    action = function.writeback_actions[0]

    assert argument.object_kind is ObjectKind.NUMPY_ARRAY
    assert argument.ownership_owner is OwnershipOwner.CALLER
    assert argument.transfer_mode is TransferMode.IN_PLACE
    assert argument.binding.codegen_action is CodegenAction.IN_PLACE_ARGUMENT
    assert action.object_kind is ObjectKind.NUMPY_ARRAY
    assert action.phase is WritebackPhase.COPY_OUT
    assert action.binding is not None
    assert action.binding.codegen_action is CodegenAction.IN_PLACE_ARGUMENT


def test_projected_array_lowering_increfs_original_objects_and_reuses_tuple_aggregation():
    artifacts = WrapperCodeGenerator().generate(_output_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    assert "PyObject * result_obj = bound_values_obj;" in c_source
    assert "Py_INCREF(result_obj);" in c_source
    assert "PyObject * result_0_obj = bound_left_obj;" in c_source
    assert "PyObject * result_1_obj = bound_right_obj;" in c_source
    assert "PyTuple_New(2)" in c_source
    assert "PyTuple_SET_ITEM(result_obj, 0, result_0_obj)" in c_source
    assert "PyTuple_SET_ITEM(result_obj, 1, result_1_obj)" in c_source


def test_mutable_bool_array_writeback_normalizes_the_aliased_numpy_buffer_in_place():
    plan = _logical_output_plan()
    arguments = plan.namespaces[0].functions[0].arguments
    values, out = arguments[1:]

    assert values.array_writeback_abi is ArrayWritebackABI.LOGICAL_LOW_BIT_INT8
    assert out.array_writeback_abi is ArrayWritebackABI.LOGICAL_LOW_BIT_INT8

    artifacts = WrapperCodeGenerator().generate(plan)
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "integer(c_int8_t), pointer, dimension(:) :: out_logical_bytes" in bridge_source
    assert "call native_invert_flags(n, values, out)" in bridge_source
    assert "call c_f_pointer(bound_out, out_logical_bytes, [out_extent_0])" in bridge_source
    assert "out_logical_bytes = iand(out_logical_bytes, 1_c_int8_t)" in bridge_source


def test_high_rank_bool_array_writeback_wraps_the_flattened_shape_product():
    artifacts = WrapperCodeGenerator().generate(_high_rank_logical_output_plan())
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "values_extent_0 * &" in bridge_source
    assert "& values_extent_14])" in bridge_source
    assert max(map(len, bridge_source.splitlines())) <= 132


def test_generator_rejects_a_non_normalized_mutable_bool_array_writeback_abi():
    plan = _logical_output_plan()
    plan.namespaces[0].functions[0].arguments[-1].array_writeback_abi = ArrayWritebackABI.NATIVE_ARRAY

    with pytest.raises(ValueError, match="invalid-array-writeback-abi"):
        WrapperCodeGenerator().generate(plan)
