"""Language-neutral semantic IR records shared by later stages.

``SemanticModule`` is the convergence object produced by frontend conversion.
Its declarations retain stable type, storage, projection, and provenance facts
through ``SemanticType``, ``SemanticStorageContract``, and ``SemanticOrigin``.
The records do not complete ownership or choose emitted mechanisms; policy and
planning own those later decisions. Read the public dataclasses in module
order, then the equality helpers that define structural comparison.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


EXTERNAL_TYPE_REF_METADATA = "external_type_ref"
PROTOTYPE_REF_METADATA = "prototype_ref"
PROTOTYPE_INTENT_METADATA = "prototype_intent"
INTERNAL_MODULE_VARIABLE_ACCESS_METADATA = "internal_module_variable_access"
INTERNAL_MODULE_VARIABLE_NAME_METADATA = "internal_module_variable_name"
INTERNAL_NATIVE_ARRAY_HANDLE_OPERATION_METADATA = "internal_native_array_handle_operation"
INTERNAL_NATIVE_ARRAY_HANDLE_OWNER_CLASS_METADATA = "internal_native_array_handle_owner_class"
PYTHON_VALUE_MUTABILITY_METADATA = "python_value_mutability"
PYTHON_VALUE_IMMUTABLE = "immutable"
NATIVE_BY_VALUE_METADATA = "native_by_value"
RUNTIME_RELEASE_GIL_METADATA = "runtime_release_gil"
RUNTIME_RETAIN_RESULT_OWNER_METADATA = "runtime_retain_result_owner"
RUNTIME_STATUS_ERROR_METADATA = "runtime_status_error"
RESOLVED_RUNTIME_STATUS_ERROR_POLICY_METADATA = "resolved_runtime_status_error_policy"
DECLARATION_EXPRESSION_CALLABLES_METADATA = "declaration_expression_callables"


# ============================================================
# Semantic Constraints
# ============================================================


@dataclass
class SemanticConstraint:
    name: str
    arguments: list[Any] = field(default_factory=list)


# ============================================================
# Semantic Coercions
# ============================================================


@dataclass
class SemanticCoercion:
    source_type: str
    implicit: bool = True
    cost: int = 1
    zero_copy: bool = False


# ============================================================
# Ownership / Lifetime
# ============================================================


@dataclass
class OwnershipPolicy:
    ownership: str = "borrowed"
    mutable: bool = False
    aliasing: bool = True


# ============================================================
# Origin And Storage Contracts
# ============================================================


@dataclass
class SemanticOrigin:
    source_language: str | None = None
    native_name: str | None = None
    native_abi: str | None = None
    native_symbol: str | None = None
    native_scope: str | None = None
    source_kind: str | None = None
    source_type: str | None = None
    source_location: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticExpressionCallable:
    """Identify a native callable referenced by a declaration expression.

    ``name`` is the spelling used by the semantic contract. ``native_name``
    and ``native_scope`` preserve the source declaration reached by normal
    language name resolution. ``placement`` distinguishes a concrete standalone
    interface from an unresolved name when neither has a module scope. The
    optional declaration link is semantic-only and lets post-IR policy validate
    exact prototype characteristics without duplicating them on the call site.
    """

    name: str
    native_name: str | None = None
    native_scope: str | None = None
    source_language: str | None = None
    placement: str | None = None
    declaration: SemanticFunction | None = field(default=None, compare=False, repr=False)


@dataclass
class SemanticArrayContract:
    """Describe an array's semantic shape, storage layout, and provenance.

    Shape entries use the public language-neutral expression dialect.
    The ``expression_callables`` property is parallel to ``shape`` and records
    native procedure identities used by each axis; source bounds retain the
    original declaration syntax for diagnostics and source-oriented consumers.
    """

    rank: int | None = None
    shape: list[str] = field(default_factory=list)
    # Native-source provenance, excluded from public contract equality.
    lower_bounds: list[str | None] = field(default_factory=list)
    upper_bounds: list[str | None] = field(default_factory=list)
    source_shape: list[str] = field(default_factory=list)
    category: str | None = None
    order: str | None = None
    copy_order: str | None = None
    axes: list[str] = field(default_factory=list)
    contiguous: bool | None = None
    allocatable: bool = False
    pointer: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def expression_callables(self) -> list[list[SemanticExpressionCallable]]:
        """Return native callable references aligned with the array's shape axes.

        Empty axes are represented by empty lists. Arrays without any callable
        reference return an empty list and do not gain serialized metadata.
        """
        value = self.metadata.get(DECLARATION_EXPRESSION_CALLABLES_METADATA, [])
        return value if isinstance(value, list) else []

    @expression_callables.setter
    def expression_callables(self, value: list[list[SemanticExpressionCallable]]) -> None:
        """Store nonempty per-axis references or remove empty provenance.

        The setter consumes a shape-aligned list and mutates only ``metadata``.
        Omitting all-empty data preserves the historical serialization of
        arrays that do not use declaration functions.
        """
        if any(value):
            self.metadata[DECLARATION_EXPRESSION_CALLABLES_METADATA] = value
        else:
            self.metadata.pop(DECLARATION_EXPRESSION_CALLABLES_METADATA, None)


@dataclass
class SemanticStorageContract:
    kind: str = "value"
    read_only: bool = False
    mutable: bool = False
    pointer_depth: int = 0
    ownership: str = "borrowed"
    array: SemanticArrayContract | None = None
    calling_convention: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================
# Semantic Types
# ============================================================


@dataclass(eq=False)
class SemanticType:
    name: str

    rank: int = 0

    dtype: str | None = None

    shape: list[str] = field(default_factory=list)

    constraints: list[SemanticConstraint] = field(default_factory=list)

    coercions: list[SemanticCoercion] = field(default_factory=list)

    ownership: OwnershipPolicy = field(default_factory=OwnershipPolicy)

    metadata: dict[str, Any] = field(default_factory=dict)

    storage: SemanticStorageContract | None = None

    origin: SemanticOrigin = field(default_factory=SemanticOrigin, compare=False)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticType):
            return False
        return _semantic_type_key(self, {}) == _semantic_type_key(other, {})


# ============================================================
# Semantic Variables And Bindings
# ============================================================


@dataclass
class SemanticVariable:
    name: str

    semantic_type: SemanticType

    visibility: str = "public"

    default_value: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    origin: SemanticOrigin = field(default_factory=SemanticOrigin, compare=False)

    @property
    def optional(self) -> bool:
        """Compatibility view for data declarations parsed from ``= ...``."""
        return bool(self.metadata.get("optional", False))

    @optional.setter
    def optional(self, value: bool) -> None:
        if value:
            self.metadata["optional"] = True
        else:
            self.metadata.pop("optional", None)


@dataclass(init=False)
class SemanticArgument(SemanticVariable):
    optional: bool = False

    def __init__(
        self,
        name: str,
        semantic_type: SemanticType,
        optional: bool = False,
        visibility: str = "public",
        default_value: str | None = None,
        metadata: dict[str, Any] | None = None,
        origin: SemanticOrigin | None = None,
    ) -> None:
        self.name = name
        self.semantic_type = semantic_type
        self.visibility = visibility
        self.default_value = default_value
        self.metadata = {} if metadata is None else metadata
        self.optional = optional
        self.origin = SemanticOrigin() if origin is None else origin


@dataclass
class SemanticField(SemanticVariable):
    pass


# ============================================================
# Semantic Contracts
# ============================================================


@dataclass
class SemanticContract:
    name: str | None = None

    preconditions: list[str] = field(default_factory=list)

    postconditions: list[str] = field(default_factory=list)

    invariants: list[str] = field(default_factory=list)


# ============================================================
# API Projection
# ============================================================


@dataclass
class ProjectionMapping:
    python_name: str | None = None
    native_name: str = ""
    native_position: int | None = None
    python_position: int | None = None
    result_position: int | None = None
    value_kind: str = ""
    value: Any = None


# ============================================================
# Semantic Functions
# ============================================================


@dataclass(eq=False)
class SemanticFunction:
    name: str

    native_name: str | None = None

    arguments: list[SemanticArgument] = field(default_factory=list)

    return_type: SemanticType | None = None
    locals: list[SemanticVariable] = field(default_factory=list)

    contracts: list[SemanticContract] = field(default_factory=list)

    projection: list[ProjectionMapping] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
    visibility: str = "public"
    origin: SemanticOrigin = field(default_factory=SemanticOrigin, compare=False)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, SemanticFunction):
            return False

        self_call_args = _call_arguments(self)
        other_call_args = _call_arguments(other)
        self_name_map = _argument_name_map(self_call_args)
        other_name_map = _argument_name_map(other_call_args)
        return (
            self.name,
            self.native_name,
            _function_arguments_key(self_call_args, self_name_map),
            self.locals,
            _return_projection_key(self, self_name_map),
            self.contracts,
            _projection_key(self.projection, self_name_map),
            self.metadata,
            self.visibility,
            getattr(self, "is_static", None),
            getattr(self, "passed_object_name", None),
            getattr(self, "passed_object_position", None),
            getattr(self, "binding_attributes", ()),
            getattr(self, "pure", None),
        ) == (
            other.name,
            other.native_name,
            _function_arguments_key(other_call_args, other_name_map),
            other.locals,
            _return_projection_key(other, other_name_map),
            other.contracts,
            _projection_key(other.projection, other_name_map),
            other.metadata,
            other.visibility,
            getattr(other, "is_static", None),
            getattr(other, "passed_object_name", None),
            getattr(other, "passed_object_position", None),
            getattr(other, "binding_attributes", ()),
            getattr(other, "pure", None),
        )


# ============================================================
# Named Procedure Prototypes
# ============================================================


@dataclass(eq=False)
class SemanticPrototype(SemanticFunction):
    """Reusable exact native procedure signature with no Python export."""

    pure: bool = False


# ============================================================
# Semantic Methods
# ============================================================


@dataclass(eq=False)
class SemanticMethod(SemanticFunction):
    is_static: bool = False
    passed_object_name: str | None = None
    passed_object_position: int | None = None
    binding_attributes: tuple[str, ...] = ()


@dataclass
class ProcedureOverloadSet:
    name: str
    procedures: list[SemanticFunction] = field(default_factory=list)


FORTRAN_GENERIC_NAME_METADATA = "fortran_generic_name"
OVERLOAD_KIND_METADATA = "overload_kind"
OVERLOAD_TARGET_METADATA = "overload_target"
PYTHON_BOUND_POSITION_METADATA = "python_bound_position"
PYTHON_METHOD_NAME_METADATA = "python_method_name"
PYTHON_EXPORTS_METADATA = "python_exports"
PYTHON_EXPORTS_PREPARED_METADATA = "python_exports_prepared"
POLICY_COMPLETION_PREPARED_METADATA = "policy_completion_prepared"
RESOLVED_OWNERSHIP_POLICY_METADATA = "resolved_ownership_policy"
RESOLVED_RETURN_OWNERSHIP_POLICY_METADATA = "resolved_return_ownership_policy"
RESOLVED_UPDATE_RESULT_OWNERSHIP_POLICY_METADATA = "resolved_update_result_ownership_policy"
RESOLVED_CLASS_INSTANCE_POLICY_METADATA = "resolved_class_instance_policy"
RESOLVED_CLASS_SELF_POLICY_METADATA = "resolved_class_self_policy"
RESOLVED_DERIVED_FIELD_POLICY_METADATA = "resolved_derived_field_policy"
RESOLVED_DERIVED_TYPE_POLICY_METADATA = "resolved_derived_type_policy"
RESOLVED_CLASS_SURFACE_POLICY_METADATA = "resolved_class_surface_policy"
RESOLVED_MODULE_OVERLOAD_POLICIES_METADATA = "resolved_module_overload_policies"
RESOLVED_DERIVED_TYPE_IDENTITY_METADATA = "resolved_derived_type_identity"
RESOLVED_GETTER_OWNERSHIP_POLICY_METADATA = "resolved_getter_ownership_policy"
RESOLVED_SETTER_OWNERSHIP_POLICY_METADATA = "resolved_setter_ownership_policy"
RESOLVED_NATIVE_ARRAY_HANDLE_POLICY_METADATA = "resolved_native_array_handle_policy"
RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA = "resolved_function_wrapper_policy"
RESOLVED_CALLBACK_POLICY_METADATA = "resolved_callback_policy"
RESOLVED_MODULE_VARIABLE_POLICY_METADATA = "resolved_module_variable_policy"
RESOLVED_MODULE_VARIABLE_INITIALIZER_METADATA = "resolved_module_variable_initializer"
PYTHON_STATIC_METADATA = "python_static"


def _call_arguments(func: SemanticFunction) -> list[SemanticArgument]:
    return list(func.arguments)


def _argument_name_map(arguments: list[SemanticArgument]) -> dict[str, str]:
    return {arg.name: f"__arg_{i}__" for i, arg in enumerate(arguments)}


def _function_arguments_key(
    arguments: list[SemanticArgument],
    name_map: dict[str, str],
) -> tuple[tuple[Any, ...], ...]:
    return tuple(_function_argument_key(arg, name_map) for arg in arguments)


def _function_argument_key(
    arg: SemanticArgument,
    name_map: dict[str, str],
) -> tuple[Any, ...]:
    return (
        _semantic_type_key(arg.semantic_type, name_map),
        arg.optional,
        arg.visibility,
        _canonical_expression(arg.default_value, name_map),
        arg.metadata,
    )


def _semantic_type_key(
    semantic_type: SemanticType | None,
    name_map: dict[str, str],
    *,
    include_ownership: bool = True,
) -> tuple[Any, ...] | None:
    if semantic_type is None:
        return None
    shape = (
        semantic_type.storage.array.shape
        if semantic_type.storage is not None and semantic_type.storage.array is not None
        else semantic_type.shape
    )
    return (
        semantic_type.name,
        semantic_type.rank,
        semantic_type.dtype,
        tuple(_canonical_expression(item, name_map) for item in shape),
        tuple(_constraint_key(c, name_map) for c in _semantic_contract_constraints(semantic_type)),
        tuple(semantic_type.coercions),
        semantic_type.ownership if include_ownership else None,
        semantic_type.metadata,
        _storage_contract_key(semantic_type.storage, name_map),
    )


def _semantic_contract_constraints(semantic_type: SemanticType) -> list[SemanticConstraint]:
    if semantic_type.storage is None:
        return semantic_type.constraints
    storage_constraint_names = {
        "Allocatable",
        "ORDER_ANY",
        "ORDER_C",
        "ORDER_F",
        "Pointer",
    }
    return [constraint for constraint in semantic_type.constraints if constraint.name not in storage_constraint_names]


def _storage_contract_key(
    storage: SemanticStorageContract | None,
    name_map: dict[str, str],
) -> tuple[Any, ...] | None:
    if storage is None:
        return None
    return (
        storage.kind,
        storage.read_only,
        storage.mutable,
        storage.pointer_depth,
        storage.ownership,
        _array_contract_key(storage.array, name_map),
        storage.calling_convention,
        _canonical_expression(storage.metadata, name_map),
    )


def _array_contract_key(
    array: SemanticArrayContract | None,
    name_map: dict[str, str],
) -> tuple[Any, ...] | None:
    if array is None:
        return None
    return (
        array.rank,
        tuple(_canonical_expression(item, name_map) for item in array.shape),
        array.order,
        array.copy_order,
        tuple(array.axes),
        array.contiguous,
        array.allocatable,
        array.pointer,
        _canonical_expression(array.metadata, name_map),
    )


def _return_projection_key(
    func: SemanticFunction,
    name_map: dict[str, str],
) -> tuple[tuple[Any, ...], ...]:
    returns: list[tuple[Any, ...]] = []
    if func.return_type is not None:
        returns.append((_semantic_type_key(func.return_type, name_map, include_ownership=False),))
    return tuple(returns)


def _projection_key(
    projection: list[ProjectionMapping],
    name_map: dict[str, str],
) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            mapping.native_position,
            mapping.python_position,
            mapping.result_position,
            mapping.value_kind,
            _native_projection_value_key(mapping.value, name_map),
        )
        for mapping in projection
        if _requires_explicit_projection_mapping(mapping)
    )


def _requires_explicit_projection_mapping(mapping: ProjectionMapping) -> bool:
    if mapping.value_kind:
        return True
    if mapping.result_position is not None:
        return mapping.python_position is None or mapping.python_position != mapping.native_position
    if mapping.python_position is None:
        return True
    return mapping.native_position is not None and mapping.python_position != mapping.native_position


def _native_projection_value_key(value: Any, name_map: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return tuple(sorted((key, _native_projection_value_key(item, name_map)) for key, item in value.items()))
    if isinstance(value, list | tuple):
        return tuple(_native_projection_value_key(item, name_map) for item in value)
    return _canonical_expression(value, name_map)


def _constraint_key(
    constraint: SemanticConstraint,
    name_map: dict[str, str],
) -> tuple[Any, ...]:
    return (
        constraint.name,
        tuple(_canonical_expression(arg, name_map) for arg in constraint.arguments),
    )


def _canonical_expression(value: Any, name_map: dict[str, str]) -> Any:
    if isinstance(value, str):
        return _canonical_expression_text(value, name_map)
    if isinstance(value, list):
        return [_canonical_expression(item, name_map) for item in value]
    if isinstance(value, tuple):
        return tuple(_canonical_expression(item, name_map) for item in value)
    if isinstance(value, dict):
        return {
            _canonical_expression(key, name_map): _canonical_expression(item, name_map) for key, item in value.items()
        }
    return value


def _canonical_expression_text(text: str, name_map: dict[str, str]) -> str:
    if not name_map:
        return text
    result = text
    for name, placeholder in name_map.items():
        result = re.sub(rf"\b{re.escape(name)}\b", placeholder, result)
    return result


# ============================================================
# Semantic Classes
# ============================================================


@dataclass
class SemanticClass:
    name: str

    native_name: str | None = None

    fields: list[SemanticField] = field(default_factory=list)

    methods: list[SemanticMethod] = field(default_factory=list)

    overload_sets: list[ProcedureOverloadSet] = field(default_factory=list)

    classes: list[SemanticClass] = field(default_factory=list)

    base_classes: list[str] = field(default_factory=list)

    contracts: list[SemanticContract] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
    visibility: str = "public"
    origin: SemanticOrigin = field(default_factory=SemanticOrigin, compare=False)


# ============================================================
# Semantic Modules
# ============================================================


@dataclass
class SemanticImportItem:
    source: str
    target: str | None = None


@dataclass
class SemanticImport:
    module: str
    items: list[SemanticImportItem] = field(default_factory=list)


@dataclass
class SemanticModule:
    name: str

    functions: list[SemanticFunction] = field(default_factory=list)

    prototypes: list[SemanticPrototype] = field(default_factory=list)

    overload_sets: list[ProcedureOverloadSet] = field(default_factory=list)

    classes: list[SemanticClass] = field(default_factory=list)
    variables: list[SemanticVariable] = field(default_factory=list)

    imports: list[str | SemanticImport] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    origin: SemanticOrigin = field(default_factory=SemanticOrigin, compare=False)


def _semantic_type_tree(semantic_type: SemanticType | None) -> tuple[SemanticType, ...]:
    """Collect one semantic type and its callback signature in stable order."""
    if semantic_type is None:
        return ()
    collected = []
    pending = [semantic_type]
    while pending:
        current = pending.pop()
        collected.append(current)
        if current.storage is None or current.storage.kind != "callback":
            continue
        nested = []
        arguments = current.metadata.get("arguments")
        if isinstance(arguments, list):
            nested.extend(arguments)
        result = current.metadata.get("return")
        if result is not None:
            nested.append(result)
        pending.extend(reversed(nested))
    return tuple(collected)


def _module_semantic_types(module: SemanticModule) -> tuple[SemanticType, ...]:
    """Collect every semantic type owned by a module in established order."""

    def class_types(declaration: SemanticClass) -> tuple[SemanticType, ...]:
        collected = []
        for nested in declaration.classes:
            collected.extend(class_types(nested))
        for semantic_field in declaration.fields:
            collected.extend(_semantic_type_tree(semantic_field.semantic_type))
        for method in declaration.methods:
            for argument in method.arguments:
                collected.extend(_semantic_type_tree(argument.semantic_type))
            collected.extend(_semantic_type_tree(method.return_type))
        for overload_set in declaration.overload_sets:
            for procedure in overload_set.procedures:
                for argument in procedure.arguments:
                    collected.extend(_semantic_type_tree(argument.semantic_type))
                collected.extend(_semantic_type_tree(procedure.return_type))
        return tuple(collected)

    collected = []
    for variable in module.variables:
        collected.extend(_semantic_type_tree(variable.semantic_type))
    for declaration in module.classes:
        collected.extend(class_types(declaration))
    for function in module.functions:
        for argument in function.arguments:
            collected.extend(_semantic_type_tree(argument.semantic_type))
        collected.extend(_semantic_type_tree(function.return_type))
    for prototype in module.prototypes:
        for argument in prototype.arguments:
            collected.extend(_semantic_type_tree(argument.semantic_type))
        collected.extend(_semantic_type_tree(prototype.return_type))
    for overload_set in module.overload_sets:
        for procedure in overload_set.procedures:
            for argument in procedure.arguments:
                collected.extend(_semantic_type_tree(argument.semantic_type))
            collected.extend(_semantic_type_tree(procedure.return_type))
    return tuple(collected)


if __name__ == "__main__":
    example_type = SemanticType(
        "Float64",
        rank=1,
        dtype="float64",
        shape=["n"],
        storage=SemanticStorageContract(
            kind="array",
            array=SemanticArrayContract(rank=1, shape=["n"], order="F"),
        ),
        origin=SemanticOrigin(source_language="fortran", source_type="real"),
    )
    example_function = SemanticFunction(
        "scale",
        native_name="SCALE",
        arguments=[SemanticArgument("values", example_type)],
    )
    example_module = SemanticModule("geometry", functions=[example_function])

    print(f"Semantic module: {example_module.name}")
    print(f"Function: {example_function.name} -> native {example_function.native_name}")
    print(
        f"Argument: values: {example_type.name}, rank={example_type.rank}, "
        f"shape={tuple(example_type.shape)}, order={example_type.storage.array.order}"
    )
    print(f"Source provenance: {example_type.origin.source_language} {example_type.origin.source_type}")
