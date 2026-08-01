"""Runtime constructors exposed by concrete prik contract annotations."""

import numpy as np
import pytest

import prik.contracts as contracts
from prik.runtime.handles import (
    AllocatableArray,
    _bind_contract_native_array_handle,
    _native_array_descriptor_argument_for_binding,
    _native_array_descriptor_handoff_for_binding,
)


def test_fresh_contract_handle_supplies_present_empty_read_only_descriptor_facts():
    handle = contracts.Allocatable[contracts.Float64[:]]()

    assert _native_array_descriptor_argument_for_binding(
        handle,
        descriptor_kind="allocatable",
        expected_dtype=np.float64,
        expected_rank=1,
    ) == (0, 8, 1, 0, 0, 8)


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
                ops={
                    "shape": lambda _handle: None,
                    "array_actual": lambda _handle: None,
                    "descriptor": lambda _handle: None,
                    "allocated": lambda _handle: False,
                },
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
        _bind_contract_native_array_handle(
            handle,
            "allocatable",
            dtype,
            rank,
            {},
            object(),
            "owned",
            "unsupported",
        )


def test_writable_contract_handle_adopts_generated_storage_and_closes_once():
    handle = contracts.Allocatable[contracts.Float64[:]]()
    calls = []
    owner = object()

    def bind_default(value):
        _bind_contract_native_array_handle(
            value,
            "allocatable",
            "float64",
            1,
            {
                "shape": lambda received_owner: calls.append(("shape", received_owner)) or None,
                "array_actual": lambda received_owner: 0x5678,
                "descriptor": lambda received_owner: received_owner,
                "allocated": lambda received_owner: False,
                "destroy": lambda received_owner: calls.append(("destroy", received_owner)),
            },
            owner,
            "owned",
            "unsupported",
        )

    assert _native_array_descriptor_handoff_for_binding(
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
        _bind_contract_native_array_handle(
            handle,
            "allocatable",
            "float64",
            1,
            {},
            object(),
            "owned",
            "unsupported",
        )
