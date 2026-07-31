"""Tests split by stable ownership concept from `test_handle_policy_dispatch.py`."""

from tests.fortran._support.ownership_policy import (
    CodegenAction,
    DestructionPolicy,
    NativeArrayBuildRequirement,
    NativeBarrierAction,
    OwnershipContext,
    OwnershipOwner,
    RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA,
    RESOLVED_OWNERSHIP_POLICY_METADATA,
    StorageMode,
    TransferMode,
    _array_type,
    complete_semantic_policies,
    default_ownership_policy,
    native_array_handle_build_requirements,
    parse_pyi_text,
)


def test_allocatable_array_field_is_wrapper_owned_borrowed_view():
    decision = default_ownership_policy.decide_semantic_type(
        _array_type(allocatable=True),
        OwnershipContext.field(),
    )

    assert decision.owner is OwnershipOwner.WRAPPER
    assert decision.transfer is TransferMode.BORROWED_VIEW
    assert decision.destruction is DestructionPolicy.WRAPPER_DEALLOC
    assert decision.storage_mode is StorageMode.HEAP
    assert decision.borrowed is True
    assert decision.nullable is True


def test_hidden_allocatable_handle_output_completes_as_owned_result_before_lowering():
    module = parse_pyi_text(
        """
@native_call([Return("values", 0)])
def make_values() -> Allocatable[Float64[:]]: ...
""",
        module_name="hidden_allocatable_handle_result",
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
    assert policy.handle_kind == "owned_result_descriptor"
    assert policy.origin == "projected_result"
    assert policy.owner_retention == "wrapper_owner_storage"
    assert policy.descriptor_ownership == "owned"
    assert policy.output_projection == "projected_handle"


def test_visible_descriptor_writeback_completes_caller_handle_construction_lifecycle():
    module = parse_pyi_text(
        """
@native_call([Arg(0)])
def replace_values(
    values: Allocatable[Float64[:]],
) -> Returns["values", Allocatable[Float64[:]]]: ...
""",
        module_name="caller_created_handle",
    )
    complete_semantic_policies(module)

    policy = module.functions[0].arguments[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]

    assert policy.default_construction == "lazy_owned_descriptor"
    assert policy.default_descriptor_ownership == "owned"
    assert policy.default_release == "wrapper_dealloc"
    assert policy.default_destroy_behavior == "handle_finalizer"
    assert "destroy" in policy.default_operations


def test_aliased_does_not_change_allocatable_live_view_semantics():
    module = parse_pyi_text(
        """
values: Allocatable[Float64[:]]
shared_values: Annotated[Allocatable[Float64[:]], Aliased]
""",
        module_name="allocatable_numpy_policy",
    )

    complete_semantic_policies(module)

    values = module.variables[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]
    shared_values = module.variables[1].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]

    assert values.to_numpy == "descriptor_view"
    assert shared_values.to_numpy == "borrowed_view"
    assert values.owner == shared_values.owner == "native"
    assert values.borrowed is shared_values.borrowed is True
    assert values.descriptor_interop == "module_allocatable_c_descriptor"
    assert shared_values.descriptor_interop == "none"


def test_owned_allocatable_result_records_local_standard_c_descriptor_build_requirement():
    module = parse_pyi_text(
        """
def make_values() -> Allocatable[Float64[:]]: ...
""",
        module_name="owned_allocatable_build",
    )
    complete_semantic_policies(module)

    requirements = native_array_handle_build_requirements(module)

    assert requirements.pointer_c_descriptor_interop is False
    assert requirements.requires_iso_fortran_binding is True
    assert requirements.headers == ("ISO_Fortran_binding.h",)
    assert requirements.items == (
        NativeArrayBuildRequirement(
            owner="owned_allocatable_build.make_values.return",
            item="return",
            descriptor_kind="allocatable",
            handle_kind="owned_result_descriptor",
            descriptor_interop="owned_allocatable_c_descriptor",
            headers=("ISO_Fortran_binding.h",),
        ),
    )
