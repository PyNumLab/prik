"""Resolve basic C typedef and tag references in completed parser projects.

This parser-stage module runs after every explicit C input has been parsed and
project indexes have been assembled.  It canonicalizes supported typedef chains
and unqualified struct, union, and enum tags while preserving unresolved
references and emitting stable diagnostics for typedef cycles.  It does not
make semantic or wrapper-policy decisions.

For example, consider two parsed files that together declare::

    typedef unsigned long api_size;
    api_size count(void);

    struct state { int id; };
    void step(struct state *value);

Before resolution, ``count`` and ``step`` may hold separate parser reference
objects named ``api_size`` and ``state``.  Afterwards, ``count.result_type``
is ``project.typedefs["api_size"]``, and the ``struct state`` component in
``step``'s pointer type is ``project.structs["state"]``.  Typedef chains are
linked recursively too: ``typedef raw_size api_size;`` makes
``api_size.type`` refer to ``raw_size``'s canonical typedef object.
"""

from __future__ import annotations

from prik.parsers.c.models import (
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


# Public project-resolution entrypoint.


def resolve_project_types(project: CProject) -> CProject:
    """Canonicalize basic cross-file type references in a parsed C project.

    Call this after the parser has populated ``project`` and all of its indexes.
    The resolver mutates declaration types in place, returns the same project
    for fluent parser orchestration, leaves unknown names as ``CTypedef``
    references, and appends one diagnostic per typedef cycle.

    The supported scope is deliberately limited to typedef chains and
    unqualified struct, union, and enum tag links; broader conflict policy and
    semantic datatype interpretation remain downstream responsibilities.
    """

    emitted_cycles: set[tuple[str, ...]] = set()

    # Stage 1: resolve the canonical typedef index before use sites.
    for typedef in project.typedefs.values():
        _resolve_typedef_definition(project, typedef, [], emitted_cycles)

    # Stage 2: resolve every declaration category in each parsed file's order.
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


# Declaration traversal helpers.  Each mutates parser-owned model fields.


def _resolve_function(
    project: CProject,
    function: CFunction,
    emitted_cycles: set[tuple[str, ...]],
) -> None:
    """Resolve one function result and parameters in declaration order.

    ``function`` is updated in place.  Resolving the result before parameters
    preserves the existing traversal order and shared typedef-cycle state.
    """
    function.result_type = _resolve_type(project, function.result_type, [], emitted_cycles)
    for parameter in function.parameters:
        _resolve_parameter(project, parameter, emitted_cycles)


def _resolve_parameter(
    project: CProject,
    parameter: CParameter,
    emitted_cycles: set[tuple[str, ...]],
) -> None:
    """Resolve one parameter's effective and, when present, declared type.

    Both fields are parser facts: arrays and function parameters may have a
    distinct declared type.  The parameter is mutated in place while sharing
    the project's cycle-diagnostic set.
    """
    parameter.type = _resolve_type(project, parameter.type, [], emitted_cycles)
    if parameter.declared_type is not None:
        parameter.declared_type = _resolve_type(project, parameter.declared_type, [], emitted_cycles)


def _resolve_variable(
    project: CProject,
    variable: CVariable,
    emitted_cycles: set[tuple[str, ...]],
) -> None:
    """Resolve the type stored by one variable or aggregate member in place."""
    variable.type = _resolve_type(project, variable.type, [], emitted_cycles)


def _resolve_typedef_definition(
    project: CProject,
    typedef: CTypedef,
    stack: list[str],
    emitted_cycles: set[tuple[str, ...]],
) -> None:
    """Resolve a typedef definition while extending its current alias stack.

    Typedefs without a definition are left untouched.  The copied stack records
    the alias path for cycle detection without mutating a caller's recursion
    state.
    """
    if typedef.type is None:
        return
    typedef.type = _resolve_type(project, typedef.type, [*stack, typedef.name], emitted_cycles)


# Recursive type and reference resolution.


def _resolve_type(
    project: CProject,
    type_: CType,
    stack: list[str],
    emitted_cycles: set[tuple[str, ...]],
) -> CType:
    """Resolve nested parser type components and supported named references.

    Composite and function types retain their original container objects while
    their child references are replaced in place.  Typedefs and unqualified
    tags return the project-indexed object when known; all other type facts are
    returned unchanged.
    """

    # Stage 1: recurse through containers before resolving their leaf references.
    if isinstance(type_, CComposedType):
        type_.components = [_resolve_type(project, component, stack, emitted_cycles) for component in type_.components]
        return type_
    if isinstance(type_, CFunctionType):
        type_.result_type = _resolve_type(project, type_.result_type, stack, emitted_cycles)
        type_.parameter_types = [
            _resolve_type(project, parameter_type, stack, emitted_cycles) for parameter_type in type_.parameter_types
        ]
        return type_

    # Stage 2: resolve aliases and only canonical unqualified tag references.
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
    """Resolve one typedef use without replacing unknown or cyclic references.

    A matching definition is resolved first so typedef chains share canonical
    objects.  If the name is absent or appears in ``stack``, the original use
    remains in place and a normalized cycle diagnostic is recorded when needed.
    """
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
    """Append one stable diagnostic for a typedef loop, regardless of rotation.

    ``cycle`` may include an acyclic alias prefix.  The helper isolates the
    actual loop, rotates it to a canonical spelling, and uses ``emitted_cycles``
    to avoid duplicate diagnostics from later declaration use sites.
    """

    # Stage 1: isolate the repeated portion from any acyclic alias prefix.
    first = cycle[-1]
    start = cycle.index(first)
    loop = cycle[start:-1]
    rotations = [tuple(loop[index:] + loop[:index]) for index in range(len(loop))]
    normalized_loop = min(rotations)
    normalized = (*normalized_loop, normalized_loop[0])

    # Stage 2: emit the canonical loop at most once for the whole project.
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


if __name__ == "__main__":
    canonical_struct = CStruct(name="state")
    state_handle = CTypedef(name="state_handle", type=CStruct(name="state"))
    raw_state = CTypedef(name="raw_state", type=CStruct(name="state"))
    state_alias = CTypedef(name="state_alias", type=CTypedef(name="raw_state"))
    example_project = CProject(
        structs={"state": canonical_struct},
        typedefs={
            "state_handle": state_handle,
            "raw_state": raw_state,
            "state_alias": state_alias,
        },
    )

    resolve_project_types(example_project)

    print("Tag reference:")
    print(f"{state_handle.name} -> {state_handle.type.reference_name}")
    print("Typedef chain:")
    print(f"{state_alias.name} -> {state_alias.type.name} -> {state_alias.type.type.reference_name}")
