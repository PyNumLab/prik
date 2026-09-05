"""Runtime helpers for native Fortran array descriptor handles."""

from __future__ import annotations

import ctypes
import operator
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

import numpy as np


HandleOperation = Callable[..., Any]
_PRESENT_NATIVE_ARRAY_DESCRIPTOR_ARGUMENT = ctypes.c_int(1)
_PRESENT_NATIVE_ARRAY_DESCRIPTOR_ARGUMENT_ADDRESS = ctypes.addressof(_PRESENT_NATIVE_ARRAY_DESCRIPTOR_ARGUMENT)

# The base a C-built descriptor starts from when no Fortran bound is available.
# Only a handle that reports its own descriptor can carry a declared lower
# bound; one reduced to a bare address has none to report.
_UNKNOWN_DESCRIPTOR_LOWER_BOUND = 0
# Returned when an extraction reports descriptor fields rather than a view, so
# the caller falls back to decoding them.
_EXTRACTION_UNAVAILABLE = object()


class _OwnerRetainedNDArray(np.ndarray):
    """Internal ndarray view carrying a strong reference to native owner state."""


def _retain_numpy_owner(value: np.ndarray, owner: Any) -> np.ndarray:
    """Return a zero-copy ndarray view that retains one Python owner object."""
    retained = value.view(_OwnerRetainedNDArray)
    retained._prik_owner = owner
    return retained


@dataclass(frozen=True)
class _NativeArrayHandoff:
    """Internal opaque native pointer handoff returned by generated handle ops."""

    address: int
    owner: Any = None

    def __post_init__(self) -> None:
        if isinstance(self.address, bool) or not isinstance(self.address, int):
            raise TypeError("native array handoff address must be an integer")
        if self.address <= 0:
            raise ValueError("native array handoff address must be a non-null positive pointer value")


@dataclass(frozen=True)
class _NativeArrayDescriptorHandoff:
    """Internal opaque handoff for one versioned native-handle capsule."""

    capsule: Any

    def __post_init__(self) -> None:
        if self.capsule is None:
            raise TypeError("native array descriptor handoff capsule is required")


def _numpy_view_from_pointer_c_descriptor(
    descriptor: Any,
    *,
    dtype: Any,
    expected_rank: int | None = None,
) -> np.ndarray | None:
    """Build a NumPy view from generated TS 29113 pointer descriptor fields."""
    base_addr = _pointer_descriptor_base_addr(descriptor)
    if base_addr == 0:
        return None
    array_dtype = np.dtype(dtype)
    _validate_pointer_descriptor_itemsize(descriptor, array_dtype)
    shape, strides = _pointer_descriptor_shape_and_strides(descriptor)
    if expected_rank is not None and len(shape) != int(expected_rank):
        raise ValueError(
            f"pointer descriptor rank {len(shape)} does not match declared handle rank {int(expected_rank)}"
        )
    buffer_offset, buffer_nbytes, view_offset = _descriptor_view_buffer_window(
        tuple(shape),
        tuple(strides),
        array_dtype.itemsize,
    )
    buffer_addr = base_addr + buffer_offset
    if buffer_addr < 0:
        raise ValueError("pointer descriptor view buffer starts before address zero")
    buffer_type = ctypes.c_char * buffer_nbytes
    buffer = buffer_type.from_address(buffer_addr)
    return np.ndarray(tuple(shape), dtype=array_dtype, buffer=buffer, strides=tuple(strides), offset=view_offset)


def _native_array_handle_from_generated_ops(
    descriptor_kind: str,
    dtype: Any,
    rank: int,
    ops: Mapping[str, HandleOperation],
    owner: Any = None,
    descriptor_ownership: str = "borrowed",
    to_numpy_policy: str = "borrowed_view",
    native_ops: Any = None,
    generation: int | None = None,
) -> NativeArrayHandleBase:
    """Build a runtime handle from generated operation callables.

    ``native_ops`` is an optional capsule publishing the entity's native entry
    points, so a binding can reach it with one indirect call.  It is carried,
    not required: a handle without one is placed through its operations.
    """
    owned = descriptor_ownership == "owned"
    normalized_ops = {}
    for name, operation in ops.items():
        if name == "descriptor" and owned:
            normalized = _generated_owned_descriptor_operation(operation, owner)
        elif name in {"shape", "to_numpy"} and owned:
            normalized = _generated_owned_descriptor_record_operation(operation, owner)
        elif name == "associate":
            normalized = _generated_pointer_associate_operation(
                operation,
                owner=owner if owned else None,
            )
        elif name in {"allocate", "resize"}:
            normalized = _generated_shape_operation(operation, owner=owner if owned else None)
        elif owned:
            normalized = _generated_owned_handle_operation(operation, owner)
        else:
            normalized = _generated_handle_operation(operation)
        normalized_ops[name] = normalized
    try:
        handle_cls = {
            "allocatable": AllocatableArray,
            "pointer": PointerArray,
        }[descriptor_kind]
    except KeyError:
        raise ValueError("generated native array handle kind must be 'allocatable' or 'pointer'") from None
    try:
        handle = handle_cls(
            dtype=dtype,
            rank=rank,
            ops=normalized_ops,
            owner=owner,
            descriptor_ownership=descriptor_ownership,
            to_numpy_policy=to_numpy_policy,
            generation=generation,
        )
        handle._native_ops = native_ops
        return handle
    except BaseException:
        if owned and "destroy" in normalized_ops:
            with suppress(Exception):
                normalized_ops["destroy"](None)
        raise


def _native_array_handle_from_contract(
    descriptor_kind: str,
    dtype: Any,
    rank: int,
) -> NativeArrayHandleBase:
    """Create one owned, initially empty descriptor handle from a contract."""
    descriptor_state = {
        "record": _empty_descriptor_record(dtype, rank),
        "owner": None,
    }

    def current_shape(_handle: NativeArrayHandleBase) -> tuple[int, ...] | None:
        record = descriptor_state["record"]
        if _pointer_descriptor_base_addr(record) == 0:
            return None
        shape, _strides = _pointer_descriptor_shape_and_strides(record)
        return shape

    def descriptor(_handle: NativeArrayHandleBase) -> Mapping[str, Any]:
        return descriptor_state["record"]

    def present(_handle: NativeArrayHandleBase) -> bool:
        return _pointer_descriptor_base_addr(descriptor_state["record"]) != 0

    def current_view(_handle: NativeArrayHandleBase) -> np.ndarray | None:
        return _numpy_view_from_pointer_c_descriptor(
            descriptor_state["record"],
            dtype=dtype,
            expected_rank=rank,
        )

    def clear(_handle: NativeArrayHandleBase) -> None:
        descriptor_state["record"] = _empty_descriptor_record(dtype, rank)
        descriptor_state["owner"] = None

    def associate_record(
        _handle: NativeArrayHandleBase,
        record: Mapping[str, Any],
        owner: NativeArrayHandleBase,
    ) -> None:
        descriptor_state["record"] = _copy_pointer_descriptor_record(record)
        descriptor_state["owner"] = owner

    common_ops = {
        "shape": current_shape,
        "descriptor": descriptor,
        "to_numpy": current_view,
        "destroy": clear,
    }
    try:
        handle_cls, descriptor_ops = {
            "allocatable": (AllocatableArray, {"allocated": present}),
            "pointer": (
                PointerArray,
                {
                    "associated": present,
                    "nullify": clear,
                    "_associate_record": associate_record,
                },
            ),
        }[descriptor_kind]
    except KeyError:
        raise ValueError("contract native array handle kind must be 'allocatable' or 'pointer'") from None
    handle = handle_cls(
        dtype=dtype,
        rank=rank,
        ops={**common_ops, **descriptor_ops},
        descriptor_ownership="owned",
        to_numpy_policy="borrowed_view",
    )
    handle._contract_default = True
    return handle


def _empty_descriptor_record(dtype: Any, rank: int) -> dict[str, Any]:
    """Return canonical unallocated or unassociated descriptor facts."""
    array_dtype = np.dtype(dtype)
    return {
        "base_addr": 0,
        "elem_len": array_dtype.itemsize,
        "rank": int(rank),
        "dim": [{"lower_bound": 0, "extent": 0, "sm": array_dtype.itemsize} for _axis in range(int(rank))],
    }


def _copy_pointer_descriptor_record(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    """Copy validated standard descriptor facts for independent association state."""
    dimensions = _pointer_descriptor_dimensions(descriptor)
    return {
        "base_addr": _required_descriptor_int(descriptor, "base_addr"),
        "elem_len": _required_descriptor_int(descriptor, "elem_len"),
        "rank": _required_descriptor_int(descriptor, "rank"),
        "dim": [
            {
                "lower_bound": _required_descriptor_int(dimension, "lower_bound", field_owner=f"dim[{index}]"),
                "extent": _required_descriptor_int(dimension, "extent", field_owner=f"dim[{index}]"),
                "sm": _required_descriptor_int(dimension, "sm", field_owner=f"dim[{index}]"),
            }
            for index, dimension in enumerate(dimensions)
        ],
    }


def _pointer_descriptor_record_facts(descriptor: Mapping[str, Any]) -> tuple[int, ...]:
    """Flatten standard descriptor facts for one generated association operation."""
    record = _copy_pointer_descriptor_record(descriptor)
    fields = [
        record["base_addr"],
        record["elem_len"],
        record["rank"],
    ]
    for dimension in record["dim"]:
        fields.extend(
            (
                dimension["lower_bound"],
                dimension["extent"],
                dimension["sm"],
            )
        )
    return tuple(fields)


def _bind_contract_native_array_handle(
    handle: NativeArrayHandleBase,
    descriptor_kind: str,
    dtype: Any,
    rank: int,
    ops: Mapping[str, HandleOperation],
    owner: Any,
    descriptor_ownership: str,
    to_numpy_policy: str | None,
    generation: int | None = None,
    native_ops: Any = None,
) -> None:
    """Attach generated persistent descriptor storage to a contract handle.

    ``to_numpy_policy`` is ``None`` when the argument that supplied the storage
    does not project a result.  Such an argument gives the handle a descriptor
    to hand over, but it does not define what the handle exposes, so the
    handle keeps the exposure it was created with.

    ``native_ops`` is the entry-point table for the attached storage, which
    subsequent calls read directly from C.
    """
    if not isinstance(handle, NativeArrayHandleBase) or not handle._contract_default:
        raise TypeError("generated descriptor storage can attach only to a fresh contract handle")
    if handle.closed:
        raise ReferenceError(f"{handle.descriptor_kind} handle is closed")
    if handle.descriptor_kind != descriptor_kind:
        raise TypeError(f"cannot attach {descriptor_kind} descriptor storage to {handle.descriptor_kind} handle")
    if handle.rank != int(rank):
        raise ValueError(f"{descriptor_kind} handle rank {handle.rank} does not match generated rank {int(rank)}")
    if not handle._dtype_matches(dtype):
        raise TypeError(f"{descriptor_kind} handle dtype {handle.dtype!r} does not match generated dtype {dtype!r}")
    pending_pointer_descriptor = (
        handle._association_descriptor_record() if isinstance(handle, PointerArray) and handle.associated else None
    )
    generated = _native_array_handle_from_generated_ops(
        descriptor_kind,
        dtype,
        rank,
        ops,
        owner=owner,
        descriptor_ownership=descriptor_ownership,
        to_numpy_policy=handle._to_numpy_policy if to_numpy_policy is None else to_numpy_policy,
        generation=generation,
    )
    handle._ops = generated._ops
    handle._owner = generated._owner
    handle._descriptor_ownership = generated._descriptor_ownership
    handle._to_numpy_policy = generated._to_numpy_policy
    handle._generation = generated._generation
    # The storage just attached is the wrapper's own and lives as long as the
    # handle, so the handle can publish it the way a module array publishes
    # its entity.  Later calls then reach it from C without coming back here.
    handle._native_ops = native_ops
    handle._contract_default = False
    generated._closed = True
    if pending_pointer_descriptor is not None:
        handle._call_op("associate", pending_pointer_descriptor)


def _generated_handle_operation(operation: HandleOperation) -> HandleOperation:
    """Adapt a generated operation callable to the handle operation protocol."""

    def call(_handle: NativeArrayHandleBase, *args: Any) -> Any:
        return operation(*args)

    return call


def _generated_owned_handle_operation(operation: HandleOperation, owner: Any) -> HandleOperation:
    """Adapt an operation whose first argument is persistent native owner storage."""

    def call(_handle: NativeArrayHandleBase, *args: Any) -> Any:
        return operation(owner, *args)

    return call


def _generated_owned_descriptor_operation(operation: HandleOperation, owner: Any) -> HandleOperation:
    """Adapt an owned standard-descriptor pointer operation to typed handoff."""

    def call(_handle: NativeArrayHandleBase, *args: Any) -> _NativeArrayDescriptorHandoff:
        value = operation(owner, *args)
        return _native_array_descriptor_handoff_from_generated_result(value, owner=owner)

    return call


def _generated_owned_descriptor_record_operation(operation: HandleOperation, owner: Any) -> HandleOperation:
    """Adapt owned descriptor facts and normalize compiler zero-extent sentinels."""

    def call(_handle: NativeArrayHandleBase, *args: Any) -> Any:
        value = operation(owner, *args)
        if not isinstance(value, Mapping):
            return value
        dimensions = value.get("dim")
        if not isinstance(dimensions, Sequence):
            return value
        normalized_dimensions = []
        for dimension in dimensions:
            if not isinstance(dimension, Mapping) or dimension.get("extent") != -1:
                normalized_dimensions.append(dimension)
                continue
            normalized_dimensions.append({**dimension, "extent": 0})
        return {**value, "dim": normalized_dimensions}

    return call


def _generated_pointer_associate_operation(
    operation: HandleOperation,
    *,
    owner: Any = None,
) -> HandleOperation:
    """Adapt pointer association to one generated standard-descriptor operation."""

    def call(_handle: NativeArrayHandleBase, descriptor: Mapping[str, Any]) -> Any:
        facts = _pointer_descriptor_record_facts(descriptor)
        if owner is None:
            return operation(facts)
        return operation(owner, facts)

    return call


def _generated_shape_operation(operation: HandleOperation, *, owner: Any = None) -> HandleOperation:
    """Adapt generated shape operations from one runtime shape tuple to scalar extents."""

    def call(_handle: NativeArrayHandleBase, shape: Sequence[int]) -> Any:
        extents = tuple(np.int64(extent) for extent in shape)
        return operation(*extents) if owner is None else operation(owner, *extents)

    return call


def _native_array_descriptor_handoff_from_generated_result(
    value: Any,
    *,
    owner: Any = None,
) -> _NativeArrayDescriptorHandoff:
    """Normalize a generated native-handle capsule into a typed handoff."""
    if isinstance(value, _NativeArrayDescriptorHandoff):
        return value
    if owner is None:
        raise TypeError("generated native array descriptor handoff requires an owner capsule")
    if value is not owner:
        raise TypeError("generated native array descriptor operation must return its owner capsule")
    return _NativeArrayDescriptorHandoff(owner)


def _pointer_descriptor_base_addr(descriptor: Any) -> int:
    base_addr = _required_descriptor_int(descriptor, "base_addr")
    if base_addr < 0:
        raise ValueError(f"pointer descriptor base_addr must be non-negative; received {base_addr}")
    return base_addr


def _validate_pointer_descriptor_itemsize(descriptor: Any, array_dtype: np.dtype) -> None:
    elem_len = _required_descriptor_int(descriptor, "elem_len")
    if elem_len != array_dtype.itemsize:
        raise ValueError(
            f"pointer descriptor elem_len {elem_len} does not match NumPy dtype itemsize {array_dtype.itemsize}"
        )


def _pointer_descriptor_shape_and_strides(descriptor: Any) -> tuple[list[int], list[int]]:
    dimensions = _pointer_descriptor_dimensions(descriptor)
    shape: list[int] = []
    strides: list[int] = []
    for index, dimension in enumerate(dimensions):
        extent, stride = _pointer_descriptor_dimension_extent_stride(index, dimension)
        shape.append(extent)
        strides.append(stride)
    return shape, strides


def _pointer_descriptor_dimensions(descriptor: Any) -> Sequence[Any]:
    rank = _pointer_descriptor_rank(descriptor)
    dimensions = _required_descriptor_field(descriptor, "dim")
    if not isinstance(dimensions, Sequence) or isinstance(dimensions, (str, bytes)):
        raise TypeError("pointer descriptor field 'dim' must be a sequence of dimension records")
    if rank != len(dimensions):
        raise ValueError(f"pointer descriptor rank {rank} does not match {len(dimensions)} dimension records")
    return dimensions


def _pointer_descriptor_rank(descriptor: Any) -> int:
    rank = _required_descriptor_int(descriptor, "rank")
    if rank < 0:
        raise ValueError(f"pointer descriptor rank must be non-negative; received {rank}")
    return rank


def _pointer_descriptor_dimension_extent_stride(index: int, dimension: Any) -> tuple[int, int]:
    if not _is_pointer_descriptor_dimension_record(dimension):
        raise TypeError(f"pointer descriptor dimension {index} must be a mapping or field-record object")
    _required_descriptor_int(dimension, "lower_bound", field_owner=f"dim[{index}]")
    extent = _required_descriptor_int(dimension, "extent", field_owner=f"dim[{index}]")
    stride = _required_descriptor_int(dimension, "sm", field_owner=f"dim[{index}]")
    if extent < 0:
        raise ValueError(f"pointer descriptor dim[{index}].extent must be non-negative; received {extent}")
    return extent, stride


def _required_descriptor_int(
    descriptor: Any,
    field: str,
    *,
    field_owner: str = "descriptor",
) -> int:
    value = _required_descriptor_field(descriptor, field, field_owner=field_owner)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"pointer {field_owner} field {field!r} must be an integer")
    return value


def _required_descriptor_field(
    record: Any,
    field: str,
    *,
    field_owner: str = "descriptor",
) -> Any:
    if isinstance(record, Mapping):
        try:
            return record[field]
        except KeyError:
            pass
    else:
        missing = object()
        value = getattr(record, field, missing)
        if value is not missing:
            return value
    raise TypeError(f"pointer {field_owner} field {field!r} is required")


def _is_pointer_descriptor_record(value: Any) -> bool:
    fields = ("base_addr", "elem_len", "rank", "dim")
    return isinstance(value, Mapping) or all(hasattr(value, field) for field in fields)


def _is_pointer_descriptor_dimension_record(value: Any) -> bool:
    fields = ("lower_bound", "extent", "sm")
    return isinstance(value, Mapping) or all(hasattr(value, field) for field in fields)


def _descriptor_view_buffer_window(
    shape: tuple[int, ...],
    strides: tuple[int, ...],
    itemsize: int,
) -> tuple[int, int, int]:
    if not shape:
        return 0, itemsize, 0
    if any(extent == 0 for extent in shape):
        return 0, 0, 0
    axis_offsets = [(extent - 1) * stride for extent, stride in zip(shape, strides, strict=True)]
    min_offset = sum(min(0, offset) for offset in axis_offsets)
    max_offset = sum(max(0, offset) for offset in axis_offsets)
    return min_offset, max_offset - min_offset + itemsize, -min_offset


class NativeArrayHandleBase:
    """Shared runtime state and operation dispatch for native array handles."""

    _REQUIRED_DESCRIPTOR_OPS: frozenset[str] = frozenset()
    _VALID_DESCRIPTOR_KINDS = frozenset({"allocatable", "pointer"})
    _VALID_DESCRIPTOR_OWNERSHIP = frozenset({"borrowed", "owned"})
    _VALID_TO_NUMPY_POLICIES = frozenset(
        {
            "borrowed_view",
            "contiguous_view",
            "descriptor_view",
            "unsupported",
        }
    )

    def __init__(
        self,
        *,
        dtype: Any,
        rank: int,
        ops: Mapping[str, HandleOperation],
        owner: Any = None,
        descriptor_kind: str,
        descriptor_ownership: str,
        to_numpy_policy: str = "borrowed_view",
        generation: int | None = None,
    ) -> None:
        self._closed = True
        if rank < 0:
            raise ValueError("native array handle rank must be non-negative")
        if descriptor_kind not in self._VALID_DESCRIPTOR_KINDS:
            raise ValueError("native array handle descriptor_kind must be 'allocatable' or 'pointer'")
        if descriptor_ownership not in self._VALID_DESCRIPTOR_OWNERSHIP:
            raise ValueError("native array handle descriptor_ownership must be 'borrowed' or 'owned'")
        if to_numpy_policy not in self._VALID_TO_NUMPY_POLICIES:
            raise ValueError(
                f"native array handle to_numpy_policy must be one of {sorted(self._VALID_TO_NUMPY_POLICIES)!r}"
            )
        self._dtype = None if dtype is None else np.dtype(dtype)
        self._rank = int(rank)
        self._ops = self._normalize_ops(ops)
        self._owner = owner
        self._descriptor_kind = descriptor_kind
        self._descriptor_ownership = descriptor_ownership
        self._to_numpy_policy = to_numpy_policy
        self._generation = generation
        # Holds the most recent borrowed descriptor copy so it outlives the call
        # that reads it; see _generated_borrowed_descriptor_operation.
        self._borrowed_descriptor: Any = None
        # Optional capsule publishing this entity's native entry points.
        self._native_ops: Any = None
        self._contract_default = False
        self._validate_required_ops()
        self._closed = False

    @property
    def dtype(self) -> np.dtype:
        if self._dtype is not None:
            return self._dtype
        return self._deferred_character_dtype()

    def _deferred_character_dtype(self) -> np.dtype:
        """Resolve one deferred character width from generated native state."""
        if "element_length" in self._ops:
            length = operator.index(self._call_op("element_length"))
            if length < 0:
                raise ValueError("native character array element length must be non-negative")
            return np.dtype(f"S{length}")
        value = self._call_op("to_numpy")
        if isinstance(value, np.ndarray) and value.dtype.kind == "S":
            return value.dtype
        if _is_pointer_descriptor_record(value):
            length = _required_descriptor_int(value, "elem_len")
            if length < 0:
                raise ValueError("native character array element length must be non-negative")
            return np.dtype(f"S{length}")
        raise TypeError("deferred character handle cannot resolve its runtime element length")

    @property
    def _reads_its_own_descriptor(self) -> bool:
        """Report whether this handle's inquiries read a descriptor it owns.

        A generated handle over wrapper-owned storage answers from the
        descriptor in front of it, absence included.  A borrowed one reaches
        its entity through the compiler's own inquiries, which say nothing
        about whether the entity is there, and a handle built from supplied
        operations makes no promise at all.
        """
        return self._native_ops is not None and self._descriptor_ownership == "owned"

    @property
    def rank(self) -> int:
        return self._rank

    @property
    def shape(self) -> tuple[int, ...] | None:
        if self._reads_its_own_descriptor:
            # The generated inquiry reads the descriptor, so it reports absent
            # storage as None instead of being asked about it first, and the
            # extents it returns are the compiler's own.
            if self.closed:
                raise ReferenceError(f"{self.descriptor_kind} handle is closed")
            extents = self._ops["shape"](self)
            if extents is None:
                return None
            if _is_pointer_descriptor_record(extents):
                # A deferred character inquiry reports fields, not extents.
                shape, _strides = _pointer_descriptor_shape_and_strides(extents)
                return self._normalize_shape(shape)
            return extents
        if self._to_numpy_absent_state():
            return None
        shape = self._call_op("shape")
        if shape is None:
            return None
        if _is_pointer_descriptor_record(shape):
            shape, _strides = _pointer_descriptor_shape_and_strides(shape)
        normalized = self._normalize_shape(shape)
        if len(normalized) != self.rank:
            raise ValueError(
                f"{self.descriptor_kind} handle shape rank {len(normalized)} does not match declared rank {self.rank}"
            )
        return normalized

    @property
    def owner(self) -> Any:
        return self._owner

    @property
    def descriptor_kind(self) -> str:
        return self._descriptor_kind

    @property
    def descriptor_ownership(self) -> str:
        return self._descriptor_ownership

    @property
    def to_numpy_policy(self) -> str:
        return self._to_numpy_policy

    @property
    def borrowed(self) -> bool:
        return self.descriptor_ownership == "borrowed"

    @property
    def owned(self) -> bool:
        return self.descriptor_ownership == "owned"

    @property
    def generation(self) -> int | None:
        return self._generation

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> Any:
        """Release generated owner storage for an owned native descriptor handle."""
        if self.closed or not self.owned:
            return None
        operation = self._ops["destroy"]
        try:
            return operation(self)
        finally:
            self._closed = True
            self._owner = None
            self._ops = {}

    def __del__(self) -> None:
        with suppress(Exception):
            self.close()

    def _descriptor_for_binding(
        self,
        *,
        expected_dtype: Any = None,
        expected_rank: int | None = None,
        expected_shape: Sequence[int | None] | int | None = None,
    ) -> Any:
        """Return the generated native descriptor after validating handle metadata."""
        if expected_rank is not None and self.rank != int(expected_rank):
            raise ValueError(
                f"{self.descriptor_kind} handle rank {self.rank} does not match expected rank {int(expected_rank)}"
            )
        if expected_dtype is not None and not self._dtype_matches(expected_dtype):
            raise TypeError(
                f"{self.descriptor_kind} handle dtype {self.dtype!r} does not match expected dtype {expected_dtype!r}"
            )
        # Reading the shape is also the gate that rejects nonsense extents
        # before any descriptor reaches native code, so it is not conditional
        # on the dummy constraining a shape.
        shape = self.shape
        if shape is not None:
            self._validate_expected_shape(shape, expected_shape)
        descriptor = self._call_op("descriptor")
        if isinstance(descriptor, _NativeArrayDescriptorHandoff):
            return descriptor
        if _is_pointer_descriptor_record(descriptor):
            if _pointer_descriptor_base_addr(descriptor) == 0:
                return self._absent_descriptor_record()
            _validate_pointer_descriptor_itemsize(descriptor, np.dtype(self.dtype))
            descriptor_shape, _ = _pointer_descriptor_shape_and_strides(descriptor)
            if len(descriptor_shape) != self.rank:
                raise ValueError(
                    f"{self.descriptor_kind} descriptor rank {len(descriptor_shape)} "
                    f"does not match declared rank {self.rank}"
                )
            return descriptor
        address = descriptor.address if isinstance(descriptor, _NativeArrayHandoff) else descriptor
        if isinstance(address, ctypes.c_void_p):
            address = address.value or 0
        if isinstance(address, bool) or not isinstance(address, int):
            raise TypeError(
                f"{self.descriptor_kind} handle descriptor operation must return descriptor fields "
                f"or an integer data address; received {type(descriptor).__name__}"
            )
        return self._contiguous_descriptor_record(address, shape)

    def _descriptor_record_for_binding(self) -> Any:
        """Return standard descriptor fields for a fact-packed descriptor call."""
        descriptor = self._call_op("to_numpy")
        if not _is_pointer_descriptor_record(descriptor):
            raise TypeError(
                f"{self.descriptor_kind} handle cannot expose standard descriptor fields for binding handoff"
            )
        return descriptor

    def _absent_descriptor_record(self) -> dict[str, Any]:
        """Return descriptor fields for storage that is not there.

        Every axis is empty, so the bounds describe nothing and no value is
        being asserted about an array that does not exist.
        """
        dtype = np.dtype(self.dtype)
        return {
            "base_addr": 0,
            "elem_len": dtype.itemsize,
            "rank": self.rank,
            "dim": [{"lower_bound": 0, "extent": 0, "sm": dtype.itemsize} for _axis in range(self.rank)],
        }

    def _contiguous_descriptor_record(self, address: int, shape: tuple[int, ...] | None) -> dict[str, Any]:
        """Build standard descriptor fields for a contiguous native array actual.

        A bare address carries no bounds, so every axis is described from the
        zero base a C-built descriptor starts at rather than from a Fortran
        bound this cannot know.  A handle that can name its bounds -- any that
        reports its own descriptor -- must do so through its descriptor
        operation, which is where a declared lower bound survives; generated
        module handles all take that route, so nothing prik emits relies on the
        base chosen here.
        """
        dtype = np.dtype(self.dtype)
        extents = (0,) * self.rank if shape is None else shape
        strides = []
        stride = dtype.itemsize
        for extent in extents:
            strides.append(stride)
            stride *= max(int(extent), 1)
        return {
            "base_addr": int(address),
            "elem_len": dtype.itemsize,
            "rank": self.rank,
            "dim": [
                {"lower_bound": _UNKNOWN_DESCRIPTOR_LOWER_BOUND, "extent": int(extent), "sm": int(axis_stride)}
                for extent, axis_stride in zip(extents, strides, strict=True)
            ],
        }

    def to_numpy(self) -> Any:
        """Return a live view of current native storage, or ``None``."""
        policy = self._to_numpy_policy
        if self._reads_its_own_descriptor and policy != "unsupported":
            extracted = self._own_descriptor_view(policy)
            if extracted is not _EXTRACTION_UNAVAILABLE:
                return extracted
        if self._to_numpy_absent_state():
            return None
        if policy == "unsupported":
            raise NotImplementedError(
                f"{self.descriptor_kind} handle to_numpy extraction is unsupported by completed policy"
            )
        if policy == "contiguous_view" and "contiguous" in self._ops and not bool(self._call_op("contiguous")):
            raise ValueError(f"{self.descriptor_kind} handle to_numpy target must be contiguous")
        value = self._call_op("to_numpy")
        if value is None:
            raise TypeError(
                f"{self.descriptor_kind} handle to_numpy operation returned None for present descriptor state"
            )
        # A generated operation builds the view itself; only an operation that
        # reports descriptor fields needs decoding here.
        if not isinstance(value, np.ndarray) and _is_pointer_descriptor_record(value):
            value = _numpy_view_from_pointer_c_descriptor(value, dtype=self.dtype, expected_rank=self.rank)
            if value is None:
                raise TypeError(
                    f"{self.descriptor_kind} handle extraction returned a null descriptor for present descriptor state"
                )
            value = _retain_numpy_owner(value, self)
        elif isinstance(value, np.ndarray) and value.base is not None and value.base is self._owner:
            # A generated operation builds its view over the storage the owner
            # record holds, and this handle releases that storage when it is
            # finalized, so the view has to keep the handle alive too.  An
            # operation returning an array of its own owns its memory already
            # and is handed back untouched.
            value = _retain_numpy_owner(value, self)
        self._validate_numpy_result(value)
        if policy == "contiguous_view":
            self._validate_contiguous_numpy_result(value)
        return value

    def _own_descriptor_view(self, policy: str) -> Any:
        """Return the view a generated extraction builds over owned storage.

        The extraction reads the descriptor itself, so it reports an absent
        state as None rather than needing to be asked first, and what it
        returns was built from the declared type, so a second check of the
        result adds nothing.  An extraction that reports fields instead is not
        one of these, and says so by returning the unavailable sentinel.
        """
        if self.closed:
            raise ReferenceError(f"{self.descriptor_kind} handle is closed")
        value = self._ops["to_numpy"](self)
        if value is None:
            return None
        if not isinstance(value, np.ndarray):
            return _EXTRACTION_UNAVAILABLE
        if value.base is not None and value.base is self._owner:
            value = _retain_numpy_owner(value, self)
        if policy == "contiguous_view":
            self._validate_contiguous_numpy_result(value)
        return value

    def _call_op(self, name: str, *args: Any) -> Any:
        if self.closed:
            raise ReferenceError(f"{self.descriptor_kind} handle is closed")
        try:
            operation = self._ops[name]
        except KeyError:
            raise NotImplementedError(f"{self.descriptor_kind} handle operation {name!r} is not available") from None
        return operation(self, *args)

    def _to_numpy_absent_state(self) -> bool:
        """Return whether descriptor state makes extraction produce ``None``."""
        return False

    def _validate_numpy_result(self, value: Any) -> None:
        if not isinstance(value, np.ndarray):
            raise TypeError(
                f"{self.descriptor_kind} handle to_numpy operation must return a NumPy array or None; "
                f"received {type(value).__name__}"
            )
        if value.ndim != self.rank:
            raise ValueError(
                f"{self.descriptor_kind} handle to_numpy result rank {value.ndim} does not match declared "
                f"rank {self.rank}"
            )
        if not self._dtype_matches(value.dtype):
            raise TypeError(
                f"{self.descriptor_kind} handle to_numpy result dtype {value.dtype!r} does not match declared "
                f"dtype {self.dtype!r}"
            )

    def _validate_contiguous_numpy_result(self, value: np.ndarray) -> None:
        if not (value.flags.c_contiguous or value.flags.f_contiguous):
            raise ValueError(f"{self.descriptor_kind} handle to_numpy result must be contiguous")

    def _dtype_matches(self, expected_dtype: Any) -> bool:
        try:
            return np.dtype(self.dtype) == np.dtype(expected_dtype)
        except TypeError:
            return self.dtype == expected_dtype

    def _validate_expected_shape(
        self,
        shape: tuple[int, ...],
        expected_shape: Sequence[int | None] | int | None,
    ) -> None:
        """Validate a concrete expected shape before native array-actual handoff."""
        if expected_shape is None:
            return
        expected = self._normalize_expected_shape(expected_shape)
        if len(expected) != len(shape):
            raise ValueError(
                f"{self.descriptor_kind} handle shape rank {len(shape)} does not match expected shape rank "
                f"{len(expected)}"
            )
        for axis, (actual, wanted) in enumerate(zip(shape, expected, strict=True)):
            if wanted is not None and actual != wanted:
                raise ValueError(
                    f"{self.descriptor_kind} handle shape {shape!r} does not match expected shape "
                    f"{expected!r} at axis {axis}"
                )

    def _validate_required_ops(self) -> None:
        if "shape" not in self._ops:
            raise ValueError(f"{self.descriptor_kind} native array handle requires generated operation 'shape'")
        if "descriptor" not in self._ops:
            raise ValueError(f"{self.descriptor_kind} native array handle requires generated operation 'descriptor'")
        for name in sorted(self._REQUIRED_DESCRIPTOR_OPS):
            if name not in self._ops:
                raise ValueError(f"{self.descriptor_kind} native array handle requires generated operation {name!r}")
        if self.to_numpy_policy != "unsupported" and "to_numpy" not in self._ops:
            raise ValueError(
                f"{self.descriptor_kind} native array handle with to_numpy_policy "
                f"{self.to_numpy_policy!r} requires generated operation 'to_numpy'"
            )
        if self.owned and "destroy" not in self._ops:
            raise ValueError(f"{self.descriptor_kind} owned native array handle requires generated operation 'destroy'")

    @staticmethod
    def _normalize_ops(ops: Mapping[str, HandleOperation]) -> dict[str, HandleOperation]:
        normalized = dict(ops)
        for name, operation in normalized.items():
            if not isinstance(name, str):
                raise TypeError(f"native array handle operation names must be strings; received {type(name).__name__}")
            if not callable(operation):
                raise TypeError(
                    f"native array handle operation {name!r} must be callable; received {type(operation).__name__}"
                )
        return normalized

    @staticmethod
    def _normalize_shape(shape: Sequence[int] | int) -> tuple[int, ...]:
        try:
            normalized = (operator.index(shape),)
        except TypeError:
            normalized = tuple(operator.index(dimension) for dimension in shape)
        for dimension in normalized:
            if dimension < 0:
                raise ValueError(f"native array handle shape dimensions must be non-negative; received {normalized!r}")
        return normalized

    @staticmethod
    def _normalize_expected_shape(shape: Sequence[int | None] | int) -> tuple[int | None, ...]:
        try:
            normalized = (operator.index(shape),)
        except TypeError:
            normalized = tuple(None if dimension is None else int(dimension) for dimension in shape)
        for dimension in normalized:
            if dimension is not None and dimension < 0:
                raise ValueError(
                    f"expected native array shape dimensions must be non-negative; received {normalized!r}"
                )
        return normalized


class AllocatableArray(NativeArrayHandleBase):
    """Runtime handle for a native allocatable array descriptor."""

    _REQUIRED_DESCRIPTOR_OPS = frozenset({"allocated"})

    def __init__(
        self,
        *,
        dtype: Any,
        rank: int,
        ops: Mapping[str, HandleOperation],
        owner: Any = None,
        descriptor_ownership: str = "borrowed",
        to_numpy_policy: str = "borrowed_view",
        generation: int | None = None,
    ) -> None:
        super().__init__(
            dtype=dtype,
            rank=rank,
            ops=ops,
            owner=owner,
            descriptor_kind="allocatable",
            descriptor_ownership=descriptor_ownership,
            to_numpy_policy=to_numpy_policy,
            generation=generation,
        )

    @property
    def allocated(self) -> bool:
        return bool(self._call_op("allocated"))

    def _to_numpy_absent_state(self) -> bool:
        return not self.allocated

    def deallocate(self) -> Any:
        return self._call_op("deallocate")

    def resize(self, shape: Sequence[int] | int) -> Any:
        return self._call_op("resize", self._normalize_shape(shape))


class PointerArray(NativeArrayHandleBase):
    """Runtime handle for a native pointer array descriptor."""

    _REQUIRED_DESCRIPTOR_OPS = frozenset({"associated", "nullify"})

    def __init__(
        self,
        *,
        dtype: Any,
        rank: int,
        ops: Mapping[str, HandleOperation],
        owner: Any = None,
        descriptor_ownership: str = "borrowed",
        to_numpy_policy: str = "borrowed_view",
        generation: int | None = None,
    ) -> None:
        super().__init__(
            dtype=dtype,
            rank=rank,
            ops=ops,
            owner=owner,
            descriptor_kind="pointer",
            descriptor_ownership=descriptor_ownership,
            to_numpy_policy=to_numpy_policy,
            generation=generation,
        )

    @property
    def associated(self) -> bool:
        return bool(self._call_op("associated"))

    def _to_numpy_absent_state(self) -> bool:
        return not self.associated

    def _association_descriptor_record(self) -> dict[str, Any]:
        """Return independent standard descriptor facts for pointer assignment."""
        descriptor = self._descriptor_for_binding(
            expected_dtype=self.dtype,
            expected_rank=self.rank,
        )
        if isinstance(descriptor, _NativeArrayDescriptorHandoff):
            descriptor = self._descriptor_record_for_binding()
        record = _copy_pointer_descriptor_record(descriptor)
        _validate_pointer_descriptor_itemsize(record, self.dtype)
        return record

    def associate(self, other: PointerArray) -> Any:
        """Make this pointer's association match another pointer handle."""
        if self.closed:
            raise ReferenceError("pointer handle is closed")
        if not isinstance(other, PointerArray):
            raise TypeError(f"pointer association requires another PointerArray; received {type(other).__name__}")
        if other.closed:
            raise ReferenceError("source pointer handle is closed")
        if self.rank != other.rank:
            raise ValueError(f"pointer handle rank {self.rank} does not match source rank {other.rank}")
        if not self._dtype_matches(other.dtype):
            raise TypeError(f"pointer handle dtype {self.dtype!r} does not match source dtype {other.dtype!r}")
        descriptor = other._association_descriptor_record()
        if self._contract_default:
            return self._call_op("_associate_record", descriptor, other)
        return self._call_op("associate", descriptor)

    def nullify(self) -> Any:
        return self._call_op("nullify")

    def allocate(self, shape: Sequence[int] | int) -> Any:
        return self._call_op("allocate", self._normalize_shape(shape))

    def deallocate(self) -> Any:
        return self._call_op("deallocate")

    def resize(self, shape: Sequence[int] | int) -> Any:
        return self._call_op("resize", self._normalize_shape(shape))


def _native_array_descriptor_for_binding(
    value: Any,
    *,
    descriptor_kind: str,
    expected_dtype: Any = None,
    expected_rank: int | None = None,
    expected_shape: Sequence[int | None] | int | None = None,
    optional: bool = False,
) -> Any:
    """Return a generated native descriptor for a handle-typed binding argument."""
    try:
        expected_type = {
            "allocatable": AllocatableArray,
            "pointer": PointerArray,
        }[descriptor_kind]
    except KeyError:
        raise ValueError(f"unsupported native array descriptor kind: {descriptor_kind!r}") from None
    if value is None:
        if optional:
            return None
        raise TypeError(f"{descriptor_kind} native array handle argument is required; received None")
    if not isinstance(value, expected_type):
        raise TypeError(f"expected {descriptor_kind} native array handle argument; received {type(value).__name__}")
    return value._descriptor_for_binding(
        expected_dtype=expected_dtype,
        expected_rank=expected_rank,
        expected_shape=expected_shape,
    )


def _native_array_descriptor_handoff_for_binding(
    value: Any,
    *,
    descriptor_kind: str,
    expected_dtype: Any = None,
    expected_rank: int | None = None,
    expected_shape: Sequence[int | None] | int | None = None,
    optional_absent: bool = False,
    bind_default: HandleOperation | None = None,
) -> tuple[Any | None, ...]:
    """Pack a versioned native-handle capsule for a descriptor argument."""
    if isinstance(value, NativeArrayHandleBase) and value._contract_default:
        if bind_default is None:
            raise TypeError(
                f"writable {descriptor_kind} contract handle requires generated persistent descriptor storage"
            )
        _native_array_descriptor_for_binding(
            value,
            descriptor_kind=descriptor_kind,
            expected_dtype=expected_dtype,
            expected_rank=expected_rank,
            expected_shape=expected_shape,
            optional=optional_absent,
        )
        bind_default(value)
    descriptor = _native_array_descriptor_for_binding(
        value,
        descriptor_kind=descriptor_kind,
        expected_dtype=expected_dtype,
        expected_rank=expected_rank,
        expected_shape=expected_shape,
        optional=optional_absent,
    )
    if descriptor is None:
        return (None, None) if optional_absent else (None,)
    if not isinstance(descriptor, _NativeArrayDescriptorHandoff):
        raise TypeError(
            f"writable {descriptor_kind} descriptor argument requires a generated direct descriptor handoff"
        )
    if optional_absent:
        return descriptor.capsule, _PRESENT_NATIVE_ARRAY_DESCRIPTOR_ARGUMENT_ADDRESS
    return (descriptor.capsule,)


def _native_array_descriptor_handoff_for_binding_positional(
    value: Any,
    descriptor_kind: str,
    expected_dtype: Any = None,
    expected_rank: int | None = None,
    expected_shape: Sequence[int | None] | int | None = None,
    optional_absent: bool = False,
    bind_default: HandleOperation | None = None,
) -> tuple[Any | None, ...]:
    """Positional wrapper used by projected-handle CPython binding code."""
    return _native_array_descriptor_handoff_for_binding(
        value,
        descriptor_kind=str(descriptor_kind),
        expected_dtype=None if expected_dtype is None else np.dtype(expected_dtype),
        expected_rank=None if expected_rank is None else int(expected_rank),
        expected_shape=expected_shape,
        optional_absent=bool(optional_absent),
        bind_default=bind_default,
    )


__all__ = (
    "AllocatableArray",
    "NativeArrayHandleBase",
    "PointerArray",
)


if __name__ == "__main__":
    # Generated extensions supply small operation dictionaries like this one.
    # The adapter turns their raw call signatures into the stable handle API.
    state = {"array": np.array([1.0, 2.0, 3.0], dtype=np.float64)}

    def resize(*extents: np.int64) -> None:
        state["array"] = np.zeros(tuple(int(extent) for extent in extents), dtype=np.float64)

    array = _native_array_handle_from_generated_ops(
        "allocatable",
        np.float64,
        1,
        {
            "allocated": lambda: True,
            "descriptor": lambda: state["array"].ctypes.data,
            "shape": lambda: state["array"].shape,
            "to_numpy": lambda: state["array"],
            "resize": resize,
        },
    )

    print(f"Runtime handle: {type(array).__name__}")
    print(f"Descriptor kind: {array.descriptor_kind}")
    print(f"Initial view: {array.to_numpy().tolist()}")
    array.resize(4)
    print(f"Resized shape: {array.shape}")
    print(f"Generated resize received NumPy extents: {state['array'].shape == (4,)}")
