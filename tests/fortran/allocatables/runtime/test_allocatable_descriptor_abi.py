"""Allocatable descriptor handoff through the runtime ABI."""

from tests.fortran._support.native_array_handles import (
    AllocatableArray,
    _handoff,
    np,
    pytest,
)


def test_allocatable_descriptor_hook_accepts_unallocated_descriptor_without_numpy_conversion():
    descriptor = _handoff(234)
    calls = []
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "shape": lambda _handle: None,
            "allocated": lambda _handle: False,
            "to_numpy": lambda _handle: pytest.fail("descriptor handoff must not call to_numpy"),
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "descriptor": lambda _handle: calls.append("descriptor") or descriptor,
        },
        to_numpy_policy="unsupported",
    )

    assert handle._descriptor_for_binding(expected_dtype="float64", expected_rank=1) == {
        "base_addr": descriptor.address,
        "elem_len": 8,
        "rank": 1,
        "dim": [{"lower_bound": 0, "extent": 0, "sm": 8}],
    }
    assert calls == ["descriptor"]
