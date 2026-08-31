"""Immutable backend-neutral records for completed wrapper policy.

This module owns the stable enums, frozen policy records, and cross-stage
reason constants produced by post-IR policy construction and consumed by
wrapper planning and lowering. It contains no semantic policy construction:
those rules remain in :mod:`prik.policy.construction`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from prik.policy.ownership import (
    AssignmentMode,
    CodegenAction,
    NativeBarrierAction,
    ObjectKind,
    OwnershipDecision,
    OwnershipOwner,
    PythonBarrierAction,
    SetterAction,
    StorageMode,
)
from prik.policy.exports import PythonExportPolicy


FIXED_STRING_RESULT_COPY_REASON = "copy fixed-length Fortran character output into C-owned null-terminated storage"
ORDINARY_ARRAY_RESULT_COPY_REASON = "copy non-descriptor Fortran array output into C-owned contiguous storage"
OWNED_NATIVE_ARRAY_HANDLE_COPY_REASON = "materialize native descriptor into persistent wrapper-owned CFI storage"
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
LOGICAL_SCALAR_KIND_COPY_REASON = "adapt a C-interoperable Boolean through storage with the native Fortran logical kind"
LOGICAL_ARRAY_KIND_COPY_REASON = "adapt a one-byte Boolean array through storage with the native Fortran logical kind"


class OptionalMode(str, Enum):
    """Completed ABI behavior for one argument's presence states."""

    REQUIRED = "required"
    REQUIRED_DESCRIPTOR = "required_descriptor"
    NULLABLE_VALUE = "nullable_value"
    DESCRIPTOR = "descriptor"


class NativeEntrypointAction(str, Enum):
    """Completed per-operation route from the binding to native code."""

    DIRECT_C_ABI = "direct_c_abi"
    GENERATED_FORTRAN_ADAPTER = "generated_fortran_adapter"


@dataclass(frozen=True)
class DirectCABITypePolicy:
    """One preserved C declaration type selected before wrapper planning."""

    source_spelling: str | None
    scalar_type_name: str | None
    pointer_depth: int
    qualifiers: tuple[str, ...]
    const: bool
    # Scalar values whose native declaration differs from canonical contract
    # storage are converted at the call boundary. Exact NumPy storage already
    # has the native representation, so its completed decision remains false.
    converts_to_contract_storage: bool = False


@dataclass(frozen=True)
class DirectCABIPolicy:
    """Exact direct-C function ABI facts owned by post-IR policy."""

    calling_convention: str
    result_transport: str
    result: DirectCABITypePolicy | None
    parameters: tuple[DirectCABITypePolicy, ...]


class EntrypointPassingConvention(str, Enum):
    """Completed C-boundary transport for one parameter or result."""

    C_VALUE = "c_value"
    POINTER_REFERENCE = "pointer_reference"
    NULLABLE_POINTER = "nullable_pointer"
    C_DESCRIPTOR_POINTER = "c_descriptor_pointer"
    RUNTIME_HANDLE = "runtime_handle"
    C_FUNCTION_RETURN = "c_function_return"
    OUTPUT_STORAGE = "output_storage"
    BLOCKED = "blocked"


class EntrypointOptionalityAction(str, Enum):
    """Native presence representation, independent of Python defaults."""

    REQUIRED = "required"
    NULL_POINTER = "null_pointer"
    NULL_C_DESCRIPTOR_POINTER = "null_c_descriptor_pointer"
    EXPLICIT_NATIVE_PRESENCE = "explicit_native_presence"
    ADAPTER_SIDE_FORTRAN_OMISSION = "adapter_side_fortran_omission"
    BLOCKED = "blocked"


class EntrypointProjectionAction(str, Enum):
    """Binding-owned materialization for one ordered native-call mapping."""

    ARGUMENT_DEFAULT = "argument_default"
    ARGUMENT_VALUE = "argument_value"
    ARGUMENT_ADDRESS = "argument_address"
    HIDDEN_OUTPUT_STORAGE = "hidden_output_storage"
    TYPED_LITERAL = "typed_literal"
    COMPUTED_LENGTH = "computed_length"
    COMPUTED_PRESENCE = "computed_presence"
    COMPUTED_SIZE = "computed_size"
    COMPUTED_SHAPE = "computed_shape"
    COMPUTED_STRIDE = "computed_stride"
    WORK_STORAGE = "work_storage"
    DESCRIPTOR = "descriptor"
    RUNTIME_HANDLE = "runtime_handle"
    BLOCKED = "blocked"


class ArrayPythonLayout(str, Enum):
    """Completed memory layout one Python array actual must already have.

    Policy selects the constraint; a backend only enforces it. ``ANY_STRIDED``
    states that the contract constrains neither ordering nor contiguity, so the
    caller's own strides reach the native call unchanged.
    """

    ANY_CONTIGUOUS = "any_contiguous"
    C_CONTIGUOUS = "c_contiguous"
    F_CONTIGUOUS = "f_contiguous"
    POSITIVE_STRIDED_F = "positive_strided_f"
    ANY_STRIDED = "any_strided"


class ArgumentHandoffMode(str, Enum):
    """Completed binding-to-bridge ABI shape for one argument."""

    VALUE = "value"
    TYPED_REFERENCE = "typed_reference"
    OPAQUE_ADDRESS = "opaque_address"
    CHARACTER_BUFFER = "character_buffer"
    ARRAY_BUFFER = "array_buffer"
    NATIVE_DESCRIPTOR = "native_descriptor"


class ArgumentConversionPhase(str, Enum):
    """Completed binding conversion schedule for one Python argument."""

    IMMEDIATE = "immediate"
    DEFERRED_REPLACEMENT = "deferred_replacement"


class BridgeDataAction(str, Enum):
    """Completed bridge-side data movement for one boundary value."""

    DIRECT_TRANSFER = "direct_transfer"
    ASSOCIATE_VIEW = "associate_view"
    COPY_REPRESENTATION = "copy_representation"
    BLOCKED = "blocked"


class DirectResultABI(str, Enum):
    """Completed scalar ABI used for one direct native function result."""

    NOT_APPLICABLE = "not_applicable"
    NATIVE_SCALAR = "native_scalar"
    LOGICAL_LOW_BIT_INT8 = "logical_low_bit_int8"


class ArrayWritebackABI(str, Enum):
    """Completed post-call element ABI for one mutable ordinary array."""

    NOT_APPLICABLE = "not_applicable"
    NATIVE_ARRAY = "native_array"
    LOGICAL_LOW_BIT_INT8 = "logical_low_bit_int8"


class ScalarLogicalABI(str, Enum):
    """Completed scalar logical adaptation between the C and native dummies."""

    NOT_APPLICABLE = "not_applicable"
    C_BOOL = "c_bool"
    NATIVE_KIND_COPY = "native_kind_copy"


class ArrayLogicalABI(str, Enum):
    """Completed Boolean-array adaptation between NumPy and native storage."""

    NOT_APPLICABLE = "not_applicable"
    C_BOOL_VIEW = "c_bool_view"
    NATIVE_KIND_COPY = "native_kind_copy"


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
    NATIVE_CONSTANT_VALUE = "native_constant_value"
    NATIVE_CONSTANT_ARRAY_VALUE = "native_constant_array_value"
    DIRECT_VALUE = "direct_value"
    CHARACTER_VALUE = "character_value"
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


class DeclarationCallableAction(str, Enum):
    """Completed bridge mechanism for one declaration-expression function."""

    MODULE_IMPORT = "module_import"
    STANDALONE_PROCEDURE = "standalone_procedure"


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
    bind_c: bool
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
    destructors: tuple[str, ...]
    bind_c: bool
    supported: bool
    blockers: tuple[str, ...] = ()
    abstract: bool = False
    deferred_bindings: tuple[str, ...] = ()


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
    call: ClassMethodPolicy | None
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
    """One completed exact-type predicate in an overload signature.

    ``builtin_scalar_family`` is ``bool``, ``int``, ``float``, or ``complex``
    only when reflected dispatch admits that exact Python builtin beside the
    recorded NumPy scalar type. ``None`` keeps dispatch NumPy-exact.
    """

    python_name: str
    kind: OverloadMatchKind
    optional: bool
    semantic_type_name: str
    rank: int
    derived_type_identity: tuple[str, str] | None
    builtin_scalar_family: str | None = None


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


class CharacterLocalRelease(str, Enum):
    """Completed release responsibility for one adapter-local character value.

    ``NONE`` covers a plain or ``allocatable`` local, which the compiler frees
    when the adapter returns.  A ``pointer`` local is storage the adapter itself
    allocated, so it names when the adapter must free it again.
    """

    NONE = "none"
    DEALLOCATE = "deallocate"
    DEALLOCATE_IF_RETAINED = "deallocate_if_retained"


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


class NativeArrayDefaultConstruction(str, Enum):
    """Completed storage path for a runtime-constructed empty descriptor."""

    NONE = "none"
    FACT_PACKED_EMPTY = "fact_packed_empty"
    LAZY_OWNED_DESCRIPTOR = "lazy_owned_descriptor"


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
    ASSOCIATE = "associate"
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
    result_position: int | None
    semantic_type_name: str
    rank: int
    character_length: int | None = None
    # A visible message names a buffer the caller supplied, so the binding
    # reads it through the argument instead of a projected native output.
    python_position: int | None = None


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
    character_length: int | None = None
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
    python_layout: ArrayPythonLayout
    minimum_rank: int
    maximum_rank: int
    flatten_python_storage: bool = False
    flat_axis: int | None = None
    itemsize: int | None = None
    # Whether the buffer holds characters. A character array always reports its
    # width at runtime, so the role exists even when ``itemsize`` is assumed.
    character: bool = False
    category: str | None = None
    extent_references: tuple[tuple[str, ...], ...] = ()
    extent_reference_roles: tuple[tuple[str, ...], ...] = ()
    extent_callable_references: tuple[tuple[str, ...], ...] = ()
    extent_callable_roles: tuple[tuple[str, ...], ...] = ()
    extent_evaluation: tuple[str, ...] = ()
    extent_blockers: tuple[tuple[str, ...], ...] = ()
    display_shape: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProcedurePrototypeArgumentPolicy:
    """Exact native dummy characteristics shared by every prototype use."""

    owner_path: str
    name: str
    semantic_type_name: str
    rank: int
    passed_by_value: bool
    intent: str | None
    character_length: int | None
    array: ArrayHandoffPolicy | None
    derived_type_identity: tuple[str, str] | None


@dataclass(frozen=True)
class ProcedurePrototypeResultPolicy:
    """Exact native function-result characteristics for one prototype."""

    owner_path: str
    semantic_type_name: str
    rank: int
    character_length: int | None
    array: ArrayHandoffPolicy | None
    derived_type_identity: tuple[str, str] | None


@dataclass(frozen=True)
class ProcedurePrototypePolicy:
    """One reusable exact signature, independent of its eventual entity role."""

    owner_path: str
    name: str
    identity: str
    pure: bool
    source_language: str | None
    native_abi: str | None
    arguments: tuple[ProcedurePrototypeArgumentPolicy, ...]
    result: ProcedurePrototypeResultPolicy | None


@dataclass(frozen=True)
class DeclarationCallablePolicy:
    """One native entity used while evaluating declared extents."""

    owner_path: str
    source_name: str
    native_name: str
    native_scope: str | None
    symbolic_role: str
    expression_token: str
    action: DeclarationCallableAction
    prototype: ProcedurePrototypePolicy | None = None
    blockers: tuple[str, ...] = ()


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
class NativeArrayDefaultHandlePolicy:
    """Completed lifecycle for a caller-created empty descriptor handle."""

    construction: NativeArrayDefaultConstruction
    descriptor_ownership: NativeArrayDescriptorOwnership | None
    release: NativeArrayRelease
    destroy_behavior: NativeArrayDestroyBehavior
    operations: tuple[NativeArrayOperation, ...]


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
    default_handle: NativeArrayDefaultHandlePolicy


@dataclass(frozen=True)
class CharacterLocalPolicy:
    """Completed adapter-local storage for one scalar character value.

    The C ABI is the same for every scalar character argument: a byte buffer
    and a length.  What differs is the Fortran local the adapter must build
    before the original dummy accepts it, so this records the attribute and
    length kind that local carries and who releases it.
    """

    descriptor_kind: NativeArrayDescriptorKind | None
    deferred_length: bool
    release: CharacterLocalRelease


@dataclass(frozen=True)
class ScalarDescriptorResultPolicy:
    """Completed nullable rank-zero descriptor result copy contract.

    ``may_be_unallocated`` marks a result whose storage the native procedure is
    not obliged to establish, so reading it directly is not permitted and the
    value has to be moved out through a dummy that can test allocation first.
    """

    descriptor_kind: NativeArrayDescriptorKind
    runtime_length: bool
    nullable: bool
    copy_reason: str
    release_owner: OwnershipOwner
    may_be_unallocated: bool = False


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
    intent: str | None
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
    prototype: ProcedurePrototypePolicy
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
    scalar_logical_abi: ScalarLogicalABI
    scalar_native_type: str | None
    array_logical_abi: ArrayLogicalABI
    array_native_type: str | None
    array_copy_in: bool
    array_copy_out: bool
    array_writeback_abi: ArrayWritebackABI
    optional: bool
    optional_mode: OptionalMode
    conversion_phase: ArgumentConversionPhase
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
    character_local: CharacterLocalPolicy | None = None
    array: ArrayHandoffPolicy | None = None
    native_array_actual: NativeArrayActualPolicy | None = None
    native_array_handle: NativeArrayHandleWrapperPolicy | None = None
    derived: DerivedHandoffPolicy | None = None
    derived_call: DerivedCallPolicy | None = None
    callback: CallbackHandoffPolicy | None = None
    polymorphic: PolymorphicDispatchPolicy | None = None
    transformations: tuple[TransformationPolicy, ...] = ()
    entrypoint_passing: EntrypointPassingConvention = EntrypointPassingConvention.BLOCKED
    entrypoint_optionality: EntrypointOptionalityAction = EntrypointOptionalityAction.BLOCKED
    entrypoint_pass_character_length: bool = False
    entrypoint_pass_array_metadata: bool = False
    entrypoint_pass_descriptor_presence: bool = False
    entrypoint_pass_derived_transaction: bool = False
    entrypoint_pass_callback_parameter: bool = False
    native_storage_c_type: str | None = None
    native_array_element_c_type: str | None = None
    character_allows_embedded_nul: bool = False

    @property
    def projects_character_descriptor_update(self) -> bool:
        """Report whether this argument returns its replaced value as a projected result.

        ``character_local`` carries a descriptor kind only for a call-local
        ``allocatable`` or ``pointer`` character input, so an input that also
        occupies a Python result position is the update lane.  Its output
        travels as one descriptor-backed result rather than as argument
        writeback.
        """
        return bool(
            self.character_local is not None
            and self.character_local.descriptor_kind is not None
            and self.projects_result
        )


@dataclass(frozen=True)
class ResultPolicy:
    """Completed wrapper policy for one native result.

    ``updates_argument`` marks the one shape whose native output storage is also
    a Python-visible argument: a ``character(len=:), allocatable`` update whose
    caller supplies a ``str`` and receives the reallocated value.  Its producer
    is the argument's own native call slot, so stages that pair a hidden output
    with a dedicated result slot must consult this fact instead.
    """

    owner_path: str
    semantic_type_name: str
    rank: int
    direct_result_abi: DirectResultABI
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
    # Declared by a ``Hidden`` slot: the native call produces it exactly like
    # any other output, but the binding never builds a Python value from it.
    python_returned: bool = True
    native_name: str | None = None
    native_position: int | None = None
    result_position: int = 0
    native_array_handle: NativeArrayHandleWrapperPolicy | None = None
    scalar_descriptor: ScalarDescriptorResultPolicy | None = None
    derived: DerivedHandoffPolicy | None = None
    transformations: tuple[TransformationPolicy, ...] = ()
    entrypoint_passing: EntrypointPassingConvention = EntrypointPassingConvention.BLOCKED
    updates_argument: bool = False


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
    native_scalar_c_type: str | None = None
    scalar_logical_abi: ScalarLogicalABI = ScalarLogicalABI.NOT_APPLICABLE
    scalar_native_type: str | None = None
    array_logical_abi: ArrayLogicalABI = ArrayLogicalABI.NOT_APPLICABLE
    array_native_type: str | None = None
    array_copy_in: bool = False
    array_copy_out: bool = False
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
    projection_action: EntrypointProjectionAction = EntrypointProjectionAction.BLOCKED
    entrypoint_passing: EntrypointPassingConvention = EntrypointPassingConvention.BLOCKED
    entrypoint_optionality: EntrypointOptionalityAction = EntrypointOptionalityAction.BLOCKED


@dataclass(frozen=True)
class FunctionWrapperPolicy:
    """Completed wrapper-facing contract for one semantic function.

    ``build_function_wrapper_policy`` constructs this record after ownership
    policy completion.  Wrapper planning consumes the ordered arguments,
    results, native-call slots, and lifecycle actions; a policy with
    ``supported=False`` must be rejected using its ``blockers``.
    """

    owner_path: str
    python_exports: tuple[PythonExportPolicy, ...]
    native_name: str
    native_invocation: NativeInvocationKind
    native_operator: str | None
    standalone: bool
    external_declaration: ExternalDeclarationMode
    native_module: str | None
    native_is_subroutine: bool
    release_gil: bool
    status_error: NativeStatusErrorPolicy | None
    class_call: ClassMethodPolicy | None
    module_export: bool
    supported: bool
    arguments: tuple[ArgumentPolicy, ...] = ()
    results: tuple[ResultPolicy, ...] = ()
    native_call_slots: tuple[NativeCallSlotPolicy, ...] = ()
    declaration_callables: tuple[DeclarationCallablePolicy, ...] = ()
    blockers: tuple[str, ...] = ()
    writeback_actions: tuple[LifecyclePolicy, ...] = ()
    cleanup_actions: tuple[LifecyclePolicy, ...] = ()
    release_actions: tuple[LifecyclePolicy, ...] = ()
    entrypoint_action: NativeEntrypointAction | None = None
    entrypoint_symbol: str = ""
    entrypoint_diagnostics: tuple[str, ...] = ()
    direct_c_abi: DirectCABIPolicy | None = None
    # A positional-only surface takes no keyword arguments, so its argument
    # names are not part of the Python API. Policy renames them to ``arg0``
    # upward, because a native declaration's parameter names are an
    # implementation detail that need not agree across targets.
    accepts_keyword_arguments: bool = True


if __name__ == "__main__":
    example_array = ArrayHandoffPolicy(
        rank=2,
        shape=("rows", "columns"),
        axes=("rows", "columns"),
        order="F",
        native_order="F",
        contiguous=True,
        python_layout=ArrayPythonLayout.F_CONTIGUOUS,
        minimum_rank=2,
        maximum_rank=2,
    )
    example_lifecycle = LifecyclePolicy(
        owner_path="math.scale.values",
        phase=WritebackPhase.COPY_OUT,
        source_role="argument",
        codegen_action=CodegenAction.COPY_IN_OUT,
        semantic_type_name="Float64",
        result_position=0,
        object_kind=ObjectKind.NUMPY_ARRAY,
    )

    print(f"Array policy: rank={example_array.rank}, shape={example_array.shape}, order={example_array.order}")
    print(
        f"Lifecycle policy: {example_lifecycle.phase.value} "
        f"{example_lifecycle.operation.value} via {example_lifecycle.codegen_action.value}"
    )
    try:
        example_lifecycle.source_role = "result"
    except AttributeError:
        print("Completed record mutation rejected: True")
