"""Internal ownership defaults, dispatch, and validation contracts."""

from pathlib import Path
import subprocess
import sys

import pytest
from prik.semantics.metadata import ADDRESS_ROLE_PROJECTION
from prik.semantics.ownership import (
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    NativeBarrierDispatcher,
    ObjectKind,
    OwnershipContext,
    OwnershipDecision,
    OwnershipOwner,
    OwnershipPolicyResolver,
    PolicyActionDispatcher,
    PythonBarrierAction,
    PythonBarrierDispatcher,
    StorageMode,
    TransferMode,
    default_ownership_policy,
)
from tests.fortran._support.ownership_policy import (
    _address_type,
    _array_type,
    _derived_type,
    _hidden_output_context,
    _read_only_argument_context,
    _scalar_storage_type,
    _scalar_type,
    _string_storage_type,
    _string_type,
    _writable_argument_context,
)


def test_default_policy_decisions_cover_public_object_kinds():
    resolver = default_ownership_policy

    scalar = resolver.decide_semantic_type(_scalar_type(), OwnershipContext.result())
    assert scalar.owner is OwnershipOwner.PYTHON
    assert scalar.transfer is TransferMode.BY_VALUE
    assert scalar.codegen_action is CodegenAction.DIRECT_VALUE

    scalar_replacement = resolver.decide_semantic_type(
        _scalar_type(),
        _writable_argument_context(projects_result=True),
    )
    assert scalar_replacement.owner is OwnershipOwner.PYTHON
    assert scalar_replacement.transfer is TransferMode.COPY_RETURN
    assert scalar_replacement.codegen_action is CodegenAction.COPY_IN_OUT

    string = resolver.decide_semantic_type(_string_type(), OwnershipContext.result())
    assert string.owner is OwnershipOwner.PYTHON
    assert string.transfer is TransferMode.COPY_RETURN

    string_replacement = resolver.decide_semantic_type(
        _string_type(),
        _writable_argument_context(projects_result=True),
    )
    assert string_replacement.owner is OwnershipOwner.PYTHON
    assert string_replacement.transfer is TransferMode.COPY_RETURN
    assert "immutable Python strings" in string_replacement.reason

    caller_array = resolver.decide_semantic_type(_array_type(), _hidden_output_context())
    assert caller_array.owner is OwnershipOwner.CALLER
    assert caller_array.transfer is TransferMode.IN_PLACE
    assert caller_array.codegen_action is CodegenAction.IDENTITY_OUTPUT

    projected_caller_array = resolver.decide_semantic_type(
        _array_type(),
        _hidden_output_context(projects_result=True, python_visible=True),
    )
    assert projected_caller_array.transfer is TransferMode.IN_PLACE
    assert projected_caller_array.codegen_action is CodegenAction.IDENTITY_OUTPUT

    allocatable_output = resolver.decide_semantic_type(
        _array_type(allocatable=True),
        _hidden_output_context(projects_result=True, python_visible=False),
    )
    assert allocatable_output.owner is OwnershipOwner.WRAPPER
    assert allocatable_output.transfer is TransferMode.WRAPPER_INSTANCE
    assert allocatable_output.destruction is DestructionPolicy.WRAPPER_DEALLOC
    assert allocatable_output.storage_mode is StorageMode.HEAP
    assert allocatable_output.nullable is True

    module_allocatable = resolver.decide_semantic_type(
        _array_type(allocatable=True, metadata={"aliased": True}),
        OwnershipContext.module_variable(),
    )
    assert module_allocatable.owner is OwnershipOwner.NATIVE
    assert module_allocatable.transfer is TransferMode.BORROWED_VIEW
    assert module_allocatable.destruction is DestructionPolicy.NATIVE_OWNER

    plain_module_allocatable = resolver.decide_semantic_type(
        _array_type(allocatable=True),
        OwnershipContext.module_variable(),
    )
    assert plain_module_allocatable.owner is OwnershipOwner.NATIVE
    assert plain_module_allocatable.transfer is TransferMode.BORROWED_VIEW
    assert plain_module_allocatable.destruction is DestructionPolicy.NATIVE_OWNER

    derived_output = resolver.decide_semantic_type(_derived_type(), OwnershipContext.result())
    assert derived_output.owner is OwnershipOwner.WRAPPER
    assert derived_output.transfer is TransferMode.WRAPPER_INSTANCE

    aliased_module_object = resolver.decide_semantic_type(
        _derived_type(metadata={"aliased": True}),
        OwnershipContext.module_variable(),
    )
    assert aliased_module_object.owner is OwnershipOwner.NATIVE
    assert aliased_module_object.transfer is TransferMode.BORROWED_VIEW
    assert aliased_module_object.destruction is DestructionPolicy.NATIVE_OWNER
    assert aliased_module_object.boundary_storage_mode is StorageMode.ALIAS

    plain_module_object = resolver.decide_semantic_type(
        _derived_type(),
        OwnershipContext.module_variable(),
    )
    assert plain_module_object.owner is OwnershipOwner.NATIVE
    assert plain_module_object.transfer is TransferMode.BORROWED_VIEW
    assert plain_module_object.destruction is DestructionPolicy.NATIVE_OWNER
    assert plain_module_object.codegen_action is CodegenAction.BORROWED_VIEW

    projected_derived_output = resolver.decide_semantic_type(
        _derived_type(),
        _hidden_output_context(projects_result=True, python_visible=True),
    )
    assert projected_derived_output.transfer is TransferMode.IN_PLACE
    assert projected_derived_output.codegen_action is CodegenAction.IDENTITY_OUTPUT

    hidden_derived_output = resolver.decide_semantic_type(
        _derived_type(),
        _hidden_output_context(projects_result=True, python_visible=False),
    )
    assert hidden_derived_output.transfer is TransferMode.WRAPPER_INSTANCE
    assert hidden_derived_output.codegen_action is CodegenAction.WRAPPER_INSTANCE

    derived_field = resolver.decide_semantic_type(_derived_type(), OwnershipContext.field())
    assert derived_field.owner is OwnershipOwner.WRAPPER
    assert derived_field.transfer is TransferMode.BORROWED_VIEW
    assert derived_field.destruction is DestructionPolicy.WRAPPER_DEALLOC


def test_default_policy_completes_non_raw_python_and_native_barrier_actions():
    pointer_projection = _address_type(ADDRESS_ROLE_PROJECTION)
    pointer_projection.metadata["fortran_pointer"] = True
    cases = [
        (
            "scalar_value",
            _scalar_type(),
            _read_only_argument_context(),
            PythonBarrierAction.SCALAR_VALUE,
            NativeBarrierAction.PASS_VALUE,
        ),
        (
            "scalar_address_projection",
            _address_type(ADDRESS_ROLE_PROJECTION),
            _read_only_argument_context(),
            PythonBarrierAction.SCALAR_VALUE,
            NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
        ),
        (
            "scalar_storage",
            _scalar_storage_type(),
            _writable_argument_context(),
            PythonBarrierAction.SCALAR_STORAGE,
            NativeBarrierAction.PASS_STORAGE_ADDRESS,
        ),
        (
            "pointer_scalar_address_projection",
            pointer_projection,
            _read_only_argument_context(),
            PythonBarrierAction.SCALAR_VALUE,
            NativeBarrierAction.PASS_STORAGE_ADDRESS,
        ),
        (
            "array_storage",
            _array_type(),
            _read_only_argument_context(),
            PythonBarrierAction.ARRAY_STORAGE,
            NativeBarrierAction.PASS_ARRAY_BUFFER,
        ),
        (
            "string_value",
            _string_type(),
            _writable_argument_context(projects_result=True),
            PythonBarrierAction.STRING_VALUE,
            NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
        ),
        (
            "string_storage",
            _string_storage_type(),
            _writable_argument_context(),
            PythonBarrierAction.STRING_STORAGE,
            NativeBarrierAction.PASS_STORAGE_ADDRESS,
        ),
        (
            "wrapper_instance",
            _derived_type(),
            _read_only_argument_context(),
            PythonBarrierAction.WRAPPER_INSTANCE,
            NativeBarrierAction.PASS_WRAPPER_ADDRESS,
        ),
    ]

    for label, semantic_type, context, python_action, native_action in cases:
        decision = default_ownership_policy.decide_semantic_type(semantic_type, context)
        assert decision.python_barrier_action is python_action, label
        assert decision.native_barrier_action is native_action, label


def test_policy_handler_dictionary_changes_one_object_kind():
    def native_scalar_handler(_facts, _context):
        return OwnershipDecision(
            ObjectKind.SCALAR,
            OwnershipOwner.NATIVE,
            TransferMode.BORROWED_VIEW,
            DestructionPolicy.NATIVE_OWNER,
            borrowed=True,
        )

    resolver = OwnershipPolicyResolver({ObjectKind.SCALAR: native_scalar_handler})

    scalar = resolver.decide_semantic_type(_scalar_type(), OwnershipContext.result())
    array = resolver.decide_semantic_type(_array_type(allocatable=True), OwnershipContext.result())

    assert scalar.owner is OwnershipOwner.NATIVE
    assert scalar.transfer is TransferMode.BORROWED_VIEW
    assert array.owner is OwnershipOwner.WRAPPER
    assert array.transfer is TransferMode.WRAPPER_INSTANCE


def test_codegen_action_dispatcher_routes_policy_actions_to_named_methods():
    class FakeVar:
        rank = 1
        ownership_decision = OwnershipDecision(
            ObjectKind.NUMPY_ARRAY,
            OwnershipOwner.PYTHON,
            TransferMode.SNAPSHOT_COPY,
            DestructionPolicy.PYTHON_REFCOUNT,
            storage_mode=StorageMode.ALIAS,
            codegen_action=CodegenAction.SNAPSHOT_COPY,
        )

    class Target:
        def snapshot(self, var, decision, marker):
            return marker, var.rank, decision.codegen_action

    dispatcher = PolicyActionDispatcher(
        {(ObjectKind.NUMPY_ARRAY, CodegenAction.SNAPSHOT_COPY): "snapshot"},
    )

    assert dispatcher.dispatch(Target(), FakeVar(), "seen") == (
        "seen",
        1,
        CodegenAction.SNAPSHOT_COPY,
    )


def test_codegen_action_dispatcher_rejects_missing_policy_pairs():
    class FakeVar:
        ownership_decision = OwnershipDecision(
            ObjectKind.STRING,
            OwnershipOwner.TEMPORARY,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.CALL_LOCAL,
            codegen_action=CodegenAction.CALL_LOCAL_INPUT,
        )

    dispatcher = PolicyActionDispatcher({})

    with pytest.raises(ValueError, match="string/call_local_input"):
        dispatcher.handler_name(FakeVar())


def test_barrier_dispatchers_route_completed_actions_to_named_methods():
    class FakeVar:
        ownership_decision = OwnershipDecision(
            ObjectKind.SCALAR,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            codegen_action=CodegenAction.CALL_LOCAL_INPUT,
            python_barrier_action=PythonBarrierAction.SCALAR_VALUE,
            native_barrier_action=NativeBarrierAction.PASS_VALUE,
        )

    class Target:
        def python_scalar(self, var, decision, marker):
            return marker, var.ownership_decision.python_barrier_action, decision.python_barrier_action

        def native_value(self, var, decision, marker):
            return marker, var.ownership_decision.native_barrier_action, decision.native_barrier_action

    python_dispatcher = PythonBarrierDispatcher({PythonBarrierAction.SCALAR_VALUE: "python_scalar"})
    native_dispatcher = NativeBarrierDispatcher({NativeBarrierAction.PASS_VALUE: "native_value"})

    assert python_dispatcher.dispatch(Target(), FakeVar(), "py") == (
        "py",
        PythonBarrierAction.SCALAR_VALUE,
        PythonBarrierAction.SCALAR_VALUE,
    )
    assert native_dispatcher.dispatch(Target(), FakeVar(), "native") == (
        "native",
        NativeBarrierAction.PASS_VALUE,
        NativeBarrierAction.PASS_VALUE,
    )


def test_barrier_dispatchers_reject_missing_completed_actions():
    decision = OwnershipDecision(
        ObjectKind.SCALAR,
        OwnershipOwner.CALLER,
        TransferMode.CALL_LOCAL,
        DestructionPolicy.NONE,
        codegen_action=CodegenAction.CALL_LOCAL_INPUT,
        python_barrier_action=PythonBarrierAction.RAW_ADDRESS,
        native_barrier_action=NativeBarrierAction.PASS_RAW_ADDRESS,
    )

    with pytest.raises(ValueError, match="Python-barrier handler"):
        PythonBarrierDispatcher({}).handler_name_for_decision(decision, "x")
    with pytest.raises(ValueError, match="native-barrier handler"):
        NativeBarrierDispatcher({}).handler_name_for_decision(decision, "x")


def test_ownership_policy_direct_example_is_runnable():
    repository_root = Path(__file__).resolve().parents[4]

    result = subprocess.run(
        [sys.executable, "prik/semantics/ownership.py"],
        cwd=repository_root,
        capture_output=True,
        check=True,
        text=True,
    )

    assert result.stdout == (
        "before: math.scale(value): Float64 semantic IR\nafter: scalar/caller/call_local; scalar_value -> pass_value\n"
    )
