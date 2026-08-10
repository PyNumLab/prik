"""Tests split by stable ownership concept from `test_handle_policy_dispatch.py`."""

from prik.semantics.models import (
    SemanticArgument,
    SemanticClass,
    SemanticField,
    SemanticFunction,
    SemanticModule,
    SemanticVariable,
)
from prik.semantics.ownership import (
    CodegenAction,
    DestructionPolicy,
    OwnershipOwner,
    TransferMode,
    default_ownership_policy,
)
from tests.fortran._support.ownership_policy import (
    _array_type,
    _derived_type,
    _hidden_output_context,
    _scalar_type,
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


def test_recursive_module_policy_map_includes_nested_fields_and_functions():
    module = SemanticModule(
        name="geometry",
        variables=[
            SemanticVariable(
                "values",
                _array_type(allocatable=True, metadata={"aliased": True}),
            )
        ],
        classes=[
            SemanticClass(
                "particle",
                fields=[SemanticField("origin", _derived_type("point"))],
                classes=[
                    SemanticClass(
                        "buffer",
                        fields=[SemanticField("values", _array_type(allocatable=True))],
                    )
                ],
            )
        ],
        functions=[
            SemanticFunction(
                "build",
                arguments=[SemanticArgument("n", _scalar_type())],
                return_type=_array_type(allocatable=True),
            )
        ],
    )

    decisions = default_ownership_policy.decide_semantic_module(module)

    assert decisions["geometry.values"].owner is OwnershipOwner.NATIVE
    assert decisions["geometry.particle.origin"].owner is OwnershipOwner.WRAPPER
    assert decisions["geometry.particle.buffer.values"].transfer is TransferMode.BORROWED_VIEW
    assert decisions["geometry.build.n"].transfer is TransferMode.CALL_LOCAL
    assert decisions["geometry.build.return"].transfer is TransferMode.WRAPPER_INSTANCE
