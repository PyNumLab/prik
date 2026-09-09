"""Descriptor handoff and view construction through the runtime ABI."""

import numpy as np
import pytest

import prik.contracts as contracts
from prik.runtime.handles import (
    AllocatableArray,
    PointerArray,
    _bind_contract_native_array_handle,
    _native_array_backend_for_binding,
    _native_array_backend_for_binding_positional,
    _numpy_view_from_descriptor_facts,
)
from tests.fortran._support.native_array_handles import (
    _descriptor_facts_for_array,
    _generated_handle_dispatch,
    _handle_dispatch,
)


def _bound_pointer(backend, *, dtype=np.float64, rank=1):
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
            }
        ),
        to_numpy_policy="unsupported",
    )
    handle._native_backend = backend
    return handle


def test_descriptor_argument_hands_over_the_backend_the_handle_publishes():
    """The backend is what crosses; nothing rebuilds a descriptor in Python."""
    backend = object()
    handle = _bound_pointer(backend)

    assert _native_array_backend_for_binding(
        handle,
        descriptor_kind="pointer",
        expected_dtype=np.float64,
        expected_rank=1,
    ) == (backend,)
    assert _native_array_backend_for_binding(
        None,
        descriptor_kind="pointer",
        optional_absent=True,
    ) == (None, None)


def test_an_optional_descriptor_argument_reports_presence_alongside_its_backend():
    backend = object()
    supplied, presence = _native_array_backend_for_binding(
        _bound_pointer(backend),
        descriptor_kind="pointer",
        expected_dtype=np.float64,
        expected_rank=1,
        optional_absent=True,
    )

    assert supplied is backend
    assert isinstance(presence, int)
    assert presence > 0


@pytest.mark.parametrize(
    ("value", "error", "message"),
    [
        (np.zeros(2, dtype=np.float64), TypeError, "expected pointer native array handle"),
        (None, TypeError, "handle argument is required"),
        (
            AllocatableArray(
                dtype=np.dtype(np.float64),
                rank=1,
                **_handle_dispatch({"shape": lambda _handle: None, "allocated": lambda _handle: False}),
                to_numpy_policy="unsupported",
            ),
            TypeError,
            "expected pointer native array handle",
        ),
    ],
)
def test_descriptor_argument_rejects_values_that_are_not_the_declared_handle(value, error, message: str):
    with pytest.raises(error, match=message):
        _native_array_backend_for_binding(value, descriptor_kind="pointer")


def test_descriptor_argument_rejects_a_mismatched_dtype_or_rank():
    handle = _bound_pointer(object())

    with pytest.raises(ValueError, match="does not match expected rank 2"):
        _native_array_backend_for_binding(handle, descriptor_kind="pointer", expected_rank=2)
    with pytest.raises(TypeError, match="does not match expected dtype"):
        _native_array_backend_for_binding(handle, descriptor_kind="pointer", expected_dtype=np.int32)


def test_descriptor_argument_refuses_a_handle_that_has_no_storage_yet():
    """A fresh contract handle publishes no backend until a binder attaches one."""
    handle = contracts.Pointer[contracts.Float64[:]]()

    with pytest.raises(TypeError, match="requires generated persistent descriptor storage"):
        _native_array_backend_for_binding(handle, descriptor_kind="pointer")


def test_descriptor_argument_binds_a_fresh_contract_handle_then_reads_its_backend():
    handle = contracts.Pointer[contracts.Float64[:]]()
    backend = object()

    def bind_default(value):
        operations = {
            "shape": lambda _owner: None,
            "associated": lambda _owner: False,
            "nullify": lambda _owner: None,
            "descriptor": lambda _owner: None,
            "associate": lambda _owner, _facts: None,
            "destroy": lambda _owner: None,
        }
        _bind_contract_native_array_handle(
            value,
            "pointer",
            "float64",
            1,
            _generated_handle_dispatch(operations),
            operations,
            backend,
            "owned",
            "unsupported",
            native_backend=backend,
        )

    assert _native_array_backend_for_binding_positional(
        handle,
        "pointer",
        np.float64,
        1,
        False,
        bind_default,
    ) == (backend,)


def test_view_from_facts_preserves_a_strided_target():
    source = np.arange(8, dtype=np.float64)
    strided = source[::2]

    view = _numpy_view_from_descriptor_facts(_descriptor_facts_for_array(strided), np.float64)

    assert view.shape == (4,)
    assert view.strides == (16,)
    np.testing.assert_allclose(view, strided)
    view[1] = np.float64(99.0)
    assert source[2] == np.float64(99.0)


def test_view_from_facts_preserves_a_negative_stride_target():
    """A reversed target keeps its data pointer, strides and accessible span."""
    source = np.arange(6, dtype=np.float64)
    reversed_view = source[::-1]

    view = _numpy_view_from_descriptor_facts(_descriptor_facts_for_array(reversed_view), np.float64)

    assert view.shape == (6,)
    assert view.strides == (-8,)
    np.testing.assert_allclose(view, source[::-1])
    view[0] = np.float64(42.0)
    assert source[5] == np.float64(42.0)


def test_view_from_facts_reports_absent_storage_and_a_disagreeing_element_width():
    assert _numpy_view_from_descriptor_facts((0, 8, 1, 0, 0, 8), np.float64) is None

    with pytest.raises(ValueError, match="does not match NumPy dtype itemsize"):
        _numpy_view_from_descriptor_facts((1024, 4, 1, 1, 2, 4), np.float64)
