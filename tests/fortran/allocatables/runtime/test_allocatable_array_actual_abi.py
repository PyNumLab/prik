"""Allocatable handle handoff to ordinary native array arguments."""

import numpy as np
import pytest
from prik.runtime.handles import (
    AllocatableArray,
    _native_array_actual_argument_for_binding_positional,
)
from tests.fortran._support.native_array_handles import (
    _ArrayState,
    _handoff,
)


def test_allocatable_array_actual_hook_requires_allocated_state_without_to_numpy():
    actual = _handoff(201)
    calls = []
    state = _ArrayState()
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(202),
            "shape": lambda _handle: state.shape,
            "allocated": lambda _handle: state.shape is not None,
            "to_numpy": lambda _handle: pytest.fail("array-actual handoff must not call to_numpy"),
            "array_actual": lambda _handle: calls.append("array_actual") or actual,
        },
    )

    with pytest.raises(ValueError, match="unallocated"):
        handle._array_actual_for_binding(expected_dtype=np.float64, expected_rank=1)

    state.shape = (4,)

    assert handle._array_actual_for_binding(expected_dtype="float64", expected_rank=1) is actual
    assert calls == ["array_actual"]


def test_array_actual_argument_abi_packer_uses_allocatable_native_array_actual_without_numpy_conversion():
    actual = _handoff(246)
    calls = []
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(247),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "layout": lambda _handle: "F",
            "writeable": lambda _handle: True,
            "native_byte_order": lambda _handle: True,
            "aligned": lambda _handle: True,
            "to_numpy": lambda _handle: pytest.fail("array-actual ABI packing must not call to_numpy"),
            "array_actual": lambda _handle: calls.append("array_actual") or actual,
        },
    )

    assert _native_array_actual_argument_for_binding_positional(
        handle,
        "float64",
        1,
        (2,),
        "F",
        True,
        True,
        True,
        True,
        True,
        True,
    ) == (actual.address, 1, np.dtype(np.float64).itemsize, 2, 1, 1)
    assert calls == ["array_actual"]
