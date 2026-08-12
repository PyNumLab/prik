"""Complete lifetime and boundary policy before wrapper planning and lowering.

Ownership is represented as several independent questions instead of one
``owned`` or ``borrowed`` flag:

* ``OwnershipOwner`` says who owns the represented storage.
* ``TransferMode`` says how the value or storage relationship crosses the
  Python/native boundary.
* ``DestructionPolicy`` says who releases an owned resource.
* ``StorageMode`` says whether PRIK keeps a direct value, heap-backed value, or
  alias for both the contract and ABI boundary representations.
* the action enums tell planning and lowering exactly which generated
  mechanism to use.

The separation matters because the Python object and its native storage can
have different owners.  For example,
``PYTHON + COPY_RETURN + PYTHON_REFCOUNT`` describes an independent Python
copy, while ``NATIVE + BORROWED_VIEW + NATIVE_OWNER`` describes a live Python
view whose storage remains owned and released by native code.  The resolver
accepts only implemented combinations and fails closed when the owner,
transfer, release responsibility, or required lifetime proof is missing.

``OwnershipPolicyResolver`` first selects defaults from semantic storage and
use context, then applies explicit contract metadata, validates the completed
lifetime triple, and finally derives strict lowering actions.  Post-IR policy
completion attaches the resulting immutable ``OwnershipDecision`` before
wrapper planning begins.  Bridge and binding generators consume those
decisions; they must not reconstruct semantic policy from datatypes, source
``intent``, rank, alias flags, or local memory checks.

For example, a normal scalar input commonly resolves to caller-owned,
call-local use with no wrapper release action, while an array result commonly
resolves to a Python-owned copy released by Python reference counting.  See
``docs/developer/internal-architecture/ownership-tracking.md`` for the full
stage map, supported triples, pointer-policy boundary, and change routes.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_PROJECTION,
    ADDRESS_ROLE_RAW,
    NATIVE_ARRAY_DESCRIPTOR_METADATA,
    PROJECTED_OUTPUT_METADATA,
    SCALAR_STORAGE_CATEGORY,
)
from prik.semantics.models import PYTHON_VALUE_IMMUTABLE, PYTHON_VALUE_MUTABILITY_METADATA
from prik.semantics.ownership_metadata import OWNERSHIP_POLICY_METADATA, POINTER_POLICY_METADATA
from prik.semantics.scalar_types import BOOLEAN_SEMANTIC_TYPE_NAMES


# Completed policy vocabulary


class ObjectKind(str, Enum):
    """Classify the Python-facing category selected by ownership policy.

    ``OwnershipPolicyResolver`` chooses a kind before selecting lifetime and
    ABI actions.  Strict lowering dispatchers consume this value as part of
    their completed-policy key.

    Values:
        ``SCALAR`` is an ordinary scalar value or addressable scalar cell.
        ``STRING`` is a Python string value or native character storage.
        ``NUMPY_ARRAY`` is NumPy-compatible array storage, including native
        descriptor-backed arrays. ``DERIVED_TYPE`` is an opaque native object
        represented through a generated wrapper.
    """

    SCALAR = "scalar"
    STRING = "string"
    NUMPY_ARRAY = "numpy_array"
    DERIVED_TYPE = "derived_type"


class OwnershipOwner(str, Enum):
    """Name the party that owns the represented value or storage.

    Values:
        ``PYTHON`` means Python, NumPy, or a Python-owned capsule owns the
        value or buffer. ``CALLER`` means the supplied caller object retains
        ownership across the call. ``NATIVE`` means an independent Fortran or
        external native owner retains the storage. ``WRAPPER`` means a
        generated wrapper or handle owns or controls the native resource.
        ``TEMPORARY`` means generated storage exists only for the current
        call. ``UNKNOWN`` records that no safe owner is known and is used by
        fail-closed decisions.

    The owner does not by itself say whether a copy or view crosses the
    boundary; read it together with ``TransferMode`` and
    ``DestructionPolicy``.
    """

    PYTHON = "python"
    CALLER = "caller"
    NATIVE = "native"
    WRAPPER = "wrapper"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class TransferMode(str, Enum):
    """Describe how a value or storage relationship crosses the boundary.

    Values:
        ``BY_VALUE`` passes an independent scalar-like value. ``IN_PLACE``
        lets native code use caller-visible storage without replacement.
        ``COPY_RETURN`` copies or converts native output into a fresh Python
        result. ``SNAPSHOT_COPY`` detaches a copy of current persistent native
        state. ``BORROWED_VIEW`` exposes storage owned elsewhere without
        transferring ownership. ``CALL_LOCAL`` keeps storage or association
        valid only for one wrapped call. ``WRAPPER_INSTANCE`` returns a
        generated object that owns or controls a native instance. ``BLOCKED``
        states that no supported safe transfer exists.

    A transfer is an observable relationship, not a cleanup instruction;
    cleanup comes from ``DestructionPolicy``.
    """

    BY_VALUE = "by_value"
    IN_PLACE = "in_place"
    COPY_RETURN = "copy_return"
    SNAPSHOT_COPY = "snapshot_copy"
    BORROWED_VIEW = "borrowed_view"
    CALL_LOCAL = "call_local"
    WRAPPER_INSTANCE = "wrapper_instance"
    BLOCKED = "blocked"


class DestructionPolicy(str, Enum):
    """Describe who releases any resource represented by the decision.

    Values:
        ``PYTHON_REFCOUNT`` delegates release to Python, NumPy, or a
        Python-owned capsule. ``CALLER`` leaves release responsibility with
        the caller that supplied the object. ``WRAPPER_DEALLOC`` uses a
        generated wrapper or handle deallocator. ``NATIVE_OWNER`` leaves
        release to an independent native owner. ``CALL_LOCAL`` runs generated
        cleanup before the wrapped call finishes. ``NONE`` means this boundary
        value creates no resource that PRIK must release. ``BLOCKED`` means
        release responsibility is unsafe, contradictory, or unimplemented.

    ``NONE`` does not claim that no storage exists.  For example, an existing
    wrapper-owned object passed call-locally still has storage, but that call
    creates nothing new to destroy.
    """

    PYTHON_REFCOUNT = "python_refcount"
    CALLER = "caller"
    WRAPPER_DEALLOC = "wrapper_dealloc"
    NATIVE_OWNER = "native_owner"
    CALL_LOCAL = "call_local"
    NONE = "none"
    BLOCKED = "blocked"


class StorageMode(str, Enum):
    """Select storage for a contract value or ABI boundary representation.

    Values:
        ``STACK`` is a direct or call-frame value with no persistent heap
        allocation. ``HEAP`` is storage whose lifetime extends beyond a native
        stack value. ``ALIAS`` refers to existing storage without owning an
        independent value at this location.

    ``OwnershipDecision.storage_mode`` describes the contract value;
    ``boundary_storage_mode`` may separately describe the ABI-facing form.
    """

    STACK = "stack"
    HEAP = "heap"
    ALIAS = "alias"


class CodegenAction(str, Enum):
    """Identify the completed general lowering mechanism.

    Values:
        ``DIRECT_VALUE`` converts or returns an independent value.
        ``CALL_LOCAL_INPUT`` prepares input storage valid for one call.
        ``IN_PLACE_ARGUMENT`` passes caller-visible mutable storage.
        ``IDENTITY_OUTPUT`` mutates and projects the same supplied object.
        ``COPY_IN_OUT`` copies immutable Python input into mutable call storage
        and returns its final value. ``COPY_OUT`` materializes native output as
        a fresh Python result. ``SNAPSHOT_COPY`` materializes a detached copy
        of persistent state. ``BORROWED_VIEW`` exposes owner-controlled
        storage. ``WRAPPER_INSTANCE`` constructs or returns a generated native
        object wrapper. ``BLOCKED`` rejects lowering.

    This action is derived only after the lifetime triple is validated.
    """

    DIRECT_VALUE = "direct_value"
    CALL_LOCAL_INPUT = "call_local_input"
    IN_PLACE_ARGUMENT = "in_place_argument"
    IDENTITY_OUTPUT = "identity_output"
    COPY_IN_OUT = "copy_in_out"
    COPY_OUT = "copy_out"
    SNAPSHOT_COPY = "snapshot_copy"
    BORROWED_VIEW = "borrowed_view"
    WRAPPER_INSTANCE = "wrapper_instance"
    BLOCKED = "blocked"


class PythonBarrierAction(str, Enum):
    """Identify how a Python-visible argument enters wrapper storage.

    Values:
        ``SCALAR_VALUE`` reads an ordinary Python scalar. ``SCALAR_STORAGE``
        reads or creates addressable scalar storage. ``ARRAY_STORAGE``
        validates and uses NumPy-compatible array storage. ``STRING_VALUE``
        reads an immutable Python string. ``STRING_STORAGE`` uses mutable
        character storage. ``RAW_ADDRESS`` accepts an explicit raw address.
        ``WRAPPER_INSTANCE`` extracts an opaque instance or native descriptor
        from a generated wrapper. ``NONE`` means there is no Python argument
        for this value. ``BLOCKED`` rejects Python-boundary lowering.
    """

    SCALAR_VALUE = "scalar_value"
    SCALAR_STORAGE = "scalar_storage"
    ARRAY_STORAGE = "array_storage"
    STRING_VALUE = "string_value"
    STRING_STORAGE = "string_storage"
    RAW_ADDRESS = "raw_address"
    WRAPPER_INSTANCE = "wrapper_instance"
    NONE = "none"
    BLOCKED = "blocked"


class NativeBarrierAction(str, Enum):
    """Identify how wrapper storage crosses the native ABI boundary.

    Values:
        ``PASS_VALUE`` passes a converted value directly.
        ``PASS_CALL_LOCAL_ADDRESS`` passes wrapper-created call-local storage
        by address. ``PASS_STORAGE_ADDRESS`` passes existing mutable storage by
        address. ``PASS_RAW_ADDRESS`` forwards an explicit raw address.
        ``PASS_ARRAY_BUFFER`` passes a validated array data buffer.
        ``PASS_NATIVE_DESCRIPTOR`` passes an allocatable or pointer descriptor.
        ``PASS_WRAPPER_ADDRESS`` passes an opaque address held by a generated
        object wrapper. ``NONE`` means no native argument is required.
        ``BLOCKED`` rejects native-boundary lowering.
    """

    PASS_VALUE = "pass_value"
    PASS_CALL_LOCAL_ADDRESS = "pass_call_local_address"
    PASS_STORAGE_ADDRESS = "pass_storage_address"
    PASS_RAW_ADDRESS = "pass_raw_address"
    PASS_ARRAY_BUFFER = "pass_array_buffer"
    PASS_NATIVE_DESCRIPTOR = "pass_native_descriptor"
    PASS_WRAPPER_ADDRESS = "pass_wrapper_address"
    NONE = "none"
    BLOCKED = "blocked"


class AssignmentMode(str, Enum):
    """Describe the native assignment mechanism selected for a setter.

    Values:
        ``NONE`` emits no native assignment. ``VALUE_COPY`` copies the incoming
        value into existing native storage. ``ALIAS`` associates the
        destination with existing storage rather than copying it.
    """

    NONE = "none"
    VALUE_COPY = "value_copy"
    ALIAS = "alias"


class SetterAction(str, Enum):
    """Describe the Python property setter behavior selected by policy.

    Values:
        ``WRITE_THROUGH`` exposes a setter that updates native state.
        ``REJECT_REPLACEMENT`` keeps the property readable but explicitly
        rejects replacing its storage. ``OMIT`` exposes no Python setter.
    """

    WRITE_THROUGH = "write_through"
    REJECT_REPLACEMENT = "reject_replacement"
    OMIT = "omit"


@dataclass(frozen=True)
class PolicyActionDispatcher:
    """Route a completed object-kind/codegen-action pair to a named lowering method.

    Backends use this dispatcher only after policy completion has attached an
    ``OwnershipDecision``.  Missing pairs fail closed with ``ValueError``;
    the dispatcher never derives an alternative action from a datatype.
    """

    handlers: Mapping[tuple[ObjectKind, CodegenAction], str]

    def handler_name_for_decision(self, decision: OwnershipDecision, name: str) -> str:
        """Return the registered handler for ``decision`` or reject the subject ``name``."""
        key = (decision.kind, decision.codegen_action)
        try:
            return self.handlers[key]
        except KeyError:
            raise ValueError(
                f"No policy codegen handler for {name!r}: {decision.kind.value}/{decision.codegen_action.value}"
            ) from None

    def handler_name(self, var: Any) -> tuple[OwnershipDecision, str]:
        """Read a variable's completed decision and return it with its handler name."""
        decision = ownership_decision_for_codegen_variable(var)
        name = str(getattr(var, "name", type(var).__name__))
        return decision, self.handler_name_for_decision(decision, name)

    def dispatch(self, target: Any, var: Any, *args: Any, **kwargs: Any) -> Any:
        """Invoke this policy pair's named method on ``target`` with ``var`` and its decision."""
        decision, handler_name = self.handler_name(var)
        handler = getattr(target, handler_name)
        return handler(var, decision, *args, **kwargs)

    def dispatch_decision(
        self,
        target: Any,
        subject: Any,
        decision: OwnershipDecision,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Dispatch an accessor or nested decision stored beside ``subject``.

        The supplied decision is used directly, so callers can dispatch
        getter, setter, or nested policies without attaching it as an
        ``ownership_decision`` attribute first.
        """
        name = str(getattr(subject, "name", getattr(subject, "python_name", type(subject).__name__)))
        handler = getattr(target, self.handler_name_for_decision(decision, name))
        return handler(subject, decision, *args, **kwargs)


@dataclass(frozen=True)
class PolicyProjectionDispatcher:
    """Route output projections using kind, codegen action, and result projection.

    Projection lowering needs the extra ``projects_result`` axis because the
    same native action can either remain an input or appear in Python output.
    Missing combinations raise ``ValueError`` rather than choosing a fallback.
    """

    handlers: Mapping[tuple[ObjectKind, CodegenAction, bool], str]

    def handler_name_for_decision(self, decision: OwnershipDecision, name: str) -> str:
        """Return the projection handler for ``decision`` or reject the subject ``name``."""
        key = (decision.kind, decision.codegen_action, decision.projects_result)
        try:
            return self.handlers[key]
        except KeyError:
            raise ValueError(
                f"No projection handler for {name!r}: "
                f"{decision.kind.value}/{decision.codegen_action.value}/projects_result={decision.projects_result}"
            ) from None

    def dispatch(self, target: Any, var: Any, *args: Any, **kwargs: Any) -> Any:
        """Invoke the selected projection method on ``target`` using ``var``'s decision."""
        decision = ownership_decision_for_codegen_variable(var)
        name = str(getattr(var, "name", type(var).__name__))
        handler = getattr(target, self.handler_name_for_decision(decision, name))
        return handler(var, decision, *args, **kwargs)


@dataclass(frozen=True)
class PythonBarrierDispatcher:
    """Route a completed Python-boundary action to a named lowering method."""

    handlers: Mapping[PythonBarrierAction, str]

    def handler_name_for_decision(self, decision: OwnershipDecision, name: str) -> str:
        """Return the Python-boundary handler for ``decision`` or reject ``name``."""
        try:
            return self.handlers[decision.python_barrier_action]
        except KeyError:
            raise ValueError(
                f"No Python-barrier handler for {name!r}: {decision.python_barrier_action.value}"
            ) from None

    def dispatch(self, target: Any, var: Any, *args: Any, **kwargs: Any) -> Any:
        """Invoke the selected Python-boundary method with ``var`` and its policy."""
        decision = ownership_decision_for_codegen_variable(var)
        name = str(getattr(var, "name", type(var).__name__))
        handler = getattr(target, self.handler_name_for_decision(decision, name))
        return handler(var, decision, *args, **kwargs)


@dataclass(frozen=True)
class NativeBarrierDispatcher:
    """Route a completed native-ABI action to a named lowering method."""

    handlers: Mapping[NativeBarrierAction, str]

    def handler_name_for_decision(self, decision: OwnershipDecision, name: str) -> str:
        """Return the native-boundary handler for ``decision`` or reject ``name``."""
        try:
            return self.handlers[decision.native_barrier_action]
        except KeyError:
            raise ValueError(
                f"No native-barrier handler for {name!r}: {decision.native_barrier_action.value}"
            ) from None

    def dispatch(self, target: Any, var: Any, *args: Any, **kwargs: Any) -> Any:
        """Invoke the selected native-boundary method with ``var`` and its policy."""
        decision = ownership_decision_for_codegen_variable(var)
        name = str(getattr(var, "name", type(var).__name__))
        handler = getattr(target, self.handler_name_for_decision(decision, name))
        return handler(var, decision, *args, **kwargs)


@dataclass(frozen=True)
class SetterActionDispatcher:
    """Route a completed setter action to a named lowering method without inference."""

    handlers: Mapping[SetterAction, str]

    def dispatch(self, target: Any, subject: Any, decision: OwnershipDecision, *args: Any) -> Any:
        """Invoke ``subject``'s selected setter handler or reject an unregistered action."""
        try:
            handler_name = self.handlers[decision.setter_action]
        except KeyError:
            name = str(getattr(subject, "name", getattr(subject, "python_name", type(subject).__name__)))
            raise ValueError(f"No setter handler for {name!r}: {decision.setter_action.value}") from None
        return getattr(target, handler_name)(subject, decision, *args)


@dataclass(frozen=True)
class DestructionPolicyDispatcher:
    """Route a completed release responsibility to a named cleanup method."""

    handlers: Mapping[DestructionPolicy, str]

    def dispatch(self, target: Any, subject: Any, decision: OwnershipDecision, *args: Any) -> Any:
        """Invoke ``subject``'s selected release handler or reject an unregistered policy."""
        try:
            handler_name = self.handlers[decision.destruction]
        except KeyError:
            name = str(getattr(subject, "name", getattr(subject, "python_name", type(subject).__name__)))
            raise ValueError(f"No release handler for {name!r}: {decision.destruction.value}") from None
        return getattr(target, handler_name)(subject, decision, *args)


_STANDARD_SCALAR_TYPES = frozenset(
    {
        *BOOLEAN_SEMANTIC_TYPE_NAMES,
        "Byte",
        "CEnum",
        "Char",
        "Complex64",
        "Complex128",
        "Float16",
        "Float32",
        "Float64",
        "Float128",
        "Int",
        "Int8",
        "Int16",
        "Int32",
        "Int64",
        "UInt",
        "UInt8",
        "UInt16",
        "UInt32",
        "UInt64",
        "Void",
    }
)

_OWNER_LABELS = {
    OwnershipOwner.PYTHON: "Python-owned",
    OwnershipOwner.CALLER: "Caller-owned",
    OwnershipOwner.NATIVE: "Native-owned",
    OwnershipOwner.WRAPPER: "Wrapper-owned",
    OwnershipOwner.TEMPORARY: "Temporary",
    OwnershipOwner.UNKNOWN: "Unknown owner",
}

_CODEGEN_ACTION_BY_TRANSFER = {
    TransferMode.BY_VALUE: CodegenAction.DIRECT_VALUE,
    TransferMode.CALL_LOCAL: CodegenAction.CALL_LOCAL_INPUT,
    TransferMode.IN_PLACE: CodegenAction.IN_PLACE_ARGUMENT,
    TransferMode.COPY_RETURN: CodegenAction.COPY_OUT,
    TransferMode.SNAPSHOT_COPY: CodegenAction.SNAPSHOT_COPY,
    TransferMode.BORROWED_VIEW: CodegenAction.BORROWED_VIEW,
    TransferMode.WRAPPER_INSTANCE: CodegenAction.WRAPPER_INSTANCE,
    TransferMode.BLOCKED: CodegenAction.BLOCKED,
}

_VALID_DESTRUCTION_BY_OWNER_TRANSFER = {
    (OwnershipOwner.PYTHON, TransferMode.BY_VALUE): frozenset({DestructionPolicy.PYTHON_REFCOUNT}),
    (OwnershipOwner.PYTHON, TransferMode.COPY_RETURN): frozenset({DestructionPolicy.PYTHON_REFCOUNT}),
    (OwnershipOwner.PYTHON, TransferMode.SNAPSHOT_COPY): frozenset({DestructionPolicy.PYTHON_REFCOUNT}),
    (OwnershipOwner.CALLER, TransferMode.CALL_LOCAL): frozenset({DestructionPolicy.NONE, DestructionPolicy.CALL_LOCAL}),
    (OwnershipOwner.CALLER, TransferMode.IN_PLACE): frozenset({DestructionPolicy.CALLER}),
    (OwnershipOwner.NATIVE, TransferMode.BORROWED_VIEW): frozenset({DestructionPolicy.NATIVE_OWNER}),
    (OwnershipOwner.WRAPPER, TransferMode.CALL_LOCAL): frozenset({DestructionPolicy.NONE}),
    (OwnershipOwner.WRAPPER, TransferMode.IN_PLACE): frozenset({DestructionPolicy.WRAPPER_DEALLOC}),
    (OwnershipOwner.WRAPPER, TransferMode.BORROWED_VIEW): frozenset({DestructionPolicy.WRAPPER_DEALLOC}),
    (OwnershipOwner.WRAPPER, TransferMode.WRAPPER_INSTANCE): frozenset({DestructionPolicy.WRAPPER_DEALLOC}),
    (OwnershipOwner.TEMPORARY, TransferMode.CALL_LOCAL): frozenset({DestructionPolicy.CALL_LOCAL}),
}


# Semantic context and completed decisions


@dataclass(frozen=True)
class OwnershipContext:
    """Describe where a semantic value appears and how native code may use it.

    Construct one of the named factories for normal result, argument, field,
    or module-variable cases.  The resolver combines these flags with storage
    facts to select an ownership decision; callers do not need to infer a
    codegen action themselves.

    ``location`` is the diagnostic location label. ``reads_argument`` and
    ``writes_argument`` describe native access to a supplied argument.
    ``is_result``, ``is_argument``, ``is_field``, and ``is_module_variable``
    identify the semantic owner. ``projects_result`` says the value occupies a
    declared Python result position, while ``python_visible`` says the caller
    supplies it as a Python argument.

    For example, a hidden output dummy uses
    ``OwnershipContext.argument(reads_argument=False, writes_argument=True,
    projects_result=True, python_visible=False)``: native code writes it, the
    wrapper returns it, and the Python caller does not supply it.
    """

    location: str = "value"
    reads_argument: bool = True
    writes_argument: bool = False
    is_result: bool = False
    is_argument: bool = False
    is_field: bool = False
    is_module_variable: bool = False
    projects_result: bool = False
    python_visible: bool = True

    @classmethod
    def result(cls) -> OwnershipContext:
        """Create the context for a direct Python result produced by native code."""
        return cls(location="result", reads_argument=False, writes_argument=True, is_result=True)

    @classmethod
    def argument(
        cls,
        *,
        reads_argument: bool = True,
        writes_argument: bool = False,
        projects_result: bool = False,
        python_visible: bool = True,
    ) -> OwnershipContext:
        """Create an argument context from read, write, projection, and visibility facts."""
        return cls(
            location="argument",
            reads_argument=bool(reads_argument),
            writes_argument=bool(writes_argument),
            is_argument=True,
            projects_result=projects_result,
            python_visible=python_visible,
        )

    @classmethod
    def field(cls) -> OwnershipContext:
        """Create the context for storage owned by a derived-type instance."""
        return cls(location="derived_field", is_field=True)

    @classmethod
    def module_variable(cls) -> OwnershipContext:
        """Create the context for persistent storage owned by a native module."""
        return cls(location="module_variable", is_module_variable=True)


def ownership_context_for_argument(function: Any, argument: Any) -> OwnershipContext:
    """Build the completed-use context for one semantic function argument.

    The function's projection table and argument metadata determine Python
    visibility and result projection; the argument storage then determines
    whether native code may write it.  The returned context is consumed by
    ``OwnershipPolicyResolver`` and does not mutate either input.
    """
    # Derive result projection and Python visibility from the full signature.
    projection = tuple(getattr(function, "projection", ()))
    argument_name = str(getattr(argument, "name", "")).casefold()
    mapping = next(
        (item for item in projection if str(getattr(item, "native_name", "")).casefold() == argument_name),
        None,
    )
    metadata = getattr(argument, "metadata", {}) or {}
    projects_result = bool(metadata.get(PROJECTED_OUTPUT_METADATA))
    projects_result |= mapping is not None and getattr(mapping, "result_position", None) is not None
    python_visible = mapping is None or getattr(mapping, "python_position", None) is not None
    storage = getattr(getattr(argument, "semantic_type", None), "storage", None)
    type_metadata = getattr(getattr(argument, "semantic_type", None), "metadata", {}) or {}
    explicit_policy = type_metadata.get(OWNERSHIP_POLICY_METADATA)
    transfer = explicit_policy.get("transfer") if isinstance(explicit_policy, Mapping) else None
    explicit_call_local_input = transfer == TransferMode.CALL_LOCAL.value and not projects_result
    # A source-free descriptor is a normal input unless its contract projects a result.
    writes_argument = bool(
        projects_result
        or (
            not explicit_call_local_input
            and not _is_source_free_scalar_descriptor_input(argument, type_metadata, projects_result)
            and not _is_source_free_native_array_handle_input(argument, type_metadata, projects_result)
            and _argument_has_mutable_storage(argument, storage)
        )
    )
    return OwnershipContext.argument(
        reads_argument=python_visible,
        writes_argument=writes_argument,
        projects_result=projects_result,
        python_visible=python_visible,
    )


def _is_native_array_handle_facts(facts: _StorageFacts) -> bool:
    """Return whether completed storage facts identify an array descriptor handle."""
    metadata = facts.metadata or {}
    return bool(
        facts.rank > 0
        and (
            facts.allocatable
            or facts.pointer
            or metadata.get(NATIVE_ARRAY_DESCRIPTOR_METADATA) in {"allocatable", "pointer"}
        )
    )


def _is_source_free_scalar_descriptor_input(
    argument: Any,
    type_metadata: Mapping[str, Any],
    projects_result: bool,
) -> bool:
    """Return whether a `.pyi` scalar descriptor argument is a normal scalar input."""
    semantic_type = getattr(argument, "semantic_type", None)
    source_language = getattr(getattr(argument, "origin", None), "source_language", None) or getattr(
        getattr(semantic_type, "origin", None),
        "source_language",
        None,
    )
    return bool(
        not projects_result
        and source_language is None
        and getattr(semantic_type, "rank", None) == 0
        and (type_metadata.get("fortran_allocatable") or type_metadata.get("fortran_pointer"))
    )


def _is_source_free_native_array_handle_input(
    argument: Any,
    type_metadata: Mapping[str, Any],
    projects_result: bool,
) -> bool:
    """Return whether a `.pyi` array descriptor is a normal read-only input."""
    semantic_type = getattr(argument, "semantic_type", None)
    source_language = getattr(getattr(argument, "origin", None), "source_language", None) or getattr(
        getattr(semantic_type, "origin", None),
        "source_language",
        None,
    )
    storage = getattr(semantic_type, "storage", None)
    array_storage = getattr(storage, "array", None)
    descriptor = type_metadata.get(NATIVE_ARRAY_DESCRIPTOR_METADATA)
    return bool(
        not projects_result
        and getattr(semantic_type, "rank", 0) > 0
        and (
            descriptor in {"allocatable", "pointer"}
            or (
                source_language is None
                and (
                    bool(getattr(array_storage, "allocatable", False)) or bool(getattr(array_storage, "pointer", False))
                )
            )
        )
    )


def _argument_has_mutable_storage(argument: Any, storage: Any) -> bool:
    """Return whether an argument's semantic storage implies native writes."""
    ownership = getattr(getattr(argument, "semantic_type", None), "ownership", None)
    if ownership is not None and getattr(ownership, "mutable", False):
        return True
    return bool(
        storage is not None and (getattr(storage, "mutable", False) or not getattr(storage, "read_only", False))
    )


@dataclass(frozen=True)
class OwnershipDecision:
    """The complete ownership and lowering contract for one semantic value.

    Policy completion stores this immutable record beside semantic values and
    wrapper planning projects it into backend-neutral records.  A blocked
    decision carries its diagnostic in ``blocker`` and must not be lowered.

    ``kind`` selects the Python representation. ``owner``, ``transfer``, and
    ``destruction`` form the validated lifetime triple. ``storage_mode`` and
    ``boundary_storage_mode`` describe contract and ABI storage. The three
    action fields select general, Python-barrier, and native-barrier lowering.

    ``nullable`` permits an absent value or descriptor. ``borrowed`` records a
    non-owning relationship. ``mutates_native`` records observable native
    mutation. ``projects_result`` and ``python_visible`` describe the Python
    signature, while ``descriptor_boundary`` selects native descriptor
    transport. ``assignment_mode`` and ``setter_action`` complete property
    write behavior. ``blocker`` explains a fail-closed decision and ``reason``
    explains the selected supported policy.

    For example, a live module array normally has kind ``NUMPY_ARRAY``, owner
    ``NATIVE``, transfer ``BORROWED_VIEW``, destruction ``NATIVE_OWNER``, and
    alias storage. The resulting actions expose native-controlled storage
    without giving Python permission to destroy it.
    """

    kind: ObjectKind
    owner: OwnershipOwner
    transfer: TransferMode
    destruction: DestructionPolicy
    storage_mode: StorageMode = StorageMode.STACK
    boundary_storage_mode: StorageMode | None = None
    codegen_action: CodegenAction = CodegenAction.BLOCKED
    python_barrier_action: PythonBarrierAction = PythonBarrierAction.BLOCKED
    native_barrier_action: NativeBarrierAction = NativeBarrierAction.BLOCKED
    nullable: bool = False
    borrowed: bool = False
    mutates_native: bool = False
    projects_result: bool = False
    python_visible: bool = True
    descriptor_boundary: bool = False
    assignment_mode: AssignmentMode = AssignmentMode.NONE
    setter_action: SetterAction = SetterAction.OMIT
    blocker: str | None = None
    reason: str = ""

    @property
    def owner_label(self) -> str:
        """Return the user-facing label for the selected storage owner."""
        return _OWNER_LABELS[self.owner]

    @property
    def is_blocked(self) -> bool:
        """Report whether this decision intentionally prevents wrapper lowering."""
        return self.transfer is TransferMode.BLOCKED or self.destruction is DestructionPolicy.BLOCKED

    @property
    def is_copy_return(self) -> bool:
        """Report whether the Python result receives independent copied storage."""
        return self.transfer in {TransferMode.COPY_RETURN, TransferMode.SNAPSHOT_COPY}


@dataclass(frozen=True)
class _StorageFacts:
    """Normalized read-only storage facts used internally by resolver decision branches."""

    rank: int
    name: str
    constant: bool = False
    allocatable: bool = False
    pointer: bool = False
    is_ndarray: bool = False
    is_string: bool = False
    is_custom: bool = False
    storage_kind: str = "value"
    address_role: str | None = None
    scalar_storage: bool = False
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class _OwnershipOverride:
    """Hold one normalized explicit lifetime override before it is applied.

    The record contains the effective values selected from explicit metadata
    and the resolver's default decision.  Keeping this intermediate immutable
    separates metadata parsing from decision replacement and safety
    validation.

    For example, metadata requesting ``python/copy_return/python_refcount``
    becomes one record whose ``owner``, ``transfer``, and ``destruction`` are
    the corresponding enums; the later application step also derives its
    storage mode and blocked diagnostic.
    """

    owner: OwnershipOwner
    transfer: TransferMode
    destruction: DestructionPolicy
    nullable: bool
    borrowed: bool
    reason: str


Handler = Callable[[_StorageFacts, OwnershipContext], OwnershipDecision]


# Ownership-policy resolution


class OwnershipPolicyResolver:
    """Resolve semantic storage and use contexts into completed ownership policy.

    Use this resolver during post-IR policy completion.  It classifies the
    semantic type, applies declared ownership metadata, validates unsupported
    combinations, and attaches lowering actions to the returned immutable
    ``OwnershipDecision``.  Backends consume those actions but do not call the
    resolver to invent a policy during lowering.
    """

    def __init__(self, handlers: Mapping[ObjectKind, Handler] | None = None):
        """Initialize standard kind handlers, optionally replacing selected resolver branches.

        ``handlers`` is an internal extension point for callers that need a
        different decision function for an existing object kind.  Unspecified
        kinds keep the standard policy methods.
        """
        self._handlers: dict[ObjectKind, Handler] = {
            ObjectKind.SCALAR: self._scalar_decision,
            ObjectKind.STRING: self._string_decision,
            ObjectKind.NUMPY_ARRAY: self._array_decision,
            ObjectKind.DERIVED_TYPE: self._derived_type_decision,
        }
        if handlers:
            self._handlers.update(handlers)

    def decide_semantic_type(self, semantic_type: Any, context: OwnershipContext) -> OwnershipDecision:
        """Complete ownership, lifetime, and ABI policy for one semantic type.

        Use this primitive when the caller already knows the type's semantic
        location.  It reads type metadata without mutation and returns either
        a lowering-ready decision or a fail-closed decision whose ``blocker``
        explains the unsupported contract.
        """
        # Normalize source/contract representation into resolver-specific facts.
        facts = self._semantic_facts(semantic_type)
        # Choose the default policy for the type kind and semantic location.
        decision = self._decide(facts, context)
        # Apply explicit contract policy, then reject unsafe or contradictory combinations.
        decision = self._apply_overrides(decision, facts, context)
        decision = self._validate_aliased_decision(decision, facts, context)
        decision = self._validate_pointer_decision(decision, facts, context)
        decision = self._complete_immutable_policy(decision, facts, context)
        decision = self._validate_result_projection(decision, context)
        decision = self._validate_policy_combination(decision)
        # Derive lowering actions only after the lifetime contract is final.
        completed = replace(
            decision,
            boundary_storage_mode=decision.boundary_storage_mode or decision.storage_mode,
            codegen_action=self._codegen_action(decision, context),
            projects_result=context.projects_result,
            python_visible=context.python_visible,
        )
        return replace(
            completed,
            python_barrier_action=self._python_barrier_action(completed, facts, context),
            native_barrier_action=self._native_barrier_action(completed, facts, context),
        )

    def decide_semantic_variable(
        self,
        variable: Any,
        context: OwnershipContext | None = None,
    ) -> OwnershipDecision:
        """Complete policy for a semantic variable, inferring its usual location when absent.

        ``context`` overrides automatic field/argument inference.  Optional
        projected outputs gain nullability on the returned decision; neither
        the variable nor its semantic type is modified.
        """
        actual_context = context or self._semantic_variable_context(variable)
        decision = self.decide_semantic_type(variable.semantic_type, actual_context)
        if bool(getattr(variable, "optional", False)) and actual_context.projects_result:
            return replace(decision, nullable=True)
        return decision

    def decide_semantic_getter(
        self,
        variable: Any,
        context: OwnershipContext,
    ) -> OwnershipDecision:
        """Complete the value policy exposed by a field or module-variable getter.

        Array and derived storage retains its storage decision; scalar/string
        getters normally receive result policy so Python observes a value
        rather than native container storage.
        """
        storage = self.decide_semantic_variable(variable, context)
        if storage.is_blocked or storage.kind in {ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}:
            return storage
        if storage.kind is ObjectKind.SCALAR and storage.transfer is TransferMode.SNAPSHOT_COPY:
            return storage
        return self.decide_semantic_type(variable.semantic_type, OwnershipContext.result())

    def decide_semantic_setter(
        self,
        variable: Any,
        context: OwnershipContext,
    ) -> OwnershipDecision:
        """Complete setter exposure and incoming conversion for a field or module variable.

        Constants and blocked storage omit the setter.  Supported storage uses
        argument policy for the incoming value, then records whether lowering
        must copy, alias, reject replacement, or expose write-through.
        """
        storage = self.decide_semantic_variable(variable, context)
        if self._is_semantic_constant(variable.semantic_type):
            return replace(
                storage,
                assignment_mode=AssignmentMode.NONE,
                setter_action=SetterAction.OMIT,
            )
        if storage.is_blocked:
            return replace(
                storage,
                assignment_mode=AssignmentMode.NONE,
                setter_action=SetterAction.OMIT,
            )
        incoming = self.decide_semantic_type(variable.semantic_type, OwnershipContext.argument())
        return replace(
            incoming,
            assignment_mode=(
                AssignmentMode.ALIAS if storage.storage_mode is StorageMode.ALIAS else AssignmentMode.VALUE_COPY
            ),
            setter_action=self._setter_action(storage, incoming, context),
        )

    @staticmethod
    def _setter_action(
        storage: OwnershipDecision,
        incoming: OwnershipDecision,
        context: OwnershipContext,
    ) -> SetterAction:
        """Select Python setter exposure from completed storage and incoming policy.

        The result is a pure action choice.  It preserves special scalar,
        string-field, and derived module-variable rules already decided by the
        ownership contract.
        """
        if storage.kind is ObjectKind.SCALAR:
            if storage.transfer is TransferMode.SNAPSHOT_COPY and storage.nullable:
                return SetterAction.REJECT_REPLACEMENT
            return SetterAction.WRITE_THROUGH
        if storage.kind is ObjectKind.STRING and context.is_field:
            return SetterAction.WRITE_THROUGH
        if storage.kind is ObjectKind.DERIVED_TYPE and context.is_module_variable:
            return SetterAction.REJECT_REPLACEMENT
        if storage.kind is ObjectKind.DERIVED_TYPE and incoming.transfer is TransferMode.CALL_LOCAL:
            return SetterAction.WRITE_THROUGH
        return SetterAction.REJECT_REPLACEMENT

    def decide_semantic_function(self, function: Any, prefix: str = "") -> dict[str, OwnershipDecision]:
        """Return completed decisions for a function's ordered arguments and direct return.

        ``prefix`` namespaces the stable mapping keys for enclosing class or
        overload owners.  Argument contexts use the complete projection table;
        no decision is written back to ``function``.
        """
        name = f"{prefix}{function.name}"
        decisions = {
            f"{name}.{argument.name}": self.decide_semantic_variable(
                argument,
                ownership_context_for_argument(function, argument),
            )
            for argument in getattr(function, "arguments", ())
        }
        return_type = getattr(function, "return_type", None)
        if return_type is not None:
            decisions[f"{name}.return"] = self.decide_semantic_type(return_type, OwnershipContext.result())
        return decisions

    def decide_semantic_class(self, semantic_class: Any, prefix: str = "") -> dict[str, OwnershipDecision]:
        """Return completed decisions for one class, including nested classes and methods.

        Mapping keys follow declaration ownership paths.  Fields use field
        context while methods reuse function processing; the class remains
        unchanged.
        """
        name = f"{prefix}{semantic_class.name}"
        decisions = {
            f"{name}.{field.name}": self.decide_semantic_variable(field, OwnershipContext.field())
            for field in getattr(semantic_class, "fields", ())
        }
        for nested in getattr(semantic_class, "classes", ()):
            decisions.update(self.decide_semantic_class(nested, prefix=f"{name}."))
        for method in getattr(semantic_class, "methods", ()):
            decisions.update(self.decide_semantic_function(method, prefix=f"{name}."))
        return decisions

    def decide_semantic_module(self, module: Any) -> dict[str, OwnershipDecision]:
        """Return completed decisions for module state, classes, functions, and overloads.

        Results are keyed by stable module-qualified paths in declaration order
        where each source collection supplies that order.  This convenience
        traversal is read-only and is normally used for diagnostics or tests;
        policy completion owns metadata attachment.
        """
        name = str(getattr(module, "name", "module"))
        decisions = {
            f"{name}.{variable.name}": self.decide_semantic_variable(
                variable,
                OwnershipContext.module_variable(),
            )
            for variable in getattr(module, "variables", ())
        }
        for semantic_class in getattr(module, "classes", ()):
            decisions.update(self.decide_semantic_class(semantic_class, prefix=f"{name}."))
        for function in getattr(module, "functions", ()):
            decisions.update(self.decide_semantic_function(function, prefix=f"{name}."))
        for overload_set in getattr(module, "overload_sets", ()):
            overload_name = f"{name}.{overload_set.name}"
            for procedure in getattr(overload_set, "procedures", ()):
                decisions.update(self.decide_semantic_function(procedure, prefix=f"{overload_name}."))
        return decisions

    def _decide(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Choose the unoverridden decision branch for normalized facts and location."""
        if context.is_module_variable:
            return self._module_variable_decision(facts, context)
        if context.is_field:
            return self._derived_field_decision(facts, context)
        kind = self._kind(facts, context)
        return self._handlers[kind](facts, context)

    def _kind(self, facts: _StorageFacts, context: OwnershipContext) -> ObjectKind:
        """Classify normalized storage into the resolver's four policy categories."""
        if facts.scalar_storage and not facts.is_string and not facts.allocatable and not facts.pointer:
            return ObjectKind.NUMPY_ARRAY
        if facts.rank > 0 or facts.is_ndarray:
            return ObjectKind.NUMPY_ARRAY
        if facts.is_string:
            return ObjectKind.STRING
        if facts.is_custom:
            return ObjectKind.DERIVED_TYPE
        return ObjectKind.SCALAR

    def _scalar_decision(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return default scalar policy, delegating specialized storage and address cases."""
        if facts.scalar_storage:
            return self._scalar_storage_decision(facts, context)
        if facts.address_role == ADDRESS_ROLE_PROJECTION:
            return self._address_projection_scalar_decision(facts, context)
        if facts.allocatable:
            return self._allocatable_scalar_decision(facts, context)
        if facts.pointer:
            return self._pointer_scalar_decision(facts, context)
        if context.is_result:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.BY_VALUE,
                DestructionPolicy.PYTHON_REFCOUNT,
                reason="scalar output is returned as a Python value",
            )
        if context.writes_argument and not context.reads_argument:
            if not context.projects_result:
                return OwnershipDecision(
                    ObjectKind.SCALAR,
                    OwnershipOwner.CALLER,
                    TransferMode.IN_PLACE,
                    DestructionPolicy.CALLER,
                    mutates_native=True,
                    reason="identity scalar output writes caller-provided storage",
                )
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.BY_VALUE,
                DestructionPolicy.PYTHON_REFCOUNT,
                mutates_native=True,
                reason="scalar output is returned as a Python value",
            )
        if context.writes_argument and context.reads_argument:
            if context.projects_result:
                return OwnershipDecision(
                    ObjectKind.SCALAR,
                    OwnershipOwner.PYTHON,
                    TransferMode.COPY_RETURN,
                    DestructionPolicy.PYTHON_REFCOUNT,
                    mutates_native=True,
                    reason="projected scalar update uses call-local native storage and returns a replacement value",
                )
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.CALLER,
                TransferMode.IN_PLACE,
                DestructionPolicy.CALLER,
                mutates_native=True,
                reason="scalar update mutates caller-visible storage",
            )
        return OwnershipDecision(
            ObjectKind.SCALAR,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            reason="scalar input is converted for the call only",
        )

    @staticmethod
    def _scalar_storage_decision(facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return policy for rank-zero scalar storage exposed through an array-like boundary."""
        if context.is_result:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.BY_VALUE,
                DestructionPolicy.PYTHON_REFCOUNT,
                reason="scalar storage is returned as a Python value",
            )
        if context.writes_argument:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.CALLER,
                TransferMode.IN_PLACE,
                DestructionPolicy.CALLER,
                mutates_native=True,
                reason="rank-0 scalar storage mutates caller-provided NumPy storage",
            )
        return OwnershipDecision(
            ObjectKind.SCALAR,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            reason="rank-0 scalar storage is borrowed for the duration of the call",
        )

    @staticmethod
    def _address_projection_scalar_decision(facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return policy for a scalar passed through its explicit native-address projection."""
        if context.is_result:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.BY_VALUE,
                DestructionPolicy.PYTHON_REFCOUNT,
                reason="address-projected scalar result is returned as a Python value",
            )
        if context.writes_argument and context.reads_argument and context.projects_result:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.COPY_RETURN,
                DestructionPolicy.PYTHON_REFCOUNT,
                mutates_native=True,
                reason="address-projected scalar value uses mutable native storage and a replacement return",
            )
        if context.writes_argument and context.projects_result and not context.python_visible:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.BY_VALUE,
                DestructionPolicy.PYTHON_REFCOUNT,
                mutates_native=True,
                reason="address-projected hidden scalar output is returned as a Python value",
            )
        return OwnershipDecision(
            ObjectKind.SCALAR,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            storage_mode=StorageMode.ALIAS,
            mutates_native=context.writes_argument,
            reason="address-projected scalar value passes the address of call-local native storage",
        )

    def _allocatable_scalar_decision(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return detached accessor or descriptor-boundary policy for an allocatable scalar."""
        if context.is_field or context.is_module_variable:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.SNAPSHOT_COPY,
                DestructionPolicy.PYTHON_REFCOUNT,
                storage_mode=StorageMode.HEAP,
                nullable=True,
                reason="allocatable scalar storage is copied into a detached Python value",
            )
        return self._function_scalar_descriptor_decision(
            facts,
            context,
            StorageMode.HEAP,
            reason="allocatable scalar function boundary uses a normal Python scalar and a call-local native descriptor",
        )

    def _pointer_scalar_decision(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return detached accessor or descriptor-boundary policy for a pointer scalar."""
        if context.is_field or context.is_module_variable:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.SNAPSHOT_COPY,
                DestructionPolicy.PYTHON_REFCOUNT,
                storage_mode=StorageMode.ALIAS,
                nullable=True,
                reason="pointer scalar result is copied into a detached Python value",
            )
        return self._function_scalar_descriptor_decision(
            facts,
            context,
            StorageMode.ALIAS,
            reason="pointer scalar function boundary uses a normal Python scalar and a call-local native descriptor",
        )

    def _function_scalar_descriptor_decision(
        self,
        facts: _StorageFacts,
        context: OwnershipContext,
        boundary_storage_mode: StorageMode,
        *,
        reason: str,
    ) -> OwnershipDecision:
        """Return scalar descriptor policy for a function argument or result boundary.

        ``boundary_storage_mode`` identifies allocatable versus pointer ABI
        storage.  Writable descriptors must project an output or return a
        blocked decision, keeping replacement semantics explicit.
        """
        if context.is_result:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.SNAPSHOT_COPY,
                DestructionPolicy.PYTHON_REFCOUNT,
                storage_mode=boundary_storage_mode,
                boundary_storage_mode=boundary_storage_mode,
                nullable=True,
                descriptor_boundary=True,
                reason=reason,
            )
        if context.writes_argument and not context.projects_result:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.UNKNOWN,
                TransferMode.BLOCKED,
                DestructionPolicy.BLOCKED,
                boundary_storage_mode=boundary_storage_mode,
                nullable=True,
                descriptor_boundary=True,
                blocker="scalar descriptor writes must be projected into the Python return annotation",
                reason=reason,
            )
        if context.writes_argument and context.reads_argument:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.COPY_RETURN,
                DestructionPolicy.PYTHON_REFCOUNT,
                boundary_storage_mode=boundary_storage_mode,
                nullable=True,
                mutates_native=True,
                projects_result=True,
                descriptor_boundary=True,
                reason=reason,
            )
        if context.writes_argument:
            return OwnershipDecision(
                ObjectKind.SCALAR,
                OwnershipOwner.PYTHON,
                TransferMode.BY_VALUE,
                DestructionPolicy.PYTHON_REFCOUNT,
                boundary_storage_mode=boundary_storage_mode,
                nullable=True,
                mutates_native=True,
                projects_result=True,
                python_visible=False,
                descriptor_boundary=True,
                reason=reason,
            )
        return OwnershipDecision(
            ObjectKind.SCALAR,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            boundary_storage_mode=boundary_storage_mode,
            nullable=True,
            descriptor_boundary=True,
            reason=reason,
        )

    def _string_decision(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return default string policy after handling descriptor, raw-address, and storage cases."""
        descriptor_decision = self._string_descriptor_decision(facts, context)
        if descriptor_decision is not None:
            return descriptor_decision
        if facts.address_role == ADDRESS_ROLE_RAW:
            return OwnershipDecision(
                ObjectKind.STRING,
                OwnershipOwner.CALLER,
                TransferMode.IN_PLACE,
                DestructionPolicy.CALLER,
                mutates_native=True,
                reason="raw string address aliases caller-owned fixed-width storage",
            )
        if facts.scalar_storage:
            return self._scalar_string_storage_decision(context)
        if context.is_result:
            return OwnershipDecision(
                ObjectKind.STRING,
                OwnershipOwner.PYTHON,
                TransferMode.COPY_RETURN,
                DestructionPolicy.PYTHON_REFCOUNT,
                reason="string output is copied into a Python string",
            )
        if context.writes_argument and not context.reads_argument:
            return self._string_output_argument_decision(context)
        if context.writes_argument and context.reads_argument:
            return self._string_update_argument_decision(context)
        return OwnershipDecision(
            ObjectKind.STRING,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            reason="string input is converted for the call only",
        )

    @staticmethod
    def _string_descriptor_decision(
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> OwnershipDecision | None:
        """Return a scalar string descriptor decision when storage requires one, else ``None``."""
        if not (facts.allocatable or facts.pointer):
            return None

        storage = StorageMode.HEAP if facts.allocatable else StorageMode.ALIAS
        if context.is_result:
            return OwnershipDecision(
                ObjectKind.STRING,
                OwnershipOwner.PYTHON,
                TransferMode.COPY_RETURN,
                DestructionPolicy.PYTHON_REFCOUNT,
                storage_mode=storage,
                boundary_storage_mode=storage,
                nullable=True,
                descriptor_boundary=True,
                reason="scalar string descriptor result is copied before native descriptor release",
            )
        if context.writes_argument and context.projects_result and not context.python_visible:
            return OwnershipDecision(
                ObjectKind.STRING,
                OwnershipOwner.PYTHON,
                TransferMode.COPY_RETURN,
                DestructionPolicy.PYTHON_REFCOUNT,
                storage_mode=storage,
                boundary_storage_mode=storage,
                nullable=True,
                descriptor_boundary=True,
                mutates_native=True,
                projects_result=True,
                python_visible=False,
                reason="hidden scalar string descriptor output is copied before native descriptor release",
            )
        return None

    @staticmethod
    def _scalar_string_storage_decision(context: OwnershipContext) -> OwnershipDecision:
        """Return aliasing or call-local policy for rank-zero mutable character storage."""
        if context.is_result:
            return OwnershipDecision(
                ObjectKind.STRING,
                OwnershipOwner.PYTHON,
                TransferMode.COPY_RETURN,
                DestructionPolicy.PYTHON_REFCOUNT,
                reason="scalar string storage result is copied into a Python string",
            )
        if context.writes_argument:
            return OwnershipDecision(
                ObjectKind.STRING,
                OwnershipOwner.CALLER,
                TransferMode.IN_PLACE,
                DestructionPolicy.CALLER,
                storage_mode=StorageMode.ALIAS,
                mutates_native=True,
                reason="rank-0 string storage mutates caller-provided NumPy bytes storage",
            )
        return OwnershipDecision(
            ObjectKind.STRING,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            storage_mode=StorageMode.ALIAS,
            reason="rank-0 string storage is borrowed for the duration of the call",
        )

    @staticmethod
    def _string_output_argument_decision(context: OwnershipContext) -> OwnershipDecision:
        """Return string-output policy, copying only when its mutation is projected to Python."""
        if not context.projects_result:
            return OwnershipDecision(
                ObjectKind.STRING,
                OwnershipOwner.TEMPORARY,
                TransferMode.CALL_LOCAL,
                DestructionPolicy.CALL_LOCAL,
                mutates_native=True,
                reason="identity string output uses temporary storage and discards native mutation",
            )
        return OwnershipDecision(
            ObjectKind.STRING,
            OwnershipOwner.PYTHON,
            TransferMode.COPY_RETURN,
            DestructionPolicy.PYTHON_REFCOUNT,
            mutates_native=True,
            reason="string output is copied into a Python string",
        )

    @staticmethod
    def _string_update_argument_decision(context: OwnershipContext) -> OwnershipDecision:
        """Return string update policy, preserving immutable Python replacement semantics."""
        if not context.projects_result:
            return OwnershipDecision(
                ObjectKind.STRING,
                OwnershipOwner.TEMPORARY,
                TransferMode.CALL_LOCAL,
                DestructionPolicy.CALL_LOCAL,
                mutates_native=True,
                reason="string update uses a mutable call-local copy and discards native mutation",
            )
        return OwnershipDecision(
            ObjectKind.STRING,
            OwnershipOwner.PYTHON,
            TransferMode.COPY_RETURN,
            DestructionPolicy.PYTHON_REFCOUNT,
            mutates_native=True,
            reason="immutable Python strings use copy-in/copy-out replacement for updates",
        )

    def _array_decision(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return array or native-descriptor policy for the current semantic location."""
        if _is_native_array_handle_facts(facts):
            if context.is_argument:
                if context.projects_result and not context.python_visible:
                    return self._native_array_handle_projected_output_decision(facts)
                return self._native_array_handle_argument_decision(facts, context)
            if context.is_result:
                return self._native_array_handle_result_decision(facts)
        if facts.pointer:
            return self._pointer_array_decision(facts, context)
        if facts.allocatable:
            return self._allocatable_array_decision(facts, context)
        if context.is_result:
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                OwnershipOwner.PYTHON,
                TransferMode.COPY_RETURN,
                DestructionPolicy.PYTHON_REFCOUNT,
                reason="array result is returned as Python-owned NumPy storage",
            )
        if context.writes_argument and context.projects_result and not context.python_visible:
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                OwnershipOwner.PYTHON,
                TransferMode.COPY_RETURN,
                DestructionPolicy.PYTHON_REFCOUNT,
                mutates_native=True,
                reason="hidden array output is copied into Python-owned NumPy storage",
            )
        if context.writes_argument:
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                OwnershipOwner.CALLER,
                TransferMode.IN_PLACE,
                DestructionPolicy.CALLER,
                mutates_native=True,
                reason="explicit-shape array output mutates caller storage",
            )
        return OwnershipDecision(
            ObjectKind.NUMPY_ARRAY,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            reason="array input is borrowed for the duration of the call",
        )

    @staticmethod
    def _native_array_handle_argument_decision(
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> OwnershipDecision:
        """Pass a native descriptor handle as a caller-owned descriptor argument.

        Writable pointer descriptors require explicit pointer-policy metadata;
        all other supported handle inputs retain the caller's handle identity.
        """
        if context.writes_argument:
            if facts.pointer and not isinstance((facts.metadata or {}).get(POINTER_POLICY_METADATA), Mapping):
                return OwnershipDecision(
                    ObjectKind.NUMPY_ARRAY,
                    OwnershipOwner.UNKNOWN,
                    TransferMode.BLOCKED,
                    DestructionPolicy.BLOCKED,
                    storage_mode=StorageMode.ALIAS,
                    boundary_storage_mode=StorageMode.ALIAS,
                    nullable=True,
                    descriptor_boundary=True,
                    blocker="pointer array dummy reassociation needs explicit PointerPolicy metadata",
                    reason="writable pointer descriptor ownership and reassociation are not implicit",
                )
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                OwnershipOwner.CALLER,
                TransferMode.IN_PLACE,
                DestructionPolicy.CALLER,
                storage_mode=StorageMode.ALIAS if facts.pointer else StorageMode.HEAP,
                boundary_storage_mode=StorageMode.ALIAS,
                nullable=True,
                borrowed=True,
                mutates_native=True,
                descriptor_boundary=True,
                reason="native array handle argument passes a caller descriptor that native code may update",
            )
        return OwnershipDecision(
            ObjectKind.NUMPY_ARRAY,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            storage_mode=StorageMode.ALIAS if facts.pointer else StorageMode.HEAP,
            boundary_storage_mode=StorageMode.ALIAS,
            nullable=True,
            borrowed=True,
            descriptor_boundary=True,
            reason="native array handle argument passes the caller descriptor for the call",
        )

    @staticmethod
    def _native_array_handle_projected_output_decision(facts: _StorageFacts) -> OwnershipDecision:
        """Create stable wrapper-owned storage for a Python-hidden descriptor output."""
        return OwnershipDecision(
            ObjectKind.NUMPY_ARRAY,
            OwnershipOwner.WRAPPER,
            TransferMode.WRAPPER_INSTANCE,
            DestructionPolicy.WRAPPER_DEALLOC,
            storage_mode=StorageMode.HEAP,
            boundary_storage_mode=StorageMode.ALIAS,
            nullable=True,
            borrowed=False,
            mutates_native=True,
            descriptor_boundary=True,
            reason="hidden descriptor output moves into wrapper-owned stable descriptor storage",
        )

    @staticmethod
    def _native_array_handle_result_decision(facts: _StorageFacts) -> OwnershipDecision:
        """Materialize a supported direct descriptor result as one runtime handle."""
        return OwnershipDecision(
            ObjectKind.NUMPY_ARRAY,
            OwnershipOwner.WRAPPER,
            TransferMode.WRAPPER_INSTANCE,
            DestructionPolicy.WRAPPER_DEALLOC,
            storage_mode=StorageMode.HEAP,
            boundary_storage_mode=StorageMode.ALIAS,
            nullable=True,
            descriptor_boundary=True,
            reason="descriptor result moves into wrapper-owned stable descriptor storage",
        )

    def _allocatable_array_decision(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return allocatable-array policy for fields, module state, calls, or results."""
        if context.is_field:
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                OwnershipOwner.WRAPPER,
                TransferMode.BORROWED_VIEW,
                DestructionPolicy.WRAPPER_DEALLOC,
                storage_mode=StorageMode.HEAP,
                boundary_storage_mode=StorageMode.ALIAS,
                nullable=True,
                borrowed=True,
                reason="allocatable field storage is owned by the containing wrapper instance",
            )
        if context.is_module_variable:
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                OwnershipOwner.NATIVE,
                TransferMode.BORROWED_VIEW,
                DestructionPolicy.NATIVE_OWNER,
                storage_mode=StorageMode.HEAP,
                boundary_storage_mode=StorageMode.ALIAS,
                nullable=True,
                borrowed=True,
                reason="allocatable module storage is borrowed from the native module",
            )
        if context.is_result or context.writes_argument:
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                OwnershipOwner.PYTHON,
                TransferMode.COPY_RETURN,
                DestructionPolicy.PYTHON_REFCOUNT,
                storage_mode=StorageMode.HEAP,
                nullable=True,
                reason="allocatable array output is copied before native storage is released",
            )
        return OwnershipDecision(
            ObjectKind.NUMPY_ARRAY,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            storage_mode=StorageMode.HEAP,
            nullable=True,
            reason="allocatable array input is associated only for the call",
        )

    def _pointer_array_decision(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return pointer-array policy without claiming ownership of an unknown target."""
        if context.is_field or context.is_module_variable:
            owner = OwnershipOwner.WRAPPER if context.is_field else OwnershipOwner.NATIVE
            destruction = DestructionPolicy.WRAPPER_DEALLOC if context.is_field else DestructionPolicy.NATIVE_OWNER
            reason = (
                "pointer array field exposes descriptor association without target ownership"
                if context.is_field
                else "pointer array module variable exposes descriptor association without target ownership"
            )
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                owner,
                TransferMode.BORROWED_VIEW,
                destruction,
                storage_mode=StorageMode.ALIAS,
                boundary_storage_mode=StorageMode.ALIAS,
                nullable=True,
                borrowed=True,
                reason=reason,
            )
        if context.is_result:
            return self._native_array_handle_result_decision(facts)
        if context.writes_argument:
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                OwnershipOwner.UNKNOWN,
                TransferMode.BLOCKED,
                DestructionPolicy.BLOCKED,
                storage_mode=StorageMode.ALIAS,
                nullable=True,
                blocker="pointer array writable reassociation policy is unknown",
                reason="pointer array dummy reassociation needs explicit policy metadata",
            )
        return OwnershipDecision(
            ObjectKind.NUMPY_ARRAY,
            OwnershipOwner.CALLER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            storage_mode=StorageMode.ALIAS,
            reason="pointer input is associated with caller storage only for the call",
        )

    def _derived_type_decision(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return wrapper-instance policy for derived values, arguments, and outputs."""
        descriptor_boundary = facts.allocatable or facts.pointer
        boundary_storage = StorageMode.HEAP if facts.allocatable else StorageMode.ALIAS
        argument_boundary_storage = StorageMode.ALIAS
        if context.is_result or (
            context.writes_argument
            and not context.reads_argument
            and context.projects_result
            and not context.python_visible
        ):
            return OwnershipDecision(
                ObjectKind.DERIVED_TYPE,
                OwnershipOwner.WRAPPER,
                TransferMode.WRAPPER_INSTANCE,
                DestructionPolicy.WRAPPER_DEALLOC,
                storage_mode=StorageMode.HEAP,
                boundary_storage_mode=boundary_storage,
                nullable=descriptor_boundary,
                descriptor_boundary=descriptor_boundary,
                reason="derived output is represented by a wrapper-owned native instance",
            )
        if context.writes_argument and not context.reads_argument:
            return OwnershipDecision(
                ObjectKind.DERIVED_TYPE,
                OwnershipOwner.WRAPPER,
                TransferMode.IN_PLACE,
                DestructionPolicy.WRAPPER_DEALLOC,
                storage_mode=StorageMode.ALIAS,
                boundary_storage_mode=argument_boundary_storage,
                nullable=descriptor_boundary,
                descriptor_boundary=descriptor_boundary,
                mutates_native=True,
                reason="identity derived output mutates the supplied wrapper instance",
            )
        if context.writes_argument and context.reads_argument:
            return OwnershipDecision(
                ObjectKind.DERIVED_TYPE,
                OwnershipOwner.WRAPPER,
                TransferMode.IN_PLACE,
                DestructionPolicy.WRAPPER_DEALLOC,
                storage_mode=StorageMode.ALIAS,
                boundary_storage_mode=argument_boundary_storage,
                nullable=descriptor_boundary,
                descriptor_boundary=descriptor_boundary,
                mutates_native=True,
                reason="derived update mutates the wrapper-owned native instance",
            )
        return OwnershipDecision(
            ObjectKind.DERIVED_TYPE,
            OwnershipOwner.WRAPPER,
            TransferMode.CALL_LOCAL,
            DestructionPolicy.NONE,
            storage_mode=StorageMode.ALIAS,
            boundary_storage_mode=argument_boundary_storage,
            nullable=descriptor_boundary,
            descriptor_boundary=descriptor_boundary,
            reason="derived input is passed through its existing wrapper",
        )

    def _module_variable_decision(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return policy for persistent module storage, preserving native ownership by default."""
        if facts.constant:
            return self._module_constant_decision(facts)
        if facts.is_custom:
            return OwnershipDecision(
                ObjectKind.DERIVED_TYPE,
                OwnershipOwner.NATIVE,
                TransferMode.BORROWED_VIEW,
                DestructionPolicy.NATIVE_OWNER,
                storage_mode=StorageMode.ALIAS,
                boundary_storage_mode=StorageMode.ALIAS,
                nullable=facts.allocatable or facts.pointer,
                borrowed=True,
                reason=(
                    "addressable derived module storage uses a live native borrow"
                    if (facts.metadata or {}).get("aliased")
                    else "plain derived module storage uses live typed module access"
                ),
            )
        if facts.allocatable and facts.rank == 0:
            return self._allocatable_scalar_decision(facts, context)
        if facts.pointer and facts.rank == 0:
            return self._pointer_scalar_decision(facts, context)
        if facts.rank > 0 or facts.is_ndarray:
            if facts.pointer:
                return self._pointer_array_decision(facts, context)
            if facts.allocatable:
                return self._allocatable_array_decision(facts, context)
        return OwnershipDecision(
            self._kind(facts, OwnershipContext()),
            OwnershipOwner.NATIVE,
            TransferMode.BORROWED_VIEW,
            DestructionPolicy.NATIVE_OWNER,
            storage_mode=StorageMode.ALIAS if facts.rank > 0 else StorageMode.STACK,
            borrowed=True,
            reason="module variable storage is owned by native module state",
        )

    def _module_constant_decision(self, facts: _StorageFacts) -> OwnershipDecision:
        """Return immutable value policy for one module-level constant."""
        if facts.rank > 0 or facts.is_ndarray:
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                OwnershipOwner.PYTHON,
                TransferMode.BY_VALUE,
                DestructionPolicy.PYTHON_REFCOUNT,
                storage_mode=StorageMode.HEAP,
                reason="module array constants are materialized once as immutable Python-owned snapshots",
            )
        if facts.is_custom:
            return OwnershipDecision(
                ObjectKind.DERIVED_TYPE,
                OwnershipOwner.WRAPPER,
                TransferMode.WRAPPER_INSTANCE,
                DestructionPolicy.WRAPPER_DEALLOC,
                storage_mode=StorageMode.STACK,
                reason="derived module constant is materialized as a wrapper-owned value copy",
            )
        return OwnershipDecision(
            self._kind(facts, OwnershipContext()),
            OwnershipOwner.PYTHON,
            TransferMode.BY_VALUE,
            DestructionPolicy.PYTHON_REFCOUNT,
            storage_mode=StorageMode.STACK,
            reason="module constant is materialized directly as an immutable Python value",
        )

    def _derived_field_decision(self, facts: _StorageFacts, context: OwnershipContext) -> OwnershipDecision:
        """Return policy for storage that remains owned by the containing derived wrapper."""
        if facts.allocatable and facts.rank == 0:
            return self._allocatable_scalar_decision(facts, context)
        if facts.pointer and facts.rank == 0:
            return self._pointer_scalar_decision(facts, context)
        if facts.rank > 0 or facts.is_ndarray:
            if facts.pointer:
                return self._pointer_array_decision(facts, context)
            if facts.allocatable:
                return self._allocatable_array_decision(facts, context)
            return OwnershipDecision(
                ObjectKind.NUMPY_ARRAY,
                OwnershipOwner.WRAPPER,
                TransferMode.BORROWED_VIEW,
                DestructionPolicy.WRAPPER_DEALLOC,
                storage_mode=StorageMode.STACK,
                boundary_storage_mode=StorageMode.ALIAS,
                borrowed=True,
                reason="array field storage is part of the containing wrapper instance",
            )
        if self._kind(facts, OwnershipContext()) is ObjectKind.STRING:
            return OwnershipDecision(
                ObjectKind.STRING,
                OwnershipOwner.PYTHON,
                TransferMode.COPY_RETURN,
                DestructionPolicy.PYTHON_REFCOUNT,
                storage_mode=StorageMode.STACK,
                boundary_storage_mode=StorageMode.STACK,
                borrowed=False,
                reason="fixed string field access copies the current value into Python storage",
            )
        return OwnershipDecision(
            self._kind(facts, OwnershipContext()),
            OwnershipOwner.WRAPPER,
            TransferMode.BORROWED_VIEW,
            DestructionPolicy.WRAPPER_DEALLOC,
            storage_mode=StorageMode.STACK,
            boundary_storage_mode=StorageMode.ALIAS if facts.is_custom else StorageMode.STACK,
            borrowed=True,
            reason="field storage is part of the containing wrapper instance",
        )

    def _apply_overrides(
        self,
        decision: OwnershipDecision,
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> OwnershipDecision:
        """Apply declared ownership metadata without bypassing later safety validation.

        Pointer container metadata stays separate from general ownership
        overrides. Unsupported borrowed pointer views become blocked here so
        lower stages cannot fabricate target retention.

        For example, an array result default can be overridden with
        ``python/copy_return/python_refcount``. The method selects that metadata,
        normalizes it into ``_OwnershipOverride``, applies storage invariants,
        and returns a new decision. A pointer requesting ``borrowed_view`` is
        instead returned as an explicit blocked decision.
        """
        # Select the applicable general or non-container pointer metadata.
        raw = self._ownership_override_metadata(facts, context)
        if raw is None:
            return decision

        # Normalize the owner before pointer rejection to preserve metadata diagnostics.
        owner = self._enum_value(OwnershipOwner, raw.get("owner"), decision.owner)

        # Normalize the transfer used to select the supported or blocked path.
        transfer = self._enum_value(TransferMode, raw.get("transfer"), decision.transfer)

        # Fail closed before parsing later fields when pointer borrowing has no lifetime proof.
        blocked = self._blocked_borrowed_pointer_override(decision, facts, raw, transfer)
        if blocked is not None:
            return blocked

        # Convert all remaining metadata into one immutable effective override.
        override = self._ownership_override(decision, raw, owner, transfer)

        # Apply the normalized values while preserving pointer and allocatable storage invariants.
        return self._decision_with_ownership_override(decision, facts, override)

    @staticmethod
    def _ownership_override_metadata(
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> Mapping[str, Any] | None:
        """Select the explicit lifetime metadata that applies to one value.

        ``facts`` supplies the type metadata and pointer/storage category;
        ``context`` identifies whether a pointer is a descriptor container.
        General ``ownership_policy`` metadata is returned as-is. For a
        non-container pointer, ``pointer_policy`` values override matching
        general keys. Pointer-array containers keep the two contracts separate
        because their descriptor ownership is fixed by their native parent.

        For example, a scalar pointer with general owner ``native`` and pointer
        transfer ``call_local`` returns a merged mapping containing both
        values. A pointer-array field returns only its general ownership mapping.
        """
        metadata = facts.metadata or {}
        raw = metadata.get(OWNERSHIP_POLICY_METADATA)
        pointer_policy = metadata.get(POINTER_POLICY_METADATA)

        # Identify descriptor containers whose parent fixes their ownership.
        pointer_container = OwnershipPolicyResolver._is_pointer_container(facts, context)
        if facts.pointer and isinstance(pointer_policy, Mapping) and not pointer_container:
            raw = {**(raw if isinstance(raw, Mapping) else {}), **pointer_policy}
        if not isinstance(raw, Mapping):
            return None
        return raw

    @staticmethod
    def _is_pointer_container(facts: _StorageFacts, context: OwnershipContext) -> bool:
        """Return whether a pointer value is a native descriptor container.

        ``facts`` supplies pointer and rank information, while ``context`` says
        whether the value belongs to an argument, field, module variable, or
        result. A rank-positive pointer in one of those locations has native
        descriptor identity whose container ownership must not be replaced by
        target-oriented ``PointerPolicy`` metadata.

        For example, a pointer-array field returns ``True`` because its parent
        wrapper owns the descriptor container. A scalar pointer or neutral
        temporary returns ``False`` and may merge pointer-policy transfer facts
        into the general override.
        """
        owner_contexts = (
            context.is_argument,
            context.is_field,
            context.is_module_variable,
            context.is_result,
        )
        return bool(facts.pointer and facts.rank > 0 and any(owner_contexts))

    @staticmethod
    def _blocked_borrowed_pointer_override(
        decision: OwnershipDecision,
        facts: _StorageFacts,
        raw: Mapping[str, Any],
        transfer: TransferMode,
    ) -> OwnershipDecision | None:
        """Return the fail-closed decision for unsupported pointer borrowing.

        The default ``decision`` supplies unrelated completed fields, ``facts``
        identifies whether storage is a pointer, ``raw`` supplies explicit
        nullability, and ``transfer`` is the already-normalized requested mode.
        Non-pointer and non-borrowed requests return ``None`` so normal override
        application can continue.

        For example, a pointer request with ``transfer='borrowed_view'`` returns
        ``UNKNOWN/BLOCKED/BLOCKED`` and explains the missing owner retention and
        stale-view invalidation mechanism.
        """
        if facts.pointer and transfer is TransferMode.BORROWED_VIEW:
            # Preserve unrelated fields while replacing every unsafe lifetime axis.
            return replace(
                decision,
                owner=OwnershipOwner.UNKNOWN,
                transfer=TransferMode.BLOCKED,
                destruction=DestructionPolicy.BLOCKED,
                storage_mode=StorageMode.ALIAS,
                nullable=bool(raw.get("nullable", True)),
                borrowed=False,
                blocker="borrowed pointer views need native-owner retention and stale-view invalidation",
                reason="borrowed pointer views are not implemented",
            )
        return None

    def _ownership_override(
        self,
        decision: OwnershipDecision,
        raw: Mapping[str, Any],
        owner: OwnershipOwner,
        transfer: TransferMode,
    ) -> _OwnershipOverride:
        """Normalize explicit metadata against an existing default decision.

        ``owner`` and ``transfer`` have already been validated because pointer
        borrowing must be rejected before later metadata is interpreted. This
        helper validates destruction, fills omitted Boolean and reason fields
        from ``decision``, and returns an immutable value without applying it.

        For example, ``{'destruction': 'python_refcount'}`` combined with a
        preselected ``PYTHON`` owner and ``COPY_RETURN`` transfer produces an
        override with ``DestructionPolicy.PYTHON_REFCOUNT`` while preserving the
        decision's nullability.
        """
        # Normalize release responsibility only after pointer-specific rejection.
        destruction = self._enum_value(DestructionPolicy, raw.get("destruction"), decision.destruction)
        # Package the effective fields without mutating the resolver's default decision.
        return _OwnershipOverride(
            owner=owner,
            transfer=transfer,
            destruction=destruction,
            nullable=bool(raw.get("nullable", decision.nullable)),
            borrowed=transfer is TransferMode.BORROWED_VIEW or bool(raw.get("borrowed", decision.borrowed)),
            reason=str(raw.get("reason", "explicit ownership policy metadata")),
        )

    def _decision_with_ownership_override(
        self,
        decision: OwnershipDecision,
        facts: _StorageFacts,
        override: _OwnershipOverride,
    ) -> OwnershipDecision:
        """Apply one normalized override while preserving storage invariants.

        ``decision`` is the resolver default, ``facts`` supplies pointer,
        allocatable, and array storage constraints, and ``override`` supplies
        the effective lifetime fields. The result is a new decision; later
        resolver steps still validate the triple and derive lowering actions.

        For example, an allocatable result overridden to ``snapshot_copy``
        remains heap-backed, while a borrowed ordinary array is forced to alias
        storage. An explicit ``blocked`` transfer also gains a stable blocker
        when the default decision had none.
        """
        # Derive storage from the normalized transfer without violating native storage facts.
        storage_mode = self._storage_for_override(facts, override.transfer, decision.storage_mode)
        blocker = (
            None if override.transfer is not TransferMode.BLOCKED else decision.blocker or "blocked by ownership policy"
        )
        # Return a new decision for the resolver's later validation and action derivation.
        return replace(
            decision,
            owner=override.owner,
            transfer=override.transfer,
            destruction=override.destruction,
            storage_mode=storage_mode,
            nullable=override.nullable,
            borrowed=override.borrowed,
            blocker=blocker,
            reason=override.reason,
        )

    @staticmethod
    def _validate_aliased_decision(
        decision: OwnershipDecision,
        _facts: _StorageFacts,
        _context: OwnershipContext,
    ) -> OwnershipDecision:
        """Keep Aliased as addressability metadata, not live-object eligibility."""
        return decision

    @staticmethod
    def _validate_pointer_decision(
        decision: OwnershipDecision,
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> OwnershipDecision:
        """Block pointer cases whose requested lifetime or reassociation mechanism is unsupported."""
        if not facts.pointer or decision.is_blocked:
            return decision
        if (context.is_argument or context.is_result) and _is_native_array_handle_facts(facts):
            return decision
        blocker = OwnershipPolicyResolver._pointer_argument_blocker(
            decision, facts, context
        ) or OwnershipPolicyResolver._pointer_container_blocker(decision, facts, context)
        if blocker is None:
            return decision
        return replace(
            decision,
            owner=OwnershipOwner.UNKNOWN,
            transfer=TransferMode.BLOCKED,
            destruction=DestructionPolicy.BLOCKED,
            borrowed=False,
            blocker=blocker,
            reason="requested pointer policy is not implemented by code generation",
        )

    @staticmethod
    def _pointer_argument_blocker(
        decision: OwnershipDecision,
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> str | None:
        """Return a blocker for an unsupported pointer argument policy."""
        if not context.is_argument:
            return None
        if facts.rank == 0 and facts.is_custom and decision.kind is ObjectKind.DERIVED_TYPE:
            # Scalar-derived pointer calls are completed by the actual/dummy
            # handoff policy.  Their association and writeback rules do not
            # use the older scalar/array descriptor projection lane below.
            return None
        supported_scalar_write = facts.rank == 0 and decision.descriptor_boundary and context.projects_result
        if context.writes_argument and not supported_scalar_write:
            return "pointer output and reassociation code generation is not implemented"
        if not context.writes_argument and decision.transfer is not TransferMode.CALL_LOCAL:
            return "pointer input arguments currently require call_local transfer"
        return None

    @staticmethod
    def _pointer_container_blocker(
        decision: OwnershipDecision,
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> str | None:
        """Return a blocker for an unsupported pointer field or module policy."""
        if not (context.is_field or context.is_module_variable):
            return None
        if facts.is_custom and decision.kind is ObjectKind.DERIVED_TYPE:
            return None
        if facts.rank > 0:
            if isinstance((facts.metadata or {}).get(OWNERSHIP_POLICY_METADATA), Mapping):
                return (
                    "pointer array container descriptor ownership is fixed by its native parent; "
                    "use PointerPolicy for extraction and descriptor operations"
                )
            return None
        if decision.transfer is not TransferMode.SNAPSHOT_COPY:
            return "scalar pointer field and module accessors require snapshot_copy detached values"
        return None

    @staticmethod
    def _complete_immutable_policy(
        decision: OwnershipDecision,
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> OwnershipDecision:
        """Adapt writable immutable values to replacement, discarded-copy, or blocked policy.

        Only writable argument contexts with explicit immutable metadata are
        changed.  The returned decision makes replacement projection explicit
        before ABI action selection.
        """
        metadata = facts.metadata or {}
        if metadata.get(PYTHON_VALUE_MUTABILITY_METADATA) != PYTHON_VALUE_IMMUTABLE:
            return decision
        if not context.is_argument or not context.writes_argument or decision.is_blocked:
            return decision

        if facts.is_custom:
            if context.writes_argument and not context.reads_argument and context.projects_result:
                return replace(
                    decision,
                    owner=OwnershipOwner.WRAPPER,
                    transfer=TransferMode.WRAPPER_INSTANCE,
                    destruction=DestructionPolicy.WRAPPER_DEALLOC,
                    storage_mode=StorageMode.STACK,
                    boundary_storage_mode=StorageMode.ALIAS,
                    borrowed=False,
                    mutates_native=True,
                    reason="immutable derived output uses a new wrapper-owned native instance",
                )
            return replace(
                decision,
                owner=OwnershipOwner.UNKNOWN,
                transfer=TransferMode.BLOCKED,
                destruction=DestructionPolicy.BLOCKED,
                borrowed=False,
                blocker="immutable derived replacement is not implemented",
                reason="derived replacement needs an explicit native copy/finalization policy",
            )

        raw_policy = metadata.get(OWNERSHIP_POLICY_METADATA)
        explicit_transfer = raw_policy.get("transfer") if isinstance(raw_policy, Mapping) else None
        if explicit_transfer is None and context.projects_result:
            decision = replace(
                decision,
                owner=OwnershipOwner.PYTHON,
                transfer=TransferMode.COPY_RETURN,
                destruction=DestructionPolicy.PYTHON_REFCOUNT,
                borrowed=False,
                mutates_native=True,
                reason="immutable writable value uses a mutable native temporary and replacement return",
            )

        if decision.transfer is TransferMode.COPY_RETURN and context.projects_result:
            return replace(
                decision,
                owner=OwnershipOwner.PYTHON,
                destruction=DestructionPolicy.PYTHON_REFCOUNT,
                borrowed=False,
                mutates_native=True,
            )
        if decision.transfer is TransferMode.CALL_LOCAL:
            return replace(
                decision,
                owner=OwnershipOwner.TEMPORARY,
                destruction=DestructionPolicy.CALL_LOCAL,
                borrowed=False,
                mutates_native=True,
                reason="immutable writable value uses a call-local copy and discards native mutation",
            )

        return replace(
            decision,
            owner=OwnershipOwner.UNKNOWN,
            transfer=TransferMode.BLOCKED,
            destruction=DestructionPolicy.BLOCKED,
            borrowed=False,
            blocker=(
                "immutable writable values require a projected copy_return replacement "
                "or explicit call_local discarded mutation"
            ),
            reason="immutable writeback policy is incomplete or contradictory",
        )

    @staticmethod
    def _validate_result_projection(
        decision: OwnershipDecision,
        context: OwnershipContext,
    ) -> OwnershipDecision:
        """Block copy-return arguments that have no declared Python result projection."""
        if (
            decision.is_blocked
            or not context.is_argument
            or decision.transfer is not TransferMode.COPY_RETURN
            or context.projects_result
        ):
            return decision
        return replace(
            decision,
            owner=OwnershipOwner.UNKNOWN,
            transfer=TransferMode.BLOCKED,
            destruction=DestructionPolicy.BLOCKED,
            borrowed=False,
            blocker="copy_return argument policy requires an explicit projected result",
            reason="argument replacement has no Python result projection",
        )

    @staticmethod
    def _validate_policy_combination(decision: OwnershipDecision) -> OwnershipDecision:
        """Reject owner, transfer, and destruction triples with no implemented lifetime."""
        if decision.is_blocked:
            return replace(
                decision,
                owner=OwnershipOwner.UNKNOWN,
                transfer=TransferMode.BLOCKED,
                destruction=DestructionPolicy.BLOCKED,
                borrowed=False,
                blocker=decision.blocker or "blocked by ownership policy",
            )

        allowed = _VALID_DESTRUCTION_BY_OWNER_TRANSFER.get((decision.owner, decision.transfer))
        if allowed is not None and decision.destruction in allowed:
            return decision

        expected = (
            "no supported destruction policy"
            if allowed is None
            else "expected " + " or ".join(sorted(policy.value for policy in allowed))
        )
        triple = f"{decision.owner.value}/{decision.transfer.value}/{decision.destruction.value}"
        return replace(
            decision,
            owner=OwnershipOwner.UNKNOWN,
            transfer=TransferMode.BLOCKED,
            destruction=DestructionPolicy.BLOCKED,
            borrowed=False,
            blocker=f"ownership policy {triple} is contradictory or unsupported; {expected}",
            reason="ownership, boundary transfer, and release responsibility must form a supported triple",
        )

    @staticmethod
    def _codegen_action(decision: OwnershipDecision, context: OwnershipContext) -> CodegenAction:
        """Derive the strict lowering action after a lifetime decision has been validated."""
        if decision.is_blocked:
            return CodegenAction.BLOCKED
        if context.is_argument and context.writes_argument and not context.reads_argument:
            if not context.projects_result:
                return CodegenAction.IDENTITY_OUTPUT
            if context.python_visible and decision.transfer is TransferMode.IN_PLACE:
                return CodegenAction.IDENTITY_OUTPUT
            return _CODEGEN_ACTION_BY_TRANSFER[decision.transfer]
        if (
            context.is_argument
            and context.writes_argument
            and context.reads_argument
            and decision.transfer is TransferMode.COPY_RETURN
        ):
            return CodegenAction.COPY_IN_OUT
        return _CODEGEN_ACTION_BY_TRANSFER[decision.transfer]

    @staticmethod
    def _python_barrier_action(
        decision: OwnershipDecision,
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> PythonBarrierAction:
        """Derive the Python-to-wrapper barrier action for a completed argument decision."""
        if decision.is_blocked:
            return PythonBarrierAction.BLOCKED
        if not context.is_argument or not context.python_visible:
            return PythonBarrierAction.NONE
        if facts.address_role == ADDRESS_ROLE_RAW:
            return PythonBarrierAction.RAW_ADDRESS
        if _is_native_array_handle_facts(facts) and decision.descriptor_boundary:
            return PythonBarrierAction.WRAPPER_INSTANCE
        if facts.scalar_storage or (
            decision.kind is ObjectKind.SCALAR and decision.codegen_action is CodegenAction.IDENTITY_OUTPUT
        ):
            if decision.kind is ObjectKind.STRING:
                return PythonBarrierAction.STRING_STORAGE
            return PythonBarrierAction.SCALAR_STORAGE
        if decision.kind is ObjectKind.SCALAR:
            return PythonBarrierAction.SCALAR_VALUE
        if decision.kind is ObjectKind.STRING:
            return PythonBarrierAction.STRING_VALUE
        if decision.kind is ObjectKind.NUMPY_ARRAY:
            return PythonBarrierAction.ARRAY_STORAGE
        if decision.kind is ObjectKind.DERIVED_TYPE:
            return PythonBarrierAction.WRAPPER_INSTANCE
        return PythonBarrierAction.BLOCKED

    @staticmethod
    def _native_barrier_action(
        decision: OwnershipDecision,
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> NativeBarrierAction:
        """Derive the wrapper-to-native ABI action for a completed argument decision."""
        if decision.is_blocked:
            return NativeBarrierAction.BLOCKED
        if not context.is_argument:
            return NativeBarrierAction.NONE
        if facts.address_role == ADDRESS_ROLE_RAW:
            return NativeBarrierAction.PASS_RAW_ADDRESS
        if OwnershipPolicyResolver._uses_descriptor_call_local_boundary(decision, facts, context):
            return NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
        if OwnershipPolicyResolver._passes_scalar_storage_address(decision, facts):
            return NativeBarrierAction.PASS_STORAGE_ADDRESS
        if OwnershipPolicyResolver._passes_scalar_alias_address(decision, facts):
            return NativeBarrierAction.PASS_STORAGE_ADDRESS
        if decision.kind is ObjectKind.NUMPY_ARRAY:
            if decision.descriptor_boundary:
                return NativeBarrierAction.PASS_NATIVE_DESCRIPTOR
            return NativeBarrierAction.PASS_ARRAY_BUFFER
        if decision.kind is ObjectKind.STRING:
            return NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
        if decision.kind is ObjectKind.DERIVED_TYPE:
            return NativeBarrierAction.PASS_WRAPPER_ADDRESS
        if decision.kind is ObjectKind.SCALAR:
            hidden_output = context.projects_result and not context.python_visible and not decision.descriptor_boundary
            if (
                facts.address_role == ADDRESS_ROLE_PROJECTION
                or hidden_output
                or decision.codegen_action is CodegenAction.COPY_IN_OUT
            ):
                return NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
            return NativeBarrierAction.PASS_VALUE
        return NativeBarrierAction.BLOCKED

    @staticmethod
    def _uses_descriptor_call_local_boundary(
        decision: OwnershipDecision,
        facts: _StorageFacts,
        context: OwnershipContext,
    ) -> bool:
        """Report whether a scalar descriptor needs call-local address storage at the ABI boundary."""
        return bool(
            context.is_argument
            and decision.kind is ObjectKind.SCALAR
            and decision.codegen_action in {CodegenAction.CALL_LOCAL_INPUT, CodegenAction.COPY_IN_OUT}
            and decision.descriptor_boundary
            and facts.address_role != ADDRESS_ROLE_PROJECTION
        )

    @staticmethod
    def _passes_scalar_storage_address(decision: OwnershipDecision, facts: _StorageFacts) -> bool:
        """Report whether scalar storage or identity output passes its caller storage address."""
        return bool(
            facts.scalar_storage
            or (
                decision.kind is ObjectKind.SCALAR
                and decision.codegen_action in {CodegenAction.IN_PLACE_ARGUMENT, CodegenAction.IDENTITY_OUTPUT}
            )
        )

    @staticmethod
    def _passes_scalar_alias_address(decision: OwnershipDecision, facts: _StorageFacts) -> bool:
        """Report whether a scalar alias must cross the ABI as a storage address."""
        return bool(
            decision.kind is ObjectKind.SCALAR
            and decision.storage_mode is StorageMode.ALIAS
            and (facts.address_role != ADDRESS_ROLE_PROJECTION or facts.pointer)
        )

    @staticmethod
    def _enum_value(enum_type: type[Enum], value: object, default: Any) -> Any:
        """Convert one optional metadata value to an enum, preserving ``default`` when absent.

        Invalid present values raise ``ValueError`` listing the accepted enum
        values so malformed contracts fail during policy completion.

        For example, ``_enum_value(TransferMode, 'copy_return', default)``
        returns ``TransferMode.COPY_RETURN``, while a ``None`` value returns the
        supplied default unchanged.
        """
        if value is None:
            return default
        try:
            return enum_type(str(value))
        except ValueError as exc:
            allowed = ", ".join(item.value for item in enum_type)
            raise ValueError(f"Unsupported ownership policy value {value!r}; expected one of: {allowed}") from exc

    @staticmethod
    def _storage_for_override(
        facts: _StorageFacts,
        transfer: TransferMode,
        default: StorageMode,
    ) -> StorageMode:
        """Choose override storage without violating native storage invariants.

        ``facts`` identifies pointer, allocatable, and array storage;
        ``transfer`` is the normalized override and ``default`` is the storage
        chosen by the normal resolver branch. Pointers remain aliases,
        allocatables remain heap-backed, borrowed ordinary arrays become
        aliases, and all other values keep ``default``.

        For example, an allocatable with ``transfer=SNAPSHOT_COPY`` returns
        ``HEAP``, while an ordinary borrowed array returns ``ALIAS``.
        """
        if facts.pointer:
            return StorageMode.ALIAS
        if facts.allocatable:
            return StorageMode.HEAP
        if transfer is TransferMode.BORROWED_VIEW and (facts.rank > 0 or facts.is_ndarray):
            return StorageMode.ALIAS
        return default

    @staticmethod
    def _semantic_facts(semantic_type: Any) -> _StorageFacts:
        """Normalize a semantic type's storage and metadata into resolver-specific facts.

        This is read-only: it consumes the semantic representation and returns
        a compact immutable record that keeps type inspection out of policy
        branches.
        """
        metadata = getattr(semantic_type, "metadata", {}) or {}
        constraints = getattr(semantic_type, "constraints", ()) or ()
        storage = getattr(semantic_type, "storage", None)
        array = getattr(storage, "array", None) if storage is not None else None
        storage_metadata = getattr(storage, "metadata", {}) if storage is not None else {}
        name = str(getattr(semantic_type, "name", ""))
        rank = int(getattr(semantic_type, "rank", 0) or 0)
        is_string = name == "String"
        is_custom = rank == 0 and not is_string and name not in _STANDARD_SCALAR_TYPES
        return _StorageFacts(
            rank=rank,
            name=name,
            constant=any(getattr(constraint, "name", None) == "Constant" for constraint in constraints),
            allocatable=bool(getattr(array, "allocatable", False) or metadata.get("fortran_allocatable")),
            pointer=bool(getattr(array, "pointer", False) or metadata.get("fortran_pointer")),
            is_string=is_string,
            is_custom=is_custom,
            storage_kind=str(getattr(storage, "kind", "value") if storage is not None else "value"),
            address_role=(
                str(storage_metadata.get(ADDRESS_ROLE_METADATA))
                if storage_metadata.get(ADDRESS_ROLE_METADATA) is not None
                else None
            ),
            scalar_storage=bool(getattr(array, "category", None) == SCALAR_STORAGE_CATEGORY),
            metadata=metadata,
        )

    @staticmethod
    def _is_semantic_constant(semantic_type: Any) -> bool:
        """Report whether a semantic type carries the ``Constant`` constraint."""
        constraints = getattr(semantic_type, "constraints", ()) or ()
        return any(getattr(constraint, "name", None) == "Constant" for constraint in constraints)

    @staticmethod
    def _semantic_variable_context(variable: Any) -> OwnershipContext:
        """Infer field or argument context from a semantic variable's concrete model type.

        Arguments preserve mutability and output-projection facts; all other
        unrecognized variables use neutral value context.  The variable is not
        changed.
        """
        class_name = type(variable).__name__
        if class_name == "SemanticField":
            return OwnershipContext.field()
        if class_name == "SemanticArgument":
            storage = variable.semantic_type.storage
            return OwnershipContext.argument(
                writes_argument=bool(
                    variable.semantic_type.ownership.mutable
                    or (storage is not None and (storage.mutable or not storage.read_only))
                    or variable.metadata.get(PROJECTED_OUTPUT_METADATA)
                )
            )
        return OwnershipContext(location="value")


default_ownership_policy = OwnershipPolicyResolver()


def ownership_decision_for_codegen_variable(var: Any) -> OwnershipDecision:
    """Return a lowering variable's completed decision or reject incomplete semantic policy.

    Bridge and binding code use this gate instead of reconstructing ownership
    from backend datatypes.  Missing policy raises ``ValueError`` with the
    required post-IR completion step.
    """
    decision = getattr(var, "ownership_decision", None)
    if decision is None:
        name = getattr(var, "name", type(var).__name__)
        raise ValueError(
            f"Codegen variable {name!r} is missing completed ownership policy; "
            "run complete_semantic_policies before ir2ast lowering"
        )
    return decision


def codegen_action_for_variable(var: Any) -> CodegenAction:
    """Return ``var``'s completed lowering action after enforcing policy presence."""
    return ownership_decision_for_codegen_variable(var).codegen_action


def python_barrier_action_for_variable(var: Any) -> PythonBarrierAction:
    """Return ``var``'s completed Python-boundary action after enforcing policy presence."""
    return ownership_decision_for_codegen_variable(var).python_barrier_action


def native_barrier_action_for_variable(var: Any) -> NativeBarrierAction:
    """Return ``var``'s completed native-ABI action after enforcing policy presence."""
    return ownership_decision_for_codegen_variable(var).native_barrier_action


# Direct ownership-resolution example


if __name__ == "__main__":
    from prik.semantics.models import SemanticArgument, SemanticFunction, SemanticType

    semantic_function = SemanticFunction(
        name="scale",
        arguments=[SemanticArgument("value", SemanticType("Float64", dtype="Float64"))],
        return_type=SemanticType("Float64", dtype="Float64"),
    )
    semantic_argument = semantic_function.arguments[0]
    argument_context = ownership_context_for_argument(semantic_function, semantic_argument)
    print(f"before: math.scale({semantic_argument.name}): {semantic_argument.semantic_type.name} semantic IR")
    decision = default_ownership_policy.decide_semantic_type(semantic_argument.semantic_type, argument_context)
    print(
        f"after: {decision.kind.value}/{decision.owner.value}/{decision.transfer.value}; "
        f"{decision.python_barrier_action.value} -> {decision.native_barrier_action.value}"
    )
