"""Build the complete reference BLAS once per pytest session with both tools."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import pytest


EXAMPLE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = EXAMPLE_ROOT.parents[1]
NATIVE_ROOT = EXAMPLE_ROOT / "native"
FORTRAN_SUFFIXES = frozenset({".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"})
BLAS_SOURCES = tuple(
    sorted(path for path in NATIVE_ROOT.iterdir() if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES)
)
BUILD_FLAGS = "-O0"


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


def _compiler() -> str:
    compiler = shutil.which("gfortran")
    if compiler is None:
        pytest.skip("GNU Fortran is required to build the reference BLAS example")
    return compiler


def _compiler_identity(compiler: str) -> str:
    result = subprocess.run(  # nosec B603 - fixed local compiler identity probe
        (compiler, "--version"),
        capture_output=True,
        text=True,
        check=False,
    )
    first_line = result.stdout.splitlines()[0] if result.stdout else compiler
    return f"{Path(compiler).resolve()}: {first_line}"


def _build_environment(compiler: str) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "CFLAGS": BUILD_FLAGS,
            "FC": compiler,
            "F77": compiler,
            "F90": compiler,
            "FFLAGS": BUILD_FLAGS,
            "F90FLAGS": BUILD_FLAGS,
            "PYTHONPATH": os.pathsep.join(filter(None, (str(REPOSITORY_ROOT), environment.get("PYTHONPATH")))),
        }
    )
    return environment


def _run_build(command: tuple[str, ...], workdir: Path, compiler: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(  # nosec B603 - command is assembled from repository sources and fixed tools
        command,
        cwd=workdir,
        env=_build_environment(compiler),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        pytest.fail(
            "Reference BLAS build failed\n"
            f"compiler: {_compiler_identity(compiler)}\n"
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


@pytest.fixture(scope="session")
def prik_build(tmp_path_factory: pytest.TempPathFactory) -> BuiltBLAS:
    """Build and import the complete source set through PRIK once."""
    compiler = _compiler()
    workdir = tmp_path_factory.mktemp("prik-reference-blas")
    module_name = "prik_reference_blas"
    jobs = max(1, min(os.cpu_count() or 1, 8))
    command = (
        sys.executable,
        "-m",
        "prik",
        *(str(source) for source in BLAS_SOURCES),
        "--out",
        module_name,
        "--out-dir",
        str(workdir / "generated"),
        "--compiler",
        compiler,
        "--jobs",
        str(jobs),
        f"--native-compile-flags={BUILD_FLAGS}",
        f"--wrapper-fortran-flags={BUILD_FLAGS}",
        f"--wrapper-c-flags={BUILD_FLAGS}",
    )
    result = _run_build(command, workdir, compiler)
    return BuiltBLAS(
        module=_import_built_module(module_name, workdir),
        module_name=module_name,
        workdir=workdir,
        command=command,
        compiler_identity=_compiler_identity(compiler),
        stdout=result.stdout,
        stderr=result.stderr,
    )


@pytest.fixture(scope="session")
def f2py_build(tmp_path_factory: pytest.TempPathFactory) -> BuiltBLAS:
    """Build and import the identical complete source set through f2py once."""
    compiler = _compiler()
    workdir = tmp_path_factory.mktemp("f2py-reference-blas")
    module_name = "f2py_reference_blas"
    command = (
        sys.executable,
        "-m",
        "numpy.f2py",
        "-c",
        "-m",
        module_name,
        *(str(source) for source in BLAS_SOURCES),
        "--build-dir",
        str(workdir / "generated"),
        f"--f77flags={BUILD_FLAGS}",
        f"--f90flags={BUILD_FLAGS}",
        f"--opt={BUILD_FLAGS}",
    )
    result = _run_build(command, workdir, compiler)
    return BuiltBLAS(
        module=_import_built_module(module_name, workdir),
        module_name=module_name,
        workdir=workdir,
        command=command,
        compiler_identity=_compiler_identity(compiler),
        stdout=result.stdout,
        stderr=result.stderr,
    )


@pytest.fixture(scope="session")
def prik_blas(prik_build: BuiltBLAS):
    """Return the session-scoped PRIK module."""
    return prik_build.module


@pytest.fixture(scope="session")
def f2py_blas(f2py_build: BuiltBLAS):
    """Return the session-scoped f2py module."""
    return f2py_build.module
