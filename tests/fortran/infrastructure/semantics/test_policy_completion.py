"""Internal semantic-policy completion contracts."""

import pytest
from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_PROJECTION,
)
from prik.semantics.models import (
    RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA,
    RESOLVED_OWNERSHIP_POLICY_METADATA,
    RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA,
    RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA,
    SemanticArgument,
    SemanticClass,
    SemanticField,
    SemanticFunction,
    SemanticModule,
    SemanticType,
    SemanticVariable,
)
from prik.semantics.native_array_handles import native_array_descriptor_kind
from prik.policy.ownership import (
    AssignmentMode,
    CodegenAction,
    NativeBarrierAction,
    PythonBarrierAction,
    SetterAction,
    StorageMode,
    TransferMode,
)
from prik.policy.completion import complete_semantic_policies
from tests.fortran._support.ownership_policy import (
    _scalar_type,
    parse_pyi_text,
)

from prik.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
    SemanticCoercion,
)
from pathlib import Path
import subprocess
import sys

from prik.semantics.metadata import PROJECTED_OUTPUT_METADATA
from prik.semantics.models import (
    POLICY_COMPLETION_PREPARED_METADATA,
    ProjectionMapping,
)
from prik.policy.ownership import OwnershipOwner
from tests.fortran._support.ownership_policy import _array_type


def test_policy_completion_converts_native_addr_projection_after_python_boundary_parsing():
    module = parse_pyi_text(
        """
@native_call([Addr(Arg(0))])
def inspect(value: Int32) -> None: ...
""",
        module_name="native_projection_policy",
    )
    argument = module.functions[0].arguments[0]

    assert argument.semantic_type.storage is None

    complete_semantic_policies(module)

    assert argument.semantic_type.storage.kind == "address"
    assert argument.semantic_type.storage.metadata[ADDRESS_ROLE_METADATA] == ADDRESS_ROLE_PROJECTION
    decision = argument.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA]
    assert decision.python_barrier_action is PythonBarrierAction.SCALAR_VALUE
    assert decision.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS


@pytest.mark.parametrize(
    ("descriptor_kind", "annotation"),
    [
        ("allocatable", "Allocatable[Float64[:]]"),
        ("pointer", "Pointer[Float64[:]]"),
    ],
)
def test_policy_completion_rejects_addr_projection_for_array_descriptor_handles(
    descriptor_kind,
    annotation,
):
    module = parse_pyi_text(
        f"""
@native_call([Addr(Arg(0))])
def consume(values: {annotation}) -> None: ...
""",
        module_name=f"{descriptor_kind}_addr_projection",
    )
    argument = module.functions[0].arguments[0]

    assert native_array_descriptor_kind(argument.semantic_type) == descriptor_kind

    with pytest.raises(ValueError, match=r"Addr\(Arg\(i\)\) is only valid for primitive scalar values"):
        complete_semantic_policies(module)


def test_scalar_accessor_policies_are_complete_before_ir_lowering():
    module = SemanticModule(
        name="state",
        variables=[SemanticVariable("counter", _scalar_type())],
        classes=[SemanticClass("point", fields=[SemanticField("x", _scalar_type())])],
    )

    complete_semantic_policies(module)

    for variable in (module.variables[0], module.classes[0].fields[0]):
        getter = variable.metadata[RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA]
        setter = variable.metadata[RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA]
        assert getter.codegen_action is CodegenAction.DIRECT_VALUE
        assert getter.storage_mode is StorageMode.STACK
        assert setter.codegen_action is CodegenAction.CALL_LOCAL_INPUT
        assert setter.assignment_mode is AssignmentMode.VALUE_COPY
        assert setter.setter_action is SetterAction.WRITE_THROUGH


def test_scalar_descriptor_accessor_policies_are_nullable_snapshots():
    module = parse_pyi_text(
        """
alloc_value: Allocatable[Float64]
ptr_value: Pointer[Int32]

class point:
    alloc_field: Allocatable[Float64]
    ptr_field: Pointer[Int32]
""",
        module_name="descriptor_state",
    )

    complete_semantic_policies(module)

    variables = [
        module.variables[0],
        module.variables[1],
        module.classes[0].fields[0],
        module.classes[0].fields[1],
    ]
    for variable in variables:
        storage = variable.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA]
        getter = variable.metadata[RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA]
        setter = variable.metadata[RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA]
        assert storage.transfer is TransferMode.SNAPSHOT_COPY
        assert storage.nullable is True
        assert storage.codegen_action is CodegenAction.SNAPSHOT_COPY
        assert getter.transfer is TransferMode.SNAPSHOT_COPY
        assert getter.nullable is True
        assert getter.codegen_action is CodegenAction.SNAPSHOT_COPY
        assert setter.setter_action is SetterAction.REJECT_REPLACEMENT

    alloc_module, ptr_module, alloc_field, ptr_field = variables
    assert alloc_module.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA].storage_mode is StorageMode.HEAP
    assert alloc_field.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA].storage_mode is StorageMode.HEAP
    assert ptr_module.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA].storage_mode is StorageMode.ALIAS
    assert ptr_field.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA].storage_mode is StorageMode.ALIAS


def test_scalar_descriptor_function_boundaries_use_normal_scalar_values():
    module = parse_pyi_text(
        """
@native_call(
    [Allocatable(Arg(0)), Pointer(Arg(1))],
    result=Pointer(Return(0)),
)
def combine(
    scale: Float64 | None,
    current: Int32 | None,
) -> Float64 | None: ...
""",
        module_name="descriptor_call",
    )

    complete_semantic_policies(module)

    scale, current = module.functions[0].arguments
    result = module.functions[0].metadata[RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA]
    scale_policy = scale.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA]
    current_policy = current.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA]

    assert scale_policy.transfer is TransferMode.CALL_LOCAL
    assert scale_policy.storage_mode is StorageMode.STACK
    assert scale_policy.boundary_storage_mode is StorageMode.HEAP
    assert scale_policy.descriptor_boundary is True
    assert scale_policy.python_barrier_action is PythonBarrierAction.SCALAR_VALUE
    assert scale_policy.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert current_policy.transfer is TransferMode.CALL_LOCAL
    assert current_policy.storage_mode is StorageMode.STACK
    assert current_policy.boundary_storage_mode is StorageMode.ALIAS
    assert current_policy.descriptor_boundary is True
    assert current_policy.python_barrier_action is PythonBarrierAction.SCALAR_VALUE
    assert current_policy.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert result.transfer is TransferMode.SNAPSHOT_COPY
    assert result.storage_mode is StorageMode.ALIAS
    assert result.nullable is True
    assert result.codegen_action is CodegenAction.SNAPSHOT_COPY


def test_semantic_coercion_without_conversion_action_blocks_completed_function_policy():
    function = SemanticFunction(
        "consume",
        arguments=[
            SemanticArgument(
                "value",
                SemanticType("Int32", coercions=[SemanticCoercion("Float64")]),
            )
        ],
    )
    module = SemanticModule("coercions", functions=[function])

    complete_semantic_policies(module)

    policy = function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert policy.supported is False
    assert "argument 'value' has no wrapper conversion actions for semantic coercions ('Float64',)" in policy.blockers


def test_policy_completion_attaches_decisions_before_ir_lowering():
    module = SemanticModule(
        name="generated_policy",
        variables=[
            SemanticVariable(
                "module_values",
                _array_type(allocatable=True, metadata={"aliased": True}),
            )
        ],
        classes=[
            SemanticClass(
                "buffer",
                fields=[SemanticField("values", _array_type(allocatable=True))],
            )
        ],
        functions=[
            SemanticFunction(
                "replace",
                arguments=[
                    SemanticArgument(
                        "values",
                        _array_type(allocatable=True),
                        metadata={PROJECTED_OUTPUT_METADATA: True},
                    )
                ],
                return_type=None,
                projection=[
                    ProjectionMapping(
                        python_name="values",
                        native_name="values",
                        native_position=0,
                        python_position=0,
                        result_position=0,
                    )
                ],
            )
        ],
    )

    complete_semantic_policies(module)

    assert module.metadata[POLICY_COMPLETION_PREPARED_METADATA] is True
    assert module.variables[0].metadata[RESOLVED_OWNERSHIP_POLICY_METADATA].owner is OwnershipOwner.NATIVE
    module_setter = module.variables[0].metadata[RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA]
    assert module_setter.codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert module_setter.setter_action is SetterAction.REJECT_REPLACEMENT
    assert (
        module.variables[0].metadata[RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA].codegen_action
        is CodegenAction.BORROWED_VIEW
    )
    assert module.classes[0].fields[0].metadata[RESOLVED_OWNERSHIP_POLICY_METADATA].owner is OwnershipOwner.WRAPPER
    assert (
        module.classes[0].fields[0].metadata[RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA].codegen_action
        is CodegenAction.CALL_LOCAL_INPUT
    )
    assert (
        module.functions[0].arguments[0].metadata[RESOLVED_OWNERSHIP_POLICY_METADATA].transfer is TransferMode.IN_PLACE
    )
    assert RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA not in module.functions[0].metadata


def test_policy_completion_direct_example_is_runnable():
    repository_root = Path(__file__).resolve().parents[4]

    result = subprocess.run(
        [sys.executable, "prik/policy/completion.py"],
        cwd=repository_root,
        capture_output=True,
        check=True,
        text=True,
    )

    assert result.stdout == (
        "before: math.scale(value): Float64 semantic IR\nafter: math.scale(value): scalar_value -> pass_value\n"
    )
