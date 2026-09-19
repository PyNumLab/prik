"""Complete the names each generated contract binds from other modules.

A contract has to bind every name it writes without declaring: a type or a
prototype its signatures name, a callable its declaration expressions call, the
module a procedure-local type is qualified by, and each name it publishes out of
another module. That, and not the ``use`` statements its source happened to
write, is what it imports. A ``use`` that only extends a generic the module
declares, or reaches a name no declaration mentions, binds nothing here.

``complete_contract_imports`` replaces a module's ``imports`` with those
bindings, spelled both ways a contract is written: as the sources name each
side, and as the completed contracts do. The printer renders them and decides
nothing.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from prik.naming import normalize_public_name, preserves_source_case
from prik.policy.exports import contract_name_for_source, contract_names_by_source, imported_type_reference
from prik.semantics import models
from prik.semantics.pyi_metadata import PYI_LOADED_METADATA


def complete_contract_imports(
    modules: Iterable[models.SemanticModule],
    *,
    dependencies: Iterable[models.SemanticModule] = (),
) -> None:
    """Replace each module's imports with the bindings its contract writes.

    Names must already be completed for ``modules`` and ``dependencies``: an
    import asks the module it reads from for the name that module's contract
    declares. ``dependencies`` are contracts completed alongside but not
    written here.
    """
    modules = list(modules)
    completed = {module.name.casefold(): contract_names_by_source(module) for module in (*dependencies, *modules)}
    for module in modules:
        module.imports = _ContractImports(module, completed).bindings()


class _ContractImports:
    """Bind each name one contract needs, once, from the one entity it names.

    Every binding passes through ``_bind``. A module does not import from
    itself or import a declaration it already carries; a name reached twice
    from the same entity binds once; and a name bound to two entities, or to
    one while the contract declares another, cannot be written.
    """

    def __init__(self, module: models.SemanticModule, completed: dict[str, dict[str, str]]):
        self._module = module
        self._completed = completed
        # A loaded contract already writes Python; only a native one is spelled.
        self._native = not module.metadata.get(PYI_LOADED_METADATA)
        self._preserve_case = not self._native or preserves_source_case(module.origin.source_language)
        self._key = str if self._preserve_case else str.casefold
        # The one spelling naming completed for each name this contract imports.
        self._imported = module.metadata.get(models.CONTRACT_IMPORT_NAMES_METADATA, {}) if self._native else {}
        declarations = (*module.functions, *module.classes, *module.variables, *module.prototypes)
        self._declared_names = {self._key(str(item.name)) for item in (*declarations, *module.overload_sets)}
        self._declared = {
            *(
                _identity(item.origin.native_scope or module.name, getattr(item, "native_name", None) or item.name)
                for item in declarations
            ),
            *(_identity(item.native_scope or module.name, item.name) for item in module.overload_sets),
        }
        self._bound: dict[str, tuple[str, str]] = {}
        self._statements: list[str | models.SemanticImport] = []
        self._from: dict[str, models.SemanticImport] = {}

    def bindings(self) -> list[str | models.SemanticImport]:
        """Return the import statements the contract writes, in writing order.

        The contract's own imports come first, then the names it publishes in
        the order its source reached them, then every name its declarations
        refer to. Those are sorted, so reordering declarations never reorders
        the imports they need.
        """
        for statement in self._module.imports:
            self._stated(statement)
        for reexport in self._module.reexports:
            # A name published out of another module is bound to be published.
            if reexport.publishes_to_python() and reexport.origin_module:
                self._bind(
                    str(reexport.origin_module),
                    str(reexport.source_name or reexport.local_name),
                    str(reexport.local_name),
                    verbatim=reexport.entity_kind == "prototype",
                )
        for origin, source, local, kind in sorted(set(self._references())):
            self._bind(origin, source, local, verbatim=kind in {"prototype", "namespace"})
        return self._statements

    def _stated(self, statement: str | models.SemanticImport) -> None:
        """Carry one import the module states itself."""
        if isinstance(statement, str) or not statement.items:
            self._statements.append(statement)
            return
        for item in statement.items:
            self._bind(statement.module, item.source, item.target or item.source)

    def _references(self) -> Iterator[tuple[str, str, str, str]]:
        """Yield ``(module, source, local, kind)`` for each name a declaration names."""
        for semantic_type in models._module_semantic_types(self._module):
            yield from _type_reference(semantic_type)
            yield from _prototype_reference(semantic_type.metadata.get(models.PROTOTYPE_REF_METADATA))
            yield from _callable_references(semantic_type)

    def _bind(self, origin: str, source: str, local: str, *, verbatim: bool = False) -> None:
        """Bind ``local`` to ``source`` read from ``origin``, or refuse a second meaning.

        The contract binds the spelling naming completed for ``local``, which is
        the one its annotations and ``__all__`` write. A name completion did not
        spell -- a prototype, or a callable a declaration expression writes --
        keeps the spelling it is written with.
        """
        origin_key = origin.lstrip(".").casefold()
        if origin_key == self._module.name.casefold() or _identity(origin_key, source) in self._declared:
            return
        key = self._key(local)
        identity = (origin_key, self._key(source))
        existing = self._bound.get(key)
        if existing == identity:
            return
        if existing is not None or key in self._declared_names:
            raise ValueError(
                f"Contract for {self._module.name!r} cannot bind {local!r} to {origin}.{source}: "
                "the name already means something else there"
            )
        self._bound[key] = identity
        written = f".{origin}" if self._native and not origin.startswith(".") else origin
        statement = self._from.get(written)
        if statement is None:
            statement = self._from[written] = models.SemanticImport(module=written)
            self._statements.append(statement)
        contract_source = self._contract_source(origin_key, source, verbatim)
        contract_target = contract_name_for_source(self._imported, local) or local
        statement.items.append(
            models.SemanticImportItem(
                source=source,
                target=None if local == source else local,
                contract_source=contract_source,
                contract_target=None if contract_target == contract_source else contract_target,
            )
        )

    def _contract_source(self, origin_key: str, source: str, verbatim: bool) -> str:
        """Return the name the module read from declares for ``source``.

        Its own completion settled that. A module outside this completion is
        spelled the way this one spells a name, except a prototype or a module,
        which keep their spelling everywhere; a loaded contract already writes
        Python and keeps every spelling.
        """
        if not self._native:
            return source
        completed = contract_name_for_source(self._completed.get(origin_key), source)
        if completed is not None:
            return completed
        return source if verbatim else normalize_public_name(source, preserve_case=self._preserve_case).name


def _identity(scope: str, name: str) -> tuple[str, str]:
    """Return the case-folded ``(module, name)`` identity of one declaration."""
    return str(scope).casefold(), str(name).casefold()


def _type_reference(semantic_type: models.SemanticType) -> Iterator[tuple[str, str, str, str]]:
    """Yield the binding one annotation naming an imported type needs."""
    reference = imported_type_reference(semantic_type)
    if reference is None:
        return
    if reference.procedure_local:
        # A procedure-local type is written qualified by its module.
        yield ".", reference.module, reference.module, "namespace"
    else:
        yield reference.module, reference.name, reference.local, "type"


def _prototype_reference(ref: object) -> Iterator[tuple[str, str, str, str]]:
    """Yield the binding one callback annotation naming a prototype needs."""
    if not isinstance(ref, dict):
        return
    origin = str(ref.get("origin_module") or "")
    local = str(ref.get("local_name") or ref.get("name") or "")
    if origin and local:
        yield origin, str(ref.get("name") or local), local, "prototype"


def _callable_references(semantic_type: models.SemanticType) -> Iterator[tuple[str, str, str, str]]:
    """Yield the binding each callable a declaration expression calls needs."""
    array = semantic_type.storage.array if semantic_type.storage is not None else None
    for axis in array.expression_callables if array is not None else ():
        for reference in axis:
            if reference.native_scope is not None:
                local = reference.name.rsplit(".", 1)[-1]
                yield reference.native_scope, reference.native_name or local, local, "procedure"
