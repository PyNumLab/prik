"""Convert semantic `.pyi` text, files, and path sets into semantic IR."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from prik.parsers.pyi import parse_pyi_text
from prik.semantics.models import SemanticModule
from prik.semantics.pyi_metadata import PYI_LOADED_METADATA
from prik.semantics.pyi2ir import convert_pyi_to_ir, reconcile_external_type_refs

__all__ = ("pyi_file_to_semantic_module", "pyi_paths_to_semantic_modules", "pyi_text_to_semantic_module")


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
