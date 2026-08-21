"""Runtime evidence for allocatable and pointer scalar ``character`` boundaries."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_or_generated_pyi_and_import

FIXTURES = Path(__file__).parent / "fixtures"
DESCRIPTOR_SOURCE = FIXTURES / "fstring_descriptors_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"

pytestmark = pytest.mark.fortran_end_to_end


@pytest.fixture
def compiled_descriptor_module(pyi_parity_build_mode: str, tmp_path: Path):
    """Build the same module from Fortran source and from its generated contract.

    Every descriptor form here has a contract spelling, so both routes must
    reach the same runtime behavior; building only from source would hide a
    contract that no longer describes the procedure it was generated from.
    """
    return _build_source_or_generated_pyi_and_import(
        DESCRIPTOR_SOURCE,
        tmp_path,
        {
            "bind_c_fstring_descriptors_f90_wrapper.f90",
            "fstring_descriptors_f90_wrapper.c",
            "fstring_descriptors_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fstring_descriptors_f90",
        pyi_parity_build_mode,
    )


def test_deferred_length_string_update_returns_the_reallocated_value(compiled_descriptor_module):
    """The caller receives the length the native procedure chose, not the one it passed.

    Returning the pre-call value compiles, imports, and runs, so only a real
    call proves the adapter reads back the reallocated local.
    """
    module = compiled_descriptor_module

    assert module.grow("ab") == "ab!!!"
    assert module.grow("") == "!!!"
    assert module.grow("café") == "café!!!"
    assert module.shrink("abcdef") == "ab"


def test_deferred_length_string_update_reports_an_unallocated_dummy_as_none(compiled_descriptor_module):
    """Deallocation is a value Python can observe, so it must not read freed storage."""
    module = compiled_descriptor_module

    assert module.drop("abc") is None
    assert module.optional_grow() is None
    assert module.optional_grow(None) is None
    assert module.optional_grow("abc") == "abc?"


def test_deferred_length_string_updates_keep_their_public_result_order(compiled_descriptor_module):
    """Several updates, and an update beside another output, stay in contract order."""
    module = compiled_descriptor_module

    assert module.grow_both("a", "b") == ("a-1", "b-2")
    assert module.grow_and_measure("ab") == ("ab-tail", np.int32(7))


def test_read_only_deferred_length_character_lanes_still_wrap(compiled_descriptor_module):
    """The input and output lanes keep working beside the new update lane."""
    module = compiled_descriptor_module

    assert module.measure("abcd") == 4
    assert module.make() == "made"


def test_deferred_length_string_update_reports_allocation_failure(
    compiled_descriptor_module,
    monkeypatch: pytest.MonkeyPatch,
):
    """The returned copy is C storage, so a failed allocation must raise, not truncate."""
    module = compiled_descriptor_module

    monkeypatch.setenv("PRIK_WRAPPER_FAIL_ALLOC", "1")
    with pytest.raises(MemoryError):
        module.grow("ab")


def test_fixed_length_allocatable_character_arguments_wrap_in_every_direction(compiled_descriptor_module):
    """A declared length does not remove the allocatable attribute from the dummy.

    The actual argument must still be allocatable, so these forms exercise the
    same descriptor lanes a deferred length uses while keeping their width.
    """
    module = compiled_descriptor_module

    assert module.measure_fixed_allocatable("abcd") == 4
    assert module.make_fixed_allocatable() == "MADE"
    assert module.relabel_fixed_allocatable("abcd") == "Xbcd"
    assert module.drop_fixed_allocatable("abcd") is None


def test_character_pointer_arguments_wrap_in_every_direction(compiled_descriptor_module):
    """A pointer dummy needs an associated actual, which the adapter allocates itself."""
    module = compiled_descriptor_module

    assert module.measure_pointer("abcde") == 5
    assert module.point_at_static() == "STATIC"
    assert module.measure_fixed_pointer("abcd") == 4
    assert module.point_at_fixed_static() == "FOUR"
    assert module.relabel_fixed_pointer("abcd") == "Pbcd"


def test_character_pointer_update_reports_whatever_the_dummy_ends_up_holding(compiled_descriptor_module):
    """A pointer update publishes the association the native procedure leaves behind.

    In-place writes, reassociation to native storage, deallocation, and
    nullification are four different endings for the same dummy, and each is a
    distinct Python value rather than the value the caller passed in.
    """
    module = compiled_descriptor_module

    assert module.edit_pointer_in_place("abc") == "Z  "
    assert module.reassociate_pointer("ab") == "STATIC"
    assert module.deallocate_pointer("ab") is None
    assert module.nullify_pointer("ab") is None
    assert module.regrow_pointer("ab") == "ab>>>"


def test_absent_optional_character_pointer_is_never_released(compiled_descriptor_module):
    """An absent argument skips the allocation, so the local has nothing to free.

    Releasing it anyway reads an association status the adapter never
    established, which crashes rather than returning a wrong value.
    """
    module = compiled_descriptor_module

    assert module.optional_pointer_measure() == -1
    assert module.optional_pointer_measure(None) == -1
    assert module.optional_pointer_measure("abcde") == 5
    assert module.optional_pointer_edit() is None
    assert module.optional_pointer_edit(None) is None
    assert module.optional_pointer_edit("abc") == "q  "


def test_character_pointer_update_release_survives_repeated_calls(compiled_descriptor_module):
    """The adapter allocates a target per call, so its release must be exactly once.

    Deallocating storage the native procedure already freed, or freeing the
    replacement it associated instead, crashes rather than fails an assertion,
    so repetition is what makes the release decision observable.
    """
    module = compiled_descriptor_module

    for _ in range(2000):
        assert module.deallocate_pointer("ab") is None
        assert module.regrow_pointer("ab") == "ab>>>"
        assert module.reassociate_pointer("ab") == "STATIC"
        assert module.nullify_pointer("ab") is None
        assert module.measure_pointer("abcde") == 5
        assert module.optional_pointer_measure() == -1


def test_descriptor_character_function_results_are_copied_before_return(compiled_descriptor_module):
    """Allocatable and pointer results both reach Python as ordinary strings."""
    module = compiled_descriptor_module

    assert module.allocatable_result() == "allocatable"
    assert module.fixed_allocatable_result() == "FIXA"
    assert module.pointer_result() == "STATIC"
    assert module.fixed_pointer_result() == "FOUR"
