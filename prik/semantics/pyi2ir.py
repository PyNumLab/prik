"""Translate parsed editable semantic ``.pyi`` contracts into semantic IR.

The public entrypoints consume Python AST produced by :mod:`prik.parsers.pyi`.
They validate the supported contract subset, retain declared native facts and
projections, and return ``SemanticModule`` objects for native-contract
validation and post-IR policy completion.  They deliberately do not choose
wrapper ownership or lowering policy.
"""

from __future__ import annotations

import ast
import re
from copy import deepcopy
from dataclasses import dataclass, field

from prik.contracts import CONTRACT_SYMBOLS, CONTRACT_TYPE_NAMES
from prik.utilities.declaration_expressions import (
    declaration_expression_calls,
    is_declaration_expression_helper,
    is_public_declaration_expression,
)
from prik.types.numpy import SEMANTIC_SCALAR_TYPE_NAMES
from prik.semantics.ownership_metadata import (
    OWNERSHIP_POLICY_METADATA,
    set_ownership_metadata,
    set_pointer_policy_metadata,
)
from prik.semantics.metadata import (
    ADDRESS_ROLE_METADATA,
    ADDRESS_ROLE_PROJECTION,
    ADDRESS_ROLE_RAW,
    BIND_TARGET_METADATA,
    MAYBE_UNALLOCATED_METADATA,
    NATIVE_PROJECTION_METADATA,
    OPTIONAL_ABSENT_HANDLE_METADATA,
    PROJECTED_OUTPUT_METADATA,
    SCALAR_STORAGE_CATEGORY,
    SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA,
    USER_PRIVATE_METADATA,
)
from prik.semantics.native_array_handles import mark_native_array_handle, native_array_descriptor_kind
from prik.utilities.visitor import ClassVisitor

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
    PROTOTYPE_INTENT_METADATA,
    PROTOTYPE_REF_METADATA,
    RUNTIME_RELEASE_GIL_METADATA,
    RUNTIME_STATUS_ERROR_METADATA,
    ProjectionMapping,
    ProcedureOverloadSet,
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticConstraint,
    SemanticExpressionCallable,
    SemanticField,
    SemanticFunction,
    SemanticImport,
    SemanticImportItem,
    SemanticMethod,
    SemanticModule,
    SemanticOrigin,
    SemanticPrototype,
    SemanticStorageContract,
    SemanticType,
    SemanticVariable,
    _iter_module_semantic_types,
)

__all__ = ("convert_pyi_to_ir", "reconcile_external_type_refs")


_PYI_OPTIONAL_RETURN_METADATA = "_pyi_optional_return"
_CONTRACT_MODULE = "prik.contracts"
_FLAT_DIMENSION_SENTINEL = "@prik.Flat"
_STRIDED_DIMENSION_SENTINEL = "@prik.Strided"


# Contract-conversion state and public entrypoints


@dataclass(frozen=True)
class _PrototypeArgumentSpec:
    """Store one exact interface dummy's type, transport, and direction."""

    semantic_type: SemanticType
    passes_by_value: bool
    intent: str | None = None


def convert_pyi_to_ir(
    tree: ast.Module,
    *,
    module_name: str = "<pyi>",
    source: str = "",
    native_language: str = "fortran",
) -> SemanticModule:
    """Convert one parsed editable semantic ``.pyi`` contract into semantic IR.

    Use this after :func:`prik.parsers.pyi.parse_pyi_text` when the caller
    already owns AST parsing.  ``tree`` must be an ``ast.Module``; ``source``
    is retained only to preserve source spelling for array dimensions.
    ``native_language`` selects declared array-layout defaults (``"fortran"``
    or ``"c"``).  The returned module is normally passed to native-contract
    validation and policy completion; malformed supported-contract syntax
    raises ``TypeError`` or ``ValueError`` before those later stages.

    Examples:
        >>> import ast
        >>> contract = "from prik.contracts import Float64\\n" "def scale(value: Float64) -> Float64: ...\\n"
        >>> module = convert_pyi_to_ir(ast.parse(contract), module_name="math", source=contract)
        >>> module.functions[0].return_type.name
        'Float64'
    """

    if not isinstance(tree, ast.Module):
        raise TypeError("convert_pyi_to_ir expects a Python ast.Module parsed by prik.parsers.pyi")

    # Interpret top-level declarations and validate their local relationships.
    module = _PyiAstParser(
        module_name=module_name,
        source=source,
        native_language=native_language,
    ).parse(tree)

    # Mark imported names so batch reconciliation can bind cross-module types.
    _annotate_imported_external_type_refs(module)
    return module


@dataclass
class _Decorators:
    """Accumulate validated declaration decorators before IR construction."""

    visibility: str = "public"
    projection: list[ProjectionMapping] = field(default_factory=list)
    native_result: ProjectionMapping | None = None
    has_native_call: bool = False
    overload_target: str | None = None
    overload_generic: str | None = None
    bind_target: str | None = None
    native_type: dict[str, object] | None = None
    standalone: bool = False
    is_static: bool = False
    release_gil: bool = False
    error_status_policy: dict[str, object] | None = None
    prototype: bool = False
    pure: bool = False


@dataclass
class _PendingOverload:
    """Keep an overload declaration until its specific target is available."""

    owner: SemanticModule | SemanticClass
    declaration: SemanticFunction
    target: str
    generic_name: str | None = None


class _PyiAstParser:
    """Stateful AST visitor that builds one semantic module from a contract.

    The parser stores import bindings, declared user type names, and unresolved
    overloads while visitors create the module's declarations.  Resolution runs
    only after the complete module body has been visited.
    """

    def __init__(self, *, module_name: str, source: str = "", native_language: str = "fortran"):
        """Initialize module-building state from the declared target language.

        ``native_language`` is normalized once and must be ``"c"`` or
        ``"fortran"``.  The initializer creates the mutable semantic module
        and empty resolution registries; invalid languages fail immediately.
        """
        native_language = native_language.casefold()
        if native_language not in {"c", "fortran"}:
            raise ValueError(f"Unsupported semantic .pyi native language: {native_language!r}")
        self.module = SemanticModule(name=module_name, origin=SemanticOrigin(source_language=native_language))
        self.source = source
        self.native_language = native_language
        self._pending_overloads: list[_PendingOverload] = []
        self._contract_bindings: dict[str, str] = {}
        self._user_type_names: set[str] = set()

    def parse(self, tree: ast.Module) -> SemanticModule:
        """Visit a module AST and finalize relationships that require all declarations.

        The method mutates this parser's module in declaration order, then
        resolves pending overloads and local prototype references.  It returns
        that same completed ``SemanticModule`` and propagates validation errors.
        """
        # Build imports and declarations in source order.
        _ModuleVisitor(self)._visit(tree)

        # Resolve references whose targets can appear later in the module.
        self._resolve_overloads()
        self._resolve_local_prototype_references()
        self._resolve_declaration_expression_callables()
        return self.module

    # Module declarations and imports

    def _resolve_local_prototype_references(self) -> None:
        """Bind local prototype annotations after all declarations are known."""
        prototypes = {prototype.name: prototype for prototype in self.module.prototypes}
        if len(prototypes) != len(self.module.prototypes):
            raise ValueError("Prototype names must be unique within a semantic module")
        runtime_names = {item.name for item in [*self.module.functions, *self.module.classes, *self.module.variables]}
        collisions = sorted(runtime_names & prototypes.keys())
        if collisions:
            raise ValueError(f"Prototype name collides with a runtime declaration: {collisions[0]!r}")
        for semantic_type in _iter_module_semantic_types(self.module):
            if semantic_type.storage is not None and semantic_type.storage.kind == "callback":
                continue
            prototype = prototypes.get(semantic_type.name)
            if prototype is not None:
                _bind_prototype_reference(
                    semantic_type,
                    prototype,
                    origin_module=self.module.name,
                    source_name=prototype.name,
                )

    def _resolve_declaration_expression_callables(self) -> None:
        """Reconstruct native call provenance from local declarations and imports.

        This finalization pass consumes every array shape after the whole
        contract is known and mutates only each array's parallel callable
        provenance. Calls remain declarative annotation text and are never
        imported or executed by the loader.
        """
        local_functions = {function.name.casefold(): function for function in self.module.functions}
        local_prototypes = {prototype.name.casefold(): prototype for prototype in self.module.prototypes}
        explicit_imports, namespace_imports = self._declaration_callable_imports()
        for semantic_type in _iter_module_semantic_types(self.module):
            storage = semantic_type.storage
            array = storage.array if storage is not None else None
            if array is None:
                continue
            array.expression_callables = [
                self._expression_callable_references(
                    expression,
                    local_functions,
                    local_prototypes,
                    explicit_imports,
                    namespace_imports,
                )
                for expression in array.shape
            ]

    def _declaration_callable_imports(
        self,
    ) -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
        """Index explicit imported names and visible module namespaces."""
        explicit: dict[str, tuple[str, str]] = {}
        namespaces: dict[str, str] = {}
        for imported in self.module.imports:
            if isinstance(imported, SemanticImport):
                if imported.items:
                    for item in imported.items:
                        explicit[(item.target or item.source).casefold()] = (imported.module, item.source)
                else:
                    namespaces[imported.module.split(".", 1)[0].casefold()] = imported.module
                continue
            for item in str(imported).split(","):
                module_name, _, alias = item.strip().partition(" as ")
                namespaces[(alias or module_name.split(".", 1)[0]).casefold()] = module_name
        return explicit, namespaces

    def _expression_callable_references(
        self,
        expression: str,
        local_functions: dict[str, SemanticFunction],
        local_prototypes: dict[str, SemanticPrototype],
        explicit_imports: dict[str, tuple[str, str]],
        namespace_imports: dict[str, str],
    ) -> list[SemanticExpressionCallable]:
        """Resolve one axis's calls to semantic native identities when possible."""
        references = []
        for name in declaration_expression_calls(expression):
            reference = self._resolve_expression_callable(
                name,
                local_functions,
                local_prototypes,
                explicit_imports,
                namespace_imports,
            )
            if reference is not None:
                references.append(reference)
            elif name != "<invalid>" and not is_declaration_expression_helper(name):
                references.append(
                    SemanticExpressionCallable(
                        name=name,
                        native_name=name.rsplit(".", 1)[-1],
                        source_language=self.native_language,
                    )
                )
        return references

    def _resolve_expression_callable(
        self,
        name: str,
        local_functions: dict[str, SemanticFunction],
        local_prototypes: dict[str, SemanticPrototype],
        explicit_imports: dict[str, tuple[str, str]],
        namespace_imports: dict[str, str],
    ) -> SemanticExpressionCallable | None:
        """Resolve one contract call against local, flattened, or qualified names."""
        if "." in name:
            namespace, native_name = name.rsplit(".", 1)
            native_scope = namespace_imports.get(namespace.casefold())
            if native_scope is None:
                return None
            return SemanticExpressionCallable(
                name=name,
                native_name=native_name,
                native_scope=native_scope,
                source_language=self.native_language,
                placement="module",
            )

        prototype = local_prototypes.get(name.casefold())
        if prototype is not None:
            return SemanticExpressionCallable(
                name=name,
                native_name=prototype.native_name or prototype.name,
                native_scope=None,
                source_language=self.native_language,
                placement="standalone",
                declaration=prototype,
            )

        function = local_functions.get(name.casefold())
        if function is not None:
            standalone = function.origin.source_language == "fortran" and function.origin.native_scope is None
            return SemanticExpressionCallable(
                name=name,
                native_name=function.native_name or function.name,
                native_scope=None if standalone else (function.origin.native_scope or self.module.name),
                source_language=function.origin.source_language or self.native_language,
                placement="standalone" if standalone else "module",
                declaration=function,
            )
        imported = explicit_imports.get(name.casefold())
        if imported is not None:
            return SemanticExpressionCallable(
                name=name,
                native_name=imported[1],
                native_scope=imported[0],
                source_language=self.native_language,
                placement="module",
            )
        return None

    def import_from(self, node: ast.ImportFrom) -> SemanticImport:
        """Convert one non-contract ``from`` import AST node into semantic metadata.

        Relative-dot depth and aliases are preserved exactly in the returned
        ``SemanticImport``; this method does not mutate the module.
        """
        module_name = "." * node.level + (node.module or "")
        return SemanticImport(
            module=module_name,
            items=[SemanticImportItem(source=alias.name, target=alias.asname) for alias in node.names],
        )

    def register_contract_import(self, node: ast.ImportFrom) -> bool:
        """Register imported ``prik.contracts`` names and report whether it was one.

        The method consumes a ``from`` import, records local aliases in parser
        state, and returns ``False`` for every other module.  Duplicate or
        unknown contract bindings fail rather than being interpreted by name.
        """
        module_name = "." * node.level + (node.module or "")
        if module_name != _CONTRACT_MODULE:
            return False
        for alias in node.names:
            if alias.name == "*":
                raise ValueError("prik.contracts does not support wildcard imports")
            if alias.name not in CONTRACT_SYMBOLS:
                raise ValueError(f"Unknown prik contract name {alias.name!r}")
            local_name = alias.asname or alias.name
            previous = self._contract_bindings.get(local_name)
            if previous is not None and previous != alias.name:
                raise ValueError(f"Contract import name {local_name!r} is bound more than once")
            self._contract_bindings[local_name] = alias.name
        return True

    def import_name(self, node: ast.Import) -> str:
        """Render a plain import AST node for the module import list without mutation."""
        return ", ".join(f"{alias.name} as {alias.asname}" if alias.asname else alias.name for alias in node.names)

    def register_user_type_names(self, node: ast.Module) -> None:
        """Record names that can intentionally shadow contract type spellings."""
        for item in ast.walk(node):
            if isinstance(item, ast.ClassDef):
                self._user_type_names.add(item.name)
            elif isinstance(item, ast.ImportFrom):
                module_name = "." * item.level + (item.module or "")
                if module_name == _CONTRACT_MODULE:
                    continue
                for alias in item.names:
                    if alias.name != "*":
                        self._user_type_names.add(alias.asname or alias.name)
            elif isinstance(item, ast.Import):
                for alias in item.names:
                    self._user_type_names.add(alias.asname or alias.name.split(".", 1)[0])

    def class_def(
        self,
        node: ast.ClassDef,
        *,
        visibility: str,
        native_type: dict[str, object] | None = None,
    ) -> SemanticClass:
        """Convert one class AST node, its body, and supported native metadata.

        The class-body visitor supplies fields, methods, nested classes, and
        delayed overload declarations.  This method records those overloads on
        parser state, preserves field-constructor rules, and returns the new
        ``SemanticClass`` without inserting it into the module itself.
        """
        body = _ClassBodyVisitor(self, class_name=node.name)
        body._walk_nodes(node.body)
        if body.constructor_from_fields and body.has_bound_constructor:
            raise ValueError("Direct constructor bindings replace the generated field constructor; remove one __init__")
        base_classes = [self.base_class_name(base) for base in node.bases]
        origin = self._origin(
            source_language="fortran" if body.constructor_from_fields or native_type is not None else None,
            user_private=visibility == "private",
        )
        if not body.constructor_from_fields:
            origin.metadata[SUPPRESS_DEFAULT_CONSTRUCTOR_METADATA] = True

        metadata = self._class_metadata(base_classes)
        if native_type is not None:
            attributes = list(native_type.get("attributes", ()))
            metadata["fortran_type_attributes"] = attributes
            normalized_attributes = {str(item).strip().casefold().replace(" ", "") for item in attributes}
            if "bind(c)" in normalized_attributes:
                metadata["fortran_bind_c"] = True
            if "sequence" in normalized_attributes:
                metadata["fortran_sequence"] = True
            finalizers = list(native_type.get("finalizers", ()))
            if finalizers:
                metadata["fortran_final_procedures"] = finalizers
        semantic_class = SemanticClass(
            name=node.name,
            native_name=node.name,
            fields=body.fields,
            methods=body.methods,
            classes=body.classes,
            base_classes=base_classes,
            metadata=metadata,
            visibility=visibility,
            origin=origin,
        )
        self._pending_overloads.extend(
            _PendingOverload(semantic_class, declaration, target, generic_name)
            for declaration, target, generic_name in body.pending_overloads
        )
        return semantic_class

    @staticmethod
    def _class_metadata(base_classes: list[str]) -> dict[str, object]:
        """Derive representation markers from supported contract base-class names."""
        metadata: dict[str, object] = {}
        if "CStruct" in base_classes:
            metadata["c_kind"] = "struct"
        if "CUnion" in base_classes:
            metadata["c_kind"] = "union"
        if "CAnonymous" in base_classes:
            metadata["c_anonymous"] = True
        if "Opaque" in base_classes:
            metadata["representation"] = "opaque"
        return metadata

    def base_class_name(self, node: ast.expr) -> str:
        """Return a class base name, resolving imported contract aliases."""
        contract_name = self.contract_name(node)
        if contract_name is not None:
            return contract_name
        return ast.unparse(node)

    @staticmethod
    def _origin(*, source_language: str | None = None, user_private: bool = False) -> SemanticOrigin:
        """Create declaration provenance, marking user-private declarations when requested."""
        origin = SemanticOrigin(source_language=source_language)
        if user_private:
            origin.metadata[USER_PRIVATE_METADATA] = True
        return origin

    def function_def(
        self,
        node: ast.FunctionDef,
        *,
        visibility: str,
        projection: list[ProjectionMapping] | None = None,
        native_result: ProjectionMapping | None = None,
        native_name: str | None = None,
        standalone: bool = False,
        has_native_call: bool = False,
        release_gil: bool = False,
        error_status_policy: dict[str, object] | None = None,
    ) -> SemanticFunction:
        """Convert a module-level stub into a semantic function declaration.

        The method consumes validated decorator facts and a typed function AST,
        builds argument/result projections, and returns a declaration without
        appending it to the module.  Native binding and runtime-status metadata
        are copied verbatim from the decorators.
        """
        actual_projection = projection if projection is not None else []
        semantic_args, return_type = self._callable_parts(
            node,
            projection=actual_projection,
            native_result=native_result,
        )
        metadata = {BIND_TARGET_METADATA: native_name} if native_name is not None else {}
        if has_native_call:
            metadata[NATIVE_PROJECTION_METADATA] = True
        if release_gil:
            metadata[RUNTIME_RELEASE_GIL_METADATA] = True
        if error_status_policy is not None:
            metadata[RUNTIME_STATUS_ERROR_METADATA] = dict(error_status_policy)
        origin = self._origin(
            source_language="fortran" if standalone else None,
            user_private=visibility == "private",
        )
        if standalone:
            origin.source_kind = "function" if return_type is not None else "subroutine"
            origin.native_name = native_name or node.name
        return SemanticFunction(
            name=node.name,
            native_name=native_name or node.name,
            arguments=semantic_args,
            return_type=return_type,
            projection=actual_projection,
            metadata=metadata,
            visibility=visibility,
            origin=origin,
        )

    def prototype_def(
        self,
        node: ast.FunctionDef,
        *,
        visibility: str,
        pure: bool,
    ) -> SemanticPrototype:
        """Convert one exact native interface without creating a runtime function."""
        self._validate_callable_header(node)
        arguments = []
        for argument, default in zip(node.args.args, self._argument_defaults(node), strict=False):
            if argument.annotation is None:
                raise ValueError(f"Expected typed prototype argument: {argument.arg!r}")
            spec = self._prototype_argument_spec(argument.annotation)
            origin_metadata: dict[str, object] = {"value": spec.passes_by_value}
            if spec.intent is not None:
                origin_metadata[PROTOTYPE_INTENT_METADATA] = spec.intent
            arguments.append(
                SemanticArgument(
                    argument.arg,
                    spec.semantic_type,
                    optional=self.default_marks_optional(default),
                    visibility=visibility,
                    origin=SemanticOrigin(metadata=origin_metadata),
                )
            )
        return_type = (
            SemanticType("None", dtype="None")
            if isinstance(node.returns, ast.Constant) and node.returns.value is None
            else self.semantic_type(node.returns)
        )
        metadata = {"fortran_attributes": ["pure"]} if pure else {}
        return SemanticPrototype(
            name=node.name,
            native_name=node.name,
            arguments=arguments,
            return_type=return_type,
            metadata=metadata,
            visibility=visibility,
            origin=SemanticOrigin(
                native_name=node.name,
                native_scope=self.module.name,
                source_kind="prototype",
            ),
            pure=pure,
        )

    def method_def(
        self,
        node: ast.FunctionDef,
        *,
        visibility: str,
        projection: list[ProjectionMapping] | None = None,
        native_result: ProjectionMapping | None = None,
        is_static: bool = False,
        native_name: str | None = None,
        class_name: str,
        infer_passed_object: bool = True,
        has_native_call: bool = False,
        release_gil: bool = False,
        error_status_policy: dict[str, object] | None = None,
    ) -> SemanticMethod:
        """Convert a class stub into a semantic method declaration.

        It consumes decorator facts and typed arguments, inserting an internal
        passed-object argument for non-static bound methods when required.  The
        insertion rewrites later projection positions in place so Python and
        native positions remain aligned; the method returns the declaration.
        """
        actual_projection = projection if projection is not None else []
        semantic_args, return_type = self._callable_parts(
            node,
            projection=actual_projection,
            native_result=native_result,
            drop_untyped_self=True,
        )
        metadata = {BIND_TARGET_METADATA: native_name} if native_name is not None else {}
        if has_native_call:
            metadata[NATIVE_PROJECTION_METADATA] = True
        passed_object_name = None
        passed_object_position = None
        if infer_passed_object and not is_static:
            pass_mappings = [mapping for mapping in actual_projection if mapping.value_kind == "pass"]
            if node.name == "__init__" and len(pass_mappings) != 1:
                raise ValueError("Bound constructor native_call requires exactly one Pass() entry")
            if len(pass_mappings) > 1:
                raise ValueError("native_call may contain at most one Pass() entry")
            passed_object_position = pass_mappings[0].native_position if pass_mappings else 0
            if not isinstance(passed_object_position, int) or not 0 <= passed_object_position <= len(semantic_args):
                raise ValueError("native_call Pass() position is out of range")
            passed_object_name = "self"
            semantic_args.insert(
                passed_object_position,
                SemanticArgument(
                    passed_object_name,
                    SemanticType(
                        class_name,
                        dtype=class_name,
                        storage=SemanticStorageContract(kind="reference", mutable=True, pointer_depth=1),
                    ),
                ),
            )
            self._restore_pass_projection(actual_projection, passed_object_position)
        if release_gil:
            metadata[RUNTIME_RELEASE_GIL_METADATA] = True
        if error_status_policy is not None:
            metadata[RUNTIME_STATUS_ERROR_METADATA] = dict(error_status_policy)
        origin = self._origin(
            source_language=None,
            user_private=visibility == "private",
        )
        return SemanticMethod(
            name=node.name,
            native_name=native_name or node.name,
            arguments=semantic_args,
            return_type=return_type,
            projection=actual_projection,
            metadata=metadata,
            visibility=visibility,
            origin=origin,
            is_static=is_static,
            passed_object_name=passed_object_name,
            passed_object_position=passed_object_position,
        )

    @staticmethod
    def _restore_pass_projection(projection: list[ProjectionMapping], passed_position: int) -> None:
        """Replace ``Pass()`` markers after inserting ``self`` into a method signature.

        The projection list is mutated in place: the pass marker becomes the
        passed object's normal Python mapping and later argument references are
        shifted by one to preserve their original targets.
        """
        for mapping in projection:
            if mapping.value_kind == "pass":
                mapping.value_kind = None
                mapping.python_position = passed_position
                mapping.python_name = "self"
                mapping.native_name = mapping.native_name or "self"
            elif mapping.python_position is not None and mapping.python_position >= passed_position:
                old_position = mapping.python_position
                mapping.python_position += 1
                _PyiAstParser._shift_argument_value_ref(mapping, old_position, mapping.python_position)

    def ann_assign(
        self,
        node: ast.AnnAssign,
        *,
        binding_cls: type[SemanticVariable] = SemanticVariable,
    ) -> SemanticVariable:
        """Convert one annotated assignment into a variable or field declaration.

        ``binding_cls`` selects the concrete semantic binding type.  The method
        validates writable-value metadata, applies source-name and visibility
        metadata, and returns a new binding without attaching it to an owner.
        """
        name = self.annotation_target(node.target)
        visibility, semantic_type, original_name = self.visible_type(node.annotation)
        if original_name is not None:
            name = original_name
        self._validate_python_value_policy(
            semantic_type,
            writable=self._type_uses_writable_storage(semantic_type),
            owner=name,
        )
        binding = binding_cls(
            name=name,
            semantic_type=semantic_type,
            visibility=visibility,
            default_value=self.assignment_default_value(node.value, semantic_type),
        )
        if visibility == "private":
            binding.origin.metadata[USER_PRIVATE_METADATA] = True
        binding.optional = self.default_marks_optional(node.value)
        return binding

    # Decorators and overload resolution

    def decorators(self, nodes: list[ast.expr], *, context: str) -> _Decorators:
        """Validate a declaration's decorators and return their normalized facts.

        Decorators are processed in source order into a fresh internal record.
        Incompatible combinations, including overload plus native-call, raise
        before a declaration is constructed.
        """
        parsed = _Decorators()
        for node in nodes:
            self._apply_decorator(parsed, node, context=context)
        if parsed.overload_target is not None and parsed.has_native_call:
            raise ValueError("overload cannot be combined with native_call; put native_call on the specific procedure")
        if parsed.pure and not parsed.prototype:
            raise ValueError("pure requires prototype")
        if parsed.prototype:
            if parsed.standalone:
                raise ValueError(
                    "prototype cannot be combined with standalone; "
                    "prototype use already determines its native procedure role"
                )
            if parsed.has_native_call or parsed.overload_target is not None or parsed.bind_target is not None:
                raise ValueError("prototype cannot be combined with native_call, overload, or bind")
            if parsed.release_gil or parsed.error_status_policy is not None or parsed.native_type is not None:
                raise ValueError("prototype cannot carry wrapper or native-type decorators")
            if parsed.visibility != "public" or parsed.is_static:
                raise ValueError("prototype cannot be private or static")
        return parsed

    def _apply_decorator(self, parsed: _Decorators, node: ast.expr, *, context: str) -> None:
        """Dispatch one decorator AST node to its validator, mutating ``parsed``.

        Built-in Python ``staticmethod`` and the supported contract decorators
        are recognized through imports.  Any other decorator fails closed with
        context-specific diagnostics.
        """
        if self.matches_name(node, "private"):
            parsed.visibility = "private"
            return
        if self.matches_plain_name(node, "staticmethod"):
            parsed.is_static = True
            return
        target = node.func if isinstance(node, ast.Call) else node
        handlers = {
            "overload": self._apply_overload_decorator,
            "bind": self._apply_bind_decorator,
            "standalone": self._apply_standalone_decorator,
            "nogil": self._apply_nogil_decorator,
            "native_call": self._apply_native_call_decorator,
            "native_type": self._apply_native_type_decorator,
            "prototype": self._apply_prototype_decorator,
            "pure": self._apply_pure_decorator,
            "raises": self._apply_raises_decorator,
        }
        handler = next((value for name, value in handlers.items() if self.matches_name(target, name)), None)
        if handler is None:
            raise ValueError(f"Unsupported {context} decorator: {ast.unparse(node)!r}")
        handler(parsed, node, context)

    @staticmethod
    def _apply_prototype_decorator(parsed: _Decorators, node: ast.expr, context: str) -> None:
        """Mark a module-level declaration as an exact native interface."""
        if isinstance(node, ast.Call):
            raise ValueError("prototype does not accept arguments")
        if context != ".pyi":
            raise ValueError("prototype is only valid for module-level declarations")
        if parsed.prototype:
            raise ValueError("Duplicate prototype decorator")
        parsed.prototype = True

    @staticmethod
    def _apply_pure_decorator(parsed: _Decorators, node: ast.expr, context: str) -> None:
        """Mark an exact interface with the native pure characteristic."""
        if isinstance(node, ast.Call):
            raise ValueError("pure does not accept arguments")
        if context != ".pyi":
            raise ValueError("pure is only valid for module-level prototype declarations")
        if parsed.pure:
            raise ValueError("Duplicate pure decorator")
        parsed.pure = True

    def _apply_overload_decorator(self, parsed: _Decorators, node: ast.expr, context: str) -> None:
        """Record one specific-procedure target for deferred overload resolution."""
        if not isinstance(node, ast.Call):
            raise ValueError("overload expects one specific procedure name")
        if parsed.overload_target is not None:
            raise ValueError(f"Duplicate {context} overload decorator")
        if len(node.args) != 1:
            raise ValueError("overload expects one specific procedure name")
        target = ast.literal_eval(node.args[0])
        if not isinstance(target, str) or not target:
            raise ValueError("overload expects a non-empty specific procedure name")
        if len(node.keywords) > 1 or any(keyword.arg != "generic" for keyword in node.keywords):
            raise ValueError("overload accepts only the optional generic keyword")
        if node.keywords:
            generic_name = ast.literal_eval(node.keywords[0].value)
            if not isinstance(generic_name, str) or not generic_name:
                raise ValueError("overload generic expects a non-empty Fortran generic name")
            parsed.overload_generic = generic_name
        parsed.overload_target = target

    @staticmethod
    def _required_string_decorator_argument(node: ast.expr, name: str) -> str:
        """Extract the sole non-empty string argument required by a named decorator."""
        if not isinstance(node, ast.Call) or len(node.args) != 1 or node.keywords:
            raise ValueError(f"{name} expects one native symbol name")
        target = ast.literal_eval(node.args[0])
        if not isinstance(target, str) or not target:
            raise ValueError(f"{name} expects a non-empty native symbol name")
        return target

    def _apply_bind_decorator(self, parsed: _Decorators, node: ast.expr, context: str) -> None:
        """Store one native symbol binding in decorator state, rejecting duplicates."""
        if parsed.bind_target is not None:
            raise ValueError(f"Duplicate {context} bind decorator")
        parsed.bind_target = self._required_string_decorator_argument(node, "bind")

    @staticmethod
    def _apply_nogil_decorator(parsed: _Decorators, node: ast.expr, context: str) -> None:
        """Record a no-argument GIL-release request in decorator state."""
        if isinstance(node, ast.Call):
            raise ValueError("nogil does not accept arguments")
        if parsed.release_gil:
            raise ValueError(f"Duplicate {context} nogil decorator")
        parsed.release_gil = True

    @staticmethod
    def _apply_standalone_decorator(parsed: _Decorators, node: ast.expr, context: str) -> None:
        """Record a standalone native declaration marker in decorator state."""
        if isinstance(node, ast.Call):
            raise ValueError("standalone does not accept arguments")
        if parsed.standalone:
            raise ValueError(f"Duplicate {context} standalone decorator")
        parsed.standalone = True

    @staticmethod
    def _apply_native_type_decorator(parsed: _Decorators, node: ast.expr, context: str) -> None:
        """Validate and store class-level native type attributes and finalizers."""
        if parsed.native_type is not None:
            raise ValueError(f"Duplicate {context} native_type decorator")
        if not isinstance(node, ast.Call) or node.args:
            raise ValueError("native_type accepts keyword arguments only")
        allowed = {"attributes", "finalizers"}
        values: dict[str, object] = {}
        for keyword in node.keywords:
            if keyword.arg not in allowed:
                raise ValueError(f"native_type got unsupported keyword {keyword.arg!r}")
            if keyword.arg in values:
                raise ValueError(f"native_type repeats {keyword.arg!r}")
            value = ast.literal_eval(keyword.value)
            if not isinstance(value, tuple) or not all(isinstance(item, str) and item for item in value):
                raise ValueError(f"native_type {keyword.arg} must be a tuple of non-empty strings")
            values[keyword.arg] = value
        parsed.native_type = values

    def _apply_native_call_decorator(self, parsed: _Decorators, node: ast.expr, context: str) -> None:
        """Parse ``native_call`` projection facts into decorator state."""
        del context
        if not isinstance(node, ast.Call):
            raise ValueError("native_call expects a single list argument")
        parsed.has_native_call = True
        parsed.projection, parsed.native_result = self.native_call(node)

    def _apply_raises_decorator(self, parsed: _Decorators, node: ast.expr, context: str) -> None:
        """Parse a native status-error policy into decorator state, once only."""
        if not isinstance(node, ast.Call):
            raise ValueError("raises expects keyword arguments")
        if parsed.error_status_policy is not None:
            raise ValueError(f"Duplicate {context} raises decorator")
        parsed.error_status_policy = self.error_status_policy(node)

    def native_call(self, node: ast.Call) -> tuple[list[ProjectionMapping], ProjectionMapping | None]:
        """Parse a ``native_call`` AST into ordered argument and optional result mappings.

        Projection entries retain their native-list positions.  Invalid list or
        result syntax raises before the mappings are returned.
        """
        if len(node.args) != 1:
            raise ValueError("native_call expects one native-argument list")
        if len(node.keywords) > 1 or any(keyword.arg != "result" for keyword in node.keywords):
            raise ValueError("native_call accepts only the optional result keyword")
        entries = node.args[0]
        if not isinstance(entries, ast.List):
            raise ValueError("native_call expects a list of projection entries")
        projection = [
            self.native_projection_entry(entry, native_position) for native_position, entry in enumerate(entries.elts)
        ]
        native_result = self.native_result_projection(node.keywords[0].value) if node.keywords else None
        return projection, native_result

    def native_result_projection(self, node: ast.AST) -> ProjectionMapping:
        """Parse the nullable scalar descriptor returned by a native function."""
        mapping = self.native_projection_entry(node, native_position=-1)
        if mapping.value_kind in {"allocatable", "pointer"} and mapping.python_position is not None:
            raise ValueError("native_call result must reference Return(i), not Arg(i)")
        if mapping.value_kind not in {"allocatable", "pointer"} or mapping.result_position is None:
            raise ValueError("native_call result expects Allocatable(Return(i)) or Pointer(Return(i))")
        mapping.native_position = None
        if mapping.result_position != 0:
            raise ValueError("native scalar descriptor function result must map to Python result slot 0")
        return mapping

    @staticmethod
    def error_status_policy(node: ast.Call) -> dict[str, object]:
        """Validate ``raises`` keyword syntax and return its immutable policy facts."""
        if node.args:
            raise ValueError("raises accepts keyword arguments only")
        allowed = {"status", "message", "success"}
        values: dict[str, object] = {}
        for keyword in node.keywords:
            if keyword.arg is None:
                raise ValueError("raises does not accept ** expansion")
            if keyword.arg not in allowed:
                raise ValueError(f"raises got unsupported keyword {keyword.arg!r}")
            if keyword.arg in values:
                raise ValueError(f"raises repeats {keyword.arg!r}")
            values[keyword.arg] = ast.literal_eval(keyword.value)

        status = values.get("status")
        if not isinstance(status, str) or not status:
            raise ValueError("raises requires status=<non-empty output name>")

        message = values.get("message")
        if message is not None and (not isinstance(message, str) or not message):
            raise ValueError("raises message must be a non-empty output name")

        success = values.get("success", 0)
        if not isinstance(success, int) or isinstance(success, bool):
            raise ValueError("raises success must be an integer status value")

        policy = {"status": status, "success": success}
        if message is not None:
            policy["message"] = message
        return policy

    def _resolve_overloads(self) -> None:
        """Resolve all pending overload declarations into owner overload sets.

        This consumes the parser's delayed-overload list after every declaration
        is known, deep-copies validated target signatures, and appends them to
        their semantic owners.  Missing, duplicate, or incompatible targets fail.
        """
        for pending in self._pending_overloads:
            target = self._resolve_overload_target(pending.owner, pending.target)
            candidate = self._validated_overload_candidate(
                pending.owner,
                pending.declaration,
                target,
                generic_name=pending.generic_name,
            )
            overload_sets = pending.owner.overload_sets
            overload_name = self._overload_set_name(pending.owner, pending.declaration.name)
            overload_set = next((item for item in overload_sets if item.name == overload_name), None)
            if overload_set is None:
                overload_set = ProcedureOverloadSet(overload_name)
                overload_sets.append(overload_set)
            if any(proc.metadata.get(OVERLOAD_TARGET_METADATA) == pending.target for proc in overload_set.procedures):
                raise ValueError(
                    f"Overload {pending.declaration.name!r} references specific procedure "
                    f"{pending.target!r} more than once"
                )
            overload_set.procedures.append(candidate)

    @classmethod
    def _iter_classes(cls, classes: list[SemanticClass]):
        """Yield classes and nested classes depth first in source-list order."""
        for semantic_class in classes:
            yield semantic_class
            yield from cls._iter_classes(semantic_class.classes)

    @staticmethod
    def _overload_set_name(owner: SemanticModule | SemanticClass, declaration_name: str) -> str:
        """Return the semantic overload-set name, normalizing reflected class operators."""
        if isinstance(owner, SemanticModule):
            return declaration_name
        return {
            "__radd__": "__add__",
            "__rsub__": "__sub__",
            "__rmul__": "__mul__",
            "__rtruediv__": "__truediv__",
            "__rpow__": "__pow__",
            "__rand__": "__and__",
            "__ror__": "__or__",
        }.get(declaration_name, declaration_name)

    def _resolve_overload_target(
        self,
        owner: SemanticModule | SemanticClass,
        target_name: str,
    ) -> SemanticFunction:
        """Find exactly one specific procedure visible to a pending overload declaration."""
        candidates = [
            function for function in self.module.functions if target_name in {function.name, function.native_name}
        ]
        if isinstance(owner, SemanticClass) and not candidates:
            candidates = [method for method in owner.methods if target_name in {method.name, method.native_name}]
        if not candidates:
            raise ValueError(f"Overload references missing specific procedure {target_name!r}")
        if len(candidates) != 1:
            raise ValueError(f"Overload target {target_name!r} is ambiguous")
        return candidates[0]

    def _validated_overload_candidate(
        self,
        owner: SemanticModule | SemanticClass,
        declaration: SemanticFunction,
        target: SemanticFunction,
        *,
        generic_name: str | None,
    ) -> SemanticFunction:
        """Copy and validate an overload target for the declaration's owner context.

        Module overloads become generic procedure entries; class overloads also
        record Python method, binding, and passed-object facts.  The returned
        copy is safe to attach to an overload set without mutating its target.
        """
        candidate = deepcopy(target)
        candidate.visibility = declaration.visibility
        candidate.metadata[OVERLOAD_TARGET_METADATA] = target.name
        for key in (RUNTIME_RELEASE_GIL_METADATA, RUNTIME_STATUS_ERROR_METADATA):
            if key in declaration.metadata:
                candidate.metadata[key] = deepcopy(declaration.metadata[key])

        if isinstance(owner, SemanticModule):
            if generic_name is not None:
                raise ValueError("generic is only valid for class overloads; use bind on a module overload")
            self._validate_overload_signature(declaration, candidate, list(candidate.arguments))
            if bind_target := declaration.metadata.get(BIND_TARGET_METADATA):
                candidate.native_name = str(bind_target)
                candidate.metadata[BIND_TARGET_METADATA] = str(bind_target)
            candidate.metadata[OVERLOAD_KIND_METADATA] = "generic"
            return candidate

        bound_position = self._class_overload_bound_position(owner, declaration, candidate)
        call_arguments = (
            list(candidate.arguments)
            if bound_position is None
            else [arg for index, arg in enumerate(candidate.arguments) if index != bound_position]
        )
        self._validate_overload_signature(declaration, candidate, call_arguments, bound_position=bound_position)
        kind, native_name = self._class_overload_identity(
            declaration.name,
            bound_position,
            generic_name=generic_name,
        )
        candidate.metadata[FORTRAN_GENERIC_NAME_METADATA] = native_name
        candidate.metadata[OVERLOAD_KIND_METADATA] = kind
        candidate.metadata[PYTHON_METHOD_NAME_METADATA] = declaration.name
        if bind_target := declaration.metadata.get(BIND_TARGET_METADATA):
            candidate.native_name = str(bind_target)
            candidate.metadata[BIND_TARGET_METADATA] = str(bind_target)
        if bound_position is not None:
            candidate.metadata[PYTHON_BOUND_POSITION_METADATA] = bound_position
        if isinstance(declaration, SemanticMethod) and declaration.is_static:
            candidate.metadata[PYTHON_STATIC_METADATA] = True
        return candidate

    @staticmethod
    def _validate_overload_signature(
        declaration: SemanticFunction,
        target: SemanticFunction,
        call_arguments: list[SemanticArgument],
        *,
        bound_position: int | None = None,
    ) -> None:
        """Reject an overload whose public signature differs from its target.

        Address-backed projected scalars are compared through their visible value
        form.  A class overload may instead expose a projected bound-object
        return; every other mismatch raises ``ValueError``.
        """
        visible_declaration_arguments = [_PyiAstParser._visible_overload_argument(arg) for arg in declaration.arguments]
        visible_call_arguments = [_PyiAstParser._visible_overload_argument(arg) for arg in call_arguments]
        if visible_declaration_arguments == visible_call_arguments and (
            _PyiAstParser._visible_overload_type(declaration.return_type)
            == _PyiAstParser._visible_overload_type(target.return_type)
            or _PyiAstParser._matches_bound_projection_return(declaration, target, bound_position)
        ):
            return
        raise ValueError(
            f"Overload declaration {declaration.name!r} is incompatible with "
            f"specific procedure {target.native_name or target.name!r}"
        )

    @staticmethod
    def _visible_overload_argument(argument: SemanticArgument) -> SemanticArgument:
        """Copy one overload argument with its type normalized for public comparison."""
        visible = deepcopy(argument)
        visible.semantic_type = _PyiAstParser._visible_overload_type(argument.semantic_type)
        return visible

    @staticmethod
    def _visible_overload_type(semantic_type: SemanticType | None) -> SemanticType | None:
        """Return a visible comparison type, hiding projection-only scalar addresses."""
        if semantic_type is None:
            return None
        storage = semantic_type.storage
        if (
            semantic_type.rank == 0
            and storage is not None
            and storage.kind == "address"
            and storage.metadata.get(ADDRESS_ROLE_METADATA) == ADDRESS_ROLE_PROJECTION
        ):
            visible_type = deepcopy(semantic_type)
            visible_type.storage = SemanticStorageContract(
                kind="value",
                read_only=storage.read_only,
                mutable=not storage.read_only,
            )
            visible_type.ownership.mutable = not storage.read_only
            return visible_type
        return semantic_type

    @staticmethod
    def _matches_bound_projection_return(
        declaration: SemanticFunction,
        target: SemanticFunction,
        bound_position: int | None,
    ) -> bool:
        """Check whether a method overload returns its projected bound object."""
        if bound_position is None or declaration.return_type is None:
            return False
        if not 0 <= bound_position < len(target.arguments):
            return False
        if not any(
            mapping.native_position == bound_position and mapping.result_position is not None
            for mapping in target.projection
        ):
            return False
        expected = deepcopy(target.arguments[bound_position].semantic_type)
        if expected.rank == 0 and expected.storage is not None and expected.storage.kind in {"address", "reference"}:
            expected.storage = None
        expected.ownership = deepcopy(declaration.return_type.ownership)
        return _PyiAstParser._visible_overload_type(declaration.return_type) == expected

    @staticmethod
    def _class_overload_bound_position(
        owner: SemanticClass,
        declaration: SemanticFunction,
        target: SemanticFunction,
    ) -> int | None:
        """Locate the unique native wrapped-object argument for a class overload.

        Static methods need no bound object.  Instance methods must match one
        target argument whose type is the owning class and whose removal leaves
        the declared Python arguments in order; ambiguity is an error.
        """
        if isinstance(declaration, SemanticMethod) and declaration.is_static:
            return None
        remaining_names = [argument.name for argument in declaration.arguments]
        matching = [
            index
            for index, argument in enumerate(target.arguments)
            if argument.semantic_type.name.casefold() == owner.name.casefold()
            and [arg.name for pos, arg in enumerate(target.arguments) if pos != index] == remaining_names
        ]
        if len(matching) == 1:
            return matching[0]
        if not matching:
            raise ValueError(
                f"Overload declaration {declaration.name!r} cannot bind an argument of type {owner.name!r} "
                f"from specific procedure {target.native_name or target.name!r}"
            )
        raise ValueError(
            f"Overload declaration {declaration.name!r} has an ambiguous bound argument in "
            f"specific procedure {target.native_name or target.name!r}"
        )

    @staticmethod
    def _class_overload_identity(
        method_name: str,
        bound_position: int | None,
        *,
        generic_name: str | None,
    ) -> tuple[str, str]:
        """Map a Python class-overload spelling to its Fortran generic identity.

        Operator, comparison, constructor, assignment, and named-operator forms
        have explicit identities.  The returned kind and native generic name are
        consumed by overload resolution; incompatible bound positions fail.
        """
        direct_operators = {
            "__add__": "+",
            "__sub__": "-",
            "__mul__": "*",
            "__truediv__": "/",
            "__pow__": "**",
            "__and__": ".and.",
            "__or__": ".or.",
            "__invert__": ".not.",
            "__pos__": "+",
            "__neg__": "-",
            "__eq__": "==",
            "__ne__": "/=",
            "__lt__": "<",
            "__le__": "<=",
            "__gt__": ">",
            "__ge__": ">=",
        }
        reflected_operators = {
            "__radd__": "+",
            "__rsub__": "-",
            "__rmul__": "*",
            "__rtruediv__": "/",
            "__rpow__": "**",
            "__rand__": ".and.",
            "__ror__": ".or.",
        }
        if method_name in reflected_operators:
            if bound_position != 1:
                raise ValueError(f"{method_name} requires the wrapped object to be the second native operand")
            identity = ("operator", f"operator({reflected_operators[method_name]})")
            return _PyiAstParser._validated_generic_override(method_name, identity, generic_name)
        if method_name in direct_operators:
            token = direct_operators[method_name]
            if method_name in {"__lt__", "__le__", "__gt__", "__ge__"} and bound_position == 1:
                token = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[token]
            kind = (
                "comparison"
                if method_name in {"__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__"}
                else "operator"
            )
            identity = (kind, f"operator({token})")
            return _PyiAstParser._validated_generic_override(method_name, identity, generic_name)
        if method_name == "assign":
            identity = ("assignment", "assignment(=)")
            return _PyiAstParser._validated_generic_override(method_name, identity, generic_name)
        if method_name == "__init__":
            if generic_name is not None:
                raise ValueError("overload generic is not valid for constructor declarations")
            return "constructor", method_name
        reflected_named = method_name.startswith("r_operator_")
        if reflected_named or method_name.startswith("operator_"):
            prefix = "r_operator_" if reflected_named else "operator_"
            token = method_name.removeprefix(prefix)
            if not token or not token.isidentifier():
                raise ValueError(f"Invalid named operator method {method_name!r}")
            if reflected_named and bound_position != 1:
                raise ValueError(f"{method_name} requires the wrapped object to be the second native operand")
            identity = ("named_operator", f"operator(.{token}.)")
            return _PyiAstParser._validated_generic_override(method_name, identity, generic_name)
        if generic_name is not None:
            raise ValueError(f"overload generic is not valid for ordinary method {method_name!r}")
        return "generic", method_name

    @staticmethod
    def _validated_generic_override(
        method_name: str,
        identity: tuple[str, str],
        generic_name: str | None,
    ) -> tuple[str, str]:
        """Validate an explicit generic override against an operator's allowed names."""
        if generic_name is None:
            return identity
        compact = re.sub(r"\s+", "", generic_name).casefold()
        allowed_overrides = {
            "__eq__": {"operator(==)", "operator(.eq.)", "operator(.eqv.)"},
            "__ne__": {"operator(/=)", "operator(.ne.)", "operator(.neqv.)"},
        }
        if compact not in allowed_overrides.get(method_name, {identity[1].casefold()}):
            raise ValueError(f"overload generic {generic_name!r} is incompatible with method {method_name!r}")
        return identity[0], generic_name

    # Native-call projection parsing

    def native_projection_entry(self, node: ast.AST, native_position: int) -> ProjectionMapping:
        """Convert one ``native_call`` list item into a positioned projection mapping.

        Shape, address, descriptor, typed-literal, and named helper forms are
        dispatched here.  ``native_position`` is preserved in the returned
        mapping; unsupported or untyped expressions fail closed.
        """
        shape_mapping = self.native_shape_projection_entry(node, native_position)
        if shape_mapping is not None:
            return shape_mapping
        if isinstance(node, ast.Constant):
            raise ValueError('native_call hidden literals require typed calls such as Int32(1) or String[1]("N")')
        if not isinstance(node, ast.Call):
            raise ValueError("native_call expects projection entry calls")
        if node.keywords:
            if self._native_literal_type(node.func) is not None:
                raise ValueError("native_call typed literals accept one positional value")
            raise ValueError(f"{self.required_name(node.func)} expects positional arguments only")

        if self._is_addr_call(node):
            return self.native_address_projection_entry(node, native_position)

        descriptor = self.contract_name(node.func)
        if descriptor == "Value":
            return self.native_value_projection_entry(node, native_position)
        if descriptor in {"Allocatable", "Pointer"}:
            return self.native_descriptor_projection_entry(node, native_position, descriptor)

        literal = self.native_literal_projection_entry(node, native_position)
        if literal is not None:
            return literal

        helper = self.required_name(node.func)
        return self._native_helper_projection_entry(helper, node, native_position)

    def native_value_projection_entry(
        self,
        node: ast.Call,
        native_position: int,
    ) -> ProjectionMapping:
        """Parse an exact typed derived-value projection around ``Arg(i)``."""
        if len(node.args) != 1:
            raise ValueError("Value projection expects one Arg(...) reference")
        value = self.native_value_ref(node.args[0])
        if value["kind"] != "arg":
            raise ValueError("Value projection expects Arg(i)")
        return ProjectionMapping(
            native_position=native_position,
            python_position=int(value["position"]),
            value_kind="value",
            value=value,
        )

    def native_descriptor_projection_entry(
        self,
        node: ast.Call,
        native_position: int,
        descriptor: str,
    ) -> ProjectionMapping:
        """Parse a nullable scalar descriptor projection around Arg/Return."""
        if len(node.args) != 1:
            raise ValueError(f"{descriptor} projection expects one Arg(...) or Return(...) reference")
        value = self.native_value_ref(node.args[0], allow_named_return=True)
        mapping = ProjectionMapping(
            native_position=native_position,
            value_kind=descriptor.casefold(),
            value=value,
        )
        if value["kind"] == "arg":
            mapping.python_position = int(value["position"])
        elif value["kind"] == "return":
            mapping.result_position = int(value["position"])
            mapping.native_name = str(value.get("name") or "")
        else:
            raise ValueError(f"{descriptor} projection expects Arg(...) or Return(...)")
        return mapping

    def _native_helper_projection_entry(
        self,
        helper: str,
        node: ast.Call,
        native_position: int,
    ) -> ProjectionMapping:
        """Dispatch a named projection helper after its call shape has been checked."""
        handlers = {
            "Arg": self._native_arg_projection_entry,
            "Return": self._native_return_projection_entry,
            "Pass": self._native_pass_projection_entry,
            "Len": self._native_len_projection_entry,
            "IsPresent": self._native_is_present_projection_entry,
            "Work": self._native_work_projection_entry,
        }
        try:
            handler = handlers[helper]
        except KeyError as exc:
            raise ValueError(f"Unsupported native_call projection entry: {helper}") from exc
        return handler(node, native_position)

    @staticmethod
    def _native_arg_projection_entry(node: ast.Call, native_position: int) -> ProjectionMapping:
        """Parse ``Arg(i)`` into a mapping for one visible Python argument."""
        if len(node.args) != 1:
            raise ValueError("Arg expects one positional index")
        return ProjectionMapping(
            native_position=native_position,
            python_position=int(ast.literal_eval(node.args[0])),
        )

    @staticmethod
    def _native_return_projection_entry(node: ast.Call, native_position: int) -> ProjectionMapping:
        """Parse ``Return`` output syntax into a native mapping and result slot."""
        if len(node.args) not in {1, 2}:
            raise ValueError("Return expects one positional index or a name and index")
        native_name = ""
        position_arg = node.args[0]
        if len(node.args) == 2:
            native_name = str(ast.literal_eval(node.args[0]))
            position_arg = node.args[1]
        return ProjectionMapping(
            native_name=native_name,
            native_position=native_position,
            result_position=int(ast.literal_eval(position_arg)),
        )

    @staticmethod
    def _native_pass_projection_entry(node: ast.Call, native_position: int) -> ProjectionMapping:
        """Parse ``Pass()`` as the temporary passed-object mapping for a method."""
        if node.args:
            raise ValueError("Pass does not accept arguments")
        return ProjectionMapping(
            native_position=native_position,
            value_kind="pass",
        )

    def _native_len_projection_entry(self, node: ast.Call, native_position: int) -> ProjectionMapping:
        """Parse ``Len(value)`` into a hidden native length projection."""
        if len(node.args) != 1:
            raise ValueError("Len expects one value reference")
        return ProjectionMapping(
            native_position=native_position,
            value_kind="len",
            value=self.native_value_ref(node.args[0]),
        )

    def _native_is_present_projection_entry(self, node: ast.Call, native_position: int) -> ProjectionMapping:
        """Parse ``IsPresent(Arg(i))`` into a hidden optional-presence projection."""
        if len(node.args) != 1:
            raise ValueError("IsPresent expects one value reference")
        return ProjectionMapping(
            native_position=native_position,
            value_kind="is_present",
            value=self.native_value_ref(node.args[0]),
        )

    @staticmethod
    def _native_work_projection_entry(node: ast.Call, native_position: int) -> ProjectionMapping:
        """Parse ``Work(name)`` into a hidden named workspace projection."""
        if len(node.args) != 1:
            raise ValueError("Work expects one workspace name")
        return ProjectionMapping(
            native_position=native_position,
            value_kind="work",
            value=str(ast.literal_eval(node.args[0])),
        )

    def native_literal_projection_entry(
        self,
        node: ast.Call,
        native_position: int,
    ) -> ProjectionMapping | None:
        """Parse a typed hidden native literal, or return ``None`` for other calls."""
        native_type = self._native_literal_type(node.func)
        if native_type is None:
            return None
        if node.keywords or len(node.args) != 1:
            raise ValueError("native_call typed literals accept one positional value")
        return ProjectionMapping(
            native_position=native_position,
            value_kind="literal",
            value={
                "type": native_type,
                "value": ast.literal_eval(node.args[0]),
            },
        )

    def _native_literal_type(self, node: ast.AST) -> str | None:
        """Return the imported scalar type name accepted for a typed hidden literal."""
        if isinstance(node, ast.Subscript) and self.matches_name(node.value, "String"):
            length = self._native_literal_string_length(node)
            return f"String[{length}]"
        name = self.contract_name(node)
        if name is None:
            return None
        if name == "String":
            raise ValueError('native_call string literals require String[length](value), for example String[1]("N")')
        if name in SEMANTIC_SCALAR_TYPE_NAMES and name not in {"String", "Void"}:
            return name
        return None

    def _native_literal_string_length(self, node: ast.Subscript) -> str:
        """Validate and return the fixed ``String[n]`` length for a hidden literal."""
        items = self.subscript_items(node)
        if len(items) != 1:
            raise ValueError("native_call string literals require exactly one String length")
        item = items[0]
        if isinstance(item, ast.Slice) or (isinstance(item, ast.Constant) and item.value is Ellipsis):
            raise ValueError("native_call string literals require a fixed String length")
        return self.dimension_text(item)

    def native_address_projection_entry(self, node: ast.Call, native_position: int) -> ProjectionMapping:
        """Parse an ``Addr`` projection and preserve its depth and referenced value."""
        if len(node.args) != 1:
            raise ValueError("Addr projection expects one Arg(...), Return(...), or Work(...) reference")
        if self._addr_depth(node.func) != 1:
            raise ValueError("native_call address projection only supports Addr(...)")
        value = self.native_value_ref(node.args[0])
        mapping = ProjectionMapping(
            native_position=native_position,
            value_kind="addr",
            value=value,
        )
        if value["kind"] == "arg":
            mapping.python_position = int(value["position"])
        elif value["kind"] == "return":
            mapping.result_position = int(value["position"])
        return mapping

    def native_shape_projection_entry(
        self,
        node: ast.AST,
        native_position: int,
    ) -> ProjectionMapping | None:
        """Parse a ``value.shape[i]`` native projection, or return ``None`` if absent."""
        if not isinstance(node, ast.Subscript) or not isinstance(node.value, ast.Attribute):
            return None
        attribute = node.value.attr
        if attribute != "shape":
            return None
        return ProjectionMapping(
            native_position=native_position,
            value_kind="shape",
            value={
                "value": self.native_value_ref(node.value.value),
                "dim": int(ast.literal_eval(node.slice)),
            },
        )

    def native_value_ref(
        self,
        node: ast.AST,
        *,
        allow_named_return: bool = False,
    ) -> dict[str, int | str]:
        """Parse a projection value reference into its normalized dictionary form.

        ``Arg``, ``Return``, and ``Work`` references are validated here.  The
        returned dictionary is embedded in a projection mapping and never keeps
        a live AST reference; named returns require explicit permission.
        """
        if not isinstance(node, ast.Call):
            raise ValueError("Expected Arg(...), Return(...), or Work(...) value reference")
        if node.keywords:
            raise ValueError(f"{self.required_name(node.func)} value reference expects one positional argument")
        helper = self.required_name(node.func)
        if helper == "Arg":
            if len(node.args) != 1:
                raise ValueError("Arg value reference expects one positional argument")
            return {"kind": "arg", "position": int(ast.literal_eval(node.args[0]))}
        if helper == "Return":
            if len(node.args) == 1:
                return {"kind": "return", "position": int(ast.literal_eval(node.args[0]))}
            if allow_named_return and len(node.args) == 2:
                return {
                    "kind": "return",
                    "name": str(ast.literal_eval(node.args[0])),
                    "position": int(ast.literal_eval(node.args[1])),
                }
            raise ValueError("Return value reference expects one index or a name and index")
        if helper == "Work":
            if len(node.args) != 1:
                raise ValueError("Work value reference expects one positional argument")
            return {"kind": "work", "name": str(ast.literal_eval(node.args[0]))}
        raise ValueError("Expected Arg(...), Return(...), or Work(...) value reference")

    # Semantic type and metadata conversion

    def visible_type(
        self,
        node: ast.expr,
        *,
        allow_optional_absent_handle: bool = False,
    ) -> tuple[str, SemanticType, str | None]:
        """Load a type annotation and split visibility and optional source-name metadata."""
        if self.is_subscript_of(node, "private"):
            semantic_type, original_name = self.semantic_type_annotation(
                self.subscript_slice(node),
                allow_optional_absent_handle=allow_optional_absent_handle,
            )
            return "private", semantic_type, original_name
        semantic_type, original_name = self.semantic_type_annotation(
            node,
            allow_optional_absent_handle=allow_optional_absent_handle,
        )
        return "public", semantic_type, original_name

    def semantic_type_annotation(
        self,
        node: ast.expr,
        *,
        allow_optional_absent_handle: bool = False,
    ) -> tuple[SemanticType, str | None]:
        """Interpret ``Annotated`` and nullable-handle wrappers before loading their base type."""
        optional_item = self._optional_union_item(node)
        if optional_item is not None:
            semantic_type = self.semantic_type(optional_item)
            if native_array_descriptor_kind(semantic_type) is not None:
                if not allow_optional_absent_handle:
                    raise ValueError(
                        "Native array handle '| None' is only valid for optional callable arguments; "
                        "unallocated allocatables and unassociated pointers are states inside a present handle"
                    )
                semantic_type.metadata[OPTIONAL_ABSENT_HANDLE_METADATA] = True
                return semantic_type, None
        if not self.is_subscript_of(node, "Annotated"):
            return self.semantic_type(node), None

        items = self.subscript_items(node)
        if not items:
            raise ValueError(f"Annotated type is empty: {ast.unparse(node)!r}")

        original_name = None
        semantic_type = self.semantic_type(items[0])
        for item in items[1:]:
            parsed_name = self.name_metadata(item)
            if parsed_name is not None:
                original_name = parsed_name
                continue
            self.apply_annotation_metadata(semantic_type, item)
        self._validate_array_copy_metadata(semantic_type)
        return semantic_type, original_name

    def semantic_type(self, node: ast.expr) -> SemanticType:
        """Convert one supported type-expression AST node into a semantic type.

        Contract imports determine the allowed spelling.  Descriptor, address,
        array, character, and user/external forms are normalized; malformed or
        unimported contract spellings raise ``ValueError``.
        """
        self._reject_unimported_contract_type(node)
        optional_item = self._optional_union_item(node)
        if optional_item is not None:
            semantic_type = self.semantic_type(optional_item)
            if native_array_descriptor_kind(semantic_type) is not None:
                raise ValueError(
                    "Native array handle '| None' is only valid for optional callable arguments; "
                    "unallocated allocatables and unassociated pointers are states inside a present handle"
                )
        if self.is_subscript_of(node, "Annotated"):
            semantic_type, _ = self.semantic_type_annotation(node)
            return semantic_type
        if self.is_subscript_of(node, "Final"):
            return self._final_type(node)
        if isinstance(node, ast.Call) and self._is_addr_call(node):
            return self._address_type(node)
        if isinstance(node, ast.Call):
            raise ValueError(f"Unsupported semantic type call: {ast.unparse(node)!r}")

        if isinstance(node, ast.Subscript) and self.matches_name(node.value, "String"):
            if self._string_subscript_is_array_dimensions(node):
                raise ValueError(
                    "String[:] is ambiguous; use String for scalar non-fixed length, "
                    "String[:][:] for an array of non-fixed strings, or String[n] for fixed length"
                )
            return self._character_type(node)
        if self.is_subscript_of(node, "Allocatable"):
            return self._descriptor_type(node, "Allocatable")
        if self.is_subscript_of(node, "Pointer"):
            return self._descriptor_type(node, "Pointer")

        name = self.type_name(node)
        if name == "Unknown":
            raise ValueError("Unknown semantic type is not allowed in .pyi annotations")
        if not isinstance(node, ast.Subscript):
            return SemanticType(name=name, dtype=name)

        if not self._is_array_subscript(node):
            raise ValueError(
                "Non-dimensional type subscriptions are not supported; "
                "use Final[...] for constants and Annotated[...] for constraints or array metadata"
            )
        return self.array_type(node)

    def _reject_unimported_contract_type(self, node: ast.expr) -> None:
        """Reject a bare known contract type that was not imported into this contract."""
        name_node = node.value if isinstance(node, ast.Subscript) else node
        if not isinstance(name_node, ast.Name):
            return
        if self.contract_name(name_node) is not None:
            return
        if name_node.id not in CONTRACT_TYPE_NAMES or name_node.id in self._user_type_names:
            return
        raise ValueError(f"Contract type {name_node.id!r} must be imported from prik.contracts")

    def _descriptor_type(self, node: ast.Subscript, descriptor: str) -> SemanticType:
        """Load ``Allocatable[T]`` or ``Pointer[T]`` and mark its descriptor storage."""
        items = self.subscript_items(node)
        if len(items) != 1:
            raise ValueError(f"{descriptor} expects exactly one type: {ast.unparse(node)!r}")
        semantic_type = self.semantic_type(items[0])
        storage = semantic_type.storage
        if semantic_type.rank > 0 or (storage is not None and storage.array is not None):
            return self._array_descriptor_handle_type(semantic_type, descriptor)
        self._apply_scalar_descriptor_kind(semantic_type, descriptor.casefold())
        return semantic_type

    @classmethod
    def _array_descriptor_handle_type(cls, semantic_type: SemanticType, descriptor: str) -> SemanticType:
        """Copy an array type into an explicit native descriptor-handle contract."""
        storage = semantic_type.storage
        if storage is None or storage.array is None or semantic_type.rank <= 0:
            raise ValueError(f"{descriptor}[...] array handles require an array type such as {descriptor}[Float64[:]]")
        descriptor_kind = descriptor.casefold()
        mark_native_array_handle(semantic_type, descriptor_kind)
        return semantic_type

    @staticmethod
    def _apply_scalar_descriptor_kind(semantic_type: SemanticType, descriptor: str) -> None:
        """Mark a rank-zero semantic type as an allocatable or pointer descriptor."""
        if semantic_type.rank > 0 or (semantic_type.storage is not None and semantic_type.storage.array is not None):
            raise ValueError(f"{descriptor.capitalize()} projection supports scalar values only")
        if descriptor == "allocatable":
            semantic_type.metadata["fortran_allocatable"] = True
            return
        if descriptor != "pointer":
            raise ValueError(f"Unsupported scalar descriptor projection: {descriptor!r}")
        semantic_type.metadata["fortran_pointer"] = True
        semantic_type.metadata["fortran_pointer_association"] = "runtime"
        semantic_type.storage = SemanticStorageContract(kind="reference", mutable=True, pointer_depth=1)

    def _final_type(self, node: ast.Subscript) -> SemanticType:
        """Load ``Final[T]`` and append the immutable compile-time-value constraint."""
        items = self.subscript_items(node)
        if len(items) != 1:
            raise ValueError(f"Final expects exactly one type: {ast.unparse(node)!r}")
        semantic_type = self.semantic_type(items[0])
        if not any(constraint.name == "Constant" for constraint in semantic_type.constraints):
            semantic_type.constraints.append(SemanticConstraint("Constant"))
        return semantic_type

    def _address_type(self, node: ast.Call) -> SemanticType:
        """Load ``Addr(T)`` and create mutable native address storage for ``T``."""
        if len(node.args) != 1 or node.keywords:
            raise ValueError(f"Addr type expects one argument: {ast.unparse(node)!r}")
        pointee = self.semantic_type(node.args[0])
        read_only = pointee.storage.read_only if pointee.storage is not None else False
        metadata = dict(pointee.storage.metadata) if pointee.storage is not None else {}
        array = pointee.storage.array if pointee.storage is not None else None
        metadata[ADDRESS_ROLE_METADATA] = ADDRESS_ROLE_RAW
        pointer_depth = self._addr_depth(node.func)
        pointee.storage = SemanticStorageContract(
            kind="address" if pointer_depth == 1 else "pointer",
            read_only=read_only,
            mutable=not read_only,
            pointer_depth=pointer_depth,
            array=array,
            metadata=metadata,
        )
        pointee.ownership.mutable = not read_only
        return pointee

    def array_type(self, node: ast.Subscript) -> SemanticType:
        """Load a bracketed scalar type as an array or fixed-length character contract."""
        if isinstance(node.value, ast.Subscript):
            if self.matches_name(node.value.value, "String"):
                semantic_type = self._character_type(node.value, allow_deferred_length=True)
                return self._array_type_from_dimensions(
                    semantic_type.name,
                    self.array_dimension_texts(node),
                    metadata=semantic_type.metadata,
                )
            semantic_type = self.array_type(node.value)
            selector = ", ".join(self.dimension_text(item) for item in self.subscript_items(node))
            semantic_type.metadata["rank_selector"] = selector
            if semantic_type.storage and semantic_type.storage.array:
                semantic_type.storage.array.metadata["rank_selector"] = selector
            return semantic_type

        return self._array_type_from_dimensions(
            self.type_name(node),
            self.array_dimension_texts(node),
        )

    def _string_subscript_is_array_dimensions(self, node: ast.Subscript) -> bool:
        """Return whether ``String[...]`` is an array contract, not a length."""
        return any(
            isinstance(item, ast.Slice) or (isinstance(item, ast.Constant) and item.value is Ellipsis)
            for item in self.subscript_items(node)
        )

    def array_dimension_texts(self, node: ast.Subscript) -> list[str]:
        """Return normalized source dimension spellings from a bracketed type AST."""
        items = self.subscript_items(node)
        raw_items = self._source_dimension_items(node)
        if raw_items is None or len(raw_items) != len(items):
            return [self.dimension_text(item) for item in items]
        dimensions = []
        for raw_item, item in zip(raw_items, items, strict=True):
            if isinstance(item, ast.Slice) and self._is_empty_step_slice(raw_item):
                dimensions.append(self._strided_dimension_text(raw_item))
            else:
                dimensions.append(self.dimension_text(item))
        return dimensions

    def _source_dimension_items(self, node: ast.Subscript) -> list[str] | None:
        """Recover source-preserving dimension tokens when original contract text exists."""
        if not self.source:
            return None
        source = ast.get_source_segment(self.source, node.slice)
        if source is None:
            return None
        return self._split_top_level_dimensions(source)

    @staticmethod
    def _split_top_level_dimensions(source: str) -> list[str]:
        """Split a dimension fragment at commas outside nested syntax and strings."""
        items = []
        start = 0
        depth = 0
        quote: str | None = None
        escape = False
        for index, char in enumerate(source):
            if quote is not None:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == quote:
                    quote = None
                continue
            if char in {"'", '"'}:
                quote = char
                continue
            if char in "([{":
                depth += 1
                continue
            if char in ")]}":
                depth = max(depth - 1, 0)
                continue
            if char == "," and depth == 0:
                items.append(source[start:index].strip())
                start = index + 1
        items.append(source[start:].strip())
        return items

    @staticmethod
    def _is_empty_step_slice(text: str) -> bool:
        """Report whether a three-part source slice omits its final step value."""
        parts = text.split(":")
        return len(parts) == 3 and parts[2].strip() == ""

    @staticmethod
    def _strided_dimension_text(text: str) -> str:
        """Replace a syntactic empty stride with the internal strided-dimension marker."""
        lower, upper, _step = text.split(":", 2)
        return f"{lower.strip()}:{upper.strip()}:{_STRIDED_DIMENSION_SENTINEL}"

    def _array_type_from_dimensions(
        self,
        name: str,
        dims: list[str],
        *,
        metadata: dict[str, object] | None = None,
    ) -> SemanticType:
        """Build array storage, bounds, axes, and layout from already-parsed dimensions."""
        strided_axes = [_STRIDED_DIMENSION_SENTINEL in dim for dim in dims]
        dims, category, source_shape, lower_bounds, upper_bounds = _PyiAstParser._flat_array_dimensions(dims)
        if not dims:
            category = SCALAR_STORAGE_CATEGORY
        if dims == ["..."]:
            category = "assumed_rank"
            source_shape = [".."]

        rank = 1 if category == "assumed_rank" else len(dims)
        array = SemanticArrayContract(
            rank=rank,
            shape=list(dims),
            order=self._array_order_for_dimensions(category, rank, source_shape),
            axes=["strided" if strided else "dense" for strided in strided_axes],
            contiguous=not any(strided_axes),
            category=category,
            source_shape=source_shape,
            lower_bounds=lower_bounds,
            upper_bounds=upper_bounds,
        )
        storage = SemanticStorageContract(kind="array", array=array)
        return SemanticType(
            name=name,
            rank=rank or 0,
            dtype=name,
            shape=list(dims) if rank is not None else [],
            constraints=[],
            metadata=dict(metadata or {}),
            storage=storage,
        )

    @staticmethod
    def _flat_array_dimensions(
        dims: list[str],
    ) -> tuple[list[str], str | None, list[str], list[str | None], list[str | None]]:
        """Normalize ``Flat`` placement and derive shape, category, and bounds metadata."""
        if not dims:
            return [], SCALAR_STORAGE_CATEGORY, [], [], []
        if _FLAT_DIMENSION_SENTINEL not in dims:
            source_shape = (
                [] if any(dim in {":", "..."} or _STRIDED_DIMENSION_SENTINEL in dim for dim in dims) else list(dims)
            )
            lower_bounds, upper_bounds = _PyiAstParser._bounds_from_source_shape(source_shape)
            return (
                [dim.replace(_STRIDED_DIMENSION_SENTINEL, "Strided") for dim in dims],
                None,
                source_shape,
                lower_bounds,
                upper_bounds,
            )
        if (
            dims.count(_FLAT_DIMENSION_SENTINEL) != 1
            or "..." in dims
            or dims.index(_FLAT_DIMENSION_SENTINEL) not in {0, len(dims) - 1}
        ):
            raise ValueError("Flat must appear exactly once at the first or final concrete array dimension")
        source_shape = ["*" if dim == _FLAT_DIMENSION_SENTINEL else dim for dim in dims]
        lower_bounds, upper_bounds = _PyiAstParser._bounds_from_source_shape(source_shape)
        return (
            [":" if dim == _FLAT_DIMENSION_SENTINEL else dim for dim in dims],
            "assumed_size",
            source_shape,
            lower_bounds,
            upper_bounds,
        )

    def _array_order_for_dimensions(
        self,
        category: str | None,
        rank: int | None,
        source_shape: list[str],
    ) -> str | None:
        """Choose the declared default layout for a concrete multidimensional array."""
        if rank is None or rank <= 1:
            return None
        if category == "assumed_size":
            return _PyiAstParser._flat_array_order(source_shape, rank)
        return "ORDER_F" if self.native_language == "fortran" else "ORDER_C"

    @staticmethod
    def _flat_array_order(source_shape: list[str], rank: int | None) -> str | None:
        """Infer flat-array layout from whether its ``*`` dimension is first or final."""
        if rank is None or rank <= 1 or "*" not in source_shape:
            return None
        return "ORDER_C" if source_shape.index("*") == 0 else "ORDER_F"

    def _character_type(self, node: ast.Subscript, *, allow_deferred_length: bool = False) -> SemanticType:
        """Load a fixed or allowed deferred ``String`` length annotation."""
        items = self.subscript_items(node)
        if len(items) != 1 or (isinstance(items[0], ast.Constant) and items[0].value is Ellipsis):
            raise ValueError("Fixed character types use String[length]; use String for non-fixed length")
        if isinstance(items[0], ast.Slice):
            length = self.dimension_text(items[0])
            if allow_deferred_length and length == ":":
                return SemanticType(
                    name="String",
                    dtype="String",
                    metadata={"fortran_character_length": ":"},
                )
            raise ValueError(
                "String[:] is ambiguous; use String for scalar non-fixed length, "
                "String[:][:] for an array of non-fixed strings, or String[n] for fixed length"
            )
        length = self.dimension_text(items[0])
        return SemanticType(
            name="String",
            dtype="String",
            metadata={"fortran_character_length": length},
        )

    def apply_annotation_metadata(self, semantic_type: SemanticType, node: ast.expr) -> None:
        """Apply one ``Annotated`` metadata AST item to a semantic type in place.

        Imported contract markers update recognized storage or policy-input
        metadata; other names become user constraints.  Unsupported expressions
        fail rather than silently discarding contract information.
        """
        if isinstance(node, ast.Name):
            name = self.contract_name(node)
            if name is None:
                self._append_constraint_metadata(semantic_type, node.id, [])
            elif not self._apply_metadata_name(semantic_type, name):
                self._append_constraint_metadata(semantic_type, name, [])
            return
        if isinstance(node, ast.Call):
            self._apply_annotation_metadata_call(semantic_type, node)
            return
        raise ValueError(f"Unsupported Annotated metadata: {ast.unparse(node)!r}")

    def _apply_annotation_metadata_call(self, semantic_type: SemanticType, node: ast.Call) -> None:
        """Dispatch one callable metadata form, mutating type metadata or constraints."""
        helper = self._annotation_metadata_call_helper(semantic_type, node)
        if helper is None:
            return
        if helper in {
            "FortranType",
            "FortranCallback",
            "LowerBounds",
            "SourceDims",
            "SourceShape",
            "UpperBounds",
        }:
            raise ValueError(f"{helper} metadata is no longer part of the semantic .pyi contract")
        if helper == "PointerAssociation":
            self._apply_pointer_association_metadata(semantic_type, node)
            return
        if helper == "PointerPolicy":
            self._apply_pointer_policy_metadata(semantic_type, node)
            return
        if helper in {"Ownership", "Transfer", "Destruction"}:
            self._apply_ownership_annotation_metadata(semantic_type, node, helper)
            return
        if helper == "ArrayCategory":
            self._require_array_storage(semantic_type).category = str(ast.literal_eval(node.args[0]))
            return
        if node.keywords:
            raise ValueError(f"Constraint metadata expects positional arguments only: {ast.unparse(node)!r}")
        self._append_constraint_metadata(
            semantic_type,
            helper,
            [ast.literal_eval(arg) for arg in node.args],
        )

    def _annotation_metadata_call_helper(self, semantic_type: SemanticType, node: ast.Call) -> str | None:
        """Resolve a metadata helper name, applying an unimported user constraint directly."""
        helper = self.contract_name(node.func)
        if helper is not None:
            return helper
        if not isinstance(node.func, ast.Name):
            return self.required_name(node.func)
        if node.func.id in CONTRACT_SYMBOLS:
            raise ValueError(f"Expected imported prik contract helper: {ast.unparse(node.func)!r}")
        self._apply_user_constraint_metadata_call(semantic_type, node)
        return None

    def _apply_user_constraint_metadata_call(self, semantic_type: SemanticType, node: ast.Call) -> None:
        """Append a positional user-defined constraint call to a semantic type."""
        if not isinstance(node.func, ast.Name):
            raise ValueError(f"Expected user constraint name: {ast.unparse(node)!r}")
        if node.keywords:
            raise ValueError(f"Constraint metadata expects positional arguments only: {ast.unparse(node)!r}")
        self._append_constraint_metadata(
            semantic_type,
            node.func.id,
            [ast.literal_eval(arg) for arg in node.args],
        )

    @staticmethod
    def _require_single_metadata_argument(node: ast.Call, helper: str):
        """Return a helper's sole literal metadata argument or raise for another call shape."""
        if len(node.args) != 1 or node.keywords:
            raise ValueError(f"{helper} metadata expects one argument: {ast.unparse(node)!r}")
        return ast.literal_eval(node.args[0])

    def _apply_pointer_association_metadata(self, semantic_type: SemanticType, node: ast.Call) -> None:
        """Record a pointer-association fact and mark the type as a Fortran pointer."""
        value = self._require_single_metadata_argument(node, "PointerAssociation")
        semantic_type.metadata["fortran_pointer_association"] = str(value)
        semantic_type.metadata["fortran_pointer"] = True

    @staticmethod
    def _apply_pointer_policy_metadata(semantic_type: SemanticType, node: ast.Call) -> None:
        """Validate ``PointerPolicy`` keywords and delegate their metadata update in place."""
        if node.args:
            raise ValueError(f"PointerPolicy metadata accepts keyword arguments only: {ast.unparse(node)!r}")
        values = {}
        for keyword in node.keywords:
            if keyword.arg is None:
                raise ValueError("PointerPolicy metadata does not accept ** expansion")
            if keyword.arg in values:
                raise ValueError(f"PointerPolicy metadata repeats {keyword.arg!r}")
            values[keyword.arg] = ast.literal_eval(keyword.value)
        set_pointer_policy_metadata(semantic_type.metadata, **values)

    def _apply_ownership_annotation_metadata(self, semantic_type: SemanticType, node: ast.Call, helper: str) -> None:
        """Store one declared ownership, transfer, or destruction policy input on a type."""
        value = str(self._require_single_metadata_argument(node, helper))
        set_ownership_metadata(
            semantic_type.metadata,
            owner=value if helper == "Ownership" else None,
            transfer=value if helper == "Transfer" else None,
            destruction=value if helper == "Destruction" else None,
        )

    def _apply_metadata_name(self, semantic_type: SemanticType, name: str) -> bool:
        """Apply one known bare metadata marker and report whether it was recognized.

        Array layout/copy facts and policy inputs update ``semantic_type`` in
        place.  The boolean lets the caller preserve unknown imported names as
        ordinary constraints while contradictions raise immediately.
        """
        if name in {"ORDER_C", "ORDER_F", "ORDER_ANY"}:
            array = self._require_array_storage(semantic_type)
            if array.rank is None or array.rank <= 1:
                raise ValueError(f"{name} requires a multidimensional array")
            expected_order = self._flat_array_order(array.source_shape, array.rank)
            if expected_order is not None and name != expected_order:
                raise ValueError(f"{name} conflicts with {expected_order} implied by Flat placement")
            default_order = self._array_order_for_dimensions(array.category, array.rank, array.source_shape)
            if expected_order is None and name == default_order:
                raise ValueError(
                    f"{name} is implicit for {self.native_language} semantic .pyi contracts; remove the annotation"
                )
            array.order = name
            return True
        if name == "COPY_F":
            self._require_array_storage(semantic_type).copy_order = "ORDER_F"
            return True
        if name == "Allocatable":
            raise ValueError(
                "Annotated[..., Allocatable] is not an active array descriptor spelling; use Allocatable[T[...]]"
            )
        if name == "Pointer":
            raise ValueError("Annotated[..., Pointer] is not an active array descriptor spelling; use Pointer[T[...]]")
        if name == "Contiguous":
            self._require_array_storage(semantic_type).contiguous = True
            return True
        if name == "Immutable":
            semantic_type.metadata[PYTHON_VALUE_MUTABILITY_METADATA] = PYTHON_VALUE_IMMUTABLE
            return True
        if name == "MaybeUnallocated":
            semantic_type.metadata[MAYBE_UNALLOCATED_METADATA] = True
            return True
        if name == "FortranAllocatable":
            semantic_type.metadata["fortran_allocatable"] = True
            return True
        if name == "Aliased":
            semantic_type.metadata["aliased"] = True
            semantic_type.metadata["fortran_target"] = True
            return True
        if name == "AssumedType":
            semantic_type.metadata["fortran_assumed_type"] = True
            return True
        if name == "Polymorphic":
            semantic_type.metadata["fortran_polymorphic"] = True
            return True
        return False

    @staticmethod
    def _validate_array_copy_metadata(semantic_type: SemanticType) -> None:
        """Fail closed on representation-copy forms outside the first dense lane."""
        storage = semantic_type.storage
        array = storage.array if storage is not None else None
        if array is None or array.copy_order is None:
            return
        if array.rank is None or array.rank <= 1:
            raise ValueError("COPY_F requires a concrete multidimensional array rank")
        if array.copy_order != "ORDER_F" or array.order != "ORDER_C":
            raise ValueError("COPY_F requires a C-order Python array and targets Fortran order")
        if array.category in {"assumed_size", "assumed_rank"} or array.contiguous is not True:
            raise ValueError("COPY_F initially supports only dense concrete-shape arrays")
        if semantic_type.name == "String" or native_array_descriptor_kind(semantic_type) is not None:
            raise ValueError("COPY_F does not apply to character arrays or native descriptor handles")

    @staticmethod
    def _append_constraint_metadata(
        semantic_type: SemanticType,
        name: str,
        arguments: list[object],
    ) -> None:
        """Append validated user constraint metadata, rejecting obsolete built-in spellings."""
        if name == "Constant":
            raise ValueError("Constant metadata is not supported; use Final[...]")
        if name == "Shape":
            raise ValueError("Shape metadata is not supported; put dimensions inside T[...]")
        semantic_type.constraints.append(SemanticConstraint(name=name, arguments=arguments))

    @staticmethod
    def _validate_python_value_policy(semantic_type: SemanticType, *, writable: bool, owner: str) -> None:
        """Reject the unsupported writable immutable borrowed-view policy combination."""
        if semantic_type.metadata.get(PYTHON_VALUE_MUTABILITY_METADATA) != PYTHON_VALUE_IMMUTABLE:
            return
        if not writable:
            return
        policy = semantic_type.metadata.get(OWNERSHIP_POLICY_METADATA)
        transfer = policy.get("transfer") if isinstance(policy, dict) else None
        if transfer != "borrowed_view":
            return
        raise ValueError(
            f"Invalid .pyi contract for {owner}: Immutable values cannot request "
            'Transfer("borrowed_view") for writable native storage. Use a projected '
            "replacement return or remove Immutable."
        )

    @staticmethod
    def _require_array_storage(semantic_type: SemanticType) -> SemanticArrayContract:
        """Ensure a semantic type owns array storage and return that mutable contract."""
        if semantic_type.storage is None:
            semantic_type.storage = SemanticStorageContract(kind="array")
        if semantic_type.storage.array is None:
            semantic_type.storage.array = SemanticArrayContract(
                rank=semantic_type.rank,
                shape=list(semantic_type.shape),
            )
        return semantic_type.storage.array

    @staticmethod
    def _bounds_from_source_shape(shape: list[str]) -> tuple[list[str | None], list[str | None]]:
        """Derive normalized lower and upper bounds from source dimension text."""
        lower_bounds: list[str | None] = []
        upper_bounds: list[str | None] = []
        for dim in shape:
            token = str(dim).strip()
            if ":" in token:
                lower, upper = token.split(":", 1)
                lower_text = lower.strip() or None
                lower_bounds.append(None if lower_text == "1" else lower_text)
                upper_bounds.append(upper.strip() or None)
            elif token == "*":
                lower_bounds.append(None)
                upper_bounds.append("*")
            else:
                lower_bounds.append(None)
                upper_bounds.append(None)
        return lower_bounds, upper_bounds

    @staticmethod
    def _type_uses_writable_storage(semantic_type: SemanticType) -> bool:
        """Report whether a type's existing storage can be written by native code."""
        storage = semantic_type.storage
        if storage is None:
            return False
        return storage.kind in {"reference", "array", "pointer", "callback", "address"} and not storage.read_only

    def _is_addr_call(self, node: ast.Call) -> bool:
        """Recognize imported ``Addr`` calls, including explicit address-depth subscripts."""
        return self.matches_name(node.func, "Addr") or (
            isinstance(node.func, ast.Subscript) and self.matches_name(node.func.value, "Addr")
        )

    @staticmethod
    def _addr_depth(node: ast.AST) -> int:
        """Return an ``Addr`` pointer depth, rejecting the redundant depth-one form."""
        if isinstance(node, ast.Subscript):
            depth = int(ast.literal_eval(node.slice))
            if depth <= 1:
                raise ValueError("Addr[1](...) is invalid; use Addr(...)")
            return depth
        return 1

    def _is_array_subscript(self, node: ast.Subscript) -> bool:
        """Distinguish dimension subscriptions from contract metadata subscriptions."""
        if isinstance(node.value, ast.Subscript):
            return self._is_array_subscript(node.value)
        items = self.subscript_items(node)
        if not items:
            return True
        if any(isinstance(item, ast.Slice | ast.Constant) for item in items):
            return True
        if any(
            isinstance(item, ast.Name)
            and (
                self.contract_name(item) is None
                or self.contract_name(item) not in self._non_dimension_subscription_names()
            )
            for item in items
        ):
            return True
        if any(
            isinstance(item, ast.Call) and self.contract_name(item.func) in self._non_dimension_subscription_names()
            for item in items
        ):
            return False
        if any(isinstance(item, ast.Call) for item in items):
            return True
        return any(
            isinstance(item, ast.BinOp | ast.UnaryOp | ast.BoolOp | ast.Compare | ast.IfExp)
            or (isinstance(item, ast.Attribute | ast.Subscript) and is_public_declaration_expression(ast.unparse(item)))
            for item in items
        )

    @staticmethod
    def _non_dimension_subscription_names() -> set[str]:
        """Return imported helper names that cannot be interpreted as array dimensions."""
        return {
            "Allocatable",
            "Constant",
            "Contiguous",
            "COPY_F",
            "Aliased",
            "Immutable",
            "Ownership",
            "ORDER_ANY",
            "ORDER_C",
            "ORDER_F",
            "Pointer",
            "PointerAssociation",
            "PointerPolicy",
            "Shape",
            "Transfer",
            "Destruction",
        }

    def dimension_text(self, node: ast.expr) -> str:
        """Render one validated array-dimension AST item into canonical source text."""
        if isinstance(node, ast.Constant) and node.value is Ellipsis:
            return "..."
        if isinstance(node, ast.Slice):
            return self.slice_text(node)
        if isinstance(node, ast.Constant):
            return str(node.value)
        if self.matches_name(node, "Flat"):
            return _FLAT_DIMENSION_SENTINEL
        expression = ast.unparse(node)
        if not is_public_declaration_expression(expression):
            raise ValueError(f"Unsupported array dimension expression: {expression!r}")
        return expression

    def slice_text(self, node: ast.Slice) -> str:
        """Render one dimension slice, preserving the contract's strided marker."""
        lower = "" if node.lower is None else ast.unparse(node.lower)
        upper = "" if node.upper is None else ast.unparse(node.upper)
        step = ""
        if node.step is not None:
            step = _STRIDED_DIMENSION_SENTINEL if self.matches_name(node.step, "Strided") else ast.unparse(node.step)
        if step:
            return f"{lower}:{upper}:{step}"
        return f"{lower}:{upper}"

    # Callback and result conversion

    def _prototype_argument_spec(self, node: ast.expr) -> _PrototypeArgumentSpec:
        """Convert one prototype annotation into exact direction and transport facts."""
        if isinstance(node, ast.Call):
            wrapper = self.contract_name(node.func)
            if wrapper in {"In", "Out", "InOut"}:
                if len(node.args) != 1 or node.keywords:
                    raise ValueError(f"{wrapper} expects one prototype argument type")
                nested = self._prototype_argument_spec(node.args[0])
                if nested.intent is not None:
                    raise ValueError("prototype intent wrappers cannot be nested")
                intent = {"In": "in", "Out": "out", "InOut": "inout"}[wrapper]
                return _PrototypeArgumentSpec(nested.semantic_type, nested.passes_by_value, intent)
        return self._prototype_transport_spec(node)

    def _prototype_transport_spec(self, node: ast.expr) -> _PrototypeArgumentSpec:
        """Convert the transport-bearing inner type of one prototype dummy."""
        if isinstance(node, ast.Call):
            wrapper = self.contract_name(node.func)
            if wrapper == "Value":
                if len(node.args) != 1 or node.keywords:
                    raise ValueError("Value expects one callback argument type")
                semantic_type = self.semantic_type(node.args[0])
                if semantic_type.rank > 0:
                    raise ValueError("Value(...) callback arguments must be scalar")
                if self._is_primitive_scalar_value_type(semantic_type):
                    raise ValueError(
                        "Value(...) is unnecessary for primitive callback arguments; "
                        "bare primitive types are passed by value"
                    )
                if (
                    semantic_type.name == "String"
                    or semantic_type.storage is not None
                    or self._has_callback_descriptor_metadata(semantic_type)
                ):
                    raise ValueError("Value(...) callback arguments are only valid for rank-zero wrapped types")
                return _PrototypeArgumentSpec(semantic_type, True)
            if self._is_addr_call(node):
                return self._prototype_address_argument_spec(node)

        semantic_type = self.semantic_type(node)
        if self._is_primitive_scalar_value_type(semantic_type):
            return _PrototypeArgumentSpec(semantic_type, True)
        self._mark_callback_reference_type(semantic_type)
        return _PrototypeArgumentSpec(semantic_type, False)

    def _prototype_address_argument_spec(self, node: ast.Call) -> _PrototypeArgumentSpec:
        """Parse the prototype-only primitive reference marker."""
        if len(node.args) != 1 or node.keywords:
            raise ValueError(f"Addr type expects one callback argument type: {ast.unparse(node)!r}")
        if self._addr_depth(node.func) != 1:
            raise ValueError("Addr[...](...) is not supported inside prototype declarations; use Addr(T)")
        semantic_type = self.semantic_type(node.args[0])
        if not self._is_primitive_scalar_value_type(semantic_type):
            raise ValueError(
                "Addr(...) inside prototype declarations is only valid for primitive scalar reference dummies; "
                "arrays, strings, and wrapped objects already use reference storage"
            )
        self._mark_callback_reference_type(semantic_type)
        return _PrototypeArgumentSpec(semantic_type, False)

    @staticmethod
    def _is_primitive_scalar_value_type(semantic_type: SemanticType) -> bool:
        """Report whether a callback type is a plain native scalar passed by value."""
        return bool(
            semantic_type.rank == 0
            and semantic_type.name not in {"String", "Void"}
            and (semantic_type.dtype or semantic_type.name) in SEMANTIC_SCALAR_TYPE_NAMES
            and semantic_type.storage is None
            and not _PyiAstParser._has_callback_descriptor_metadata(semantic_type)
        )

    @staticmethod
    def _has_callback_descriptor_metadata(semantic_type: SemanticType) -> bool:
        """Report whether callback metadata requires non-value storage treatment."""
        return any(
            semantic_type.metadata.get(name)
            for name in (
                "fortran_allocatable",
                "fortran_pointer",
                "fortran_polymorphic",
                "fortran_assumed_type",
            )
        )

    @staticmethod
    def _mark_callback_reference_type(semantic_type: SemanticType) -> None:
        """Mutate a callback argument type into writable reference-compatible storage."""
        storage = semantic_type.storage
        if semantic_type.name == "String" and semantic_type.rank == 0:
            semantic_type.storage = SemanticStorageContract(
                kind="array",
                read_only=False,
                mutable=True,
                array=SemanticArrayContract(rank=0, shape=[], category=SCALAR_STORAGE_CATEGORY),
            )
        elif storage is None:
            semantic_type.storage = SemanticStorageContract(
                kind="reference",
                read_only=False,
                mutable=True,
                pointer_depth=1,
            )
        else:
            storage.read_only = False
            storage.mutable = True
        semantic_type.ownership.mutable = True

    @staticmethod
    def _semantic_shape_dimensions(semantic_type: SemanticType) -> list[tuple[str, bool]]:
        """Return semantic shape dimensions paired with their strided-axis markers."""
        storage = semantic_type.storage
        array = storage.array if storage is not None else None
        dimensions = list(semantic_type.shape)
        if not dimensions and array is not None:
            dimensions = list(array.shape)
        axes = list(array.axes) if array is not None else []
        if len(axes) != len(dimensions):
            axes = ["dense"] * len(dimensions)
        return [(str(dimension), axis == "strided") for dimension, axis in zip(dimensions, axes, strict=True)]

    @staticmethod
    def _callback_metadata(arguments: list[SemanticType] | None, return_type: SemanticType) -> dict[str, object]:
        """Build the fixed callback ABI metadata dictionary from signature semantic types."""
        return {
            "arguments": arguments,
            "return": return_type,
            "fortran_callback_kind": "subroutine" if return_type.name == "None" else "function",
            "callback_lifetime": "call",
            "callback_thread": "entering_thread",
            "callback_exception": "print_traceback_and_abort",
        }

    @staticmethod
    def _callback_storage() -> SemanticStorageContract:
        """Return the standard borrowed, call-lifetime storage contract for a callback."""
        return SemanticStorageContract(
            kind="callback",
            ownership="borrowed",
            calling_convention="fortran_dummy_procedure",
        )

    def return_projection(
        self,
        node: ast.expr,
        *,
        optional_return_positions: set[int] | None = None,
    ) -> tuple[SemanticType | None, list[SemanticArgument]]:
        """Split a stub return annotation into direct and projected semantic results.

        The first plain result is the direct function result; later plain items
        and every ``Returns[name, T]`` item become ordered output arguments.
        Nullable result slots are retained only where native projections allow
        them, and the resulting list preserves source tuple order.
        """
        if isinstance(node, ast.Constant) and node.value is None:
            return None, []

        return_type: SemanticType | None = None
        returned_args: list[SemanticArgument] = []
        plain_return_index = 0
        optional_positions = optional_return_positions or set()

        for item_index, item in enumerate(self.return_items(node)):
            returned_optional = self._optional_union_item(item)
            returned_item = returned_optional or item
            returned = self.returned_argument(returned_item)
            if returned is not None:
                returned.optional = returned.optional or returned_optional is not None
                returned.metadata["return_position"] = item_index
                returned_args.append(returned)
                continue

            semantic_type, optional = self._return_item_type(
                item,
                unwrap_optional=item_index in optional_positions,
            )
            if item_index == 0:
                if optional:
                    semantic_type.metadata[_PYI_OPTIONAL_RETURN_METADATA] = True
                return_type = semantic_type
            else:
                returned_args.append(
                    SemanticArgument(
                        name=f"__return_{plain_return_index}",
                        semantic_type=semantic_type,
                        optional=optional,
                        metadata={"return_position": item_index},
                    )
                )
            plain_return_index += 1

        return return_type, returned_args

    def _return_item_type(self, node: ast.expr, *, unwrap_optional: bool) -> tuple[SemanticType, bool]:
        """Load one return item and report whether an allowed ``| None`` was unwrapped."""
        if not unwrap_optional:
            return self.semantic_type(node), False
        optional_node = self._optional_union_item(node)
        if optional_node is None:
            return self.semantic_type(node), False
        return self.semantic_type(optional_node), True

    @staticmethod
    def _optional_union_item(node: ast.expr) -> ast.expr | None:
        """Return the non-``None`` item of a two-way optional union, if present."""
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.BitOr):
            return None
        left_none = isinstance(node.left, ast.Constant) and node.left.value is None
        right_none = isinstance(node.right, ast.Constant) and node.right.value is None
        if left_none == right_none:
            return None
        return node.right if left_none else node.left

    def returned_argument(self, node: ast.expr) -> SemanticArgument | None:
        """Convert ``Returns[name, T]`` into a mutable output argument, or return ``None``."""
        if not self.is_subscript_of(node, "Returns"):
            return None
        items = self.subscript_items(node)
        if len(items) != 2:
            raise ValueError(
                f"Returns expects a name and type; use '| None' for nullable returns: {ast.unparse(node)!r}"
            )

        semantic_type = self.semantic_type(items[1])
        semantic_type.ownership.mutable = True
        return SemanticArgument(
            name=str(ast.literal_eval(items[0])),
            semantic_type=semantic_type,
        )

    def name_metadata(self, node: ast.expr) -> str | None:
        """Return the native name from supported ``SourceName`` metadata, if any."""
        if isinstance(node, ast.Call) and self.matches_name(node.func, "SourceName"):
            if len(node.args) != 1:
                raise ValueError(f"SourceName metadata expects one argument: {ast.unparse(node)!r}")
            return str(ast.literal_eval(node.args[0]))
        return None

    @staticmethod
    def annotation_target(node: ast.AST) -> str:
        """Return an assignment target name, including the supported ``var[...]`` escape."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "var":
            return str(ast.literal_eval(node.slice))
        raise ValueError(f"Unsupported annotation target: {ast.unparse(node)!r}")

    @staticmethod
    def default_marks_optional(node: ast.expr | None) -> bool:
        """Report whether an ellipsis or ``None`` default marks a contract value optional."""
        return isinstance(node, ast.Constant) and node.value in {Ellipsis, None}

    @staticmethod
    def literal_default_value(node: ast.expr | None) -> str | None:
        """Validate and render an immutable literal default, returning ``None`` for optional defaults."""
        if node is None or _PyiAstParser.default_marks_optional(node):
            return None
        try:
            ast.literal_eval(node)
        except (ValueError, SyntaxError):
            raise ValueError(f"Mutable defaults must be literal values: {ast.unparse(node)!r}") from None
        return ast.unparse(node)

    @staticmethod
    def assignment_default_value(node: ast.expr | None, semantic_type: SemanticType) -> str | None:
        """Render an assignment default, allowing non-literals only for ``Final`` constants."""
        if node is None or _PyiAstParser.default_marks_optional(node):
            return None
        if any(constraint.name == "Constant" for constraint in semantic_type.constraints):
            return ast.unparse(node)
        return _PyiAstParser.literal_default_value(node)

    @staticmethod
    def qualified_name(node: ast.AST) -> tuple[str, ...] | None:
        """Return a dotted name's components, or ``None`` for an unsupported AST expression."""
        if isinstance(node, ast.Name):
            return (node.id,)
        if isinstance(node, ast.Attribute):
            parent = _PyiAstParser.qualified_name(node.value)
            if parent is None:
                return None
            return (*parent, node.attr)
        return None

    def contract_name(self, node: ast.AST) -> str | None:
        """Resolve one local name through the contract-import bindings without mutation."""
        if not isinstance(node, ast.Name):
            return None
        return self._contract_bindings.get(node.id)

    def matches_name(self, node: ast.AST, name: str) -> bool:
        """Report whether an AST name resolves to a particular imported contract symbol."""
        return self.contract_name(node) == name

    @staticmethod
    def matches_plain_name(node: ast.AST, name: str) -> bool:
        """Report whether an AST node is exactly an unqualified Python name."""
        return isinstance(node, ast.Name) and node.id == name

    def required_name(self, node: ast.AST) -> str:
        """Resolve an imported contract helper or raise a closed diagnostic for other names."""
        name = self.contract_name(node)
        if name is None:
            raise ValueError(f"Expected imported prik contract helper: {ast.unparse(node)!r}")
        return name

    def is_subscript_of(self, node: ast.AST, name: str) -> bool:
        """Report whether a subscript uses one particular imported contract helper."""
        return isinstance(node, ast.Subscript) and self.matches_name(node.value, name)

    @staticmethod
    def subscript_slice(node: ast.AST) -> ast.expr:
        """Return a subscript's slice or reject expressions that are not subscriptions."""
        if not isinstance(node, ast.Subscript):
            raise ValueError(f"Unsupported type annotation: {ast.unparse(node)!r}")
        return node.slice

    def subscript_items(self, node: ast.AST) -> list[ast.expr]:
        """Return a subscript slice as a one-or-many list while preserving tuple order."""
        value = self.subscript_slice(node)
        if isinstance(value, ast.Tuple):
            return list(value.elts)
        return [value]

    def type_name(self, node: ast.AST) -> str:
        """Render a type base name while replacing imported aliases with contract names."""
        if isinstance(node, ast.Subscript):
            contract_name = self.contract_name(node.value)
            return contract_name or ast.unparse(node.value)
        contract_name = self.contract_name(node)
        if contract_name is not None:
            return contract_name
        return ast.unparse(node)

    # Callable construction

    def _callable_parts(
        self,
        node: ast.FunctionDef,
        *,
        projection: list[ProjectionMapping],
        native_result: ProjectionMapping | None = None,
        drop_untyped_self: bool = False,
    ) -> tuple[list[SemanticArgument], SemanticType | None]:
        """Build a callable's arguments, results, and native projection metadata.

        The ordered stages validate the stub header, load typed arguments,
        apply input projection storage, construct direct and projected results,
        and then complete mapping names.  ``projection`` is intentionally
        mutated when identity mappings are required for ``Returns`` syntax.
        """
        # Validate and load the callable's visible input contract.
        self._validate_callable_header(node)
        semantic_args = self._callable_semantic_arguments(node, projection, drop_untyped_self=drop_untyped_self)
        visible_args = list(semantic_args)
        self._apply_argument_value_projections(visible_args, projection)
        self._apply_argument_descriptor_projections(visible_args, projection)

        # Construct direct and projected outputs from the Python return shape.
        optional_return_positions = self._optional_native_return_positions(projection, native_result)
        return_type, returned_args = self.return_projection(
            node.returns,
            optional_return_positions=optional_return_positions,
        )
        self._validate_callable_descriptor_return(return_type, native_result)
        return_type, returned_args = self._apply_native_call_returns(return_type, returned_args, projection)
        return_type = self._apply_native_result_projection(return_type, native_result)

        # Complete native output placement and the mapping's visible names.
        return_positions = self._return_positions_by_name(returned_args)
        self._apply_projected_returns(semantic_args, returned_args)
        if returned_args and not projection:
            projection.extend(self._identity_return_projection(semantic_args, visible_args, return_positions))
        self._apply_native_call_argument_names(visible_args, return_positions, projection)
        return semantic_args, return_type

    def _validate_callable_header(self, node: ast.FunctionDef) -> None:
        """Validate the supported semantic `.pyi` callable header shape."""
        self._validate_stub_callable(node)
        if node.returns is None:
            if getattr(node, "end_lineno", node.lineno) != node.lineno:
                raise ValueError(f"Unterminated callable starting at line {node.lineno}")
            raise ValueError(f"Unsupported function header: {_node_text(node)!r}")
        if node.args.vararg or node.args.kwarg or node.args.kwonlyargs or node.args.posonlyargs:
            raise ValueError(f"Unsupported function header: {_node_text(node)!r}")

    def _callable_semantic_arguments(
        self,
        node: ast.FunctionDef,
        projection: list[ProjectionMapping],
        *,
        drop_untyped_self: bool,
    ) -> list[SemanticArgument]:
        """Load callable arguments and enforce scalar descriptor projection syntax."""
        args = list(zip(node.args.args, self._argument_defaults(node), strict=False))
        if drop_untyped_self and args and args[0][0].arg == "self":
            args = args[1:]
        descriptor_positions = self._descriptor_argument_positions(projection)
        semantic_args = [
            self._callable_argument(arg, default, nullable_descriptor=index in descriptor_positions)
            for index, (arg, default) in enumerate(args)
        ]
        self._validate_callable_descriptor_arguments(semantic_args, descriptor_positions)
        return semantic_args

    @staticmethod
    def _descriptor_argument_positions(projection: list[ProjectionMapping]) -> set[int]:
        """Return Python argument positions wrapped by descriptor projections."""
        return {
            mapping.python_position
            for mapping in projection
            if mapping.value_kind in {"allocatable", "pointer"} and mapping.python_position is not None
        }

    def _validate_callable_descriptor_arguments(
        self,
        arguments: list[SemanticArgument],
        descriptor_positions: set[int],
    ) -> None:
        """Reject descriptor type wrappers on callable Python annotations."""
        for index, argument in enumerate(arguments):
            if index in descriptor_positions:
                continue
            if self._semantic_scalar_descriptor_kind(argument.semantic_type) is not None:
                raise ValueError(
                    "Procedure scalar descriptors use nullable value annotations plus "
                    "Allocatable(Arg(i)) or Pointer(Arg(i)) in native_call"
                )

    @staticmethod
    def _optional_native_return_positions(
        projection: list[ProjectionMapping],
        native_result: ProjectionMapping | None,
    ) -> set[int]:
        """Return nullable result slots and reject duplicate native producers."""
        positions = {
            mapping.result_position
            for mapping in projection
            if mapping.result_position is not None and mapping.python_position is None
        }
        if native_result is None or native_result.result_position is None:
            return positions
        if native_result.result_position in positions:
            raise ValueError(
                f"native_call result slot {native_result.result_position} is also used by a native output argument"
            )
        positions.add(native_result.result_position)
        return positions

    def _validate_callable_descriptor_return(
        self,
        return_type: SemanticType | None,
        native_result: ProjectionMapping | None,
    ) -> None:
        """Reject descriptor type wrappers on callable Python return annotations."""
        if native_result is None and self._semantic_scalar_descriptor_kind(return_type) is not None:
            raise ValueError(
                "Procedure scalar descriptor results use a nullable value annotation plus "
                "native_call result=Allocatable(Return(0)) or result=Pointer(Return(0))"
            )

    def _callable_argument(
        self,
        arg: ast.arg,
        default: ast.expr | None,
        *,
        nullable_descriptor: bool = False,
    ) -> SemanticArgument:
        """Convert one typed stub parameter into a semantic argument declaration.

        Nullable descriptor arguments are unwrapped only when their projection
        requires them.  The returned argument records visibility, optionality,
        and writable storage facts; contradictory optional-handle policies fail.
        """
        if arg.annotation is None:
            raise ValueError(f"Expected typed argument: {arg.arg!r}")
        annotation = arg.annotation
        if nullable_descriptor:
            annotation = self._optional_union_item(annotation)
            if annotation is None:
                raise ValueError(
                    f"Scalar descriptor argument {arg.arg!r} must use a nullable annotation such as Float64 | None"
                )
        elif (optional_annotation := self._optional_union_item(annotation)) is not None:
            optional_type = self.semantic_type(optional_annotation)
            if self.contract_name(optional_annotation) is None and native_array_descriptor_kind(optional_type) is None:
                annotation = optional_annotation
        visibility, semantic_type, original_name = self.visible_type(
            annotation,
            allow_optional_absent_handle=True,
        )
        self._validate_optional_native_array_handle_argument(arg, default, semantic_type)
        writable = self._type_uses_writable_storage(semantic_type)
        semantic_type.ownership.mutable = writable
        if semantic_type.storage is not None:
            semantic_type.storage.mutable = writable
        self._validate_python_value_policy(semantic_type, writable=writable, owner=arg.arg)
        return SemanticArgument(
            name=original_name or arg.arg,
            semantic_type=semantic_type,
            optional=self.default_marks_optional(default),
            visibility=visibility,
            origin=self._origin(user_private=visibility == "private"),
        )

    def _validate_optional_native_array_handle_argument(
        self,
        arg: ast.arg,
        default: ast.expr | None,
        semantic_type: SemanticType,
    ) -> None:
        """Require consistent nullable spelling and default syntax for array handles."""
        descriptor_kind = native_array_descriptor_kind(semantic_type)
        if descriptor_kind is None:
            return
        has_optional_absence = bool(semantic_type.metadata.get(OPTIONAL_ABSENT_HANDLE_METADATA))
        has_optional_default = self.default_marks_optional(default)
        if has_optional_absence and not has_optional_default:
            raise ValueError(
                f"Native array handle argument {arg.arg!r} uses '| None' for an absent optional dummy, "
                "so it must use '= ...' or '= None'"
            )
        if has_optional_default and not has_optional_absence:
            wrapper = "Allocatable" if descriptor_kind == "allocatable" else "Pointer"
            raise ValueError(
                f"Optional native array handle argument {arg.arg!r} must use {wrapper}[T[...]] | None = ..."
            )

    def _apply_argument_descriptor_projections(
        self,
        arguments: list[SemanticArgument],
        projection: list[ProjectionMapping],
    ) -> None:
        """Apply scalar allocatable/pointer projection kinds to referenced arguments in place."""
        for mapping in projection:
            if mapping.value_kind not in {"allocatable", "pointer"} or mapping.python_position is None:
                continue
            if not 0 <= mapping.python_position < len(arguments):
                raise ValueError(f"native_call argument position is out of range: {mapping.python_position}")
            self._apply_scalar_descriptor_kind(arguments[mapping.python_position].semantic_type, mapping.value_kind)

    @staticmethod
    def _apply_argument_value_projections(
        arguments: list[SemanticArgument],
        projection: list[ProjectionMapping],
    ) -> None:
        """Record exact typed value transport on the projected argument."""
        for mapping in projection:
            if mapping.value_kind != "value" or mapping.python_position is None:
                continue
            if not 0 <= mapping.python_position < len(arguments):
                raise ValueError(f"native_call argument position is out of range: {mapping.python_position}")
            argument = arguments[mapping.python_position]
            semantic_type = argument.semantic_type
            if (
                semantic_type.rank != 0
                or semantic_type.name in SEMANTIC_SCALAR_TYPE_NAMES
                or semantic_type.name == "String"
            ):
                raise ValueError(
                    "Value(Arg(i)) is only valid for exact rank-zero wrapped derived objects; "
                    "primitive scalars already use Arg(i) value passing"
                )
            argument.metadata[NATIVE_BY_VALUE_METADATA] = True

    @staticmethod
    def _semantic_scalar_descriptor_kind(semantic_type: SemanticType | None) -> str | None:
        """Return the declared scalar descriptor kind, excluding arrays and plain values."""
        if semantic_type is None or semantic_type.rank != 0:
            return None
        if semantic_type.metadata.get("fortran_allocatable"):
            return "allocatable"
        if semantic_type.metadata.get("fortran_pointer"):
            return "pointer"
        return None

    def _apply_native_result_projection(
        self,
        return_type: SemanticType | None,
        native_result: ProjectionMapping | None,
    ) -> SemanticType | None:
        """Apply the nullable scalar descriptor mapping to the direct result type."""
        if native_result is None:
            return return_type
        if return_type is None:
            raise ValueError("native_call result requires a native function result in Python result slot 0")
        if not return_type.metadata.pop(_PYI_OPTIONAL_RETURN_METADATA, False):
            raise ValueError("native scalar descriptor function result must use a nullable T | None annotation")
        self._apply_scalar_descriptor_kind(return_type, native_result.value_kind)
        return return_type

    @staticmethod
    def _argument_defaults(node: ast.FunctionDef) -> list[ast.expr | None]:
        """Align positional parameter defaults with every declared positional argument."""
        defaults: list[ast.expr | None] = [None] * (len(node.args.args) - len(node.args.defaults))
        defaults.extend(node.args.defaults)
        return defaults

    @staticmethod
    def _validate_stub_callable(node: ast.FunctionDef) -> None:
        """Require the semantic-contract stub body to consist solely of an ellipsis."""
        if len(node.body) != 1:
            raise ValueError(f"Unsupported function header: {_node_text(node)!r}")
        body = node.body[0]
        if not (isinstance(body, ast.Expr) and isinstance(body.value, ast.Constant) and body.value.value is Ellipsis):
            raise ValueError(f"Unsupported function header: {_node_text(node)!r}")

    @staticmethod
    def _apply_projected_returns(semantic_args: list[SemanticArgument], returned_args: list[SemanticArgument]) -> None:
        """Merge ``Returns`` outputs into native arguments and mark their storage writable."""
        by_name = {arg.name: arg for arg in semantic_args}
        for returned in returned_args:
            existing = by_name.get(returned.name)
            if existing is None:
                _PyiAstParser._mark_projected_output(returned.semantic_type)
                returned.metadata[PROJECTED_OUTPUT_METADATA] = True
                returned.metadata.pop("return_position", None)
                native_position = returned.metadata.pop("native_position", None)
                if isinstance(native_position, int) and 0 <= native_position <= len(semantic_args):
                    semantic_args.insert(native_position, returned)
                else:
                    semantic_args.append(returned)
                continue
            existing.metadata[PROJECTED_OUTPUT_METADATA] = True
            _PyiAstParser._mark_projected_output(existing.semantic_type)

    @staticmethod
    def _mark_projected_output(semantic_type: SemanticType) -> None:
        """Mutate a projected result type so later stages see writable output storage."""
        semantic_type.ownership.mutable = True
        if semantic_type.storage is not None:
            semantic_type.storage.read_only = False
            semantic_type.storage.mutable = True

    @staticmethod
    def _identity_return_projection(
        semantic_args: list[SemanticArgument],
        visible_args: list[SemanticArgument],
        return_positions: dict[str, int | None],
    ) -> list[ProjectionMapping]:
        """Reconstruct native-order identity mappings for `Returns[...]` syntax."""
        visible_positions = {argument.name: position for position, argument in enumerate(visible_args)}
        return [
            ProjectionMapping(
                python_name=argument.name,
                native_name=argument.name,
                native_position=native_position,
                python_position=visible_positions.get(argument.name),
                result_position=return_positions.get(argument.name),
            )
            for native_position, argument in enumerate(semantic_args)
        ]

    @classmethod
    def _apply_native_call_returns(
        cls,
        return_type: SemanticType | None,
        returned_args: list[SemanticArgument],
        projection: list[ProjectionMapping],
    ) -> tuple[SemanticType | None, list[SemanticArgument]]:
        """Move native-call output mappings from Python result slots into output arguments."""
        output_by_result = {
            mapping.result_position: mapping
            for mapping in projection
            if mapping.result_position is not None and mapping.python_position is None
        }
        return_type = cls._apply_direct_native_call_return(return_type, returned_args, output_by_result.get(0))
        cls._apply_named_native_call_returns(returned_args, output_by_result)
        return return_type, returned_args

    @classmethod
    def _apply_direct_native_call_return(
        cls,
        return_type: SemanticType | None,
        returned_args: list[SemanticArgument],
        mapping: ProjectionMapping | None,
    ) -> SemanticType | None:
        """Move a direct Python return into a projected native output argument."""
        if return_type is None or mapping is None:
            return return_type
        cls._complete_native_output_mapping_name(mapping)
        return_type.ownership.mutable = True
        nullable_output = bool(return_type.metadata.pop(_PYI_OPTIONAL_RETURN_METADATA, False))
        descriptor_output = cls._apply_descriptor_output_kind(return_type, mapping, nullable=nullable_output)
        if not descriptor_output and return_type.rank == 0 and return_type.storage is None:
            return_type.storage = SemanticStorageContract(
                kind="address",
                mutable=True,
                pointer_depth=1,
                metadata={ADDRESS_ROLE_METADATA: ADDRESS_ROLE_PROJECTION},
            )
        returned_args.insert(
            0,
            SemanticArgument(
                name=mapping.native_name or f"__return_{mapping.result_position}",
                semantic_type=return_type,
                optional=nullable_output and not descriptor_output,
                metadata={"native_position": mapping.native_position},
            ),
        )
        return None

    @classmethod
    def _apply_named_native_call_returns(
        cls,
        returned_args: list[SemanticArgument],
        output_by_result: dict[int | None, ProjectionMapping],
    ) -> None:
        """Apply native output mappings to named Python result slots."""
        for returned in returned_args:
            position = returned.metadata.get("return_position")
            mapping = output_by_result.get(position)
            if mapping is None:
                continue
            cls._complete_native_output_mapping_name(mapping)
            if mapping.native_name:
                returned.name = mapping.native_name
            cls._mark_projected_output(returned.semantic_type)
            descriptor_output = cls._apply_descriptor_output_kind(
                returned.semantic_type,
                mapping,
                nullable=returned.optional,
            )
            if descriptor_output:
                returned.optional = False
            returned.metadata["native_position"] = mapping.native_position

    @staticmethod
    def _complete_native_output_mapping_name(mapping: ProjectionMapping) -> None:
        """Complete a projected output's Python name from its native name."""
        if mapping.native_name and not mapping.python_name:
            mapping.python_name = mapping.native_name

    @classmethod
    def _apply_descriptor_output_kind(
        cls,
        semantic_type: SemanticType,
        mapping: ProjectionMapping,
        *,
        nullable: bool,
    ) -> bool:
        """Apply nullable descriptor facts to one projected output type."""
        if mapping.value_kind not in {"allocatable", "pointer"}:
            return False
        if not nullable:
            raise ValueError("native scalar descriptor output must use a nullable T | None annotation")
        cls._apply_scalar_descriptor_kind(semantic_type, mapping.value_kind)
        return True

    @staticmethod
    def _return_positions_by_name(returned_args: list[SemanticArgument]) -> dict[str, int | None]:
        """Index projected return names by their original tuple result positions."""
        return {returned.name: returned.metadata.get("return_position") for returned in returned_args}

    @staticmethod
    def _apply_native_call_argument_names(
        semantic_args: list[SemanticArgument],
        return_positions: dict[str, int | None],
        projection: list[ProjectionMapping],
    ) -> None:
        """Complete projection names and output slots from their referenced semantic arguments."""
        for mapping in projection:
            if mapping.python_position is None:
                continue
            if not 0 <= mapping.python_position < len(semantic_args):
                raise ValueError(f"native_call argument position is out of range: {mapping.python_position}")
            arg = semantic_args[mapping.python_position]
            mapping.python_name = arg.name
            if not mapping.native_name:
                mapping.native_name = arg.name
            if arg.metadata.get(PROJECTED_OUTPUT_METADATA) and mapping.result_position is None:
                mapping.result_position = return_positions.get(arg.name)

    @staticmethod
    def _shift_argument_value_ref(
        mapping: ProjectionMapping,
        old_position: int,
        new_position: int,
    ) -> None:
        """Update an embedded argument value reference after a preceding insertion."""
        if mapping.value_kind not in {"addr", "allocatable", "pointer", "value"} or not isinstance(mapping.value, dict):
            return
        if mapping.value.get("kind") == "arg" and mapping.value.get("position") == old_position:
            mapping.value["position"] = new_position

    def return_items(self, node: ast.expr) -> list[ast.expr]:
        """Flatten supported ``tuple[...]`` returns, otherwise keep one return expression."""
        if isinstance(node, ast.Subscript) and (
            self.matches_plain_name(node.value, "tuple") or self.matches_plain_name(node.value, "Tuple")
        ):
            return self.subscript_items(node)
        return [node]


# AST visitor adapters


class _ClassBodyVisitor(ClassVisitor):
    """Collect declarations from one class body before constructing its semantic class."""

    def __init__(self, parser: _PyiAstParser, *, class_name: str):
        """Initialize empty class members and constructor/overload bookkeeping state."""
        self.parser = parser
        self.class_name = class_name
        self.fields: list[SemanticField] = []
        self.methods: list[SemanticMethod] = []
        self.pending_overloads: list[tuple[SemanticMethod, str, str | None]] = []
        self.classes: list[SemanticClass] = []
        self.constructor_from_fields = False
        self.has_bound_constructor = False

    def _walk_nodes(self, nodes: list[ast.stmt]) -> None:
        """Visit each statement in one class body."""
        for node in nodes:
            self._visit(node)

    def _visit_Pass(self, node: ast.Pass) -> None:
        """Accept an empty class-body placeholder."""
        pass

    def _visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Convert an annotated class field declaration."""
        self.fields.append(self.parser.ann_assign(node, binding_cls=SemanticField))

    def _visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Convert a method, constructor, or overload declaration."""
        decorators = self.parser.decorators(node.decorator_list, context="class body")
        if decorators.standalone:
            raise ValueError("standalone is not valid for a class method")
        if decorators.native_type is not None:
            raise ValueError("native_type is only valid for classes")
        if not node.decorator_list and self._is_generated_constructor(node):
            self.constructor_from_fields = True
            return
        if node.name == "__init__" and decorators.bind_target is None and decorators.overload_target is None:
            raise ValueError('Non-generated __init__ declarations must use @bind("specific_name")')
        if (
            node.name == "__init__"
            and decorators.bind_target is not None
            and node.args.args
            and node.args.args[0].arg == "self"
            and node.args.args[0].annotation is not None
        ):
            raise ValueError("Bound constructor declarations omit the native self argument")
        method = self.parser.method_def(
            node,
            visibility=decorators.visibility,
            projection=decorators.projection,
            native_result=decorators.native_result,
            is_static=decorators.is_static,
            native_name=decorators.bind_target,
            class_name=self.class_name,
            infer_passed_object=decorators.overload_target is None,
            has_native_call=decorators.has_native_call,
            release_gil=decorators.release_gil,
            error_status_policy=decorators.error_status_policy,
        )
        if node.name == "__init__" and decorators.bind_target is not None and decorators.overload_target is None:
            self.has_bound_constructor = True
        if decorators.overload_target is not None:
            self.pending_overloads.append((method, decorators.overload_target, decorators.overload_generic))
        else:
            self.methods.append(method)

    @staticmethod
    def _is_generated_constructor(node: ast.FunctionDef) -> bool:
        """Recognize the printer's self-only or all-default-keyword constructor stub."""
        args = node.args
        if (
            node.name == "__init__"
            and len(args.args) == 1
            and args.args[0].arg == "self"
            and args.args[0].annotation is None
            and not args.defaults
            and not args.kwonlyargs
            and not args.vararg
            and not args.kwarg
            and not args.posonlyargs
        ):
            return True
        return (
            node.name == "__init__"
            and len(args.args) == 1
            and args.args[0].arg == "self"
            and args.args[0].annotation is None
            and not args.defaults
            and bool(args.kwonlyargs)
            and all(default is not None for default in args.kw_defaults)
            and not args.vararg
            and not args.kwarg
            and not args.posonlyargs
        )

    def _visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Convert a nested class declaration."""
        decorators = self.parser.decorators(node.decorator_list, context="class body")
        if (
            decorators.has_native_call
            or decorators.bind_target is not None
            or decorators.release_gil
            or decorators.error_status_policy is not None
            or decorators.standalone
        ):
            raise ValueError(f"Unsupported class body decorator: {ast.unparse(node.decorator_list[-1])!r}")
        if (
            len(node.bases) == 1
            and isinstance(node.bases[0], ast.Subscript)
            and self.parser.matches_plain_name(node.bases[0].value, "Enum")
        ):
            raise ValueError(
                f"Enum declarations are not supported; use Final[...] integer constants: {_node_text(node)!r}"
            )
        self.classes.append(
            self.parser.class_def(
                node,
                visibility=decorators.visibility,
                native_type=decorators.native_type,
            )
        )

    @staticmethod
    def _visit_not_supported(node: ast.AST) -> None:
        """Reject unsupported class-body syntax."""
        raise ValueError(f"Unsupported class body node: {_node_text(node)!r}")


class _ModuleVisitor(ClassVisitor):
    """Dispatch supported top-level AST nodes into a parser's mutable semantic module."""

    def __init__(self, parser: _PyiAstParser):
        """Keep the parser whose module receives visited top-level declarations."""
        self.parser = parser

    def _visit_Module(self, node: ast.Module) -> None:
        """Visit all top-level declarations in source order."""
        self.parser.register_user_type_names(node)
        for item in node.body:
            self._visit(item)

    def _visit_Import(self, node: ast.Import) -> None:
        """Convert a direct import declaration."""
        self.parser.module.imports.append(self.parser.import_name(node))

    def _visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Convert a from-import declaration."""
        if self.parser.register_contract_import(node):
            return
        semantic_import = self.parser.import_from(node)
        if semantic_import.module == "typing" and any(item.source == "overload" for item in semantic_import.items):
            raise ValueError('typing.overload is not supported; use prik @overload("specific")')
        self.parser.module.imports.append(semantic_import)

    def _visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Convert a module variable declaration."""
        self.parser.module.variables.append(self.parser.ann_assign(node))

    def _visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Convert a semantic class declaration."""
        decorators = self.parser.decorators(node.decorator_list, context="class")
        if (
            decorators.has_native_call
            or decorators.bind_target is not None
            or decorators.release_gil
            or decorators.error_status_policy is not None
            or decorators.standalone
        ):
            raise ValueError(f"Unsupported class decorator: {ast.unparse(node.decorator_list[-1])!r}")
        if (
            len(node.bases) == 1
            and isinstance(node.bases[0], ast.Subscript)
            and self.parser.matches_plain_name(node.bases[0].value, "Enum")
        ):
            raise ValueError(
                f"Enum declarations are not supported; use Final[...] integer constants: {_node_text(node)!r}"
            )
        self.parser.module.classes.append(
            self.parser.class_def(
                node,
                visibility=decorators.visibility,
                native_type=decorators.native_type,
            )
        )

    def _visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Convert a function or overload declaration."""
        decorators = self.parser.decorators(node.decorator_list, context=".pyi")
        if decorators.native_type is not None:
            raise ValueError("native_type is only valid for classes")
        if decorators.prototype:
            self.parser.module.prototypes.append(
                self.parser.prototype_def(
                    node,
                    visibility=decorators.visibility,
                    pure=decorators.pure,
                )
            )
            return
        function = self.parser.function_def(
            node,
            visibility=decorators.visibility,
            projection=decorators.projection,
            native_result=decorators.native_result,
            native_name=decorators.bind_target,
            standalone=decorators.standalone,
            has_native_call=decorators.has_native_call,
            release_gil=decorators.release_gil,
            error_status_policy=decorators.error_status_policy,
        )
        if decorators.overload_target is not None:
            self.parser._pending_overloads.append(
                _PendingOverload(
                    self.parser.module,
                    function,
                    decorators.overload_target,
                    decorators.overload_generic,
                )
            )
        else:
            self.parser.module.functions.append(function)

    @staticmethod
    def _visit_not_supported(node: ast.AST) -> None:
        """Reject unsupported top-level `.pyi` syntax."""
        raise ValueError(f"Unsupported .pyi node: {_node_text(node)!r}")


# Cross-module reference reconciliation


def _node_text(node: ast.AST) -> str:
    """Render the first line of an AST node for concise validation diagnostics."""
    text = ast.unparse(node)
    return text.splitlines()[0] if text else type(node).__name__


def _annotate_imported_external_type_refs(module: SemanticModule) -> None:
    """Mark types named by imports as unresolved external references in place.

    The function reads module imports and semantic types, adds default reference
    metadata only when absent, and leaves cross-module representation resolution
    to :func:`reconcile_external_type_refs`.
    """
    imported = _imported_type_refs(module)
    for semantic_type in _iter_module_semantic_types(module):
        imported_ref = imported.get(semantic_type.name)
        if imported_ref is None:
            continue
        origin_module, source_name, local_name = imported_ref
        semantic_type.metadata.setdefault(
            EXTERNAL_TYPE_REF_METADATA,
            {
                "name": source_name,
                "local_name": local_name,
                "origin_module": origin_module,
                "wrapped": False,
                "representation": "opaque",
            },
        )


def _imported_type_refs(module: SemanticModule) -> dict[str, tuple[str, str, str]]:
    """Index direct and dotted imported type spellings by local semantic type name."""
    imported: dict[str, tuple[str, str, str]] = {}
    imported_namespaces: dict[str, str] = {}
    for imp in module.imports:
        if isinstance(imp, SemanticImport):
            for item in imp.items:
                local_name = item.target or item.source
                imported[local_name] = (imp.module, item.source, local_name)
                if imp.module.startswith("."):
                    imported_namespaces[local_name] = _relative_imported_namespace(imp.module, item.source)
            continue
        for item in imp.split(","):
            module_name, _, alias = item.strip().partition(" as ")
            visible_name = alias or module_name
            imported[visible_name] = (module_name, visible_name, visible_name)
            imported_namespaces[visible_name] = module_name

    for semantic_type in _iter_module_semantic_types(module):
        if "." not in semantic_type.name:
            continue
        module_name, type_name = semantic_type.name.rsplit(".", 1)
        visible_module = module_name.split(".", 1)[0]
        imported_module = imported_namespaces.get(visible_module)
        if imported_module is not None:
            imported[semantic_type.name] = (imported_module, type_name, semantic_type.name)
    return imported


def _relative_imported_namespace(module_name: str, source_name: str) -> str:
    """Join a relative import's namespace and imported name without package context."""
    module_path = module_name.lstrip(".")
    if not module_path:
        return source_name
    return f"{module_path}.{source_name}"


def _bind_prototype_reference(
    semantic_type: SemanticType,
    prototype: SemanticPrototype,
    *,
    origin_module: str,
    source_name: str,
) -> None:
    """Complete one type annotation as a named callback prototype reference."""
    local_name = semantic_type.name
    arguments = deepcopy(prototype.arguments)
    return_type = deepcopy(prototype.return_type) or SemanticType("None", dtype="None")
    semantic_type.dtype = "Prototype"
    semantic_type.metadata = {
        "arguments": [argument.semantic_type for argument in arguments],
        "callback_arguments": arguments,
        "return": return_type,
        "callback_lifetime": "call",
        "callback_thread": "entering_thread",
        "callback_exception": "print_traceback_and_abort",
        "prototype_metadata": deepcopy(prototype.metadata),
        "native_callback_kind": "subroutine" if return_type.name == "None" else "function",
        PROTOTYPE_REF_METADATA: {
            "name": source_name,
            "local_name": local_name,
            "origin_module": origin_module,
        },
    }
    semantic_type.storage = SemanticStorageContract(
        kind="callback",
        ownership="borrowed",
        calling_convention="native_dummy_procedure",
    )
    semantic_type.origin = SemanticOrigin(
        native_name=source_name,
        native_scope=origin_module,
        source_kind="prototype_reference",
    )


def reconcile_external_type_refs(modules: list[SemanticModule]) -> list[SemanticModule]:
    """Resolve imported class and prototype references across converted modules.

    Use this for a complete batch after each module has passed
    :func:`convert_pyi_to_ir`.  The input list and referenced type metadata are
    mutated in place: matching prototypes become callback references, while
    classes are marked ``wrapped`` or ``opaque``.  The same list is returned for
    pipeline chaining; absent external definitions remain opaque references.
    """
    definitions = {(module.name, declaration.name): declaration for module in modules for declaration in module.classes}
    prototypes = {(module.name, prototype.name): prototype for module in modules for prototype in module.prototypes}
    functions = {(module.name, function.name): function for module in modules for function in module.functions}
    for module in modules:
        for semantic_type in _iter_module_semantic_types(module):
            ref = semantic_type.metadata.get(EXTERNAL_TYPE_REF_METADATA)
            if not isinstance(ref, dict):
                continue
            origin_module = ref.get("origin_module")
            source_name = ref.get("name")
            if isinstance(origin_module, str) and isinstance(source_name, str):
                module_candidates = (
                    origin_module,
                    origin_module.lstrip("."),
                    origin_module.lstrip(".").rsplit(".", 1)[-1],
                )
                prototype = next(
                    (
                        candidate_prototype
                        for candidate in module_candidates
                        if candidate and (candidate_prototype := prototypes.get((candidate, source_name))) is not None
                    ),
                    None,
                )
                if prototype is not None:
                    _bind_prototype_reference(
                        semantic_type,
                        prototype,
                        origin_module=str(prototype.origin.native_scope or origin_module.lstrip(".")),
                        source_name=source_name,
                    )
                    continue
            declaration = definitions.get((ref.get("origin_module"), ref.get("name")))
            wrapped = declaration is not None and (
                not isinstance(declaration, SemanticClass) or "Opaque" not in declaration.base_classes
            )
            ref["wrapped"] = wrapped
            ref["representation"] = "wrapped" if wrapped else "opaque"
        _reconcile_declaration_expression_callables(module, prototypes, functions)
    return modules


def _reconcile_declaration_expression_callables(
    module: SemanticModule,
    prototypes: dict[tuple[str, str], SemanticPrototype],
    functions: dict[tuple[str, str], SemanticFunction],
) -> None:
    """Link imported declaration calls to exact batch declarations when present."""
    for reference in _unresolved_declaration_expression_callables(module):
        scopes = _declaration_callable_scope_candidates(reference.native_scope)
        native_name = reference.native_name or reference.name.rsplit(".", 1)[-1]
        prototype = _declaration_callable_prototype(prototypes, scopes, native_name)
        if prototype is not None:
            _bind_declaration_expression_callable(reference, prototype, native_scope=None, placement="standalone")
            continue
        function_match = _declaration_callable_function(functions, scopes, native_name)
        if function_match is not None:
            function, native_scope = function_match
            _bind_declaration_expression_callable(reference, function, native_scope=native_scope, placement="module")


def _unresolved_declaration_expression_callables(module: SemanticModule):
    """Yield imported array-expression callables that still need batch binding.

    The semantic module remains unmodified while traversing. References that
    already have a declaration or lack a native scope are intentionally omitted
    because their provenance is complete or explicitly unresolved.
    """
    for semantic_type in _iter_module_semantic_types(module):
        storage = semantic_type.storage
        array = storage.array if storage is not None else None
        if array is None:
            continue
        for references in array.expression_callables:
            for reference in references:
                if reference.declaration is None and reference.native_scope is not None:
                    yield reference


def _declaration_callable_scope_candidates(native_scope: str) -> tuple[str, str, str]:
    """Return the exact, relative-stripped, and leaf module spellings to match."""
    return (
        native_scope,
        native_scope.lstrip("."),
        native_scope.lstrip(".").rsplit(".", 1)[-1],
    )


def _declaration_callable_prototype(
    prototypes: dict[tuple[str, str], SemanticPrototype],
    scopes: tuple[str, str, str],
    native_name: str,
) -> SemanticPrototype | None:
    """Return the first prototype matching the established scope-candidate order."""
    for scope in scopes:
        prototype = prototypes.get((scope, native_name))
        if scope and prototype is not None:
            return prototype
    return None


def _declaration_callable_function(
    functions: dict[tuple[str, str], SemanticFunction],
    scopes: tuple[str, str, str],
    native_name: str,
) -> tuple[SemanticFunction, str] | None:
    """Return the first matching function together with its resolved module scope."""
    for scope in scopes:
        function = functions.get((scope, native_name))
        if scope and function is not None:
            return function, scope
    return None


def _bind_declaration_expression_callable(
    reference: SemanticExpressionCallable,
    declaration: SemanticPrototype | SemanticFunction,
    *,
    native_scope: str | None,
    placement: str,
) -> None:
    """Mutate one expression reference with its resolved declaration provenance."""
    reference.declaration = declaration
    reference.native_name = declaration.native_name or declaration.name
    reference.native_scope = native_scope
    reference.placement = placement


if __name__ == "__main__":
    from prik.parsers.pyi import parse_pyi_text

    contract = """from prik.contracts import Float64

def scale(value: Float64) -> Float64: ...
"""
    parsed_contract = parse_pyi_text(contract, filename="math.pyi")
    semantic_module = convert_pyi_to_ir(parsed_contract, module_name="math", source=contract)
    semantic_function = semantic_module.functions[0]
    semantic_argument = semantic_function.arguments[0]
    print(
        f"{semantic_module.name}.{semantic_function.name}"
        f"({semantic_argument.name}): {semantic_argument.semantic_type.name}"
        f" -> {semantic_function.return_type.name}"
    )
