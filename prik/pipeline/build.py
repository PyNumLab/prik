"""Orchestrate source-first and contract-first extension builds.

The public boundary is the build records plus ``build_fortran_extension()``,
``build_pyi_extension()``, and ``build_pyi_extension_from_manifest()``. Each
entrypoint prepares semantic input, completes policy, plans and renders a
wrapper, materializes its sources, prepares native inputs, then returns a
``WrapperBuildResult`` after compilation, source-only output, or Makefile
generation.

Private helpers are grouped by configuration, generated-wrapper materialization,
native scheduling, source and contract inputs, `.pyi` loading and export
projection, native planning, manifest handling, wrapper assembly, Makefile
output, type probing, and semantic preparation. Read from a public entrypoint
to the phase it calls; this module delegates language meaning, policy, lowering,
printing, and compiler command construction to their owning stages.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import shlex
import sys
import time
from types import ModuleType

from prik.compiler.objects import ObjectFile
from prik.compiler.compilers import Compiler, get_condaless_search_path
from prik.compiler.native_support import install_native_support
from prik.parsers.fortran.parser import parse_fortran_project
from prik.preprocessing.probes.fortran_types import (
    evaluate_fortran_type_facts,
    evaluate_fortran_type_requirements,
    resolve_fortran_logical_storage_types,
)
from prik.preprocessing import PreprocessingConfig, preprocess_source
from prik.pipeline.pyi import emit_module_stubs
from prik.pipeline.wrapper import GeneratedSource, GeneratedWrapper, WrapperGenerator
from prik.semantics.fortran2ir import (
    collect_fortran_type_storage_requirements,
    collect_semantic_compile_time_requirements,
    fortran_project_to_semantic_modules,
)
from prik.semantics.models import (
    PYTHON_EXPORTS_METADATA,
    PYTHON_EXPORTS_PREPARED_METADATA,
    ProcedureOverloadSet,
    SemanticClass,
    SemanticFunction,
    SemanticImport,
    SemanticModule,
    SemanticPrototype,
    SemanticVariable,
    _module_semantic_types,
)
from prik.semantics.native_contract import NATIVE_CONTRACT_PREPARED_METADATA, validate_pyi_native_contract
from prik.policy.native_array_handles import (
    NativeArrayBuildRequirements,
    native_array_handle_build_requirements,
)
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.pyi import _PyiSemanticModuleCache
from prik.semantics.pyi_metadata import PYI_LOADED_METADATA
from prik.planning import NativeGeneratedCodeGroupPlan, WrapperPlanner
from prik.semantics.scalar_types import boolean_storage_bits, is_boolean_semantic_type_name


_DEFAULT_BUILD_DIR_NAME = "__prik__"
_BUILD_MANIFEST_NAME = "prik-build.json"
_BUILD_MANIFEST_SCHEMA_VERSION = 3
_FORTRAN_SOURCE_SUFFIXES = {".f", ".f03", ".f08", ".f77", ".f90", ".f95", ".for", ".ftn"}
_C_SOURCE_SUFFIXES = {".c"}
_NATIVE_PATH_LINK_KINDS = frozenset({"object", "archive", "shared_library"})
_NATIVE_LINK_KINDS = frozenset({*_NATIVE_PATH_LINK_KINDS, "named_library", "linker_argument"})
_GENERATED_WRAPPER_SOURCE_LANGUAGES = {
    ".c": "c",
    ".f": "fortran",
    ".f03": "fortran",
    ".f08": "fortran",
    ".f77": "fortran",
    ".f90": "fortran",
    ".f95": "fortran",
    ".for": "fortran",
    ".ftn": "fortran",
}
_GENERATED_WRAPPER_NATIVE_SUPPORT_IMPORTS = {
    "binding_support": ("binding_support/prik_binding",),
}


# Build configuration, timing, and mode validation


def _print_verbose_timing(verbose: bool | int, elapsed: float) -> None:
    """Print the elapsed time for the immediately preceding build operation."""
    if verbose:
        print(f">> Timing: {elapsed:.3f}s")


def _print_verbose_total_build_time(verbose: bool | int, elapsed: float) -> None:
    """Print the completed end-to-end direct-build duration."""
    if verbose:
        print(f">> Total build time: {elapsed:.3f}s")


def _report_total_build_time(
    verbose: bool | int,
    elapsed: float,
    *,
    on_total_build_time: Callable[[float], None] | None,
) -> None:
    """Print or defer the final duration for one successful direct build."""
    if on_total_build_time is not None:
        on_total_build_time(elapsed)
        return
    _print_verbose_total_build_time(verbose, elapsed)


def _print_verbose_step(verbose: bool | int, label: str) -> None:
    """Print one readable build step before it can report a native error."""
    if verbose:
        print(f">> {label}")


def _available_compile_jobs() -> int:
    """Return the processor count available to this build process."""
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:
        return max(1, os.cpu_count() or 1)


def _normalize_compile_jobs(jobs: int | None) -> int:
    """Resolve an optional positive compiler-process limit."""
    if jobs is None:
        return _available_compile_jobs()
    if isinstance(jobs, bool) or not isinstance(jobs, int) or jobs < 1:
        raise ValueError("compile jobs must be a positive integer")
    return jobs


def _resolve_build_mode(
    *,
    makefile: bool,
    generate_sources: bool,
    jobs: int | None,
    verbose: bool | int,
) -> tuple[bool, int]:
    """Validate build-output mode and resolve its compiler job limit."""
    if makefile and generate_sources:
        raise ValueError("source-only and Makefile generation are mutually exclusive")
    generation_only = makefile or generate_sources
    compile_jobs = _normalize_compile_jobs(jobs)
    if generation_only and verbose:
        raise ValueError("source/Makefile generation and verbose direct compilation are separate modes")
    return generation_only, compile_jobs


# Public build records


@dataclass(frozen=True)
class NativeCompilationUnit:
    """Describe one native source file that a wrapper build must compile.

    Use this record to inspect the compilation portion of
    :attr:`WrapperBuildResult.native_build_plan`; callers normally provide the
    corresponding ``native_fortran_sources`` and ``native_fortran_flags`` to a
    build entrypoint rather than construct this record themselves.

    Parameters
    ----------
    source
        Native source path passed to the compiler.
    object_path
        Object path produced in the build directory.
    language
        Compiler language selected for ``source``.
    module_dir, include_dirs, flags
        Module-output location, header/module search paths, and per-source
        compiler flags recorded for reproducible builds.
    """

    source: Path
    object_path: Path
    language: str
    module_dir: Path | None = None
    include_dirs: tuple[Path, ...] = ()
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Normalize path and flag fields after dataclass construction.

        The caller may supply path-like values and any iterable of flags.  The
        frozen record is changed in place with ``Path`` and tuple values so
        later manifest and compiler code can rely on a stable representation.
        """
        object.__setattr__(self, "source", Path(self.source))
        object.__setattr__(self, "object_path", Path(self.object_path))
        if self.module_dir is not None:
            object.__setattr__(self, "module_dir", Path(self.module_dir))
        object.__setattr__(self, "include_dirs", tuple(Path(path) for path in self.include_dirs))
        object.__setattr__(self, "flags", tuple(str(flag) for flag in self.flags))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready representation of this compilation unit.

        Paths become strings and tuples become lists.  The method does not
        write a manifest or modify the compilation unit.
        """
        return {
            "source": str(self.source),
            "object": str(self.object_path),
            "language": self.language,
            "module_dir": str(self.module_dir) if self.module_dir is not None else None,
            "include_dirs": [str(path) for path in self.include_dirs],
            "flags": list(self.flags),
        }


@dataclass(frozen=True)
class NativePrebuiltArtifact:
    """Describe one existing object, archive, or shared library to link.

    Build callers usually pass the artifact path through ``native_objects``.
    This record appears in the resulting native build plan, where ``kind`` is
    one of ``"object"``, ``"archive"``, or ``"shared_library"``.
    """

    path: Path
    kind: str

    def __post_init__(self) -> None:
        """Validate the artifact kind and normalize its path field.

        Raises
        ------
        ValueError
            If ``kind`` cannot be represented as a filesystem link input.
        """
        if self.kind not in _NATIVE_PATH_LINK_KINDS:
            raise ValueError(f"Unsupported native artifact kind: {self.kind!r}")
        object.__setattr__(self, "path", Path(self.path))

    def to_dict(self) -> dict[str, object]:
        """Return the artifact kind and string path for JSON serialization."""
        return {
            "kind": self.kind,
            "path": str(self.path),
        }


@dataclass(frozen=True)
class NativeLinkItem:
    """Describe one ordered linker input for a wrapper extension.

    Pass these records through ``native_link_items`` when link order matters.
    Filesystem items use ``"object"``, ``"archive"``, or
    ``"shared_library"`` with a path value; ``"named_library"`` uses a bare
    library name and ``"linker_argument"`` passes an argument through
    unchanged.
    """

    kind: str
    value: Path | str

    def __post_init__(self) -> None:
        """Validate ``kind`` and normalize its value to a path or string.

        Path-based items retain a ``Path`` for file validation.  Named
        libraries and raw linker arguments retain strings for command output.
        """
        if self.kind not in _NATIVE_LINK_KINDS:
            raise ValueError(f"Unsupported native link item kind: {self.kind!r}")
        if self.kind in _NATIVE_PATH_LINK_KINDS:
            object.__setattr__(self, "value", Path(self.value))
        else:
            object.__setattr__(self, "value", str(self.value))

    def to_dict(self) -> dict[str, object]:
        """Return the item in the dictionary shape accepted by build APIs.

        Path-based kinds use ``path``, named libraries use ``name``, and raw
        arguments use ``argument``.  The record itself remains unchanged.
        """
        if self.kind in _NATIVE_PATH_LINK_KINDS:
            return {
                "kind": self.kind,
                "path": str(self.value),
            }
        if self.kind == "named_library":
            return {
                "kind": self.kind,
                "name": str(self.value),
            }
        return {
            "kind": self.kind,
            "argument": str(self.value),
        }


@dataclass(frozen=True)
class NativeBuildPlan:
    """Record the native compilation and link inputs selected for a build.

    Inspect :attr:`WrapperBuildResult.native_build_plan` to learn which native
    sources will compile, which artifacts and libraries will link, and which
    include or module directories the generated wrapper uses.  It is an
    immutable build report, not a command executor.
    """

    compilation_units: tuple[NativeCompilationUnit, ...] = ()
    produced_objects: tuple[Path, ...] = ()
    prebuilt_artifacts: tuple[NativePrebuiltArtifact, ...] = ()
    module_dirs: tuple[Path, ...] = ()
    include_dirs: tuple[Path, ...] = ()
    library_dirs: tuple[Path, ...] = ()
    link_items: tuple[NativeLinkItem, ...] = ()

    def __post_init__(self) -> None:
        """Normalize every collection and filesystem field in this plan.

        This converts accepted iterable/path-like constructor values to tuples
        and ``Path`` objects.  No files are created, compiled, or linked.
        """
        object.__setattr__(self, "compilation_units", tuple(self.compilation_units))
        object.__setattr__(self, "produced_objects", tuple(Path(path) for path in self.produced_objects))
        object.__setattr__(self, "prebuilt_artifacts", tuple(self.prebuilt_artifacts))
        object.__setattr__(self, "module_dirs", tuple(Path(path) for path in self.module_dirs))
        object.__setattr__(self, "include_dirs", tuple(Path(path) for path in self.include_dirs))
        object.__setattr__(self, "library_dirs", tuple(Path(path) for path in self.library_dirs))
        object.__setattr__(self, "link_items", tuple(self.link_items))

    def to_dict(self) -> dict[str, object]:
        """Return a complete JSON-ready snapshot of the native build plan."""
        return {
            "compilation_units": [unit.to_dict() for unit in self.compilation_units],
            "produced_objects": [str(path) for path in self.produced_objects],
            "prebuilt_artifacts": [artifact.to_dict() for artifact in self.prebuilt_artifacts],
            "module_dirs": [str(path) for path in self.module_dirs],
            "include_dirs": [str(path) for path in self.include_dirs],
            "library_dirs": [str(path) for path in self.library_dirs],
            "link_items": [item.to_dict() for item in self.link_items],
        }


@dataclass(frozen=True)
class WrapperBuildResult:
    """Report the generated artifacts and mode selected by one build call.

    Every public build entrypoint returns this record.  Check ``compiled`` to
    distinguish a built extension from ``generate_sources=True`` or
    ``makefile=True`` output; then use ``shared_library``,
    ``generated_sources``, ``build_makefile``, and ``build_manifest`` as
    applicable.  Call :meth:`import_module` to explicitly load an existing
    extension artifact.  ``native_build_plan`` explains the native inputs that
    were compiled or linked.
    """

    sources: tuple[Path, ...]
    module_name: str
    output_dir: Path
    shared_library: Path
    build_makefile: Path | None
    compiled: bool
    generated_sources: tuple[Path, ...]
    generated_files: tuple[Path, ...]
    native_build_plan: NativeBuildPlan = field(default_factory=NativeBuildPlan)
    build_manifest: Path | None = None
    manifest: dict[str, object] | None = None
    native_generated_code_groups: tuple[NativeGeneratedCodeGroupPlan, ...] = ()

    def import_module(self) -> ModuleType:
        """Import and return this result's built extension module.

        The shared-library artifact is loaded under ``module_name`` without
        changing ``sys.path``.  Direct-build results can be imported
        immediately; source-only and Makefile results become importable after
        their shared-library path exists.  Repeated calls return the cached
        module for the same artifact.  A different module already cached under
        the same name raises ``ImportError`` instead of silently returning it.

        Raises
        ------
        FileNotFoundError
            If ``shared_library`` has not been built yet.
        ImportError
            If Python cannot create a loader for the artifact or the module
            name is already bound to a different module.
        """
        if not self.shared_library.is_file():
            raise FileNotFoundError(f"Built extension not found: {self.shared_library}")

        cached_module = sys.modules.get(self.module_name)
        if cached_module is not None:
            cached_path = getattr(cached_module, "__file__", None)
            if cached_path is not None and Path(cached_path).resolve(strict=False) == self.shared_library.resolve(
                strict=False
            ):
                return cached_module
            raise ImportError(
                f"Cannot import {self.shared_library}: module name {self.module_name!r} "
                f"is already bound to {cached_path!r}"
            )

        spec = spec_from_file_location(self.module_name, self.shared_library)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create an import loader for {self.shared_library}")
        module = module_from_spec(spec)
        sys.modules[self.module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(self.module_name, None)
            raise
        return module

    def to_dict(self) -> dict[str, object]:
        """Return all result paths and nested plans in JSON-ready form.

        This is suitable for logging or caller-owned serialization.  It does
        not write a file, trigger compilation, or mutate the result.
        """
        return {
            "sources": [str(source) for source in self.sources],
            "module_name": self.module_name,
            "output_dir": str(self.output_dir),
            "shared_library": str(self.shared_library),
            "build_makefile": str(self.build_makefile) if self.build_makefile is not None else None,
            "compiled": self.compiled,
            "generated_sources": [str(path) for path in self.generated_sources],
            "generated_files": [str(path) for path in self.generated_files],
            "native_build_plan": self.native_build_plan.to_dict(),
            "build_manifest": str(self.build_manifest) if self.build_manifest is not None else None,
            "manifest": self.manifest,
            "native_generated_code_groups": [
                {
                    "kind": group.kind.value,
                    "language": group.language,
                    "member_keys": list(group.member_keys),
                    "source_paths": list(group.source_paths),
                }
                for group in self.native_generated_code_groups
            ],
        }


# Shared build utilities


def _default_preprocessing_config() -> PreprocessingConfig:
    """Create the default compiler-backed preprocessing configuration.

    The build pipeline calls this only when a caller did not provide a
    ``PreprocessingConfig``.  It returns a fresh configuration for ``gfortran``
    so a build cannot modify shared default lists.
    """
    return PreprocessingConfig(
        mode="compiler",
        compiler="gfortran",
        defines=[],
        include_dirs=[],
    )


def _fortran_source_for_pipeline(path: Path, preprocessing: PreprocessingConfig) -> str:
    """Read one source path in the form required by the Fortran parser.

    Compiler-backed preprocessing produces the expanded source text; other
    modes read UTF-8 text directly.  The helper reads ``path`` but does not
    change the source file or preprocessing configuration.
    """
    if preprocessing.uses_compiler:
        return preprocess_source(path, language="fortran", config=preprocessing).source
    return path.read_text(encoding="utf-8")


def _compiler_flags(flags: Iterable[str] | None) -> tuple[str, ...]:
    """Normalize optional caller compiler flags into an immutable tuple.

    ``None`` becomes an empty tuple and each supplied value becomes a string.
    The helper consumes the iterable without invoking a compiler.
    """
    return tuple(str(flag) for flag in (flags or ()))


def _new_compiler(
    *,
    execute_commands: bool = True,
    debug: bool = False,
    input_compiler: str | None = None,
) -> Compiler:
    """Create the compiler configured for generated wrapper code.

    ``input_compiler`` overrides the default ``gfortran`` executable;
    ``execute_commands`` selects real compilation versus command recording,
    and ``debug`` enables the compiler's debug configuration.  The returned
    compiler has a Conda-free search path and has not run any commands yet.
    """
    return Compiler.from_fortran_executable(
        input_compiler or "gfortran",
        debug=debug,
        execute_commands=execute_commands,
        search_path=get_condaless_search_path("verbose"),
    )


def _validated_wrapper_module_name(requested_name: str | None, default_name: str) -> str:
    """Choose a requested or default extension name and validate it.

    Returns the requested name when present, otherwise ``default_name``.  A
    non-identifier cannot be imported as a Python extension and raises
    ``ValueError`` before files are generated.
    """
    module_name = requested_name or default_name
    if not module_name.isidentifier():
        raise ValueError(f"Output name must be a valid Python identifier: {module_name!r}")
    return module_name


# Generated wrapper materialization and native compilation


def _expected_generated_files(
    *,
    source_objects: tuple[ObjectFile, ...],
    output_dir: Path,
    module_name: str,
    shared_library: Path,
) -> tuple[Path, ...]:
    """Collect the build artifacts that currently exist on disk.

    Combines caller-native object paths, expected generated bridge/binding
    files, the shared library, and installed native-support files.  Missing
    optional outputs are omitted; this helper only reads filesystem state.
    """
    candidates = [
        *(source_obj.object_path for source_obj in source_objects),
        output_dir / f"bind_c_{module_name}.mod",
        output_dir / f"bind_c_{module_name}_wrapper.mod",
        output_dir / f"bind_c_{module_name}_wrapper.f90",
        output_dir / f"bind_c_{module_name}_wrapper.o",
        output_dir / f"{module_name}_wrapper.c",
        output_dir / f"{module_name}_wrapper.h",
        output_dir / f"{module_name}_wrapper.o",
        shared_library,
    ]
    native_support_dir = output_dir / "binding_support"
    if native_support_dir.is_dir():
        candidates.extend(sorted(path for path in native_support_dir.rglob("*") if path.is_file()))
    return tuple(path for path in candidates if path.exists())


def _generated_source_output_path(output_dir: Path, path: Path) -> Path:
    """Return the output path for one generated wrapper source."""
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Generated wrapper source path must stay inside the build directory: {path}")
    return output_dir / path


BUILD_CONTRACT_DIRECTORY_NAME = "contracts"


def _write_build_contract_package(
    source_modules: tuple[SemanticModule, ...],
    output_dir: Path,
    *,
    verbose: bool | int = False,
) -> tuple[Path, ...]:
    """Write the editable semantic contract for one build beside its artifacts.

    Every build leaves the contract that describes the API it just generated, so
    reshaping the Python surface never needs a separate `generate --pyi` run.
    The package lives in its own directory inside the build output so its
    ``__init__.pyi`` cannot make the build directory look like a Python package.
    """
    if not source_modules:
        return ()
    try:
        stubs = emit_module_stubs(source_modules)
    except (ValueError, KeyError) as error:
        # The extension is already built; a contract that cannot be rendered is
        # reported rather than allowed to fail the build behind it.
        _print_verbose_step(verbose, f"Skip contract package: {error}")
        return ()
    package_dir = output_dir / BUILD_CONTRACT_DIRECTORY_NAME
    package_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for module_name, text in stubs.items():
        path = package_dir / f"{module_name}.pyi"
        path.write_text(f"{text}\n", encoding="utf-8")
        _print_verbose_step(verbose, f"Write semantic contract: {path}")
        written.append(path)
    root = package_dir / "__init__.pyi"
    root.write_text("".join(f"from . import {name}\n" for name in sorted(stubs)), encoding="utf-8")
    _print_verbose_step(verbose, f"Write semantic contract package: {root}")
    written.append(root)
    return tuple(written)


def _write_generated_wrapper_sources(
    rendered: GeneratedWrapper,
    output_dir: Path,
    *,
    verbose: bool | int = False,
) -> tuple[Path, ...]:
    """Write one generated wrapper's sources into a build directory."""
    written = []
    for source in rendered.sources:
        path = _generated_source_output_path(output_dir, source.path)
        _print_verbose_step(verbose, f"{_generated_source_write_label(rendered, source.path)}: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source.text, encoding="utf-8")
        written.append(path)
    return tuple(written)


def _generated_source_payloads(
    rendered: GeneratedWrapper,
) -> dict[Path, GeneratedSource]:
    """Return source payloads keyed by generated wrapper path."""
    return {Path(source.path): source for source in rendered.sources}


def _generated_source_write_label(rendered: GeneratedWrapper, source_path: Path) -> str:
    """Return the verbose write label for one generated source."""
    if source_path in rendered.bridge_sources:
        return "Write bridge source"
    if source_path in rendered.binding_sources:
        return "Write binding source"
    if source_path in rendered.headers:
        return "Write binding header"
    return "Write generated source"


def _generated_wrapper_compile_source_paths(
    rendered: GeneratedWrapper,
) -> tuple[Path, ...]:
    """Return generated wrapper source paths in compile order."""
    source_paths = rendered.compile_sources
    payloads = _generated_source_payloads(rendered)
    missing = tuple(path for path in source_paths if path not in payloads)
    if missing:
        raise ValueError(f"Generated wrapper is missing source payloads: {missing!r}")
    return source_paths


def _generated_wrapper_source_language(path: Path) -> str:
    """Return the compiler language for one generated wrapper source."""
    try:
        return _GENERATED_WRAPPER_SOURCE_LANGUAGES[path.suffix.lower()]
    except KeyError:
        raise ValueError(f"Unsupported generated wrapper source suffix: {path}") from None


def _generated_wrapper_native_support_imports(native_support_keys: Iterable[str]) -> tuple[str, ...]:
    """Return native-support import keys consumed by the support installer."""
    imports: list[str] = []
    for key in native_support_keys:
        try:
            imports.extend(_GENERATED_WRAPPER_NATIVE_SUPPORT_IMPORTS[key])
        except KeyError:
            raise ValueError(f"Unsupported wrapper native support key: {key!r}") from None
    return tuple(imports)


def _generated_wrapper_object_file(
    source_path: Path,
    output_dir: Path,
    *,
    flags: tuple[str, ...],
    include_dirs: tuple[Path, ...],
    language: str,
) -> ObjectFile:
    """Return one explicit object-file input for a generated wrapper source."""
    source = _generated_source_output_path(output_dir, source_path)
    return ObjectFile(
        source=source,
        object_path=source.with_suffix(".o"),
        language=language,
        flags=flags,
        include_dirs=include_dirs,
        tools=frozenset({"python"}) if language == "c" else frozenset(),
    )


def _generated_wrapper_object_stages(
    rendered: GeneratedWrapper,
    output_dir: Path,
    *,
    wrapper_fortran_flags: tuple[str, ...],
    wrapper_c_flags: tuple[str, ...],
    native_module_dirs: tuple[Path, ...],
) -> tuple[tuple[ObjectFile, ...], tuple[ObjectFile, ...]]:
    """Return bridge and binding objects in their required compile order."""
    source_paths = _generated_wrapper_compile_source_paths(rendered)
    bridge_source_paths = source_paths[: len(rendered.bridge_sources)]
    binding_source_paths = source_paths[len(bridge_source_paths) :]
    bridge_objects = tuple(
        _generated_wrapper_object_file(
            source_path,
            output_dir,
            flags=wrapper_fortran_flags,
            include_dirs=native_module_dirs,
            language=_generated_wrapper_source_language(source_path),
        )
        for source_path in bridge_source_paths
    )
    binding_objects = tuple(
        _generated_wrapper_object_file(
            source_path,
            output_dir,
            flags=wrapper_c_flags,
            include_dirs=native_module_dirs,
            language=_generated_wrapper_source_language(source_path),
        )
        for source_path in binding_source_paths
    )
    return bridge_objects, binding_objects


def _generated_wrapper_link_language(
    bridge_objects: tuple[ObjectFile, ...],
    binding_objects: tuple[ObjectFile, ...],
    *,
    native_objects: tuple[ObjectFile, ...] = (),
    required_languages: tuple[str, ...] = (),
) -> str:
    """Return the linker language required by every generated and native input."""
    languages = {
        *required_languages,
        *(item.language for item in native_objects),
        *(item.language for item in bridge_objects),
        *(item.language for item in binding_objects),
    }
    if "fortran" in languages:
        return "fortran"
    if not binding_objects:
        raise ValueError("Generated wrapper must include at least one binding source")
    return binding_objects[-1].language


@dataclass(frozen=True)
class _CompiledObject:
    """Store the recorded compiler command and elapsed time for one object."""

    command: tuple[str, ...] | None
    elapsed: float


def _compile_one_object(compiler: Compiler, object_file: ObjectFile) -> _CompiledObject:
    """Compile one object and return its command record plus elapsed time.

    The supplied ``compiler`` performs the compile and may create the object
    file.  A tuple command is retained for Makefile generation; other compiler
    return values are represented as ``None``.
    """
    started = time.perf_counter()
    command = compiler.compile_object(object_file, verbose=False)
    return _CompiledObject(
        command=command if isinstance(command, tuple) else None,
        elapsed=time.perf_counter() - started,
    )


def _report_compiled_object(
    object_file: ObjectFile,
    result: _CompiledObject,
    *,
    label: str,
    verbose: bool | int,
) -> None:
    """Print verbose diagnostics for one completed object compilation.

    Receives the object and timing record produced by ``_compile_one_object``.
    When ``verbose`` is false it changes nothing; otherwise it writes the
    labelled source-to-object mapping, command, and duration to standard out.
    """
    if not verbose:
        return
    _print_verbose_step(verbose, f"{label}: {object_file.source} -> {object_file.object_path}")
    if result.command is not None:
        print(shlex.join(result.command))
    _print_verbose_timing(verbose, result.elapsed)


def _compile_object_stage(
    compiler: Compiler,
    object_files: Iterable[ObjectFile],
    *,
    label: str,
    verbose: bool | int,
) -> None:
    """Compile one named object group and expose that boundary in verbose logs."""
    for object_file in object_files:
        result = _compile_one_object(compiler, object_file)
        _report_compiled_object(object_file, result, label=label, verbose=verbose)


def _submit_object_stage(
    executor: ThreadPoolExecutor,
    compiler: Compiler,
    object_files: Iterable[ObjectFile],
) -> tuple[tuple[ObjectFile, Future[_CompiledObject]], ...]:
    """Submit one independent compilation group to an executor.

    Each input object produces one ``(object_file, future)`` pair.  The helper
    schedules work but does not wait for it or report verbose output.
    """
    return tuple(
        (object_file, executor.submit(_compile_one_object, compiler, object_file)) for object_file in object_files
    )


def _finish_object_stage(
    pending: Iterable[tuple[ObjectFile, Future[_CompiledObject]]],
    *,
    label: str,
    verbose: bool | int,
) -> None:
    """Wait for a submitted compilation group and report each result.

    ``pending`` comes from ``_submit_object_stage``.  Calling ``future.result``
    propagates compiler failures; successful objects are reported in input
    order when verbose output is enabled.
    """
    for object_file, future in pending:
        _report_compiled_object(object_file, future.result(), label=label, verbose=verbose)


def _compile_extension_objects(
    compiler: Compiler,
    *,
    native_batches: Iterable[Iterable[ObjectFile]],
    bridge_objects: Iterable[ObjectFile],
    binding_objects: Iterable[ObjectFile],
    jobs: int,
    verbose: bool | int,
) -> None:
    """Compile one dependency-aware extension graph within a shared job limit."""
    native_groups = tuple(tuple(batch) for batch in native_batches)
    bridges = tuple(bridge_objects)
    bindings = tuple(binding_objects)
    if jobs == 1:
        for batch in native_groups:
            _compile_object_stage(compiler, batch, label="Compile native source", verbose=verbose)
        _compile_object_stage(compiler, bridges, label="Compile bridge source", verbose=verbose)
        _compile_object_stage(compiler, bindings, label="Compile binding source", verbose=verbose)
        return

    with ThreadPoolExecutor(max_workers=jobs, thread_name_prefix="prik-compile") as executor:
        binding_futures = _submit_object_stage(executor, compiler, bindings)
        for batch in native_groups:
            native_futures = _submit_object_stage(executor, compiler, batch)
            _finish_object_stage(native_futures, label="Compile native source", verbose=verbose)
        bridge_futures = _submit_object_stage(executor, compiler, bridges)
        _finish_object_stage(bridge_futures, label="Compile bridge source", verbose=verbose)
        _finish_object_stage(binding_futures, label="Compile binding source", verbose=verbose)


def _build_generated_wrapper_extension(
    rendered: GeneratedWrapper,
    *,
    output_dir: str | Path,
    shared_library_output_dir: str | Path | None = None,
    sources: Iterable[str | Path] = (),
    native_build_plan: NativeBuildPlan | None = None,
    native_dependencies: Iterable[ObjectFile] = (),
    native_compile_batches: Iterable[Iterable[ObjectFile]] = (),
    native_link_args: Iterable[str] = (),
    wrapper_fortran_flags: Iterable[str] | None = None,
    wrapper_c_flags: Iterable[str] | None = None,
    compiler: Compiler | None = None,
    compile_jobs: int | None = None,
    verbose: bool | int = False,
) -> WrapperBuildResult:
    """Write, compile, and link one complete generated wrapper."""
    # Materialize the canonical wrapper output before creating compiler inputs.
    rendered.freeze()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    shared_output_path = Path(shared_library_output_dir) if shared_library_output_dir is not None else output_path
    shared_output_path.mkdir(parents=True, exist_ok=True)
    _write_generated_wrapper_sources(rendered, output_path, verbose=verbose)

    # Prepare generated-object inputs and their native support files.
    compiler = compiler or _new_compiler()
    resolved_native_build_plan = native_build_plan or NativeBuildPlan()
    bridge_objects, binding_objects = _generated_wrapper_object_stages(
        rendered,
        output_path,
        wrapper_fortran_flags=_compiler_flags(wrapper_fortran_flags),
        wrapper_c_flags=_compiler_flags(wrapper_c_flags),
        native_module_dirs=_unique_paths(
            (
                *resolved_native_build_plan.module_dirs,
                *resolved_native_build_plan.include_dirs,
            )
        ),
    )
    native_support_imports = _generated_wrapper_native_support_imports(rendered.native_support_keys)
    install_native_support(
        native_support_imports,
        prik_dirpath=str(output_path),
        verbose=verbose,
    )

    # Compile dependency-ready native sources, then the bridge and binding.
    _compile_extension_objects(
        compiler,
        native_batches=native_compile_batches,
        bridge_objects=bridge_objects,
        binding_objects=binding_objects,
        jobs=_normalize_compile_jobs(compile_jobs),
        verbose=verbose,
    )

    # Link the generated and caller-supplied objects into the extension.
    linking_started = time.perf_counter()
    shared_library = compiler.link_extension(
        module_name=rendered.module_name,
        output_dir=shared_output_path,
        language=_generated_wrapper_link_language(
            bridge_objects,
            binding_objects,
            native_objects=tuple(native_dependencies),
            required_languages=rendered.required_link_languages,
        ),
        objects=(*tuple(native_dependencies), *bridge_objects, *binding_objects),
        link_args=tuple(native_link_args),
        library_dirs=resolved_native_build_plan.library_dirs,
        flags=_compiler_flags(wrapper_c_flags),
        verbose=verbose,
    )
    _print_verbose_timing(verbose, time.perf_counter() - linking_started)
    generated_source_paths = tuple(
        path for path in rendered.generated_files if _generated_source_output_path(output_path, path).exists()
    )
    generated_sources = tuple(_generated_source_output_path(output_path, path) for path in generated_source_paths)
    return WrapperBuildResult(
        sources=tuple(Path(source) for source in sources),
        module_name=rendered.module_name,
        output_dir=output_path,
        shared_library=shared_library,
        build_makefile=None,
        compiled=True,
        generated_sources=generated_sources,
        generated_files=_expected_generated_files(
            source_objects=tuple(native_dependencies),
            output_dir=output_path,
            module_name=rendered.module_name,
            shared_library=shared_library,
        ),
        native_build_plan=resolved_native_build_plan,
        native_generated_code_groups=rendered.native_generated_code_groups,
    )


def _attach_build_makefile(
    result: WrapperBuildResult,
    *,
    compiler: Compiler,
    source_objects: tuple[ObjectFile, ...],
    extra_dependencies: tuple[Path, ...] = (),
    build_manifest: Path | None = None,
) -> WrapperBuildResult:
    """Attach one replayable Makefile to an unexecuted canonical build."""
    build_makefile = _write_build_makefile(
        path=result.output_dir / "Makefile.prik",
        commands=compiler.command_log,
        source_objects=source_objects,
        working_directory=Path.cwd(),
        extra_dependencies=extra_dependencies,
    )
    additions = tuple(path for path in (build_manifest, build_makefile) if path is not None)
    return replace(
        result,
        build_makefile=build_makefile,
        compiled=False,
        generated_files=(*result.generated_files, *additions),
        build_manifest=build_manifest,
    )


def _finalize_build_mode(
    result: WrapperBuildResult,
    *,
    makefile: bool,
    generate_sources: bool,
    compiler: Compiler,
    source_objects: tuple[ObjectFile, ...],
    extra_dependencies: tuple[Path, ...] = (),
    build_manifest: Path | None = None,
) -> WrapperBuildResult:
    """Turn a planned build into its requested source-only or Makefile result."""
    if makefile:
        return _attach_build_makefile(
            result,
            compiler=compiler,
            source_objects=source_objects,
            extra_dependencies=extra_dependencies,
            build_manifest=build_manifest,
        )
    if generate_sources:
        return replace(result, compiled=False)
    return result


def _render_wrapper_plan(
    module: SemanticModule,
    *,
    progress: Callable[[str, float | None], None] | None = None,
) -> GeneratedWrapper:
    """Render one policy-completed module through the canonical generator."""
    plan = WrapperPlanner().build(module)
    return WrapperGenerator().generate(plan, progress=progress)


def _generate_wrapper(
    module: SemanticModule,
    *,
    strict_wrapper_names: bool,
    verbose: bool | int = False,
) -> GeneratedWrapper:
    """Complete policy and generate the one production wrapper representation."""
    _print_verbose_step(verbose, "Complete wrapper policies")
    policy_started = time.perf_counter()
    complete_semantic_policies(module, strict_wrapper_names=strict_wrapper_names)
    _print_verbose_timing(verbose, time.perf_counter() - policy_started)

    def render_progress(label: str, elapsed: float | None) -> None:
        """Translate generator progress events into this build's verbose output.

        A missing duration starts a labelled step; a present duration completes
        the previous step's timing.  The callback only writes optional console
        output and does not affect generation.
        """
        if elapsed is None:
            _print_verbose_step(verbose, label)
            return
        _print_verbose_timing(verbose, elapsed)

    return _render_wrapper_plan(module, progress=render_progress)


# Native source compilation scheduling


def _source_compile_object(
    source_path: Path,
    output_dir: Path,
    *,
    object_stem: str,
    flags: Iterable[str] = (),
    include_dirs: Iterable[Path] = (),
) -> ObjectFile:
    """Describe the object compilation for one caller-native source.

    Uses ``object_stem`` beneath ``output_dir`` to avoid collisions, preserves
    the supplied flags, and appends the output directory to include paths so
    later sources can locate generated Fortran module files.  It returns only
    an ``ObjectFile`` description and does not compile it.
    """
    target = output_dir / f"{object_stem}.o"
    return ObjectFile(
        source=source_path,
        object_path=target,
        language="fortran",
        flags=tuple(flags),
        include_dirs=(*tuple(include_dirs), output_dir),
    )


def _serial_compile_batches(object_files: Iterable[ObjectFile]) -> tuple[tuple[ObjectFile, ...], ...]:
    """Place each object in its own ordered compilation batch.

    This conservative fallback consumes ``object_files`` and returns singleton
    tuples, ensuring that a caller compiles sources serially when dependency
    information is unavailable or cyclic.
    """
    return tuple((object_file,) for object_file in object_files)


def _fortran_owner_used_modules(owner: object) -> set[str]:
    """Return lowercased modules used directly or indirectly by one owner.

    ``owner`` may be a parsed module, program, procedure, or submodule.  The
    helper reads its ``uses`` mappings and the uses of contained procedures and
    interface procedures, returning a new set without changing the parsed AST.
    """
    used = {str(name).lower() for name in getattr(owner, "uses", {})}
    for procedure in getattr(owner, "procedures", ()):
        used.update(str(name).lower() for name in getattr(procedure, "uses", {}))
    for interface in getattr(owner, "interfaces", ()):
        for procedure in getattr(interface, "procedures", ()):
            used.update(str(name).lower() for name in getattr(procedure, "uses", {}))
    return used


def _fortran_file_used_modules(parsed_file: object) -> set[str]:
    """Return lowercased module dependencies declared by one parsed file.

    Scans top-level parsed owners, interfaces, and submodule parent/ancestor
    relationships.  The returned names let the scheduler order object files;
    the parsed file remains unmodified.
    """
    owners = (
        *getattr(parsed_file, "modules", ()),
        *getattr(parsed_file, "submodules", ()),
        *getattr(parsed_file, "programs", ()),
        *getattr(parsed_file, "procedures", ()),
    )
    used = set()
    for owner in owners:
        used.update(_fortran_owner_used_modules(owner))
    for interface in getattr(parsed_file, "interfaces", ()):
        for procedure in getattr(interface, "procedures", ()):
            used.update(str(name).lower() for name in getattr(procedure, "uses", {}))
    for submodule in getattr(parsed_file, "submodules", ()):
        used.add(str(submodule.parent).lower())
        if submodule.ancestor:
            used.add(str(submodule.ancestor).lower())
    return used


def _dependency_compile_batches(
    object_files: tuple[ObjectFile, ...],
    dependencies: dict[Path, set[Path]],
) -> tuple[tuple[ObjectFile, ...], ...]:
    """Topologically group object files into safe parallel compile batches.

    ``dependencies`` maps normalized source paths to provider source paths.
    Every returned batch depends only on earlier batches.  If no source is
    ready, a cycle or incomplete graph is present, so the function returns the
    serial fallback rather than guess an unsafe order.
    """
    object_by_source = {_path_key(object_file.source): object_file for object_file in object_files}
    remaining = list(object_by_source)
    completed: set[Path] = set()
    batches = []
    while remaining:
        ready = [source for source in remaining if dependencies.get(source, set()) <= completed]
        if not ready:
            return _serial_compile_batches(object_files)
        batches.append(tuple(object_by_source[source] for source in ready))
        completed.update(ready)
        remaining = [source for source in remaining if source not in completed]
    return tuple(batches)


def _project_compile_batches(
    parsed_project: object,
    object_files: tuple[ObjectFile, ...],
) -> tuple[tuple[ObjectFile, ...], ...]:
    """Group parsed project objects into dependency-ready compiler batches."""
    # Every compiled source must correspond to one parsed project file.
    parsed_files = tuple(getattr(parsed_project, "files", ()))
    parsed_by_source = {
        _path_key(Path(parsed_file.filename)): parsed_file
        for parsed_file in parsed_files
        if getattr(parsed_file, "filename", None)
    }
    object_sources = {_path_key(object_file.source) for object_file in object_files}
    if set(parsed_by_source) != object_sources:
        return _serial_compile_batches(object_files)

    # Map providers before resolving each file's module dependencies.
    module_sources: dict[str, Path] = {}
    for source, parsed_file in parsed_by_source.items():
        for module in getattr(parsed_file, "modules", ()):
            module_sources[str(module.name).lower()] = source
        for submodule in getattr(parsed_file, "submodules", ()):
            module_sources[str(submodule.name).lower()] = source

    dependencies: dict[Path, set[Path]] = {}
    for source, parsed_file in parsed_by_source.items():
        dependencies[source] = {
            dependency_source
            for name in _fortran_file_used_modules(parsed_file)
            if (dependency_source := module_sources.get(name)) is not None and dependency_source != source
        }
    return _dependency_compile_batches(object_files, dependencies)


# Source and semantic-contract inputs


def _source_paths(sources: str | Path | Iterable[str | Path]) -> tuple[Path, ...]:
    """Validate and expand wrapper source inputs into a unique ordered tuple.

    A file must have a supported Fortran suffix; a directory is recursively
    expanded in sorted order.  The result preserves the caller's input order
    while removing repeated paths.  Missing files, empty directories, and
    unsupported suffixes raise clear input errors before parsing begins.
    """
    inputs = (Path(sources),) if isinstance(sources, str | Path) else tuple(Path(source) for source in sources)
    if not inputs:
        raise ValueError("wrapper build requires at least one Fortran source file or directory")

    paths: list[Path] = []
    for path in inputs:
        if path.is_dir():
            discovered = sorted(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file() and candidate.suffix.lower() in _FORTRAN_SOURCE_SUFFIXES
            )
            if not discovered:
                raise ValueError(f"No recognized Fortran sources found under: {path}")
            paths.extend(discovered)
            continue
        if not path.is_file():
            raise FileNotFoundError(f"Fortran source not found: {path}")
        if path.suffix.lower() not in _FORTRAN_SOURCE_SUFFIXES:
            raise ValueError(f"Unrecognized Fortran source suffix: {path}")
        paths.append(path)
    return tuple(dict.fromkeys(paths))


def _wrapper_output_paths(output_dir: str | Path | None) -> tuple[Path, Path]:
    """Return build and extension directories owned by one wrapper invocation."""
    if output_dir is not None:
        path = Path(output_dir)
        return path, path
    invocation_dir = Path.cwd()
    build_dir = invocation_dir / _DEFAULT_BUILD_DIR_NAME
    return build_dir, build_dir


def _pyi_entry_path(contract: str | Path) -> Path:
    """Validate and return the single semantic ``.pyi`` entry contract path.

    The public ``build_pyi_extension`` API accepts exactly one existing
    ``.pyi`` file.  This helper rejects collections, other suffixes, and
    missing paths, then returns the unmodified ``Path`` for contract loading.
    """
    if not isinstance(contract, str | Path):
        raise TypeError(".pyi wrapper build accepts exactly one entry contract path")
    path = Path(contract)
    if path.suffix.lower() != ".pyi":
        raise ValueError(f".pyi wrapper build expects one semantic contract file, not {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Semantic .pyi contract not found: {path}")
    return path


@dataclass(frozen=True)
class _PyiContractBundle:
    """Keep one resolved ``.pyi`` import graph and its native contract leaves."""

    entry: Path
    leaves: tuple[Path, ...]
    paths: tuple[Path, ...]
    modules: tuple[SemanticModule, ...]


@dataclass(frozen=True)
class _NativeBuildInputs:
    """Hold validated native source, artifact, include, and link input groups."""

    source_paths: tuple[Path, ...]
    source_flags: tuple[str, ...]
    artifact_paths: tuple[Path, ...]
    libraries: tuple[str, ...]
    explicit_link_items: tuple[NativeLinkItem, ...]
    complete_link_items: tuple[NativeLinkItem, ...] | None
    link_item_paths: tuple[Path, ...]
    library_dirs: tuple[Path, ...]
    explicit_include_dirs: tuple[Path, ...]


# Semantic `.pyi` contract loading and export projection


def _pyi_contract_bundle(
    entry: Path,
) -> _PyiContractBundle:
    """Load one semantic contract graph and retain its native declaration leaves.

    Starting at ``entry``, this resolves relative imports through one cache,
    validates package-placement rules, projects Python exports, and validates
    native contracts.  It returns the entry, all discovered paths, and only
    modules with native declarations; no generated sources are written.
    """
    # Load the complete relative-import graph through one semantic-module cache.
    module_cache = _PyiSemanticModuleCache()
    discovered = {entry, *_discover_pyi_imports(entry, module_cache)}
    sorted_paths = tuple(sorted(discovered))
    loaded_modules = module_cache.paths_to_semantic_modules(sorted_paths)
    modules_by_path = dict(zip(sorted_paths, loaded_modules, strict=True))
    _validate_pyi_bundle_placement(entry, modules_by_path)
    _apply_pyi_python_exports(entry, modules_by_path)

    # Keep only contract leaves that declare a native API to wrap.
    leaves = [path for path in sorted_paths if _module_has_native_declarations(modules_by_path[path])]
    if not leaves:
        raise ValueError("Entry contract does not resolve any native declarations")
    native_modules = tuple(modules_by_path[path] for path in leaves)
    validate_pyi_native_contract(list(native_modules))
    return _PyiContractBundle(
        entry=entry,
        leaves=tuple(leaves),
        paths=(entry, *sorted(discovered - {entry})),
        modules=native_modules,
    )


def _validate_pyi_bundle_placement(entry: Path, modules_by_path: dict[Path, SemanticModule]) -> None:
    """Reject root/module placement edits that contradict the file graph."""
    entry_module = modules_by_path[entry]
    if entry.name == "__init__.pyi" and _module_has_native_declarations(entry_module):
        invalid = [
            declaration.name
            for declaration in _module_declarations(entry_module)
            if not _declaration_is_standalone(declaration)
        ]
        if invalid:
            raise ValueError(
                "Package entry contracts cannot contain native module declarations; "
                "import module leaves or mark standalone procedures with @standalone. "
                f"Invalid declaration: {invalid[0]}"
            )

    namespace_imports = _namespace_imported_pyi_paths(entry, modules_by_path)
    for path in namespace_imports:
        module = modules_by_path[path]
        invalid = [
            declaration.name for declaration in _module_declarations(module) if _declaration_is_standalone(declaration)
        ]
        if invalid:
            raise ValueError(
                "A contract imported as a Python child namespace cannot contain @standalone declarations; "
                "keep standalone procedures in the entry contract or import standalone fragments by name. "
                f"Invalid declaration: {invalid[0]} in {path}"
            )


def _declaration_is_standalone(declaration: object) -> bool:
    """Return whether a declaration represents a standalone Fortran procedure.

    Individual semantic functions are standalone when they have no native scope;
    overload sets are standalone only when every candidate is standalone. Other
    declaration kinds return ``False`` and are not modified.
    """
    if isinstance(declaration, ProcedureOverloadSet):
        return bool(declaration.procedures) and all(_declaration_is_standalone(item) for item in declaration.procedures)
    if isinstance(declaration, SemanticFunction):
        return declaration.origin.source_language == "fortran" and declaration.origin.native_scope is None
    return False


def _namespace_imported_pyi_paths(entry: Path, modules_by_path: dict[Path, SemanticModule]) -> set[Path]:
    """Find relative ``.pyi`` modules imported as child Python namespaces.

    Traverses the semantic import graph rooted at ``entry``.  Named child
    module imports are collected separately from direct declaration imports so
    placement validation can enforce their different standalone-procedure rule.
    """
    namespace_imports: set[Path] = set()
    pending = [entry]
    seen: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        module = modules_by_path[path]
        for semantic_import in module.imports:
            if not isinstance(semantic_import, SemanticImport) or not semantic_import.module.startswith("."):
                continue
            if semantic_import.module.strip("."):
                dependency = _relative_import_path(path, semantic_import.module, semantic_import.module.lstrip("."))
                pending.append(dependency)
                continue
            for item in semantic_import.items:
                if item.source == "*":
                    continue
                dependency = _relative_import_path(path, semantic_import.module, item.source)
                namespace_imports.add(dependency)
                pending.append(dependency)
    return namespace_imports


def _discover_pyi_imports(root: Path, module_cache: _PyiSemanticModuleCache | None = None) -> tuple[Path, ...]:
    """Resolve every relative semantic ``.pyi`` import reachable from ``root``.

    Reuses an optional semantic-module cache, follows only relative imports,
    and returns sorted dependency paths excluding the root.  A referenced but
    missing contract raises ``FileNotFoundError`` instead of being skipped.
    """
    module_cache = module_cache or _PyiSemanticModuleCache()
    discovered: set[Path] = set()
    pending = [root]
    while pending:
        path = pending.pop()
        module = module_cache.file_to_semantic_module(path)
        for dependency in _relative_pyi_dependencies(path, module):
            if dependency in discovered or dependency == root:
                continue
            if not dependency.is_file():
                raise FileNotFoundError(f"Imported semantic .pyi contract not found: {dependency}")
            discovered.add(dependency)
            pending.append(dependency)
    return tuple(sorted(discovered))


def _relative_pyi_dependencies(path: Path, module: SemanticModule) -> tuple[Path, ...]:
    """Translate a module's relative imports into candidate contract paths.

    ``path`` anchors the package-relative calculation and ``module`` supplies
    parsed import records.  The returned paths may not exist yet; existence is
    checked by the graph discovery caller.
    """
    dependencies: list[Path] = []
    for semantic_import in module.imports:
        if not isinstance(semantic_import, SemanticImport) or not semantic_import.module.startswith("."):
            continue
        level = len(semantic_import.module) - len(semantic_import.module.lstrip("."))
        parent = path.parent
        for _ in range(level - 1):
            parent = parent.parent
        imported_module = semantic_import.module[level:]
        if imported_module:
            dependencies.append(_pyi_dependency_path(parent, imported_module))
        else:
            dependencies.extend(_pyi_dependency_path(parent, item.source) for item in semantic_import.items)
    return tuple(dependencies)


def _pyi_dependency_path(parent: Path, dotted_name: str) -> Path:
    """Choose the file or package-entry path for one relative import target.

    Forms the dotted target below ``parent`` and returns ``name.pyi`` unless
    the target is an existing directory, in which case it returns its
    ``__init__.pyi`` entry.  It does not create either path.
    """
    target = parent.joinpath(*dotted_name.split("."))
    module_file = target.with_suffix(".pyi")
    if module_file.is_file() or not target.is_dir():
        return module_file
    return target / "__init__.pyi"


def _module_has_native_declarations(module: SemanticModule) -> bool:
    """Return whether a semantic module contributes any native wrapper surface."""
    return bool(module.variables or module.functions or module.classes or module.overload_sets)


@dataclass
class _PyiExportNode:
    """Represent declarations and nested Python exports at one namespace node."""

    declarations: list[object] = field(default_factory=list)
    children: dict[str, _PyiExportNode] = field(default_factory=dict)
    origins: set[Path] = field(default_factory=set)


def _apply_pyi_python_exports(entry: Path, modules_by_path: dict[Path, SemanticModule]) -> None:
    """Replace contract declaration export metadata with the resolved tree.

    Clears each loaded declaration's current Python exports, marks its module
    as prepared, resolves exports rooted at ``entry``, and writes the resulting
    namespace paths back into declaration metadata.  The semantic modules are
    deliberately mutated before wrapper policy completion.
    """
    for module in modules_by_path.values():
        module.metadata[PYTHON_EXPORTS_PREPARED_METADATA] = True
        for declaration in _module_declarations(module):
            _set_declaration_exports(declaration, [])

    tree = _pyi_export_tree(entry, modules_by_path, cache={}, pending=set())
    _record_pyi_exports(tree)


def _pyi_export_tree(
    path: Path,
    modules_by_path: dict[Path, SemanticModule],
    *,
    cache: dict[Path, _PyiExportNode],
    pending: set[Path],
) -> _PyiExportNode:
    """Build and cache the export tree rooted at one semantic contract file.

    The recursive graph combines public declarations, prototypes, and relative
    imports.  ``cache`` shares completed nodes, while ``pending`` detects an
    import cycle and raises ``ValueError`` rather than recurse forever.
    """
    if path in cache:
        return cache[path]
    if path in pending:
        raise ValueError(f"Cyclic relative .pyi export imports include {path}")
    pending.add(path)
    module = modules_by_path[path]
    tree = _PyiExportNode(origins={path})
    for declaration in _module_declarations(module):
        if getattr(declaration, "visibility", "public") == "public":
            _merge_export_child(
                tree,
                declaration.name,
                _PyiExportNode(declarations=[declaration], origins={path}),
                origin=path,
            )

    for prototype in module.prototypes:
        _merge_export_child(
            tree,
            prototype.name,
            _PyiExportNode(declarations=[prototype], origins={path}),
            origin=path,
        )

    for semantic_import in module.imports:
        if not isinstance(semantic_import, SemanticImport) or not semantic_import.module.startswith("."):
            continue
        _merge_relative_import(tree, path, semantic_import, modules_by_path, cache, pending)
    pending.remove(path)
    cache[path] = tree
    return tree


def _merge_relative_import(
    tree: _PyiExportNode,
    path: Path,
    semantic_import: SemanticImport,
    modules_by_path: dict[Path, SemanticModule],
    cache: dict[Path, _PyiExportNode],
    pending: set[Path],
) -> None:
    """Merge one relative import's exports into the current namespace tree.

    Direct imports select declaration children from the dependency; child
    namespace imports attach the entire dependency tree.  Invalid names or
    collisions are reported by the lookup and merge helpers; ``tree`` changes
    in place.
    """
    imported_module = semantic_import.module.lstrip(".")
    if imported_module:
        dependency = _relative_import_path(path, semantic_import.module, imported_module)
        dependency_tree = _required_export_tree(dependency, modules_by_path, cache, pending)
        for item in semantic_import.items:
            if item.source == "*":
                for name, child in dependency_tree.children.items():
                    _merge_export_child(tree, name, child, origin=path)
                continue
            if item.source not in dependency_tree.children:
                raise ValueError(f"Imported semantic name {item.source!r} not found in {dependency}")
            _merge_export_child(tree, item.target or item.source, dependency_tree.children[item.source], origin=path)
        return

    for item in semantic_import.items:
        dependency = _relative_import_path(path, semantic_import.module, item.source)
        dependency_tree = _required_export_tree(dependency, modules_by_path, cache, pending)
        _merge_export_child(tree, item.target or item.source, dependency_tree, origin=path)


def _relative_import_path(path: Path, module: str, imported_module: str) -> Path:
    """Resolve one dotted relative import from its importing contract path."""
    level = len(module) - len(module.lstrip("."))
    parent = path.parent
    for _ in range(level - 1):
        parent = parent.parent
    return _pyi_dependency_path(parent, imported_module)


def _required_export_tree(
    path: Path,
    modules_by_path: dict[Path, SemanticModule],
    cache: dict[Path, _PyiExportNode],
    pending: set[Path],
) -> _PyiExportNode:
    """Return a dependency export tree or reject an absent imported contract."""
    if path not in modules_by_path:
        raise FileNotFoundError(f"Imported semantic .pyi contract not found: {path}")
    return _pyi_export_tree(path, modules_by_path, cache=cache, pending=pending)


def _merge_export_child(tree: _PyiExportNode, name: str, child: _PyiExportNode, *, origin: Path) -> None:
    """Insert one named export into ``tree`` or reject a conflicting origin.

    Existing identical nodes are retained.  Distinct nodes with the same name
    cause a detailed ``ValueError`` naming both source origins; otherwise the
    supplied child becomes part of the tree.
    """
    existing = tree.children.get(name)
    if existing is None or existing is child:
        tree.children[name] = child
        return
    existing_origins = ", ".join(str(path) for path in sorted(existing.origins))
    new_origins = ", ".join(str(path) for path in sorted(child.origins))
    raise ValueError(
        f"Conflicting .pyi exports for {name!r} while resolving {origin}: "
        f"existing from {existing_origins}; new from {new_origins}"
    )


def _record_pyi_exports(tree: _PyiExportNode, namespace: tuple[str, ...] = ()) -> None:
    """Write resolved namespace paths from an export tree into declarations.

    Walks ``tree`` recursively, skips prototypes, and appends de-duplicated
    ``namespace``/``name`` records to each semantic declaration's metadata.
    The declaration metadata is intentionally mutated for later planning.
    """
    for name, child in tree.children.items():
        for declaration in child.declarations:
            if isinstance(declaration, SemanticPrototype):
                continue
            exports = _declaration_exports(declaration)
            export = {"namespace": namespace, "name": name}
            if export not in exports:
                exports.append(export)
        _record_pyi_exports(child, (*namespace, name))


def _module_declarations(module: SemanticModule) -> tuple[object, ...]:
    """Return every declaration category that can receive export metadata."""
    return (*module.variables, *module.functions, *module.overload_sets, *module.classes)


def _declaration_metadata(declaration: object) -> dict[str, object]:
    """Return the mutable metadata dictionary for one supported declaration.

    Overload sets use their first candidate's metadata because that is where
    their shared export projection is stored.  Unsupported objects raise
    ``TypeError`` rather than silently lose metadata.
    """
    if isinstance(declaration, ProcedureOverloadSet):
        if not declaration.procedures:
            return {}
        return declaration.procedures[0].metadata
    if isinstance(declaration, SemanticVariable | SemanticFunction | SemanticClass):
        return declaration.metadata
    raise TypeError(f"Unsupported semantic declaration: {type(declaration).__name__}")


def _declaration_exports(declaration: object) -> list[dict[str, object]]:
    """Return and initialize the declaration's mutable Python export list."""
    metadata = _declaration_metadata(declaration)
    return metadata.setdefault(PYTHON_EXPORTS_METADATA, [])


def _set_declaration_exports(declaration: object, exports: list[dict[str, object]]) -> None:
    """Replace one declaration's stored Python export projection in place."""
    metadata = _declaration_metadata(declaration)
    metadata[PYTHON_EXPORTS_METADATA] = exports


def _apply_source_python_exports(modules: list[SemanticModule]) -> None:
    """Project direct Fortran source declarations to their Python namespaces.

    Marks every module as export-prepared and overwrites declaration metadata.
    Public module members receive their module namespace; standalone public
    procedures receive the root namespace; private declarations receive none.
    """
    for module in modules:
        module.metadata[PYTHON_EXPORTS_PREPARED_METADATA] = True
        namespace = (module.name.casefold(),) if module.origin.source_kind == "module" else ()
        for declaration in _module_declarations(module):
            _set_declaration_exports(
                declaration,
                (
                    []
                    if getattr(declaration, "visibility", "public") == "private"
                    else [{"namespace": namespace, "name": None}]
                ),
            )


# Native build inputs and link planning


def _existing_paths(
    paths: Iterable[str | Path] | None,
    *,
    kind: str,
    require_directory: bool = False,
) -> tuple[Path, ...]:
    """Validate caller paths and return them as a tuple of ``Path`` values.

    Files are required by default; ``require_directory`` instead requires each
    path to be a directory.  Missing inputs raise a kind-specific
    ``FileNotFoundError`` and no filesystem state is changed.
    """
    resolved = tuple(Path(path) for path in (paths or ()))
    for path in resolved:
        if require_directory:
            if not path.is_dir():
                raise FileNotFoundError(f"{kind} directory not found: {path}")
        elif not path.is_file():
            raise FileNotFoundError(f"{kind} not found: {path}")
    return resolved


def _native_artifact_kind(path: Path) -> str:
    """Classify a native artifact path for linker and manifest representation."""
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix in {".a", ".lib"}:
        return "archive"
    if suffix in {".so", ".dylib", ".dll"} or ".so." in name:
        return "shared_library"
    return "object"


def _unique_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    """Return input paths once each, preserving their first-seen order."""
    return tuple(dict.fromkeys(Path(path) for path in paths))


def _native_build_plan(
    *,
    source_paths: tuple[Path, ...],
    source_objects: tuple[ObjectFile, ...],
    artifact_paths: tuple[Path, ...],
    libraries: tuple[str, ...],
    explicit_link_items: tuple[NativeLinkItem, ...],
    complete_link_items: tuple[NativeLinkItem, ...] | None = None,
    library_dirs: tuple[Path, ...],
    explicit_include_dirs: tuple[Path, ...],
    include_dirs: tuple[Path, ...],
    module_dir: Path | None,
) -> NativeBuildPlan:
    """Assemble the ordered native compile and link plan for one extension.

    Combines compiled source objects, prebuilt artifacts, named libraries, and
    explicit or complete link items.  The returned immutable plan preserves
    link order and includes derived module/include directories; it does not
    compile, link, or validate that prebuilt paths exist.
    """
    produced_objects = tuple(source_object.object_path for source_object in source_objects)
    source_link_items = tuple(NativeLinkItem("object", object_path) for object_path in produced_objects)
    prebuilt_artifacts = tuple(
        NativePrebuiltArtifact(path=path, kind=_native_artifact_kind(path)) for path in artifact_paths
    )
    artifact_link_items = tuple(NativeLinkItem(artifact.kind, artifact.path) for artifact in prebuilt_artifacts)
    library_link_items = tuple(NativeLinkItem("named_library", library) for library in libraries)
    link_items = (
        complete_link_items
        if complete_link_items is not None
        else (*source_link_items, *artifact_link_items, *explicit_link_items, *library_link_items)
    )
    produced_object_set = set(produced_objects)
    explicit_path_artifacts = tuple(
        NativePrebuiltArtifact(path=Path(item.value), kind=item.kind)
        for item in link_items
        if item.kind in _NATIVE_PATH_LINK_KINDS and Path(item.value) not in produced_object_set
    )
    return NativeBuildPlan(
        compilation_units=tuple(
            NativeCompilationUnit(
                source=source_path,
                object_path=source_object.object_path,
                language="fortran",
                module_dir=module_dir,
                include_dirs=include_dirs,
                flags=tuple(source_object.flags),
            )
            for source_path, source_object in zip(source_paths, source_objects, strict=True)
        ),
        produced_objects=produced_objects,
        prebuilt_artifacts=explicit_path_artifacts,
        module_dirs=_unique_paths(path for path in (module_dir, *explicit_include_dirs) if path is not None),
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        link_items=link_items,
    )


def _native_link_args(link_items: Iterable[NativeLinkItem]) -> tuple[str, ...]:
    """Convert ordered link records to the command-line arguments they require.

    Files become paths, bare named libraries acquire ``-l`` when needed, and
    raw linker arguments pass through.  The resulting tuple preserves input
    order and is ready for the compiler linker invocation.
    """
    args = []
    for item in link_items:
        if item.kind in _NATIVE_PATH_LINK_KINDS:
            args.append(str(item.value))
        elif item.kind == "named_library":
            name = str(item.value)
            args.append(name if name.startswith("-l") else f"-l{name}")
        else:
            args.append(str(item.value))
    return tuple(args)


def _generated_wrapper_native_link_args(plan: NativeBuildPlan) -> tuple[str, ...]:
    """Return link arguments not already supplied as generated-wrapper dependencies."""
    produced_objects = {_path_key(path) for path in plan.produced_objects}
    return _native_link_args(
        item
        for item in plan.link_items
        if item.kind not in _NATIVE_PATH_LINK_KINDS or _path_key(Path(item.value)) not in produced_objects
    )


def _coerce_native_link_items(items: Iterable[NativeLinkItem | dict[str, object]] | None) -> tuple[NativeLinkItem, ...]:
    """Normalize public native link-item records or dictionaries.

    Dictionary inputs must use the same ``kind`` and value-key conventions as
    :meth:`NativeLinkItem.to_dict`.  Returns immutable ``NativeLinkItem``
    records, or raises a precise type/value error before a build is started.
    """
    if items is None:
        return ()
    result = []
    for item in items:
        if isinstance(item, NativeLinkItem):
            result.append(item)
            continue
        if not isinstance(item, dict):
            raise TypeError("native link items must be NativeLinkItem instances or dictionaries")
        kind = item.get("kind")
        if not isinstance(kind, str):
            raise ValueError("native link item dictionaries require a string 'kind'")
        if kind in _NATIVE_PATH_LINK_KINDS:
            path = item.get("path")
            if not isinstance(path, str | Path):
                raise ValueError(f"{kind!r} native link item requires a path")
            result.append(NativeLinkItem(kind, path))
        elif kind == "named_library":
            name = item.get("name")
            if not isinstance(name, str):
                raise ValueError("named_library native link item requires a name")
            result.append(NativeLinkItem(kind, name))
        elif kind == "linker_argument":
            argument = item.get("argument")
            if not isinstance(argument, str):
                raise ValueError("linker_argument native link item requires an argument")
            result.append(NativeLinkItem(kind, argument))
        else:
            raise ValueError(f"Unsupported native link item kind: {kind!r}")
    return tuple(result)


def _link_item_paths(link_items: Iterable[NativeLinkItem]) -> tuple[Path, ...]:
    """Extract only filesystem-backed paths from ordered native link items."""
    return tuple(Path(item.value) for item in link_items if item.kind in _NATIVE_PATH_LINK_KINDS)


def _path_key(path: Path) -> Path:
    """Return a non-strict resolved path suitable for equality and lookup."""
    return path.resolve(strict=False)


def _shared_library_dirs(link_items: Iterable[NativeLinkItem]) -> tuple[Path, ...]:
    """Return parent directories of shared-library link items in input order."""
    return tuple(Path(item.value).parent for item in link_items if item.kind == "shared_library")


def _native_build_inputs(
    *,
    native_fortran_sources: Iterable[str | Path] | None,
    native_fortran_flags: Iterable[str] | None,
    native_objects: Iterable[str | Path] | None,
    native_libraries: Iterable[str] | None,
    native_link_items: Iterable[NativeLinkItem | dict[str, object]] | None,
    complete_native_link_items: Iterable[NativeLinkItem | dict[str, object]] | None,
    native_library_dirs: Iterable[str | Path] | None,
    native_include_dirs: Iterable[str | Path] | None,
) -> _NativeBuildInputs:
    """Validate and normalize all caller-native inputs for a build request.

    Accepts optional sources, artifacts, libraries, ordered link records, and
    search paths, derives shared-library search directories, and returns one
    internal input record.  It rejects missing files/directories and a request
    with no native implementation input before any generated code is compiled.
    """
    # Validate independent source, artifact, and explicit-link inputs first.
    source_paths = _existing_paths(native_fortran_sources, kind="Native Fortran source")
    source_flags = tuple(str(flag) for flag in (native_fortran_flags or ()))
    artifact_paths = _existing_paths(native_objects, kind="Native artifact")
    libraries = tuple(native_libraries or ())
    explicit_link_items = _coerce_native_link_items(native_link_items)
    complete_link_items = (
        None if complete_native_link_items is None else _coerce_native_link_items(complete_native_link_items)
    )
    selected_link_items = explicit_link_items if complete_link_items is None else complete_link_items
    link_item_paths = _link_item_paths(selected_link_items)

    # Derive search paths after the final ordered link input is known.
    library_dirs = _unique_paths(
        (
            *_existing_paths(native_library_dirs, kind="Native library", require_directory=True),
            *(path.parent for path in artifact_paths if _native_artifact_kind(path) == "shared_library"),
            *_shared_library_dirs(selected_link_items),
        )
    )
    explicit_include_dirs = _existing_paths(native_include_dirs, kind="Native include", require_directory=True)

    # A wrapper has no native implementation without at least one link input.
    if (
        not source_paths
        and not artifact_paths
        and not libraries
        and not explicit_link_items
        and not complete_link_items
    ):
        raise ValueError(
            "Wrapper build requires at least one native source, object, archive, shared library, "
            "ordered link item, or -l name"
        )
    return _NativeBuildInputs(
        source_paths=source_paths,
        source_flags=source_flags,
        artifact_paths=artifact_paths,
        libraries=libraries,
        explicit_link_items=explicit_link_items,
        complete_link_items=complete_link_items,
        link_item_paths=link_item_paths,
        library_dirs=library_dirs,
        explicit_include_dirs=explicit_include_dirs,
    )


def _native_include_dirs(inputs: _NativeBuildInputs, *, output_path: Path) -> tuple[Path, ...]:
    """Derive de-duplicated include/module search paths for native compilation.

    Includes the build directory when source compilation produces module files,
    caller include directories, and parents of linked artifacts.  Returns the
    paths without creating directories or changing ``inputs``.
    """
    module_include_dirs = (output_path,) if inputs.source_paths else ()
    inferred_include_dirs = _unique_paths((*inputs.artifact_paths, *inputs.link_item_paths))
    return _unique_paths(
        (
            *module_include_dirs,
            *inputs.explicit_include_dirs,
            *(path.parent for path in inferred_include_dirs),
        )
    )


def _source_object_stems(source_paths: tuple[Path, ...]) -> tuple[str, ...]:
    """Return collision-free object stems for an ordered source-path sequence.

    Unique basenames retain their stem.  Repeated stems gain a deterministic
    one-based suffix in source order so distinct native files never target the
    same object path.
    """
    totals: dict[str, int] = {}
    for source_path in source_paths:
        totals[source_path.stem] = totals.get(source_path.stem, 0) + 1

    seen: dict[str, int] = {}
    stems = []
    for source_path in source_paths:
        stem = source_path.stem
        seen[stem] = seen.get(stem, 0) + 1
        stems.append(stem if totals[stem] == 1 else f"{stem}_{seen[stem]}")
    return tuple(stems)


def _native_source_objects(
    inputs: _NativeBuildInputs,
    *,
    output_path: Path,
    include_dirs: tuple[Path, ...],
) -> tuple[ObjectFile, ...]:
    """Create uncompiled object descriptions for all validated native sources.

    Pairs each source with its collision-free stem and applies the normalized
    source flags and include directories.  Returns the planned objects in
    source order without invoking the compiler.
    """
    return tuple(
        _source_compile_object(
            source_path,
            output_path,
            object_stem=object_stem,
            flags=inputs.source_flags,
            include_dirs=include_dirs,
        )
        for source_path, object_stem in zip(inputs.source_paths, _source_object_stems(inputs.source_paths), strict=True)
    )


def _validate_native_link_paths(plan: NativeBuildPlan) -> None:
    """Reject missing filesystem link inputs that this build will not produce.

    Produced object paths are allowed before compilation.  Every other path
    referenced by an ordered link item must already be a file; the plan itself
    is not modified.
    """
    produced_object_keys = {_path_key(path) for path in plan.produced_objects}
    for path in _link_item_paths(plan.link_items):
        if _path_key(path) not in produced_object_keys and not path.is_file():
            raise FileNotFoundError(f"Native link item not found: {path}")


def _prepare_native_build_plan(
    inputs: _NativeBuildInputs,
    *,
    output_path: Path,
) -> tuple[tuple[ObjectFile, ...], NativeBuildPlan]:
    """Create and validate compiler objects and link inputs for one build."""
    include_dirs = _native_include_dirs(inputs, output_path=output_path)
    source_objects = _native_source_objects(
        inputs,
        output_path=output_path,
        include_dirs=include_dirs,
    )
    plan = _native_build_plan(
        source_paths=inputs.source_paths,
        source_objects=source_objects,
        artifact_paths=inputs.artifact_paths,
        libraries=inputs.libraries,
        explicit_link_items=inputs.explicit_link_items,
        complete_link_items=inputs.complete_link_items,
        library_dirs=inputs.library_dirs,
        explicit_include_dirs=inputs.explicit_include_dirs,
        include_dirs=include_dirs,
        module_dir=output_path if source_objects else None,
    )
    _validate_native_link_paths(plan)
    return source_objects, plan


# Build manifest serialization


def _manifest_path(path: str | Path, *, base: Path) -> str:
    """Encode a path for a portable manifest relative to ``base`` when possible.

    Relative inputs are interpreted from the current working directory before
    comparison.  Paths on another filesystem fall back to their absolute text;
    no files are read or written.
    """
    value = Path(path)
    absolute = value if value.is_absolute() else Path.cwd() / value
    try:
        return os.path.relpath(absolute, base)
    except ValueError:
        return str(absolute)


def _resolve_manifest_path(path: str, *, base: Path) -> Path:
    """Turn a manifest path string into an absolute or base-relative path."""
    value = Path(path)
    return value if value.is_absolute() else base / value


def _manifest_link_item(item: NativeLinkItem, *, base: Path) -> dict[str, object]:
    """Serialize one native link record using manifest-relative file paths.

    File-backed items use a relative ``path`` where possible; named libraries
    and raw arguments retain their string values.  The input item is not
    modified.
    """
    if item.kind in _NATIVE_PATH_LINK_KINDS:
        return {
            "kind": item.kind,
            "path": _manifest_path(Path(item.value), base=base),
        }
    if item.kind == "named_library":
        return {
            "kind": item.kind,
            "name": str(item.value),
        }
    return {
        "kind": item.kind,
        "argument": str(item.value),
    }


def _manifest_native_plan(plan: NativeBuildPlan, *, base: Path) -> dict[str, object]:
    """Serialize a complete native build plan for a replayable manifest.

    Converts every filesystem field in ``plan`` to a path relative to ``base``
    when possible and preserves ordered link items and compiler flags.  The
    returned dictionary is ready for JSON encoding.
    """
    return {
        "compilation_units": [
            {
                "source": _manifest_path(unit.source, base=base),
                "object": _manifest_path(unit.object_path, base=base),
                "language": unit.language,
                "module_dir": _manifest_path(unit.module_dir, base=base) if unit.module_dir is not None else None,
                "include_dirs": [_manifest_path(path, base=base) for path in unit.include_dirs],
                "flags": list(unit.flags),
            }
            for unit in plan.compilation_units
        ],
        "produced_objects": [_manifest_path(path, base=base) for path in plan.produced_objects],
        "prebuilt_artifacts": [
            {
                "kind": artifact.kind,
                "path": _manifest_path(artifact.path, base=base),
            }
            for artifact in plan.prebuilt_artifacts
        ],
        "module_dirs": [_manifest_path(path, base=base) for path in plan.module_dirs],
        "include_dirs": [_manifest_path(path, base=base) for path in plan.include_dirs],
        "library_dirs": [_manifest_path(path, base=base) for path in plan.library_dirs],
        "link_items": [_manifest_link_item(item, base=base) for item in plan.link_items],
    }


def _manifest_native_array_requirements(requirements: NativeArrayBuildRequirements) -> dict[str, object]:
    """Serialize native-array bridge requirements into plain manifest values."""
    return {
        "pointer_c_descriptor_interop": requirements.pointer_c_descriptor_interop,
        "headers": list(requirements.headers),
        "items": [
            {
                "owner": item.owner,
                "item": item.item,
                "descriptor_kind": item.descriptor_kind,
                "handle_kind": item.handle_kind,
                "descriptor_interop": item.descriptor_interop,
                "headers": list(item.headers),
            }
            for item in requirements.items
        ],
    }


def _manifest_generated_wrapper(result: WrapperBuildResult, *, base: Path) -> dict[str, object]:
    """Serialize physical sources and independently planned native membership."""
    return {
        "sources": [_manifest_path(path, base=base) for path in result.generated_sources],
        "native_code_groups": [
            {
                "kind": group.kind.value,
                "language": group.language,
                "member_keys": list(group.member_keys),
                "source_paths": list(group.source_paths),
            }
            for group in result.native_generated_code_groups
        ],
    }


def _pyi_build_manifest(
    *,
    bundle: _PyiContractBundle,
    module_name: str,
    output_dir: Path,
    shared_library: Path,
    strict_wrapper_names: bool,
    requested_output_name: str | None,
    input_compiler: str,
    native_fortran_flags: tuple[str, ...],
    wrapper_compiler_debug: bool,
    wrapper_fortran_flags: tuple[str, ...],
    wrapper_c_flags: tuple[str, ...],
    native_build_plan: NativeBuildPlan,
    native_array_build_requirements: NativeArrayBuildRequirements,
    generated_wrapper: dict[str, object],
    manifest_dir: Path,
) -> dict[str, object]:
    """Build the complete in-memory manifest for a semantic ``.pyi`` build.

    Receives the resolved contract bundle, output and compiler choices, and
    native plans/array requirements.  It returns a schema-versioned plain
    dictionary whose paths are relative to ``manifest_dir``; it neither writes
    the manifest nor changes the build result.
    """
    return {
        "schema_version": _BUILD_MANIFEST_SCHEMA_VERSION,
        "build_kind": "pyi-wrapper",
        "entry_contract": _manifest_path(bundle.entry, base=manifest_dir),
        "contract_paths": [_manifest_path(path, base=manifest_dir) for path in bundle.paths],
        "extension": {
            "requested_name": requested_output_name,
            "module_name": module_name,
        },
        "output": {
            "output_dir": _manifest_path(output_dir, base=manifest_dir),
            "shared_library": _manifest_path(shared_library, base=manifest_dir),
            "strict_wrapper_names": strict_wrapper_names,
        },
        "compiler": {
            "vendor": "GNU",
            "input_executable": input_compiler,
            "fortran_flags": list(native_fortran_flags),
            "wrapper_compiler_debug": wrapper_compiler_debug,
            "wrapper_fortran_flags": list(wrapper_fortran_flags),
            "wrapper_c_flags": list(wrapper_c_flags),
            "position_independent_code": True,
        },
        "native_array_build_requirements": _manifest_native_array_requirements(native_array_build_requirements),
        "generated_wrapper": generated_wrapper,
        "native_build_plan": _manifest_native_plan(native_build_plan, base=manifest_dir),
    }


def _write_build_manifest(path: Path, manifest: dict[str, object]) -> Path:
    """Write one deterministic, newline-terminated JSON build manifest.

    The parent directory must already exist.  This creates or replaces
    ``path`` with sorted, indented JSON and returns the same path for result
    attachment.
    """
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _with_pyi_manifest(
    result: WrapperBuildResult,
    *,
    bundle: _PyiContractBundle,
    strict_wrapper_names: bool,
    requested_output_name: str | None,
    input_compiler: str,
    native_fortran_flags: tuple[str, ...],
    wrapper_compiler_debug: bool,
    wrapper_fortran_flags: tuple[str, ...],
    wrapper_c_flags: tuple[str, ...],
    native_array_build_requirements: NativeArrayBuildRequirements,
) -> WrapperBuildResult:
    """Attach the standard in-memory `.pyi` build manifest to a plan result."""
    manifest = _pyi_build_manifest(
        bundle=bundle,
        module_name=result.module_name,
        output_dir=result.output_dir,
        shared_library=result.shared_library,
        strict_wrapper_names=strict_wrapper_names,
        requested_output_name=requested_output_name,
        input_compiler=input_compiler,
        native_fortran_flags=native_fortran_flags,
        wrapper_compiler_debug=wrapper_compiler_debug,
        wrapper_fortran_flags=wrapper_fortran_flags,
        wrapper_c_flags=wrapper_c_flags,
        native_build_plan=result.native_build_plan,
        native_array_build_requirements=native_array_build_requirements,
        generated_wrapper=_manifest_generated_wrapper(result, base=result.output_dir),
        manifest_dir=result.output_dir,
    )
    return replace(result, manifest=manifest)


# Build manifest validation and replay inputs


def _load_build_manifest(path: str | Path) -> tuple[Path, dict[str, object]]:
    """Read and validate the top-level schema of a saved ``.pyi`` manifest.

    Returns the manifest path and its JSON object only when the file exists,
    decodes to an object, and matches this module's schema version and build
    kind.  Invalid or incompatible files raise input errors before replay.
    """
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Wrapper build manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Wrapper build manifest must be a JSON object")
    if payload.get("schema_version") != _BUILD_MANIFEST_SCHEMA_VERSION:
        raise ValueError(f"Unsupported wrapper build manifest schema version: {payload.get('schema_version')!r}")
    if payload.get("build_kind") != "pyi-wrapper":
        raise ValueError(f"Unsupported wrapper build manifest kind: {payload.get('build_kind')!r}")
    return manifest_path, payload


def _manifest_section(payload: dict[str, object], key: str) -> dict[str, object]:
    """Return a required object section from a validated manifest payload."""
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Wrapper build manifest missing object section: {key}")
    return value


def _manifest_string_list(section: dict[str, object], key: str) -> tuple[str, ...]:
    """Return one optional manifest list field after enforcing string items."""
    value = section.get(key, ())
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"Wrapper build manifest field {key!r} must be a list of strings")
    return tuple(value)


def _manifest_bool(section: dict[str, object], key: str, *, default: bool = False) -> bool:
    """Return one manifest boolean field or its explicit default after validation."""
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"Wrapper build manifest field {key!r} must be a boolean")
    return value


def _manifest_string(section: dict[str, object], key: str) -> str:
    """Return a required non-empty manifest string field or raise ``ValueError``."""
    value = section.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Wrapper build manifest field {key!r} must be a non-empty string")
    return value


def _manifest_path_list(section: dict[str, object], key: str, *, base: Path) -> tuple[Path, ...]:
    """Resolve an optional manifest string-list field into paths from ``base``."""
    return tuple(_resolve_manifest_path(item, base=base) for item in _manifest_string_list(section, key))


def _native_link_item_from_manifest(item: object, *, base: Path) -> NativeLinkItem:
    """Validate and reconstruct one ordered native link record from manifest JSON.

    File-backed item paths are resolved from ``base``; library names and raw
    arguments remain strings.  Unsupported shapes and kinds raise ``ValueError``
    instead of producing a partially replayable build.
    """
    if not isinstance(item, dict):
        raise ValueError("Wrapper build manifest link items must be objects")
    kind = item.get("kind")
    if not isinstance(kind, str):
        raise ValueError("Wrapper build manifest link item is missing kind")
    if kind in _NATIVE_PATH_LINK_KINDS:
        path = item.get("path")
        if not isinstance(path, str):
            raise ValueError(f"Wrapper build manifest {kind!r} link item is missing path")
        return NativeLinkItem(kind, _resolve_manifest_path(path, base=base))
    if kind == "named_library":
        name = item.get("name")
        if not isinstance(name, str):
            raise ValueError("Wrapper build manifest named library link item is missing name")
        return NativeLinkItem(kind, name)
    if kind == "linker_argument":
        argument = item.get("argument")
        if not isinstance(argument, str):
            raise ValueError("Wrapper build manifest linker argument item is missing argument")
        return NativeLinkItem(kind, argument)
    raise ValueError(f"Unsupported wrapper build manifest link item kind: {kind!r}")


def _manifest_link_items(section: dict[str, object], *, base: Path) -> tuple[NativeLinkItem, ...]:
    """Reconstruct the ordered native link-item list stored in a manifest."""
    value = section.get("link_items", ())
    if not isinstance(value, list):
        raise ValueError("Wrapper build manifest field 'link_items' must be a list")
    return tuple(_native_link_item_from_manifest(item, base=base) for item in value)


def _manifest_compilation_sources(section: dict[str, object], *, base: Path) -> tuple[Path, ...]:
    """Return Fortran source paths recorded by a manifest's compilation units.

    Validates the unit-list shape and rejects source languages this replay path
    cannot rebuild.  Paths are resolved relative to ``base`` and returned in
    recorded order without checking their current existence.
    """
    value = section.get("compilation_units", ())
    if not isinstance(value, list):
        raise ValueError("Wrapper build manifest field 'compilation_units' must be a list")
    sources = []
    for unit in value:
        if not isinstance(unit, dict) or not isinstance(unit.get("source"), str):
            raise ValueError("Wrapper build manifest compilation units must include source paths")
        if unit.get("language") != "fortran":
            raise ValueError(f"Unsupported manifest native source language: {unit.get('language')!r}")
        sources.append(_resolve_manifest_path(unit["source"], base=base))
    return tuple(sources)


# Wrapper module assembly


def _merge_wrapper_modules(modules: list[SemanticModule], *, name: str | None = None) -> SemanticModule:
    """Flatten semantic source modules into the one extension-facing module.

    Concatenates every declaration category while preserving list order and
    derives combined metadata and the origin from the first module.  An empty
    input cannot produce a wrapper and raises ``ValueError``.
    """
    if not modules:
        raise ValueError("wrapper build found no Fortran modules or standalone procedures")

    return SemanticModule(
        name=name or modules[0].name,
        functions=[function for module in modules for function in module.functions],
        prototypes=[prototype for module in modules for prototype in module.prototypes],
        overload_sets=[overload for module in modules for overload in module.overload_sets],
        classes=[semantic_class for module in modules for semantic_class in module.classes],
        variables=[variable for module in modules for variable in module.variables],
        metadata=_wrapper_module_metadata(modules),
        origin=modules[0].origin,
    )


def _wrapper_module_metadata(modules: list[SemanticModule]) -> dict[str, object]:
    """Collect metadata needed by one merged wrapper module.

    Records native module scopes and propagates export/contract readiness flags
    when any input module has them.  It returns a fresh dictionary and does not
    change the input semantic modules.
    """
    metadata: dict[str, object] = {"wrapper_native_modules": _wrapper_native_modules(modules)}
    if any(module.metadata.get(PYTHON_EXPORTS_PREPARED_METADATA) for module in modules):
        metadata[PYTHON_EXPORTS_PREPARED_METADATA] = True
    if any(module.metadata.get(PYI_LOADED_METADATA) for module in modules):
        metadata[PYI_LOADED_METADATA] = True
        metadata[NATIVE_CONTRACT_PREPARED_METADATA] = True
    return metadata


def _wrapper_native_modules(modules: list[SemanticModule]) -> list[str]:
    """Return unique native module names that require a generated native scope."""
    return list(
        dict.fromkeys(
            str(module.origin.native_name or module.name)
            for module in modules
            if module.origin.source_kind == "module" and _module_requires_native_scope(module)
        )
    )


def _module_requires_native_scope(module: SemanticModule) -> bool:
    """Return whether a module needs native-scope access in generated wrappers.

    Variables and classes always need a scope.  Procedures need one only when
    their native origin declares it; the module is inspected but not changed.
    """
    if module.variables or module.classes:
        return True
    functions = [*module.functions, *(procedure for item in module.overload_sets for procedure in item.procedures)]
    return any(function.origin.native_scope is not None for function in functions)


# Recorded compiler commands and Makefile output


def _command_output(command: tuple[str, ...]) -> str | None:
    """Return the argument following ``-o`` in one recorded compiler command."""
    try:
        return command[command.index("-o") + 1]
    except (ValueError, IndexError):
        return None


def _command_source(command: tuple[str, ...]) -> str | None:
    """Return the first recognized native source argument in a compiler command."""
    for part in command:
        if Path(part).suffix.lower() in _FORTRAN_SOURCE_SUFFIXES | _C_SOURCE_SUFFIXES:
            return part
    return None


def _command_language(command: tuple[str, ...]) -> str | None:
    """Infer ``fortran`` or ``c`` from a command's detected source suffix."""
    source = _command_source(command)
    if source is None:
        return None
    return "fortran" if Path(source).suffix.lower() in _FORTRAN_SOURCE_SUFFIXES else "c"


def _absolute_command_path(path: str | Path, working_directory: Path) -> Path:
    """Resolve a recorded command path against its original working directory."""
    result = Path(path)
    return result if result.is_absolute() else working_directory / result


def _make_target(path: Path) -> str:
    """Escape a filesystem path for safe use as a GNU Make target or dependency."""
    return str(path).replace("$", "$$").replace("#", r"\#").replace(" ", r"\ ")


def _make_shell_literal(text: str) -> str:
    """Escape dollar signs so Make passes a recorded literal through to the shell."""
    return text.replace("$", "$$")


def _make_recipe(command: tuple[str, ...], working_directory: Path) -> str:
    """Convert one recorded compiler command into an overridable Make recipe.

    Selects the Fortran, C, or shared-linker variable from the command and
    separates compiler-fixed arguments from caller-overridable flag variables.
    The returned tab-prefixed recipe runs from ``working_directory``.
    """
    language = _command_language(command)
    if "-shared" in command:
        compiler_var, flags_var = "PRIK_LD", "PRIK_LDFLAGS"
    elif language == "fortran":
        compiler_var, flags_var = "FC", "PRIK_FFLAGS"
    else:
        compiler_var, flags_var = "CC", "PRIK_CFLAGS"

    output_index = command.index("-o")
    before_output = _make_shell_literal(shlex.join(command[1:output_index]))
    output_and_after = _make_shell_literal(shlex.join(command[output_index:]))
    directory = _make_shell_literal(shlex.quote(str(working_directory)))
    return f"\tcd {directory} && $({compiler_var}) {before_output} $({flags_var}) {output_and_after}".rstrip()


def _compiler_executable(commands: tuple[tuple[str, ...], ...], *, language: str | None, shared: bool) -> str:
    """Find the recorded compiler executable for one Makefile variable.

    Searches commands by source language or shared-link status and returns a
    conservative GNU compiler default when no matching command was recorded.
    """
    for command in commands:
        if ("-shared" in command) == shared and (shared or _command_language(command) == language):
            return command[0]
    return "gfortran" if language == "fortran" or shared else "gcc"


def _write_build_makefile(
    *,
    path: Path,
    commands: tuple[tuple[str, ...], ...],
    source_objects: tuple[ObjectFile, ...],
    working_directory: Path,
    extra_dependencies: Iterable[Path] = (),
) -> Path:
    """Write a GNU Make build from recorded compiler commands."""
    # Separate recorded compile and link commands before constructing rules.
    compile_commands = tuple(command for command in commands if "-c" in command and _command_output(command))
    link_command = next((command for command in reversed(commands) if "-shared" in command), None)
    if link_command is None:
        raise RuntimeError("cannot generate Makefile without a shared-library link command")

    user_outputs = tuple(
        _absolute_command_path(source_object.object_path, working_directory) for source_object in source_objects
    )
    compile_outputs = tuple(
        _absolute_command_path(_command_output(command), working_directory) for command in compile_commands
    )
    makefile_path = path.resolve()

    # Preserve compiler selection while leaving caller-overridable flags empty.
    lines = [
        "# Generated by prik. Edit variables or override them on the make command line.",
        "# User Fortran sources are conservatively chained in supplied order.",
        "# Generated bridge and C binding objects may be built in parallel with make -j.",
        f"FC := {_make_shell_literal(shlex.quote(_compiler_executable(commands, language='fortran', shared=False)))}",
        f"CC := {_make_shell_literal(shlex.quote(_compiler_executable(commands, language='c', shared=False)))}",
        f"PRIK_LD := {_make_shell_literal(shlex.quote(_compiler_executable(commands, language=None, shared=True)))}",
        "PRIK_FFLAGS ?=",
        "PRIK_CFLAGS ?=",
        "PRIK_LDFLAGS ?=",
        "",
    ]

    link_output = _absolute_command_path(_command_output(link_command), working_directory)
    lines.extend([".PHONY: all rebuild clean", f"all: {_make_target(link_output)}", ""])

    # User sources remain ordered; generated objects depend on all native objects.
    previous_user_output = None
    for command, output in zip(compile_commands, compile_outputs, strict=True):
        source = _absolute_command_path(_command_source(command), working_directory)
        dependencies = [source]
        if output in user_outputs:
            if previous_user_output is not None:
                dependencies.append(previous_user_output)
            previous_user_output = output
        elif _command_language(command) == "fortran":
            dependencies.extend(user_outputs)
        dependency_text = " ".join(_make_target(dependency) for dependency in dict.fromkeys(dependencies))
        lines.extend(
            [
                f"{_make_target(output)}: {dependency_text}",
                _make_recipe(command, working_directory),
                "",
            ]
        )

    all_link_dependencies = tuple(dict.fromkeys((*compile_outputs, *extra_dependencies)))
    object_dependencies = " ".join(_make_target(output) for output in all_link_dependencies)

    # Link, rebuild, and cleanup rules share the recorded artifact paths.
    lines.extend(
        [
            f"{_make_target(link_output)}: {object_dependencies}",
            _make_recipe(link_command, working_directory),
            "",
            "rebuild:",
            f"\t$(MAKE) -f {_make_target(makefile_path)} clean",
            f"\t$(MAKE) -f {_make_target(makefile_path)} all",
            "",
            "clean:",
            "\trm -f " + " ".join(shlex.quote(str(output)) for output in (*compile_outputs, link_output)),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# Fortran type probing


def _can_probe_fortran_types(preprocessing: PreprocessingConfig) -> bool:
    """Return whether the preprocessing configuration can invoke a compiler probe."""
    return preprocessing.uses_compiler and bool(preprocessing.compiler)


def _type_probe_preprocessing(
    preprocessing: PreprocessingConfig,
    native_fortran_flags: Iterable[str],
) -> PreprocessingConfig:
    """Use the native target profile for internal semantic type measurement."""
    flags = [str(flag) for flag in native_fortran_flags]
    if not flags:
        return preprocessing
    return replace(
        preprocessing,
        compiler_args=[*preprocessing.compiler_args, *flags],
    )


def _wrap_compile_time_values(
    parsed,
    preprocessing: PreprocessingConfig,
    *,
    report=None,
    runner: list[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> dict[str, int] | None:
    """Measure only the compile-time values required by a parsed source project.

    Returns ``None`` when no report/probe is possible or no values are needed.
    Otherwise it delegates the parsed requirements and optional probe controls
    to the type evaluator, which may read or refresh its cache.
    """
    if report is None and not _can_probe_fortran_types(preprocessing):
        return None
    requirements = collect_semantic_compile_time_requirements(parsed)
    if not requirements:
        return None
    return evaluate_fortran_type_requirements(
        preprocessing,
        requirements,
        report=report,
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )


def _wrap_type_facts(
    parsed,
    preprocessing: PreprocessingConfig,
    *,
    compile_time_values: dict[str, int] | None,
    report=None,
    runner: list[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> dict[tuple[str, str | None], dict[str, object]] | None:
    """Measure native type-storage facts required by a parsed source project.

    Uses prior ``compile_time_values`` to derive requirements.  Returns
    ``None`` when probing is unavailable or unnecessary; otherwise delegates to
    the type-fact evaluator, which may execute or reuse a compiler probe.
    """
    if report is None and not _can_probe_fortran_types(preprocessing):
        return None
    requirements = collect_fortran_type_storage_requirements(parsed, compile_time_values=compile_time_values)
    if not requirements:
        return None
    return evaluate_fortran_type_facts(
        preprocessing,
        requirements,
        report=report,
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )


def _bundle_output_name(bundle: _PyiContractBundle) -> str:
    """Derive a default extension name from a file or package-entry contract.

    Package ``__init__.pyi`` entries use their parent directory name; ordinary
    contract files use their stem.  The bundle is read only and name validation
    happens separately.
    """
    if bundle.entry.name == "__init__.pyi":
        return bundle.entry.resolve().parent.name
    return bundle.entry.stem


# Source-to-semantic preparation


def _fortran_wrapper_module(
    source_paths: tuple[Path, ...],
    *,
    preprocessing: PreprocessingConfig,
    type_probe_preprocessing: PreprocessingConfig,
    output_name: str | None,
    fortran_type_report,
    fortran_type_probe_runner: list[str] | None,
    fortran_type_probe_cache_dir: str | Path | None,
    refresh_fortran_type_probe: bool,
    assume_intent_in_scalars: bool = False,
) -> tuple[object, SemanticModule, tuple[SemanticModule, ...]]:
    """Parse Fortran sources, resolve type facts, and form one wrapper module."""
    # Preprocess and parse the complete source project.
    preprocessed_sources = {
        str(source_path): _fortran_source_for_pipeline(source_path, preprocessing) for source_path in source_paths
    }
    parsed = parse_fortran_project(preprocessed_sources)

    # Measure compiler-dependent values before building semantic IR.
    compile_time_values = _wrap_compile_time_values(
        parsed,
        type_probe_preprocessing,
        report=fortran_type_report,
        runner=fortran_type_probe_runner,
        cache_dir=fortran_type_probe_cache_dir,
        refresh=refresh_fortran_type_probe,
    )
    type_facts = _wrap_type_facts(
        parsed,
        type_probe_preprocessing,
        compile_time_values=compile_time_values,
        report=fortran_type_report,
        runner=fortran_type_probe_runner,
        cache_dir=fortran_type_probe_cache_dir,
        refresh=refresh_fortran_type_probe,
    )

    # Preserve source export paths while flattening the wrapper-facing module.
    modules = fortran_project_to_semantic_modules(
        parsed,
        compile_time_values=compile_time_values,
        type_facts=type_facts,
        assume_intent_in_scalars=assume_intent_in_scalars,
    )
    _apply_source_python_exports(modules)
    module_name = _validated_wrapper_module_name(output_name, source_paths[0].stem)
    return parsed, _merge_wrapper_modules(modules, name=module_name), tuple(modules)


def _complete_pyi_fortran_boolean_types(
    modules: list[SemanticModule],
    *,
    compiler: str,
    compiler_args: Iterable[str],
) -> None:
    """Attach exact compiler logical spellings to Boolean contract types.

    The helper consumes loaded semantic modules plus the selected Fortran
    compiler target.  It probes only when a Boolean type occurs, then mutates
    each such type's source origin before policy completion.  All Boolean names
    retain their one-byte NumPy dtype; the attached spelling is solely the
    native bridge representation and ambiguous widths fail through the probe.
    """
    boolean_types = [
        semantic_type
        for module in modules
        for semantic_type in _module_semantic_types(module)
        if is_boolean_semantic_type_name(semantic_type.name)
    ]
    if not boolean_types:
        return
    native_types = resolve_fortran_logical_storage_types(
        PreprocessingConfig(
            mode="compiler",
            compiler=compiler,
            compiler_args=list(compiler_args),
        ),
        (boolean_storage_bits(semantic_type.name) for semantic_type in boolean_types),
    )
    for semantic_type in boolean_types:
        semantic_type.origin.source_language = "fortran"
        semantic_type.origin.source_type = native_types[boolean_storage_bits(semantic_type.name)]


# Public build entry points


def build_fortran_extension(
    sources: str | Path | Iterable[str | Path],
    *,
    output_dir: str | Path | None = None,
    output_name: str | None = None,
    preprocessing: PreprocessingConfig | None = None,
    strict_wrapper_names: bool = False,
    assume_intent_in_scalars: bool = False,
    fortran_type_report=None,
    fortran_type_probe_runner: list[str] | None = None,
    fortran_type_probe_cache_dir: str | Path | None = None,
    refresh_fortran_type_probe: bool = False,
    compile_input_sources: bool = True,
    native_fortran_sources: Iterable[str | Path] | None = None,
    native_fortran_flags: Iterable[str] | None = None,
    native_objects: Iterable[str | Path] | None = None,
    native_libraries: Iterable[str] | None = None,
    native_link_items: Iterable[NativeLinkItem | dict[str, object]] | None = None,
    native_library_dirs: Iterable[str | Path] | None = None,
    native_include_dirs: Iterable[str | Path] | None = None,
    makefile: bool = False,
    generate_sources: bool = False,
    jobs: int | None = None,
    verbose: bool | int = False,
    wrapper_compiler_debug: bool = False,
    wrapper_fortran_flags: Iterable[str] | None = None,
    wrapper_c_flags: Iterable[str] | None = None,
    _on_total_build_time: Callable[[float], None] | None = None,
) -> WrapperBuildResult:
    """Build a Python extension from one or more Fortran source files.

    This is the source-first public build API.  Supply a file, an ordered
    iterable of files, or a directory of Fortran sources, along with the native
    implementation that exports the wrapped procedures.  On success, import
    the built extension from ``result.shared_library.parent`` or inspect the
    generated sources and native link plan in the returned result.

    For the usual direct build, use the same sources for parsing and native
    compilation::

        result = build_fortran_extension(
            "solver.f90", output_dir="build/solver", output_name="solver"
        )
        # result.shared_library is the importable extension artifact.

    Parameters
    ----------
    sources
        One supported Fortran source path, an ordered iterable of paths, or a
        directory to discover recursively.  Source order is preserved and is
        used for compilation fallback ordering.
    output_dir, output_name
        Build directory and optional importable Python module name.  Omit
        ``output_dir`` to use ``__prik__`` in the current directory; omit
        ``output_name`` to derive it from the first source.
    preprocessing
        Optional source preprocessing configuration.  The default uses
        compiler-backed ``gfortran`` preprocessing.
    strict_wrapper_names
        Reject generated Python names that cannot be represented without a
        strict naming decision.
    assume_intent_in_scalars
        Treat a primitive scalar dummy that declares no ``intent`` as
        ``intent(in)`` rather than applying the conservative ``intent(inout)``
        default, so its value is not projected as a Python result.  A declared
        ``intent`` is always honored, and arrays, derived-type objects, and
        character values are unaffected.
    fortran_type_report, fortran_type_probe_runner,
    fortran_type_probe_cache_dir, refresh_fortran_type_probe
        Optional controls for compiler-probed Fortran type facts used while
        constructing semantic IR.
    compile_input_sources
        Compile ``sources`` as native implementation inputs.  Set false only
        when their implementation is supplied separately as objects, libraries,
        link items, or ``native_fortran_sources``.
    native_fortran_sources, native_fortran_flags
        Additional implementation sources and their compiler flags.
    native_objects, native_libraries, native_link_items,
    native_library_dirs, native_include_dirs
        Existing artifacts, ``-l`` names, ordered linker records, and search
        paths for the native implementation.  Use ``native_link_items`` when
        linker order is significant.
    makefile, generate_sources
        Choose a non-executing output mode.  ``makefile=True`` writes a
        replayable ``Makefile.prik``; ``generate_sources=True`` writes wrapper
        artifacts only.  They cannot be combined with each other or ``verbose``.
    jobs
        Positive maximum number of simultaneous compiler processes.  ``None``
        uses the available processor count.
    verbose, wrapper_compiler_debug, wrapper_fortran_flags, wrapper_c_flags
        Build progress output, generated-wrapper debug mode, and additional
        flags for generated bridge and binding compilation.

    Returns
    -------
    WrapperBuildResult
        Paths, generated files, compilation mode, and the complete native build
        plan.  ``compiled`` is false in source-only and Makefile modes.

    Raises
    ------
    ValueError, FileNotFoundError
        If inputs, module names, modes, native link items, or source paths are
        invalid.
    """

    generation_only, compile_jobs = _resolve_build_mode(
        makefile=makefile,
        generate_sources=generate_sources,
        jobs=jobs,
        verbose=verbose,
    )

    build_started = time.perf_counter()

    # 1. Collect the source and native implementation inputs.
    source_paths = _source_paths(sources)
    output_path, shared_library_output_path = _wrapper_output_paths(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    preprocessing = preprocessing or _default_preprocessing_config()
    supplemental_source_paths = tuple(Path(path) for path in (native_fortran_sources or ()))
    input_implementation_paths = source_paths if compile_input_sources else ()
    implementation_source_paths = (*input_implementation_paths, *supplemental_source_paths)
    native_inputs = _native_build_inputs(
        native_fortran_sources=implementation_source_paths,
        native_fortran_flags=native_fortran_flags,
        native_objects=native_objects,
        native_libraries=native_libraries,
        native_link_items=native_link_items,
        complete_native_link_items=None,
        native_library_dirs=native_library_dirs,
        native_include_dirs=native_include_dirs,
    )
    type_probe_preprocessing = _type_probe_preprocessing(preprocessing, native_inputs.source_flags)

    # 2. Parse source, resolve target facts, and assemble semantic IR.
    parsed, module, source_modules = _fortran_wrapper_module(
        source_paths,
        preprocessing=preprocessing,
        type_probe_preprocessing=type_probe_preprocessing,
        output_name=output_name,
        fortran_type_report=fortran_type_report,
        fortran_type_probe_runner=fortran_type_probe_runner,
        fortran_type_probe_cache_dir=fortran_type_probe_cache_dir,
        refresh_fortran_type_probe=refresh_fortran_type_probe,
        assume_intent_in_scalars=assume_intent_in_scalars,
    )

    # 3. Complete wrapper policy and generate the canonical wrapper.
    generated_wrapper = _generate_wrapper(
        module,
        strict_wrapper_names=strict_wrapper_names,
        verbose=verbose,
    )

    # 4. Prepare native compilation, dependency batches, and link inputs.
    wrapper_fortran_flags = _compiler_flags(wrapper_fortran_flags)
    wrapper_c_flags = _compiler_flags(wrapper_c_flags)
    compiler = _new_compiler(
        execute_commands=not generation_only,
        debug=wrapper_compiler_debug,
        input_compiler=preprocessing.compiler if preprocessing.uses_compiler else None,
    )
    native_source_objects, native_build_plan = _prepare_native_build_plan(native_inputs, output_path=output_path)
    native_compile_batches = _project_compile_batches(parsed, native_source_objects)

    # 5. Build the extension, or retain the generated source/Makefile plan.
    result = _build_generated_wrapper_extension(
        generated_wrapper,
        output_dir=output_path,
        shared_library_output_dir=shared_library_output_path,
        sources=source_paths,
        native_build_plan=native_build_plan,
        native_dependencies=native_source_objects,
        native_compile_batches=native_compile_batches,
        native_link_args=_generated_wrapper_native_link_args(native_build_plan),
        wrapper_fortran_flags=wrapper_fortran_flags,
        wrapper_c_flags=wrapper_c_flags,
        compiler=compiler,
        compile_jobs=1 if generation_only else compile_jobs,
        verbose=verbose,
    )
    result = _finalize_build_mode(
        result,
        makefile=makefile,
        generate_sources=generate_sources,
        compiler=compiler,
        source_objects=native_source_objects,
        extra_dependencies=_link_item_paths(native_build_plan.link_items),
    )
    _write_build_contract_package(source_modules, output_path, verbose=verbose)
    _report_total_build_time(
        verbose,
        time.perf_counter() - build_started,
        on_total_build_time=_on_total_build_time,
    )
    return result


def build_pyi_extension(
    contract: str | Path,
    *,
    input_compiler: str = "gfortran",
    native_fortran_sources: Iterable[str | Path] | None = None,
    native_fortran_flags: Iterable[str] | None = None,
    native_objects: Iterable[str | Path] | None = None,
    native_libraries: Iterable[str] | None = None,
    native_link_items: Iterable[NativeLinkItem | dict[str, object]] | None = None,
    native_library_dirs: Iterable[str | Path] | None = None,
    native_include_dirs: Iterable[str | Path] | None = None,
    output_name: str | None = None,
    output_dir: str | Path | None = None,
    strict_wrapper_names: bool = False,
    makefile: bool = False,
    generate_sources: bool = False,
    jobs: int | None = None,
    verbose: bool | int = False,
    complete_native_link_items: Iterable[NativeLinkItem | dict[str, object]] | None = None,
    wrapper_compiler_debug: bool = False,
    wrapper_fortran_flags: Iterable[str] | None = None,
    wrapper_c_flags: Iterable[str] | None = None,
    _on_total_build_time: Callable[[float], None] | None = None,
) -> WrapperBuildResult:
    """Build a Python extension from an editable semantic ``.pyi`` contract.

    Use this API when the public Python surface is defined by a semantic
    contract and native code already exists separately.  The entry contract may
    import relative ``.pyi`` modules; all reachable native declarations are
    validated, rendered, and linked into one extension.

    For example, compile an existing native implementation and pass its object
    file to the contract build::

        result = build_pyi_extension(
            "api.pyi", native_objects=["build/api.o"], output_dir="build/api"
        )

    Parameters
    ----------
    contract
        Existing semantic ``.pyi`` entry file.  Its relative-import graph is
        loaded as one contract bundle.
    input_compiler
        Fortran compiler executable used for generated bridge code and optional
        native source compilation.
    native_fortran_sources, native_fortran_flags
        Existing implementation source paths to compile and their flags.
    native_objects, native_libraries, native_link_items,
    native_library_dirs, native_include_dirs
        Existing artifacts, ``-l`` names, ordered linker records, and search
        paths.  Use ``native_link_items`` to append ordered inputs, or
        ``complete_native_link_items`` to supply the full ordered link plan.
    output_name, output_dir
        Optional Python extension name and build directory.  The default name
        comes from the contract file or package entry.
    strict_wrapper_names
        Enforce strict generated Python-name validation during policy
        completion.
    makefile, generate_sources
        Select non-executing output: a replayable ``Makefile.prik`` or generated
        sources only.  These modes are mutually exclusive and cannot be verbose.
    jobs
        Positive compiler-process limit; omit to use available processors.
    verbose, wrapper_compiler_debug, wrapper_fortran_flags, wrapper_c_flags
        Progress, generated-wrapper debug mode, and generated bridge/binding
        compiler flags.

    Returns
    -------
    WrapperBuildResult
        Generated artifact paths, a native build plan, and an in-memory build
        manifest.  Makefile mode also persists that manifest and records its
        path in ``build_manifest``.

    Raises
    ------
    ValueError, FileNotFoundError
        If the contract graph, native inputs, requested mode, or link plan is
        invalid.
    """

    generation_only, compile_jobs = _resolve_build_mode(
        makefile=makefile,
        generate_sources=generate_sources,
        jobs=jobs,
        verbose=verbose,
    )

    build_started = time.perf_counter()

    # 1. Load the contract graph and collect native implementation inputs.
    entry = _pyi_entry_path(contract)
    bundle = _pyi_contract_bundle(entry)
    native_inputs = _native_build_inputs(
        native_fortran_sources=native_fortran_sources,
        native_fortran_flags=native_fortran_flags,
        native_objects=native_objects,
        native_libraries=native_libraries,
        native_link_items=native_link_items,
        complete_native_link_items=complete_native_link_items,
        native_library_dirs=native_library_dirs,
        native_include_dirs=native_include_dirs,
    )

    output_path, shared_library_output_path = _wrapper_output_paths(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    wrapper_fortran_flags = _compiler_flags(wrapper_fortran_flags)
    wrapper_c_flags = _compiler_flags(wrapper_c_flags)

    # 2. Assemble semantic IR, complete policy, and generate the wrapper.
    modules = list(bundle.modules)
    _complete_pyi_fortran_boolean_types(
        modules,
        compiler=input_compiler,
        compiler_args=(*native_inputs.source_flags, *wrapper_fortran_flags),
    )
    module_name = _validated_wrapper_module_name(output_name, _bundle_output_name(bundle))
    module = _merge_wrapper_modules(modules, name=module_name)
    generated_wrapper = _generate_wrapper(
        module,
        strict_wrapper_names=strict_wrapper_names,
        verbose=verbose,
    )

    # 3. Prepare native compilation and link inputs before selecting the compiler.
    native_source_objects, native_build_plan = _prepare_native_build_plan(native_inputs, output_path=output_path)
    compiler = _new_compiler(
        execute_commands=not generation_only,
        debug=wrapper_compiler_debug,
        input_compiler=input_compiler,
    )
    native_array_build_requirements = native_array_handle_build_requirements(module)

    # 4. Build the extension and attach its replayable manifest data.
    result = _build_generated_wrapper_extension(
        generated_wrapper,
        output_dir=output_path,
        shared_library_output_dir=shared_library_output_path,
        sources=bundle.paths,
        native_build_plan=native_build_plan,
        native_dependencies=native_source_objects,
        native_compile_batches=_serial_compile_batches(native_source_objects),
        native_link_args=_generated_wrapper_native_link_args(native_build_plan),
        wrapper_fortran_flags=wrapper_fortran_flags,
        wrapper_c_flags=wrapper_c_flags,
        compiler=compiler,
        compile_jobs=1 if generation_only else compile_jobs,
        verbose=verbose,
    )
    result = _with_pyi_manifest(
        result,
        bundle=bundle,
        strict_wrapper_names=strict_wrapper_names,
        requested_output_name=output_name,
        input_compiler=input_compiler,
        native_fortran_flags=native_inputs.source_flags,
        wrapper_compiler_debug=wrapper_compiler_debug,
        wrapper_fortran_flags=wrapper_fortran_flags,
        wrapper_c_flags=wrapper_c_flags,
        native_array_build_requirements=native_array_build_requirements,
    )

    # 5. Optionally persist the manifest and Makefile instead of a direct build.
    build_manifest = None
    makefile_dependencies: tuple[Path, ...] = ()
    if makefile:
        build_manifest = _write_build_manifest(output_path / _BUILD_MANIFEST_NAME, result.manifest)
        makefile_dependencies = (
            *bundle.paths,
            *_link_item_paths(native_build_plan.link_items),
            build_manifest,
        )
    result = _finalize_build_mode(
        result,
        makefile=makefile,
        generate_sources=generate_sources,
        compiler=compiler,
        source_objects=native_source_objects,
        extra_dependencies=makefile_dependencies,
        build_manifest=build_manifest,
    )
    _report_total_build_time(
        verbose,
        time.perf_counter() - build_started,
        on_total_build_time=_on_total_build_time,
    )
    return result


def build_pyi_extension_from_manifest(
    manifest: str | Path,
    *,
    output_name: str | None = None,
    input_compiler: str | None = None,
    include_dirs: Iterable[str | Path] | None = None,
    makefile: bool = False,
    generate_sources: bool = False,
    jobs: int | None = None,
    verbose: bool | int = False,
    _on_total_build_time: Callable[[float], None] | None = None,
) -> WrapperBuildResult:
    """Replay a saved semantic ``.pyi`` wrapper build manifest.

    First create a manifest with ``build_pyi_extension(..., makefile=True)``.
    This entrypoint restores its contract, compiler choices, native compilation
    sources, and ordered link plan, then delegates to ``build_pyi_extension``.
    The current contract import graph must still match the recorded graph.

    Parameters
    ----------
    manifest
        Existing ``prik-build.json`` produced by a semantic ``.pyi`` build.
    output_name, input_compiler, include_dirs
        Optional replay overrides for the extension name, compiler executable,
        and additional native include directories.  All other build choices are
        restored from the manifest.
    makefile, generate_sources, jobs, verbose
        Output mode and compilation controls with the same meanings as
        :func:`build_pyi_extension`.

    Returns
    -------
    WrapperBuildResult
        The direct-build, source-only, or Makefile result produced by replay.

    Raises
    ------
    FileNotFoundError, ValueError
        If the manifest is absent or incompatible, recorded inputs are invalid,
        or the present contract graph no longer matches the saved build.
    """

    build_started = time.perf_counter()

    # 1. Load the recorded build inputs and validate required sections.
    manifest_path, payload = _load_build_manifest(manifest)
    base = manifest_path.parent
    native_section = _manifest_section(payload, "native_build_plan")
    output_section = _manifest_section(payload, "output")
    compiler_section = _manifest_section(payload, "compiler")
    extension_section = _manifest_section(payload, "extension")

    entry_contract = payload.get("entry_contract")
    if not isinstance(entry_contract, str):
        raise ValueError("Wrapper build manifest missing entry_contract")
    output_dir = output_section.get("output_dir")
    if not isinstance(output_dir, str):
        raise ValueError("Wrapper build manifest missing output.output_dir")
    output_path = _resolve_manifest_path(output_dir, base=base)
    strict_wrapper_names = output_section.get("strict_wrapper_names", False)
    if not isinstance(strict_wrapper_names, bool):
        raise ValueError("Wrapper build manifest output.strict_wrapper_names must be a boolean")
    requested_name = output_name if output_name is not None else extension_section.get("requested_name")
    if requested_name is not None and not isinstance(requested_name, str):
        raise ValueError("Wrapper build manifest extension.requested_name must be a string or null")

    # 2. Restore native include paths and compiler selection from the manifest.
    manifest_module_dirs = _manifest_path_list(native_section, "module_dirs", base=base)
    native_include_dirs = _unique_paths(
        (
            *(path for path in manifest_module_dirs if _path_key(path) != _path_key(output_path)),
            *(Path(path) for path in (include_dirs or ())),
        )
    )
    selected_input_compiler = input_compiler
    if selected_input_compiler is None:
        selected_input_compiler = _manifest_string(compiler_section, "input_executable")

    # 3. Delegate execution to the regular `.pyi` build path.
    result = build_pyi_extension(
        _resolve_manifest_path(entry_contract, base=base),
        input_compiler=selected_input_compiler,
        native_fortran_sources=_manifest_compilation_sources(native_section, base=base),
        native_fortran_flags=_manifest_string_list(compiler_section, "fortran_flags"),
        native_include_dirs=native_include_dirs,
        native_library_dirs=_manifest_path_list(native_section, "library_dirs", base=base),
        output_name=requested_name,
        output_dir=output_path,
        strict_wrapper_names=strict_wrapper_names,
        makefile=makefile,
        generate_sources=generate_sources,
        jobs=jobs,
        verbose=verbose,
        wrapper_compiler_debug=_manifest_bool(compiler_section, "wrapper_compiler_debug"),
        wrapper_fortran_flags=_manifest_string_list(compiler_section, "wrapper_fortran_flags"),
        wrapper_c_flags=_manifest_string_list(compiler_section, "wrapper_c_flags"),
        complete_native_link_items=_manifest_link_items(native_section, base=base),
        _on_total_build_time=lambda _elapsed: None,
    )

    # 4. Ensure the current contract graph still matches the recorded build.
    recorded_contracts = tuple(
        _resolve_manifest_path(path, base=base) for path in _manifest_string_list(payload, "contract_paths")
    )
    if result.sources != recorded_contracts:
        raise ValueError("Current .pyi import graph does not match the wrapper build manifest contract_paths")
    _report_total_build_time(
        verbose,
        time.perf_counter() - build_started,
        on_total_build_time=_on_total_build_time,
    )
    return result


# Direct-execution example


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    import numpy as np

    source_text = """\
real(8) function scale(value, factor) result(output)
  real(8), intent(in) :: value
  real(8), intent(in) :: factor
  output = value * factor
end function scale
"""
    with TemporaryDirectory() as temporary_dir:
        temporary_path = Path(temporary_dir)
        source_path = temporary_path / "scale.f90"
        source_path.write_text(source_text, encoding="utf-8")
        build = build_fortran_extension(
            source_path,
            output_dir=temporary_path / "build",
            output_name="build_example",
        )
        module = build.import_module()
        value = module.scale(np.float64(3.0), np.float64(2.5))
        print(f"scale(3.0, 2.5) = {value}")
