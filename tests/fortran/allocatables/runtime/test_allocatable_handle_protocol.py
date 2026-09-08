"""Allocatable handle state, live-view, and operation protocol."""

import numpy as np
import pytest
from prik.runtime.handles import (
    AllocatableArray,
    NativeArrayHandleBase,
)
from tests.fortran._support.native_array_handles import (
    _ArrayState,
    _common_ops,
    _handle_dispatch,
)


def test_allocatable_handle_uses_common_metadata_shape_owner_and_numpy_dispatch():
    owner = object()
    state = _ArrayState(shape=(2, 3), value=np.zeros((2, 3), dtype=np.float64))
    ops = {
        **_common_ops(state),
        "allocated": lambda _handle: state.shape is not None,
        "deallocate": lambda _handle: setattr(state, "shape", None),
        "resize": lambda _handle, shape: setattr(state, "shape", shape),
    }

    handle = AllocatableArray(
        dtype="float64",
        rank=2,
        **_handle_dispatch(ops),
        owner=owner,
        descriptor_ownership="borrowed",
        generation=7,
    )

    assert isinstance(handle, NativeArrayHandleBase)
    assert handle.descriptor_kind == "allocatable"
    assert isinstance(handle.dtype, np.dtype)
    assert handle.dtype == np.dtype("float64")
    assert handle.rank == 2
    assert handle.shape == (2, 3)
    assert handle.to_numpy() is state.value
    assert handle.owner is owner
    assert handle.borrowed is True
    assert handle.owned is False
    assert handle.to_numpy_policy == "borrowed_view"
    assert handle.generation == 7
    assert handle.allocated is True


def test_allocatable_extraction_reports_unallocated_state_as_no_view():
    """Absence is reported by the extraction, not asked about beforehand.

    The generated extraction reads the descriptor, which is where whether the
    storage exists is recorded, so nothing has to test allocation first.
    """
    handle = AllocatableArray(
        dtype="float64",
        rank=1,
        **_handle_dispatch(
            {
                "shape": lambda _handle: None,
                "to_numpy": lambda _handle: None,
                "allocated": lambda _handle: pytest.fail("extraction must not need the allocation state"),
            }
        ),
    )

    assert handle.to_numpy() is None


def test_allocatable_handle_reports_absent_state_and_routes_resize_deallocate():
    state = _ArrayState()
    ops = {
        **_common_ops(state),
        "allocated": lambda _handle: state.shape is not None,
        "deallocate": lambda _handle: setattr(state, "shape", None),
        "resize": lambda _handle, shape: setattr(state, "shape", shape),
    }
    handle = AllocatableArray(dtype="float64", rank=1, **_handle_dispatch(ops))

    assert handle.allocated is False
    assert handle.shape is None
    assert handle.to_numpy() is None

    handle.resize(4)
    assert handle.allocated is True
    assert handle.shape == (4,)

    handle.deallocate()
    assert handle.allocated is False
    assert handle.shape is None


def test_allocatable_to_numpy_policy_returns_mutable_borrowed_view():
    source = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    state = _ArrayState(shape=source.shape, value=source)
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        **_handle_dispatch(
            {
                **_common_ops(state),
                "allocated": lambda _handle: True,
                "deallocate": lambda _handle: None,
                "resize": lambda _handle, _shape: None,
            }
        ),
        to_numpy_policy="borrowed_view",
    )

    view = handle.to_numpy()

    assert view is source
    assert view.flags.writeable is True
    view[1] = 8.0
    assert source[1] == 8.0


def test_allocatable_to_numpy_explicit_copy_is_independent():
    source = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    state = _ArrayState(shape=source.shape, value=source)
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        **_handle_dispatch(
            {
                **_common_ops(state),
                "allocated": lambda _handle: True,
                "deallocate": lambda _handle: None,
                "resize": lambda _handle, _shape: None,
            }
        ),
        to_numpy_policy="descriptor_view",
    )

    view = handle.to_numpy()
    independent = view.copy()

    assert np.shares_memory(view, source) is True
    assert np.shares_memory(independent, source) is False
    source[0] = 99.0
    assert view[0] == 99.0
    assert independent[0] == 1.0


def test_allocatable_handle_requires_generated_allocated_operation():
    with pytest.raises(ValueError, match="requires generated operation 'allocated'"):
        AllocatableArray(
            dtype="float64",
            rank=1,
            **_handle_dispatch(
                {
                    "shape": lambda _handle: (1,),
                    "to_numpy": lambda _handle: None,
                }
            ),
        )


def test_allocatable_operations_are_gated_by_completed_capabilities():
    handle = AllocatableArray(
        dtype="float64",
        rank=1,
        **_handle_dispatch(
            {
                "shape": lambda _handle: None,
                "allocated": lambda _handle: False,
            }
        ),
        to_numpy_policy="unsupported",
    )

    with pytest.raises(NotImplementedError, match="operation 'deallocate' is not available"):
        handle.deallocate()
    with pytest.raises(NotImplementedError, match="operation 'resize' is not available"):
        handle.resize(2)


def test_close_is_a_noop_for_a_borrowed_allocatable_handle():
    owner = object()
    handle = AllocatableArray(
        dtype="float64",
        rank=1,
        **_handle_dispatch(
            {
                "shape": lambda _handle: None,
                "allocated": lambda _handle: False,
            }
        ),
        owner=owner,
        descriptor_ownership="borrowed",
        to_numpy_policy="unsupported",
    )

    assert handle.close() is None
    assert handle.closed is False
    assert handle.owner is owner
    assert handle.allocated is False


def test_deferred_length_character_allocation_requires_an_element_length():
    """The width is asked for exactly where the entity cannot supply one.

    A handle with no static dtype reads its width from the descriptor, which is
    the same condition under which the standard refuses to allocate from a
    shape alone. Passing a width anywhere else would be a second, conflicting
    source for a width the entity already has.
    """
    calls: list[tuple[str, tuple]] = []

    def invoke(name, args):
        calls.append((name, args))
        return 6 if name == "element_length" else None

    deferred = AllocatableArray(
        invoke=invoke,
        capabilities=("allocated", "deallocate", "element_length", "resize", "shape", "to_numpy"),
        dtype=None,
        rank=1,
        to_numpy_policy="descriptor_view",
        element_length_argument=True,
    )

    deferred.resize(3, element_length=4)
    assert calls[-1][0] == "resize"
    assert [int(value) for value in calls[-1][1]] == [3, 4]

    with pytest.raises(TypeError, match="needs an element_length"):
        deferred.resize(3)

    with pytest.raises(ValueError, match="must not be negative"):
        deferred.resize(3, element_length=-1)

    with pytest.raises(TypeError, match="must be an integer"):
        deferred.resize(3, element_length=1.5)


def test_a_fixed_width_handle_refuses_an_element_length():
    """A handle that knows its width will not take a second one."""
    fixed = AllocatableArray(
        invoke=lambda name, args: None,
        capabilities=("allocated", "resize", "shape", "to_numpy"),
        dtype="S8",
        rank=1,
        to_numpy_policy="descriptor_view",
    )

    with pytest.raises(TypeError, match="fixed element width"):
        fixed.resize(4, element_length=8)
