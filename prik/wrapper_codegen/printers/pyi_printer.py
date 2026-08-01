from __future__ import annotations

import ast
from collections.abc import Iterable
from copy import deepcopy
import json
import keyword
import re

from prik.contracts import CONTRACT_SYMBOLS, CONTRACT_TYPE_NAMES
from prik.naming import NamingPolicy
from prik.semantics.ownership import OWNERSHIP_POLICY_METADATA, POINTER_POLICY_FIELDS, POINTER_POLICY_METADATA
from prik.types.numpy import SEMANTIC_DTYPE_TO_NUMPY_DTYPE, SEMANTIC_SCALAR_TYPE_NAMES
from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_PROJECTION,
    ADDRESS_ROLE_RAW,
    BIND_TARGET_METADATA,
    MAYBE_UNALLOCATED_METADATA,
    NATIVE_PROJECTION_METADATA,
    OPTIONAL_ABSENT_HANDLE_METADATA,
    SCALAR_STORAGE_CATEGORY,
    USER_PRIVATE_METADATA,
)
from prik.semantics.models import (
    EXTERNAL_TYPE_REF_METADATA,
    FORTRAN_GENERIC_NAME_METADATA,
    OVERLOAD_KIND_METADATA,
    OVERLOAD_TARGET_METADATA,
    NATIVE_BY_VALUE_METADATA,
    PYTHON_BOUND_POSITION_METADATA,
    PYTHON_METHOD_NAME_METADATA,
    PYTHON_STATIC_METADATA,
    PYTHON_VALUE_IMMUTABLE,
    PYTHON_VALUE_MUTABILITY_METADATA,
    PROTOTYPE_REF_METADATA,
    RUNTIME_RELEASE_GIL_METADATA,
    RUNTIME_STATUS_ERROR_METADATA,
    ProjectionMapping,
    ProcedureOverloadSet,
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticConstraint,
    SemanticFunction,
    SemanticImport,
    SemanticImportItem,
    SemanticMethod,
    SemanticModule,
    SemanticPrototype,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
    _iter_module_semantic_types,
)
from prik.semantics.native_array_handles import native_array_data_type, native_array_descriptor_kind
from prik.utilities.visitor import ClassVisitor

_WRAPPED_CALLABLE_TYPE_METADATA = "pyi_wrapped_callable_type"
_CONTRACT_MODULE = "prik.contracts"
_CONTRACT_ALIAS_PREFIX = "_prik_"
_FLAT_DIMENSION_PRINT_SENTINEL = "@prik.Flat"


class PyiPrinter(ClassVisitor):
    """Emit Python stub text from semantic IR models.

    The class follows the same reading order as ``FortranParser``: its public
    entrypoint comes first, semantic model visitors follow in model-flow order,
    and formatting helpers remain next to the visitor group that owns them.
    """

    # ------------------------------------------------------------------
    # Public entrypoints and state
    # ------------------------------------------------------------------

    def __init__(self, *, normalize_fortran_public_names: bool = False):
        """Configure whether source-generated Fortran contracts use Python public names."""
        self._normalize_fortran_public_names = normalize_fortran_public_names
        self._naming_policy = NamingPolicy()
        self._public_namespace: tuple[str, ...] = ()
        self._reserved_public_names: dict[tuple[tuple[str, ...], str, object], str] = {}
        self._semantic_class_names: set[str] = set()
        self._contract_imports: set[str] = set()
        self._contract_aliases: dict[str, str] = {}
        self._default_array_order: str | None = None

    def emit(self, node) -> str:
        """Emit the supported semantic model passed by the caller."""
        if not isinstance(node, SemanticModule):
            return self._visit(node)
        previous_default_order = self._default_array_order
        self._default_array_order = self._native_default_array_order(node.origin.source_language)
        try:
            if not self._normalize_fortran_public_names:
                return self._visit(node)
            previous_policy = self._naming_policy
            previous_namespace = self._public_namespace
            previous_reserved = self._reserved_public_names
            self._naming_policy = NamingPolicy()
            self._public_namespace = ()
            self._reserved_public_names = {}
            try:
                return self._visit(node)
            finally:
                self._naming_policy = previous_policy
                self._public_namespace = previous_namespace
                self._reserved_public_names = previous_reserved
        finally:
            self._default_array_order = previous_default_order

    @staticmethod
    def _visit_not_supported(node):
        """Reject semantic models that have no `.pyi` visitor."""
        raise TypeError(f"Unsupported semantic model for .pyi emission: {type(node)!r}")

    # ------------------------------------------------------------------
    # Model visitors
    # ------------------------------------------------------------------

    def _visit_SemanticConstraint(self, constraint: SemanticConstraint) -> str:
        """Emit constraint syntax."""
        if constraint.name == "Constant":
            raise ValueError("Constant constraints are emitted through Final[...] data declarations")
        if constraint.name == "Shape":
            raise ValueError("Shape constraints are not canonical; put dimensions inside T[...]")
        name = self._contract(constraint.name)
        if not constraint.arguments:
            return name
        args = ", ".join(map(repr, constraint.arguments))
        return f"{name}({args})"

    def _visit_SemanticType(self, semantic_type: SemanticType) -> str:
        """Emit semantic type syntax."""
        if semantic_type.name == "Unknown" or semantic_type.dtype == "Unknown":
            raise ValueError("Cannot emit .pyi with unresolved semantic type 'Unknown'")
        array_descriptor = native_array_descriptor_kind(semantic_type)
        if PROTOTYPE_REF_METADATA in semantic_type.metadata:
            text = semantic_type.name
        elif array_descriptor is not None:
            wrapper = "Allocatable" if array_descriptor == "allocatable" else "Pointer"
            text = f"{self._contract(wrapper)}[{self._visit(native_array_data_type(semantic_type))}]"
        elif self._is_scalar_allocatable_descriptor(semantic_type):
            text = f"{self._contract('Allocatable')}[{self._scalar_descriptor_inner_text(semantic_type)}]"
        elif self._is_scalar_pointer_descriptor(semantic_type):
            text = f"{self._contract('Pointer')}[{self._scalar_descriptor_inner_text(semantic_type)}]"
        elif semantic_type.storage is not None:
            text = self._emit_storage_type(semantic_type)
        else:
            text = self._semantic_base_type(semantic_type)
        annotations = [
            *self._semantic_annotation_metadata(semantic_type),
        ]
        if array_descriptor is None:
            annotations.extend(self._visit(constraint) for constraint in semantic_type.constraints)
        if annotations:
            return self._annotated_type_text(text, annotations)
        return text

    def _visit_SemanticArgument(self, arg: SemanticArgument) -> str:
        """Emit argument syntax."""
        name = self._parameter_target(arg.name)
        return self._emit_typed_name(
            name,
            arg,
            original_name=arg.name if name != arg.name else None,
        )

    def _visit_SemanticVariable(self, arg: SemanticVariable) -> str:
        """Emit data member syntax."""
        return self._emit_data_member(arg)

    def _visit_SemanticFunction(self, func: SemanticFunction) -> str:
        """Emit function syntax."""
        return self._emit_function(func)

    def _visit_SemanticPrototype(self, prototype: SemanticPrototype) -> str:
        """Emit one semantic-only named callback prototype."""
        return_type = prototype.return_type or SemanticType("None", dtype="None")
        arguments = []
        for argument in prototype.arguments:
            text = f"{self._parameter_target(argument.name)}: {self._emit_prototype_argument(argument)}"
            if argument.optional:
                text += " = ..."
            arguments.append(text)
        return self._emit_callable(
            name=prototype.name,
            arguments=arguments,
            return_type=self._visit(return_type),
            decorator=f"@{self._contract('prototype')}\n",
            def_indent="",
            parameter_indent="    ",
        )

    def _emit_function(self, func: SemanticFunction, *, name_owner: object | None = None) -> str:
        """Emit function syntax with an optional shared overload-set public name."""
        return_type = self._projected_return_annotation(func)
        name = self._callable_name(func, owner=name_owner)
        decorator = self._decorators(func, emitted_name=name)
        return self._emit_callable(
            name=name,
            arguments=[self._emit_call_argument(func, arg) for arg in self._call_arguments(func)],
            return_type=return_type,
            decorator=decorator,
            def_indent="",
            parameter_indent="    ",
        )

    def _visit_SemanticMethod(self, method: SemanticMethod) -> str:
        """Emit method syntax."""
        return self._emit_method(method)

    def _emit_method(self, method: SemanticMethod, *, name_owner: object | None = None) -> str:
        """Emit method syntax with an optional shared overload-set public name."""
        return_type = self._projected_return_annotation(method)
        name = self._callable_name(method, owner=name_owner)
        decorator = self._decorators(method, indent="    ", emitted_name=name)
        arguments = [self._emit_call_argument(method, arg) for arg in self._method_call_arguments(method)]
        if not method.is_static:
            arguments.insert(0, "self")
        return self._emit_callable(
            name=name,
            arguments=arguments,
            return_type=return_type,
            decorator=decorator,
            def_indent="    ",
            parameter_indent="        ",
        ).rstrip()

    def _visit_ProcedureOverloadSet(self, overload_set: ProcedureOverloadSet, *, in_class: bool = False) -> str:
        """Emit overload set syntax."""
        definitions = []
        for procedure in overload_set.procedures:
            candidate = deepcopy(procedure)
            target = str(candidate.metadata.get(OVERLOAD_TARGET_METADATA) or candidate.native_name or candidate.name)
            if in_class:
                candidate = self._overload_method(overload_set, candidate)
                definition = self._emit_method(
                    candidate,
                    name_owner=("overload", overload_set.name, candidate.name),
                )
                indent = "    "
            else:
                candidate.name = overload_set.name
                definition = self._emit_function(
                    candidate,
                    name_owner=("overload", overload_set.name),
                )
                indent = ""
            generic = self._overload_generic_argument(candidate, overload_set.name) if in_class else ""
            bind_target = candidate.metadata.get(BIND_TARGET_METADATA)
            bind = f"{indent}@{self._contract('bind')}({json.dumps(str(bind_target))})\n" if bind_target else ""
            definitions.append(f'{bind}{indent}@{self._contract("overload")}("{target}"{generic})\n{definition}')
        return "\n\n".join(definitions)

    def _visit_SemanticClass(self, cls: SemanticClass) -> str:
        """Emit class syntax."""
        bases = f"({', '.join(self._class_base_text(base) for base in cls.base_classes)})" if cls.base_classes else ""
        previous_namespace = self._public_namespace
        self._public_namespace = (*self._public_namespace, cls.name)
        try:
            body = self._class_body(cls)
        finally:
            self._public_namespace = previous_namespace
        decorators = []
        if self._is_private(cls):
            decorators.append(f"@{self._contract('private')}")
        native_type = self._native_type_decorator(cls)
        if native_type:
            decorators.append(native_type)
        decorator_text = "\n".join(decorators)
        if decorator_text:
            decorator_text += "\n"
        return f"""
{decorator_text}class {cls.name}{bases}:
{body}
""".strip()

    def _class_base_text(self, base: str) -> str:
        """Return an imported contract base name or a user base name."""
        return self._contract_type(base)

    def _native_type_decorator(self, cls: SemanticClass) -> str:
        """Emit native derived-type metadata when the class needs it."""
        if cls.origin.source_language != "fortran" or cls.origin.source_kind != "derived_type":
            return ""
        attributes = tuple(str(item) for item in cls.metadata.get("fortran_type_attributes", ()))
        finalizers = tuple(str(item) for item in cls.metadata.get("fortran_final_procedures", ()))
        parts = []
        if attributes:
            parts.append(f"attributes={attributes!r}")
        if finalizers:
            parts.append(f"finalizers={finalizers!r}")
        return f"@{self._contract('native_type')}({', '.join(parts)})" if parts else ""

    def _visit_SemanticModule(self, module: SemanticModule) -> str:
        """Emit module syntax."""
        previous_class_names = self._semantic_class_names
        previous_contract_imports = self._contract_imports
        previous_contract_aliases = self._contract_aliases
        self._semantic_class_names = {
            str(cls.name)
            for cls in module.classes
            if cls.origin.source_language == "fortran" and cls.origin.source_kind == "derived_type"
        }
        self._contract_imports = set()
        self._contract_aliases = self._contract_aliases_for_module(module)
        body_sections: list[str] = []
        try:
            self._append_items(body_sections, self._contract_items(module.classes), self.emit)
            self._append_items(body_sections, module.prototypes, self._visit)
            self._append_items(body_sections, self._contract_items(module.variables), self._emit_module_variable)
            overload_targets = self._module_overload_target_names(module)
            self._append_items(
                body_sections,
                self._contract_items(module.functions, keep_names=overload_targets),
                self._visit,
            )
            self._append_items(body_sections, module.overload_sets, self._visit)
            sections: list[str] = []
            self._append_imports(sections, module)
            sections.extend(body_sections)
            return "\n".join(sections).rstrip()
        finally:
            self._semantic_class_names = previous_class_names
            self._contract_imports = previous_contract_imports
            self._contract_aliases = previous_contract_aliases

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _emit_storage_type(self, semantic_type: SemanticType) -> str:
        """Emit storage type syntax."""
        storage = semantic_type.storage
        base_type = self._semantic_base_type(semantic_type)
        if storage is None:
            return base_type
        if storage.kind == "value":
            return base_type
        if storage.kind in {"reference", "pointer", "address"}:
            if self._is_normal_storage_address(semantic_type):
                return base_type
            target = self._address_target_type(semantic_type)
            if storage.pointer_depth > 1:
                return f"{self._contract('Addr')}[{storage.pointer_depth}]({target})"
            return f"{self._contract('Addr')}({target})"
        if storage.kind == "array":
            return self._emit_array_type(semantic_type)
        return base_type

    def _semantic_base_type(self, semantic_type: SemanticType, *, include_deferred_length: bool = False) -> str:
        """Return the semantic dtype including fixed character length."""
        if semantic_type.name != "String":
            return self._contract_type(semantic_type.name)
        length = semantic_type.metadata.get("fortran_character_length")
        string = self._contract("String")
        if length is None or str(length) in {"", "*"}:
            return string
        if str(length) == ":":
            return f"{string}[:]" if include_deferred_length else string
        return f"{string}[{length}]"

    def _is_normal_storage_address(self, semantic_type: SemanticType) -> bool:
        """Return whether address storage is hidden behind the normal Python object."""
        storage = semantic_type.storage
        return bool(
            semantic_type.rank == 0
            and storage is not None
            and storage.kind in {"reference", "pointer", "address"}
            and storage.pointer_depth == 1
            and storage.metadata.get(ADDRESS_ROLE_METADATA) != ADDRESS_ROLE_RAW
            and (
                semantic_type.name == "String"
                or str(semantic_type.name) in self._semantic_class_names
                or semantic_type.metadata.get(_WRAPPED_CALLABLE_TYPE_METADATA)
            )
        )

    def _address_target_type(self, semantic_type: SemanticType) -> str:
        """Return the pointee type spelling for a raw address contract."""
        base_type = self._semantic_base_type(semantic_type, include_deferred_length=semantic_type.rank > 0)
        if semantic_type.rank <= 0:
            return base_type
        dimensions = semantic_type.shape
        if not dimensions:
            storage = semantic_type.storage
            array = storage.array if storage is not None else None
            dimensions = tuple(array.source_shape or array.shape) if array is not None else ()
        return f"{base_type}[{', '.join(str(dimension) for dimension in dimensions)}]"

    def _emit_array_type(self, semantic_type: SemanticType) -> str:
        """Emit array type syntax."""
        storage = semantic_type.storage
        array = storage.array if storage is not None else None
        if array is not None and array.category == SCALAR_STORAGE_CATEGORY:
            return f"{self._semantic_base_type(semantic_type, include_deferred_length=True)}[()]"
        dimensions = self._array_dimensions(semantic_type, array)
        base = f"{self._semantic_base_type(semantic_type, include_deferred_length=True)}[{', '.join(dimensions)}]"

        metadata = self._array_annotation_metadata(array)
        if metadata:
            return self._annotated_type_text(base, metadata)
        return base

    def _array_dimensions(
        self,
        semantic_type: SemanticType,
        array: SemanticArrayContract | None,
    ) -> list[str]:
        """Handle array dimensions for the current generation context."""
        if array is not None and array.category == "assumed_size" and array.source_shape:
            shape = list(array.shape if array.shape else semantic_type.shape)
            if len(shape) != len(array.source_shape):
                shape = list(array.source_shape)
            for axis, source_dimension in enumerate(array.source_shape):
                if PyiPrinter._assumed_size_array_dimension(source_dimension) == _FLAT_DIMENSION_PRINT_SENTINEL:
                    shape[axis] = _FLAT_DIMENSION_PRINT_SENTINEL
        else:
            shape = list(array.shape if array is not None and array.shape else semantic_type.shape)
        if not shape and semantic_type.rank > 0:
            shape = [":" for _ in range(semantic_type.rank)]
        dimensions = [PyiPrinter._printed_array_dimension(dim) for dim in shape]
        return [self._contract("Flat") if dim == _FLAT_DIMENSION_PRINT_SENTINEL else dim for dim in dimensions]

    @staticmethod
    def _assumed_size_array_dimension(dimension: object) -> str:
        """Map assumed-size Fortran dimensions to the `.pyi` Flat marker."""
        text = str(dimension).strip()
        if text == "*":
            return _FLAT_DIMENSION_PRINT_SENTINEL
        if ":" in text:
            _lower, upper = text.split(":", 1)
            if upper.strip() == "*":
                return _FLAT_DIMENSION_PRINT_SENTINEL
        return text

    @staticmethod
    def _canonical_array_dimension(dimension: object) -> str:
        """Handle canonical array dimension for the current generation context."""
        text = str(dimension)
        try:
            return ast.unparse(ast.parse(text, mode="eval").body)
        except SyntaxError:
            return text

    @staticmethod
    def _printed_array_dimension(dimension: object) -> str:
        """Return the public `.pyi` spelling for an array dimension."""
        text = PyiPrinter._canonical_array_dimension(dimension)
        if text == "::Strided":
            return "::"
        if text.endswith(":Strided"):
            return text[: -len("Strided")]
        return text

    def _array_annotation_metadata(self, array: SemanticArrayContract | None) -> list[str]:
        """Handle array annotation metadata for the current generation context."""
        if array is None:
            return []
        if array.rank is None or array.rank <= 1:
            return []
        metadata: list[str] = []
        if (
            array.order in {"ORDER_F", "ORDER_ANY"}
            and array.order != self._default_array_order
            and not (array.category == "assumed_size" and array.order == "ORDER_F")
        ):
            metadata.append(self._contract(array.order))
        if array.order == "ORDER_C" and array.order != self._default_array_order:
            metadata.append(self._contract("ORDER_C"))
        if array.copy_order == "ORDER_F":
            metadata.append(self._contract("COPY_F"))
        if array.allocatable:
            metadata.append(self._contract("Allocatable"))
        if array.pointer:
            metadata.append(self._contract("Pointer"))
        return metadata

    @staticmethod
    def _native_default_array_order(native_language: str | None) -> str | None:
        """Return the implicit multidimensional storage order for one native language."""
        if native_language == "fortran":
            return "ORDER_F"
        if native_language == "c":
            return "ORDER_C"
        return "ORDER_F"

    def _semantic_annotation_metadata(self, semantic_type: SemanticType) -> list[str]:
        """Handle semantic annotation metadata for the current generation context."""
        metadata: list[str] = []
        source_type = (semantic_type.origin.source_type or "").casefold().replace(" ", "")
        if source_type in {"type(*)", "class(*)"} or semantic_type.metadata.get("fortran_assumed_type"):
            metadata.append(self._contract("AssumedType"))
        if semantic_type.metadata.get("fortran_polymorphic"):
            metadata.append(self._contract("Polymorphic"))
        if (
            semantic_type.metadata.get("fortran_allocatable")
            and not self._is_scalar_allocatable_descriptor(semantic_type)
            and native_array_descriptor_kind(semantic_type) is None
        ):
            metadata.append(self._contract("FortranAllocatable"))
        if semantic_type.metadata.get("aliased"):
            metadata.append(self._contract("Aliased"))
        if semantic_type.metadata.get(PYTHON_VALUE_MUTABILITY_METADATA) == PYTHON_VALUE_IMMUTABLE:
            metadata.append(self._contract("Immutable"))
        if semantic_type.metadata.get(MAYBE_UNALLOCATED_METADATA):
            metadata.append(self._contract("MaybeUnallocated"))
        pointer_association = semantic_type.metadata.get("fortran_pointer_association")
        if pointer_association is not None and not self._is_scalar_pointer_descriptor(semantic_type):
            metadata.append(f"{self._contract('PointerAssociation')}({json.dumps(str(pointer_association))})")
        pointer_policy = self._pointer_policy_annotation(semantic_type)
        if pointer_policy is not None:
            metadata.append(pointer_policy)
        metadata.extend(self._ownership_policy_annotations(semantic_type))
        return metadata

    def _pointer_policy_annotation(self, semantic_type: SemanticType) -> str | None:
        """Render one structured pointer policy annotation when present."""
        pointer_policy = semantic_type.metadata.get(POINTER_POLICY_METADATA)
        if not isinstance(pointer_policy, dict):
            return None
        arguments = []
        for name in POINTER_POLICY_FIELDS:
            value = pointer_policy.get(name)
            if value is not None:
                rendered = repr(value) if isinstance(value, bool) else json.dumps(str(value))
                arguments.append(f"{name}={rendered}")
        return f"{self._contract('PointerPolicy')}({', '.join(arguments)})"

    def _ownership_policy_annotations(self, semantic_type: SemanticType) -> tuple[str, ...]:
        """Render explicit owner, transfer, and destruction policy metadata."""
        ownership_policy = semantic_type.metadata.get(OWNERSHIP_POLICY_METADATA)
        if not isinstance(ownership_policy, dict):
            return ()
        fields = (
            ("owner", "Ownership"),
            ("transfer", "Transfer"),
            ("destruction", "Destruction"),
        )
        return tuple(
            f"{self._contract(contract)}({json.dumps(str(ownership_policy[key]))})"
            for key, contract in fields
            if ownership_policy.get(key) is not None
        )

    @staticmethod
    def _is_scalar_allocatable_descriptor(semantic_type: SemanticType) -> bool:
        """Return whether a rank-0 type is a native allocatable descriptor."""
        return bool(
            semantic_type.rank == 0
            and semantic_type.metadata.get("fortran_allocatable")
            and not PyiPrinter._is_allocatable_array(semantic_type)
        )

    @staticmethod
    def _is_scalar_pointer_descriptor(semantic_type: SemanticType) -> bool:
        """Return whether a rank-0 type is a native pointer descriptor."""
        storage = semantic_type.storage
        return bool(
            semantic_type.rank == 0
            and semantic_type.metadata.get("fortran_pointer")
            and not (storage is not None and storage.array is not None)
        )

    def _scalar_descriptor_inner_text(self, semantic_type: SemanticType) -> str:
        """Emit the scalar descriptor element type without descriptor metadata."""
        return self._visit(self._visible_scalar_descriptor_type(semantic_type))

    @staticmethod
    def _scalar_descriptor_kind(semantic_type: SemanticType | None) -> str | None:
        """Return the native scalar descriptor kind carried by a semantic type."""
        if semantic_type is None or semantic_type.rank != 0:
            return None
        if semantic_type.metadata.get("fortran_allocatable"):
            return "allocatable"
        if semantic_type.metadata.get("fortran_pointer"):
            return "pointer"
        return None

    @staticmethod
    def _visible_scalar_descriptor_type(semantic_type: SemanticType) -> SemanticType:
        """Remove native scalar descriptor topology from a Python value annotation."""
        visible = deepcopy(semantic_type)
        for key in ("fortran_allocatable", "fortran_pointer", "fortran_pointer_association"):
            visible.metadata.pop(key, None)
        if visible.storage is not None and visible.storage.kind in {"reference", "pointer", "address"}:
            visible.storage = None
        visible.ownership.mutable = False
        return visible

    def _emit_prototype_argument(self, argument: SemanticArgument) -> str:
        """Emit one prototype dummy using the public callback transport rules."""
        if self._is_prototype_descriptor_type(argument.semantic_type):
            return self._prototype_descriptor_type_text(argument.semantic_type)
        inner = self._prototype_argument_inner_type(argument.semantic_type)
        if bool(getattr(argument.origin, "metadata", {}).get("value")):
            if self._is_prototype_primitive_value(argument.semantic_type):
                return inner
            return f"{self._contract('Value')}({inner})"
        if self._is_prototype_primitive_reference(argument.semantic_type):
            return f"{self._contract('Addr')}({inner})"
        return inner

    def _prototype_argument_inner_type(self, semantic_type: SemanticType) -> str:
        """Return the native prototype dummy type without transport wrappers."""
        storage = semantic_type.storage
        if (
            semantic_type.name == "String"
            and storage is not None
            and storage.array is not None
            and storage.array.category == SCALAR_STORAGE_CATEGORY
        ):
            return self._semantic_base_type(semantic_type, include_deferred_length=True)
        if storage is not None and storage.kind in {"reference", "address", "pointer"}:
            return self._address_target_type(semantic_type)
        return self._visit(semantic_type)

    def _prototype_descriptor_type_text(self, semantic_type: SemanticType) -> str:
        """Render descriptor metadata without a second reference wrapper."""
        if semantic_type.metadata.get("fortran_allocatable") or semantic_type.metadata.get("fortran_pointer"):
            return self._visit(semantic_type)
        visible = deepcopy(semantic_type)
        if visible.storage is not None and visible.storage.kind in {"reference", "address", "pointer"}:
            visible.storage = None
        return self._visit(visible)

    @staticmethod
    def _is_prototype_primitive_value(semantic_type: SemanticType) -> bool:
        storage = semantic_type.storage
        return bool(
            semantic_type.rank == 0
            and semantic_type.name not in {"String", "Void"}
            and (semantic_type.dtype or semantic_type.name) in SEMANTIC_SCALAR_TYPE_NAMES
            and (storage is None or storage.kind == "value")
            and not PyiPrinter._is_prototype_descriptor_type(semantic_type)
        )

    @staticmethod
    def _is_prototype_primitive_reference(semantic_type: SemanticType) -> bool:
        storage = semantic_type.storage
        return bool(
            semantic_type.rank == 0
            and semantic_type.name not in {"String", "Void"}
            and (semantic_type.dtype or semantic_type.name) in SEMANTIC_SCALAR_TYPE_NAMES
            and storage is not None
            and storage.kind in {"reference", "address", "pointer"}
            and storage.pointer_depth == 1
            and not PyiPrinter._is_prototype_descriptor_type(semantic_type)
        )

    @staticmethod
    def _is_prototype_descriptor_type(semantic_type: SemanticType) -> bool:
        return any(
            semantic_type.metadata.get(name)
            for name in (
                "fortran_allocatable",
                "fortran_pointer",
                "fortran_polymorphic",
                "fortran_assumed_type",
            )
        )

    def _emit_data_member(self, variable: SemanticVariable) -> str:
        """Emit a variable in class-field context rather than argument context."""
        name = self._data_member_name(variable)
        return self._emit_typed_name(
            self._annotation_target(name),
            variable,
            original_name=variable.name if name != variable.name else None,
        )

    def _emit_module_variable(self, arg: SemanticVariable) -> str:
        """Emit module variable syntax."""
        name = self._module_variable_name(arg)
        return self._emit_typed_name(
            self._annotation_target(name),
            arg,
            original_name=arg.name if name != arg.name else None,
        )

    @staticmethod
    def _is_allocatable_array(semantic_type: SemanticType) -> bool:
        """Return whether is allocatable array."""
        storage = semantic_type.storage
        return bool(storage is not None and storage.array is not None and storage.array.allocatable)

    def _emit_typed_name(
        self,
        name: str,
        arg: SemanticVariable,
        *,
        original_name: str | None = None,
        nullable: bool = False,
        allow_optional_absent_handle: bool = False,
    ) -> str:
        """Emit typed name syntax."""
        semantic_type = self._without_constant_constraint(arg.semantic_type)
        type_text = self._visit(semantic_type)
        annotation_metadata = []
        if original_name is not None:
            annotation_metadata.append(f"{self._contract('SourceName')}({json.dumps(original_name)})")
        if annotation_metadata:
            type_text = self._annotated_type_text(type_text, annotation_metadata)
        if self._is_constant(arg.semantic_type):
            type_text = f"{self._contract('Final')}[{type_text}]"
        if getattr(arg, "visibility", "public") == "private":
            type_text = f"{self._contract('private')}[{type_text}]"
        optional_absent_handle = arg.semantic_type.metadata.get(OPTIONAL_ABSENT_HANDLE_METADATA) or (
            arg.optional and native_array_descriptor_kind(arg.semantic_type) is not None
        )
        if optional_absent_handle and not allow_optional_absent_handle:
            raise ValueError("Optional absent native array handles can only be emitted for callable arguments")
        if nullable or (allow_optional_absent_handle and optional_absent_handle):
            type_text = f"{type_text} | None"

        text = f"{name}: {type_text}"
        if arg.optional:
            text += " = ..."
        else:
            default_value = self._pyi_default_value(arg)
            if default_value is not None:
                text += f" = {default_value}"
        return text

    def _emit_call_argument(self, func: SemanticFunction, arg: SemanticArgument) -> str:
        """Emit a callable argument with compact output metadata when possible."""
        name = self._parameter_target(arg.name)
        emitted_arg = self._projected_address_argument(func, arg)
        descriptor_kind = self._scalar_descriptor_kind(emitted_arg.semantic_type)
        if descriptor_kind is not None:
            emitted_arg = deepcopy(emitted_arg)
            emitted_arg.semantic_type = self._visible_scalar_descriptor_type(emitted_arg.semantic_type)
        visible_type = self._visible_wrapped_callable_type(emitted_arg.semantic_type)
        if visible_type is not emitted_arg.semantic_type:
            emitted_arg = deepcopy(emitted_arg)
            emitted_arg.semantic_type = visible_type
        return self._emit_typed_name(
            name,
            emitted_arg,
            original_name=arg.name if name != arg.name else None,
            nullable=descriptor_kind is not None,
            allow_optional_absent_handle=True,
        )

    @classmethod
    def _projected_address_argument(
        cls,
        func: SemanticFunction,
        arg: SemanticArgument,
    ) -> SemanticArgument:
        """Return the Python-visible value form for projected scalar addresses."""
        if not cls._uses_address_projection(func, arg):
            return arg
        emitted_arg = deepcopy(arg)
        storage = arg.semantic_type.storage
        emitted_arg.semantic_type.storage = SemanticStorageContract(
            kind="value",
            read_only=bool(storage is not None and storage.read_only),
            mutable=not bool(storage is not None and storage.read_only),
        )
        emitted_arg.semantic_type.ownership.mutable = not bool(storage is not None and storage.read_only)
        return emitted_arg

    @classmethod
    def _uses_address_projection(cls, func: SemanticFunction, arg: SemanticArgument) -> bool:
        """Return whether `arg` is emitted as a value plus `Addr(Arg(...))`."""
        if not cls._is_scalar_address_projection(arg.semantic_type):
            return False
        return any(cls._mapping_projects_argument(mapping, arg) for mapping in func.projection)

    @staticmethod
    def _is_scalar_address_projection(semantic_type: SemanticType) -> bool:
        """Return whether semantic type is a Python-value scalar passed by native address."""
        storage = semantic_type.storage
        return bool(
            semantic_type.rank == 0
            and semantic_type.name != "String"
            and not semantic_type.metadata.get("fortran_allocatable")
            and not semantic_type.metadata.get("fortran_pointer")
            and semantic_type.dtype in SEMANTIC_SCALAR_TYPE_NAMES
            and storage is not None
            and (
                (storage.kind == "address" and storage.metadata.get(ADDRESS_ROLE_METADATA) == ADDRESS_ROLE_PROJECTION)
                or storage.kind == "reference"
            )
            and storage.pointer_depth == 1
        )

    @staticmethod
    def _mapping_projects_argument(mapping: ProjectionMapping, arg: SemanticArgument) -> bool:
        """Return whether a projection mapping consumes `arg` as a Python argument."""
        return bool(
            mapping.native_position is not None
            and mapping.python_position is not None
            and (mapping.python_name or mapping.native_name) == arg.name
        )

    def _annotated_type_text(self, type_text: str, metadata: list[str]) -> str:
        """Handle annotated type text for the current generation context."""
        suffix = ", ".join(metadata)
        annotated = self._contract("Annotated")
        if type_text.startswith(f"{annotated}[") and type_text.endswith("]"):
            return f"{type_text[:-1]}, {suffix}]"
        return f"{annotated}[{type_text}, {suffix}]"

    @staticmethod
    def _is_constant(semantic_type: SemanticType) -> bool:
        """Return whether is constant."""
        return any(constraint.name == "Constant" for constraint in semantic_type.constraints)

    @staticmethod
    def _is_enum_constant(arg: SemanticVariable) -> bool:
        """Return whether is enum constant."""
        return PyiPrinter._is_constant(arg.semantic_type) and bool(
            arg.semantic_type.metadata.get("semantic_enum") or arg.semantic_type.metadata.get("c_enum")
        )

    @staticmethod
    def _enum_default_value(arg: SemanticVariable) -> str | None:
        """Handle enum default value for the current generation context."""
        pyi_value = arg.metadata.get("pyi_default_value")
        if isinstance(pyi_value, str):
            return pyi_value
        if arg.origin.source_language == "c":
            return None
        return arg.default_value

    @staticmethod
    def _pyi_default_value(arg: SemanticVariable) -> str | None:
        """Handle pyi default value for the current generation context."""
        if (self_value := arg.metadata.get("pyi_default_value")) and isinstance(self_value, str):
            return self_value
        if PyiPrinter._is_enum_constant(arg):
            return PyiPrinter._enum_default_value(arg)
        if (initializer := arg.metadata.get("fortran_initializer")) and (
            literal := PyiPrinter._fortran_literal_text(initializer)
        ):
            return literal
        return PyiPrinter._python_literal_text(arg.default_value)

    @staticmethod
    def _python_literal_text(value: str | None) -> str | None:
        """Handle python literal text for the current generation context."""
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        text = re.sub(r"\.true\.", "True", text, flags=re.IGNORECASE)
        text = re.sub(r"\.false\.", "False", text, flags=re.IGNORECASE)
        text = re.sub(r"(?<=\d)[dD](?=[+-]?\d)", "e", text)
        try:
            return ast.unparse(ast.parse(text, mode="eval").body)
        except SyntaxError:
            return None

    @staticmethod
    def _fortran_literal_text(value: str | None) -> str | None:
        """Return a Python literal spelling for literal Fortran initializer text."""
        text = PyiPrinter._python_literal_text(value)
        if text is None:
            return None
        try:
            ast.literal_eval(ast.parse(text, mode="eval").body)
        except (ValueError, SyntaxError):
            return None
        return text

    @staticmethod
    def _without_constant_constraint(semantic_type: SemanticType) -> SemanticType:
        """Handle without constant constraint for the current generation context."""
        if not PyiPrinter._is_constant(semantic_type):
            return semantic_type
        return SemanticType(
            name=semantic_type.name,
            rank=semantic_type.rank,
            dtype=semantic_type.dtype,
            shape=list(semantic_type.shape),
            constraints=[constraint for constraint in semantic_type.constraints if constraint.name != "Constant"],
            coercions=list(semantic_type.coercions),
            ownership=semantic_type.ownership,
            metadata=dict(semantic_type.metadata),
            storage=semantic_type.storage,
            origin=semantic_type.origin,
        )

    @staticmethod
    def _overload_generic_argument(procedure: SemanticFunction, public_name: str) -> str:
        """Handle overload generic argument for the current generation context."""
        generic_name = str(procedure.metadata.get(FORTRAN_GENERIC_NAME_METADATA, ""))
        if procedure.metadata.get(OVERLOAD_KIND_METADATA) == "generic":
            return "" if generic_name == public_name else f', generic="{generic_name}"'
        if procedure.metadata.get(OVERLOAD_KIND_METADATA) not in {"operator", "comparison"}:
            return ""
        if re.sub(r"\s+", "", generic_name).casefold() not in {
            "operator(.eqv.)",
            "operator(.neqv.)",
        }:
            return ""
        return f', generic="{generic_name}"'

    @staticmethod
    def _overload_method(
        overload_set: ProcedureOverloadSet,
        procedure: SemanticFunction,
    ) -> SemanticMethod:
        """Handle overload method for the current generation context."""
        bound_position = procedure.metadata.get(PYTHON_BOUND_POSITION_METADATA)
        return SemanticMethod(
            name=str(procedure.metadata.get(PYTHON_METHOD_NAME_METADATA, overload_set.name)),
            native_name=procedure.native_name,
            arguments=procedure.arguments,
            return_type=procedure.return_type,
            locals=procedure.locals,
            contracts=procedure.contracts,
            projection=procedure.projection,
            metadata=procedure.metadata,
            visibility=procedure.visibility,
            origin=procedure.origin,
            is_static=bool(procedure.metadata.get(PYTHON_STATIC_METADATA)),
            passed_object_name=(procedure.arguments[bound_position].name if isinstance(bound_position, int) else None),
            passed_object_position=bound_position if isinstance(bound_position, int) else None,
        )

    def _emit_callable(
        self,
        *,
        name: str,
        arguments: list[str],
        return_type: str,
        decorator: str,
        def_indent: str,
        parameter_indent: str,
    ) -> str:
        """Emit callable syntax."""
        if not arguments:
            return f"{decorator}{def_indent}def {name}() -> {return_type}: ..."
        if arguments == ["self"]:
            return f"{decorator}{def_indent}def {name}(self) -> {return_type}: ..."

        args = (",\n" + parameter_indent).join(arguments)
        return f"{decorator}{def_indent}def {name}(\n{parameter_indent}{args}\n{def_indent}) -> {return_type}: ..."

    def _class_body(self, cls: SemanticClass) -> str:
        """Handle class body for the current generation context."""
        body_parts = []

        nested_classes = "\n\n".join(
            self._indent_block(self._visit(nested), "    ") for nested in self._contract_items(cls.classes)
        )
        if nested_classes:
            body_parts.append(nested_classes)

        constructor = self._class_constructor(cls)
        if constructor:
            body_parts.append(constructor)

        fields = "\n".join(f"    {self._emit_data_member(field)}" for field in self._contract_items(cls.fields))
        if fields:
            body_parts.append(fields)

        overload_targets = self._overload_target_names(cls.overload_sets)
        methods = "\n\n".join(
            self._visit(method) for method in self._contract_items(cls.methods, keep_names=overload_targets)
        )
        if methods:
            body_parts.append(methods)

        overload_sets = "\n\n".join(self._visit(overload_set, in_class=True) for overload_set in cls.overload_sets)
        if overload_sets:
            body_parts.append(overload_sets)

        if not body_parts:
            return "    pass"
        return "\n\n".join(body_parts)

    def _class_constructor(self, cls: SemanticClass) -> str:
        """Handle class constructor for the current generation context."""
        if cls.origin.source_language != "fortran":
            return ""
        arguments = [
            self._constructor_argument(field) for field in cls.fields if self._constructor_accepts_field(field)
        ]
        if not arguments and cls.fields:
            return "    def __init__(self) -> None: ..."
        if not arguments:
            return ""
        return self._emit_callable(
            name="__init__",
            arguments=["self", "*", *arguments],
            return_type="None",
            decorator="",
            def_indent="    ",
            parameter_indent="        ",
        ).rstrip()

    def _constructor_argument(self, field: SemanticVariable) -> str:
        """Handle constructor argument for the current generation context."""
        name = self._data_member_name(field)
        semantic_type = self._without_constant_constraint(field.semantic_type)
        type_text = self._visit(semantic_type)
        default_value = (
            self._fortran_literal_text(field.metadata.get("fortran_initializer"))
            or self._python_literal_text(field.default_value)
            or "..."
        )
        if name != field.name:
            type_text = self._annotated_type_text(
                type_text,
                [f"{self._contract('SourceName')}({json.dumps(field.name)})"],
            )
        return f"{name}: {type_text} = {default_value}"

    @staticmethod
    def _constructor_accepts_field(field: SemanticVariable) -> bool:
        """Handle constructor accepts field for the current generation context."""
        semantic_type = field.semantic_type
        return (
            field.visibility == "public"
            and semantic_type.rank == 0
            and semantic_type.name != "String"
            and semantic_type.name in SEMANTIC_DTYPE_TO_NUMPY_DTYPE
        )

    @staticmethod
    def _indent_block(text: str, indent: str) -> str:
        """Handle indent block for the current generation context."""
        return "\n".join(f"{indent}{line}" if line else line for line in text.splitlines())

    def _contract(self, name: str) -> str:
        """Return the local imported spelling for one prik contract symbol."""
        if name not in CONTRACT_SYMBOLS:
            return name
        self._contract_imports.add(name)
        return self._contract_aliases.get(name, name)

    def _contract_type(self, name: str) -> str:
        """Return the local spelling for a contract type name."""
        if name in CONTRACT_TYPE_NAMES:
            return self._contract(name)
        return name

    @classmethod
    def _contract_aliases_for_module(cls, module: SemanticModule) -> dict[str, str]:
        """Choose collision-free local names for contract imports used by a module."""
        reserved = cls._module_reserved_names(module)
        aliases: dict[str, str] = {}
        for name in sorted(CONTRACT_SYMBOLS & reserved):
            alias = cls._fresh_contract_alias(name, reserved)
            aliases[name] = alias
            reserved.add(alias)
        return aliases

    @staticmethod
    def _fresh_contract_alias(name: str, reserved: set[str]) -> str:
        """Return an arbitrary generated alias that does not collide with user names."""
        base = f"{_CONTRACT_ALIAS_PREFIX}{name}"
        if base not in reserved:
            return base
        index = 2
        while f"{base}_{index}" in reserved:
            index += 1
        return f"{base}_{index}"

    @classmethod
    def _module_reserved_names(cls, module: SemanticModule) -> set[str]:
        """Return user/import names that cannot be reused by contract imports."""
        names: set[str] = set()
        names.update(cls._required_procedure_namespace_import_names(module))
        for imp in module.imports:
            names.update(cls._import_local_names(imp))
        for item in [*module.classes, *module.prototypes, *module.variables, *module.functions, *module.overload_sets]:
            cls._collect_reserved_item_names(item, names)
        for semantic_type in _iter_module_semantic_types(module):
            names.update(cls._contract_like_dimension_names(semantic_type))
        return names

    @classmethod
    def _collect_reserved_item_names(cls, item: object, names: set[str]) -> None:
        """Collect emitted declaration names that can shadow imports."""
        for attr in ("name", "native_name"):
            value = getattr(item, attr, None)
            if isinstance(value, str) and value:
                names.add(value)
        if isinstance(item, ProcedureOverloadSet):
            for procedure in item.procedures:
                cls._collect_reserved_item_names(procedure, names)
            return
        for attr in ("arguments", "fields", "methods", "classes", "variables", "functions", "overload_sets"):
            values = getattr(item, attr, None)
            if isinstance(values, Iterable) and not isinstance(values, str | bytes):
                for value in values:
                    cls._collect_reserved_item_names(value, names)

    @staticmethod
    def _contract_like_dimension_names(semantic_type: SemanticType) -> set[str]:
        """Return exact dimension tokens that would collide with a contract import."""
        storage = semantic_type.storage
        array = storage.array if storage is not None else None
        dimensions = list(semantic_type.shape)
        if not dimensions and array is not None:
            dimensions = list(array.shape)
        return {str(dimension) for dimension in dimensions if str(dimension) in CONTRACT_SYMBOLS}

    @staticmethod
    def _import_local_names(imp: str | SemanticImport) -> set[str]:
        """Return local names introduced by an import."""
        if isinstance(imp, SemanticImport):
            if not imp.items:
                return {imp.module.split(".", 1)[0]}
            return {item.target or item.source for item in imp.items}
        names = set()
        for item in str(imp).split(","):
            module_name, _, alias = item.strip().partition(" as ")
            names.add(alias or module_name.split(".", 1)[0])
        return names

    def _append_imports(self, sections: list[str], module: SemanticModule) -> None:
        """Append imports."""
        contract_import = self._contract_import()
        if contract_import:
            sections.append(contract_import)
        imports = self._effective_imports(module)
        for imp in imports:
            sections.append(self._emit_import(imp))
        if contract_import or imports:
            sections.append("")

    def _contract_import(self) -> str:
        """Emit the direct import for contract symbols used by the generated stub."""
        if not self._contract_imports:
            return ""
        items = []
        for name in sorted(self._contract_imports):
            alias = self._contract_aliases.get(name)
            items.append(f"{name} as {alias}" if alias else name)
        return f"from {_CONTRACT_MODULE} import {', '.join(items)}"

    @classmethod
    def _effective_imports(cls, module: SemanticModule) -> list[str | SemanticImport]:
        """Handle effective imports for the current generation context."""
        imports = [
            imp
            for imp in module.imports
            if not PyiPrinter._is_source_kind_import(imp) and not PyiPrinter._is_contract_import(imp)
        ]
        procedure_namespaces = cls._required_procedure_namespace_import_names(module)
        cls._validate_procedure_namespace_imports(module, procedure_namespaces, imports)
        satisfied_namespaces = cls._satisfied_procedure_namespace_import_names(imports, procedure_namespaces)
        imports.extend(cls._synthetic_flat_external_type_imports(module, imports, procedure_namespaces))
        imports.extend(cls._missing_procedure_namespace_imports(procedure_namespaces, satisfied_namespaces))
        return imports

    @classmethod
    def _synthetic_flat_external_type_imports(
        cls,
        module: SemanticModule,
        imports: list[str | SemanticImport],
        procedure_namespaces: set[str],
    ) -> list[SemanticImport]:
        """Return synthetic flattened imports needed by external type refs."""
        imported_items = {
            (imp.module, item.source, item.target or item.source)
            for imp in imports
            if isinstance(imp, SemanticImport)
            for item in imp.items
        }
        synthetic: dict[str, list[SemanticImportItem]] = {}
        for semantic_type in _iter_module_semantic_types(module):
            ref = cls._flat_external_type_import_ref(semantic_type)
            if ref is None:
                continue
            origin_module, source_name, local_name = ref
            key = (origin_module, source_name, local_name)
            if key in imported_items:
                continue
            if local_name in procedure_namespaces:
                raise ValueError(
                    f"Procedure-local Fortran import namespace collides with generated .pyi name: {local_name!r}"
                )
            synthetic.setdefault(origin_module, []).append(
                SemanticImportItem(
                    source=source_name,
                    target=local_name if local_name != source_name else None,
                )
            )
            imported_items.add(key)
        return [
            SemanticImport(
                module=module_name,
                items=sorted(items, key=lambda item: (item.source, item.target or "")),
            )
            for module_name, items in sorted(synthetic.items())
        ]

    @classmethod
    def _flat_external_type_import_ref(cls, semantic_type: SemanticType) -> tuple[str, str, str] | None:
        """Return flattened external type import fields, or None for qualified refs."""
        ref = semantic_type.metadata.get(EXTERNAL_TYPE_REF_METADATA)
        if not isinstance(ref, dict) or cls._is_procedure_local_external_ref(ref):
            return None
        origin_module = ref.get("origin_module")
        source_name = ref.get("name")
        local_name = ref.get("local_name") or source_name
        if not all(isinstance(value, str) and value for value in (origin_module, source_name, local_name)):
            return None
        if "." in local_name:
            return None
        return origin_module, source_name, local_name

    @staticmethod
    def _missing_procedure_namespace_imports(
        procedure_namespaces: set[str],
        satisfied_namespaces: set[str],
    ) -> list[SemanticImport]:
        """Return missing namespace imports for procedure-local external refs."""
        missing_namespaces = sorted(procedure_namespaces - satisfied_namespaces)
        if not missing_namespaces:
            return []
        return [
            SemanticImport(
                module=".",
                items=[SemanticImportItem(source=name) for name in missing_namespaces],
            )
        ]

    @staticmethod
    def _is_procedure_local_external_ref(ref: dict[object, object]) -> bool:
        """Return whether an external ref came from a procedure-local Fortran use."""
        return ref.get("import_scope") == "procedure"

    @classmethod
    def _required_procedure_namespace_import_names(cls, module: SemanticModule) -> set[str]:
        """Return module namespaces required by procedure-local imported types."""
        names: set[str] = set()
        for semantic_type in _iter_module_semantic_types(module):
            ref = semantic_type.metadata.get(EXTERNAL_TYPE_REF_METADATA)
            if not isinstance(ref, dict) or not cls._is_procedure_local_external_ref(ref):
                continue
            origin_module = ref.get("origin_module")
            source_name = ref.get("name")
            local_name = ref.get("local_name")
            if not all(isinstance(value, str) and value for value in (origin_module, source_name, local_name)):
                continue
            names.add(origin_module)
        return names

    @classmethod
    def _validate_procedure_namespace_imports(
        cls,
        module: SemanticModule,
        procedure_namespaces: set[str],
        imports: list[str | SemanticImport],
    ) -> None:
        """Reject namespace imports that would collide with emitted public names."""
        if not procedure_namespaces:
            return
        declaration_collisions = procedure_namespaces & cls._top_level_declaration_names(module)
        import_collisions = {
            name
            for imp in imports
            for name in cls._import_local_names(imp) & procedure_namespaces
            if not cls._import_satisfies_procedure_namespace(imp, name)
        }
        collisions = sorted(declaration_collisions | import_collisions)
        if collisions:
            joined = ", ".join(repr(name) for name in collisions)
            raise ValueError(f"Procedure-local Fortran import namespace collides with generated .pyi name: {joined}")

    @staticmethod
    def _top_level_declaration_names(module: SemanticModule) -> set[str]:
        """Return names emitted in a module-level stub namespace."""
        return {
            str(item.name)
            for item in [
                *module.classes,
                *module.prototypes,
                *module.variables,
                *module.functions,
                *module.overload_sets,
            ]
            if getattr(item, "name", None)
        }

    @classmethod
    def _satisfied_procedure_namespace_import_names(
        cls,
        imports: list[str | SemanticImport],
        procedure_namespaces: set[str],
    ) -> set[str]:
        """Return procedure namespace imports already provided by module imports."""
        return {
            name
            for name in procedure_namespaces
            if any(cls._import_satisfies_procedure_namespace(imp, name) for imp in imports)
        }

    @staticmethod
    def _import_satisfies_procedure_namespace(imp: str | SemanticImport, name: str) -> bool:
        """Return whether an import binds exactly the required module namespace."""
        if isinstance(imp, SemanticImport):
            if not imp.items:
                return imp.module == name
            return imp.module == "." and any(item.source == name and item.target is None for item in imp.items)
        for item in str(imp).split(","):
            module_name, _, alias = item.strip().partition(" as ")
            if alias:
                continue
            if module_name == name:
                return True
        return False

    @staticmethod
    def _is_source_kind_import(imp: str | SemanticImport) -> bool:
        """Return whether an import only names a source-language kind module."""
        module = imp.module if isinstance(imp, SemanticImport) else str(imp).split()[0]
        return module.casefold().lstrip(".") in {"iso_c_binding", "iso_fortran_env"}

    @staticmethod
    def _is_contract_import(imp: str | SemanticImport) -> bool:
        """Return whether an import names the generated contract namespace."""
        module = imp.module if isinstance(imp, SemanticImport) else str(imp).split()[0]
        return module == _CONTRACT_MODULE

    @staticmethod
    def _has_overload_sets(module: SemanticModule) -> bool:
        """Return whether has overload sets."""

        def class_has_overloads(cls: SemanticClass) -> bool:
            return bool(cls.overload_sets) or any(class_has_overloads(nested) for nested in cls.classes)

        return bool(module.overload_sets) or any(
            class_has_overloads(cls) for cls in module.classes if isinstance(cls, SemanticClass)
        )

    @staticmethod
    def _emit_import(imp: str | SemanticImport) -> str:
        """Emit import syntax."""
        if isinstance(imp, str):
            return f"import {imp}"
        if not imp.items:
            return f"import {imp.module}"
        items = ", ".join(PyiPrinter._emit_import_item(item) for item in imp.items)
        return f"from {imp.module} import {items}"

    @staticmethod
    def _emit_import_item(item: SemanticImportItem) -> str:
        """Emit import item syntax."""
        if item.target and item.target != item.source:
            return f"{item.source} as {item.target}"
        return item.source

    def _append_items(self, sections: list[str], items: list, emit_item) -> None:
        """Append items."""
        for item in items:
            sections.append(emit_item(item))
            sections.append("")

    @classmethod
    def _contract_items(cls, items: Iterable, *, keep_names: set[str] | None = None) -> list:
        """Handle contract items for the current generation context."""
        keep_names = set() if keep_names is None else keep_names
        return [item for item in items if cls._should_emit_contract_item(item, keep_names=keep_names)]

    @staticmethod
    def _should_emit_contract_item(item, *, keep_names: set[str]) -> bool:
        """Handle should emit contract item for the current generation context."""
        if PyiPrinter._item_names(item) & keep_names:
            return True
        if not PyiPrinter._is_source_private(item):
            return True
        return PyiPrinter._is_user_private(item)

    @staticmethod
    def _item_names(item) -> set[str]:
        """Handle item names for the current generation context."""
        names = {value for value in (getattr(item, "name", None), getattr(item, "native_name", None)) if value}
        return {str(name) for name in names}

    @staticmethod
    def _overload_target_names(overload_sets: Iterable[ProcedureOverloadSet]) -> set[str]:
        """Handle overload target names for the current generation context."""
        targets: set[str] = set()
        for overload_set in overload_sets:
            for procedure in overload_set.procedures:
                target = procedure.metadata.get(OVERLOAD_TARGET_METADATA) or procedure.native_name or procedure.name
                if target:
                    targets.add(str(target))
                targets.update(PyiPrinter._item_names(procedure))
        return targets

    @classmethod
    def _module_overload_target_names(cls, module: SemanticModule) -> set[str]:
        """Handle module overload target names for the current generation context."""
        targets = cls._overload_target_names(module.overload_sets)
        for semantic_class in module.classes:
            targets.update(cls._class_overload_target_names(semantic_class))
        return targets

    @classmethod
    def _class_overload_target_names(cls, semantic_class: SemanticClass) -> set[str]:
        """Handle class overload target names for the current generation context."""
        targets = cls._overload_target_names(semantic_class.overload_sets)
        for nested in semantic_class.classes:
            targets.update(cls._class_overload_target_names(nested))
        return targets

    @staticmethod
    def _is_source_private(node) -> bool:
        """Return whether is source private."""
        if isinstance(node, SemanticMethod):
            attributes = {str(attr).casefold() for attr in getattr(node, "binding_attributes", ())}
            return "private" in attributes
        origin = getattr(node, "origin", None)
        return (
            getattr(node, "visibility", "public") == "private" and getattr(origin, "source_language", None) == "fortran"
        )

    @staticmethod
    def _is_user_private(node) -> bool:
        """Return whether is user private."""
        origin = getattr(node, "origin", None)
        metadata = getattr(origin, "metadata", {})
        return isinstance(metadata, dict) and bool(metadata.get(USER_PRIVATE_METADATA))

    def _projected_return_annotation(self, func: SemanticFunction) -> str:
        """Handle projected return annotation for the current generation context."""
        parts = []
        if func.return_type:
            if self._scalar_descriptor_kind(func.return_type) is not None:
                visible_result = self._visible_scalar_descriptor_type(func.return_type)
                parts.append(f"{self._visit(visible_result)} | None")
            else:
                parts.append(self._visit(self._visible_wrapped_callable_type(func.return_type)))
        parts.extend(
            self._projected_argument_return(func, arg, visible=visible)
            for _, arg, visible in sorted(
                self._projected_return_arguments(func),
                key=lambda item: item[0],
            )
        )
        if not parts:
            return "None"
        if len(parts) == 1:
            return parts[0]
        return f"tuple[{', '.join(parts)}]"

    @staticmethod
    def _projected_return_arguments(func: SemanticFunction) -> list[tuple[int, SemanticArgument, bool]]:
        """Handle projected return arguments for the current generation context."""
        by_name = {arg.name: arg for arg in func.arguments}
        returned = []
        for mapping in func.projection:
            if mapping.result_position is None:
                continue
            arg_name = mapping.python_name or mapping.native_name
            arg = by_name.get(arg_name)
            if arg is not None:
                returned.append(
                    (
                        mapping.result_position,
                        arg,
                        PyiPrinter._is_visible_projected_return(func, mapping),
                    )
                )
        return returned

    @staticmethod
    def _is_visible_projected_return(func: SemanticFunction, mapping: ProjectionMapping) -> bool:
        """Return whether a projected return should keep a named argument result."""
        if (
            isinstance(func, SemanticMethod)
            and not func.is_static
            and mapping.native_position == func.passed_object_position
        ):
            return False
        return mapping.python_position is not None

    def _projected_argument_return(
        self,
        func_or_arg: SemanticFunction | SemanticArgument,
        arg: SemanticArgument | None = None,
        *,
        visible: bool,
    ) -> str:
        """Handle projected argument return for the current generation context."""
        if isinstance(func_or_arg, SemanticFunction):
            if arg is None:
                raise TypeError("Function projection return emission requires an argument")
            func = func_or_arg
            projected_arg = arg
        else:
            func = None
            projected_arg = func_or_arg
        if visible:
            return self._named_return(projected_arg, func=func)
        return self._plain_projected_return(projected_arg)

    def _named_return(self, arg: SemanticArgument, *, func: SemanticFunction | None = None) -> str:
        """Handle named return for the current generation context."""
        semantic_type = self._visible_projected_type(
            arg.semantic_type,
            unwrap_address_projection=func is not None and self._uses_address_projection(func, arg),
        )
        descriptor_kind = self._scalar_descriptor_kind(semantic_type)
        if descriptor_kind is not None:
            semantic_type = self._visible_scalar_descriptor_type(semantic_type)
        return_text = f'{self._contract("Returns")}["{arg.name}", {self._visit(semantic_type)}]'
        if descriptor_kind is not None or arg.optional:
            return f"{return_text} | None"
        return return_text

    @staticmethod
    def _visible_projected_type(
        semantic_type: SemanticType,
        *,
        unwrap_address_projection: bool = False,
    ) -> SemanticType:
        """Return the Python-visible type for address-projected scalars."""
        wrapped = PyiPrinter._visible_wrapped_callable_type(semantic_type)
        if wrapped is not semantic_type:
            return wrapped
        storage = semantic_type.storage
        if (
            unwrap_address_projection
            and semantic_type.rank == 0
            and storage is not None
            and storage.kind in {"address", "reference"}
            and storage.pointer_depth == 1
        ) or (
            semantic_type.rank == 0
            and storage is not None
            and storage.kind == "address"
            and storage.metadata.get(ADDRESS_ROLE_METADATA) == ADDRESS_ROLE_PROJECTION
        ):
            visible = deepcopy(semantic_type)
            visible.storage = SemanticStorageContract(
                kind="value",
                read_only=storage.read_only,
                mutable=not storage.read_only,
            )
            return visible
        return semantic_type

    @staticmethod
    def _visible_wrapped_callable_type(semantic_type: SemanticType) -> SemanticType:
        """Hide native address topology behind a wrapped Python object."""
        storage = semantic_type.storage
        if not (
            semantic_type.rank == 0
            and semantic_type.name != "String"
            and (semantic_type.dtype or semantic_type.name) not in SEMANTIC_SCALAR_TYPE_NAMES
            and storage is not None
            and storage.kind in {"reference", "pointer", "address"}
            and storage.pointer_depth == 1
            and storage.metadata.get(ADDRESS_ROLE_METADATA) != ADDRESS_ROLE_RAW
        ):
            return semantic_type
        visible = deepcopy(semantic_type)
        visible.metadata[_WRAPPED_CALLABLE_TYPE_METADATA] = True
        return visible

    def _plain_projected_return(self, arg: SemanticArgument) -> str:
        """Handle plain projected return for the current generation context."""
        semantic_type = deepcopy(arg.semantic_type)
        descriptor_kind = self._scalar_descriptor_kind(semantic_type)
        if descriptor_kind is not None:
            semantic_type = self._visible_scalar_descriptor_type(semantic_type)
        storage = semantic_type.storage
        if (
            semantic_type.rank == 0
            and storage is not None
            and (storage.kind == "reference" or storage.kind == "address")
        ):
            semantic_type.storage = None
        type_text = self._visit(semantic_type)
        if descriptor_kind is not None or arg.optional:
            return f"{type_text} | None"
        return type_text

    def _callable_name(self, func: SemanticFunction, *, owner: object | None = None) -> str:
        """Return the Python-visible callable name to write in the contract."""
        if (
            not self._normalize_fortran_public_names
            or func.name.startswith("__")
            or func.origin.source_language != "fortran"
        ):
            return func.name
        return self._public_name(
            func.name,
            category="method" if isinstance(func, SemanticMethod) else "function",
            owner=owner if owner is not None else func,
        )

    def _data_member_name(self, variable: SemanticVariable) -> str:
        """Return the Python-visible class data-member name."""
        if not self._normalize_fortran_public_names:
            return variable.name
        return self._public_name(variable.name, category="field", owner=variable)

    def _module_variable_name(self, variable: SemanticVariable) -> str:
        """Return the Python-visible module variable name."""
        if not self._normalize_fortran_public_names:
            return variable.name
        return self._public_name(variable.name, category="variable", owner=variable)

    def _public_name(self, raw_name: str, *, category: str, owner: object) -> str:
        """Reserve and return a normalized Python public name."""
        key = (self._public_namespace, category, self._public_owner_key(owner))
        reserved = self._reserved_public_names.get(key)
        if reserved is not None:
            return reserved
        public_name = self._naming_policy.reserve_public_name(
            self._public_namespace,
            raw_name,
            category=category,
            owner=raw_name,
        )
        self._reserved_public_names[key] = public_name
        return public_name

    @staticmethod
    def _public_owner_key(owner: object) -> object:
        """Return a stable cache key for one emitted public declaration."""
        if isinstance(owner, str | int | tuple):
            return owner
        return id(owner)

    def _decorators(self, func: SemanticFunction, *, indent: str = "", emitted_name: str | None = None) -> str:
        """Handle decorators for the current generation context."""
        decorators = []
        emitted_name = emitted_name or func.name
        if self._is_private(func):
            decorators.append(f"{indent}@{self._contract('private')}")
        if isinstance(func, SemanticMethod) and func.is_static:
            decorators.append(f"{indent}@staticmethod")
        bind_target = func.metadata.get(BIND_TARGET_METADATA)
        if bind_target is None and func.native_name and func.native_name != emitted_name:
            bind_target = func.native_name
        if bind_target and not func.metadata.get(OVERLOAD_TARGET_METADATA):
            decorators.append(f"{indent}@{self._contract('bind')}({json.dumps(str(bind_target))})")
        if (
            func.origin.source_language == "fortran"
            and func.origin.native_scope is None
            and not isinstance(func, SemanticMethod)
            and not func.metadata.get(OVERLOAD_TARGET_METADATA)
        ):
            decorators.append(f"{indent}@{self._contract('external')}")
        if not func.metadata.get(OVERLOAD_TARGET_METADATA) and self._requires_native_call(func):
            decorators.append(
                f"{indent}{self._native_call(self._pyi_projection(func), self._native_result_projection(func))}"
            )
        if isinstance(policy := func.metadata.get(RUNTIME_STATUS_ERROR_METADATA), dict):
            decorators.append(f"{indent}{self._raises(policy)}")
        if func.metadata.get(RUNTIME_RELEASE_GIL_METADATA):
            decorators.append(f"{indent}@{self._contract('nogil')}")
        if not decorators:
            return ""
        return "\n".join(decorators) + "\n"

    @staticmethod
    def _pyi_projection(func: SemanticFunction) -> list[ProjectionMapping]:
        """Return projection metadata adjusted for bound instance methods."""
        if not isinstance(func, SemanticMethod) or func.is_static or func.passed_object_position is None:
            projected = deepcopy(func.projection)
            if not projected and any(
                PyiPrinter._scalar_descriptor_kind(argument.semantic_type) is not None for argument in func.arguments
            ):
                projected = [
                    ProjectionMapping(
                        python_name=argument.name,
                        native_name=argument.name,
                        native_position=index,
                        python_position=index,
                    )
                    for index, argument in enumerate(func.arguments)
                ]
            projected = PyiPrinter._with_value_projections(func, projected)
            projected = PyiPrinter._with_descriptor_projections(func, projected)
            return PyiPrinter._with_address_projections(func, projected)
        passed_position = func.passed_object_position
        projected = deepcopy(func.projection)
        if not projected:
            projected = [
                ProjectionMapping(
                    python_name=argument.name,
                    native_name=argument.name,
                    native_position=index,
                    python_position=index,
                )
                for index, argument in enumerate(func.arguments)
            ]
        for mapping in projected:
            if mapping.python_position == passed_position:
                mapping.python_position = None
                mapping.value_kind = "pass"
                continue
            if mapping.python_position is not None and mapping.python_position > passed_position:
                old_position = mapping.python_position
                mapping.python_position -= 1
                PyiPrinter._shift_argument_value_ref(mapping, old_position, mapping.python_position)
        projected = PyiPrinter._with_value_projections(func, projected)
        projected = PyiPrinter._with_descriptor_projections(func, projected)
        return PyiPrinter._with_address_projections(func, projected)

    @staticmethod
    def _with_value_projections(
        func: SemanticFunction,
        projection: list[ProjectionMapping],
    ) -> list[ProjectionMapping]:
        """Mark exact derived value arguments on their native-call slots."""
        by_name = {argument.name: argument for argument in func.arguments}
        for mapping in projection:
            if mapping.value_kind:
                continue
            argument = by_name.get(mapping.python_name or mapping.native_name)
            if (
                argument is None
                and mapping.python_position is not None
                and 0 <= mapping.python_position < len(func.arguments)
            ):
                argument = func.arguments[mapping.python_position]
            if argument is None or not argument.metadata.get(NATIVE_BY_VALUE_METADATA):
                continue
            if mapping.python_position is None:
                raise ValueError("Value projection requires a visible Python argument")
            mapping.value_kind = "value"
            mapping.value = {"kind": "arg", "position": mapping.python_position}
        return projection

    @staticmethod
    def _with_descriptor_projections(
        func: SemanticFunction,
        projection: list[ProjectionMapping],
    ) -> list[ProjectionMapping]:
        """Mark scalar descriptor arguments as explicit native projections."""
        by_name = {argument.name: argument for argument in func.arguments}
        for mapping in projection:
            if mapping.value_kind:
                continue
            argument = by_name.get(mapping.python_name or mapping.native_name)
            if (
                argument is None
                and mapping.python_position is not None
                and 0 <= mapping.python_position < len(func.arguments)
            ):
                argument = func.arguments[mapping.python_position]
            if argument is None:
                continue
            descriptor = PyiPrinter._scalar_descriptor_kind(argument.semantic_type)
            if descriptor is None:
                continue
            mapping.value_kind = descriptor
            if mapping.python_position is not None:
                mapping.value = {"kind": "arg", "position": mapping.python_position}
            elif mapping.result_position is not None:
                mapping.value = {
                    "kind": "return",
                    "name": mapping.native_name,
                    "position": mapping.result_position,
                }
        return projection

    @staticmethod
    def _native_result_projection(func: SemanticFunction) -> ProjectionMapping | None:
        """Return the explicit native scalar descriptor function-result mapping."""
        descriptor = PyiPrinter._scalar_descriptor_kind(func.return_type)
        if descriptor is None:
            return None
        return ProjectionMapping(
            result_position=0,
            value_kind=descriptor,
            value={"kind": "return", "position": 0},
        )

    @staticmethod
    def _shift_argument_value_ref(
        mapping: ProjectionMapping,
        old_position: int,
        new_position: int,
    ) -> None:
        """Keep nested native-call argument refs aligned with method arguments."""
        if mapping.value_kind not in {"addr", "allocatable", "pointer", "value"} or not isinstance(mapping.value, dict):
            return
        if mapping.value.get("kind") == "arg" and mapping.value.get("position") == old_position:
            mapping.value["position"] = new_position

    @staticmethod
    def _with_address_projections(
        func: SemanticFunction,
        projection: list[ProjectionMapping],
    ) -> list[ProjectionMapping]:
        """Mark scalar address mappings as explicit native address projections."""
        by_name = {arg.name: arg for arg in func.arguments}
        for mapping in projection:
            if mapping.value_kind:
                continue
            if mapping.python_position is None:
                continue
            arg = by_name.get(mapping.python_name or mapping.native_name)
            if arg is None:
                continue
            if not PyiPrinter._uses_address_projection(func, arg):
                continue
            mapping.value_kind = "addr"
            mapping.value = {"kind": "arg", "position": mapping.python_position}
        return projection

    def _raises(self, policy: dict[str, object]) -> str:
        """Handle raises for the current generation context."""
        status = policy.get("status")
        if not isinstance(status, str) or not status:
            raise ValueError("raises metadata requires a non-empty status output name")
        parts = [f"status={json.dumps(status)}"]
        message = policy.get("message")
        if message is not None:
            if not isinstance(message, str) or not message:
                raise ValueError("raises metadata message must be a non-empty output name")
            parts.append(f"message={json.dumps(message)}")
        success = policy.get("success", 0)
        if not isinstance(success, int) or isinstance(success, bool):
            raise ValueError("raises metadata success must be an integer")
        parts.append(f"success={success}")
        return f"@{self._contract('raises')}({', '.join(parts)})"

    def _native_call(
        self,
        projection: list[ProjectionMapping],
        native_result: ProjectionMapping | None = None,
    ) -> str:
        """Handle native call for the current generation context."""
        entries = ", ".join(
            self._native_projection_entry(mapping)
            for mapping in sorted(
                projection, key=lambda item: item.native_position if item.native_position is not None else -1
            )
        )
        suffix = ""
        if native_result is not None:
            suffix = f", result={self._native_projection_value(native_result)}"
        return f"@{self._contract('native_call')}([{entries}]{suffix})"

    def _native_projection_entry(self, mapping: ProjectionMapping) -> str:
        """Handle native projection entry for the current generation context."""
        if mapping.value_kind:
            return self._native_projection_value(mapping)
        if mapping.python_position is not None:
            return f"{self._contract('Arg')}({mapping.python_position})"
        if mapping.result_position is not None:
            if mapping.native_name:
                return f"{self._contract('Return')}({mapping.native_name!r}, {mapping.result_position})"
            return f"{self._contract('Return')}({mapping.result_position})"
        raise ValueError("native_call cannot represent a native-only projection entry")

    def _native_projection_value(self, mapping: ProjectionMapping) -> str:
        """Handle native projection value for the current generation context."""
        if mapping.value_kind == "addr":
            return f"{self._contract('Addr')}({self._native_value_ref(mapping.value)})"
        if mapping.value_kind == "value":
            return f"{self._contract('Value')}({self._native_value_ref(mapping.value)})"
        if mapping.value_kind in {"allocatable", "pointer"}:
            helper = "Allocatable" if mapping.value_kind == "allocatable" else "Pointer"
            return f"{self._contract(helper)}({self._native_value_ref(mapping.value)})"
        if mapping.value_kind == "literal":
            return self._native_literal_value(mapping.value)
        if mapping.value_kind == "len":
            return f"{self._contract('Len')}({self._native_value_ref(mapping.value)})"
        if mapping.value_kind == "shape":
            return f"{self._native_value_ref(mapping.value['value'])}.shape[{mapping.value['dim']}]"
        if mapping.value_kind == "is_present":
            return f"{self._contract('IsPresent')}({self._native_value_ref(mapping.value)})"
        if mapping.value_kind == "work":
            return f"{self._contract('Work')}({mapping.value!r})"
        if mapping.value_kind == "pass":
            return f"{self._contract('Pass')}()"
        raise ValueError(f"Unsupported native_call projection entry: {mapping.value_kind!r}")

    def _native_literal_value(self, value: object) -> str:
        """Emit a hidden native literal with its ABI type."""
        if not isinstance(value, dict) or "type" not in value or "value" not in value:
            raise ValueError("native_call literal entries require 'type' and 'value'")
        literal = value["value"]
        rendered = json.dumps(literal) if isinstance(literal, str) else repr(literal)
        return f"{self._native_literal_type(str(value['type']))}({rendered})"

    def _native_literal_type(self, type_text: str) -> str:
        """Return a typed-literal type with imported contract base name."""
        match = re.fullmatch(r"([A-Za-z_]\w*)(.*)", type_text)
        if match is None:
            return type_text
        name, suffix = match.groups()
        return f"{self._contract(name)}{suffix}" if name in CONTRACT_SYMBOLS else type_text

    def _native_value_ref(self, value: dict[str, int | str]) -> str:
        """Handle native value ref for the current generation context."""
        kind = value.get("kind")
        if kind == "arg":
            return f"{self._contract('Arg')}({value['position']})"
        if kind == "return":
            if value.get("name"):
                return f"{self._contract('Return')}({value['name']!r}, {value['position']})"
            return f"{self._contract('Return')}({value['position']})"
        if kind == "work":
            return f"{self._contract('Work')}({value['name']!r})"
        raise ValueError(f"Unsupported native_call value reference: {kind!r}")

    @staticmethod
    def _requires_native_call(func: SemanticFunction) -> bool:
        """Return whether requires native call."""
        if isinstance(func, SemanticMethod) and func.name == "__init__" and func.metadata.get(BIND_TARGET_METADATA):
            return True
        if PyiPrinter._scalar_descriptor_kind(func.return_type) is not None:
            return True
        if any(PyiPrinter._scalar_descriptor_kind(argument.semantic_type) is not None for argument in func.arguments):
            return True
        if func.metadata.get(NATIVE_PROJECTION_METADATA) and any(
            mapping.result_position is not None for mapping in func.projection
        ):
            return True
        if isinstance(func, SemanticMethod) and not func.is_static and func.passed_object_position not in {None, 0}:
            return True
        projection = PyiPrinter._with_value_projections(func, deepcopy(func.projection))
        projection = PyiPrinter._with_address_projections(func, projection)
        return any(
            PyiPrinter._requires_explicit_projection_mapping(mapping)
            for mapping in projection
            if not PyiPrinter._is_assignment_passed_object_return(func, mapping)
        )

    @staticmethod
    def _is_assignment_passed_object_return(func: SemanticFunction, mapping: ProjectionMapping) -> bool:
        """Return whether mapping only records assignment returning the bound object."""
        return bool(
            func.metadata.get(OVERLOAD_KIND_METADATA) == "assignment"
            and isinstance(func, SemanticMethod)
            and not func.is_static
            and mapping.result_position is not None
            and mapping.native_position == func.passed_object_position
            and mapping.python_position == func.passed_object_position
        )

    @staticmethod
    def _requires_explicit_projection_mapping(mapping: ProjectionMapping) -> bool:
        """Return whether requires explicit projection mapping."""
        if mapping.value_kind:
            return True
        if mapping.result_position is not None:
            return mapping.python_position is None or mapping.python_position != mapping.native_position
        if mapping.python_position is None:
            return True
        return mapping.native_position is not None and mapping.python_position != mapping.native_position

    @staticmethod
    def _call_arguments(func: SemanticFunction) -> list[SemanticArgument]:
        """Handle call arguments for the current generation context."""
        hidden_names = {
            mapping.python_name or mapping.native_name
            for mapping in func.projection
            if mapping.native_position is not None and mapping.python_position is None
        }
        return [arg for arg in func.arguments if arg.name not in hidden_names]

    @classmethod
    def _method_call_arguments(cls, method: SemanticMethod) -> list[SemanticArgument]:
        """Handle method call arguments for the current generation context."""
        args = cls._call_arguments(method)
        if method.is_static:
            return args
        if method.passed_object_position is not None:
            return [arg for index, arg in enumerate(args) if index != method.passed_object_position]
        if args and args[0].name == "self":
            return args[1:]
        return args

    @staticmethod
    def _is_private(node) -> bool:
        """Return whether is private."""
        return getattr(node, "visibility", "public") == "private"

    @staticmethod
    def _annotation_target(name: str) -> str:
        """Handle annotation target for the current generation context."""
        if name.isidentifier() and not keyword.iskeyword(name):
            return name
        return f"var[{name!r}]"

    @staticmethod
    def _parameter_target(name: str) -> str:
        """Handle parameter target for the current generation context."""
        if name.isidentifier() and not keyword.iskeyword(name):
            return name
        if name.isidentifier():
            return f"{name}_"
        target = re.sub(r"\W+", "_", name).strip("_") or "arg"
        if target[:1].isdigit():
            target = f"arg_{target}"
        if keyword.iskeyword(target):
            target = f"{target}_"
        return target

    @staticmethod
    def _opaque_dependency_class(type_name: str, c_kind: str | None) -> SemanticClass:
        """Build the semantic placeholder for one missing opaque dependency."""
        base_classes: list[str] = []
        metadata: dict[str, object] = {"representation": "opaque"}
        if c_kind == "struct":
            base_classes.append("CStruct")
            metadata["c_kind"] = "struct"
        elif c_kind == "union":
            base_classes.append("CUnion")
            metadata["c_kind"] = "union"
        base_classes.append("Opaque")
        return SemanticClass(
            name=type_name,
            native_name=type_name,
            base_classes=base_classes,
            metadata=metadata,
        )

    @staticmethod
    def _module_list(modules: SemanticModule | Iterable[SemanticModule] | None) -> list[SemanticModule]:
        """Normalize one semantic module or an iterable to a list."""
        if modules is None:
            return []
        if isinstance(modules, SemanticModule):
            return [modules]
        return list(modules)


_DEFAULT_PRINTER = PyiPrinter()


def emit_module(module: SemanticModule, *, normalize_fortran_public_names: bool = False) -> str:
    """Emit one semantic module through the default stateless printer."""
    if normalize_fortran_public_names:
        return PyiPrinter(normalize_fortran_public_names=True).emit(module)
    return _DEFAULT_PRINTER.emit(module)


def opaque_dependency_modules(
    modules: SemanticModule | Iterable[SemanticModule],
    *,
    available_modules: Iterable[SemanticModule] | None = None,
) -> list[SemanticModule]:
    """Build missing opaque dependency modules required by emitted stubs."""
    source_modules = PyiPrinter._module_list(modules)
    known_modules = PyiPrinter._module_list(available_modules) if available_modules is not None else source_modules
    known_classes = {
        (module.name, cls.name) for module in known_modules for cls in module.classes if isinstance(cls, SemanticClass)
    }
    dependencies: dict[str, dict[str, str | None]] = {}
    for module in source_modules:
        for semantic_type in _iter_module_semantic_types(module):
            ref = semantic_type.metadata.get(EXTERNAL_TYPE_REF_METADATA)
            if not isinstance(ref, dict) or ref.get("representation") != "opaque":
                continue
            origin_module = ref.get("origin_module")
            type_name = ref.get("name")
            if not isinstance(origin_module, str) or not isinstance(type_name, str):
                continue
            if (origin_module, type_name) in known_classes:
                continue
            c_kind = semantic_type.metadata.get("c_kind")
            dependencies.setdefault(origin_module, {}).setdefault(
                type_name,
                c_kind if c_kind in {"struct", "union"} else None,
            )
    return [
        SemanticModule(
            name=module_name,
            classes=[
                PyiPrinter._opaque_dependency_class(type_name, c_kind)
                for type_name, c_kind in sorted(type_kinds.items())
            ],
        )
        for module_name, type_kinds in sorted(dependencies.items())
    ]


def emit_module_stubs(
    modules: SemanticModule | Iterable[SemanticModule],
    *,
    available_modules: Iterable[SemanticModule] | None = None,
    normalize_fortran_public_names: bool = False,
) -> dict[str, str]:
    """Emit a mapping of module names to complete stub texts."""
    from prik.semantics.policy_completion import complete_semantic_policies

    source_modules = PyiPrinter._module_list(modules)
    emitted_modules: dict[str, SemanticModule] = {}
    for module in source_modules:
        if module.name in emitted_modules:
            raise ValueError(f"Cannot emit duplicate semantic module '{module.name}'")
        emitted_modules[module.name] = deepcopy(module)

    for dependency in opaque_dependency_modules(
        source_modules,
        available_modules=available_modules,
    ):
        target = emitted_modules.setdefault(dependency.name, SemanticModule(name=dependency.name))
        existing = {cls.name for cls in target.classes}
        target.classes.extend(cls for cls in dependency.classes if cls.name not in existing)

    complete_semantic_policies(emitted_modules.values())
    return {
        module_name: emit_module(
            module,
            normalize_fortran_public_names=normalize_fortran_public_names,
        ).strip()
        for module_name, module in emitted_modules.items()
    }
