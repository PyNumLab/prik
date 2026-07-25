"""Editable wrapper-plan records for the isolated wrapper-plan route."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from x2py.semantics.ownership import (
    AssignmentMode,
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    ObjectKind,
    OwnershipOwner,
    PythonBarrierAction,
    SetterAction,
    StorageMode,
    TransferMode,
)
from x2py.semantics.wrapper_policy import (
    ArgumentHandoffMode,
    BridgeDataAction,
    CallbackABIKind,
    CallbackFatalAction,
    CallbackGILAction,
    CallbackLifecycleAction,
    CallbackResultAction,
    CallbackThreadAction,
    CallbackTransferAction,
    ClassConstructorKind,
    ClassInvocationKind,
    ClassMethodKind,
    OverloadMatchKind,
    ClassRegistrationAction,
    ConstructionLifecycleAction,
    DerivedActualAccess,
    DerivedCallAction,
    DerivedDummyCategory,
    DerivedObjectOrigin,
    DerivedObjectStorage,
    DerivedFieldAccessMechanism,
    DerivedNativeHandoff,
    LifecycleOperation,
    DerivedOwnerRetention,
    DerivedRelease,
    DerivedTargetLifetime,
    DerivedWriteback,
    ExternalDeclarationMode,
    ModuleGetterAction,
    ModuleObjectAccessMechanism,
    NativeArrayDescriptorInterop,
    NativeArrayDescriptorKind,
    NativeArrayDescriptorOwnership,
    NativeArrayDestroyBehavior,
    NativeArrayExtractionAction,
    NativeArrayGetterBehavior,
    NativeArrayHandleKind,
    NativeArrayHandleOrigin,
    NativeArrayOperation,
    NativeArrayOutputProjection,
    NativeArrayResultAllocation,
    NativeArrayOwnerRetention,
    NativeArrayRelease,
    NativeArraySourceKind,
    NativeDescriptorHandoffABI,
    NativeInvocationKind,
    OptionalMode,
    PythonExceptionKind,
    TransformationAction,
    TransformationLayer,
    WritebackPhase,
)
from x2py.stage_values import StageRecord


class DatatypeFamily(Enum):
    """Backend-relevant datatype family copied from semantic type facts."""

    BOOL = "bool"
    INTEGER = "integer"
    REAL = "real"
    COMPLEX = "complex"
    STRING = "string"
    DERIVED = "derived"
    CALLBACK = "callback"


@dataclass
class DerivedHandoffPlan(StageRecord):
    """Editable scalar-derived identity, origin, and lifetime facet."""

    type_name: str
    type_identity: tuple[str, str]
    backend_symbol: str
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


@dataclass
class DerivedCallCasePlan(StageRecord):
    """Editable exhaustive actual-storage/dummy-form compatibility cell."""

    actual_storage: DerivedObjectStorage
    action: DerivedCallAction
    access: DerivedActualAccess
    abi_code: int
    requires_present: bool
    target_lifetime: DerivedTargetLifetime
    failure_kind: str | None
    failure_message: str | None


@dataclass
class DerivedCallPlan(StageRecord):
    """Dummy-driven scalar-derived matrix and ordered transaction facts."""

    dummy_category: DerivedDummyCategory
    cases: tuple[DerivedCallCasePlan, ...]
    writeback: DerivedWriteback
    status_role: str
    origin_identity_role: str
    acquisition_order: int
    cleanup_order: int


@dataclass
class DerivedFieldPlan(StageRecord):
    """One field policy subordinate to its owning derived type."""

    owner_path: str
    name: str
    native_name: str
    semantic_type_name: str
    string_element: bool
    rank: int
    object_kind: ObjectKind
    access: DerivedFieldAccessMechanism
    getter_action: CodegenAction
    setter_action: SetterAction
    native_assignment: AssignmentMode
    owner_retention: DerivedOwnerRetention
    character_length: int | None
    getter_role: str
    setter_role: str | None
    array: ArrayHandoffPlan | None = None
    native_array_handle: NativeArrayHandlePlan | None = None
    derived: DerivedHandoffPlan | None = None
    docstring: str = ""


@dataclass
class DerivedMemberPathPlan(StageRecord):
    """One typed finite module-proxy member path."""

    path: tuple[str, ...]
    native_path: tuple[str, ...]
    declaring_type_name: str
    declaring_type_identity: tuple[str, str]
    field: DerivedFieldPlan


@dataclass
class DerivedTypePlan(StageRecord):
    """One namespace-owned opaque derived runtime type definition."""

    owner_path: str
    type_name: str
    type_identity: tuple[str, str]
    backend_symbol: str
    native_type_name: str
    native_scope: str
    python_names: tuple[str, ...]
    fields: tuple[DerivedFieldPlan, ...]
    finalizers: tuple[str, ...]
    bind_c: bool
    sequence: bool


@dataclass
class ConstructorFieldPlan(StageRecord):
    """One editable keyword-only generated-constructor field."""

    owner_path: str
    name: str
    default_value: str | None
    setter_action: SetterAction


@dataclass
class ConstructorPlan(StageRecord):
    """Editable constructor selection and owned-instance lifecycle."""

    kind: ClassConstructorKind
    fields: tuple[ConstructorFieldPlan, ...]
    target_owner_path: str | None
    overload_name: str | None
    lifecycle: tuple[ConstructionLifecycleAction, ...]
    rejection_message: str | None = None
    target: FunctionPlan | None = None
    overload: OverloadPlan | None = None
    docstring: str = ""


@dataclass
class ClassMethodPlan(StageRecord):
    """One class descriptor linked to an ordinary editable function plan."""

    owner_path: str
    python_name: str
    kind: ClassMethodKind
    passed_object_position: int | None
    public: bool
    function: FunctionPlan
    docstring: str = ""


@dataclass
class OverloadArgumentMatchPlan(StageRecord):
    """One editable exact-type predicate for overload dispatch."""

    python_name: str
    kind: OverloadMatchKind
    optional: bool
    semantic_type_name: str
    rank: int
    derived_type_identity: tuple[str, str] | None
    accept_builtin_scalar: bool = False


@dataclass
class OverloadPlan(StageRecord):
    """One exact-match overload and its concrete editable candidates."""

    owner_path: str
    python_name: str
    kind: str
    candidates: tuple[FunctionPlan, ...]
    candidate_matches: tuple[tuple[OverloadArgumentMatchPlan, ...], ...]
    candidate_passed_objects: tuple[bool, ...]
    unsupported_extra_argument_message: str | None = None
    identity_receiver_shortcut: bool = False
    docstring: str = ""


@dataclass
class ClassSurfacePlan(StageRecord):
    """Namespace-owned generated class composed over a derived type plan."""

    owner_path: str
    type_identity: tuple[str, str]
    python_names: tuple[str, ...]
    base_identities: tuple[tuple[str, str], ...]
    constructor: ConstructorPlan
    methods: tuple[ClassMethodPlan, ...]
    overloads: tuple[OverloadPlan, ...]
    registration: tuple[ClassRegistrationAction, ...]
    docstring: str = ""


@dataclass
class DerivedModuleObjectPlan(StageRecord):
    """Live derived module-object access subordinate to module state."""

    handoff: DerivedHandoffPlan
    access: ModuleObjectAccessMechanism
    replacement: SetterAction
    member_paths: tuple[DerivedMemberPathPlan, ...]


@dataclass
class ArrayHandoffPlan(StageRecord):
    """Editable array storage or raw-pointee layout and ABI roles."""

    rank: int | None
    shape: tuple[str, ...]
    axes: tuple[str, ...]
    order: str | None
    native_order: str | None
    contiguous: bool | None
    flatten_python_storage: bool
    flat_axis: int | None
    itemsize: int | None
    category: str | None
    data_role: str
    extent_roles: tuple[str, ...]
    extent_reference_roles: tuple[tuple[str, ...], ...] = ()
    upper_bound_roles: tuple[str, ...] = ()
    stride_roles: tuple[str, ...] = ()
    runtime_rank_role: str | None = None
    itemsize_role: str | None = None


@dataclass
class NativeArrayActualPlan(StageRecord):
    """Editable accepted-source facts for the ordinary array-buffer ABI."""

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


@dataclass
class NativeDescriptorHandoffPlan(StageRecord):
    """Editable descriptor ABI roles subordinate to one native handle."""

    abi: NativeDescriptorHandoffABI
    descriptor_pointer_role: str | None
    base_addr_role: str | None
    elem_len_role: str | None
    rank_role: str | None
    lower_bound_roles: tuple[str, ...]
    extent_roles: tuple[str, ...]
    stride_multiplier_roles: tuple[str, ...]
    presence_role: str | None
    owner_storage_role: str | None
    operation_roles: tuple[tuple[NativeArrayOperation, str], ...]


@dataclass
class NativeArrayHandlePlan(StageRecord):
    """One typed editable native-array handle policy and descriptor handoff."""

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
    array: ArrayHandoffPlan
    handoff: NativeDescriptorHandoffPlan


@dataclass
class ScalarDescriptorResultPlan(StageRecord):
    """Editable nullable rank-zero descriptor result copy facts."""

    descriptor_kind: NativeArrayDescriptorKind
    runtime_length: bool
    nullable: bool
    copy_reason: str
    release_owner: OwnershipOwner
    presence_role: str


@dataclass
class TransformationPlan(StageRecord):
    """One explicitly layer-owned transformation subordinate to a transfer."""

    phase: WritebackPhase
    layer: TransformationLayer
    action: TransformationAction
    source_representation: str
    target_representation: str
    reason: str


@dataclass
class BindingStatusErrorPlan(StageRecord):
    """Binding-owned post-call native status projection."""

    status_role: str
    message_role: str | None
    success: int
    exception_kind: PythonExceptionKind


@dataclass
class BindingModulePlan(StageRecord):
    """Binding-facing module facts."""

    owner_path: str


@dataclass
class BridgeModulePlan(StageRecord):
    """Bridge-facing module facts."""

    owner_path: str


@dataclass
class BindingModuleVariablePlan(StageRecord):
    """Python module-attribute behavior for one state value."""

    python_names: tuple[str, ...]
    getter_action: ModuleGetterAction
    setter_action: SetterAction
    initializer: Any
    constant_value: Any


@dataclass
class BridgeModuleVariablePlan(StageRecord):
    """Native module-variable access behavior selected by completed policy."""

    native_name: str
    native_module: str
    getter_action: ModuleGetterAction
    native_assignment: AssignmentMode
    descriptor_kind: str | None
    getter_role: str | None
    setter_role: str | None


@dataclass
class ModuleVariablePlan(StageRecord):
    """One concise shared module-variable plan."""

    owner_path: str
    symbol_name: str
    semantic_type_name: str
    datatype_family: DatatypeFamily
    binding: BindingModuleVariablePlan
    bridge: BridgeModuleVariablePlan
    array: ArrayHandoffPlan | None
    native_array_handle: NativeArrayHandlePlan | None
    derived: DerivedModuleObjectPlan | None = None
    docstring: str = ""


@dataclass
class BindingFunctionPlan(StageRecord):
    """Binding-facing function facts."""

    python_name: str
    docstring: str
    hold_gil: bool
    status_error: BindingStatusErrorPlan | None
    public: bool = True


@dataclass
class BridgeFunctionPlan(StageRecord):
    """Bridge-facing function facts."""

    native_name: str
    native_invocation: NativeInvocationKind
    native_operator: str | None
    external: bool
    external_declaration: ExternalDeclarationMode
    native_module: str | None
    native_is_subroutine: bool


@dataclass
class ClassCallPlan(StageRecord):
    """Native receiver and invocation facts for one class-owned call."""

    kind: ClassMethodKind
    passed_object_position: int | None
    invocation: ClassInvocationKind
    type_bound_name: str | None


@dataclass
class BindingArgumentPlan(StageRecord):
    """Python input conversion and binding-to-bridge handoff facts."""

    python_name: str
    python_action: PythonBarrierAction
    codegen_action: CodegenAction
    handoff_role: str
    optional_mode: OptionalMode
    nullable: bool
    writable: bool
    descriptor_boundary: bool
    length_handoff_role: str | None = None


@dataclass
class BridgeArgumentPlan(StageRecord):
    """Bridge ABI and native argument conversion facts."""

    native_name: str
    native_action: NativeBarrierAction
    codegen_action: CodegenAction
    handoff_mode: ArgumentHandoffMode
    data_action: BridgeDataAction
    copy_reason: str | None
    abi_position: int
    handoff_role: str
    optional_mode: OptionalMode
    presence_role: str | None
    length_handoff_role: str | None = None
    descriptor_output_role: str | None = None
    descriptor_output_presence_role: str | None = None


@dataclass
class BindingResultPlan(StageRecord):
    """Binding-facing result projection facts."""

    codegen_action: CodegenAction
    python_action: PythonBarrierAction
    python_result_role: str


@dataclass
class BridgeResultPlan(StageRecord):
    """Bridge-facing result production facts."""

    codegen_action: CodegenAction
    native_action: NativeBarrierAction
    data_action: BridgeDataAction
    copy_reason: str | None
    native_result_role: str
    native_name: str | None
    abi_position: int | None


@dataclass
class BindingLifecyclePlan(StageRecord):
    """Binding-owned lifecycle action facts."""

    source_role: str
    codegen_action: CodegenAction
    semantic_type_name: str
    datatype_family: DatatypeFamily
    result_position: int
    python_result_role: str | None
    operation: LifecycleOperation


@dataclass
class BridgeLifecyclePlan(StageRecord):
    """Bridge-owned lifecycle action facts."""

    source_role: str


@dataclass
class NativeCallSlotPlan(StageRecord):
    """One ordered ABI slot referenced by its owning transfer when applicable."""

    owner_path: str
    native_position: int
    source_kind: str
    python_position: int | None
    python_name: str | None
    native_name: str
    value_kind: str
    symbolic_role: str
    native_action: NativeBarrierAction
    codegen_action: CodegenAction
    bridge_data_action: BridgeDataAction
    bridge_copy_reason: str | None
    object_kind: ObjectKind | None
    literal_type: str | None = None
    literal_value: Any = None
    result_position: int | None = None
    semantic_type_name: str | None = None
    datatype_family: DatatypeFamily | None = None
    character_length: int | None = None
    array: ArrayHandoffPlan | None = None
    native_array_handle: NativeArrayHandlePlan | None = None
    scalar_descriptor: ScalarDescriptorResultPlan | None = None
    derived: DerivedHandoffPlan | None = None


@dataclass
class PolymorphicVariantPlan(StageRecord):
    """One concrete class accepted by an enumerated polymorphic input."""

    type_identity: tuple[str, str]
    backend_symbol: str
    python_name: str
    abi_code: int


@dataclass
class PolymorphicDispatchPlan(StageRecord):
    """Stable concrete-type dispatch for one scalar input dummy."""

    owner_path: str
    variants: tuple[PolymorphicVariantPlan, ...]


@dataclass
class CallbackTransferPlan(StageRecord):
    """One typed native-to-Python transfer inside a callback adapter."""

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
    array: ArrayHandoffPlan | None
    derived_type_identity: tuple[str, str] | None
    derived_backend_symbol: str | None
    data_role: str
    extent_roles: tuple[str, ...]
    length_role: str | None


@dataclass
class CallbackResultPlan(StageRecord):
    """Typed callback result conversion and its optional transfer."""

    transfer: CallbackTransferPlan | None
    action: CallbackResultAction


@dataclass
class CallbackHandoffPlan(StageRecord):
    """Call-scoped callback context, symbols, transfers, and fatal contract."""

    owner_path: str
    prototype_name: str
    prototype_module: str | None
    declaration_mode: ExternalDeclarationMode
    context_type_symbol: str
    context_current_symbol: str
    adapter_symbol: str
    trampoline_symbol: str
    abort_symbol: str
    arguments: tuple[CallbackTransferPlan, ...]
    result: CallbackResultPlan
    lifecycle: tuple[CallbackLifecycleAction, ...]
    thread_action: CallbackThreadAction
    gil_actions: tuple[CallbackGILAction, ...]
    fatal_action: CallbackFatalAction


@dataclass
class ArgumentTransferPlan(StageRecord):
    """One shared Python-to-native transfer, including its native-call slot."""

    owner_path: str
    python_position: int
    native_position: int
    semantic_type_name: str
    datatype_family: DatatypeFamily
    character_length: int | None
    object_kind: ObjectKind
    ownership_owner: OwnershipOwner
    transfer_mode: TransferMode
    destruction_policy: DestructionPolicy
    storage_mode: StorageMode
    boundary_storage_mode: StorageMode
    nullable: bool
    mutates_native: bool
    projects_result: bool
    python_visible: bool
    result_position: int | None
    array: ArrayHandoffPlan | None
    native_array_actual: NativeArrayActualPlan | None
    native_array_handle: NativeArrayHandlePlan | None
    derived: DerivedHandoffPlan | None
    derived_call: DerivedCallPlan | None
    callback: CallbackHandoffPlan | None
    polymorphic: PolymorphicDispatchPlan | None
    binding: BindingArgumentPlan
    bridge: BridgeArgumentPlan
    native_call_slot: NativeCallSlotPlan
    transformations: tuple[TransformationPlan, ...] = ()


@dataclass
class ResultPlan(StageRecord):
    """One native-to-Python transfer and its hidden ABI slot when applicable."""

    owner_path: str
    semantic_type_name: str
    datatype_family: DatatypeFamily
    source_kind: str
    result_position: int
    character_length: int | None
    object_kind: ObjectKind
    ownership_owner: OwnershipOwner
    transfer_mode: TransferMode
    destruction_policy: DestructionPolicy
    storage_mode: StorageMode
    boundary_storage_mode: StorageMode
    nullable: bool
    array: ArrayHandoffPlan | None
    native_array_handle: NativeArrayHandlePlan | None
    binding: BindingResultPlan
    bridge: BridgeResultPlan
    native_call_slot: NativeCallSlotPlan | None = None
    scalar_descriptor: ScalarDescriptorResultPlan | None = None
    derived: DerivedHandoffPlan | None = None
    transformations: tuple[TransformationPlan, ...] = ()


@dataclass
class LifecycleActionPlan(StageRecord):
    """One transfer-owned action kept in function-wide execution order."""

    owner_path: str
    phase: WritebackPhase
    source_role: str
    codegen_action: CodegenAction
    semantic_type_name: str
    datatype_family: DatatypeFamily
    object_kind: ObjectKind
    result_position: int
    operation: LifecycleOperation
    binding: BindingLifecyclePlan | None = None
    bridge: BridgeLifecyclePlan | None = None


@dataclass
class FunctionPlan(StageRecord):
    """Stable orchestration plus ordered ABI and lifecycle transfer indexes."""

    owner_path: str
    symbol_name: str
    binding: BindingFunctionPlan
    bridge: BridgeFunctionPlan
    class_call: ClassCallPlan | None
    arguments: tuple[ArgumentTransferPlan, ...]
    results: tuple[ResultPlan, ...]
    native_call_slots: tuple[NativeCallSlotPlan, ...]
    available_roles: tuple[str, ...]
    writeback_actions: tuple[LifecycleActionPlan, ...] = ()
    cleanup_actions: tuple[LifecycleActionPlan, ...] = ()
    release_actions: tuple[LifecycleActionPlan, ...] = ()


@dataclass
class NamespacePlan(StageRecord):
    """One Python namespace containing directly exported wrapper owners."""

    owner_path: str
    python_path: tuple[str, ...]
    functions: tuple[FunctionPlan, ...] = ()
    variables: tuple[ModuleVariablePlan, ...] = ()
    derived_types: tuple[DerivedTypePlan, ...] = ()
    classes: tuple[ClassSurfacePlan, ...] = ()
    overloads: tuple[OverloadPlan, ...] = ()
    docstring: str = ""


@dataclass
class ModulePlan(StageRecord):
    """One shared generation-unit plan containing an explicit namespace tree."""

    owner_path: str
    binding: BindingModulePlan
    bridge: BridgeModulePlan
    namespaces: tuple[NamespacePlan, ...]
    required_headers: tuple[str, ...] = ()


@dataclass
class WrapperPlanDiagnostic(StageRecord):
    """One owner-path diagnostic produced before backend generation."""

    owner_path: str
    code: str
    message: str
