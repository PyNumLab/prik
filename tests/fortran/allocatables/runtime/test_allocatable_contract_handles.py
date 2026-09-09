"""Runtime constructors exposed by concrete prik contract annotations."""

import numpy as np
import pytest

import prik.contracts as contracts
from prik.runtime.handles import (
    AllocatableArray,
    _bind_contract_native_array_handle,
    _native_array_backend_for_binding,
)
from tests.fortran._support.native_array_handles import _generated_handle_dispatch, _handle_dispatch


def test_fresh_contract_handle_has_no_descriptor_to_hand_over_on_its_own():
    """A handle the caller made owns no descriptor until the wrapper gives it one.

    Nothing rebuilds a descriptor from reported fields any more, so the only
    thing such a handle can supply is storage a generated binder attached to
    it.  Reaching the call without that is a wrapper bug, not a caller error,
    so it is refused rather than papered over with an empty descriptor.
    """
    handle = contracts.Allocatable[contracts.Float64[:]]()

    with pytest.raises(TypeError, match="requires generated persistent descriptor storage"):
        _native_array_backend_for_binding(
            handle,
            descriptor_kind="allocatable",
            expected_dtype=np.float64,
            expected_rank=1,
        )


def test_contract_default_allocatable_constructor_preserves_dtype_rank_and_empty_state():
    handle = contracts.Allocatable[contracts.Float64[:]]()

    assert isinstance(handle, AllocatableArray)
    assert handle.dtype == np.dtype(np.float64)
    assert handle.rank == 1
    assert handle.owned is True
    assert handle.allocated is False
    assert handle.shape is None
    assert handle.to_numpy() is None


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: contracts.Allocatable[contracts.Float64](),
            "scalar allocatable contracts",
        ),
        (
            lambda: contracts.Allocatable[contracts.Float64[()]](),
            "positive array rank",
        ),
    ],
)
def test_non_array_allocatable_annotations_are_not_factories(factory, message: str):
    with pytest.raises(TypeError, match=message):
        factory()


@pytest.mark.parametrize(
    ("prepare", "dtype", "rank", "error", "message"),
    [
        (
            lambda: AllocatableArray(
                dtype="float64",
                rank=1,
                **_handle_dispatch(
                    {
                        "shape": lambda _handle: None,
                        "allocated": lambda _handle: False,
                    }
                ),
                to_numpy_policy="unsupported",
            ),
            "float64",
            1,
            TypeError,
            "fresh contract handle",
        ),
        (
            lambda: contracts.Allocatable[contracts.Float64[:]](),
            "float64",
            2,
            ValueError,
            "does not match generated rank 2",
        ),
        (
            lambda: contracts.Allocatable[contracts.Float64[:]](),
            "int32",
            1,
            TypeError,
            "does not match generated dtype",
        ),
    ],
)
def test_generated_storage_rejects_incompatible_allocatable_contract_handles(
    prepare,
    dtype: str,
    rank: int,
    error: type[Exception],
    message: str,
):
    handle = prepare()

    with pytest.raises(error, match=message):
        operations = {}
        _bind_contract_native_array_handle(
            handle,
            "allocatable",
            dtype,
            rank,
            _generated_handle_dispatch(operations),
            operations,
            object(),
            "owned",
            "unsupported",
        )


def test_writable_contract_handle_adopts_generated_storage_and_closes_once():
    """Binding attaches storage, and the backend over it is what goes to the call.

    An owned handle's backend and its owner are the same capsule: the record
    holds the descriptor the binder allocated, and every later call reads it
    without coming back through Python.
    """
    handle = contracts.Allocatable[contracts.Float64[:]]()
    calls = []
    owner = object()

    def bind_default(value):
        operations = {
            "shape": lambda received_owner: calls.append(("shape", received_owner)) or None,
            "allocated": lambda received_owner: False,
            "destroy": lambda received_owner: calls.append(("destroy", received_owner)),
        }
        _bind_contract_native_array_handle(
            value,
            "allocatable",
            "float64",
            1,
            _generated_handle_dispatch(operations),
            operations,
            owner,
            "owned",
            "unsupported",
            native_backend=owner,
        )

    assert _native_array_backend_for_binding(
        handle,
        descriptor_kind="allocatable",
        expected_dtype=np.float64,
        expected_rank=1,
        bind_default=bind_default,
    ) == (owner,)
    assert handle.owner == owner

    handle.close()
    handle.close()
    assert calls == [("destroy", owner)]


def test_generated_storage_rejects_a_closed_contract_handle():
    handle = contracts.Allocatable[contracts.Float64[:]]()
    handle.close()

    with pytest.raises(ReferenceError, match="handle is closed"):
        operations = {}
        _bind_contract_native_array_handle(
            handle,
            "allocatable",
            "float64",
            1,
            _generated_handle_dispatch(operations),
            operations,
            object(),
            "owned",
            "unsupported",
        )
