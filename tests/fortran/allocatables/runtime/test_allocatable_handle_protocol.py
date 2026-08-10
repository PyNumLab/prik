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
    _required_handoff_ops,
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
        ops=ops,
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


def test_allocatable_to_numpy_short_circuits_unallocated_state_before_generated_extraction():
    handle = AllocatableArray(
        dtype="float64",
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: None,
            "to_numpy": lambda _handle: pytest.fail("unallocated handles must not call generated extraction"),
            "allocated": lambda _handle: False,
        },
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
    handle = AllocatableArray(dtype="float64", rank=1, ops=ops)

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
        ops={
            **_common_ops(state),
            "allocated": lambda _handle: True,
            "deallocate": lambda _handle: None,
            "resize": lambda _handle, _shape: None,
        },
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
        ops={
            **_common_ops(state),
            "allocated": lambda _handle: True,
            "deallocate": lambda _handle: None,
            "resize": lambda _handle, _shape: None,
        },
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
            ops={
                **_required_handoff_ops(),
                "shape": lambda _handle: (1,),
                "to_numpy": lambda _handle: None,
            },
        )


def test_allocatable_operations_are_gated_by_the_completed_ops_table():
    handle = AllocatableArray(
        dtype="float64",
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: None,
            "allocated": lambda _handle: False,
        },
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
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: None,
            "allocated": lambda _handle: False,
        },
        owner=owner,
        descriptor_ownership="borrowed",
        to_numpy_policy="unsupported",
    )

    assert handle.close() is None
    assert handle.closed is False
    assert handle.owner is owner
    assert handle.allocated is False
