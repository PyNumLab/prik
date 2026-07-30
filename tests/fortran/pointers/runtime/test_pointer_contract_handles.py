"""Pointer contract constructors and native-storage attachment."""

import numpy as np
import pytest

import x2py.contracts as contracts
from x2py.runtime.handles import (
    AllocatableArray,
    PointerArray,
    _bind_contract_native_array_handle,
    _native_array_actual_for_binding,
)


def _pointer_descriptor(value):
    return {
        "base_addr": int(value.ctypes.data),
        "elem_len": int(value.dtype.itemsize),
        "rank": value.ndim,
        "dim": [
            {
                "lower_bound": 1,
                "extent": int(extent),
                "sm": int(stride),
            }
            for extent, stride in zip(value.shape, value.strides, strict=True)
        ],
    }


def test_contract_default_handle_constructors_preserve_dtype_rank_and_empty_state():
    allocatable = contracts.Allocatable[contracts.Float64[:]]()
    pointer = contracts.Pointer[contracts.Int32[:, :]]()

    assert isinstance(allocatable, AllocatableArray)
    assert allocatable.dtype == np.dtype(np.float64)
    assert allocatable.rank == 1
    assert allocatable.owned is True
    assert allocatable.allocated is False
    assert allocatable.shape is None
    assert allocatable.to_numpy() is None

    assert isinstance(pointer, PointerArray)
    assert pointer.dtype == np.dtype(np.int32)
    assert pointer.rank == 2
    assert pointer.owned is True
    assert pointer.associated is False
    assert pointer.shape is None
    assert pointer.to_numpy() is None


def test_fresh_pointer_associate_copies_association_without_following_source_descriptor():
    value = np.arange(6, dtype=np.float64)[::2]
    source_state = {"descriptor": _pointer_descriptor(value)}

    def source_nullify(_handle):
        source_state["descriptor"] = {
            "base_addr": 0,
            "elem_len": 8,
            "rank": 1,
            "dim": [{"lower_bound": 0, "extent": 0, "sm": 8}],
        }

    source = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            "shape": lambda _handle: value.shape,
            "array_actual": lambda _handle: int(value.ctypes.data),
            "descriptor": lambda _handle: source_state["descriptor"],
            "to_numpy": lambda _handle: source_state["descriptor"],
            "associated": lambda _handle: source_state["descriptor"]["base_addr"] != 0,
            "associate": lambda _handle, descriptor: source_state.update(descriptor=descriptor),
            "nullify": source_nullify,
        },
        to_numpy_policy="descriptor_view",
    )
    target = contracts.Pointer[contracts.Float64[:]]()

    target.associate(source)
    assert target.associated is True
    assert target.shape == (3,)
    np.testing.assert_array_equal(target.to_numpy(), value)
    assert _native_array_actual_for_binding(target).address == value.ctypes.data

    source.nullify()
    assert source.associated is False
    assert target.associated is True
    np.testing.assert_array_equal(target.to_numpy(), value)

    target.associate(source)
    assert target.associated is False
    assert target.to_numpy() is None


def test_fresh_pointer_pending_association_is_applied_when_native_storage_attaches():
    value = np.arange(4, dtype=np.float64)
    descriptor = _pointer_descriptor(value)
    source = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            "shape": lambda _handle: value.shape,
            "array_actual": lambda _handle: int(value.ctypes.data),
            "descriptor": lambda _handle: descriptor,
            "to_numpy": lambda _handle: descriptor,
            "associated": lambda _handle: True,
            "associate": lambda _handle, _descriptor: None,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="descriptor_view",
    )
    target = contracts.Pointer[contracts.Float64[:]]()
    target.associate(source)
    owner = object()
    received = []
    state = {"associated": False}

    def associate(received_owner, facts):
        received.append((received_owner, facts))
        state["associated"] = True

    _bind_contract_native_array_handle(
        target,
        "pointer",
        "float64",
        1,
        {
            "shape": lambda _owner: value.shape if state["associated"] else None,
            "array_actual": lambda _owner: int(value.ctypes.data),
            "descriptor": lambda received_owner: received_owner,
            "associated": lambda _owner: state["associated"],
            "associate": associate,
            "nullify": lambda _owner: state.update(associated=False),
            "destroy": lambda _owner: None,
        },
        owner,
        "owned",
        "unsupported",
    )

    assert target.associated is True
    assert received == [
        (
            owner,
            (
                int(value.ctypes.data),
                8,
                1,
                1,
                4,
                8,
            ),
        )
    ]


@pytest.mark.parametrize(
    ("prepare", "descriptor_kind", "dtype", "rank", "error", "message"),
    [
        (
            lambda: contracts.Allocatable[contracts.Float64[:]](),
            "pointer",
            "float64",
            1,
            TypeError,
            "cannot attach pointer descriptor storage",
        ),
    ],
)
def test_generated_storage_rejects_incompatible_contract_handles(
    prepare,
    descriptor_kind,
    dtype,
    rank,
    error,
    message,
):
    handle = prepare()

    with pytest.raises(error, match=message):
        _bind_contract_native_array_handle(
            handle,
            descriptor_kind,
            dtype,
            rank,
            {},
            object(),
            "owned",
            "unsupported",
        )


def test_pointer_association_rejects_closed_handles():
    target = contracts.Pointer[contracts.Float64[:]]()
    source = contracts.Pointer[contracts.Float64[:]]()
    target.close()

    with pytest.raises(ReferenceError, match="pointer handle is closed"):
        target.associate(source)

    target = contracts.Pointer[contracts.Float64[:]]()
    source.close()
    with pytest.raises(ReferenceError, match="source pointer handle is closed"):
        target.associate(source)


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
