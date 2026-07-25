from __future__ import annotations

import ast
import re
from copy import deepcopy
from dataclasses import dataclass, field

from x2py.contracts import CONTRACT_SYMBOLS, CONTRACT_TYPE_NAMES
from x2py.types.numpy import SEMANTIC_SCALAR_TYPE_NAMES
from x2py.semantics.ownership import OWNERSHIP_POLICY_METADATA, set_ownership_metadata, set_pointer_policy_metadata
from x2py.semantics.metadata import (
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
from x2py.semantics.native_array_handles import mark_native_array_handle, native_array_descriptor_kind
from x2py.utilities.visitor import ClassVisitor

from .models import (
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
    RUNTIME_HOLD_GIL_METADATA,
    RUNTIME_STATUS_ERROR_METADATA,
    ProjectionMapping,
    ProcedureOverloadSet,
    SemanticArgument,
    SemanticArrayContract,
    SemanticClass,
    SemanticConstraint,
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
_CONTRACT_MODULE = "x2py.contracts"
_FLAT_DIMENSION_SENTINEL = "@x2py.Flat"
_STRIDED_DIMENSION_SENTINEL = "@x2py.Strided"


@dataclass(frozen=True)
class _CallbackArgumentSpec:
    semantic_type: SemanticType
    passes_by_value: bool


def convert_pyi_to_ir(
    tree: ast.Module,
    *,
    module_name: str = "<pyi>",
    source: str = "",
    native_language: str = "fortran",
) -> SemanticModule:
    """Convert a parsed semantic `.pyi` AST into semantic IR."""

    if not isinstance(tree, ast.Module):
        raise TypeError("convert_pyi_to_ir expects a Python ast.Module parsed by x2py.parsers.pyi")
    module = _PyiAstParser(
        module_name=module_name,
        source=source,
        native_language=native_language,
    ).parse(tree)
    _annotate_imported_external_type_refs(module)
    return module


@dataclass
class _Decorators:
    visibility: str = "public"
    projection: list[ProjectionMapping] = field(default_factory=list)
    native_result: ProjectionMapping | None = None
    has_native_call: bool = False
    overload_target: str | None = None
    overload_generic: str | None = None
    bind_target: str | None = None
    native_type: dict[str, object] | None = None
    external: bool = False
    is_static: bool = False
    hold_gil: bool = False
    error_status_policy: dict[str, object] | None = None
    prototype: bool = False


@dataclass
class _PendingOverload:
    owner: SemanticModule | SemanticClass
    declaration: SemanticFunction
    target: str
    generic_name: str | None = None


class _PyiAstParser:
    def __init__(self, *, module_name: str, source: str = "", native_language: str = "fortran"):
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
        _ModuleVisitor(self)._visit(tree)
        self._resolve_overloads()
        self._restore_type_bound_targets()
        self._resolve_local_prototype_references()
        return self.module

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

    def import_from(self, node: ast.ImportFrom) -> SemanticImport:
        module_name = "." * node.level + (node.module or "")
        return SemanticImport(
            module=module_name,
            items=[SemanticImportItem(source=alias.name, target=alias.asname) for alias in node.names],
        )

    def register_contract_import(self, node: ast.ImportFrom) -> bool:
        module_name = "." * node.level + (node.module or "")
        if module_name != _CONTRACT_MODULE:
            return False
        for alias in node.names:
            if alias.name == "*":
                raise ValueError("x2py.contracts does not support wildcard imports")
            if alias.name not in CONTRACT_SYMBOLS:
                raise ValueError(f"Unknown x2py contract name {alias.name!r}")
            local_name = alias.asname or alias.name
            previous = self._contract_bindings.get(local_name)
            if previous is not None and previous != alias.name:
                raise ValueError(f"Contract import name {local_name!r} is bound more than once")
            self._contract_bindings[local_name] = alias.name
        return True

    def import_name(self, node: ast.Import) -> str:
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
        self._validate_bound_constructor_targets(semantic_class)
        self._pending_overloads.extend(
            _PendingOverload(semantic_class, declaration, target, generic_name)
            for declaration, target, generic_name in body.pending_overloads
        )
        return semantic_class

    @staticmethod
    def _validate_bound_constructor_targets(semantic_class: SemanticClass) -> None:
        for constructor in semantic_class.methods:
            target_name = constructor.metadata.get(BIND_TARGET_METADATA)
            if constructor.name != "__init__" or not isinstance(target_name, str):
                continue
            candidates = [
                method for method in semantic_class.methods if method is not constructor and method.name == target_name
            ]
            if not candidates:
                raise ValueError(f"Bound constructor references missing class method {target_name!r}")
            if len(candidates) > 1:
                raise ValueError(f"Bound constructor target {target_name!r} is ambiguous")
            target = candidates[0]
            target_arguments = list(target.arguments)
            if isinstance(target, SemanticMethod) and target.passed_object_position is not None:
                target_arguments.pop(target.passed_object_position)
            if constructor.arguments != target_arguments or constructor.return_type != target.return_type:
                raise ValueError(f"Bound constructor declaration is incompatible with class method {target_name!r}")
            constructor.native_name = target.native_name or target.name

    @staticmethod
    def _class_metadata(base_classes: list[str]) -> dict[str, object]:
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
        external: bool = False,
        has_native_call: bool = False,
        hold_gil: bool = False,
        error_status_policy: dict[str, object] | None = None,
    ) -> SemanticFunction:
        actual_projection = projection if projection is not None else []
        semantic_args, return_type = self._callable_parts(
            node,
            projection=actual_projection,
            native_result=native_result,
        )
        metadata = {BIND_TARGET_METADATA: native_name} if native_name is not None else {}
        if has_native_call:
            metadata[NATIVE_PROJECTION_METADATA] = True
        if hold_gil:
            metadata[RUNTIME_HOLD_GIL_METADATA] = True
        if error_status_policy is not None:
            metadata[RUNTIME_STATUS_ERROR_METADATA] = dict(error_status_policy)
        origin = self._origin(
            source_language="fortran" if external else None,
            user_private=visibility == "private",
        )
        if external:
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

    def prototype_def(self, node: ast.FunctionDef, *, visibility: str) -> SemanticPrototype:
        """Convert one named callback prototype without creating a runtime function."""
        self._validate_callable_header(node)
        arguments = []
        for argument, default in zip(node.args.args, self._argument_defaults(node), strict=False):
            if argument.annotation is None:
                raise ValueError(f"Expected typed prototype argument: {argument.arg!r}")
            spec = self._prototype_argument_spec(argument.annotation)
            arguments.append(
                SemanticArgument(
                    argument.arg,
                    spec.semantic_type,
                    optional=self.default_marks_optional(default),
                    visibility=visibility,
                    origin=SemanticOrigin(metadata={"value": spec.passes_by_value}),
                )
            )
        return_type = (
            SemanticType("None", dtype="None")
            if isinstance(node.returns, ast.Constant) and node.returns.value is None
            else self.semantic_type(node.returns)
        )
        return SemanticPrototype(
            name=node.name,
            native_name=node.name,
            arguments=arguments,
            return_type=return_type,
            visibility=visibility,
            origin=SemanticOrigin(
                native_name=node.name,
                native_scope=self.module.name,
                source_kind="prototype",
            ),
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
        hold_gil: bool = False,
        error_status_policy: dict[str, object] | None = None,
    ) -> SemanticMethod:
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
        if infer_passed_object and not is_static and node.name != "__init__":
            pass_mappings = [mapping for mapping in actual_projection if mapping.value_kind == "pass"]
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
        if hold_gil:
            metadata[RUNTIME_HOLD_GIL_METADATA] = True
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

    def decorators(self, nodes: list[ast.expr], *, context: str) -> _Decorators:
        parsed = _Decorators()
        for node in nodes:
            self._apply_decorator(parsed, node, context=context)
        if parsed.overload_target is not None and parsed.bind_target is not None:
            raise ValueError("bind cannot be combined with overload")
        if parsed.overload_target is not None and parsed.has_native_call:
            raise ValueError("overload cannot be combined with native_call; put native_call on the specific procedure")
        if parsed.prototype and len(nodes) != 1:
            raise ValueError("prototype cannot be combined with other decorators")
        return parsed

    def _apply_decorator(self, parsed: _Decorators, node: ast.expr, *, context: str) -> None:
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
            "external": self._apply_external_decorator,
            "hold_gil": self._apply_hold_gil_decorator,
            "native_call": self._apply_native_call_decorator,
            "native_type": self._apply_native_type_decorator,
            "prototype": self._apply_prototype_decorator,
            "raises": self._apply_raises_decorator,
        }
        handler = next((value for name, value in handlers.items() if self.matches_name(target, name)), None)
        if handler is None:
            raise ValueError(f"Unsupported {context} decorator: {ast.unparse(node)!r}")
        handler(parsed, node, context)

    @staticmethod
    def _apply_prototype_decorator(parsed: _Decorators, node: ast.expr, context: str) -> None:
        if isinstance(node, ast.Call):
            raise ValueError("prototype does not accept arguments")
        if context != ".pyi":
            raise ValueError("prototype is only valid for module-level declarations")
        if parsed.prototype:
            raise ValueError("Duplicate prototype decorator")
        parsed.prototype = True

    def _apply_overload_decorator(self, parsed: _Decorators, node: ast.expr, context: str) -> None:
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
        if not isinstance(node, ast.Call) or len(node.args) != 1 or node.keywords:
            raise ValueError(f"{name} expects one native symbol name")
        target = ast.literal_eval(node.args[0])
        if not isinstance(target, str) or not target:
            raise ValueError(f"{name} expects a non-empty native symbol name")
        return target

    def _apply_bind_decorator(self, parsed: _Decorators, node: ast.expr, context: str) -> None:
        if parsed.bind_target is not None:
            raise ValueError(f"Duplicate {context} bind decorator")
        parsed.bind_target = self._required_string_decorator_argument(node, "bind")

    @staticmethod
    def _apply_hold_gil_decorator(parsed: _Decorators, node: ast.expr, context: str) -> None:
        if isinstance(node, ast.Call):
            raise ValueError("hold_gil does not accept arguments")
        if parsed.hold_gil:
            raise ValueError(f"Duplicate {context} hold_gil decorator")
        parsed.hold_gil = True

    @staticmethod
    def _apply_external_decorator(parsed: _Decorators, node: ast.expr, context: str) -> None:
        if isinstance(node, ast.Call):
            raise ValueError("external does not accept arguments")
        if parsed.external:
            raise ValueError(f"Duplicate {context} external decorator")
        parsed.external = True

    @staticmethod
    def _apply_native_type_decorator(parsed: _Decorators, node: ast.expr, context: str) -> None:
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
        del context
        if not isinstance(node, ast.Call):
            raise ValueError("native_call expects a single list argument")
        parsed.has_native_call = True
        parsed.projection, parsed.native_result = self.native_call(node)

    def _apply_raises_decorator(self, parsed: _Decorators, node: ast.expr, context: str) -> None:
        if not isinstance(node, ast.Call):
            raise ValueError("raises expects keyword arguments")
        if parsed.error_status_policy is not None:
            raise ValueError(f"Duplicate {context} raises decorator")
        parsed.error_status_policy = self.error_status_policy(node)

    def native_call(self, node: ast.Call) -> tuple[list[ProjectionMapping], ProjectionMapping | None]:
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

    def _restore_type_bound_targets(self) -> None:
        """Mark module procedures referenced by type-bound method declarations."""

        by_name = {
            target: function
            for function in self.module.functions
            for target in {function.name, function.native_name}
            if target
        }
        for semantic_class in self._iter_classes(self.module.classes):
            for method in semantic_class.methods:
                if method.is_static or method.passed_object_position is None:
                    continue
                target = by_name.get(method.native_name or method.name)
                if target is None:
                    continue
                passed_position = method.passed_object_position
                if not 0 <= passed_position < len(target.arguments):
                    continue
                target.metadata["fortran_type_bound_target"] = True
                target.metadata["fortran_passed_object_name"] = target.arguments[passed_position].name
                target.metadata["fortran_passed_object_position"] = passed_position
                target.arguments[passed_position].semantic_type.metadata["fortran_polymorphic"] = True

    @classmethod
    def _iter_classes(cls, classes: list[SemanticClass]):
        for semantic_class in classes:
            yield semantic_class
            yield from cls._iter_classes(semantic_class.classes)

    @staticmethod
    def _overload_set_name(owner: SemanticModule | SemanticClass, declaration_name: str) -> str:
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
        candidate = deepcopy(target)
        candidate.visibility = declaration.visibility
        candidate.metadata[OVERLOAD_TARGET_METADATA] = target.name
        for key in (RUNTIME_HOLD_GIL_METADATA, RUNTIME_STATUS_ERROR_METADATA):
            if key in declaration.metadata:
                candidate.metadata[key] = deepcopy(declaration.metadata[key])

        if isinstance(owner, SemanticModule):
            self._validate_overload_signature(declaration, candidate, list(candidate.arguments))
            candidate.metadata[FORTRAN_GENERIC_NAME_METADATA] = generic_name or declaration.name
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
        visible = deepcopy(argument)
        visible.semantic_type = _PyiAstParser._visible_overload_type(argument.semantic_type)
        return visible

    @staticmethod
    def _visible_overload_type(semantic_type: SemanticType | None) -> SemanticType | None:
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

    def native_projection_entry(self, node: ast.AST, native_position: int) -> ProjectionMapping:
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
        if len(node.args) != 1:
            raise ValueError("Arg expects one positional index")
        return ProjectionMapping(
            native_position=native_position,
            python_position=int(ast.literal_eval(node.args[0])),
        )

    @staticmethod
    def _native_return_projection_entry(node: ast.Call, native_position: int) -> ProjectionMapping:
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
        if node.args:
            raise ValueError("Pass does not accept arguments")
        return ProjectionMapping(
            native_position=native_position,
            value_kind="pass",
        )

    def _native_len_projection_entry(self, node: ast.Call, native_position: int) -> ProjectionMapping:
        if len(node.args) != 1:
            raise ValueError("Len expects one value reference")
        return ProjectionMapping(
            native_position=native_position,
            value_kind="len",
            value=self.native_value_ref(node.args[0]),
        )

    def _native_is_present_projection_entry(self, node: ast.Call, native_position: int) -> ProjectionMapping:
        if len(node.args) != 1:
            raise ValueError("IsPresent expects one value reference")
        return ProjectionMapping(
            native_position=native_position,
            value_kind="is_present",
            value=self.native_value_ref(node.args[0]),
        )

    @staticmethod
    def _native_work_projection_entry(node: ast.Call, native_position: int) -> ProjectionMapping:
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
        items = self.subscript_items(node)
        if len(items) != 1:
            raise ValueError("native_call string literals require exactly one String length")
        item = items[0]
        if isinstance(item, ast.Slice) or (isinstance(item, ast.Constant) and item.value is Ellipsis):
            raise ValueError("native_call string literals require a fixed String length")
        return self.dimension_text(item)

    def native_address_projection_entry(self, node: ast.Call, native_position: int) -> ProjectionMapping:
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

    def visible_type(
        self,
        node: ast.expr,
        *,
        allow_optional_absent_handle: bool = False,
    ) -> tuple[str, SemanticType, str | None]:
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
        name_node = node.value if isinstance(node, ast.Subscript) else node
        if not isinstance(name_node, ast.Name):
            return
        if self.contract_name(name_node) is not None:
            return
        if name_node.id not in CONTRACT_TYPE_NAMES or name_node.id in self._user_type_names:
            return
        raise ValueError(f"Contract type {name_node.id!r} must be imported from x2py.contracts")

    def _descriptor_type(self, node: ast.Subscript, descriptor: str) -> SemanticType:
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
        storage = semantic_type.storage
        if storage is None or storage.array is None or semantic_type.rank <= 0:
            raise ValueError(f"{descriptor}[...] array handles require an array type such as {descriptor}[Float64[:]]")
        descriptor_kind = descriptor.casefold()
        mark_native_array_handle(semantic_type, descriptor_kind)
        return semantic_type

    @staticmethod
    def _apply_scalar_descriptor_kind(semantic_type: SemanticType, descriptor: str) -> None:
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
        items = self.subscript_items(node)
        if len(items) != 1:
            raise ValueError(f"Final expects exactly one type: {ast.unparse(node)!r}")
        semantic_type = self.semantic_type(items[0])
        if not any(constraint.name == "Constant" for constraint in semantic_type.constraints):
            semantic_type.constraints.append(SemanticConstraint("Constant"))
        return semantic_type

    def _address_type(self, node: ast.Call) -> SemanticType:
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
        if not self.source:
            return None
        source = ast.get_source_segment(self.source, node.slice)
        if source is None:
            return None
        return self._split_top_level_dimensions(source)

    @staticmethod
    def _split_top_level_dimensions(source: str) -> list[str]:
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
        parts = text.split(":")
        return len(parts) == 3 and parts[2].strip() == ""

    @staticmethod
    def _strided_dimension_text(text: str) -> str:
        lower, upper, _step = text.split(":", 2)
        return f"{lower.strip()}:{upper.strip()}:{_STRIDED_DIMENSION_SENTINEL}"

    def _array_type_from_dimensions(
        self,
        name: str,
        dims: list[str],
        *,
        metadata: dict[str, object] | None = None,
    ) -> SemanticType:
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
        if rank is None or rank <= 1:
            return None
        if category == "assumed_size":
            return _PyiAstParser._flat_array_order(source_shape, rank)
        return "ORDER_F" if self.native_language == "fortran" else "ORDER_C"

    @staticmethod
    def _flat_array_order(source_shape: list[str], rank: int | None) -> str | None:
        if rank is None or rank <= 1 or "*" not in source_shape:
            return None
        return "ORDER_C" if source_shape.index("*") == 0 else "ORDER_F"

    def _character_type(self, node: ast.Subscript, *, allow_deferred_length: bool = False) -> SemanticType:
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
        helper = self.contract_name(node.func)
        if helper is not None:
            return helper
        if not isinstance(node.func, ast.Name):
            return self.required_name(node.func)
        if node.func.id in CONTRACT_SYMBOLS:
            raise ValueError(f"Expected imported x2py contract helper: {ast.unparse(node.func)!r}")
        self._apply_user_constraint_metadata_call(semantic_type, node)
        return None

    def _apply_user_constraint_metadata_call(self, semantic_type: SemanticType, node: ast.Call) -> None:
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
        if len(node.args) != 1 or node.keywords:
            raise ValueError(f"{helper} metadata expects one argument: {ast.unparse(node)!r}")
        return ast.literal_eval(node.args[0])

    def _apply_pointer_association_metadata(self, semantic_type: SemanticType, node: ast.Call) -> None:
        value = self._require_single_metadata_argument(node, "PointerAssociation")
        semantic_type.metadata["fortran_pointer_association"] = str(value)
        semantic_type.metadata["fortran_pointer"] = True

    @staticmethod
    def _apply_pointer_policy_metadata(semantic_type: SemanticType, node: ast.Call) -> None:
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
        value = str(self._require_single_metadata_argument(node, helper))
        set_ownership_metadata(
            semantic_type.metadata,
            owner=value if helper == "Ownership" else None,
            transfer=value if helper == "Transfer" else None,
            destruction=value if helper == "Destruction" else None,
        )

    def _apply_metadata_name(self, semantic_type: SemanticType, name: str) -> bool:
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
        if name == "Constant":
            raise ValueError("Constant metadata is not supported; use Final[...]")
        if name == "Shape":
            raise ValueError("Shape metadata is not supported; put dimensions inside T[...]")
        semantic_type.constraints.append(SemanticConstraint(name=name, arguments=arguments))

    @staticmethod
    def _validate_python_value_policy(semantic_type: SemanticType, *, writable: bool, owner: str) -> None:
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
        storage = semantic_type.storage
        if storage is None:
            return False
        return storage.kind in {"reference", "array", "pointer", "callback", "address"} and not storage.read_only

    def _is_addr_call(self, node: ast.Call) -> bool:
        return self.matches_name(node.func, "Addr") or (
            isinstance(node.func, ast.Subscript) and self.matches_name(node.func.value, "Addr")
        )

    @staticmethod
    def _addr_depth(node: ast.AST) -> int:
        if isinstance(node, ast.Subscript):
            depth = int(ast.literal_eval(node.slice))
            if depth <= 1:
                raise ValueError("Addr[1](...) is invalid; use Addr(...)")
            return depth
        return 1

    def _is_array_subscript(self, node: ast.Subscript) -> bool:
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
        return any(isinstance(item, ast.BinOp | ast.UnaryOp) for item in items)

    @staticmethod
    def _non_dimension_subscription_names() -> set[str]:
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
        if isinstance(node, ast.Constant) and node.value is Ellipsis:
            return "..."
        if isinstance(node, ast.Slice):
            return self.slice_text(node)
        if isinstance(node, ast.Constant):
            return str(node.value)
        if self.matches_name(node, "Flat"):
            return _FLAT_DIMENSION_SENTINEL
        if isinstance(node, ast.Attribute | ast.Subscript):
            raise ValueError(f"Unsupported array dimension expression: {ast.unparse(node)!r}")
        return ast.unparse(node)

    def slice_text(self, node: ast.Slice) -> str:
        lower = "" if node.lower is None else ast.unparse(node.lower)
        upper = "" if node.upper is None else ast.unparse(node.upper)
        step = ""
        if node.step is not None:
            step = _STRIDED_DIMENSION_SENTINEL if self.matches_name(node.step, "Strided") else ast.unparse(node.step)
        if step:
            return f"{lower}:{upper}:{step}"
        return f"{lower}:{upper}"

    def _prototype_argument_spec(self, node: ast.expr) -> _CallbackArgumentSpec:
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
                return _CallbackArgumentSpec(semantic_type, True)
            if self._is_addr_call(node):
                return self._prototype_address_argument_spec(node)

        semantic_type = self.semantic_type(node)
        if self._is_primitive_scalar_value_type(semantic_type):
            return _CallbackArgumentSpec(semantic_type, True)
        self._mark_callback_reference_type(semantic_type)
        return _CallbackArgumentSpec(semantic_type, False)

    def _prototype_address_argument_spec(self, node: ast.Call) -> _CallbackArgumentSpec:
        """Parse the callback-only primitive reference marker."""
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
        return _CallbackArgumentSpec(semantic_type, False)

    @staticmethod
    def _is_primitive_scalar_value_type(semantic_type: SemanticType) -> bool:
        return bool(
            semantic_type.rank == 0
            and semantic_type.name not in {"String", "Void"}
            and (semantic_type.dtype or semantic_type.name) in SEMANTIC_SCALAR_TYPE_NAMES
            and semantic_type.storage is None
            and not _PyiAstParser._has_callback_descriptor_metadata(semantic_type)
        )

    @staticmethod
    def _has_callback_descriptor_metadata(semantic_type: SemanticType) -> bool:
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
        if not unwrap_optional:
            return self.semantic_type(node), False
        optional_node = self._optional_union_item(node)
        if optional_node is None:
            return self.semantic_type(node), False
        return self.semantic_type(optional_node), True

    @staticmethod
    def _optional_union_item(node: ast.expr) -> ast.expr | None:
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.BitOr):
            return None
        left_none = isinstance(node.left, ast.Constant) and node.left.value is None
        right_none = isinstance(node.right, ast.Constant) and node.right.value is None
        if left_none == right_none:
            return None
        return node.right if left_none else node.left

    def returned_argument(self, node: ast.expr) -> SemanticArgument | None:
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
        if isinstance(node, ast.Call) and self.matches_name(node.func, "SourceName"):
            if len(node.args) != 1:
                raise ValueError(f"SourceName metadata expects one argument: {ast.unparse(node)!r}")
            return str(ast.literal_eval(node.args[0]))
        return None

    @staticmethod
    def annotation_target(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "var":
            return str(ast.literal_eval(node.slice))
        raise ValueError(f"Unsupported annotation target: {ast.unparse(node)!r}")

    @staticmethod
    def default_marks_optional(node: ast.expr | None) -> bool:
        return isinstance(node, ast.Constant) and node.value in {Ellipsis, None}

    @staticmethod
    def literal_default_value(node: ast.expr | None) -> str | None:
        if node is None or _PyiAstParser.default_marks_optional(node):
            return None
        try:
            ast.literal_eval(node)
        except (ValueError, SyntaxError):
            raise ValueError(f"Mutable defaults must be literal values: {ast.unparse(node)!r}") from None
        return ast.unparse(node)

    @staticmethod
    def assignment_default_value(node: ast.expr | None, semantic_type: SemanticType) -> str | None:
        if node is None or _PyiAstParser.default_marks_optional(node):
            return None
        if any(constraint.name == "Constant" for constraint in semantic_type.constraints):
            return ast.unparse(node)
        return _PyiAstParser.literal_default_value(node)

    @staticmethod
    def qualified_name(node: ast.AST) -> tuple[str, ...] | None:
        if isinstance(node, ast.Name):
            return (node.id,)
        if isinstance(node, ast.Attribute):
            parent = _PyiAstParser.qualified_name(node.value)
            if parent is None:
                return None
            return (*parent, node.attr)
        return None

    def contract_name(self, node: ast.AST) -> str | None:
        if not isinstance(node, ast.Name):
            return None
        return self._contract_bindings.get(node.id)

    def matches_name(self, node: ast.AST, name: str) -> bool:
        return self.contract_name(node) == name

    @staticmethod
    def matches_plain_name(node: ast.AST, name: str) -> bool:
        return isinstance(node, ast.Name) and node.id == name

    def required_name(self, node: ast.AST) -> str:
        name = self.contract_name(node)
        if name is None:
            raise ValueError(f"Expected imported x2py contract helper: {ast.unparse(node)!r}")
        return name

    def is_subscript_of(self, node: ast.AST, name: str) -> bool:
        return isinstance(node, ast.Subscript) and self.matches_name(node.value, name)

    @staticmethod
    def subscript_slice(node: ast.AST) -> ast.expr:
        if not isinstance(node, ast.Subscript):
            raise ValueError(f"Unsupported type annotation: {ast.unparse(node)!r}")
        return node.slice

    def subscript_items(self, node: ast.AST) -> list[ast.expr]:
        value = self.subscript_slice(node)
        if isinstance(value, ast.Tuple):
            return list(value.elts)
        return [value]

    def type_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Subscript):
            contract_name = self.contract_name(node.value)
            return contract_name or ast.unparse(node.value)
        contract_name = self.contract_name(node)
        if contract_name is not None:
            return contract_name
        return ast.unparse(node)

    def _callable_parts(
        self,
        node: ast.FunctionDef,
        *,
        projection: list[ProjectionMapping],
        native_result: ProjectionMapping | None = None,
        drop_untyped_self: bool = False,
    ) -> tuple[list[SemanticArgument], SemanticType | None]:
        self._validate_callable_header(node)
        semantic_args = self._callable_semantic_arguments(node, projection, drop_untyped_self=drop_untyped_self)
        visible_args = list(semantic_args)
        self._apply_argument_value_projections(visible_args, projection)
        self._apply_argument_descriptor_projections(visible_args, projection)
        optional_return_positions = self._optional_native_return_positions(projection, native_result)
        return_type, returned_args = self.return_projection(
            node.returns,
            optional_return_positions=optional_return_positions,
        )
        self._validate_callable_descriptor_return(return_type, native_result)
        return_type, returned_args = self._apply_native_call_returns(return_type, returned_args, projection)
        return_type = self._apply_native_result_projection(return_type, native_result)
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
        defaults: list[ast.expr | None] = [None] * (len(node.args.args) - len(node.args.defaults))
        defaults.extend(node.args.defaults)
        return defaults

    @staticmethod
    def _validate_stub_callable(node: ast.FunctionDef) -> None:
        if len(node.body) != 1:
            raise ValueError(f"Unsupported function header: {_node_text(node)!r}")
        body = node.body[0]
        if not (isinstance(body, ast.Expr) and isinstance(body.value, ast.Constant) and body.value.value is Ellipsis):
            raise ValueError(f"Unsupported function header: {_node_text(node)!r}")

    @staticmethod
    def _apply_projected_returns(semantic_args: list[SemanticArgument], returned_args: list[SemanticArgument]) -> None:
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
        return {returned.name: returned.metadata.get("return_position") for returned in returned_args}

    @staticmethod
    def _apply_native_call_argument_names(
        semantic_args: list[SemanticArgument],
        return_positions: dict[str, int | None],
        projection: list[ProjectionMapping],
    ) -> None:
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
        if mapping.value_kind not in {"addr", "allocatable", "pointer", "value"} or not isinstance(mapping.value, dict):
            return
        if mapping.value.get("kind") == "arg" and mapping.value.get("position") == old_position:
            mapping.value["position"] = new_position

    def return_items(self, node: ast.expr) -> list[ast.expr]:
        if isinstance(node, ast.Subscript) and (
            self.matches_plain_name(node.value, "tuple") or self.matches_plain_name(node.value, "Tuple")
        ):
            return self.subscript_items(node)
        return [node]


class _ClassBodyVisitor(ClassVisitor):
    def __init__(self, parser: _PyiAstParser, *, class_name: str):
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
        if decorators.external:
            raise ValueError("external is not valid for a class method")
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
            hold_gil=decorators.hold_gil,
            error_status_policy=decorators.error_status_policy,
        )
        if node.name == "__init__" and decorators.bind_target is not None:
            self.has_bound_constructor = True
        if decorators.overload_target is not None:
            self.pending_overloads.append((method, decorators.overload_target, decorators.overload_generic))
        else:
            self.methods.append(method)

    @staticmethod
    def _is_generated_constructor(node: ast.FunctionDef) -> bool:
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
            or decorators.hold_gil
            or decorators.error_status_policy is not None
            or decorators.external
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
    def __init__(self, parser: _PyiAstParser):
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
            raise ValueError('typing.overload is not supported; use x2py @overload("specific")')
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
            or decorators.hold_gil
            or decorators.error_status_policy is not None
            or decorators.external
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
            self.parser.module.prototypes.append(self.parser.prototype_def(node, visibility=decorators.visibility))
            return
        function = self.parser.function_def(
            node,
            visibility=decorators.visibility,
            projection=decorators.projection,
            native_result=decorators.native_result,
            native_name=decorators.bind_target,
            external=decorators.external,
            has_native_call=decorators.has_native_call,
            hold_gil=decorators.hold_gil,
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


def _node_text(node: ast.AST) -> str:
    text = ast.unparse(node)
    return text.splitlines()[0] if text else type(node).__name__


def _annotate_imported_external_type_refs(module: SemanticModule) -> None:
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
    definitions = {(module.name, declaration.name): declaration for module in modules for declaration in module.classes}
    prototypes = {(module.name, prototype.name): prototype for module in modules for prototype in module.prototypes}
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
    return modules
