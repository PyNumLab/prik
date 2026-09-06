"""Generated handles used as every supported ordinary Fortran array form."""

from __future__ import annotations

import gc
import sys
from pathlib import Path

import numpy as np
import pytest

from prik import contracts
from prik.runtime.handles import AllocatableArray, PointerArray
from tests.fortran._support.wrapper_build import _build_text_and_import


pytestmark = pytest.mark.fortran_end_to_end


NATIVE_HANDLE_ARRAY_FORMS_SOURCE = """\
module fhandle_array_forms_f90
  implicit none
  real(8), allocatable :: values(:)
  real(8), allocatable :: matrix(:, :)
  real(8), allocatable :: hyper(:, :, :, :, :, :, :, :, :, :, :, :, :, :, :)
  real(8), target :: backing(8)
  real(8), pointer :: strided_values(:)
  character(len=:), allocatable :: words(:)
contains
  subroutine setup()
    integer :: i

    allocate(values(4))
    values = [1.0_8, 2.0_8, 3.0_8, 4.0_8]
    allocate(matrix(2, 3))
    matrix = reshape([(1.0_8 * i, i = 1, 6)], [2, 3])
    allocate(hyper(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1))
    hyper = 1.0_8
    backing = [(1.0_8 * i, i = 1, 8)]
    strided_values => backing(1:8:2)
    allocate(character(len=5) :: words(2))
    words = [character(len=5) :: "alpha", "bravo"]
  end subroutine setup

  function explicit_total(actual, n) result(total)
    integer(4), intent(in) :: n
    real(8), intent(in) :: actual(n)
    real(8) :: total

    total = sum(actual)
  end function explicit_total

  function assumed_total(actual) result(total)
    real(8), intent(in) :: actual(:)
    real(8) :: total

    total = sum(actual)
  end function assumed_total

  function flat_total(actual, n) result(total)
    integer(4), intent(in) :: n
    real(8), intent(in) :: actual(*)
    real(8) :: total

    total = sum(actual(:n))
  end function flat_total

  function optional_total(actual) result(total)
    real(8), intent(in), optional :: actual(:)
    real(8) :: total

    if (present(actual)) then
      total = sum(actual)
    else
      total = -1.0_8
    end if
  end function optional_total

  function rank_score(actual) result(score)
    real(8), intent(in) :: actual(..)
    integer(4) :: score

    select rank (actual)
    rank (1)
      score = 100 + size(actual)
    rank (2)
      score = 200 + size(actual)
    rank (15)
      score = 1500 + size(actual)
    rank default
      score = -1
    end select
  end function rank_score

  function element_width(actual) result(width)
    character(len=*), intent(in) :: actual(:)
    integer(4) :: width

    width = len(actual)
  end function element_width
end module fhandle_array_forms_f90
"""


def test_generated_handles_cover_supported_ordinary_array_forms(tmp_path: Path):
    module = _build_text_and_import(
        NATIVE_HANDLE_ARRAY_FORMS_SOURCE,
        "fhandle_array_forms_f90.f90",
        tmp_path,
        {
            "bind_c_fhandle_array_forms_f90_wrapper.f90",
            "fhandle_array_forms_f90_wrapper.c",
            "fhandle_array_forms_f90_wrapper.h",
        },
    )

    values = module.values
    strided = module.strided_values
    assert isinstance(values, AllocatableArray)
    assert isinstance(strided, PointerArray)
    with pytest.raises(ValueError, match="unallocated"):
        module.assumed_total(values)
    with pytest.raises(ValueError, match="unassociated"):
        module.assumed_total(strided)

    module.setup()

    assert module.explicit_total(values, np.int32(4)) == np.float64(10.0)
    assert module.assumed_total(values) == np.float64(10.0)
    assert module.flat_total(values, np.int32(4)) == np.float64(10.0)
    assert module.optional_total() == np.float64(-1.0)
    assert module.optional_total(None) == np.float64(-1.0)
    assert module.optional_total(values) == np.float64(10.0)
    assert module.rank_score(values) == np.int32(104)
    assert module.rank_score(module.matrix) == np.int32(206)
    assert module.rank_score(module.hyper) == np.int32(1501)
    assert module.assumed_total(strided) == np.float64(16.0)
    assert module.element_width(module.words) == np.int32(5)

    with pytest.raises(TypeError, match="incompatible shape at axis 0"):
        module.explicit_total(values, np.int32(3))
    with pytest.raises(TypeError, match="does not match expected dtype"):
        module.assumed_total(module.words)


NATIVE_HANDLE_DESCRIPTOR_MATRIX_SOURCE = """\
module fhandle_descriptor_matrix_f90
  use iso_c_binding, only: c_bool
  implicit none

  type :: holder
    real(8), allocatable :: field_allocatable_values_with_long_name(:)
    logical(4), allocatable :: field_flags(:)
    real(8), pointer :: field_ptr(:) => null()
    character(len=:), pointer :: field_words(:) => null()
  end type holder

  integer(4), allocatable :: ints(:)
  real(4), allocatable :: reals(:)
  complex(8), allocatable :: complexes(:)
  logical(c_bool), allocatable :: flags(:)
  character(len=4), allocatable :: fixed_words(:)
  character(len=:), allocatable :: deferred_words(:)
  real(8), allocatable :: empty(:)
  real(8), allocatable :: spare(:)
  real(8), allocatable :: probe(:)
  real(8), allocatable :: optional_probe(:)
  real(8), allocatable :: pair_left(:)
  real(8), allocatable :: pair_right(:)
  real(8), allocatable :: pair_third(:)
  real(8), allocatable :: cube(:, :, :)
  real(8), target :: store(8)
  real(8), pointer :: reversed(:) => null()
  real(8), pointer :: strided(:) => null()
  real(8), pointer :: unassociated(:) => null()
  type(holder) :: parent

contains

  subroutine setup()
    integer :: i

    allocate(ints(3));        ints = [1_4, 2_4, 3_4]
    allocate(reals(2));       reals = [1.5_4, 2.5_4]
    allocate(complexes(2));   complexes = [(1.0_8, 2.0_8), (3.0_8, 4.0_8)]
    allocate(flags(3));       flags = [.true._c_bool, .false._c_bool, .true._c_bool]
    allocate(fixed_words(2)); fixed_words = ['abcd', 'efgh']
    allocate(character(len=6) :: deferred_words(2))
    deferred_words = ['alphas', 'bravos']
    allocate(empty(0))
    allocate(probe(3)); probe = 2.0_8
    allocate(optional_probe(3)); optional_probe = 2.0_8
    allocate(pair_left(3));  pair_left = 6.0_8
    allocate(pair_right(3)); pair_right = 7.0_8
    allocate(pair_third(3)); pair_third = 8.0_8
    allocate(cube(2, 3, 4)); cube = 1.0_8
    store = [(1.0_8 * i, i = 1, 8)]
    reversed => store(8:1:-1)
    strided => store(1:8:2)
    allocate(parent%field_allocatable_values_with_long_name(3))
    parent%field_allocatable_values_with_long_name = 5.0_8
    allocate(parent%field_flags(3)); parent%field_flags = [.true., .false., .true.]
    parent%field_ptr => store(2:6:2)
    allocate(character(len=5) :: parent%field_words(2))
    parent%field_words = ['alpha', 'beta ']
  end subroutine setup

  subroutine reshape_alloc(values, n)
    real(8), allocatable, intent(inout) :: values(:)
    integer(4), intent(in) :: n

    if (allocated(values)) deallocate(values)
    allocate(values(n))
    values = 4.0_8
  end subroutine reshape_alloc

  subroutine grow_pair(first, second, n)
    real(8), allocatable, intent(inout) :: first(:), second(:)
    integer(4), intent(in) :: n

    if (allocated(first)) deallocate(first)
    if (allocated(second)) deallocate(second)
    allocate(first(n));  first = 8.0_8
    allocate(second(n)); second = 9.0_8
  end subroutine grow_pair

  subroutine grow_three(first, second, third, n)
    real(8), allocatable, intent(inout) :: first(:), second(:), third(:)
    integer(4), intent(in) :: n

    if (allocated(first)) deallocate(first)
    if (allocated(second)) deallocate(second)
    if (allocated(third)) deallocate(third)
    allocate(first(n));  first = 8.0_8
    allocate(second(n)); second = 9.0_8
    allocate(third(n));  third = 10.0_8
  end subroutine grow_three

  function optional_state(values) result(state)
    real(8), allocatable, optional, intent(in) :: values(:)
    integer(4) :: state

    if (.not. present(values)) then
      state = 0
    else if (.not. allocated(values)) then
      state = 1
    else
      state = int(sum(values), kind=4)
    end if
  end function optional_state

  subroutine grow_and_count(values, n, produced)
    real(8), allocatable, intent(inout) :: values(:)
    integer(4), intent(in) :: n
    integer(4), intent(out) :: produced

    if (allocated(values)) deallocate(values)
    allocate(values(n)); values = 11.0_8
    produced = n
  end subroutine grow_and_count

  function optional_alloc_state(values) result(state)
    real(8), allocatable, intent(in), optional :: values(:)
    integer(4) :: state

    if (.not. present(values)) then
      state = 0
    else if (allocated(values)) then
      state = 2
    else
      state = 1
    end if
  end function optional_alloc_state

  function assumed_total(actual) result(total)
    real(8), intent(in) :: actual(:)
    real(8) :: total

    total = sum(actual)
  end function assumed_total

  function int_total(actual) result(total)
    integer(4), intent(in) :: actual(:)
    integer(4) :: total

    total = sum(actual)
  end function int_total

  function real4_total(actual) result(total)
    real(4), intent(in) :: actual(:)
    real(4) :: total

    total = sum(actual)
  end function real4_total

  function complex_total(actual) result(total)
    complex(8), intent(in) :: actual(:)
    complex(8) :: total

    total = sum(actual)
  end function complex_total

  function true_count(actual) result(counted)
    logical(c_bool), intent(in) :: actual(:)
    integer(4) :: counted

    counted = count(actual)
  end function true_count

  function word_width(actual) result(width)
    character(len=*), intent(in) :: actual(:)
    integer(4) :: width

    width = len(actual)
  end function word_width

  function cube_score(actual) result(score)
    real(8), intent(in) :: actual(:, :, :)
    integer(4) :: score

    score = size(actual)
  end function cube_score
end module fhandle_descriptor_matrix_f90
"""


@pytest.fixture(scope="module")
def descriptor_matrix(tmp_path_factory):
    module = _build_text_and_import(
        NATIVE_HANDLE_DESCRIPTOR_MATRIX_SOURCE,
        "fhandle_descriptor_matrix_f90.f90",
        tmp_path_factory.mktemp("descriptor_matrix"),
        {
            "bind_c_fhandle_descriptor_matrix_f90_wrapper.f90",
            "fhandle_descriptor_matrix_f90_wrapper.c",
            "fhandle_descriptor_matrix_f90_wrapper.h",
        },
    )
    module.setup()
    return module


@pytest.mark.parametrize(
    ("name", "dtype", "shape", "expected"),
    [
        ("ints", np.int32, (3,), [1, 2, 3]),
        ("reals", np.float32, (2,), [1.5, 2.5]),
        ("complexes", np.complex128, (2,), [1 + 2j, 3 + 4j]),
        ("flags", np.bool_, (3,), [True, False, True]),
        ("fixed_words", "S4", (2,), [b"abcd", b"efgh"]),
        ("deferred_words", "S6", (2,), [b"alphas", b"bravos"]),
        ("empty", np.float64, (0,), []),
        ("cube", np.float64, (2, 3, 4), None),
    ],
)
def test_every_supported_element_type_reports_its_own_dtype_shape_and_view(
    descriptor_matrix,
    name: str,
    dtype,
    shape: tuple[int, ...],
    expected,
):
    """One descriptor read answers dtype, shape and the view, for every element type."""
    handle = getattr(descriptor_matrix, name)

    assert isinstance(handle, AllocatableArray)
    assert handle.allocated is True
    assert handle.dtype == np.dtype(dtype)
    assert handle.shape == shape

    view = handle.to_numpy()
    assert view.dtype == np.dtype(dtype)
    assert view.shape == shape
    if expected is not None:
        np.testing.assert_array_equal(view, np.array(expected, dtype=dtype))


def test_each_element_type_reaches_a_matching_ordinary_dummy(descriptor_matrix):
    """The storage behind a handle satisfies an ordinary dummy of its own type."""
    assert descriptor_matrix.int_total(descriptor_matrix.ints) == np.int32(6)
    assert descriptor_matrix.real4_total(descriptor_matrix.reals) == np.float32(4.0)
    assert descriptor_matrix.complex_total(descriptor_matrix.complexes) == np.complex128(4 + 6j)
    assert descriptor_matrix.true_count(descriptor_matrix.flags) == np.int32(2)
    assert descriptor_matrix.word_width(descriptor_matrix.fixed_words) == np.int32(4)
    assert descriptor_matrix.word_width(descriptor_matrix.deferred_words) == np.int32(6)
    assert descriptor_matrix.cube_score(descriptor_matrix.cube) == np.int32(24)
    # A zero-sized allocation is present storage that happens to hold nothing.
    assert descriptor_matrix.assumed_total(descriptor_matrix.empty) == np.float64(0.0)


def test_pointer_targets_report_their_shape_and_reach_an_ordinary_dummy(descriptor_matrix):
    """A pointer's storage satisfies an array dummy however its target is laid out.

    The dummy is reached through a descriptor, which carries a signed stride per
    axis, so the direction an axis runs is something the callee is told rather
    than something the caller has to undo. A reversed target and a strided one
    both arrive, and both sum to what their own elements sum to. Extraction
    itself stays gated behind PointerPolicy.
    """
    reversed_handle = descriptor_matrix.reversed
    strided_handle = descriptor_matrix.strided

    assert isinstance(reversed_handle, PointerArray)
    assert reversed_handle.associated is True
    assert reversed_handle.shape == (8,)
    assert strided_handle.shape == (4,)

    assert descriptor_matrix.assumed_total(strided_handle) == np.float64(16.0)
    # store is 1..8, so the reversed view holds the same elements either way.
    assert descriptor_matrix.assumed_total(reversed_handle) == np.float64(36.0)

    for handle in (reversed_handle, strided_handle):
        with pytest.raises(NotImplementedError, match="unsupported by completed policy"):
            handle.to_numpy()


def test_an_unassociated_pointer_reports_absence_through_every_inquiry(descriptor_matrix):
    handle = descriptor_matrix.unassociated

    assert handle.associated is False
    assert handle.shape is None
    assert handle.to_numpy() is None
    with pytest.raises(ValueError, match="unassociated"):
        descriptor_matrix.assumed_total(handle)


def test_a_derived_type_field_view_retains_its_parent(descriptor_matrix):
    """A field's storage belongs to its parent, so a view has to keep it alive."""
    parent = descriptor_matrix.parent
    field = parent.field_allocatable_values_with_long_name
    pointer_field = parent.field_ptr
    logical_field = parent.field_flags
    words_field = parent.field_words

    assert field.shape == (3,)
    np.testing.assert_allclose(field.to_numpy(), np.array([5.0, 5.0, 5.0]))
    assert pointer_field.associated is True
    assert pointer_field.shape == (3,)
    assert logical_field.dtype == np.dtype(np.int32)
    np.testing.assert_array_equal(logical_field.to_numpy().astype(bool), [True, False, True])
    assert words_field.associated is True
    assert words_field.shape == (2,)
    assert words_field.dtype == np.dtype("S5")
    words_field.deallocate()
    assert words_field.associated is False
    assert words_field.shape is None

    view = field.to_numpy()
    assert view.base is not None
    del field
    del parent
    gc.collect()
    np.testing.assert_allclose(view, np.array([5.0, 5.0, 5.0]))


def test_reallocating_through_a_dummy_updates_every_later_inquiry(descriptor_matrix):
    """Allocation state written by the callee reaches the caller's handle.

    `spare` is this test's alone, so the shared fixture keeps the state every
    other test in this module reads.
    """
    spare = descriptor_matrix.spare
    assert spare.allocated is False
    assert spare.shape is None

    descriptor_matrix.reshape_alloc(spare, np.int32(3))
    assert spare.shape == (3,)
    np.testing.assert_allclose(spare.to_numpy(), np.array([4.0, 4.0, 4.0]))
    assert descriptor_matrix.assumed_total(spare) == np.float64(12.0)

    descriptor_matrix.reshape_alloc(spare, np.int32(5))
    assert spare.shape == (5,)

    spare.deallocate()
    assert spare.allocated is False
    assert spare.shape is None
    assert spare.to_numpy() is None
    with pytest.raises(ValueError, match="unallocated"):
        descriptor_matrix.assumed_total(spare)


def test_a_bound_handle_reaches_a_native_call_without_running_python(descriptor_matrix):
    """Argument handoff costs no Python frame once the arguments are parsed.

    A handle publishes its backend to C, so the binding reads the capsule,
    validates it against the dummy and enters the descriptor itself. Nothing on
    that path imports the runtime, looks an operation up on the handle, or packs
    descriptor fields into Python values for C to read back -- which is the
    whole point of the capsule, and is only observable as the absence of a
    Python call.
    """
    ordinary = descriptor_matrix.ints
    descriptor = descriptor_matrix.probe
    int_total = descriptor_matrix.int_total
    reshape_alloc = descriptor_matrix.reshape_alloc
    assumed_total = descriptor_matrix.assumed_total
    optional_alloc_state = descriptor_matrix.optional_alloc_state
    called: list[str] = []

    def record(frame, event, _arg):
        if event == "call":
            called.append(f"{frame.f_code.co_filename}:{frame.f_code.co_name}")

    sys.setprofile(record)
    try:
        int_total(ordinary)
        assumed_total(descriptor)
        reshape_alloc(descriptor, np.int32(2))
        assert optional_alloc_state() == np.int32(0)
        assert optional_alloc_state(None) == np.int32(0)
        assert optional_alloc_state(descriptor) == np.int32(2)
    finally:
        sys.setprofile(None)

    assert called == []
    assert descriptor.shape == (2,)


def test_two_descriptor_dummies_reach_borrowed_and_owned_storage_alike(descriptor_matrix):
    """Two descriptors are live at once, so both callees' writes reach their entities.

    Each argument is entered in turn and the call is made inside the last
    consumer, where every descriptor the Fortran runtime built is still valid.
    A module array and a caller-created handle are placed the same way, and
    both see the reallocation the callee performed.
    """
    left = descriptor_matrix.pair_left
    right = descriptor_matrix.pair_right

    descriptor_matrix.grow_pair(left, right, np.int32(2))
    assert left.shape == (2,)
    assert right.shape == (2,)
    np.testing.assert_allclose(left.to_numpy(), np.array([8.0, 8.0]))
    np.testing.assert_allclose(right.to_numpy(), np.array([9.0, 9.0]))

    owned_first = contracts.Allocatable[contracts.Float64[:]]()
    try:
        # One borrowed and one owned handle in the same call: the chain enters
        # whatever each publishes without distinguishing them.
        descriptor_matrix.grow_pair(left, owned_first, np.int32(3))
        assert left.shape == (3,)
        assert owned_first.shape == (3,)
        np.testing.assert_allclose(owned_first.to_numpy(), np.array([9.0, 9.0, 9.0]))
    finally:
        owned_first.close()


def test_three_descriptor_dummies_keep_every_borrowed_descriptor_live(descriptor_matrix):
    first = descriptor_matrix.pair_left
    second = descriptor_matrix.pair_right
    third = descriptor_matrix.pair_third

    descriptor_matrix.grow_three(first, second, third, np.int32(4))

    assert first.shape == second.shape == third.shape == (4,)
    np.testing.assert_allclose(first.to_numpy(), np.full(4, 8.0))
    np.testing.assert_allclose(second.to_numpy(), np.full(4, 9.0))
    np.testing.assert_allclose(third.to_numpy(), np.full(4, 10.0))


def test_a_handle_reaches_a_call_with_a_hidden_output_without_running_python(descriptor_matrix):
    """An intent(out) argument is carried, not read after the consumer returns.

    The call runs inside the consumer holding the descriptor, so the hidden
    output is written through the address this frame carried in; the frame
    outlives every consumer it enters, so reading it afterwards is sound and
    no Python runs on the way.
    """
    spare = descriptor_matrix.pair_left
    called: list[str] = []

    def record(frame, event, _arg):
        if event == "call":
            called.append(frame.f_code.co_name)

    descriptor_matrix.grow_and_count(spare, np.int32(2))
    sys.setprofile(record)
    try:
        produced = descriptor_matrix.grow_and_count(spare, np.int32(4))
    finally:
        sys.setprofile(None)

    assert called == []
    assert int(produced[1]) == 4
    assert spare.shape == (4,)


def test_an_optional_descriptor_argument_runs_no_python_however_it_is_supplied(descriptor_matrix):
    """Absence is decided in C, for an omitted argument as much as a supplied one.

    An absent optional has no handle to publish a backend, so nothing is
    entered for it and the binding establishes the unallocated placeholder the
    bridge is handed. Deciding that needs the argument object and nothing else,
    so none of the three ways of supplying it goes back into Python.
    """
    # This array is this test's alone, so its sum stays what the fixture set.
    present = descriptor_matrix.optional_probe
    called: list[str] = []

    def record(frame, event, _arg):
        if event == "call":
            called.append(frame.f_code.co_name)

    descriptor_matrix.optional_state()
    descriptor_matrix.optional_state(None)
    descriptor_matrix.optional_state(present)

    sys.setprofile(record)
    try:
        omitted = descriptor_matrix.optional_state()
        explicit_none = descriptor_matrix.optional_state(None)
        supplied = descriptor_matrix.optional_state(present)
    finally:
        sys.setprofile(None)

    assert called == []
    assert omitted == np.int32(0)
    assert explicit_none == np.int32(0)
    assert supplied == np.int32(6)
