"""Typed, editable records shared by wrapper planning and direct generation.

``WrapperPlanner`` constructs these records only after post-IR policy has made
every ownership, transfer, and projection decision. The generator then
validates and freezes the same object graph before binding or bridge lowering.
This module deliberately models those completed facts; it never infers policy
from a datatype, native ``intent``, shape, or backend-local condition.

Records appear in plan-tree order: shared vocabulary; derived and class
surfaces; array and descriptor facets; module and procedure views; callback
and transfer records; then module-level orchestration. Consumers normally use
the ``ModulePlan`` root returned by :class:`prik.planning.WrapperPlanner`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from prik.policy.ownership import (
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
from prik.policy.models import (
    ArgumentConversionPhase,
    ArgumentHandoffMode,
    ArrayLogicalABI,
    ArrayWritebackABI,
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
    DirectResultABI,
    DeclarationCallableAction,
    ExternalDeclarationMode,
    ModuleGetterAction,
    ModuleObjectAccessMechanism,
    NativeArrayDescriptorInterop,
    NativeArrayDescriptorKind,
    NativeArrayDescriptorOwnership,
    NativeArrayDefaultConstruction,
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
    ScalarLogicalABI,
    OptionalMode,
    PythonExceptionKind,
    TransformationAction,
    TransformationLayer,
    WritebackPhase,
    NativeEntrypointAction,
    EntrypointPassingConvention,
    EntrypointOptionalityAction,
    EntrypointProjectionAction,
)
from prik.utilities.stage_values import StageRecord


# ============================================================================
# Shared plan vocabulary
# ============================================================================


class DatatypeFamily(Enum):
    """Classify a completed value for the datatype-specific validation route.

    The planner copies this coarse family from semantic type facts onto
    transfer records. Validators and backend dispatch use it alongside the
    already-completed action selectors; it does not by itself choose policy.
    """

    BOOL = "bool"
    INTEGER = "integer"
    REAL = "real"
    COMPLEX = "complex"
    STRING = "string"
    DERIVED = "derived"
    CALLBACK = "callback"


class NativeEntrypointABIValueKind(Enum):
    """Classify one value in a generated support procedure's C ABI."""

    VOID = "void"
    BOOL = "bool"
    INT = "int"
    INT8 = "int8"
    INT64 = "int64"
    OPAQUE = "opaque"
    CHARACTER = "character"
    SEMANTIC_SCALAR = "semantic_scalar"
    DESCRIPTOR = "descriptor"
    CALLBACK = "callback"


class GeneratedSupportProcedureImplementationOwner(Enum):
    """Identify which generated side defines one support procedure."""

    BINDING = "binding"
    FORTRAN = "fortran"


@dataclass
class NativeEntrypointABIValuePlan(StageRecord):
    """Describe one ordered parameter or result in a support-procedure C ABI.

    ``pointer_depth`` describes the C representation. The remaining structured
    facts let C and Fortran lowering spell the same ABI without storing rendered
    source text in planning. Callback values may carry their own nested C ABI
    signature; named runtime callback typedefs use ``c_type_name``.
    """

    role: str
    c_name: str
    fortran_name: str
    kind: NativeEntrypointABIValueKind
    pointer_depth: int = 0
    const: bool = False
    semantic_type_name: str | None = None
    rank: int | None = None
    character_length: int | None = None
    descriptor_kind: NativeArrayDescriptorKind | None = None
    intent: str | None = None
    c_type_name: str | None = None
    callback_signature: NativeEntrypointSignaturePlan | None = None


@dataclass
class NativeEntrypointSignaturePlan(StageRecord):
    """Store one complete ordered generated-support entrypoint signature."""

    parameters: tuple[NativeEntrypointABIValuePlan, ...]
    result: NativeEntrypointABIValuePlan


@dataclass
class GeneratedSupportProcedureEntrypointPlan(StageRecord):
    """Name one externally linked generated support procedure and its C ABI."""

    key: str
    owner_path: str
    role: str
    symbol_name: str
    signature: NativeEntrypointSignaturePlan
    implementation_owner: GeneratedSupportProcedureImplementationOwner


# ============================================================================
# Derived types and generated class surfaces
# ============================================================================


@dataclass
class DerivedHandoffPlan(StageRecord):
    """Store completed identity, origin, ownership, and ABI facts for a derived value.

    Derived fields, arguments, results, and module objects reference this
    facet. The generator consumes its preselected retention, release, storage,
    and native-handoff values without rediscovering lifetime policy.
    """

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
    """Describe one completed actual-storage and dummy-category compatibility case.

    ``DerivedCallPlan`` keeps these cells in the policy-established order so
    lowering can select the recorded ABI code, access mode, and failure path.
    """

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
    """Collect a derived dummy's compatibility matrix and transaction ordering.

    Argument transfers reference this record when a derived actual needs
    dummy-driven access, writeback, acquisition, or cleanup behavior.
    """

    dummy_category: DerivedDummyCategory
    cases: tuple[DerivedCallCasePlan, ...]
    writeback: DerivedWriteback
    status_role: str
    origin_identity_role: str
    acquisition_order: int
    cleanup_order: int


@dataclass
class DerivedFieldPlan(StageRecord):
    """Represent one completed field surface within a derived type or class.

    Array, native-handle, and nested-derived facets are attached only when
    selected by policy. Printers and lowerers consume the stored getter,
    setter, assignment, and role choices directly.
    """

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
    docstring: str | None = None


@dataclass
class DerivedMemberPathPlan(StageRecord):
    """Map one finite Python member path to its declaring type and native path.

    Module-object access uses this immutable path description to expose a
    known field without searching or inferring members during generation.
    """

    path: tuple[str, ...]
    native_path: tuple[str, ...]
    declaring_type_name: str
    declaring_type_identity: tuple[str, str]
    field: DerivedFieldPlan


@dataclass
class DerivedTypePlan(StageRecord):
    """Describe one namespace-owned runtime wrapper type for a native derived type.

    The planner supplies identity, native naming, fields, and finalizers;
    generated class assembly uses this record as the authoritative type shape.
    """

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
    """Describe one generated constructor keyword and its completed setter action."""

    owner_path: str
    name: str
    default_value: str | None
    setter_action: SetterAction


@dataclass
class ConstructorPlan(StageRecord):
    """Record a class constructor route, target, and owned-instance lifecycle.

    A class surface uses either explicit fields, a concrete function target, or
    an overload. Rejection text and lifecycle actions are already decided
    before this record reaches generation.
    """

    kind: ClassConstructorKind
    fields: tuple[ConstructorFieldPlan, ...]
    target_owner_path: str | None
    overload_name: str | None
    lifecycle: tuple[ConstructionLifecycleAction, ...]
    rejection_message: str | None = None
    target: FunctionPlan | None = None
    overload: OverloadPlan | None = None
    docstring: str | None = None


@dataclass
class ClassMethodPlan(StageRecord):
    """Link one Python class descriptor to its ordinary function plan.

    ``kind`` and ``passed_object_position`` preserve the completed receiver
    convention while the referenced function retains the common call details.
    """

    owner_path: str
    python_name: str
    kind: ClassMethodKind
    passed_object_position: int | None
    public: bool
    function: FunctionPlan
    docstring: str | None = None


@dataclass
class OverloadArgumentMatchPlan(StageRecord):
    """Store one exact argument predicate selected for overload dispatch.

    A non-null ``builtin_scalar_family`` is the completed reflected-operator
    exception to the otherwise exact NumPy scalar match. Lowering dispatches
    that family directly and does not classify it again from the semantic type.
    """

    python_name: str
    kind: OverloadMatchKind
    optional: bool
    semantic_type_name: str
    rank: int
    derived_type_identity: tuple[str, str] | None
    builtin_scalar_family: str | None = None


@dataclass
class OverloadPlan(StageRecord):
    """Describe an exact-match overload and the function candidates it owns.

    Candidate IDs, match tuples, and receiver flags remain parallel in planner
    order. Class and namespace surfaces consume this record to emit one
    deterministic dispatch.
    """

    owner_path: str
    python_name: str
    kind: str
    candidates: tuple[FunctionPlan, ...]
    candidate_ids: tuple[int, ...]
    candidate_matches: tuple[tuple[OverloadArgumentMatchPlan, ...], ...]
    candidate_passed_objects: tuple[bool, ...]
    unsupported_extra_argument_message: str | None = None
    identity_receiver_shortcut: bool = False
    docstring: str | None = None


@dataclass
class ClassSurfacePlan(StageRecord):
    """Compose one namespace-owned Python class over a completed derived-type plan.

    Constructor, methods, overloads, registration, and rendered documentation
    are all stored here so class lowering has no semantic discovery work.
    """

    owner_path: str
    type_identity: tuple[str, str]
    python_names: tuple[str, ...]
    base_identities: tuple[tuple[str, str], ...]
    constructor: ConstructorPlan
    methods: tuple[ClassMethodPlan, ...]
    overloads: tuple[OverloadPlan, ...]
    registration: tuple[ClassRegistrationAction, ...]
    docstring: str | None = None


@dataclass
class DerivedModuleObjectPlan(StageRecord):
    """Describe live module-state access for a derived object and its members."""

    handoff: DerivedHandoffPlan
    access: ModuleObjectAccessMechanism
    replacement: SetterAction
    member_paths: tuple[DerivedMemberPathPlan, ...]


# ============================================================================
# Array buffers, descriptors, and native handles
# ============================================================================


@dataclass
class ArrayHandoffPlan(StageRecord):
    """Store completed array layout, extent, and ABI handoff roles.

    Array transfers, results, fields, and descriptor handles share this record.
    Its role tuples are already bound to visible producers, so backends render
    them without evaluating declaration expressions or inventing extents.
    """

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
    extent_reference_tokens: tuple[tuple[str, ...], ...] = ()
    extent_reference_roles: tuple[tuple[str, ...], ...] = ()
    extent_callable_tokens: tuple[tuple[str, ...], ...] = ()
    extent_callable_roles: tuple[tuple[str, ...], ...] = ()
    extent_evaluation: tuple[str, ...] = ()
    upper_bound_roles: tuple[str, ...] = ()
    stride_roles: tuple[str, ...] = ()
    dense_actual_role: str | None = None
    runtime_rank_role: str | None = None
    itemsize_role: str | None = None
    display_shape: tuple[str, ...] = ()


@dataclass
class NativeArrayActualPlan(StageRecord):
    """Describe the accepted Python source and validation contract for one array ABI.

    The binding uses these precomputed source, dtype, layout, and mutability
    requirements when extracting an ordinary array-buffer actual.
    """

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
    """Store the descriptor-ABI roles that carry one native-array handle.

    This facet is subordinate to ``NativeArrayHandlePlan`` and names every
    descriptor component required by the selected ABI and operations.
    """

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
class NativeArrayDefaultHandlePlan(StageRecord):
    """Describe caller-created descriptor storage and its completed lifecycle.

    Native-array defaults use this only when policy selected caller construction
    instead of a native-produced handle; lowerers follow its operations and
    release behavior verbatim.
    """

    construction: NativeArrayDefaultConstruction
    descriptor_ownership: NativeArrayDescriptorOwnership | None
    release: NativeArrayRelease
    destroy_behavior: NativeArrayDestroyBehavior
    operations: tuple[NativeArrayOperation, ...]
    owner_storage_role: str | None
    operation_roles: tuple[tuple[NativeArrayOperation, str], ...]


@dataclass
class NativeArrayHandlePlan(StageRecord):
    """Represent one completed native-array handle policy and descriptor handoff.

    The record joins identity, ownership, nullability, getter/setter behavior,
    allocation, release, descriptor ABI, and required headers. It is the single
    source for handle lowering; no backend may derive missing choices locally.
    """

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
    default_handle: NativeArrayDefaultHandlePlan


@dataclass
class ScalarDescriptorResultPlan(StageRecord):
    """Describe a nullable rank-zero descriptor result and its copy/release contract."""

    descriptor_kind: NativeArrayDescriptorKind
    runtime_length: bool
    nullable: bool
    copy_reason: str
    release_owner: OwnershipOwner
    presence_role: str


@dataclass
class TransformationPlan(StageRecord):
    """Record one explicitly layer-owned representation transformation.

    Transfers list transformations in policy order. ``phase`` and ``layer``
    make the owner of each conversion and its reason visible to validation and
    generation.
    """

    phase: WritebackPhase
    layer: TransformationLayer
    action: TransformationAction
    source_representation: str
    target_representation: str
    reason: str


# ============================================================================
# Module, procedure, and native-call views
# ============================================================================


@dataclass
class BindingStatusErrorPlan(StageRecord):
    """Describe binding-owned conversion of a completed native status into an exception.

    Function plans attach this optional facet when policy selected status and
    message projection after the native call completes.
    """

    status_role: str
    message_role: str | None
    success: int
    exception_kind: PythonExceptionKind


@dataclass
class BindingModulePlan(StageRecord):
    """Store module-wide binding surfaces selected before C lowering.

    The three owner-path inventories select static CPython capsule and holder
    helpers.  They are distinct from externally linked generated support
    procedures, whose existence and complete ABI live in the entrypoint module
    plan.
    """

    owner_path: str
    owned_derived_type_owner_paths: tuple[str, ...] = ()
    allocatable_holder_type_owner_paths: tuple[str, ...] = ()
    pointer_holder_type_owner_paths: tuple[str, ...] = ()


@dataclass
class NativeEntrypointModulePlan(StageRecord):
    """Store the shared C-ABI owner and generated support procedures."""

    owner_path: str
    support_procedures: tuple[GeneratedSupportProcedureEntrypointPlan, ...] = ()
    native_languages: tuple[str, ...] = ()


class NativeGeneratedCodeGroupKind(Enum):
    """Classify independently planned generated-native membership."""

    FORTRAN_ADAPTERS = "fortran_adapters"
    FORTRAN_SUPPORT = "fortran_support"


@dataclass
class NativeGeneratedCodeGroupPlan(StageRecord):
    """Group generated native members that share one physical source set."""

    kind: NativeGeneratedCodeGroupKind
    language: str
    member_keys: tuple[str, ...]
    source_paths: tuple[str, ...]


@dataclass
class BridgeModulePlan(StageRecord):
    """Store module-wide Fortran support selected before bridge lowering.

    Holder-definition inventories include every holder used by an adapter or
    generated support procedure.  The narrower field inventories select only
    holder types whose values can cross back to Python and expose field
    support.
    """

    owner_path: str
    allocatable_holder_type_owner_paths: tuple[str, ...] = ()
    pointer_holder_type_owner_paths: tuple[str, ...] = ()
    allocatable_holder_field_type_owner_paths: tuple[str, ...] = ()
    pointer_holder_field_type_owner_paths: tuple[str, ...] = ()


@dataclass
class BindingModuleVariablePlan(StageRecord):
    """Describe Python module-attribute access and initialization for one value.

    ``python_names`` retains every public spelling. The binding consumes the
    completed getter and setter actions plus the selected initializer/value.
    """

    python_names: tuple[str, ...]
    getter_action: ModuleGetterAction
    setter_action: SetterAction
    initializer: Any
    constant_value: Any


@dataclass
class NativeEntrypointModuleVariablePlan(StageRecord):
    """Describe the C-ABI operations shared by module-variable lowerers."""

    descriptor_kind: str | None
    getter_role: str | None
    setter_role: str | None


@dataclass
class BridgeModuleVariablePlan(StageRecord):
    """Describe native module-variable access selected by completed policy.

    This record contains only original-Fortran naming and adapter-local access
    behavior. The matching entrypoint record owns public C symbols and roles.
    """

    native_name: str
    native_module: str
    native_getter_action: ModuleGetterAction
    native_assignment: AssignmentMode


@dataclass
class ModuleVariablePlan(StageRecord):
    """Join binding, entrypoint, and bridge views of one module-state value.

    Optional array, native-handle, and derived-object facets are attached only
    when policy selected them. Namespace plans own these records for emission.
    """

    owner_path: str
    symbol_name: str
    semantic_type_name: str
    datatype_family: DatatypeFamily
    binding: BindingModuleVariablePlan
    entrypoint: NativeEntrypointModuleVariablePlan
    bridge: BridgeModuleVariablePlan
    array: ArrayHandoffPlan | None
    native_array_handle: NativeArrayHandlePlan | None
    derived: DerivedModuleObjectPlan | None = None
    docstring: str | None = None


@dataclass
class BindingFunctionPlan(StageRecord):
    """Store Python-visible call behavior for one generated binding function.

    The planner fixes public naming, GIL handling, optional status projection,
    and argument-conversion order. Code generation fills an unresolved
    docstring while preserving any explicit editable-plan value.
    """

    python_name: str
    docstring: str | None
    release_gil: bool
    status_error: BindingStatusErrorPlan | None
    argument_conversion_order: tuple[str, ...]
    public: bool = True


@dataclass
class NativeEntrypointParameterPlan(StageRecord):
    """Order one argument or result parameter group in the shared C ABI.

    The referenced argument or result entrypoint facet owns the group's exact
    transport. ``position`` orders groups after any direct function return.
    """

    owner_path: str
    position: int
    source_kind: str
    native_position: int | None = None


@dataclass
class NativeEntrypointFunctionPlan(StageRecord):
    """Describe one shared C-ABI symbol, return, and ordered parameter groups."""

    symbol_name: str
    action: NativeEntrypointAction
    parameters: tuple[NativeEntrypointParameterPlan, ...]
    results: tuple[NativeEntrypointResultPlan, ...]
    projected_slots: tuple[NativeEntrypointProjectedSlotPlan, ...]


@dataclass
class BridgeFunctionPlan(StageRecord):
    """Store native invocation and declaration facts for one bridge procedure.

    The bridge dispatches its recorded invocation, standalone, and external
    declaration mode; it does not infer a native interface from the call.
    """

    native_name: str
    native_invocation: NativeInvocationKind
    native_operator: str | None
    standalone: bool
    external_declaration: ExternalDeclarationMode
    native_module: str | None
    native_is_subroutine: bool


@dataclass
class ClassCallPlan(StageRecord):
    """Describe the completed receiver and invocation route for one class-owned call."""

    kind: ClassMethodKind
    passed_object_position: int | None
    invocation: ClassInvocationKind
    type_bound_name: str | None


@dataclass
class BindingArgumentPlan(StageRecord):
    """Describe Python input conversion and the binding-to-entrypoint handoff.

    Argument transfers own this binding view. Its barrier action, conversion
    phase, Python optionality, mutability, and local extraction facts are
    complete policy decisions. Shared C-ABI roles live only in the entrypoint
    facet.
    """

    python_name: str
    python_action: PythonBarrierAction
    codegen_action: CodegenAction
    conversion_phase: ArgumentConversionPhase
    optional_mode: OptionalMode
    nullable: bool
    writable: bool
    descriptor_boundary: bool


@dataclass
class NativeEntrypointArgumentPlan(StageRecord):
    """Describe one binding-to-entrypoint C-ABI parameter group."""

    parameter_name: str
    handoff_mode: ArgumentHandoffMode
    handoff_role: str
    optional_mode: OptionalMode
    presence_role: str | None
    passing: EntrypointPassingConvention
    optionality: EntrypointOptionalityAction
    pass_character_length: bool = False
    pass_array_metadata: bool = False
    pass_descriptor_presence: bool = False
    pass_derived_transaction: bool = False
    pass_callback_parameter: bool = False
    length_handoff_role: str | None = None
    descriptor_output_role: str | None = None
    descriptor_output_presence_role: str | None = None


@dataclass
class BridgeArgumentPlan(StageRecord):
    """Describe adapter-local conversion into one original Fortran argument.

    The native name identifies the original dummy. C-ABI transport and ordering
    live in the matching native-entrypoint facet.
    """

    native_name: str
    native_action: NativeBarrierAction
    codegen_action: CodegenAction
    data_action: BridgeDataAction
    copy_reason: str | None


@dataclass
class BindingResultPlan(StageRecord):
    """Describe binding-side projection of one completed native result."""

    codegen_action: CodegenAction
    python_action: PythonBarrierAction
    python_result_role: str


@dataclass
class NativeEntrypointResultPlan(StageRecord):
    """Describe one native-to-binding result at the shared C-ABI boundary."""

    owner_path: str
    parameter_name: str | None
    source_kind: str
    result_position: int | None
    native_result_role: str
    direct_result_abi: DirectResultABI
    semantic_type_name: str
    datatype_family: DatatypeFamily
    object_kind: ObjectKind
    character_length: int | None
    array: ArrayHandoffPlan | None
    native_array_handle: NativeArrayHandlePlan | None
    scalar_descriptor: ScalarDescriptorResultPlan | None
    passing: EntrypointPassingConvention


@dataclass
class BridgeResultPlan(StageRecord):
    """Describe adapter-local production and conversion of one Fortran result."""

    codegen_action: CodegenAction
    native_action: NativeBarrierAction
    data_action: BridgeDataAction
    copy_reason: str | None
    native_name: str | None


@dataclass
class BindingLifecyclePlan(StageRecord):
    """Describe the binding-owned portion of one ordered lifecycle action."""

    source_role: str
    codegen_action: CodegenAction
    semantic_type_name: str
    datatype_family: DatatypeFamily
    result_position: int
    python_result_role: str | None
    operation: LifecycleOperation


@dataclass
class BridgeLifecyclePlan(StageRecord):
    """Describe the bridge-owned symbolic source for one lifecycle action."""

    source_role: str


@dataclass
class BridgeCallSlotPlan(StageRecord):
    """Store only adapter-local actions for one projected call slot."""

    native_action: NativeBarrierAction
    codegen_action: CodegenAction
    bridge_data_action: BridgeDataAction
    bridge_copy_reason: str | None


@dataclass
class NativeEntrypointProjectedSlotPlan(StageRecord):
    """Authoritative ordered binding projection with an optional adapter facet.

    This record owns the route-neutral projection source, order, shared C-ABI
    transport, and boundary type facts. Adapter-only conversion and original
    Fortran invocation facts live in ``adapter`` and are never copied into this
    entrypoint facet.
    """

    owner_path: str
    native_position: int
    source_kind: str
    python_position: int | None
    python_name: str | None
    native_name: str
    value_kind: str
    symbolic_role: str
    object_kind: ObjectKind | None
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
    datatype_family: DatatypeFamily | None = None
    character_length: int | None = None
    array: ArrayHandoffPlan | None = None
    native_array_handle: NativeArrayHandlePlan | None = None
    scalar_descriptor: ScalarDescriptorResultPlan | None = None
    derived: DerivedHandoffPlan | None = None
    projection_action: EntrypointProjectionAction = EntrypointProjectionAction.BLOCKED
    passing: EntrypointPassingConvention = EntrypointPassingConvention.BLOCKED
    optionality: EntrypointOptionalityAction = EntrypointOptionalityAction.BLOCKED
    adapter: BridgeCallSlotPlan | None = None


@dataclass
class PolymorphicVariantPlan(StageRecord):
    """Describe one concrete derived type accepted by an enumerated polymorphic input."""

    type_identity: tuple[str, str]
    backend_symbol: str
    python_name: str
    abi_code: int


@dataclass
class PolymorphicDispatchPlan(StageRecord):
    """Store stable concrete-type dispatch variants for one scalar input dummy."""

    owner_path: str
    variants: tuple[PolymorphicVariantPlan, ...]


@dataclass
class ProcedurePrototypeArgumentPlan(StageRecord):
    """Describe exact native dummy characteristics shared by every prototype use.

    Prototype declarations consume this record when they need an abstract
    interface or a matching concrete native procedure entity.
    """

    owner_path: str
    name: str
    semantic_type_name: str
    rank: int
    passed_by_value: bool
    intent: str | None
    character_length: int | None
    array: ArrayHandoffPlan | None
    derived_type_identity: tuple[str, str] | None
    derived_backend_symbol: str | None


@dataclass
class ProcedurePrototypeResultPlan(StageRecord):
    """Describe exact native function-result characteristics for one prototype."""

    owner_path: str
    semantic_type_name: str
    rank: int
    character_length: int | None
    array: ArrayHandoffPlan | None
    derived_type_identity: tuple[str, str] | None
    derived_backend_symbol: str | None


@dataclass
class ProcedurePrototypePlan(StageRecord):
    """Represent one reusable exact native signature and abstract-interface symbol.

    Callback and standalone declaration paths share this normalized prototype.
    Its ``interface_symbol`` avoids collisions with a concrete native entity.
    """

    owner_path: str
    name: str
    identity: str
    interface_symbol: str
    pure: bool
    arguments: tuple[ProcedurePrototypeArgumentPlan, ...]
    result: ProcedurePrototypeResultPlan | None


@dataclass
class CallbackTransferPlan(StageRecord):
    """Describe one typed native-to-Python transfer inside a callback adapter.

    Callback handoff records preserve the exact native characteristics and the
    completed adapter/Python actions for each argument or result transfer.
    """

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
    array: ArrayHandoffPlan | None
    derived_type_identity: tuple[str, str] | None
    derived_backend_symbol: str | None
    data_role: str
    extent_roles: tuple[str, ...]
    length_role: str | None


@dataclass
class CallbackResultPlan(StageRecord):
    """Join an optional callback result transfer to its completed result action."""

    transfer: CallbackTransferPlan | None
    action: CallbackResultAction


@dataclass
class BindingCallbackPlan(StageRecord):
    """Store binding-owned callback runtime symbols."""

    context_type_symbol: str
    context_current_symbol: str
    abort_symbol: str


@dataclass
class NativeEntrypointCallbackPlan(StageRecord):
    """Store the binding-implemented trampoline contract shared with Fortran."""

    support_procedure: GeneratedSupportProcedureEntrypointPlan


@dataclass
class BridgeCallbackPlan(StageRecord):
    """Store the adapter-local callback symbol used to call original Fortran."""

    adapter_symbol: str


@dataclass
class CallbackHandoffPlan(StageRecord):
    """Describe one call-scoped callback context, adapter, transfers, and fatal contract.

    This record gives callback lowering its generated symbols plus already
    completed lifecycle, thread, GIL, and fatal-error actions.
    """

    owner_path: str
    prototype: ProcedurePrototypePlan
    binding: BindingCallbackPlan
    entrypoint: NativeEntrypointCallbackPlan
    bridge: BridgeCallbackPlan
    arguments: tuple[CallbackTransferPlan, ...]
    result: CallbackResultPlan
    lifecycle: tuple[CallbackLifecycleAction, ...]
    thread_action: CallbackThreadAction
    gil_actions: tuple[CallbackGILAction, ...]
    fatal_action: CallbackFatalAction


# ============================================================================
# Shared transfers, lifecycle, and plan-tree orchestration
# ============================================================================


@dataclass
class ArgumentTransferPlan(StageRecord):
    """Represent one complete Python-to-native transfer and bridge call slot.

    This is the primary datatype-varying plan record. It combines completed
    ownership, storage, nullability, mutation, projection, ABI, optional
    array/derived/callback facets, and the selected lowering views. The planner
    shares ``projected_call_slot`` with the function entrypoint sequence by
    identity; an adapter route may additionally reference its narrow bridge
    facet.
    """

    owner_path: str
    python_position: int
    native_position: int
    semantic_type_name: str
    datatype_family: DatatypeFamily
    character_length: int | None
    scalar_logical_abi: ScalarLogicalABI
    scalar_native_type: str | None
    array_logical_abi: ArrayLogicalABI
    array_native_type: str | None
    array_copy_in: bool
    array_copy_out: bool
    array_writeback_abi: ArrayWritebackABI
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
    entrypoint: NativeEntrypointArgumentPlan
    bridge: BridgeArgumentPlan | None
    projected_call_slot: NativeEntrypointProjectedSlotPlan
    transformations: tuple[TransformationPlan, ...] = ()


@dataclass
class ResultPlan(StageRecord):
    """Represent one complete native-to-Python transfer and optional hidden ABI slot.

    Direct function results omit ``projected_call_slot``; hidden output results
    share the corresponding function-wide projected slot. Binding, entrypoint,
    and bridge facets hold their completed projection, transport, and
    production choices.
    """

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
    entrypoint: NativeEntrypointResultPlan
    bridge: BridgeResultPlan | None
    projected_call_slot: NativeEntrypointProjectedSlotPlan | None = None
    scalar_descriptor: ScalarDescriptorResultPlan | None = None
    derived: DerivedHandoffPlan | None = None
    transformations: tuple[TransformationPlan, ...] = ()


@dataclass
class LifecycleActionPlan(StageRecord):
    """Record one transfer-owned action in a function-wide execution sequence.

    Functions keep writeback, cleanup, and release tuples separately in their
    completed order. Optional binding or bridge facets state which backend owns
    the operation without duplicating the transfer policy.
    """

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
    """Orchestrate one generated call with stable ABI and lifecycle indexes.

    Namespace plans own functions. Arguments/results hold datatype-specific
    facts, while this record owns entrypoint and original-Fortran call order,
    callable declarations, available roles, and function-wide writeback,
    cleanup, and release order.
    """

    owner_path: str
    symbol_name: str
    binding: BindingFunctionPlan
    entrypoint: NativeEntrypointFunctionPlan
    bridge: BridgeFunctionPlan | None
    class_call: ClassCallPlan | None
    arguments: tuple[ArgumentTransferPlan, ...]
    results: tuple[ResultPlan, ...]
    declaration_callables: tuple[DeclarationCallablePlan, ...]
    available_roles: tuple[str, ...]
    writeback_actions: tuple[LifecycleActionPlan, ...] = ()
    cleanup_actions: tuple[LifecycleActionPlan, ...] = ()
    release_actions: tuple[LifecycleActionPlan, ...] = ()


@dataclass
class DeclarationCallablePlan(StageRecord):
    """Describe one planned module import or standalone native procedure entity.

    Declaration expressions refer to ``expression_token`` and ``symbolic_role``.
    The completed action tells the bridge whether to use a visible entity,
    imported procedure, or prototype-backed standalone declaration.
    """

    owner_path: str
    source_name: str
    native_name: str
    native_scope: str | None
    backend_symbol: str
    symbolic_role: str
    expression_token: str
    action: DeclarationCallableAction
    prototype: ProcedurePrototypePlan | None = None


@dataclass
class NamespacePlan(StageRecord):
    """Represent one Python namespace and its directly exported wrapper owners.

    ``python_path`` identifies the root or child module path; contained tuples
    preserve planner order for functions, variables, types, classes, and
    overloads. ``ModulePlan`` groups these namespaces into one generation unit.
    """

    owner_path: str
    python_path: tuple[str, ...]
    functions: tuple[FunctionPlan, ...] = ()
    variables: tuple[ModuleVariablePlan, ...] = ()
    derived_types: tuple[DerivedTypePlan, ...] = ()
    classes: tuple[ClassSurfacePlan, ...] = ()
    overloads: tuple[OverloadPlan, ...] = ()
    docstring: str | None = None


@dataclass
class ModulePlan(StageRecord):
    """Serve as the root editable plan for one generated extension module.

    Constructed by ``WrapperPlanner.build()``, this root joins binding,
    native-entrypoint, and bridge module views with an explicit namespace tree
    and required headers. Pass it to ``WrapperGenerator.generate()``;
    generation validates then freezes the graph before it renders artifacts.
    """

    owner_path: str
    binding: BindingModulePlan
    entrypoint: NativeEntrypointModulePlan
    bridge: BridgeModulePlan | None
    namespaces: tuple[NamespacePlan, ...]
    native_generated_code_groups: tuple[NativeGeneratedCodeGroupPlan, ...] = ()
    required_headers: tuple[str, ...] = ()


@dataclass
class WrapperPlanDiagnostic(StageRecord):
    """Store one owner-path diagnostic produced before backend generation begins."""

    owner_path: str
    code: str
    message: str


if __name__ == "__main__":
    # This module owns the typed representation rather than semantic-policy
    # completion or source generation. Constructing the smallest procedure
    # plan is therefore its nearest deterministic stage-local demonstration.
    binding_function = BindingFunctionPlan(
        python_name="ping",
        docstring="Call the native PING subroutine.",
        release_gil=False,
        status_error=None,
        argument_conversion_order=(),
    )
    bridge_function = BridgeFunctionPlan(
        native_name="PING",
        native_invocation=NativeInvocationKind.PROCEDURE,
        native_operator=None,
        standalone=True,
        external_declaration=ExternalDeclarationMode.IMPLICIT_EXTERNAL,
        native_module=None,
        native_is_subroutine=True,
    )
    entrypoint_function = NativeEntrypointFunctionPlan(
        symbol_name="bind_c_ping",
        action=NativeEntrypointAction.GENERATED_FORTRAN_ADAPTER,
        parameters=(),
        results=(),
        projected_slots=(),
    )
    function = FunctionPlan(
        owner_path="demo.ping",
        symbol_name="ping",
        binding=binding_function,
        entrypoint=entrypoint_function,
        bridge=bridge_function,
        class_call=None,
        arguments=(),
        results=(),
        declaration_callables=(),
        available_roles=(),
    )
    plan = ModulePlan(
        owner_path="demo",
        binding=BindingModulePlan(owner_path="demo"),
        entrypoint=NativeEntrypointModulePlan(owner_path="demo"),
        bridge=BridgeModulePlan(owner_path="demo"),
        namespaces=(NamespacePlan(owner_path="demo", python_path=(), functions=(function,)),),
    )

    print(f"Plan owner: {plan.owner_path}")
    print(f"Python export: {plan.namespaces[0].functions[0].binding.python_name}")
    print(f"Native procedure: {plan.namespaces[0].functions[0].bridge.native_name}")
    print(f"Projected call slots: {len(plan.namespaces[0].functions[0].entrypoint.projected_slots)}")
