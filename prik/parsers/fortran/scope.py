"""How one Fortran scope reads its ``use`` statements.

A scope may name one module in several statements, spelled any way, and the
language reads them together: an ``only`` list narrows what its own statement
brings in, a rename binds an entity under a new name and leaves the old one
naming nothing, and any statement without ``only`` carries whatever else the
module publishes.

This is the single reading of that. It answers what a scope sees under a local
name and by which routes, and it answers nothing else: several routes to
different entities are reported as several routes, because whether that is an
ambiguity or a set of contributors is a question about the entities, which the
stage holding them decides.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass

from prik.parsers.fortran.models import FortranUseMapping, FortranUseStatement

#: Answers the public names one used module offers, or ``None`` when unread.
OfferedNames = Callable[[str], Collection[str] | None]


@dataclass(frozen=True)
class UseRoute:
    """One way a scope reaches a name: the module used, and the name there."""

    module: str
    source_name: str

    @property
    def key(self) -> tuple[str, str]:
        """Return the case-folded identity two spellings of one route share."""
        return self.module.casefold(), self.source_name.casefold()


class ScopeUses:
    """One scope's ``use`` statements, grouped by the module each names.

    Fortran module names are case-insensitive, so ``use DEP`` and ``use dep``
    are statements about one module and are read together.
    """

    def __init__(self, statements: Iterable[FortranUseStatement]) -> None:
        self._by_module: dict[str, list[FortranUseStatement]] = {}
        for statement in statements:
            self._by_module.setdefault(statement.module.casefold(), []).append(statement)

    def modules(self) -> tuple[str, ...]:
        """Return each used module once, spelled as its first statement wrote it."""
        return tuple(statements[0].module for statements in self._by_module.values())

    def imports_all(self, module: str) -> bool:
        """Return whether any statement for ``module`` omitted ``only``."""
        return any(not statement.only for statement in self._by_module.get(module.casefold(), ()))

    def mappings(self, module: str) -> tuple[FortranUseMapping, ...]:
        """Return every name the statements for ``module`` listed, in order."""
        seen: dict[tuple[str, str], FortranUseMapping] = {}
        for statement in self._by_module.get(module.casefold(), ()):
            for mapping in statement.mappings:
                seen.setdefault((mapping.source.casefold(), mapping.local_name.casefold()), mapping)
        return tuple(seen.values())

    def routes_for(self, local_name: str, offered: OfferedNames) -> tuple[UseRoute, ...]:
        """Return every route by which this scope reaches one local name.

        A listed name states its own route. A module imported whole is a route
        for a name it publishes, unless a rename took that name away. A module
        this project never read cannot be enumerated, so it offers no route
        rather than an assumed one.
        """
        folded = local_name.casefold()
        routes: dict[tuple[str, str], UseRoute] = {}
        for module in self.modules():
            for mapping in self.mappings(module):
                if mapping.local_name.casefold() == folded:
                    route = UseRoute(module, mapping.source)
                    routes.setdefault(route.key, route)
        for module in self.modules():
            if not self.imports_all(module) or folded in self._renamed_away(module):
                continue
            names = offered(module)
            if names is not None and folded in names:
                route = UseRoute(module, local_name)
                routes.setdefault(route.key, route)
        return tuple(routes.values())

    def accessible_names(self, offered: OfferedNames) -> tuple[str, ...]:
        """Return every local name this scope reaches, in source order.

        A listed name keeps the spelling its ``use`` statement bound it under;
        a name carried whole keeps the spelling its module publishes.
        """
        names: dict[str, str] = {}
        for module in self.modules():
            for mapping in self.mappings(module):
                names.setdefault(mapping.local_name.casefold(), mapping.local_name)
        for module in self.modules():
            if not self.imports_all(module):
                continue
            renamed_away = self._renamed_away(module)
            for name in sorted(offered(module) or ()):
                if name not in renamed_away:
                    names.setdefault(name.casefold(), name)
        return tuple(names.values())

    def unresolved_routes_for(self, local_name: str, offered: OfferedNames) -> tuple[UseRoute, ...]:
        """Return possible whole-module routes whose names cannot be enumerated.

        A plain ``use`` of a module this project never read carries names none
        of which can be listed. The route stays possible unless a rename took
        this spelling away; the consuming entity category decides whether that
        uncertainty makes the name ambiguous or permits an opaque fallback.
        """
        folded = local_name.casefold()
        return tuple(
            UseRoute(module, local_name)
            for module in self.modules()
            if self.imports_all(module) and offered(module) is None and folded not in self._renamed_away(module)
        )

    def _renamed_away(self, module: str) -> frozenset[str]:
        """Return the names a rename reaches, which are not reachable as written."""
        return frozenset(item.source.casefold() for item in self.mappings(module) if item.target)


def used_module_statements(owner: object) -> list[FortranUseStatement]:
    """Return every ``use`` statement one scope writes, including nested ones.

    A ``use`` written inside a contained procedure or an interface body is a
    dependency of the scope holding it just as much as one written at its top,
    so the whole tree is read. Compile ordering, project dependencies, and
    module source discovery all ask this, and they have to get the same answer.
    """
    statements: list[FortranUseStatement] = list(getattr(owner, "uses", ()))
    for procedure in getattr(owner, "procedures", ()):
        statements.extend(getattr(procedure, "uses", ()))
    for interface in getattr(owner, "interfaces", ()):
        for procedure in getattr(interface, "procedures", ()):
            statements.extend(getattr(procedure, "uses", ()))
    return statements


def used_module_names(owner: object) -> set[str]:
    """Return every module one scope names, lowercased."""
    return {statement.module.lower() for statement in used_module_statements(owner)}
