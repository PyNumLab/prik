from pathlib import Path

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.wrapper_build import wrapper_source
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from prik.preprocessing import PreprocessingConfig
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
)
from prik.policy.ownership import (
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    ObjectKind,
    OwnershipOwner,
    PythonBarrierAction,
    TransferMode,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    ArgumentConversionPhase,
    CharacterLocalRelease,
    NativeArrayDescriptorKind,
    ArgumentHandoffMode,
    BridgeDataAction,
    OptionalMode,
    WritebackPhase,
)

FMATH_CONTRACT = Path("tests/fortran/data_types/end_to_end/fixtures/baseline/contracts/fmath/__init__.pyi")


def _source_semantic_module(filename: str, *, module_name: str):
    source = wrapper_source(filename)
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


def test_wrapper_policy_completes_required_read_only_string_value_handoff():
    module = parse_pyi_text(
        "def consume(value: String) -> None: ...",
        module_name="string_argument",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is True
    assert policy.blockers == ()
    argument = policy.arguments[0]
    assert argument.python_barrier_action is PythonBarrierAction.STRING_VALUE
    assert argument.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert argument.codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert argument.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER
    assert argument.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert argument.bridge_copy_reason == ("materialize Fortran character storage from the binding UTF-8 byte buffer")


def test_wrapper_policy_completes_fixed_string_direct_and_hidden_copy_results():
    module = parse_pyi_text(
        """
def direct_label() -> String[8]: ...

@native_call([Return("label", 0)])
def hidden_label() -> String[8]: ...
""",
        module_name="fixed_string_results",
    )
    complete_semantic_policies(module)
    direct_policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    hidden_policy = module.functions[1].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert direct_policy.supported is True
    direct = direct_policy.results[0]
    assert direct.ownership.kind is ObjectKind.STRING
    assert direct.codegen_action is CodegenAction.COPY_OUT
    assert direct.native_barrier_action is NativeBarrierAction.NONE
    assert direct.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert direct.character_length == 8

    assert hidden_policy.supported is True
    hidden = hidden_policy.results[0]
    assert hidden.ownership.kind is ObjectKind.STRING
    assert hidden.codegen_action is CodegenAction.COPY_OUT
    assert hidden.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert hidden.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert hidden.character_length == 8
    assert hidden_policy.native_call_slots[0].character_length == hidden.character_length


def test_wrapper_policy_completes_fixed_string_replacement_and_discarded_identity():
    module = parse_pyi_text(
        """
def replace_name(name: String[8]) -> Returns["name", String[8]]: ...
def discard_name(name: String[8]) -> None: ...
""",
        module_name="fixed_string_writeback",
    )
    complete_semantic_policies(module)
    replacement = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    identity = module.functions[1].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert replacement.supported is True
    argument = replacement.arguments[0]
    assert argument.ownership.kind is ObjectKind.STRING
    assert argument.ownership.owner is OwnershipOwner.PYTHON
    assert argument.ownership.transfer is TransferMode.COPY_RETURN
    assert argument.ownership.destruction is DestructionPolicy.PYTHON_REFCOUNT
    assert argument.codegen_action is CodegenAction.COPY_IN_OUT
    assert argument.conversion_phase is ArgumentConversionPhase.DEFERRED_REPLACEMENT
    assert argument.character_length == 8
    assert argument.projects_result is True
    # The native call mutates a binding-owned replacement, not the immutable
    # Python string supplied at the public boundary.
    assert argument.writable is False
    assert tuple(action.phase for action in replacement.writeback_actions) == tuple(WritebackPhase)

    assert identity.supported is True
    assert identity.arguments[0].codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert identity.arguments[0].projects_result is False
    assert identity.writeback_actions == ()


def _semantic_module_from_text(source_text: str, tmp_path: Path, *, module_name: str):
    """Complete policy for one inline Fortran source without a shared fixture."""
    source = tmp_path / f"{module_name}.f90"
    source.write_text(source_text, encoding="utf-8")
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


def test_read_only_deferred_length_string_argument_completes_deferred_policy(tmp_path: Path):
    """A ``character(len=:)`` input records the fact the adapter needs.

    No ``bind(C)`` interface can declare a deferred-length dummy, so the
    generated Fortran adapter must build the allocatable local itself.  Policy
    owns that fact; the bridge only implements it.
    """
    module = _semantic_module_from_text(
        """
module deferred_input
  implicit none
contains
  subroutine measure(value, length)
    character(len=:), allocatable, intent(in) :: value
    integer(4), intent(out) :: length
    length = len(value)
  end subroutine measure
end module deferred_input
""",
        tmp_path,
        module_name="deferred_input",
    )
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is True
    argument = policy.arguments[0]
    assert argument.character_local is not None
    assert argument.character_local.deferred_length is True
    assert argument.character_local.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
    assert argument.character_local.release is CharacterLocalRelease.NONE
    assert argument.character_length is None
    assert argument.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER


def test_fixed_and_assumed_length_string_arguments_stay_plain_locals():
    """Only a descriptor attribute selects a descriptor adapter local.

    ``character(len=8)`` and ``character(len=*)`` are neither allocatable nor
    pointer, so both keep the plain fixed-length local and owe no release.
    """
    module = parse_pyi_text(
        """
def fixed(text: String[8]) -> Int32: ...
def assumed(text: String) -> Int32: ...
""",
        module_name="non_deferred_strings",
    )
    complete_semantic_policies(module)

    for index in (0, 1):
        policy = module.functions[index].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
        local = policy.arguments[0].character_local
        assert local is not None
        assert local.descriptor_kind is None
        assert local.deferred_length is False
        assert local.release is CharacterLocalRelease.NONE


@pytest.mark.parametrize(
    ("intent", "release"),
    [
        ("in", CharacterLocalRelease.DEALLOCATE),
        ("inout", CharacterLocalRelease.DEALLOCATE_IF_RETAINED),
    ],
)
def test_character_pointer_arguments_complete_their_release_responsibility(
    intent: str,
    release: CharacterLocalRelease,
    tmp_path: Path,
):
    """A pointer local is storage the adapter allocated, so policy must say who frees it.

    An ``intent(in)`` dummy cannot change its association, so the allocation is
    always still the adapter's to release.  A mutable dummy may be reassociated
    or deallocated by the native procedure, so the adapter may only release the
    allocation while the dummy still identifies it.
    """
    module = _semantic_module_from_text(
        f"""
module pointer_input
  implicit none
contains
  subroutine consume(value, length)
    character(len=:), pointer, intent({intent}) :: value
    integer(4), intent(out) :: length
    length = 0
    if (associated(value)) length = len(value)
  end subroutine consume
end module pointer_input
""",
        tmp_path,
        module_name="pointer_input",
    )
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is True
    local = policy.arguments[0].character_local
    assert local is not None
    assert local.descriptor_kind is NativeArrayDescriptorKind.POINTER
    assert local.deferred_length is True
    assert local.release is release


def test_deferred_length_string_update_completes_input_plus_descriptor_result(tmp_path: Path):
    """A mutable ``character(len=:)`` dummy keeps its input and gains a result facet.

    The caller's ``str`` cannot carry back a length chosen during the call, so
    policy completes two decisions for the one dummy: a call-local character
    buffer for the input, and a nullable descriptor result that owns the
    reallocated storage.  Argument writeback stays absent because the value
    travels as that result.
    """
    module = _semantic_module_from_text(
        """
module deferred_update
  implicit none
contains
  subroutine grow(value)
    character(len=:), allocatable, intent(inout) :: value
    if (allocated(value)) value = value // '!'
  end subroutine grow
end module deferred_update
""",
        tmp_path,
        module_name="deferred_update",
    )
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is True
    argument = policy.arguments[0]
    assert argument.codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert argument.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER
    assert argument.optional_mode is OptionalMode.REQUIRED
    assert argument.descriptor_boundary is False
    assert argument.nullable is False
    assert argument.projects_character_descriptor_update is True
    assert policy.writeback_actions == ()

    result = policy.results[0]
    assert result.updates_argument is True
    assert result.owner_path == argument.owner_path
    assert result.codegen_action is CodegenAction.COPY_OUT
    assert result.ownership.owner is OwnershipOwner.PYTHON
    assert result.ownership.python_visible is False
    assert result.scalar_descriptor is not None
    assert result.scalar_descriptor.runtime_length is True
    assert result.scalar_descriptor.nullable is True
    assert result.scalar_descriptor.release_owner is OwnershipOwner.PYTHON


def test_fixed_length_allocatable_string_update_takes_the_descriptor_result_lane(tmp_path: Path):
    """The descriptor attribute, not the length, selects the update lane.

    A copy-in/copy-out replacement writes back through the caller's buffer,
    which means passing that buffer as the actual argument.  An allocatable
    dummy will not accept one, so a fixed-length allocatable takes the same
    call-local input and projected descriptor result a deferred length does.
    """
    module = _semantic_module_from_text(
        """
module fixed_update
  implicit none
contains
  subroutine relabel(value)
    character(len=8), allocatable, intent(inout) :: value
    value = 'fixed'
  end subroutine relabel
end module fixed_update
""",
        tmp_path,
        module_name="fixed_update",
    )
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is True
    argument = policy.arguments[0]
    assert argument.codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert argument.projects_character_descriptor_update is True
    assert argument.character_local is not None
    assert argument.character_local.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
    assert argument.character_local.deferred_length is False
    assert policy.writeback_actions == ()
    assert policy.results[0].updates_argument is True


def test_plain_fixed_length_string_update_keeps_copy_in_out_replacement(tmp_path: Path):
    """A dummy with no descriptor attribute keeps the caller-buffer replacement.

    Nothing about that dummy rejects the caller's buffer as the actual
    argument, so it stays on the writeback lane rather than gaining a result.
    """
    module = _semantic_module_from_text(
        """
module plain_update
  implicit none
contains
  subroutine relabel(value)
    character(len=8), intent(inout) :: value
    value = 'fixed'
  end subroutine relabel
end module plain_update
""",
        tmp_path,
        module_name="plain_update",
    )
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    argument = policy.arguments[0]
    assert argument.codegen_action is CodegenAction.COPY_IN_OUT
    assert argument.projects_character_descriptor_update is False
    assert policy.results == ()
    assert tuple(action.phase for action in policy.writeback_actions) == tuple(WritebackPhase)
