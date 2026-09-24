"""Exact source-side export selection for Fortran semantic modules."""

from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass
import re

from prik.semantics.models import (
    EXTERNAL_TYPE_REF_METADATA,
    ProcedureOverloadSet,
    SemanticFunction,
    SemanticModule,
    _semantic_type_tree,
)


_FORTRAN_IDENTIFIER = r"[A-Za-z][A-Za-z0-9_]*"
_FORTRAN_EXPORT_RE = re.compile(rf"^(?P<module>{_FORTRAN_IDENTIFIER})::(?P<symbol>{_FORTRAN_IDENTIFIER})$")


@dataclass(frozen=True)
class FortranExportSelection:
    """Selected wrapper roots and the surrounding semantic source context."""

    primary_sources: tuple[SemanticModule, ...]
    primary_modules: tuple[SemanticModule, ...]
    context_modules: tuple[SemanticModule, ...]

    @property
    def available_modules(self) -> tuple[SemanticModule, ...]:
        return (*self.primary_modules, *self.context_modules)


def parse_fortran_export_identity(value: str) -> tuple[str, str]:
    """Return one case-folded ``module::symbol`` identity or raise."""
    match = _FORTRAN_EXPORT_RE.fullmatch(str(value))
    if match is None:
        raise ValueError(f"invalid Fortran module symbol identity: {value}")
    return match.group("module").casefold(), match.group("symbol").casefold()


def select_fortran_export_symbols(
    modules: Iterable[SemanticModule],
    symbols: Iterable[str],
) -> FortranExportSelection:
    """Select exact module procedures and variables with semantic source context.

    Selection is expressed in native identities before policy names anything.
    Primary module copies contain only requested procedures and variables;
    classes and prototypes remain available as signature facts. Other
    source modules remain available as context. Contract-import policy decides
    which of them the generated contract needs to emit.
    """
    source_modules = tuple(
        module
        for module in modules
        if module.origin.source_language == "fortran" and module.origin.source_kind == "module"
    )
    requested = _validated_fortran_export_symbols(symbols)
    module_index = {_native_module_name(module): module for module in source_modules}
    selectable, non_selectable = _fortran_export_candidates(source_modules)
    _validate_fortran_export_resolution(requested, selectable, non_selectable, module_index)

    selected = _selected_identities(requested, module_index)
    primary_names = {module_name for module_name, _symbol_name in selected}
    primary_sources = []
    primary_modules = []
    for module in source_modules:
        module_name = _native_module_name(module)
        if module_name not in primary_names:
            continue
        selected_module = _select_module_surface(module, selected, set(requested))
        primary_sources.append(module)
        primary_modules.append(selected_module)

    required_types = _with_dependent_types(_required_type_identities(primary_modules, selected), module_index)
    for module in primary_modules:
        _retain_required_types(module, module_index[_native_module_name(module)], required_types)

    # Root selection owns only the requested symbol surface. Contract-import
    # completion already owns which available modules selected declarations
    # actually name, including private callback prototypes and imported types
    # that are not Fortran reexports. Keep the remaining modules available and
    # let that one authority emit only the dependencies the contract binds.
    context_names = tuple(name for name in module_index if name not in primary_names)
    context_modules = tuple(deepcopy(module_index[name]) for name in context_names)
    return FortranExportSelection(tuple(primary_sources), tuple(primary_modules), context_modules)


def _selected_identities(requested, module_index):
    """Add the declaring identity of each name selected through a facade re-export."""
    selected = set(requested)
    for module_name, symbol_name in requested:
        for reexport in module_index[module_name].reexports:
            if reexport.local_name.casefold() == symbol_name:
                selected.add((reexport.origin_module.casefold(), reexport.source_name.casefold()))
    return selected


def _select_module_surface(module, selected, requested):
    """Retain selected declarations while keeping generic specifics private to them."""
    selected_module = deepcopy(module)
    module_name = _native_module_name(module)
    selected_module.overload_sets = [
        overload
        for overload in selected_module.overload_sets
        if (module_name, _native_symbol_name(overload)) in selected
    ]
    _retain_selected_procedures(selected_module, module_name, selected)
    selected_module.variables = [
        variable for variable in selected_module.variables if (module_name, _native_symbol_name(variable)) in selected
    ]
    selected_module.reexports = [
        reexport for reexport in selected_module.reexports if (module_name, reexport.local_name.casefold()) in requested
    ]
    for reexport in selected_module.reexports:
        reexport.explicitly_public = True
        reexport.python_exported = None
    selected_module.exported_names = [
        declaration.name
        for declaration in (*selected_module.functions, *selected_module.overload_sets, *selected_module.variables)
        if (module_name, _native_symbol_name(declaration)) in selected
    ]
    selected_module.exported_names.extend(reexport.local_name for reexport in selected_module.reexports)
    return selected_module


def _retain_selected_procedures(module, module_name, selected):
    """Keep named procedures and the specifics of each selected generic."""
    specifics = {
        _native_symbol_name(procedure): procedure
        for overload in module.overload_sets
        for procedure in overload.procedures
    }
    module.functions = [
        function
        for function in module.functions
        if (module_name, _native_symbol_name(function)) in selected or _native_symbol_name(function) in specifics
    ]
    declared = {_native_symbol_name(function) for function in module.functions}
    module.functions.extend(deepcopy(procedure) for name, procedure in specifics.items() if name not in declared)


def _retain_required_types(module, source_module, required_types):
    """Publish only derived types required by selected values or signatures."""
    module_name = _native_module_name(module)
    module.classes = [cls for cls in module.classes if (module_name, _native_symbol_name(cls)) in required_types]
    for cls in module.classes:
        cls.methods = []
        cls.overload_sets = []
        if cls.name not in module.exported_names:
            module.exported_names.append(cls.name)
    for reexport in source_module.reexports:
        identity = (reexport.origin_module.casefold(), reexport.source_name.casefold())
        if reexport.entity_kind != "derived_type" or identity not in required_types:
            continue
        if any(item.local_name.casefold() == reexport.local_name.casefold() for item in module.reexports):
            continue
        dependency = deepcopy(reexport)
        dependency.explicitly_public = True
        dependency.python_exported = None
        module.reexports.append(dependency)
        module.exported_names.append(dependency.local_name)


def _required_type_identities(modules: list[SemanticModule], selected: set[tuple[str, str]]) -> set[tuple[str, str]]:
    """Find derived declarations named by selected signatures and values."""
    required: set[tuple[str, str]] = set()
    for module in modules:
        module_name = _native_module_name(module)
        owners = (
            *module.variables,
            *module.functions,
            *module.overload_sets,
        )
        for owner in owners:
            if (module_name, _native_symbol_name(owner)) not in selected:
                continue
            functions = owner.procedures if isinstance(owner, ProcedureOverloadSet) else (owner,)
            for declaration in functions:
                types = (
                    (declaration.semantic_type,)
                    if hasattr(declaration, "semantic_type")
                    else (
                        *(argument.semantic_type for argument in declaration.arguments),
                        declaration.return_type,
                    )
                )
                for semantic_type in types:
                    required.update(_type_identities(semantic_type, module_name))
    return required


def _type_identities(semantic_type, module_name: str) -> set[tuple[str, str]]:
    """Return the declaring identities one semantic type names, including callback types."""
    identities = set()
    for item in _semantic_type_tree(semantic_type):
        reference = item.metadata.get(EXTERNAL_TYPE_REF_METADATA)
        origin = reference.get("origin_module") if isinstance(reference, dict) else module_name
        name = reference.get("name") if isinstance(reference, dict) else item.name
        identities.add((str(origin).casefold(), str(name).casefold()))
    return identities


def _with_dependent_types(required: set[tuple[str, str]], module_index) -> set[tuple[str, str]]:
    """Close required derived types over the component and parent types they declare.

    A published type is usable only with the types its components and parent
    name, so each of those is retained wherever it is declared.
    """
    closed: set[tuple[str, str]] = set()
    pending = list(required)
    while pending:
        identity = pending.pop()
        if identity in closed:
            continue
        closed.add(identity)
        module = module_index.get(identity[0])
        if module is None:
            continue
        declaration = next((cls for cls in module.classes if _native_symbol_name(cls) == identity[1]), None)
        if declaration is None:
            pending.extend(
                (reexport.origin_module.casefold(), reexport.source_name.casefold())
                for reexport in module.reexports
                if reexport.entity_kind == "derived_type" and reexport.local_name.casefold() == identity[1]
            )
            continue
        for component in declaration.fields:
            pending.extend(_type_identities(component.semantic_type, identity[0]))
        pending.extend(_named_type_identity(module, base) for base in declaration.base_classes)
    return closed


def _named_type_identity(module: SemanticModule, name: str) -> tuple[str, str]:
    """Resolve a type name written in ``module`` to its local or use-associated declaration."""
    wanted = name.casefold()
    for semantic_import in module.imports:
        for item in semantic_import.items:
            if (item.target or item.source).casefold() == wanted:
                return semantic_import.module.casefold(), item.source.casefold()
    return _native_module_name(module), wanted


def _validated_fortran_export_symbols(symbols: Iterable[str]) -> tuple[tuple[str, str], ...]:
    requested_text = tuple(str(symbol) for symbol in symbols)
    if not requested_text:
        raise ValueError("Fortran export-symbol selection requires at least one module symbol identity")
    requested = []
    invalid = []
    repeated = []
    seen: set[tuple[str, str]] = set()
    for value in requested_text:
        try:
            identity = parse_fortran_export_identity(value)
        except ValueError:
            invalid.append(value)
            continue
        if identity in seen and value not in repeated:
            repeated.append(value)
        seen.add(identity)
        requested.append(identity)
    problems = []
    if invalid:
        problems.append("invalid symbol identities: " + ", ".join(invalid))
    if repeated:
        problems.append("repeated identities: " + ", ".join(repeated))
    if problems:
        raise ValueError("Fortran export-symbol selection failed: " + "; ".join(problems))
    return tuple(requested)


def _fortran_export_candidates(modules: tuple[SemanticModule, ...]):
    selectable: dict[tuple[str, str], list[object]] = {}
    non_selectable: set[tuple[str, str]] = set()
    for module in modules:
        module_name = _native_module_name(module)
        for declaration in (*module.functions, *module.overload_sets, *module.variables):
            selectable.setdefault((module_name, _native_symbol_name(declaration)), []).append(declaration)
        for reexport in module.reexports:
            if reexport.entity_kind in {"procedure", "generic", "variable"}:
                selectable.setdefault((module_name, reexport.local_name.casefold()), []).append(reexport)
        for declaration in (*module.classes, *module.prototypes):
            non_selectable.add((module_name, _native_symbol_name(declaration)))
    return selectable, non_selectable


def _validate_fortran_export_resolution(requested, selectable, non_selectable, module_index) -> None:
    problems = []
    unknown_modules = [module for module, _name in requested if module not in module_index]
    non_symbols = [identity for identity in requested if identity in non_selectable and identity not in selectable]
    unknown = [
        identity
        for identity in requested
        if identity[0] in module_index and identity not in selectable and identity not in non_selectable
    ]
    ambiguous = [identity for identity in requested if len(selectable.get(identity, ())) > 1]
    inaccessible = [
        identity
        for identity in requested
        if any(
            getattr(declaration, "visibility", "public") == "private" for declaration in selectable.get(identity, ())
        )
    ]
    for label, identities in (
        ("unknown modules", tuple(dict.fromkeys(unknown_modules))),
        ("unknown symbols", unknown),
        ("unsupported declarations", non_symbols),
        ("ambiguous symbols", ambiguous),
        ("private symbols", inaccessible),
    ):
        if identities:
            formatted = [item if isinstance(item, str) else "::".join(item) for item in identities]
            problems.append(f"{label}: {', '.join(formatted)}")
    if problems:
        raise ValueError("Fortran export-symbol selection failed: " + "; ".join(problems))


def _native_module_name(module: SemanticModule) -> str:
    return str(module.origin.native_name or module.name).casefold()


def _native_symbol_name(declaration: object) -> str:
    if isinstance(declaration, ProcedureOverloadSet):
        return str(declaration.name).casefold()
    if isinstance(declaration, SemanticFunction):
        return str(declaration.origin.native_name or declaration.native_name or declaration.name).casefold()
    return str(getattr(getattr(declaration, "origin", None), "native_name", None) or declaration.name).casefold()
