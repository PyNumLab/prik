"""Real BLAS/LAPACK full-contract wrapper import and runtime tests."""

from __future__ import annotations

import concurrent.futures
import hashlib
import importlib
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import REPO_ROOT
from x2py import build_pyi_extension
from x2py.pipeline.pyi import pyi_paths_to_semantic_modules

FORTRAN_LIBRARY_ROOT = Path(__file__).parent
NATIVE_CACHE_ENV = "X2PY_REAL_LIBRARY_NATIVE_CACHE_DIR"
NATIVE_JOBS_ENV = "X2PY_REAL_LIBRARY_NATIVE_JOBS"
DEFAULT_NATIVE_CACHE_ROOT = REPO_ROOT / ".pytest_cache" / "x2py" / "real-library-native"
NATIVE_CACHE_VERSION = "full-library-v3"
NATIVE_MODULE_SOURCE_STEMS = {"la_constants", "la_xisnan"}
DEFAULT_NATIVE_COMPILE_JOB_LIMIT = 8
pytestmark = pytest.mark.fortran_end_to_end
FULL_LIBRARY_WRAPPER_FLAGS = ("-O0", "-g0")
FORTRAN_SUFFIXES = {".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"}
FULL_LIBRARY_CASES = {
    "blas": {
        "root_function_count": 155,
        "source_stem_exceptions": set(),
        "extra_function_names": set(),
        "sentinel_functions": {"dasum", "daxpy", "ddot", "dgemm", "dscal", "lsame", "xerbla"},
    },
    "lapack": {
        "root_function_count": 2063,
        "source_stem_exceptions": {"la_constants", "la_xisnan"},
        "extra_function_names": {"dladiv1", "dladiv2", "sladiv1", "sladiv2"},
        "sentinel_functions": {"dgesv", "dgetrf", "dgetrs", "dlamrg", "zgesv"},
    },
}
LAPACK_RUNTIME_EXCLUDED_IMPORTS = {"from . import LA_CONSTANTS\n", "from . import LA_XISNAN\n"}


def _compiler() -> str:
    compiler = shutil.which("gfortran")
    if compiler is None:
        pytest.skip("gfortran is required for real BLAS/LAPACK wrapper tests")
    return compiler


def _archiver() -> str:
    archiver = shutil.which("ar")
    if archiver is None:
        pytest.skip("ar is required for real BLAS/LAPACK native cache tests")
    return archiver


def _library_sources(library: str) -> tuple[Path, ...]:
    root = FORTRAN_LIBRARY_ROOT / library / "native"
    return tuple(sorted(path for path in root.iterdir() if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES))


def _native_sources(library: str) -> tuple[Path, ...]:
    if library == "blas":
        return _library_sources("blas")
    lapack_sources = _library_sources("lapack")
    module_sources = tuple(
        source
        for source in (
            FORTRAN_LIBRARY_ROOT / "lapack" / "native" / "la_constants.f90",
            FORTRAN_LIBRARY_ROOT / "lapack" / "native" / "la_xisnan.F90",
        )
        if source.is_file()
    )
    module_source_set = set(module_sources)
    lapack_rest = tuple(source for source in lapack_sources if source not in module_source_set)
    lapack_stems = {source.stem.lower() for source in lapack_sources}
    blas_dependencies = tuple(source for source in _library_sources("blas") if source.stem.lower() not in lapack_stems)
    return (*module_sources, *lapack_rest, *blas_dependencies)


def _source_stems(library: str) -> set[str]:
    return {path.stem.lower() for path in _library_sources(library)}


def _compiler_identity(compiler: str) -> str:
    result = subprocess.run([compiler, "--version"], capture_output=True, text=True, check=False)
    first_line = result.stdout.splitlines()[0] if result.stdout else compiler
    return f"{Path(compiler).resolve()}:{first_line}"


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
    digest.update(NATIVE_CACHE_VERSION.encode())
    digest.update(b"\0")
    digest.update(library.encode())
    digest.update(b"\0")
    digest.update(_compiler_identity(compiler).encode())
    digest.update(b"\0")
    digest.update(_native_platform_identity().encode())
    for source in sources:
        digest.update(b"\0")
        digest.update(source.relative_to(REPO_ROOT).as_posix().encode())
        digest.update(b":")
        digest.update(_source_digest(source).encode())
    return digest.hexdigest()[:24]


def _native_cache_root() -> Path:
    configured = os.environ.get(NATIVE_CACHE_ENV)
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_NATIVE_CACHE_ROOT


def _native_compile_jobs() -> int:
    configured = os.environ.get(NATIVE_JOBS_ENV)
    if configured:
        try:
            jobs = int(configured)
        except ValueError:
            pytest.fail(f"{NATIVE_JOBS_ENV} must be a positive integer, got {configured!r}")
        if jobs < 1:
            pytest.fail(f"{NATIVE_JOBS_ENV} must be a positive integer, got {configured!r}")
        return jobs
    return max(1, min(os.cpu_count() or 1, DEFAULT_NATIVE_COMPILE_JOB_LIMIT))


def _generate_contract(source_root: Path, package: Path) -> Path:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "x2py",
            "generate",
            "--pyi",
            str(source_root),
            "--language",
            "fortran",
            "--out",
            str(package),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return package / "__init__.pyi"


def _contract_modules(package: Path):
    return pyi_paths_to_semantic_modules([package])


def _root_module(package: Path):
    return next(module for module in _contract_modules(package) if module.name == "__init__")


def _function_names(package: Path) -> set[str]:
    return {function.name for module in _contract_modules(package) for function in module.functions}


def _cached_object_path(objects_dir: Path, source: Path) -> Path:
    return objects_dir / source.relative_to(FORTRAN_LIBRARY_ROOT).with_suffix(".o")


def _compile_native_source(compiler: str, source: Path, native_object: Path, module_dir: Path) -> None:
    native_object.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            compiler,
            "-fPIC",
            "-c",
            str(source),
            "-o",
            str(native_object),
            "-J",
            str(module_dir),
            "-I",
            str(module_dir),
        ],
        check=True,
    )


def _compile_independent_native_sources(
    compiler: str,
    sources: tuple[Path, ...],
    objects_dir: Path,
    module_dir: Path,
) -> None:
    if not sources:
        return
    jobs = min(_native_compile_jobs(), len(sources))
    if jobs == 1:
        for source in sources:
            _compile_native_source(compiler, source, _cached_object_path(objects_dir, source), module_dir)
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = [
            executor.submit(
                _compile_native_source,
                compiler,
                source,
                _cached_object_path(objects_dir, source),
                module_dir,
            )
            for source in sources
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()


def _split_ordered_module_sources(sources: tuple[Path, ...]) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    module_sources = tuple(source for source in sources if source.stem.lower() in NATIVE_MODULE_SOURCE_STEMS)
    module_source_set = set(module_sources)
    independent_sources = tuple(source for source in sources if source not in module_source_set)
    return module_sources, independent_sources


def _cached_objects(cache_dir: Path, sources: tuple[Path, ...], compiler: str) -> tuple[Path, ...]:
    objects_dir = cache_dir / "objects"
    complete = cache_dir / "objects.complete"
    objects = tuple(_cached_object_path(objects_dir, source) for source in sources)
    if complete.is_file() and all(obj.is_file() for obj in objects):
        return objects

    temp_objects_dir = cache_dir / f"objects.{os.getpid()}.tmp"
    temp_module_dir = cache_dir / f"modules.{os.getpid()}.tmp"
    shutil.rmtree(temp_objects_dir, ignore_errors=True)
    shutil.rmtree(temp_module_dir, ignore_errors=True)
    temp_objects_dir.mkdir(parents=True)
    temp_module_dir.mkdir(parents=True)
    module_sources, independent_sources = _split_ordered_module_sources(sources)
    for source in module_sources:
        _compile_native_source(compiler, source, _cached_object_path(temp_objects_dir, source), temp_module_dir)
    _compile_independent_native_sources(compiler, independent_sources, temp_objects_dir, temp_module_dir)
    shutil.rmtree(objects_dir, ignore_errors=True)
    temp_objects_dir.rename(objects_dir)
    shutil.rmtree(temp_module_dir, ignore_errors=True)
    complete.write_text(f"{NATIVE_CACHE_VERSION}\n", encoding="utf-8")
    (cache_dir / "archive.complete").unlink(missing_ok=True)
    (cache_dir / "shared.complete").unlink(missing_ok=True)
    return tuple(_cached_object_path(objects_dir, source) for source in sources)


def _cached_archive(cache_dir: Path, library: str, objects: tuple[Path, ...]) -> Path:
    archive = cache_dir / f"libx2py_full_{library}.a"
    complete = cache_dir / "archive.complete"
    if complete.is_file() and archive.is_file():
        return archive

    temp_archive = cache_dir / f"{archive.name}.{os.getpid()}.tmp"
    temp_archive.unlink(missing_ok=True)
    subprocess.run([_archiver(), "rcs", str(temp_archive), *(str(obj) for obj in objects)], check=True)
    os.replace(temp_archive, archive)
    complete.write_text(f"{NATIVE_CACHE_VERSION}\n", encoding="utf-8")
    return archive


def _cached_shared_library(cache_dir: Path, library: str, archive: Path, compiler: str) -> Path:
    shared = cache_dir / f"libx2py_full_{library}.so"
    complete = cache_dir / "shared.complete"
    if complete.is_file() and shared.is_file():
        return shared

    temp_shared = cache_dir / f"{shared.name}.{os.getpid()}.tmp"
    temp_shared.unlink(missing_ok=True)
    subprocess.run(
        [
            compiler,
            "-shared",
            "-o",
            str(temp_shared),
            "-Wl,--whole-archive",
            str(archive),
            "-Wl,--no-whole-archive",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    os.replace(temp_shared, shared)
    complete.write_text(f"{NATIVE_CACHE_VERSION}\n", encoding="utf-8")
    return shared


def _cached_native_shared_library(library: str) -> Path:
    compiler = _compiler()
    sources = _native_sources(library)
    cache_dir = _native_cache_root() / f"{library}-{_native_cache_key(library, compiler, sources)}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    shared = cache_dir / f"libx2py_full_{library}.so"
    if (cache_dir / "shared.complete").is_file() and shared.is_file():
        return shared
    objects = _cached_objects(cache_dir, sources, compiler)
    archive = _cached_archive(cache_dir, library, objects)
    return _cached_shared_library(cache_dir, library, archive, compiler)


def _runtime_entry(library: str, entry: Path, workdir: Path) -> Path:
    if library != "lapack":
        return entry
    # The full LAPACK package also contains helper modules with constants and
    # generic interfaces. Runtime evidence here covers the root procedure set.
    runtime_package = workdir / "runtime_contract" / library
    shutil.copytree(entry.parent, runtime_package)
    runtime_entry = runtime_package / "__init__.pyi"
    lines = runtime_entry.read_text(encoding="utf-8").splitlines(keepends=True)
    runtime_entry.write_text(
        "".join(line for line in lines if line not in LAPACK_RUNTIME_EXCLUDED_IMPORTS),
        encoding="utf-8",
    )
    return runtime_entry


def _import_extension(module_name: str, build_dir: Path, *, lazy: bool = False):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(build_dir))
    old_flags = sys.getdlopenflags()
    if lazy:
        sys.setdlopenflags(getattr(os, "RTLD_LAZY", old_flags) | getattr(os, "RTLD_GLOBAL", 0))
    try:
        return importlib.import_module(module_name)
    finally:
        if lazy:
            sys.setdlopenflags(old_flags)
        sys.path.remove(str(build_dir))


def _assert_blas_runtime_smoke(module) -> None:
    x = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    y = np.array([10.0, 20.0, 30.0], dtype=np.float64)
    daxpy_scalars = module.daxpy(np.int32(3), np.float64(2.0), x, np.int32(1), y, np.int32(1))
    assert daxpy_scalars == (np.int32(3), np.float64(2.0), np.int32(1), np.int32(1))
    np.testing.assert_allclose(y, [12.0, 24.0, 36.0])
    assert module.ddot(np.int32(3), x, np.int32(1), y, np.int32(1)) == (
        np.float64(168.0),
        np.int32(3),
        np.int32(1),
        np.int32(1),
    )
    assert module.dasum(np.int32(3), y, np.int32(1)) == (
        np.float64(72.0),
        np.int32(3),
        np.int32(1),
    )
    dscal_scalars = module.dscal(np.int32(3), np.float64(0.5), y, np.int32(1))
    assert dscal_scalars == (np.int32(3), np.float64(0.5), np.int32(1))
    np.testing.assert_allclose(y, [6.0, 12.0, 18.0])


def _assert_lapack_runtime_smoke(module) -> None:
    index = np.zeros(5, dtype=np.int32)
    values = np.array([1.0, 4.0, 7.0, 2.0, 8.0], dtype=np.float64)
    scalars = module.dlamrg(np.int32(3), np.int32(2), values, np.int32(1), np.int32(1), index)
    assert scalars == (np.int32(3), np.int32(2), np.int32(1), np.int32(1))
    np.testing.assert_array_equal(index, [1, 4, 2, 3, 5])


@pytest.mark.real_library
@pytest.mark.parametrize("library", ["blas", "lapack"])
def test_full_library_wrapper_imports_every_root_procedure_from_cached_shared_library(library: str, tmp_path: Path):
    entry = _generate_contract(FORTRAN_LIBRARY_ROOT / library / "native", tmp_path / "contracts" / library)

    root = _root_module(entry.parent)
    all_function_names = _function_names(entry.parent)
    case = FULL_LIBRARY_CASES[library]

    assert len(root.functions) == case["root_function_count"]
    assert case["sentinel_functions"] <= all_function_names
    assert _source_stems(library) - all_function_names == case["source_stem_exceptions"]
    assert all_function_names - _source_stems(library) == case["extra_function_names"]

    shared = _cached_native_shared_library(library)
    runtime_entry = _runtime_entry(library, entry, tmp_path)
    expected_root_names = {function.name for function in _root_module(runtime_entry.parent).functions}
    result = build_pyi_extension(
        runtime_entry,
        output_name=f"full_{library}",
        output_dir=tmp_path / "build" / library,
        native_objects=[shared],
        wrapper_fortran_flags=FULL_LIBRARY_WRAPPER_FLAGS,
        wrapper_c_flags=FULL_LIBRARY_WRAPPER_FLAGS,
    )
    module = _import_extension(result.module_name, result.output_dir, lazy=library == "lapack")

    missing = sorted(name for name in expected_root_names if not hasattr(module, name))
    assert missing == []
    native_plan = result.native_build_plan.to_dict()
    assert native_plan["link_items"] == [{"kind": "shared_library", "path": str(shared)}]
    assert native_plan["compilation_units"] == []
    assert native_plan["module_dirs"] == []
    assert result.manifest is not None
    assert result.manifest["compiler"]["wrapper_fortran_flags"] == list(FULL_LIBRARY_WRAPPER_FLAGS)
    assert result.manifest["compiler"]["wrapper_c_flags"] == list(FULL_LIBRARY_WRAPPER_FLAGS)

    if library == "blas":
        bridge = (result.output_dir / "bind_c_full_blas_wrapper.f90").read_text(encoding="utf-8").lower()
        assert "use full_blas_interfaces" not in bridge
        assert "external :: daxpy" in bridge
        assert "subroutine daxpy(" not in bridge
        assert "private\n" not in bridge
        assert "public :: bind_c_daxpy" not in bridge
        _assert_blas_runtime_smoke(module)
    else:
        _assert_lapack_runtime_smoke(module)
