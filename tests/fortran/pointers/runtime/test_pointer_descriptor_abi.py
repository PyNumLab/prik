"""Fail-closed checks at the runtime descriptor boundary.

A handle of the wrong kind, dtype, rank, or state must be refused before its
backend reaches native code; the successful handoffs are proved end to end.
"""

import numpy as np
import pytest

import prik.contracts as contracts
from prik.runtime.handles import (
    AllocatableArray,
    PointerArray,
    _native_array_backend_for_binding,
    _numpy_view_from_descriptor_facts,
)
from tests.fortran._support.native_array_handles import _handle_dispatch


def _bound_pointer(*, dtype=np.float64, rank=1):
    """Return a pointer handle standing for storage a wrapper attached."""
    handle = PointerArray(
        dtype=np.dtype(dtype),
        rank=rank,
        **_handle_dispatch(
            {
                "shape": lambda _handle: None,
                "associated": lambda _handle: False,
                "nullify": lambda _handle: None,
                "descriptor": lambda _handle: None,
                "associate": lambda _handle, _facts: None,
            }
        ),
        to_numpy_policy="unsupported",
    )
    handle._native_backend = object()
    return handle


def _unattached_allocatable():
    return AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        **_handle_dispatch({"shape": lambda _handle: None, "allocated": lambda _handle: False}),
        to_numpy_policy="unsupported",
    )


@pytest.mark.parametrize(
    ("value", "kind", "expected", "error", "message"),
    [
        pytest.param(np.zeros(2), "pointer", {}, TypeError, "expected pointer native array handle", id="plain-array"),
        pytest.param(None, "pointer", {}, TypeError, "handle argument is required", id="none"),
        pytest.param(
            _unattached_allocatable(),
            "pointer",
            {},
            TypeError,
            "expected pointer native array handle",
            id="allocatable-for-pointer",
        ),
        pytest.param(
            _bound_pointer(), "pointer", {"expected_rank": 2}, ValueError, "does not match expected rank 2", id="rank"
        ),
        pytest.param(
            _bound_pointer(),
            "pointer",
            {"expected_dtype": np.int32},
            TypeError,
            "does not match expected dtype",
            id="dtype",
        ),
        pytest.param(
            contracts.Pointer[contracts.Float64[:]](),
            "pointer",
            {},
            TypeError,
            "requires generated persistent descriptor storage",
            id="fresh-pointer-without-storage",
        ),
        pytest.param(
            contracts.Allocatable[contracts.Float64[:]](),
            "allocatable",
            {"expected_dtype": np.float64, "expected_rank": 1},
            TypeError,
            "requires generated persistent descriptor storage",
            id="fresh-allocatable-without-storage",
        ),
    ],
)
def test_descriptor_argument_refuses_a_handle_that_is_not_the_declared_one(value, kind, expected, error, message):
    with pytest.raises(error, match=message):
        _native_array_backend_for_binding(value, descriptor_kind=kind, **expected)


def test_view_from_facts_reports_absent_storage_and_a_disagreeing_element_width():
    assert _numpy_view_from_descriptor_facts((0, 8, 1, 0, 0, 8), np.float64) is None

    with pytest.raises(ValueError, match="does not match NumPy dtype itemsize"):
        _numpy_view_from_descriptor_facts((1024, 4, 1, 1, 2, 4), np.float64)


@pytest.mark.parametrize(
    ("other", "error", "message"),
    [
        pytest.param(object(), TypeError, "requires another PointerArray", id="not-a-pointer"),
        pytest.param(_bound_pointer(dtype=np.int32), TypeError, "dtype", id="dtype"),
        pytest.param(_bound_pointer(rank=2), ValueError, "rank", id="rank"),
    ],
)
def test_pointer_associate_rejects_incompatible_sources(other, error, message):
    with pytest.raises(error, match=message):
        _bound_pointer().associate(other)


def test_pointer_association_rejects_closed_and_unattached_character_handles():
    target = contracts.Pointer[contracts.Float64[:]]()
    source = contracts.Pointer[contracts.Float64[:]]()
    target.close()
    with pytest.raises(ReferenceError, match="pointer handle is closed"):
        target.associate(source)

    target = contracts.Pointer[contracts.Float64[:]]()
    source.close()
    with pytest.raises(ReferenceError, match="source pointer handle is closed"):
        target.associate(source)

    # A character pointer cannot record a pending association, so it refuses
    # instead of deferring one until storage is attached.
    with pytest.raises(TypeError, match="target handle to be attached"):
        contracts.Pointer[contracts.String[4][:]]().associate(contracts.Pointer[contracts.String[4][:]]())
