"""Projected ordinary outputs preserve their original Python array identity."""

from __future__ import annotations

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.ownership import CodegenAction, ObjectKind, OwnershipOwner, TransferMode
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner
from x2py.wrapper_codegen.plan import WritebackPhase


def _output_plan():
    module = parse_pyi_text(
        """
from x2py.contracts import Float64, Int32, Returns

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
