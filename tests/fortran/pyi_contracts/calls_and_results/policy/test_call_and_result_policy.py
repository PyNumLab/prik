"""Completed call projection and immutable replacement policy."""

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.models import RESOLVED_OWNERSHIP_POLICY_METADATA
from prik.policy.ownership import CodegenAction, ObjectKind, StorageMode
from prik.policy.completion import complete_semantic_policies
from prik.policy.construction import completed_function_wrapper_policy


def _completed_policy(source: str):
    module = parse_pyi_text(source, module_name="edited_calls")
    complete_semantic_policies(module)
    return module, completed_function_wrapper_policy(module.functions[0])


def test_native_order_and_projected_result_positions_are_completed_before_planning():
    _, native_order = _completed_policy(
        """
def scalar_status(base: Int32[()], status: Int32[()]) -> None: ...
"""
    )
    assert [(argument.python_position, argument.native_position) for argument in native_order.arguments] == [
        (0, 0),
        (1, 1),
    ]
    assert native_order.results == ()
    assert [slot.source_kind for slot in native_order.native_call_slots] == ["implicit", "implicit"]

    _, projected = _completed_policy(
        """
@nogil
@native_call([Return("status", 0), Addr(Arg(0))])
def scalar_status(base: Int32) -> Returns["status", Int32]: ...
"""
    )
    assert projected.release_gil is True
    assert [(slot.source_kind, slot.native_position) for slot in projected.native_call_slots] == [
        ("result", 0),
        ("projection", 1),
    ]
    assert projected.arguments[0].native_position == 1
    assert projected.results[0].native_position == 0
    assert projected.results[0].result_position == 0


def test_immutable_replacement_policy_is_complete_before_ir_lowering():
    module, policy = _completed_policy(
        """
def normalize(
    values: Annotated[Float64[:], Immutable]
) -> Returns["values", Float64[:]]: ...
"""
    )

    decision = module.functions[0].arguments[0].metadata[RESOLVED_OWNERSHIP_POLICY_METADATA]
    assert decision.kind is ObjectKind.NUMPY_ARRAY
    assert decision.codegen_action is CodegenAction.COPY_IN_OUT
    assert decision.storage_mode is StorageMode.STACK
    assert decision.boundary_storage_mode is StorageMode.STACK
    assert decision.projects_result is True
    assert decision.python_visible is True
    assert policy.writeback_actions[0].codegen_action is CodegenAction.COPY_IN_OUT
