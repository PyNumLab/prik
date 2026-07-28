"""Tests split by stable ownership concept from `test_factories_and_lifecycle.py`."""

from tests.runtime.handles._support import (
    AllocatableArray,
    NativeArrayHandleBase,
    PointerArray,
    _ArrayState,
    _common_ops,
    _handoff,
    _native_array_actual_for_binding,
    _native_array_descriptor_for_binding,
    _native_array_handle_from_generated_ops,
    _pointer_descriptor_for_array,
    _required_handoff_ops,
    np,
    pytest,
)


def test_allocatable_handle_uses_common_metadata_shape_owner_and_numpy_dispatch():
    owner = object()
    state = _ArrayState(shape=(2, 3), value=np.zeros((2, 3), dtype=np.float64))
    ops = {
        **_common_ops(state),
        "allocated": lambda _handle: state.shape is not None,
        "deallocate": lambda _handle: setattr(state, "shape", None),
        "resize": lambda _handle, shape: setattr(state, "shape", shape),
    }

    handle = AllocatableArray(
        dtype="float64",
        rank=2,
        ops=ops,
        owner=owner,
        descriptor_ownership="borrowed",
        generation=7,
    )

    assert isinstance(handle, NativeArrayHandleBase)
    assert handle.descriptor_kind == "allocatable"
    assert isinstance(handle.dtype, np.dtype)
    assert handle.dtype == np.dtype("float64")
    assert handle.rank == 2
    assert handle.shape == (2, 3)
    assert handle.to_numpy() is state.value
    assert handle.owner is owner
    assert handle.borrowed is True
    assert handle.owned is False
    assert handle.to_numpy_policy == "borrowed_view"
    assert handle.generation == 7
    assert handle.allocated is True


def test_allocatable_to_numpy_short_circuits_unallocated_state_before_generated_extraction():
    handle = AllocatableArray(
        dtype="float64",
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: None,
            "to_numpy": lambda _handle: pytest.fail("unallocated handles must not call generated extraction"),
            "allocated": lambda _handle: False,
        },
    )

    assert handle.to_numpy() is None


def test_pointer_to_numpy_short_circuits_unassociated_state_before_unsupported_policy():
    handle = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: None,
            "associated": lambda _handle: False,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="unsupported",
    )

    assert handle.to_numpy() is None


def test_shape_short_circuits_absent_descriptor_state_before_generated_shape():
    def fail_shape(_handle):
        pytest.fail("absent descriptor state must not call generated shape")

    allocatable = AllocatableArray(
        dtype="float64",
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": fail_shape,
            "allocated": lambda _handle: False,
        },
        to_numpy_policy="unsupported",
    )
    pointer = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": fail_shape,
            "associated": lambda _handle: False,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="unsupported",
    )

    assert allocatable.shape is None
    assert pointer.shape is None


def test_allocatable_handle_reports_absent_state_and_routes_resize_deallocate():
    state = _ArrayState()
    ops = {
        **_common_ops(state),
        "allocated": lambda _handle: state.shape is not None,
        "deallocate": lambda _handle: setattr(state, "shape", None),
        "resize": lambda _handle, shape: setattr(state, "shape", shape),
    }
    handle = AllocatableArray(dtype="float64", rank=1, ops=ops)

    assert handle.allocated is False
    assert handle.shape is None
    assert handle.to_numpy() is None

    handle.resize(4)
    assert handle.allocated is True
    assert handle.shape == (4,)

    handle.deallocate()
    assert handle.allocated is False
    assert handle.shape is None


def test_allocatable_to_numpy_policy_returns_mutable_borrowed_view():
    source = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    state = _ArrayState(shape=source.shape, value=source)
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            **_common_ops(state),
            "allocated": lambda _handle: True,
            "deallocate": lambda _handle: None,
            "resize": lambda _handle, _shape: None,
        },
        to_numpy_policy="borrowed_view",
    )

    view = handle.to_numpy()

    assert view is source
    assert view.flags.writeable is True
    view[1] = 8.0
    assert source[1] == 8.0


def test_allocatable_to_numpy_explicit_copy_is_independent():
    source = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    state = _ArrayState(shape=source.shape, value=source)
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            **_common_ops(state),
            "allocated": lambda _handle: True,
            "deallocate": lambda _handle: None,
            "resize": lambda _handle, _shape: None,
        },
        to_numpy_policy="descriptor_view",
    )

    view = handle.to_numpy()
    independent = view.copy()

    assert np.shares_memory(view, source) is True
    assert np.shares_memory(independent, source) is False
    source[0] = 99.0
    assert view[0] == 99.0
    assert independent[0] == 1.0


def test_to_numpy_contiguous_view_policy_rejects_non_contiguous_storage():
    source = np.arange(8, dtype=np.float64)
    strided = source[::2]
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            **_required_handoff_ops(),
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
            **_required_handoff_ops(),
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
            **_required_handoff_ops(),
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


def test_to_numpy_rejects_generated_none_for_present_descriptor_state():
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: (2,),
            "to_numpy": lambda _handle: None,
            "allocated": lambda _handle: True,
        },
    )

    with pytest.raises(TypeError, match="returned None for present descriptor state"):
        handle.to_numpy()


def test_to_numpy_rejects_generated_array_with_wrong_rank_or_dtype():
    wrong_rank = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            **_required_handoff_ops(),
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
            **_required_handoff_ops(),
            "shape": lambda _handle: (2,),
            "to_numpy": lambda _handle: np.zeros(2, dtype=np.int32),
            "allocated": lambda _handle: True,
        },
    )
    with pytest.raises(TypeError, match="to_numpy result dtype"):
        wrong_dtype.to_numpy()


def test_runtime_handle_shapes_reject_negative_extents_before_binding_handoff():
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "shape": lambda _handle: (-1,),
            "allocated": lambda _handle: True,
            "array_actual": lambda _handle: pytest.fail("negative shape must block native handoff"),
            "descriptor": lambda _handle: pytest.fail("negative shape must block descriptor handoff"),
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(ValueError, match="non-negative"):
        _ = handle.shape
    with pytest.raises(ValueError, match="non-negative"):
        _native_array_actual_for_binding(handle)
    with pytest.raises(ValueError, match="non-negative"):
        _native_array_descriptor_for_binding(handle, descriptor_kind="allocatable")
    with pytest.raises(ValueError, match="non-negative"):
        handle.resize(-1)

    valid_handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: _handoff(228),
            "shape": lambda _handle: (1,),
            "allocated": lambda _handle: True,
            "descriptor": lambda _handle: _handoff(229),
        },
        to_numpy_policy="unsupported",
    )
    with pytest.raises(ValueError, match="non-negative"):
        valid_handle._descriptor_for_binding(expected_shape=(-1,))


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


def test_pointer_associate_accepts_reassociation_and_an_unassociated_source():
    first_value = np.arange(3, dtype=np.float64)
    second_value = np.arange(4, dtype=np.float64)
    destination_state = {"descriptor": _pointer_descriptor_for_array(first_value)}
    source_state = {"descriptor": _pointer_descriptor_for_array(second_value)}

    def pointer(state):
        return PointerArray(
            dtype="float64",
            rank=1,
            ops={
                "shape": lambda _handle: tuple(dimension["extent"] for dimension in state["descriptor"]["dim"]),
                "array_actual": lambda _handle: _handoff(state["descriptor"]["base_addr"]),
                "descriptor": lambda _handle: state["descriptor"],
                "to_numpy": lambda _handle: state["descriptor"],
                "associated": lambda _handle: state["descriptor"]["base_addr"] != 0,
                "associate": lambda _handle, descriptor: state.update(descriptor=descriptor),
                "nullify": lambda _handle: state.update(
                    descriptor={
                        "base_addr": 0,
                        "elem_len": 8,
                        "rank": 1,
                        "dim": [{"lower_bound": 0, "extent": 0, "sm": 8}],
                    }
                ),
            },
            to_numpy_policy="descriptor_view",
        )

    destination = pointer(destination_state)
    source = pointer(source_state)

    destination.associate(source)
    assert destination.associated is True
    assert destination.shape == (4,)
    np.testing.assert_array_equal(destination.to_numpy(), second_value)

    source.nullify()
    destination.associate(source)
    assert destination.associated is False


def test_generated_pointer_associate_packs_standard_descriptor_facts():
    value = np.arange(6, dtype=np.float64)[::2]
    source_state = {"descriptor": _pointer_descriptor_for_array(value)}
    source = PointerArray(
        dtype="float64",
        rank=1,
        ops={
            "shape": lambda _handle: value.shape,
            "array_actual": lambda _handle: _handoff(value.ctypes.data),
            "descriptor": lambda _handle: source_state["descriptor"],
            "to_numpy": lambda _handle: source_state["descriptor"],
            "associated": lambda _handle: True,
            "associate": lambda _handle, descriptor: source_state.update(descriptor=descriptor),
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="descriptor_view",
    )
    received = []
    destination = _native_array_handle_from_generated_ops(
        "pointer",
        "float64",
        1,
        {
            "shape": lambda: None,
            "array_actual": lambda: 1,
            "descriptor": lambda: 1,
            "associated": lambda: False,
            "associate": lambda facts: received.append(facts),
            "nullify": lambda: None,
        },
        to_numpy_policy="unsupported",
    )

    destination.associate(source)

    assert received == [
        (
            int(value.ctypes.data),
            8,
            1,
            1,
            3,
            16,
        )
    ]


@pytest.mark.parametrize(
    ("other", "error", "message"),
    [
        (object(), TypeError, "requires another PointerArray"),
        (
            PointerArray(
                dtype="int32",
                rank=1,
                ops={
                    **_required_handoff_ops(),
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
                    **_required_handoff_ops(),
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
            **_required_handoff_ops(),
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
            **_required_handoff_ops(),
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
            **_required_handoff_ops(),
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
            **_required_handoff_ops(),
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


def test_common_handle_requires_generated_handoff_operations():
    with pytest.raises(ValueError, match="requires generated operation 'array_actual'"):
        AllocatableArray(
            dtype="float64",
            rank=1,
            ops={
                "shape": lambda _handle: (1,),
                "allocated": lambda _handle: True,
            },
            to_numpy_policy="unsupported",
        )
    with pytest.raises(ValueError, match="requires generated operation 'descriptor'"):
        AllocatableArray(
            dtype="float64",
            rank=1,
            ops={
                "array_actual": lambda _handle: _handoff(244),
                "shape": lambda _handle: (1,),
                "allocated": lambda _handle: True,
            },
            to_numpy_policy="unsupported",
        )


def test_extraction_enabled_handle_requires_generated_to_numpy_operation():
    with pytest.raises(ValueError, match="requires generated operation 'to_numpy'"):
        AllocatableArray(
            dtype="float64",
            rank=1,
            ops={
                **_required_handoff_ops(),
                "shape": lambda _handle: (1,),
                "allocated": lambda _handle: True,
            },
            to_numpy_policy="borrowed_view",
        )


def test_allocatable_handle_requires_generated_allocated_operation():
    with pytest.raises(ValueError, match="requires generated operation 'allocated'"):
        AllocatableArray(
            dtype="float64",
            rank=1,
            ops={
                **_required_handoff_ops(),
                "shape": lambda _handle: (1,),
                "to_numpy": lambda _handle: None,
            },
        )


def test_pointer_handle_requires_generated_associated_and_nullify_operations():
    with pytest.raises(ValueError, match="requires generated operation 'associated'"):
        PointerArray(
            dtype="float64",
            rank=1,
            ops={
                **_required_handoff_ops(),
                "shape": lambda _handle: (1,),
                "nullify": lambda _handle: None,
            },
        )
    with pytest.raises(ValueError, match="requires generated operation 'nullify'"):
        PointerArray(
            dtype="float64",
            rank=1,
            ops={
                **_required_handoff_ops(),
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
