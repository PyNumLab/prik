"""Native sources to semantic IR: the one route builds and generated contracts share.

A wrapper build and ``prik generate`` both turn Fortran sources into semantic
modules, and they must turn the same sources into the same modules, or a
contract generated from a project would describe something other than what a
build of that project wraps. Both therefore read, parse, measure, convert,
and select exports here, and differ only in what they do with the result.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from prik.parsers.fortran.models import FortranProject
from prik.parsers.fortran.module_sources import resolve_fortran_module_sources
from prik.parsers.fortran.parser import parse_fortran_project
from prik.preprocessing import PreprocessingConfig, read_fortran_source
from prik.preprocessing.probes.fortran_types import (
    evaluate_fortran_type_facts,
    evaluate_fortran_type_requirements,
)
from prik.semantics.models import SemanticModule
from prik.semantics.fortran2ir import (
    collect_fortran_type_storage_requirements,
    collect_semantic_compile_time_requirements,
    fortran_project_to_semantic_files,
)


@dataclass(frozen=True)
class FortranTypeProbe:
    """How compiler-dependent Fortran values and type storage are measured.

    ``preprocessing`` selects the compiler and target flags the probe runs
    with; without a compiler, and without a ``report`` to read instead, no
    probe runs and those facts stay symbolic.
    """

    preprocessing: PreprocessingConfig
    report: object | None = None
    runner: list[str] | None = None
    cache_dir: str | Path | None = None
    refresh: bool = False

    @property
    def available(self) -> bool:
        """Return whether a report or a compiler can answer the probe."""
        return self.report is not None or (self.preprocessing.uses_compiler and bool(self.preprocessing.compiler))

    def options(self) -> dict[str, object]:
        """Return the evaluator options this probe states."""
        options: dict[str, object] = {}
        if self.report is not None:
            options["report"] = self.report
        if self.runner is not None:
            options["runner"] = self.runner
        if self.cache_dir is not None:
            options["cache_dir"] = self.cache_dir
        if self.refresh:
            options["refresh"] = True
        return options


@dataclass(frozen=True)
class FortranSemanticSources:
    """Fortran sources read, parsed, measured, converted, and selected.

    ``files`` pairs each source, in the order named, with its semantic
    modules, which are the selected ones when symbols were selected.
    ``modules`` is every module a consumer needs, in project order, and
    ``context_modules`` those among them only reached as selection context.
    """

    project: FortranProject
    files: tuple[tuple[Path, tuple[SemanticModule, ...]], ...]
    modules: tuple[SemanticModule, ...]
    context_modules: tuple[SemanticModule, ...] = ()
    recipes: Mapping[Path, dict[str, object] | None] = field(default_factory=dict)
    dependencies: tuple[Path, ...] = ()


def discover_fortran_sources(
    entries: Sequence[Path],
    module_source_dirs: Iterable[Path],
    preprocessing: PreprocessingConfig,
) -> tuple[Path, ...]:
    """Return ``entries`` with every source of a module they use, dependencies first."""
    return resolve_fortran_module_sources(
        entries,
        tuple(Path(directory) for directory in module_source_dirs),
        lambda path: read_fortran_source(path, preprocessing).source,
        command_line_macros=preprocessing.defines_command_line_macros,
    )


def fortran_sources_to_semantic_modules(
    source_paths: Sequence[Path],
    preprocessing: PreprocessingConfig,
    *,
    probe: FortranTypeProbe | None = None,
    assume_intent_in_scalars: bool = False,
    export_symbols: Iterable[str] | None = None,
) -> FortranSemanticSources:
    """Turn Fortran sources into the semantic modules a build or a contract uses.

    The sources are read under ``preprocessing`` and parsed as one project,
    ordered by their dependencies. Compile-time values and type storage are
    measured with ``probe``, which defaults to ``preprocessing``, and every
    file is converted with the whole project as context. ``export_symbols``,
    when given, narrows each file to the selected symbols and keeps the rest
    as context.
    """
    paths = tuple(Path(path) for path in source_paths)
    texts = {path: read_fortran_source(path, preprocessing) for path in paths}
    project = parse_fortran_project({str(path): text.source for path, text in texts.items()})
    probe = probe or FortranTypeProbe(preprocessing)
    compile_time_values = _compile_time_values(project, probe)
    type_facts = _type_facts(project, probe, compile_time_values)

    converted = fortran_project_to_semantic_files(
        project,
        compile_time_values=compile_time_values,
        assume_intent_in_scalars=assume_intent_in_scalars,
        **({"type_facts": type_facts} if type_facts is not None else {}),
    )
    by_path = {Path(str(parsed.filename)): tuple(modules) for parsed, modules in converted}
    files = tuple((path, by_path[path]) for path in paths)
    modules = tuple(module for _parsed, file_modules in converted for module in file_modules)
    context_modules: tuple[SemanticModule, ...] = ()
    if export_symbols is not None:
        from prik.semantics.fortran_exports import select_fortran_export_symbols

        selection = select_fortran_export_symbols(modules, export_symbols)
        selected = {
            id(source): module
            for source, module in zip(selection.primary_sources, selection.primary_modules, strict=True)
        }
        files = tuple(
            (path, chosen)
            for path, file_modules in files
            if (chosen := tuple(selected[id(module)] for module in file_modules if id(module) in selected))
        )
        modules = tuple(selection.available_modules)
        context_modules = tuple(selection.context_modules)

    return FortranSemanticSources(
        project=project,
        files=files,
        modules=modules,
        context_modules=context_modules,
        recipes={path: text.recipe for path, text in texts.items()},
        dependencies=tuple(
            dict.fromkeys(
                dependency
                for path, text in texts.items()
                for dependency in semantic_dependency_paths(path, text.included_files)
            )
        ),
    )


def semantic_dependency_paths(root: Path, included_files: Iterable[object]) -> tuple[Path, ...]:
    """Return one source and every existing file its preprocessing read, in stable order."""
    dependencies = [root.resolve(strict=False)]
    for item in included_files:
        raw_path = item.get("path") if isinstance(item, Mapping) else getattr(item, "path", None)
        if not isinstance(raw_path, str | Path) or str(raw_path).startswith("<"):
            continue
        path = Path(raw_path)
        if not path.is_absolute():
            path = root.parent / path
        path = path.resolve(strict=False)
        if path.is_file():
            dependencies.append(path)
    return tuple(dict.fromkeys(dependencies))


def _compile_time_values(project: FortranProject, probe: FortranTypeProbe) -> dict[str, int] | None:
    """Measure the compile-time values the project's declarations need, if any."""
    if not probe.available:
        return None
    requirements = collect_semantic_compile_time_requirements(project)
    if not requirements:
        return None
    return evaluate_fortran_type_requirements(probe.preprocessing, requirements, **probe.options())


def _type_facts(
    project: FortranProject,
    probe: FortranTypeProbe,
    compile_time_values: dict[str, int] | None,
) -> dict[tuple[str, str | None], dict[str, object]] | None:
    """Measure the native storage of the intrinsic types the project uses, if any."""
    if not probe.available:
        return None
    requirements = collect_fortran_type_storage_requirements(project, compile_time_values=compile_time_values)
    if not requirements:
        return None
    return evaluate_fortran_type_facts(probe.preprocessing, requirements, **probe.options())
