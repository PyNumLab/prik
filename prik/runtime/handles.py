"""Runtime helpers for native Fortran array descriptor handles."""

from __future__ import annotations

import ctypes
import operator
from collections.abc import Callable, Iterable, Sequence
from contextlib import suppress
from typing import Any

import numpy as np


HandleDispatcher = Callable[[str, tuple[Any, ...]], Any]
_PRESENT_NATIVE_ARRAY_DESCRIPTOR_ARGUMENT = ctypes.c_int(1)
_PRESENT_NATIVE_ARRAY_DESCRIPTOR_ARGUMENT_ADDRESS = ctypes.addressof(_PRESENT_NATIVE_ARRAY_DESCRIPTOR_ARGUMENT)

# What a pointer reports about the target it is associated with, and what
# another pointer is given to reproduce that association:
#
#     (base address, element width, rank, then per axis lower bound, extent,
#      stride in bytes)
#
# A generated handle reads these out of its live descriptor in C and a
# generated association writes them back into one, so they are exchanged in
# this flat form and never assembled into a descriptor in Python. A contract
# handle that has no native storage yet keeps its association here until it
# is given some.
_DESCRIPTOR_FACT_HEADER = 3
_DESCRIPTOR_FACTS_PER_AXIS = 3


class _OwnerRetainedNDArray(np.ndarray):
    """Internal ndarray view carrying a strong reference to native owner state."""


def _retain_numpy_owner(value: np.ndarray, owner: Any) -> np.ndarray:
    """Return a zero-copy ndarray view that retains one Python owner object."""
    retained = value.view(_OwnerRetainedNDArray)
    retained._prik_owner = owner
    return retained


def _descriptor_facts(value: Any, rank: int) -> tuple[int, ...]:
    """Validate one flat descriptor-fact tuple reported for a handle."""
    expected = _DESCRIPTOR_FACT_HEADER + _DESCRIPTOR_FACTS_PER_AXIS * int(rank)
    try:
        facts = tuple(operator.index(field) for field in value)
    except TypeError:
        raise TypeError("native array descriptor facts must be a sequence of integers") from None
    if len(facts) != expected:
        raise ValueError(f"native array descriptor facts must hold {expected} values; received {len(facts)}")
    if facts[0] < 0:
        raise ValueError(f"native array descriptor base address must be non-negative; received {facts[0]}")
    if facts[2] != int(rank):
        raise ValueError(f"native array descriptor rank {facts[2]} does not match declared rank {int(rank)}")
    return facts


def _descriptor_facts_shape_and_strides(facts: tuple[int, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Split one fact tuple into its extents and byte strides."""
    axes = range(facts[2])
    offsets = tuple(_DESCRIPTOR_FACT_HEADER + _DESCRIPTOR_FACTS_PER_AXIS * axis for axis in axes)
    return (
        tuple(facts[offset + 1] for offset in offsets),
        tuple(facts[offset + 2] for offset in offsets),
    )


def _empty_descriptor_facts(dtype: Any, rank: int) -> tuple[int, ...]:
    """Return the facts of storage that is not there.

    Every axis is empty, so the bounds describe nothing and no claim is made
    about an array that does not exist.
    """
    itemsize = 0 if dtype is None else np.dtype(dtype).itemsize
    return (0, itemsize, int(rank), *((0, 0, itemsize) * int(rank)))


def _numpy_view_from_descriptor_facts(facts: tuple[int, ...], dtype: Any) -> np.ndarray | None:
    """Build a NumPy view over the storage one fact tuple describes.

    Only a handle with no native storage of its own takes this route; every
    generated handle builds its view in C, where the descriptor is.
    """
    if facts[0] == 0:
        return None
    array_dtype = np.dtype(dtype)
    if facts[1] != array_dtype.itemsize:
        raise ValueError(
            f"native array element width {facts[1]} does not match NumPy dtype itemsize {array_dtype.itemsize}"
        )
    shape, strides = _descriptor_facts_shape_and_strides(facts)
    offset, nbytes, view_offset = _descriptor_view_buffer_window(shape, strides, array_dtype.itemsize)
    start = facts[0] + offset
    if start < 0:
        raise ValueError("native array view buffer starts before address zero")
    buffer = (ctypes.c_char * nbytes).from_address(start)
    return np.ndarray(shape, dtype=array_dtype, buffer=buffer, strides=strides, offset=view_offset)


def _native_array_handle_from_generated_dispatch(
    descriptor_kind: str,
    dtype: Any,
    rank: int,
    invoke: HandleDispatcher,
    capabilities: Iterable[str],
    owner: Any = None,
    descriptor_ownership: str = "borrowed",
    to_numpy_policy: str = "borrowed_view",
    native_backend: Any = None,
    generation: int | None = None,
    element_length_argument: bool = False,
    owner_association: bool = False,
) -> NativeArrayHandleBase:
    """Build a runtime handle from one generated operation dispatcher.

    ``native_backend`` is the capsule publishing the entity's native backend,
    which a binding reads directly to reach the descriptor. It is carried, not
    required: a handle created from a contract has none until it is given storage.
    """
    owned = descriptor_ownership == "owned"
    normalized_capabilities = frozenset(capabilities)
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
            invoke=invoke,
            capabilities=normalized_capabilities,
            owner=owner,
            descriptor_ownership=descriptor_ownership,
            to_numpy_policy=to_numpy_policy,
            generation=generation,
            element_length_argument=element_length_argument,
            owner_association=owner_association,
        )
        handle._native_backend = native_backend
        return handle
    except BaseException:
        if owned and "destroy" in normalized_capabilities:
            with suppress(Exception):
                invoke("destroy", (owner,) if owner is not None else ())
        raise


def _native_array_handle_from_contract(
    descriptor_kind: str,
    dtype: Any,
    rank: int,
    *,
    owner_association: bool = False,
) -> NativeArrayHandleBase:
    """Create one owned, initially empty descriptor handle from a contract.

    Such a handle has no native storage until a call gives it some, so it
    answers from a fact tuple of its own instead of from a descriptor. That is
    also where a pointer association taken before it was ever bound is kept,
    so the association can be replayed once storage arrives.
    """
    state: dict[str, Any] = {"facts": _empty_descriptor_facts(dtype, rank), "source": None}

    def current_shape() -> tuple[int, ...] | None:
        if state["facts"][0] == 0:
            return None
        shape, _strides = _descriptor_facts_shape_and_strides(state["facts"])
        return shape

    def descriptor() -> tuple[int, ...]:
        return state["facts"]

    def present() -> bool:
        return state["facts"][0] != 0

    def current_view() -> np.ndarray | None:
        if dtype is None:
            return None
        return _numpy_view_from_descriptor_facts(state["facts"], dtype)

    def clear() -> None:
        state["facts"] = _empty_descriptor_facts(dtype, rank)
        state["source"] = None

    def associate_facts(
        facts: tuple[int, ...],
        source: NativeArrayHandleBase,
    ) -> None:
        state["facts"] = facts
        state["source"] = source

    operations = {
        "shape": current_shape,
        "descriptor": descriptor,
        "to_numpy": current_view,
        "destroy": clear,
        "allocated": present,
        "associated": present,
        "nullify": clear,
        "_associate_facts": associate_facts,
        "element_length": lambda: state["facts"][1],
    }

    def dispatch(operation: str, args: tuple[Any, ...]) -> Any:
        return operations[operation](*args)

    try:
        handle_cls, capabilities = {
            "allocatable": (
                AllocatableArray,
                {"allocated", "shape", "descriptor", "to_numpy", "destroy", "element_length"},
            ),
            "pointer": (
                PointerArray,
                {
                    "associated",
                    "shape",
                    "descriptor",
                    "to_numpy",
                    "destroy",
                    "nullify",
                    "_associate_facts",
                    "element_length",
                },
            ),
        }[descriptor_kind]
    except KeyError:
        raise ValueError("contract native array handle kind must be 'allocatable' or 'pointer'") from None
    handle = handle_cls(
        dtype=dtype,
        rank=rank,
        invoke=dispatch,
        capabilities=capabilities,
        descriptor_ownership="owned",
        to_numpy_policy="unsupported" if owner_association and dtype is None else "borrowed_view",
        owner_association=owner_association,
    )
    handle._contract_default = True
    return handle


def _bind_contract_native_array_handle(
    handle: NativeArrayHandleBase,
    descriptor_kind: str,
    dtype: Any,
    rank: int,
    invoke: HandleDispatcher,
    capabilities: Iterable[str],
    owner: Any,
    descriptor_ownership: str,
    to_numpy_policy: str | None,
    generation: int | None = None,
    native_backend: Any = None,
    element_length_argument: bool = False,
    owner_association: bool = False,
) -> None:
    """Attach generated persistent descriptor storage to a contract handle.

    ``to_numpy_policy`` is ``None`` when the argument that supplied the storage
    does not project a result.  Such an argument gives the handle a descriptor
    to hand over, but it does not define what the handle exposes, so the
    handle keeps the exposure it was created with.

    ``native_backend`` is the backend over the attached storage, which every
    later call reads directly from C.
    """
    if not isinstance(handle, NativeArrayHandleBase) or not handle._contract_default:
        raise TypeError("generated descriptor storage can attach only to a fresh contract handle")
    if handle.closed:
        raise ReferenceError(f"{handle.descriptor_kind} handle is closed")
    if handle.descriptor_kind != descriptor_kind:
        raise TypeError(f"cannot attach {descriptor_kind} descriptor storage to {handle.descriptor_kind} handle")
    if handle.rank != int(rank):
        raise ValueError(f"{descriptor_kind} handle rank {handle.rank} does not match generated rank {int(rank)}")
    if dtype is None and handle._dtype is not None:
        raise TypeError(
            f"{descriptor_kind} handle dtype {handle.dtype!r} does not match a deferred-length character array"
        )
    if dtype is not None and not handle._dtype_matches(dtype):
        raise TypeError(f"{descriptor_kind} handle dtype {handle.dtype!r} does not match generated dtype {dtype!r}")
    # An association taken before there was anywhere native to record it is
    # replayed onto the storage that just arrived.
    pending = (
        handle._call_operation("descriptor")
        if isinstance(handle, PointerArray) and not handle._owner_association and handle.associated
        else None
    )
    generated = _native_array_handle_from_generated_dispatch(
        descriptor_kind,
        dtype,
        rank,
        invoke,
        capabilities,
        owner=owner,
        descriptor_ownership=descriptor_ownership,
        to_numpy_policy=handle._to_numpy_policy if to_numpy_policy is None else to_numpy_policy,
        native_backend=native_backend,
        generation=generation,
        element_length_argument=element_length_argument,
        owner_association=owner_association,
    )
    handle._invoke = generated._invoke
    handle._capabilities = generated._capabilities
    handle._owner = generated._owner
    handle._descriptor_ownership = generated._descriptor_ownership
    handle._to_numpy_policy = generated._to_numpy_policy
    handle._generation = generated._generation
    handle._element_length_argument = generated._element_length_argument
    handle._owner_association = generated._owner_association
    # The storage just attached is the wrapper's own and lives as long as the
    # handle, so the handle can publish it the way a module array publishes
    # its entity.  Later calls then reach it from C without coming back here.
    handle._native_backend = generated._native_backend
    handle._contract_default = False
    generated._closed = True
    if pending is not None:
        handle._call_operation("associate", pending)


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
    """Shared runtime state and single-call dispatch for native array handles."""

    _REQUIRED_CAPABILITIES: frozenset[str] = frozenset()
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
        invoke: HandleDispatcher,
        capabilities: Iterable[str],
        owner: Any = None,
        descriptor_kind: str,
        descriptor_ownership: str,
        to_numpy_policy: str = "borrowed_view",
        generation: int | None = None,
        element_length_argument: bool = False,
        owner_association: bool = False,
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
        if not callable(invoke):
            raise TypeError(f"native array handle dispatcher must be callable; received {type(invoke).__name__}")
        self._invoke: HandleDispatcher | None = invoke
        self._capabilities = self._normalize_capabilities(capabilities)
        self._owner = owner
        self._descriptor_kind = descriptor_kind
        self._descriptor_ownership = descriptor_ownership
        self._to_numpy_policy = to_numpy_policy
        self._generation = generation
        self._element_length_argument = bool(element_length_argument)
        self._owner_association = bool(owner_association)
        # Optional capsule publishing this entity's native descriptor backend.
        self._native_backend: Any = None
        self._contract_default = False
        self._validate_required_capabilities()
        self._closed = False

    @property
    def dtype(self) -> np.dtype:
        if self._dtype is not None:
            return self._dtype
        return self._deferred_character_dtype()

    def _allocation_arguments(
        self,
        shape: Sequence[int] | int,
        element_length: int | None,
    ) -> tuple[tuple[int, ...], int | None]:
        """Normalize one allocation request against the completed contract.

        A deferred-length character entity has no width to fall back on, so the
        caller supplies it; every other entity already knows its element width
        and must not be given a second, conflicting one.
        """
        extents = self._normalize_shape(shape)
        if not self._element_length_argument:
            if element_length is not None:
                raise TypeError(
                    f"{self.descriptor_kind} handle element_length is only accepted by a deferred-length "
                    f"character array; this handle has a fixed element width"
                )
            return extents, None
        if element_length is None:
            raise TypeError(
                f"{self.descriptor_kind} handle is a deferred-length character array, so allocation needs an "
                f"element_length; pass element_length=<width>"
            )
        try:
            width = operator.index(element_length)
        except TypeError:
            raise TypeError(
                f"{self.descriptor_kind} handle element_length must be an integer; "
                f"received {type(element_length).__name__}"
            ) from None
        if width < 0:
            raise ValueError(f"{self.descriptor_kind} handle element_length must not be negative; received {width}")
        return extents, width

    def _deferred_character_dtype(self) -> np.dtype:
        """Resolve one deferred character width from generated native state."""
        length = operator.index(self._call_operation("element_length"))
        if length < 0:
            raise ValueError("native character array element length must be non-negative")
        return np.dtype(f"S{length}")

    @property
    def rank(self) -> int:
        return self._rank

    @property
    def shape(self) -> tuple[int, ...] | None:
        """Return current extents, or ``None`` when the storage is not there.

        The inquiry reads the descriptor itself, so it reports absence rather
        than being asked about it first, and the extents it returns are the
        ones the compiler recorded.
        """
        shape = self._call_operation("shape")
        if shape is None:
            return None
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
        invoke = self._invoke
        if invoke is None:
            return None
        try:
            return self._call_operation("destroy")
        finally:
            self._closed = True
            self._owner = None
            self._native_backend = None
            self._invoke = None
            self._capabilities = frozenset()

    def __del__(self) -> None:
        with suppress(Exception):
            self.close()

    def to_numpy(self) -> Any:
        """Return a live view of current native storage, or ``None``.

        The extraction reads the descriptor itself, so it reports absent
        storage rather than being asked about it first, and it builds the view
        from the declared element type over the storage the descriptor names.
        """
        policy = self._to_numpy_policy
        if policy == "unsupported":
            # There is nothing to expose either way when the storage is not
            # there, so absence is reported before the refusal.
            if not self._present():
                return None
            raise NotImplementedError(
                f"{self.descriptor_kind} handle to_numpy extraction is unsupported by completed policy"
            )
        value = self._call_operation("to_numpy")
        if value is None:
            return None
        self._validate_numpy_result(value)
        if self.owned and value.base is not None and value.base is self._owner:
            # The view was built over storage this handle releases when it is
            # finalized, so the view has to keep the handle alive too, not just
            # the record that holds the storage.
            value = _retain_numpy_owner(value, self)
        if policy == "contiguous_view":
            self._validate_contiguous_numpy_result(value)
        return value

    def _call_operation(self, name: str, *args: Any) -> Any:
        if self.closed:
            raise ReferenceError(f"{self.descriptor_kind} handle is closed")
        if name not in self._capabilities:
            raise NotImplementedError(f"{self.descriptor_kind} handle operation {name!r} is not available") from None
        invoke = self._invoke
        if invoke is None:
            raise ReferenceError(f"{self.descriptor_kind} handle is closed")
        if name in {"allocate", "resize"}:
            extents, element_length = args
            args = tuple(np.int64(extent) for extent in extents)
            if element_length is not None:
                args = (*args, np.int64(element_length))
        if self.owned and self._owner is not None:
            args = (self._owner, *args)
        return invoke(name, args)

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

    def _present(self) -> bool:
        """Report whether this handle currently stands for any storage."""
        return True

    def _dtype_matches(self, expected_dtype: Any) -> bool:
        try:
            return np.dtype(self.dtype) == np.dtype(expected_dtype)
        except TypeError:
            return self.dtype == expected_dtype

    def _validate_required_capabilities(self) -> None:
        if "shape" not in self._capabilities:
            raise ValueError(f"{self.descriptor_kind} native array handle requires generated operation 'shape'")
        for name in sorted(self._REQUIRED_CAPABILITIES):
            if name not in self._capabilities:
                raise ValueError(f"{self.descriptor_kind} native array handle requires generated operation {name!r}")
        if self.to_numpy_policy != "unsupported" and "to_numpy" not in self._capabilities:
            raise ValueError(
                f"{self.descriptor_kind} native array handle with to_numpy_policy "
                f"{self.to_numpy_policy!r} requires generated operation 'to_numpy'"
            )
        if self.owned and "destroy" not in self._capabilities:
            raise ValueError(f"{self.descriptor_kind} owned native array handle requires generated operation 'destroy'")

    @staticmethod
    def _normalize_capabilities(capabilities: Iterable[str]) -> frozenset[str]:
        normalized = frozenset(capabilities)
        for name in normalized:
            if not isinstance(name, str):
                raise TypeError(f"native array handle capability names must be strings; received {type(name).__name__}")
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


class AllocatableArray(NativeArrayHandleBase):
    """Runtime handle for a native allocatable array descriptor."""

    _REQUIRED_CAPABILITIES = frozenset({"allocated"})

    def __init__(
        self,
        *,
        dtype: Any,
        rank: int,
        invoke: HandleDispatcher,
        capabilities: Iterable[str],
        owner: Any = None,
        descriptor_ownership: str = "borrowed",
        to_numpy_policy: str = "borrowed_view",
        generation: int | None = None,
        element_length_argument: bool = False,
        owner_association: bool = False,
    ) -> None:
        super().__init__(
            dtype=dtype,
            rank=rank,
            invoke=invoke,
            capabilities=capabilities,
            owner=owner,
            descriptor_kind="allocatable",
            descriptor_ownership=descriptor_ownership,
            to_numpy_policy=to_numpy_policy,
            generation=generation,
            element_length_argument=element_length_argument,
            owner_association=owner_association,
        )

    @property
    def allocated(self) -> bool:
        return bool(self._call_operation("allocated"))

    def _present(self) -> bool:
        return self.allocated

    def deallocate(self) -> Any:
        return self._call_operation("deallocate")

    def resize(self, shape: Sequence[int] | int, *, element_length: int | None = None) -> Any:
        return self._call_operation("resize", *self._allocation_arguments(shape, element_length))


class PointerArray(NativeArrayHandleBase):
    """Runtime handle for a native pointer array descriptor."""

    _REQUIRED_CAPABILITIES = frozenset({"associated", "nullify"})

    def __init__(
        self,
        *,
        dtype: Any,
        rank: int,
        invoke: HandleDispatcher,
        capabilities: Iterable[str],
        owner: Any = None,
        descriptor_ownership: str = "borrowed",
        to_numpy_policy: str = "borrowed_view",
        generation: int | None = None,
        element_length_argument: bool = False,
        owner_association: bool = False,
    ) -> None:
        super().__init__(
            dtype=dtype,
            rank=rank,
            invoke=invoke,
            capabilities=capabilities,
            owner=owner,
            descriptor_kind="pointer",
            descriptor_ownership=descriptor_ownership,
            to_numpy_policy=to_numpy_policy,
            generation=generation,
            element_length_argument=element_length_argument,
            owner_association=owner_association,
        )

    @property
    def associated(self) -> bool:
        return bool(self._call_operation("associated"))

    def _present(self) -> bool:
        return self.associated

    def _association_facts(self) -> tuple[int, ...]:
        """Report what this pointer is associated with, as flat facts.

        A pointer assignment copies the association as it stands now; it does
        not make the target follow the source afterwards. Reading the facts
        here is what makes that snapshot.
        """
        facts = _descriptor_facts(self._call_operation("descriptor"), self.rank)
        itemsize = np.dtype(self.dtype).itemsize
        if facts[0] != 0 and facts[1] != itemsize:
            raise ValueError(f"pointer handle element width {facts[1]} does not match NumPy dtype itemsize {itemsize}")
        return facts

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
        if self._owner_association:
            if not other._owner_association:
                raise TypeError("Fortran-owned pointer association requires another compatible owner handle")
            if self._dtype is not None and self._dtype != other._dtype:
                raise TypeError(f"pointer handle dtype {self.dtype!r} does not match source dtype {other.dtype!r}")
            if self._contract_default:
                raise TypeError(
                    "Fortran-owned pointer association requires the target handle to be attached to a native "
                    "argument before associate() is called"
                )
            if other._native_backend is None:
                raise TypeError("pointer association source has no generated Fortran owner")
            return self._call_operation("associate", other._native_backend)
        if not self._dtype_matches(other.dtype):
            raise TypeError(f"pointer handle dtype {self.dtype!r} does not match source dtype {other.dtype!r}")
        facts = other._association_facts()
        if self._contract_default:
            # No native storage yet: keep the association, and the handle it
            # came from, until storage arrives and it can be replayed.
            return self._call_operation("_associate_facts", facts, other)
        return self._call_operation("associate", facts)

    def nullify(self) -> Any:
        return self._call_operation("nullify")

    def allocate(self, shape: Sequence[int] | int, *, element_length: int | None = None) -> Any:
        return self._call_operation("allocate", *self._allocation_arguments(shape, element_length))

    def deallocate(self) -> Any:
        return self._call_operation("deallocate")

    def resize(self, shape: Sequence[int] | int, *, element_length: int | None = None) -> Any:
        return self._call_operation("resize", *self._allocation_arguments(shape, element_length))


def _native_array_backend_for_binding(
    value: Any,
    *,
    descriptor_kind: str,
    expected_dtype: Any = None,
    expected_rank: int | None = None,
    optional_absent: bool = False,
    bind_default: Callable[..., Any] | None = None,
) -> tuple[Any | None, ...]:
    """Return the backend capsule a descriptor argument hands over.

    Only a handle that has no storage yet reaches this: everything else
    publishes a backend the binding reads without coming back here.  Attaching
    storage is what gives such a handle one, so the binder runs first and the
    backend it published is what goes back.
    """
    try:
        expected_type = {
            "allocatable": AllocatableArray,
            "pointer": PointerArray,
        }[descriptor_kind]
    except KeyError:
        raise ValueError(f"unsupported native array descriptor kind: {descriptor_kind!r}") from None
    if value is None:
        if optional_absent:
            return (None, None)
        raise TypeError(f"{descriptor_kind} native array handle argument is required; received None")
    if not isinstance(value, expected_type):
        raise TypeError(f"expected {descriptor_kind} native array handle argument; received {type(value).__name__}")
    if expected_rank is not None and value.rank != int(expected_rank):
        raise ValueError(
            f"{descriptor_kind} handle rank {value.rank} does not match expected rank {int(expected_rank)}"
        )
    if expected_dtype is not None and not value._dtype_matches(expected_dtype):
        raise TypeError(
            f"{descriptor_kind} handle dtype {value.dtype!r} does not match expected dtype {expected_dtype!r}"
        )
    if value._contract_default:
        if bind_default is None:
            raise TypeError(
                f"writable {descriptor_kind} contract handle requires generated persistent descriptor storage"
            )
        bind_default(value)
    backend = value._native_backend
    if backend is None:
        raise TypeError(
            f"writable {descriptor_kind} descriptor argument requires generated persistent descriptor storage"
        )
    if optional_absent:
        return backend, _PRESENT_NATIVE_ARRAY_DESCRIPTOR_ARGUMENT_ADDRESS
    return (backend,)


def _native_array_backend_for_binding_positional(
    value: Any,
    descriptor_kind: str,
    expected_dtype: Any = None,
    expected_rank: int | None = None,
    optional_absent: bool = False,
    bind_default: Callable[..., Any] | None = None,
) -> tuple[Any | None, ...]:
    """Positional wrapper used by projected-handle CPython binding code."""
    return _native_array_backend_for_binding(
        value,
        descriptor_kind=str(descriptor_kind),
        expected_dtype=None if expected_dtype is None else np.dtype(expected_dtype),
        expected_rank=None if expected_rank is None else int(expected_rank),
        optional_absent=bool(optional_absent),
        bind_default=bind_default,
    )


__all__ = (
    "AllocatableArray",
    "NativeArrayHandleBase",
    "PointerArray",
)


if __name__ == "__main__":
    # Generated extensions supply one dispatcher and its completed capabilities.
    state = {"array": np.array([1.0, 2.0, 3.0], dtype=np.float64)}

    def resize(*extents: np.int64) -> None:
        state["array"] = np.zeros(tuple(int(extent) for extent in extents), dtype=np.float64)

    operations = {
        "allocated": lambda: True,
        "shape": lambda: state["array"].shape,
        "to_numpy": lambda: state["array"],
        "resize": resize,
    }

    def invoke(operation: str, args: tuple[Any, ...]) -> Any:
        return operations[operation](*args)

    array = _native_array_handle_from_generated_dispatch(
        "allocatable",
        np.float64,
        1,
        invoke,
        operations,
    )

    print(f"Runtime handle: {type(array).__name__}")
    print(f"Descriptor kind: {array.descriptor_kind}")
    print(f"Initial view: {array.to_numpy().tolist()}")
    array.resize(4)
    print(f"Resized shape: {array.shape}")
    print(f"Generated resize received NumPy extents: {state['array'].shape == (4,)}")
