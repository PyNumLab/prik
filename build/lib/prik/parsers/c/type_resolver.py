"""Basic C project type resolution for parser models."""

from __future__ import annotations

from .models import (
    CComposedType,
    CDiagnostic,
    CEnum,
    CFunction,
    CFunctionType,
    CParameter,
    CProject,
    CStruct,
    CType,
    CTypedef,
    CUnion,
    CVariable,
)


def resolve_project_types(project: CProject) -> CProject:
    """Resolve basic typedef and tag references inside a parsed C project."""
    emitted_cycles: set[tuple[str, ...]] = set()
    for typedef in project.typedefs.values():
        _resolve_typedef_definition(project, typedef, [], emitted_cycles)

    for file in project.files.values():
        for function in file.functions:
            _resolve_function(project, function, emitted_cycles)
        for typedef in file.typedefs:
            _resolve_typedef_definition(project, typedef, [], emitted_cycles)
        for variable in file.variables:
            _resolve_variable(project, variable, emitted_cycles)
        for aggregate in [*file.structs, *file.unions]:
            for member in aggregate.members:
                _resolve_variable(project, member, emitted_cycles)

    return project


def _resolve_function(
    project: CProject,
    function: CFunction,
    emitted_cycles: set[tuple[str, ...]],
) -> None:
    function.result_type = _resolve_type(project, function.result_type, [], emitted_cycles)
    for parameter in function.parameters:
        _resolve_parameter(project, parameter, emitted_cycles)


def _resolve_parameter(
    project: CProject,
    parameter: CParameter,
    emitted_cycles: set[tuple[str, ...]],
) -> None:
    parameter.type = _resolve_type(project, parameter.type, [], emitted_cycles)
    if parameter.declared_type is not None:
        parameter.declared_type = _resolve_type(project, parameter.declared_type, [], emitted_cycles)


def _resolve_variable(
    project: CProject,
    variable: CVariable,
    emitted_cycles: set[tuple[str, ...]],
) -> None:
    variable.type = _resolve_type(project, variable.type, [], emitted_cycles)


def _resolve_typedef_definition(
    project: CProject,
    typedef: CTypedef,
    stack: list[str],
    emitted_cycles: set[tuple[str, ...]],
) -> None:
    if typedef.type is None:
        return
    typedef.type = _resolve_type(project, typedef.type, [*stack, typedef.name], emitted_cycles)


def _resolve_type(
    project: CProject,
    type_: CType,
    stack: list[str],
    emitted_cycles: set[tuple[str, ...]],
) -> CType:
    if isinstance(type_, CComposedType):
        type_.components = [_resolve_type(project, component, stack, emitted_cycles) for component in type_.components]
        return type_
    if isinstance(type_, CFunctionType):
        type_.result_type = _resolve_type(project, type_.result_type, stack, emitted_cycles)
        type_.parameter_types = [
            _resolve_type(project, parameter_type, stack, emitted_cycles) for parameter_type in type_.parameter_types
        ]
        return type_
    if isinstance(type_, CTypedef):
        return _resolve_typedef_reference(project, type_, stack, emitted_cycles)
    if isinstance(type_, CStruct) and type_.name and not type_.qualifiers:
        return project.structs.get(type_.name, type_)
    if isinstance(type_, CUnion) and type_.name and not type_.qualifiers:
        return project.unions.get(type_.name, type_)
    if isinstance(type_, CEnum) and type_.name and not type_.qualifiers:
        return project.enums.get(type_.name, type_)
    return type_


def _resolve_typedef_reference(
    project: CProject,
    reference: CTypedef,
    stack: list[str],
    emitted_cycles: set[tuple[str, ...]],
) -> CType:
    target = project.typedefs.get(reference.name)
    if target is None:
        return reference
    if target.name in stack:
        _record_typedef_cycle(project, [*stack, target.name], target, emitted_cycles)
        return reference
    _resolve_typedef_definition(project, target, stack, emitted_cycles)
    return target


def _record_typedef_cycle(
    project: CProject,
    cycle: list[str],
    typedef: CTypedef,
    emitted_cycles: set[tuple[str, ...]],
) -> None:
    first = cycle[-1]
    start = cycle.index(first)
    loop = cycle[start:-1]
    rotations = [tuple(loop[index:] + loop[:index]) for index in range(len(loop))]
    normalized_loop = min(rotations)
    normalized = (*normalized_loop, normalized_loop[0])
    if normalized in emitted_cycles:
        return
    emitted_cycles.add(normalized)
    project.diagnostics.append(
        CDiagnostic(
            code="C_TYPEDEF_CYCLE",
            message=f"Typedef cycle detected: {' -> '.join(normalized)}.",
            severity="error",
            location=typedef.source_location,
            unit_kind="typedef",
            unit_name=typedef.name,
        )
    )


__all__ = ("resolve_project_types",)
