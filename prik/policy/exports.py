"""Resolve Python export names for later wrapper-policy construction.

``complete_python_export_policy`` walks public semantic declarations in their
lowering order, normalizes their requested names, and reserves one name in each
Python namespace. It writes the completed names back to semantic metadata so
all policy constructors see the same collision-checked result.

``completed_python_exports`` retrieves that metadata as immutable
``PythonExportPolicy`` records while wrapper policy is assembled. This module
decides Python placement only: it does not choose a wrapper mechanism or emit
the namespace.
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
    """
    contract_named = bool(module.metadata.get(PYI_LOADED_METADATA))
    complete_reexport_publication_policy(module, contract_named=contract_named)
    naming = NamingPolicy(
        strict_public_names=strict_wrapper_names,
        preserve_case=contract_named or preserves_source_case(module.origin.source_language),
    )
    for owner in _module_export_owners(module):
        if getattr(owner, "visibility", "public") == "private":
            continue
        metadata = _owner_metadata(owner)
        exports = metadata.get(models.PYTHON_EXPORTS_METADATA)
        if not exports:
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
    _complete_reexport_names(module, naming, contract_named=contract_named)


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
    """
    if contract_named is None:
        contract_named = bool(module.metadata.get(PYI_LOADED_METADATA))
    for reexport in module.reexports:
        if reexport.python_exported is not None:
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


def _reexport_namespace(module: models.SemanticModule, reexport: models.SemanticReexport) -> tuple[str, ...]:
    """Return the Python namespace one re-export publishes into.

    A re-export names the module publishing it. Completing that same module
    names it against the module's own root, which is where its declarations
    are; completing a merged package instead names it inside the namespace
    that module occupies there, beside the declarations it sits with.
    """
    publisher = str(reexport.module or "")
    if not publisher or publisher.casefold() == str(module.name).casefold():
        return ()
    return tuple(part.casefold() for part in publisher.split(".") if part)


def _module_export_owners(module: models.SemanticModule):
    """Return public-name owners in the same order as semantic lowering."""
    return (*module.classes, *module.functions, *module.overload_sets, *module.variables)


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


def completed_python_exports(
    owner: models.SemanticFunction | models.SemanticVariable,
    default_name: str,
) -> tuple[PythonExportPolicy, ...]:
    """Return stable local names grouped by their completed namespace path."""
    exports = []
    for item in owner.metadata.get(models.PYTHON_EXPORTS_METADATA, ()):
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if name is None:
            raise ValueError(
                f"Python export policy for {owner.name!r} is incomplete; "
                "run complete_semantic_policies before wrapper planning"
            )
        exports.append(
            PythonExportPolicy(
                namespace=export_namespace(item),
                name=str(name),
            )
        )
    if not exports and getattr(owner, "visibility", "public") != "private":
        fallback = normalize_public_name(
            default_name,
            preserve_case=preserves_source_case(owner.origin.source_language),
            category=_owner_category(owner),
        )
        exports.append(PythonExportPolicy((), fallback.name))
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
    example_export = completed_python_exports(example_function, example_function.name)[0]

    print(f"Native semantic owner: {example_module.name}.{example_function.native_name}")
    print(f"Python export: {'.'.join((*example_export.namespace, example_export.name))}")
    print(f"Completed policy type: {type(example_export).__name__}")
