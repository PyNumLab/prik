"""Pointer handle state, association, extraction, and operation protocols."""

import numpy as np
import pytest
from prik.runtime.handles import (
    AllocatableArray,
    NativeArrayHandleBase,
    PointerArray,
    _native_array_handle_from_generated_ops,
    _numpy_view_from_descriptor_facts,
)
from tests.fortran._support.native_array_handles import (
    _ArrayState,
    _common_ops,
    _descriptor_facts_for_array,
)


def test_pointer_to_numpy_reports_unassociated_state_before_an_unsupported_policy():
    """There is nothing to expose either way when the target is not there.

    A policy that blocks extraction still has to answer an unassociated
    pointer with None rather than refusing, because no view is being withheld.
    """
    handle = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            "shape": lambda _handle: None,
            "associated": lambda _handle: False,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="unsupported",
    )

    assert handle.to_numpy() is None


def test_shape_reports_absent_descriptor_state_without_being_asked_first():
    def fail_state(_handle):
        pytest.fail("the shape inquiry reads the descriptor, which records absence itself")

    allocatable = AllocatableArray(
        dtype="float64",
        rank=1,
        ops={
            "shape": lambda _handle: None,
            "allocated": fail_state,
        },
        to_numpy_policy="unsupported",
    )
    pointer = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            "shape": lambda _handle: None,
            "associated": fail_state,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="unsupported",
    )

    assert allocatable.shape is None
    assert pointer.shape is None


def test_to_numpy_contiguous_view_policy_rejects_non_contiguous_storage():
    source = np.arange(8, dtype=np.float64)
    strided = source[::2]
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "shape": lambda _handle: strided.shape,
            "to_numpy": lambda _handle: strided,
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="contiguous_view",
    )

    with pytest.raises(ValueError, match="must be contiguous"):
        handle.to_numpy()


def test_to_numpy_descriptor_view_policy_never_copies_storage():
    source = np.arange(4, dtype=np.float64)
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "shape": lambda _handle: source.shape,
            "to_numpy": lambda _handle: source,
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="descriptor_view",
    )

    view = handle.to_numpy()

    assert np.shares_memory(view, source) is True
    assert view.flags.writeable is True
    view[0] = 99.0
    assert source[0] == 99.0


@pytest.mark.parametrize(
    "policy",
    ["borrowed_view", "contiguous_view", "descriptor_view"],
)
def test_to_numpy_rejects_generated_non_numpy_results(policy: str):
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "shape": lambda _handle: (2,),
            "to_numpy": lambda _handle: [1.0, 2.0],
            "allocated": lambda _handle: True,
            "deallocate": lambda _handle: None,
            "resize": lambda _handle, _shape: None,
        },
        to_numpy_policy=policy,
    )

    with pytest.raises(TypeError, match="must return a NumPy array or None"):
        handle.to_numpy()


def test_to_numpy_rejects_generated_array_with_wrong_rank_or_dtype():
    wrong_rank = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "shape": lambda _handle: (2,),
            "to_numpy": lambda _handle: np.zeros((1, 2), dtype=np.float64),
            "allocated": lambda _handle: True,
        },
    )
    with pytest.raises(ValueError, match="to_numpy result rank 2 does not match declared rank 1"):
        wrong_rank.to_numpy()

    wrong_dtype = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "shape": lambda _handle: (2,),
            "to_numpy": lambda _handle: np.zeros(2, dtype=np.int32),
            "allocated": lambda _handle: True,
        },
    )
    with pytest.raises(TypeError, match="to_numpy result dtype"):
        wrong_dtype.to_numpy()


def test_runtime_handle_shapes_reject_negative_extents():
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "shape": lambda _handle: (-1,),
            "allocated": lambda _handle: True,
            "resize": lambda _handle, _shape: None,
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(ValueError, match="non-negative"):
        _ = handle.shape
    with pytest.raises(ValueError, match="non-negative"):
        handle.resize(-1)


def test_pointer_handle_uses_common_base_and_nullify_operation():
    state = _ArrayState(shape=(5,), value=np.zeros(5, dtype=np.int32))

    def nullify(_handle):
        state.shape = None
        state.value = None

    ops = {
        **_common_ops(state),
        "associated": lambda _handle: state.shape is not None,
        "nullify": nullify,
        "destroy": lambda _handle: None,
    }
    handle = PointerArray(dtype="int32", rank=1, ops=ops, descriptor_ownership="owned")

    assert isinstance(handle, NativeArrayHandleBase)
    assert handle.descriptor_kind == "pointer"
    assert handle.owned is True
    assert handle.associated is True
    assert handle.shape == (5,)
    assert handle.to_numpy() is state.value

    handle.nullify()
    assert handle.associated is False
    assert handle.shape is None
    assert handle.to_numpy() is None


def test_pointer_associate_copies_the_target_as_it_stands_and_does_not_follow_it():
    """A pointer assignment snapshots the source's target, it does not track it."""
    first_value = np.arange(3, dtype=np.float64)
    second_value = np.arange(4, dtype=np.float64)
    absent = (0, 8, 1, 0, 0, 8)

    def pointer(state):
        return PointerArray(
            dtype="float64",
            rank=1,
            ops={
                "shape": lambda _handle: (state["facts"][4],) if state["facts"][0] else None,
                "descriptor": lambda _handle: state["facts"],
                "to_numpy": lambda _handle: _numpy_view_from_descriptor_facts(state["facts"], "float64"),
                "associated": lambda _handle: state["facts"][0] != 0,
                "associate": lambda _handle, facts: state.update(facts=facts),
                "nullify": lambda _handle: state.update(facts=absent),
            },
            to_numpy_policy="descriptor_view",
        )

    destination = pointer({"facts": _descriptor_facts_for_array(first_value)})
    source = pointer({"facts": _descriptor_facts_for_array(second_value)})

    destination.associate(source)
    assert destination.associated is True
    assert destination.shape == (4,)
    np.testing.assert_array_equal(destination.to_numpy(), second_value)

    source.nullify()
    assert destination.associated is True
    destination.associate(source)
    assert destination.associated is False


def test_generated_pointer_associate_hands_over_flat_descriptor_facts():
    value = np.arange(6, dtype=np.float64)[::2]
    source = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            "shape": lambda _handle: value.shape,
            "descriptor": lambda _handle: _descriptor_facts_for_array(value),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
            "associate": lambda _handle, _facts: None,
        },
        to_numpy_policy="unsupported",
    )
    received = []
    destination = _native_array_handle_from_generated_ops(
        "pointer",
        "float64",
        1,
        {
            "shape": lambda: None,
            "descriptor": lambda: None,
            "associated": lambda: False,
            "associate": lambda facts: received.append(facts),
            "nullify": lambda: None,
        },
        to_numpy_policy="unsupported",
    )

    destination.associate(source)

    assert received == [(int(value.ctypes.data), 8, 1, 1, 3, 16)]


@pytest.mark.parametrize(
    ("other", "error", "message"),
    [
        (object(), TypeError, "requires another PointerArray"),
        (
            PointerArray(
                dtype="int32",
                rank=1,
                ops={
                    "shape": lambda _handle: None,
                    "associated": lambda _handle: False,
                    "nullify": lambda _handle: None,
                },
                to_numpy_policy="unsupported",
            ),
            TypeError,
            "dtype",
        ),
        (
            PointerArray(
                dtype="float64",
                rank=2,
                ops={
                    "shape": lambda _handle: None,
                    "associated": lambda _handle: False,
                    "nullify": lambda _handle: None,
                },
                to_numpy_policy="unsupported",
            ),
            ValueError,
            "rank",
        ),
    ],
)
def test_pointer_associate_rejects_incompatible_sources(other, error, message):
    destination = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            "shape": lambda _handle: None,
            "associated": lambda _handle: False,
            "associate": lambda _handle, _descriptor: None,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(error, match=message):
        destination.associate(other)


def test_pointer_allocation_operations_are_policy_gated_by_ops_table():
    state = _ArrayState(shape=(1,), value=object())
    handle = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            **_common_ops(state),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
        },
    )

    with pytest.raises(NotImplementedError, match="pointer handle operation 'allocate' is not available"):
        handle.allocate((3,))
    with pytest.raises(NotImplementedError, match="pointer handle operation 'deallocate' is not available"):
        handle.deallocate()
    with pytest.raises(NotImplementedError, match="pointer handle operation 'resize' is not available"):
        handle.resize((4,))


def test_pointer_allocation_operations_route_when_policy_ops_exist():
    state = _ArrayState(shape=None, value=None)

    def allocate(_handle, shape):
        state.shape = shape
        state.value = object()

    def deallocate(_handle):
        state.shape = None
        state.value = None

    def resize(_handle, shape):
        state.shape = shape
        state.value = object()

    handle = PointerArray(
        dtype="float64",
        rank=2,
        ops={
            **_common_ops(state),
            "associated": lambda _handle: state.shape is not None,
            "nullify": lambda _handle: deallocate(_handle),
            "allocate": allocate,
            "deallocate": deallocate,
            "resize": resize,
        },
    )

    assert handle.associated is False
    handle.allocate((2, 3))
    assert handle.associated is True
    assert handle.shape == (2, 3)

    handle.resize([4, 5])
    assert handle.shape == (4, 5)

    handle.deallocate()
    assert handle.associated is False
    assert handle.shape is None


def test_pointer_to_numpy_reports_missing_descriptor_extraction():
    handle = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            "shape": lambda _handle: (2,),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(NotImplementedError, match="to_numpy extraction is unsupported by completed policy"):
        handle.to_numpy()


def test_to_numpy_policy_unsupported_reports_completed_policy_block():
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "shape": lambda _handle: (2,),
            "to_numpy": lambda _handle: pytest.fail("unsupported policy must not call generated extraction"),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(NotImplementedError, match="to_numpy extraction is unsupported by completed policy"):
        handle.to_numpy()


def test_common_shape_dispatch_validates_rank():
    handle = AllocatableArray(
        dtype="float64",
        rank=2,
        ops={
            "shape": lambda _handle: (4,),
            "to_numpy": lambda _handle: None,
            "allocated": lambda _handle: True,
            "deallocate": lambda _handle: None,
            "resize": lambda _handle, _shape: None,
        },
    )

    with pytest.raises(ValueError, match="shape rank 1 does not match declared rank 2"):
        _ = handle.shape


def test_common_handle_rejects_invalid_descriptor_kind():
    with pytest.raises(ValueError, match="descriptor_kind must be 'allocatable' or 'pointer'"):
        NativeArrayHandleBase(
            dtype="float64",
            rank=1,
            ops={},
            descriptor_kind="target",
            descriptor_ownership="borrowed",
        )


def test_common_handle_rejects_invalid_generated_operation_table():
    with pytest.raises(TypeError, match="operation names must be strings"):
        AllocatableArray(dtype="float64", rank=1, ops={1: lambda _handle: None})
    with pytest.raises(TypeError, match="operation 'shape' must be callable"):
        AllocatableArray(dtype="float64", rank=1, ops={"shape": None})


def test_common_handle_requires_generated_shape_operation():
    with pytest.raises(ValueError, match="requires generated operation 'shape'"):
        AllocatableArray(dtype="float64", rank=1, ops={})


def test_extraction_enabled_handle_requires_generated_to_numpy_operation():
    with pytest.raises(ValueError, match="requires generated operation 'to_numpy'"):
        AllocatableArray(
            dtype="float64",
            rank=1,
            ops={
                "shape": lambda _handle: (1,),
                "allocated": lambda _handle: True,
            },
            to_numpy_policy="borrowed_view",
        )


def test_pointer_handle_requires_generated_associated_and_nullify_operations():
    with pytest.raises(ValueError, match="requires generated operation 'associated'"):
        PointerArray(
            dtype="float64",
            rank=1,
            ops={
                "shape": lambda _handle: (1,),
                "nullify": lambda _handle: None,
            },
        )
    with pytest.raises(ValueError, match="requires generated operation 'nullify'"):
        PointerArray(
            dtype="float64",
            rank=1,
            ops={
                "shape": lambda _handle: (1,),
                "associated": lambda _handle: True,
            },
        )


def test_common_handle_rejects_invalid_descriptor_ownership():
    with pytest.raises(ValueError, match="descriptor_ownership must be 'borrowed' or 'owned'"):
        AllocatableArray(dtype="float64", rank=1, ops={}, descriptor_ownership="temporary")


def test_common_handle_rejects_invalid_to_numpy_policy():
    with pytest.raises(ValueError, match="to_numpy_policy must be one of"):
        AllocatableArray(dtype="float64", rank=1, ops={}, to_numpy_policy="maybe_copy")
