"""Completed Python export paths shared by wrapper policy lanes."""

from __future__ import annotations

from dataclasses import dataclass

from prik.naming import NamingPolicy, normalize_public_name
from prik.semantics import models


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
    """Resolve every public export name within its owning Python namespace."""
    naming = NamingPolicy(strict_public_names=strict_wrapper_names)
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
            namespace = _export_namespace(export)
            raw_name = owner.name if export.get("name") is None else export["name"]
            resolved_name = naming.reserve_public_name(
                namespace,
                raw_name,
                category=category,
                owner=f"{category} {owner.name}",
            )
            if export.get("name") is None:
                export["name"] = resolved_name


def _module_export_owners(module: models.SemanticModule):
    """Yield public-name owners in the same order as semantic lowering."""
    yield from module.classes
    yield from module.functions
    yield from module.overload_sets
    yield from module.variables


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


def _export_namespace(export: dict[str, object]) -> tuple[str, ...]:
    """Return one normalized namespace tuple from semantic export metadata."""
    raw_namespace = export.get("namespace", ())
    if not isinstance(raw_namespace, tuple | list):
        return ()
    return tuple(str(part) for part in raw_namespace)


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
                namespace=_export_namespace(item),
                name=str(name),
            )
        )
    if not exports and getattr(owner, "visibility", "public") != "private":
        exports.append(PythonExportPolicy((), normalize_public_name(default_name).name))
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
