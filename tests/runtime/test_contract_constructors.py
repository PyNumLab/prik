"""Runtime constructors exposed by concrete x2py contract annotations."""

import numpy as np
import pytest

import x2py.contracts as contracts
from x2py.runtime.handles import (
    AllocatableArray,
    PointerArray,
    _bind_contract_native_array_handle,
    _native_array_descriptor_argument_for_binding,
    _native_array_descriptor_handoff_for_binding,
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


@pytest.mark.parametrize(
    ("contract", "scalar_type"),
    [
        (contracts.Bool, np.bool_),
        (contracts.Int8, np.int8),
        (contracts.Int16, np.int16),
        (contracts.Int32, np.int32),
        (contracts.Int64, np.int64),
        (contracts.UInt8, np.uint8),
        (contracts.UInt16, np.uint16),
        (contracts.UInt32, np.uint32),
        (contracts.UInt64, np.uint64),
        (contracts.Float16, np.float16),
        (contracts.Float32, np.float32),
        (contracts.Float64, np.float64),
        (contracts.Float128, np.longdouble),
        (contracts.Complex64, np.complex64),
        (contracts.Complex128, np.complex128),
        (contracts.Complex256, np.clongdouble),
        (contracts.SizeT, np.uintp),
    ],
)
def test_concrete_primitive_default_constructors_return_zero_numpy_scalars(contract, scalar_type):
    value = contract()

    assert isinstance(value, scalar_type)
    assert value == scalar_type(0)


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


def test_fresh_contract_handle_supplies_present_empty_read_only_descriptor_facts():
    handle = contracts.Allocatable[contracts.Float64[:]]()

    assert _native_array_descriptor_argument_for_binding(
        handle,
        descriptor_kind="allocatable",
        expected_dtype=np.float64,
        expected_rank=1,
    ) == (0, 8, 1, 0, 0, 8)


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


def test_non_array_descriptor_and_ordinary_array_annotations_are_not_factories():
    with pytest.raises(TypeError, match="scalar allocatable contracts"):
        contracts.Allocatable[contracts.Float64]()
    with pytest.raises(TypeError, match="ordinary array contract annotations"):
        contracts.Float64[:]()
    with pytest.raises(TypeError, match="element contract 'String'"):
        contracts.Pointer[contracts.String[:]]()
    with pytest.raises(TypeError, match="positive array rank"):
        contracts.Allocatable[contracts.Float64[()]]()
    with pytest.raises(TypeError, match="positive array rank"):
        contracts.Pointer[contracts.Float64[...]]()
    with pytest.raises(TypeError, match="explicit native length and encoding"):
        contracts.String()
    with pytest.raises(TypeError, match="default constructor takes no arguments"):
        contracts.Int32(3)
