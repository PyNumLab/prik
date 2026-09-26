"""Contract handle constructors and generated-storage attachment checks."""

import numpy as np
import pytest

import prik.contracts as contracts
from prik.runtime.handles import AllocatableArray, _bind_contract_native_array_handle
from tests.fortran._support.native_array_handles import _generated_handle_dispatch, _handle_dispatch


def _closed_allocatable():
    handle = contracts.Allocatable[contracts.Float64[:]]()
    handle.close()
    return handle


@pytest.mark.parametrize(
    ("prepare", "descriptor_kind", "dtype", "rank", "error", "message"),
    [
        pytest.param(
            lambda: contracts.Allocatable[contracts.Float64[:]](),
            "pointer",
            "float64",
            1,
            TypeError,
            "cannot attach pointer descriptor storage",
            id="allocatable-into-pointer-storage",
        ),
        pytest.param(
            lambda: AllocatableArray(
                dtype="float64",
                rank=1,
                **_handle_dispatch({"shape": lambda _handle: None, "allocated": lambda _handle: False}),
                to_numpy_policy="unsupported",
            ),
            "allocatable",
            "float64",
            1,
            TypeError,
            "fresh contract handle",
            id="not-a-contract-handle",
        ),
        pytest.param(
            lambda: contracts.Allocatable[contracts.Float64[:]](),
            "allocatable",
            "float64",
            2,
            ValueError,
            "does not match generated rank 2",
            id="rank",
        ),
        pytest.param(
            lambda: contracts.Allocatable[contracts.Float64[:]](),
            "allocatable",
            "int32",
            1,
            TypeError,
            "does not match generated dtype",
            id="dtype",
        ),
        pytest.param(_closed_allocatable, "allocatable", "float64", 1, ReferenceError, "handle is closed", id="closed"),
    ],
)
def test_generated_storage_rejects_incompatible_contract_handles(prepare, descriptor_kind, dtype, rank, error, message):
    handle = prepare()

    with pytest.raises(error, match=message):
        operations = {}
        _bind_contract_native_array_handle(
            handle,
            descriptor_kind,
            dtype,
            rank,
            _generated_handle_dispatch(operations),
            operations,
            object(),
            "owned",
            "unsupported",
        )


def test_non_array_descriptor_and_ordinary_array_annotations_are_not_factories():
    with pytest.raises(TypeError, match="scalar allocatable contracts"):
        contracts.Allocatable[contracts.Float64]()
    with pytest.raises(TypeError, match="element contract 'String'"):
        contracts.Pointer[contracts.String[:]]()
    with pytest.raises(TypeError, match="positive array rank"):
        contracts.Allocatable[contracts.Float64[()]]()
    with pytest.raises(TypeError, match="positive array rank"):
        contracts.Pointer[contracts.Float64[...]]()
    with pytest.raises(TypeError, match="explicit native length and encoding"):
        contracts.String()


def test_character_array_contracts_create_fixed_and_deferred_handle_types():
    fixed = contracts.Pointer[contracts.String[4][:, :]]()
    deferred_pointer = contracts.Pointer[contracts.String[:][:]]()
    deferred_allocatable = contracts.Allocatable[contracts.String[:][:]]()

    assert fixed.dtype == np.dtype("S4")
    assert fixed.rank == 2
    assert deferred_pointer.dtype == np.dtype("S0")
    assert deferred_pointer.to_numpy_policy == "unsupported"
    assert deferred_allocatable.dtype == np.dtype("S0")

    for width in (True, 0, -1):
        with pytest.raises(TypeError, match="positive integer width or ':'"):
            contracts.Pointer[contracts.String[width][:]]()
