"""Resolve contract spellings and Python exports before later stages run.

``complete_python_export_policy`` walks semantic declarations in lowering
order, completes public placement, then records the collision-checked spelling
the generated contract declares for every owner. Withheld declarations and
class members still need a contract identity even when they publish nothing.

``completed_python_exports`` retrieves that metadata as immutable
``PythonExportPolicy`` records while wrapper policy is assembled. This module
decides Python placement and contract spelling only: it does not choose a
wrapper mechanism or emit the namespace.
"""

from __future__ import annotations

from dataclasses import dataclass

from prik.naming import NamingPolicy, normalize_public_name, preserves_source_case
from prik.semantics import models
from prik.semantics.pyi_metadata import PYI_LOADED_METADATA
from prik.semantics.models import export_namespace


@dataclass(frozen=True)
class PythonExportPolicy:
    """One completed Python namespace and local export name."""

    namespace: tuple[str, ...]
    name: str


def _stated_export_names(module: models.SemanticModule) -> set[str] | None:
    """Return the surface one contract states, or ``None`` when it states none.

    A contract that writes no ``__all__`` publishes what it declares, so there
    is nothing stated to read and every declaration is completed as before. An
    empty list is a statement, not the absence of one: it says the module
    publishes nothing.

    The names are compared exactly. A contract is Python, where ``Foo`` and
    ``foo`` are different names, so a list naming ``Foo`` does not publish a
    declaration written ``foo`` -- it names something the module does not
    define.
    """
    if module.exported_names is None:
        return None
    return {str(name) for name in module.exported_names}


def complete_python_export_policy(
    module: models.SemanticModule,
    *,
    strict_wrapper_names: bool = False,
) -> None:
    """Resolve every public export name within its owning Python namespace.

    A module read from a semantic ``.pyi`` is already named in Python -- the
    contract states the names it publishes -- so those spellings are kept
    exactly. Only a module converted from native source has names PRIK must
    choose, and only where the source language has no spelling of its own.

    Such a contract also states its whole surface in ``__all__``, which is the
    authority on what it publishes. A declaration it leaves out stays written
    and reachable, because annotations and imports resolve against it, and no
    export is completed for it -- a prototype or a generic reads back public by
    default, and completing one would publish what the contract declined to.
    """
    contract_named = bool(module.metadata.get(PYI_LOADED_METADATA))
    complete_reexport_publication_policy(module, contract_named=contract_named)
    stated = _stated_export_names(module)
    naming = NamingPolicy(
        strict_public_names=strict_wrapper_names,
        preserve_case=contract_named or preserves_source_case(module.origin.source_language),
    )
    for owner in _module_export_owners(module):
        metadata = _owner_metadata(owner)
        if getattr(owner, "visibility", "public") == "private" or (
            stated is not None and str(owner.name) not in stated
        ):
            # Completion states every owner's decision, publishing nowhere
            # included, so no later reader is left to answer it differently.
            metadata.setdefault(models.PYTHON_EXPORTS_METADATA, [])
            continue
        exports = metadata.get(models.PYTHON_EXPORTS_METADATA)
        if exports is None:
            # No earlier stage placed this declaration, so it publishes itself
            # in its own namespace. An empty list is not that: it is a stage
            # having decided the declaration publishes nothing.
            exports = [{"namespace": (), "name": None}]
            metadata[models.PYTHON_EXPORTS_METADATA] = exports
        category = _owner_category(owner)
        for export in exports:
            namespace = export_namespace(export)
            raw_name = owner.name if export.get("name") is None else export["name"]
            resolved_name = naming.reserve_public_name(
                namespace,
                raw_name,
                category="function" if contract_named else category,
                owner=f"{category} {owner.name}",
            )
            export["name"] = resolved_name
    # A nested class is bound on its parent class, never in a namespace.
    for parent in _all_classes(module.classes):
        for nested in parent.classes:
            nested.metadata.setdefault(models.PYTHON_EXPORTS_METADATA, [])
    _complete_reexport_names(module, naming, contract_named=contract_named)
    _complete_contract_names(
        module,
        strict_wrapper_names=strict_wrapper_names,
        contract_named=contract_named,
    )


#: Entity kinds a second namespace cannot publish, whatever it may reach.
#:
#: A generic dispatcher has no single object another namespace can bind, so it
#: is published where it is declared and nowhere else. An intrinsic module's
#: name has no declaration at all, so nothing is there to publish.
UNPUBLISHABLE_REEXPORT_KINDS = frozenset({"generic", "intrinsic"})


def complete_reexport_publication_policy(
    module: models.SemanticModule,
    *,
    contract_named: bool | None = None,
) -> None:
    """Complete which public use associations become Python publications.

    Native Fortran keeps declaration dependencies semantically accessible but
    does not expose them in the generated Python namespace unless an explicit
    ``public`` statement names them. A loaded contract has already stated its
    export surface, so every re-export record constructed from that surface is
    published.

    A generic is reachable through the importing module like any other name,
    but it dispatches rather than naming one object, so PRIK publishes it in
    its declaring namespace alone. That is a publication decision, settled here
    once, rather than an accessibility one.
    """
    if contract_named is None:
        contract_named = bool(module.metadata.get(PYI_LOADED_METADATA))
    for reexport in module.reexports:
        if reexport.python_exported is not None:
            continue
        if reexport.entity_kind in UNPUBLISHABLE_REEXPORT_KINDS:
            reexport.python_exported = False
            continue
        reexport.python_exported = bool(
            contract_named or not reexport.declaration_dependency or reexport.explicitly_public
        )


def _complete_reexport_names(
    module: models.SemanticModule,
    naming: NamingPolicy,
    *,
    contract_named: bool,
) -> None:
    """Name each use-associated binding in its importing namespace.

    Published associations add runtime attributes; dependency-only associations
    still add contract imports. Both compete with declarations for a Python
    spelling, so the same ledger names them after the module's declarations. A
    dependency keeps an ordinary import-binding spelling even when the entity
    is a type; only a published type receives class-style capitalization.
    """
    for reexport in module.reexports:
        if reexport.python_name:
            continue
        published = reexport.publishes_to_python()
        if published and reexport.entity_kind == "variable":
            completed_name = _completed_variable_reexport_name(module, reexport)
            if completed_name is not None:
                reexport.python_name = completed_name
                continue
        category = (
            {
                "derived_type": "class",
                "variable": "variable",
            }.get(reexport.entity_kind, "function")
            if published
            else "function"
        )
        reexport.python_name = naming.reserve_public_name(
            _reexport_namespace(module, reexport),
            reexport.local_name,
            category="function" if contract_named else category,
            owner=f"re-export {reexport.local_name}",
        )


def _completed_variable_reexport_name(
    module: models.SemanticModule,
    reexport: models.SemanticReexport,
) -> str | None:
    """Read a variable re-export name from its declaring variable policy.

    A merged source build contains the declaring variable, whose export list is
    the authority for every publication. Contract extraction may emit an
    importing module separately, in which case the declaration is unavailable
    and the re-export is named locally instead.
    """
    wanted_module = str(reexport.origin_module).casefold()
    wanted_name = str(reexport.source_name).casefold()
    namespace = _reexport_namespace(module, reexport)
    for variable in module.variables:
        native_module = str(variable.origin.native_scope or "").casefold()
        native_name = str(variable.origin.native_name or variable.name).casefold()
        if native_module != wanted_module or native_name != wanted_name:
            continue
        for export in variable.metadata.get(models.PYTHON_EXPORTS_METADATA, ()):
            if export_namespace(export) == namespace and export.get("name") is not None:
                return str(export["name"])
    return None


def _placement_namespace(module: models.SemanticModule, scope: object) -> tuple[str, ...]:
    """Return the namespace a name written by module ``scope`` is placed in.

    Completing that same module places it at the module's own root. Completing
    a merged package -- a build folds every source module into one -- places it
    inside the namespace that module occupies there, beside the declarations it
    sits with, so names from two modules never compete for one spelling.
    """
    declaring = str(scope or "")
    if not declaring or declaring.casefold() == str(module.name).casefold():
        return ()
    return tuple(part.casefold() for part in declaring.split(".") if part)


def _reexport_namespace(module: models.SemanticModule, reexport: models.SemanticReexport) -> tuple[str, ...]:
    """Return the Python namespace one re-export publishes into: its publisher's."""
    return _placement_namespace(module, reexport.module)


def _declaring_namespace(module: models.SemanticModule, owner) -> tuple[str, ...]:
    """Return the namespace of the module one declaration is written in."""
    scope = owner.native_scope if isinstance(owner, models.ProcedureOverloadSet) else owner.origin.native_scope
    return _placement_namespace(module, scope)


def _module_export_owners(module: models.SemanticModule):
    """Return public-name owners in the same order as semantic lowering."""
    return (*module.classes, *module.functions, *module.overload_sets, *module.variables)


def _complete_contract_names(
    module: models.SemanticModule,
    *,
    strict_wrapper_names: bool,
    contract_named: bool,
) -> None:
    """Record every declaration spelling consumed by contract emission.

    A name has to be unique among the names written in one contract, so each
    is held where it is placed: a published declaration in the namespace its
    export completed, a re-export in its publisher's, a withheld declaration
    in the file being completed. A build folds every source module into one,
    and placing by those authorities keeps two modules' names apart there.
    Published spellings are held first, so a withheld helper cannot move a
    public API aside; each class then gets one member ledger, shared with
    class-surface policy.
    """
    preserve_case = contract_named or preserves_source_case(module.origin.source_language)
    naming = NamingPolicy(strict_public_names=strict_wrapper_names, preserve_case=preserve_case)
    owners = _module_export_owners(module)

    for owner in owners:
        placed = _own_export(module, owner)
        if placed is None:
            continue
        namespace, completed = placed
        naming.hold_completed_public_name(
            namespace,
            completed,
            category=_owner_category(owner),
            owner=f"{_owner_category(owner)} {owner.name}",
        )
        owner.metadata[models.CONTRACT_NAME_METADATA] = completed

    # Imports bind names in the same contract namespace as declarations. Their
    # export spelling was already settled against public declarations; holding
    # it here prevents a withheld declaration from taking the binding.
    for reexport in module.reexports:
        if reexport.python_name:
            naming.hold_completed_public_name(
                _reexport_namespace(module, reexport),
                reexport.python_name,
                category="function",
                owner=f"re-export {reexport.local_name}",
            )

    for prototype in module.prototypes:
        completed = str(prototype.name)
        naming.hold_completed_public_name(
            _declaring_namespace(module, prototype),
            completed,
            category="function",
            owner=f"prototype {prototype.native_name or prototype.name}",
        )
        prototype.metadata[models.CONTRACT_NAME_METADATA] = completed

    # A withheld declaration is written in the file being completed, whatever
    # module declared it natively: a generic's inherited specifics are carried
    # into the facade that extends it, beside each other.
    for owner in owners:
        if owner.metadata.get(models.CONTRACT_NAME_METADATA) is not None:
            continue
        owner.metadata[models.CONTRACT_NAME_METADATA] = naming.reserve_public_name(
            (),
            owner.name,
            category=_owner_category(owner),
            owner=f"{_owner_category(owner)} {owner.name}",
        )

    for semantic_class in module.classes:
        _complete_class_member_contract_names(
            semantic_class,
            (*_declaring_namespace(module, semantic_class), models.completed_contract_name(semantic_class)),
            strict_wrapper_names=strict_wrapper_names,
            preserve_case=preserve_case,
        )

    _complete_local_type_contract_names(module)
    _complete_overload_target_contract_names(module, preserve_case=preserve_case)


def _own_export(module: models.SemanticModule, owner) -> tuple[tuple[str, ...], str] | None:
    """Return the namespace and spelling one declaration is published under at home.

    Its home is the namespace of the module it is written in, or the root of
    the file being completed; an export elsewhere is a second publication of
    it, which names nothing in its own contract.
    """
    home = {(), _declaring_namespace(module, owner)}
    for export in _owner_metadata(owner).get(models.PYTHON_EXPORTS_METADATA, ()) or ():
        if not isinstance(export, dict) or export.get("name") is None:
            continue
        namespace = tuple(part.casefold() for part in export_namespace(export))
        if namespace in home:
            return namespace, str(export["name"])
    return None


def _all_classes(classes: list[models.SemanticClass]):
    """Yield every class, each followed by the classes nested inside it."""
    for semantic_class in classes:
        yield semantic_class
        yield from _all_classes(semantic_class.classes)


def _complete_class_member_contract_names(
    semantic_class: models.SemanticClass,
    namespace: tuple[str, ...],
    *,
    strict_wrapper_names: bool,
    preserve_case: bool,
) -> None:
    """Complete one class's field, method, and overload spellings once."""
    naming = NamingPolicy(strict_public_names=strict_wrapper_names, preserve_case=preserve_case)
    for field in semantic_class.fields:
        field.metadata[models.CONTRACT_NAME_METADATA] = naming.reserve_public_name(
            namespace,
            field.name,
            category="field",
            owner=field.name,
        )
    for method in semantic_class.methods:
        if method.name.startswith("__"):
            method.metadata[models.CONTRACT_NAME_METADATA] = method.name
            continue
        method.metadata[models.CONTRACT_NAME_METADATA] = naming.reserve_public_name(
            namespace,
            method.name,
            category="function",
            owner=method.name,
        )
    for overload in semantic_class.overload_sets:
        source_names = tuple(
            dict.fromkeys(
                str(procedure.metadata.get(models.PYTHON_METHOD_NAME_METADATA, overload.name))
                for procedure in overload.procedures
            )
        ) or (str(overload.name),)
        for source_name in source_names:
            completed = naming.reserve_public_name(
                namespace,
                source_name,
                category="function",
                owner=source_name,
            )
            overload.metadata.setdefault(models.CONTRACT_NAME_METADATA, completed)
            for procedure in overload.procedures:
                procedure_name = str(procedure.metadata.get(models.PYTHON_METHOD_NAME_METADATA, overload.name))
                if procedure_name == source_name:
                    procedure.metadata[models.CONTRACT_NAME_METADATA] = completed
    # A nested class is written inside its parent, so it is named among the
    # parent's members and its own members get a ledger beneath that name.
    for nested in semantic_class.classes:
        nested.metadata[models.CONTRACT_NAME_METADATA] = naming.reserve_public_name(
            namespace,
            nested.name,
            category="class",
            owner=nested.name,
        )
        _complete_class_member_contract_names(
            nested,
            (*namespace, models.completed_contract_name(nested)),
            strict_wrapper_names=strict_wrapper_names,
            preserve_case=preserve_case,
        )


def _complete_local_type_contract_names(module: models.SemanticModule) -> None:
    """Attach local class spellings to every semantic type that names one."""
    by_exact = {str(cls.name): models.completed_contract_name(cls) for cls in _all_classes(module.classes)}
    by_folded: dict[str, list[str]] = {}
    for source, completed in by_exact.items():
        by_folded.setdefault(source.casefold(), []).append(completed)
    for semantic_type in models._module_semantic_types(module):
        completed = by_exact.get(str(semantic_type.name))
        if completed is None:
            matches = by_folded.get(str(semantic_type.name).casefold(), ())
            completed = matches[0] if len(matches) == 1 else None
        if completed is not None:
            semantic_type.metadata[models.CONTRACT_NAME_METADATA] = completed
    for semantic_class in _all_classes(module.classes):
        semantic_class.metadata[models.CONTRACT_BASE_NAMES_METADATA] = {
            base: by_exact.get(base, base) for base in semantic_class.base_classes
        }


def _complete_overload_target_contract_names(
    module: models.SemanticModule,
    *,
    preserve_case: bool,
) -> None:
    """Resolve overload targets to the contract spelling of their specific.

    A target is written the way the contract's reader resolves it: against the
    module's own procedures first, then the methods of the type whose generic
    it is. One procedure can be declared both ways -- ``counter_add_integer``
    at module level, ``add_integer`` as the method binding it -- and they are
    reached differently, so the contract has to name the one its reader finds.
    """
    _name_overload_targets(module.overload_sets, (module.functions,), preserve_case=preserve_case)
    for semantic_class in _all_classes(module.classes):
        _name_overload_targets(
            semantic_class.overload_sets,
            (module.functions, semantic_class.methods),
            preserve_case=preserve_case,
        )


def _name_overload_targets(
    overloads: list[models.ProcedureOverloadSet],
    specific_groups: tuple[list[models.SemanticFunction], ...],
    *,
    preserve_case: bool,
) -> None:
    """Record, on each candidate, the spelling its specific is declared under."""
    by_identity: dict[tuple[str, str], str] = {}
    by_source: dict[str, str] = {}
    for specifics in specific_groups:
        for specific in specifics:
            identity = _specific_identity(specific)
            if identity is not None:
                by_identity.setdefault(identity, models.completed_contract_name(specific))
            by_source.setdefault(str(specific.name), models.completed_contract_name(specific))
    for overload in overloads:
        for candidate in overload.procedures:
            target = str(
                candidate.metadata.get(models.OVERLOAD_TARGET_METADATA) or candidate.native_name or candidate.name
            )
            scope = str(candidate.origin.native_scope or "").casefold()
            completed = by_identity.get((scope, target.casefold())) or by_source.get(target)
            if completed is None:
                completed = normalize_public_name(target, preserve_case=preserve_case).name
            candidate.metadata[models.CONTRACT_TARGET_NAME_METADATA] = completed


def _specific_identity(function: models.SemanticFunction) -> tuple[str, str] | None:
    """Return the native declaration identity used by an overload target."""
    scope = str(function.origin.native_scope or "")
    native = str(function.native_name or function.name)
    if not scope or not native:
        return None
    return scope.casefold(), native.casefold()


def contract_names_by_source(module: models.SemanticModule) -> dict[str, str]:
    """Return source spellings mapped to the names this contract declares."""
    names = {str(owner.name): models.completed_contract_name(owner) for owner in _module_export_owners(module)}
    names.update((str(prototype.name), models.completed_contract_name(prototype)) for prototype in module.prototypes)
    names.update(
        (str(reexport.local_name), str(reexport.python_name or reexport.local_name)) for reexport in module.reexports
    )
    return names


def _owner_metadata(owner) -> dict[str, object]:
    """Return the metadata mapping that owns one export policy."""
    if isinstance(owner, models.ProcedureOverloadSet):
        return owner.procedures[0].metadata if owner.procedures else {}
    return owner.metadata


def _owner_category(owner) -> str:
    """Return the public-name category used for collision diagnostics."""
    if isinstance(owner, models.SemanticVariable):
        return "variable"
    if isinstance(owner, models.SemanticClass):
        return "class"
    return "function"


def completed_python_exports(owner) -> tuple[PythonExportPolicy, ...]:
    """Return the placements completion recorded for one declaration.

    This reads the decision and never makes it. Completion records one for
    every declaration it reaches, publishing nowhere included, so an empty
    result is an answer; a missing one means completion never ran.
    """
    recorded = owner.metadata.get(models.PYTHON_EXPORTS_METADATA)
    if recorded is None:
        raise ValueError(
            f"Python export policy for {owner.name!r} is incomplete; "
            "run complete_semantic_policies before wrapper planning"
        )
    exports = []
    for item in recorded:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if name is None:
            raise ValueError(
                f"Python export policy for {owner.name!r} is incomplete; "
                "run complete_semantic_policies before wrapper planning"
            )
        exports.append(PythonExportPolicy(namespace=export_namespace(item), name=str(name)))
    return tuple(dict.fromkeys(exports))


if __name__ == "__main__":
    example_function = models.SemanticFunction(
        "scale_value",
        native_name="SCALE_VALUE",
        metadata={
            models.PYTHON_EXPORTS_METADATA: [
                {"namespace": ("linear_algebra",), "name": None},
            ]
        },
    )
    example_module = models.SemanticModule("math", functions=[example_function])
    complete_python_export_policy(example_module)
    example_export = completed_python_exports(example_function)[0]

    print(f"Native semantic owner: {example_module.name}.{example_function.native_name}")
    print(f"Python export: {'.'.join((*example_export.namespace, example_export.name))}")
    print(f"Completed policy type: {type(example_export).__name__}")
