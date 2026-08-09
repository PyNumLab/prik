"""Complete semantic policy decisions after IR construction and before planning.

This module turns full semantic signatures into the ownership, transfer,
destruction, mutability, storage, accessor, projection, and ABI decisions that
wrapper planning consumes.  It is the final semantic authority: lower stages
may dispatch from its completed policies but must not infer replacements.
"""

from __future__ import annotations

from dataclasses import replace
import keyword
import re
from collections.abc import Iterable

from prik.types.numpy import SEMANTIC_SCALAR_TYPE_NAMES
from prik.semantics.ownership import (
    CodegenAction,
    OWNERSHIP_POLICY_METADATA,
    POINTER_POLICY_METADATA,
    OwnershipDecision,
    OwnershipContext,
    ObjectKind,
    SetterAction,
    default_ownership_policy,
    ownership_context_for_argument,
)
from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_PROJECTION,
    ADDRESS_ROLE_RAW,
    BIND_TARGET_METADATA,
    MAYBE_UNALLOCATED_METADATA,
    OPTIONAL_ABSENT_HANDLE_METADATA,
    PROJECTED_OUTPUT_METADATA,
    SCALAR_STORAGE_CATEGORY,
)
from prik.semantics import models
from prik.semantics.native_array_handles import NativeArrayHandlePolicy, native_array_descriptor_kind
from prik.semantics.wrapper_policy import (
    ArgumentPolicy,
    OverloadArgumentPolicy,
    OverloadMatchKind,
    OverloadPolicy,
    ClassInvocationKind,
    ClassMethodKind,
    ClassMethodPolicy,
    ClassSurfacePolicy,
    DerivedFieldPolicy,
    DerivedTypePolicy,
    FunctionWrapperPolicy,
    NativeStatusErrorPolicy,
    NativeStatusOutputPolicy,
    OptionalMode,
    PythonExceptionKind,
    build_class_surface_policy,
    build_callback_handoff_policy,
    build_derived_field_policy,
    build_derived_type_policy,
    build_module_variable_policy,
    build_module_overload_policy,
    build_function_wrapper_policy,
    derived_member_path_policies,
    overload_builtin_scalar_family,
)
from prik.semantics.wrapper_exports import complete_python_export_policy

__all__ = ("complete_semantic_policies",)


_POINTER_ALLOCATE_PERMISSION_VALUES = frozenset(
    {
        "allocate",
        "allocate_resize",
        "reallocate",
        "reassociate_allocate",
    }
)
_POINTER_DEALLOCATE_PERMISSION_VALUES = frozenset(
    {
        "deallocate",
        "deallocate_resize",
        "owner_deallocate",
        "unsafe_deallocate",
        "wrapper_dealloc",
    }
)
_POINTER_RESIZE_PERMISSION_VALUES = frozenset(
    {
        "resize",
        "allocate_resize",
        "deallocate_resize",
        "reallocate",
    }
)


# Public completion entrypoint


def complete_semantic_policies(
    semantic_ir: models.SemanticModule | Iterable[models.SemanticModule],
    *,
    strict_wrapper_names: bool = False,
) -> list[models.SemanticModule]:
    """Complete policy decisions for semantic modules after parser-to-IR conversion.

    Use this after semantic conversion and before wrapper planning.  It accepts
    either one module or any iterable of modules, mutates each in place, and
    returns an ordered list of those same objects for pipeline chaining.
    ``strict_wrapper_names`` is forwarded to export and class-surface policy
    validation.  Invalid or incomplete semantic contracts raise ``ValueError``
    rather than leaving a lower stage to choose a fallback.

    This shared post-IR boundary completes entry export reachability, ownership,
    transfer, destruction, mutability/writeback, projection, nullability,
    release, codegen action, contract/boundary storage modes, getter behavior,
    native setter assignment, and Python setter exposure. Future policy passes
    belong here, not in planning, lowering, bridges, or bindings.
    """

    modules = list(semantic_ir) if not isinstance(semantic_ir, models.SemanticModule) else [semantic_ir]
    for module in modules:
        # Limit entry declarations before completing their dependent policies.
        _complete_entry_export_policy(module)
        complete_python_export_policy(module, strict_wrapper_names=strict_wrapper_names)

        # Resolve all remaining ownership and wrapper-facing semantic choices.
        _complete_ownership_policies(module, strict_wrapper_names=strict_wrapper_names)
    return modules


# Entry export reachability


def _complete_entry_export_policy(module: models.SemanticModule) -> None:
    """Remove public declarations not reachable from an explicit entry export policy."""
    if not module.metadata.get(models.PYTHON_EXPORTS_PREPARED_METADATA):
        return
    module.variables = [variable for variable in module.variables if _is_entry_export_reachable(variable)]
    module.functions = [function for function in module.functions if _is_entry_export_reachable(function)]
    module.overload_sets = [
        overload_set for overload_set in module.overload_sets if _is_entry_export_reachable(overload_set)
    ]


def _is_entry_export_reachable(declaration: object) -> bool:
    """Keep private declarations and public declarations selected by entry exports."""
    if getattr(declaration, "visibility", "public") == "private":
        return True
    return bool(_entry_exports(declaration))


def _entry_exports(declaration: object) -> object:
    """Return a declaration's entry-export metadata, with overloads using their first procedure."""
    if isinstance(declaration, models.ProcedureOverloadSet):
        if not declaration.procedures:
            return ()
        return declaration.procedures[0].metadata.get(models.PYTHON_EXPORTS_METADATA, ())
    if isinstance(declaration, models.SemanticVariable | models.SemanticFunction | models.SemanticClass):
        return declaration.metadata.get(models.PYTHON_EXPORTS_METADATA, ())
    raise TypeError(f"Unsupported semantic declaration: {type(declaration).__name__}")


def _complete_ownership_policies(
    module: models.SemanticModule,
    *,
    strict_wrapper_names: bool,
) -> models.SemanticModule:
    """Attach resolved ownership decisions to a full semantic module.

    Raw semantic types such as ``Float64[:]`` do not carry enough context to
    decide boundary behavior or storage. This pass runs after complete
    signatures are known and before ``ir2ast`` lowering.
    """

    # Resolve identities before any class, field, or callable policy uses them.
    _complete_local_derived_type_identities(module)

    # Complete persistent module state and its accessors first.
    for variable in module.variables:
        _complete_variable(variable, OwnershipContext.module_variable())
        _complete_accessor_policies(variable, OwnershipContext.module_variable())
        _complete_module_variable_initializer(variable)
    # Complete classes, derived-type graph facts, and wrapper-facing surfaces.
    for semantic_class in module.classes:
        class_scope = str(semantic_class.origin.native_scope or module.name)
        _complete_class(semantic_class, f"{class_scope}.{semantic_class.name}")
    derived_types = _complete_derived_type_graph_policies(module.classes)
    _complete_class_surface_policies(
        module.classes,
        derived_types,
        strict_wrapper_names=strict_wrapper_names,
    )
    polymorphic_variants = _polymorphic_variant_map(module.classes)
    _complete_class_method_policies(
        module.classes,
        module.functions,
        derived_types,
        polymorphic_variants,
    )
    _complete_class_overload_policies(module.classes)
    # Attach module-variable policies after their type and accessor facts exist.
    for variable in module.variables:
        variable_scope = str(variable.origin.native_scope or module.name)
        variable.metadata[models.RESOLVED_MODULE_VARIABLE_POLICY_METADATA] = build_module_variable_policy(
            variable,
            module_name=variable_scope,
            derived_types=derived_types,
        )
    # Complete direct functions and overload candidates with their full context.
    for function in module.functions:
        function_scope = str(function.origin.native_scope or module.name)
        _complete_function(
            function,
            f"{function_scope}.{function.name}",
            derived_types=derived_types,
            module_export=True,
            polymorphic_variants=polymorphic_variants,
        )
    for overload_set in module.overload_sets:
        for procedure in overload_set.procedures:
            procedure_scope = str(procedure.origin.native_scope or module.name)
            _complete_function(
                procedure,
                f"{procedure_scope}.{overload_set.name}.{procedure.name}",
                derived_types=derived_types,
            )
    # Build resolved module overload tables after every candidate is complete.
    overload_functions = {
        f"{(procedure.origin.native_scope or module.name)!s}.{overload_set.name}.{procedure.name}": procedure
        for overload_set in module.overload_sets
        for procedure in overload_set.procedures
    }
    module.metadata[models.RESOLVED_MODULE_OVERLOAD_POLICIES_METADATA] = tuple(
        _complete_overload_policy(
            build_module_overload_policy(module, overload_set),
            overload_functions,
            require_uniform_receiver=False,
        )
        for overload_set in module.overload_sets
    )
    module.metadata[models.POLICY_COMPLETION_PREPARED_METADATA] = True
    return module


# Derived-type identity and class policy completion


def _complete_local_derived_type_identities(module: models.SemanticModule) -> None:
    """Attach canonical native identities to unqualified local type references."""
    identities: dict[str, set[tuple[str, str]]] = {}
    scoped_identities: dict[tuple[str, str], set[tuple[str, str]]] = {}

    def collect_class(semantic_class: models.SemanticClass) -> None:
        """Index one nested class under unscoped and native-scope identity keys."""
        identity = (
            str(semantic_class.origin.native_scope or module.name),
            str(semantic_class.native_name or semantic_class.name),
        )
        identities.setdefault(semantic_class.name, set()).add(identity)
        scoped_identities.setdefault((identity[0], semantic_class.name), set()).add(identity)
        for nested in semantic_class.classes:
            collect_class(nested)

    for semantic_class in module.classes:
        collect_class(semantic_class)

    def annotate(semantic_type: models.SemanticType | None, native_scope: str) -> None:
        """Attach a unique local derived identity while leaving external references untouched."""
        if semantic_type is None or models.EXTERNAL_TYPE_REF_METADATA in semantic_type.metadata:
            return
        matches = scoped_identities.get((native_scope, semantic_type.name), set())
        if not matches:
            matches = identities.get(semantic_type.name, set())
        if len(matches) == 1:
            semantic_type.metadata[models.RESOLVED_DERIVED_TYPE_IDENTITY_METADATA] = next(iter(matches))

    def annotate_function(function: models.SemanticFunction) -> None:
        """Annotate one function's argument and direct-return type identities."""
        native_scope = str(function.origin.native_scope or module.name)
        for argument in function.arguments:
            annotate(argument.semantic_type, native_scope)
        annotate(function.return_type, native_scope)

    def annotate_class(semantic_class: models.SemanticClass) -> None:
        """Recursively annotate one class's fields, methods, overloads, and nested classes."""
        native_scope = str(semantic_class.origin.native_scope or module.name)
        for field in semantic_class.fields:
            annotate(field.semantic_type, native_scope)
        for method in semantic_class.methods:
            annotate_function(method)
        for overload_set in semantic_class.overload_sets:
            for procedure in overload_set.procedures:
                annotate_function(procedure)
        for nested in semantic_class.classes:
            annotate_class(nested)

    for variable in module.variables:
        annotate(variable.semantic_type, str(variable.origin.native_scope or module.name))
    for function in module.functions:
        annotate_function(function)
    for overload_set in module.overload_sets:
        for procedure in overload_set.procedures:
            annotate_function(procedure)
    for semantic_class in module.classes:
        annotate_class(semantic_class)


def _complete_class(semantic_class: models.SemanticClass, owner_path: str) -> None:
    """Complete one class's instance, self, field, accessor, and derived-type policies.

    The class and its fields are mutated in place, then nested classes receive
    the corresponding owner path.  The method does not construct wrapper plans.
    """
    class_type = models.SemanticType(name=semantic_class.name, dtype=semantic_class.name)
    semantic_class.metadata[models.RESOLVED_CLASS_INSTANCE_POLICY_METADATA] = (
        default_ownership_policy.decide_semantic_type(class_type, OwnershipContext.result())
    )
    semantic_class.metadata[models.RESOLVED_CLASS_SELF_POLICY_METADATA] = default_ownership_policy.decide_semantic_type(
        class_type,
        OwnershipContext.argument(writes_argument=True),
    )
    for field in semantic_class.fields:
        _complete_variable(field, OwnershipContext.field())
        _complete_accessor_policies(field, OwnershipContext.field())
        field.metadata[models.RESOLVED_DERIVED_FIELD_POLICY_METADATA] = build_derived_field_policy(
            field,
            owner_path=owner_path,
        )
    semantic_class.metadata[models.RESOLVED_DERIVED_TYPE_POLICY_METADATA] = build_derived_type_policy(
        semantic_class,
        owner_path=owner_path,
    )
    for nested in semantic_class.classes:
        _complete_class(nested, f"{owner_path}.{nested.name}")


def _derived_type_policy_map(
    classes: list[models.SemanticClass],
) -> dict[tuple[str, str], DerivedTypePolicy]:
    """Return completed type policies by canonical semantic identity."""
    policies: dict[tuple[str, str], DerivedTypePolicy] = {}

    def collect(semantic_class: models.SemanticClass) -> None:
        """Store an already-completed class policy under its canonical identity."""
        policy = semantic_class.metadata.get(models.RESOLVED_DERIVED_TYPE_POLICY_METADATA)
        if isinstance(policy, DerivedTypePolicy):
            policies[policy.type_identity] = policy
        for nested in semantic_class.classes:
            collect(nested)

    for semantic_class in classes:
        collect(semantic_class)
    return policies


def _complete_derived_type_graph_policies(
    classes: list[models.SemanticClass],
) -> dict[tuple[str, str], DerivedTypePolicy]:
    """Validate finite derived member graphs after every local type is known."""
    policies = _derived_type_policy_map(classes)

    def complete(semantic_class: models.SemanticClass) -> None:
        """Complete recursive member-path policies for one class before indexing it."""
        policy = semantic_class.metadata.get(models.RESOLVED_DERIVED_TYPE_POLICY_METADATA)
        if isinstance(policy, DerivedTypePolicy):
            _paths, graph_blockers = derived_member_path_policies(policy, policies)
            blockers = tuple(dict.fromkeys((*policy.blockers, *graph_blockers)))
            completed = replace(policy, supported=not blockers, blockers=blockers)
            semantic_class.metadata[models.RESOLVED_DERIVED_TYPE_POLICY_METADATA] = completed
            policies[completed.type_identity] = completed
        for nested in semantic_class.classes:
            complete(nested)

    for semantic_class in classes:
        complete(semantic_class)
    return policies


def _complete_class_surface_policies(
    classes: list[models.SemanticClass],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
    *,
    strict_wrapper_names: bool,
) -> None:
    """Complete class orchestration after every derived identity is known."""
    identities = {
        semantic_class.name: policy.type_identity
        for semantic_class in _iter_semantic_classes(classes)
        for policy in (semantic_class.metadata.get(models.RESOLVED_DERIVED_TYPE_POLICY_METADATA),)
        if isinstance(policy, DerivedTypePolicy)
    }
    for semantic_class in _iter_semantic_classes(classes):
        derived = semantic_class.metadata.get(models.RESOLVED_DERIVED_TYPE_POLICY_METADATA)
        if not isinstance(derived, DerivedTypePolicy):
            continue
        surface = build_class_surface_policy(
            semantic_class,
            owner_path=derived.owner_path,
            derived=derived,
            class_identities=identities,
            strict_wrapper_names=strict_wrapper_names,
        )
        completed_derived = replace(derived, fields=surface.effective_fields)
        semantic_class.metadata[models.RESOLVED_DERIVED_TYPE_POLICY_METADATA] = completed_derived
        derived_types[completed_derived.type_identity] = completed_derived
        fields_by_owner = {field.owner_path: field for field in surface.effective_fields}
        for field in semantic_class.fields:
            owner_path = f"{derived.owner_path}.{field.name}"
            if owner_path in fields_by_owner:
                field.metadata[models.RESOLVED_DERIVED_FIELD_POLICY_METADATA] = fields_by_owner[owner_path]
        semantic_class.metadata[models.RESOLVED_CLASS_SURFACE_POLICY_METADATA] = surface

    surfaces = {
        surface.type_identity: (semantic_class, surface)
        for semantic_class in _iter_semantic_classes(classes)
        for surface in (semantic_class.metadata.get(models.RESOLVED_CLASS_SURFACE_POLICY_METADATA),)
        if isinstance(surface, ClassSurfacePolicy)
    }

    def effective_fields(
        identity: tuple[str, str],
        active: frozenset[tuple[str, str]] = frozenset(),
    ) -> tuple[DerivedFieldPolicy, ...]:
        """Compose inherited fields once while guarding malformed base cycles."""
        if identity in active:
            return ()
        entry = surfaces.get(identity)
        if entry is None:
            return ()
        _semantic_class, surface = entry
        inherited = tuple(
            field for base in surface.base_identities for field in effective_fields(base, active | {identity})
        )
        derived = derived_types[identity]
        return (*inherited, *derived.fields)

    for identity, (semantic_class, surface) in surfaces.items():
        semantic_class.metadata[models.RESOLVED_CLASS_SURFACE_POLICY_METADATA] = replace(
            surface,
            effective_fields=effective_fields(identity),
        )


def _complete_class_method_policies(
    classes: list[models.SemanticClass],
    module_functions: list[models.SemanticFunction],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
    polymorphic_variants: dict[tuple[str, str], tuple[tuple[str, str], ...]],
) -> None:
    """Complete methods once from class policy, type graphs, and dispatch sets."""
    type_bound_targets = _type_bound_target_names(module_functions)
    module_targets = {str(function.native_name or function.name) for function in module_functions}
    for semantic_class in _iter_semantic_classes(classes):
        _complete_one_class_method_policy(
            semantic_class,
            type_bound_targets,
            module_targets,
            derived_types,
            polymorphic_variants,
        )


def _type_bound_target_names(module_functions: list[models.SemanticFunction]) -> set[str]:
    """Return native names explicitly marked as type-bound root targets."""
    return {
        str(function.native_name or function.name)
        for function in module_functions
        if function.metadata.get("fortran_type_bound_target")
    }


def _complete_one_class_method_policy(
    semantic_class: models.SemanticClass,
    type_bound_targets: set[str],
    module_targets: set[str],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
    polymorphic_variants: dict[tuple[str, str], tuple[tuple[str, str], ...]],
) -> None:
    """Complete ordinary and overloaded calls for one prepared class surface."""
    derived = semantic_class.metadata.get(models.RESOLVED_DERIVED_TYPE_POLICY_METADATA)
    surface = semantic_class.metadata.get(models.RESOLVED_CLASS_SURFACE_POLICY_METADATA)
    if not isinstance(derived, DerivedTypePolicy) or not isinstance(surface, ClassSurfacePolicy):
        return
    native_bindings = {
        str(method.native_name or method.name): _native_type_bound_binding_name(method)
        for method in semantic_class.methods
        if method.name != "__init__"
    }
    completed_methods = _completed_class_method_invocations(
        surface,
        native_bindings,
        type_bound_targets,
        module_targets,
    )
    semantic_class.metadata[models.RESOLVED_CLASS_SURFACE_POLICY_METADATA] = replace(
        surface,
        methods=completed_methods,
    )
    _complete_concrete_class_methods(
        semantic_class,
        derived,
        completed_methods,
        derived_types,
        polymorphic_variants,
    )
    _complete_class_overload_methods(
        semantic_class,
        derived,
        type_bound_targets,
        module_targets,
        derived_types,
        polymorphic_variants,
    )


def _completed_class_method_invocations(
    surface: ClassSurfacePolicy,
    native_bindings: dict[str, str],
    type_bound_targets: set[str],
    module_targets: set[str],
) -> tuple[ClassMethodPolicy, ...]:
    """Select direct or type-bound invocation for every ordinary method."""
    return tuple(
        replace(
            method,
            invocation=ClassInvocationKind.TYPE_BOUND,
            type_bound_name=native_bindings[method.native_name],
        )
        if _uses_type_bound_invocation(method, type_bound_targets, module_targets)
        else method
        for method in surface.methods
    )


def _complete_concrete_class_methods(
    semantic_class: models.SemanticClass,
    derived: DerivedTypePolicy,
    completed_methods: tuple[ClassMethodPolicy, ...],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
    polymorphic_variants: dict[tuple[str, str], tuple[tuple[str, str], ...]],
) -> None:
    """Attach completed function policy to constructors and ordinary methods."""
    calls = {method.owner_path: method for method in completed_methods}
    surface = semantic_class.metadata.get(models.RESOLVED_CLASS_SURFACE_POLICY_METADATA)
    constructor_call = surface.constructor.call if isinstance(surface, ClassSurfacePolicy) else None
    for method in semantic_class.methods:
        owner_path = f"{derived.owner_path}.{method.name}"
        if method.name == "__init__":
            if method.metadata.get("bind_target"):
                _complete_function(
                    method,
                    owner_path,
                    derived_types=derived_types,
                    class_call=constructor_call,
                    module_export=False,
                    polymorphic_variants=polymorphic_variants,
                )
            continue
        function_owner_path = f"{derived.owner_path}.__method__.{method.name}"
        _complete_function(
            method,
            function_owner_path,
            derived_types=derived_types,
            class_call=calls.get(owner_path),
            polymorphic_variants=polymorphic_variants,
        )


def _complete_class_overload_methods(
    semantic_class: models.SemanticClass,
    derived: DerivedTypePolicy,
    type_bound_targets: set[str],
    module_targets: set[str],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
    polymorphic_variants: dict[tuple[str, str], tuple[tuple[str, str], ...]],
) -> None:
    """Complete every concrete overload through one typed call leaf."""
    generic_bindings = {
        _class_overload_native_target(procedure): overload.name
        for overload in semantic_class.overload_sets
        if overload.name != "__init__"
        for procedure in overload.procedures
    }
    for overload in semantic_class.overload_sets:
        for procedure in overload.procedures:
            _complete_one_class_overload_method(
                overload,
                procedure,
                derived,
                generic_bindings,
                type_bound_targets,
                module_targets,
                derived_types,
                polymorphic_variants,
            )


def _complete_one_class_overload_method(
    overload: models.ProcedureOverloadSet,
    procedure: models.SemanticFunction,
    derived: DerivedTypePolicy,
    generic_bindings: dict[str, str],
    type_bound_targets: set[str],
    module_targets: set[str],
    derived_types: dict[tuple[str, str], DerivedTypePolicy],
    polymorphic_variants: dict[tuple[str, str], tuple[tuple[str, str], ...]],
) -> None:
    """Complete one overload candidate and its native dispatch spelling."""
    owner_path = f"{derived.owner_path}.{overload.name}.{procedure.name}"
    native_name = _class_overload_native_target(procedure)
    bind_target = procedure.metadata.get(BIND_TARGET_METADATA)
    passed_position = _class_overload_passed_object_position(procedure)
    type_bound = native_name in type_bound_targets or (
        passed_position is not None and native_name not in module_targets
    )
    call = _class_overload_call_policy(
        overload,
        procedure,
        owner_path,
        type_bound=type_bound,
        type_bound_name=(str(bind_target) if bind_target else generic_bindings.get(native_name))
        if type_bound
        else None,
    )
    overload_kind = str(procedure.metadata.get(models.OVERLOAD_KIND_METADATA, "generic"))
    native_dispatch_name = (
        str(bind_target)
        if bind_target
        else (
            str(procedure.metadata.get(models.FORTRAN_GENERIC_NAME_METADATA, overload.name))
            if overload_kind != "generic"
            else None
        )
    )
    _complete_function(
        procedure,
        owner_path,
        derived_types=derived_types,
        class_call=call,
        polymorphic_variants=polymorphic_variants,
        native_dispatch_name=native_dispatch_name,
    )


def _class_overload_native_target(procedure: models.SemanticFunction) -> str:
    """Return the completed native target selected by an overload contract."""
    return str(procedure.metadata.get(BIND_TARGET_METADATA) or procedure.native_name or procedure.name)


def _uses_type_bound_invocation(
    method: ClassMethodPolicy,
    explicit_targets: set[str],
    module_targets: set[str],
) -> bool:
    """Restore generated-.pyi type-bound calls when their private root target is absent."""
    if method.kind is ClassMethodKind.STATIC:
        return False
    return method.native_name in explicit_targets or method.native_name not in module_targets


def _native_type_bound_binding_name(method: models.SemanticMethod) -> str:
    """Recover the native binding hidden by Python keyword normalization."""
    name = str(method.name)
    if method.metadata.get(BIND_TARGET_METADATA) and name.endswith("_"):
        candidate = name[:-1]
        if keyword.iskeyword(candidate):
            return candidate
    return name


def _complete_class_overload_policies(classes: list[models.SemanticClass]) -> None:
    """Attach exact runtime predicates after concrete calls are completed."""
    for semantic_class in _iter_semantic_classes(classes):
        surface = semantic_class.metadata.get(models.RESOLVED_CLASS_SURFACE_POLICY_METADATA)
        if not isinstance(surface, ClassSurfacePolicy):
            continue
        functions = {
            f"{surface.owner_path}.{overload.name}.{procedure.name}": procedure
            for overload in semantic_class.overload_sets
            for procedure in overload.procedures
        }
        blockers = list(surface.blockers)
        overloads = []
        for overload in surface.overloads:
            completed = _complete_overload_policy(overload, functions, require_uniform_receiver=True)
            overloads.append(completed)
            blockers.extend(completed.blockers)
        semantic_class.metadata[models.RESOLVED_CLASS_SURFACE_POLICY_METADATA] = replace(
            surface,
            overloads=tuple(overloads),
            supported=not blockers,
            blockers=tuple(dict.fromkeys(blockers)),
        )


def _complete_overload_policy(
    overload: OverloadPolicy,
    functions: dict[str, models.SemanticFunction],
    *,
    require_uniform_receiver: bool,
) -> OverloadPolicy:
    """Attach exact candidate predicates after all concrete calls are complete."""
    blockers = list(overload.blockers)
    candidates = []
    for candidate in overload.candidates:
        function = functions[candidate.owner_path]
        function_policy = function.metadata.get(models.RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA)
        if not isinstance(function_policy, FunctionWrapperPolicy):
            blockers.append(f"overload candidate {candidate.owner_path!r} has no completed call policy")
            candidates.append(candidate)
            continue
        if (
            function_policy.class_call is not None
            and function_policy.class_call.invocation is ClassInvocationKind.TYPE_BOUND
            and function_policy.class_call.type_bound_name is None
        ):
            blockers.append(f"overload candidate {candidate.owner_path!r} has no accessible type-bound binding")
        matches, match_blockers = _overload_matches(function_policy)
        blockers.extend(f"overload candidate {candidate.owner_path!r}: {reason}" for reason in match_blockers)
        candidates.append(
            replace(
                candidate,
                arguments=matches,
                passed_object=(
                    function_policy.class_call is not None
                    and function_policy.class_call.passed_object_position is not None
                ),
            )
        )
    if require_uniform_receiver and len({candidate.passed_object for candidate in candidates}) > 1:
        blockers.append(f"overload {overload.owner_path!r} mixes instance and static candidates")
    signatures = tuple(_overload_candidate_signature(candidate.arguments) for candidate in candidates)
    if len(set(signatures)) != len(signatures):
        blockers.append(f"overload {overload.owner_path!r} has indistinguishable Python signatures")
    builtin_signatures = tuple(_overload_candidate_builtin_signature(candidate.arguments) for candidate in candidates)
    if len(set(builtin_signatures)) != len(builtin_signatures):
        blockers.append(f"overload {overload.owner_path!r} has overlapping reflected scalar signatures")
    return replace(overload, candidates=tuple(candidates), blockers=tuple(dict.fromkeys(blockers)))


def _overload_candidate_signature(arguments: tuple[OverloadArgumentPolicy, ...]) -> tuple:
    """Return only runtime-relevant facts for ambiguity detection."""
    return tuple(
        (
            argument.kind,
            argument.optional,
            argument.semantic_type_name,
            argument.rank,
            argument.derived_type_identity,
        )
        for argument in arguments
    )


def _overload_candidate_builtin_signature(arguments: tuple[OverloadArgumentPolicy, ...]) -> tuple:
    """Normalize reflected Python scalar domains for overlap detection."""
    return tuple(
        (
            argument.kind,
            argument.optional,
            (
                overload_builtin_scalar_family(argument.semantic_type_name)
                if argument.accept_builtin_scalar
                else argument.semantic_type_name
            ),
            argument.rank,
            argument.derived_type_identity,
        )
        for argument in arguments
    )


def _overload_matches(
    function: FunctionWrapperPolicy,
) -> tuple[tuple[OverloadArgumentPolicy, ...], tuple[str, ...]]:
    """Translate one completed call signature into exact Python predicates."""
    passed_position = function.class_call.passed_object_position if function.class_call is not None else None
    reflected = bool(function.class_call is not None and function.class_call.passed_object_position not in {None, 0})
    matches = []
    blockers = []
    for argument in function.arguments:
        if not argument.python_visible or argument.native_position == passed_position:
            continue
        match = _overload_argument_match(argument, accept_builtin_scalar=reflected)
        if match is None:
            blockers.append(
                f"argument {argument.python_name!r} has no exact overload predicate for {argument.ownership.kind.value}"
            )
        else:
            matches.append(match)
    return tuple(matches), tuple(blockers)


def _overload_argument_match(
    argument: ArgumentPolicy,
    *,
    accept_builtin_scalar: bool,
) -> OverloadArgumentPolicy | None:
    """Return one typed match record without embedding generated source text."""
    kind = argument.ownership.kind
    match_kind = None
    derived_identity = None
    if kind is ObjectKind.SCALAR and argument.semantic_type_name in SEMANTIC_SCALAR_TYPE_NAMES:
        match_kind = OverloadMatchKind.NUMPY_SCALAR
    elif kind is ObjectKind.STRING:
        match_kind = OverloadMatchKind.STRING
    elif kind is ObjectKind.NUMPY_ARRAY and argument.array is not None:
        match_kind = OverloadMatchKind.NUMPY_ARRAY
    elif kind is ObjectKind.DERIVED_TYPE and argument.derived is not None:
        match_kind = OverloadMatchKind.DERIVED
        derived_identity = argument.derived.type_identity
    if match_kind is None:
        return None
    return OverloadArgumentPolicy(
        python_name=argument.python_name,
        kind=match_kind,
        optional=argument.optional_mode not in {OptionalMode.REQUIRED, OptionalMode.REQUIRED_DESCRIPTOR},
        semantic_type_name=argument.semantic_type_name,
        rank=argument.rank,
        derived_type_identity=derived_identity,
        accept_builtin_scalar=accept_builtin_scalar and match_kind is OverloadMatchKind.NUMPY_SCALAR,
    )


def _iter_semantic_classes(classes: list[models.SemanticClass]):
    """Yield one stable depth-first class sequence for policy completion."""
    for semantic_class in classes:
        yield semantic_class
        yield from _iter_semantic_classes(semantic_class.classes)


def _polymorphic_variant_map(
    classes: list[models.SemanticClass],
) -> dict[tuple[str, str], tuple[tuple[str, str], ...]]:
    """Enumerate known extensions from completed base identities, most-derived first."""
    surfaces = tuple(
        surface
        for semantic_class in _iter_semantic_classes(classes)
        for surface in (semantic_class.metadata.get(models.RESOLVED_CLASS_SURFACE_POLICY_METADATA),)
        if isinstance(surface, ClassSurfacePolicy)
    )
    bases = {surface.type_identity: surface.base_identities for surface in surfaces}

    def extends(candidate: tuple[str, str], base: tuple[str, str]) -> bool:
        """Report whether a completed class identity is the base or extends it transitively."""
        return candidate == base or any(extends(parent, base) for parent in bases.get(candidate, ()))

    identities = tuple(surface.type_identity for surface in surfaces)
    return {
        base: tuple(candidate for candidate in reversed(identities) if extends(candidate, base)) for base in identities
    }


def _class_overload_call_policy(
    overload: models.ProcedureOverloadSet,
    procedure: models.SemanticFunction,
    owner_path: str,
    *,
    type_bound: bool,
    type_bound_name: str | None,
) -> ClassMethodPolicy:
    """Complete one concrete class-overload call from parser-owned metadata."""
    passed = _class_overload_passed_object_position(procedure)
    return ClassMethodPolicy(
        owner_path=owner_path,
        python_name=str(procedure.metadata.get(models.PYTHON_METHOD_NAME_METADATA, overload.name)),
        native_name=str(procedure.native_name or procedure.name),
        kind=ClassMethodKind.INSTANCE if passed is not None else ClassMethodKind.STATIC,
        passed_object_position=passed,
        public=True,
        invocation=ClassInvocationKind.TYPE_BOUND if type_bound else ClassInvocationKind.MODULE_PROCEDURE,
        type_bound_name=type_bound_name,
    )


def _class_overload_passed_object_position(procedure: models.SemanticFunction) -> int | None:
    """Return one validated parser-owned passed-object position."""
    position = procedure.metadata.get(models.PYTHON_BOUND_POSITION_METADATA)
    return position if isinstance(position, int) and not isinstance(position, bool) else None


def _complete_function(
    function: models.SemanticFunction,
    owner_path: str,
    *,
    derived_types: dict[tuple[str, str], DerivedTypePolicy] | None = None,
    class_call: ClassMethodPolicy | None = None,
    module_export: bool | None = None,
    polymorphic_variants: dict[tuple[str, str], tuple[tuple[str, str], ...]] | None = None,
    native_dispatch_name: str | None = None,
) -> None:
    """Complete one function's arguments, result, special policies, and wrapper policy.

    The function is mutated in place.  It first validates/normalizes address
    projections, then resolves per-argument and result ownership, adds native
    handle and status policies, and finally builds the wrapper-facing policy.
    """
    # Normalize signature-level ABI facts before ownership uses them.
    _complete_callable_address_policy(function)

    # Complete inputs and the direct return's ownership policy.
    for argument in function.arguments:
        _complete_variable(
            argument,
            ownership_context_for_argument(function, argument),
            owner_path=f"{owner_path}.{argument.name}",
        )
    if function.return_type is not None:
        _validate_maybe_unallocated_return(function, owner_path)
        decision = default_ownership_policy.decide_semantic_type(function.return_type, OwnershipContext.result())
        function.metadata[models.RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA] = decision
        _complete_native_array_handle_result_policy(function, decision)
    else:
        function.metadata.pop(models.RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA, None)
        function.metadata.pop(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA, None)
    # Complete cross-result status handling before the wrapper policy consumes it.
    _complete_native_status_error_policy(function, owner_path)
    function.metadata[models.RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA] = build_function_wrapper_policy(
        function,
        owner_path=owner_path,
        derived_types=derived_types,
        class_call=class_call,
        module_export=module_export,
        polymorphic_variants=polymorphic_variants,
        native_dispatch_name=native_dispatch_name,
    )


def _complete_native_status_error_policy(function: models.SemanticFunction, owner_path: str) -> None:
    """Validate and complete one native-status-to-Python-exception decision."""
    raw_policy = function.metadata.get(models.RUNTIME_STATUS_ERROR_METADATA)
    if raw_policy is None:
        function.metadata.pop(models.RESOLVED_RUNTIME_STATUS_ERROR_POLICY_METADATA, None)
        return
    if not isinstance(raw_policy, dict):
        raise ValueError(f"Function {function.name!r} has invalid raises metadata")

    success = raw_policy.get("success", 0)
    if not isinstance(success, int) or isinstance(success, bool):
        raise ValueError(f"Function {function.name!r} raises success value must be an integer")
    status = _native_status_output(function, owner_path, raw_policy.get("status"), subject="status")
    if status.rank != 0 or not _is_scalar_integer_status(status.semantic_type_name):
        raise ValueError(
            f"Function {function.name!r} raises status target {status.name!r} must be a scalar integer hidden output"
        )

    message_name = raw_policy.get("message")
    message = None
    if message_name is not None:
        message = _native_status_output(function, owner_path, message_name, subject="message")
        if message.rank != 0 or message.semantic_type_name != "String":
            raise ValueError(
                f"Function {function.name!r} raises message target {message.name!r} "
                "must be a scalar string hidden output"
            )
        if message.owner_path == status.owner_path:
            raise ValueError(f"Function {function.name!r} raises status and message targets must be distinct")

    function.metadata[models.RESOLVED_RUNTIME_STATUS_ERROR_POLICY_METADATA] = NativeStatusErrorPolicy(
        status=status,
        message=message,
        success=success,
        exception_kind=PythonExceptionKind.RUNTIME_ERROR,
    )


def _native_status_output(
    function: models.SemanticFunction,
    owner_path: str,
    output_name: object,
    *,
    subject: str,
) -> NativeStatusOutputPolicy:
    """Return one completed hidden output selected by a runtime policy."""
    if not isinstance(output_name, str) or not output_name:
        raise ValueError(f"Function {function.name!r} raises {subject} target must name a hidden output")
    mappings = tuple(
        mapping
        for mapping in function.projection
        if (
            mapping.python_position is None
            and isinstance(mapping.result_position, int)
            and output_name in {mapping.python_name, mapping.native_name}
        )
    )
    if len(mappings) != 1:
        raise ValueError(f"Function {function.name!r} raises {subject} target must name a hidden output")
    mapping = mappings[0]
    argument = next((item for item in function.arguments if item.name == mapping.python_name), None)
    if argument is None or not isinstance(mapping.native_position, int):
        raise ValueError(f"Function {function.name!r} raises {subject} target must name a hidden output")
    decision = argument.metadata.get(models.RESOLVED_OWNERSHIP_POLICY_METADATA)
    if not isinstance(decision, OwnershipDecision) or not _is_compatible_status_handoff(decision):
        raise ValueError(
            f"Function {function.name!r} raises {subject} target {output_name!r} "
            "has no compatible completed hidden-output handoff"
        )
    semantic_type = argument.semantic_type
    return NativeStatusOutputPolicy(
        owner_path=f"{owner_path}.{argument.name}",
        name=argument.name,
        native_name=mapping.native_name or argument.name,
        native_position=mapping.native_position,
        result_position=mapping.result_position,
        semantic_type_name=semantic_type.name,
        rank=int(semantic_type.rank or 0),
        character_length=_fixed_character_length(semantic_type),
    )


def _is_compatible_status_handoff(decision: OwnershipDecision) -> bool:
    """Report whether a hidden scalar/string result has a valid status handoff action."""
    expected_action = {
        ObjectKind.SCALAR: CodegenAction.DIRECT_VALUE,
        ObjectKind.STRING: CodegenAction.COPY_OUT,
    }.get(decision.kind)
    return bool(decision.projects_result and not decision.python_visible and decision.codegen_action is expected_action)


def _is_scalar_integer_status(semantic_type_name: str) -> bool:
    """Report whether a semantic scalar name can serve as a native status code."""
    return semantic_type_name in {
        "Byte",
        "CEnum",
        "Int",
        "Int8",
        "Int16",
        "Int32",
        "Int64",
        "SizeT",
        "UInt",
        "UInt8",
        "UInt16",
        "UInt32",
        "UInt64",
    }


def _fixed_character_length(semantic_type: models.SemanticType) -> int | None:
    """Return a positive rank-zero character length if the contract provides one."""
    if semantic_type.rank != 0:
        return None
    value = semantic_type.metadata.get("fortran_character_length")
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    if isinstance(value, str) and value.strip().isdigit() and int(value.strip()) > 0:
        return int(value.strip())
    return None


def _complete_native_array_handle_result_policy(
    function: models.SemanticFunction,
    decision: OwnershipDecision,
) -> None:
    """Attach or clear a direct-result native-array-handle policy on a function."""
    return_type = function.return_type
    descriptor_kind = native_array_descriptor_kind(return_type)
    if descriptor_kind is None or return_type is None:
        function.metadata.pop(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA, None)
        return
    policy = _native_array_handle_policy(
        descriptor_kind,
        return_type,
        decision,
        OwnershipContext.result(),
    )
    function.metadata[models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA] = policy


def _validate_maybe_unallocated_return(function: models.SemanticFunction, owner_path: str) -> None:
    """Require MaybeUnallocated only on direct allocatable array function results."""
    return_type = function.return_type
    if return_type is None or not return_type.metadata.get(MAYBE_UNALLOCATED_METADATA):
        return
    if native_array_descriptor_kind(return_type) != "allocatable" or int(return_type.rank or 0) <= 0:
        raise ValueError(f"MaybeUnallocated metadata on {owner_path}.return requires an Allocatable[...] array result")


def _complete_native_array_handle_variable_policy(
    variable: models.SemanticVariable,
    context: OwnershipContext,
) -> None:
    """Attach or clear a native-array-handle policy for one variable or argument.

    The variable's resolved ownership policy must already exist; a descriptor
    type receives a completed handle policy derived from that decision and its
    semantic context.
    """
    descriptor_kind = native_array_descriptor_kind(variable.semantic_type)
    if descriptor_kind is None:
        variable.metadata.pop(models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA, None)
        return
    decision = variable.metadata[models.RESOLVED_OWNERSHIP_POLICY_METADATA]
    policy = _native_array_handle_policy(
        descriptor_kind,
        variable.semantic_type,
        decision,
        context,
        variable=variable,
    )
    variable.metadata[models.RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA] = policy


def _native_array_handle_policy(
    descriptor_kind: str,
    semantic_type: models.SemanticType,
    decision: OwnershipDecision,
    context: OwnershipContext,
    *,
    variable: models.SemanticVariable | None = None,
) -> NativeArrayHandlePolicy:
    """Build the complete runtime contract for one native allocatable/pointer handle.

    This pure policy builder combines descriptor kind, completed ownership, and
    declaration context into ownership, access, lifetime, operations, and ABI
    facts.  It does not mutate the semantic type or generate wrapper code.
    """
    optional_absent = bool(
        variable is not None and variable.optional and semantic_type.metadata.get(OPTIONAL_ABSENT_HANDLE_METADATA)
    )
    handle_kind = _native_array_handle_kind(descriptor_kind, context, optional_absent=optional_absent)
    blocker = _native_array_handle_blocker(descriptor_kind, handle_kind, decision)
    descriptor_ownership = _native_array_descriptor_ownership(handle_kind)
    to_numpy = _native_array_to_numpy_policy(descriptor_kind, handle_kind, decision, semantic_type)
    operations = _native_array_handle_operations(descriptor_kind, handle_kind, context, semantic_type)
    default_construction = _native_array_default_construction(handle_kind, context, semantic_type)
    return NativeArrayHandlePolicy(
        descriptor_kind=descriptor_kind,
        handle_kind=handle_kind,
        origin=_native_array_handle_origin(context),
        owner=_native_array_handle_owner(handle_kind),
        owner_retention=_native_array_owner_retention(handle_kind),
        descriptor_ownership=descriptor_ownership,
        borrowed=descriptor_ownership == "borrowed",
        getter_behavior=_native_array_getter_behavior(handle_kind, context, blocker),
        python_setter=_native_array_python_setter(variable),
        native_setter=_native_array_native_setter(variable),
        output_projection=_native_array_output_projection(descriptor_kind, handle_kind, context),
        result_allocation=_native_array_result_allocation(descriptor_kind, handle_kind, context, semantic_type),
        release=_native_array_release_responsibility(handle_kind),
        target_lifetime=_native_array_target_lifetime(descriptor_kind, handle_kind, semantic_type, blocker),
        destroy_behavior=_native_array_destroy_behavior(handle_kind, blocker),
        to_numpy=to_numpy,
        descriptor_interop=_native_array_descriptor_interop_requirement(
            descriptor_kind,
            handle_kind,
            semantic_type,
        ),
        nullable=bool(decision.nullable or optional_absent),
        optional_absent=optional_absent,
        storage_mode=decision.storage_mode.value,
        operations=operations,
        blocker=blocker,
        default_construction=default_construction,
        default_descriptor_ownership="owned" if default_construction != "none" else "unknown",
        default_release="wrapper_dealloc" if default_construction != "none" else "none",
        default_destroy_behavior="handle_finalizer" if default_construction != "none" else "none",
        default_operations=(tuple(sorted({*operations, "destroy"})) if default_construction != "none" else ()),
    )


def _native_array_handle_kind(
    descriptor_kind: str,
    context: OwnershipContext,
    *,
    optional_absent: bool,
) -> str:
    """Classify a descriptor by declaration context and optional-absence state."""
    if optional_absent:
        return "optional_absent_handle"
    if context.is_module_variable:
        return "borrowed_module_descriptor"
    if context.is_field:
        return "borrowed_field_descriptor"
    if context.is_argument and context.projects_result and not context.python_visible:
        return "owned_result_descriptor"
    if context.is_argument:
        return "argument_descriptor"
    if context.is_result:
        return "owned_result_descriptor"
    return "unsupported"


def _native_array_default_construction(
    handle_kind: str,
    context: OwnershipContext,
    semantic_type: models.SemanticType,
) -> str:
    """Complete how a runtime-constructed descriptor reaches one argument."""
    if (
        semantic_type.name == "String"
        or handle_kind not in {"argument_descriptor", "optional_absent_handle"}
        or not context.is_argument
    ):
        return "none"
    if context.projects_result:
        return "lazy_owned_descriptor"
    return "fact_packed_empty"


def _native_array_handle_origin(context: OwnershipContext) -> str:
    """Return the semantic origin label used by a completed descriptor policy."""
    if context.is_module_variable:
        return "module_variable"
    if context.is_field:
        return "derived_field"
    if context.is_argument:
        if context.projects_result and not context.python_visible:
            return "projected_result"
        return "argument"
    if context.is_result:
        return "result"
    return "unknown"


def _native_array_handle_owner(handle_kind: str) -> str:
    """Return the owner category prescribed for one completed descriptor kind."""
    return {
        "argument_descriptor": "caller",
        "borrowed_field_descriptor": "wrapper",
        "borrowed_module_descriptor": "native",
        "optional_absent_handle": "caller",
        "owned_result_descriptor": "wrapper",
    }.get(handle_kind, "unknown")


def _native_array_owner_retention(handle_kind: str) -> str:
    """Return the object or storage that retains a descriptor policy's owner."""
    return {
        "argument_descriptor": "caller_handle",
        "borrowed_field_descriptor": "parent_wrapper",
        "borrowed_module_descriptor": "native_module",
        "optional_absent_handle": "optional_argument",
        "owned_result_descriptor": "wrapper_owner_storage",
    }.get(handle_kind, "unknown")


def _native_array_descriptor_ownership(handle_kind: str) -> str:
    """Return whether the descriptor object itself is owned, borrowed, or unknown."""
    if handle_kind == "owned_result_descriptor":
        return "owned"
    if handle_kind == "unsupported":
        return "unknown"
    return "borrowed"


def _native_array_getter_behavior(handle_kind: str, context: OwnershipContext, blocker: str | None) -> str:
    """Choose a descriptor getter result only when the completed policy is supported."""
    if blocker is not None:
        return "blocked"
    if context.is_module_variable or context.is_field:
        return "handle"
    if handle_kind == "owned_result_descriptor":
        return "return_handle"
    return "none"


def _native_array_python_setter(variable: models.SemanticVariable | None) -> str:
    """Return the resolved Python setter action for a descriptor variable, if applicable."""
    setter = None if variable is None else variable.metadata.get(models.RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA)
    if setter is None:
        return "none"
    return setter.setter_action.value


def _native_array_native_setter(variable: models.SemanticVariable | None) -> str:
    """Return the resolved native assignment action for a descriptor variable, if applicable."""
    setter = None if variable is None else variable.metadata.get(models.RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA)
    if setter is None:
        return "none"
    return setter.assignment_mode.value


def _native_array_output_projection(
    descriptor_kind: str,
    handle_kind: str,
    context: OwnershipContext,
) -> str:
    """Return how a descriptor becomes a Python-visible output in its context."""
    if handle_kind == "unsupported":
        return "unsupported"
    if context.is_result:
        return "handle_result"
    if context.is_argument and context.projects_result:
        return "projected_handle"
    return "none"


def _native_array_result_allocation(
    descriptor_kind: str,
    handle_kind: str,
    context: OwnershipContext,
    semantic_type: models.SemanticType,
) -> str:
    """Return the allocation guarantee for an allocatable descriptor function result."""
    if context.is_result and descriptor_kind == "allocatable" and handle_kind == "owned_result_descriptor":
        if semantic_type.metadata.get(MAYBE_UNALLOCATED_METADATA):
            return "maybe_unallocated"
        return "always_allocated"
    return "not_applicable"


def _native_array_release_responsibility(handle_kind: str) -> str:
    """Return the component responsible for releasing one descriptor handle kind."""
    return {
        "argument_descriptor": "none",
        "borrowed_field_descriptor": "wrapper_dealloc",
        "borrowed_module_descriptor": "native_owner",
        "optional_absent_handle": "none",
        "owned_result_descriptor": "wrapper_dealloc",
        "unsupported": "blocked",
    }[handle_kind]


def _native_array_target_lifetime(
    descriptor_kind: str,
    handle_kind: str,
    semantic_type: models.SemanticType,
    blocker: str | None,
) -> str:
    """Return the declared target lifetime, honoring explicit pointer-lifetime metadata."""
    if handle_kind == "unsupported":
        return "unknown"
    if descriptor_kind == "pointer":
        pointer_lifetime = _pointer_policy_value(_pointer_policy_metadata(semantic_type), "lifetime")
        if pointer_lifetime:
            return pointer_lifetime
        if handle_kind == "owned_result_descriptor":
            return "unknown"
        if blocker is not None and handle_kind in {"borrowed_field_descriptor", "borrowed_module_descriptor"}:
            return "unknown"
    return {
        "argument_descriptor": "call",
        "borrowed_field_descriptor": "parent_wrapper",
        "borrowed_module_descriptor": "module",
        "optional_absent_handle": "absent_or_call",
        "owned_result_descriptor": "wrapper_owner_storage",
    }[handle_kind]


def _native_array_destroy_behavior(handle_kind: str, blocker: str | None) -> str:
    """Return the allowed destruction behavior, blocking unsafe lifetime/release policies."""
    if handle_kind == "unsupported" or (
        blocker is not None
        and any(reason in blocker for reason in ("release policy", "stable owner storage", "target lifetime"))
    ):
        return "blocked"
    return {
        "argument_descriptor": "none",
        "borrowed_field_descriptor": "parent_wrapper_finalizer",
        "borrowed_module_descriptor": "none",
        "optional_absent_handle": "none",
        "owned_result_descriptor": "handle_finalizer",
        "unsupported": "blocked",
    }[handle_kind]


def _native_array_to_numpy_policy(
    descriptor_kind: str,
    handle_kind: str,
    decision: OwnershipDecision,
    semantic_type: models.SemanticType,
) -> str:
    """Return the supported NumPy exposure policy for a completed descriptor handle."""
    if handle_kind == "unsupported":
        return "unsupported"
    if descriptor_kind == "pointer":
        return _native_array_pointer_to_numpy_policy(semantic_type)
    if decision.is_blocked:
        return "unsupported"
    if handle_kind == "borrowed_module_descriptor" and not semantic_type.metadata.get("aliased"):
        return "descriptor_view"
    return "borrowed_view"


def _native_array_pointer_to_numpy_policy(semantic_type: models.SemanticType) -> str:
    """Choose pointer NumPy exposure from explicit pointer-policy metadata only."""
    pointer_policy = _pointer_policy_metadata(semantic_type)
    if not pointer_policy:
        return "unsupported"
    if _pointer_policy_value(pointer_policy, "contiguity") == "contiguous":
        return "contiguous_view"
    return "descriptor_view"


def _native_array_handle_operations(
    descriptor_kind: str,
    handle_kind: str,
    context: OwnershipContext,
    semantic_type: models.SemanticType,
) -> tuple[str, ...]:
    """Return the sorted descriptor operations allowed by kind, context, and metadata."""
    if handle_kind == "unsupported":
        return ()
    if descriptor_kind == "allocatable":
        operations = {"allocated", "to_numpy"}
        if handle_kind in {"borrowed_module_descriptor", "borrowed_field_descriptor", "owned_result_descriptor"} or (
            context.is_argument and context.writes_argument
        ):
            operations.add("deallocate")
            if not _is_deferred_character_array(semantic_type):
                operations.add("resize")
        return tuple(sorted(operations))
    operations = {"associate", "associated", "nullify", "to_numpy"}
    pointer_policy = _pointer_policy_metadata(semantic_type)
    if _pointer_policy_allows_allocate(pointer_policy):
        operations.add("allocate")
    if _pointer_policy_allows_deallocate(pointer_policy):
        operations.add("deallocate")
    if _pointer_policy_allows_resize(pointer_policy):
        operations.add("resize")
    return tuple(sorted(operations))


def _is_deferred_character_array(semantic_type: models.SemanticType) -> bool:
    """Return whether shape mutation also requires a runtime character length."""
    return semantic_type.name == "String" and semantic_type.metadata.get("fortran_character_length") == ":"


def _native_array_descriptor_interop_requirement(
    descriptor_kind: str,
    handle_kind: str,
    semantic_type: models.SemanticType,
) -> str:
    """Return the C-descriptor interop mechanism required by a supported handle."""
    if descriptor_kind == "allocatable" and handle_kind == "owned_result_descriptor":
        return "owned_allocatable_c_descriptor"
    if (
        descriptor_kind == "allocatable"
        and handle_kind == "borrowed_module_descriptor"
        and not semantic_type.metadata.get("aliased")
    ):
        return "module_allocatable_c_descriptor"
    if descriptor_kind == "pointer" and handle_kind != "unsupported":
        return "pointer_c_descriptor"
    return "none"


def _pointer_policy_metadata(semantic_type: models.SemanticType) -> dict[str, object]:
    """Copy pointer-policy metadata into a safe mutable mapping, or return an empty mapping."""
    policy = semantic_type.metadata.get(POINTER_POLICY_METADATA)
    return dict(policy) if isinstance(policy, dict) else {}


def _pointer_policy_value(policy: dict[str, object], key: str) -> str:
    """Normalize one string pointer-policy value for membership checks."""
    value = policy.get(key)
    return str(value).strip().casefold() if isinstance(value, str) else ""


def _pointer_policy_allows_allocate(policy: dict[str, object]) -> bool:
    """Report whether reassociation metadata permits pointer allocation."""
    return _pointer_policy_value(policy, "reassociation") in _POINTER_ALLOCATE_PERMISSION_VALUES


def _pointer_policy_allows_deallocate(policy: dict[str, object]) -> bool:
    """Report whether deallocation metadata permits pointer deallocation."""
    return _pointer_policy_value(policy, "deallocation") in _POINTER_DEALLOCATE_PERMISSION_VALUES


def _pointer_policy_allows_resize(policy: dict[str, object]) -> bool:
    """Report whether both pointer-policy dimensions permit resize operations."""
    reassociation = _pointer_policy_value(policy, "reassociation")
    deallocation = _pointer_policy_value(policy, "deallocation")
    return reassociation in _POINTER_RESIZE_PERMISSION_VALUES and deallocation in _POINTER_RESIZE_PERMISSION_VALUES


def _native_array_handle_blocker(
    _descriptor_kind: str,
    handle_kind: str,
    decision: OwnershipDecision,
) -> str | None:
    """Return the inherited ownership blocker or reject an unsupported descriptor origin."""
    if decision.is_blocked:
        return decision.blocker or decision.reason
    if handle_kind == "unsupported":
        return "native array handle origin is unsupported before wrapper lowering"
    return None


# Callable projections and raw-address validation


def _complete_callable_address_policy(function: models.SemanticFunction) -> None:
    """Validate Python/native address boundaries and complete scalar projections."""
    _complete_hidden_scalar_output_projections(function)
    visible_scalar_names = {
        argument.name for argument in function.arguments if _is_visible_extent_source(argument.semantic_type)
    }
    for argument in function.arguments:
        _validate_raw_address_type(
            argument.semantic_type,
            owner=function.name,
            item=argument.name,
            visible_scalar_names=visible_scalar_names,
        )
    if function.return_type is not None:
        _validate_raw_address_type(
            function.return_type,
            owner=function.name,
            item="return",
            visible_scalar_names=visible_scalar_names,
        )
    _complete_native_address_projections(function)


def _complete_hidden_scalar_output_projections(function: models.SemanticFunction) -> None:
    """Complete every primitive hidden ``Return(...)`` as address storage."""
    arguments_by_name = {argument.name: argument for argument in function.arguments}
    for mapping in function.projection:
        if mapping.python_position is not None or mapping.result_position is None:
            continue
        if mapping.value_kind:
            continue
        argument = arguments_by_name.get(mapping.python_name)
        if argument is None or not _is_primitive_scalar_value(argument.semantic_type, allow_completed_projection=True):
            continue
        _apply_scalar_address_projection(argument)


def _complete_native_address_projections(function: models.SemanticFunction) -> None:
    """Validate ``Addr(Arg(i))`` mappings and mutate eligible scalars to address storage."""
    arguments_by_name = {argument.name: argument for argument in function.arguments}
    for mapping in function.projection:
        if mapping.value_kind != "addr":
            continue
        value = mapping.value
        if not isinstance(value, dict) or value.get("kind") != "arg":
            raise ValueError(
                f"Invalid native Addr projection in {function.name!r}: only Addr(Arg(i)) is supported; "
                "Return and Work projections already name native storage."
            )
        argument = arguments_by_name.get(mapping.python_name)
        if argument is None:
            position = mapping.python_position
            if not isinstance(position, int) or not 0 <= position < len(function.arguments):
                raise ValueError(f"Invalid native Addr projection in {function.name!r}: argument is out of range")
            argument = function.arguments[position]
        if not _is_primitive_scalar_value(argument.semantic_type, allow_completed_projection=True):
            raise ValueError(
                f"Invalid native Addr projection for {function.name!r} argument {argument.name!r}: "
                "Addr(Arg(i)) is only valid for primitive scalar values; use Arg(i) for arrays, strings, "
                "scalar storage, wrapped objects, and raw addresses."
            )
        _apply_scalar_address_projection(argument)


def _apply_scalar_address_projection(argument: models.SemanticArgument) -> None:
    """Replace an eligible scalar argument's storage with its completed address projection.

    The argument type is mutated in place.  A declared call-local transfer stays
    read-only unless the argument projects a result; all other scalar address
    projections become writable native storage.
    """
    semantic_type = argument.semantic_type
    storage = semantic_type.storage
    metadata = dict(storage.metadata) if storage is not None else {}
    metadata[ADDRESS_ROLE_METADATA] = ADDRESS_ROLE_PROJECTION
    explicit_policy = semantic_type.metadata.get(OWNERSHIP_POLICY_METADATA)
    transfer = explicit_policy.get("transfer") if isinstance(explicit_policy, dict) else None
    projects_output = bool(argument.metadata.get(PROJECTED_OUTPUT_METADATA))
    read_only = transfer == "call_local" and not projects_output
    mutable = not read_only
    semantic_type.storage = models.SemanticStorageContract(
        kind="address",
        read_only=read_only,
        mutable=mutable,
        pointer_depth=1,
        ownership=storage.ownership if storage is not None else "borrowed",
        calling_convention=storage.calling_convention if storage is not None else None,
        metadata=metadata,
    )
    semantic_type.ownership.mutable = mutable


def _is_primitive_scalar_value(
    semantic_type: models.SemanticType,
    *,
    allow_completed_projection: bool = False,
) -> bool:
    """Report whether a type is a plain scalar value or an allowed completed address projection."""
    if semantic_type.rank != 0 or semantic_type.name == "String":
        return False
    if (semantic_type.dtype or semantic_type.name) not in SEMANTIC_SCALAR_TYPE_NAMES:
        return False
    storage = semantic_type.storage
    if storage is None or storage.kind == "value":
        return True
    return bool(
        allow_completed_projection
        and storage.kind == "address"
        and storage.pointer_depth == 1
        and storage.metadata.get(ADDRESS_ROLE_METADATA) == ADDRESS_ROLE_PROJECTION
    )


def _is_visible_extent_source(semantic_type: models.SemanticType) -> bool:
    """Report whether a scalar type can safely supply an array/raw-address extent name."""
    if _is_primitive_scalar_value(semantic_type, allow_completed_projection=True):
        return True
    storage = semantic_type.storage
    return bool(
        semantic_type.rank == 0
        and semantic_type.name != "String"
        and (semantic_type.dtype or semantic_type.name) in SEMANTIC_SCALAR_TYPE_NAMES
        and storage is not None
        and storage.array is not None
        and storage.array.category == SCALAR_STORAGE_CATEGORY
    )


def _validate_raw_address_type(
    semantic_type: models.SemanticType,
    *,
    owner: str,
    item: str,
    visible_scalar_names: set[str],
) -> None:
    """Reject unsupported raw-address shape, type, depth, and extent combinations.

    Types without raw-address metadata are ignored.  Raw arrays and strings
    must be primitive and fully described by literals or visible scalar
    arguments; unsupported contracts fail before wrapper planning.
    """
    storage = semantic_type.storage
    if storage is None or storage.metadata.get(ADDRESS_ROLE_METADATA) != ADDRESS_ROLE_RAW:
        return
    if storage.pointer_depth != 1:
        raise ValueError(
            f"Invalid raw address contract for {owner!r} {item!r}: callable Addr(T) supports depth one only."
        )
    if semantic_type.rank > 0:
        if (semantic_type.dtype or semantic_type.name) not in SEMANTIC_SCALAR_TYPE_NAMES:
            raise ValueError(
                f"Invalid raw address contract for {owner!r} {item!r}: raw arrays require a primitive dtype."
            )
        dimensions = _semantic_shape(semantic_type)
        if len(dimensions) != semantic_type.rank or not all(
            _is_resolved_extent(dimension, visible_scalar_names) for dimension in dimensions
        ):
            raise ValueError(
                f"Invalid raw address contract for {owner!r} {item!r}: raw arrays require a fully resolved "
                "rank and shape using literals or visible scalar arguments."
            )
        return
    if semantic_type.name == "String":
        length = semantic_type.metadata.get("fortran_character_length")
        if length is None or not _is_resolved_extent(length, visible_scalar_names):
            raise ValueError(
                f"Invalid raw address contract for {owner!r} {item!r}: raw strings require a fixed length."
            )
        return
    if (semantic_type.dtype or semantic_type.name) not in SEMANTIC_SCALAR_TYPE_NAMES:
        raise ValueError(
            f"Invalid raw address contract for {owner!r} {item!r}: Addr(WrappedType) is not allowed; "
            "use WrappedType and Arg(i)."
        )


def _semantic_shape(semantic_type: models.SemanticType) -> list[str]:
    """Return a type's semantic shape, falling back to array storage source shape."""
    if semantic_type.shape:
        return [str(dimension) for dimension in semantic_type.shape]
    storage = semantic_type.storage
    array = storage.array if storage is not None else None
    if array is None:
        return []
    return [str(dimension) for dimension in (array.shape or array.source_shape)]


def _is_resolved_extent(value: object, visible_scalar_names: set[str]) -> bool:
    """Report whether an extent is concrete or references only visible scalar inputs."""
    text = str(value).strip()
    if not text or text in {":", "*", "...", ".."} or ":" in text:
        return False
    names = set(re.findall(r"\b[A-Za-z_]\w*\b", text))
    return names <= visible_scalar_names


def _complete_variable(
    variable: models.SemanticVariable,
    context: OwnershipContext,
    *,
    owner_path: str | None = None,
) -> None:
    """Attach ownership, callback, and descriptor-handle policies to one variable.

    The variable and nested callback type metadata are mutated in place.
    ``MaybeUnallocated`` is rejected outside direct function returns so later
    stages never receive an ambiguous variable contract.
    """
    if variable.semantic_type.metadata.get(MAYBE_UNALLOCATED_METADATA):
        raise ValueError(
            f"MaybeUnallocated metadata on {owner_path or variable.name!r} is only valid on function return types"
        )
    decision = default_ownership_policy.decide_semantic_variable(variable, context)
    variable.metadata[models.RESOLVED_OWNERSHIP_POLICY_METADATA] = decision
    _complete_prototype_reference_policy(variable.semantic_type, owner_path=owner_path or variable.name)
    _complete_native_array_handle_variable_policy(variable, context)


def _complete_accessor_policies(variable: models.SemanticVariable, context: OwnershipContext) -> None:
    """Attach resolved getter and setter decisions, then refresh descriptor-handle facts."""
    variable.metadata[models.RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA] = (
        default_ownership_policy.decide_semantic_getter(variable, context)
    )
    variable.metadata[models.RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA] = (
        default_ownership_policy.decide_semantic_setter(variable, context)
    )
    _complete_native_array_handle_variable_policy(variable, context)


def _complete_module_variable_initializer(variable: models.SemanticVariable) -> None:
    """Record a safe scalar write-through module initializer, or remove stale metadata."""
    variable.metadata.pop(models.RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA, None)
    if variable.default_value is None or _is_constant(variable):
        return
    setter = variable.metadata[models.RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA]
    if variable.semantic_type.rank != 0 or setter.setter_action is not SetterAction.WRITE_THROUGH:
        return
    variable.metadata[models.RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA] = variable.default_value


def _is_constant(variable: models.SemanticVariable) -> bool:
    """Report whether a semantic variable is constrained as a compile-time constant."""
    return any(constraint.name == "Constant" for constraint in variable.semantic_type.constraints)


# Callback prototype completion


def _complete_prototype_reference_policy(
    semantic_type: models.SemanticType,
    *,
    owner_path: str,
) -> None:
    """Complete callback handoff policy and validate nested callback ABI contracts.

    Non-callback types are left untouched.  Callback arguments and returns are
    completed in place with callback-specific ownership contexts before the
    final handoff policy is stored on the outer semantic type.
    """
    if semantic_type.storage is None or semantic_type.storage.kind != "callback":
        return

    visible_scalar_names: set[str] = set()
    callback_arguments = semantic_type.metadata.get("callback_arguments")
    if isinstance(callback_arguments, list):
        visible_scalar_names = {
            argument.name
            for argument in callback_arguments
            if isinstance(argument, models.SemanticArgument) and _is_visible_extent_source(argument.semantic_type)
        }
        for index, argument in enumerate(callback_arguments):
            if isinstance(argument, models.SemanticArgument):
                _validate_callback_argument_contract(argument)
                _validate_raw_address_type(
                    argument.semantic_type,
                    owner="prototype",
                    item=argument.name,
                    visible_scalar_names=visible_scalar_names,
                )
                _complete_variable(
                    argument,
                    _callback_argument_ownership_context(argument),
                    owner_path=f"{owner_path}.callback_arg_{index}",
                )

    return_type = semantic_type.metadata.get("return")
    if isinstance(return_type, models.SemanticType) and return_type.name != "None":
        _validate_raw_address_type(
            return_type,
            owner="prototype",
            item="return",
            visible_scalar_names=visible_scalar_names,
        )
        decision = default_ownership_policy.decide_semantic_type(return_type, OwnershipContext.result())
        return_type.metadata[models.RESOLVED_OWNERSHIP_POLICY_METADATA] = decision
    semantic_type.metadata[models.RESOLVED_CALLBACK_POLICY_METADATA] = build_callback_handoff_policy(
        semantic_type,
        owner_path=owner_path,
    )


def _callback_argument_ownership_context(argument: models.SemanticArgument) -> OwnershipContext:
    """Return the read-only/value or writable/reference context declared by a callback argument."""
    if bool(getattr(argument.origin, "metadata", {}).get("value")):
        return OwnershipContext.argument(reads_argument=True, writes_argument=False)
    return OwnershipContext.argument(reads_argument=True, writes_argument=True)


def _validate_callback_argument_contract(argument: models.SemanticArgument) -> None:
    """Require reference callback strings to use mutable scalar character storage."""
    semantic_type = argument.semantic_type
    if semantic_type.name != "String":
        return
    if bool(getattr(argument.origin, "metadata", {}).get("value")):
        return
    if _is_scalar_string_storage(semantic_type):
        return
    raise ValueError("Reference callback strings require mutable scalar character storage")


def _is_scalar_string_storage(semantic_type: models.SemanticType) -> bool:
    """Report whether a type uses the rank-zero scalar-character storage representation."""
    storage = semantic_type.storage
    array = storage.array if storage is not None else None
    return bool(
        storage is not None
        and storage.kind == "array"
        and array is not None
        and array.rank == 0
        and array.category == SCALAR_STORAGE_CATEGORY
    )


if __name__ == "__main__":
    from prik.semantics.models import SemanticArgument, SemanticFunction, SemanticModule, SemanticType

    semantic_module = SemanticModule(
        name="math",
        functions=[
            SemanticFunction(
                name="scale",
                arguments=[SemanticArgument("value", SemanticType("Float64", dtype="Float64"))],
                return_type=SemanticType("Float64", dtype="Float64"),
            )
        ],
    )
    semantic_function = semantic_module.functions[0]
    semantic_argument = semantic_function.arguments[0]
    print(
        f"before: {semantic_module.name}.{semantic_function.name}({semantic_argument.name}): "
        f"{semantic_argument.semantic_type.name} semantic IR"
    )
    complete_semantic_policies(semantic_module)
    function_policy = semantic_function.metadata[models.RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    argument_policy = function_policy.arguments[0]
    native_slot = function_policy.native_call_slots[0]
    print(
        f"after: {semantic_module.name}.{semantic_function.name}({argument_policy.python_name}): "
        f"{argument_policy.python_barrier_action.value} -> {native_slot.native_barrier_action.value}"
    )
