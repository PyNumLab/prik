"""Tests split by stable ownership concept from `test_factories_and_lifecycle.py`."""

from tests.runtime.handles._support import (
    AllocatableArray,
    PointerArray,
    _ArrayState,
    _NativeArrayHandoff,
    _handoff,
    _native_array_actual_argument_for_binding_positional,
    _native_array_actual_for_binding,
    np,
    pytest,
)


def test_allocatable_array_actual_hook_requires_allocated_state_without_to_numpy():
    actual = _handoff(201)
    calls = []
    state = _ArrayState()
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(202),
            "shape": lambda _handle: state.shape,
            "allocated": lambda _handle: state.shape is not None,
            "to_numpy": lambda _handle: pytest.fail("array-actual handoff must not call to_numpy"),
            "array_actual": lambda _handle: calls.append("array_actual") or actual,
        },
    )

    with pytest.raises(ValueError, match="unallocated"):
        handle._array_actual_for_binding(expected_dtype=np.float64, expected_rank=1)

    state.shape = (4,)

    assert handle._array_actual_for_binding(expected_dtype="float64", expected_rank=1) is actual
    assert calls == ["array_actual"]


def test_array_actual_hook_rejects_generated_none_handoff():
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(203),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "array_actual": lambda _handle: None,
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(TypeError, match="array_actual operation must return a native handoff object"):
        _native_array_actual_for_binding(handle)


def test_native_array_handoff_requires_non_null_pointer_address():
    assert _NativeArrayHandoff(1).address == 1
    with pytest.raises(TypeError, match="address must be an integer"):
        _NativeArrayHandoff(True)
    with pytest.raises(TypeError, match="address must be an integer"):
        _NativeArrayHandoff("1")
    with pytest.raises(ValueError, match="non-null positive pointer"):
        _NativeArrayHandoff(0)
    with pytest.raises(ValueError, match="non-null positive pointer"):
        _NativeArrayHandoff(-1)


def test_array_actual_hook_rejects_generated_untyped_handoff_object():
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(245),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "array_actual": lambda _handle: object(),
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(TypeError, match="received object"):
        _native_array_actual_for_binding(handle)


def test_array_actual_hook_validates_expected_dtype_and_rank():
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=2,
        ops={
            "descriptor": lambda _handle: _handoff(204),
            "shape": lambda _handle: (2, 3),
            "allocated": lambda _handle: True,
            "array_actual": lambda _handle: _handoff(205),
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(ValueError, match="expected rank 1"):
        handle._array_actual_for_binding(expected_rank=1)
    with pytest.raises(TypeError, match="expected dtype"):
        handle._array_actual_for_binding(expected_dtype=np.int32)


def test_array_actual_hook_validates_expected_shape_layout_and_writeability():
    actual = _handoff(206)
    calls = []
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=2,
        ops={
            "descriptor": lambda _handle: _handoff(207),
            "shape": lambda _handle: (0, 3),
            "allocated": lambda _handle: True,
            "layout": lambda _handle: "F",
            "writeable": lambda _handle: True,
            "array_actual": lambda _handle: calls.append("array_actual") or actual,
        },
        to_numpy_policy="unsupported",
    )

    assert (
        handle._array_actual_for_binding(
            expected_dtype=np.float64,
            expected_rank=2,
            expected_shape=(0, 3),
            expected_layout="F",
            require_writeable=True,
        )
        is actual
    )
    assert calls == ["array_actual"]

    with pytest.raises(ValueError, match=r"expected shape .* axis 0"):
        handle._array_actual_for_binding(expected_shape=(1, 3))
    with pytest.raises(ValueError, match="expected shape rank 1"):
        handle._array_actual_for_binding(expected_shape=(0,))
    assert handle._array_actual_for_binding(expected_layout="f") is actual
    with pytest.raises(ValueError, match="expected layout 'C'"):
        handle._array_actual_for_binding(expected_layout="C")

    read_only = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(208),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "writeable": lambda _handle: False,
            "array_actual": lambda _handle: _handoff(209),
        },
        to_numpy_policy="unsupported",
    )
    with pytest.raises(TypeError, match="must be writeable"):
        read_only._array_actual_for_binding(require_writeable=True)

    missing_writeable = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(210),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "array_actual": lambda _handle: _handoff(211),
        },
        to_numpy_policy="unsupported",
    )
    with pytest.raises(NotImplementedError, match="operation 'writeable' is not available"):
        missing_writeable._array_actual_for_binding(require_writeable=True)


def test_array_actual_hook_rejects_unsupported_layout_names_before_handoff():
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(212),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "layout": lambda _handle: pytest.fail("unsupported expected layout must not call generated layout op"),
            "array_actual": lambda _handle: pytest.fail("unsupported expected layout must block native handoff"),
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(ValueError, match="unsupported expected NumPy array layout 'A'"):
        handle._array_actual_for_binding(expected_layout="A")

    invalid_actual = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(213),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "layout": lambda _handle: "K",
            "array_actual": lambda _handle: pytest.fail("unsupported actual layout must block native handoff"),
        },
        to_numpy_policy="unsupported",
    )
    with pytest.raises(ValueError, match="layout operation returned unsupported layout 'K'"):
        invalid_actual._array_actual_for_binding(expected_layout="F")


def test_array_actual_hook_validates_native_byte_order_and_alignment_ops():
    actual = _handoff(214)
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(215),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "native_byte_order": lambda _handle: True,
            "aligned": lambda _handle: True,
            "array_actual": lambda _handle: actual,
        },
        to_numpy_policy="unsupported",
    )

    assert (
        handle._array_actual_for_binding(
            require_native_byte_order=True,
            require_aligned=True,
        )
        is actual
    )

    byte_swapped = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(216),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "native_byte_order": lambda _handle: False,
            "array_actual": lambda _handle: _handoff(217),
        },
        to_numpy_policy="unsupported",
    )
    with pytest.raises(TypeError, match="native byte order"):
        byte_swapped._array_actual_for_binding(require_native_byte_order=True)

    unaligned = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(218),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "aligned": lambda _handle: False,
            "array_actual": lambda _handle: _handoff(219),
        },
        to_numpy_policy="unsupported",
    )
    with pytest.raises(TypeError, match="aligned"):
        unaligned._array_actual_for_binding(require_aligned=True)


def test_array_actual_binding_helper_accepts_ndarray_path_with_shared_validation():
    values = np.asfortranarray(np.zeros((2, 3), dtype=np.float64))

    assert (
        _native_array_actual_for_binding(
            values,
            expected_dtype=np.float64,
            expected_rank=2,
            expected_shape=(2, 3),
            expected_layout="F",
            require_writeable=True,
        )
        is values
    )

    with pytest.raises(TypeError, match="expected rank 1"):
        _native_array_actual_for_binding(values, expected_rank=1)
    with pytest.raises(TypeError, match="expected dtype"):
        _native_array_actual_for_binding(values, expected_dtype=np.float32)
    with pytest.raises(TypeError, match=r"incompatible shape at axis 0"):
        _native_array_actual_for_binding(values, expected_shape=(1, 3))
    with pytest.raises(TypeError, match=r"expected ordering \(C\)"):
        _native_array_actual_for_binding(values, expected_layout="C")

    read_only = values.copy()
    read_only.setflags(write=False)
    with pytest.raises(TypeError, match="writeable"):
        _native_array_actual_for_binding(read_only, require_writeable=True)


def test_array_actual_binding_helper_rejects_byte_swapped_and_unaligned_ndarrays():
    swapped_dtype = np.dtype(np.float64).newbyteorder("S")
    swapped = np.array([1.0, 2.0], dtype=swapped_dtype)
    with pytest.raises(TypeError, match="native byte order"):
        _native_array_actual_for_binding(swapped, require_native_byte_order=True)

    storage = np.zeros(8 * 2 + 1, dtype=np.uint8)
    unaligned = storage[1:].view(np.float64)
    assert not unaligned.flags.aligned
    with pytest.raises(TypeError, match="aligned"):
        _native_array_actual_for_binding(unaligned, require_aligned=True)


def test_array_actual_binding_helper_routes_handles_without_numpy_conversion():
    alloc_actual = _handoff(220)
    pointer_actual = _handoff(221)
    calls = []
    alloc_handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(222),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "layout": lambda _handle: "F",
            "writeable": lambda _handle: True,
            "native_byte_order": lambda _handle: True,
            "aligned": lambda _handle: True,
            "to_numpy": lambda _handle: pytest.fail("array-actual handoff must not call to_numpy"),
            "array_actual": lambda _handle: calls.append("alloc") or alloc_actual,
        },
    )
    pointer_handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(223),
            "shape": lambda _handle: (2,),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
            "layout": lambda _handle: "F",
            "writeable": lambda _handle: True,
            "native_byte_order": lambda _handle: True,
            "aligned": lambda _handle: True,
            "to_numpy": lambda _handle: pytest.fail("array-actual handoff must not call to_numpy"),
            "array_actual": lambda _handle: calls.append("pointer") or pointer_actual,
        },
    )

    assert (
        _native_array_actual_for_binding(
            alloc_handle,
            expected_dtype=np.float64,
            expected_rank=1,
            expected_shape=(2,),
            expected_layout="F",
            require_writeable=True,
            require_native_byte_order=True,
            require_aligned=True,
        )
        is alloc_actual
    )
    assert (
        _native_array_actual_for_binding(
            pointer_handle,
            expected_dtype=np.float64,
            expected_rank=1,
            expected_shape=(2,),
            expected_layout="F",
            require_writeable=True,
            require_native_byte_order=True,
            require_aligned=True,
        )
        is pointer_actual
    )
    assert calls == ["alloc", "pointer"]


def test_array_actual_binding_helper_preserves_zero_length_array_actuals():
    values = np.zeros((0,), dtype=np.float64)
    assert _native_array_actual_for_binding(values, expected_dtype=np.float64, expected_shape=(0,)) is values

    alloc_actual = _handoff(224)
    pointer_actual = _handoff(225)
    alloc_handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(226),
            "shape": lambda _handle: (0,),
            "allocated": lambda _handle: True,
            "array_actual": lambda _handle: alloc_actual,
        },
        to_numpy_policy="unsupported",
    )
    pointer_handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(227),
            "shape": lambda _handle: (0,),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
            "array_actual": lambda _handle: pointer_actual,
        },
        to_numpy_policy="unsupported",
    )

    assert _native_array_actual_for_binding(alloc_handle, expected_shape=(0,)) is alloc_actual
    assert _native_array_actual_for_binding(pointer_handle, expected_shape=(0,)) is pointer_actual


def test_array_actual_argument_abi_packer_uses_ndarray_data_pointer_and_shape_fields():
    values = np.asfortranarray(np.zeros((2, 3), dtype=np.float64))

    assert _native_array_actual_argument_for_binding_positional(
        values,
        np.float64,
        2,
        (2, 3),
        "F",
        True,
        True,
        True,
        True,
        True,
        True,
    ) == (values.ctypes.data, 2, values.dtype.itemsize, 2, 3, 1, 2, 1, 1)


def test_array_actual_argument_abi_packer_flattens_contiguous_storage_shape():
    values = np.asfortranarray(np.arange(6, dtype=np.float64).reshape((2, 3), order="F"))

    assert _native_array_actual_argument_for_binding_positional(
        values,
        expected_dtype=np.float64,
        expected_rank=-1,
        expected_shape=None,
        require_native_byte_order=True,
        require_aligned=True,
        require_contiguous=True,
        flatten_storage=True,
    ) == (values.ctypes.data, values.size)


def test_array_actual_argument_abi_packer_flattens_native_handle_shape():
    actual = _handoff(252)
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=2,
        ops={
            "descriptor": lambda _handle: _handoff(253),
            "shape": lambda _handle: (2, 3),
            "allocated": lambda _handle: True,
            "layout": lambda _handle: "F",
            "writeable": lambda _handle: True,
            "native_byte_order": lambda _handle: True,
            "aligned": lambda _handle: True,
            "to_numpy": lambda _handle: pytest.fail("flat array-actual ABI packing must not call to_numpy"),
            "array_actual": lambda _handle: actual,
        },
    )

    assert _native_array_actual_argument_for_binding_positional(
        handle,
        expected_dtype=np.float64,
        expected_rank=-1,
        expected_shape=None,
        require_native_byte_order=True,
        require_aligned=True,
        require_contiguous=True,
        flatten_storage=True,
    ) == (actual.address, 6)


def test_array_actual_argument_abi_packer_uses_allocatable_native_array_actual_without_numpy_conversion():
    actual = _handoff(246)
    calls = []
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(247),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "layout": lambda _handle: "F",
            "writeable": lambda _handle: True,
            "native_byte_order": lambda _handle: True,
            "aligned": lambda _handle: True,
            "to_numpy": lambda _handle: pytest.fail("array-actual ABI packing must not call to_numpy"),
            "array_actual": lambda _handle: calls.append("array_actual") or actual,
        },
    )

    assert _native_array_actual_argument_for_binding_positional(
        handle,
        "float64",
        1,
        (2,),
        "F",
        True,
        True,
        True,
        True,
        True,
        True,
    ) == (actual.address, 1, np.dtype(np.float64).itemsize, 2, 1, 1)
    assert calls == ["array_actual"]


def test_array_actual_argument_abi_packer_uses_pointer_native_array_actual_dtype_metadata():
    actual = _handoff(248)
    handle = PointerArray(
        dtype=np.dtype(np.float32),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(249),
            "shape": lambda _handle: (3,),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
            "array_actual": lambda _handle: actual,
        },
        to_numpy_policy="unsupported",
    )

    assert _native_array_actual_argument_for_binding_positional(
        handle,
        None,
        1,
        (3,),
        None,
        False,
        False,
        False,
        False,
        True,
        False,
    ) == (actual.address, np.dtype(np.float32).itemsize, 3)


def test_array_actual_argument_abi_packer_rejects_absent_handles_before_generated_handoff():
    alloc_handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(250),
            "shape": lambda _handle: None,
            "allocated": lambda _handle: False,
            "to_numpy": lambda _handle: pytest.fail("array-actual ABI packing must not call to_numpy"),
            "array_actual": lambda _handle: pytest.fail("unallocated handle must block native array handoff"),
        },
    )
    pointer_handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(251),
            "shape": lambda _handle: None,
            "associated": lambda _handle: False,
            "nullify": lambda _handle: None,
            "to_numpy": lambda _handle: pytest.fail("array-actual ABI packing must not call to_numpy"),
            "array_actual": lambda _handle: pytest.fail("unassociated handle must block native array handoff"),
        },
    )

    with pytest.raises(ValueError, match="unallocated"):
        _native_array_actual_argument_for_binding_positional(alloc_handle)
    with pytest.raises(ValueError, match="unassociated"):
        _native_array_actual_argument_for_binding_positional(pointer_handle)


def test_array_actual_binding_helper_rejects_absent_handles_none_and_non_arrays():
    alloc_handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(230),
            "shape": lambda _handle: None,
            "allocated": lambda _handle: False,
            "to_numpy": lambda _handle: pytest.fail("array-actual handoff must not call to_numpy"),
            "array_actual": lambda _handle: _handoff(231),
        },
    )
    pointer_handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(232),
            "shape": lambda _handle: None,
            "associated": lambda _handle: False,
            "nullify": lambda _handle: None,
            "to_numpy": lambda _handle: pytest.fail("array-actual handoff must not call to_numpy"),
            "array_actual": lambda _handle: _handoff(233),
        },
    )

    with pytest.raises(ValueError, match="unallocated"):
        _native_array_actual_for_binding(alloc_handle)
    with pytest.raises(ValueError, match="unassociated"):
        _native_array_actual_for_binding(pointer_handle)
    with pytest.raises(TypeError, match="received None"):
        _native_array_actual_for_binding(None)
    with pytest.raises(TypeError, match="received list"):
        _native_array_actual_for_binding([1.0, 2.0])


def test_pointer_array_actual_hook_requires_associated_state_without_to_numpy():
    actual = _handoff(242)
    calls = []
    state = _ArrayState()
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "descriptor": lambda _handle: _handoff(243),
            "shape": lambda _handle: state.shape,
            "associated": lambda _handle: state.shape is not None,
            "nullify": lambda _handle: setattr(state, "shape", None),
            "to_numpy": lambda _handle: pytest.fail("array-actual handoff must not call to_numpy"),
            "array_actual": lambda _handle: calls.append("array_actual") or actual,
        },
    )

    with pytest.raises(ValueError, match="unassociated"):
        handle._array_actual_for_binding(expected_dtype=np.float64, expected_rank=1)

    state.shape = (3,)

    assert handle._array_actual_for_binding(expected_dtype="float64", expected_rank=1) is actual
    assert calls == ["array_actual"]
