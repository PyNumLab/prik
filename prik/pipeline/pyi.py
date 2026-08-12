"""Convert semantic `.pyi` text, files, and path sets into semantic IR."""

from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

from prik.parsers.pyi import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.printers.pyi import emit_module
from prik.semantics.models import EXTERNAL_TYPE_REF_METADATA, SemanticClass, SemanticModule, _iter_module_semantic_types
from prik.semantics.pyi_metadata import PYI_LOADED_METADATA
from prik.semantics.pyi2ir import convert_pyi_to_ir, reconcile_external_type_refs

__all__ = (
    "emit_module_stubs",
    "opaque_dependency_modules",
    "pyi_file_to_semantic_module",
    "pyi_paths_to_semantic_modules",
    "pyi_text_to_semantic_module",
)


def _module_list(modules: SemanticModule | Iterable[SemanticModule] | None) -> list[SemanticModule]:
    """Normalize one semantic module or an iterable to a list."""
    if modules is None:
        return []
    if isinstance(modules, SemanticModule):
        return [modules]
    return list(modules)


def _opaque_dependency_class(type_name: str, c_kind: str | None) -> SemanticClass:
    """Build the semantic placeholder for one missing opaque dependency."""
    base_classes: list[str] = []
    metadata: dict[str, object] = {"representation": "opaque"}
    if c_kind == "struct":
        base_classes.append("CStruct")
        metadata["c_kind"] = "struct"
    elif c_kind == "union":
        base_classes.append("CUnion")
        metadata["c_kind"] = "union"
    base_classes.append("Opaque")
    return SemanticClass(
        name=type_name,
        native_name=type_name,
        base_classes=base_classes,
        metadata=metadata,
    )


def opaque_dependency_modules(
    modules: SemanticModule | Iterable[SemanticModule],
    *,
    available_modules: Iterable[SemanticModule] | None = None,
) -> list[SemanticModule]:
    """Build semantic modules for opaque types referenced but not supplied.

    Use this before package emission when a contract refers to C opaque types
    from absent modules. The input modules are inspected but not mutated; the
    returned list is ordered deterministically by module and type name.
    """
    source_modules = _module_list(modules)
    known_modules = _module_list(available_modules) if available_modules is not None else source_modules
    known_classes = {
        (module.name, cls.name) for module in known_modules for cls in module.classes if isinstance(cls, SemanticClass)
    }
    dependencies: dict[str, dict[str, str | None]] = {}
    for module in source_modules:
        for semantic_type in _iter_module_semantic_types(module):
            ref = semantic_type.metadata.get(EXTERNAL_TYPE_REF_METADATA)
            if not isinstance(ref, dict) or ref.get("representation") != "opaque":
                continue
            origin_module = ref.get("origin_module")
            type_name = ref.get("name")
            if not isinstance(origin_module, str) or not isinstance(type_name, str):
                continue
            if (origin_module, type_name) in known_classes:
                continue
            c_kind = semantic_type.metadata.get("c_kind")
            dependencies.setdefault(origin_module, {}).setdefault(
                type_name,
                c_kind if c_kind in {"struct", "union"} else None,
            )
    return [
        SemanticModule(
            name=module_name,
            classes=[_opaque_dependency_class(type_name, c_kind) for type_name, c_kind in sorted(type_kinds.items())],
        )
        for module_name, type_kinds in sorted(dependencies.items())
    ]


def emit_module_stubs(
    modules: SemanticModule | Iterable[SemanticModule],
    *,
    available_modules: Iterable[SemanticModule] | None = None,
    normalize_fortran_public_names: bool = False,
) -> dict[str, str]:
    """Complete and render semantic modules plus opaque dependencies.

    Inputs are deep-copied before dependency insertion and policy completion,
    so callers retain their original semantic modules. The returned mapping is
    keyed by module name and is normally written into a generated contract
    package by a pipeline stage.
    """
    source_modules = _module_list(modules)
    emitted_modules: dict[str, SemanticModule] = {}
    for module in source_modules:
        if module.name in emitted_modules:
            raise ValueError(f"Cannot emit duplicate semantic module '{module.name}'")
        emitted_modules[module.name] = deepcopy(module)

    for dependency in opaque_dependency_modules(
        source_modules,
        available_modules=available_modules,
    ):
        target = emitted_modules.setdefault(dependency.name, SemanticModule(name=dependency.name))
        existing = {cls.name for cls in target.classes}
        target.classes.extend(cls for cls in dependency.classes if cls.name not in existing)

    complete_semantic_policies(emitted_modules.values())
    return {
        module_name: emit_module(
            module,
            normalize_fortran_public_names=normalize_fortran_public_names,
        ).strip()
        for module_name, module in emitted_modules.items()
    }


@dataclass
class _PyiSemanticModuleCache:
    modules: dict[tuple[Path, str, str, str], SemanticModule] = field(default_factory=dict)

    def file_to_semantic_module(
        self,
        path: str | Path,
        *,
        module_name: str | None = None,
        encoding: str = "utf-8",
        native_language: str = "fortran",
    ) -> SemanticModule:
        pyi_path = Path(path)
        resolved_module_name = module_name or pyi_path.stem
        key = (pyi_path.resolve(), resolved_module_name, encoding, native_language)
        cached = self.modules.get(key)
        if cached is not None:
            return cached
        try:
            source = pyi_path.read_text(encoding=encoding)
            module = pyi_text_to_semantic_module(
                source,
                module_name=resolved_module_name,
                filename=str(pyi_path),
                native_language=native_language,
            )
        except ValueError as exc:
            raise ValueError(f"{pyi_path}: {exc}") from exc
        self.modules[key] = module
        return module

    def paths_to_semantic_modules(
        self,
        paths: str | Path | Iterable[str | Path],
        *,
        encoding: str = "utf-8",
        native_language: str = "fortran",
    ) -> list[SemanticModule]:
        raw_paths = [paths] if isinstance(paths, str | Path) else list(paths)
        expanded: dict[Path, str | None] = {}
        for raw_path in raw_paths:
            path = Path(raw_path)
            if path.is_dir():
                for item in path.rglob("*.pyi"):
                    if not item.is_file():
                        continue
                    module_name = ".".join(item.relative_to(path).with_suffix("").parts)
                    previous = expanded.get(item)
                    if previous is not None and previous != module_name:
                        raise ValueError(f"Ambiguous module name for {item}: {previous!r} or {module_name!r}")
                    expanded[item] = module_name
            else:
                expanded.setdefault(path, None)
        return reconcile_external_type_refs(
            [
                self.file_to_semantic_module(
                    path,
                    module_name=module_name,
                    encoding=encoding,
                    native_language=native_language,
                )
                for path, module_name in sorted(expanded.items())
            ]
        )


def pyi_text_to_semantic_module(
    source: str,
    *,
    module_name: str = "<pyi>",
    filename: str = "<pyi>",
    native_language: str = "fortran",
) -> SemanticModule:
    """Parse inline semantic `.pyi` text and convert it to semantic IR."""

    tree = parse_pyi_text(source, filename=filename)
    module = convert_pyi_to_ir(
        tree,
        module_name=module_name,
        source=source,
        native_language=native_language,
    )
    module.metadata[PYI_LOADED_METADATA] = True
    return module


def pyi_file_to_semantic_module(
    path: str | Path,
    *,
    module_name: str | None = None,
    encoding: str = "utf-8",
    native_language: str = "fortran",
) -> SemanticModule:
    """Convert one semantic `.pyi` file to semantic IR."""
    return _PyiSemanticModuleCache().file_to_semantic_module(
        path,
        module_name=module_name,
        encoding=encoding,
        native_language=native_language,
    )


def pyi_paths_to_semantic_modules(
    paths: str | Path | Iterable[str | Path],
    *,
    encoding: str = "utf-8",
    native_language: str = "fortran",
) -> list[SemanticModule]:
    """Convert semantic `.pyi` files or directories and reconcile external types."""
    return _PyiSemanticModuleCache().paths_to_semantic_modules(
        paths,
        encoding=encoding,
        native_language=native_language,
    )
