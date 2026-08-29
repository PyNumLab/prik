"""Project completed semantic decisions into backend-neutral wrapper policies.

This module consumes semantic signatures and ownership decisions completed by
``completion``.  It produces immutable records for wrapper planning:
Python/native boundaries, ordered call slots, result projections, lifecycle,
module and derived-object access, and fail-closed support blockers.  Planners
and backend generators consume these records without inferring replacement
policy from a datatype or native declaration.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import dataclass, replace
import re

import numpy

from immutabledict import immutabledict

from prik.contracts import NATIVE_C_SCALAR_IDENTITIES
from prik.naming import NamingPolicy
from prik.semantics import models
from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_RAW,
    BIND_TARGET_METADATA,
    NATIVE_C_SCALAR_IDENTITY_METADATA,
    NULLABLE_ANNOTATION_METADATA,
    SCALAR_STORAGE_CATEGORY,
    SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA,
)
from prik.policy.native_array_handles import (
    NATIVE_ARRAY_POINTER_C_DESCRIPTOR_HEADER,
    NativeArrayHandlePolicy as CompletedNativeArrayHandlePolicy,
)
from prik.semantics.native_array_handles import native_array_descriptor_kind
from prik.policy.exports import PythonExportPolicy, completed_python_exports
from prik.policy.ownership import (
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
    character_descriptor_kind,
    declared_character_length,
    is_character_descriptor_update,
    uses_deferred_character_length,
)
from prik.policy.models import (
    FIXED_STRING_RESULT_COPY_REASON,
    ORDINARY_ARRAY_RESULT_COPY_REASON,
    OWNED_NATIVE_ARRAY_HANDLE_COPY_REASON,
    SCALAR_DESCRIPTOR_RESULT_COPY_REASON,
    STRING_INPUT_COPY_REASON,
    STRING_REPLACEMENT_COPY_REASON,
    STRING_STORAGE_COPY_REASON,
    RAW_STRING_ADDRESS_COPY_REASON,
    DERIVED_VALUE_COPY_REASON,
    LOGICAL_SCALAR_KIND_COPY_REASON,
    LOGICAL_ARRAY_KIND_COPY_REASON,
    NativeEntrypointAction,
    DirectCABITypePolicy,
    DirectCABIPolicy,
    EntrypointPassingConvention,
    EntrypointOptionalityAction,
    EntrypointProjectionAction,
    OptionalMode,
    ArgumentHandoffMode,
    ArgumentConversionPhase,
    BridgeDataAction,
    DirectResultABI,
    ArrayWritebackABI,
    ScalarLogicalABI,
    ArrayLogicalABI,
    WritebackPhase,
    LifecycleOperation,
    TransformationLayer,
    TransformationAction,
    CallbackABIKind,
    CallbackTransferAction,
    CallbackResultAction,
    CallbackLifecycleAction,
    CallbackThreadAction,
    CallbackGILAction,
    CallbackFatalAction,
    ModuleGetterAction,
    ModuleObjectAccessMechanism,
    DerivedFieldAccessMechanism,
    DerivedObjectOrigin,
    DerivedOwnerRetention,
    DerivedRelease,
    DerivedNativeHandoff,
    DerivedObjectStorage,
    DerivedDummyCategory,
    DerivedCallAction,
    DerivedActualAccess,
    DerivedTargetLifetime,
    DerivedWriteback,
    ClassConstructorKind,
    ClassMethodKind,
    ClassInvocationKind,
    NativeInvocationKind,
    ExternalDeclarationMode,
    DeclarationCallableAction,
    ClassRegistrationAction,
    ConstructionLifecycleAction,
    DerivedCallCasePolicy,
    DerivedCallPolicy,
    DerivedHandoffPolicy,
    DerivedModuleObjectPolicy,
    DerivedFieldPolicy,
    DerivedMemberPathPolicy,
    DerivedTypePolicy,
    ConstructorFieldPolicy,
    ConstructorPolicy,
    ClassMethodPolicy,
    OverloadCandidatePolicy,
    OverloadPolicy,
    ClassSurfacePolicy,
    CharacterLocalPolicy,
    CharacterLocalRelease,
    NativeArrayDescriptorKind,
    NativeArrayHandleKind,
    NativeDescriptorHandoffABI,
    NativeArrayDefaultConstruction,
    NativeArraySourceKind,
    NativeArrayHandleOrigin,
    NativeArrayOwnerRetention,
    NativeArrayDescriptorOwnership,
    NativeArrayGetterBehavior,
    NativeArrayOutputProjection,
    NativeArrayResultAllocation,
    NativeArrayRelease,
    NativeArrayDestroyBehavior,
    NativeArrayExtractionAction,
    NativeArrayDescriptorInterop,
    NativeArrayOperation,
    NativeStatusErrorPolicy,
    ModuleVariablePolicy,
    LifecyclePolicy,
    ArrayHandoffPolicy,
    ProcedurePrototypeArgumentPolicy,
    ProcedurePrototypeResultPolicy,
    ProcedurePrototypePolicy,
    DeclarationCallablePolicy,
    TransformationPolicy,
    NativeArrayActualPolicy,
    NativeDescriptorHandoffPolicy,
    NativeArrayDefaultHandlePolicy,
    NativeArrayHandleWrapperPolicy,
    ScalarDescriptorResultPolicy,
    PolymorphicDispatchPolicy,
    CallbackTransferPolicy,
    CallbackResultPolicy,
    CallbackHandoffPolicy,
    ArgumentPolicy,
    ResultPolicy,
    NativeCallSlotPolicy,
    FunctionWrapperPolicy,
)
from prik.utilities.declaration_expressions import (
    declaration_expression_call_sites,
    declaration_extent_references,
    resolve_declaration_extent,
)
from prik.semantics.scalar_types import (
    BOOLEAN_SEMANTIC_TYPE_NAMES,
    is_boolean_semantic_type_name,
    is_integer_semantic_type_name,
)


_PLAN_PRIMITIVE_SCALAR_TYPES = frozenset(
    {
        *BOOLEAN_SEMANTIC_TYPE_NAMES,
        "Int8",
        "Int16",
        "Int32",
        "Int64",
        "UInt8",
        "UInt16",
        "UInt32",
        "UInt64",
        "SizeT",
        "Float32",
        "Float64",
        "Float128",
        "Complex64",
        "Complex128",
        "Complex256",
    }
)

# Two 128-bit reals differ only in mantissa width: x87 extended precision and
# IEEE binary128 share a storage size. Whether either is representable depends
# on the build target's ``long double``, so the decision reads measured facts
# rather than the source language.
_EXTENDED_PRECISION_SCALAR_TYPES = frozenset({"Float128", "Complex256"})

# Binding-owned extent, length, presence, and workspace slots record the Python
# position of the argument they are derived from, but they never transport it.
_DERIVED_NATIVE_CALL_SLOT_KINDS = frozenset({"computed", "work"})

# Qualifiers describe the native view of a pointee, not the call-local storage
# that receives a converted Python value, so they are dropped whole rather than
# by substring, which would corrupt a spelling that merely contains one.
_C_POINTEE_QUALIFIER_WORDS = frozenset({"const", "restrict", "__restrict", "__restrict__", "volatile", "_Atomic"})

_NUMPY_DTYPE_NAMES = {
    **dict.fromkeys(BOOLEAN_SEMANTIC_TYPE_NAMES, "bool"),
    "Int8": "int8",
    "Int16": "int16",
    "Int32": "int32",
    "Int64": "int64",
    "UInt8": "uint8",
    "UInt16": "uint16",
    "UInt32": "uint32",
    "UInt64": "uint64",
    "SizeT": "uintp",
    "Float32": "float32",
    "Float64": "float64",
    "Float128": "longdouble",
    "Complex64": "complex64",
    "Complex128": "complex128",
    "Complex256": "clongdouble",
}


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


def overload_builtin_scalar_family(semantic_type_name: str) -> str:
    """Return the Python scalar family admitted by reflected dispatch."""
    if is_boolean_semantic_type_name(semantic_type_name):
        return "bool"
    if semantic_type_name.startswith("Int"):
        return "int"
    if semantic_type_name.startswith("Float"):
        return "float"
    if semantic_type_name.startswith("Complex"):
        return "complex"
    raise ValueError(f"Unsupported reflected overload scalar {semantic_type_name!r}")


@dataclass(frozen=True)
class _ArgumentBoundaryPolicy:
    """Normalized wrapper-boundary fields for one ordinary or callback input."""

    optional_mode: OptionalMode
    conversion_phase: ArgumentConversionPhase
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
class _FunctionPolicyContext:
    """Keep the facts shared by every policy step for one function.

    ``function`` and ``owner_path`` identify the callable being completed.
    The two mappings contain already-completed derived-type and polymorphic
    facts, while ``class_call`` identifies an optional class-surface call.
    For example, all argument, result, and native-slot builders for
    ``math.scale`` receive the same context instead of separately threading
    those five values through each helper.

    Step-local products such as native positions and call slots deliberately
    remain ordinary helper arguments; they are not fixed function context.
    """

    function: models.SemanticFunction
    owner_path: str
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy]
    polymorphic_variants: Mapping[tuple[str, str], tuple[tuple[str, str], ...]]
    class_call: ClassMethodPolicy | None


@dataclass(frozen=True)
class _ResultPolicyCandidate:
    """Store one result policy candidate together with its support blockers.

    ``policy`` is ``None`` when completion cannot construct a usable result,
    such as a direct return without completed ownership.  Keeping blockers on
    the same record prevents callers from coordinating parallel policy and
    diagnostic tuples by position.
    """

    policy: ResultPolicy | None
    blockers: tuple[str, ...]


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
    array = _array_handoff_policy(field.semantic_type)
    blockers = (
        *_runtime_semantic_validation_blockers(field.semantic_type, f"field {field.name!r}"),
        *_derived_field_blockers(field, getter, setter, handle, array),
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
        array=array,
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
    abstract = "abstract" in type_attributes
    blockers = tuple(
        [*(f"field {name!r} is missing completed derived-field policy" for name in missing)]
        + [reason for field in fields for reason in field.blockers]
        + (
            [f"deferred type-bound procedure {name!r} needs a declaring abstract type" for name in deferred_bindings]
            if not abstract
            else []
        )
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
        destructors=tuple(str(item.native_name or item.name) for item in semantic_class.destructors),
        bind_c=bool(semantic_class.metadata.get("fortran_bind_c")),
        supported=not blockers,
        blockers=blockers,
        abstract=abstract,
        deferred_bindings=deferred_bindings,
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
    """Select exactly one constructor surface from the semantic contract.

    An abstract native type has no constructor at all: Fortran forbids an
    instance of it, so the generated class exposes its inherited surface while
    only a concrete extension can be created.
    """
    if derived.abstract:
        return (
            ConstructorPolicy(
                kind=ClassConstructorKind.ABSENT,
                fields=(),
                target_owner_path=None,
                overload_name=None,
                call=None,
                lifecycle=(),
                rejection_message=(
                    f"{semantic_class.name} is an abstract native type and cannot be instantiated; "
                    "create one of its concrete extensions instead"
                ),
            ),
            (),
        )
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
                call=None,
                lifecycle=lifecycle,
            ),
            tuple(blockers),
        )
    if bound:
        method = bound[0]
        call = replace(_class_method_policy(owner_path, method), public=False)
        blocker = _class_method_blockers(call)
        if blocker:
            blockers.append(blocker)
        return (
            ConstructorPolicy(
                kind=ClassConstructorKind.BOUND_PROCEDURE,
                fields=(),
                target_owner_path=call.owner_path,
                overload_name=None,
                call=call,
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
                call=None,
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
            call=None,
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
    array: ArrayHandoffPolicy | None,
) -> list[str]:
    """Return exact unsupported public-field forms before lowering."""
    return [
        *_derived_field_completed_policy_blockers(field, getter, setter),
        *_derived_field_descriptor_blockers(field, handle),
        *_derived_field_object_kind_blockers(field, getter),
        *_derived_field_setter_blockers(field, setter),
        *_persistent_array_extent_blockers(f"field {field.name!r}", array),
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
    """Return a lowering-ready module-variable policy or fail before planning.

    Use this after post-IR policy completion.  Missing or unsupported records
    raise ``ValueError`` so getter/setter lowering cannot infer an alternate
    storage or replacement policy.
    """
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy] | None = None,
) -> ModuleVariablePolicy:
    """Build one module-variable access policy from completed semantic decisions.

    The function selects an already-defined family for descriptor handles,
    derived objects, ordinary arrays, or scalar values, then validates runtime
    and initialization requirements.  It returns a new record and does not
    mutate ``variable``.
    """
    owner_path = f"{module_name}.{variable.name}"
    # Gather semantic decisions shared by all module-variable policy families.
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
    # Select the one completed access family without backend-specific inference.
    if _is_parameter_array(variable):
        policy = _constant_array_module_variable_policy(
            variable,
            module_name,
            owner_path,
            getter,
            setter,
            array,
        )
    elif native_array_handle is not None:
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
    # Add runtime and import-time initialization blockers to the selected family.
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
    if variable.default_value is None or _is_scalar_module_constant(variable) or _is_parameter_array(variable):
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
        "character_length": _character_length(variable.semantic_type),
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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


def _constant_array_module_variable_policy(
    variable: models.SemanticVariable,
    module_name: str,
    owner_path: str,
    getter: OwnershipDecision | None,
    setter: OwnershipDecision | None,
    array: ArrayHandoffPolicy | None,
) -> ModuleVariablePolicy:
    """Build one immutable Python-owned snapshot policy for a parameter array.

    Fortran ``parameter`` arrays have no addressable module storage.  The
    selected bridge therefore copies the compiler-evaluated values into a
    module-owned NumPy allocation once during import; it never exposes or
    aliases a native address.
    """
    blockers = _constant_array_module_variable_blockers(variable, getter, setter, array)
    return ModuleVariablePolicy(
        **_module_variable_policy_base(variable, module_name, owner_path),
        getter_action=ModuleGetterAction.NATIVE_CONSTANT_ARRAY_VALUE,
        getter=getter,
        setter_action=SetterAction.OMIT,
        native_assignment=AssignmentMode.NONE,
        setter=setter,
        descriptor_kind=None,
        initializer=None,
        constant_value=None,
        supported=not blockers,
        blockers=tuple(blockers),
        array=array,
    )


def _constant_array_module_variable_blockers(
    variable: models.SemanticVariable,
    getter: OwnershipDecision | None,
    setter: OwnershipDecision | None,
    array: ArrayHandoffPolicy | None,
) -> tuple[str, ...]:
    """Validate the post-IR immutable-copy contract for one parameter array."""
    blockers = []
    if variable.visibility != "public":
        blockers.append("module parameter array is not public")
    if array is None or array.rank is None or array.rank <= 0 or len(array.shape) != array.rank:
        blockers.append("module parameter array requires one concrete fixed rank")
    if variable.semantic_type.name not in _PLAN_PRIMITIVE_SCALAR_TYPES | {"String"}:
        blockers.append("module parameter array requires a primitive numeric element type")
    expected_getter = (
        getter is not None
        and getter.kind is ObjectKind.NUMPY_ARRAY
        and getter.owner is OwnershipOwner.PYTHON
        and getter.transfer is TransferMode.BY_VALUE
        and getter.destruction is DestructionPolicy.PYTHON_REFCOUNT
        and getter.storage_mode is StorageMode.HEAP
    )
    if not expected_getter:
        blockers.append("module parameter array is not a completed Python-owned immutable snapshot")
    if setter is None or setter.setter_action is not SetterAction.OMIT:
        blockers.append("module parameter array must omit native replacement assignment")
    return tuple(blockers)


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
    getter_action = _scalar_module_getter_action(variable, getter, constant)
    blockers = _scalar_module_variable_blockers(
        variable,
        getter,
        setter,
        descriptor_kind,
        constant,
        getter_action,
    )
    initializer = variable.metadata.get(models.RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA)
    return ModuleVariablePolicy(
        **_module_variable_policy_base(variable, module_name, owner_path),
        getter_action=getter_action,
        getter=getter,
        setter_action=setter.setter_action if setter is not None else SetterAction.OMIT,
        native_assignment=_scalar_module_native_assignment(setter, variable),
        setter=setter,
        descriptor_kind=descriptor_kind,
        initializer=(
            _scalar_module_literal_value(initializer, variable.semantic_type.name) if initializer is not None else None
        ),
        constant_value=(
            _scalar_module_literal_value(variable.default_value, variable.semantic_type.name)
            if getter_action is ModuleGetterAction.CONSTANT_VALUE and variable.default_value is not None
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
    if variable.semantic_type.name not in _PLAN_PRIMITIVE_SCALAR_TYPES | {"String"}:
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
    blockers.extend(_persistent_array_extent_blockers(f"module variable {variable.name!r}", array))
    return tuple(blockers)


def _persistent_array_extent_blockers(
    owner: str,
    array: ArrayHandoffPolicy | None,
) -> tuple[str, ...]:
    """Reject persistent extents that still require unavailable runtime values.

    Module arrays and fields have no call-local scalar or input-array roles.
    This consumes their role-free extent references and returns one diagnostic
    per dependent axis; it does not mutate the array policy.
    """
    if array is None:
        return ()
    return tuple(
        f"{owner} extent axis {axis} depends on unavailable declaration values {references}"
        for axis, references in enumerate(array.extent_references)
        if references
    )


def completed_function_wrapper_policy(function: models.SemanticFunction) -> FunctionWrapperPolicy:
    """Return a lowering-ready function policy stored by post-IR completion.

    Use this at the planning boundary.  Missing policy or an unsupported policy
    raises ``ValueError`` with the completed-policy diagnostic, preventing
    lower stages from substituting a fallback behavior.
    """

    policy = function.metadata.get(models.RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA)
    if not isinstance(policy, FunctionWrapperPolicy):
        raise ValueError(
            f"Semantic function {function.name!r} is missing completed wrapper policy; "
            "run complete_semantic_policies before wrapper planning"
        )
    if not policy.supported:
        details = "; ".join(policy.blockers) or "unsupported wrapper policy"
        raise ValueError(f"Semantic function {policy.owner_path!r} has unsupported wrapper policy: {details}")
    if policy.entrypoint_action is None:
        raise ValueError(f"Semantic function {policy.owner_path!r} is missing completed native entrypoint action")
    if policy.entrypoint_action is NativeEntrypointAction.DIRECT_C_ABI and not policy.entrypoint_symbol:
        raise ValueError(f"Semantic function {policy.owner_path!r} has a direct entrypoint without a linkable symbol")
    if policy.entrypoint_action is NativeEntrypointAction.DIRECT_C_ABI and policy.entrypoint_diagnostics:
        raise ValueError(f"Semantic function {policy.owner_path!r} has an inconsistent direct entrypoint action")
    incomplete_slots = [
        slot.native_position
        for slot in policy.native_call_slots
        if slot.projection_action is EntrypointProjectionAction.BLOCKED
        or slot.entrypoint_passing is EntrypointPassingConvention.BLOCKED
        or slot.entrypoint_optionality is EntrypointOptionalityAction.BLOCKED
    ]
    if incomplete_slots:
        raise ValueError(
            f"Semantic function {policy.owner_path!r} has incomplete native entrypoint slots {incomplete_slots}"
        )
    return policy


def build_callback_handoff_policy(
    semantic_type: models.SemanticType,
    *,
    owner_path: str,
) -> CallbackHandoffPolicy:
    """Complete one immediate callback's ABI, transfers, lifecycle, and blockers.

    The semantic type must carry a resolved callback prototype and nested
    ownership decisions.  The returned record is consumed by wrapper policy
    and planning; unsupported signatures remain represented with blockers.
    """
    # Validate the call-scoped callback envelope before inspecting its signature.
    raw_arguments = semantic_type.metadata.get("callback_arguments")
    return_type = semantic_type.metadata.get("return")
    blockers = list(_callback_envelope_blockers(semantic_type))
    if not isinstance(raw_arguments, list) or not all(
        isinstance(argument, models.SemanticArgument) for argument in raw_arguments
    ):
        blockers.append("callback signature is missing ordered argument records")
        arguments: tuple[CallbackTransferPolicy, ...] = ()
    else:
        # Complete each callback transfer and collect signature-level failures.
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
    # Complete the shared exact signature after argument and result ABI facts exist.
    prototype_ref = semantic_type.metadata.get(models.PROTOTYPE_REF_METADATA)
    source_name = prototype_ref.get("name") if isinstance(prototype_ref, dict) else None
    local_name = prototype_ref.get("local_name") if isinstance(prototype_ref, dict) else None
    origin_module = prototype_ref.get("origin_module") if isinstance(prototype_ref, dict) else None
    if not isinstance(source_name, str) or not source_name:
        blockers.append("callback argument requires a resolved named prototype")
        source_name = semantic_type.name
    if not isinstance(local_name, str) or not local_name:
        local_name = semantic_type.name
    prototype = _procedure_prototype_policy(
        owner_path=owner_path,
        name=local_name,
        identity=f"{origin_module or owner_path}.{source_name}",
        pure=_prototype_metadata_is_pure(semantic_type.metadata.get("prototype_metadata")),
        source_language=semantic_type.metadata.get("prototype_source_language"),
        native_abi=semantic_type.metadata.get("prototype_native_abi"),
        arguments=tuple(raw_arguments) if isinstance(raw_arguments, list) else (),
        result=return_type if isinstance(return_type, models.SemanticType) else None,
    )
    if prototype.pure:
        blockers.append(
            "pure @prototype cannot be used as a Python callback because its adapter calls the Python runtime"
        )
    return CallbackHandoffPolicy(
        owner_path=owner_path,
        prototype=prototype,
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


def _procedure_prototype_policy(
    *,
    owner_path: str,
    name: str,
    identity: str,
    pure: bool,
    source_language: str | None,
    native_abi: str | None,
    arguments: tuple[models.SemanticArgument, ...],
    result: models.SemanticType | None,
) -> ProcedurePrototypePolicy:
    """Project one semantic signature for callback and direct-procedure uses."""
    return ProcedurePrototypePolicy(
        owner_path=f"{owner_path}.prototype",
        name=name,
        identity=identity,
        pure=pure,
        source_language=source_language,
        native_abi=native_abi,
        arguments=tuple(_semantic_prototype_argument_policy(argument, owner_path=owner_path) for argument in arguments),
        result=(
            _semantic_prototype_result_policy(result, owner_path=owner_path)
            if result is not None and result.name != "None"
            else None
        ),
    )


def _prototype_metadata_is_pure(metadata: object) -> bool:
    """Return the one purity fact retained by a semantic prototype reference."""
    attributes = metadata.get("fortran_attributes", ()) if isinstance(metadata, dict) else ()
    return any(str(attribute).casefold() == "pure" for attribute in attributes)


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
        intent=(
            str(intent)
            if (intent := argument.origin.metadata.get(models.PROTOTYPE_INTENT_METADATA)) is not None
            else None
        ),
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
    """Select callback copy direction from the prototype's exact dummy intent."""
    semantic_type = argument.semantic_type
    intent = argument.origin.metadata.get(models.PROTOTYPE_INTENT_METADATA)
    if intent == "out":
        return CallbackTransferAction.COPY_OUT
    if intent == "inout":
        return CallbackTransferAction.COPY_IN_OUT
    if (
        intent == "in"
        or bool(argument.origin.metadata.get("value"))
        or (semantic_type.name in _PLAN_PRIMITIVE_SCALAR_TYPES and int(semantic_type.rank or 0) == 0)
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
        intent=None,
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy] | None = None,
    class_call: ClassMethodPolicy | None = None,
    module_export: bool | None = None,
    polymorphic_variants: Mapping[tuple[str, str], tuple[tuple[str, str], ...]] | None = None,
    native_dispatch_name: str | None = None,
) -> FunctionWrapperPolicy:
    """Build a complete wrapper-facing function policy from post-IR decisions.

    Use this only after ownership, callback, status, and export policy are
    complete.  It preserves signature and projection order while producing
    arguments, results, native call slots, lifecycle actions, and all support
    blockers.  The input function is read without mutation; callers normally
    store the returned record in its resolved-policy metadata.
    """

    # Freeze the facts shared by every function-policy step so native-slot,
    # argument, and result completion cannot receive different ambient inputs.
    context = _FunctionPolicyContext(
        function=function,
        owner_path=owner_path,
        derived_types=immutabledict(derived_types or {}),
        polymorphic_variants=immutabledict(polymorphic_variants or {}),
        class_call=class_call,
    )
    # Establish native ABI order before projecting Python-visible arguments.
    argument_native_positions, native_call_slots, slot_blockers = _native_call_slot_policies(context)
    arguments, argument_blockers = _argument_policies(
        context,
        argument_native_positions,
        native_call_slots,
    )
    # Complete result representation and declaration call targets, then bind
    # every array-extent producer to its immutable role.
    results, result_blockers = _result_policies(context)
    if function.origin.source_language == "c":
        arguments, results, native_call_slots = _normalize_c_direct_scalar_identities(
            function,
            arguments,
            results,
            native_call_slots,
        )
    declaration_callables = _function_declaration_callable_policies(function, owner_path)
    arguments, results, native_call_slots = _complete_function_array_extent_policies(
        function,
        owner_path,
        arguments,
        results,
        native_call_slots,
        declaration_callables,
    )
    arguments, native_call_slots = _complete_direct_descriptor_handoffs(
        function,
        arguments,
        native_call_slots,
    )
    # Record ordered writeback, cleanup, and ownership-transfer lifecycle work.
    writeback_actions, lifecycle_blockers = _lifecycle_policies(arguments)
    cleanup_actions, release_actions = _derived_result_lifecycle_policies(results)
    status_error = _completed_native_status_error_policy(function)
    native_module = _native_module(function, owner_path)
    native_call_slots = _complete_entrypoint_slot_policies(arguments, results, native_call_slots)
    # Aggregate all support validation before exposing the immutable plan input.
    blockers = (
        _function_shape_blockers(function, class_call)
        + argument_blockers
        + result_blockers
        + slot_blockers
        + lifecycle_blockers
        + _result_position_blockers(results, arguments)
        + _array_extent_reference_blockers(arguments, results)
        + tuple(blocker for callable_policy in declaration_callables for blocker in callable_policy.blockers)
        + _runtime_status_plan_blockers(status_error)
        + _string_result_status_blockers(results, status_error)
        + _string_writeback_status_blockers(arguments, status_error)
    )
    native_name = native_dispatch_name or _native_name(function)
    native_invocation, native_operator = _native_invocation_policy(native_name)
    standalone = _is_standalone(function)
    arguments, native_call_slots, entrypoint_action, entrypoint_symbol, entrypoint_diagnostics = (
        _complete_function_entrypoint_route(
            function,
            class_call=class_call,
            native_invocation=native_invocation,
            arguments=arguments,
            results=results,
            slots=native_call_slots,
        )
    )
    # Only a C-source operation carries an exact C declaration plan. A Fortran
    # ``bind(C)`` procedure keeps its established backend-projected prototype,
    # which is the only route that can lower strings, derived objects, and
    # callbacks through the shared direct entrypoint.
    direct_c_abi = (
        _completed_direct_c_abi_policy(function, arguments, results, native_call_slots)
        if entrypoint_action is NativeEntrypointAction.DIRECT_C_ABI and function.origin.source_language == "c"
        else None
    )
    if function.origin.source_language == "c":
        blockers = (*blockers, *entrypoint_diagnostics)
    return FunctionWrapperPolicy(
        owner_path=owner_path,
        python_exports=completed_python_exports(function, function.name),
        native_name=native_name,
        native_invocation=native_invocation,
        native_operator=native_operator,
        standalone=standalone,
        external_declaration=_external_declaration_mode(
            standalone=standalone,
            native_invocation=native_invocation,
            arguments=tuple(arguments),
            results=results,
            native_call_slots=tuple(native_call_slots),
        ),
        native_module=native_module,
        native_is_subroutine=_native_is_subroutine(function),
        release_gil=bool(function.metadata.get(models.RUNTIME_RELEASE_GIL_METADATA)),
        status_error=status_error,
        class_call=class_call,
        module_export=(
            not bool(function.metadata.get("fortran_type_bound_target")) if module_export is None else module_export
        ),
        supported=not blockers,
        arguments=tuple(arguments),
        results=results,
        native_call_slots=tuple(native_call_slots),
        declaration_callables=declaration_callables,
        blockers=tuple(blockers),
        writeback_actions=writeback_actions,
        cleanup_actions=cleanup_actions,
        release_actions=release_actions,
        entrypoint_action=entrypoint_action,
        entrypoint_symbol=entrypoint_symbol,
        entrypoint_diagnostics=entrypoint_diagnostics,
        direct_c_abi=direct_c_abi,
    )


def _complete_function_entrypoint_route(
    function: models.SemanticFunction,
    *,
    class_call: ClassMethodPolicy | None,
    native_invocation: NativeInvocationKind,
    arguments: list[ArgumentPolicy],
    results: tuple[ResultPolicy, ...],
    slots: tuple[NativeCallSlotPolicy, ...],
) -> tuple[
    list[ArgumentPolicy],
    tuple[NativeCallSlotPolicy, ...],
    NativeEntrypointAction | None,
    str,
    tuple[str, ...],
]:
    """Complete one function's route and route-dependent boundary metadata."""
    entrypoint_diagnostics = _direct_c_abi_ineligibility(
        function,
        class_call=class_call,
        native_invocation=native_invocation,
        arguments=tuple(arguments),
        results=results,
        slots=slots,
    )
    is_c_operation = function.origin.source_language == "c"
    entrypoint_action = (
        NativeEntrypointAction.DIRECT_C_ABI
        if not entrypoint_diagnostics
        else None
        if is_c_operation
        else NativeEntrypointAction.GENERATED_FORTRAN_ADAPTER
    )
    # C policy errors deliberately have no adapter action.  The preliminary
    # route below exists only to finish the policy record; planning rejects the
    # completed unsupported record before it can emit an artifact.
    completed_action = entrypoint_action or NativeEntrypointAction.DIRECT_C_ABI
    arguments = [_complete_entrypoint_argument_route(argument, completed_action) for argument in arguments]
    optionality_by_position = {argument.native_position: argument.entrypoint_optionality for argument in arguments}
    slots = tuple(
        replace(slot, entrypoint_optionality=optionality_by_position[slot.native_position])
        if slot.native_position in optionality_by_position
        else slot
        for slot in slots
    )
    entrypoint_symbol = (
        str(function.origin.native_symbol or function.origin.native_name or function.native_name or function.name)
        if entrypoint_action is NativeEntrypointAction.DIRECT_C_ABI
        else ""
    )
    return arguments, slots, entrypoint_action, entrypoint_symbol, entrypoint_diagnostics


def _normalize_c_direct_scalar_identities(
    function: models.SemanticFunction,
    arguments: list[ArgumentPolicy],
    results: tuple[ResultPolicy, ...],
    slots: tuple[NativeCallSlotPolicy, ...],
) -> tuple[list[ArgumentPolicy], tuple[ResultPolicy, ...], tuple[NativeCallSlotPolicy, ...]]:
    """Copy target-resolved C scalar identities into completed lowering policy.

    C's public ``Int`` spelling intentionally survives semantic conversion,
    while the measured storage identity (for example ``Int32``) is what the
    shared NumPy and binding path consumes.  This is policy normalization, not
    backend inference; source spelling remains in ``c_abi`` provenance.
    """
    # Argument identity is keyed by name: a route-neutral projection may
    # reorder native slots, so a positional map would resolve one argument's
    # Python conversion against another argument's declared type.
    by_name = {argument.name: _c_direct_scalar_name(argument.semantic_type) for argument in function.arguments}
    semantic_by_name = {argument.name: argument for argument in function.arguments}
    slots_by_name = {slot.python_name: slot for slot in slots if slot.python_name is not None}
    normalized_arguments = [
        replace(
            argument,
            semantic_type_name=by_name.get(argument.name) or argument.semantic_type_name,
            native_storage_c_type=(
                _c_direct_argument_storage_type(
                    function,
                    argument.native_position,
                    semantic_argument=semantic_by_name.get(argument.name),
                )
                or (
                    slots_by_name[argument.name].native_scalar_c_type
                    if argument.name in slots_by_name and slots_by_name[argument.name].value_kind == "addr"
                    else None
                )
            ),
            native_array_element_c_type=(
                slots_by_name[argument.name].native_scalar_c_type
                if argument.ownership.kind is ObjectKind.NUMPY_ARRAY and argument.name in slots_by_name
                else None
            ),
            # A C payload is bytes plus whatever length the contract passes.
            # Refusing an embedded NUL would impose a terminator convention
            # that belongs to the C author, not to PRIK.
            character_allows_embedded_nul=argument.semantic_type_name == "String",
        )
        for argument in arguments
    ]
    return_name = _c_direct_scalar_name(function.return_type)

    def normalize_result(result: ResultPolicy) -> ResultPolicy:
        if result.source_kind == "direct_return" and return_name is not None:
            return replace(
                result,
                semantic_type_name=return_name,
                direct_result_abi=DirectResultABI.NATIVE_SCALAR,
                bridge_data_action=BridgeDataAction.DIRECT_TRANSFER,
                bridge_copy_reason=None,
            )
        projected_name = by_name.get(result.native_name)
        return replace(result, semantic_type_name=projected_name) if projected_name is not None else result

    normalized_results = tuple(normalize_result(result) for result in results)
    # Only a slot that transports one visible argument inherits that argument's
    # identity.  A binding-owned extent, length, presence, or literal slot owns
    # its own completed type and must keep it.
    normalized_slots = tuple(
        replace(slot, semantic_type_name=by_name.get(slot.python_name) or slot.semantic_type_name)
        if slot.python_name is not None
        else slot
        for slot in slots
    )
    return normalized_arguments, normalized_results, normalized_slots


def _complete_entrypoint_argument_route(
    argument: ArgumentPolicy,
    action: NativeEntrypointAction,
) -> ArgumentPolicy:
    """Project a selected route into one argument's completed ABI metadata."""
    uses_adapter = action is NativeEntrypointAction.GENERATED_FORTRAN_ADAPTER
    return replace(
        argument,
        entrypoint_pass_character_length=(
            uses_adapter
            and (
                argument.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER
                # Rank-zero NumPy string storage always reports the caller's
                # itemsize beside the address, declared width or not, so the
                # adapter has one shape to receive. A raw string address is the
                # exception: the caller hands over a bare integer with no Python
                # object to measure, so its width can only be the declared one.
                or (
                    argument.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
                    and argument.semantic_type_name == "String"
                    and argument.native_barrier_action is NativeBarrierAction.PASS_STORAGE_ADDRESS
                )
            )
        ),
        entrypoint_pass_array_metadata=(uses_adapter and argument.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER),
        entrypoint_pass_descriptor_presence=(uses_adapter and argument.optional_mode is OptionalMode.DESCRIPTOR),
        entrypoint_pass_derived_transaction=(uses_adapter and argument.derived_call is not None),
        entrypoint_pass_callback_parameter=(
            action is NativeEntrypointAction.DIRECT_C_ABI and argument.callback is not None
        ),
        entrypoint_optionality=(
            EntrypointOptionalityAction.EXPLICIT_NATIVE_PRESENCE
            if uses_adapter and argument.optional_mode is OptionalMode.DESCRIPTOR
            else argument.entrypoint_optionality
        ),
    )


def _complete_direct_descriptor_handoffs(
    function: models.SemanticFunction,
    arguments: list[ArgumentPolicy],
    slots: tuple[NativeCallSlotPolicy, ...],
) -> tuple[list[ArgumentPolicy], tuple[NativeCallSlotPolicy, ...]]:
    """Select persistent standard descriptors for Fortran C-ABI candidates."""
    if function.origin.source_language != "fortran" or function.origin.native_abi != "c":
        return arguments, slots
    upgraded_by_position: dict[int, NativeArrayHandleWrapperPolicy] = {}
    completed_arguments = []
    for argument in arguments:
        handle = argument.native_array_handle
        if (
            handle is not None
            and handle.handle_kind
            in {
                NativeArrayHandleKind.ARGUMENT_DESCRIPTOR,
                NativeArrayHandleKind.OPTIONAL_ABSENT_HANDLE,
            }
            and argument.rank > 0
            and argument.semantic_type_name in _PLAN_PRIMITIVE_SCALAR_TYPES
        ):
            handle = replace(
                handle,
                handoff=replace(handle.handoff, abi=NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR),
                default_handle=replace(
                    handle.default_handle,
                    construction=NativeArrayDefaultConstruction.LAZY_OWNED_DESCRIPTOR,
                ),
            )
            upgraded_by_position[argument.native_position] = handle
            argument = replace(argument, native_array_handle=handle)
        completed_arguments.append(argument)
    completed_slots = tuple(
        replace(slot, native_array_handle=upgraded_by_position[slot.native_position])
        if slot.native_position in upgraded_by_position
        else slot
        for slot in slots
    )
    return completed_arguments, completed_slots


def _native_invocation_policy(native_name: str) -> tuple[NativeInvocationKind, str | None]:
    """Classify procedure, defined-operator, and defined-assignment syntax once."""
    compact = "".join(native_name.split()).casefold()
    if compact == "assignment(=)":
        return NativeInvocationKind.DEFINED_ASSIGNMENT, "="
    if compact.startswith("operator(") and compact.endswith(")"):
        return NativeInvocationKind.DEFINED_OPERATOR, compact[len("operator(") : -1]
    return NativeInvocationKind.PROCEDURE, None


def _argument_passes_by_value(
    argument: models.SemanticArgument,
    slot: NativeCallSlotPolicy | None,
) -> bool:
    """Return the original declared value transport without backend inference."""
    if "value" in argument.origin.metadata:
        return bool(argument.origin.metadata["value"])
    if slot is None:
        return False
    return slot.value_kind == "value" or slot.native_barrier_action is NativeBarrierAction.PASS_VALUE


def _argument_entrypoint_passing(
    function: models.SemanticFunction,
    argument: models.SemanticArgument,
    boundary: _ArgumentBoundaryPolicy,
    slot: NativeCallSlotPolicy | None,
    callback: CallbackHandoffPolicy | None,
) -> EntrypointPassingConvention:
    """Complete one C parameter transport from already completed boundary facts."""
    if callback is not None:
        return EntrypointPassingConvention.RUNTIME_HANDLE
    if function.origin.source_language == "c" and _c_source_pointer_depth_for_argument(function, argument) == 1:
        # Source C's conservative ``T *`` default is one scalar local whose
        # address crosses the direct entrypoint. Array promotion is an edited
        # semantic contract and arrives below through ARRAY_BUFFER instead.
        return EntrypointPassingConvention.POINTER_REFERENCE
    direct_c_abi = (function.origin.source_language == "fortran" and function.origin.native_abi == "c") or (
        function.origin.source_language == "c"
    )
    if boundary.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
        return EntrypointPassingConvention.C_DESCRIPTOR_POINTER
    if argument.optional:
        return EntrypointPassingConvention.NULLABLE_POINTER
    if direct_c_abi:
        if _argument_passes_by_value(argument, slot):
            return EntrypointPassingConvention.C_VALUE
        return EntrypointPassingConvention.POINTER_REFERENCE
    if boundary.handoff_mode is ArgumentHandoffMode.VALUE:
        return EntrypointPassingConvention.C_VALUE
    if boundary.handoff_mode in {
        ArgumentHandoffMode.TYPED_REFERENCE,
        ArgumentHandoffMode.OPAQUE_ADDRESS,
        ArgumentHandoffMode.CHARACTER_BUFFER,
        ArgumentHandoffMode.ARRAY_BUFFER,
    }:
        return EntrypointPassingConvention.POINTER_REFERENCE
    return EntrypointPassingConvention.BLOCKED


def _argument_entrypoint_optionality(
    function: models.SemanticFunction,
    argument: models.SemanticArgument,
    boundary: _ArgumentBoundaryPolicy,
    slot: NativeCallSlotPolicy | None,
) -> EntrypointOptionalityAction:
    """Complete original native presence independently from the Python surface."""
    if not argument.optional:
        return EntrypointOptionalityAction.REQUIRED
    if boundary.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR:
        return EntrypointOptionalityAction.NULL_C_DESCRIPTOR_POINTER
    if _argument_passes_by_value(argument, slot):
        return EntrypointOptionalityAction.ADAPTER_SIDE_FORTRAN_OMISSION
    if (function.origin.source_language == "fortran" and function.origin.native_abi == "c") or (
        function.origin.source_language == "c"
    ):
        return EntrypointOptionalityAction.NULL_POINTER
    return EntrypointOptionalityAction.ADAPTER_SIDE_FORTRAN_OMISSION


def _complete_entrypoint_slot_policies(
    arguments: list[ArgumentPolicy],
    results: tuple[ResultPolicy, ...],
    slots: tuple[NativeCallSlotPolicy, ...],
) -> tuple[NativeCallSlotPolicy, ...]:
    """Attach binding projection, passing, and presence decisions to ordered slots."""
    arguments_by_position = {argument.python_position: argument for argument in arguments}
    results_by_native_position = {
        result.native_position: result
        for result in results
        if result.source_kind == "hidden_output" and result.native_position is not None
    }
    completed = []
    for slot in slots:
        argument = arguments_by_position.get(slot.python_position) if slot.python_position is not None else None
        result = results_by_native_position.get(slot.native_position)
        projection_action = _entrypoint_projection_action(slot)
        if result is not None:
            passing = result.entrypoint_passing
            optionality = EntrypointOptionalityAction.REQUIRED
        elif projection_action is EntrypointProjectionAction.HIDDEN_OUTPUT_STORAGE:
            passing = (
                EntrypointPassingConvention.C_DESCRIPTOR_POINTER
                if slot.native_array_handle is not None or slot.scalar_descriptor is not None
                else EntrypointPassingConvention.OUTPUT_STORAGE
            )
            optionality = EntrypointOptionalityAction.REQUIRED
        elif projection_action in {
            EntrypointProjectionAction.TYPED_LITERAL,
            EntrypointProjectionAction.COMPUTED_LENGTH,
            EntrypointProjectionAction.COMPUTED_PRESENCE,
            EntrypointProjectionAction.COMPUTED_SHAPE,
            EntrypointProjectionAction.COMPUTED_STRIDE,
        }:
            passing = EntrypointPassingConvention.C_VALUE
            optionality = EntrypointOptionalityAction.REQUIRED
        elif argument is not None:
            optionality = argument.entrypoint_optionality
            if optionality in {
                EntrypointOptionalityAction.NULL_POINTER,
                EntrypointOptionalityAction.ADAPTER_SIDE_FORTRAN_OMISSION,
            }:
                passing = EntrypointPassingConvention.NULLABLE_POINTER
            elif projection_action is EntrypointProjectionAction.ARGUMENT_DEFAULT:
                passing = argument.entrypoint_passing
            elif projection_action is EntrypointProjectionAction.ARGUMENT_ADDRESS:
                passing = EntrypointPassingConvention.POINTER_REFERENCE
            elif projection_action is EntrypointProjectionAction.ARGUMENT_VALUE:
                passing = EntrypointPassingConvention.C_VALUE
            else:
                passing = argument.entrypoint_passing
        elif projection_action is EntrypointProjectionAction.WORK_STORAGE:
            passing = EntrypointPassingConvention.POINTER_REFERENCE
            optionality = EntrypointOptionalityAction.REQUIRED
        else:
            passing = EntrypointPassingConvention.BLOCKED
            optionality = EntrypointOptionalityAction.BLOCKED
        completed.append(
            replace(
                slot,
                projection_action=projection_action,
                entrypoint_passing=passing,
                entrypoint_optionality=optionality,
            )
        )
    return tuple(completed)


def _entrypoint_projection_action(slot: NativeCallSlotPolicy) -> EntrypointProjectionAction:
    """Map one normalized projection kind to its binding-owned materialization."""
    if slot.source_kind == "literal" or slot.value_kind == "literal":
        return EntrypointProjectionAction.TYPED_LITERAL
    if slot.source_kind == "result":
        return EntrypointProjectionAction.HIDDEN_OUTPUT_STORAGE
    if slot.native_array_handle is not None:
        return EntrypointProjectionAction.DESCRIPTOR
    if slot.callback is not None:
        return EntrypointProjectionAction.RUNTIME_HANDLE
    return {
        "addr": EntrypointProjectionAction.ARGUMENT_ADDRESS,
        "arg": EntrypointProjectionAction.ARGUMENT_DEFAULT,
        "value": EntrypointProjectionAction.ARGUMENT_VALUE,
        "is_present": EntrypointProjectionAction.COMPUTED_PRESENCE,
        "len": EntrypointProjectionAction.COMPUTED_LENGTH,
        "shape": EntrypointProjectionAction.COMPUTED_SHAPE,
        "stride": EntrypointProjectionAction.COMPUTED_STRIDE,
        "work": EntrypointProjectionAction.WORK_STORAGE,
        "allocatable": EntrypointProjectionAction.DESCRIPTOR,
        "pointer": EntrypointProjectionAction.DESCRIPTOR,
        "pass": EntrypointProjectionAction.ARGUMENT_ADDRESS,
    }.get(slot.value_kind, EntrypointProjectionAction.BLOCKED)


def _direct_c_abi_ineligibility(
    function: models.SemanticFunction,
    *,
    class_call: ClassMethodPolicy | None,
    native_invocation: NativeInvocationKind,
    arguments: tuple[ArgumentPolicy, ...],
    results: tuple[ResultPolicy, ...],
    slots: tuple[NativeCallSlotPolicy, ...],
) -> tuple[str, ...]:
    """Return completed direct-route blockers without choosing an adapter."""
    if function.origin.source_language == "c":
        return _direct_c_operation_ineligibility(function, arguments=arguments, results=results, slots=slots)
    if function.origin.source_language != "fortran" or function.origin.native_abi != "c":
        return ("original procedure has no Fortran C ABI fact",)

    reasons = list(
        _direct_operation_ineligibility(
            function,
            class_call=class_call,
            native_invocation=native_invocation,
        )
    )
    for argument in arguments:
        reasons.extend(_direct_argument_ineligibility(argument))
    for result in results:
        reasons.extend(_direct_result_ineligibility(result))
    for slot in slots:
        reasons.extend(_direct_slot_ineligibility(slot))
    return tuple(dict.fromkeys(reasons))


def _direct_c_array_ineligibility(argument: ArgumentPolicy) -> tuple[str, ...]:
    """Validate the selected one-level C-pointer NumPy-array mechanism."""
    reasons = []
    if argument.rank < 1 or argument.rank > 15:
        reasons.append(f"C_DIRECT_ARRAY_RANK:{argument.name}")
    if argument.handoff_mode is not ArgumentHandoffMode.ARRAY_BUFFER or argument.array is None:
        reasons.append(f"C_DIRECT_ARRAY_CONTRACT:{argument.name}")
    if argument.entrypoint_passing is not EntrypointPassingConvention.POINTER_REFERENCE:
        reasons.append(f"C_DIRECT_ARRAY_PASSING:{argument.name}")
    if argument.native_array_handle is not None or argument.derived is not None or argument.callback is not None:
        reasons.append(f"C_DIRECT_ARRAY_CONTRACT:{argument.name}")
    if argument.transformations:
        reasons.append(f"C_DIRECT_ARRAY_TRANSFORMATION:{argument.name}")
    if argument.entrypoint_optionality is not EntrypointOptionalityAction.REQUIRED:
        reasons.append(f"C_DIRECT_NULLABLE_POINTER:{argument.name}")
    if argument.rank > 1 and argument.array is not None and argument.array.order != "ORDER_C":
        reasons.append(f"C_DIRECT_ARRAY_ORDER:{argument.name}")
    return tuple(dict.fromkeys(reasons))


def _direct_c_operation_ineligibility(
    function: models.SemanticFunction,
    *,
    arguments: tuple[ArgumentPolicy, ...],
    results: tuple[ResultPolicy, ...],
    slots: tuple[NativeCallSlotPolicy, ...],
) -> tuple[str, ...]:
    """Return fail-closed blockers for the initial direct-only C lane."""
    semantic_arguments = {argument.name: argument for argument in function.arguments}
    reasons: list[str] = [
        *_direct_c_callable_ineligibility(function),
        *(
            reason
            for argument in arguments
            for reason in _direct_c_argument_source_ineligibility(
                function,
                argument,
                semantic_arguments[argument.name],
            )
        ),
    ]
    if function.return_type is not None and function.return_type.metadata.get("c_type_fact_source") == "fallback":
        reasons.append("C_DIRECT_UNPROBED_PRIMITIVE_ABI:return")
    for argument in arguments:
        if argument.native_array_element_c_type == "_Bool":
            reasons.append(f"C_DIRECT_BOOL_ARRAY:{argument.name}")
        if _is_c_string_argument(argument):
            reasons.extend(_direct_c_string_ineligibility(argument))
        elif argument.rank > 0:
            reasons.extend(_direct_c_array_ineligibility(argument))
        else:
            reasons.extend(_direct_argument_ineligibility(argument))
    for result in results:
        if result.semantic_type_name == "String":
            # Only argument character contracts are adopted. A projected string
            # result would need the owned-allocation protocol the Fortran
            # adapter provides, and C has no adapter to allocate it.
            reasons.append(f"C_DIRECT_UNSUPPORTED_STRING_RESULT:{result.owner_path.rsplit('.', 1)[-1]}")
        reasons.extend(_direct_result_ineligibility(result))
    for slot in slots:
        reasons.extend(
            _direct_slot_ineligibility(
                slot,
                # Only a slot that transports one visible argument carries an
                # adopted C character contract; a hidden output does not.
                character_representation_is_binding_owned=slot.python_name is not None,
            )
        )
    return tuple(dict.fromkeys(reasons))


def _is_c_string_argument(argument: ArgumentPolicy) -> bool:
    """Return whether one completed C argument carries a character contract."""
    return argument.semantic_type_name == "String"


def _direct_c_string_ineligibility(argument: ArgumentPolicy) -> tuple[str, ...]:
    """Validate the adopted rank-zero C character forms.

    A C ``char *`` is a pointer to bytes; the terminator convention belongs to
    the C author.  ``String`` hands over Python's own NUL-terminated buffer for
    a read-only input, and rank-zero string storage hands over the caller's
    NumPy bytes untouched.  Anything else stays fail-closed.
    """
    reasons = []
    if argument.rank != 0:
        reasons.append(f"C_DIRECT_UNSUPPORTED_STRING_CONTRACT:{argument.name}")
    if argument.handoff_mode not in {ArgumentHandoffMode.CHARACTER_BUFFER, ArgumentHandoffMode.OPAQUE_ADDRESS}:
        reasons.append(f"C_DIRECT_UNSUPPORTED_STRING_CONTRACT:{argument.name}")
    if argument.entrypoint_passing is not EntrypointPassingConvention.POINTER_REFERENCE:
        reasons.append(f"C_DIRECT_UNSUPPORTED_STRING_CONTRACT:{argument.name}")
    if argument.entrypoint_optionality is not EntrypointOptionalityAction.REQUIRED:
        reasons.append(f"C_DIRECT_NULLABLE_POINTER:{argument.name}")
    if argument.transformations or argument.derived is not None or argument.callback is not None:
        reasons.append(f"C_DIRECT_UNSUPPORTED_STRING_CONTRACT:{argument.name}")
    if argument.writable and argument.handoff_mode is not ArgumentHandoffMode.OPAQUE_ADDRESS:
        # A borrowed Python payload is immutable and may be interned, so only
        # caller-owned NumPy storage may be written through.
        reasons.append(f"C_DIRECT_IMMUTABLE_STRING_WRITEBACK:{argument.name}")
    return tuple(dict.fromkeys(reasons))


def _direct_c_callable_ineligibility(function: models.SemanticFunction) -> tuple[str, ...]:
    """Return the direct-C blockers owned by one operation's own declaration."""
    raw_abi = function.metadata.get("c_abi")
    source_abi = raw_abi if isinstance(raw_abi, dict) else {}
    result_facts = source_abi.get("result") if isinstance(source_abi.get("result"), dict) else {}
    reasons = []
    if isinstance(raw_abi, dict):
        if source_abi.get("calling_convention") != "c":
            reasons.append("C_DIRECT_UNSUPPORTED_CALLING_CONVENTION")
        if source_abi.get("variadic"):
            reasons.append("C_DIRECT_VARIADIC_FUNCTION")
    if "static" in function.metadata.get("storage", ()):
        reasons.append("C_DIRECT_TRANSLATION_UNIT_LOCAL_SYMBOL")
    if function.origin.native_abi not in {None, "c"}:
        reasons.append("C_DIRECT_UNSUPPORTED_CALLING_CONVENTION")
    if function.return_type is not None:
        if _c_direct_scalar_name(function.return_type) is None:
            reasons.append("C_DIRECT_UNRESOLVED_PRIMITIVE_ABI:return")
        if _c_source_pointer_depth(function, result=True) > 0:
            reasons.append("C_DIRECT_POINTER_RESULT")
    if {"volatile", "_Atomic"} & set(result_facts.get("qualifiers", ())):
        reasons.append("C_DIRECT_UNSUPPORTED_QUALIFIER:return")
    return tuple(reasons)


def _direct_c_argument_source_ineligibility(
    function: models.SemanticFunction,
    argument: ArgumentPolicy,
    semantic_argument: models.SemanticArgument,
) -> tuple[str, ...]:
    """Return the direct-C blockers one argument's preserved source facts prove."""
    semantic_type = semantic_argument.semantic_type
    source_type = _c_source_type_facts(function, argument.native_position)
    pointer_depth = int(source_type.get("pointer_depth", _c_pointer_depth(semantic_type)))
    storage = semantic_type.storage
    reasons = []
    if semantic_type.name == "CFunctionPointer" or source_type.get("has_function_pointer"):
        reasons.append(f"C_DIRECT_CALLBACK:{argument.name}")
    if source_type.get("has_array_declarator"):
        reasons.append(f"C_DIRECT_ARRAY_DECLARATOR:{argument.name}")
    if {"volatile", "_Atomic"} & set(source_type.get("qualifiers", ())):
        reasons.append(f"C_DIRECT_UNSUPPORTED_QUALIFIER:{argument.name}")
    if pointer_depth > 1:
        reasons.append(f"C_DIRECT_POINTER_DEPTH:{argument.name}")
    if _argument_declares_nullable_c_pointer(argument, semantic_type):
        reasons.append(f"C_DIRECT_NULLABLE_POINTER:{argument.name}")
    if storage is not None and storage.metadata.get("address_role") == "raw":
        reasons.append(f"C_DIRECT_RAW_ADDRESS:{argument.name}")
    if _c_direct_scalar_name(semantic_type) is None and not _is_c_string_argument(argument):
        reasons.append(f"C_DIRECT_UNRESOLVED_PRIMITIVE_ABI:{argument.name}")
    if argument.rank > 0 and semantic_type.name in {"Bool", "Bool8"}:
        reasons.append(f"C_DIRECT_BOOL_ARRAY:{argument.name}")
    if pointer_depth and source_type.get("const") and _argument_requests_native_write(argument):
        reasons.append(f"C_DIRECT_CONST_POINTER_OUTPUT:{argument.name}")
    if semantic_type.metadata.get("c_type_fact_source") == "fallback":
        reasons.append(f"C_DIRECT_UNPROBED_PRIMITIVE_ABI:{argument.name}")
    return tuple(reasons)


def _argument_declares_nullable_c_pointer(argument: ArgumentPolicy, semantic_type: models.SemanticType) -> bool:
    """Return whether one C argument was written as a nullable value.

    Subscripted storage loses its ``| None`` spelling during conversion, so the
    recorded annotation fact stands in for it.
    """
    return bool(
        argument.nullable
        or argument.optional
        or " | None" in semantic_type.name
        or semantic_type.metadata.get(NULLABLE_ANNOTATION_METADATA)
    )


def _argument_requests_native_write(argument: ArgumentPolicy) -> bool:
    """Return whether a completed contract expects native writes to be visible."""
    return bool(argument.writable or argument.projects_result or argument.array_copy_out)


def _c_direct_scalar_name(semantic_type: models.SemanticType | None) -> str | None:
    """Return the resolved lowering identity without replacing public C spelling."""
    if semantic_type is None:
        return None
    candidate = semantic_type.dtype or semantic_type.name
    return str(candidate) if candidate in _PLAN_PRIMITIVE_SCALAR_TYPES else None


def _c_source_type_facts(function: models.SemanticFunction, native_position: int) -> dict[str, object]:
    raw_abi = function.metadata.get("c_abi")
    if not isinstance(raw_abi, dict):
        return {}
    parameters = raw_abi.get("parameters")
    if not isinstance(parameters, list) or not 0 <= native_position < len(parameters):
        return {}
    value = parameters[native_position]
    return dict(value) if isinstance(value, dict) else {}


def _c_source_pointer_depth(function: models.SemanticFunction, *, result: bool) -> int:
    raw_abi = function.metadata.get("c_abi")
    if not isinstance(raw_abi, dict):
        return _c_pointer_depth(function.return_type) if result else 0
    value = raw_abi.get("result") if result else None
    return int(value.get("pointer_depth", 0)) if isinstance(value, dict) else 0


def _c_source_pointer_depth_for_argument(
    function: models.SemanticFunction,
    argument: models.SemanticArgument,
) -> int:
    """Return one source C parameter's preserved pointer depth."""
    position = argument.metadata.get("native_position")
    if not isinstance(position, int):
        return 0
    return int(_c_source_type_facts(function, position).get("pointer_depth", 0))


def _c_direct_argument_storage_type(
    function: models.SemanticFunction,
    native_position: int,
    *,
    semantic_argument: models.SemanticArgument | None = None,
) -> str | None:
    """Return the policy-selected local C scalar type for a source C argument.

    The source declaration remains the direct entrypoint prototype, while this
    spelling owns scalar storage passed through a pointer.  Matching it avoids
    aliasing a normalized ``int64_t`` local as a distinct source type such as
    ``long long``.  A type written through a typedef resolves to its underlying
    builtin spelling, because the binding cannot declare a name that only the
    user's headers define.  ``const`` and ``restrict`` qualify the native view,
    not the temporary that receives Python input before the call.
    """
    resolved = _c_typedef_resolved_spelling(
        semantic_argument.semantic_type if semantic_argument is not None else None,
        pointer_depth=0,
        const=False,
    )
    if resolved is not None:
        return resolved
    source_type = _c_source_type_facts(function, native_position)
    spelling = source_type.get("source_spelling")
    if not isinstance(spelling, str):
        return None
    base = spelling.split("*", maxsplit=1)[0]
    words = [word for word in base.split() if word not in _C_POINTEE_QUALIFIER_WORDS]
    return " ".join(words) or None


def _c_pointer_depth(semantic_type: models.SemanticType | None) -> int:
    return int(semantic_type.storage.pointer_depth) if semantic_type is not None and semantic_type.storage else 0


def _completed_direct_c_abi_policy(
    function: models.SemanticFunction,
    arguments: list[ArgumentPolicy],
    results: tuple[ResultPolicy, ...],
    slots: tuple[NativeCallSlotPolicy, ...],
) -> DirectCABIPolicy:
    """Copy the selected C declaration facts into immutable policy output."""
    raw_abi = function.metadata.get("c_abi")
    source_abi = raw_abi if isinstance(raw_abi, dict) else {}
    parameter_source = source_abi.get("parameters") if isinstance(source_abi.get("parameters"), list) else []
    semantic_arguments_by_name = {argument.name: argument for argument in function.arguments}
    argument_policies_by_name = {argument.name: argument for argument in arguments}

    def slot_semantic_type(slot: NativeCallSlotPolicy) -> models.SemanticType | None:
        """Return the declared type of the argument one slot transports.

        A binding-owned extent, length, presence, or literal slot names no
        argument and keeps its own completed identity, so it returns ``None``
        rather than borrowing the type of the argument it was derived from.
        """
        if slot.python_name is None:
            return None
        semantic_argument = semantic_arguments_by_name.get(slot.python_name)
        return semantic_argument.semantic_type if semantic_argument is not None else None

    parameters = tuple(
        _direct_c_abi_type_policy(
            parameter_source[slot.native_position]
            if slot.native_position < len(parameter_source) and isinstance(parameter_source[slot.native_position], dict)
            else None,
            semantic_type=slot_semantic_type(slot),
            semantic_type_name=slot.semantic_type_name,
            pointer_depth=(0 if slot.entrypoint_passing is EntrypointPassingConvention.C_VALUE else 1),
            # A hidden output slot is storage the callee writes into.
            writes_output=slot.source_kind == "result",
            native_scalar_c_type=slot.native_scalar_c_type,
            converts_to_contract_storage=(
                slot.native_scalar_c_type is not None
                and (
                    slot.python_name not in argument_policies_by_name
                    or argument_policies_by_name[slot.python_name].native_array_element_c_type is None
                )
            ),
        )
        for slot in sorted(slots, key=lambda item: item.native_position)
    )
    direct_result = next((result for result in results if result.source_kind == "direct_return"), None)
    result_source = source_abi.get("result") if isinstance(source_abi.get("result"), dict) else None
    result = (
        _direct_c_abi_type_policy(
            result_source,
            semantic_type=function.return_type,
            semantic_type_name=None,
            pointer_depth=0,
            native_scalar_c_type=_native_scalar_c_type(function.return_type),
        )
        if direct_result is not None and function.return_type is not None
        else None
    )
    return DirectCABIPolicy(
        calling_convention=str(source_abi.get("calling_convention", "c")),
        result_transport="value" if result is not None else "void",
        result=result,
        parameters=parameters,
    )


def _direct_c_abi_type_policy(
    source: dict[str, object] | None,
    *,
    semantic_type: models.SemanticType | None,
    semantic_type_name: str | None,
    pointer_depth: int,
    writes_output: bool = False,
    native_scalar_c_type: str | None = None,
    converts_to_contract_storage: bool | None = None,
) -> DirectCABITypePolicy:
    """Normalize preserved source facts or the canonical source-free C form."""
    if semantic_type_name == "String":
        return _direct_c_character_abi_type_policy(source, semantic_type=semantic_type, writes_output=writes_output)
    scalar_name = _c_direct_scalar_name(semantic_type) or semantic_type_name
    if scalar_name is None:
        raise ValueError("C direct ABI policy requires a resolved primitive scalar")
    if scalar_name not in _PLAN_PRIMITIVE_SCALAR_TYPES:
        raise ValueError(f"C direct ABI policy requires a supported scalar, not {scalar_name!r}")
    source = source or {}
    source_pointer_depth = int(source.get("pointer_depth", pointer_depth))
    contract_spelling = semantic_type.metadata.get("c_abi_spelling") if semantic_type is not None else None
    # A source-free contract has no declaration text, but target-sized standard
    # types still name an exact C spelling.  Preserve that spelling at every
    # pointer depth instead of replacing ``int *`` or ``size_t *`` with a
    # same-width fixed-width typedef in the generated prototype.
    native_spelling = None
    if native_scalar_c_type is not None:
        native_spelling = (
            f"{native_scalar_c_type} {'*' * source_pointer_depth}" if source_pointer_depth else native_scalar_c_type
        )
    contract_declaration = (
        f"{contract_spelling} {'*' * source_pointer_depth}"
        if isinstance(contract_spelling, str) and source_pointer_depth
        else contract_spelling
    )
    preserved = source.get("source_spelling") or native_spelling or contract_declaration
    qualifiers = tuple(str(item) for item in source.get("qualifiers", ()))
    const = bool(source.get("const", False))
    declarable = _c_typedef_resolved_spelling(semantic_type, pointer_depth=source_pointer_depth, const=const)
    return DirectCABITypePolicy(
        source_spelling=declarable or (str(preserved) if preserved else None),
        scalar_type_name=scalar_name,
        pointer_depth=source_pointer_depth,
        qualifiers=qualifiers,
        const=const,
        converts_to_contract_storage=(
            native_scalar_c_type is not None if converts_to_contract_storage is None else converts_to_contract_storage
        ),
    )


def _direct_c_character_abi_type_policy(
    source: dict[str, object] | None,
    *,
    semantic_type: models.SemanticType | None,
    writes_output: bool = False,
) -> DirectCABITypePolicy:
    """Return the exact C declaration for one rank-zero character contract.

    A borrowed Python payload is read-only, so it is declared ``const char *``.
    Caller-owned NumPy storage may be written by the callee and is declared
    ``char *``.  The contract states which one it is; PRIK never infers it from
    a C declaration it cannot see.
    """
    source = source or {}
    mutable = writes_output or bool(
        semantic_type is not None and semantic_type.storage is not None and semantic_type.storage.mutable
    )
    preserved = source.get("source_spelling")
    spelling = str(preserved) if isinstance(preserved, str) and preserved else ("char *" if mutable else "const char *")
    return DirectCABITypePolicy(
        source_spelling=spelling,
        scalar_type_name="String",
        pointer_depth=int(source.get("pointer_depth", 1)),
        qualifiers=tuple(str(item) for item in source.get("qualifiers", ())),
        const=bool(source.get("const", not mutable)),
    )


def _native_scalar_c_type(semantic_type: models.SemanticType | None) -> str | None:
    """Resolve one semantic native-call identity marker to its exact C spelling."""
    marker = semantic_type.metadata.get(NATIVE_C_SCALAR_IDENTITY_METADATA) if semantic_type is not None else None
    return NATIVE_C_SCALAR_IDENTITIES.get(marker) if isinstance(marker, str) else None


def _c_typedef_resolved_spelling(
    semantic_type: models.SemanticType | None,
    *,
    pointer_depth: int,
    const: bool,
) -> str | None:
    """Return the underlying builtin spelling of a type written through a typedef.

    The generated binding declares the entrypoint prototype itself, so a
    typedef name that only the user's own headers define cannot appear there.
    A typedef is exactly its underlying type, so substituting the probed
    builtin spelling preserves width, signedness, and representation instead of
    choosing a nearby one; the typedef chain stays recorded on the semantic
    type as provenance.
    """
    if semantic_type is None or not semantic_type.metadata.get("c_typedefs"):
        return None
    primitive = semantic_type.metadata.get("c_primitive") or _c_underlying_type_spelling(semantic_type)
    if not isinstance(primitive, str) or not primitive:
        return None
    declared = f"const {primitive}" if const else primitive
    return f"{declared} {'*' * pointer_depth}" if pointer_depth else declared


def _c_underlying_type_spelling(semantic_type: models.SemanticType) -> str | None:
    """Return the probed builtin spelling recorded for a standard C typedef."""
    for key in ("c_standard_type_fact", "c_type_fact"):
        fact = semantic_type.metadata.get(key)
        underlying = fact.get("underlying_c_type") if isinstance(fact, dict) else None
        if isinstance(underlying, str) and underlying:
            return underlying
    return None


def _direct_operation_ineligibility(
    function: models.SemanticFunction,
    *,
    class_call: ClassMethodPolicy | None,
    native_invocation: NativeInvocationKind,
) -> tuple[str, ...]:
    """Return direct-route blockers owned by the original operation."""
    reasons = []
    if not function.origin.native_symbol:
        reasons.append("C ABI procedure has no linkable native symbol")
    if class_call is not None:
        reasons.append("type-bound or constructor invocation requires a Fortran adapter")
    if native_invocation is not NativeInvocationKind.PROCEDURE:
        reasons.append("defined or generic invocation requires a Fortran adapter")
    return tuple(reasons)


def _direct_argument_ineligibility(argument: ArgumentPolicy) -> tuple[str, ...]:
    """Return direct-route blockers owned by one completed argument policy."""
    callback_supported = _direct_callback_supported(argument.callback)
    descriptor_supported = _direct_descriptor_supported(argument)
    derived_reference_supported = _direct_derived_reference_supported(argument)
    mechanism_supported = any(
        (
            _direct_scalar_supported(argument),
            _direct_array_supported(argument),
            derived_reference_supported,
            callback_supported,
            descriptor_supported,
        )
    )

    reasons = []
    if not mechanism_supported:
        reasons.append(f"argument {argument.name!r} has no adopted direct interoperable mechanism")
    if (
        (argument.callback is not None and not callback_supported)
        or (argument.derived is not None and not derived_reference_supported)
        or (argument.native_array_handle is not None and not descriptor_supported)
    ):
        reasons.append(f"argument {argument.name!r} requires a specialized native handoff")
    if argument.transformations:
        reasons.append(f"argument {argument.name!r} requires representation transformation")
    if argument.scalar_logical_abi is ScalarLogicalABI.NATIVE_KIND_COPY:
        reasons.append(f"argument {argument.name!r} uses non-C Boolean storage")
    if argument.entrypoint_passing is EntrypointPassingConvention.BLOCKED:
        reasons.append(f"argument {argument.name!r} has no completed C passing convention")
    if argument.entrypoint_optionality is EntrypointOptionalityAction.ADAPTER_SIDE_FORTRAN_OMISSION:
        reasons.append(f"argument {argument.name!r} requires adapter-side Fortran omission")
    if argument.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION and not _is_scalar_c_character(argument):
        reasons.append(f"argument {argument.name!r} requires adapter representation work")
    return tuple(reasons)


def _direct_scalar_supported(argument: ArgumentPolicy) -> bool:
    """Return whether one scalar has an adopted interoperable C mechanism."""
    return argument.rank == 0 and (
        argument.semantic_type_name in _PLAN_PRIMITIVE_SCALAR_TYPES or _is_scalar_c_character(argument)
    )


def _direct_array_supported(argument: ArgumentPolicy) -> bool:
    """Return whether one explicit or assumed-size array can use its C pointer."""
    return bool(
        argument.rank > 0
        and (
            argument.semantic_type_name in _PLAN_PRIMITIVE_SCALAR_TYPES
            or (argument.semantic_type_name == "String" and argument.character_length == 1)
        )
        and argument.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER
        and argument.array is not None
        and argument.array.category in {"explicit_shape", "assumed_size"}
    )


def _direct_derived_reference_supported(argument: ArgumentPolicy) -> bool:
    """Return whether one opaque interoperable object can cross by reference."""
    return bool(
        argument.rank == 0
        and argument.derived is not None
        and argument.derived.bind_c
        and argument.derived.native_handoff is DerivedNativeHandoff.REFERENCE
        and argument.derived.storage is DerivedObjectStorage.DIRECT
        and not argument.derived.nullable
        and argument.optional_mode is OptionalMode.REQUIRED
        and argument.entrypoint_passing is EntrypointPassingConvention.POINTER_REFERENCE
    )


def _is_scalar_c_character(argument: ArgumentPolicy) -> bool:
    """Return whether one argument is an interoperable scalar C character."""
    return argument.rank == 0 and argument.semantic_type_name == "String" and argument.character_length == 1


def _direct_result_ineligibility(result: ResultPolicy) -> tuple[str, ...]:
    """Return direct-route blockers owned by one completed result policy."""
    reasons = []
    if result.rank != 0 or result.semantic_type_name not in _PLAN_PRIMITIVE_SCALAR_TYPES:
        reasons.append(f"result {result.owner_path!r} is not a directly supported interoperable scalar")
    if result.derived is not None or result.native_array_handle is not None or result.scalar_descriptor is not None:
        reasons.append(f"result {result.owner_path!r} requires a specialized native handoff")
    if result.transformations or result.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION:
        reasons.append(f"result {result.owner_path!r} requires adapter representation work")
    return tuple(reasons)


def _direct_slot_ineligibility(
    slot: NativeCallSlotPolicy,
    *,
    character_representation_is_binding_owned: bool = False,
) -> tuple[str, ...]:
    """Return direct-route blockers owned by one completed call projection.

    A Fortran character actual needs adapter-side representation work beyond a
    single element.  A C character contract does not: the binding itself hands
    over the caller's bytes, so its caller sets
    ``character_representation_is_binding_owned``.
    """
    reasons = []
    if slot.projection_action is EntrypointProjectionAction.BLOCKED:
        reasons.append(f"native-call slot {slot.native_position} has no binding projection action")
    if slot.entrypoint_passing is EntrypointPassingConvention.BLOCKED:
        reasons.append(f"native-call slot {slot.native_position} has no C passing convention")
    character_slot = slot.semantic_type_name == "String" and (
        character_representation_is_binding_owned or slot.character_length == 1
    )
    if slot.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION and not character_slot:
        reasons.append(f"native-call slot {slot.native_position} requires adapter representation work")
    return tuple(reasons)


def _direct_callback_supported(callback: CallbackHandoffPolicy | None) -> bool:
    """Return whether one immediate callback has an exact scalar C ABI."""
    if (
        callback is None
        or not callback.supported
        or callback.prototype.source_language != "fortran"
        or callback.prototype.native_abi != "c"
    ):
        return False
    transfers = (
        *callback.arguments,
        *((callback.result.transfer,) if callback.result.transfer is not None else ()),
    )
    return all(
        transfer.rank == 0
        and transfer.semantic_type_name in _PLAN_PRIMITIVE_SCALAR_TYPES
        and transfer.derived_type_identity is None
        and transfer.abi in {CallbackABIKind.VALUE, CallbackABIKind.REFERENCE}
        for transfer in transfers
    )


def _direct_descriptor_supported(argument: ArgumentPolicy) -> bool:
    """Return whether one array handle supplies the standard descriptor ABI."""
    handle = argument.native_array_handle
    return bool(
        handle is not None
        and handle.handoff.abi is NativeDescriptorHandoffABI.DIRECT_STANDARD_DESCRIPTOR
        and argument.handoff_mode is ArgumentHandoffMode.NATIVE_DESCRIPTOR
        and argument.entrypoint_passing is EntrypointPassingConvention.C_DESCRIPTOR_POINTER
        and argument.semantic_type_name in _PLAN_PRIMITIVE_SCALAR_TYPES
        and argument.rank > 0
        and argument.derived is None
        and not argument.transformations
    )


def _external_declaration_mode(
    *,
    standalone: bool,
    native_invocation: NativeInvocationKind,
    arguments: tuple[ArgumentPolicy, ...],
    results: tuple[ResultPolicy, ...],
    native_call_slots: tuple[NativeCallSlotPolicy, ...],
) -> ExternalDeclarationMode:
    """Choose the weakest correct native declaration from completed ABI facts."""
    if not standalone:
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
    context: _FunctionPolicyContext,
    argument_native_positions: dict[int, int],
    native_call_slots: tuple[NativeCallSlotPolicy, ...],
) -> tuple[list[ArgumentPolicy], tuple[str, ...]]:
    """Complete visible arguments using fixed context and native-slot products.

    ``context`` supplies the function-wide owner, type indexes, and optional
    class call.  ``argument_native_positions`` and ``native_call_slots`` are
    products of the preceding native-slot step and therefore remain explicit.
    The result contains ordered argument policies plus every support blocker.
    """
    policies: list[ArgumentPolicy] = []
    blockers: list[str] = []
    python_position = 0
    for argument in context.function.arguments:
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
            context,
            argument,
            decision,
            current_python_position,
            native_position,
            _native_call_slot_for_python_position(native_call_slots, current_python_position),
        )
        policies.append(policy)
        blockers.extend(argument_blockers)
    return policies, tuple(blockers)


def _native_call_slot_for_python_position(
    slots: tuple[NativeCallSlotPolicy, ...],
    python_position: int,
) -> NativeCallSlotPolicy | None:
    """Find the completed native-call slot owned by one visible argument.

    A binding-owned producer such as ``Arg(i).shape[0]`` or ``Len(Arg(i))``
    records the Python position of the argument it measures, so it is skipped
    here.  Matching the first position-equal slot would otherwise hand an array
    its own extent slot and lower the buffer as a by-value scalar.
    """
    return next(
        (
            slot
            for slot in slots
            if slot.python_position == python_position and slot.source_kind not in _DERIVED_NATIVE_CALL_SLOT_KINDS
        ),
        None,
    )


def _argument_policy(
    context: _FunctionPolicyContext,
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    python_position: int,
    native_position: int,
    native_slot: NativeCallSlotPolicy | None,
) -> tuple[ArgumentPolicy, tuple[str, ...]]:
    """Complete one visible argument from fixed and position-specific facts.

    ``context`` provides the callable-wide policy environment.  The remaining
    inputs identify this argument's completed ownership and its Python/native
    positions.  The returned pair contains the immutable argument policy and
    any blockers found while constructing it.
    """
    function = context.function
    argument_path = f"{context.owner_path}.{argument.name}"
    scalar_logical_abi, scalar_native_type = _scalar_logical_argument_abi(argument)
    array_logical_abi, array_native_type, array_copy_in, array_copy_out = _array_logical_argument_abi(
        argument,
        decision,
    )
    optional_mode = _optional_mode(argument, decision)
    callback = _callback_handoff_policy(argument)
    array_policy = _array_handoff_policy(argument.semantic_type)
    transformations, transformation_blockers = _argument_transformation_policies(
        argument,
        decision,
        array_policy,
    )
    derived = _argument_derived_handoff(
        argument,
        decision,
        callback,
        argument_path,
        context.derived_types,
    )
    derived_call = _argument_derived_call(argument, decision, callback, native_position)
    polymorphic = _polymorphic_dispatch_policy(
        argument,
        decision,
        derived,
        context.polymorphic_variants,
        owner_path=argument_path,
        force=_is_passed_object_argument(context.class_call, native_position)
        or _is_exported_passed_object_argument(function, native_position),
    )
    bridge_data_action, bridge_copy_reason = _completed_argument_bridge_action(
        argument,
        decision,
        optional_mode,
        native_slot,
        callback,
        derived,
    )
    boundary = _argument_boundary_policy(function, argument, decision, python_position, callback)
    entrypoint_passing = _argument_entrypoint_passing(
        function,
        argument,
        boundary,
        native_slot,
        callback,
    )
    entrypoint_optionality = _argument_entrypoint_optionality(
        function,
        argument,
        boundary,
        native_slot,
    )
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
        context.derived_types,
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
            scalar_logical_abi=scalar_logical_abi,
            scalar_native_type=scalar_native_type,
            array_logical_abi=array_logical_abi,
            array_native_type=array_native_type,
            array_copy_in=array_copy_in,
            array_copy_out=array_copy_out,
            array_writeback_abi=_array_writeback_abi(
                argument.semantic_type,
                decision,
                boundary.handoff_mode,
                array_policy,
                array_logical_abi,
            ),
            optional=argument.optional,
            optional_mode=boundary.optional_mode,
            conversion_phase=boundary.conversion_phase,
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
            character_local=_character_local_policy(argument.semantic_type, decision),
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
            entrypoint_passing=entrypoint_passing,
            entrypoint_optionality=entrypoint_optionality,
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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


def _is_exported_passed_object_argument(function: models.SemanticFunction, native_position: int) -> bool:
    """Reuse passed-object dispatch when its native procedure is also exported."""
    return bool(
        function.metadata.get("fortran_type_bound_target")
        and function.metadata.get("fortran_passed_object_position") == native_position
    )


def _completed_argument_bridge_action(
    argument: models.SemanticArgument,
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
    action, reason = _derived_argument_bridge_data_action(derived, action, reason)
    return _logical_argument_bridge_action(argument, decision, action, reason)


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
            conversion_phase=ArgumentConversionPhase.IMMEDIATE,
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
        conversion_phase=_argument_conversion_phase(decision),
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


def _argument_conversion_phase(decision: OwnershipDecision) -> ArgumentConversionPhase:
    """Schedule stack scalar replacements before allocated replacements."""
    if (
        decision.codegen_action is CodegenAction.COPY_IN_OUT
        and decision.python_barrier_action is not PythonBarrierAction.SCALAR_VALUE
    ):
        return ArgumentConversionPhase.DEFERRED_REPLACEMENT
    return ArgumentConversionPhase.IMMEDIATE


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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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


def _result_policies(context: _FunctionPolicyContext) -> tuple[tuple[ResultPolicy, ...], tuple[str, ...]]:
    """Combine direct and hidden results in their established diagnostic order.

    Hidden-output candidates are collected for every callable.  Subroutines
    return those candidates directly.  Functions prepend one direct-result
    candidate; if that candidate cannot be built, the existing fail-closed
    behavior discards all results while retaining hidden diagnostics first.
    """
    hidden_candidates = _hidden_result_policies(context)
    hidden_results = tuple(candidate.policy for candidate in hidden_candidates if candidate.policy is not None)
    hidden_blockers = tuple(reason for candidate in hidden_candidates for reason in candidate.blockers)
    if context.function.return_type is None:
        return hidden_results, hidden_blockers

    direct = _direct_result_policy(context)
    if direct.policy is None:
        return (), (*hidden_blockers, *direct.blockers)
    return (direct.policy, *hidden_results), (*direct.blockers, *hidden_blockers)


def _direct_result_policy(context: _FunctionPolicyContext) -> _ResultPolicyCandidate:
    """Build one function's direct return from completed ownership facts.

    ``context.function`` must have a return type.  The method validates its
    descriptor, bridge action, and derived-type handoff, then returns either a
    completed ``ResultPolicy`` with blockers or a blocked empty candidate when
    ownership completion is missing.
    """
    function = context.function
    return_type = function.return_type
    if return_type is None:
        raise ValueError("Direct result policy requires a function return type")
    decision = function.metadata.get(models.RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA)
    if not isinstance(decision, OwnershipDecision):
        return _ResultPolicyCandidate(None, ("function result is missing completed ownership policy",))
    result_path = f"{context.owner_path}.return"
    direct_handle = _native_array_handle_wrapper_policy(
        return_type,
        function.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
        result_path,
    )
    scalar_descriptor = _scalar_descriptor_result_policy(
        return_type,
        decision,
        may_be_unallocated=_scalar_descriptor_kind(return_type) == "allocatable",
    )
    blockers = list(_result_blockers(return_type, decision))
    if (
        scalar_descriptor is not None
        and scalar_descriptor.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
        and decision.kind is not ObjectKind.STRING
    ):
        # A character result is moved out through an allocatable dummy, which
        # makes allocation testable; other scalars have no such completed move.
        blockers.append(
            "direct allocatable scalar function results cannot preserve unallocated state; "
            "use an allocatable hidden output projection"
        )
    bridge_data_action, bridge_copy_reason = _result_bridge_data_action(return_type)
    if bridge_data_action is BridgeDataAction.BLOCKED and decision.kind is not ObjectKind.SCALAR:
        blockers.append("result has no completed bridge data action")
    derived = _derived_handoff_policy(
        return_type,
        decision,
        owner_path=result_path,
        origin=DerivedObjectOrigin.WRAPPER_RESULT,
        derived_types=context.derived_types,
    )
    blockers.extend(_derived_type_definition_blockers("result", derived, context.derived_types))
    blockers.extend(
        _allocatable_holder_field_blockers(
            "result",
            derived,
            context.derived_types,
            required=bool(derived is not None and derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER),
        )
    )
    return _ResultPolicyCandidate(
        ResultPolicy(
            owner_path=result_path,
            semantic_type_name=return_type.name,
            rank=int(return_type.rank or 0),
            direct_result_abi=_direct_result_abi(return_type, decision, scalar_descriptor),
            ownership=decision,
            codegen_action=decision.codegen_action,
            python_barrier_action=decision.python_barrier_action,
            native_barrier_action=decision.native_barrier_action,
            storage_mode=decision.storage_mode,
            boundary_storage_mode=decision.boundary_storage_mode or decision.storage_mode,
            bridge_data_action=bridge_data_action,
            bridge_copy_reason=bridge_copy_reason,
            character_length=_character_length(return_type),
            array=_array_handoff_policy(return_type),
            native_array_handle=direct_handle,
            scalar_descriptor=scalar_descriptor,
            derived=derived,
            entrypoint_passing=EntrypointPassingConvention.C_FUNCTION_RETURN,
        ),
        tuple(blockers),
    )


def _hidden_result_policies(context: _FunctionPolicyContext) -> tuple[_ResultPolicyCandidate, ...]:
    """Coordinate hidden-output selection and policy construction.

    A source-generated hidden output is normally a nonoptional Fortran dummy
    such as ``integer, intent(out) :: status``.  Native code receives writable
    storage for that dummy, but Python does not pass an argument; the wrapper
    returns the written value instead.  Not every ``intent(out)`` dummy is
    hidden—for example, ordinary output arrays can remain visible—and edited
    semantic contracts can express the same role directly with ``Return(...)``.
    Therefore this stage recognizes the completed policy facts
    ``projects_result=True`` and ``python_visible=False`` rather than reading
    Fortran ``intent`` again.

    The context supplies one completed semantic function.  This coordinator
    indexes its result projections, omits arguments reserved for runtime-status
    handling, and asks ``_hidden_result_candidate`` to complete each remaining
    hidden output.  For example, a subroutine with hidden ``value`` and
    ``status`` outputs returns only the ``value`` candidate when ``status`` is
    consumed by ``Raises(...)``.
    """
    function = context.function

    # Index result mappings once so each hidden argument has a direct lookup;
    # first-entry-wins preserves the previous ``next(...)`` behavior.
    projections = _hidden_result_projection_index(function)

    # Resolve outputs owned by runtime error handling before ordinary result
    # selection so status and message values are not exposed twice.
    suppressed_outputs = _runtime_status_output_owner_paths(function)

    policies = []
    for argument in function.arguments:
        # Select only non-visible projected arguments that remain ordinary
        # Python results after runtime-status outputs have been removed.
        decision = _hidden_result_ownership(context, argument, suppressed_outputs)
        if decision is None:
            continue

        # Complete the selected argument from its indexed projection and keep
        # any failure beside the candidate that produced it.
        policies.append(
            _hidden_result_candidate(
                context,
                argument,
                decision,
                projections.get(argument.name),
            )
        )
    return tuple(policies)


def _update_result_ownership(argument: models.SemanticArgument) -> OwnershipDecision | None:
    """Return the completed result facet of one caller-supplied string update, if any."""
    return _ownership_decision(argument, models.RESOLVED_UPDATE_RESULT_OWNERSHIP_POLICY_METADATA)


def _hidden_result_projection_index(
    function: models.SemanticFunction,
) -> dict[str, models.ProjectionMapping]:
    """Index the first named result projection for each hidden argument.

    ``function.projection`` may mix arguments, literals, and results.  A result
    mapping represents hidden native output storage—commonly an ``intent(out)``
    dummy—through ``Return(...)``.  This
    helper keeps mappings with both a Python name and result position, keyed by
    that name, and preserves the first match used by the former linear lookup.
    For example, ``Return('value')`` becomes ``{'value': mapping}``, while an
    ordinary ``Arg(0)`` mapping is omitted.
    """
    projections: dict[str, models.ProjectionMapping] = {}
    for mapping in function.projection:
        if mapping.result_position is None or not isinstance(mapping.python_name, str):
            continue
        projections.setdefault(mapping.python_name, mapping)
    return projections


def _hidden_result_ownership(
    context: _FunctionPolicyContext,
    argument: models.SemanticArgument,
    suppressed_outputs: frozenset[str],
) -> OwnershipDecision | None:
    """Return ownership only when an argument is an exposed native output.

    The helper receives one possible native output dummy and the owner paths
    reserved by runtime status handling.  Source parsing may originally have
    classified that dummy from ``intent(out)``, but this policy stage requires
    the completed, source-independent ownership facts
    ``projects_result=True`` and ``python_visible=False``, then rejects a
    reserved path.  For example, hidden ``value`` returns its decision, while
    hidden ``status`` returns ``None`` when ``module.proc.status`` appears in
    ``suppressed_outputs``.

    A caller-supplied string descriptor update is the one shape whose
    result facet is a second completed decision rather than the argument's own,
    so a Python-visible argument reaches this stage through
    ``RESOLVED_UPDATE_RESULT_OWNERSHIP_POLICY_METADATA``.  That facet is an
    ordinary native output: it carries ``python_visible=False`` and is completed,
    validated, and lowered exactly like an ``intent(out)`` descriptor result.
    """
    decision = _update_result_ownership(argument) or _ownership_decision(
        argument,
        models.RESOLVED_OWNERSHIP_POLICY_METADATA,
    )
    if decision is None or not (decision.projects_result and not decision.python_visible):
        return None
    if f"{context.owner_path}.{argument.name}" in suppressed_outputs:
        return None
    return decision


def _hidden_result_candidate(
    context: _FunctionPolicyContext,
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    mapping: models.ProjectionMapping | None,
) -> _ResultPolicyCandidate:
    """Build one hidden result and retain every blocker found while doing so.

    ``argument`` and ``decision`` identify a selected hidden native output
    dummy, commonly a scalar or allocatable ``intent(out)`` argument;
    ``mapping``
    supplies its native and Python result positions.  The helper completes
    descriptor, bridge, logical, and derived handoffs before returning a
    ``ResultPolicy``.  For example, hidden ``doubled`` at native position 1 and
    result position 0 becomes a ``source_kind='hidden_output'`` candidate; a
    missing mapping instead returns ``policy=None`` with a projection blocker.
    """
    if mapping is None:
        return _ResultPolicyCandidate(
            None,
            (f"hidden result {argument.name!r} has no completed return projection",),
        )

    owner_path = f"{context.owner_path}.{argument.name}"
    label = f"hidden result {argument.name!r}"

    # Validate the completed ownership family and result positions before
    # constructing backend-neutral descriptor and bridge details.
    blockers = _hidden_result_blockers(argument, decision, mapping)

    # Complete persistent descriptor behavior for allocatable or pointer
    # arrays; ordinary scalar and array results receive ``None`` here.
    native_array_handle = _native_array_handle_wrapper_policy(
        argument.semantic_type,
        argument.metadata.get(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA),
        owner_path,
    )

    # Preserve nullable rank-zero descriptor state separately from normal
    # scalar results, using the mapping's descriptor kind as the ABI selector.
    scalar_descriptor = _scalar_descriptor_result_policy(
        argument.semantic_type,
        decision,
        descriptor_kind=mapping.value_kind,
    )

    # Select result data movement and then apply any native logical-kind
    # adaptation required for the same hidden argument.
    bridge_data_action, bridge_copy_reason = _native_result_bridge_data_action(
        argument.semantic_type,
        descriptor_kind=mapping.value_kind,
    )
    bridge_data_action, bridge_copy_reason = _logical_argument_bridge_action(
        argument,
        decision,
        bridge_data_action,
        bridge_copy_reason,
    )
    if bridge_data_action is BridgeDataAction.BLOCKED and decision.kind is not ObjectKind.SCALAR:
        blockers = (*blockers, f"{label} has no completed bridge data action")

    # Complete an opaque derived-object handoff only when the semantic type is
    # a wrapped derived type; primitive and ordinary array results use ``None``.
    derived = _derived_handoff_policy(
        argument.semantic_type,
        decision,
        owner_path=owner_path,
        origin=DerivedObjectOrigin.WRAPPER_RESULT,
        derived_types=context.derived_types,
    )

    # Require the referenced derived definition and any allocatable-holder
    # member support before exposing this candidate to wrapper planning.
    blockers = (
        *blockers,
        *_derived_type_definition_blockers(label, derived, context.derived_types),
        *_allocatable_holder_field_blockers(
            label,
            derived,
            context.derived_types,
            required=bool(derived is not None and derived.storage is DerivedObjectStorage.ALLOCATABLE_HOLDER),
        ),
    )

    # Store the completed selections in the immutable result record consumed
    # mechanically by wrapper planning and both generated backends.
    return _ResultPolicyCandidate(
        ResultPolicy(
            owner_path=owner_path,
            semantic_type_name=argument.semantic_type.name,
            rank=int(argument.semantic_type.rank or 0),
            direct_result_abi=DirectResultABI.NOT_APPLICABLE,
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
            python_returned=not argument.metadata.get(models.HIDDEN_NATIVE_OUTPUT_METADATA),
            native_name=mapping.native_name or argument.name,
            native_position=mapping.native_position,
            result_position=int(mapping.result_position),
            native_array_handle=native_array_handle,
            scalar_descriptor=scalar_descriptor,
            derived=derived,
            entrypoint_passing=(
                EntrypointPassingConvention.C_DESCRIPTOR_POINTER
                if native_array_handle is not None or scalar_descriptor is not None
                else EntrypointPassingConvention.OUTPUT_STORAGE
            ),
            updates_argument=_update_result_ownership(argument) is not None,
        ),
        tuple(blockers),
    )


def _native_call_slot_policies(
    context: _FunctionPolicyContext,
) -> tuple[dict[int, int], tuple[NativeCallSlotPolicy, ...], tuple[str, ...]]:
    """Complete ordered native call slots from one fixed function context.

    The returned mapping connects visible Python argument positions to native
    positions; slot records preserve native ABI order and blockers diagnose
    missing completed decisions without mutating ``context.function``.  The
    projected and implicit leaves still receive their exact dependencies.
    """
    if context.function.projection:
        return _projected_native_call_slot_policies(
            context.function,
            context.owner_path,
            context.derived_types,
        )
    return _implicit_native_call_slot_policies(
        context.function,
        context.owner_path,
        context.derived_types,
    )


def _projected_native_call_slot_policies(
    function: models.SemanticFunction,
    owner_path: str,
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
) -> tuple[NativeCallSlotPolicy | None, int | None, tuple[str, ...]]:
    """Dispatch one projection mapping to its literal, result, or argument leaf."""
    native_position = mapping.native_position
    if not isinstance(native_position, int):
        return None, None, ("native-call projection is missing a native position",)
    if mapping.value_kind == "literal":
        slot, blockers = _literal_native_call_slot_policy(mapping, owner_path, native_position)
        return slot, None, blockers
    if mapping.value_kind in {"len", "is_present", "shape", "stride", "work"}:
        slot, blockers = _computed_native_call_slot_policy(mapping, owner_path, native_position)
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


def _computed_native_call_slot_policy(
    mapping: models.ProjectionMapping,
    owner_path: str,
    native_position: int,
) -> tuple[NativeCallSlotPolicy, tuple[str, ...]]:
    """Complete one binding-owned length, presence, shape, stride, or work slot."""
    value_kind = mapping.value_kind
    source_position = _projection_value_argument_position(mapping.value)
    semantic_type_name, cast_blockers = _computed_slot_cast_type(mapping, native_position)
    blockers = list(cast_blockers)
    if value_kind != "work" and source_position is None:
        blockers.append(f"native-call {value_kind} slot {native_position} has no argument source")
    if value_kind == "work":
        blockers.append(f"native-call work slot {native_position} has no completed typed storage policy")
    return (
        NativeCallSlotPolicy(
            owner_path=f"{owner_path}.native_slot_{native_position}",
            native_position=native_position,
            source_kind="computed" if value_kind != "work" else "work",
            python_position=source_position,
            python_name=None,
            native_name=mapping.native_name or f"{value_kind}_{native_position}",
            value_kind=value_kind,
            native_barrier_action=(
                NativeBarrierAction.BLOCKED if value_kind == "work" else NativeBarrierAction.PASS_VALUE
            ),
            codegen_action=(CodegenAction.BLOCKED if value_kind == "work" else CodegenAction.DIRECT_VALUE),
            bridge_data_action=(BridgeDataAction.BLOCKED if value_kind == "work" else BridgeDataAction.DIRECT_TRANSFER),
            bridge_copy_reason=None,
            object_kind=None,
            semantic_type_name=semantic_type_name,
            literal_value=mapping.value,
        ),
        tuple(blockers),
    )


def _computed_slot_cast_type(
    mapping: models.ProjectionMapping,
    native_position: int,
) -> tuple[str, tuple[str, ...]]:
    """Return the type one computed producer is materialized as, and any blockers.

    A computed producer has no Python-visible annotation, so its default native
    identity is ``SizeT``.  A contract may state a different integer identity
    when the native parameter is not a ``size_t``; the binding then materializes
    that type directly instead of a ``size_t``.
    """
    if mapping.value_kind == "is_present":
        return "Bool", ()
    requested = mapping.value_cast
    if requested is None:
        return "SizeT", ()
    if not _is_castable_projection_type(requested):
        message = f"native-call {mapping.value_kind} slot {native_position} cannot be materialized as {requested!r}"
        return "SizeT", (message,)
    return requested, ()


def _is_castable_projection_type(type_name: str) -> bool:
    """Return whether a computed projection may be materialized as this type."""
    return type_name in _PLAN_PRIMITIVE_SCALAR_TYPES and is_integer_semantic_type_name(type_name)


def _projection_value_argument_position(value: object) -> int | None:
    """Return the Arg source nested in one route-neutral computed projection."""
    if not isinstance(value, dict):
        return None
    if value.get("kind") == "arg":
        position = value.get("position")
        return position if isinstance(position, int) and not isinstance(position, bool) else None
    return _projection_value_argument_position(value.get("value"))


def _projected_argument_native_call_slot_policy(
    mapping: models.ProjectionMapping,
    owner_path: str,
    native_position: int,
    python_position: int | None,
    visible_arguments: tuple[models.SemanticArgument, ...],
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
) -> tuple[NativeCallSlotPolicy, tuple[str, ...]]:
    """Construct one completed native slot for a visible projected argument."""
    argument_path = f"{owner_path}.{argument.name}"
    value_kind = _native_argument_value_kind(argument, mapping.value_kind or "arg")
    callback = _callback_handoff_policy(argument)
    scalar_logical_abi, scalar_native_type = _scalar_logical_argument_abi(argument)
    array_logical_abi, array_native_type, array_copy_in, array_copy_out = _array_logical_argument_abi(
        argument,
        decision,
    )
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
            native_scalar_c_type=NATIVE_C_SCALAR_IDENTITIES.get(mapping.native_c_identity),
            native_barrier_action=native_barrier_action,
            codegen_action=codegen_action,
            bridge_data_action=bridge_data_action,
            bridge_copy_reason=bridge_copy_reason,
            object_kind=decision.kind,
            scalar_logical_abi=scalar_logical_abi,
            scalar_native_type=scalar_native_type,
            array_logical_abi=array_logical_abi,
            array_native_type=array_native_type,
            array_copy_in=array_copy_in,
            array_copy_out=array_copy_out,
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
    action, reason = _derived_argument_bridge_data_action(derived, action, reason)
    return _logical_argument_bridge_action(argument, decision, action, reason)


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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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
                native_scalar_c_type=NATIVE_C_SCALAR_IDENTITIES.get(mapping.native_c_identity),
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
                native_scalar_c_type=NATIVE_C_SCALAR_IDENTITIES.get(mapping.native_c_identity),
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
    bridge_data_action, bridge_copy_reason = _logical_argument_bridge_action(
        argument,
        decision,
        bridge_data_action,
        bridge_copy_reason,
    )
    scalar_logical_abi, scalar_native_type = _scalar_logical_argument_abi(argument)
    array_logical_abi, array_native_type, array_copy_in, array_copy_out = _array_logical_argument_abi(
        argument,
        decision,
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
            native_scalar_c_type=NATIVE_C_SCALAR_IDENTITIES.get(mapping.native_c_identity),
            native_barrier_action=decision.native_barrier_action,
            codegen_action=decision.codegen_action,
            bridge_data_action=bridge_data_action,
            bridge_copy_reason=bridge_copy_reason,
            object_kind=decision.kind,
            scalar_logical_abi=scalar_logical_abi,
            scalar_native_type=scalar_native_type,
            array_logical_abi=array_logical_abi,
            array_native_type=array_native_type,
            array_copy_in=array_copy_in,
            array_copy_out=array_copy_out,
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
    character_length = _character_literal_length(literal_type)
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
            semantic_type_name="String" if character_length is not None else literal_type,
            character_length=character_length,
        ),
        tuple(blockers),
    )


def _character_literal_length(literal_type: str | None) -> int | None:
    """Return the declared length of one ``String[n]`` hidden literal type."""
    if literal_type is None:
        return None
    match = re.fullmatch(r"String\[(\d+)\]", literal_type)
    return int(match.group(1)) if match is not None else None


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
    elif _character_literal_length(literal_type) == 1:
        blockers.extend(_character_literal_value_blockers(literal_value, native_position))
    return literal_type if isinstance(literal_type, str) else None, literal_value, blockers


def _character_literal_value_blockers(value: object, native_position: int) -> tuple[str, ...]:
    """Validate the one-byte value carried by a ``String[1]`` literal."""
    prefix = f"native-call literal slot {native_position} declares String[1]"
    if not isinstance(value, str):
        return (f"{prefix} but its value is not a string",)
    if len(value) != 1:
        return (f"{prefix} but its value must contain exactly one character",)
    if ord(value) > 0xFF:
        return (f"{prefix} but its value is not representable as one C char byte",)
    return ()


def _implicit_native_call_slot_policies(
    function: models.SemanticFunction,
    owner_path: str,
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
) -> tuple[dict[int, int], tuple[NativeCallSlotPolicy, ...], tuple[str, ...]]:
    """Build declaration-ordered slots when no explicit native projection exists.

    Every argument consumes its completed ownership/callback/derived policy.
    Missing or unsupported bridge decisions are accumulated as blockers while
    the returned slots preserve source argument order.
    """
    slots: list[NativeCallSlotPolicy] = []
    positions: dict[int, int] = {}
    blockers: list[str] = []
    for position, argument in enumerate(function.arguments):
        decision = _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)
        if decision is None:
            blockers.append(f"implicit native-call slot {position} references argument without completed policy")
            continue
        value_kind = _native_argument_value_kind(argument, "arg")
        scalar_logical_abi, scalar_native_type = _scalar_logical_argument_abi(argument)
        array_logical_abi, array_native_type, array_copy_in, array_copy_out = _array_logical_argument_abi(
            argument,
            decision,
        )
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
            bridge_data_action, bridge_copy_reason = _logical_argument_bridge_action(
                argument,
                decision,
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
                scalar_logical_abi=scalar_logical_abi,
                scalar_native_type=scalar_native_type,
                array_logical_abi=array_logical_abi,
                array_native_type=array_native_type,
                array_copy_in=array_copy_in,
                array_copy_out=array_copy_out,
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
) -> tuple[str, ...]:
    """Require the exact native type definition for a typed value call."""
    if derived is None:
        return ()
    return _derived_type_definition_blockers(f"argument {argument.name!r}", derived, derived_types)


def _derived_type_definition_blockers(
    label: str,
    derived: DerivedHandoffPolicy | None,
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
) -> tuple[str, ...]:
    """Require an exported local wrapper definition for every derived handoff."""
    if derived is None or derived.type_identity in derived_types:
        return ()
    return (f"{label} has no completed wrapper type definition for {derived.type_identity!r}",)


def _allocatable_holder_field_blockers(
    label: str,
    derived: DerivedHandoffPolicy | None,
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy] | None = None,
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
        bind_c=bool(type_policy is not None and type_policy.bind_c),
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


# An abstract type has no instances of its own. Every origin that would declare
# storage of that exact type -- a wrapper-owned holder, or a module variable --
# has nothing to hold, so only a plain concrete object address stays reachable.
# The adapter converts that address to the extension's own type and passes it to
# the `class(...)` dummy through the polymorphic discriminator.
_ABSTRACT_REACHABLE_STORAGES = frozenset({DerivedObjectStorage.DIRECT})
_ABSTRACT_INCOMPATIBLE_STORAGES = frozenset(DerivedObjectStorage) - _ABSTRACT_REACHABLE_STORAGES


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
    abstract_dummy = bool(argument.semantic_type.metadata.get("fortran_abstract_type"))
    cases = tuple(
        _derived_call_case(category, storage, projects_result=decision.projects_result)
        if not (abstract_dummy and storage in _ABSTRACT_INCOMPATIBLE_STORAGES)
        else _derived_incompatible_case(
            storage,
            "abstract-owner-storage",
            (
                f"{argument.semantic_type.name} is an abstract type; a "
                f"{storage.value.replace('_', ' ')} actual would declare storage of that exact "
                "type, which has no instance. Pass a concrete extension instead."
            ),
        )
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
    """Return the compatibility matrix cell for a non-descriptor derived dummy.

    ``category`` distinguishes value from ordinary object dummies; ``storage``
    selects address access, required presence, and target lifetime without
    changing the established matrix.
    """
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
    """Return the supported allocatable-dummy cell or an explicit incompatible result."""
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
    """Return the supported pointer-dummy cell, including projected-writeback rejection.

    Pointer holders and module pointers retain their distinct transaction
    mechanisms.  Other non-projected storage reuses payload input adaptation.
    """
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
    """Create one explicit unsupported derived-actual matrix cell with its diagnostic."""
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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
    precision_blocker = _extended_precision_blocker(argument.semantic_type)
    if precision_blocker is not None:
        blockers.append(f"argument {argument.name!r}: {precision_blocker}")
    blockers.extend(_character_descriptor_blockers(argument, decision))
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
    if (
        decision.codegen_action is CodegenAction.CALL_LOCAL_INPUT
        and decision.projects_result
        and not is_character_descriptor_update(argument.semantic_type.metadata, decision)
    ):
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
    if _character_length(argument.semantic_type) is None and expected_storage is not StorageMode.ALIAS:
        # Rank-zero string storage may leave the capacity assumed: the caller's
        # NumPy buffer carries its own itemsize, which the binding hands to the
        # boundary beside the address. Other address forms still need a
        # declared length.
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
    """Return projected-result action blockers for one argument.

    A projected argument normally replaces or mutates caller-visible storage.
    The deferred-length string update instead keeps a call-local input and
    returns the reallocated value through its own completed result facet.
    """
    if is_character_descriptor_update(argument.semantic_type.metadata, decision):
        return ()
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
        if descriptor_kind is not None:
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
def _direct_result_abi(
    semantic_type: models.SemanticType,
    decision: OwnershipDecision,
    scalar_descriptor: ScalarDescriptorResultPolicy | None,
) -> DirectResultABI:
    """Complete the direct scalar return ABI before wrapper planning."""
    if scalar_descriptor is not None or decision.kind is not ObjectKind.SCALAR or int(semantic_type.rank or 0) != 0:
        return DirectResultABI.NOT_APPLICABLE
    if is_boolean_semantic_type_name(semantic_type.name):
        return DirectResultABI.LOGICAL_LOW_BIT_INT8
    if semantic_type.name in _PLAN_PRIMITIVE_SCALAR_TYPES:
        return DirectResultABI.NATIVE_SCALAR
    return DirectResultABI.NOT_APPLICABLE


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
    precision_blocker = _extended_precision_blocker(semantic_type)
    if precision_blocker is not None:
        blockers.append(f"result: {precision_blocker}")
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
        if descriptor_kind is not None:
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
    """Require one wrapper-owned native descriptor handle result."""
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
        blockers.append(f"{label} native handle must preserve an absent descriptor state")
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
        blockers.append(f"{label} is nullable outside descriptor string results")
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
    """Require native results and visible writebacks to cover one public order.

    A deferred-length string update contributes its position through the result
    facet that carries the reallocated value, so counting the argument again
    would report a duplicate for one public output.
    """
    positions = tuple(result.result_position for result in results) + tuple(
        argument.result_position
        for argument in arguments
        if argument.projects_result and not argument.projects_character_descriptor_update
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
    has_native_c_scalar_identity = any(
        mapping.native_c_identity is not None for mapping in function.projection
    ) or bool(function.return_type is not None and function.return_type.metadata.get(NATIVE_C_SCALAR_IDENTITY_METADATA))
    if has_native_c_scalar_identity and function.origin.source_language != "c":
        blockers.append("native C scalar identities require a C native contract")
    return tuple(blockers)


def _completed_native_status_error_policy(
    function: models.SemanticFunction,
) -> NativeStatusErrorPolicy | None:
    """Return the status-error record completed upstream, without reconstructing it."""
    policy = function.metadata.get(models.RESOLVED_RUNTIME_STATUS_ERROR_POLICY_METADATA)
    return policy if isinstance(policy, NativeStatusErrorPolicy) else None


def _runtime_status_output_owner_paths(function: models.SemanticFunction) -> frozenset[str]:
    """Return stable owner paths for the status and optional message native outputs."""
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
    if (
        policy.message is not None
        and policy.message.character_length is None
        and policy.message.python_position is None
    ):
        # Only a hidden message is allocated by the binding, so only a hidden
        # message needs the contract to state the width. A visible argument
        # brings its own storage.
        blockers.append("native status error message requires a fixed positive character length")
    return tuple(blockers)


def _has_deferred_character_length(semantic_type: models.SemanticType) -> bool:
    """Return whether one character value declares a deferred length parameter."""
    return uses_deferred_character_length(semantic_type.metadata)


def _character_local_policy(
    semantic_type: models.SemanticType,
    decision: OwnershipDecision,
) -> CharacterLocalPolicy | None:
    """Complete the adapter-local storage one caller-supplied character input needs.

    The binding always hands the adapter a byte buffer and a length, so the
    only open decision is the Fortran local that buffer is materialized into.
    A dummy with no descriptor attribute keeps a fixed-length local; an
    ``allocatable`` or ``pointer`` dummy needs a local carrying the same
    attribute, and a ``pointer`` local is adapter-allocated storage the adapter
    must also release.
    """
    if int(semantic_type.rank or 0) != 0 or semantic_type.name != "String":
        return None
    plain = CharacterLocalPolicy(
        descriptor_kind=None,
        deferred_length=False,
        release=CharacterLocalRelease.NONE,
    )
    if decision.codegen_action is CodegenAction.COPY_IN_OUT:
        # A replacement writes back through the caller's own buffer, so its
        # local is the fixed-length storage that buffer already sizes.
        return plain
    if decision.codegen_action is not CodegenAction.CALL_LOCAL_INPUT:
        return None
    descriptor = character_descriptor_kind(semantic_type.metadata)
    if descriptor is None:
        return None if _has_deferred_character_length(semantic_type) else plain
    return CharacterLocalPolicy(
        descriptor_kind=NativeArrayDescriptorKind(descriptor),
        deferred_length=_has_deferred_character_length(semantic_type),
        release=_character_local_release(descriptor, decision),
    )


def _character_local_release(descriptor: str, decision: OwnershipDecision) -> CharacterLocalRelease:
    """Return who frees the adapter-local character storage after the call.

    An ``allocatable`` local is released by the compiler when the adapter
    returns.  A ``pointer`` local is storage the adapter allocated itself: a
    read-only dummy cannot change its association, so the adapter always frees
    it, while an update dummy may be reassociated or deallocated by the native
    procedure and is freed only while it still identifies that allocation.
    """
    if descriptor != "pointer":
        return CharacterLocalRelease.NONE
    if decision.projects_result:
        return CharacterLocalRelease.DEALLOCATE_IF_RETAINED
    return CharacterLocalRelease.DEALLOCATE


def _character_descriptor_blockers(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[str, ...]:
    """Restrict descriptor and deferred-length character arguments to completed lanes.

    A Python-visible ``allocatable`` or ``pointer`` character dummy is wrapped
    as one call-local input, optionally paired with the projected result an
    update returns.  Any other action has no completed conversion, so it stops
    here instead of reaching an adapter with nothing to build.  A deferred
    length additionally requires one of those attributes, because
    ``character(len=:)`` is not a declarable local without it.
    """
    semantic_type = argument.semantic_type
    if int(semantic_type.rank or 0) != 0 or semantic_type.name != "String":
        return ()
    descriptor = character_descriptor_kind(semantic_type.metadata)
    deferred = _has_deferred_character_length(semantic_type)
    if not (descriptor or deferred):
        return ()
    label = f"argument {argument.name!r}"
    if descriptor is None:
        return (f"{label} is a deferred-length character argument without an allocatable or pointer attribute",)
    if decision.codegen_action is not CodegenAction.CALL_LOCAL_INPUT:
        return (
            f"{label} is an {descriptor} character argument with action {decision.codegen_action.value}; "
            "only a call-local input, alone or with a projected update result, is wrapped",
        )
    return ()


def _character_length(semantic_type: models.SemanticType) -> int | None:
    """Return a positive fixed Fortran character length, normalizing accepted metadata spellings."""
    return declared_character_length(semantic_type.metadata)


def _lifecycle_policies(
    arguments: list[ArgumentPolicy],
) -> tuple[tuple[LifecyclePolicy, ...], tuple[str, ...]]:
    """Return completed replacement/writeback actions and structural blockers."""
    actions = []
    blockers: list[str] = []
    for argument in arguments:
        if not argument.projects_result:
            continue
        # A string descriptor update publishes its value through the
        # projected descriptor result, so it owns no writeback phase.
        if argument.projects_character_descriptor_update:
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
    """Reject slot positions that do not cover the contiguous native ABI order exactly once."""
    positions = tuple(native_positions)
    if sorted(positions) != list(range(len(positions))):
        return ("native-call slots must cover each native position exactly once in order",)
    return ()


def _ownership_decision(owner: object, metadata_key: str) -> OwnershipDecision | None:
    """Read one typed completed ownership record from metadata, returning ``None`` when absent."""
    decision = getattr(owner, "metadata", {}).get(metadata_key)
    return decision if isinstance(decision, OwnershipDecision) else None


def _is_first_lane_scalar_type(semantic_type: models.SemanticType) -> bool:
    """Report whether a rank-zero primitive uses the supported ordinary scalar lane."""
    return bool(
        int(semantic_type.rank or 0) == 0
        and not _is_scalar_storage_type(semantic_type)
        and semantic_type.name != "String"
        and _is_plan_primitive_value_type(semantic_type)
    )


def _is_plan_primitive_value_type(semantic_type: models.SemanticType) -> bool:
    """Use resolved storage dtype when a source spelling keeps a public alias."""
    return (semantic_type.dtype or semantic_type.name) in _PLAN_PRIMITIVE_SCALAR_TYPES


def _target_long_double_mantissa_bits() -> int:
    """Return the build target's ``long double`` mantissa width, implicit bit included."""
    return int(numpy.finfo(numpy.longdouble).nmant) + 1


def _measured_mantissa_bits(semantic_type: models.SemanticType) -> int | None:
    """Return the compiler-measured mantissa width recorded for one scalar.

    The C probe reports ``precision_bits`` from ``LDBL_MANT_DIG`` and the
    Fortran probe reports ``digits``; both count the implicit bit. A contract
    that declares the type without a source language carries neither.
    """
    for fact_key, field in (("c_type_fact", "precision_bits"), ("fortran_type_fact", "digits")):
        fact = semantic_type.metadata.get(fact_key)
        if isinstance(fact, Mapping):
            measured = fact.get(field)
            if isinstance(measured, int) and measured > 0:
                return int(measured)
    return None


def _extended_precision_blocker(semantic_type: models.SemanticType) -> str | None:
    """Refuse an extended-precision scalar whose measured format the target cannot hold.

    ``Float128`` names the target's ``long double``, which NumPy exposes as
    ``longdouble``. A source declaring a wider mantissa -- Fortran ``real(16)``
    on a target whose ``long double`` is x87 extended precision -- has no NumPy
    representation, and its storage size cannot reveal that on its own.
    """
    if semantic_type.name not in _EXTENDED_PRECISION_SCALAR_TYPES:
        return None
    measured = _measured_mantissa_bits(semantic_type)
    if measured is None or measured == _target_long_double_mantissa_bits():
        return None
    return (
        f"{semantic_type.name} declares a {measured}-bit mantissa but this target's long double "
        f"provides {_target_long_double_mantissa_bits()} bits"
    )


def _is_scalar_storage_type(semantic_type: models.SemanticType) -> bool:
    """Report whether a type carries rank-zero array-backed scalar storage metadata."""
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
    """Return whether a hidden literal type belongs to the scalar input lane.

    A one-character literal joins the lane because it crosses the boundary as
    an interoperable ``char`` value.  A longer fixed-length literal would need
    caller-side storage and a separate length, which this lane does not carry.
    """
    if _character_literal_length(literal_type) == 1:
        return True
    return is_boolean_semantic_type_name(literal_type) or literal_type in {
        "Int32",
        "Float32",
        "Float64",
        "Complex64",
        "Complex128",
    }


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
    may_be_unallocated: bool = False,
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
        may_be_unallocated=may_be_unallocated,
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
        default_handle=_native_array_default_handle_policy(completed, operations, owner_path),
    )


def _native_array_default_handle_policy(
    completed: CompletedNativeArrayHandlePolicy,
    operations: set[NativeArrayOperation],
    owner_path: str,
) -> NativeArrayDefaultHandlePolicy:
    """Translate completed caller-construction lifecycle selectors."""
    construction = _native_array_enum(
        NativeArrayDefaultConstruction,
        completed.default_construction,
        owner_path,
        "default construction",
    )
    if construction is NativeArrayDefaultConstruction.NONE:
        descriptor_ownership = None
    else:
        descriptor_ownership = _native_array_enum(
            NativeArrayDescriptorOwnership,
            completed.default_descriptor_ownership,
            owner_path,
            "default descriptor ownership",
        )
    default_operations = {
        _native_array_enum(NativeArrayOperation, item, owner_path, "default operation")
        for item in completed.default_operations
    }
    if construction is not NativeArrayDefaultConstruction.NONE:
        default_operations.update(
            operation
            for operation in operations
            if operation
            in {
                NativeArrayOperation.SHAPE,
                NativeArrayOperation.ARRAY_ACTUAL,
                NativeArrayOperation.DESCRIPTOR,
                NativeArrayOperation.NATIVE_BYTE_ORDER,
                NativeArrayOperation.ALIGNED,
                NativeArrayOperation.WRITEABLE,
                NativeArrayOperation.LAYOUT,
                NativeArrayOperation.CONTIGUOUS,
            }
        )
    return NativeArrayDefaultHandlePolicy(
        construction=construction,
        descriptor_ownership=descriptor_ownership,
        release=_native_array_enum(
            NativeArrayRelease,
            completed.default_release,
            owner_path,
            "default release",
        ),
        destroy_behavior=_native_array_enum(
            NativeArrayDestroyBehavior,
            completed.default_destroy_behavior,
            owner_path,
            "default destroy behavior",
        ),
        operations=tuple(sorted(default_operations, key=lambda item: item.value)),
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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
    derived_types: Mapping[tuple[str, str], DerivedTypePolicy],
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
    getter_action: ModuleGetterAction,
) -> list[str]:
    """Return Phase 4 blockers for one module variable."""
    blockers = []
    if variable.visibility != "public":
        blockers.append("module variable is not public")
    blockers.extend(_scalar_module_getter_blockers(variable, getter, getter_action))
    blockers.extend(_scalar_module_optional_setter_blockers(setter, descriptor_kind, constant))
    blockers.extend(_scalar_module_constant_value_blockers(variable, getter_action))
    blockers.extend(_scalar_module_initializer_blockers(variable, setter))
    return blockers


def _scalar_module_getter_blockers(
    variable: models.SemanticVariable,
    getter: OwnershipDecision | None,
    getter_action: ModuleGetterAction,
) -> tuple[str, ...]:
    """Validate one completed scalar or literal-string getter."""
    blockers = []
    literal_string = _is_binding_literal_string(variable, getter_action)
    character_value = getter_action is ModuleGetterAction.CHARACTER_VALUE
    # A descriptor character module variable reaches Python through the same
    # nullable snapshot a descriptor scalar uses, carrying a runtime width.
    character_snapshot = (
        getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT and variable.semantic_type.name == "String"
    )
    string_getter = literal_string or character_value
    if not (_is_first_lane_scalar_type(variable.semantic_type) or string_getter or character_snapshot):
        blockers.append("module variable is not a primitive rank-zero scalar")
    if character_value and _character_length(variable.semantic_type) is None:
        blockers.append("character module variable requires one declared length")
    expected_getter_kind = ObjectKind.STRING if string_getter else ObjectKind.SCALAR
    supported_getter_actions = (
        {CodegenAction.COPY_OUT} if string_getter else {CodegenAction.DIRECT_VALUE, CodegenAction.SNAPSHOT_COPY}
    )
    if getter is None:
        blockers.append("module variable is missing completed getter policy")
    elif getter.is_blocked or getter.kind is not expected_getter_kind:
        blockers.append("module variable getter is not a supported scalar policy")
    elif getter.codegen_action not in supported_getter_actions:
        blockers.append(f"module variable getter action {getter.codegen_action.value!r} is unsupported")
    return tuple(blockers)


def _is_binding_literal_string(
    variable: models.SemanticVariable,
    getter_action: ModuleGetterAction,
) -> bool:
    """Return whether the binding materializes one rank-zero string literal."""
    return bool(
        getter_action is ModuleGetterAction.CONSTANT_VALUE
        and variable.semantic_type.name == "String"
        and int(variable.semantic_type.rank or 0) == 0
    )


def _scalar_module_optional_setter_blockers(
    setter: OwnershipDecision | None,
    descriptor_kind: str | None,
    constant: bool,
) -> tuple[str, ...]:
    """Validate presence and consistency of one completed scalar setter."""
    if setter is None:
        return ("module variable is missing completed setter policy",)
    return _scalar_module_setter_blockers(setter, descriptor_kind, constant)


def _scalar_module_constant_value_blockers(
    variable: models.SemanticVariable,
    getter_action: ModuleGetterAction,
) -> tuple[str, ...]:
    """Validate a constant only when its value is binding-owned."""
    if getter_action is not ModuleGetterAction.CONSTANT_VALUE:
        return ()
    if variable.default_value is None:
        return ("scalar module constant is missing its completed value",)
    if not _is_scalar_module_literal(variable.default_value, variable.semantic_type.name):
        return ("scalar module constant value is not a supported literal",)
    return ()


def _scalar_module_initializer_blockers(
    variable: models.SemanticVariable,
    setter: OwnershipDecision | None,
) -> tuple[str, ...]:
    """Validate one optional import-time scalar initializer."""
    initializer = variable.metadata.get(models.RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA)
    if initializer is None:
        return ()
    blockers = []
    if setter is None or setter.setter_action is not SetterAction.WRITE_THROUGH:
        blockers.append("module variable initializer requires a write-through setter")
    if not _is_scalar_module_literal(initializer, variable.semantic_type.name):
        blockers.append("module variable initializer is not a supported scalar literal")
    return tuple(blockers)


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
        if setter.assignment_mode not in {AssignmentMode.VALUE_COPY, AssignmentMode.CHARACTER_COPY}:
            return ("write-through scalar setter requires value-copy native assignment",)
        expected_python_action = (
            PythonBarrierAction.STRING_VALUE if setter.kind is ObjectKind.STRING else PythonBarrierAction.SCALAR_VALUE
        )
        if setter.python_barrier_action is not expected_python_action:
            return (f"write-through scalar setter requires {expected_python_action.value} Python conversion",)
        return ()
    if setter.setter_action is SetterAction.REJECT_REPLACEMENT:
        if descriptor_kind is None:
            return ("rejected scalar replacement requires persistent descriptor storage",)
        return ()
    return (f"non-constant scalar setter action {setter.setter_action.value!r} is unsupported",)


def _scalar_module_getter_action(
    variable: models.SemanticVariable,
    getter: OwnershipDecision | None,
    constant: bool,
) -> ModuleGetterAction:
    """Select scalar module getter behavior from constant and completed getter policy."""
    if constant:
        if _source_parameter_needs_native_getter(variable):
            return ModuleGetterAction.NATIVE_CONSTANT_VALUE
        return ModuleGetterAction.CONSTANT_VALUE
    if getter is not None and getter.codegen_action is CodegenAction.SNAPSHOT_COPY and getter.nullable:
        return ModuleGetterAction.NULLABLE_SNAPSHOT
    if _is_fixed_length_character_scalar(variable):
        # A character value cannot cross the C ABI by value, so it copies
        # through a fixed-width byte buffer the way a character field does.
        return ModuleGetterAction.CHARACTER_VALUE
    return ModuleGetterAction.DIRECT_VALUE


def _is_fixed_length_character_scalar(variable: models.SemanticVariable) -> bool:
    """Return whether one module variable is a rank-zero declared-length character."""
    semantic_type = variable.semantic_type
    return bool(
        semantic_type.name == "String"
        and int(semantic_type.rank or 0) == 0
        and _character_length(semantic_type) is not None
        and character_descriptor_kind(semantic_type.metadata) is None
    )


def _source_parameter_needs_native_getter(variable: models.SemanticVariable) -> bool:
    """Return whether a source parameter value remains compiler-owned."""
    return bool(
        variable.origin.source_language == "fortran"
        and variable.origin.source_kind == "variable"
        and (
            variable.default_value is None
            or not _is_scalar_module_literal(variable.default_value, variable.semantic_type.name)
        )
    )


def _scalar_module_native_assignment(
    setter: OwnershipDecision | None,
    variable: models.SemanticVariable,
) -> AssignmentMode:
    """Project the completed native setter action for bridge lowering.

    A character value has no by-value C ABI, so its write is a distinct native
    mechanism rather than the same value copy a numeric scalar uses.
    """
    if setter is None or setter.setter_action is not SetterAction.WRITE_THROUGH:
        return AssignmentMode.NONE
    if setter.assignment_mode is AssignmentMode.VALUE_COPY and _is_fixed_length_character_scalar(variable):
        return AssignmentMode.CHARACTER_COPY
    return setter.assignment_mode


def _scalar_module_descriptor_kind(variable: models.SemanticVariable) -> str | None:
    """Return the scalar descriptor family recorded on a module variable, if any."""
    metadata = variable.semantic_type.metadata
    if metadata.get("fortran_allocatable"):
        return "allocatable"
    if metadata.get("fortran_pointer"):
        return "pointer"
    return None


def _is_scalar_module_constant(variable: models.SemanticVariable) -> bool:
    """Report whether a module variable is constrained as a semantic constant."""
    return any(constraint.name == "Constant" for constraint in variable.semantic_type.constraints)


def _is_parameter_array(variable: models.SemanticVariable) -> bool:
    """Report whether a fixed Fortran parameter needs immutable-array lowering."""
    return bool(
        variable.origin.source_language == "fortran"
        and variable.origin.source_kind == "variable"
        and int(variable.semantic_type.rank or 0) > 0
        and _is_scalar_module_constant(variable)
    )


def _is_scalar_module_literal(value: object, semantic_type_name: str) -> bool:
    """Report whether a module initializer parses as a supported scalar literal."""
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
    if is_boolean_semantic_type_name(semantic_type_name):
        lowered = text.casefold()
        if lowered in {".true.", "true"}:
            return True
        if lowered in {".false.", "false"}:
            return False
    if semantic_type_name == "String":
        return ast.literal_eval(text)
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
    """Report whether rank-zero scalar storage uses the ordinary array-view bridge path."""
    return (
        optional_mode in _ARRAY_VALUE_OPTIONAL_MODES
        and decision.python_barrier_action is PythonBarrierAction.SCALAR_STORAGE
        and decision.native_barrier_action is NativeBarrierAction.PASS_STORAGE_ADDRESS
        and decision.codegen_action in _ARRAY_VIEW_CODEGEN_ACTIONS
    )


def _copy_in_out_array_bridge_uses_view(decision: OwnershipDecision, optional_mode: OptionalMode) -> bool:
    """Report whether a projected copy-in/out array retains its supported view handoff."""
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
    """Return descriptor-handle bridge movement for a completed descriptor action, else ``None``."""
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
    """Report whether a required raw array address can use the existing view bridge path."""
    return (
        optional_mode is OptionalMode.REQUIRED
        and decision.python_barrier_action is PythonBarrierAction.RAW_ADDRESS
        and decision.native_barrier_action is NativeBarrierAction.PASS_RAW_ADDRESS
        and decision.codegen_action in _RAW_ARRAY_VIEW_CODEGEN_ACTIONS
    )


def _array_storage_bridge_uses_view(decision: OwnershipDecision, optional_mode: OptionalMode) -> bool:
    """Report whether ordinary array storage uses the established contiguous view handoff."""
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


# Logical bridge data policy.
def _fortran_logical_native_type(argument: models.SemanticArgument) -> str | None:
    """Return one exact Fortran logical spelling retained by semantic IR.

    Native-source conversion stores the spelling on the argument origin;
    semantic ``.pyi`` builds attach their probe-resolved spelling to the type
    origin.  The helper consumes either representation without changing it and
    returns ``None`` for non-Fortran or non-logical declarations.
    """
    semantic_type = argument.semantic_type
    origins = (argument.origin, semantic_type.origin)
    source_type = next(
        (
            str(origin.source_type).strip()
            for origin in origins
            if origin.source_language == "fortran" and origin.source_type
        ),
        "",
    )
    if not source_type.casefold().startswith("logical"):
        return None
    declared_bits = next(
        (
            origin.metadata.get("declared_storage_bits")
            for origin in origins
            if isinstance(origin.metadata.get("declared_storage_bits"), int)
        ),
        None,
    )
    if source_type.casefold() == "logical" and isinstance(declared_bits, int) and declared_bits > 0:
        return f"logical(kind={declared_bits // 8})"
    return source_type


def _scalar_logical_argument_abi(
    argument: models.SemanticArgument,
) -> tuple[ScalarLogicalABI, str | None]:
    """Complete exact native-kind storage for one Fortran logical scalar."""
    semantic_type = argument.semantic_type
    if not is_boolean_semantic_type_name(semantic_type.name) or int(semantic_type.rank or 0) != 0:
        return ScalarLogicalABI.NOT_APPLICABLE, None
    source_type = _fortran_logical_native_type(argument)
    if source_type is None:
        if semantic_type.name in {"Bool", "Bool8"}:
            return ScalarLogicalABI.C_BOOL, "logical(c_bool)"
        return ScalarLogicalABI.NATIVE_KIND_COPY, None
    compact = "".join(source_type.casefold().split())
    if compact == "logical(kind=c_bool)":
        return ScalarLogicalABI.C_BOOL, "logical(c_bool)"
    return ScalarLogicalABI.NATIVE_KIND_COPY, source_type


def _array_logical_argument_abi(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
) -> tuple[ArrayLogicalABI, str | None, bool, bool]:
    """Complete native storage and directional copies for a Boolean array.

    The helper consumes semantic type/origin facts and completed ownership.  It
    returns the ABI selector, exact native spelling, and independent copy-in
    and copy-out flags.  Exact ``c_bool`` arrays borrow the NumPy buffer; other
    Fortran logical kinds require a bridge-local representation.
    """
    semantic_type = argument.semantic_type
    if not is_boolean_semantic_type_name(semantic_type.name) or int(semantic_type.rank or 0) <= 0:
        return ArrayLogicalABI.NOT_APPLICABLE, None, False, False
    source_type = _fortran_logical_native_type(argument)
    if source_type is None:
        if semantic_type.name in {"Bool", "Bool8"}:
            return ArrayLogicalABI.C_BOOL_VIEW, "logical(c_bool)", False, False
        copy_in = bool(getattr(argument, "_source_reads_argument", True))
        return ArrayLogicalABI.NATIVE_KIND_COPY, None, copy_in, decision.mutates_native
    if "".join(source_type.casefold().split()) == "logical(kind=c_bool)":
        return ArrayLogicalABI.C_BOOL_VIEW, "logical(c_bool)", False, False
    copy_in = bool(getattr(argument, "_source_reads_argument", True))
    copy_out = decision.mutates_native
    return ArrayLogicalABI.NATIVE_KIND_COPY, source_type, copy_in, copy_out


def _logical_argument_bridge_action(
    argument: models.SemanticArgument,
    decision: OwnershipDecision,
    action: BridgeDataAction,
    reason: str | None,
) -> tuple[BridgeDataAction, str | None]:
    """Select explicit representation copying for a non-C logical argument."""
    abi, _native_type = _scalar_logical_argument_abi(argument)
    if abi is ScalarLogicalABI.NATIVE_KIND_COPY:
        return BridgeDataAction.COPY_REPRESENTATION, LOGICAL_SCALAR_KIND_COPY_REASON
    array_abi, _native_type, _copy_in, _copy_out = _array_logical_argument_abi(argument, decision)
    if array_abi is ArrayLogicalABI.NATIVE_KIND_COPY:
        return BridgeDataAction.COPY_REPRESENTATION, LOGICAL_ARRAY_KIND_COPY_REASON
    return action, reason


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
    if native_array_descriptor_kind(semantic_type) is not None:
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
        and semantic_type.name not in {"String", "Void"}
        and not _is_plan_primitive_value_type(semantic_type)
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
        int(semantic_type.rank or 0) > 0
        and semantic_type.name != "String"
        and not _is_plan_primitive_value_type(semantic_type)
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
    if native_array_descriptor_kind(semantic_type) is not None:
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
def _array_writeback_abi(
    semantic_type: models.SemanticType,
    decision: OwnershipDecision,
    handoff_mode: ArgumentHandoffMode,
    array: ArrayHandoffPolicy | None,
    logical_abi: ArrayLogicalABI,
) -> ArrayWritebackABI:
    """Complete mutable ordinary-array byte normalization before planning.

    Exact-kind logical copies canonicalize bytes while copying out, so only a
    direct ``c_bool`` view needs the separate low-bit normalization pass.
    """
    if array is None or handoff_mode is not ArgumentHandoffMode.ARRAY_BUFFER or not decision.mutates_native:
        return ArrayWritebackABI.NOT_APPLICABLE
    if is_boolean_semantic_type_name(semantic_type.name):
        return (
            ArrayWritebackABI.LOGICAL_LOW_BIT_INT8
            if logical_abi is ArrayLogicalABI.C_BOOL_VIEW
            else ArrayWritebackABI.NOT_APPLICABLE
        )
    return ArrayWritebackABI.NATIVE_ARRAY


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
        character=semantic_type.name == "String",
        category=array.category,
        extent_references=tuple(declaration_extent_references(item) for item in shape),
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
    # A character array may leave its width assumed: every element of a NumPy
    # ``S`` array shares one itemsize, which already travels beside the buffer.
    supported_element = _is_plan_primitive_value_type(semantic_type) or (
        semantic_type.name == "String" and not scalar_storage
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
    """Report whether a handoff policy represents rank-zero scalar array storage."""
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
    supported_element = _is_plan_primitive_value_type(semantic_type) or (
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
        character=semantic_type.name == "String",
        category="raw_address",
        extent_references=tuple(declaration_extent_references(item) for item in shape),
    )


def _complete_function_array_extent_policies(
    function: models.SemanticFunction,
    owner_path: str,
    arguments: list[ArgumentPolicy],
    results: tuple[ResultPolicy, ...],
    native_call_slots: tuple[NativeCallSlotPolicy, ...],
    declaration_callables: tuple[DeclarationCallablePolicy, ...],
) -> tuple[list[ArgumentPolicy], tuple[ResultPolicy, ...], tuple[NativeCallSlotPolicy, ...]]:
    """Resolve callable shape expressions to completed scalar or array-extent roles."""
    scalar_roles, array_roles = _function_array_extent_sources(function, owner_path)
    callable_roles = {
        item.source_name.casefold(): (item.expression_token, item.symbolic_role) for item in declaration_callables
    }

    def complete(array: ArrayHandoffPolicy | None) -> ArrayHandoffPolicy | None:
        if array is None:
            return None
        display_shape = array.display_shape or array.shape
        resolutions = tuple(
            resolve_declaration_extent(expression, scalar_roles, array_roles, callable_roles)
            for expression in array.shape
        )
        return replace(
            array,
            shape=tuple(item.expression for item in resolutions),
            extent_references=tuple(item.references for item in resolutions),
            extent_reference_roles=tuple(item.roles for item in resolutions),
            extent_callable_references=tuple(item.callable_references for item in resolutions),
            extent_callable_roles=tuple(item.callable_roles for item in resolutions),
            extent_evaluation=tuple("bridge" if item.callable_roles else "binding" for item in resolutions),
            extent_blockers=tuple(item.blockers for item in resolutions),
            display_shape=display_shape,
        )

    def complete_argument(argument: ArgumentPolicy) -> ArgumentPolicy:
        """Keep an argument's accepted-actual shape identical to its resolved handoff."""
        array = complete(argument.array)
        native_actual = argument.native_array_actual
        if native_actual is not None and array is not None:
            native_actual = replace(native_actual, shape=array.shape)
        return replace(argument, array=array, native_array_actual=native_actual)

    return (
        [complete_argument(argument) for argument in arguments],
        tuple(replace(result, array=complete(result.array)) for result in results),
        tuple(replace(slot, array=complete(slot.array)) for slot in native_call_slots),
    )


def _function_declaration_callable_policies(
    function: models.SemanticFunction,
    owner_path: str,
) -> tuple[DeclarationCallablePolicy, ...]:
    """Validate and classify every native call appearing in one function's extents."""
    entries: dict[str, tuple[models.SemanticExpressionCallable, list[int], bool]] = {}
    for semantic_type in _function_declaration_types(function):
        storage = semantic_type.storage
        array = storage.array if storage is not None else None
        if array is None:
            continue
        for axis, expression in enumerate(array.shape):
            references = array.expression_callables[axis] if axis < len(array.expression_callables) else ()
            sites = declaration_expression_call_sites(expression)
            for reference in references:
                arities = [
                    site.argument_count
                    for site in sites
                    if site.name.casefold() == reference.name.casefold() and not site.has_keywords
                ]
                keyword_use = any(
                    site.name.casefold() == reference.name.casefold() and site.has_keywords for site in sites
                )
                key = reference.name.casefold()
                if key not in entries:
                    entries[key] = (reference, arities, keyword_use)
                else:
                    entries[key][1].extend(arities)
                    entries[key] = (entries[key][0], entries[key][1], entries[key][2] or keyword_use)
    return tuple(
        _declaration_callable_policy(reference, arities, has_keywords, owner_path, index)
        for index, (reference, arities, has_keywords) in enumerate(entries.values())
    )


def _function_declaration_types(function: models.SemanticFunction) -> tuple[models.SemanticType, ...]:
    """Return function-owned semantic types that may carry declared extents."""
    return tuple(
        semantic_type
        for semantic_type in (
            *(argument.semantic_type for argument in function.arguments),
            function.return_type,
            *(variable.semantic_type for variable in function.locals),
        )
        if isinstance(semantic_type, models.SemanticType)
    )


def _declaration_callable_policy(
    reference: models.SemanticExpressionCallable,
    arities: list[int],
    has_keywords: bool,
    owner_path: str,
    index: int,
) -> DeclarationCallablePolicy:
    """Complete one declaration call as a module import or explicit interface."""
    callable_path = f"{owner_path}.declaration_callable.{reference.name}"
    blockers: list[str] = []
    declaration = reference.declaration
    if has_keywords:
        blockers.append(f"declaration callable {reference.name!r} does not accept keyword syntax")
    if reference.placement == "module" or reference.native_scope is not None:
        action = DeclarationCallableAction.MODULE_IMPORT
        if declaration is not None and declaration.visibility != "public":
            blockers.append(f"module declaration callable {reference.name!r} is not public")
        prototype = None
        if declaration is not None:
            blockers.extend(
                _specification_function_blockers(
                    declaration,
                    arities,
                    label=f"module declaration callable {reference.name!r}",
                    require_exact_reference_intent=False,
                    require_pure_diagnostic=True,
                )
            )
    elif reference.placement == "standalone":
        action = DeclarationCallableAction.STANDALONE_PROCEDURE
        if not isinstance(declaration, models.SemanticPrototype):
            blockers.append(
                f"standalone declaration callable {reference.name!r} requires an exact @prototype signature"
            )
            prototype = None
        else:
            prototype = _direct_prototype_policy(
                declaration,
                owner_path=callable_path,
                local_name=reference.name,
            )
            blockers.extend(_direct_prototype_blockers(declaration, arities))
    else:
        action = DeclarationCallableAction.STANDALONE_PROCEDURE
        prototype = None
        kind = "abstract" if reference.placement == "abstract" else "unresolved"
        blockers.append(f"declaration callable {reference.name!r} has {kind} native placement")
    return DeclarationCallablePolicy(
        owner_path=callable_path,
        source_name=reference.name,
        native_name=reference.native_name or reference.name.rsplit(".", 1)[-1],
        native_scope=reference.native_scope,
        symbolic_role=f"{callable_path}:function",
        expression_token=f"__prik_callable_{index}",
        action=action,
        prototype=prototype,
        blockers=tuple(blockers),
    )


def _direct_prototype_policy(
    prototype: models.SemanticPrototype,
    *,
    owner_path: str,
    local_name: str,
) -> ProcedurePrototypePolicy:
    """Project one directly called signature into the shared prototype model."""
    return _procedure_prototype_policy(
        owner_path=owner_path,
        name=local_name,
        identity=f"{prototype.origin.native_scope or owner_path}.{prototype.name}",
        pure=prototype.pure,
        source_language=prototype.origin.source_language,
        native_abi=prototype.origin.native_abi,
        arguments=tuple(prototype.arguments),
        result=prototype.return_type,
    )


def _semantic_prototype_argument_policy(
    argument: models.SemanticArgument,
    *,
    owner_path: str,
) -> ProcedurePrototypeArgumentPolicy:
    """Copy one semantic prototype dummy into the shared signature model."""
    semantic_type = argument.semantic_type
    return ProcedurePrototypeArgumentPolicy(
        owner_path=f"{owner_path}.prototype_argument.{argument.name}",
        name=argument.name,
        semantic_type_name=semantic_type.name,
        rank=int(semantic_type.rank or 0),
        passed_by_value=bool(argument.origin.metadata.get("value")),
        intent=(
            str(intent)
            if (intent := argument.origin.metadata.get(models.PROTOTYPE_INTENT_METADATA)) is not None
            else None
        ),
        character_length=_character_length(semantic_type),
        array=_array_handoff_policy(semantic_type) if int(semantic_type.rank or 0) > 0 else None,
        derived_type_identity=(
            _derived_type_identity(semantic_type, owner_path) if _is_scalar_derived_type(semantic_type) else None
        ),
    )


def _semantic_prototype_result_policy(
    semantic_type: models.SemanticType,
    *,
    owner_path: str,
) -> ProcedurePrototypeResultPolicy:
    """Copy one semantic prototype result into the shared signature model."""
    return ProcedurePrototypeResultPolicy(
        owner_path=f"{owner_path}.prototype_result",
        semantic_type_name=semantic_type.name,
        rank=int(semantic_type.rank or 0),
        character_length=_character_length(semantic_type),
        array=_array_handoff_policy(semantic_type) if int(semantic_type.rank or 0) > 0 else None,
        derived_type_identity=(
            _derived_type_identity(semantic_type, owner_path) if _is_scalar_derived_type(semantic_type) else None
        ),
    )


def _direct_prototype_blockers(
    prototype: models.SemanticPrototype,
    arities: list[int],
) -> tuple[str, ...]:
    """Require the exact prototype subset supported by direct bridge calls."""
    blockers = list(
        _specification_function_blockers(
            prototype,
            arities,
            label=f"direct prototype {prototype.name!r}",
            require_exact_reference_intent=True,
            require_pure_diagnostic=False,
        )
    )
    if not prototype.pure:
        blockers.insert(
            0,
            f"direct prototype {prototype.name!r} used in a declaration expression must be @pure",
        )
    return tuple(blockers)


def _specification_function_blockers(
    declaration: models.SemanticFunction,
    arities: list[int],
    *,
    label: str,
    require_exact_reference_intent: bool,
    require_pure_diagnostic: bool,
) -> tuple[str, ...]:
    """Validate the scalar-integer specification-function subset used by extents."""
    blockers = []
    if require_pure_diagnostic and not _semantic_function_is_pure(declaration):
        blockers.append(f"{label} must be pure")
    result = declaration.return_type
    if result is None or int(result.rank or 0) != 0 or not _is_integer_extent_scalar(result):
        blockers.append(f"{label} must return one scalar integer")
    if arities and any(arity != len(declaration.arguments) for arity in arities):
        blockers.append(
            f"{label} expects {len(declaration.arguments)} arguments, "
            f"but declaration calls use {tuple(dict.fromkeys(arities))}"
        )
    for argument in declaration.arguments:
        intent = argument.origin.metadata.get(models.PROTOTYPE_INTENT_METADATA)
        passed_by_value = bool(argument.origin.metadata.get("value"))
        if argument.optional:
            blockers.append(f"{label} argument {argument.name!r} cannot be optional")
        if int(argument.semantic_type.rank or 0) != 0 or not _is_integer_extent_scalar(argument.semantic_type):
            blockers.append(f"{label} argument {argument.name!r} must be a scalar integer")
        if intent in {"out", "inout"}:
            blockers.append(f"{label} argument {argument.name!r} cannot be {intent}")
        if require_exact_reference_intent and not passed_by_value and intent != "in":
            blockers.append(f"reference prototype argument {argument.name!r} requires exact In(...) direction")
    return tuple(blockers)


def _semantic_function_is_pure(declaration: models.SemanticFunction | None) -> bool:
    """Return source purity when a module declaration retained that characteristic."""
    if declaration is None:
        return True
    attributes = declaration.metadata.get("fortran_attributes", ())
    return any(str(attribute).casefold() == "pure" for attribute in attributes)


def _function_array_extent_sources(
    function: models.SemanticFunction,
    owner_path: str,
) -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, tuple[str, ...]]]]:
    """Return visible scalar values and concrete input-array extents by source name."""
    scalar_roles: dict[str, tuple[str, str]] = {}
    array_roles: dict[str, tuple[str, tuple[str, ...]]] = {}
    for argument in function.arguments:
        decision = _ownership_decision(argument, models.RESOLVED_OWNERSHIP_POLICY_METADATA)
        if decision is None or not decision.python_visible:
            continue
        argument_path = f"{owner_path}.{argument.name}"
        if int(argument.semantic_type.rank or 0) == 0 and _is_integer_extent_scalar(argument.semantic_type):
            scalar_roles[argument.name.casefold()] = (argument.name, f"{argument_path}:value")
            continue
        array = _array_handoff_policy(argument.semantic_type)
        if array is None or array.rank is None:
            continue
        roles = tuple(f"{argument_path}:extent:{axis}" for axis in range(array.rank))
        array_roles[argument.name.casefold()] = (argument.name, roles)
    return scalar_roles, array_roles


def _is_integer_extent_scalar(semantic_type: models.SemanticType) -> bool:
    """Return whether a visible scalar can safely supply a native array extent.

    Declaration extents consume integer values.  Excluding Boolean, real,
    character, derived, and callback arguments prevents their data pointers or
    payloads from being substituted into generated integer expressions.
    """
    name = semantic_type.name
    return name == "SizeT" or name.startswith("Int") or name.startswith("UInt")


def _array_extent_reference_blockers(
    arguments: list[ArgumentPolicy],
    results: tuple[ResultPolicy, ...],
) -> tuple[str, ...]:
    """Require every declared extent dependency to have a completed visible role."""
    blockers = []
    for owner in (*arguments, *results):
        if owner.array is None:
            continue
        for axis, missing in enumerate(owner.array.extent_blockers):
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


def _native_name(function: models.SemanticFunction) -> str:
    """Return the callable's resolved native spelling, preferring explicit semantic identity."""
    return str(function.native_name or function.origin.native_name or function.name)


def _native_module(function: models.SemanticFunction, owner_path: str) -> str | None:
    """Return the completed native module scope for non-standalone procedures."""
    if _is_standalone(function):
        return None
    return str(function.origin.native_scope or owner_path.split(".", maxsplit=1)[0])


def _native_is_subroutine(function: models.SemanticFunction) -> bool:
    """Return whether the native callable has subroutine call semantics."""
    return function.origin.source_kind == "subroutine" or function.return_type is None


def _is_standalone(function: models.SemanticFunction) -> bool:
    """Report whether a Fortran callable has standalone native placement."""
    return bool(function.origin.source_language == "fortran" and function.origin.native_scope is None)


def _argument_native_name(
    function: models.SemanticFunction,
    python_position: int,
    argument: models.SemanticArgument,
) -> str:
    """Return an argument's projected native spelling, falling back to its semantic name."""
    for mapping in function.projection:
        if mapping.python_position == python_position:
            return mapping.native_name or argument.name
    return argument.name


# Direct wrapper-policy example.


if __name__ == "__main__":
    semantic_function = models.SemanticFunction(
        name="scale",
        arguments=[models.SemanticArgument("value", models.SemanticType("Float64", dtype="Float64"))],
        return_type=models.SemanticType("Float64", dtype="Float64"),
    )
    semantic_argument = semantic_function.arguments[0]
    semantic_argument.metadata[models.RESOLVED_OWNERSHIP_POLICY_METADATA] = OwnershipDecision(
        kind=ObjectKind.SCALAR,
        owner=OwnershipOwner.CALLER,
        transfer=TransferMode.CALL_LOCAL,
        destruction=DestructionPolicy.NONE,
        codegen_action=CodegenAction.CALL_LOCAL_INPUT,
        python_barrier_action=PythonBarrierAction.SCALAR_VALUE,
        native_barrier_action=NativeBarrierAction.PASS_VALUE,
    )
    semantic_function.metadata[models.RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA] = OwnershipDecision(
        kind=ObjectKind.SCALAR,
        owner=OwnershipOwner.PYTHON,
        transfer=TransferMode.BY_VALUE,
        destruction=DestructionPolicy.PYTHON_REFCOUNT,
        codegen_action=CodegenAction.DIRECT_VALUE,
        python_barrier_action=PythonBarrierAction.NONE,
        native_barrier_action=NativeBarrierAction.NONE,
    )
    print(f"before: math.scale({semantic_argument.name}): {semantic_argument.semantic_type.name} semantic IR")
    policy = build_function_wrapper_policy(semantic_function, owner_path="math.scale")
    print(
        f"after: {policy.arguments[0].bridge_data_action.value}; "
        f"result={policy.results[0].direct_result_abi.value}; "
        f"native={policy.native_call_slots[0].native_barrier_action.value}"
    )
