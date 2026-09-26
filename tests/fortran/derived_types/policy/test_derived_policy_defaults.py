"""Tests split by stable ownership concept from `test_handle_policy_dispatch.py`."""

from prik.policy.ownership import (
    CodegenAction,
    DestructionPolicy,
    OwnershipOwner,
    TransferMode,
    default_ownership_policy,
)
from tests.fortran._support.ownership_policy import (
    _derived_type,
    _hidden_output_context,
    _writable_argument_context,
)


def test_immutable_derived_output_selects_wrapper_instance_and_replacement_blocks():
    semantic_type = _derived_type("point")
    semantic_type.metadata["python_value_mutability"] = "immutable"

    output = default_ownership_policy.decide_semantic_type(
        semantic_type,
        _hidden_output_context(projects_result=True, python_visible=True),
    )
    assert output.owner is OwnershipOwner.WRAPPER
    assert output.transfer is TransferMode.WRAPPER_INSTANCE
    assert output.destruction is DestructionPolicy.WRAPPER_DEALLOC
    assert output.codegen_action is CodegenAction.WRAPPER_INSTANCE

    replacement = default_ownership_policy.decide_semantic_type(
        semantic_type,
        _writable_argument_context(projects_result=True, python_visible=True),
    )
    assert replacement.is_blocked
    assert replacement.blocker == "immutable derived replacement is not implemented"
