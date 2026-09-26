"""Runtime release, finalizer, and fail-closed construction of native handles.

These paths cannot be reached through a correct generated extension, or only
show up as a leak or a double free there, so they are driven with test doubles.
Observable handle behaviour is proved by the allocatable and pointer
end-to-end suites.
"""

import gc

import numpy as np
import pytest
from prik.runtime.handles import (
    AllocatableArray,
    PointerArray,
    _native_array_handle_from_generated_dispatch,
)
from tests.fortran._support.native_array_handles import (
    _generated_handle_dispatch,
    _handle_dispatch,
)


def _owned_allocatable(destroy):
    return AllocatableArray(
        dtype="float64",
        rank=1,
        **_handle_dispatch(
            {
                "shape": lambda _handle: (1,),
                "allocated": lambda _handle: True,
                "destroy": destroy,
            }
        ),
        descriptor_ownership="owned",
        to_numpy_policy="unsupported",
    )


@pytest.mark.parametrize("release", ["close_twice_then_collect", "finalizer_only"])
def test_owned_handle_destroys_its_descriptor_exactly_once(release: str):
    calls = []
    handle = _owned_allocatable(lambda _handle: calls.append("destroy"))

    if release == "close_twice_then_collect":
        assert handle.closed is False
        assert handle.close() is None
        assert handle.close() is None
        assert handle.closed is True
        with pytest.raises(ReferenceError, match="allocatable handle is closed"):
            _ = handle.shape
        with pytest.raises(ReferenceError, match="allocatable handle is closed"):
            handle.to_numpy()
    del handle
    gc.collect()

    assert calls == ["destroy"]


def test_owned_handle_close_marks_closed_when_destroy_raises():
    calls = []

    def destroy(_handle):
        calls.append("destroy")
        raise RuntimeError("boom")

    handle = _owned_allocatable(destroy)

    with pytest.raises(RuntimeError, match="boom"):
        handle.close()
    assert handle.closed is True
    assert handle.close() is None

    del handle
    gc.collect()

    assert calls == ["destroy"]


def test_generated_owned_handle_factory_releases_owner_once_when_construction_fails():
    calls = []
    owner = 0x1234

    def destroy(received_owner):
        calls.append(("destroy", received_owner))

    with pytest.raises(ValueError, match="requires generated operation 'allocated'"):
        operations = {
            "shape": lambda _owner: (1,),
            "destroy": destroy,
        }
        _native_array_handle_from_generated_dispatch(
            "allocatable",
            "float64",
            1,
            _generated_handle_dispatch(operations),
            operations,
            owner=owner,
            descriptor_ownership="owned",
            to_numpy_policy="unsupported",
        )

    gc.collect()
    assert calls == [("destroy", owner)]


@pytest.mark.parametrize("kind", ["allocatable", "pointer"])
def test_borrowed_handle_close_and_finalizer_do_not_destroy_native_storage(kind: str):
    calls = []
    owner = object()
    state_operation = {"allocatable": "allocated", "pointer": "associated"}[kind]
    handle_type = {"allocatable": AllocatableArray, "pointer": PointerArray}[kind]
    handle = handle_type(
        dtype="float64",
        rank=1,
        **_handle_dispatch(
            {
                "shape": lambda _handle: (1,),
                state_operation: lambda _handle: True,
                "nullify": lambda _handle: None,
                "destroy": lambda _handle: calls.append("destroy"),
            }
        ),
        owner=owner,
        to_numpy_policy="unsupported",
    )

    assert handle.close() is None
    assert handle.closed is False
    assert handle.owner is owner
    del handle
    gc.collect()

    assert calls == []


def _operations(*names):
    return {name: (lambda *_args: None) for name in names}


@pytest.mark.parametrize(
    ("construct", "message"),
    [
        pytest.param(
            lambda: AllocatableArray(
                dtype="float64",
                rank=1,
                **_handle_dispatch(_operations("shape", "allocated")),
                descriptor_ownership="owned",
                to_numpy_policy="unsupported",
            ),
            "owned native array handle requires generated operation 'destroy'",
            id="owned-without-destroy",
        ),
        pytest.param(
            lambda: AllocatableArray(dtype="float64", rank=1, **_handle_dispatch({})),
            "requires generated operation 'shape'",
            id="missing-shape",
        ),
        pytest.param(
            lambda: AllocatableArray(dtype="float64", rank=1, **_handle_dispatch(_operations("shape", "to_numpy"))),
            "requires generated operation 'allocated'",
            id="allocatable-without-allocated",
        ),
        pytest.param(
            lambda: PointerArray(dtype="float64", rank=1, **_handle_dispatch(_operations("shape", "associated"))),
            "requires generated operation 'nullify'",
            id="pointer-without-nullify",
        ),
        pytest.param(
            lambda: AllocatableArray(
                dtype="float64",
                rank=1,
                **_handle_dispatch(_operations("shape", "allocated")),
                to_numpy_policy="borrowed_view",
            ),
            "requires generated operation 'to_numpy'",
            id="view-policy-without-extraction",
        ),
        pytest.param(
            lambda: AllocatableArray(
                dtype="float64",
                rank=1,
                **_handle_dispatch(_operations("shape", "allocated")),
                descriptor_ownership="temporary",
            ),
            "descriptor_ownership must be 'borrowed' or 'owned'",
            id="unknown-ownership",
        ),
        pytest.param(
            lambda: AllocatableArray(
                dtype="float64",
                rank=1,
                **_handle_dispatch(_operations("shape", "allocated")),
                to_numpy_policy="maybe_copy",
            ),
            "to_numpy_policy must be one of",
            id="unknown-extraction-policy",
        ),
        pytest.param(
            lambda: _native_array_handle_from_generated_dispatch(
                "target",
                "float64",
                1,
                _generated_handle_dispatch({}),
                _operations("shape", "allocated", "to_numpy"),
            ),
            "generated native array handle kind",
            id="unknown-descriptor-kind",
        ),
    ],
)
def test_handle_construction_rejects_an_incomplete_generated_contract(construct, message: str):
    with pytest.raises(ValueError, match=message):
        construct()


@pytest.mark.parametrize(
    ("kind", "call", "operation"),
    [
        ("allocatable", lambda handle: handle.deallocate(), "deallocate"),
        ("allocatable", lambda handle: handle.resize(2), "resize"),
        ("pointer", lambda handle: handle.allocate((3,)), "allocate"),
        ("pointer", lambda handle: handle.deallocate(), "deallocate"),
        ("pointer", lambda handle: handle.resize((4,)), "resize"),
    ],
)
def test_operations_outside_the_completed_capabilities_are_refused(kind: str, call, operation: str):
    """A handle offers only what completed policy granted, e.g. no target release by default."""
    if kind == "allocatable":
        handle = AllocatableArray(
            dtype="float64",
            rank=1,
            **_handle_dispatch({"shape": lambda _handle: (1,), "allocated": lambda _handle: True}),
            to_numpy_policy="unsupported",
        )
    else:
        handle = PointerArray(
            dtype="float64",
            rank=1,
            **_handle_dispatch(
                {
                    "shape": lambda _handle: (1,),
                    "associated": lambda _handle: True,
                    "nullify": lambda _handle: None,
                }
            ),
            to_numpy_policy="unsupported",
        )

    with pytest.raises(NotImplementedError, match=f"{kind} handle operation '{operation}' is not available"):
        call(handle)


@pytest.mark.parametrize(
    ("shape", "result", "policy", "error", "message"),
    [
        pytest.param(
            (2,), [1.0, 2.0], "descriptor_view", TypeError, "must return a NumPy array or None", id="not-numpy"
        ),
        pytest.param(
            (2,),
            np.zeros((1, 2), dtype=np.float64),
            "descriptor_view",
            ValueError,
            "to_numpy result rank 2 does not match declared rank 1",
            id="wrong-rank",
        ),
        pytest.param(
            (2,), np.zeros(2, dtype=np.int32), "descriptor_view", TypeError, "to_numpy result dtype", id="wrong-dtype"
        ),
        pytest.param(
            (4,),
            np.arange(8, dtype=np.float64)[::2],
            "contiguous_view",
            ValueError,
            "must be contiguous",
            id="strided-under-contiguous-policy",
        ),
    ],
)
def test_generated_views_that_disagree_with_the_declared_handle_are_refused(shape, result, policy, error, message):
    """A view over native memory is only exposed when it matches what the handle declares."""
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        **_handle_dispatch(
            {
                "shape": lambda _handle: shape,
                "to_numpy": lambda _handle: result,
                "allocated": lambda _handle: True,
            }
        ),
        to_numpy_policy=policy,
    )

    with pytest.raises(error, match=message):
        handle.to_numpy()


def test_generated_shapes_are_validated_against_rank_and_sign():
    reported = {"shape": (-1,)}
    handle = AllocatableArray(
        dtype=np.dtype(np.float64),
        rank=1,
        **_handle_dispatch(
            {
                "shape": lambda _handle: reported["shape"],
                "allocated": lambda _handle: True,
                "resize": lambda _handle, _shape: None,
            }
        ),
        to_numpy_policy="unsupported",
    )

    with pytest.raises(ValueError, match="non-negative"):
        _ = handle.shape
    with pytest.raises(ValueError, match="non-negative"):
        handle.resize(-1)
    reported["shape"] = (4, 2)
    with pytest.raises(ValueError, match="shape rank 2 does not match declared rank 1"):
        _ = handle.shape
