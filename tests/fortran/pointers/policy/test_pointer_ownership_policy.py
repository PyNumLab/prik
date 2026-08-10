"""Completed pointer ownership and native-array handle policy."""

import pytest
from prik.codegen.printers import PyiPrinter
from prik.semantics.models import (
    RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA,
    RESOLVED_OWNERSHIP_POLICY_METADATA,
)
from prik.semantics.native_array_handles import (
    NativeArrayBuildRequirement,
    NativeArrayHandlePolicyDispatcher,
    native_array_handle_build_requirements,
)
from prik.semantics.ownership import (
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    OwnershipContext,
    OwnershipOwner,
    TransferMode,
    default_ownership_policy,
    set_ownership_metadata,
)
from prik.semantics.policy_completion import complete_semantic_policies
from tests.fortran._support.ownership_policy import (
    _array_type,
    _derived_type,
    _hidden_output_context,
    _native_array_policy,
    _read_only_argument_context,
    _scalar_type,
    _string_type,
    _writable_argument_context,
    parse_pyi_text,
)


def test_native_array_handle_dispatcher_routes_completed_policy_to_named_method():
    class Subject:
        name = "values"

    class Target:
        def handle(self, subject, policy, marker):
            return marker, subject.name, policy.descriptor_kind, policy.handle_kind

    dispatcher = NativeArrayHandlePolicyDispatcher(
        {("allocatable", "borrowed_module_descriptor"): "handle"},
    )

    assert dispatcher.dispatch(Target(), Subject(), _native_array_policy(), "seen") == (
        "seen",
        "values",
        "allocatable",
        "borrowed_module_descriptor",
    )


def test_native_array_handle_dispatcher_rejects_missing_completed_policy_pair():
    dispatcher = NativeArrayHandlePolicyDispatcher({})

    with pytest.raises(ValueError, match="pointer/borrowed_module_descriptor"):
        dispatcher.handler_name_for_policy(
            _native_array_policy(descriptor_kind="pointer"),
            "target",
        )


def test_native_array_handle_build_requirements_include_default_pointer_descriptor_accessors():
    module = parse_pyi_text(
        """
target: Pointer[Float64[:]]

class box:
    target: Pointer[Float64[:]]
""",
        module_name="native_handle_no_interop",
    )

    complete_semantic_policies(module)

    requirements = native_array_handle_build_requirements(module)

    assert requirements.pointer_c_descriptor_interop is True
    assert requirements.requires_iso_fortran_binding is True
    assert requirements.headers == ("ISO_Fortran_binding.h",)
    assert requirements.items == (
        NativeArrayBuildRequirement(
            owner="native_handle_no_interop.target",
            item="target",
            descriptor_kind="pointer",
            handle_kind="borrowed_module_descriptor",
            descriptor_interop="pointer_c_descriptor",
            headers=("ISO_Fortran_binding.h",),
        ),
        NativeArrayBuildRequirement(
            owner="native_handle_no_interop.box.target",
            item="target",
            descriptor_kind="pointer",
            handle_kind="borrowed_field_descriptor",
            descriptor_interop="pointer_c_descriptor",
            headers=("ISO_Fortran_binding.h",),
        ),
    )


def test_hidden_pointer_handle_output_owns_descriptor_but_not_target_policy():
    module = parse_pyi_text(
        """
@native_call([Return("values", 0)])
def select_values() -> Pointer[Float64[:]]: ...
""",
        module_name="hidden_pointer_handle_result",
    )
    complete_semantic_policies(module)

    argument = module.functions[0].arguments[0]
    decision = argument.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA]
    policy = argument.metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]

    assert decision.owner is OwnershipOwner.WRAPPER
    assert decision.transfer is TransferMode.WRAPPER_INSTANCE
    assert decision.destruction is DestructionPolicy.WRAPPER_DEALLOC
    assert decision.codegen_action is CodegenAction.WRAPPER_INSTANCE
    assert decision.native_barrier_action is NativeBarrierAction.PASS_NATIVE_DESCRIPTOR
    assert policy.descriptor_kind == "pointer"
    assert policy.handle_kind == "owned_result_descriptor"
    assert policy.origin == "projected_result"
    assert policy.owner_retention == "wrapper_owner_storage"
    assert policy.descriptor_ownership == "owned"
    assert policy.output_projection == "projected_handle"
    assert policy.target_lifetime == "unknown"
    assert policy.destroy_behavior == "handle_finalizer"
    assert policy.to_numpy == "unsupported"
    assert set(policy.operations) == {"associate", "associated", "nullify", "to_numpy"}


@pytest.mark.parametrize(
    ("owner", "transfer", "destruction", "context"),
    [
        ("python", "copy_return", "python_refcount", OwnershipContext.result()),
        ("python", "snapshot_copy", "python_refcount", OwnershipContext.result()),
        ("caller", "call_local", "none", _read_only_argument_context()),
        ("caller", "in_place", "caller", _writable_argument_context()),
        ("native", "borrowed_view", "native_owner", OwnershipContext.module_variable()),
        ("wrapper", "borrowed_view", "wrapper_dealloc", OwnershipContext.field()),
        ("temporary", "call_local", "call_local", _read_only_argument_context()),
    ],
)
def test_explicit_supported_ownership_triples_remain_codegen_ready(
    owner: str,
    transfer: str,
    destruction: str,
    context: OwnershipContext,
):
    metadata: dict[str, object] = {}
    set_ownership_metadata(
        metadata,
        owner=owner,
        transfer=transfer,
        destruction=destruction,
    )

    decision = default_ownership_policy.decide_semantic_type(
        _array_type(metadata=metadata),
        context,
    )

    assert decision.owner.value == owner
    assert decision.transfer.value == transfer
    assert decision.destruction.value == destruction
    assert not decision.is_blocked


@pytest.mark.parametrize(
    ("owner", "transfer", "destruction"),
    [
        ("native", "copy_return", "native_owner"),
        ("native", "borrowed_view", "python_refcount"),
        ("python", "copy_return", "native_owner"),
        ("python", "borrowed_view", "python_refcount"),
        ("wrapper", "wrapper_instance", "python_refcount"),
    ],
)
def test_contradictory_ownership_triples_fail_closed(
    owner: str,
    transfer: str,
    destruction: str,
):
    metadata: dict[str, object] = {}
    set_ownership_metadata(
        metadata,
        owner=owner,
        transfer=transfer,
        destruction=destruction,
    )

    decision = default_ownership_policy.decide_semantic_type(
        _array_type(metadata=metadata),
        OwnershipContext.result(),
    )

    assert decision.is_blocked
    assert decision.owner is OwnershipOwner.UNKNOWN
    assert decision.transfer is TransferMode.BLOCKED
    assert decision.destruction is DestructionPolicy.BLOCKED
    assert f"{owner}/{transfer}/{destruction}" in decision.blocker


def test_explicit_blocked_policy_normalizes_all_lifetime_axes():
    metadata: dict[str, object] = {}
    set_ownership_metadata(
        metadata,
        owner="native",
        transfer="blocked",
        destruction="native_owner",
    )

    decision = default_ownership_policy.decide_semantic_type(
        _array_type(metadata=metadata),
        OwnershipContext.result(),
    )

    assert decision.owner is OwnershipOwner.UNKNOWN
    assert decision.transfer is TransferMode.BLOCKED
    assert decision.destruction is DestructionPolicy.BLOCKED
    assert decision.codegen_action is CodegenAction.BLOCKED


def test_documented_transfer_and_destruction_modes_resolve_or_fail_closed():
    snapshot_metadata: dict[str, object] = {}
    set_ownership_metadata(
        snapshot_metadata,
        owner="python",
        transfer="snapshot_copy",
        destruction="python_refcount",
    )
    cases = [
        ("by_value", _scalar_type(), OwnershipContext.result()),
        ("call_local_none", _scalar_type(), _read_only_argument_context()),
        ("call_local_cleanup", _string_type(), _hidden_output_context()),
        ("caller_in_place", _array_type(), _writable_argument_context()),
        ("copy_return", _array_type(), OwnershipContext.result()),
        ("snapshot_copy", _array_type(metadata=snapshot_metadata), OwnershipContext.result()),
        (
            "native_borrowed_view",
            _array_type(allocatable=True, metadata={"aliased": True}),
            OwnershipContext.module_variable(),
        ),
        ("wrapper_borrowed_view", _array_type(allocatable=True), OwnershipContext.field()),
        ("wrapper_instance", _derived_type(), OwnershipContext.result()),
        ("wrapper_in_place", _derived_type(), _writable_argument_context()),
        (
            "blocked",
            _array_type(pointer=True),
            _writable_argument_context(),
        ),
    ]

    decisions = [
        default_ownership_policy.decide_semantic_type(semantic_type, context)
        for _label, semantic_type, context in cases
    ]
    transfer_modes = {decision.transfer for decision in decisions}
    destruction_modes = {decision.destruction for decision in decisions}

    assert transfer_modes == set(TransferMode)
    assert destruction_modes == set(DestructionPolicy)

    for label, decision in zip((case[0] for case in cases), decisions, strict=True):
        if decision.transfer is TransferMode.BLOCKED:
            assert decision.is_blocked, label
            assert decision.codegen_action is CodegenAction.BLOCKED, label
            assert decision.blocker, label
        else:
            assert not decision.is_blocked, label
            assert decision.codegen_action is not CodegenAction.BLOCKED, label


def test_pyi_policy_metadata_round_trips_pointer_array_handle_policy():
    default_type = _array_type(pointer=True)
    default_field = default_ownership_policy.decide_semantic_type(default_type, OwnershipContext.field())
    assert not default_field.is_blocked
    assert default_field.owner is OwnershipOwner.WRAPPER
    assert default_field.transfer is TransferMode.BORROWED_VIEW
    assert default_field.destruction is DestructionPolicy.WRAPPER_DEALLOC
    assert default_field.borrowed is True

    default_module = default_ownership_policy.decide_semantic_type(default_type, OwnershipContext.module_variable())
    assert not default_module.is_blocked
    assert default_module.owner is OwnershipOwner.NATIVE
    assert default_module.transfer is TransferMode.BORROWED_VIEW
    assert default_module.destruction is DestructionPolicy.NATIVE_OWNER

    metadata: dict[str, object] = {}
    set_ownership_metadata(
        metadata,
        owner="python",
        transfer="snapshot_copy",
        destruction="python_refcount",
    )
    overridden = default_ownership_policy.decide_semantic_type(
        _array_type(pointer=True, metadata=metadata),
        OwnershipContext.field(),
    )
    assert overridden.is_blocked
    assert overridden.blocker == (
        "pointer array container descriptor ownership is fixed by its native parent; "
        "use PointerPolicy for extraction and descriptor operations"
    )
    module_overridden = default_ownership_policy.decide_semantic_type(
        _array_type(pointer=True, metadata=metadata),
        OwnershipContext.module_variable(),
    )
    assert module_overridden.is_blocked
    assert module_overridden.blocker == (
        "pointer array container descriptor ownership is fixed by its native parent; "
        "use PointerPolicy for extraction and descriptor operations"
    )

    module = parse_pyi_text(
        """
class box:
    values: Annotated[
        Pointer[Float64[:]],
        Ownership("python"),
        Transfer("snapshot_copy"),
        Destruction("python_refcount"),
    ]
""",
        module_name="policy_box",
    )
    field_type = module.classes[0].fields[0].semantic_type
    parsed = default_ownership_policy.decide_semantic_type(field_type, OwnershipContext.field())
    assert parsed.is_blocked
    assert "detached-copy accessors" not in parsed.blocker
    assert "use PointerPolicy for extraction and descriptor operations" in parsed.blocker

    result = default_ownership_policy.decide_semantic_type(field_type, OwnershipContext.result())
    assert result.owner is OwnershipOwner.PYTHON
    assert result.transfer is TransferMode.SNAPSHOT_COPY
    assert result.destruction is DestructionPolicy.PYTHON_REFCOUNT
    assert result.codegen_action is CodegenAction.SNAPSHOT_COPY

    emitted = PyiPrinter().emit(field_type)
    assert 'Ownership("python")' in emitted
    assert 'Transfer("snapshot_copy")' in emitted
    assert 'Destruction("python_refcount")' in emitted


def test_plain_pointer_array_container_policy_completes_default_handle_profile():
    module = parse_pyi_text(
        """
value: Pointer[Float64[:]]

class box:
    target: Pointer[Float64[:]]
""",
        module_name="pointer_default_profile",
    )

    complete_semantic_policies(module)

    module_policy = module.variables[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    field_policy = module.classes[0].fields[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]

    assert not module_policy.is_blocked
    assert module_policy.handle_kind == "borrowed_module_descriptor"
    assert module_policy.getter_behavior == "handle"
    assert module_policy.to_numpy == "unsupported"
    assert module_policy.descriptor_interop == "pointer_c_descriptor"
    assert module_policy.requires_pointer_c_descriptor_interop is True
    assert module_policy.target_lifetime == "module"
    assert module_policy.destroy_behavior == "none"
    assert set(module_policy.operations) == {"associate", "associated", "nullify", "to_numpy"}
    assert "allocate" not in module_policy.operations
    assert "deallocate" not in module_policy.operations
    assert "resize" not in module_policy.operations

    assert not field_policy.is_blocked
    assert field_policy.handle_kind == "borrowed_field_descriptor"
    assert field_policy.getter_behavior == "handle"
    assert field_policy.to_numpy == "unsupported"
    assert field_policy.descriptor_interop == "pointer_c_descriptor"
    assert field_policy.requires_pointer_c_descriptor_interop is True
    assert field_policy.target_lifetime == "parent_wrapper"
    assert field_policy.destroy_behavior == "parent_wrapper_finalizer"
    assert set(field_policy.operations) == {"associate", "associated", "nullify", "to_numpy"}


def test_complete_pointer_policy_metadata_round_trips_without_overriding_container_ownership():
    module = parse_pyi_text(
        """
value: Annotated[
    Pointer[Float64[:]],
    PointerAssociation("runtime"),
    PointerPolicy(
        nullable=True,
        transfer="snapshot_copy",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="contiguous",
        reassociation="snapshot_final",
        aliasing="independent_copy",
        mutability="copy",
    ),
]
""",
        module_name="pointer_policy",
    )
    semantic_type = module.variables[0].semantic_type
    policy = semantic_type.metadata["pointer_policy"]
    assert policy == {
        "nullable": True,
        "transfer": "snapshot_copy",
        "target_owner": "module",
        "lifetime": "module",
        "deallocation": "never",
        "shape_source": "pointer_bounds",
        "contiguity": "contiguous",
        "reassociation": "snapshot_final",
        "aliasing": "independent_copy",
        "mutability": "copy",
    }
    assert semantic_type.metadata["fortran_pointer_association"] == "runtime"
    emitted = PyiPrinter().emit(semantic_type)
    assert 'PointerAssociation("runtime")' in emitted
    assert "PointerPolicy(nullable=True" in emitted
    assert 'mutability="copy")' in emitted

    policy["transfer"] = "borrowed_view"
    decision = default_ownership_policy.decide_semantic_type(semantic_type, OwnershipContext.module_variable())
    assert not decision.is_blocked
    assert decision.owner is OwnershipOwner.NATIVE
    assert decision.transfer is TransferMode.BORROWED_VIEW
    assert decision.destruction is DestructionPolicy.NATIVE_OWNER


def test_copy_oriented_pointer_policy_still_exposes_live_contiguous_view():
    module = parse_pyi_text(
        """
value: Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="snapshot_copy",
        target_owner="module",
        lifetime="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="contiguous",
        reassociation="snapshot_final",
        aliasing="independent_copy",
        mutability="copy",
    ),
]
""",
        module_name="pointer_policy",
    )

    complete_semantic_policies(module)

    handle_policy = module.variables[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    assert not handle_policy.is_blocked
    assert handle_policy.getter_behavior == "handle"
    assert handle_policy.to_numpy == "contiguous_view"
    assert handle_policy.descriptor_interop == "pointer_c_descriptor"
    assert handle_policy.requires_pointer_c_descriptor_interop is True
    assert handle_policy.blocker is None


def test_pointer_policy_metadata_requires_every_fact():
    with pytest.raises(ValueError, match="missing: lifetime"):
        parse_pyi_text(
            """
value: Annotated[
    Pointer[Float64[:]],
    PointerPolicy(
        nullable=True,
        transfer="snapshot_copy",
        target_owner="module",
        deallocation="never",
        shape_source="pointer_bounds",
        contiguity="contiguous",
        reassociation="snapshot_final",
        aliasing="independent_copy",
        mutability="copy",
    ),
]
""",
            module_name="incomplete_pointer_policy",
        )


def test_pointer_policy_unsafe_deallocate_is_explicit_operation_opt_in():
    module = parse_pyi_text(
        """
def consume(
    default_target: Pointer[Float64[:]],
    unsafe_target: Annotated[
        Pointer[Float64[:]],
        PointerPolicy(
            nullable=True,
            transfer="call_local",
            target_owner="external",
            lifetime="call",
            deallocation="unsafe_deallocate",
            shape_source="pointer_bounds",
            contiguity="contiguous",
            reassociation="snapshot_final",
            aliasing="descriptor",
            mutability="mutable",
        ),
    ],
) -> None: ...
""",
        module_name="unsafe_deallocate_policy",
    )

    complete_semantic_policies(module)

    default_target = module.functions[0].arguments[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    unsafe_target = module.functions[0].arguments[1].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]

    assert set(default_target.operations) == {"associate", "associated", "nullify", "to_numpy"}
    assert set(unsafe_target.operations) == {"associate", "associated", "deallocate", "nullify", "to_numpy"}
    assert "allocate" not in unsafe_target.operations
    assert "resize" not in unsafe_target.operations

    emitted = PyiPrinter().emit(module.functions[0].arguments[1].semantic_type)
    assert 'deallocation="unsafe_deallocate"' in emitted


def test_native_array_handle_policies_complete_before_ir_lowering():
    module = parse_pyi_text(
        """
values: Allocatable[Float64[:]]
target_values: Annotated[Allocatable[Float64[:]], Aliased]

class box:
    values: Allocatable[Float64[:]]
    target: Pointer[Float64[:]]

def consume(
    values: Allocatable[Float64[:]],
    managed_target: Annotated[
        Pointer[Float64[:]],
        PointerPolicy(
            nullable=True,
            transfer="call_local",
            target_owner="caller",
            lifetime="call",
            deallocation="deallocate_resize",
            shape_source="pointer_bounds",
            contiguity="contiguous",
            reassociation="allocate_resize",
            aliasing="descriptor",
            mutability="mutable",
        ),
    ],
    maybe_target: Pointer[Float64[:]] | None = ...,
) -> None: ...

def make_values() -> Allocatable[Float64[:]]: ...
def make_target() -> Pointer[Float64[:]]: ...
""",
        module_name="native_handles",
    )

    complete_semantic_policies(module)

    values = module.variables[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    target_values = module.variables[1].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    field_values = module.classes[0].fields[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    field_target = module.classes[0].fields[1].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    argument_values = module.functions[0].arguments[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    managed_target = module.functions[0].arguments[1].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    optional_target = module.functions[0].arguments[2].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    allocatable_result = module.functions[1].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    pointer_result = module.functions[2].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]

    assert values.descriptor_kind == "allocatable"
    assert values.handle_kind == "borrowed_module_descriptor"
    assert values.origin == "module_variable"
    assert values.owner == "native"
    assert values.owner_retention == "native_module"
    assert values.descriptor_ownership == "borrowed"
    assert values.target_lifetime == "module"
    assert values.destroy_behavior == "none"
    assert values.to_numpy == "descriptor_view"
    assert values.descriptor_interop == "module_allocatable_c_descriptor"
    assert values.requires_pointer_c_descriptor_interop is False
    assert values.requires_c_descriptor_interop is True
    assert values.storage_mode == "heap"
    assert set(values.operations) == {"allocated", "deallocate", "resize", "to_numpy"}

    assert target_values.handle_kind == "borrowed_module_descriptor"
    assert target_values.owner_retention == "native_module"
    assert target_values.target_lifetime == "module"
    assert target_values.to_numpy == "borrowed_view"
    assert target_values.descriptor_interop == "none"
    assert target_values.requires_pointer_c_descriptor_interop is False

    assert field_values.handle_kind == "borrowed_field_descriptor"
    assert field_values.owner == "wrapper"
    assert field_values.owner_retention == "parent_wrapper"
    assert field_values.release == "wrapper_dealloc"
    assert field_values.target_lifetime == "parent_wrapper"
    assert field_values.destroy_behavior == "parent_wrapper_finalizer"

    assert field_target.descriptor_kind == "pointer"
    assert field_target.handle_kind == "borrowed_field_descriptor"
    assert field_target.target_lifetime == "parent_wrapper"
    assert field_target.destroy_behavior == "parent_wrapper_finalizer"
    assert field_target.getter_behavior == "handle"
    assert field_target.to_numpy == "unsupported"
    assert field_target.descriptor_interop == "pointer_c_descriptor"
    assert field_target.requires_pointer_c_descriptor_interop is True
    assert field_target.is_blocked is False
    assert set(field_target.operations) == {"associate", "associated", "nullify", "to_numpy"}

    assert argument_values.handle_kind == "argument_descriptor"
    assert argument_values.origin == "argument"
    assert argument_values.owner_retention == "caller_handle"
    assert argument_values.target_lifetime == "call"
    assert argument_values.destroy_behavior == "none"
    assert argument_values.is_blocked is False
    assert argument_values.blocker is None
    assert argument_values.descriptor_interop == "none"
    assert argument_values.requires_pointer_c_descriptor_interop is False
    assert set(argument_values.operations) == {"allocated", "to_numpy"}
    assert argument_values.default_construction == "fact_packed_empty"
    assert argument_values.default_descriptor_ownership == "owned"
    assert argument_values.default_release == "wrapper_dealloc"
    assert argument_values.default_destroy_behavior == "handle_finalizer"
    assert "destroy" in argument_values.default_operations

    assert optional_target.handle_kind == "optional_absent_handle"
    assert optional_target.optional_absent is True
    assert optional_target.nullable is True
    assert optional_target.owner_retention == "optional_argument"
    assert optional_target.target_lifetime == "absent_or_call"
    assert optional_target.destroy_behavior == "none"
    assert optional_target.is_blocked is False
    assert optional_target.blocker is None
    assert optional_target.descriptor_interop == "pointer_c_descriptor"
    assert optional_target.requires_pointer_c_descriptor_interop is True
    assert set(optional_target.operations) == {"associate", "associated", "nullify", "to_numpy"}
    assert optional_target.default_construction == "fact_packed_empty"
    assert "destroy" in optional_target.default_operations
    assert "allocate" not in optional_target.operations
    assert "deallocate" not in optional_target.operations
    assert "resize" not in optional_target.operations

    assert managed_target.handle_kind == "argument_descriptor"
    assert managed_target.descriptor_kind == "pointer"
    assert managed_target.target_lifetime == "call"
    assert managed_target.destroy_behavior == "none"
    assert managed_target.is_blocked is False
    assert managed_target.blocker is None
    assert managed_target.to_numpy == "contiguous_view"
    assert managed_target.descriptor_interop == "pointer_c_descriptor"
    assert managed_target.requires_pointer_c_descriptor_interop is True
    assert set(managed_target.operations) == {
        "allocate",
        "associate",
        "associated",
        "deallocate",
        "nullify",
        "resize",
        "to_numpy",
    }

    assert allocatable_result.handle_kind == "owned_result_descriptor"
    assert allocatable_result.origin == "result"
    assert allocatable_result.owner == "wrapper"
    assert allocatable_result.owner_retention == "wrapper_owner_storage"
    assert allocatable_result.descriptor_ownership == "owned"
    assert allocatable_result.output_projection == "handle_result"
    assert allocatable_result.release == "wrapper_dealloc"
    assert allocatable_result.target_lifetime == "wrapper_owner_storage"
    assert allocatable_result.destroy_behavior == "handle_finalizer"
    assert allocatable_result.is_blocked is False
    assert allocatable_result.descriptor_interop == "owned_allocatable_c_descriptor"
    assert allocatable_result.requires_pointer_c_descriptor_interop is False
    assert allocatable_result.requires_c_descriptor_interop is True
    assert set(allocatable_result.operations) == {"allocated", "deallocate", "resize", "to_numpy"}
    assert allocatable_result.default_construction == "none"
    assert allocatable_result.default_operations == ()

    assert pointer_result.handle_kind == "owned_result_descriptor"
    assert pointer_result.origin == "result"
    assert pointer_result.owner == "wrapper"
    assert pointer_result.owner_retention == "wrapper_owner_storage"
    assert pointer_result.descriptor_ownership == "owned"
    assert pointer_result.output_projection == "handle_result"
    assert pointer_result.release == "wrapper_dealloc"
    assert pointer_result.target_lifetime == "unknown"
    assert pointer_result.destroy_behavior == "handle_finalizer"
    assert pointer_result.is_blocked is False
    assert pointer_result.blocker is None
    assert pointer_result.descriptor_interop == "pointer_c_descriptor"
    assert pointer_result.requires_pointer_c_descriptor_interop is True
    assert pointer_result.requires_c_descriptor_interop is True
    assert set(pointer_result.operations) == {"associate", "associated", "nullify", "to_numpy"}
    assert pointer_result.default_construction == "none"


def test_native_array_handle_build_requirements_are_selected_from_completed_policy():
    module = parse_pyi_text(
        """
values: Allocatable[Float64[:]]
default_target: Pointer[Float64[:]]

def inspect(
    copy_target: Annotated[
        Pointer[Float64[:]],
        PointerPolicy(
            nullable=True,
            transfer="snapshot_copy",
            target_owner="caller",
            lifetime="call",
            deallocation="never",
            shape_source="pointer_bounds",
            contiguity="contiguous",
            reassociation="never",
            aliasing="independent_copy",
            mutability="copy",
        ),
    ],
    contiguous_target: Annotated[
        Pointer[Float64[:]],
        PointerPolicy(
            nullable=True,
            transfer="call_local",
            target_owner="caller",
            lifetime="call",
            deallocation="never",
            shape_source="pointer_bounds",
            contiguity="contiguous",
            reassociation="never",
            aliasing="borrowed",
            mutability="view",
        ),
    ],
    target: Annotated[
        Pointer[Float64[:]],
        PointerPolicy(
            nullable=True,
            transfer="call_local",
            target_owner="caller",
            lifetime="call",
            deallocation="never",
            shape_source="pointer_bounds",
            contiguity="strided",
            reassociation="never",
            aliasing="borrowed",
            mutability="view",
        ),
    ],
) -> None: ...
""",
        module_name="native_handle_build",
    )

    complete_semantic_policies(module)

    copy_target = module.functions[0].arguments[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    contiguous_target = module.functions[0].arguments[1].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    descriptor_target = module.functions[0].arguments[2].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]

    assert copy_target.to_numpy == "contiguous_view"
    assert copy_target.requires_pointer_c_descriptor_interop is True
    assert contiguous_target.to_numpy == "contiguous_view"
    assert contiguous_target.requires_pointer_c_descriptor_interop is True
    assert descriptor_target.to_numpy == "descriptor_view"
    assert descriptor_target.requires_pointer_c_descriptor_interop is True

    requirements = native_array_handle_build_requirements(module)

    assert requirements.pointer_c_descriptor_interop is True
    assert requirements.requires_iso_fortran_binding is True
    assert requirements.headers == ("ISO_Fortran_binding.h",)
    assert requirements.items == (
        NativeArrayBuildRequirement(
            owner="native_handle_build.values",
            item="values",
            descriptor_kind="allocatable",
            handle_kind="borrowed_module_descriptor",
            descriptor_interop="module_allocatable_c_descriptor",
            headers=("ISO_Fortran_binding.h",),
        ),
        NativeArrayBuildRequirement(
            owner="native_handle_build.default_target",
            item="default_target",
            descriptor_kind="pointer",
            handle_kind="borrowed_module_descriptor",
            descriptor_interop="pointer_c_descriptor",
            headers=("ISO_Fortran_binding.h",),
        ),
        NativeArrayBuildRequirement(
            owner="native_handle_build.inspect.copy_target",
            item="copy_target",
            descriptor_kind="pointer",
            handle_kind="argument_descriptor",
            descriptor_interop="pointer_c_descriptor",
            headers=("ISO_Fortran_binding.h",),
        ),
        NativeArrayBuildRequirement(
            owner="native_handle_build.inspect.contiguous_target",
            item="contiguous_target",
            descriptor_kind="pointer",
            handle_kind="argument_descriptor",
            descriptor_interop="pointer_c_descriptor",
            headers=("ISO_Fortran_binding.h",),
        ),
        NativeArrayBuildRequirement(
            owner="native_handle_build.inspect.target",
            item="target",
            descriptor_kind="pointer",
            handle_kind="argument_descriptor",
            descriptor_interop="pointer_c_descriptor",
            headers=("ISO_Fortran_binding.h",),
        ),
    )


def test_native_array_handle_build_requirements_require_completed_policy():
    module = parse_pyi_text(
        """
target: Pointer[Float64[:]]
""",
        module_name="native_handle_missing_policy",
    )

    with pytest.raises(ValueError, match="run complete_semantic_policies"):
        native_array_handle_build_requirements(module)
