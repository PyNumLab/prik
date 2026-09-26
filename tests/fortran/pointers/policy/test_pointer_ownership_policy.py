"""Completed pointer ownership and native-array handle policy."""

from pathlib import Path

import pytest
from prik.printers import PyiPrinter
from prik.semantics.models import (
    RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA,
)
from prik.policy.native_array_handles import (
    NativeArrayBuildRequirement,
    NativeArrayHandlePolicyDispatcher,
    native_array_handle_build_requirements,
)
from prik.policy.ownership import (
    CodegenAction,
    DestructionPolicy,
    OwnershipContext,
    OwnershipOwner,
    TransferMode,
    default_ownership_policy,
)
from prik.semantics.ownership_metadata import set_ownership_metadata
from prik.policy.completion import complete_semantic_policies
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

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


def test_native_array_handle_dispatcher_rejects_missing_completed_policy_pair():
    dispatcher = NativeArrayHandlePolicyDispatcher({})

    with pytest.raises(ValueError, match="pointer/borrowed_module_descriptor"):
        dispatcher.handler_name_for_policy(
            _native_array_policy(descriptor_kind="pointer"),
            "target",
        )


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
    ("owner", "transfer", "destruction", "blocker"),
    [
        ("native", "copy_return", "native_owner", "native/copy_return/native_owner"),
        ("native", "borrowed_view", "python_refcount", "native/borrowed_view/python_refcount"),
        ("python", "copy_return", "native_owner", "python/copy_return/native_owner"),
        ("python", "borrowed_view", "python_refcount", "python/borrowed_view/python_refcount"),
        ("wrapper", "wrapper_instance", "python_refcount", "wrapper/wrapper_instance/python_refcount"),
        ("native", "blocked", "native_owner", "blocked by ownership policy"),
    ],
)
def test_contradictory_or_explicitly_blocked_ownership_triples_fail_closed(
    owner: str,
    transfer: str,
    destruction: str,
    blocker: str,
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
    assert decision.codegen_action is CodegenAction.BLOCKED
    assert blocker in decision.blocker


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


def test_pointer_container_ownership_is_fixed_by_its_native_parent():
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


def test_deferred_character_pointer_arguments_select_an_opaque_fortran_owner():
    module = parse_pyi_text(
        """
deferred_ptr: Pointer[String[:][:]]

def inspect(values: Pointer[String[:][:]]) -> None: ...
""",
        module_name="deferred_character_pointer_arrays",
    )

    complete_semantic_policies(module)

    module_policy = module.variables[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    argument_policy = module.functions[0].arguments[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]

    assert module_policy.is_blocked is False
    assert module_policy.descriptor_inquiries is False
    assert module_policy.descriptor_interop == "none"
    assert set(module_policy.operations) == {"associated", "deallocate", "nullify"}
    assert argument_policy.is_blocked is False
    assert argument_policy.descriptor_inquiries is False
    assert argument_policy.descriptor_interop == "none"
    assert argument_policy.owner_storage == "fortran_owner"
    assert argument_policy.default_construction == "lazy_fortran_owner"
    assert argument_policy.owner_type_name
    assert argument_policy.owner_signature
    assert set(argument_policy.operations) == {"associate", "associated", "nullify"}


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


_BORROWED_ALLOCATABLE_OPERATIONS = ("allocated", "deallocate", "resize", "to_numpy")
_DEFAULT_POINTER_OPERATIONS = ("associate", "associated", "deallocate", "nullify", "to_numpy")


def test_native_array_handle_policies_complete_before_ir_lowering():
    """Each handle origin completes one ownership, lifetime, and operation profile.

    Borrowed descriptors are never destroyed by their handle; owned result
    descriptors are, and a pointer result owns its descriptor but not its
    target.  Release of a default pointer target is a manual operation, while
    allocation needs an explicit `PointerPolicy`.
    """
    module = parse_pyi_text(
        (NATIVE_FIXTURES / "native_array_handle_policies_complete_before_ir_lowering.f90").read_text(encoding="utf-8"),
        module_name="native_handles",
    )

    complete_semantic_policies(module)

    entities = {variable.name: variable for variable in module.variables}
    entities.update({f"box.{field.name}": field for field in module.classes[0].fields})
    entities.update({f"consume.{argument.name}": argument for argument in module.functions[0].arguments})
    entities.update({function.name: function for function in module.functions[1:]})
    completed = {
        name: (
            policy.descriptor_kind,
            policy.handle_kind,
            policy.descriptor_ownership,
            policy.target_lifetime,
            policy.destroy_behavior,
            policy.to_numpy,
            tuple(sorted(policy.operations)),
            policy.default_construction,
        )
        for name, entity in entities.items()
        for policy in (entity.metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA],)
        if not policy.is_blocked
    }

    module_allocatable = (
        "allocatable",
        "borrowed_module_descriptor",
        "borrowed",
        "module",
        "none",
        "descriptor_view",
        _BORROWED_ALLOCATABLE_OPERATIONS,
        "none",
    )
    assert completed == {
        "values": module_allocatable,
        # `Aliased` selects neither another NumPy exposure nor another interop.
        "target_values": module_allocatable,
        "module_target": (
            "pointer",
            "borrowed_module_descriptor",
            "borrowed",
            "module",
            "none",
            "unsupported",
            _DEFAULT_POINTER_OPERATIONS,
            "none",
        ),
        "box.values": (
            "allocatable",
            "borrowed_field_descriptor",
            "borrowed",
            "parent_wrapper",
            "parent_wrapper_finalizer",
            "borrowed_view",
            _BORROWED_ALLOCATABLE_OPERATIONS,
            "none",
        ),
        "box.target": (
            "pointer",
            "borrowed_field_descriptor",
            "borrowed",
            "parent_wrapper",
            "parent_wrapper_finalizer",
            "unsupported",
            _DEFAULT_POINTER_OPERATIONS,
            "none",
        ),
        # A descriptor argument is handed a descriptor the Fortran runtime
        # built, so a caller-created handle lazily gets storage of its own.
        "consume.values": (
            "allocatable",
            "argument_descriptor",
            "borrowed",
            "call",
            "none",
            "borrowed_view",
            ("allocated", "to_numpy"),
            "lazy_owned_descriptor",
        ),
        "consume.managed_target": (
            "pointer",
            "argument_descriptor",
            "borrowed",
            "call",
            "none",
            "contiguous_view",
            ("allocate", "associate", "associated", "deallocate", "nullify", "resize", "to_numpy"),
            "lazy_owned_descriptor",
        ),
        "consume.maybe_target": (
            "pointer",
            "optional_absent_handle",
            "borrowed",
            "absent_or_call",
            "none",
            "unsupported",
            ("associate", "associated", "nullify", "to_numpy"),
            "lazy_owned_descriptor",
        ),
        "make_values": (
            "allocatable",
            "owned_result_descriptor",
            "owned",
            "wrapper_owner_storage",
            "handle_finalizer",
            "borrowed_view",
            _BORROWED_ALLOCATABLE_OPERATIONS,
            "none",
        ),
        "make_target": (
            "pointer",
            "owned_result_descriptor",
            "owned",
            "unknown",
            "handle_finalizer",
            "unsupported",
            _DEFAULT_POINTER_OPERATIONS,
            "none",
        ),
    }


def test_native_array_handle_build_requirements_are_selected_from_completed_policy():
    """Copy and contiguous pointers expose a contiguous view; a strided one exposes the descriptor."""
    module = parse_pyi_text(
        """
values: Allocatable[Float64[:]]
default_target: Pointer[Float64[:]]

class box:
    target: Pointer[Float64[:]]

def make_values() -> Allocatable[Float64[:]]: ...

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

    arguments = module.functions[1].arguments
    copy_target, contiguous_target, descriptor_target = (
        argument.metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA] for argument in arguments
    )

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
            owner="native_handle_build.box.target",
            item="target",
            descriptor_kind="pointer",
            handle_kind="borrowed_field_descriptor",
            descriptor_interop="pointer_c_descriptor",
            headers=("ISO_Fortran_binding.h",),
        ),
        NativeArrayBuildRequirement(
            owner="native_handle_build.make_values.return",
            item="return",
            descriptor_kind="allocatable",
            handle_kind="owned_result_descriptor",
            descriptor_interop="owned_allocatable_c_descriptor",
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
