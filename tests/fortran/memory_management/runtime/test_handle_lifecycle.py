"""Runtime ownership, factory, close, and finalizer behavior for native handles."""

import ctypes
import gc
import numpy as np
import pytest
from prik.runtime.handles import (
    AllocatableArray,
    PointerArray,
    _native_array_descriptor_handoff_for_binding,
    _native_array_handle_from_generated_ops,
)
from tests.fortran._support.native_array_handles import (
    _ArrayState,
    _common_ops,
    _required_handoff_ops,
)


def test_generated_handle_factory_adapts_private_operations_to_runtime_protocol():
    owner = object()
    value = np.arange(3, dtype=np.float64)
    calls = []

    def shape():
        calls.append(("shape", ()))
        return (3,)

    def descriptor():
        calls.append(("descriptor", ()))
        return ctypes.c_void_p(1002)

    def allocated():
        calls.append(("allocated", ()))
        return True

    def to_numpy():
        calls.append(("to_numpy", ()))
        return value

    handle = _native_array_handle_from_generated_ops(
        "allocatable",
        "float64",
        1,
        {
            "shape": shape,
            "descriptor": descriptor,
            "allocated": allocated,
            "to_numpy": to_numpy,
        },
        owner=owner,
        descriptor_ownership="borrowed",
        to_numpy_policy="borrowed_view",
        generation=9,
    )

    assert isinstance(handle, AllocatableArray)
    assert isinstance(handle.dtype, np.dtype)
    assert handle.dtype == np.dtype("float64")
    assert handle.owner is owner
    assert handle.generation == 9
    assert handle.shape == (3,)
    assert handle.to_numpy() is value
    assert handle._descriptor_for_binding(expected_dtype="float64", expected_rank=1) == {
        "base_addr": 1002,
        "elem_len": 8,
        "rank": 1,
        "dim": [{"lower_bound": 0, "extent": 3, "sm": 8}],
    }
    assert {name for name, _args in calls} == {"allocated", "shape", "to_numpy", "descriptor"}
    assert all(args == () for _name, args in calls)


def test_generated_handle_factory_splats_shape_operations_to_scalar_extents():
    calls = []
    handle = _native_array_handle_from_generated_ops(
        "allocatable",
        "float64",
        2,
        {
            "shape": lambda: (2, 3),
            "descriptor": lambda: 1002,
            "allocated": lambda: True,
            "resize": lambda *extents: calls.append(("resize", extents)),
        },
        to_numpy_policy="unsupported",
    )

    handle.resize((4, 5))

    assert calls == [("resize", (4, 5))]


def test_generated_owned_handle_factory_passes_persistent_owner_to_every_operation():
    calls = []
    owner = object()
    value = np.arange(3, dtype=np.float64)

    def operation(name, result=None):
        def call(received_owner, *args):
            calls.append((name, received_owner, args))
            return result

        return call

    handle = _native_array_handle_from_generated_ops(
        "allocatable",
        "float64",
        1,
        {
            "shape": operation("shape", (3,)),
            "descriptor": operation("descriptor", owner),
            "allocated": operation("allocated", True),
            "to_numpy": operation("to_numpy", value),
            "resize": operation("resize"),
            "destroy": operation("destroy"),
        },
        owner=owner,
        descriptor_ownership="owned",
    )

    assert handle.shape == (3,)
    assert handle.to_numpy() is value
    assert _native_array_descriptor_handoff_for_binding(
        handle,
        descriptor_kind="allocatable",
        expected_dtype=np.float64,
        expected_rank=1,
    ) == (owner,)
    handle.resize((5,))
    handle.close()

    assert {name for name, _owner, _args in calls} == {
        "allocated",
        "shape",
        "to_numpy",
        "descriptor",
        "resize",
        "destroy",
    }
    assert all(received_owner is owner for _name, received_owner, _args in calls)
    assert ("resize", owner, (np.int64(5),)) in calls
    assert calls.count(("destroy", owner, ())) == 1


def test_generated_owned_handle_normalizes_compiler_zero_extent_descriptor_records():
    owner = 1234
    descriptor = {
        "base_addr": 5678,
        "elem_len": 8,
        "rank": 1,
        "dim": [{"lower_bound": 1, "extent": -1, "sm": 8}],
    }
    handle = _native_array_handle_from_generated_ops(
        "allocatable",
        "float64",
        1,
        {
            "shape": lambda _native_owner: descriptor,
            "descriptor": lambda _native_owner: 5678,
            "to_numpy": lambda _native_owner: descriptor,
            "allocated": lambda _native_owner: True,
            "destroy": lambda _native_owner: None,
        },
        owner=owner,
        descriptor_ownership="owned",
    )

    assert handle.shape == (0,)
    assert handle.to_numpy().shape == (0,)


def test_generated_handle_resolves_deferred_character_dtype_from_runtime_element_length():
    state = {"itemsize": 3}
    handle = _native_array_handle_from_generated_ops(
        "allocatable",
        None,
        1,
        {
            "shape": lambda: (2,),
            "element_length": lambda: state["itemsize"],
            "descriptor": lambda: 0x1234,
            "allocated": lambda: True,
            "to_numpy": lambda: np.array([b"red", b"sky"], dtype=f"S{state['itemsize']}"),
        },
    )

    assert handle.dtype == np.dtype("S3")
    state["itemsize"] = 5
    assert handle.dtype == np.dtype("S5")


def test_generated_owned_handle_factory_releases_owner_once_when_construction_fails():
    calls = []
    owner = 0x1234

    def destroy(received_owner):
        calls.append(("destroy", received_owner))

    with pytest.raises(ValueError, match="requires generated operation 'descriptor'"):
        _native_array_handle_from_generated_ops(
            "allocatable",
            "float64",
            1,
            {
                "shape": lambda _owner: (1,),
                "allocated": lambda _owner: True,
                "destroy": destroy,
            },
            owner=owner,
            descriptor_ownership="owned",
            to_numpy_policy="unsupported",
        )

    gc.collect()
    assert calls == [("destroy", owner)]


def test_generated_handle_factory_rejects_invalid_descriptor_kind_and_descriptor_result():
    ops = {
        "shape": lambda: (1,),
        "descriptor": lambda: object(),
        "allocated": lambda: True,
        "to_numpy": lambda: np.zeros(1, dtype=np.float64),
    }

    with pytest.raises(ValueError, match="generated native array handle kind"):
        _native_array_handle_from_generated_ops("target", "float64", 1, ops)

    handle = _native_array_handle_from_generated_ops("allocatable", "float64", 1, ops)
    with pytest.raises(TypeError, match="descriptor operation must return descriptor fields or an integer"):
        handle._descriptor_for_binding(expected_dtype="float64", expected_rank=1)


def test_owned_handle_close_calls_destroy_once_and_blocks_later_use():
    calls = []
    state = _ArrayState(shape=(2,), value=np.zeros(2, dtype=np.float64))
    handle = AllocatableArray(
        dtype="float64",
        rank=1,
        ops={
            **_common_ops(state),
            "allocated": lambda _handle: True,
            "destroy": lambda _handle: calls.append(("destroy", _handle.shape, _handle.to_numpy())),
        },
        descriptor_ownership="owned",
    )

    assert handle.closed is False
    assert handle.close() is None
    assert handle.closed is True
    assert handle.close() is None
    assert calls == [("destroy", (2,), state.value)]
    with pytest.raises(ReferenceError, match="allocatable handle is closed"):
        _ = handle.shape
    with pytest.raises(ReferenceError, match="allocatable handle is closed"):
        handle.to_numpy()


def test_owned_handle_close_marks_closed_when_destroy_raises():
    calls = []

    def destroy(_handle):
        calls.append("destroy")
        raise RuntimeError("boom")

    handle = AllocatableArray(
        dtype="float64",
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: (1,),
            "allocated": lambda _handle: True,
            "destroy": destroy,
        },
        descriptor_ownership="owned",
        to_numpy_policy="unsupported",
    )

    with pytest.raises(RuntimeError, match="boom"):
        handle.close()
    assert handle.closed is True
    assert handle.close() is None

    del handle
    gc.collect()

    assert calls == ["destroy"]


def test_owned_handle_finalizer_calls_destroy_once():
    calls = []

    handle = AllocatableArray(
        dtype="float64",
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: (1,),
            "allocated": lambda _handle: True,
            "destroy": lambda _handle: calls.append("destroy"),
        },
        descriptor_ownership="owned",
        to_numpy_policy="unsupported",
    )

    del handle
    gc.collect()

    assert calls == ["destroy"]


def test_owned_handle_construction_requires_generated_destroy_operation():
    with pytest.raises(ValueError, match="owned native array handle requires generated operation 'destroy'"):
        AllocatableArray(
            dtype="float64",
            rank=1,
            ops={
                **_required_handoff_ops(),
                "shape": lambda _handle: (1,),
                "allocated": lambda _handle: True,
            },
            descriptor_ownership="owned",
            to_numpy_policy="unsupported",
        )


def test_borrowed_handle_close_and_finalizer_do_not_destroy_native_storage():
    calls = []

    handle = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: (1,),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
            "destroy": lambda _handle: calls.append("destroy"),
        },
        to_numpy_policy="unsupported",
    )

    assert handle.close() is None
    assert handle.closed is False
    del handle
    gc.collect()

    assert calls == []
