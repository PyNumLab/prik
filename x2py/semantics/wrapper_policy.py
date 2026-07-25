"""Completed wrapper policies for the currently supported generation lanes."""

from __future__ import annotations

import ast
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from x2py.naming import NamingPolicy
from x2py.semantics import models
from x2py.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_RAW,
    BIND_TARGET_METADATA,
    SCALAR_STORAGE_CATEGORY,
    SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA,
)
from x2py.semantics.native_array_handles import (
    NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER,
    NativeArrayHandlePolicy as CompletedNativeArrayHandlePolicy,
    native_array_descriptor_kind,
)
from x2py.semantics.wrapper_exports import PythonExportPolicy, completed_python_exports
from x2py.semantics.ownership import (
    AssignmentMode,
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    ObjectKind,
    OwnershipDecision,
    OwnershipOwner,
    PythonBarrierAction,
    SetterAction,
    StorageMode,
    TransferMode,
)


_PLAN_PRIMITIVE_SCALAR_TYPES = frozenset(
    {
        "Bool",
        "Int8",
        "Int16",
        "Int32",
        "Int64",
        "Float32",
        "Float64",
        "Complex64",
        "Complex128",
    }
)

_NUMPY_DTYPE_NAMES = {
    "Bool": "bool",
    "Int8": "int8",
    "Int16": "int16",
    "Int32": "int32",
    "Int64": "int64",
    "Float32": "float32",
    "Float64": "float64",
    "Complex64": "complex64",
    "Complex128": "complex128",
}

FIXED_STRING_RESULT_COPY_REASON = "copy fixed-length Fortran character output into C-owned null-terminated storage"
ORDINARY_ARRAY_RESULT_COPY_REASON = "copy non-descriptor Fortran array output into C-owned contiguous storage"
OWNED_NATIVE_ARRAY_HANDLE_COPY_REASON = (
    "materialize native allocatable descriptor into persistent wrapper-owned CFI storage"
)
SCALAR_DESCRIPTOR_RESULT_COPY_REASON = (
    "copy a present rank-zero native descriptor value before releasing call-local descriptor storage"
)
STRING_INPUT_COPY_REASON = "materialize Fortran character storage from the binding UTF-8 byte buffer"
STRING_REPLACEMENT_COPY_REASON = (
    "materialize mutable Fortran character storage and copy post-call bytes back to binding storage"
)
STRING_STORAGE_COPY_REASON = (
    "materialize fixed-length Fortran character storage from caller-owned NumPy bytes and copy mutation back"
)
RAW_STRING_ADDRESS_COPY_REASON = (
    "materialize fixed-length Fortran character storage from a caller-supplied raw address and copy mutation back"
)
DERIVED_VALUE_COPY_REASON = "pass an exact derived pointee through a typed native value dummy"


class OptionalMode(str, Enum):
    """Completed ABI behavior for one argument's presence states."""

    REQUIRED = "required"
    REQUIRED_DESCRIPTOR = "required_descriptor"
    NULLABLE_VALUE = "nullable_value"
    DESCRIPTOR = "descriptor"


class ArgumentHandoffMode(str, Enum):
    """Completed binding-to-bridge ABI shape for one argument."""

    VALUE = "value"
    TYPED_REFERENCE = "typed_reference"
    OPAQUE_ADDRESS = "opaque_address"
    CHARACTER_BUFFER = "character_buffer"
    ARRAY_BUFFER = "array_buffer"
    NATIVE_DESCRIPTOR = "native_descriptor"


class BridgeDataAction(str, Enum):
    """Completed bridge-side data movement for one boundary value."""

    DIRECT_TRANSFER = "direct_transfer"
    ASSOCIATE_VIEW = "associate_view"
    COPY_REPRESENTATION = "copy_representation"
    BLOCKED = "blocked"


_ARRAY_VALUE_OPTIONAL_MODES = frozenset({OptionalMode.REQUIRED, OptionalMode.NULLABLE_VALUE})
_ARRAY_DESCRIPTOR_OPTIONAL_MODES = frozenset({OptionalMode.REQUIRED, OptionalMode.DESCRIPTOR})
_ARRAY_VIEW_CODEGEN_ACTIONS = frozenset(
    {
        CodegenAction.CALL_LOCAL_INPUT,
        CodegenAction.IN_PLACE_ARGUMENT,
        CodegenAction.IDENTITY_OUTPUT,
    }
)
_RAW_ARRAY_VIEW_CODEGEN_ACTIONS = frozenset({CodegenAction.CALL_LOCAL_INPUT, CodegenAction.IN_PLACE_ARGUMENT})


class WritebackPhase(str, Enum):
    """Ordered phases of one completed replacement writeback."""

    COPY_IN = "copy_in"
    NATIVE_MUTATION = "native_mutation"
    COPY_OUT = "copy_out"
    CLEANUP = "cleanup"


class LifecycleOperation(str, Enum):
    """Typed purpose of one ordered transfer lifecycle record."""

    WRITEBACK = "writeback"
    DESTROY_ON_FAILURE = "destroy_on_failure"
    TRANSFER_TO_WRAPPER = "transfer_to_wrapper"


class TransformationLayer(str, Enum):
    """Backend layer that owns one complete representation transformation."""

    BINDING = "binding"
    BRIDGE = "bridge"


class TransformationAction(str, Enum):
    """Typed representation or lifecycle operation selected before planning."""

    COPY_ARRAY_REPRESENTATION = "copy_array_representation"
    PUBLISH_ARRAY_REPLACEMENT = "publish_array_replacement"
    RELEASE_TEMPORARY = "release_temporary"


class CallbackABIKind(str, Enum):
    """Stable C ABI shape for one callback transfer."""

    VALUE = "value"
    REFERENCE = "reference"
    DATA_AND_SHAPE = "data_and_shape"
    DATA_AND_LENGTH = "data_and_length"
    DERIVED_ADDRESS = "derived_address"


class CallbackTransferAction(str, Enum):
    """Fortran-adapter movement selected for one callback transfer."""

    COPY_IN = "copy_in"
    COPY_OUT = "copy_out"
    COPY_IN_OUT = "copy_in_out"
    BORROW_READ_ONLY = "borrow_read_only"
    BORROW_WRITABLE = "borrow_writable"


class CallbackResultAction(str, Enum):
    """Typed result conversion performed by one callback trampoline."""

    RETURN_VOID = "return_void"
    RETURN_SCALAR = "return_scalar"
    RETURN_ARRAY_ADDRESS = "return_array_address"
    RETURN_DERIVED_ADDRESS = "return_derived_address"
    REJECT_RESULT = "reject_result"


class CallbackLifecycleAction(str, Enum):
    """Ordered call-scoped lifetime actions around native entry."""

    VALIDATE_CALLBACK = "validate_callback"
    RETAIN_CALLABLE = "retain_callable"
    PUSH_CONTEXT = "push_context"
    ENTER_NATIVE = "enter_native"
    POP_CONTEXT = "pop_context"
    RELEASE_CALLBACK = "release_callback"


class CallbackThreadAction(str, Enum):
    """Thread relationship required by an immediate callback."""

    REQUIRE_ENTERING_THREAD = "require_entering_thread"


class CallbackGILAction(str, Enum):
    """Python runtime lock action owned by the C trampoline."""

    ACQUIRE_GIL = "acquire_gil"
    RELEASE_GIL = "release_gil"


class CallbackFatalAction(str, Enum):
    """Non-returning callback error boundary."""

    ABORT_WITH_PYTHON_ERROR = "abort_with_python_error"


class ModuleGetterAction(str, Enum):
    """Completed Python-visible read behavior for a module variable."""

    CONSTANT_VALUE = "constant_value"
    DIRECT_VALUE = "direct_value"
    NULLABLE_SNAPSHOT = "nullable_snapshot"
    BORROWED_ARRAY_VIEW = "borrowed_array_view"
    NATIVE_ARRAY_HANDLE = "native_array_handle"
    DERIVED_OBJECT = "derived_object"


class ModuleObjectAccessMechanism(str, Enum):
    """Completed native access path for one derived module value."""

    DIRECT_ADDRESS = "direct_address"
    MEMBER_PROXY = "member_proxy"
    VALUE_COPY = "value_copy"


class DerivedFieldAccessMechanism(str, Enum):
    """Typed bridge mechanism for one public live derived field."""

    SCALAR_VALUE = "scalar_value"
    FIXED_STRING_COPY = "fixed_string_copy"
    ORDINARY_ARRAY_DESCRIPTOR = "ordinary_array_descriptor"
    NATIVE_ARRAY_HANDLE = "native_array_handle"
    NESTED_OBJECT = "nested_object"


class DerivedObjectOrigin(str, Enum):
    """Completed origin of one scalar derived object."""

    CALLER_WRAPPER = "caller_wrapper"
    WRAPPER_RESULT = "wrapper_result"
    NATIVE_MODULE = "native_module"
    BORROWED_FIELD = "borrowed_field"
    CONSTANT_VALUE = "constant_value"


class DerivedOwnerRetention(str, Enum):
    """Python owner retained by one live derived wrapper."""

    CALLER_WRAPPER = "caller_wrapper"
    WRAPPER_INSTANCE = "wrapper_instance"
    NATIVE_MODULE = "native_module"
    PARENT_WRAPPER = "parent_wrapper"
    NONE = "none"


class DerivedRelease(str, Enum):
    """Completed release responsibility for derived native storage."""

    NONE = "none"
    WRAPPER_DESTROY = "wrapper_destroy"
    NATIVE_OWNER = "native_owner"


class DerivedNativeHandoff(str, Enum):
    """Completed typed native call mechanism for a scalar derived object."""

    REFERENCE = "reference"
    TYPED_VALUE = "typed_value"


class DerivedObjectStorage(str, Enum):
    """Persistent native storage shape carried by one derived wrapper."""

    DIRECT = "direct"
    ALLOCATABLE_HOLDER = "allocatable_holder"
    POINTER_HOLDER = "pointer_holder"
    MODULE_PROXY = "module_proxy"
    MODULE_TARGET = "module_target"
    MODULE_ALLOCATABLE = "module_allocatable"
    MODULE_ALLOCATABLE_TARGET = "module_allocatable_target"
    MODULE_POINTER = "module_pointer"


class DerivedDummyCategory(str, Enum):
    """Exact native scalar-derived dummy form completed before lowering."""

    OBJECT = "object"
    TARGET = "target"
    ALLOCATABLE = "allocatable"
    ALLOCATABLE_TARGET = "allocatable_target"
    POINTER = "pointer"
    VALUE = "value"


class DerivedCallAction(str, Enum):
    """Public compatibility action selected for one actual/dummy cell."""

    DIRECT_REFERENCE = "direct_reference"
    SCOPED_REFERENCE = "scoped_reference"
    HOLDER_REFERENCE = "holder_reference"
    MODULE_ADDRESS = "module_address"
    ALLOCATABLE_HOLDER = "allocatable_holder"
    MODULE_ALLOCATABLE_TRANSACTION = "module_allocatable_transaction"
    POINTEE_REFERENCE = "pointee_reference"
    POINTER_HOLDER = "pointer_holder"
    MODULE_POINTER_TRANSACTION = "module_pointer_transaction"
    POINTER_INPUT_ADAPTER = "pointer_input_adapter"
    TYPED_VALUE_COPY = "typed_value_copy"
    INCOMPATIBLE = "incompatible"


class DerivedActualAccess(str, Enum):
    """Mechanical carrier used by a completed scalar-derived matrix cell."""

    NONE = "none"
    DIRECT_ADDRESS = "direct_address"
    SCOPED_ADDRESS = "scoped_address"
    ALLOCATABLE_HOLDER = "allocatable_holder"
    POINTER_HOLDER = "pointer_holder"
    MODULE_ALLOCATABLE_TRANSACTION = "module_allocatable_transaction"
    MODULE_POINTER_TRANSACTION = "module_pointer_transaction"


class DerivedTargetLifetime(str, Enum):
    """Lifetime of targetability supplied by one completed call cell."""

    NONE = "none"
    CALL = "call"
    OWNER = "owner"
    MODULE = "module"


class DerivedWriteback(str, Enum):
    """Native state retained after a scalar-derived call."""

    NONE = "none"
    OBJECT_MUTATION = "object_mutation"
    ALLOCATION_STATE = "allocation_state"
    POINTER_ASSOCIATION = "pointer_association"


class ClassConstructorKind(str, Enum):
    """Completed public construction surface for one generated class."""

    ABSENT = "absent"
    DEFAULT_FIELDS = "default_fields"
    BOUND_PROCEDURE = "bound_procedure"
    OVERLOAD_SET = "overload_set"


class ClassMethodKind(str, Enum):
    """Completed descriptor attached to one generated class."""

    INSTANCE = "instance"
    STATIC = "static"


class ClassInvocationKind(str, Enum):
    """Native call form selected for one concrete class callable."""

    MODULE_PROCEDURE = "module_procedure"
    TYPE_BOUND = "type_bound"


class NativeInvocationKind(str, Enum):
    """Completed native syntax for one concrete wrapper call."""

    PROCEDURE = "procedure"
    DEFINED_OPERATOR = "defined_operator"
    DEFINED_ASSIGNMENT = "defined_assignment"


class ExternalDeclarationMode(str, Enum):
    """Completed Fortran declaration form for one native procedure."""

    NONE = "none"
    IMPLICIT_EXTERNAL = "implicit_external"
    EXPLICIT_INTERFACE = "explicit_interface"


def overload_builtin_scalar_family(semantic_type_name: str) -> str:
    """Return the Python scalar family admitted by reflected dispatch."""
    if semantic_type_name == "Bool":
        return "bool"
    if semantic_type_name.startswith("Int"):
        return "int"
    if semantic_type_name.startswith("Float"):
        return "float"
    if semantic_type_name.startswith("Complex"):
        return "complex"
    raise ValueError(f"Unsupported reflected overload scalar {semantic_type_name!r}")


class ClassRegistrationAction(str, Enum):
    """Dependency-ordered Python class registration actions."""

    CREATE_TYPE = "create_type"
    SET_BASE = "set_base"
    READY_TYPE = "ready_type"
    EXPORT_TYPE = "export_type"


class ConstructionLifecycleAction(str, Enum):
    """Owned-instance lifecycle selected before class lowering."""

    ALLOCATE = "allocate"
    INITIALIZE = "initialize"
    COMMIT_OWNER = "commit_owner"
    CLEANUP_UNCOMMITTED = "cleanup_uncommitted"
    DESTROY_OWNED = "destroy_owned"


class OverloadMatchKind(str, Enum):
    """Exact Python runtime category used by overload selection."""

    NUMPY_SCALAR = "numpy_scalar"
    NUMPY_ARRAY = "numpy_array"
    STRING = "string"
    DERIVED = "derived"


@dataclass(frozen=True)
class DerivedCallCasePolicy:
    """One exhaustive actual-storage/dummy-form compatibility decision."""

    actual_storage: DerivedObjectStorage
    action: DerivedCallAction
    access: DerivedActualAccess
    abi_code: int
    requires_present: bool
    target_lifetime: DerivedTargetLifetime
    failure_kind: str | None = None
    failure_message: str | None = None


@dataclass(frozen=True)
class DerivedCallPolicy:
    """Completed exhaustive dummy compatibility independent from lowering."""

    dummy_category: DerivedDummyCategory
    cases: tuple[DerivedCallCasePolicy, ...]
    writeback: DerivedWriteback
    status_role: str
    origin_identity_role: str
    acquisition_order: int
    cleanup_order: int


@dataclass(frozen=True)
class DerivedHandoffPolicy:
    """Typed scalar-derived identity, origin, lifetime, and native handoff."""

    type_name: str
    type_identity: tuple[str, str]
    native_type_name: str
    native_scope: str
    origin: DerivedObjectOrigin
    owner_retention: DerivedOwnerRetention
    release: DerivedRelease
    target_owner_retention: DerivedOwnerRetention
    target_release: DerivedRelease
    nullable: bool
    native_handoff: DerivedNativeHandoff
    storage: DerivedObjectStorage


@dataclass(frozen=True)
class DerivedModuleObjectPolicy:
    """Completed live module-object mechanism and lifetime facts."""

    handoff: DerivedHandoffPolicy
    access: ModuleObjectAccessMechanism
    replacement: SetterAction
    member_paths: tuple[DerivedMemberPathPolicy, ...] = ()
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class DerivedFieldPolicy:
    """Completed public field behavior beneath one derived type."""

    owner_path: str
    name: str
    native_name: str
    semantic_type_name: str
    string_element: bool
    rank: int
    object_kind: ObjectKind
    access: DerivedFieldAccessMechanism
    getter: OwnershipDecision
    setter: OwnershipDecision
    getter_action: CodegenAction
    setter_action: SetterAction
    native_assignment: AssignmentMode
    owner_retention: DerivedOwnerRetention
    character_length: int | None
    array: ArrayHandoffPolicy | None
    native_array_handle: NativeArrayHandleWrapperPolicy | None
    derived: DerivedHandoffPolicy | None
    supported: bool
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class DerivedMemberPathPolicy:
    """One finite typed member path used by a plain live module proxy."""

    path: tuple[str, ...]
    native_path: tuple[str, ...]
    declaring_type_name: str
    declaring_type_identity: tuple[str, str]
    field: DerivedFieldPolicy


@dataclass(frozen=True)
class DerivedTypePolicy:
    """Completed identity, lifecycle, and field policy for one derived type."""

    owner_path: str
    type_name: str
    type_identity: tuple[str, str]
    native_type_name: str
    native_scope: str
    python_exports: tuple[PythonExportPolicy, ...]
    python_names: tuple[str, ...]
    fields: tuple[DerivedFieldPolicy, ...]
    finalizers: tuple[str, ...]
    bind_c: bool
    sequence: bool
    supported: bool
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConstructorFieldPolicy:
    """One keyword-only field initialized by the generated constructor."""

    owner_path: str
    name: str
    default_value: str | None
    setter_action: SetterAction


@dataclass(frozen=True)
class ConstructorPolicy:
    """Completed construction selection and owned-instance lifecycle."""

    kind: ClassConstructorKind
    fields: tuple[ConstructorFieldPolicy, ...]
    target_owner_path: str | None
    overload_name: str | None
    lifecycle: tuple[ConstructionLifecycleAction, ...]
    rejection_message: str | None = None


@dataclass(frozen=True)
class ClassMethodPolicy:
    """One concrete class descriptor linked to a completed function policy."""

    owner_path: str
    python_name: str
    native_name: str
    kind: ClassMethodKind
    passed_object_position: int | None
    public: bool
    invocation: ClassInvocationKind
    type_bound_name: str | None


@dataclass(frozen=True)
class OverloadArgumentPolicy:
    """One completed exact-type predicate in an overload signature."""

    python_name: str
    kind: OverloadMatchKind
    optional: bool
    semantic_type_name: str
    rank: int
    derived_type_identity: tuple[str, str] | None
    accept_builtin_scalar: bool = False


@dataclass(frozen=True)
class OverloadCandidatePolicy:
    """One concrete overload target and its ordered runtime predicates."""

    owner_path: str
    arguments: tuple[OverloadArgumentPolicy, ...]
    passed_object: bool


@dataclass(frozen=True)
class OverloadPolicy:
    """One overload set with explicit concrete candidates and exports."""

    owner_path: str
    python_name: str
    kind: str
    candidates: tuple[OverloadCandidatePolicy, ...]
    python_exports: tuple[PythonExportPolicy, ...] = ()
    blockers: tuple[str, ...] = ()
    unsupported_extra_argument_message: str | None = None
    identity_receiver_shortcut: bool = False


@dataclass(frozen=True)
class ClassSurfacePolicy:
    """Completed public class surface composed over one derived-type policy."""

    owner_path: str
    type_identity: tuple[str, str]
    python_exports: tuple[PythonExportPolicy, ...]
    base_identities: tuple[tuple[str, str], ...]
    effective_fields: tuple[DerivedFieldPolicy, ...]
    constructor: ConstructorPolicy
    methods: tuple[ClassMethodPolicy, ...]
    overloads: tuple[OverloadPolicy, ...]
    registration: tuple[ClassRegistrationAction, ...]
    supported: bool
    blockers: tuple[str, ...] = ()


class NativeArrayDescriptorKind(str, Enum):
    """Public native descriptor family."""

    ALLOCATABLE = "allocatable"
    POINTER = "pointer"


class NativeArrayHandleKind(str, Enum):
    """Completed native handle owner/use category."""

    ARGUMENT_DESCRIPTOR = "argument_descriptor"
    OPTIONAL_ABSENT_HANDLE = "optional_absent_handle"
    BORROWED_MODULE_DESCRIPTOR = "borrowed_module_descriptor"
    BORROWED_FIELD_DESCRIPTOR = "borrowed_field_descriptor"
    OWNED_RESULT_DESCRIPTOR = "owned_result_descriptor"


class NativeDescriptorHandoffABI(str, Enum):
    """Binding-to-bridge descriptor representation."""

    FACT_PACKED_CALL_LOCAL = "fact_packed_call_local"
    DIRECT_STANDARD_DESCRIPTOR = "direct_standard_descriptor"
    OWNED_RESULT_STORAGE = "owned_result_storage"


class NativeArraySourceKind(str, Enum):
    """Python runtime sources accepted by an ordinary array argument."""

    NDARRAY = "ndarray"
    ALLOCATABLE_HANDLE = "allocatable_handle"
    POINTER_HANDLE = "pointer_handle"


class NativeArrayHandleOrigin(str, Enum):
    """Completed source owner for a native handle."""

    ARGUMENT = "argument"
    PROJECTED_RESULT = "projected_result"
    RESULT = "result"
    MODULE_VARIABLE = "module_variable"
    DERIVED_FIELD = "derived_field"


class NativeArrayOwnerRetention(str, Enum):
    """Python owner retained by a runtime handle."""

    CALLER_HANDLE = "caller_handle"
    OPTIONAL_ARGUMENT = "optional_argument"
    NATIVE_MODULE = "native_module"
    PARENT_WRAPPER = "parent_wrapper"
    WRAPPER_OWNER_STORAGE = "wrapper_owner_storage"


class NativeArrayDescriptorOwnership(str, Enum):
    """Ownership of persistent standard-descriptor storage."""

    BORROWED = "borrowed"
    OWNED = "owned"


class NativeArrayGetterBehavior(str, Enum):
    """Python getter behavior for a handle owner."""

    NONE = "none"
    HANDLE = "handle"
    RETURN_HANDLE = "return_handle"


class NativeArrayOutputProjection(str, Enum):
    """Result identity/materialization selected for a handle."""

    NONE = "none"
    PROJECTED_HANDLE = "projected_handle"
    HANDLE_RESULT = "handle_result"


class NativeArrayResultAllocation(str, Enum):
    """Direct native allocatable function result allocation contract."""

    NOT_APPLICABLE = "not_applicable"
    ALWAYS_ALLOCATED = "always_allocated"
    MAYBE_UNALLOCATED = "maybe_unallocated"


class NativeArrayRelease(str, Enum):
    """Completed release owner for descriptor storage."""

    NONE = "none"
    NATIVE_OWNER = "native_owner"
    WRAPPER_DEALLOC = "wrapper_dealloc"


class NativeArrayDestroyBehavior(str, Enum):
    """Runtime destruction behavior for a handle."""

    NONE = "none"
    HANDLE_FINALIZER = "handle_finalizer"
    PARENT_WRAPPER_FINALIZER = "parent_wrapper_finalizer"


class NativeArrayExtractionAction(str, Enum):
    """Completed `.to_numpy()` behavior."""

    BORROWED_VIEW = "borrowed_view"
    CONTIGUOUS_VIEW = "contiguous_view"
    DESCRIPTOR_VIEW = "descriptor_view"
    UNSUPPORTED = "unsupported"


class NativeArrayDescriptorInterop(str, Enum):
    """Standard C descriptor requirement."""

    NONE = "none"
    MODULE_ALLOCATABLE_C_DESCRIPTOR = "module_allocatable_c_descriptor"
    POINTER_C_DESCRIPTOR = "pointer_c_descriptor"
    OWNED_ALLOCATABLE_C_DESCRIPTOR = "owned_allocatable_c_descriptor"


class NativeArrayOperation(str, Enum):
    """Generated runtime operation supported by one handle."""

    ALLOCATED = "allocated"
    ASSOCIATED = "associated"
    SHAPE = "shape"
    ELEMENT_LENGTH = "element_length"
    ARRAY_ACTUAL = "array_actual"
    DESCRIPTOR = "descriptor"
    TO_NUMPY = "to_numpy"
    NATIVE_BYTE_ORDER = "native_byte_order"
    ALIGNED = "aligned"
    WRITEABLE = "writeable"
    LAYOUT = "layout"
    CONTIGUOUS = "contiguous"
    ALLOCATE = "allocate"
    DEALLOCATE = "deallocate"
    RESIZE = "resize"
    NULLIFY = "nullify"
    DESTROY = "destroy"


class PythonExceptionKind(str, Enum):
    """Completed Python exception selected for one native failure policy."""

    RUNTIME_ERROR = "RuntimeError"


@dataclass(frozen=True)
class NativeStatusOutputPolicy:
    """One validated native output consumed by status-error handling."""

    owner_path: str
    name: str
    native_name: str
    native_position: int
    result_position: int
    semantic_type_name: str
    rank: int
    character_length: int | None = None


@dataclass(frozen=True)
class NativeStatusErrorPolicy:
    """Completed native-status decision owned by post-IR policy completion."""

    status: NativeStatusOutputPolicy
    message: NativeStatusOutputPolicy | None
    success: int
    exception_kind: PythonExceptionKind


@dataclass(frozen=True)
class ModuleVariablePolicy:
    """Completed module-variable behavior before wrapper planning."""

    owner_path: str
    name: str
    python_exports: tuple[PythonExportPolicy, ...]
    native_name: str
    native_module: str
    semantic_type_name: str
    rank: int
    getter_action: ModuleGetterAction
    getter: OwnershipDecision | None
    setter_action: SetterAction
    native_assignment: AssignmentMode
    setter: OwnershipDecision | None
    descriptor_kind: str | None
    initializer: Any
    constant_value: Any
    supported: bool
    blockers: tuple[str, ...] = ()
    array: ArrayHandoffPolicy | None = None
    native_array_handle: NativeArrayHandleWrapperPolicy | None = None
    derived: DerivedModuleObjectPolicy | None = None


@dataclass(frozen=True)
class LifecyclePolicy:
    """One completed writeback or cleanup action."""

    owner_path: str
    phase: WritebackPhase
    source_role: str
    codegen_action: CodegenAction
    semantic_type_name: str
    result_position: int
    object_kind: ObjectKind
    operation: LifecycleOperation = LifecycleOperation.WRITEBACK


@dataclass(frozen=True)
class ArrayHandoffPolicy:
    """Completed array storage or raw-pointee layout facts."""

    rank: int | None
    shape: tuple[str, ...]
    axes: tuple[str, ...]
    order: str | None
    native_order: str | None
    contiguous: bool | None
    flatten_python_storage: bool = False
    flat_axis: int | None = None
    itemsize: int | None = None
    category: str | None = None
    extent_references: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class TransformationPolicy:
    """One layer-owned transformation subordinate to a transfer policy."""

    phase: WritebackPhase
    layer: TransformationLayer
    action: TransformationAction
    source_representation: str
    target_representation: str
    reason: str


@dataclass(frozen=True)
class NativeArrayActualPolicy:
    """Completed accepted-source and validation facts for an ordinary array."""

    accepted_sources: tuple[NativeArraySourceKind, ...]
    dtype: str
    rank: int
    shape: tuple[str, ...]
    order: str | None
    writable: bool
    require_native_byte_order: bool
    require_aligned: bool
    require_contiguous: bool
    flatten_storage: bool = False
    flat_axis: int | None = None


@dataclass(frozen=True)
class NativeDescriptorHandoffPolicy:
    """Completed descriptor ABI form subordinate to one handle policy."""

    abi: NativeDescriptorHandoffABI
    rank: int
    optional_presence: bool


@dataclass(frozen=True)
class NativeArrayHandleWrapperPolicy:
    """Typed wrapper-facing projection of completed native handle policy."""

    descriptor_kind: NativeArrayDescriptorKind
    handle_kind: NativeArrayHandleKind
    origin: NativeArrayHandleOrigin
    owner: OwnershipOwner
    owner_retention: NativeArrayOwnerRetention
    descriptor_ownership: NativeArrayDescriptorOwnership
    borrowed: bool
    getter_behavior: NativeArrayGetterBehavior
    setter_action: SetterAction
    native_assignment: AssignmentMode
    output_projection: NativeArrayOutputProjection
    result_allocation: NativeArrayResultAllocation
    release: NativeArrayRelease
    target_lifetime: str
    destroy_behavior: NativeArrayDestroyBehavior
    extraction_action: NativeArrayExtractionAction
    descriptor_interop: NativeArrayDescriptorInterop
    nullable: bool
    optional_absent: bool
    storage_mode: StorageMode
    operations: tuple[NativeArrayOperation, ...]
    required_headers: tuple[str, ...]
    array: ArrayHandoffPolicy
    handoff: NativeDescriptorHandoffPolicy


@dataclass(frozen=True)
class ScalarDescriptorResultPolicy:
    """Completed nullable rank-zero descriptor result copy contract."""

    descriptor_kind: NativeArrayDescriptorKind
    runtime_length: bool
    nullable: bool
    copy_reason: str
    release_owner: OwnershipOwner


@dataclass(frozen=True)
class PolymorphicDispatchPolicy:
    """Enumerated concrete native types accepted by one scalar input dummy."""

    owner_path: str
    variants: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CallbackTransferPolicy:
    """Completed native-to-Python transfer inside one callback invocation."""

    owner_path: str
    name: str
    semantic_type_name: str
    object_kind: ObjectKind
    rank: int
    passed_by_value: bool
    abi: CallbackABIKind
    adapter_action: CallbackTransferAction
    python_action: PythonBarrierAction
    character_length: int | None
    array: ArrayHandoffPolicy | None
    derived_type_identity: tuple[str, str] | None


@dataclass(frozen=True)
class CallbackResultPolicy:
    """Completed result representation returned through a C trampoline."""

    transfer: CallbackTransferPolicy | None
    action: CallbackResultAction


@dataclass(frozen=True)
class CallbackHandoffPolicy:
    """Complete immediate-callback contract consumed by wrapper planning."""

    owner_path: str
    prototype_name: str
    prototype_module: str | None
    declaration_mode: ExternalDeclarationMode
    arguments: tuple[CallbackTransferPolicy, ...]
    result: CallbackResultPolicy
    lifecycle: tuple[CallbackLifecycleAction, ...]
    thread_action: CallbackThreadAction
    gil_actions: tuple[CallbackGILAction, ...]
    fatal_action: CallbackFatalAction
    supported: bool
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArgumentPolicy:
    """Completed wrapper policy for one Python-visible argument."""

    owner_path: str
    name: str
    python_name: str
    native_name: str
    python_position: int
    native_position: int
    semantic_type_name: str
    rank: int
    optional: bool
    optional_mode: OptionalMode
    handoff_mode: ArgumentHandoffMode
    bridge_data_action: BridgeDataAction
    bridge_copy_reason: str | None
    nullable: bool
    writable: bool
    descriptor_boundary: bool
    ownership: OwnershipDecision
    codegen_action: CodegenAction
    python_barrier_action: PythonBarrierAction
    native_barrier_action: NativeBarrierAction
    storage_mode: StorageMode
    boundary_storage_mode: StorageMode
    projects_result: bool
    python_visible: bool
    result_position: int | None
    character_length: int | None
    array: ArrayHandoffPolicy | None = None
    native_array_actual: NativeArrayActualPolicy | None = None
    native_array_handle: NativeArrayHandleWrapperPolicy | None = None
    derived: DerivedHandoffPolicy | None = None
    derived_call: DerivedCallPolicy | None = None
    callback: CallbackHandoffPolicy | None = None
    polymorphic: PolymorphicDispatchPolicy | None = None
    transformations: tuple[TransformationPolicy, ...] = ()


@dataclass(frozen=True)
class _ArgumentBoundaryPolicy:
    """Normalized wrapper-boundary fields for one ordinary or callback input."""

    optional_mode: OptionalMode
    handoff_mode: ArgumentHandoffMode
    nullable: bool
    writable: bool
    descriptor_boundary: bool
    codegen_action: CodegenAction
    python_barrier_action: PythonBarrierAction
    native_barrier_action: NativeBarrierAction
    storage_mode: StorageMode
    boundary_storage_mode: StorageMode
    projects_result: bool
    result_position: int | None


@dataclass(frozen=True)
class ResultPolicy:
    """Completed wrapper policy for one native result."""

    owner_path: str
    semantic_type_name: str
    rank: int
    ownership: OwnershipDecision
    codegen_action: CodegenAction
    python_barrier_action: PythonBarrierAction
    native_barrier_action: NativeBarrierAction
    storage_mode: StorageMode
    boundary_storage_mode: StorageMode
    bridge_data_action: BridgeDataAction
    bridge_copy_reason: str | None
    character_length: int | None = None
    array: ArrayHandoffPolicy | None = None
    source_kind: str = "direct_return"
    native_name: str | None = None
    native_position: int | None = None
    result_position: int = 0
    native_array_handle: NativeArrayHandleWrapperPolicy | None = None
    scalar_descriptor: ScalarDescriptorResultPolicy | None = None
    derived: DerivedHandoffPolicy | None = None
    transformations: tuple[TransformationPolicy, ...] = ()


@dataclass(frozen=True)
class NativeCallSlotPolicy:
    """Completed native-call slot consumed by wrapper planning.

    ``object_kind`` is copied from the owning transfer decision.  Literal slots
    have no transfer owner and therefore use ``None``.
    """

    owner_path: str
    native_position: int
    source_kind: str
    python_position: int | None
    python_name: str | None
    native_name: str
    value_kind: str
    native_barrier_action: NativeBarrierAction
    codegen_action: CodegenAction
    bridge_data_action: BridgeDataAction
    bridge_copy_reason: str | None
    object_kind: ObjectKind | None
    literal_type: str | None = None
    literal_value: Any = None
    result_position: int | None = None
    semantic_type_name: str | None = None
    character_length: int | None = None
    array: ArrayHandoffPolicy | None = None
    native_array_handle: NativeArrayHandleWrapperPolicy | None = None
    scalar_descriptor: ScalarDescriptorResultPolicy | None = None
    derived: DerivedHandoffPolicy | None = None
    callback: CallbackHandoffPolicy | None = None


@dataclass(frozen=True)
class FunctionWrapperPolicy:
    """Completed wrapper policy for one semantic function."""

    owner_path: str
    python_exports: tuple[PythonExportPolicy, ...]
    native_name: str
    native_invocation: NativeInvocationKind
    native_operator: str | None
    external: bool
    external_declaration: ExternalDeclarationMode
    native_module: str | None
    native_is_subroutine: bool
    hold_gil: bool
    status_error: NativeStatusErrorPolicy | None
    class_call: ClassMethodPolicy | None
    module_export: bool
    supported: bool
    arguments: tuple[ArgumentPolicy, ...] = ()
    results: tuple[ResultPolicy, ...] = ()
    native_call_slots: tuple[NativeCallSlotPolicy, ...] = ()
    blockers: tuple[str, ...] = ()
    writeback_actions: tuple[LifecyclePolicy, ...] = ()
    cleanup_actions: tuple[LifecyclePolicy, ...] = ()
    release_actions: tuple[LifecyclePolicy, ...] = ()


def completed_derived_type_policy(semantic_class: models.SemanticClass) -> DerivedTypePolicy:
    """Return one fully completed derived-type policy or fail closed."""
    policy = semantic_class.metadata.get(models.RESOLVED_DERIVED_TYPE_POLICY_METADATA)
    if not isinstance(policy, DerivedTypePolicy):
        raise ValueError(f"Semantic class {semantic_class.name!r} has no completed derived-type policy")
    if not policy.supported:
        details = "; ".join(policy.blockers)
        raise ValueError(f"Semantic class {policy.owner_path!r} has unsupported derived-type policy: {details}")
    return policy


def build_derived_field_policy(
    field: models.SemanticField,
    *,
    owner_path: str,
) -> DerivedFieldPolicy:
    """Complete one field from already-completed ownership and descriptor facts."""
    field_path = f"{owner_path}.{field.name}"
    getter = _ownership_decision(field, models.RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA)
    setter = _ownership_decision(field, models.RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA)
    if getter is None or setter is None:
        raise ValueError(f"Derived field {field_path!r} is missing completed accessor ownership")
    handle = _native_array_handle_wrapper_policy(
        field.semantic_type,
        field.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
        field_path,
    )
    derived = _derived_handoff_policy(
        field.semantic_type,
        getter,
        owner_path=field_path,
        origin=DerivedObjectOrigin.BORROWED_FIELD,
    )
    blockers = (
        *_runtime_semantic_validation_blockers(field.semantic_type, f"field {field.name!r}"),
        *_derived_field_blockers(field, getter, setter, handle),
    )
    return DerivedFieldPolicy(
        owner_path=field_path,
        name=field.name,
        native_name=str(field.origin.native_name or field.name),
        semantic_type_name=field.semantic_type.name,
        string_element=field.semantic_type.name == "String",
        rank=int(field.semantic_type.rank or 0),
        object_kind=getter.kind,
        access=_derived_field_access_mechanism(getter.kind, handle),
        getter=getter,
        setter=setter,
        getter_action=getter.codegen_action,
        setter_action=setter.setter_action,
        native_assignment=setter.assignment_mode,
        owner_retention=_derived_field_owner_retention(getter.kind, handle),
        character_length=_character_length(field.semantic_type),
        array=_array_handoff_policy(field.semantic_type),
        native_array_handle=handle,
        derived=derived,
        supported=not blockers,
        blockers=tuple(blockers),
    )


def _derived_field_access_mechanism(
    object_kind: ObjectKind,
    handle: NativeArrayHandleWrapperPolicy | None,
) -> DerivedFieldAccessMechanism:
    """Complete the typed field bridge mechanism before wrapper planning."""
    if handle is not None:
        return DerivedFieldAccessMechanism.NATIVE_ARRAY_HANDLE
    return {
        ObjectKind.SCALAR: DerivedFieldAccessMechanism.SCALAR_VALUE,
        ObjectKind.STRING: DerivedFieldAccessMechanism.FIXED_STRING_COPY,
        ObjectKind.NUMPY_ARRAY: DerivedFieldAccessMechanism.ORDINARY_ARRAY_DESCRIPTOR,
        ObjectKind.DERIVED_TYPE: DerivedFieldAccessMechanism.NESTED_OBJECT,
    }[object_kind]


def _derived_field_owner_retention(
    object_kind: ObjectKind,
    handle: NativeArrayHandleWrapperPolicy | None,
) -> DerivedOwnerRetention:
    """Complete whether a returned field object must keep its parent alive."""
    if handle is not None or object_kind in {ObjectKind.NUMPY_ARRAY, ObjectKind.DERIVED_TYPE}:
        return DerivedOwnerRetention.PARENT_WRAPPER
    return DerivedOwnerRetention.NONE


def build_derived_type_policy(
    semantic_class: models.SemanticClass,
    *,
    owner_path: str,
) -> DerivedTypePolicy:
    """Complete one namespace-owned type identity, lifecycle, and public fields."""
    fields = tuple(
        policy
        for field in semantic_class.fields
        if field.visibility == "public"
        for policy in (field.metadata.get(models.RESOLVED_DERIVED_FIELD_POLICY_METADATA),)
        if isinstance(policy, DerivedFieldPolicy)
    )
    missing = tuple(
        field.name
        for field in semantic_class.fields
        if field.visibility == "public"
        and not isinstance(field.metadata.get(models.RESOLVED_DERIVED_FIELD_POLICY_METADATA), DerivedFieldPolicy)
    )
    type_attributes = {
        str(attribute).casefold() for attribute in semantic_class.metadata.get("fortran_type_attributes", ())
    }
    deferred_bindings = tuple(semantic_class.metadata.get("fortran_deferred_bindings", ()))
    blockers = tuple(
        [*(f"field {name!r} is missing completed derived-field policy" for name in missing)]
        + [reason for field in fields for reason in field.blockers]
        + (
            ["abstract derived types need a non-instantiable Python class policy"]
            if "abstract" in type_attributes
            else []
        )
        + [
            f"deferred type-bound procedure {name!r} needs an override and dispatch policy"
            for name in deferred_bindings
        ]
    )
    exports = completed_python_exports(semantic_class, semantic_class.name)
    native_type_name = str(semantic_class.native_name or semantic_class.name)
    native_scope = str(semantic_class.origin.native_scope or owner_path.split(".", 1)[0])
    return DerivedTypePolicy(
        owner_path=owner_path,
        type_name=semantic_class.name,
        type_identity=(native_scope, native_type_name),
        native_type_name=native_type_name,
        native_scope=native_scope,
        python_exports=exports,
        python_names=tuple(export.name for export in exports),
        fields=fields,
        finalizers=tuple(str(item) for item in semantic_class.metadata.get("fortran_final_procedures", ())),
        bind_c=bool(semantic_class.metadata.get("fortran_bind_c")),
        sequence=bool(semantic_class.metadata.get("fortran_sequence")),
        supported=not blockers,
        blockers=blockers,
    )


def completed_class_surface_policy(semantic_class: models.SemanticClass) -> ClassSurfacePolicy:
    """Return one fully completed class surface or fail before planning."""
    policy = semantic_class.metadata.get(models.RESOLVED_CLASS_SURFACE_POLICY_METADATA)
    if not isinstance(policy, ClassSurfacePolicy):
        raise ValueError(f"Semantic class {semantic_class.name!r} has no completed class-surface policy")
    if not policy.supported:
        details = "; ".join(policy.blockers) or "unsupported class surface"
        raise ValueError(f"Semantic class {policy.owner_path!r} has unsupported class-surface policy: {details}")
    return policy


def build_class_surface_policy(
    semantic_class: models.SemanticClass,
    *,
    owner_path: str,
    derived: DerivedTypePolicy,
    class_identities: dict[str, tuple[str, str]],
    strict_wrapper_names: bool = False,
) -> ClassSurfacePolicy:
    """Complete constructor, method, inheritance, and registration decisions."""
    naming = NamingPolicy(strict_public_names=strict_wrapper_names)
    fields = _python_named_class_fields(derived.fields, naming, owner_path)
    named_derived = replace(derived, fields=fields)
    methods = _python_named_class_methods(semantic_class, naming, owner_path)
    overloads = _python_named_class_overloads(semantic_class, naming, owner_path)
    constructor, constructor_blockers = _class_constructor_policy(
        semantic_class,
        owner_path=owner_path,
        derived=named_derived,
    )
    base_identities = tuple(
        identity
        for name in semantic_class.base_classes
        for identity in (class_identities.get(name),)
        if identity is not None
    )
    blockers = [*constructor_blockers]
    missing_bases = tuple(name for name in semantic_class.base_classes if name not in class_identities)
    blockers.extend(f"base class {name!r} has no completed native identity" for name in missing_bases)
    blockers.extend(_class_method_blockers(method) for method in methods if _class_method_blockers(method))
    return ClassSurfacePolicy(
        owner_path=owner_path,
        type_identity=derived.type_identity,
        python_exports=derived.python_exports,
        base_identities=base_identities,
        effective_fields=fields,
        constructor=constructor,
        methods=methods,
        overloads=overloads,
        registration=(
            ClassRegistrationAction.CREATE_TYPE,
            *((ClassRegistrationAction.SET_BASE,) if base_identities else ()),
            ClassRegistrationAction.READY_TYPE,
            ClassRegistrationAction.EXPORT_TYPE,
        ),
        supported=not blockers,
        blockers=tuple(blockers),
    )


def _python_named_class_fields(
    fields: tuple[DerivedFieldPolicy, ...],
    naming: NamingPolicy,
    owner_path: str,
) -> tuple[DerivedFieldPolicy, ...]:
    """Reserve readable Python field names while retaining native spellings."""
    namespace = (owner_path,)
    return tuple(
        replace(
            field,
            name=naming.reserve_public_name(
                namespace,
                field.name,
                category="field",
                owner=field.owner_path,
            ),
        )
        for field in fields
    )


def _python_named_class_methods(
    semantic_class: models.SemanticClass,
    naming: NamingPolicy,
    owner_path: str,
) -> tuple[ClassMethodPolicy, ...]:
    """Reserve method names in the same Python namespace as public fields."""
    namespace = (owner_path,)
    methods = []
    for method in semantic_class.methods:
        if method.name == "__init__":
            continue
        policy = _class_method_policy(owner_path, method)
        if policy.public:
            policy = replace(
                policy,
                python_name=naming.reserve_public_name(
                    namespace,
                    policy.python_name,
                    category="function",
                    owner=policy.owner_path,
                ),
            )
        methods.append(policy)
    return tuple(methods)


def _python_named_class_overloads(
    semantic_class: models.SemanticClass,
    naming: NamingPolicy,
    owner_path: str,
) -> tuple[OverloadPolicy, ...]:
    """Split reflected operators, then reserve every public overload name."""
    namespace = (owner_path,)
    policies = []
    for overload in semantic_class.overload_sets:
        names = tuple(
            dict.fromkeys(
                str(procedure.metadata.get(models.PYTHON_METHOD_NAME_METADATA, overload.name))
                for procedure in overload.procedures
            )
        )
        for python_name in names:
            procedures = tuple(
                procedure
                for procedure in overload.procedures
                if str(procedure.metadata.get(models.PYTHON_METHOD_NAME_METADATA, overload.name)) == python_name
            )
            policy = _overload_policy(owner_path, overload, python_name=python_name, procedures=procedures)
            policies.append(
                replace(
                    policy,
                    python_name=naming.reserve_public_name(
                        namespace,
                        policy.python_name,
                        category="function",
                        owner=policy.owner_path,
                    ),
                )
            )
    return tuple(policies)


def _class_constructor_policy(
    semantic_class: models.SemanticClass,
    *,
    owner_path: str,
    derived: DerivedTypePolicy,
) -> tuple[ConstructorPolicy, tuple[str, ...]]:
    """Select exactly one constructor surface from the semantic contract."""
    bound = tuple(
        method
        for method in semantic_class.methods
        if method.name == "__init__" and method.metadata.get(BIND_TARGET_METADATA)
    )
    overloads = tuple(item for item in semantic_class.overload_sets if item.name == "__init__")
    blockers = []
    if len(bound) > 1:
        blockers.append("class has more than one bound constructor")
    if len(overloads) > 1:
        blockers.append("class has more than one constructor overload set")
    if bound and overloads:
        blockers.append("class mixes bound and overloaded constructor kinds")
    lifecycle = (
        ConstructionLifecycleAction.ALLOCATE,
        ConstructionLifecycleAction.INITIALIZE,
        ConstructionLifecycleAction.COMMIT_OWNER,
        ConstructionLifecycleAction.CLEANUP_UNCOMMITTED,
        ConstructionLifecycleAction.DESTROY_OWNED,
    )
    if overloads:
        overload = overloads[0]
        return (
            ConstructorPolicy(
                kind=ClassConstructorKind.OVERLOAD_SET,
                fields=(),
                target_owner_path=None,
                overload_name=overload.name,
                lifecycle=lifecycle,
            ),
            tuple(blockers),
        )
    if bound:
        method = bound[0]
        target_name = str(method.metadata[BIND_TARGET_METADATA])
        return (
            ConstructorPolicy(
                kind=ClassConstructorKind.BOUND_PROCEDURE,
                fields=(),
                target_owner_path=f"{owner_path}.{target_name}",
                overload_name=None,
                lifecycle=lifecycle,
            ),
            tuple(blockers),
        )
    if semantic_class.origin.metadata.get(SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA):
        return (
            ConstructorPolicy(
                kind=ClassConstructorKind.ABSENT,
                fields=(),
                target_owner_path=None,
                overload_name=None,
                lifecycle=(),
                rejection_message=(f"{semantic_class.name} has no public constructor in the edited .pyi contract"),
            ),
            tuple(blockers),
        )
    fields_by_owner = {f"{owner_path}.{field.name}": field for field in semantic_class.fields}
    fields = tuple(
        ConstructorFieldPolicy(
            owner_path=field.owner_path,
            name=field.name,
            default_value=fields_by_owner[field.owner_path].default_value,
            setter_action=field.setter_action,
        )
        for field in derived.fields
        if field.object_kind is ObjectKind.SCALAR
        and field.semantic_type_name in _PLAN_PRIMITIVE_SCALAR_TYPES
        and field.setter_action is SetterAction.WRITE_THROUGH
    )
    return (
        ConstructorPolicy(
            kind=ClassConstructorKind.DEFAULT_FIELDS,
            fields=fields,
            target_owner_path=None,
            overload_name=None,
            lifecycle=lifecycle,
        ),
        tuple(blockers),
    )


def _class_method_policy(owner_path: str, method: models.SemanticMethod) -> ClassMethodPolicy:
    """Complete one concrete method descriptor without backend naming."""
    return ClassMethodPolicy(
        owner_path=f"{owner_path}.{method.name}",
        python_name=method.name,
        native_name=str(method.native_name or method.name),
        kind=ClassMethodKind.STATIC if method.is_static else ClassMethodKind.INSTANCE,
        passed_object_position=method.passed_object_position,
        public=method.visibility == "public",
        invocation=ClassInvocationKind.MODULE_PROCEDURE,
        type_bound_name=None,
    )


def _class_method_blockers(method: ClassMethodPolicy) -> str | None:
    """Return one exact incomplete method decision, if any."""
    if method.kind is ClassMethodKind.INSTANCE and method.passed_object_position is None:
        return f"method {method.python_name!r} has no completed passed-object position"
    if method.kind is ClassMethodKind.STATIC and method.passed_object_position is not None:
        return f"static method {method.python_name!r} has a passed-object position"
    return None


def _overload_policy(
    owner_path: str,
    overload: models.ProcedureOverloadSet,
    *,
    python_name: str | None = None,
    procedures: tuple[models.SemanticFunction, ...] | None = None,
    python_exports: tuple[PythonExportPolicy, ...] = (),
) -> OverloadPolicy:
    """Complete one overload set from explicit concrete-procedure links."""
    selected = tuple(overload.procedures) if procedures is None else procedures
    public_name = python_name or overload.name
    candidates = tuple(
        OverloadCandidatePolicy(
            owner_path=f"{owner_path}.{overload.name}.{procedure.name}",
            arguments=(),
            passed_object=False,
        )
        for procedure in selected
    )
    kind = str(selected[0].metadata.get(models.OVERLOAD_KIND_METADATA, "generic")) if candidates else "generic"
    return OverloadPolicy(
        owner_path=f"{owner_path}.{public_name}",
        python_name=public_name,
        kind=kind,
        candidates=candidates,
        python_exports=python_exports,
        unsupported_extra_argument_message=("modulus is not supported" if public_name == "__pow__" else None),
        identity_receiver_shortcut=kind == "assignment",
    )


def build_module_overload_policy(
    module: models.SemanticModule,
    overload: models.ProcedureOverloadSet,
) -> OverloadPolicy:
    """Complete the stable owner and Python exports for one module generic."""
    if not overload.procedures:
        return _overload_policy(module.name, overload)
    first = overload.procedures[0]
    native_scope = str(first.origin.native_scope or module.name)
    return _overload_policy(
        native_scope,
        overload,
        python_exports=completed_python_exports(first, overload.name),
    )


def derived_member_path_policies(
    root: DerivedTypePolicy,
    policies: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[tuple[DerivedMemberPathPolicy, ...], tuple[str, ...]]:
    """Flatten finite value-member paths while memoizing recursive identities."""
    paths: list[DerivedMemberPathPolicy] = []
    blockers: list[str] = []

    def visit(
        current: DerivedTypePolicy, prefix: tuple[str, ...], native_prefix: tuple[str, ...], active: tuple[str, ...]
    ):
        for field in current.fields:
            path = (*prefix, field.name)
            native_path = (*native_prefix, field.native_name)
            paths.append(
                DerivedMemberPathPolicy(
                    path=path,
                    native_path=native_path,
                    declaring_type_name=current.type_name,
                    declaring_type_identity=current.type_identity,
                    field=field,
                )
            )
            if field.object_kind is not ObjectKind.DERIVED_TYPE:
                continue
            if field.derived is None:
                blockers.append(f"member path {'.'.join(path)!r} has no completed derived handoff")
                continue
            nested = policies.get(field.derived.type_identity)
            if nested is None:
                blockers.append(
                    f"member path {'.'.join(path)!r} has no completed derived type {field.derived.type_identity!r}"
                )
                continue
            if nested.type_identity in active:
                blockers.append(
                    f"member path {'.'.join(path)!r} forms a recursive value edge without descriptor policy"
                )
                continue
            visit(nested, path, native_path, (*active, nested.type_identity))

    visit(root, (), (), (root.type_identity,))
    return tuple(paths), tuple(blockers)


def _derived_field_blockers(
    field: models.SemanticField,
    getter: OwnershipDecision,
    setter: OwnershipDecision,
    handle: NativeArrayHandleWrapperPolicy | None,
) -> list[str]:
    """Return exact unsupported public-field forms before lowering."""
    return [
        *_derived_field_completed_policy_blockers(field, getter, setter),
        *_derived_field_descriptor_blockers(field, handle),
        *_derived_field_object_kind_blockers(field, getter),
        *_derived_field_setter_blockers(field, setter),
    ]


def _derived_field_completed_policy_blockers(
    field: models.SemanticField,
    getter: OwnershipDecision,
    setter: OwnershipDecision,
) -> list[str]:
    """Return blockers already completed by getter and setter ownership policy."""
    blockers = []
    if getter.is_blocked:
        blockers.append(f"field {field.name!r} has blocked getter policy: {getter.blocker or getter.reason}")
    if setter.is_blocked:
        blockers.append(f"field {field.name!r} has blocked setter policy: {setter.blocker or setter.reason}")
    return blockers


def _derived_field_descriptor_blockers(
    field: models.SemanticField,
    handle: NativeArrayHandleWrapperPolicy | None,
) -> list[str]:
    """Return missing or unsupported descriptor-backed field blockers."""
    semantic_type = field.semantic_type
    rank = int(semantic_type.rank or 0)
    blockers: list[str] = []
    descriptor = native_array_descriptor_kind(semantic_type)
    if descriptor is not None and rank > 0 and handle is None:
        blockers.append(f"field {field.name!r} is missing completed {descriptor} handle policy")
    if _is_descriptor_backed_scalar_derived_type(semantic_type):
        blockers.append(f"field {field.name!r} is an unsupported descriptor-backed scalar derived value")
    return blockers


def _derived_field_object_kind_blockers(
    field: models.SemanticField,
    getter: OwnershipDecision,
) -> list[str]:
    """Return blockers selected by the completed public field object kind."""
    semantic_type = field.semantic_type
    rank = int(semantic_type.rank or 0)
    blockers: list[str] = []
    if getter.kind is ObjectKind.NUMPY_ARRAY:
        if semantic_type.name not in _PLAN_PRIMITIVE_SCALAR_TYPES | {"String"}:
            blockers.append(f"field {field.name!r} is an unsupported array of derived values")
    elif getter.kind is ObjectKind.DERIVED_TYPE:
        if rank != 0:
            blockers.append(f"field {field.name!r} is not a scalar derived value")
        if semantic_type.metadata.get("fortran_polymorphic"):
            blockers.append(f"field {field.name!r} is polymorphic")
    elif getter.kind is ObjectKind.STRING:
        if rank != 0 or _character_length(semantic_type) is None:
            blockers.append(f"field {field.name!r} is not a fixed scalar string")
    elif (
        getter.kind is ObjectKind.SCALAR
        and semantic_type.name not in _PLAN_PRIMITIVE_SCALAR_TYPES
        and not _is_descriptor_backed_scalar_derived_type(semantic_type)
    ):
        blockers.append(f"field {field.name!r} is not a supported primitive scalar")
    return blockers


def _derived_field_setter_blockers(
    field: models.SemanticField,
    setter: OwnershipDecision,
) -> list[str]:
    """Return blockers for an incomplete native write-through assignment."""
    if setter.setter_action is SetterAction.WRITE_THROUGH and setter.assignment_mode not in {
        AssignmentMode.VALUE_COPY,
        AssignmentMode.ALIAS,
    }:
        return [f"field {field.name!r} has no completed native setter assignment"]
    return []


def completed_module_variable_policy(
    variable: models.SemanticVariable,
) -> ModuleVariablePolicy:
    """Return the completed module-variable policy or fail closed."""
    policy = variable.metadata.get(models.RESOLVED_MODULE_VARIABLE_POLICY_METADATA)
    if not isinstance(policy, ModuleVariablePolicy):
        raise ValueError(f"Semantic variable {variable.name!r} has no completed module-variable policy")
    if not policy.supported:
        details = "; ".join(policy.blockers)
        raise ValueError(f"Semantic variable {policy.owner_path!r} has unsupported module-variable policy: {details}")
    return policy


def build_module_variable_policy(
    variable: models.SemanticVariable,
    *,
    module_name: str,
    derived_types: dict[tuple[str, str], DerivedTypePolicy] | None = None,
) -> ModuleVariablePolicy:
    """Build one module-variable policy from completed decisions."""
    owner_path = f"{module_name}.{variable.name}"
    getter = _ownership_decision(variable, models.RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA)
    setter = _ownership_decision(variable, models.RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA)
    descriptor_kind = _scalar_module_descriptor_kind(variable)
    constant = _is_scalar_module_constant(variable)
    native_array_handle = _native_array_handle_wrapper_policy(
        variable.semantic_type,
        variable.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
        owner_path,
    )
    array = _array_handoff_policy(variable.semantic_type)
    if native_array_handle is not None:
        policy = _native_array_module_variable_policy(
            variable,
            module_name,
            owner_path,
            getter,
            setter,
            native_array_handle,
        )
    elif getter is not None and getter.kind is ObjectKind.DERIVED_TYPE:
        policy = _derived_module_variable_policy(
            variable,
            module_name,
            owner_path,
            getter,
            setter,
            constant,
            derived_types or {},
        )
    elif getter is not None and getter.kind is ObjectKind.NUMPY_ARRAY and array is not None:
        policy = _ordinary_array_module_variable_policy(
            variable,
            module_name,
            owner_path,
            getter,
            setter,
            array,
        )
    else:
        policy = _scalar_module_variable_policy(
            variable,
            module_name,
            owner_path,
            getter,
            setter,
            descriptor_kind,
            constant,
        )
    return _complete_module_variable_policy(variable, policy)


def _complete_module_variable_policy(
    variable: models.SemanticVariable,
    policy: ModuleVariablePolicy,
) -> ModuleVariablePolicy:
    """Complete runtime validation and initializer limitations on one policy."""
    validation_blockers = _runtime_semantic_validation_blockers(
        variable.semantic_type,
        f"module variable {variable.name!r}",
    )
    if validation_blockers:
        policy = replace(
            policy,
            supported=False,
            blockers=(*policy.blockers, *validation_blockers),
        )
    if variable.default_value is None or _is_scalar_module_constant(variable):
        return policy
    if policy.initializer is not None:
        return policy
    if variable.semantic_type.rank != 0:
        reason = (
            "module variable initializer requires scalar storage with a write-through native setter; "
            "rank-positive variables cannot be initialized during module import"
        )
    else:
        reason = (
            "module variable initializer requires a write-through native setter; "
            f"completed setter action is {policy.setter_action.value!r}"
        )
    return replace(
        policy,
        supported=False,
        blockers=(*policy.blockers, reason),
    )


def _module_variable_policy_base(
    variable: models.SemanticVariable,
    module_name: str,
    owner_path: str,
) -> dict[str, object]:
    """Return identity fields shared by every module-variable policy family."""
    return {
        "owner_path": owner_path,
        "name": variable.name,
        "python_exports": completed_python_exports(variable, variable.name),
        "native_name": str(variable.origin.native_name or variable.name),
        "native_module": str(variable.origin.native_scope or module_name),
        "semantic_type_name": variable.semantic_type.name,
        "rank": int(variable.semantic_type.rank or 0),
    }


def _native_array_module_variable_policy(
    variable: models.SemanticVariable,
    module_name: str,
    owner_path: str,
    getter: OwnershipDecision | None,
    setter: OwnershipDecision | None,
    handle: NativeArrayHandleWrapperPolicy,
) -> ModuleVariablePolicy:
    """Build one persistent native-array handle module policy."""
    blockers = _native_array_module_variable_blockers(variable, getter, setter, handle)
    return ModuleVariablePolicy(
        **_module_variable_policy_base(variable, module_name, owner_path),
        getter_action=ModuleGetterAction.NATIVE_ARRAY_HANDLE,
        getter=getter,
        setter_action=handle.setter_action,
        native_assignment=handle.native_assignment,
        setter=setter,
        descriptor_kind=handle.descriptor_kind.value,
        initializer=None,
        constant_value=None,
        supported=not blockers,
        blockers=tuple(blockers),
        native_array_handle=handle,
    )


def _derived_module_variable_policy(
    variable: models.SemanticVariable,
    module_name: str,
    owner_path: str,
    getter: OwnershipDecision,
    setter: OwnershipDecision | None,
    constant: bool,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> ModuleVariablePolicy:
    """Build one constant-copy or live derived module-object policy."""
    builder = _derived_module_constant_policy if constant else _derived_module_object_policy
    derived = builder(variable, getter, setter, owner_path=owner_path, derived_types=derived_types)
    blocker_builder = _derived_module_constant_blockers if constant else _derived_module_variable_blockers
    blockers = blocker_builder(variable, getter, setter, derived)
    return ModuleVariablePolicy(
        **_module_variable_policy_base(variable, module_name, owner_path),
        getter_action=ModuleGetterAction.DERIVED_OBJECT,
        getter=getter,
        setter_action=derived.replacement,
        native_assignment=AssignmentMode.NONE,
        setter=setter,
        descriptor_kind=None,
        initializer=None,
        constant_value=None,
        supported=not blockers,
        blockers=tuple(blockers),
        derived=derived,
    )


def _ordinary_array_module_variable_policy(
    variable: models.SemanticVariable,
    module_name: str,
    owner_path: str,
    getter: OwnershipDecision,
    setter: OwnershipDecision | None,
    array: ArrayHandoffPolicy,
) -> ModuleVariablePolicy:
    """Build one borrowed ordinary module-array view policy."""
    blockers = _ordinary_array_module_variable_blockers(variable, getter, setter, array)
    return ModuleVariablePolicy(
        **_module_variable_policy_base(variable, module_name, owner_path),
        getter_action=ModuleGetterAction.BORROWED_ARRAY_VIEW,
        getter=getter,
        setter_action=setter.setter_action if setter is not None else SetterAction.OMIT,
        native_assignment=AssignmentMode.NONE,
        setter=setter,
        descriptor_kind=None,
        initializer=None,
        constant_value=None,
        supported=not blockers,
        blockers=tuple(blockers),
        array=array,
    )


def _scalar_module_variable_policy(
    variable: models.SemanticVariable,
    module_name: str,
    owner_path: str,
    getter: OwnershipDecision | None,
    setter: OwnershipDecision | None,
    descriptor_kind: str | None,
    constant: bool,
) -> ModuleVariablePolicy:
    """Build one scalar value, snapshot, or constant module policy."""
    blockers = _scalar_module_variable_blockers(variable, getter, setter, descriptor_kind, constant)
    initializer = variable.metadata.get(models.RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA)
    return ModuleVariablePolicy(
        **_module_variable_policy_base(variable, module_name, owner_path),
        getter_action=_scalar_module_getter_action(getter, constant),
        getter=getter,
        setter_action=setter.setter_action if setter is not None else SetterAction.OMIT,
        native_assignment=_scalar_module_native_assignment(setter),
        setter=setter,
        descriptor_kind=descriptor_kind,
        initializer=(
            _scalar_module_literal_value(initializer, variable.semantic_type.name) if initializer is not None else None
        ),
        constant_value=(
            _scalar_module_literal_value(variable.default_value, variable.semantic_type.name)
            if constant and variable.default_value is not None
            else None
        ),
        supported=not blockers,
        blockers=tuple(blockers),
    )


def _ordinary_array_module_variable_blockers(
    variable: models.SemanticVariable,
    getter: OwnershipDecision,
    setter: OwnershipDecision | None,
    array: ArrayHandoffPolicy,
) -> tuple[str, ...]:
    """Validate one fixed addressable module array borrowed as a live view."""
    blockers = []
    if array.rank is None or array.rank <= 0 or len(array.shape) != array.rank:
        blockers.append("ordinary module array requires one concrete fixed rank")
    if variable.semantic_type.name not in _PLAN_PRIMITIVE_SCALAR_TYPES:
        blockers.append("ordinary module array requires a primitive numeric element type")
    if not variable.semantic_type.metadata.get("aliased"):
        blockers.append("ordinary module array requires addressable Aliased target storage")
    expected_getter = (
        ("owner", getter.owner, OwnershipOwner.NATIVE),
        ("transfer", getter.transfer, TransferMode.BORROWED_VIEW),
        ("destruction", getter.destruction, DestructionPolicy.NATIVE_OWNER),
        ("storage", getter.storage_mode, StorageMode.ALIAS),
    )
    blockers.extend(
        f"ordinary module array getter {name} is {actual.value}, not {required.value}"
        for name, actual, required in expected_getter
        if actual is not required
    )
    if setter is None or setter.setter_action is not SetterAction.REJECT_REPLACEMENT:
        blockers.append("ordinary module array must reject whole-array replacement")
    return tuple(blockers)


def completed_function_wrapper_policy(function: models.SemanticFunction) -> FunctionWrapperPolicy:
    """Return a completed function wrapper policy or fail before planning."""

    policy = function.metadata.get(models.RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA)
    if not isinstance(policy, FunctionWrapperPolicy):
        raise ValueError(
            f"Semantic function {function.name!r} is missing completed wrapper policy; "
            "run complete_semantic_policies before wrapper planning"
        )
    if not policy.supported:
        details = "; ".join(policy.blockers) or "unsupported wrapper policy"
        raise ValueError(f"Semantic function {policy.owner_path!r} has unsupported wrapper policy: {details}")
    return policy


def build_callback_handoff_policy(
    semantic_type: models.SemanticType,
    *,
    owner_path: str,
) -> CallbackHandoffPolicy:
    """Complete one immediate callback without consulting lowering details."""
    raw_arguments = semantic_type.metadata.get("callback_arguments")
    return_type = semantic_type.metadata.get("return")
    blockers = list(_callback_envelope_blockers(semantic_type))
    if not isinstance(raw_arguments, list) or not all(
        isinstance(argument, models.SemanticArgument) for argument in raw_arguments
    ):
        blockers.append("callback signature is missing ordered argument records")
        arguments: tuple[CallbackTransferPolicy, ...] = ()
    else:
        arguments = tuple(
            _callback_transfer_policy(argument, owner_path=f"{owner_path}.callback_arg_{index}")
            for index, argument in enumerate(raw_arguments)
        )
        blockers.extend(
            reason
            for index, argument in enumerate(raw_arguments)
            for reason in _callback_transfer_blockers(argument, arguments[index])
        )
    result = _callback_result_policy(return_type, owner_path=f"{owner_path}.callback_result")
    blockers.extend(_callback_result_blockers(return_type, result))
    prototype_ref = semantic_type.metadata.get(models.PROTOTYPE_REF_METADATA)
    prototype_name = prototype_ref.get("name") if isinstance(prototype_ref, dict) else None
    prototype_module = prototype_ref.get("origin_module") if isinstance(prototype_ref, dict) else None
    if not isinstance(prototype_name, str) or not prototype_name:
        blockers.append("callback argument requires a resolved named prototype")
        prototype_name = semantic_type.name
    declaration_mode = _callback_declaration_mode(raw_arguments, return_type, semantic_type)
    if declaration_mode is ExternalDeclarationMode.EXPLICIT_INTERFACE and not (
        isinstance(prototype_module, str) and prototype_module
    ):
        blockers.append(f"prototype {prototype_name!r} requires an importable native module")
    return CallbackHandoffPolicy(
        owner_path=owner_path,
        prototype_name=prototype_name,
        prototype_module=(prototype_module if isinstance(prototype_module, str) and prototype_module else None),
        declaration_mode=declaration_mode,
        arguments=arguments,
        result=result,
        lifecycle=(
            CallbackLifecycleAction.VALIDATE_CALLBACK,
            CallbackLifecycleAction.RETAIN_CALLABLE,
            CallbackLifecycleAction.PUSH_CONTEXT,
            CallbackLifecycleAction.ENTER_NATIVE,
            CallbackLifecycleAction.POP_CONTEXT,
            CallbackLifecycleAction.RELEASE_CALLBACK,
        ),
        thread_action=CallbackThreadAction.REQUIRE_ENTERING_THREAD,
        gil_actions=(CallbackGILAction.ACQUIRE_GIL, CallbackGILAction.RELEASE_GIL),
        fatal_action=CallbackFatalAction.ABORT_WITH_PYTHON_ERROR,
        supported=not blockers,
        blockers=tuple(blockers),
    )


def _callback_declaration_mode(
    arguments: object,
    return_type: object,
    semantic_type: models.SemanticType,
) -> ExternalDeclarationMode:
    """Select the weakest correct adapter declaration from prototype facts."""
    if isinstance(arguments, list) and any(
        isinstance(argument, models.SemanticArgument) and _prototype_argument_requires_explicit_interface(argument)
        for argument in arguments
    ):
        return ExternalDeclarationMode.EXPLICIT_INTERFACE
    if isinstance(return_type, models.SemanticType) and _prototype_result_requires_explicit_interface(return_type):
        return ExternalDeclarationMode.EXPLICIT_INTERFACE
    prototype_metadata = semantic_type.metadata.get("prototype_metadata")
    attributes = prototype_metadata.get("fortran_attributes", ()) if isinstance(prototype_metadata, dict) else ()
    normalized = {str(attribute).casefold().replace(" ", "") for attribute in attributes}
    if normalized & {"bind(c)", "elemental", "pure"}:
        return ExternalDeclarationMode.EXPLICIT_INTERFACE
    return ExternalDeclarationMode.IMPLICIT_EXTERNAL


def _prototype_argument_requires_explicit_interface(argument: models.SemanticArgument) -> bool:
    semantic_type = argument.semantic_type
    storage = semantic_type.storage
    array = storage.array if storage is not None else None
    if argument.optional:
        return True
    if any(
        semantic_type.metadata.get(name)
        for name in (
            "fortran_allocatable",
            "fortran_pointer",
            "fortran_polymorphic",
            "fortran_assumed_type",
            "fortran_target",
        )
    ):
        return True
    return array is not None and array.category in {"assumed_shape", "deferred_shape", "assumed_rank"}


def _prototype_result_requires_explicit_interface(return_type: models.SemanticType) -> bool:
    if return_type.name == "None":
        return False
    if return_type.rank > 0:
        return True
    if return_type.metadata.get("fortran_allocatable") or return_type.metadata.get("fortran_pointer"):
        return True
    if return_type.name != "String":
        return False
    length = return_type.metadata.get("fortran_character_length")
    return length is None or str(length).strip() in {"", ":", "*"}


def _callback_envelope_blockers(semantic_type: models.SemanticType) -> tuple[str, ...]:
    """Require the documented immediate, entering-thread fatal envelope."""
    required = {
        "callback_lifetime": "call",
        "callback_thread": "entering_thread",
        "callback_exception": "print_traceback_and_abort",
    }
    blockers = [
        f"callback {name.removeprefix('callback_').replace('_', ' ')} must be {expected!r}, "
        f"not {semantic_type.metadata.get(name)!r}"
        for name, expected in required.items()
        if semantic_type.metadata.get(name) != expected
    ]
    return tuple(blockers)


def _callback_transfer_policy(
    argument: models.SemanticArgument,
    *,
    owner_path: str,
) -> CallbackTransferPolicy:
    """Classify one callback argument after nested ownership completion."""
    semantic_type = argument.semantic_type
    decision = _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)
    if decision is None:
        raise ValueError(f"Callback transfer {owner_path!r} is missing completed ownership policy")
    passed_by_value = bool(argument.origin.metadata.get("value"))
    derived = _is_scalar_derived_type(semantic_type)
    array = _array_handoff_policy(semantic_type) if int(semantic_type.rank or 0) > 0 else None
    return CallbackTransferPolicy(
        owner_path=owner_path,
        name=argument.name,
        semantic_type_name=semantic_type.name,
        object_kind=decision.kind,
        rank=int(semantic_type.rank or 0),
        passed_by_value=passed_by_value,
        abi=_callback_abi_kind(argument, derived=derived),
        adapter_action=_callback_adapter_action(argument),
        python_action=decision.python_barrier_action,
        character_length=_character_length(semantic_type),
        array=array,
        derived_type_identity=(_derived_type_identity(semantic_type, owner_path) if derived else None),
    )


def _callback_abi_kind(
    argument: models.SemanticArgument,
    *,
    derived: bool,
) -> CallbackABIKind:
    """Select the C-facing callback ABI from completed type and access facts."""
    semantic_type = argument.semantic_type
    if derived:
        return CallbackABIKind.DERIVED_ADDRESS
    if semantic_type.name == "String":
        return CallbackABIKind.DATA_AND_LENGTH
    if int(semantic_type.rank or 0) > 0:
        return CallbackABIKind.DATA_AND_SHAPE
    if bool(argument.origin.metadata.get("value")):
        return CallbackABIKind.VALUE
    return CallbackABIKind.REFERENCE


def _callback_adapter_action(
    argument: models.SemanticArgument,
) -> CallbackTransferAction:
    """Select isolated primitive values or permissive non-scalar writeback."""
    semantic_type = argument.semantic_type
    if bool(argument.origin.metadata.get("value")) or (
        semantic_type.name in _PLAN_PRIMITIVE_SCALAR_TYPES and int(semantic_type.rank or 0) == 0
    ):
        return CallbackTransferAction.COPY_IN
    return CallbackTransferAction.COPY_IN_OUT


def _callback_transfer_blockers(
    argument: models.SemanticArgument,
    transfer: CallbackTransferPolicy,
) -> tuple[str, ...]:
    """Reject callback forms whose typed adapter ABI is incomplete."""
    semantic_type = argument.semantic_type
    blockers = list(_runtime_semantic_validation_blockers(semantic_type, f"callback argument {argument.name!r}"))
    if argument.optional:
        blockers.append(f"callback argument {argument.name!r} cannot be optional")
    if _uses_unsupported_callback_descriptor(semantic_type):
        blockers.append(
            f"callback argument {argument.name!r} uses unsupported allocatable, pointer, "
            "polymorphic, or assumed-type storage"
        )
    if transfer.passed_by_value and transfer.rank > 0:
        blockers.append(f"callback argument {argument.name!r} cannot pass an array by value")
    if semantic_type.name == "String":
        if transfer.character_length is None or transfer.character_length <= 0:
            blockers.append(f"callback argument {argument.name!r} requires a fixed positive character length")
    elif transfer.rank > 0:
        if transfer.array is None or len(transfer.array.shape) != transfer.rank:
            blockers.append(f"callback argument {argument.name!r} has incomplete array shape")
        if semantic_type.name not in _PLAN_PRIMITIVE_SCALAR_TYPES:
            blockers.append(f"callback argument {argument.name!r} is an unsupported array of derived values")
    elif transfer.derived_type_identity is None and semantic_type.name not in _PLAN_PRIMITIVE_SCALAR_TYPES:
        blockers.append(f"callback argument {argument.name!r} has unsupported type {semantic_type.name!r}")
    return tuple(blockers)


def _callback_result_policy(
    return_type: object,
    *,
    owner_path: str,
) -> CallbackResultPolicy:
    """Complete the representation returned from Python through the trampoline."""
    if not isinstance(return_type, models.SemanticType) or return_type.name in {"None", "Void"}:
        return CallbackResultPolicy(None, CallbackResultAction.RETURN_VOID)
    decision = return_type.metadata.get(models.RESOLVED_OWNERSHIP_POLICY_METADATA)
    if not isinstance(decision, OwnershipDecision):
        return CallbackResultPolicy(None, CallbackResultAction.REJECT_RESULT)
    derived = _is_scalar_derived_type(return_type)
    transfer = CallbackTransferPolicy(
        owner_path=owner_path,
        name="result",
        semantic_type_name=return_type.name,
        object_kind=decision.kind,
        rank=int(return_type.rank or 0),
        passed_by_value=False,
        abi=(
            CallbackABIKind.DERIVED_ADDRESS
            if derived
            else CallbackABIKind.DATA_AND_SHAPE
            if int(return_type.rank or 0) > 0
            else CallbackABIKind.VALUE
        ),
        adapter_action=CallbackTransferAction.COPY_OUT,
        python_action=decision.python_barrier_action,
        character_length=_character_length(return_type),
        array=_array_handoff_policy(return_type) if int(return_type.rank or 0) > 0 else None,
        derived_type_identity=(_derived_type_identity(return_type, owner_path) if derived else None),
    )
    if derived:
        action = CallbackResultAction.RETURN_DERIVED_ADDRESS
    elif int(return_type.rank or 0) > 0:
        action = CallbackResultAction.RETURN_ARRAY_ADDRESS
    elif return_type.name in _PLAN_PRIMITIVE_SCALAR_TYPES:
        action = CallbackResultAction.RETURN_SCALAR
    else:
        action = CallbackResultAction.REJECT_RESULT
    return CallbackResultPolicy(transfer, action)


def _callback_result_blockers(
    return_type: object,
    result: CallbackResultPolicy,
) -> tuple[str, ...]:
    """Require an exact void, primitive, fixed-array, or derived callback result."""
    if result.action is CallbackResultAction.RETURN_VOID:
        return ()
    if not isinstance(return_type, models.SemanticType) or result.transfer is None:
        return ("callback result is missing a completed semantic type",)
    transfer = result.transfer
    blockers = list(_runtime_semantic_validation_blockers(return_type, "callback result"))
    if _uses_unsupported_callback_descriptor(return_type):
        blockers.append("callback result uses unsupported allocatable, pointer, polymorphic, or assumed-type storage")
    if result.action is CallbackResultAction.REJECT_RESULT:
        blockers.append(f"callback result type {return_type.name!r} is unsupported")
    if result.action is CallbackResultAction.RETURN_ARRAY_ADDRESS:
        if transfer.array is None or len(transfer.array.shape) != transfer.rank:
            blockers.append("callback array result requires a complete fixed shape")
        if return_type.name not in _PLAN_PRIMITIVE_SCALAR_TYPES:
            blockers.append("callback array result must contain a primitive scalar type")
    return tuple(blockers)


def _uses_unsupported_callback_descriptor(semantic_type: models.SemanticType) -> bool:
    """Return whether callback lowering lacks the native descriptor ABI."""
    return any(
        semantic_type.metadata.get(name)
        for name in (
            "fortran_allocatable",
            "fortran_pointer",
            "fortran_polymorphic",
            "fortran_assumed_type",
        )
    )


def build_function_wrapper_policy(
    function: models.SemanticFunction,
    *,
    owner_path: str,
    derived_types: dict[tuple[str, str], DerivedTypePolicy] | None = None,
    class_call: ClassMethodPolicy | None = None,
    module_export: bool | None = None,
    polymorphic_variants: dict[tuple[str, str], tuple[tuple[str, str], ...]] | None = None,
    native_dispatch_name: str | None = None,
) -> FunctionWrapperPolicy:
    """Build typed function policy from completed post-IR decisions."""

    completed_derived_types = derived_types or {}
    argument_native_positions, native_call_slots, slot_blockers = _native_call_slot_policies(
        function,
        owner_path,
        completed_derived_types,
    )
    arguments, argument_blockers = _argument_policies(
        function,
        owner_path,
        argument_native_positions,
        native_call_slots,
        completed_derived_types,
        polymorphic_variants or {},
        class_call,
    )
    results, result_blockers = _result_policies(function, owner_path, completed_derived_types)
    writeback_actions, lifecycle_blockers = _lifecycle_policies(arguments)
    cleanup_actions, release_actions = _derived_result_lifecycle_policies(results)
    status_error = _completed_native_status_error_policy(function)
    native_module = _native_module(function, owner_path)
    blockers = (
        _function_shape_blockers(function, class_call)
        + argument_blockers
        + result_blockers
        + slot_blockers
        + lifecycle_blockers
        + _result_position_blockers(results, arguments)
        + _array_extent_reference_blockers(function, arguments, results)
        + _runtime_status_plan_blockers(status_error)
        + _string_result_status_blockers(results, status_error)
        + _string_writeback_status_blockers(arguments, status_error)
    )
    native_name = native_dispatch_name or _native_name(function)
    native_invocation, native_operator = _native_invocation_policy(native_name)
    external = _is_external(function)
    return FunctionWrapperPolicy(
        owner_path=owner_path,
        python_exports=completed_python_exports(function, function.name),
        native_name=native_name,
        native_invocation=native_invocation,
        native_operator=native_operator,
        external=external,
        external_declaration=_external_declaration_mode(
            external=external,
            native_invocation=native_invocation,
            arguments=tuple(arguments),
            results=results,
            native_call_slots=tuple(native_call_slots),
        ),
        native_module=native_module,
        native_is_subroutine=_native_is_subroutine(function),
        hold_gil=bool(function.metadata.get(models.RUNTIME_HOLD_GIL_METADATA))
        or any(argument.callback is not None for argument in arguments),
        status_error=status_error,
        class_call=class_call,
        module_export=(
            not bool(function.metadata.get("fortran_type_bound_target")) if module_export is None else module_export
        ),
        supported=not blockers,
        arguments=tuple(arguments),
        results=results,
        native_call_slots=tuple(native_call_slots),
        blockers=tuple(blockers),
        writeback_actions=writeback_actions,
        cleanup_actions=cleanup_actions,
        release_actions=release_actions,
    )


def _native_invocation_policy(native_name: str) -> tuple[NativeInvocationKind, str | None]:
    """Classify procedure, defined-operator, and defined-assignment syntax once."""
    compact = "".join(native_name.split()).casefold()
    if compact == "assignment(=)":
        return NativeInvocationKind.DEFINED_ASSIGNMENT, "="
    if compact.startswith("operator(") and compact.endswith(")"):
        return NativeInvocationKind.DEFINED_OPERATOR, compact[len("operator(") : -1]
    return NativeInvocationKind.PROCEDURE, None


def _external_declaration_mode(
    *,
    external: bool,
    native_invocation: NativeInvocationKind,
    arguments: tuple[ArgumentPolicy, ...],
    results: tuple[ResultPolicy, ...],
    native_call_slots: tuple[NativeCallSlotPolicy, ...],
) -> ExternalDeclarationMode:
    """Choose the weakest correct native declaration from completed ABI facts."""
    if not external:
        return ExternalDeclarationMode.NONE
    if native_invocation is not NativeInvocationKind.PROCEDURE:
        return ExternalDeclarationMode.EXPLICIT_INTERFACE
    if any(_argument_requires_explicit_interface(argument) for argument in arguments):
        return ExternalDeclarationMode.EXPLICIT_INTERFACE
    if any(_result_requires_explicit_interface(result) for result in results):
        return ExternalDeclarationMode.EXPLICIT_INTERFACE
    if any(_slot_requires_explicit_interface(slot) for slot in native_call_slots):
        return ExternalDeclarationMode.EXPLICIT_INTERFACE
    return ExternalDeclarationMode.IMPLICIT_EXTERNAL


def _argument_requires_explicit_interface(argument: ArgumentPolicy) -> bool:
    """Return whether one completed native dummy cannot use an implicit interface."""
    if argument.optional_mode is not OptionalMode.REQUIRED:
        return True
    if argument.native_array_handle is not None or argument.derived is not None or argument.polymorphic is not None:
        return True
    if argument.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
        return True
    return _array_requires_explicit_interface(argument.array)


def _result_requires_explicit_interface(result: ResultPolicy) -> bool:
    """Return whether one completed native result requires an explicit interface."""
    if result.source_kind != "direct_return":
        return False
    if result.scalar_descriptor is not None or result.native_array_handle is not None or result.derived is not None:
        return True
    if result.rank > 0 or result.semantic_type_name == "String":
        return True
    return _array_requires_explicit_interface(result.array)


def _slot_requires_explicit_interface(slot: NativeCallSlotPolicy) -> bool:
    """Return whether one ordered native slot carries descriptor-only ABI semantics."""
    if slot.value_kind == "value":
        return True
    if slot.native_array_handle is not None or slot.scalar_descriptor is not None or slot.derived is not None:
        return True
    return _array_requires_explicit_interface(slot.array)


def _array_requires_explicit_interface(array: ArrayHandoffPolicy | None) -> bool:
    """Return whether an array dummy uses a descriptor-based Fortran category."""
    return array is not None and array.category in {"assumed_shape", "deferred_shape", "assumed_rank"}


def _argument_policies(
    function: models.SemanticFunction,
    owner_path: str,
    argument_native_positions: dict[int, int],
    native_call_slots: tuple[NativeCallSlotPolicy, ...],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
    polymorphic_variants: dict[tuple[str, str], tuple[tuple[str, str], ...]],
    class_call: ClassMethodPolicy | None,
) -> tuple[list[ArgumentPolicy], tuple[str, ...]]:
    """Complete visible arguments through one uniform per-argument leaf."""
    policies: list[ArgumentPolicy] = []
    blockers: list[str] = []
    python_position = 0
    for argument in function.arguments:
        decision = _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)
        if decision is None:
            blockers.append(f"argument {argument.name!r} is missing completed ownership policy")
            continue
        if decision.projects_result and not decision.python_visible:
            continue
        current_python_position = python_position
        python_position += 1
        native_position = argument_native_positions.get(current_python_position)
        if native_position is None:
            blockers.append(f"argument {argument.name!r} has no completed native-call slot")
            native_position = -1
        policy, argument_blockers = _argument_policy(
            function,
            argument,
            decision,
            owner_path,
            current_python_position,
            native_position,
            _native_call_slot_for_python_position(native_call_slots, current_python_position),
            derived_types,
            polymorphic_variants,
            class_call,
        )
        policies.append(policy)
        blockers.extend(argument_blockers)
    return policies, tuple(blockers)


def _native_call_slot_for_python_position(
    slots: tuple[NativeCallSlotPolicy, ...],
    python_position: int,
) -> NativeCallSlotPolicy | None:
    """Find the completed native-call slot owned by one visible argument."""
    return next((slot for slot in slots if slot.python_position == python_position), None)


def _argument_policy(
    function: models.SemanticFunction,
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    owner_path: str,
    python_position: int,
    native_position: int,
    native_slot: NativeCallSlotPolicy | None,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
    polymorphic_variants: dict[tuple[str, str], tuple[tuple[str, str], ...]],
    class_call: ClassMethodPolicy | None,
) -> tuple[ArgumentPolicy, tuple[str, ...]]:
    """Complete one visible argument without mixing it with list traversal."""
    argument_path = f"{owner_path}.{argument.name}"
    optional_mode = _optional_mode(argument, decision)
    callback = _callback_handoff_policy(argument)
    array_policy = _array_handoff_policy(argument.semantic_type)
    transformations, transformation_blockers = _argument_transformation_policies(
        argument,
        decision,
        array_policy,
    )
    derived = _argument_derived_handoff(argument, decision, callback, argument_path, derived_types)
    derived_call = _argument_derived_call(argument, decision, callback, native_position)
    polymorphic = _polymorphic_dispatch_policy(
        argument,
        decision,
        derived,
        polymorphic_variants,
        owner_path=argument_path,
        force=_is_passed_object_argument(class_call, native_position),
    )
    bridge_data_action, bridge_copy_reason = _completed_argument_bridge_action(
        decision,
        optional_mode,
        native_slot,
        callback,
        derived,
    )
    boundary = _argument_boundary_policy(function, argument, decision, python_position, callback)
    blockers = _completed_argument_blockers(
        argument,
        decision,
        callback,
        derived,
        derived_call,
        polymorphic,
        bridge_data_action,
        bridge_copy_reason,
        transformation_blockers,
        derived_types,
    )
    return (
        ArgumentPolicy(
            owner_path=argument_path,
            name=argument.name,
            python_name=argument.name,
            native_name=_argument_native_name(function, python_position, argument),
            python_position=python_position,
            native_position=native_position,
            semantic_type_name=argument.semantic_type.name,
            rank=int(argument.semantic_type.rank or 0),
            optional=argument.optional,
            optional_mode=boundary.optional_mode,
            handoff_mode=boundary.handoff_mode,
            bridge_data_action=bridge_data_action,
            bridge_copy_reason=bridge_copy_reason,
            nullable=boundary.nullable,
            writable=boundary.writable,
            descriptor_boundary=boundary.descriptor_boundary,
            ownership=decision,
            codegen_action=boundary.codegen_action,
            python_barrier_action=boundary.python_barrier_action,
            native_barrier_action=boundary.native_barrier_action,
            storage_mode=boundary.storage_mode,
            boundary_storage_mode=boundary.boundary_storage_mode,
            projects_result=boundary.projects_result,
            python_visible=decision.python_visible,
            result_position=boundary.result_position,
            character_length=_character_length(argument.semantic_type),
            array=array_policy,
            native_array_actual=_native_array_actual_policy(argument, decision, array_policy),
            native_array_handle=_native_array_handle_wrapper_policy(
                argument.semantic_type,
                argument.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
                argument_path,
            ),
            derived=derived,
            derived_call=derived_call,
            callback=callback,
            polymorphic=polymorphic,
            transformations=transformations,
        ),
        blockers,
    )


def _callback_handoff_policy(argument: models.SemanticArgument) -> CallbackHandoffPolicy | None:
    """Read the completed callback policy without interpreting callback syntax."""
    policy = argument.semantic_type.metadata.get(models.RESOLVED_CALLBACK_POLICY_METADATA)
    return policy if isinstance(policy, CallbackHandoffPolicy) else None


def _argument_derived_handoff(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    callback: CallbackHandoffPolicy | None,
    owner_path: str,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> DerivedHandoffPolicy | None:
    """Complete the ordinary derived handoff, or leave callback transfer opaque."""
    if callback is not None:
        return None
    return _derived_handoff_policy(
        argument.semantic_type,
        decision,
        owner_path=owner_path,
        origin=DerivedObjectOrigin.CALLER_WRAPPER,
        native_value=_native_by_value_argument(argument),
        derived_types=derived_types,
    )


def _argument_derived_call(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    callback: CallbackHandoffPolicy | None,
    native_position: int,
) -> DerivedCallPolicy | None:
    """Keep callback and ordinary derived-call policies mutually exclusive."""
    if callback is not None:
        return None
    return _derived_call_policy(argument, decision, native_position=native_position)


def _is_passed_object_argument(class_call: ClassMethodPolicy | None, native_position: int) -> bool:
    """Return the completed class-surface fact used to force polymorphic dispatch."""
    return bool(
        class_call is not None
        and class_call.kind is ClassMethodKind.INSTANCE
        and class_call.passed_object_position == native_position
    )


def _completed_argument_bridge_action(
    decision: OwnershipDecision,
    optional_mode: OptionalMode,
    native_slot: NativeCallSlotPolicy | None,
    callback: CallbackHandoffPolicy | None,
    derived: DerivedHandoffPolicy | None,
) -> tuple[BridgeDataAction, str | None]:
    """Select one already-supported bridge movement for a visible argument."""
    if callback is not None:
        return BridgeDataAction.DIRECT_TRANSFER, None
    action, reason = _argument_bridge_data_action(
        decision,
        optional_mode,
        native_slot.value_kind if native_slot is not None else None,
    )
    return _derived_argument_bridge_data_action(derived, action, reason)


def _argument_boundary_policy(
    function: models.SemanticFunction,
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    python_position: int,
    callback: CallbackHandoffPolicy | None,
) -> _ArgumentBoundaryPolicy:
    """Normalize callback inputs onto the ordinary argument-policy schema."""
    if callback is not None:
        return _ArgumentBoundaryPolicy(
            optional_mode=OptionalMode.REQUIRED,
            handoff_mode=ArgumentHandoffMode.VALUE,
            nullable=False,
            writable=False,
            descriptor_boundary=False,
            codegen_action=CodegenAction.CALL_LOCAL_INPUT,
            python_barrier_action=PythonBarrierAction.NONE,
            native_barrier_action=NativeBarrierAction.PASS_VALUE,
            storage_mode=StorageMode.STACK,
            boundary_storage_mode=StorageMode.STACK,
            projects_result=False,
            result_position=None,
        )
    return _ArgumentBoundaryPolicy(
        optional_mode=_optional_mode(argument, decision),
        handoff_mode=_argument_handoff_mode(decision),
        nullable=decision.nullable,
        # COPY_RETURN mutates a binding-owned replacement rather than the
        # immutable Python input whose payload is copied.
        writable=decision.mutates_native and decision.transfer is not TransferMode.COPY_RETURN,
        descriptor_boundary=decision.descriptor_boundary,
        codegen_action=decision.codegen_action,
        python_barrier_action=decision.python_barrier_action,
        native_barrier_action=decision.native_barrier_action,
        storage_mode=decision.storage_mode,
        boundary_storage_mode=decision.boundary_storage_mode or decision.storage_mode,
        projects_result=decision.projects_result,
        result_position=_argument_result_position(function, python_position),
    )


def _completed_argument_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    callback: CallbackHandoffPolicy | None,
    derived: DerivedHandoffPolicy | None,
    derived_call: DerivedCallPolicy | None,
    polymorphic: PolymorphicDispatchPolicy | None,
    bridge_data_action: BridgeDataAction,
    bridge_copy_reason: str | None,
    transformation_blockers: tuple[str, ...],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[str, ...]:
    """Collect blockers after all semantic selectors have been completed."""
    blockers = [
        *transformation_blockers,
        *_runtime_semantic_validation_blockers(argument.semantic_type, f"argument {argument.name!r}"),
    ]
    if callback is not None:
        blockers.extend(callback.blockers)
        blockers.extend(_callback_derived_type_blockers(callback, derived_types))
        if argument.optional:
            blockers.append(f"argument {argument.name!r} is an unsupported optional callback")
    else:
        blockers.extend(
            _argument_blockers(
                argument,
                decision,
                bridge_data_action,
                bridge_copy_reason,
                polymorphic,
            )
        )
    blockers.extend(_derived_argument_handoff_blockers(argument, derived, derived_types))
    requires_holder = bool(
        derived_call is not None
        and any(case.action is DerivedCallAction.ALLOCATABLE_HOLDER for case in derived_call.cases)
    )
    blockers.extend(
        _allocatable_holder_field_blockers(
            f"argument {argument.name!r}",
            derived,
            derived_types,
            required=requires_holder,
        )
    )
    return tuple(blockers)


def _callback_derived_type_blockers(
    callback: CallbackHandoffPolicy,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[str, ...]:
    """Require every callback-derived transfer to use a local exact wrapper type."""
    transfers = (
        *callback.arguments,
        *((callback.result.transfer,) if callback.result.transfer is not None else ()),
    )
    return tuple(
        f"callback transfer {transfer.owner_path!r} has no completed wrapper type definition "
        f"for {transfer.derived_type_identity!r}"
        for transfer in transfers
        if transfer.derived_type_identity is not None and transfer.derived_type_identity not in derived_types
    )


def _result_policies(
    function: models.SemanticFunction,
    owner_path: str,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[tuple[ResultPolicy, ...], tuple[str, ...]]:
    """Return every ordered binding result consumer for one function."""
    hidden_candidates = _hidden_result_policies(function, owner_path, derived_types)
    hidden_results = tuple(policy for policy, _blockers in hidden_candidates if policy is not None)
    hidden_blockers = tuple(reason for _policy, blockers in hidden_candidates for reason in blockers)
    if function.return_type is None:
        projected_arguments = _visible_projected_arguments(function)
        if hidden_results and not projected_arguments:
            return hidden_results, hidden_blockers
        if projected_arguments and not hidden_results:
            return (), hidden_blockers
        if not hidden_results and not projected_arguments:
            return (), hidden_blockers
        return hidden_results, hidden_blockers

    decision = function.metadata.get(models.RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA)
    if not isinstance(decision, OwnershipDecision):
        return (), (*hidden_blockers, "function result is missing completed ownership policy")
    direct_handle = _native_array_handle_wrapper_policy(
        function.return_type,
        function.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
        f"{owner_path}.return",
    )
    scalar_descriptor = _scalar_descriptor_result_policy(function.return_type, decision)
    blockers = list(_result_blockers(function.return_type, decision))
    if scalar_descriptor is not None and scalar_descriptor.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE:
        blockers.append(
            "direct allocatable scalar function results cannot preserve unallocated state; "
            "use an allocatable hidden output projection"
        )
    bridge_data_action, bridge_copy_reason = _result_bridge_data_action(function.return_type)
    if bridge_data_action is BridgeDataAction.BLOCKED and decision.kind is not ObjectKind.SCALAR:
        blockers.append("result has no completed bridge data action")
    derived = _derived_handoff_policy(
        function.return_type,
        decision,
        owner_path=f"{owner_path}.return",
        origin=DerivedObjectOrigin.WRAPPER_RESULT,
        derived_types=derived_types,
    )
    blockers.extend(_derived_type_definition_blockers("result", derived, derived_types))
    blockers.extend(
        _allocatable_holder_field_blockers(
            "result",
            derived,
            derived_types,
            required=bool(derived is not None and derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER),
        )
    )
    direct_result = ResultPolicy(
        owner_path=f"{owner_path}.return",
        semantic_type_name=function.return_type.name,
        rank=int(function.return_type.rank or 0),
        ownership=decision,
        codegen_action=decision.codegen_action,
        python_barrier_action=decision.python_barrier_action,
        native_barrier_action=decision.native_barrier_action,
        storage_mode=decision.storage_mode,
        boundary_storage_mode=decision.boundary_storage_mode or decision.storage_mode,
        bridge_data_action=bridge_data_action,
        bridge_copy_reason=bridge_copy_reason,
        character_length=_character_length(function.return_type),
        array=_array_handoff_policy(function.return_type),
        native_array_handle=direct_handle,
        scalar_descriptor=scalar_descriptor,
        derived=derived,
    )
    results = (direct_result, *hidden_results)
    return (
        results,
        (
            *blockers,
            *hidden_blockers,
        ),
    )


def _hidden_result_policies(
    function: models.SemanticFunction,
    owner_path: str,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[tuple[ResultPolicy | None, tuple[str, ...]], ...]:
    """Return completed policy candidates for hidden scalar output projections."""
    policies = []
    suppressed_outputs = _runtime_status_output_owner_paths(function)
    for argument in function.arguments:
        decision = _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)
        if decision is None or not (decision.projects_result and not decision.python_visible):
            continue
        if f"{owner_path}.{argument.name}" in suppressed_outputs:
            continue
        mapping = next(
            (
                item
                for item in function.projection
                if item.result_position is not None and item.python_name == argument.name
            ),
            None,
        )
        if mapping is None:
            policies.append((None, (f"hidden result {argument.name!r} has no completed return projection",)))
            continue
        blockers = _hidden_result_blockers(argument, decision, mapping)
        native_array_handle = _native_array_handle_wrapper_policy(
            argument.semantic_type,
            argument.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
            f"{owner_path}.{argument.name}",
        )
        scalar_descriptor = _scalar_descriptor_result_policy(
            argument.semantic_type,
            decision,
            descriptor_kind=mapping.value_kind,
        )
        bridge_data_action, bridge_copy_reason = _native_result_bridge_data_action(
            argument.semantic_type,
            descriptor_kind=mapping.value_kind,
        )
        if bridge_data_action is BridgeDataAction.BLOCKED and decision.kind is not ObjectKind.SCALAR:
            blockers = (*blockers, f"hidden result {argument.name!r} has no completed bridge data action")
        derived = _derived_handoff_policy(
            argument.semantic_type,
            decision,
            owner_path=f"{owner_path}.{argument.name}",
            origin=DerivedObjectOrigin.WRAPPER_RESULT,
            derived_types=derived_types,
        )
        blockers = (
            *blockers,
            *_derived_type_definition_blockers(
                f"hidden result {argument.name!r}",
                derived,
                derived_types,
            ),
            *_allocatable_holder_field_blockers(
                f"hidden result {argument.name!r}",
                derived,
                derived_types,
                required=bool(derived is not None and derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER),
            ),
        )
        policies.append(
            (
                ResultPolicy(
                    owner_path=f"{owner_path}.{argument.name}",
                    semantic_type_name=argument.semantic_type.name,
                    rank=int(argument.semantic_type.rank or 0),
                    ownership=decision,
                    codegen_action=decision.codegen_action,
                    python_barrier_action=decision.python_barrier_action,
                    native_barrier_action=decision.native_barrier_action,
                    storage_mode=decision.storage_mode,
                    boundary_storage_mode=decision.boundary_storage_mode or decision.storage_mode,
                    bridge_data_action=bridge_data_action,
                    bridge_copy_reason=bridge_copy_reason,
                    character_length=_character_length(argument.semantic_type),
                    array=_array_handoff_policy(argument.semantic_type),
                    source_kind="hidden_output",
                    native_name=mapping.native_name or argument.name,
                    native_position=mapping.native_position,
                    result_position=int(mapping.result_position),
                    native_array_handle=native_array_handle,
                    scalar_descriptor=scalar_descriptor,
                    derived=derived,
                ),
                tuple(blockers),
            )
        )
    return tuple(policies)


def _native_call_slot_policies(
    function: models.SemanticFunction,
    owner_path: str,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[dict[int, int], tuple[NativeCallSlotPolicy, ...], tuple[str, ...]]:
    if function.projection:
        return _projected_native_call_slot_policies(function, owner_path, derived_types)
    return _implicit_native_call_slot_policies(function, owner_path, derived_types)


def _projected_native_call_slot_policies(
    function: models.SemanticFunction,
    owner_path: str,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[dict[int, int], tuple[NativeCallSlotPolicy, ...], tuple[str, ...]]:
    """Complete projected slots through one small mapping-dispatch leaf."""
    slots: list[NativeCallSlotPolicy] = []
    blockers: list[str] = []
    positions: dict[int, int] = {}
    visible_arguments = _visible_native_call_arguments(function)
    for mapping in sorted(
        function.projection, key=lambda item: item.native_position if item.native_position is not None else -1
    ):
        slot, python_position, slot_blockers = _projected_native_call_slot_policy(
            function,
            mapping,
            owner_path,
            visible_arguments,
            derived_types,
        )
        blockers.extend(slot_blockers)
        if slot is None:
            continue
        slots.append(slot)
        if python_position is not None:
            _record_projected_argument_position(positions, python_position, slot, blockers)
    blockers.extend(_native_position_blockers(slot.native_position for slot in slots))
    return positions, tuple(slots), tuple(blockers)


def _visible_native_call_arguments(
    function: models.SemanticFunction,
) -> tuple[models.SemanticArgument, ...]:
    """Return arguments retained by completed Python visibility policy."""
    visible = []
    for argument in function.arguments:
        decision = _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)
        if decision is not None and decision.python_visible:
            visible.append(argument)
    return tuple(visible)


def _projected_native_call_slot_policy(
    function: models.SemanticFunction,
    mapping: models.ProjectionMapping,
    owner_path: str,
    visible_arguments: tuple[models.SemanticArgument, ...],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[NativeCallSlotPolicy | None, int | None, tuple[str, ...]]:
    """Dispatch one projection mapping to its literal, result, or argument leaf."""
    native_position = mapping.native_position
    if not isinstance(native_position, int):
        return None, None, ("native-call projection is missing a native position",)
    if mapping.value_kind == "literal":
        slot, blockers = _literal_native_call_slot_policy(mapping, owner_path, native_position)
        return slot, None, blockers
    python_position = mapping.python_position
    if mapping.result_position is not None and python_position is None:
        slot, blockers = _hidden_result_native_call_slot_policy(
            function,
            mapping,
            owner_path,
            native_position,
            derived_types,
        )
        return slot, None, blockers
    return _projected_argument_native_call_slot_policy(
        mapping,
        owner_path,
        native_position,
        python_position,
        visible_arguments,
        derived_types,
    )


def _projected_argument_native_call_slot_policy(
    mapping: models.ProjectionMapping,
    owner_path: str,
    native_position: int,
    python_position: int | None,
    visible_arguments: tuple[models.SemanticArgument, ...],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[NativeCallSlotPolicy | None, int | None, tuple[str, ...]]:
    """Complete one Python argument projection after checking its position."""
    if python_position is None:
        message = f"native-call slot {native_position} is not a first-lane Python argument projection"
        return None, None, (message,)
    if not 0 <= python_position < len(visible_arguments):
        message = f"native-call slot {native_position} references argument position {python_position}"
        return None, None, (message,)
    argument = visible_arguments[python_position]
    decision = _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)
    if decision is None:
        message = f"native-call slot {native_position} references argument without completed policy"
        return None, None, (message,)
    slot, blockers = _projected_argument_slot(
        mapping,
        argument,
        decision,
        owner_path,
        native_position,
        python_position,
        derived_types,
    )
    return slot, python_position, blockers


def _projected_argument_slot(
    mapping: models.ProjectionMapping,
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    owner_path: str,
    native_position: int,
    python_position: int,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[NativeCallSlotPolicy, tuple[str, ...]]:
    """Construct one completed native slot for a visible projected argument."""
    argument_path = f"{owner_path}.{argument.name}"
    value_kind = _native_argument_value_kind(argument, mapping.value_kind or "arg")
    callback = _callback_handoff_policy(argument)
    derived = _argument_derived_handoff(argument, decision, callback, argument_path, derived_types)
    bridge_data_action, bridge_copy_reason = _completed_projected_bridge_action(
        argument,
        decision,
        value_kind,
        callback,
        derived,
    )
    native_barrier_action, codegen_action = _native_slot_barrier_actions(decision, callback)
    blockers = []
    if value_kind not in {"addr", "allocatable", "arg", "pointer", "value"}:
        blockers.append(f"native-call slot {native_position} uses unsupported scalar value kind {value_kind!r}")
    if bridge_data_action is BridgeDataAction.BLOCKED:
        blockers.append(f"native-call slot {native_position} has no completed bridge data action")
    return (
        NativeCallSlotPolicy(
            owner_path=argument_path,
            native_position=native_position,
            source_kind="projection",
            python_position=python_position,
            python_name=mapping.python_name or argument.name,
            native_name=mapping.native_name or argument.name,
            value_kind=value_kind,
            native_barrier_action=native_barrier_action,
            codegen_action=codegen_action,
            bridge_data_action=bridge_data_action,
            bridge_copy_reason=bridge_copy_reason,
            object_kind=decision.kind,
            result_position=mapping.result_position,
            semantic_type_name=argument.semantic_type.name,
            character_length=_character_length(argument.semantic_type),
            array=_array_handoff_policy(argument.semantic_type),
            native_array_handle=_native_array_handle_wrapper_policy(
                argument.semantic_type,
                argument.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
                argument_path,
            ),
            derived=derived,
            callback=callback,
        ),
        tuple(blockers),
    )


def _completed_projected_bridge_action(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    value_kind: str,
    callback: CallbackHandoffPolicy | None,
    derived: DerivedHandoffPolicy | None,
) -> tuple[BridgeDataAction, str | None]:
    """Select bridge movement for one completed native-call projection."""
    if callback is not None:
        return BridgeDataAction.DIRECT_TRANSFER, None
    action, reason = _argument_bridge_data_action(
        decision,
        _optional_mode(argument, decision),
        value_kind,
    )
    return _derived_argument_bridge_data_action(derived, action, reason)


def _native_slot_barrier_actions(
    decision: OwnershipDecision,
    callback: CallbackHandoffPolicy | None,
) -> tuple[NativeBarrierAction, CodegenAction]:
    """Normalize callback projection actions onto the native-slot schema."""
    if callback is not None:
        return NativeBarrierAction.PASS_VALUE, CodegenAction.CALL_LOCAL_INPUT
    return decision.native_barrier_action, decision.codegen_action


def _record_projected_argument_position(
    positions: dict[int, int],
    python_position: int,
    slot: NativeCallSlotPolicy,
    blockers: list[str],
) -> None:
    """Record one argument-to-native mapping and diagnose duplicate slots."""
    if python_position in positions:
        blockers.append(f"argument {slot.python_name!r} appears in more than one native-call slot")
    positions[python_position] = slot.native_position


def _hidden_result_native_call_slot_policy(
    function: models.SemanticFunction,
    mapping: models.ProjectionMapping,
    owner_path: str,
    native_position: int,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[NativeCallSlotPolicy, tuple[str, ...]]:
    """Return one native slot for a hidden scalar `Return(...)` projection."""
    argument = next((item for item in function.arguments if item.name == mapping.python_name), None)
    if argument is None:
        return (
            NativeCallSlotPolicy(
                owner_path=f"{owner_path}.native_slot_{native_position}",
                native_position=native_position,
                source_kind="result",
                python_position=None,
                python_name=mapping.python_name,
                native_name=mapping.native_name or f"result_{native_position}",
                value_kind=mapping.value_kind,
                native_barrier_action=NativeBarrierAction.BLOCKED,
                codegen_action=CodegenAction.BLOCKED,
                bridge_data_action=BridgeDataAction.BLOCKED,
                bridge_copy_reason=None,
                object_kind=None,
                result_position=mapping.result_position,
            ),
            (f"native-call result slot {native_position} has no hidden argument {mapping.python_name!r}",),
        )
    decision = _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)
    if decision is None:
        return (
            NativeCallSlotPolicy(
                owner_path=f"{owner_path}.{argument.name}",
                native_position=native_position,
                source_kind="result",
                python_position=None,
                python_name=argument.name,
                native_name=mapping.native_name or argument.name,
                value_kind=mapping.value_kind,
                native_barrier_action=NativeBarrierAction.BLOCKED,
                codegen_action=CodegenAction.BLOCKED,
                bridge_data_action=BridgeDataAction.BLOCKED,
                bridge_copy_reason=None,
                object_kind=None,
                result_position=mapping.result_position,
                semantic_type_name=argument.semantic_type.name,
                character_length=_character_length(argument.semantic_type),
                array=_array_handoff_policy(argument.semantic_type),
                native_array_handle=_native_array_handle_wrapper_policy(
                    argument.semantic_type,
                    argument.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
                    f"{owner_path}.{argument.name}",
                ),
            ),
            (f"native-call result slot {native_position} references argument without completed policy",),
        )
    bridge_data_action, bridge_copy_reason = _native_result_bridge_data_action(
        argument.semantic_type,
        descriptor_kind=mapping.value_kind,
    )
    blockers = (
        (f"native-call result slot {native_position} has no completed bridge data action",)
        if bridge_data_action is BridgeDataAction.BLOCKED
        else ()
    )
    return (
        NativeCallSlotPolicy(
            owner_path=f"{owner_path}.{argument.name}",
            native_position=native_position,
            source_kind="result",
            python_position=None,
            python_name=argument.name,
            native_name=mapping.native_name or argument.name,
            value_kind=mapping.value_kind,
            native_barrier_action=decision.native_barrier_action,
            codegen_action=decision.codegen_action,
            bridge_data_action=bridge_data_action,
            bridge_copy_reason=bridge_copy_reason,
            object_kind=decision.kind,
            result_position=mapping.result_position,
            semantic_type_name=argument.semantic_type.name,
            character_length=_character_length(argument.semantic_type),
            array=_array_handoff_policy(argument.semantic_type),
            native_array_handle=_native_array_handle_wrapper_policy(
                argument.semantic_type,
                argument.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
                f"{owner_path}.{argument.name}",
            ),
            scalar_descriptor=_scalar_descriptor_result_policy(
                argument.semantic_type,
                decision,
                descriptor_kind=mapping.value_kind,
            ),
            derived=_derived_handoff_policy(
                argument.semantic_type,
                decision,
                owner_path=f"{owner_path}.{argument.name}",
                origin=DerivedObjectOrigin.WRAPPER_RESULT,
                derived_types=derived_types,
            ),
        ),
        blockers,
    )


def _literal_native_call_slot_policy(
    mapping: models.ProjectionMapping,
    owner_path: str,
    native_position: int,
) -> tuple[NativeCallSlotPolicy, tuple[str, ...]]:
    """Return a completed hidden literal slot and any first-lane blockers."""
    literal_type, literal_value, blockers = _literal_projection_value(mapping, native_position)
    return (
        NativeCallSlotPolicy(
            owner_path=f"{owner_path}.native_slot_{native_position}",
            native_position=native_position,
            source_kind="literal",
            python_position=None,
            python_name=None,
            native_name=mapping.native_name or f"literal_{native_position}",
            value_kind="literal",
            native_barrier_action=NativeBarrierAction.PASS_VALUE,
            codegen_action=CodegenAction.DIRECT_VALUE,
            bridge_data_action=BridgeDataAction.DIRECT_TRANSFER,
            bridge_copy_reason=None,
            object_kind=None,
            literal_type=literal_type,
            literal_value=literal_value,
            semantic_type_name=literal_type,
        ),
        tuple(blockers),
    )


def _literal_projection_value(
    mapping: models.ProjectionMapping,
    native_position: int,
) -> tuple[str | None, object, list[str]]:
    """Return literal type/value details for one projection mapping."""
    value = mapping.value
    if not isinstance(value, dict):
        return None, None, [f"native-call literal slot {native_position} is missing typed literal metadata"]
    literal_type = value.get("type")
    literal_value = value.get("value")
    blockers = []
    if not isinstance(literal_type, str):
        blockers.append(f"native-call literal slot {native_position} is missing a literal type")
    elif not _is_first_lane_literal_type(literal_type):
        blockers.append(
            f"native-call literal slot {native_position} uses unsupported first-lane literal type {literal_type!r}"
        )
    return literal_type if isinstance(literal_type, str) else None, literal_value, blockers


def _implicit_native_call_slot_policies(
    function: models.SemanticFunction,
    owner_path: str,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[dict[int, int], tuple[NativeCallSlotPolicy, ...], tuple[str, ...]]:
    slots: list[NativeCallSlotPolicy] = []
    positions: dict[int, int] = {}
    blockers: list[str] = []
    for position, argument in enumerate(function.arguments):
        decision = _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)
        if decision is None:
            blockers.append(f"implicit native-call slot {position} references argument without completed policy")
            continue
        value_kind = _native_argument_value_kind(argument, "arg")
        callback = argument.semantic_type.metadata.get(models.RESOLVED_CALLBACK_POLICY_METADATA)
        callback = callback if isinstance(callback, CallbackHandoffPolicy) else None
        derived = (
            None
            if callback is not None
            else _derived_handoff_policy(
                argument.semantic_type,
                decision,
                owner_path=f"{owner_path}.{argument.name}",
                origin=DerivedObjectOrigin.CALLER_WRAPPER,
                native_value=_native_by_value_argument(argument),
                derived_types=derived_types,
            )
        )
        if callback is not None:
            bridge_data_action, bridge_copy_reason = BridgeDataAction.DIRECT_TRANSFER, None
        else:
            bridge_data_action, bridge_copy_reason = _argument_bridge_data_action(
                decision,
                _optional_mode(argument, decision),
                value_kind,
            )
            bridge_data_action, bridge_copy_reason = _derived_argument_bridge_data_action(
                derived,
                bridge_data_action,
                bridge_copy_reason,
            )
        if bridge_data_action is BridgeDataAction.BLOCKED:
            blockers.append(f"implicit native-call slot {position} has no completed bridge data action")
        positions[position] = position
        slots.append(
            NativeCallSlotPolicy(
                owner_path=f"{owner_path}.{argument.name}",
                native_position=position,
                source_kind="implicit",
                python_position=position,
                python_name=argument.name,
                native_name=argument.name,
                value_kind=value_kind,
                native_barrier_action=(
                    NativeBarrierAction.PASS_VALUE if callback is not None else decision.native_barrier_action
                ),
                codegen_action=(CodegenAction.CALL_LOCAL_INPUT if callback is not None else decision.codegen_action),
                bridge_data_action=bridge_data_action,
                bridge_copy_reason=bridge_copy_reason,
                object_kind=decision.kind,
                semantic_type_name=argument.semantic_type.name,
                character_length=_character_length(argument.semantic_type),
                array=_array_handoff_policy(argument.semantic_type),
                native_array_handle=_native_array_handle_wrapper_policy(
                    argument.semantic_type,
                    argument.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
                    f"{owner_path}.{argument.name}",
                ),
                derived=derived,
                callback=callback,
            )
        )
    return positions, tuple(slots), tuple(blockers)


def _native_argument_value_kind(argument: models.SemanticArgument, default: str) -> str:
    """Project descriptor kind into the native slot before wrapper lowering."""
    return native_array_descriptor_kind(argument.semantic_type) or default


def _native_by_value_argument(argument: models.SemanticArgument) -> bool:
    """Return the completed per-call native aggregate value fact."""
    return bool(argument.metadata.get(models.NATIVE_BY_VALUE_METADATA))


def _derived_argument_bridge_data_action(
    derived: DerivedHandoffPolicy | None,
    action: BridgeDataAction,
    reason: str | None,
) -> tuple[BridgeDataAction, str | None]:
    """Select a typed value copy only from completed derived handoff policy."""
    if derived is None or derived.native_handoff is DerivedNativeHandoff.REFERENCE:
        return action, reason
    if derived.native_handoff is DerivedNativeHandoff.TYPED_VALUE:
        return BridgeDataAction.COPY_REPRESENTATION, DERIVED_VALUE_COPY_REASON
    return action, reason


def _derived_argument_handoff_blockers(
    argument: models.SemanticArgument,
    derived: DerivedHandoffPolicy | None,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[str, ...]:
    """Require the exact native type definition for a typed value call."""
    if derived is None:
        return ()
    return _derived_type_definition_blockers(f"argument {argument.name!r}", derived, derived_types)


def _derived_type_definition_blockers(
    label: str,
    derived: DerivedHandoffPolicy | None,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> tuple[str, ...]:
    """Require an exported local wrapper definition for every derived handoff."""
    if derived is None or derived.type_identity in derived_types:
        return ()
    return (f"{label} has no completed wrapper type definition for {derived.type_identity!r}",)


def _allocatable_holder_field_blockers(
    label: str,
    derived: DerivedHandoffPolicy | None,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
    *,
    required: bool,
) -> tuple[str, ...]:
    """Keep the first holder slice within its completed scalar-member policy."""
    if not required or derived is None:
        return ()
    type_policy = derived_types.get(derived.type_identity)
    if type_policy is None:
        return ()
    return tuple(
        f"{label} allocatable holder field {field.name!r} requires unsupported {field.access.value} access"
        for field in type_policy.fields
        if field.access is not DerivedFieldAccessMechanism.SCALAR_VALUE
    )


def _derived_handoff_policy(
    semantic_type: models.SemanticType,
    decision: OwnershipDecision,
    *,
    owner_path: str,
    origin: DerivedObjectOrigin,
    native_value: bool = False,
    derived_types: dict[tuple[str, str], DerivedTypePolicy] | None = None,
) -> DerivedHandoffPolicy | None:
    """Complete one scalar-derived origin and lifetime before planning."""
    if decision.kind is not ObjectKind.DERIVED_TYPE:
        return None
    if origin is DerivedObjectOrigin.CALLER_WRAPPER:
        retention = DerivedOwnerRetention.CALLER_WRAPPER
        release = DerivedRelease.NONE
    elif origin is DerivedObjectOrigin.BORROWED_FIELD:
        retention = DerivedOwnerRetention.PARENT_WRAPPER
        release = DerivedRelease.NONE
    elif origin in {DerivedObjectOrigin.WRAPPER_RESULT, DerivedObjectOrigin.CONSTANT_VALUE}:
        retention = DerivedOwnerRetention.WRAPPER_INSTANCE
        release = DerivedRelease.WRAPPER_DESTROY
    elif origin is DerivedObjectOrigin.NATIVE_MODULE:
        retention = DerivedOwnerRetention.NATIVE_MODULE
        release = DerivedRelease.NATIVE_OWNER
    else:
        raise ValueError(f"Unsupported derived object origin for {owner_path!r}: {origin!r}")
    requested_identity = _derived_type_identity(semantic_type, owner_path)
    type_policy = _resolve_derived_type_policy(
        semantic_type,
        requested_identity=requested_identity,
        derived_types=derived_types or {},
    )
    type_identity = type_policy.type_identity if type_policy is not None else requested_identity
    native_handoff = DerivedNativeHandoff.TYPED_VALUE if native_value else DerivedNativeHandoff.REFERENCE
    storage = _derived_object_storage(semantic_type, origin)
    pointer_target = bool(semantic_type.metadata.get("fortran_pointer"))
    return DerivedHandoffPolicy(
        type_name=semantic_type.name,
        type_identity=type_identity,
        native_type_name=type_identity[1],
        native_scope=type_identity[0],
        origin=origin,
        owner_retention=retention,
        release=release,
        target_owner_retention=(DerivedOwnerRetention.NATIVE_MODULE if pointer_target else DerivedOwnerRetention.NONE),
        target_release=(DerivedRelease.NATIVE_OWNER if pointer_target else DerivedRelease.NONE),
        nullable=decision.nullable,
        native_handoff=native_handoff,
        storage=storage,
    )


def _derived_object_storage(
    semantic_type: models.SemanticType,
    origin: DerivedObjectOrigin,
) -> DerivedObjectStorage:
    """Select persistent derived storage only from completed origin facts."""
    allocatable = bool(semantic_type.metadata.get("fortran_allocatable"))
    pointer = bool(semantic_type.metadata.get("fortran_pointer"))
    target = bool(semantic_type.metadata.get("fortran_target") or semantic_type.metadata.get("aliased"))
    if origin is DerivedObjectOrigin.WRAPPER_RESULT and allocatable:
        return DerivedObjectStorage.ALLOCATABLE_HOLDER
    if origin is DerivedObjectOrigin.WRAPPER_RESULT and pointer:
        return DerivedObjectStorage.POINTER_HOLDER
    if origin is DerivedObjectOrigin.NATIVE_MODULE and allocatable and target:
        return DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET
    if origin is DerivedObjectOrigin.NATIVE_MODULE and allocatable:
        return DerivedObjectStorage.MODULE_ALLOCATABLE
    if origin is DerivedObjectOrigin.NATIVE_MODULE and pointer:
        return DerivedObjectStorage.MODULE_POINTER
    if origin is DerivedObjectOrigin.NATIVE_MODULE and target:
        return DerivedObjectStorage.MODULE_TARGET
    if origin is DerivedObjectOrigin.NATIVE_MODULE:
        return DerivedObjectStorage.MODULE_PROXY
    return DerivedObjectStorage.DIRECT


def _derived_call_policy(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    *,
    native_position: int,
) -> DerivedCallPolicy | None:
    """Complete every scalar-derived actual/dummy matrix cell before lowering."""
    if decision.kind is not ObjectKind.DERIVED_TYPE:
        return None
    category = _derived_dummy_category(
        argument.semantic_type,
        native_value=_native_by_value_argument(argument),
    )
    cases = tuple(
        _derived_call_case(category, storage, projects_result=decision.projects_result)
        for storage in DerivedObjectStorage
    )
    writeback = {
        DerivedDummyCategory.VALUE: DerivedWriteback.NONE,
        DerivedDummyCategory.ALLOCATABLE: DerivedWriteback.ALLOCATION_STATE,
        DerivedDummyCategory.ALLOCATABLE_TARGET: DerivedWriteback.ALLOCATION_STATE,
        DerivedDummyCategory.POINTER: DerivedWriteback.POINTER_ASSOCIATION,
    }.get(
        category,
        DerivedWriteback.OBJECT_MUTATION if decision.mutates_native else DerivedWriteback.NONE,
    )
    return DerivedCallPolicy(
        dummy_category=category,
        cases=cases,
        writeback=writeback,
        status_role=f"{argument.name}:derived-call-status",
        origin_identity_role=f"{argument.name}:derived-origin-identity",
        acquisition_order=native_position,
        cleanup_order=-native_position,
    )


def _derived_dummy_category(
    semantic_type: models.SemanticType,
    *,
    native_value: bool = False,
) -> DerivedDummyCategory:
    """Return the declared native dummy category from semantic metadata."""
    if native_value:
        return DerivedDummyCategory.VALUE
    if semantic_type.metadata.get("fortran_allocatable"):
        if semantic_type.metadata.get("fortran_target") or semantic_type.metadata.get("aliased"):
            return DerivedDummyCategory.ALLOCATABLE_TARGET
        return DerivedDummyCategory.ALLOCATABLE
    if semantic_type.metadata.get("fortran_pointer"):
        return DerivedDummyCategory.POINTER
    if semantic_type.metadata.get("fortran_target") or semantic_type.metadata.get("aliased"):
        return DerivedDummyCategory.TARGET
    return DerivedDummyCategory.OBJECT


_DERIVED_ACCESS_ABI = {
    DerivedActualAccess.NONE: 0,
    DerivedActualAccess.DIRECT_ADDRESS: 1,
    DerivedActualAccess.SCOPED_ADDRESS: 2,
    DerivedActualAccess.ALLOCATABLE_HOLDER: 3,
    DerivedActualAccess.POINTER_HOLDER: 4,
    DerivedActualAccess.MODULE_ALLOCATABLE_TRANSACTION: 5,
    DerivedActualAccess.MODULE_POINTER_TRANSACTION: 6,
}


def _derived_call_case(
    category: DerivedDummyCategory,
    storage: DerivedObjectStorage,
    *,
    projects_result: bool,
) -> DerivedCallCasePolicy:
    """Return one exhaustive compatibility cell from the documented matrix."""
    if category in {DerivedDummyCategory.ALLOCATABLE, DerivedDummyCategory.ALLOCATABLE_TARGET}:
        return _derived_allocatable_dummy_case(storage)
    if category is DerivedDummyCategory.POINTER:
        return _derived_pointer_dummy_case(storage, projects_result=projects_result)
    return _derived_payload_dummy_case(category, storage)


def _derived_payload_dummy_case(
    category: DerivedDummyCategory,
    storage: DerivedObjectStorage,
) -> DerivedCallCasePolicy:
    action = DerivedCallAction.TYPED_VALUE_COPY if category is DerivedDummyCategory.VALUE else None
    table = {
        DerivedObjectStorage.DIRECT: (
            action or DerivedCallAction.DIRECT_REFERENCE,
            DerivedActualAccess.DIRECT_ADDRESS,
            False,
            DerivedTargetLifetime.OWNER,
        ),
        DerivedObjectStorage.MODULE_PROXY: (
            action or DerivedCallAction.SCOPED_REFERENCE,
            DerivedActualAccess.SCOPED_ADDRESS,
            False,
            DerivedTargetLifetime.CALL,
        ),
        DerivedObjectStorage.MODULE_TARGET: (
            action or DerivedCallAction.MODULE_ADDRESS,
            DerivedActualAccess.DIRECT_ADDRESS,
            False,
            DerivedTargetLifetime.MODULE,
        ),
        DerivedObjectStorage.ALLOCATABLE_HOLDER: (
            action or DerivedCallAction.HOLDER_REFERENCE,
            DerivedActualAccess.ALLOCATABLE_HOLDER,
            True,
            DerivedTargetLifetime.OWNER,
        ),
        DerivedObjectStorage.MODULE_ALLOCATABLE: (
            action or DerivedCallAction.SCOPED_REFERENCE,
            DerivedActualAccess.SCOPED_ADDRESS,
            True,
            DerivedTargetLifetime.CALL,
        ),
        DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET: (
            action or DerivedCallAction.MODULE_ADDRESS,
            DerivedActualAccess.DIRECT_ADDRESS,
            True,
            DerivedTargetLifetime.MODULE,
        ),
        DerivedObjectStorage.POINTER_HOLDER: (
            action or DerivedCallAction.POINTEE_REFERENCE,
            DerivedActualAccess.POINTER_HOLDER,
            True,
            DerivedTargetLifetime.OWNER,
        ),
        DerivedObjectStorage.MODULE_POINTER: (
            action or DerivedCallAction.POINTEE_REFERENCE,
            DerivedActualAccess.SCOPED_ADDRESS,
            True,
            DerivedTargetLifetime.MODULE,
        ),
    }
    selected_action, access, requires_present, lifetime = table[storage]
    return DerivedCallCasePolicy(
        storage,
        selected_action,
        access,
        _DERIVED_ACCESS_ABI[access],
        requires_present,
        lifetime,
    )


def _derived_allocatable_dummy_case(storage: DerivedObjectStorage) -> DerivedCallCasePolicy:
    if storage is DerivedObjectStorage.ALLOCATABLE_HOLDER:
        return DerivedCallCasePolicy(
            storage,
            DerivedCallAction.ALLOCATABLE_HOLDER,
            DerivedActualAccess.ALLOCATABLE_HOLDER,
            _DERIVED_ACCESS_ABI[DerivedActualAccess.ALLOCATABLE_HOLDER],
            False,
            DerivedTargetLifetime.OWNER,
        )
    if storage in {
        DerivedObjectStorage.MODULE_ALLOCATABLE,
        DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET,
    }:
        lifetime = (
            DerivedTargetLifetime.MODULE
            if storage is DerivedObjectStorage.MODULE_ALLOCATABLE_TARGET
            else DerivedTargetLifetime.CALL
        )
        access = DerivedActualAccess.MODULE_ALLOCATABLE_TRANSACTION
        return DerivedCallCasePolicy(
            storage,
            DerivedCallAction.MODULE_ALLOCATABLE_TRANSACTION,
            access,
            _DERIVED_ACCESS_ABI[access],
            False,
            lifetime,
        )
    return _derived_incompatible_case(storage, "allocatable-derived-actual-required", "requires allocatable storage")


def _derived_pointer_dummy_case(
    storage: DerivedObjectStorage,
    *,
    projects_result: bool,
) -> DerivedCallCasePolicy:
    if storage is DerivedObjectStorage.POINTER_HOLDER:
        access = DerivedActualAccess.POINTER_HOLDER
        return DerivedCallCasePolicy(
            storage,
            DerivedCallAction.POINTER_HOLDER,
            access,
            _DERIVED_ACCESS_ABI[access],
            False,
            DerivedTargetLifetime.OWNER,
        )
    if storage is DerivedObjectStorage.MODULE_POINTER:
        access = DerivedActualAccess.MODULE_POINTER_TRANSACTION
        return DerivedCallCasePolicy(
            storage,
            DerivedCallAction.MODULE_POINTER_TRANSACTION,
            access,
            _DERIVED_ACCESS_ABI[access],
            False,
            DerivedTargetLifetime.MODULE,
        )
    if projects_result:
        return _derived_incompatible_case(
            storage,
            "pointer-derived-actual-required",
            "projected pointer association writeback requires pointer storage",
        )
    payload = _derived_payload_dummy_case(DerivedDummyCategory.OBJECT, storage)
    return DerivedCallCasePolicy(
        storage,
        DerivedCallAction.POINTER_INPUT_ADAPTER,
        payload.access,
        payload.abi_code,
        payload.requires_present,
        payload.target_lifetime,
    )


def _derived_incompatible_case(
    storage: DerivedObjectStorage,
    kind: str,
    message: str,
) -> DerivedCallCasePolicy:
    return DerivedCallCasePolicy(
        storage,
        DerivedCallAction.INCOMPATIBLE,
        DerivedActualAccess.NONE,
        _DERIVED_ACCESS_ABI[DerivedActualAccess.NONE],
        False,
        DerivedTargetLifetime.NONE,
        kind,
        message,
    )


def _resolve_derived_type_policy(
    semantic_type: models.SemanticType,
    *,
    requested_identity: tuple[str, str],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> DerivedTypePolicy | None:
    """Resolve one reference to a completed canonical native type identity."""
    exact = derived_types.get(requested_identity)
    if exact is not None:
        return exact
    if semantic_type.metadata.get(models.EXTERNAL_TYPE_REF_METADATA) is not None:
        return None
    local_matches = tuple(policy for policy in derived_types.values() if policy.type_name == semantic_type.name)
    return local_matches[0] if len(local_matches) == 1 else None


def _derived_type_identity(
    semantic_type: models.SemanticType,
    owner_path: str,
) -> tuple[str, str]:
    """Return stable native scope/name identity for local or imported derived types."""
    completed = semantic_type.metadata.get(models.RESOLVED_DERIVED_TYPE_IDENTITY_METADATA)
    if (
        isinstance(completed, tuple)
        and len(completed) == 2
        and all(isinstance(item, str) and item for item in completed)
    ):
        return completed
    external = semantic_type.metadata.get(models.EXTERNAL_TYPE_REF_METADATA)
    if isinstance(external, dict):
        scope = external.get("origin_module")
        name = external.get("name")
        if isinstance(scope, str) and scope and isinstance(name, str) and name:
            return scope, name
    return owner_path.split(".", 1)[0], semantic_type.name


def _argument_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    bridge_data_action: BridgeDataAction,
    bridge_copy_reason: str | None,
    polymorphic: PolymorphicDispatchPolicy | None,
) -> tuple[str, ...]:
    """Return datatype-family blockers without reconstructing policy in a backend."""
    return (
        *_argument_shape_blockers(argument, decision, polymorphic),
        *_argument_boundary_blockers(argument, decision),
        *_argument_bridge_data_blockers(argument, bridge_data_action, bridge_copy_reason),
        *_argument_projection_blockers(argument, decision),
    )


def _argument_shape_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    polymorphic: PolymorphicDispatchPolicy | None,
) -> tuple[str, ...]:
    """Dispatch one argument to its scalar/string or array policy family."""
    if decision.kind is ObjectKind.DERIVED_TYPE:
        return _derived_argument_shape_blockers(argument, decision, polymorphic)
    if decision.kind is ObjectKind.NUMPY_ARRAY:
        return _array_argument_shape_blockers(argument, decision)
    return _scalar_or_string_argument_shape_blockers(argument, decision)


def _derived_argument_shape_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    polymorphic: PolymorphicDispatchPolicy | None,
) -> tuple[str, ...]:
    """Require one concrete scalar derived wrapper argument."""
    blockers = []
    if decision.is_blocked:
        blockers.append(
            f"argument {argument.name!r} has blocked ownership policy: {decision.blocker or decision.reason}"
        )
    if int(argument.semantic_type.rank or 0) != 0:
        blockers.append(f"argument {argument.name!r} is not a scalar derived object")
    if argument.semantic_type.metadata.get("fortran_polymorphic") and polymorphic is None:
        blockers.append(f"argument {argument.name!r} uses unsupported polymorphic derived storage")
    if not decision.python_visible:
        blockers.append(f"argument {argument.name!r} is not Python-visible")
    return tuple(blockers)


def _polymorphic_dispatch_policy(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    derived: DerivedHandoffPolicy | None,
    variants: dict[tuple[str, str], tuple[tuple[str, str], ...]],
    *,
    owner_path: str,
    force: bool,
) -> PolymorphicDispatchPolicy | None:
    """Complete the narrow scalar, required, input-only polymorphic lane."""
    if not force and not argument.semantic_type.metadata.get("fortran_polymorphic"):
        return None
    if (
        derived is None
        or int(argument.semantic_type.rank or 0) != 0
        or argument.optional
        or (decision.mutates_native and not force)
        or decision.projects_result
        or decision.descriptor_boundary
    ):
        return None
    accepted = variants.get(derived.type_identity, ())
    if not accepted:
        return None
    return PolymorphicDispatchPolicy(owner_path=owner_path, variants=accepted)


# Scalar and rank-zero string argument policy.
def _scalar_or_string_argument_shape_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Return ownership, type, and visibility blockers for one rank-zero argument."""
    blockers: list[str] = []
    if decision.is_blocked:
        blockers.append(
            f"argument {argument.name!r} has blocked ownership policy: {decision.blocker or decision.reason}"
        )
    string_value = _is_plan_string_value_type(argument.semantic_type)
    if not (_is_first_lane_scalar_type(argument.semantic_type) or string_value):
        blockers.append(f"argument {argument.name!r} is not a first-lane primitive scalar")
    if not decision.python_visible:
        blockers.append(f"argument {argument.name!r} is not Python-visible")
    expected_kind = ObjectKind.STRING if string_value else ObjectKind.SCALAR
    if decision.kind is not expected_kind:
        blockers.append(f"argument {argument.name!r} policy kind is {decision.kind.value}, not {expected_kind.value}")
    return tuple(blockers)


# Ordinary-array argument policy.
def _array_argument_shape_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Require one supported non-descriptor array boundary."""
    blockers: list[str] = []
    if _is_derived_value_array(argument.semantic_type):
        blockers.append(f"argument {argument.name!r} is an unsupported array of derived values")
    elif decision.is_blocked:
        blockers.append(
            f"argument {argument.name!r} has blocked ownership policy: {decision.blocker or decision.reason}"
        )
    descriptor_kind = native_array_descriptor_kind(argument.semantic_type)
    if _is_derived_value_array(argument.semantic_type):
        pass
    elif descriptor_kind is not None:
        completed_handle = argument.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA)
        if not isinstance(completed_handle, CompletedNativeArrayHandlePolicy):
            blockers.append(f"argument {argument.name!r} is missing completed native array handle policy")
        elif completed_handle.is_blocked:
            blockers.append(
                f"argument {argument.name!r} has blocked native array handle policy: {completed_handle.blocker}"
            )
    elif decision.python_barrier_action is PythonBarrierAction.RAW_ADDRESS:
        if not _is_phase6_raw_array_address_type(argument.semantic_type):
            blockers.append(f"argument {argument.name!r} is outside raw array address support")
    elif not _is_phase6_ordinary_array_type(argument.semantic_type):
        blockers.append(f"argument {argument.name!r} is outside ordinary array buffer support")
    if not decision.python_visible:
        blockers.append(f"argument {argument.name!r} is not Python-visible")
    if decision.kind is not ObjectKind.NUMPY_ARRAY:
        blockers.append(f"argument {argument.name!r} policy kind is {decision.kind.value}, not numpy_array")
    return tuple(blockers)


def _argument_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Return Python/native boundary-action blockers for one argument."""
    if decision.kind is ObjectKind.STRING:
        return _string_boundary_blockers(argument, decision)
    if decision.kind is ObjectKind.NUMPY_ARRAY:
        return _array_boundary_blockers(argument, decision)
    if decision.kind is ObjectKind.DERIVED_TYPE:
        return _derived_boundary_blockers(argument, decision)
    return _scalar_boundary_blockers(argument, decision)


def _derived_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Validate wrapper-instance to opaque-address derived handoff."""
    blockers = []
    if decision.python_barrier_action is not PythonBarrierAction.WRAPPER_INSTANCE:
        blockers.append(
            f"argument {argument.name!r} has unsupported derived Python action {decision.python_barrier_action.value}"
        )
    if decision.native_barrier_action is not NativeBarrierAction.PASS_WRAPPER_ADDRESS:
        blockers.append(
            f"argument {argument.name!r} has unsupported derived native action {decision.native_barrier_action.value}"
        )
    if decision.codegen_action not in {
        CodegenAction.CALL_LOCAL_INPUT,
        CodegenAction.IN_PLACE_ARGUMENT,
        CodegenAction.IDENTITY_OUTPUT,
    }:
        blockers.append(
            f"argument {argument.name!r} has unsupported derived codegen action {decision.codegen_action.value}"
        )
    return tuple(blockers)


def _scalar_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Validate one completed scalar value, storage, or address boundary."""
    blockers: list[str] = []
    if decision.python_barrier_action not in {
        PythonBarrierAction.SCALAR_VALUE,
        PythonBarrierAction.SCALAR_STORAGE,
        PythonBarrierAction.RAW_ADDRESS,
    }:
        blockers.append(
            f"argument {argument.name!r} has unsupported scalar Python action {decision.python_barrier_action.value}"
        )
    if decision.native_barrier_action not in {
        NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
        NativeBarrierAction.PASS_RAW_ADDRESS,
        NativeBarrierAction.PASS_STORAGE_ADDRESS,
        NativeBarrierAction.PASS_VALUE,
    }:
        blockers.append(
            f"argument {argument.name!r} native action is {decision.native_barrier_action.value}, "
            "not a supported scalar handoff"
        )
    if (
        decision.python_barrier_action is PythonBarrierAction.SCALAR_STORAGE
        and decision.native_barrier_action is not NativeBarrierAction.PASS_STORAGE_ADDRESS
    ):
        blockers.append(f"argument {argument.name!r} scalar storage does not use its storage address")
    if (
        decision.python_barrier_action is PythonBarrierAction.RAW_ADDRESS
        and decision.native_barrier_action is not NativeBarrierAction.PASS_RAW_ADDRESS
    ):
        blockers.append(f"argument {argument.name!r} raw address is not forwarded as a raw address")
    if argument.optional and decision.python_barrier_action is PythonBarrierAction.RAW_ADDRESS:
        blockers.append(f"argument {argument.name!r} optional raw-address boundaries are not supported")
    return tuple(blockers)


# Ordinary-array boundary policy.
def _array_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Dispatch one completed array boundary without backend inference."""
    action = decision.python_barrier_action
    if action is PythonBarrierAction.SCALAR_STORAGE:
        return _scalar_storage_array_boundary_blockers(argument, decision)
    if action is PythonBarrierAction.ARRAY_STORAGE:
        return _array_storage_boundary_blockers(argument, decision)
    if action is PythonBarrierAction.RAW_ADDRESS:
        return _raw_array_address_boundary_blockers(argument, decision)
    if action is PythonBarrierAction.WRAPPER_INSTANCE:
        return _native_array_handle_boundary_blockers(argument, decision)
    return (f"argument {argument.name!r} has unsupported array Python action {action.value}",)


def _scalar_storage_array_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Require one rank-zero NumPy storage handoff to a scalar native dummy."""
    blockers = []
    if decision.owner is not OwnershipOwner.CALLER:
        blockers.append(f"argument {argument.name!r} scalar-storage owner is {decision.owner.value}, not caller")
    expected_transfer = TransferMode.IN_PLACE if decision.mutates_native else TransferMode.CALL_LOCAL
    if decision.transfer is not expected_transfer:
        blockers.append(
            f"argument {argument.name!r} scalar-storage transfer is "
            f"{decision.transfer.value}, not {expected_transfer.value}"
        )
    expected_destruction = DestructionPolicy.CALLER if decision.mutates_native else DestructionPolicy.NONE
    if decision.destruction is not expected_destruction:
        blockers.append(
            f"argument {argument.name!r} scalar-storage destruction is "
            f"{decision.destruction.value}, not {expected_destruction.value}"
        )
    if decision.storage_mode is not StorageMode.STACK:
        blockers.append(
            f"argument {argument.name!r} scalar-storage storage is {decision.storage_mode.value}, not stack"
        )
    if (decision.boundary_storage_mode or decision.storage_mode) is not StorageMode.STACK:
        blockers.append(f"argument {argument.name!r} scalar-storage boundary storage is not stack")
    if decision.native_barrier_action is not NativeBarrierAction.PASS_STORAGE_ADDRESS:
        blockers.append(f"argument {argument.name!r} scalar storage does not use its storage address")
    if decision.codegen_action not in {
        CodegenAction.CALL_LOCAL_INPUT,
        CodegenAction.IN_PLACE_ARGUMENT,
        CodegenAction.IDENTITY_OUTPUT,
    }:
        blockers.append(
            f"argument {argument.name!r} scalar-storage action is "
            f"{decision.codegen_action.value}, not a storage-address action"
        )
    if decision.descriptor_boundary:
        blockers.append(f"argument {argument.name!r} scalar storage must be non-descriptor storage")
    array_policy = _array_handoff_policy(argument.semantic_type)
    if not _is_scalar_storage_array_policy(array_policy):
        blockers.append(f"argument {argument.name!r} is not rank-zero scalar storage")
    return tuple(blockers)


def _array_storage_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Require one caller-owned ordinary NumPy buffer handoff."""
    if decision.transfer is TransferMode.COPY_RETURN:
        return _array_replacement_boundary_blockers(argument, decision)
    blockers = []
    if decision.owner is not OwnershipOwner.CALLER:
        blockers.append(f"argument {argument.name!r} array owner is {decision.owner.value}, not caller")
    expected_transfer = TransferMode.IN_PLACE if decision.mutates_native else TransferMode.CALL_LOCAL
    if decision.transfer is not expected_transfer:
        blockers.append(
            f"argument {argument.name!r} array transfer is {decision.transfer.value}, not {expected_transfer.value}"
        )
    expected_destruction = DestructionPolicy.CALLER if decision.mutates_native else DestructionPolicy.NONE
    if decision.destruction is not expected_destruction:
        blockers.append(
            f"argument {argument.name!r} array destruction is {decision.destruction.value}, "
            f"not {expected_destruction.value}"
        )
    if decision.storage_mode is not StorageMode.STACK:
        blockers.append(f"argument {argument.name!r} array storage is {decision.storage_mode.value}, not stack")
    if (decision.boundary_storage_mode or decision.storage_mode) is not StorageMode.STACK:
        blockers.append(f"argument {argument.name!r} array boundary storage is not stack")
    if decision.python_barrier_action is not PythonBarrierAction.ARRAY_STORAGE:
        blockers.append(
            f"argument {argument.name!r} array Python action is "
            f"{decision.python_barrier_action.value}, not array_storage"
        )
    if decision.native_barrier_action is not NativeBarrierAction.PASS_ARRAY_BUFFER:
        blockers.append(
            f"argument {argument.name!r} array native action is "
            f"{decision.native_barrier_action.value}, not pass_array_buffer"
        )
    expected_actions = {
        CodegenAction.CALL_LOCAL_INPUT,
        CodegenAction.IN_PLACE_ARGUMENT,
        CodegenAction.IDENTITY_OUTPUT,
    }
    if decision.codegen_action not in expected_actions:
        blockers.append(
            f"argument {argument.name!r} array action is {decision.codegen_action.value}, not a borrowed buffer action"
        )
    if decision.descriptor_boundary:
        blockers.append(f"argument {argument.name!r} ordinary array must be non-descriptor storage")
    if decision.nullable and not argument.optional:
        blockers.append(f"argument {argument.name!r} ordinary array is nullable without optional presence")
    array_policy = _array_handoff_policy(argument.semantic_type)
    if argument.optional and array_policy is not None and array_policy.rank is None:
        blockers.append(f"argument {argument.name!r} optional assumed-rank combination is not supported")
    return tuple(blockers)


def _array_replacement_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Require an immutable input copied into one Python-owned replacement."""
    blockers = []
    if decision.owner is not OwnershipOwner.PYTHON:
        blockers.append(f"argument {argument.name!r} replacement owner is {decision.owner.value}, not python")
    if decision.destruction is not DestructionPolicy.PYTHON_REFCOUNT:
        blockers.append(
            f"argument {argument.name!r} replacement destruction is {decision.destruction.value}, not python_refcount"
        )
    if decision.codegen_action is not CodegenAction.COPY_IN_OUT:
        blockers.append(
            f"argument {argument.name!r} replacement action is {decision.codegen_action.value}, not copy_in_out"
        )
    if decision.storage_mode is not StorageMode.STACK:
        blockers.append(f"argument {argument.name!r} replacement storage is {decision.storage_mode.value}, not stack")
    if (decision.boundary_storage_mode or decision.storage_mode) is not StorageMode.STACK:
        blockers.append(f"argument {argument.name!r} replacement boundary storage is not stack")
    if decision.python_barrier_action is not PythonBarrierAction.ARRAY_STORAGE:
        blockers.append(f"argument {argument.name!r} replacement is not sourced from array storage")
    if decision.native_barrier_action is not NativeBarrierAction.PASS_ARRAY_BUFFER:
        blockers.append(f"argument {argument.name!r} replacement does not pass an array buffer")
    if not decision.projects_result:
        blockers.append(f"argument {argument.name!r} replacement does not project a Python result")
    if argument.optional or decision.nullable or decision.descriptor_boundary:
        blockers.append(f"argument {argument.name!r} replacement requires nonoptional ordinary array storage")
    return tuple(blockers)


def _raw_array_address_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Require one caller-owned raw array address with completed pointee shape."""
    blockers = []
    if decision.owner is not OwnershipOwner.CALLER:
        blockers.append(f"argument {argument.name!r} raw array owner is {decision.owner.value}, not caller")
    expected_transfer = TransferMode.IN_PLACE if decision.mutates_native else TransferMode.CALL_LOCAL
    if decision.transfer is not expected_transfer:
        blockers.append(
            f"argument {argument.name!r} raw array transfer is {decision.transfer.value}, not {expected_transfer.value}"
        )
    expected_destruction = DestructionPolicy.CALLER if decision.mutates_native else DestructionPolicy.NONE
    if decision.destruction is not expected_destruction:
        blockers.append(
            f"argument {argument.name!r} raw array destruction is {decision.destruction.value}, "
            f"not {expected_destruction.value}"
        )
    if decision.storage_mode is not StorageMode.STACK:
        blockers.append(f"argument {argument.name!r} raw array storage is {decision.storage_mode.value}, not stack")
    if (decision.boundary_storage_mode or decision.storage_mode) is not StorageMode.STACK:
        blockers.append(f"argument {argument.name!r} raw array boundary storage is not stack")
    if decision.native_barrier_action is not NativeBarrierAction.PASS_RAW_ADDRESS:
        blockers.append(
            f"argument {argument.name!r} raw array native action is "
            f"{decision.native_barrier_action.value}, not pass_raw_address"
        )
    if decision.codegen_action not in {CodegenAction.CALL_LOCAL_INPUT, CodegenAction.IN_PLACE_ARGUMENT}:
        blockers.append(
            f"argument {argument.name!r} raw array action is {decision.codegen_action.value}, "
            "not a non-owning address action"
        )
    if argument.optional:
        blockers.append(f"argument {argument.name!r} optional raw array addresses are not supported")
    if decision.nullable or decision.descriptor_boundary:
        blockers.append(f"argument {argument.name!r} raw array address must be non-descriptor storage")
    if decision.projects_result:
        blockers.append(f"argument {argument.name!r} raw array address cannot project a Python result")
    return tuple(blockers)


def _native_array_handle_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Require one caller handle transported through its native descriptor."""
    blockers = []
    if native_array_descriptor_kind(argument.semantic_type) not in {"allocatable", "pointer"}:
        blockers.append(f"argument {argument.name!r} has no native array descriptor kind")
    if decision.owner is not OwnershipOwner.CALLER:
        blockers.append(f"argument {argument.name!r} descriptor owner is {decision.owner.value}, not caller")
    if decision.transfer not in {TransferMode.CALL_LOCAL, TransferMode.IN_PLACE}:
        blockers.append(f"argument {argument.name!r} descriptor transfer is {decision.transfer.value}")
    if decision.destruction not in {DestructionPolicy.NONE, DestructionPolicy.CALLER}:
        blockers.append(f"argument {argument.name!r} descriptor destruction is {decision.destruction.value}")
    if decision.native_barrier_action is not NativeBarrierAction.PASS_NATIVE_DESCRIPTOR:
        blockers.append(f"argument {argument.name!r} does not pass a native descriptor")
    if decision.codegen_action not in {CodegenAction.CALL_LOCAL_INPUT, CodegenAction.IN_PLACE_ARGUMENT}:
        blockers.append(f"argument {argument.name!r} has unsupported descriptor action {decision.codegen_action.value}")
    if not decision.descriptor_boundary or not decision.nullable:
        blockers.append(f"argument {argument.name!r} descriptor boundary is incomplete")
    return tuple(blockers)


# String argument policy.
def _string_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Dispatch one completed string boundary without backend inference."""
    action = decision.python_barrier_action
    if action is PythonBarrierAction.STRING_VALUE:
        return _string_value_boundary_blockers(argument, decision)
    if action is PythonBarrierAction.STRING_STORAGE:
        return _string_storage_boundary_blockers(argument, decision)
    if action is PythonBarrierAction.RAW_ADDRESS:
        return _raw_string_address_boundary_blockers(argument, decision)
    return (f"argument {argument.name!r} has unsupported string Python action {action.value}",)


def _string_value_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Return completed string-value input or replacement blockers."""
    blockers = []
    if decision.python_barrier_action is not PythonBarrierAction.STRING_VALUE:
        blockers.append(
            f"argument {argument.name!r} has unsupported string Python action {decision.python_barrier_action.value}"
        )
    if decision.native_barrier_action is not NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS:
        blockers.append(
            f"argument {argument.name!r} native action is {decision.native_barrier_action.value}, "
            "not a string call-local address handoff"
        )
    if decision.codegen_action not in {CodegenAction.CALL_LOCAL_INPUT, CodegenAction.COPY_IN_OUT}:
        blockers.append(
            f"argument {argument.name!r} string action is {decision.codegen_action.value}, "
            "not a call-local input or copy-in/out replacement"
        )
    if decision.codegen_action is CodegenAction.CALL_LOCAL_INPUT and decision.projects_result:
        blockers.append(f"argument {argument.name!r} call-local string input unexpectedly projects a result")
    if decision.codegen_action is CodegenAction.COPY_IN_OUT:
        blockers.extend(_string_replacement_blockers(argument, decision))
    return tuple(blockers)


def _string_storage_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Require caller-owned fixed mutable NumPy bytes storage."""
    blockers = list(
        _string_address_ownership_blockers(
            argument,
            decision,
            expected_storage=StorageMode.ALIAS,
            label="string storage",
        )
    )
    if decision.native_barrier_action is not NativeBarrierAction.PASS_STORAGE_ADDRESS:
        blockers.append(
            f"argument {argument.name!r} string storage native action is "
            f"{decision.native_barrier_action.value}, not pass_storage_address"
        )
    return tuple(blockers)


def _raw_string_address_boundary_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Require a caller-owned unsafe fixed string address contract."""
    blockers = list(
        _string_address_ownership_blockers(
            argument,
            decision,
            expected_storage=StorageMode.STACK,
            label="raw string address",
        )
    )
    if decision.native_barrier_action is not NativeBarrierAction.PASS_RAW_ADDRESS:
        blockers.append(
            f"argument {argument.name!r} raw string native action is "
            f"{decision.native_barrier_action.value}, not pass_raw_address"
        )
    return tuple(blockers)


def _string_address_ownership_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    *,
    expected_storage: StorageMode,
    label: str,
) -> tuple[str, ...]:
    """Validate ownership shared by fixed storage and raw-address forms."""
    blockers = []
    if _character_length(argument.semantic_type) is None:
        blockers.append(f"argument {argument.name!r} {label} requires a fixed positive character length")
    if decision.owner is not OwnershipOwner.CALLER:
        blockers.append(f"argument {argument.name!r} {label} owner is {decision.owner.value}, not caller")
    if decision.transfer is not TransferMode.IN_PLACE:
        blockers.append(f"argument {argument.name!r} {label} transfer is {decision.transfer.value}, not in_place")
    if decision.destruction is not DestructionPolicy.CALLER:
        blockers.append(f"argument {argument.name!r} {label} destruction is {decision.destruction.value}, not caller")
    if decision.storage_mode is not expected_storage:
        blockers.append(
            f"argument {argument.name!r} {label} storage is {decision.storage_mode.value}, not {expected_storage.value}"
        )
    if (decision.boundary_storage_mode or decision.storage_mode) is not expected_storage:
        blockers.append(f"argument {argument.name!r} {label} boundary storage is not {expected_storage.value}")
    if decision.codegen_action is not CodegenAction.IN_PLACE_ARGUMENT:
        blockers.append(
            f"argument {argument.name!r} {label} action is {decision.codegen_action.value}, not in_place_argument"
        )
    if not decision.mutates_native:
        blockers.append(f"argument {argument.name!r} {label} does not record native mutation")
    if decision.projects_result:
        blockers.append(f"argument {argument.name!r} {label} unexpectedly projects a result")
    if decision.nullable or argument.optional:
        blockers.append(f"argument {argument.name!r} optional {label} is unsupported")
    return tuple(blockers)


def _string_replacement_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Require completed Phase 5C replacement ownership and projection."""
    blockers = []
    if decision.owner is not OwnershipOwner.PYTHON:
        blockers.append(f"argument {argument.name!r} replacement owner is {decision.owner.value}, not python")
    if decision.transfer is not TransferMode.COPY_RETURN:
        blockers.append(
            f"argument {argument.name!r} replacement transfer is {decision.transfer.value}, not copy_return"
        )
    if decision.destruction is not DestructionPolicy.PYTHON_REFCOUNT:
        blockers.append(
            f"argument {argument.name!r} replacement destruction is {decision.destruction.value}, not python_refcount"
        )
    if decision.storage_mode is not StorageMode.STACK:
        blockers.append(f"argument {argument.name!r} replacement storage is {decision.storage_mode.value}, not stack")
    if (decision.boundary_storage_mode or decision.storage_mode) is not StorageMode.STACK:
        blockers.append(f"argument {argument.name!r} replacement boundary storage is not stack")
    if not decision.mutates_native:
        blockers.append(f"argument {argument.name!r} replacement does not record native mutation")
    if not decision.projects_result:
        blockers.append(f"argument {argument.name!r} replacement does not project a Python result")
    if decision.nullable and not argument.optional:
        blockers.append(f"argument {argument.name!r} replacement is nullable without optional presence")
    return tuple(blockers)


def _argument_bridge_data_blockers(
    argument: models.SemanticArgument,
    bridge_data_action: BridgeDataAction,
    bridge_copy_reason: str | None,
) -> tuple[str, ...]:
    """Return incomplete or contradictory bridge data-action blockers."""
    blockers: list[str] = []
    if bridge_data_action is BridgeDataAction.BLOCKED:
        blockers.append(f"argument {argument.name!r} has no completed bridge data action")
    if bridge_data_action is BridgeDataAction.COPY_REPRESENTATION and not bridge_copy_reason:
        blockers.append(f"argument {argument.name!r} bridge representation copy has no completed reason")
    if bridge_data_action is not BridgeDataAction.COPY_REPRESENTATION and bridge_copy_reason is not None:
        blockers.append(f"argument {argument.name!r} copy-free bridge action carries a copy reason")
    return tuple(blockers)


def _argument_projection_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Return projected-result action blockers for one argument."""
    if decision.projects_result and decision.codegen_action not in {
        CodegenAction.COPY_IN_OUT,
        CodegenAction.IN_PLACE_ARGUMENT,
    }:
        return (
            f"argument {argument.name!r} projects a result with unsupported action {decision.codegen_action.value}",
        )
    return ()


def _result_blockers(semantic_type: models.SemanticType, decision: OwnershipDecision) -> tuple[str, ...]:
    """Dispatch one result to its completed datatype and descriptor family."""
    validation_blockers = _runtime_semantic_validation_blockers(semantic_type, "result")
    if _is_derived_value_array(semantic_type):
        family_blockers = ("result is an unsupported array of derived values",)
        return (*validation_blockers, *family_blockers)
    if decision.kind is ObjectKind.DERIVED_TYPE:
        family_blockers = _derived_result_blockers(semantic_type, decision, "result")
    elif _is_scalar_descriptor_result_type(semantic_type):
        family_blockers = _scalar_descriptor_result_blockers(semantic_type, decision, "result")
    else:
        descriptor_kind = native_array_descriptor_kind(semantic_type)
        if descriptor_kind == "pointer":
            family_blockers = (
                "pointer handle results need stable owner storage and target lifetime policy before wrapping",
            )
        elif descriptor_kind is not None:
            family_blockers = _native_array_handle_result_blockers(decision, "result")
        elif _is_phase6_ordinary_array_type(semantic_type):
            family_blockers = _ordinary_array_result_blockers(semantic_type, decision, "result")
        elif _is_fixed_plan_string_result_type(semantic_type):
            family_blockers = _fixed_string_result_blockers(decision)
        else:
            family_blockers = _scalar_result_blockers(semantic_type, decision)
    return (*validation_blockers, *family_blockers)


def _runtime_semantic_validation_blockers(
    semantic_type: models.SemanticType,
    label: str,
) -> tuple[str, ...]:
    """Complete unsupported generic validators and coercions before planning."""
    constraints = tuple(
        dict.fromkeys(constraint.name for constraint in semantic_type.constraints if constraint.name != "Constant")
    )
    coercions = tuple(dict.fromkeys(coercion.source_type for coercion in semantic_type.coercions))
    blockers = []
    if constraints:
        blockers.append(f"{label} has no runtime validators for semantic constraints {constraints}")
    if coercions:
        blockers.append(f"{label} has no wrapper conversion actions for semantic coercions {coercions}")
    return tuple(blockers)


def _derived_result_blockers(
    semantic_type: models.SemanticType,
    decision: OwnershipDecision,
    label: str,
) -> tuple[str, ...]:
    """Require persistent wrapper-owned scalar derived result storage."""
    blockers = []
    if decision.is_blocked:
        blockers.append(f"{label} has blocked ownership policy: {decision.blocker or decision.reason}")
    if int(semantic_type.rank or 0) != 0:
        blockers.append(f"{label} is not a scalar derived object")
    if semantic_type.metadata.get("fortran_polymorphic"):
        blockers.append(f"{label} uses unsupported polymorphic derived storage")
    expected = (
        ("owner", decision.owner, OwnershipOwner.WRAPPER),
        ("transfer", decision.transfer, TransferMode.WRAPPER_INSTANCE),
        ("destruction", decision.destruction, DestructionPolicy.WRAPPER_DEALLOC),
        ("storage", decision.storage_mode, StorageMode.HEAP),
        ("codegen", decision.codegen_action, CodegenAction.WRAPPER_INSTANCE),
    )
    blockers.extend(
        f"{label} derived {name} is {actual.value}, not {required.value}"
        for name, actual, required in expected
        if actual is not required
    )
    return tuple(blockers)


# Scalar result policy.
def _scalar_result_blockers(
    semantic_type: models.SemanticType,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Return completed primitive scalar result blockers."""
    blockers: list[str] = []
    if decision.is_blocked:
        blockers.append(f"result has blocked ownership policy: {decision.blocker or decision.reason}")
    if not _is_first_lane_scalar_type(semantic_type):
        blockers.append("result is not a first-lane primitive scalar")
    if decision.kind is not ObjectKind.SCALAR:
        blockers.append(f"result policy kind is {decision.kind.value}, not scalar")
    if decision.codegen_action is not CodegenAction.DIRECT_VALUE:
        blockers.append(f"result codegen action is {decision.codegen_action.value}, not direct_value")
    if decision.python_barrier_action is not PythonBarrierAction.NONE:
        blockers.append(f"result Python action is {decision.python_barrier_action.value}, not none")
    if decision.native_barrier_action is not NativeBarrierAction.NONE:
        blockers.append(f"result native action is {decision.native_barrier_action.value}, not none")
    return tuple(blockers)


def _hidden_result_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    mapping: models.ProjectionMapping,
) -> tuple[str, ...]:
    """Return blockers for one hidden result projection."""
    validation_blockers = _runtime_semantic_validation_blockers(
        argument.semantic_type,
        f"hidden result {argument.name!r}",
    )
    if decision.kind is ObjectKind.DERIVED_TYPE:
        family_blockers = _derived_hidden_result_blockers(argument, decision, mapping)
    elif _is_scalar_descriptor_result_type(argument.semantic_type, descriptor_kind=mapping.value_kind):
        family_blockers = _scalar_descriptor_result_blockers(
            argument.semantic_type,
            decision,
            f"hidden result {argument.name!r}",
            mapping,
        )
    else:
        descriptor_kind = native_array_descriptor_kind(argument.semantic_type)
        if descriptor_kind == "pointer":
            family_blockers = (
                "pointer handle results need stable owner storage and target lifetime policy before wrapping",
            )
        elif descriptor_kind is not None:
            family_blockers = _native_array_handle_result_blockers(decision, f"hidden result {argument.name!r}")
        elif _is_phase6_ordinary_array_type(argument.semantic_type):
            family_blockers = _ordinary_array_hidden_result_blockers(argument, decision, mapping)
        elif _is_fixed_plan_string_result_type(argument.semantic_type):
            family_blockers = _fixed_string_hidden_result_blockers(argument, decision, mapping)
        else:
            family_blockers = _scalar_hidden_result_blockers(argument, decision, mapping)
    return (*validation_blockers, *family_blockers)


def _derived_hidden_result_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    mapping: models.ProjectionMapping,
) -> tuple[str, ...]:
    """Validate one persistent hidden derived result projection."""
    label = f"hidden result {argument.name!r}"
    blockers = list(_derived_result_blockers(argument.semantic_type, decision, label))
    blockers.extend(_hidden_result_projection_blockers(label, decision, mapping))
    return tuple(blockers)


def _scalar_hidden_result_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    mapping: models.ProjectionMapping,
) -> tuple[str, ...]:
    """Validate one primitive scalar hidden result projection."""
    label = f"hidden result {argument.name!r}"
    blockers: list[str] = []
    if decision.is_blocked:
        blockers.append(f"{label} has blocked ownership policy: {decision.blocker}")
    if not _is_first_lane_scalar_type(argument.semantic_type):
        blockers.append(f"{label} is not a primitive scalar")
    if decision.kind is not ObjectKind.SCALAR:
        blockers.append(f"{label} policy kind is {decision.kind.value}, not scalar")
    if decision.codegen_action is not CodegenAction.DIRECT_VALUE:
        blockers.append(f"{label} codegen action is {decision.codegen_action.value}, not direct_value")
    if decision.python_barrier_action is not PythonBarrierAction.NONE:
        blockers.append(f"{label} Python action is {decision.python_barrier_action.value}, not none")
    if decision.native_barrier_action not in {
        NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
        NativeBarrierAction.PASS_STORAGE_ADDRESS,
    }:
        blockers.append(f"{label} native action is {decision.native_barrier_action.value}, not address")
    blockers.extend(_hidden_result_projection_blockers(label, decision, mapping))
    if (
        isinstance(mapping.result_position, int)
        and not isinstance(mapping.result_position, bool)
        and mapping.result_position < 0
    ):
        blockers.append(f"{label} has negative result position {mapping.result_position}")
    return tuple(blockers)


def _hidden_result_projection_blockers(
    label: str,
    decision: OwnershipDecision,
    mapping: models.ProjectionMapping,
) -> tuple[str, ...]:
    """Validate visibility and positions shared by hidden result families."""
    blockers = []
    if decision.python_visible:
        blockers.append(f"{label} is Python-visible")
    if not decision.projects_result:
        blockers.append(f"{label} does not project a Python result")
    if not isinstance(mapping.native_position, int):
        blockers.append(f"{label} is missing a native position")
    if not isinstance(mapping.result_position, int) or isinstance(mapping.result_position, bool):
        blockers.append(f"{label} has no integer result position")
    return tuple(blockers)


def _scalar_descriptor_result_blockers(
    semantic_type: models.SemanticType,
    decision: OwnershipDecision,
    label: str,
    mapping: models.ProjectionMapping | None = None,
) -> tuple[str, ...]:
    """Require one nullable copied rank-zero allocatable/pointer result."""
    blockers = []
    if decision.is_blocked:
        blockers.append(f"{label} has blocked ownership policy: {decision.blocker or decision.reason}")
    expected_kind = ObjectKind.STRING if semantic_type.name == "String" else ObjectKind.SCALAR
    if decision.kind is not expected_kind:
        blockers.append(f"{label} policy kind is {decision.kind.value}, not {expected_kind.value}")
    if decision.owner is not OwnershipOwner.PYTHON:
        blockers.append(f"{label} owner is {decision.owner.value}, not python")
    if decision.destruction is not DestructionPolicy.PYTHON_REFCOUNT:
        blockers.append(f"{label} destruction is {decision.destruction.value}, not python_refcount")
    if not decision.nullable or not decision.descriptor_boundary:
        blockers.append(f"{label} does not preserve nullable descriptor state")
    if decision.python_barrier_action is not PythonBarrierAction.NONE:
        blockers.append(f"{label} Python action is {decision.python_barrier_action.value}, not none")
    if mapping is not None:
        if not decision.projects_result or decision.python_visible:
            blockers.append(f"{label} projection visibility is inconsistent")
        if mapping.value_kind not in {"allocatable", "pointer"}:
            blockers.append(f"{label} descriptor kind {mapping.value_kind!r} is unsupported")
        if not isinstance(mapping.native_position, int) or not isinstance(mapping.result_position, int):
            blockers.append(f"{label} has incomplete native/result positions")
    return tuple(blockers)


def _native_array_handle_result_blockers(
    decision: OwnershipDecision,
    label: str,
) -> tuple[str, ...]:
    """Require one wrapper-owned allocatable handle result."""
    blockers = []
    if decision.is_blocked:
        blockers.append(f"{label} has blocked ownership policy: {decision.blocker or decision.reason}")
        return tuple(blockers)
    expected = (
        ("kind", decision.kind, ObjectKind.NUMPY_ARRAY),
        ("owner", decision.owner, OwnershipOwner.WRAPPER),
        ("transfer", decision.transfer, TransferMode.WRAPPER_INSTANCE),
        ("destruction", decision.destruction, DestructionPolicy.WRAPPER_DEALLOC),
        ("action", decision.codegen_action, CodegenAction.WRAPPER_INSTANCE),
    )
    blockers.extend(
        f"{label} native handle {name} is {actual.value}, not {required.value}"
        for name, actual, required in expected
        if actual is not required
    )
    if not decision.nullable:
        blockers.append(f"{label} native handle must preserve unallocated state")
    return tuple(blockers)


# Ordinary-array result policy.
def _ordinary_array_result_blockers(
    semantic_type: models.SemanticType,
    decision: OwnershipDecision,
    label: str,
) -> tuple[str, ...]:
    """Require one Python-owned fixed-shape ordinary array copy result."""
    blockers = []
    if decision.is_blocked:
        blockers.append(f"{label} has blocked ownership policy: {decision.blocker or decision.reason}")
    if decision.kind is not ObjectKind.NUMPY_ARRAY:
        blockers.append(f"{label} policy kind is {decision.kind.value}, not numpy_array")
    if decision.owner is not OwnershipOwner.PYTHON:
        blockers.append(f"{label} owner is {decision.owner.value}, not python")
    if decision.transfer is not TransferMode.COPY_RETURN:
        blockers.append(f"{label} transfer is {decision.transfer.value}, not copy_return")
    if decision.destruction is not DestructionPolicy.PYTHON_REFCOUNT:
        blockers.append(f"{label} destruction is {decision.destruction.value}, not python_refcount")
    if decision.storage_mode is not StorageMode.STACK:
        blockers.append(f"{label} storage is {decision.storage_mode.value}, not stack")
    if decision.codegen_action is not CodegenAction.COPY_OUT:
        blockers.append(f"{label} action is {decision.codegen_action.value}, not copy_out")
    if decision.python_barrier_action is not PythonBarrierAction.NONE:
        blockers.append(f"{label} Python action is {decision.python_barrier_action.value}, not none")
    if decision.native_barrier_action is not NativeBarrierAction.NONE:
        blockers.append(f"{label} native action is {decision.native_barrier_action.value}, not none")
    if decision.nullable or decision.descriptor_boundary:
        blockers.append(f"{label} is descriptor-backed or nullable")
    array = _array_handoff_policy(semantic_type)
    if array is None or array.rank is None or any(shape in {":", "::Strided", "...", "Flat"} for shape in array.shape):
        blockers.append(f"{label} ordinary array shape is not fully expressible")
    elif array.native_order != array.order:
        blockers.append(f"{label} COPY_F applies only to Python-visible array arguments")
    elif array.order == "ORDER_C" and array.rank > 1:
        blockers.append(f"{label} ordinary array copy requires Fortran element order")
    return tuple(blockers)


def _ordinary_array_hidden_result_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    mapping: models.ProjectionMapping,
) -> tuple[str, ...]:
    """Require one hidden fixed-shape array copied through bridge-owned storage."""
    label = f"hidden result {argument.name!r}"
    blockers = list(_ordinary_array_result_blockers(argument.semantic_type, decision, label))
    blockers = [item for item in blockers if " native action is " not in item]
    expected_native = (
        NativeBarrierAction.PASS_STORAGE_ADDRESS
        if _is_scalar_storage_array_policy(_array_handoff_policy(argument.semantic_type))
        else NativeBarrierAction.PASS_ARRAY_BUFFER
    )
    if decision.native_barrier_action is not expected_native:
        blockers.append(f"{label} native action is {decision.native_barrier_action.value}, not {expected_native.value}")
    if decision.python_visible or not decision.projects_result:
        blockers.append(f"{label} projection visibility is inconsistent")
    if not isinstance(mapping.native_position, int):
        blockers.append(f"{label} is missing a native position")
    if not isinstance(mapping.result_position, int) or isinstance(mapping.result_position, bool):
        blockers.append(f"{label} has no integer result position")
    elif mapping.result_position < 0:
        blockers.append(f"{label} has negative result position {mapping.result_position}")
    return tuple(blockers)


# String result and writeback policy.
def _fixed_string_result_blockers(decision: OwnershipDecision) -> tuple[str, ...]:
    """Require the completed copy-return policy for one direct fixed string."""
    blockers = list(_fixed_string_result_ownership_blockers(decision, "result"))
    if decision.is_blocked:
        blockers.append(f"result has blocked ownership policy: {decision.blocker or decision.reason}")
    if decision.kind is not ObjectKind.STRING:
        blockers.append(f"result policy kind is {decision.kind.value}, not string")
    if decision.codegen_action is not CodegenAction.COPY_OUT:
        blockers.append(f"result codegen action is {decision.codegen_action.value}, not copy_out")
    if decision.python_barrier_action is not PythonBarrierAction.NONE:
        blockers.append(f"result Python action is {decision.python_barrier_action.value}, not none")
    if decision.native_barrier_action is not NativeBarrierAction.NONE:
        blockers.append(f"result native action is {decision.native_barrier_action.value}, not none")
    return tuple(blockers)


def _fixed_string_hidden_result_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    mapping: models.ProjectionMapping,
) -> tuple[str, ...]:
    """Require one fixed string hidden output and its completed projection."""
    label = f"hidden result {argument.name!r}"
    blockers = list(_fixed_string_result_ownership_blockers(decision, label))
    if decision.is_blocked:
        blockers.append(
            f"hidden result {argument.name!r} has blocked ownership policy: {decision.blocker or decision.reason}"
        )
    if decision.kind is not ObjectKind.STRING:
        blockers.append(f"hidden result {argument.name!r} policy kind is {decision.kind.value}, not string")
    if decision.codegen_action is not CodegenAction.COPY_OUT:
        blockers.append(
            f"hidden result {argument.name!r} codegen action is {decision.codegen_action.value}, not copy_out"
        )
    if decision.python_barrier_action is not PythonBarrierAction.NONE:
        blockers.append(
            f"hidden result {argument.name!r} Python action is {decision.python_barrier_action.value}, not none"
        )
    if decision.native_barrier_action is not NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS:
        blockers.append(
            f"hidden result {argument.name!r} native action is "
            f"{decision.native_barrier_action.value}, not call-local address"
        )
    if decision.python_visible:
        blockers.append(f"hidden result {argument.name!r} is Python-visible")
    if not decision.projects_result:
        blockers.append(f"hidden result {argument.name!r} does not project a Python result")
    if not isinstance(mapping.native_position, int):
        blockers.append(f"hidden result {argument.name!r} is missing a native position")
    if not isinstance(mapping.result_position, int) or isinstance(mapping.result_position, bool):
        blockers.append(f"hidden result {argument.name!r} has no integer result position")
    elif mapping.result_position < 0:
        blockers.append(f"hidden result {argument.name!r} has negative result position {mapping.result_position}")
    return tuple(blockers)


def _fixed_string_result_ownership_blockers(
    decision: OwnershipDecision,
    label: str,
) -> tuple[str, ...]:
    """Require Python-owned stack-to-copy-return fixed string ownership."""
    blockers = []
    if decision.owner is not OwnershipOwner.PYTHON:
        blockers.append(f"{label} owner is {decision.owner.value}, not python")
    if decision.transfer is not TransferMode.COPY_RETURN:
        blockers.append(f"{label} transfer is {decision.transfer.value}, not copy_return")
    if decision.destruction is not DestructionPolicy.PYTHON_REFCOUNT:
        blockers.append(f"{label} destruction is {decision.destruction.value}, not python_refcount")
    if decision.storage_mode is not StorageMode.STACK:
        blockers.append(f"{label} storage is {decision.storage_mode.value}, not stack")
    if (decision.boundary_storage_mode or decision.storage_mode) is not StorageMode.STACK:
        blockers.append(f"{label} boundary storage is not stack")
    if decision.nullable:
        blockers.append(f"{label} is nullable outside deferred string results")
    return tuple(blockers)


def _string_result_status_blockers(
    results: tuple[ResultPolicy, ...],
    status_error: NativeStatusErrorPolicy | None,
) -> tuple[str, ...]:
    """Block status exits until public string-result release is planned."""
    if status_error is not None and any(result.ownership.kind is ObjectKind.STRING for result in results):
        return ("fixed string result with native status error requires planned failure-path release",)
    return ()


def _string_writeback_status_blockers(
    arguments: list[ArgumentPolicy],
    status_error: NativeStatusErrorPolicy | None,
) -> tuple[str, ...]:
    """Block status exits until mutable string-buffer cleanup is planned there."""
    if status_error is not None and any(
        argument.ownership.kind is ObjectKind.STRING and argument.codegen_action is CodegenAction.COPY_IN_OUT
        for argument in arguments
    ):
        return ("string replacement with native status error requires planned failure-path cleanup",)
    return ()


def _result_position_blockers(
    results: tuple[ResultPolicy, ...],
    arguments: list[ArgumentPolicy] | tuple[ArgumentPolicy, ...] = (),
) -> tuple[str, ...]:
    """Require native results and visible writebacks to cover one public order."""
    positions = tuple(result.result_position for result in results) + tuple(
        argument.result_position for argument in arguments if argument.projects_result
    )
    if not positions:
        return ()
    if sorted(positions) == list(range(len(positions))) and len(set(positions)) == len(positions):
        return ()
    return (f"binding result positions must cover 0..{len(positions) - 1} exactly once; received {positions}",)


def _function_shape_blockers(
    function: models.SemanticFunction,
    class_call: ClassMethodPolicy | None,
) -> tuple[str, ...]:
    """Return non-transfer blockers after class ownership is completed."""
    blockers: list[str] = []
    if function.visibility != "public" and class_call is None:
        blockers.append("function is not public")
    if isinstance(function, models.SemanticMethod) and class_call is None:
        blockers.append("method is missing completed class-call policy")
    if function.locals:
        blockers.append("function locals are outside the first scalar lane")
    if function.contracts:
        blockers.append("function contracts are outside the first scalar lane")
    return tuple(blockers)


def _completed_native_status_error_policy(
    function: models.SemanticFunction,
) -> NativeStatusErrorPolicy | None:
    policy = function.metadata.get(models.RESOLVED_RUNTIME_STATUS_ERROR_POLICY_METADATA)
    return policy if isinstance(policy, NativeStatusErrorPolicy) else None


def _runtime_status_output_owner_paths(function: models.SemanticFunction) -> frozenset[str]:
    policy = _completed_native_status_error_policy(function)
    if policy is None:
        return frozenset()
    outputs = [policy.status.owner_path]
    if policy.message is not None:
        outputs.append(policy.message.owner_path)
    return frozenset(outputs)


def _runtime_status_plan_blockers(policy: NativeStatusErrorPolicy | None) -> tuple[str, ...]:
    """Return Phase 2D backend blockers after semantic validity is complete."""
    if policy is None:
        return ()
    blockers = []
    if policy.status.semantic_type_name != "Int32":
        blockers.append("native status error projection requires an Int32 status in the current plan lane")
    if policy.message is not None and policy.message.character_length is None:
        blockers.append("native status error message requires a fixed positive character length")
    return tuple(blockers)


def _character_length(semantic_type: models.SemanticType) -> int | None:
    value = semantic_type.metadata.get("fortran_character_length")
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    if isinstance(value, str) and value.strip().isdigit() and int(value.strip()) > 0:
        return int(value.strip())
    return None


def _lifecycle_policies(
    arguments: list[ArgumentPolicy],
) -> tuple[tuple[LifecyclePolicy, ...], tuple[str, ...]]:
    """Return completed replacement/writeback actions and structural blockers."""
    actions = []
    blockers: list[str] = []
    for argument in arguments:
        if not argument.projects_result:
            continue
        if argument.result_position is None:
            blockers.append(f"argument {argument.name!r} writeback is missing a result position")
            continue
        phases = (
            (WritebackPhase.COPY_OUT,) if argument.ownership.kind is ObjectKind.NUMPY_ARRAY else tuple(WritebackPhase)
        )
        actions.extend(
            LifecyclePolicy(
                owner_path=argument.owner_path,
                phase=phase,
                source_role=f"{argument.owner_path}:value",
                codegen_action=argument.codegen_action,
                semantic_type_name=argument.semantic_type_name,
                result_position=argument.result_position,
                object_kind=argument.ownership.kind,
            )
            for phase in phases
        )
    return tuple(actions), tuple(blockers)


def _derived_result_lifecycle_policies(
    results: tuple[ResultPolicy, ...],
) -> tuple[tuple[LifecyclePolicy, ...], tuple[LifecyclePolicy, ...]]:
    """Record failure cleanup and exactly-once wrapper release for owned objects."""
    owned = tuple(
        result
        for result in results
        if result.derived is not None and result.derived.release is DerivedRelease.WRAPPER_DESTROY
    )

    def action(result: ResultPolicy, operation: LifecycleOperation) -> LifecyclePolicy:
        return LifecyclePolicy(
            owner_path=result.owner_path,
            phase=WritebackPhase.CLEANUP,
            source_role=f"{result.owner_path}:native-result",
            codegen_action=result.codegen_action,
            semantic_type_name=result.semantic_type_name,
            result_position=result.result_position,
            object_kind=result.ownership.kind,
            operation=operation,
        )

    return (
        tuple(action(result, LifecycleOperation.DESTROY_ON_FAILURE) for result in owned),
        tuple(action(result, LifecycleOperation.TRANSFER_TO_WRAPPER) for result in owned),
    )


def _native_position_blockers(native_positions: object) -> tuple[str, ...]:
    positions = tuple(native_positions)
    if sorted(positions) != list(range(len(positions))):
        return ("native-call slots must cover each native position exactly once in order",)
    return ()


def _ownership_decision(owner: object, metadata_key: str) -> OwnershipDecision | None:
    decision = getattr(owner, "metadata", {}).get(metadata_key)
    return decision if isinstance(decision, OwnershipDecision) else None


def _is_first_lane_scalar_type(semantic_type: models.SemanticType) -> bool:
    scalar_name = semantic_type.dtype or semantic_type.name
    return bool(
        int(semantic_type.rank or 0) == 0
        and not _is_scalar_storage_type(semantic_type)
        and semantic_type.name != "String"
        and scalar_name in _PLAN_PRIMITIVE_SCALAR_TYPES
    )


def _is_scalar_storage_type(semantic_type: models.SemanticType) -> bool:
    storage = semantic_type.storage
    array = storage.array if storage is not None else None
    return bool(array is not None and array.category == SCALAR_STORAGE_CATEGORY)


def _is_plan_string_value_type(semantic_type: models.SemanticType) -> bool:
    """Return whether one semantic type is a scalar Python string value."""
    return bool(int(semantic_type.rank or 0) == 0 and semantic_type.name == "String")


def _is_fixed_plan_string_result_type(semantic_type: models.SemanticType) -> bool:
    """Return whether one result is a fixed positive scalar string."""
    length = _character_length(semantic_type)
    return bool(_is_plan_string_value_type(semantic_type) and length is not None and length > 0)


def _is_first_lane_literal_type(literal_type: str) -> bool:
    """Return whether a hidden literal type belongs to the scalar input lane."""
    return literal_type in {"Bool", "Int32", "Float32", "Float64", "Complex64", "Complex128"}


# Native-array-handle policy projection.
def _is_scalar_descriptor_result_type(
    semantic_type: models.SemanticType,
    *,
    descriptor_kind: str | None = None,
) -> bool:
    """Return whether rank-zero result storage is allocatable or pointer-backed."""
    descriptor = descriptor_kind or _scalar_descriptor_kind(semantic_type)
    return int(semantic_type.rank or 0) == 0 and descriptor in {"allocatable", "pointer"}


def _scalar_descriptor_kind(semantic_type: models.SemanticType) -> str | None:
    """Return the explicit rank-zero descriptor marker completed by semantics."""
    if int(semantic_type.rank or 0) != 0:
        return None
    allocatable = bool(semantic_type.metadata.get("fortran_allocatable"))
    pointer = bool(semantic_type.metadata.get("fortran_pointer"))
    if allocatable and pointer:
        raise ValueError(f"Scalar type {semantic_type.name!r} cannot be both allocatable and pointer")
    if allocatable:
        return "allocatable"
    if pointer:
        return "pointer"
    return None


def _scalar_descriptor_result_policy(
    semantic_type: models.SemanticType,
    decision: OwnershipDecision,
    *,
    descriptor_kind: str | None = None,
) -> ScalarDescriptorResultPolicy | None:
    """Project one completed nullable rank-zero descriptor copy policy."""
    if decision.kind is ObjectKind.DERIVED_TYPE:
        return None
    if not _is_scalar_descriptor_result_type(semantic_type, descriptor_kind=descriptor_kind):
        return None
    descriptor = descriptor_kind or _scalar_descriptor_kind(semantic_type)
    if descriptor is None:
        return None
    return ScalarDescriptorResultPolicy(
        descriptor_kind=NativeArrayDescriptorKind(descriptor),
        runtime_length=semantic_type.name == "String",
        nullable=decision.nullable,
        copy_reason=SCALAR_DESCRIPTOR_RESULT_COPY_REASON,
        release_owner=OwnershipOwner.PYTHON,
    )


def _native_array_handle_wrapper_policy(
    semantic_type: models.SemanticType,
    completed: object,
    owner_path: str,
) -> NativeArrayHandleWrapperPolicy | None:
    """Translate completed string selectors once into typed wrapper policy."""
    descriptor = native_array_descriptor_kind(semantic_type)
    if descriptor is None:
        return None
    if int(semantic_type.rank or 0) == 0:
        return None
    if not isinstance(completed, CompletedNativeArrayHandlePolicy):
        raise ValueError(f"Native array handle {owner_path!r} is missing completed policy")
    if completed.is_blocked:
        return None
    output_projection = _native_array_enum(
        NativeArrayOutputProjection,
        completed.output_projection,
        owner_path,
        "output projection",
    )
    handle_kind = _native_array_enum(NativeArrayHandleKind, completed.handle_kind, owner_path, "handle kind")
    handoff = NativeDescriptorHandoffPolicy(
        abi=_native_descriptor_handoff_abi(handle_kind, output_projection),
        rank=int(semantic_type.rank or 0),
        optional_presence=completed.optional_absent,
    )
    interop = _native_array_enum(
        NativeArrayDescriptorInterop,
        completed.descriptor_interop,
        owner_path,
        "descriptor interop",
    )
    operations = {
        _native_array_enum(NativeArrayOperation, item, owner_path, "operation") for item in completed.operations
    }
    operations.update(
        {
            NativeArrayOperation.SHAPE,
            NativeArrayOperation.ARRAY_ACTUAL,
            NativeArrayOperation.DESCRIPTOR,
            NativeArrayOperation.NATIVE_BYTE_ORDER,
            NativeArrayOperation.ALIGNED,
            NativeArrayOperation.WRITEABLE,
            NativeArrayOperation.LAYOUT,
        }
    )
    if semantic_type.name == "String":
        operations.add(NativeArrayOperation.ELEMENT_LENGTH)
        if semantic_type.metadata.get("fortran_character_length") == ":":
            operations.difference_update({NativeArrayOperation.ALLOCATE, NativeArrayOperation.RESIZE})
    if descriptor == "pointer":
        operations.add(NativeArrayOperation.CONTIGUOUS)
    if completed.destroy_behavior == NativeArrayDestroyBehavior.HANDLE_FINALIZER.value:
        operations.add(NativeArrayOperation.DESTROY)
    array = _array_handoff_policy(semantic_type)
    if array is None or array.rank is None:
        raise ValueError(f"Native array handle {owner_path!r} requires one concrete array handoff")
    return NativeArrayHandleWrapperPolicy(
        descriptor_kind=_native_array_enum(
            NativeArrayDescriptorKind,
            completed.descriptor_kind,
            owner_path,
            "descriptor kind",
        ),
        handle_kind=handle_kind,
        origin=_native_array_enum(NativeArrayHandleOrigin, completed.origin, owner_path, "origin"),
        owner=_native_array_enum(OwnershipOwner, completed.owner, owner_path, "owner"),
        owner_retention=_native_array_enum(
            NativeArrayOwnerRetention,
            completed.owner_retention,
            owner_path,
            "owner retention",
        ),
        descriptor_ownership=_native_array_enum(
            NativeArrayDescriptorOwnership,
            completed.descriptor_ownership,
            owner_path,
            "descriptor ownership",
        ),
        borrowed=completed.borrowed,
        getter_behavior=_native_array_enum(
            NativeArrayGetterBehavior,
            completed.getter_behavior,
            owner_path,
            "getter behavior",
        ),
        setter_action=_native_array_setter_action(completed.python_setter, owner_path),
        native_assignment=_native_array_assignment(completed.native_setter, owner_path),
        output_projection=output_projection,
        result_allocation=_native_array_enum(
            NativeArrayResultAllocation,
            completed.result_allocation,
            owner_path,
            "result allocation",
        ),
        release=_native_array_enum(NativeArrayRelease, completed.release, owner_path, "release"),
        target_lifetime=completed.target_lifetime,
        destroy_behavior=_native_array_enum(
            NativeArrayDestroyBehavior,
            completed.destroy_behavior,
            owner_path,
            "destroy behavior",
        ),
        extraction_action=_native_array_enum(
            NativeArrayExtractionAction,
            completed.to_numpy,
            owner_path,
            "extraction action",
        ),
        descriptor_interop=interop,
        nullable=completed.nullable,
        optional_absent=completed.optional_absent,
        storage_mode=_native_array_enum(StorageMode, completed.storage_mode, owner_path, "storage mode"),
        operations=tuple(sorted(operations, key=lambda item: item.value)),
        required_headers=(
            (NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER,)
            if (
                interop is not NativeArrayDescriptorInterop.NONE
                or handle_kind
                in {
                    NativeArrayHandleKind.ARGUMENT_DESCRIPTOR,
                    NativeArrayHandleKind.OPTIONAL_ABSENT_HANDLE,
                    NativeArrayHandleKind.OWNED_RESULT_DESCRIPTOR,
                }
            )
            else ()
        ),
        array=array,
        handoff=handoff,
    )


def _native_descriptor_handoff_abi(
    handle_kind: NativeArrayHandleKind,
    output_projection: NativeArrayOutputProjection,
) -> NativeDescriptorHandoffABI:
    """Select one descriptor ABI from completed handle/result policy."""
    if handle_kind is NativeArrayHandleKind.OWNED_RESULT_DESCRIPTOR:
        return NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE
    if output_projection is NativeArrayOutputProjection.PROJECTED_HANDLE:
        return NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR
    return NativeDescriptorHandoffABI.FACT_PACKED_CALL_LOCAL


def _native_array_enum(enum_type, value: object, owner_path: str, label: str):
    """Translate one completed selector or fail at the policy boundary."""
    try:
        return enum_type(value)
    except ValueError:
        raise ValueError(f"Native array handle {owner_path!r} has unsupported {label} {value!r}") from None


def _native_array_setter_action(value: str, owner_path: str) -> SetterAction:
    """Translate semantic handle setter spelling into the shared setter enum."""
    if value == "none":
        return SetterAction.OMIT
    return _native_array_enum(SetterAction, value, owner_path, "Python setter")


# Layer-owned representation transformations.
def _argument_transformation_policies(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    array: ArrayHandoffPolicy | None,
) -> tuple[tuple[TransformationPolicy, ...], tuple[str, ...]]:
    """Complete binding-owned array copies and their lifecycle before planning."""
    if array is None:
        return (), ()
    if decision.transfer is TransferMode.COPY_RETURN:
        return _array_replacement_transformations(argument, decision, array)
    if array.native_order == array.order:
        return (), ()
    blockers = _copy_to_fortran_argument_blockers(argument, decision, array)
    if blockers:
        return (), blockers
    transformations = []
    reason = "explicit COPY_F converts C-order Python storage while preserving logical Fortran axes"
    if decision.codegen_action is not CodegenAction.IDENTITY_OUTPUT:
        transformations.append(
            TransformationPolicy(
                phase=WritebackPhase.COPY_IN,
                layer=TransformationLayer.BINDING,
                action=TransformationAction.COPY_ARRAY_REPRESENTATION,
                source_representation="numpy_order_c",
                target_representation="numpy_order_f",
                reason=reason,
            )
        )
    if decision.mutates_native:
        transformations.append(
            TransformationPolicy(
                phase=WritebackPhase.COPY_OUT,
                layer=TransformationLayer.BINDING,
                action=TransformationAction.COPY_ARRAY_REPRESENTATION,
                source_representation="numpy_order_f",
                target_representation="numpy_order_c",
                reason=reason,
            )
        )
    transformations.append(
        TransformationPolicy(
            phase=WritebackPhase.CLEANUP,
            layer=TransformationLayer.BINDING,
            action=TransformationAction.RELEASE_TEMPORARY,
            source_representation="numpy_order_f",
            target_representation="released",
            reason="binding owns the complete COPY_F NumPy temporary lifecycle",
        )
    )
    return tuple(transformations), ()


def _array_replacement_transformations(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    array: ArrayHandoffPolicy,
) -> tuple[tuple[TransformationPolicy, ...], tuple[str, ...]]:
    """Copy immutable storage once and publish the mutated temporary as output."""
    blockers = []
    if argument.optional or array.rank is None or argument.semantic_type.name == "String":
        blockers.append(f"argument {argument.name!r} array replacement requires a required numeric fixed rank")
    if decision.codegen_action is not CodegenAction.COPY_IN_OUT or not decision.projects_result:
        blockers.append(f"argument {argument.name!r} array replacement has incomplete copy-out policy")
    if blockers:
        return (), tuple(blockers)
    reason = "immutable array input uses one binding-owned mutable replacement"
    return (
        (
            TransformationPolicy(
                phase=WritebackPhase.COPY_IN,
                layer=TransformationLayer.BINDING,
                action=TransformationAction.COPY_ARRAY_REPRESENTATION,
                source_representation="numpy_input",
                target_representation="numpy_native_order",
                reason=reason,
            ),
            TransformationPolicy(
                phase=WritebackPhase.COPY_OUT,
                layer=TransformationLayer.BINDING,
                action=TransformationAction.PUBLISH_ARRAY_REPLACEMENT,
                source_representation="numpy_native_order",
                target_representation="python_result",
                reason=reason,
            ),
            TransformationPolicy(
                phase=WritebackPhase.CLEANUP,
                layer=TransformationLayer.BINDING,
                action=TransformationAction.RELEASE_TEMPORARY,
                source_representation="numpy_native_order",
                target_representation="released",
                reason="binding releases the unpublished replacement on failure",
            ),
        ),
        (),
    )


def _copy_to_fortran_argument_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    array: ArrayHandoffPolicy,
) -> tuple[str, ...]:
    """Keep COPY_F on its initial required dense numeric ndarray lane."""
    blockers = []
    if argument.optional:
        blockers.append(f"argument {argument.name!r} COPY_F optional arrays are not implemented")
    if (
        decision.kind is not ObjectKind.NUMPY_ARRAY
        or decision.python_barrier_action is not PythonBarrierAction.ARRAY_STORAGE
    ):
        blockers.append(f"argument {argument.name!r} COPY_F requires ordinary NumPy array storage")
    if decision.descriptor_boundary or native_array_descriptor_kind(argument.semantic_type) is not None:
        blockers.append(f"argument {argument.name!r} COPY_F does not support native descriptors")
    if argument.semantic_type.name == "String":
        blockers.append(f"argument {argument.name!r} COPY_F character arrays are not implemented")
    if array.rank is None or array.rank <= 1 or array.contiguous is not True:
        blockers.append(f"argument {argument.name!r} COPY_F requires a concrete dense multidimensional array")
    if array.order != "ORDER_C" or array.native_order != "ORDER_F":
        blockers.append(f"argument {argument.name!r} COPY_F has inconsistent source/native order")
    return tuple(blockers)


def _native_array_assignment(value: str, owner_path: str) -> AssignmentMode:
    """Translate semantic handle native setter spelling into assignment enum."""
    return _native_array_enum(AssignmentMode, value, owner_path, "native setter")


def _native_array_actual_policy(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    array: ArrayHandoffPolicy | None,
) -> NativeArrayActualPolicy | None:
    """Complete handle-as-array-actual acceptance for the Phase 6 buffer ABI."""
    if native_array_descriptor_kind(argument.semantic_type) is not None:
        return None
    if (
        array is None
        or array.native_order != array.order
        or array.rank is None
        or argument.optional
        or argument.semantic_type.name == "String"
        or decision.transfer is TransferMode.COPY_RETURN
        or decision.python_barrier_action is not PythonBarrierAction.ARRAY_STORAGE
        or decision.native_barrier_action is not NativeBarrierAction.PASS_ARRAY_BUFFER
    ):
        return None
    try:
        dtype = _NUMPY_DTYPE_NAMES[argument.semantic_type.name]
    except KeyError:
        return None
    return NativeArrayActualPolicy(
        accepted_sources=(
            NativeArraySourceKind.NDARRAY,
            NativeArraySourceKind.ALLOCATABLE_HANDLE,
            NativeArraySourceKind.POINTER_HANDLE,
        ),
        dtype=dtype,
        rank=array.rank,
        shape=array.shape,
        order=None if array.rank == 1 else ("F" if array.order != "ORDER_C" else "C"),
        writable=decision.mutates_native,
        require_native_byte_order=True,
        require_aligned=True,
        require_contiguous=array.contiguous is True,
        flatten_storage=array.flatten_python_storage,
        flat_axis=array.flat_axis,
    )


def _native_array_module_variable_blockers(
    variable: models.SemanticVariable,
    getter: OwnershipDecision | None,
    setter: OwnershipDecision | None,
    handle: NativeArrayHandleWrapperPolicy,
) -> list[str]:
    """Validate one borrowed module descriptor handle before planning."""
    blockers = []
    if variable.visibility != "public":
        blockers.append("native array module variable is not public")
    if handle.handle_kind is not NativeArrayHandleKind.BORROWED_MODULE_DESCRIPTOR:
        blockers.append(f"native array module handle kind {handle.handle_kind.value!r} is unsupported")
    if getter is None or getter.is_blocked or getter.kind is not ObjectKind.NUMPY_ARRAY:
        blockers.append("native array module getter is missing a completed array policy")
    if setter is None or handle.setter_action is not SetterAction.REJECT_REPLACEMENT:
        blockers.append("native array module handle must reject replacement assignment")
    if handle.descriptor_ownership is not NativeArrayDescriptorOwnership.BORROWED or not handle.borrowed:
        blockers.append("native array module handle must borrow native descriptor storage")
    if handle.destroy_behavior is not NativeArrayDestroyBehavior.NONE:
        blockers.append("native array module handle cannot destroy native descriptor storage")
    return blockers


# Scalar-derived module-object policy.
def _derived_module_object_policy(
    variable: models.SemanticVariable,
    getter: OwnershipDecision,
    setter: OwnershipDecision | None,
    *,
    owner_path: str,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> DerivedModuleObjectPolicy:
    """Complete direct-address versus typed-member module access."""
    handoff = _derived_handoff_policy(
        variable.semantic_type,
        getter,
        owner_path=owner_path,
        origin=DerivedObjectOrigin.NATIVE_MODULE,
        derived_types=derived_types,
    )
    if handoff is None:
        raise ValueError(f"Derived module variable {owner_path!r} has no derived handoff")
    root = derived_types.get(handoff.type_identity)
    member_paths = ()
    member_blockers = ()
    if root is not None:
        member_paths, member_blockers = derived_member_path_policies(root, derived_types)
    else:
        member_blockers = (f"derived module object has no completed type policy for {variable.semantic_type.name!r}",)
    return DerivedModuleObjectPolicy(
        handoff=handoff,
        access=(
            ModuleObjectAccessMechanism.MEMBER_PROXY
            if _is_descriptor_backed_scalar_derived_type(variable.semantic_type)
            else ModuleObjectAccessMechanism.DIRECT_ADDRESS
            if variable.semantic_type.metadata.get("aliased")
            else ModuleObjectAccessMechanism.MEMBER_PROXY
        ),
        replacement=SetterAction.REJECT_REPLACEMENT,
        member_paths=member_paths,
        blockers=member_blockers,
    )


def _derived_module_constant_policy(
    variable: models.SemanticVariable,
    getter: OwnershipDecision,
    setter: OwnershipDecision | None,
    *,
    owner_path: str,
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
) -> DerivedModuleObjectPolicy:
    """Complete an explicit native constant as a fresh wrapper-owned value copy."""
    handoff = _derived_handoff_policy(
        variable.semantic_type,
        getter,
        owner_path=owner_path,
        origin=DerivedObjectOrigin.CONSTANT_VALUE,
        derived_types=derived_types,
    )
    if handoff is None:
        raise ValueError(f"Derived module constant {owner_path!r} has no derived handoff")
    root = derived_types.get(handoff.type_identity)
    blockers = (
        ()
        if root is not None
        else (f"derived module constant has no completed type policy for {variable.semantic_type.name!r}",)
    )
    return DerivedModuleObjectPolicy(
        handoff=handoff,
        access=ModuleObjectAccessMechanism.VALUE_COPY,
        replacement=SetterAction.REJECT_REPLACEMENT,
        blockers=blockers,
    )


def _derived_module_constant_blockers(
    variable: models.SemanticVariable,
    getter: OwnershipDecision,
    setter: OwnershipDecision | None,
    policy: DerivedModuleObjectPolicy,
) -> list[str]:
    """Validate one explicit rank-zero derived constant value copy."""
    blockers = []
    if variable.visibility != "public":
        blockers.append("derived module constant is not public")
    if int(variable.semantic_type.rank or 0) != 0:
        blockers.append("derived module constant is not rank zero")
    expected_getter = (
        getter.owner is OwnershipOwner.WRAPPER
        and getter.transfer is TransferMode.WRAPPER_INSTANCE
        and getter.destruction is DestructionPolicy.WRAPPER_DEALLOC
    )
    if not expected_getter:
        blockers.append("derived module constant is not a completed wrapper-owned value copy")
    if setter is None or setter.setter_action is not SetterAction.OMIT:
        blockers.append("derived module constant must omit native replacement assignment")
    if policy.replacement is not SetterAction.REJECT_REPLACEMENT:
        blockers.append("derived module constant must reject Python replacement")
    if policy.handoff.owner_retention is not DerivedOwnerRetention.WRAPPER_INSTANCE:
        blockers.append("derived module constant must retain its wrapper instance")
    if policy.handoff.release is not DerivedRelease.WRAPPER_DESTROY:
        blockers.append("derived module constant must release its materialized native copy")
    blockers.extend(policy.blockers)
    return blockers


def _derived_module_variable_blockers(
    variable: models.SemanticVariable,
    getter: OwnershipDecision,
    setter: OwnershipDecision | None,
    policy: DerivedModuleObjectPolicy,
) -> list[str]:
    """Validate one native-owned live rank-zero module object."""
    blockers = []
    if variable.visibility != "public":
        blockers.append("derived module variable is not public")
    if int(variable.semantic_type.rank or 0) != 0:
        blockers.append("derived module object is not rank zero")
    if variable.semantic_type.metadata.get("fortran_polymorphic"):
        blockers.append("polymorphic derived module objects are unsupported")
    expected_getter = (
        getter.owner is OwnershipOwner.NATIVE
        and getter.transfer is TransferMode.BORROWED_VIEW
        and getter.destruction is DestructionPolicy.NATIVE_OWNER
        and getter.borrowed
    )
    if not expected_getter:
        blockers.append("derived module getter is not a completed native-owned live borrow")
    if setter is None or setter.setter_action is not SetterAction.REJECT_REPLACEMENT:
        blockers.append("derived module object must reject whole-object replacement")
    if policy.handoff.owner_retention is not DerivedOwnerRetention.NATIVE_MODULE:
        blockers.append("derived module object must retain its native module owner")
    if policy.handoff.release is not DerivedRelease.NATIVE_OWNER:
        blockers.append("derived module object cannot claim native destruction")
    expected_storage = _derived_object_storage(
        variable.semantic_type,
        DerivedObjectOrigin.NATIVE_MODULE,
    )
    if policy.handoff.storage is not expected_storage:
        blockers.append(
            f"derived module object storage is {policy.handoff.storage.value!r}, not {expected_storage.value!r}"
        )
    if not policy.member_paths:
        blockers.append("derived module object has no completed finite member paths")
    blockers.extend(policy.blockers)
    return blockers


# Scalar module-variable policy.
def _scalar_module_variable_blockers(
    variable: models.SemanticVariable,
    getter: OwnershipDecision | None,
    setter: OwnershipDecision | None,
    descriptor_kind: str | None,
    constant: bool,
) -> list[str]:
    """Return Phase 4 blockers for one module variable."""
    blockers = []
    if variable.visibility != "public":
        blockers.append("module variable is not public")
    if not _is_first_lane_scalar_type(variable.semantic_type):
        blockers.append("module variable is not a primitive rank-zero scalar")
    if getter is None:
        blockers.append("module variable is missing completed getter policy")
    elif getter.is_blocked or getter.kind is not ObjectKind.SCALAR:
        blockers.append("module variable getter is not a supported scalar policy")
    elif getter.codegen_action not in {CodegenAction.DIRECT_VALUE, CodegenAction.SNAPSHOT_COPY}:
        blockers.append(f"module variable getter action {getter.codegen_action.value!r} is unsupported")
    if setter is None:
        blockers.append("module variable is missing completed setter policy")
    else:
        blockers.extend(_scalar_module_setter_blockers(setter, descriptor_kind, constant))
    if constant and variable.default_value is None:
        blockers.append("scalar module constant is missing its completed value")
    elif constant and not _is_scalar_module_literal(variable.default_value, variable.semantic_type.name):
        blockers.append("scalar module constant value is not a supported literal")
    initializer = variable.metadata.get(models.RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA)
    if initializer is not None and (setter is None or setter.setter_action is not SetterAction.WRITE_THROUGH):
        blockers.append("module variable initializer requires a write-through setter")
    if initializer is not None and not _is_scalar_module_literal(initializer, variable.semantic_type.name):
        blockers.append("module variable initializer is not a supported scalar literal")
    return blockers


def _scalar_module_setter_blockers(
    setter: OwnershipDecision,
    descriptor_kind: str | None,
    constant: bool,
) -> tuple[str, ...]:
    """Return completed setter consistency blockers."""
    if constant:
        if setter.setter_action is not SetterAction.OMIT or setter.assignment_mode is not AssignmentMode.NONE:
            return ("scalar constant must omit native setter assignment",)
        return ()
    if setter.setter_action is SetterAction.WRITE_THROUGH:
        if setter.assignment_mode is not AssignmentMode.VALUE_COPY:
            return ("write-through scalar setter requires value-copy native assignment",)
        if setter.python_barrier_action is not PythonBarrierAction.SCALAR_VALUE:
            return ("write-through scalar setter requires scalar-value Python conversion",)
        return ()
    if setter.setter_action is SetterAction.REJECT_REPLACEMENT:
        if descriptor_kind is None:
            return ("rejected scalar replacement requires persistent descriptor storage",)
        return ()
    return (f"non-constant scalar setter action {setter.setter_action.value!r} is unsupported",)


def _scalar_module_getter_action(
    getter: OwnershipDecision | None,
    constant: bool,
) -> ModuleGetterAction:
    if constant:
        return ModuleGetterAction.CONSTANT_VALUE
    if getter is not None and getter.codegen_action is CodegenAction.SNAPSHOT_COPY and getter.nullable:
        return ModuleGetterAction.NULLABLE_SNAPSHOT
    return ModuleGetterAction.DIRECT_VALUE


def _scalar_module_native_assignment(
    setter: OwnershipDecision | None,
) -> AssignmentMode:
    """Project the completed native setter action for bridge lowering."""
    if setter is None or setter.setter_action is not SetterAction.WRITE_THROUGH:
        return AssignmentMode.NONE
    return setter.assignment_mode


def _scalar_module_descriptor_kind(variable: models.SemanticVariable) -> str | None:
    metadata = variable.semantic_type.metadata
    if metadata.get("fortran_allocatable"):
        return "allocatable"
    if metadata.get("fortran_pointer"):
        return "pointer"
    return None


def _is_scalar_module_constant(variable: models.SemanticVariable) -> bool:
    return any(constraint.name == "Constant" for constraint in variable.semantic_type.constraints)


def _is_scalar_module_literal(value: object, semantic_type_name: str) -> bool:
    try:
        _scalar_module_literal_value(value, semantic_type_name)
    except (TypeError, ValueError, SyntaxError):
        return False
    return True


def _scalar_module_literal_value(value: object, semantic_type_name: str) -> object:
    """Normalize Python/Fortran scalar literal spelling during policy completion."""
    if not isinstance(value, str):
        return value
    text = value.strip()
    if semantic_type_name == "Bool":
        lowered = text.casefold()
        if lowered in {".true.", "true"}:
            return True
        if lowered in {".false.", "false"}:
            return False
    normalized = text.replace("D", "e").replace("d", "e")
    parsed = ast.literal_eval(normalized)
    if semantic_type_name in {"Complex64", "Complex128"} and isinstance(parsed, tuple):
        if len(parsed) != 2:
            raise ValueError("complex scalar literal requires real and imaginary components")
        return complex(parsed[0], parsed[1])
    return parsed


def _optional_mode(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> OptionalMode:
    """Return the completed presence behavior for one scalar argument."""
    if not argument.optional:
        if decision.kind in {ObjectKind.SCALAR, ObjectKind.DERIVED_TYPE} and decision.descriptor_boundary:
            return OptionalMode.REQUIRED_DESCRIPTOR
        return OptionalMode.REQUIRED
    if decision.descriptor_boundary:
        return OptionalMode.DESCRIPTOR
    return OptionalMode.NULLABLE_VALUE


def _argument_bridge_data_action(
    decision: OwnershipDecision,
    optional_mode: OptionalMode,
    value_kind: str | None,
) -> tuple[BridgeDataAction, str | None]:
    """Complete whether the bridge reuses, views, or copies one input payload."""
    if decision.kind is ObjectKind.DERIVED_TYPE:
        if (
            decision.python_barrier_action is PythonBarrierAction.WRAPPER_INSTANCE
            and decision.native_barrier_action is NativeBarrierAction.PASS_WRAPPER_ADDRESS
        ):
            return BridgeDataAction.ASSOCIATE_VIEW, None
        return BridgeDataAction.BLOCKED, None
    if decision.kind is ObjectKind.NUMPY_ARRAY:
        return _array_argument_bridge_data_action(decision, optional_mode)
    if decision.kind is ObjectKind.STRING:
        return _string_argument_bridge_data_action(decision, optional_mode)
    return _scalar_argument_bridge_data_action(decision, optional_mode, value_kind)


# Ordinary-array bridge data policy.
def _array_argument_bridge_data_action(
    decision: OwnershipDecision,
    optional_mode: OptionalMode,
) -> tuple[BridgeDataAction, str | None]:
    """Complete one buffer, raw-address, or native-descriptor bridge view."""
    if _scalar_storage_array_bridge_uses_view(decision, optional_mode):
        return BridgeDataAction.ASSOCIATE_VIEW, None
    if _copy_in_out_array_bridge_uses_view(decision, optional_mode):
        return BridgeDataAction.ASSOCIATE_VIEW, None
    native_descriptor_action = _native_descriptor_array_bridge_data_action(decision, optional_mode)
    if native_descriptor_action is not None:
        return native_descriptor_action, None
    if _raw_array_address_bridge_uses_view(decision, optional_mode):
        return BridgeDataAction.ASSOCIATE_VIEW, None
    if _array_storage_bridge_uses_view(decision, optional_mode):
        return BridgeDataAction.ASSOCIATE_VIEW, None
    return BridgeDataAction.BLOCKED, None


def _scalar_storage_array_bridge_uses_view(decision: OwnershipDecision, optional_mode: OptionalMode) -> bool:
    return (
        optional_mode in _ARRAY_VALUE_OPTIONAL_MODES
        and decision.python_barrier_action is PythonBarrierAction.SCALAR_STORAGE
        and decision.native_barrier_action is NativeBarrierAction.PASS_STORAGE_ADDRESS
        and decision.codegen_action in _ARRAY_VIEW_CODEGEN_ACTIONS
    )


def _copy_in_out_array_bridge_uses_view(decision: OwnershipDecision, optional_mode: OptionalMode) -> bool:
    return (
        optional_mode is OptionalMode.REQUIRED
        and decision.python_barrier_action is PythonBarrierAction.ARRAY_STORAGE
        and decision.native_barrier_action is NativeBarrierAction.PASS_ARRAY_BUFFER
        and decision.codegen_action is CodegenAction.COPY_IN_OUT
        and decision.transfer is TransferMode.COPY_RETURN
    )


def _native_descriptor_array_bridge_data_action(
    decision: OwnershipDecision,
    optional_mode: OptionalMode,
) -> BridgeDataAction | None:
    if optional_mode not in _ARRAY_DESCRIPTOR_OPTIONAL_MODES:
        return None
    if decision.python_barrier_action is not PythonBarrierAction.WRAPPER_INSTANCE:
        return None
    if decision.native_barrier_action is not NativeBarrierAction.PASS_NATIVE_DESCRIPTOR:
        return None
    if decision.codegen_action is CodegenAction.CALL_LOCAL_INPUT:
        return BridgeDataAction.ASSOCIATE_VIEW
    if decision.codegen_action is CodegenAction.IN_PLACE_ARGUMENT:
        return BridgeDataAction.DIRECT_TRANSFER
    return None


def _raw_array_address_bridge_uses_view(decision: OwnershipDecision, optional_mode: OptionalMode) -> bool:
    return (
        optional_mode is OptionalMode.REQUIRED
        and decision.python_barrier_action is PythonBarrierAction.RAW_ADDRESS
        and decision.native_barrier_action is NativeBarrierAction.PASS_RAW_ADDRESS
        and decision.codegen_action in _RAW_ARRAY_VIEW_CODEGEN_ACTIONS
    )


def _array_storage_bridge_uses_view(decision: OwnershipDecision, optional_mode: OptionalMode) -> bool:
    return (
        optional_mode in _ARRAY_VALUE_OPTIONAL_MODES
        and decision.python_barrier_action is PythonBarrierAction.ARRAY_STORAGE
        and decision.native_barrier_action is NativeBarrierAction.PASS_ARRAY_BUFFER
        and decision.codegen_action in _ARRAY_VIEW_CODEGEN_ACTIONS
    )


# String bridge data policy.
def _string_argument_bridge_data_action(
    decision: OwnershipDecision,
    optional_mode: OptionalMode,
) -> tuple[BridgeDataAction, str | None]:
    """Complete one string value, storage, or raw-address representation."""
    if (
        optional_mode in {OptionalMode.REQUIRED, OptionalMode.NULLABLE_VALUE}
        and decision.python_barrier_action is PythonBarrierAction.STRING_VALUE
        and decision.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    ):
        if decision.codegen_action is CodegenAction.CALL_LOCAL_INPUT:
            return BridgeDataAction.COPY_REPRESENTATION, STRING_INPUT_COPY_REASON
        if decision.codegen_action is CodegenAction.COPY_IN_OUT:
            return BridgeDataAction.COPY_REPRESENTATION, STRING_REPLACEMENT_COPY_REASON
    if (
        optional_mode is OptionalMode.REQUIRED
        and decision.python_barrier_action is PythonBarrierAction.STRING_STORAGE
        and decision.native_barrier_action is NativeBarrierAction.PASS_STORAGE_ADDRESS
        and decision.codegen_action is CodegenAction.IN_PLACE_ARGUMENT
    ):
        return BridgeDataAction.COPY_REPRESENTATION, STRING_STORAGE_COPY_REASON
    if (
        optional_mode is OptionalMode.REQUIRED
        and decision.python_barrier_action is PythonBarrierAction.RAW_ADDRESS
        and decision.native_barrier_action is NativeBarrierAction.PASS_RAW_ADDRESS
        and decision.codegen_action is CodegenAction.IN_PLACE_ARGUMENT
    ):
        return BridgeDataAction.COPY_REPRESENTATION, RAW_STRING_ADDRESS_COPY_REASON
    return BridgeDataAction.BLOCKED, None


# Scalar bridge data policy.
def _scalar_argument_bridge_data_action(
    decision: OwnershipDecision,
    optional_mode: OptionalMode,
    value_kind: str | None,
) -> tuple[BridgeDataAction, str | None]:
    """Complete one scalar value, storage, raw-address, or descriptor action."""
    if optional_mode in {OptionalMode.REQUIRED_DESCRIPTOR, OptionalMode.DESCRIPTOR}:
        if value_kind == "pointer":
            return BridgeDataAction.ASSOCIATE_VIEW, None
        if value_kind == "allocatable":
            return (
                BridgeDataAction.COPY_REPRESENTATION,
                "materialize owned Fortran allocatable scalar storage from the binding value",
            )
        return BridgeDataAction.BLOCKED, None
    if optional_mode is OptionalMode.NULLABLE_VALUE:
        return BridgeDataAction.ASSOCIATE_VIEW, None
    if decision.python_barrier_action in {
        PythonBarrierAction.SCALAR_STORAGE,
        PythonBarrierAction.RAW_ADDRESS,
    }:
        return BridgeDataAction.ASSOCIATE_VIEW, None
    if decision.python_barrier_action is PythonBarrierAction.SCALAR_VALUE and decision.native_barrier_action in {
        NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
        NativeBarrierAction.PASS_STORAGE_ADDRESS,
        NativeBarrierAction.PASS_VALUE,
    }:
        return BridgeDataAction.DIRECT_TRANSFER, None
    return BridgeDataAction.BLOCKED, None


def _result_bridge_data_action(
    semantic_type: models.SemanticType,
    *,
    descriptor_kind: str | None = None,
) -> tuple[BridgeDataAction, str | None]:
    """Complete direct result transfer without widening unsupported lanes."""
    if _is_scalar_derived_type(semantic_type):
        return (
            BridgeDataAction.COPY_REPRESENTATION,
            "materialize native derived result in persistent wrapper-owned storage",
        )
    if _is_scalar_descriptor_result_type(semantic_type, descriptor_kind=descriptor_kind):
        return BridgeDataAction.COPY_REPRESENTATION, SCALAR_DESCRIPTOR_RESULT_COPY_REASON
    if native_array_descriptor_kind(semantic_type) == "allocatable":
        return BridgeDataAction.COPY_REPRESENTATION, OWNED_NATIVE_ARRAY_HANDLE_COPY_REASON
    if _is_first_lane_scalar_type(semantic_type):
        return BridgeDataAction.DIRECT_TRANSFER, None
    if _is_phase6_ordinary_array_type(semantic_type):
        return BridgeDataAction.COPY_REPRESENTATION, ORDINARY_ARRAY_RESULT_COPY_REASON
    if _is_fixed_plan_string_result_type(semantic_type):
        return (
            BridgeDataAction.COPY_REPRESENTATION,
            FIXED_STRING_RESULT_COPY_REASON,
        )
    return BridgeDataAction.BLOCKED, None


def _is_scalar_derived_type(semantic_type: models.SemanticType) -> bool:
    """Return whether semantic facts name a concrete rank-zero custom type."""
    return bool(
        int(semantic_type.rank or 0) == 0
        and semantic_type.name not in _PLAN_PRIMITIVE_SCALAR_TYPES | {"String", "Void"}
        and semantic_type.name not in {"Procedure", "Callback", "FunctionPointer", "CFunctionPointer"}
    )


def _is_descriptor_backed_scalar_derived_type(semantic_type: models.SemanticType) -> bool:
    """Return whether scalar derived storage needs unimplemented descriptor policy."""
    return bool(
        _is_scalar_derived_type(semantic_type)
        and (semantic_type.metadata.get("fortran_allocatable") or semantic_type.metadata.get("fortran_pointer"))
    )


def _is_derived_value_array(semantic_type: models.SemanticType) -> bool:
    """Return whether an array contains custom derived values rather than primitives."""
    return bool(
        int(semantic_type.rank or 0) > 0 and semantic_type.name not in _PLAN_PRIMITIVE_SCALAR_TYPES | {"String"}
    )


def _native_result_bridge_data_action(
    semantic_type: models.SemanticType,
    *,
    descriptor_kind: str | None = None,
) -> tuple[BridgeDataAction, str | None]:
    """Complete bridge data movement for one hidden native output slot."""
    if _is_scalar_derived_type(semantic_type):
        return (
            BridgeDataAction.COPY_REPRESENTATION,
            "materialize hidden derived output in persistent wrapper-owned storage",
        )
    if _is_scalar_descriptor_result_type(semantic_type, descriptor_kind=descriptor_kind):
        return BridgeDataAction.COPY_REPRESENTATION, SCALAR_DESCRIPTOR_RESULT_COPY_REASON
    if native_array_descriptor_kind(semantic_type) == "allocatable":
        return BridgeDataAction.COPY_REPRESENTATION, OWNED_NATIVE_ARRAY_HANDLE_COPY_REASON
    if _is_first_lane_scalar_type(semantic_type):
        return BridgeDataAction.DIRECT_TRANSFER, None
    if _is_phase6_ordinary_array_type(semantic_type):
        return BridgeDataAction.COPY_REPRESENTATION, ORDINARY_ARRAY_RESULT_COPY_REASON
    if semantic_type.name == "String" and _character_length(semantic_type) is not None:
        return (
            BridgeDataAction.COPY_REPRESENTATION,
            FIXED_STRING_RESULT_COPY_REASON,
        )
    return BridgeDataAction.BLOCKED, None


def _argument_handoff_mode(decision: OwnershipDecision) -> ArgumentHandoffMode:
    """Return the completed ABI shape consumed by both backends."""
    if decision.kind is ObjectKind.DERIVED_TYPE:
        return ArgumentHandoffMode.OPAQUE_ADDRESS
    if decision.python_barrier_action is PythonBarrierAction.RAW_ADDRESS:
        return ArgumentHandoffMode.OPAQUE_ADDRESS
    if decision.python_barrier_action is PythonBarrierAction.SCALAR_STORAGE:
        return ArgumentHandoffMode.OPAQUE_ADDRESS
    if decision.native_barrier_action is NativeBarrierAction.PASS_NATIVE_DESCRIPTOR:
        return ArgumentHandoffMode.NATIVE_DESCRIPTOR
    if decision.kind is ObjectKind.NUMPY_ARRAY:
        return ArgumentHandoffMode.ARRAY_BUFFER
    if decision.python_barrier_action in {
        PythonBarrierAction.STRING_STORAGE,
        PythonBarrierAction.RAW_ADDRESS,
    }:
        return ArgumentHandoffMode.OPAQUE_ADDRESS
    if decision.kind is ObjectKind.STRING:
        return ArgumentHandoffMode.CHARACTER_BUFFER
    if decision.python_barrier_action in {
        PythonBarrierAction.SCALAR_STORAGE,
        PythonBarrierAction.RAW_ADDRESS,
    }:
        return ArgumentHandoffMode.OPAQUE_ADDRESS
    if decision.native_barrier_action is NativeBarrierAction.PASS_VALUE:
        return ArgumentHandoffMode.VALUE
    return ArgumentHandoffMode.TYPED_REFERENCE


# Ordinary-array handoff policy.
def _array_handoff_policy(semantic_type: models.SemanticType) -> ArrayHandoffPolicy | None:
    """Copy structured buffer or raw-pointee facts into completed wrapper policy."""
    if _is_raw_array_address_type(semantic_type):
        return _raw_array_handoff_policy(semantic_type)
    storage = semantic_type.storage
    array = storage.array if storage is not None else None
    if array is None:
        return None
    if semantic_type.name == "String" and array.category == SCALAR_STORAGE_CATEGORY:
        return None
    assumed_rank = array.category == "assumed_rank"
    rank = _array_handoff_rank(semantic_type, array.rank, assumed_rank)
    if rank is not None and rank <= 0 and not (rank == 0 and array.category == SCALAR_STORAGE_CATEGORY):
        return None
    shape = tuple(str(item) for item in (array.shape or semantic_type.shape))
    axes = tuple(str(item) for item in array.axes)
    return ArrayHandoffPolicy(
        rank=rank,
        shape=shape,
        axes=axes,
        order=_array_handoff_order(array.order, assumed_rank),
        native_order=_array_handoff_native_order(array.order, array.copy_order, assumed_rank),
        contiguous=_array_handoff_contiguous(array.contiguous, assumed_rank, array.category),
        flatten_python_storage=_array_handoff_flattens_python_storage(array),
        flat_axis=_array_handoff_flat_axis(array),
        itemsize=_array_handoff_itemsize(semantic_type),
        category=array.category,
        extent_references=tuple(_array_extent_references(item) for item in shape),
    )


def _array_handoff_rank(
    semantic_type: models.SemanticType,
    storage_rank: int | None,
    assumed_rank: bool,
) -> int | None:
    """Return the concrete rank, leaving assumed-rank selection explicit."""
    if assumed_rank:
        return None
    return int(storage_rank or semantic_type.rank or 0)


def _array_handoff_order(order: str | None, assumed_rank: bool) -> str | None:
    """Default assumed-rank buffers to native Fortran layout."""
    if assumed_rank and order is None:
        return "ORDER_F"
    return order


def _array_handoff_native_order(
    order: str | None,
    copy_order: str | None,
    assumed_rank: bool,
) -> str | None:
    """Return the completed native-copy layout independently of input layout."""
    if assumed_rank and order is None:
        return "ORDER_F"
    return copy_order if copy_order is not None else order


def _array_handoff_contiguous(contiguous: bool | None, assumed_rank: bool, category: str | None) -> bool | None:
    """Default assumed-rank handoff to one contiguous native buffer."""
    if category == SCALAR_STORAGE_CATEGORY and contiguous is None:
        return True
    if assumed_rank and contiguous is None:
        return True
    return contiguous


def _array_handoff_flattens_python_storage(array: models.SemanticArrayContract) -> bool:
    """Return whether Python may flatten a contiguous actual through one flat edge."""
    return bool(array.category == "assumed_size" and _array_handoff_flat_axis(array) is not None)


def _array_handoff_flat_axis(array: models.SemanticArrayContract) -> int | None:
    """Return the concrete flat-edge axis completed by semantic conversion."""
    if array.category != "assumed_size":
        return None
    for axis, dimension in enumerate(array.source_shape):
        if "*" in str(dimension):
            return axis
    return None


def _array_handoff_itemsize(semantic_type: models.SemanticType) -> int | None:
    """Carry fixed character width only for string array elements."""
    if semantic_type.name == "String":
        return _character_length(semantic_type)
    return None


def _is_phase6_ordinary_array_type(semantic_type: models.SemanticType) -> bool:
    """Return whether one type is an ordinary non-descriptor array buffer."""
    if _is_raw_array_address_type(semantic_type):
        return False
    array_policy = _array_handoff_policy(semantic_type)
    if array_policy is None:
        return False
    storage = semantic_type.storage
    array = storage.array if storage is not None else None
    scalar_storage = _is_scalar_storage_array_policy(array_policy)
    supported_element = semantic_type.name in _PLAN_PRIMITIVE_SCALAR_TYPES or (
        semantic_type.name == "String" and array_policy.itemsize is not None and not scalar_storage
    )
    supported_rank = array_policy.rank is None or 1 <= array_policy.rank <= 15 or scalar_storage
    return bool(
        array is not None
        and supported_element
        and supported_rank
        and (array_policy.rank is None or len(array_policy.shape) == array_policy.rank)
        and (array_policy.rank is None or len(array_policy.axes) == array_policy.rank)
        and not array.allocatable
        and not array.pointer
    )


def _is_scalar_storage_array_policy(array_policy: ArrayHandoffPolicy | None) -> bool:
    return bool(
        array_policy is not None and array_policy.rank == 0 and array_policy.category == SCALAR_STORAGE_CATEGORY
    )


def _is_phase6_raw_array_address_type(semantic_type: models.SemanticType) -> bool:
    """Return whether one type is a supported concrete raw array pointee."""
    if not _is_raw_array_address_type(semantic_type):
        return False
    policy = _array_handoff_policy(semantic_type)
    if policy is None or policy.rank is None or not 1 <= policy.rank <= 15:
        return False
    if len(policy.shape) != policy.rank or len(policy.axes) != policy.rank:
        return False
    supported_element = semantic_type.name in _PLAN_PRIMITIVE_SCALAR_TYPES or (
        semantic_type.name == "String" and policy.itemsize is not None
    )
    return supported_element and all(item not in {":", "::Strided", "...", "Flat"} for item in policy.shape)


def _is_raw_array_address_type(semantic_type: models.SemanticType) -> bool:
    """Return whether one positive-rank type carries the public raw-address role."""
    storage = semantic_type.storage
    return bool(
        semantic_type.rank > 0
        and storage is not None
        and storage.kind == "address"
        and storage.metadata.get(ADDRESS_ROLE_METADATA) == ADDRESS_ROLE_RAW
    )


def _raw_array_handoff_policy(semantic_type: models.SemanticType) -> ArrayHandoffPolicy:
    """Complete dense raw-pointee shape and orientation before lowering."""
    rank = int(semantic_type.rank or 0)
    shape = tuple(str(item) for item in semantic_type.shape)
    storage = semantic_type.storage
    array = storage.array if storage is not None else None
    order = array.order if array is not None and array.order is not None else ("ORDER_C" if rank > 1 else None)
    return ArrayHandoffPolicy(
        rank=rank,
        shape=shape,
        axes=("dense",) * rank,
        order=order,
        native_order=order,
        contiguous=True,
        itemsize=_character_length(semantic_type) if semantic_type.name == "String" else None,
        category="raw_address",
        extent_references=tuple(_array_extent_references(item) for item in shape),
    )


def _array_extent_references(expression: str) -> tuple[str, ...]:
    """Return stable scalar names used by one declared extent expression."""
    if expression in {":", "::Strided", "...", "Flat"}:
        return ()
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return ("<invalid>",)
    if not _valid_array_extent_expression(tree):
        return ("<invalid>",)
    return tuple(dict.fromkeys(node.id for node in ast.walk(tree) if isinstance(node, ast.Name)))


def _valid_array_extent_expression(tree: ast.AST) -> bool:
    """Return whether an extent uses only integer arithmetic and scalar names."""
    allowed = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.FloorDiv,
        ast.Div,
        ast.Mod,
        ast.USub,
        ast.UAdd,
    )
    return all(isinstance(node, allowed) and _is_integer_constant(node) for node in ast.walk(tree))


def _is_integer_constant(node: ast.AST) -> bool:
    return not isinstance(node, ast.Constant) or (isinstance(node.value, int) and not isinstance(node.value, bool))


def _array_extent_reference_blockers(
    function: models.SemanticFunction,
    arguments: list[ArgumentPolicy],
    results: tuple[ResultPolicy, ...],
) -> tuple[str, ...]:
    """Require every declared extent name to come from a visible scalar argument."""
    scalar_names = {
        argument.name
        for argument in function.arguments
        if int(argument.semantic_type.rank or 0) == 0
        and (decision := _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)) is not None
        and decision.python_visible
    }
    blockers = []
    for owner in (*arguments, *results):
        if owner.array is None:
            continue
        for axis, references in enumerate(owner.array.extent_references):
            missing = tuple(name for name in references if name not in scalar_names)
            if missing:
                blockers.append(
                    f"array owner {owner.owner_path!r} extent axis {axis} has unavailable scalar references {missing}"
                )
    return tuple(blockers)


def _argument_result_position(function: models.SemanticFunction, python_position: int) -> int | None:
    """Return one visible argument's completed projected result position."""
    for mapping in function.projection:
        if mapping.python_position == python_position and mapping.result_position is not None:
            return int(mapping.result_position)
    return None


def _visible_projected_arguments(function: models.SemanticFunction) -> tuple[models.SemanticArgument, ...]:
    """Return Python-visible arguments whose completed policy projects results."""
    return tuple(
        argument
        for argument in function.arguments
        if (
            (decision := _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)) is not None
            and decision.projects_result
            and decision.python_visible
        )
    )


def _native_name(function: models.SemanticFunction) -> str:
    return str(function.native_name or function.origin.native_name or function.name)


def _native_module(function: models.SemanticFunction, owner_path: str) -> str | None:
    """Return the completed native module scope for non-external procedures."""
    if _is_external(function):
        return None
    return str(function.origin.native_scope or owner_path.split(".", maxsplit=1)[0])


def _native_is_subroutine(function: models.SemanticFunction) -> bool:
    """Return whether the native callable has subroutine call semantics."""
    return function.origin.source_kind == "subroutine" or function.return_type is None


def _is_external(function: models.SemanticFunction) -> bool:
    return bool(function.origin.source_language == "fortran" and function.origin.native_scope is None)


def _argument_native_name(
    function: models.SemanticFunction,
    python_position: int,
    argument: models.SemanticArgument,
) -> str:
    for mapping in function.projection:
        if mapping.python_position == python_position:
            return mapping.native_name or argument.name
    return argument.name
