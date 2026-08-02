"""Session fixtures for the complete PRIK, f2py, and SciPy LAPACK surfaces."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from tests.fortran.building_shared_library.end_to_end.real_libraries import test_full_libraries as full

from .routine_inventory import F2PY_EXPORT_LIMITATIONS, ROUTINES, SCIPY_VERSION


EXAMPLE_ROOT = Path(__file__).resolve().parent
NATIVE_ROOT = EXAMPLE_ROOT / "native"
BUILD_FLAGS = "-O0"
FORTRAN_SUFFIXES = (".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn")
F2PY_BUILD_DEPENDENCIES = ("la_constants.f90",)
F2PY_KIND_MAP = "{'real': {'wp': 'double'}}\n"
F2PY_LINK_DEPENDENCIES = ("lapack", "blas")


@dataclass(frozen=True)
class BuiltLapack:
    """One imported wrapper and the evidence needed to diagnose its build."""

    module: object
    module_name: str
    workdir: Path
    command: tuple[str, ...]
    compiler_identity: str
    stdout: str
    stderr: str


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
        }
    )
    return environment


def _run_build(command: tuple[str, ...], workdir: Path, compiler: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(  # nosec B603 - fixed tools and repository-owned sources
        command,
        cwd=workdir,
        env=_build_environment(compiler),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        pytest.fail(
            "Reference LAPACK comparison build failed\n"
            f"compiler: {full._compiler_identity(compiler)}\n"
            f"command: {shlex.join(command)}\n"
            f"stdout:\n{result.stdout or '<empty>'}\n"
            f"stderr:\n{result.stderr or '<empty>'}"
        )
    return result


def _import_built_module(module_name: str, workdir: Path):
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(workdir))
    old_flags = sys.getdlopenflags()
    sys.setdlopenflags(getattr(os, "RTLD_LAZY", old_flags) | getattr(os, "RTLD_GLOBAL", 0))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.setdlopenflags(old_flags)
        sys.path.remove(str(workdir))


def _selected_source(routine: str) -> Path:
    """Resolve one reviewed routine to its authoritative native source file."""
    matches = tuple(path for suffix in FORTRAN_SUFFIXES if (path := NATIVE_ROOT / f"{routine}{suffix}").is_file())
    if len(matches) != 1:
        pytest.fail(f"expected exactly one authoritative source for {routine}, found {[str(path) for path in matches]}")
    return matches[0]


def _f2py_source_plan() -> tuple[Path, ...]:
    """Return reviewed implementations plus their minimal compile dependency."""
    dependencies = tuple(NATIVE_ROOT / name for name in F2PY_BUILD_DEPENDENCIES)
    missing_dependencies = [str(path) for path in dependencies if not path.is_file()]
    if missing_dependencies:
        pytest.fail(f"missing f2py build dependencies: {missing_dependencies}")
    selected = tuple(_selected_source(name) for name in ROUTINES if name not in F2PY_EXPORT_LIMITATIONS)
    return dependencies + selected


def _f2py_build_command(workdir: Path) -> tuple[str, ...]:
    """Build only reviewed implementations and link external helper symbols."""
    module_name = "f2py_reference_lapack_example"
    f2cmap = workdir / ".f2py_f2cmap"
    f2cmap.write_text(F2PY_KIND_MAP, encoding="utf-8")
    selected_routines = tuple(name for name in ROUTINES if name not in F2PY_EXPORT_LIMITATIONS)
    link_dependencies = tuple(item for dependency in F2PY_LINK_DEPENDENCIES for item in ("--dep", dependency))
    return (
        sys.executable,
        "-m",
        "numpy.f2py",
        "-c",
        "-m",
        module_name,
        *(str(source) for source in _f2py_source_plan()),
        "only:",
        *selected_routines,
        ":",
        *link_dependencies,
        "--f2cmap",
        str(f2cmap),
        "--build-dir",
        str(workdir / "generated"),
        f"--f77flags={BUILD_FLAGS}",
        f"--f90flags={BUILD_FLAGS}",
        f"--opt={BUILD_FLAGS}",
    )


@pytest.fixture(scope="session")
def prik_build(tmp_path_factory: pytest.TempPathFactory) -> BuiltLapack:
    """Build the one complete PRIK LAPACK wrapper through the established path."""
    compiler = full._compiler()
    workdir = tmp_path_factory.mktemp("prik-reference-lapack-example")
    entry = full._generate_contract(NATIVE_ROOT, workdir / "contracts" / "lapack")
    shared = full._cached_native_shared_library("lapack")
    runtime_entry = full._runtime_entry("lapack", entry, workdir)
    result = full.build_pyi_extension(
        runtime_entry,
        output_name="prik_reference_lapack_example",
        output_dir=workdir / "build",
        native_objects=[shared],
        wrapper_fortran_flags=full.FULL_LIBRARY_WRAPPER_FLAGS,
        wrapper_c_flags=full.FULL_LIBRARY_WRAPPER_FLAGS,
    )
    command = (
        sys.executable,
        "-m",
        "prik",
        "<generated-complete-lapack-contract>",
        "--native-shared-library",
        str(shared),
    )
    return BuiltLapack(
        module=_import_built_module(result.module_name, result.output_dir),
        module_name=result.module_name,
        workdir=workdir,
        command=command,
        compiler_identity=full._compiler_identity(compiler),
        stdout="",
        stderr="",
    )


@pytest.fixture(scope="session")
def prik_lapack(prik_build: BuiltLapack):
    """Return the complete session-scoped PRIK LAPACK module."""
    return prik_build.module


@pytest.fixture(scope="session")
def f2py_build(tmp_path_factory: pytest.TempPathFactory) -> BuiltLapack:
    """Build one raw f2py surface from only the reviewed implementations."""
    compiler = full._compiler()
    workdir = tmp_path_factory.mktemp("f2py-reference-lapack-example")
    module_name = "f2py_reference_lapack_example"
    command = _f2py_build_command(workdir)
    result = _run_build(command, workdir, compiler)
    return BuiltLapack(
        module=_import_built_module(module_name, workdir),
        module_name=module_name,
        workdir=workdir,
        command=command,
        compiler_identity=full._compiler_identity(compiler),
        stdout=result.stdout,
        stderr=result.stderr,
    )


@pytest.fixture(scope="session")
def f2py_lapack(f2py_build: BuiltLapack):
    """Return the session-scoped raw f2py comparison module."""
    return f2py_build.module


@pytest.fixture(scope="session")
def scipy_lapack():
    """Return the pinned SciPy low-level LAPACK module."""
    scipy = pytest.importorskip("scipy")
    if scipy.__version__ != SCIPY_VERSION:
        pytest.fail(f"expected SciPy {SCIPY_VERSION}, found {scipy.__version__}")
    return importlib.import_module("scipy.linalg.lapack")
