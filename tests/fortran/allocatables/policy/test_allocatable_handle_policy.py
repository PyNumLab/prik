"""Tests split by stable ownership concept from `test_handle_policy_dispatch.py`."""

from prik.semantics.models import (
    RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA,
    RESOLVED_OWNERSHIP_POLICY_METADATA,
)
from prik.policy.native_array_handles import (
    NativeArrayBuildRequirement,
    native_array_handle_build_requirements,
)
from prik.policy.ownership import (
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    OwnershipContext,
    OwnershipOwner,
    StorageMode,
    TransferMode,
    default_ownership_policy,
)
from prik.policy.completion import complete_semantic_policies
from prik.parsers.fortran import parse_fortran_file
from prik.planning import WrapperPlanner
from prik.policy.models import NativeArrayOwnerStorage, NativeDescriptorHandoffABI, NativeEntrypointAction
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from tests.fortran._support.ownership_policy import (
    _array_type,
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


def test_deferred_character_writeback_uses_fortran_owner_storage():
    module = parse_pyi_text(
        """
def replace_names(
    values: Allocatable[String[:][:]],
) -> Returns["values", Allocatable[String[:][:]]]: ...
""",
        module_name="caller_created_deferred_character_handle",
    )
    complete_semantic_policies(module)

    policy = module.functions[0].arguments[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]

    assert policy.default_construction == "lazy_fortran_owner"
    assert policy.owner_storage == "fortran_owner"
    assert policy.element_length_argument is True
    assert "destroy" in policy.default_operations


def test_deferred_character_owner_storage_keeps_the_direct_descriptor_abi():
    """Storage ownership does not replace a bind(C) procedure's declared ABI."""
    parsed = parse_fortran_file(
        """
module direct_character_owner
  use iso_c_binding
contains
  subroutine rewrite(values) bind(c)
    character(kind=c_char, len=:), allocatable, intent(inout) :: values(:, :)
  end subroutine
end module
"""
    )
    module = fortran_module_to_semantic_module(parsed.modules[0])
    complete_semantic_policies(module)
    function = WrapperPlanner().build(module).namespaces[0].functions[0]
    handle = function.arguments[0].native_array_handle
    assert handle.owner_storage is NativeArrayOwnerStorage.FORTRAN_OWNER
    assert handle.handoff.abi is NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR
    assert function.entrypoint.action is NativeEntrypointAction.DIRECT_C_ABI
    assert function.entrypoint.symbol_name == "rewrite"


def test_aliased_does_not_change_allocatable_live_view_semantics():
    """A module allocatable is reached through its descriptor either way.

    `Aliased` would allow `c_loc` on the variable, but that yields only a base
    address: lower bounds, strides and element length would then have to be
    assumed rather than read, and a non-default lower bound makes the assumption
    wrong. Both declarations therefore complete to the same descriptor policy.
    """
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

    assert values.to_numpy == shared_values.to_numpy == "descriptor_view"
    assert values.descriptor_interop == shared_values.descriptor_interop == "module_allocatable_c_descriptor"
    assert values.owner == shared_values.owner == "native"
    assert values.borrowed is shared_values.borrowed is True


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


def test_deferred_length_character_allocation_plans_an_explicit_element_length():
    """A deferred length has no width to reuse, so allocation must be given one.

    The standard rejects an allocate-object with a deferred length type
    parameter unless a type-spec, SOURCE or MOLD supplies the width, so policy
    completes the width as a planned argument instead of leaving the bridge to
    invent one. Every other entity already knows its element width.
    """
    module = parse_pyi_text(
        """
deferred: Allocatable[String[:][:]]
fixed: Allocatable[String[8][:]]
numeric: Allocatable[Float64[:]]
""",
        module_name="deferred_character_allocation",
    )

    complete_semantic_policies(module)

    deferred, fixed, numeric = (
        variable.metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA] for variable in module.variables
    )

    assert deferred.element_length_argument is True
    assert fixed.element_length_argument is False
    assert numeric.element_length_argument is False


def test_a_deferred_length_character_array_can_be_resized():
    """Shape mutation is available once the width travels with the extents.

    Resize was previously withheld from these arrays because the generated
    allocation had no width to name. That reason is gone, so withholding the
    operation would only remove a capability the entity supports.
    """
    module = parse_pyi_text(
        "deferred: Allocatable[String[:][:]]",
        module_name="deferred_character_resize",
    )

    complete_semantic_policies(module)

    policy = module.variables[0].metadata[RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA]

    assert policy.allows("resize")
    assert policy.allows("deallocate")
