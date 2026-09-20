"""How a Fortran logical array reaches Python, and at what width.

A logical has no fixed representation in Fortran, and some compilers default to
one their own C compiler cannot read. prik requests the option that selects the
interoperable form, so `.true.` is the same byte everywhere and a one-byte
logical is exactly what `numpy.bool_` describes. Kinds wider than a byte have no
NumPy Boolean to be, so they report the integer of matching width instead.
"""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_text_and_import

pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

LOGICAL_VIEW_SOURCE = (NATIVE_FIXTURES / "flogical_view_f90.f90").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def logical_view(tmp_path_factory):
    module = _build_text_and_import(
        LOGICAL_VIEW_SOURCE,
        "flogical_view_f90.f90",
        tmp_path_factory.mktemp("logical_view"),
        {
            "bind_c_flogical_view_f90_wrapper.f90",
            "flogical_view_f90_wrapper.c",
            "flogical_view_f90_wrapper.h",
        },
    )
    module.setup()
    return module


def test_a_one_byte_logical_is_a_numpy_boolean(logical_view):
    """`logical(c_bool)` holds zero or one in one byte, which is `numpy.bool_`."""
    assert logical_view.narrow.dtype == np.dtype(np.bool_)
    assert logical_view.narrow_alloc.to_numpy().dtype == np.dtype(np.bool_)
    assert logical_view.narrow.tolist() == [True, False, True, False]


def test_a_wider_logical_reports_the_width_its_elements_occupy(logical_view):
    """NumPy has no Boolean larger than a byte, so the width is stated instead."""
    wide = logical_view.wide

    assert wide.dtype == np.dtype(np.int32)
    assert wide.astype(bool).tolist() == [True, False, True, False]
    assert logical_view.wide_alloc.to_numpy().dtype == np.dtype(np.int32)


def test_logical_allocatable_handles_reach_matching_ordinary_dummies(logical_view):
    assert logical_view.count_narrow_actual(logical_view.narrow_alloc) == np.int32(2)
    assert logical_view.count_wide_actual(logical_view.wide_alloc) == np.int32(2)


def test_wide_logical_pointer_handles_reach_matching_ordinary_dummies(logical_view):
    assert logical_view.wide_pointer.dtype == np.dtype(np.int32)
    assert logical_view.wide_pointer.shape == (4,)
    assert logical_view.count_wide_actual(logical_view.wide_pointer) == np.int32(2)


def test_a_held_view_keeps_agreeing_with_fortran_across_native_writes(logical_view):
    """The view aliases the storage, and both sides read the same bytes.

    The interoperable representation is what makes this hold on every compiler:
    without it one of them writes all bits set for `.true.`, which C and NumPy
    would read as true where Fortran's own complement of it means false.
    """
    narrow, wide = logical_view.narrow, logical_view.wide
    try:
        logical_view.negate()

        assert narrow.tolist() == [False, True, False, True]
        assert int(narrow.sum()) == logical_view.count_narrow()
        assert wide.astype(bool).tolist() == [False, True, False, True]
        assert int(wide.astype(bool).sum()) == logical_view.count_wide()
    finally:
        logical_view.negate()


def test_reading_a_logical_view_does_not_disturb_native_storage(logical_view):
    """Reading is a borrow: nothing is rewritten on the way out."""
    before = logical_view.count_narrow()

    for _ in range(3):
        logical_view.narrow  # noqa: B018 - the read itself is what is under test

    assert logical_view.count_narrow() == before
