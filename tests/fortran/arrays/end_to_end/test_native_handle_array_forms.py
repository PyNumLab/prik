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

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


NATIVE_HANDLE_ARRAY_FORMS_SOURCE = (NATIVE_FIXTURES / "fhandle_array_forms_f90.f90").read_text(encoding="utf-8")


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


NATIVE_HANDLE_DESCRIPTOR_MATRIX_SOURCE = (NATIVE_FIXTURES / "fhandle_descriptor_matrix_f90.f90").read_text(
    encoding="utf-8"
)


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
    fixed_words_field = parent.field_fixed_words
    missing_words_field = parent.field_missing_words
    missing_pointer_field = parent.field_missing_pointer
    words_field = parent.field_words

    assert field.shape == (3,)
    np.testing.assert_allclose(field.to_numpy(), np.array([5.0, 5.0, 5.0]))
    assert pointer_field.associated is True
    assert pointer_field.shape == (3,)
    assert logical_field.dtype == np.dtype(np.int32)
    np.testing.assert_array_equal(logical_field.to_numpy().astype(bool), [True, False, True])
    assert fixed_words_field.allocated is True
    assert fixed_words_field.shape == (2,)
    assert fixed_words_field.dtype == np.dtype("S4")
    assert fixed_words_field.to_numpy().tolist() == [b"abcd", b"efgh"]
    assert descriptor_matrix.word_width(fixed_words_field) == np.int32(4)
    assert missing_words_field.allocated is False
    assert missing_words_field.shape is None
    assert missing_words_field.to_numpy() is None
    assert missing_pointer_field.associated is False
    assert missing_pointer_field.shape is None
    missing_pointer_field.associate(missing_pointer_field)
    assert missing_pointer_field.associated is False
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
