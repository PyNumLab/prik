"""Exact source-side export selection for Fortran semantic modules."""

from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass
import re

from prik.semantics.models import ProcedureOverloadSet, SemanticFunction, SemanticModule


_FORTRAN_IDENTIFIER = r"[A-Za-z][A-Za-z0-9_]*"
_FORTRAN_EXPORT_RE = re.compile(rf"^(?P<module>{_FORTRAN_IDENTIFIER})::(?P<procedure>{_FORTRAN_IDENTIFIER})$")


@dataclass(frozen=True)
class FortranExportSelection:
    """Selected wrapper roots and the surrounding semantic source context."""

    primary_modules: tuple[SemanticModule, ...]
    context_modules: tuple[SemanticModule, ...]

    @property
    def available_modules(self) -> tuple[SemanticModule, ...]:
        return (*self.primary_modules, *self.context_modules)


def parse_fortran_export_identity(value: str) -> tuple[str, str]:
    """Return one case-folded ``module::procedure`` identity or raise."""
    match = _FORTRAN_EXPORT_RE.fullmatch(str(value))
    if match is None:
        raise ValueError(f"invalid Fortran procedure identity: {value}")
    return match.group("module").casefold(), match.group("procedure").casefold()


def select_fortran_export_functions(
    modules: Iterable[SemanticModule],
    symbols: Iterable[str],
) -> FortranExportSelection:
    """Select exact module procedures with their semantic source context.

    Selection is expressed in native identities before policy names anything.
    Primary module copies contain only the requested callable declarations;
    their classes, prototypes, variables, and reexports remain available as
    signature facts but are not added to the stated public surface. Other
    source modules remain available as context. Contract-import policy decides
    which of them the generated contract needs to emit.
    """
    source_modules = tuple(modules)
    requested = _validated_fortran_export_symbols(symbols)
    module_index = {_native_module_name(module): module for module in source_modules}
    callable_index, non_callable_index = _fortran_export_candidates(source_modules)
    _validate_fortran_export_resolution(requested, callable_index, non_callable_index, module_index)

    selected = set(requested)
    primary_names = {module_name for module_name, _procedure_name in requested}
    primary_modules = []
    for module in source_modules:
        module_name = _native_module_name(module)
        if module_name not in primary_names:
            continue
        selected_module = deepcopy(module)
        selected_module.functions = [
            function
            for function in selected_module.functions
            if (module_name, _native_procedure_name(function)) in selected
        ]
        selected_module.overload_sets = [
            overload
            for overload in selected_module.overload_sets
            if (module_name, _native_procedure_name(overload)) in selected
        ]
        selected_module.exported_names = [
            declaration.name for declaration in (*selected_module.functions, *selected_module.overload_sets)
        ]
        primary_modules.append(selected_module)

    # Root selection owns only the requested callable surface. Contract-import
    # completion already owns which available modules selected declarations
    # actually name, including private callback prototypes and imported types
    # that are not Fortran reexports. Keep the remaining modules available and
    # let that one authority emit only the dependencies the contract binds.
    context_names = tuple(name for name in module_index if name not in primary_names)
    context_modules = tuple(deepcopy(module_index[name]) for name in context_names)
    return FortranExportSelection(tuple(primary_modules), context_modules)


def _validated_fortran_export_symbols(symbols: Iterable[str]) -> tuple[tuple[str, str], ...]:
    requested_text = tuple(str(symbol) for symbol in symbols)
    if not requested_text:
        raise ValueError("Fortran export-symbol selection requires at least one module procedure identity")
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
        problems.append("invalid procedure identities: " + ", ".join(invalid))
    if repeated:
        problems.append("repeated identities: " + ", ".join(repeated))
    if problems:
        raise ValueError("Fortran export-symbol selection failed: " + "; ".join(problems))
    return tuple(requested)


def _fortran_export_candidates(modules: tuple[SemanticModule, ...]):
    callables: dict[tuple[str, str], list[object]] = {}
    non_callables: set[tuple[str, str]] = set()
    for module in modules:
        module_name = _native_module_name(module)
        for declaration in (*module.functions, *module.overload_sets):
            callables.setdefault((module_name, _native_procedure_name(declaration)), []).append(declaration)
        for declaration in (*module.variables, *module.classes, *module.prototypes):
            non_callables.add((module_name, _native_procedure_name(declaration)))
    return callables, non_callables


def _validate_fortran_export_resolution(requested, callables, non_callables, module_index) -> None:
    problems = []
    unknown_modules = [module for module, _name in requested if module not in module_index]
    non_functions = [identity for identity in requested if identity in non_callables and identity not in callables]
    unknown = [
        identity
        for identity in requested
        if identity[0] in module_index and identity not in callables and identity not in non_callables
    ]
    ambiguous = [identity for identity in requested if len(callables.get(identity, ())) > 1]
    inaccessible = [
        identity
        for identity in requested
        if any(getattr(declaration, "visibility", "public") == "private" for declaration in callables.get(identity, ()))
    ]
    for label, identities in (
        ("unknown modules", tuple(dict.fromkeys(unknown_modules))),
        ("unknown procedures", unknown),
        ("non-function declarations", non_functions),
        ("ambiguous procedures", ambiguous),
        ("private procedures", inaccessible),
    ):
        if identities:
            formatted = [item if isinstance(item, str) else "::".join(item) for item in identities]
            problems.append(f"{label}: {', '.join(formatted)}")
    if problems:
        raise ValueError("Fortran export-symbol selection failed: " + "; ".join(problems))


def _native_module_name(module: SemanticModule) -> str:
    return str(module.origin.native_name or module.name).casefold()


def _native_procedure_name(declaration: object) -> str:
    if isinstance(declaration, ProcedureOverloadSet):
        return str(declaration.name).casefold()
    if isinstance(declaration, SemanticFunction):
        return str(declaration.origin.native_name or declaration.native_name or declaration.name).casefold()
    return str(getattr(getattr(declaration, "origin", None), "native_name", None) or declaration.name).casefold()
