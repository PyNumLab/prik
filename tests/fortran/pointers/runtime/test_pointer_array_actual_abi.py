"""Pointer array-actual handoff behavior."""

import numpy as np
import pytest
from prik.runtime.handles import (
    PointerArray,
    _native_array_actual_argument_for_binding_positional,
)
from tests.fortran._support.native_array_handles import (
    _ArrayState,
    _handoff,
)


def test_array_actual_argument_abi_packer_uses_pointer_native_array_actual_dtype_metadata():
    actual = _handoff(248)
    handle = PointerArray(
        dtype=np.dtype(np.float32),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(249),
            "shape": lambda _handle: (3,),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
            "array_actual": lambda _handle: actual,
        },
        to_numpy_policy="unsupported",
    )

    assert _native_array_actual_argument_for_binding_positional(
        handle,
        None,
        1,
        (3,),
        None,
        False,
        False,
        False,
        False,
        True,
        False,
    ) == (actual.address, np.dtype(np.float32).itemsize, 3)


def test_pointer_array_actual_hook_requires_associated_state_without_to_numpy():
    actual = _handoff(242)
    calls = []
    state = _ArrayState()
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(243),
            "shape": lambda _handle: state.shape,
            "associated": lambda _handle: state.shape is not None,
            "nullify": lambda _handle: setattr(state, "shape", None),
            "to_numpy": lambda _handle: pytest.fail("array-actual handoff must not call to_numpy"),
            "array_actual": lambda _handle: calls.append("array_actual") or actual,
        },
    )

    with pytest.raises(ValueError, match="unassociated"):
        handle._array_actual_for_binding(expected_dtype=np.float64, expected_rank=1)

    state.shape = (3,)

    assert handle._array_actual_for_binding(expected_dtype="float64", expected_rank=1) is actual
    assert calls == ["array_actual"]
