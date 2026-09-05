"""Every storage form a module array can take, exercised through one module.

The forms differ in what the declaration already fixes and what only exists at
runtime, and prik reaches them by three different mechanisms because of that.
This module holds them side by side so the differences are visible in one place:
what each is exposed as, whether it stays live, and what happens when it is
handed back to an ordinary Fortran array dummy.
"""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_and_import

FIXTURES = Path(__file__).parent / "fixtures"
ARRAY_FORMS_F90_SOURCE = FIXTURES / "native" / "fmodule_array_forms_f90.f90"
pytestmark = pytest.mark.fortran_end_to_end


@pytest.fixture(scope="module")
def array_forms(tmp_path_factory):
    module = _build_and_import(
        ARRAY_FORMS_F90_SOURCE,
        tmp_path_factory.mktemp("array_forms"),
        {
            "bind_c_fmodule_array_forms_f90_wrapper.f90",
            "fmodule_array_forms_f90_wrapper.c",
            "fmodule_array_forms_f90_wrapper.h",
        },
    )
    module.setup()
    return module


# A fixed shape is entirely in the declaration, so these are plain views; an
# allocatable or pointer carries runtime state, so those are handles.
@pytest.mark.parametrize(
    ("name", "exposed_as", "dtype"),
    [
        ("fixed_plain", np.ndarray, "float64"),
        ("fixed_target", np.ndarray, "float64"),
        ("fixed_matrix", np.ndarray, "float64"),
        ("fixed_shifted", np.ndarray, "float64"),
        ("fixed_counts", np.ndarray, "int32"),
        ("fixed_flags", np.ndarray, "bool"),
        ("char_fixed", np.ndarray, "S5"),
        ("char_target", np.ndarray, "S5"),
    ],
)
def test_fixed_shape_module_arrays_are_plain_views(array_forms, name, exposed_as, dtype):
    """A declared shape needs no handle: the value is the storage itself."""
    value = getattr(array_forms, name)

    assert isinstance(value, exposed_as)
    assert value.dtype == np.dtype(dtype)


@pytest.mark.parametrize(
    ("name", "dtype"),
    [
        ("alloc_plain", "float64"),
        ("alloc_target", "float64"),
        ("alloc_matrix", "float64"),
        ("alloc_shifted", "float64"),
        ("char_alloc", "S5"),
        ("char_deferred", "S6"),
    ],
)
def test_allocatable_module_arrays_are_handles(array_forms, name, dtype):
    """Allocation state is not in the declaration, so these carry it explicitly."""
    handle = getattr(array_forms, name)

    assert handle.allocated is True
    assert handle.to_numpy().dtype == np.dtype(dtype)


def test_a_bare_pointer_is_a_handle_that_declines_to_hand_out_a_view(array_forms):
    """A pointer says what it is associated with, not that a view is safe.

    Contiguity and target lifetime are not in a plain `pointer` declaration, so
    no view can be justified from it alone; that needs an explicit
    `PointerPolicy`. The association state is knowable and is reported.
    """
    handle = array_forms.ptr_link

    assert handle.associated is True
    assert handle.shape == (3,)
    with pytest.raises(NotImplementedError, match="unsupported by completed policy"):
        handle.to_numpy()


def test_derived_array_fields_are_views_through_either_owner(array_forms):
    """An array component is reached through its owner, addressable or not."""
    assert isinstance(array_forms.obj_plain.grid, np.ndarray)
    assert isinstance(array_forms.obj_target.grid, np.ndarray)
    assert array_forms.obj_plain.grid.shape == (2, 3)


@pytest.mark.parametrize(
    "name",
    ["fixed_plain", "fixed_target", "fixed_shifted", "obj_plain", "obj_target"],
)
def test_views_stay_live_across_native_writes(array_forms, name):
    """Every borrowed view names the storage native code writes, not a copy."""

    def current():
        owner = getattr(array_forms, name)
        return owner.grid if name.startswith("obj") else owner

    view = current()
    before = float(view.flat[0])
    try:
        view.flat[0] = before + 1.0
        assert float(current().flat[0]) == before + 1.0
    finally:
        # The storage is shared with every other test in this module, so the
        # write is undone rather than left for whatever runs next.
        view.flat[0] = before


def test_every_numeric_form_reaches_one_ordinary_array_dummy(array_forms):
    """`total(values(:))` accepts each form, however its storage is reached.

    A fixed array arrives as a view, an allocatable and a pointer as handles,
    and a derived component through its owner. The dummy is an ordinary array
    either way, so the conversion has to erase the difference.
    """
    assert array_forms.total(array_forms.fixed_plain) == np.float64(10.0)
    assert array_forms.total(array_forms.fixed_target) == np.float64(26.0)
    assert array_forms.total(array_forms.fixed_shifted) == np.float64(42.0)
    assert array_forms.total(array_forms.alloc_plain) == np.float64(10.0)
    assert array_forms.total(array_forms.alloc_target) == np.float64(24.0)
    assert array_forms.total_2d(array_forms.fixed_matrix) == np.float64(21.0)
    assert array_forms.total_2d(array_forms.alloc_matrix) == np.float64(12.0)
    assert array_forms.total_2d(array_forms.obj_plain.grid) == np.float64(6.0)
    assert array_forms.total_counts(array_forms.fixed_counts) == np.int32(24)
    assert array_forms.count_set(array_forms.fixed_flags) == np.int32(2)
    assert array_forms.fixed_flags.tolist() == [True, False, True]
    assert array_forms.first_word(array_forms.char_fixed) == "alpha"


def test_only_an_allocatable_dummy_carries_the_declared_lower_bound(array_forms):
    """The two dummy forms disagree about bounds, and both are right.

    An ordinary array dummy declares its own bounds, so a declared lower bound
    is discarded by the language and cannot be observed. An allocatable dummy is
    the actual's descriptor, so it adopts them -- which is why a module
    allocatable has to report the bounds it really has.
    """
    assert array_forms.lower_bound_of(array_forms.alloc_shifted) == np.int32(5)
    assert array_forms.lower_bound_of(array_forms.alloc_plain) == np.int32(1)

    # `fixed_shifted` is declared (5:8) and sums the same as any other four
    # elements: nothing downstream can tell where it started.
    assert array_forms.total(array_forms.fixed_shifted) == np.float64(42.0)


def test_a_character_handle_reaches_a_character_dummy_like_any_other(array_forms):
    """A handle stands in for an array actual whatever its element type.

    A character actual is matched on its declared width as well as its kind, so
    a handle whose elements are a different length is refused: it describes
    storage the dummy cannot accept.
    """
    assert array_forms.first_word(array_forms.char_alloc) == "epsil"
    assert array_forms.first_word(array_forms.char_alloc.to_numpy()) == "epsil"
    assert array_forms.first_word(array_forms.char_fixed) == "alpha"

    # `char_deferred` holds six-character elements; the dummy declares five.
    with pytest.raises(TypeError, match="does not match expected dtype"):
        array_forms.first_word(array_forms.char_deferred)
