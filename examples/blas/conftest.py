"""Build one native BLAS library and reuse it through PRIK and f2py."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from examples.blas.f2py_contract import F2PY_INOUT_ARGUMENTS
from examples.f2py_intents import prepare_f2py_intent_sources
from examples.native_library import (
    NativeLibrary,
    build_reference_library,
    compiler_identity,
    linker_name,
    native_cache_root,
    require_tool,
)


EXAMPLE_ROOT = Path(__file__).resolve().parent
NATIVE_ROOT = EXAMPLE_ROOT / "native"
FORTRAN_SUFFIXES = frozenset({".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"})
BLAS_SOURCES = tuple(
    sorted(path for path in NATIVE_ROOT.iterdir() if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES)
)
BUILD_FLAGS = "-O0"
PRIK_WRAPPER_FLAGS = ("-O0", "-g0")


@dataclass(frozen=True)
class BuiltBLAS:
    """One imported wrapper plus the information needed to diagnose its build."""

    module: object
    module_name: str
    workdir: Path
    command: tuple[str, ...]
    compiler_identity: str
    stdout: str
    stderr: str
    native_library: Path


def _compiler() -> str:
    try:
        return require_tool("gfortran")
    except RuntimeError as error:
        pytest.skip(str(error))


def _build_environment(compiler: str, native_library: Path | None = None) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "CFLAGS": BUILD_FLAGS,
            "FC": compiler,
            "F77": compiler,
            "F90": compiler,
            "FFLAGS": BUILD_FLAGS,
            "F90FLAGS": BUILD_FLAGS,
        }
    )
    if native_library is not None:
        rpath_flag = f"-Wl,-rpath,{native_library.parent}"
        environment["LDFLAGS"] = " ".join(filter(None, (environment.get("LDFLAGS"), rpath_flag)))
    return environment


def _run_build(
    command: tuple[str, ...],
    workdir: Path,
    compiler: str,
    native_library: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(  # nosec B603 - fixed tools and copied example inputs
        command,
        cwd=workdir,
        env=_build_environment(compiler, native_library),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        pytest.fail(
            "Reference BLAS build failed\n"
            f"compiler: {compiler_identity(compiler)}\n"
            f"command: {shlex.join(command)}\n"
            f"stdout:\n{result.stdout or '<empty>'}\n"
            f"stderr:\n{result.stderr or '<empty>'}"
        )
    return result


def _import_built_module(module_name: str, workdir: Path):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(workdir))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(workdir))


def _contract_command(workdir: Path) -> tuple[str, ...]:
    """Generate the complete BLAS semantic contract through the public CLI."""
    return (
        sys.executable,
        "-m",
        "prik",
        "generate",
        "--pyi",
        str(NATIVE_ROOT),
        "--language",
        "fortran",
        "--out",
        str(workdir / "contract" / "blas"),
    )


def _prik_build_command(
    contract_entry: Path,
    native_library: Path,
    workdir: Path,
    compiler: str,
) -> tuple[str, ...]:
    """Build the complete contract while reusing the precompiled native library."""
    jobs = max(1, min(os.cpu_count() or 1, 8))
    joined_wrapper_flags = " ".join(PRIK_WRAPPER_FLAGS)
    return (
        sys.executable,
        "-m",
        "prik",
        str(contract_entry),
        "--out",
        "prik_reference_blas",
        "--out-dir",
        str(workdir / "generated"),
        "--compiler",
        compiler,
        "--native-objects",
        str(native_library),
        "--jobs",
        str(jobs),
        f"--wrapper-fortran-flags={joined_wrapper_flags}",
        f"--wrapper-c-flags={joined_wrapper_flags}",
    )


def _f2py_signature_command(workdir: Path) -> tuple[str, ...]:
    """Generate f2py signatures from reviewed build-local intent overlays."""
    sources = prepare_f2py_intent_sources(BLAS_SOURCES, workdir, F2PY_INOUT_ARGUMENTS)
    return (
        sys.executable,
        "-m",
        "numpy.f2py",
        "-m",
        "f2py_reference_blas",
        "-h",
        str(workdir / "f2py_reference_blas.pyf"),
        *(str(source) for source in sources),
        "--overwrite-signature",
    )


def _f2py_build_command(workdir: Path, native_library: Path) -> tuple[str, ...]:
    """Build only f2py's wrapper and link the precompiled BLAS implementation."""
    return (
        sys.executable,
        "-m",
        "numpy.f2py",
        "-c",
        str(workdir / "f2py_reference_blas.pyf"),
        f"-L{native_library.parent}",
        f"-l{linker_name(native_library)}",
        "--build-dir",
        str(workdir / "generated"),
        f"--f77flags={BUILD_FLAGS}",
        f"--f90flags={BUILD_FLAGS}",
        f"--opt={BUILD_FLAGS}",
    )


@pytest.fixture(scope="session")
def native_build(tmp_path_factory: pytest.TempPathFactory) -> NativeLibrary:
    """Compile the complete BLAS implementation once for both wrappers."""
    compiler = _compiler()
    cache_root = (
        native_cache_root()
        if os.environ.get("PRIK_REAL_LIBRARY_NATIVE_CACHE_DIR")
        else tmp_path_factory.mktemp("reference-blas-native")
    )
    try:
        return build_reference_library("blas", cache_root=cache_root, compiler=compiler)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        pytest.fail(f"Reference BLAS native build failed with {compiler_identity(compiler)}\n{error}")


@pytest.fixture(scope="session")
def prik_build(tmp_path_factory: pytest.TempPathFactory, native_build: NativeLibrary) -> BuiltBLAS:
    """Build and import PRIK against the session's native BLAS library."""
    compiler = native_build.compiler
    workdir = tmp_path_factory.mktemp("prik-reference-blas")
    _run_build(_contract_command(workdir), workdir, compiler)
    contract_entry = workdir / "contract" / "blas" / "__init__.pyi"
    module_name = "prik_reference_blas"
    command = _prik_build_command(contract_entry, native_build.shared_library, workdir, compiler)
    result = _run_build(command, workdir, compiler)
    return BuiltBLAS(
        module=_import_built_module(module_name, workdir),
        module_name=module_name,
        workdir=workdir,
        command=command,
        compiler_identity=compiler_identity(compiler),
        stdout=result.stdout,
        stderr=result.stderr,
        native_library=native_build.shared_library,
    )


@pytest.fixture(scope="session")
def f2py_build(tmp_path_factory: pytest.TempPathFactory, native_build: NativeLibrary) -> BuiltBLAS:
    """Build and import f2py against the same native BLAS library."""
    compiler = native_build.compiler
    workdir = tmp_path_factory.mktemp("f2py-reference-blas")
    _run_build(_f2py_signature_command(workdir), workdir, compiler)
    module_name = "f2py_reference_blas"
    command = _f2py_build_command(workdir, native_build.shared_library)
    result = _run_build(command, workdir, compiler, native_build.shared_library)
    return BuiltBLAS(
        module=_import_built_module(module_name, workdir),
        module_name=module_name,
        workdir=workdir,
        command=command,
        compiler_identity=compiler_identity(compiler),
        stdout=result.stdout,
        stderr=result.stderr,
        native_library=native_build.shared_library,
    )


@pytest.fixture(scope="session")
def prik_blas(prik_build: BuiltBLAS):
    """Return the session-scoped PRIK module."""
    return prik_build.module


@pytest.fixture(scope="session")
def f2py_blas(f2py_build: BuiltBLAS):
    """Return the session-scoped f2py module."""
    return f2py_build.module
