"""End-to-end Fortran-to-Python extension build pipeline."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field, replace
import json
import os
from pathlib import Path
import shlex
import time

from x2py.compiling.objects import ObjectFile
from x2py.compiling.compilers import Compiler, get_condaless_search_path
from x2py.compiling.native_support import install_native_support
from x2py.parsers.fortran.parser import parse_fortran_project
from x2py.probes.fortran_types import evaluate_fortran_type_facts, evaluate_fortran_type_requirements
from x2py.pipeline.preprocessing import PreprocessingConfig, preprocess_source
from x2py.pipeline.wrapper_artifacts import GeneratedSourceFile, RenderedGeneratedWrapperArtifacts
from x2py.semantics.fortran2ir import (
    collect_fortran_type_storage_requirements,
    collect_semantic_compile_time_requirements,
    fortran_project_to_semantic_modules,
)
from x2py.semantics.models import (
    PYTHON_EXPORTS_METADATA,
    PYTHON_EXPORTS_PREPARED_METADATA,
    ProcedureOverloadSet,
    SemanticClass,
    SemanticFunction,
    SemanticImport,
    SemanticModule,
    SemanticPrototype,
    SemanticVariable,
)
from x2py.semantics.native_contract import NATIVE_CONTRACT_PREPARED_METADATA, validate_pyi_native_contract
from x2py.semantics.native_array_handles import (
    NativeArrayBuildRequirements,
    native_array_handle_build_requirements,
)
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.pipeline.pyi import _PyiSemanticModuleCache
from x2py.semantics.pyi_metadata import PYI_LOADED_METADATA
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


_DEFAULT_BUILD_DIR_NAME = "__x2py__"
_BUILD_MANIFEST_NAME = "x2py-build.json"
_BUILD_MANIFEST_SCHEMA_VERSION = 2
_FORTRAN_SOURCE_SUFFIXES = {".f", ".f03", ".f08", ".f77", ".f90", ".f95", ".for", ".ftn"}
_C_SOURCE_SUFFIXES = {".c"}
_NATIVE_PATH_LINK_KINDS = frozenset({"object", "archive", "shared_library"})
_NATIVE_LINK_KINDS = frozenset({*_NATIVE_PATH_LINK_KINDS, "named_library", "linker_argument"})
_RENDERED_WRAPPER_SOURCE_LANGUAGES = {
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
_RENDERED_WRAPPER_NATIVE_SUPPORT_IMPORTS = {
    "binding_support": ("binding_support/x2py_binding",),
}


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


@dataclass(frozen=True)
class NativeCompilationUnit:
    """One caller-supplied native source and the object it produces."""

    source: Path
    object_path: Path
    language: str
    module_dir: Path | None = None
    include_dirs: tuple[Path, ...] = ()
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", Path(self.source))
        object.__setattr__(self, "object_path", Path(self.object_path))
        if self.module_dir is not None:
            object.__setattr__(self, "module_dir", Path(self.module_dir))
        object.__setattr__(self, "include_dirs", tuple(Path(path) for path in self.include_dirs))
        object.__setattr__(self, "flags", tuple(str(flag) for flag in self.flags))

    def to_dict(self) -> dict[str, object]:
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
    """One caller-supplied native artifact used by the extension link."""

    path: Path
    kind: str

    def __post_init__(self) -> None:
        if self.kind not in _NATIVE_PATH_LINK_KINDS:
            raise ValueError(f"Unsupported native artifact kind: {self.kind!r}")
        object.__setattr__(self, "path", Path(self.path))

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "path": str(self.path),
        }


@dataclass(frozen=True)
class NativeLinkItem:
    """One ordered item in the native implementation link plan."""

    kind: str
    value: Path | str

    def __post_init__(self) -> None:
        if self.kind not in _NATIVE_LINK_KINDS:
            raise ValueError(f"Unsupported native link item kind: {self.kind!r}")
        if self.kind in _NATIVE_PATH_LINK_KINDS:
            object.__setattr__(self, "value", Path(self.value))
        else:
            object.__setattr__(self, "value", str(self.value))

    def to_dict(self) -> dict[str, object]:
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
    """Extension-level native implementation build and link plan."""

    compilation_units: tuple[NativeCompilationUnit, ...] = ()
    produced_objects: tuple[Path, ...] = ()
    prebuilt_artifacts: tuple[NativePrebuiltArtifact, ...] = ()
    module_dirs: tuple[Path, ...] = ()
    include_dirs: tuple[Path, ...] = ()
    library_dirs: tuple[Path, ...] = ()
    link_items: tuple[NativeLinkItem, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "compilation_units", tuple(self.compilation_units))
        object.__setattr__(self, "produced_objects", tuple(Path(path) for path in self.produced_objects))
        object.__setattr__(self, "prebuilt_artifacts", tuple(self.prebuilt_artifacts))
        object.__setattr__(self, "module_dirs", tuple(Path(path) for path in self.module_dirs))
        object.__setattr__(self, "include_dirs", tuple(Path(path) for path in self.include_dirs))
        object.__setattr__(self, "library_dirs", tuple(Path(path) for path in self.library_dirs))
        object.__setattr__(self, "link_items", tuple(self.link_items))

    def to_dict(self) -> dict[str, object]:
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
    """Artifacts produced by one wrapper build."""

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

    def to_dict(self) -> dict[str, object]:
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
        }


def _default_preprocessing_config() -> PreprocessingConfig:
    return PreprocessingConfig(
        mode="compiler",
        compiler="gfortran",
        defines=[],
        include_dirs=[],
    )


def _fortran_source_for_pipeline(path: Path, preprocessing: PreprocessingConfig) -> str:
    if preprocessing.uses_compiler:
        return preprocess_source(path, language="fortran", config=preprocessing).source
    return path.read_text(encoding="utf-8")


def _compiler_flags(flags: Iterable[str] | None) -> tuple[str, ...]:
    """Normalize caller-supplied compiler flags."""
    return tuple(str(flag) for flag in (flags or ()))


def _new_compiler(
    *,
    execute_commands: bool = True,
    debug: bool = False,
    input_compiler: str | None = None,
) -> Compiler:
    return Compiler.from_fortran_executable(
        input_compiler or "gfortran",
        debug=debug,
        execute_commands=execute_commands,
        search_path=get_condaless_search_path("verbose"),
    )


def _expected_generated_files(
    *,
    source_objects: tuple[ObjectFile, ...],
    output_dir: Path,
    module_name: str,
    shared_library: Path,
) -> tuple[Path, ...]:
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


def _rendered_artifact_output_path(output_dir: Path, path: Path) -> Path:
    """Return the output path for one rendered wrapper artifact."""
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Rendered wrapper artifact path must stay inside the build directory: {path}")
    return output_dir / path


def _write_rendered_wrapper_sources(
    rendered: RenderedGeneratedWrapperArtifacts,
    output_dir: Path,
    *,
    verbose: bool | int = False,
) -> tuple[Path, ...]:
    """Write rendered wrapper-plan sources into one build directory."""
    written = []
    for source in rendered.sources:
        path = _rendered_artifact_output_path(output_dir, source.path)
        _print_verbose_step(verbose, f"{_rendered_source_write_label(rendered, source.path)}: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source.text, encoding="utf-8")
        written.append(path)
    return tuple(written)


def _rendered_source_payloads(
    rendered: RenderedGeneratedWrapperArtifacts,
) -> dict[Path, GeneratedSourceFile]:
    """Return rendered payloads keyed by generated artifact path."""
    return {Path(source.path): source for source in rendered.sources}


def _rendered_source_write_label(rendered: RenderedGeneratedWrapperArtifacts, source_path: Path) -> str:
    """Return the verbose write label for one generated artifact."""
    if source_path in rendered.artifacts.bridge_sources:
        return "Write bridge source"
    if source_path in rendered.artifacts.binding_sources:
        return "Write binding source"
    if source_path in rendered.artifacts.header_files:
        return "Write binding header"
    return "Write wrapper artifact"


def _rendered_wrapper_compile_source_paths(
    rendered: RenderedGeneratedWrapperArtifacts,
) -> tuple[Path, ...]:
    """Return rendered wrapper-plan source paths in compile order."""
    source_paths = (*rendered.artifacts.bridge_sources, *rendered.artifacts.binding_sources)
    payloads = _rendered_source_payloads(rendered)
    missing = tuple(path for path in source_paths if path not in payloads)
    if missing:
        raise ValueError(f"Rendered wrapper artifacts are missing source payloads: {missing!r}")
    return source_paths


def _rendered_wrapper_source_language(path: Path) -> str:
    """Return the compiler language for one rendered wrapper source."""
    try:
        return _RENDERED_WRAPPER_SOURCE_LANGUAGES[path.suffix.lower()]
    except KeyError:
        raise ValueError(f"Unsupported rendered wrapper source suffix: {path}") from None


def _rendered_wrapper_native_support_imports(native_support_keys: Iterable[str]) -> tuple[str, ...]:
    """Return native-support import keys consumed by the support installer."""
    imports: list[str] = []
    for key in native_support_keys:
        try:
            imports.extend(_RENDERED_WRAPPER_NATIVE_SUPPORT_IMPORTS[key])
        except KeyError:
            raise ValueError(f"Unsupported wrapper native support key: {key!r}") from None
    return tuple(imports)


def _rendered_wrapper_object_file(
    source_path: Path,
    output_dir: Path,
    *,
    flags: tuple[str, ...],
    include_dirs: tuple[Path, ...],
    language: str,
) -> ObjectFile:
    """Return one explicit object-file input for a rendered wrapper source."""
    source = _rendered_artifact_output_path(output_dir, source_path)
    return ObjectFile(
        source=source,
        object_path=source.with_suffix(".o"),
        language=language,
        flags=flags,
        include_dirs=include_dirs,
        tools=frozenset({"python"}) if language == "c" else frozenset(),
    )


def _rendered_wrapper_object_stages(
    rendered: RenderedGeneratedWrapperArtifacts,
    output_dir: Path,
    *,
    wrapper_fortran_flags: tuple[str, ...],
    wrapper_c_flags: tuple[str, ...],
    native_module_dirs: tuple[Path, ...],
) -> tuple[tuple[ObjectFile, ...], tuple[ObjectFile, ...]]:
    """Return bridge and binding objects in their required compile order."""
    source_paths = _rendered_wrapper_compile_source_paths(rendered)
    bridge_source_paths = source_paths[: len(rendered.artifacts.bridge_sources)]
    binding_source_paths = source_paths[len(bridge_source_paths) :]
    bridge_objects = tuple(
        _rendered_wrapper_object_file(
            source_path,
            output_dir,
            flags=wrapper_fortran_flags,
            include_dirs=native_module_dirs,
            language=_rendered_wrapper_source_language(source_path),
        )
        for source_path in bridge_source_paths
    )
    binding_objects = tuple(
        _rendered_wrapper_object_file(
            source_path,
            output_dir,
            flags=wrapper_c_flags,
            include_dirs=native_module_dirs,
            language=_rendered_wrapper_source_language(source_path),
        )
        for source_path in binding_source_paths
    )
    return bridge_objects, binding_objects


def _rendered_wrapper_link_language(
    bridge_objects: tuple[ObjectFile, ...],
    binding_objects: tuple[ObjectFile, ...],
) -> str:
    """Return the linker language for rendered wrapper-plan sources."""
    if bridge_objects:
        return "fortran"
    if not binding_objects:
        raise ValueError("Rendered wrapper artifacts must include at least one binding source")
    return binding_objects[-1].language


@dataclass(frozen=True)
class _CompiledObject:
    command: tuple[str, ...] | None
    elapsed: float


def _compile_one_object(compiler: Compiler, object_file: ObjectFile) -> _CompiledObject:
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
    return tuple(
        (object_file, executor.submit(_compile_one_object, compiler, object_file)) for object_file in object_files
    )


def _finish_object_stage(
    pending: Iterable[tuple[ObjectFile, Future[_CompiledObject]]],
    *,
    label: str,
    verbose: bool | int,
) -> None:
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

    with ThreadPoolExecutor(max_workers=jobs, thread_name_prefix="x2py-compile") as executor:
        binding_futures = _submit_object_stage(executor, compiler, bindings)
        for batch in native_groups:
            native_futures = _submit_object_stage(executor, compiler, batch)
            _finish_object_stage(native_futures, label="Compile native source", verbose=verbose)
        bridge_futures = _submit_object_stage(executor, compiler, bridges)
        _finish_object_stage(bridge_futures, label="Compile bridge source", verbose=verbose)
        _finish_object_stage(binding_futures, label="Compile binding source", verbose=verbose)


def _build_rendered_wrapper_extension(
    rendered: RenderedGeneratedWrapperArtifacts,
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
    """Build one extension from rendered wrapper-plan artifacts."""
    rendered.freeze()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    shared_output_path = Path(shared_library_output_dir) if shared_library_output_dir is not None else output_path
    shared_output_path.mkdir(parents=True, exist_ok=True)
    _write_rendered_wrapper_sources(rendered, output_path, verbose=verbose)

    compiler = compiler or _new_compiler()
    resolved_native_build_plan = native_build_plan or NativeBuildPlan()
    bridge_objects, binding_objects = _rendered_wrapper_object_stages(
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
    native_support_imports = _rendered_wrapper_native_support_imports(rendered.artifacts.native_support_keys)
    install_native_support(
        native_support_imports,
        x2py_dirpath=str(output_path),
        verbose=verbose,
    )
    _compile_extension_objects(
        compiler,
        native_batches=native_compile_batches,
        bridge_objects=bridge_objects,
        binding_objects=binding_objects,
        jobs=_normalize_compile_jobs(compile_jobs),
        verbose=verbose,
    )

    linking_started = time.perf_counter()
    shared_library = compiler.link_extension(
        module_name=rendered.artifacts.module_name,
        output_dir=shared_output_path,
        language=_rendered_wrapper_link_language(bridge_objects, binding_objects),
        objects=(*tuple(native_dependencies), *bridge_objects, *binding_objects),
        link_args=tuple(native_link_args),
        library_dirs=resolved_native_build_plan.library_dirs,
        flags=_compiler_flags(wrapper_c_flags),
        verbose=verbose,
    )
    _print_verbose_timing(verbose, time.perf_counter() - linking_started)
    generated_sources = tuple(
        path
        for path in rendered.artifacts.generated_files
        if _rendered_artifact_output_path(output_path, path).exists()
    )
    generated_sources = tuple(_rendered_artifact_output_path(output_path, path) for path in generated_sources)
    return WrapperBuildResult(
        sources=tuple(Path(source) for source in sources),
        module_name=rendered.artifacts.module_name,
        output_dir=output_path,
        shared_library=shared_library,
        build_makefile=None,
        compiled=True,
        generated_sources=generated_sources,
        generated_files=_expected_generated_files(
            source_objects=tuple(native_dependencies),
            output_dir=output_path,
            module_name=rendered.artifacts.module_name,
            shared_library=shared_library,
        ),
        native_build_plan=resolved_native_build_plan,
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
        path=result.output_dir / "Makefile.x2py",
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


def _render_wrapper_plan(
    module: SemanticModule,
    *,
    progress: Callable[[str, float | None], None] | None = None,
) -> RenderedGeneratedWrapperArtifacts:
    """Render one policy-completed module through the canonical generator."""
    plan = WrapperPlanner().build(module)
    return WrapperCodeGenerator().generate(plan, progress=progress)


def _generated_wrapper_plan_artifacts(
    module: SemanticModule,
    *,
    strict_wrapper_names: bool,
    verbose: bool | int = False,
) -> RenderedGeneratedWrapperArtifacts:
    """Complete policy and generate the one production wrapper representation."""
    _print_verbose_step(verbose, "Complete wrapper policies")
    policy_started = time.perf_counter()
    complete_semantic_policies(module, strict_wrapper_names=strict_wrapper_names)
    _print_verbose_timing(verbose, time.perf_counter() - policy_started)

    def render_progress(label: str, elapsed: float | None) -> None:
        if elapsed is None:
            _print_verbose_step(verbose, label)
            return
        _print_verbose_timing(verbose, elapsed)

    return _render_wrapper_plan(module, progress=render_progress)


def _source_compile_object(
    source_path: Path,
    output_dir: Path,
    *,
    object_stem: str,
    flags: Iterable[str] = (),
    include_dirs: Iterable[Path] = (),
) -> ObjectFile:
    target = output_dir / f"{object_stem}.o"
    return ObjectFile(
        source=source_path,
        object_path=target,
        language="fortran",
        flags=tuple(flags),
        include_dirs=(*tuple(include_dirs), output_dir),
    )


def _serial_compile_batches(object_files: Iterable[ObjectFile]) -> tuple[tuple[ObjectFile, ...], ...]:
    return tuple((object_file,) for object_file in object_files)


def _fortran_owner_used_modules(owner: object) -> set[str]:
    used = {str(name).lower() for name in getattr(owner, "uses", {})}
    for procedure in getattr(owner, "procedures", ()):
        used.update(str(name).lower() for name in getattr(procedure, "uses", {}))
    for interface in getattr(owner, "interfaces", ()):
        for procedure in getattr(interface, "procedures", ()):
            used.update(str(name).lower() for name in getattr(procedure, "uses", {}))
    return used


def _fortran_file_used_modules(parsed_file: object) -> set[str]:
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
    parsed_files = tuple(getattr(parsed_project, "files", ()))
    parsed_by_source = {
        _path_key(Path(parsed_file.filename)): parsed_file
        for parsed_file in parsed_files
        if getattr(parsed_file, "filename", None)
    }
    object_sources = {_path_key(object_file.source) for object_file in object_files}
    if set(parsed_by_source) != object_sources:
        return _serial_compile_batches(object_files)

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


def _source_paths(sources: str | Path | Iterable[str | Path]) -> tuple[Path, ...]:
    paths = (Path(sources),) if isinstance(sources, str | Path) else tuple(Path(source) for source in sources)
    if not paths:
        raise ValueError("wrapper build requires at least one Fortran source file")
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Fortran source not found: {path}")
    return paths


def _wrapper_output_paths(output_dir: str | Path | None) -> tuple[Path, Path]:
    """Return build and extension directories owned by one wrapper invocation."""
    if output_dir is not None:
        path = Path(output_dir)
        return path, path
    invocation_dir = Path.cwd()
    build_dir = invocation_dir / _DEFAULT_BUILD_DIR_NAME
    return build_dir, build_dir


def _pyi_entry_path(contract: str | Path) -> Path:
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
    entry: Path
    leaves: tuple[Path, ...]
    paths: tuple[Path, ...]
    modules: tuple[SemanticModule, ...]


@dataclass(frozen=True)
class _NativeBuildInputs:
    source_paths: tuple[Path, ...]
    source_flags: tuple[str, ...]
    artifact_paths: tuple[Path, ...]
    libraries: tuple[str, ...]
    explicit_link_items: tuple[NativeLinkItem, ...]
    complete_link_items: tuple[NativeLinkItem, ...] | None
    link_item_paths: tuple[Path, ...]
    library_dirs: tuple[Path, ...]
    explicit_include_dirs: tuple[Path, ...]


def _pyi_contract_bundle(
    entry: Path,
) -> _PyiContractBundle:
    module_cache = _PyiSemanticModuleCache()
    discovered = {entry, *_discover_pyi_imports(entry, module_cache)}
    sorted_paths = tuple(sorted(discovered))
    loaded_modules = module_cache.paths_to_semantic_modules(sorted_paths)
    modules_by_path = dict(zip(sorted_paths, loaded_modules, strict=True))
    _validate_pyi_bundle_placement(entry, modules_by_path)
    _apply_pyi_python_exports(entry, modules_by_path)
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
            if not _declaration_is_external(declaration)
        ]
        if invalid:
            raise ValueError(
                "Package entry contracts cannot contain native module declarations; "
                "import module leaves or mark standalone procedures with @external. "
                f"Invalid declaration: {invalid[0]}"
            )

    namespace_imports = _namespace_imported_pyi_paths(entry, modules_by_path)
    for path in namespace_imports:
        module = modules_by_path[path]
        invalid = [
            declaration.name for declaration in _module_declarations(module) if _declaration_is_external(declaration)
        ]
        if invalid:
            raise ValueError(
                "A contract imported as a Python child namespace cannot contain @external declarations; "
                "keep standalone procedures in the entry contract or import external fragments by name. "
                f"Invalid declaration: {invalid[0]} in {path}"
            )


def _declaration_is_external(declaration: object) -> bool:
    if isinstance(declaration, ProcedureOverloadSet):
        return bool(declaration.procedures) and all(_declaration_is_external(item) for item in declaration.procedures)
    if isinstance(declaration, SemanticFunction):
        return declaration.origin.source_language == "fortran" and declaration.origin.native_scope is None
    return False


def _namespace_imported_pyi_paths(entry: Path, modules_by_path: dict[Path, SemanticModule]) -> set[Path]:
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
    target = parent.joinpath(*dotted_name.split("."))
    module_file = target.with_suffix(".pyi")
    if module_file.is_file() or not target.is_dir():
        return module_file
    return target / "__init__.pyi"


def _module_has_native_declarations(module: SemanticModule) -> bool:
    return bool(module.variables or module.functions or module.classes or module.overload_sets)


@dataclass
class _PyiExportNode:
    declarations: list[object] = field(default_factory=list)
    children: dict[str, _PyiExportNode] = field(default_factory=dict)
    origins: set[Path] = field(default_factory=set)


def _apply_pyi_python_exports(entry: Path, modules_by_path: dict[Path, SemanticModule]) -> None:
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
    if path not in modules_by_path:
        raise FileNotFoundError(f"Imported semantic .pyi contract not found: {path}")
    return _pyi_export_tree(path, modules_by_path, cache=cache, pending=pending)


def _merge_export_child(tree: _PyiExportNode, name: str, child: _PyiExportNode, *, origin: Path) -> None:
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
    return (*module.variables, *module.functions, *module.overload_sets, *module.classes)


def _declaration_metadata(declaration: object) -> dict[str, object]:
    if isinstance(declaration, ProcedureOverloadSet):
        if not declaration.procedures:
            return {}
        return declaration.procedures[0].metadata
    if isinstance(declaration, SemanticVariable | SemanticFunction | SemanticClass):
        return declaration.metadata
    raise TypeError(f"Unsupported semantic declaration: {type(declaration).__name__}")


def _declaration_exports(declaration: object) -> list[dict[str, object]]:
    metadata = _declaration_metadata(declaration)
    return metadata.setdefault(PYTHON_EXPORTS_METADATA, [])


def _set_declaration_exports(declaration: object, exports: list[dict[str, object]]) -> None:
    metadata = _declaration_metadata(declaration)
    metadata[PYTHON_EXPORTS_METADATA] = exports


def _apply_source_python_exports(modules: list[SemanticModule]) -> None:
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


def _existing_paths(
    paths: Iterable[str | Path] | None,
    *,
    kind: str,
    require_directory: bool = False,
) -> tuple[Path, ...]:
    resolved = tuple(Path(path) for path in (paths or ()))
    for path in resolved:
        if require_directory:
            if not path.is_dir():
                raise FileNotFoundError(f"{kind} directory not found: {path}")
        elif not path.is_file():
            raise FileNotFoundError(f"{kind} not found: {path}")
    return resolved


def _native_artifact_kind(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix in {".a", ".lib"}:
        return "archive"
    if suffix in {".so", ".dylib", ".dll"} or ".so." in name:
        return "shared_library"
    return "object"


def _unique_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
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


def _rendered_wrapper_native_link_args(plan: NativeBuildPlan) -> tuple[str, ...]:
    """Return link arguments not already supplied as rendered-wrapper dependencies."""
    produced_objects = {_path_key(path) for path in plan.produced_objects}
    return _native_link_args(
        item
        for item in plan.link_items
        if item.kind not in _NATIVE_PATH_LINK_KINDS or _path_key(Path(item.value)) not in produced_objects
    )


def _coerce_native_link_items(items: Iterable[NativeLinkItem | dict[str, object]] | None) -> tuple[NativeLinkItem, ...]:
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
    return tuple(Path(item.value) for item in link_items if item.kind in _NATIVE_PATH_LINK_KINDS)


def _path_key(path: Path) -> Path:
    return path.resolve(strict=False)


def _shared_library_dirs(link_items: Iterable[NativeLinkItem]) -> tuple[Path, ...]:
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
    library_dirs = _unique_paths(
        (
            *_existing_paths(native_library_dirs, kind="Native library", require_directory=True),
            *(path.parent for path in artifact_paths if _native_artifact_kind(path) == "shared_library"),
            *_shared_library_dirs(selected_link_items),
        )
    )
    explicit_include_dirs = _existing_paths(native_include_dirs, kind="Native include", require_directory=True)
    if (
        not source_paths
        and not artifact_paths
        and not libraries
        and not explicit_link_items
        and not complete_link_items
    ):
        raise ValueError(
            ".pyi wrapper build requires at least one native source, object, archive, shared library, "
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
    module_include_dirs = (output_path,) if inputs.source_paths else ()
    inferred_include_dirs = _unique_paths((*inputs.artifact_paths, *inputs.link_item_paths))
    return _unique_paths(
        (
            *module_include_dirs,
            *inputs.explicit_include_dirs,
            *(path.parent for path in inferred_include_dirs),
        )
    )


def _native_source_objects(
    inputs: _NativeBuildInputs,
    *,
    output_path: Path,
    include_dirs: tuple[Path, ...],
) -> tuple[ObjectFile, ...]:
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
    produced_object_keys = {_path_key(path) for path in plan.produced_objects}
    for path in _link_item_paths(plan.link_items):
        if _path_key(path) not in produced_object_keys and not path.is_file():
            raise FileNotFoundError(f"Native link item not found: {path}")


def _manifest_path(path: str | Path, *, base: Path) -> str:
    value = Path(path)
    absolute = value if value.is_absolute() else Path.cwd() / value
    try:
        return os.path.relpath(absolute, base)
    except ValueError:
        return str(absolute)


def _resolve_manifest_path(path: str, *, base: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else base / value


def _manifest_link_item(item: NativeLinkItem, *, base: Path) -> dict[str, object]:
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
    manifest_dir: Path,
) -> dict[str, object]:
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
        "native_build_plan": _manifest_native_plan(native_build_plan, base=manifest_dir),
    }


def _write_build_manifest(path: Path, manifest: dict[str, object]) -> Path:
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
        manifest_dir=result.output_dir,
    )
    return replace(result, manifest=manifest)


def _load_build_manifest(path: str | Path) -> tuple[Path, dict[str, object]]:
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
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Wrapper build manifest missing object section: {key}")
    return value


def _manifest_string_list(section: dict[str, object], key: str) -> tuple[str, ...]:
    value = section.get(key, ())
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"Wrapper build manifest field {key!r} must be a list of strings")
    return tuple(value)


def _manifest_bool(section: dict[str, object], key: str, *, default: bool = False) -> bool:
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"Wrapper build manifest field {key!r} must be a boolean")
    return value


def _manifest_string(section: dict[str, object], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Wrapper build manifest field {key!r} must be a non-empty string")
    return value


def _manifest_path_list(section: dict[str, object], key: str, *, base: Path) -> tuple[Path, ...]:
    return tuple(_resolve_manifest_path(item, base=base) for item in _manifest_string_list(section, key))


def _native_link_item_from_manifest(item: object, *, base: Path) -> NativeLinkItem:
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
    value = section.get("link_items", ())
    if not isinstance(value, list):
        raise ValueError("Wrapper build manifest field 'link_items' must be a list")
    return tuple(_native_link_item_from_manifest(item, base=base) for item in value)


def _manifest_compilation_sources(section: dict[str, object], *, base: Path) -> tuple[Path, ...]:
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


def _source_object_stems(source_paths: tuple[Path, ...]) -> tuple[str, ...]:
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


def _merge_wrapper_modules(modules: list[SemanticModule], *, name: str | None = None) -> SemanticModule:
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
    metadata: dict[str, object] = {"wrapper_native_modules": _wrapper_native_modules(modules)}
    if any(module.metadata.get(PYTHON_EXPORTS_PREPARED_METADATA) for module in modules):
        metadata[PYTHON_EXPORTS_PREPARED_METADATA] = True
    if any(module.metadata.get(PYI_LOADED_METADATA) for module in modules):
        metadata[PYI_LOADED_METADATA] = True
        metadata[NATIVE_CONTRACT_PREPARED_METADATA] = True
    return metadata


def _wrapper_native_modules(modules: list[SemanticModule]) -> list[str]:
    return list(
        dict.fromkeys(
            str(module.origin.native_name or module.name)
            for module in modules
            if module.origin.source_kind == "module" and _module_requires_native_scope(module)
        )
    )


def _module_requires_native_scope(module: SemanticModule) -> bool:
    if module.variables or module.classes:
        return True
    functions = [*module.functions, *(procedure for item in module.overload_sets for procedure in item.procedures)]
    return any(function.origin.native_scope is not None for function in functions)


def _command_output(command: tuple[str, ...]) -> str | None:
    try:
        return command[command.index("-o") + 1]
    except (ValueError, IndexError):
        return None


def _command_source(command: tuple[str, ...]) -> str | None:
    for part in command:
        if Path(part).suffix.lower() in _FORTRAN_SOURCE_SUFFIXES | _C_SOURCE_SUFFIXES:
            return part
    return None


def _command_language(command: tuple[str, ...]) -> str | None:
    source = _command_source(command)
    if source is None:
        return None
    return "fortran" if Path(source).suffix.lower() in _FORTRAN_SOURCE_SUFFIXES else "c"


def _absolute_command_path(path: str | Path, working_directory: Path) -> Path:
    result = Path(path)
    return result if result.is_absolute() else working_directory / result


def _make_target(path: Path) -> str:
    return str(path).replace("$", "$$").replace("#", r"\#").replace(" ", r"\ ")


def _make_shell_literal(text: str) -> str:
    return text.replace("$", "$$")


def _make_recipe(command: tuple[str, ...], working_directory: Path) -> str:
    language = _command_language(command)
    if "-shared" in command:
        compiler_var, flags_var = "X2PY_LD", "X2PY_LDFLAGS"
    elif language == "fortran":
        compiler_var, flags_var = "FC", "X2PY_FFLAGS"
    else:
        compiler_var, flags_var = "CC", "X2PY_CFLAGS"

    output_index = command.index("-o")
    before_output = _make_shell_literal(shlex.join(command[1:output_index]))
    output_and_after = _make_shell_literal(shlex.join(command[output_index:]))
    directory = _make_shell_literal(shlex.quote(str(working_directory)))
    return f"\tcd {directory} && $({compiler_var}) {before_output} $({flags_var}) {output_and_after}".rstrip()


def _compiler_executable(commands: tuple[tuple[str, ...], ...], *, language: str | None, shared: bool) -> str:
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
    lines = [
        "# Generated by x2py. Edit variables or override them on the make command line.",
        "# User Fortran sources are conservatively chained in supplied order.",
        "# Generated bridge and C binding objects may be built in parallel with make -j.",
        f"FC := {_make_shell_literal(shlex.quote(_compiler_executable(commands, language='fortran', shared=False)))}",
        f"CC := {_make_shell_literal(shlex.quote(_compiler_executable(commands, language='c', shared=False)))}",
        f"X2PY_LD := {_make_shell_literal(shlex.quote(_compiler_executable(commands, language=None, shared=True)))}",
        "X2PY_FFLAGS ?=",
        "X2PY_CFLAGS ?=",
        "X2PY_LDFLAGS ?=",
        "",
    ]

    link_output = _absolute_command_path(_command_output(link_command), working_directory)
    lines.extend([".PHONY: all rebuild clean", f"all: {_make_target(link_output)}", ""])

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


def _can_probe_fortran_types(preprocessing: PreprocessingConfig) -> bool:
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


def build_fortran_extension(
    sources: str | Path | Iterable[str | Path],
    *,
    output_dir: str | Path | None = None,
    output_name: str | None = None,
    preprocessing: PreprocessingConfig | None = None,
    strict_wrapper_names: bool = False,
    fortran_type_report=None,
    fortran_type_probe_runner: list[str] | None = None,
    fortran_type_probe_cache_dir: str | Path | None = None,
    refresh_fortran_type_probe: bool = False,
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
    """Build one extension, or generate its sources or Makefile, from ordered sources."""

    if makefile and generate_sources:
        raise ValueError("source-only and Makefile generation are mutually exclusive")
    generation_only = makefile or generate_sources
    compile_jobs = _normalize_compile_jobs(jobs)
    if generation_only and verbose:
        raise ValueError("source/Makefile generation and verbose direct compilation are separate modes")

    build_started = time.perf_counter()
    source_paths = _source_paths(sources)
    primary_source = source_paths[0]

    output_path, shared_library_output_path = _wrapper_output_paths(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    preprocessing = preprocessing or _default_preprocessing_config()
    supplemental_source_paths = tuple(Path(path) for path in (native_fortran_sources or ()))
    native_inputs = _native_build_inputs(
        native_fortran_sources=(*source_paths, *supplemental_source_paths),
        native_fortran_flags=native_fortran_flags,
        native_objects=native_objects,
        native_libraries=native_libraries,
        native_link_items=native_link_items,
        complete_native_link_items=None,
        native_library_dirs=native_library_dirs,
        native_include_dirs=native_include_dirs,
    )
    type_probe_preprocessing = _type_probe_preprocessing(preprocessing, native_inputs.source_flags)

    preprocessed_sources = {
        str(source_path): _fortran_source_for_pipeline(source_path, preprocessing) for source_path in source_paths
    }
    parsed = parse_fortran_project(preprocessed_sources)
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
    modules = fortran_project_to_semantic_modules(
        parsed,
        compile_time_values=compile_time_values,
        type_facts=type_facts,
    )
    _apply_source_python_exports(modules)
    requested_name = output_name or primary_source.stem
    if not requested_name.isidentifier():
        raise ValueError(f"Output name must be a valid Python identifier: {requested_name!r}")
    module = _merge_wrapper_modules(modules, name=requested_name)
    rendered_wrapper_plan = _generated_wrapper_plan_artifacts(
        module,
        strict_wrapper_names=strict_wrapper_names,
        verbose=verbose,
    )

    wrapper_fortran_flags = _compiler_flags(wrapper_fortran_flags)
    wrapper_c_flags = _compiler_flags(wrapper_c_flags)
    compiler = _new_compiler(
        execute_commands=not generation_only,
        debug=wrapper_compiler_debug,
        input_compiler=preprocessing.compiler if preprocessing.uses_compiler else None,
    )
    include_dirs = _native_include_dirs(native_inputs, output_path=output_path)
    native_source_objects = _native_source_objects(
        native_inputs,
        output_path=output_path,
        include_dirs=include_dirs,
    )
    native_build_plan = _native_build_plan(
        source_paths=native_inputs.source_paths,
        source_objects=native_source_objects,
        artifact_paths=native_inputs.artifact_paths,
        libraries=native_inputs.libraries,
        explicit_link_items=native_inputs.explicit_link_items,
        complete_link_items=None,
        library_dirs=native_inputs.library_dirs,
        explicit_include_dirs=native_inputs.explicit_include_dirs,
        include_dirs=include_dirs,
        module_dir=output_path,
    )
    _validate_native_link_paths(native_build_plan)
    native_compile_batches = _project_compile_batches(parsed, native_source_objects)

    result = _build_rendered_wrapper_extension(
        rendered_wrapper_plan,
        output_dir=output_path,
        shared_library_output_dir=shared_library_output_path,
        sources=source_paths,
        native_build_plan=native_build_plan,
        native_dependencies=native_source_objects,
        native_compile_batches=native_compile_batches,
        native_link_args=_rendered_wrapper_native_link_args(native_build_plan),
        wrapper_fortran_flags=wrapper_fortran_flags,
        wrapper_c_flags=wrapper_c_flags,
        compiler=compiler,
        compile_jobs=1 if generation_only else compile_jobs,
        verbose=verbose,
    )
    if makefile:
        result = _attach_build_makefile(
            result,
            compiler=compiler,
            source_objects=native_source_objects,
            extra_dependencies=_link_item_paths(native_build_plan.link_items),
        )
    elif generate_sources:
        result = replace(result, compiled=False)
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
    """Build one extension, or generate its sources or Makefile, from one `.pyi` entry."""

    if makefile and generate_sources:
        raise ValueError("source-only and Makefile generation are mutually exclusive")
    generation_only = makefile or generate_sources
    compile_jobs = _normalize_compile_jobs(jobs)
    if generation_only and verbose:
        raise ValueError("source/Makefile generation and verbose direct compilation are separate modes")

    build_started = time.perf_counter()
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

    modules = list(bundle.modules)
    requested_name = output_name or _bundle_output_name(bundle)
    if not requested_name.isidentifier():
        raise ValueError(f"Output name must be a valid Python identifier: {requested_name!r}")
    module = _merge_wrapper_modules(modules, name=requested_name)
    rendered_wrapper_plan = _generated_wrapper_plan_artifacts(
        module,
        strict_wrapper_names=strict_wrapper_names,
        verbose=verbose,
    )

    include_dirs = _native_include_dirs(native_inputs, output_path=output_path)
    native_source_objects = _native_source_objects(
        native_inputs,
        output_path=output_path,
        include_dirs=include_dirs,
    )
    native_build_plan = _native_build_plan(
        source_paths=native_inputs.source_paths,
        source_objects=native_source_objects,
        artifact_paths=native_inputs.artifact_paths,
        libraries=native_inputs.libraries,
        explicit_link_items=native_inputs.explicit_link_items,
        complete_link_items=native_inputs.complete_link_items,
        library_dirs=native_inputs.library_dirs,
        explicit_include_dirs=native_inputs.explicit_include_dirs,
        include_dirs=include_dirs,
        module_dir=output_path if native_source_objects else None,
    )
    _validate_native_link_paths(native_build_plan)
    compiler = _new_compiler(
        execute_commands=not generation_only,
        debug=wrapper_compiler_debug,
        input_compiler=input_compiler,
    )
    native_array_build_requirements = native_array_handle_build_requirements(module)
    result = _build_rendered_wrapper_extension(
        rendered_wrapper_plan,
        output_dir=output_path,
        shared_library_output_dir=shared_library_output_path,
        sources=bundle.paths,
        native_build_plan=native_build_plan,
        native_dependencies=native_source_objects,
        native_compile_batches=_serial_compile_batches(native_source_objects),
        native_link_args=_rendered_wrapper_native_link_args(native_build_plan),
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
    if makefile:
        build_manifest = _write_build_manifest(output_path / _BUILD_MANIFEST_NAME, result.manifest)
        dependencies = (
            *bundle.paths,
            *_link_item_paths(native_build_plan.link_items),
            build_manifest,
        )
        result = _attach_build_makefile(
            result,
            compiler=compiler,
            source_objects=native_source_objects,
            extra_dependencies=dependencies,
            build_manifest=build_manifest,
        )
    elif generate_sources:
        result = replace(result, compiled=False)
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
    """Replay a saved semantic `.pyi` wrapper build manifest."""

    build_started = time.perf_counter()
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


def _bundle_output_name(bundle: _PyiContractBundle) -> str:
    if bundle.entry.name == "__init__.pyi":
        return bundle.entry.resolve().parent.name
    return bundle.entry.stem
