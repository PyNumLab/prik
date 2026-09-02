"""Projected ordinary outputs preserve their original Python array identity."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.ownership import CodegenAction, ObjectKind, OwnershipOwner, TransferMode
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import ArrayWritebackABI
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.planning.models import WritebackPhase


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
    artifacts = WrapperGenerator().generate(_output_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    assert "PyObject * result_obj = bound_values_obj;" in c_source
    assert "Py_INCREF(result_obj);" in c_source
    assert "PyObject * result_0_obj = bound_left_obj;" in c_source
    assert "PyObject * result_1_obj = bound_right_obj;" in c_source
    assert "PyTuple_New(2)" in c_source
    assert "PyTuple_SET_ITEM(result_obj, 0, result_0_obj)" in c_source
    assert "PyTuple_SET_ITEM(result_obj, 1, result_1_obj)" in c_source


def test_mutable_bool_array_writeback_needs_no_normalization():
    """A Boolean array is written back like any other element type.

    Its elements already hold the zero or one a C `_Bool` is defined to hold,
    because the compiler profiles request the option that guarantees it, so the
    callee leaves nothing behind that has to be reduced afterwards.
    """
    plan = _logical_output_plan()
    values, out = plan.namespaces[0].functions[0].arguments[1:]

    assert values.array_writeback_abi is ArrayWritebackABI.NATIVE_ARRAY
    assert out.array_writeback_abi is ArrayWritebackABI.NATIVE_ARRAY

    artifacts = WrapperGenerator().generate(plan)
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "call native_invert_flags(n, values, out)" in bridge_source
    assert "_logical_bytes" not in bridge_source
    assert "iand(" not in bridge_source


def test_high_rank_bool_array_bridge_stays_inside_the_fortran_line_limit():
    """Free-form Fortran caps a line at 132 columns, whatever the rank.

    A rank-15 array names one extent per axis, so its generated declarations and
    calls are the longest prik emits and are where continuation would first be
    missed.
    """
    artifacts = WrapperGenerator().generate(_high_rank_logical_output_plan())
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "values_extent_14" in bridge_source
    assert max(map(len, bridge_source.splitlines())) <= 132


def test_generator_rejects_a_normalized_mutable_bool_array_writeback_abi():
    """An edited plan cannot reintroduce a normalization pass that is not needed."""
    plan = _logical_output_plan()
    plan.namespaces[0].functions[0].arguments[-1].array_writeback_abi = ArrayWritebackABI.LOGICAL_LOW_BIT_INT8

    with pytest.raises(ValueError, match="invalid-array-writeback-abi"):
        WrapperGenerator().generate(plan)
