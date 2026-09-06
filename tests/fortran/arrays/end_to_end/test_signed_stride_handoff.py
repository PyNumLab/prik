"""Signed-stride handoff to ordinary array dummies, from every supported source."""

from __future__ import annotations

import sys

import numpy as np
import pytest

from prik.runtime.handles import PointerArray
from tests.fortran._support.wrapper_build import _build_text_and_import


pytestmark = pytest.mark.fortran_end_to_end


SIGNED_STRIDE_SOURCE = """\
module fsigned_strides_f90
  use iso_c_binding
  implicit none

  type :: holder
    real(8), pointer :: field_ptr(:) => null()
  end type holder

  real(8), target :: store(24)
  real(8), pointer :: reversed_ptr(:) => null()
  real(8), pointer :: strided_ptr(:) => null()
  real(8), pointer :: unassociated_ptr(:) => null()
  type(holder) :: parent
  character(len=4), allocatable :: words(:)

contains

  subroutine setup()
    integer :: i

    do i = 1, 24
      store(i) = real(i, kind=8)
    end do
    reversed_ptr => store(8:1:-1)
    strided_ptr => store(1:8:2)
    parent%field_ptr => store(6:1:-1)
    if (allocated(words)) deallocate(words)
    allocate(words(2))
    words = ['abcd', 'efgh']
  end subroutine setup

  ! Bridged assumed-shape: not bind(C), so a bridge exists.
  function total1(a) result(t)
    real(8), intent(in) :: a(:)
    real(8) :: t

    t = sum(a)
  end function total1

  ! Direct assumed-shape: bind(C), so C calls it with no bridge at all.
  function total1_bindc(a) result(t) bind(c, name="fsigned_total1_bindc")
    real(c_double), intent(in) :: a(:)
    real(c_double) :: t

    t = sum(a)
  end function total1_bindc

  ! Weighted so that reading the axes in the wrong order changes the answer.
  function checksum2(a) result(t)
    real(8), intent(in) :: a(:, :)
    real(8) :: t
    integer :: i, j

    t = 0.0_8
    do j = 1, size(a, 2)
      do i = 1, size(a, 1)
        t = t + a(i, j) * (100.0_8 * i + 10.0_8 * j)
      end do
    end do
  end function checksum2

  function total3(a) result(t)
    real(8), intent(in) :: a(:, :, :)
    real(8) :: t

    t = sum(a)
  end function total3

  subroutine negate1(a)
    real(8), intent(inout) :: a(:)

    a = -a
  end subroutine negate1

  ! Two descriptor dummies in one call.
  function dot2(a, b) result(t)
    real(8), intent(in) :: a(:), b(:)
    real(8) :: t

    t = sum(a * b)
  end function dot2

  function optional_total(a) result(t)
    real(8), intent(in), optional :: a(:)
    real(8) :: t

    if (present(a)) then
      t = sum(a)
    else
      t = -1.0_8
    end if
  end function optional_total

  function rank_and_size(a) result(s)
    real(8), intent(in) :: a(..)
    integer(4) :: s

    s = 100_4 * int(rank(a), 4) + int(size(a), 4)
  end function rank_and_size

  ! An assumed-shape dummy always sees lower bound 1, whatever the actual had.
  function first_and_last(a) result(t)
    real(8), intent(in) :: a(:)
    real(8) :: t

    t = a(1) * 1000.0_8 + a(size(a)) + real(lbound(a, 1), kind=8)
  end function first_and_last

  ! Raw-address dummies: the declaration says the layout, nothing is conveyed.
  function explicit_total(a, n) result(t)
    integer(4), intent(in) :: n
    real(8), intent(in) :: a(n)
    real(8) :: t

    t = sum(a)
  end function explicit_total

  function flat_total(a, n) result(t)
    integer(4), intent(in) :: n
    real(8), intent(in) :: a(*)
    real(8) :: t

    t = sum(a(:n))
  end function flat_total

  function contig_total(a) result(t)
    real(8), intent(in), contiguous :: a(:)
    real(8) :: t

    t = sum(a)
  end function contig_total

  function word_width(a) result(w)
    character(len=*), intent(in) :: a(:)
    integer(4) :: w

    w = int(len(a), 4)
  end function word_width
end module fsigned_strides_f90
"""


@pytest.fixture(scope="module")
def signed(tmp_path_factory):
    module = _build_text_and_import(
        SIGNED_STRIDE_SOURCE,
        "fsigned_strides_f90.f90",
        tmp_path_factory.mktemp("signed-strides"),
        {
            "bind_c_fsigned_strides_f90_wrapper.f90",
            "fsigned_strides_f90_wrapper.c",
            "fsigned_strides_f90_wrapper.h",
        },
    )
    module.setup()
    return module


def _base(n=8):
    return np.arange(1.0, n + 1.0)


def _matrix(rows=4, cols=3):
    return np.asfortranarray(np.arange(1.0, rows * cols + 1.0).reshape((rows, cols), order="F"))


def _checksum2(array):
    total = 0.0
    for i, j in np.ndindex(array.shape):
        total += array[i, j] * (100.0 * (i + 1) + 10.0 * (j + 1))
    return total


@pytest.mark.parametrize(
    "view",
    [
        pytest.param(lambda: _base()[::-1], id="rank-one-reversal"),
        pytest.param(lambda: _base()[::-2], id="step-minus-2"),
        pytest.param(lambda: _base()[::2], id="step-2"),
        pytest.param(lambda: _base(), id="contiguous"),
        pytest.param(lambda: _base()[:0], id="zero-sized"),
        pytest.param(lambda: _base()[:0][::-1], id="zero-sized-reversed"),
        pytest.param(lambda: _base()[:1][::-1], id="single-element-reversed"),
    ],
)
def test_rank_one_numpy_views_reach_an_assumed_shape_dummy(signed, view):
    """Whatever direction an axis runs, the callee reads the caller's elements."""
    array = view()

    assert signed.total1(array) == pytest.approx(float(array.sum()))
    assert signed.total1_bindc(array) == pytest.approx(float(array.sum()))


@pytest.mark.parametrize(
    "view",
    [
        pytest.param(lambda: _matrix()[::-1, :], id="axis-0-reversed"),
        pytest.param(lambda: _matrix()[:, ::-1], id="axis-1-reversed"),
        pytest.param(lambda: _matrix()[::-1, ::-1], id="both-axes-reversed"),
        pytest.param(lambda: _matrix(8, 3)[::-2, :], id="mixed-sign-strided"),
        pytest.param(lambda: _matrix(8, 3)[::2, :], id="positive-strided"),
        pytest.param(lambda: _matrix(0, 3), id="zero-sized-axis"),
    ],
)
def test_rank_two_numpy_views_keep_their_axis_order(signed, view):
    """The weighting makes a transposed or misread axis a different answer."""
    array = view()

    assert signed.checksum2(array) == pytest.approx(_checksum2(array))


def test_a_singleton_axis_preserves_padding_between_later_sections(signed):
    """An unobservable singleton stride does not collapse a later padded axis."""
    storage = np.arange(5.0)
    view = np.ndarray((2, 1, 2), dtype=np.float64, buffer=storage, strides=(8, 0, 24))

    assert signed.total3(view) == pytest.approx(float(view.sum()))


def test_a_reversed_view_is_written_through_to_the_callers_storage(signed):
    """intent(inout) reaches the caller's own elements, in their own order."""
    array = _base()
    reversed_view = array[::-1]
    before = np.array(reversed_view, copy=True)

    signed.negate1(reversed_view)

    np.testing.assert_allclose(reversed_view, -before)
    # The original, unreversed array holds the same negated elements.
    np.testing.assert_allclose(array, -_base())


def test_an_assumed_shape_dummy_rebases_every_actual_to_one(signed):
    """A descriptor's own lower bounds are not portable, and are not relied on.

    gfortran normalises a section to zero and ifx keeps the parent's subscript,
    so nothing may read them. An assumed-shape dummy has lower bound 1 whatever
    it was handed, which is what the callee sees.
    """
    for view in (_base(), _base()[::-1], _base()[::2], _base()[::-2]):
        expected = view[0] * 1000.0 + view[-1] + 1.0
        assert signed.first_and_last(view) == pytest.approx(expected)


def test_a_reversed_pointer_handle_reaches_the_same_dummy(signed):
    """A handle's descriptor already records its direction; it is entered as it is."""
    reversed_handle = signed.reversed_ptr
    strided_handle = signed.strided_ptr

    assert isinstance(reversed_handle, PointerArray)
    assert reversed_handle.shape == (8,)

    # store is 1..24; the reversed view covers store(8:1:-1).
    assert signed.total1(reversed_handle) == pytest.approx(36.0)
    assert signed.total1_bindc(reversed_handle) == pytest.approx(36.0)
    assert signed.total1(strided_handle) == pytest.approx(16.0)


def test_a_reversed_derived_field_handle_reaches_the_same_dummy(signed):
    """A field handle is entered through its parent, and keeps its direction."""
    field = signed.parent.field_ptr

    assert isinstance(field, PointerArray)
    assert field.shape == (6,)
    # store(6:1:-1) holds 6, 5, 4, 3, 2, 1.
    assert signed.total1(field) == pytest.approx(21.0)


def test_one_call_takes_several_descriptors_from_different_sources(signed):
    """Every descriptor in a call is live at once, whoever supplied it."""
    left = _base(4)[::-1]
    right = _base(4)

    assert signed.dot2(left, right) == pytest.approx(float((left * right).sum()))

    # A borrowed handle and a NumPy array in the same call.
    handle = signed.strided_ptr
    ones = np.ones(4)
    assert signed.dot2(handle, ones) == pytest.approx(16.0)
    assert signed.dot2(ones, handle) == pytest.approx(16.0)

    # Two borrowed handles, both reversed, in the same call.
    assert signed.dot2(signed.reversed_ptr, signed.reversed_ptr) == pytest.approx(204.0)


def test_an_optional_descriptor_dummy_accepts_omitted_none_and_reversed(signed):
    """Absence is decided before anything is described."""
    assert signed.optional_total() == pytest.approx(-1.0)
    assert signed.optional_total(None) == pytest.approx(-1.0)
    assert signed.optional_total(_base()) == pytest.approx(36.0)
    assert signed.optional_total(_base()[::-1]) == pytest.approx(36.0)
    assert signed.optional_total(signed.reversed_ptr) == pytest.approx(36.0)


def test_assumed_rank_dummies_read_rank_and_size_from_the_descriptor(signed):
    """An assumed-rank dummy accepts every supported rank and section direction."""
    assert signed.rank_and_size(_base()) == np.int32(108)
    assert signed.rank_and_size(_matrix()) == np.int32(212)
    assert signed.rank_and_size(_base()[::-1]) == np.int32(108)
    assert signed.rank_and_size(_matrix()[::-1, ::-1]) == np.int32(212)
    assert signed.rank_and_size(signed.reversed_ptr) == np.int32(108)


def test_a_character_dummy_reports_its_own_width_from_either_source(signed):
    """Character arrays keep their runtime element width on the portable path."""
    assert signed.word_width(signed.words) == np.int32(4)
    assert signed.word_width(np.array([b"abcd", b"efgh"], dtype="S4")) == np.int32(4)

    with pytest.raises(TypeError, match=r"runs backwards|cannot record a direction|expected ordering"):
        signed.word_width(np.array([b"abcd", b"efgh"], dtype="S4")[::-1])


def test_a_bound_handle_reaches_a_signed_stride_call_without_running_python(signed):
    """The reversed handoff costs no Python frame once the arguments are parsed."""
    handle = signed.reversed_ptr
    total1 = signed.total1
    called: list[str] = []

    def record(frame, event, _arg):
        if event == "call":
            called.append(frame.f_code.co_name)

    total1(handle)
    sys.setprofile(record)
    try:
        value = total1(handle)
    finally:
        sys.setprofile(None)

    assert called == []
    assert value == pytest.approx(36.0)


def test_raw_address_dummies_refuse_what_an_address_cannot_convey(signed):
    """Each refusal names the restriction it comes from.

    An explicit-shape or assumed-size dummy receives the address of the first
    element and nothing else, so a direction has nowhere to be recorded. A
    CONTIGUOUS dummy keeps its requirement even though its calling convention
    carries a descriptor. Neither is the same as a layout Fortran has no form
    for at all.
    """
    reversed_view = _base()[::-1]

    with pytest.raises(TypeError, match=r"contiguous|expected ordering"):
        signed.explicit_total(reversed_view, np.int32(8))
    with pytest.raises(TypeError, match=r"contiguous|expected ordering"):
        signed.flat_total(reversed_view, np.int32(8))
    with pytest.raises(TypeError, match=r"expected ordering|contiguous"):
        signed.contig_total(reversed_view)

    # Positive strides still reach the ones that accept them.
    assert signed.explicit_total(_base(), np.int32(8)) == pytest.approx(36.0)
    assert signed.contig_total(_base()) == pytest.approx(36.0)


def test_layouts_that_are_not_array_sections_stay_refused(signed):
    """A broadcast or overlapping view has no contiguous parent to be a section of."""
    broadcast = np.broadcast_to(np.arange(1.0, 4.0), (4, 3))
    assert broadcast.strides[0] == 0
    with pytest.raises(TypeError, match=r"not a Fortran array section"):
        signed.checksum2(broadcast)

    overlapping = np.lib.stride_tricks.as_strided(_base(), shape=(4, 3), strides=(8, 8))
    with pytest.raises(TypeError, match=r"expected ordering|not a Fortran array section"):
        signed.checksum2(overlapping)

    indivisible = np.ndarray((2, 2), dtype=np.float64, buffer=np.arange(8.0), strides=(16, 40))
    with pytest.raises(TypeError, match=r"not a Fortran array section"):
        signed.checksum2(indivisible)


def test_absent_and_mismatched_storage_stay_refused(signed):
    """State and type checks are unchanged by how the storage is handed over."""
    with pytest.raises(ValueError, match=r"unassociated"):
        signed.total1(signed.unassociated_ptr)
    with pytest.raises(TypeError, match=r"dtype"):
        signed.total1(np.arange(4, dtype=np.float32))
    with pytest.raises(TypeError, match=r"dtype|rank"):
        signed.total1(_matrix())
    with pytest.raises(TypeError, match=r"byte order"):
        signed.total1(_base().astype(">f8"))
    # word_width declares character(len=*), which takes whatever width it is
    # given, so a different width is not a mismatch for it.
    assert signed.word_width(np.array([b"abcdef"], dtype="S6")) == np.int32(6)
