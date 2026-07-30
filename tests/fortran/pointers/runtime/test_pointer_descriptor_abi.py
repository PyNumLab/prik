"""Pointer descriptor handoff and strided-view ABI behavior."""

from tests.fortran._support.native_array_handles import (
    AllocatableArray,
    PointerArray,
    _ArrayState,
    _NativeArrayDescriptorHandoff,
    _common_ops,
    _handoff,
    _native_array_descriptor_argument_for_binding,
    _native_array_descriptor_argument_for_binding_positional,
    _native_array_descriptor_for_binding,
    _native_array_descriptor_handoff_for_binding,
    _native_array_descriptor_handoff_for_binding_positional,
    _numpy_view_from_pointer_c_descriptor,
    _pointer_descriptor_for_array,
    _pointer_descriptor_record_for_array,
    _required_handoff_ops,
    np,
    pytest,
)


def test_descriptor_hook_rejects_generated_none_handoff():
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: None,
            "allocated": lambda _handle: False,
            "descriptor": lambda _handle: None,
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(
        TypeError, match="descriptor operation must return descriptor fields or an integer data address"
    ):
        _native_array_descriptor_for_binding(handle, descriptor_kind="allocatable")


def test_descriptor_hook_validates_expected_dtype_rank_and_current_shape():
    descriptor = _handoff(235)
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=2,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: (2, 3),
            "allocated": lambda _handle: True,
            "descriptor": lambda _handle: descriptor,
        },
        to_numpy_policy="unsupported",
    )

    assert handle._descriptor_for_binding(
        expected_dtype=np.float64,
        expected_rank=2,
        expected_shape=(2, 3),
    ) == {
        "base_addr": descriptor.address,
        "elem_len": 8,
        "rank": 2,
        "dim": [
            {"lower_bound": 0, "extent": 2, "sm": 8},
            {"lower_bound": 0, "extent": 3, "sm": 16},
        ],
    }
    with pytest.raises(ValueError, match="expected rank 1"):
        handle._descriptor_for_binding(expected_rank=1)
    with pytest.raises(TypeError, match="expected dtype"):
        handle._descriptor_for_binding(expected_dtype=np.int32)
    with pytest.raises(ValueError, match=r"expected shape .* axis 1"):
        handle._descriptor_for_binding(expected_shape=(2, 4))


def test_descriptor_binding_helper_accepts_matching_handles_and_optional_none():
    alloc_descriptor = _handoff(236)
    pointer_descriptor = _handoff(237)
    alloc_handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: (0,),
            "allocated": lambda _handle: True,
            "descriptor": lambda _handle: alloc_descriptor,
        },
        to_numpy_policy="unsupported",
    )
    pointer_handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: None,
            "associated": lambda _handle: False,
            "nullify": lambda _handle: None,
            "descriptor": lambda _handle: pointer_descriptor,
        },
        to_numpy_policy="unsupported",
    )

    assert _native_array_descriptor_for_binding(
        alloc_handle,
        descriptor_kind="allocatable",
        expected_dtype=np.float64,
        expected_rank=1,
        expected_shape=(0,),
    ) == {
        "base_addr": alloc_descriptor.address,
        "elem_len": 8,
        "rank": 1,
        "dim": [{"lower_bound": 0, "extent": 0, "sm": 8}],
    }
    assert _native_array_descriptor_for_binding(
        pointer_handle,
        descriptor_kind="pointer",
        expected_dtype=np.float64,
        expected_rank=1,
    ) == {
        "base_addr": pointer_descriptor.address,
        "elem_len": 8,
        "rank": 1,
        "dim": [{"lower_bound": 0, "extent": 0, "sm": 8}],
    }
    assert _native_array_descriptor_for_binding(None, descriptor_kind="pointer", optional=True) is None


def test_descriptor_binding_helper_rejects_plain_arrays_none_and_wrong_kind():
    alloc_handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: (1,),
            "allocated": lambda _handle: True,
            "descriptor": lambda _handle: _handoff(238),
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(TypeError, match="received ndarray"):
        _native_array_descriptor_for_binding(np.ones(1), descriptor_kind="allocatable")
    with pytest.raises(TypeError, match="received None"):
        _native_array_descriptor_for_binding(None, descriptor_kind="allocatable")
    with pytest.raises(TypeError, match="expected pointer native array handle"):
        _native_array_descriptor_for_binding(alloc_handle, descriptor_kind="pointer")
    with pytest.raises(ValueError, match="unsupported native array descriptor kind"):
        _native_array_descriptor_for_binding(alloc_handle, descriptor_kind="coarray")
    with pytest.raises(ValueError, match="unsupported native array descriptor kind"):
        _native_array_descriptor_for_binding(None, descriptor_kind="coarray", optional=True)


def test_descriptor_argument_abi_packer_returns_required_descriptor_fields():
    descriptor = _handoff(239)
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "descriptor": lambda _handle: descriptor,
        },
        to_numpy_policy="unsupported",
    )

    assert _native_array_descriptor_argument_for_binding(
        handle,
        descriptor_kind="allocatable",
        expected_dtype=np.float64,
        expected_rank=1,
        expected_shape=(2,),
    ) == (descriptor.address, 8, 1, 0, 2, 8)


def test_descriptor_argument_abi_packer_positional_helper_matches_generated_call_shape():
    descriptor = _handoff(242)
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "descriptor": lambda _handle: descriptor,
        },
        to_numpy_policy="unsupported",
    )

    assert _native_array_descriptor_argument_for_binding_positional(
        handle,
        "allocatable",
        "float64",
        1,
        None,
        False,
    ) == (descriptor.address, 8, 1, 0, 2, 8)
    assert _native_array_descriptor_argument_for_binding_positional(
        None,
        "allocatable",
        "float64",
        1,
        None,
        True,
    ) == (None, None, None, None, None, None, None)


def test_descriptor_argument_abi_packer_maps_optional_presence_and_absence():
    descriptor = _handoff(240)
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: None,
            "associated": lambda _handle: False,
            "nullify": lambda _handle: None,
            "descriptor": lambda _handle: descriptor,
        },
        to_numpy_policy="unsupported",
    )

    *descriptor_fields, presence_token = _native_array_descriptor_argument_for_binding(
        handle,
        descriptor_kind="pointer",
        expected_dtype=np.float64,
        expected_rank=1,
        optional_absent=True,
    )
    assert descriptor_fields == [descriptor.address, 8, 1, 0, 0, 8]
    assert presence_token is not None
    assert presence_token != descriptor.address
    assert _native_array_descriptor_argument_for_binding(
        None,
        descriptor_kind="pointer",
        expected_rank=1,
        optional_absent=True,
    ) == (None, None, None, None, None, None, None)


def test_descriptor_argument_abi_packer_rejects_wrong_kind_and_unsupported_descriptor_kind():
    alloc_handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: (1,),
            "allocated": lambda _handle: True,
            "descriptor": lambda _handle: _handoff(241),
        },
        to_numpy_policy="unsupported",
    )

    with pytest.raises(TypeError, match="expected pointer native array handle"):
        _native_array_descriptor_argument_for_binding(alloc_handle, descriptor_kind="pointer")
    with pytest.raises(ValueError, match="unsupported native array descriptor kind"):
        _native_array_descriptor_argument_for_binding(None, descriptor_kind="coarray", optional_absent=True)
    with pytest.raises(TypeError, match="received ndarray"):
        _native_array_descriptor_argument_for_binding(np.ones(1), descriptor_kind="allocatable")


def test_projected_descriptor_handoff_requires_persistent_standard_descriptor_storage():
    owner = object()
    direct = _NativeArrayDescriptorHandoff(owner)
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "descriptor": lambda _handle: direct,
        },
        to_numpy_policy="unsupported",
    )

    assert _native_array_descriptor_handoff_for_binding(
        handle,
        descriptor_kind="allocatable",
        expected_dtype=np.float64,
        expected_rank=1,
        expected_shape=(2,),
    ) == (owner,)
    assert _native_array_descriptor_handoff_for_binding_positional(
        handle,
        "allocatable",
        "float64",
        1,
        (2,),
        False,
    ) == (owner,)


def test_owned_standard_descriptor_can_supply_fact_packed_read_only_handoff():
    owner = object()
    direct = _NativeArrayDescriptorHandoff(owner)
    record = {
        "base_addr": 0x5678,
        "elem_len": 8,
        "rank": 1,
        "dim": [{"lower_bound": 0, "extent": 2, "sm": 8}],
    }
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: (2,),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
            "descriptor": lambda _handle: direct,
            "to_numpy": lambda _handle: record,
            "destroy": lambda _handle: None,
        },
        descriptor_ownership="owned",
        to_numpy_policy="unsupported",
    )

    assert _native_array_descriptor_argument_for_binding(
        handle,
        descriptor_kind="pointer",
        expected_dtype=np.float64,
        expected_rank=1,
        expected_shape=(2,),
    ) == (0x5678, 8, 1, 0, 2, 8)
    assert _native_array_descriptor_handoff_for_binding(
        handle,
        descriptor_kind="pointer",
        expected_dtype=np.float64,
        expected_rank=1,
        expected_shape=(2,),
    ) == (owner,)
    assert _native_array_descriptor_handoff_for_binding_positional(
        None,
        "allocatable",
        "float64",
        1,
        None,
        True,
    ) == (None, None)

    fact_packed = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("descriptor handoff must not request array actual"),
            "shape": lambda _handle: (2,),
            "allocated": lambda _handle: True,
            "descriptor": lambda _handle: _handoff(0x5678),
        },
        to_numpy_policy="unsupported",
    )
    with pytest.raises(TypeError, match="requires a generated direct descriptor handoff"):
        _native_array_descriptor_handoff_for_binding(fact_packed, descriptor_kind="allocatable")


def test_pointer_c_descriptor_helper_builds_strided_numpy_view_from_decoded_fields():
    source = np.arange(24, dtype=np.float64).reshape((4, 6), order="F")
    expected = source[1:4:2, 2:6:3]

    view = _numpy_view_from_pointer_c_descriptor(_pointer_descriptor_for_array(expected), dtype=np.float64)

    assert view.shape == expected.shape
    assert view.strides == expected.strides
    np.testing.assert_allclose(view, expected)
    assert np.shares_memory(view, source)

    view[0, 1] = 77.0
    assert expected[0, 1] == 77.0


def test_pointer_c_descriptor_helper_builds_negative_stride_numpy_view_from_decoded_fields():
    source = np.arange(10, dtype=np.float64)
    expected = source[8:1:-2]

    view = _numpy_view_from_pointer_c_descriptor(_pointer_descriptor_for_array(expected), dtype=np.float64)

    assert view.shape == expected.shape
    assert view.strides == expected.strides
    np.testing.assert_allclose(view, expected)
    assert np.shares_memory(view, source)

    view[0] = 88.0
    assert source[8] == 88.0


def test_pointer_c_descriptor_helper_accepts_field_record_objects():
    source = np.arange(12, dtype=np.float64).reshape((3, 4))
    expected = source[:, 1:4:2]

    view = _numpy_view_from_pointer_c_descriptor(_pointer_descriptor_record_for_array(expected), dtype=np.float64)

    assert view.shape == expected.shape
    assert view.strides == expected.strides
    np.testing.assert_allclose(view, expected)
    assert np.shares_memory(view, source)

    view[1, 0] = 55.0
    assert source[1, 1] == 55.0


def test_pointer_c_descriptor_helper_validates_decoded_descriptor_fields():
    source = np.arange(4, dtype=np.float64)
    descriptor = _pointer_descriptor_for_array(source)

    assert _numpy_view_from_pointer_c_descriptor({**descriptor, "base_addr": 0}, dtype=np.float64) is None
    for field in ("base_addr", "elem_len", "rank", "dim"):
        incomplete = dict(descriptor)
        incomplete.pop(field)
        with pytest.raises(TypeError, match=f"field {field!r} is required"):
            _numpy_view_from_pointer_c_descriptor(incomplete, dtype=np.float64)
    with pytest.raises(ValueError, match="base_addr must be non-negative"):
        _numpy_view_from_pointer_c_descriptor({**descriptor, "base_addr": -1}, dtype=np.float64)
    with pytest.raises(TypeError, match="field 'base_addr' must be an integer"):
        _numpy_view_from_pointer_c_descriptor({**descriptor, "base_addr": True}, dtype=np.float64)
    with pytest.raises(ValueError, match=r"elem_len .* itemsize"):
        _numpy_view_from_pointer_c_descriptor({**descriptor, "elem_len": 4}, dtype=np.float64)
    with pytest.raises(ValueError, match="rank must be non-negative"):
        _numpy_view_from_pointer_c_descriptor({**descriptor, "rank": -1}, dtype=np.float64)
    with pytest.raises(ValueError, match="rank 2 does not match 1 dimension records"):
        _numpy_view_from_pointer_c_descriptor({**descriptor, "rank": 2}, dtype=np.float64)
    for field in ("lower_bound", "extent", "sm"):
        bad_dim_record = dict(descriptor["dim"][0])
        bad_dim_record.pop(field)
        with pytest.raises(TypeError, match=f"dim\\[0\\] field {field!r} is required"):
            _numpy_view_from_pointer_c_descriptor({**descriptor, "dim": [bad_dim_record]}, dtype=np.float64)
    with pytest.raises(TypeError, match="field 'lower_bound' must be an integer"):
        bad_dim = [{**descriptor["dim"][0], "lower_bound": True}]
        _numpy_view_from_pointer_c_descriptor({**descriptor, "dim": bad_dim}, dtype=np.float64)
    with pytest.raises(ValueError, match="dim\\[0\\]\\.extent must be non-negative"):
        bad_dim = [{**descriptor["dim"][0], "extent": -1}]
        _numpy_view_from_pointer_c_descriptor({**descriptor, "dim": bad_dim}, dtype=np.float64)
    with pytest.raises(TypeError, match="field 'sm' must be an integer"):
        bad_dim = [{**descriptor["dim"][0], "sm": True}]
        _numpy_view_from_pointer_c_descriptor({**descriptor, "dim": bad_dim}, dtype=np.float64)
    with pytest.raises(TypeError, match="field 'dim' must be a sequence"):
        _numpy_view_from_pointer_c_descriptor({**descriptor, "dim": None}, dtype=np.float64)


def test_pointer_descriptor_view_policy_uses_decoded_descriptor_fields_for_strided_view():
    source = np.arange(10, dtype=np.float64)
    strided = source[1::2]
    state = _ArrayState(shape=strided.shape, value=strided)
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            **_common_ops(state),
            "to_numpy": lambda _handle: _pointer_descriptor_for_array(strided),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="descriptor_view",
    )

    view = handle.to_numpy()

    assert view is not strided
    assert np.shares_memory(view, source)
    assert view.strides == strided.strides
    np.testing.assert_allclose(view, strided)
    view[0] = 42.0
    assert source[1] == 42.0


def test_pointer_descriptor_view_policy_rejects_decoded_descriptor_rank_mismatch():
    source = np.arange(4, dtype=np.float64)
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=2,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: (2, 2),
            "to_numpy": lambda _handle: _pointer_descriptor_for_array(source),
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="descriptor_view",
    )

    with pytest.raises(ValueError, match="pointer descriptor rank 1 does not match declared handle rank 2"):
        handle.to_numpy()


def test_pointer_descriptor_view_policy_maps_null_decoded_descriptor_to_none():
    source = np.arange(4, dtype=np.float64)
    descriptor = {**_pointer_descriptor_for_array(source), "base_addr": 0}
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: None,
            "to_numpy": lambda _handle: descriptor,
            "associated": lambda _handle: False,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="descriptor_view",
    )

    assert handle.to_numpy() is None


def test_pointer_descriptor_view_policy_rejects_null_descriptor_for_present_state():
    source = np.arange(4, dtype=np.float64)
    descriptor = {**_pointer_descriptor_for_array(source), "base_addr": 0}
    handle = PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            **_required_handoff_ops(),
            "shape": lambda _handle: (4,),
            "to_numpy": lambda _handle: descriptor,
            "associated": lambda _handle: True,
            "nullify": lambda _handle: None,
        },
        to_numpy_policy="descriptor_view",
    )

    with pytest.raises(TypeError, match="null descriptor for present descriptor state"):
        handle.to_numpy()
