"""Build one reusable native BLAS or LAPACK library from the copied examples."""

from __future__ import annotations

import argparse
import concurrent.futures
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
from collections.abc import Sequence


EXAMPLES_ROOT = Path(__file__).resolve().parent
FORTRAN_EXAMPLES_ROOT = EXAMPLES_ROOT / "fortran"
BLAS_SOURCE_ROOT = FORTRAN_EXAMPLES_ROOT / "blas" / "native"
LAPACK_SOURCE_ROOT = FORTRAN_EXAMPLES_ROOT / "lapack" / "native"
LAPACK_SUPPORT_ROOT = FORTRAN_EXAMPLES_ROOT / "lapack" / "support"
LAPACK_XBLAS_SOURCE_LIST = FORTRAN_EXAMPLES_ROOT / "lapack" / "xblas_sources.txt"
NATIVE_CACHE_ENV = "PRIK_REAL_LIBRARY_NATIVE_CACHE_DIR"
NATIVE_JOBS_ENV = "PRIK_REAL_LIBRARY_NATIVE_JOBS"
NATIVE_CACHE_VERSION = "copyable-examples-v4-default-lapack-sources"
NATIVE_MODULE_SOURCE_STEMS = frozenset({"la_constants", "la_xisnan"})
NATIVE_LINK_DEPENDENCIES = {
    "blas": (),
    "lapack": ("-llapack", "-lblas"),
}
DEFAULT_NATIVE_COMPILE_JOB_LIMIT = 8
FORTRAN_SUFFIXES = frozenset({".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"})
SUPPORTED_LIBRARIES = ("blas", "lapack")


@dataclass(frozen=True)
class NativeLibrary:
    """A complete native library compiled once for both wrapper generators."""

    name: str
    shared_library: Path
    archive: Path
    cache_dir: Path
    module_dir: Path
    wrapper_source_root: Path
    sources: tuple[Path, ...]
    compiler: str


def require_tool(name: str) -> str:
    """Return an executable path or explain the missing example prerequisite."""
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} is required to build the native-library examples")
    return executable


def compiler_identity(compiler: str) -> str:
    """Return the resolved compiler path and its first version line."""
    result = subprocess.run(  # nosec B603 - explicit local compiler identity probe
        (compiler, "--version"),
        capture_output=True,
        text=True,
        check=False,
    )
    first_line = result.stdout.splitlines()[0] if result.stdout else compiler
    return f"{Path(compiler).resolve()}: {first_line}"


def _fortran_sources(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.iterdir() if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES))


def library_sources(library: str) -> tuple[Path, ...]:
    """Return the authoritative implementation snapshot for one named library."""
    if library not in SUPPORTED_LIBRARIES:
        raise ValueError(f"unknown reference library {library!r}; choose from {', '.join(SUPPORTED_LIBRARIES)}")
    root = BLAS_SOURCE_ROOT if library == "blas" else LAPACK_SOURCE_ROOT
    return _fortran_sources(root)


def _lapack_xblas_source_names() -> frozenset[str]:
    names = tuple(
        line
        for raw_line in LAPACK_XBLAS_SOURCE_LIST.read_text(encoding="utf-8").splitlines()
        if (line := raw_line.strip()) and not line.startswith("#")
    )
    if len(names) != len(set(names)):
        raise RuntimeError(f"duplicate source names in {LAPACK_XBLAS_SOURCE_LIST}")
    available = {source.name for source in library_sources("lapack")}
    unknown = sorted(set(names) - available)
    if unknown:
        raise RuntimeError(f"unknown XBLAS-only LAPACK sources: {', '.join(unknown)}")
    return frozenset(names)


def wrapper_sources(library: str) -> tuple[Path, ...]:
    """Return the source surface compiled and exposed by one example wrapper."""
    sources = library_sources(library)
    if library == "blas":
        return sources
    excluded = _lapack_xblas_source_names()
    return tuple(source for source in sources if source.name not in excluded)


def native_sources(library: str) -> tuple[Path, ...]:
    """Return sources in a safe compilation order, including LAPACK's BLAS dependencies."""
    if library not in SUPPORTED_LIBRARIES:
        return library_sources(library)
    if library == "blas":
        return wrapper_sources("blas")
    lapack_sources = wrapper_sources("lapack")
    module_sources = tuple(
        source
        for source in (
            LAPACK_SOURCE_ROOT / "la_constants.f90",
            LAPACK_SOURCE_ROOT / "la_xisnan.F90",
        )
        if source.is_file()
    )
    module_source_set = set(module_sources)
    lapack_rest = tuple(source for source in lapack_sources if source not in module_source_set)
    lapack_stems = {source.stem.lower() for source in lapack_sources}
    blas_dependencies = tuple(source for source in library_sources("blas") if source.stem.lower() not in lapack_stems)
    return (*module_sources, *lapack_rest, *_fortran_sources(LAPACK_SUPPORT_ROOT), *blas_dependencies)


def native_cache_root() -> Path:
    """Return the configured cache, or a build directory inside the copied examples."""
    configured = os.environ.get(NATIVE_CACHE_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return EXAMPLES_ROOT / ".build" / "native"


def native_compile_jobs() -> int:
    """Return the validated native compilation parallelism."""
    configured = os.environ.get(NATIVE_JOBS_ENV)
    if configured:
        try:
            jobs = int(configured)
        except ValueError as error:
            raise ValueError(f"{NATIVE_JOBS_ENV} must be a positive integer, got {configured!r}") from error
        if jobs < 1:
            raise ValueError(f"{NATIVE_JOBS_ENV} must be a positive integer, got {configured!r}")
        return jobs
    return max(1, min(os.cpu_count() or 1, DEFAULT_NATIVE_COMPILE_JOB_LIMIT))


def _native_platform_identity() -> str:
    return f"{sysconfig.get_platform()}:{os.name}:{sys.maxsize}"


def _source_digest(source: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _native_cache_key(library: str, compiler: str, sources: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for value in (NATIVE_CACHE_VERSION, library, compiler_identity(compiler), _native_platform_identity()):
        digest.update(value.encode())
        digest.update(b"\0")
    for source in sources:
        digest.update(source.relative_to(EXAMPLES_ROOT).as_posix().encode())
        digest.update(b":")
        digest.update(_source_digest(source).encode())
        digest.update(b"\0")
    return digest.hexdigest()[:24]


def _cached_object_path(objects_dir: Path, source: Path) -> Path:
    return objects_dir / source.relative_to(EXAMPLES_ROOT).with_suffix(".o")


def _compile_source(compiler: str, source: Path, native_object: Path, module_dir: Path) -> None:
    native_object.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(  # nosec B603 - explicit compiler and copied example source
        (
            compiler,
            "-O0",
            "-fPIC",
            "-c",
            str(source),
            "-o",
            str(native_object),
            "-J",
            str(module_dir),
            "-I",
            str(module_dir),
        ),
        check=True,
    )


def _compile_independent_sources(
    compiler: str,
    sources: tuple[Path, ...],
    objects_dir: Path,
    module_dir: Path,
    jobs: int,
) -> None:
    if not sources:
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(jobs, len(sources))) as executor:
        futures = [
            executor.submit(
                _compile_source,
                compiler,
                source,
                _cached_object_path(objects_dir, source),
                module_dir,
            )
            for source in sources
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()


def _cached_objects(
    cache_dir: Path,
    sources: tuple[Path, ...],
    compiler: str,
    jobs: int,
) -> tuple[Path, ...]:
    objects_dir = cache_dir / "objects"
    modules_dir = cache_dir / "modules"
    complete = cache_dir / "objects.complete"
    objects = tuple(_cached_object_path(objects_dir, source) for source in sources)
    module_sources = tuple(source for source in sources if source.stem.lower() in NATIVE_MODULE_SOURCE_STEMS)
    modules = tuple(modules_dir / f"{source.stem.lower()}.mod" for source in module_sources)
    if (
        complete.is_file()
        and modules_dir.is_dir()
        and all(native_object.is_file() for native_object in objects)
        and all(module.is_file() for module in modules)
    ):
        return objects

    process_suffix = str(os.getpid())
    temporary_objects = cache_dir / f"objects.{process_suffix}.tmp"
    temporary_modules = cache_dir / f"modules.{process_suffix}.tmp"
    shutil.rmtree(temporary_objects, ignore_errors=True)
    shutil.rmtree(temporary_modules, ignore_errors=True)
    temporary_objects.mkdir(parents=True)
    temporary_modules.mkdir(parents=True)
    module_source_set = set(module_sources)
    independent_sources = tuple(source for source in sources if source not in module_source_set)
    for source in module_sources:
        _compile_source(compiler, source, _cached_object_path(temporary_objects, source), temporary_modules)
    _compile_independent_sources(compiler, independent_sources, temporary_objects, temporary_modules, jobs)
    shutil.rmtree(objects_dir, ignore_errors=True)
    temporary_objects.rename(objects_dir)
    shutil.rmtree(modules_dir, ignore_errors=True)
    temporary_modules.rename(modules_dir)
    complete.write_text(f"{NATIVE_CACHE_VERSION}\n", encoding="utf-8")
    (cache_dir / "archive.complete").unlink(missing_ok=True)
    (cache_dir / "shared.complete").unlink(missing_ok=True)
    return tuple(_cached_object_path(objects_dir, source) for source in sources)


def _cached_archive(cache_dir: Path, library: str, objects: tuple[Path, ...], archiver: str) -> Path:
    archive = cache_dir / f"libprik_full_{library}.a"
    complete = cache_dir / "archive.complete"
    if complete.is_file() and archive.is_file():
        return archive
    temporary_archive = cache_dir / f"{archive.name}.{os.getpid()}.tmp"
    temporary_archive.unlink(missing_ok=True)
    subprocess.run(  # nosec B603 - explicit archiver and compiled example objects
        (archiver, "rcs", str(temporary_archive), *(str(native_object) for native_object in objects)),
        check=True,
    )
    os.replace(temporary_archive, archive)
    complete.write_text(f"{NATIVE_CACHE_VERSION}\n", encoding="utf-8")
    return archive


def _cached_wrapper_source_root(cache_dir: Path, sources: tuple[Path, ...]) -> Path:
    source_root = cache_dir / "wrapper_sources"
    complete = cache_dir / "wrapper_sources.complete"
    expected_names = {source.name for source in sources}
    if len(expected_names) != len(sources):
        raise RuntimeError("wrapper source filenames must be unique")
    if (
        complete.is_file()
        and source_root.is_dir()
        and {path.name for path in source_root.iterdir() if path.is_file()} == expected_names
    ):
        return source_root

    temporary_root = cache_dir / f"wrapper_sources.{os.getpid()}.tmp"
    shutil.rmtree(temporary_root, ignore_errors=True)
    temporary_root.mkdir()
    for source in sources:
        (temporary_root / source.name).symlink_to(source.resolve())
    shutil.rmtree(source_root, ignore_errors=True)
    temporary_root.rename(source_root)
    complete.write_text(f"{NATIVE_CACHE_VERSION}\n", encoding="utf-8")
    return source_root


def _cached_shared_library(cache_dir: Path, library: str, archive: Path, compiler: str) -> Path:
    suffix = ".dylib" if sys.platform == "darwin" else ".so"
    shared_library = cache_dir / f"libprik_full_{library}{suffix}"
    complete = cache_dir / "shared.complete"
    if complete.is_file() and shared_library.is_file():
        return shared_library
    temporary_shared = cache_dir / f"{shared_library.name}.{os.getpid()}.tmp"
    temporary_shared.unlink(missing_ok=True)
    if sys.platform == "darwin":
        command = (
            compiler,
            "-dynamiclib",
            "-o",
            str(temporary_shared),
            f"-Wl,-install_name,{shared_library}",
            "-Wl,-force_load",
            str(archive),
            *NATIVE_LINK_DEPENDENCIES[library],
        )
    else:
        command = (
            compiler,
            "-shared",
            "-o",
            str(temporary_shared),
            "-Wl,--whole-archive",
            str(archive),
            "-Wl,--no-whole-archive",
            *NATIVE_LINK_DEPENDENCIES[library],
        )
    subprocess.run(  # nosec B603 - explicit compiler and compiled example archive
        command,
        check=True,
    )
    os.replace(temporary_shared, shared_library)
    complete.write_text(f"{NATIVE_CACHE_VERSION}\n", encoding="utf-8")
    return shared_library


def build_reference_library(
    library: str,
    *,
    cache_root: Path | None = None,
    compiler: str | None = None,
    archiver: str | None = None,
    jobs: int | None = None,
) -> NativeLibrary:
    """Build on a cache miss and return one complete reusable native library."""
    selected_compiler = compiler or require_tool("gfortran")
    selected_archiver = archiver or require_tool("ar")
    selected_wrapper_sources = wrapper_sources(library)
    selected_sources = native_sources(library)
    selected_jobs = jobs if jobs is not None else native_compile_jobs()
    if selected_jobs < 1:
        raise ValueError(f"jobs must be a positive integer, got {selected_jobs!r}")
    selected_cache_root = (cache_root or native_cache_root()).resolve()
    cache_dir = selected_cache_root / f"{library}-{_native_cache_key(library, selected_compiler, selected_sources)}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    wrapper_source_root = _cached_wrapper_source_root(cache_dir, selected_wrapper_sources)
    objects = _cached_objects(cache_dir, selected_sources, selected_compiler, selected_jobs)
    archive = _cached_archive(cache_dir, library, objects, selected_archiver)
    shared_library = _cached_shared_library(cache_dir, library, archive, selected_compiler)
    return NativeLibrary(
        name=library,
        shared_library=shared_library,
        archive=archive,
        cache_dir=cache_dir,
        module_dir=cache_dir / "modules",
        wrapper_source_root=wrapper_source_root,
        sources=selected_sources,
        compiler=selected_compiler,
    )


def linker_name(shared_library: Path) -> str:
    """Return the `-l` name for a shared library produced by this module."""
    name = shared_library.name
    suffix = next((candidate for candidate in (".so", ".dylib") if name.endswith(candidate)), None)
    if not name.startswith("lib") or suffix is None:
        raise ValueError(f"expected a lib*.so or lib*.dylib native library, got {shared_library}")
    return name[3 : -len(suffix)]


def main(argv: Sequence[str] | None = None) -> int:
    """Build a copied example's native library and print its reusable path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library", choices=SUPPORTED_LIBRARIES)
    parser.add_argument("--cache-dir", type=Path, default=None)
    parser.add_argument("--compiler", default=None)
    parser.add_argument("--jobs", type=int, default=None)
    args = parser.parse_args(argv)
    build = build_reference_library(
        args.library,
        cache_root=args.cache_dir,
        compiler=args.compiler,
        jobs=args.jobs,
    )
    print(build.shared_library)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
