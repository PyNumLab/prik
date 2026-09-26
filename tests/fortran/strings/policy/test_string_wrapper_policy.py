"""Character dummy attributes select one completed policy lane before planning.

Policy owns which adapter local a character dummy gets, who releases it, and
whether a mutable dummy writes back through the caller's buffer or returns its
reallocated value as a descriptor result. No ``bind(C)`` interface can declare
a deferred-length or descriptor character dummy, so the generated Fortran
adapter must build these locals; the bridge only implements the decision.
Runtime behavior of every lane is proved in ``tests/fortran/strings/end_to_end/``.
"""

from pathlib import Path

import pytest

from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import CharacterLocalRelease, NativeArrayDescriptorKind, WritebackPhase
from prik.policy.ownership import CodegenAction, OwnershipOwner
from prik.preprocessing import PreprocessingConfig, read_fortran_source
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA

ALLOCATABLE = NativeArrayDescriptorKind.ALLOCATABLE
POINTER = NativeArrayDescriptorKind.POINTER


def _completed_policy(declaration: str, tmp_path: Path):
    source = tmp_path / "character_lane.f90"
    source.write_text(
        f"""
module character_lane
  implicit none
contains
  subroutine work(value)
    {declaration} :: value
  end subroutine work
end module character_lane
""",
        encoding="utf-8",
    )
    parsed = parse_fortran_project({str(source): read_fortran_source(source, PreprocessingConfig()).source})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="character_lane")
    complete_semantic_policies(module)
    return module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]


@pytest.mark.parametrize(
    ("declaration", "descriptor_kind", "deferred", "release", "lane"),
    [
        ("character(len=8), intent(in)", None, False, CharacterLocalRelease.NONE, "input"),
        ("character(len=*), intent(in)", None, False, CharacterLocalRelease.NONE, "input"),
        ("character(len=8), intent(inout)", None, False, CharacterLocalRelease.NONE, "writeback"),
        ("character(len=:), allocatable, intent(in)", ALLOCATABLE, True, CharacterLocalRelease.NONE, "input"),
        ("character(len=:), allocatable, intent(inout)", ALLOCATABLE, True, CharacterLocalRelease.NONE, "update"),
        ("character(len=8), allocatable, intent(inout)", ALLOCATABLE, False, CharacterLocalRelease.NONE, "update"),
        ("character(len=:), pointer, intent(in)", POINTER, True, CharacterLocalRelease.DEALLOCATE, "input"),
        (
            "character(len=:), pointer, intent(inout)",
            POINTER,
            True,
            CharacterLocalRelease.DEALLOCATE_IF_RETAINED,
            "update",
        ),
    ],
    ids=[
        "fixed-input",
        "assumed-input",
        "plain-fixed-inout-writes-back",
        "deferred-allocatable-input",
        "deferred-allocatable-update",
        "fixed-allocatable-update",
        "pointer-input-always-released",
        "pointer-update-released-only-if-retained",
    ],
)
def test_character_dummy_attributes_select_local_release_and_update_lane(
    declaration: str,
    descriptor_kind: NativeArrayDescriptorKind | None,
    deferred: bool,
    release: CharacterLocalRelease,
    lane: str,
    tmp_path: Path,
):
    """The descriptor attribute, not the length, selects the adapter local and update lane.

    A plain dummy accepts the caller's buffer, so an ``inout`` one writes back
    through it. An allocatable or pointer dummy will not accept that buffer, so
    a mutable one takes a call-local input plus a nullable descriptor result
    that returns whatever length the native procedure chose. An ``intent(in)``
    pointer cannot reassociate, so its allocation is always the adapter's to
    free; a mutable one may only be freed while the dummy still identifies it.
    """
    policy = _completed_policy(declaration, tmp_path)

    assert policy.supported is True
    argument = policy.arguments[0]
    local = argument.character_local
    assert local is not None
    assert (local.descriptor_kind, local.deferred_length, local.release) == (descriptor_kind, deferred, release)

    if lane == "writeback":
        assert argument.codegen_action is CodegenAction.COPY_IN_OUT
        assert tuple(action.phase for action in policy.writeback_actions) == tuple(WritebackPhase)
        assert policy.results == ()
        return
    assert argument.codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert policy.writeback_actions == ()
    assert argument.projects_character_descriptor_update is (lane == "update")
    if lane == "update":
        (result,) = policy.results
        assert result.updates_argument is True
        assert result.owner_path == argument.owner_path
        assert result.scalar_descriptor.runtime_length is True
        assert result.scalar_descriptor.nullable is True
        assert result.scalar_descriptor.release_owner is OwnershipOwner.PYTHON
    else:
        assert policy.results == ()
