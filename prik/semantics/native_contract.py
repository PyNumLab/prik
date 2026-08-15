"""Prepare and validate source-free native facts declared by semantic `.pyi`.

``prepare_pyi_native_contract`` attaches native origins to loaded contract
modules. ``native_contract_issues`` reports incomplete or inconsistent native
placement and type facts, while ``validate_pyi_native_contract`` raises the
first issue. This module validates declared facts before policy completion; it
does not choose ownership, support, or generated mechanisms.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from prik.semantics.metadata import BIND_TARGET_METADATA

from prik.semantics.pyi_metadata import PYI_LOADED_METADATA
from prik.semantics.models import (
    OVERLOAD_TARGET_METADATA,
    ProjectionMapping,
    SemanticClass,
    SemanticFunction,
    SemanticMethod,
    SemanticModule,
    SemanticPrototype,
    SemanticType,
    _module_semantic_types,
)


NATIVE_CONTRACT_PREPARED_METADATA = "native_contract_prepared"


@dataclass(frozen=True)
class NativeContractIssue:
    code: str
    message: str
    owner: str


def prepare_pyi_native_contract(modules: Iterable[SemanticModule]) -> list[SemanticModule]:
    prepared = list(modules)
    for module in prepared:
        if module.metadata.get(PYI_LOADED_METADATA):
            _prepare_module(module)
    return prepared


def _prepare_module(module: SemanticModule) -> None:
    native_scope = module.name
    module.origin.source_language = "fortran"
    module.origin.native_name = native_scope
    module.origin.native_scope = native_scope
    module.origin.source_kind = "module"

    for variable in module.variables:
        _set_origin(variable, native_scope, "variable")
    for function in module.functions:
        _prepare_function(function, native_scope)
    for prototype in module.prototypes:
        _prepare_prototype(prototype, native_scope)
    for overload_set in module.overload_sets:
        for procedure in overload_set.procedures:
            _prepare_function(procedure, native_scope)
    for semantic_class in module.classes:
        _prepare_class(semantic_class, native_scope)
    for semantic_type in _module_semantic_types(module):
        semantic_type.origin.source_language = "fortran"


def _set_origin(node, native_scope: str | None, source_kind: str) -> None:
    node.origin.source_language = "fortran"
    node.origin.native_name = node.origin.native_name or getattr(node, "native_name", None) or node.name
    node.origin.native_scope = native_scope
    node.origin.source_kind = source_kind


def _prepare_function(function: SemanticFunction, native_scope: str) -> None:
    is_external = function.origin.source_language == "fortran" and function.origin.native_scope is None
    function_scope = None if is_external else native_scope
    source_kind = "function" if function.return_type is not None else "subroutine"
    _set_origin(function, function_scope, source_kind)
    function.origin.native_name = function.native_name or function.name
    for argument in function.arguments:
        _set_origin(argument, function.origin.native_name, "argument")


def _prepare_prototype(prototype: SemanticPrototype, native_scope: str) -> None:
    _set_origin(prototype, native_scope, "prototype")
    prototype.origin.native_name = prototype.native_name or prototype.name
    for argument in prototype.arguments:
        _set_origin(argument, prototype.origin.native_name, "prototype_argument")


def _prepare_class(semantic_class: SemanticClass, native_scope: str) -> None:
    _set_origin(semantic_class, native_scope, "derived_type")
    for field in semantic_class.fields:
        _set_origin(field, native_scope, "field")
    for method in semantic_class.methods:
        _prepare_function(method, native_scope)
    for overload_set in semantic_class.overload_sets:
        for procedure in overload_set.procedures:
            _prepare_function(procedure, native_scope)
    for nested in semantic_class.classes:
        _prepare_class(nested, native_scope)


def native_contract_issues(module: SemanticModule) -> list[NativeContractIssue]:
    if not module.metadata.get(PYI_LOADED_METADATA):
        return []
    _prepare_module(module)
    issues: list[NativeContractIssue] = []
    if not module.name or module.name == "<pyi>":
        issues.append(
            NativeContractIssue(
                "pyi_native_module_name_missing",
                "A native module contract requires a filename-derived module name.",
                module.name,
            )
        )
    for variable in module.variables:
        issues.extend(_type_issues(variable.semantic_type, f"{module.name}.{variable.name}"))
    for function in module.functions:
        issues.extend(_function_issues(function, module, owner_kind="module"))
    for prototype in module.prototypes:
        for argument in prototype.arguments:
            issues.extend(_type_issues(argument.semantic_type, f"{module.name}.{prototype.name}.{argument.name}"))
        if prototype.return_type is not None and prototype.return_type.name != "None":
            issues.extend(_type_issues(prototype.return_type, f"{module.name}.{prototype.name}.return"))
    for overload_set in module.overload_sets:
        for procedure in overload_set.procedures:
            issues.extend(_function_issues(procedure, module, owner_kind="module"))
    for semantic_class in module.classes:
        issues.extend(_class_issues(semantic_class, module, prefix=module.name))
    return issues


def validate_pyi_native_contract(modules: Iterable[SemanticModule]) -> None:
    for module in prepare_pyi_native_contract(modules):
        issues = native_contract_issues(module)
        if issues:
            issue = issues[0]
            raise ValueError(f"{issue.code}: {issue.message} Owner: {issue.owner}")


def _class_issues(
    semantic_class: SemanticClass,
    module: SemanticModule,
    *,
    prefix: str,
) -> list[NativeContractIssue]:
    owner = f"{prefix}.{semantic_class.name}"
    issues: list[NativeContractIssue] = []
    if semantic_class.origin.native_scope != module.name:
        issues.append(
            NativeContractIssue(
                "pyi_native_type_scope_mismatch",
                "Native derived type scope does not match its module-leaf filename.",
                owner,
            )
        )
    for field in semantic_class.fields:
        issues.extend(_type_issues(field.semantic_type, f"{owner}.{field.name}"))
    for method in semantic_class.methods:
        if method.name == "__init__" and method.metadata.get(BIND_TARGET_METADATA):
            continue
        issues.extend(_function_issues(method, module, owner_kind="type_bound", prefix=owner))
    for overload_set in semantic_class.overload_sets:
        for procedure in overload_set.procedures:
            issues.extend(_function_issues(procedure, module, owner_kind="type_bound", prefix=owner))
    for nested in semantic_class.classes:
        issues.extend(_class_issues(nested, module, prefix=owner))
    return issues


def _function_issues(
    function: SemanticFunction,
    module: SemanticModule,
    *,
    owner_kind: str,
    prefix: str | None = None,
) -> list[NativeContractIssue]:
    owner = f"{prefix or module.name}.{function.name}"
    if function.metadata.get(OVERLOAD_TARGET_METADATA):
        return []
    issues = _projection_issues(function.projection, owner, len(function.arguments))
    expected_scope = None if function.origin.native_scope is None else module.name
    if function.origin.native_scope != expected_scope:
        issues.append(
            NativeContractIssue(
                "pyi_native_procedure_scope_mismatch",
                "Native procedure scope contradicts its leaf or @standalone placement.",
                owner,
            )
        )
    if isinstance(function, SemanticMethod) and owner_kind == "type_bound" and not function.is_static:
        passed_position = function.passed_object_position
        if not isinstance(passed_position, int) or not 0 <= passed_position < len(function.arguments):
            issues.append(
                NativeContractIssue(
                    "pyi_native_pass_object_missing",
                    "Non-static type-bound procedures require a reconstructable passed object.",
                    owner,
                )
            )
    for argument in function.arguments:
        issues.extend(_type_issues(argument.semantic_type, f"{owner}.{argument.name}"))
    if function.return_type is not None:
        issues.extend(_type_issues(function.return_type, f"{owner}.return"))
    return issues


def _projection_issues(
    projection: list[ProjectionMapping],
    owner: str,
    argument_count: int,
) -> list[NativeContractIssue]:
    if not projection:
        return []
    positions = [mapping.native_position for mapping in projection]
    if any(not isinstance(position, int) for position in positions):
        return [
            NativeContractIssue(
                "pyi_native_argument_position_missing",
                "Every native_call entry requires a native argument position.",
                owner,
            )
        ]
    if sorted(positions) != list(range(len(positions))):
        return [
            NativeContractIssue(
                "pyi_native_argument_order_invalid",
                "native_call entries must cover each native argument position exactly once in order.",
                owner,
            )
        ]
    invalid_python_positions = [
        mapping.python_position
        for mapping in projection
        if mapping.python_position is not None and not 0 <= mapping.python_position < argument_count
    ]
    if invalid_python_positions:
        return [
            NativeContractIssue(
                "pyi_python_argument_position_invalid",
                f"native_call references Python argument position {invalid_python_positions[0]} out of range.",
                owner,
            )
        ]
    return []


def _type_issues(semantic_type: SemanticType, owner: str) -> list[NativeContractIssue]:
    if not semantic_type.name or not semantic_type.dtype:
        return [
            NativeContractIssue(
                "pyi_native_type_missing",
                "Native data requires a concrete semantic type annotation.",
                owner,
            )
        ]
    if semantic_type.storage is None or semantic_type.storage.kind != "callback":
        return []
    arguments = semantic_type.metadata.get("arguments")
    kind = semantic_type.metadata.get("native_callback_kind")
    if not isinstance(arguments, list) or kind not in {"function", "subroutine"}:
        return [
            NativeContractIssue(
                "pyi_native_callback_incomplete",
                "Native callbacks require a resolved named prototype.",
                owner,
            )
        ]
    issues: list[NativeContractIssue] = []
    for index, argument in enumerate(arguments):
        if isinstance(argument, SemanticType):
            issues.extend(_type_issues(argument, f"{owner}.callback_arg[{index}]"))
    callback_return = semantic_type.metadata.get("return")
    if isinstance(callback_return, SemanticType) and callback_return.name != "None":
        issues.extend(_type_issues(callback_return, f"{owner}.callback_return"))
    return issues


if __name__ == "__main__":
    from prik.semantics.models import SemanticArgument

    valid_module = SemanticModule(
        "math",
        functions=[
            SemanticFunction(
                "scale",
                arguments=[SemanticArgument("value", SemanticType("Float64", dtype="float64"))],
            )
        ],
        metadata={PYI_LOADED_METADATA: True},
    )
    prepare_pyi_native_contract([valid_module])
    valid_issues = native_contract_issues(valid_module)

    invalid_module = SemanticModule(
        "math",
        functions=[
            SemanticFunction(
                "broken",
                arguments=[SemanticArgument("value", SemanticType("Float64"))],
            )
        ],
        metadata={PYI_LOADED_METADATA: True},
    )
    invalid_issue = native_contract_issues(invalid_module)[0]

    print(
        f"Prepared origin: {valid_module.origin.source_language} "
        f"{valid_module.origin.source_kind} {valid_module.origin.native_name}"
    )
    print(f"Valid contract issues: {len(valid_issues)}")
    print(f"Invalid contract issue: {invalid_issue.code} at {invalid_issue.owner}")
