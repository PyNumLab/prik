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
    ArgumentHandoffMode,
    BridgeDataAction,
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
    assert argument.deferred_character_length is True
    assert argument.character_length is None
    assert argument.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER


def test_fixed_and_assumed_length_string_arguments_stay_fixed_length():
    """Only a deferred length selects the allocatable adapter local.

    ``character(len=8)`` and ``character(len=*)`` both keep the fixed-length
    local, so this guards the narrow scope of the deferred flag.
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
        assert policy.arguments[0].deferred_character_length is False


@pytest.mark.parametrize(
    ("attribute", "intent", "expected"),
    [
        ("allocatable", "inout", "mutable deferred-length character argument"),
        ("pointer", "in", "deferred-length character pointer"),
    ],
)
def test_unsupported_deferred_length_character_arguments_are_blocked(
    attribute: str,
    intent: str,
    expected: str,
    tmp_path: Path,
):
    """Only the read-only allocatable deferred lane is wrapped.

    A mutable dummy may be reallocated to a length the caller buffer cannot
    hold, and a pointer dummy needs a pointer actual the adapter has no target
    for.  Both must stop at policy rather than emit an adapter that miscompiles
    or silently returns the pre-call value.
    """
    module = _semantic_module_from_text(
        f"""
module deferred_unsupported
  implicit none
contains
  subroutine consume(value, length)
    character(len=:), {attribute}, intent({intent}) :: value
    integer(4), intent(out) :: length
    length = len(value)
  end subroutine consume
end module deferred_unsupported
""",
        tmp_path,
        module_name="deferred_unsupported",
    )
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert any(expected in blocker for blocker in policy.blockers)
