"""Build one native LAPACK library and reuse it through PRIK and f2py."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from examples.f2py_intents import prepare_f2py_intent_sources
from examples.native_library import (
    NativeLibrary,
    build_reference_library,
    compiler_identity,
    linker_name,
    native_cache_root,
    require_tool,
)

from .contracts import remove_internal_root_imports
from .f2py_contract import F2PY_INOUT_ARGUMENTS
from .routine_inventory import F2PY_EXPORT_LIMITATIONS, ROUTINES, SCIPY_VERSION


EXAMPLE_ROOT = Path(__file__).resolve().parent
NATIVE_ROOT = EXAMPLE_ROOT / "native"
BUILD_FLAGS = "-O0"
PRIK_WRAPPER_FLAGS = ("-O0", "-g0")
FORTRAN_SUFFIXES = (".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn")
F2PY_BUILD_DEPENDENCIES = ("la_constants.f90",)
F2PY_KIND_MAP = "{'real': {'wp': 'double'}}\n"


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
            "Reference LAPACK build failed\n"
            f"compiler: {compiler_identity(compiler)}\n"
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
        raise FileNotFoundError(
            f"expected exactly one authoritative source for {routine}, found {[str(path) for path in matches]}"
        )
    return matches[0]


def _f2py_source_plan(workdir: Path) -> tuple[Path, ...]:
    """Return reviewed signatures with intent overlays and their kind dependency."""
    dependencies = tuple(NATIVE_ROOT / name for name in F2PY_BUILD_DEPENDENCIES)
    missing_dependencies = [str(path) for path in dependencies if not path.is_file()]
    if missing_dependencies:
        raise FileNotFoundError(f"missing f2py signature dependencies: {missing_dependencies}")
    selected = tuple(_selected_source(name) for name in ROUTINES if name not in F2PY_EXPORT_LIMITATIONS)
    return prepare_f2py_intent_sources(dependencies + selected, workdir, F2PY_INOUT_ARGUMENTS)


def _f2py_signature_command(workdir: Path) -> tuple[str, ...]:
    """Generate reviewed f2py signatures without compiling implementations."""
    module_name = "f2py_reference_lapack_example"
    f2cmap = workdir / ".f2py_f2cmap"
    f2cmap.write_text(F2PY_KIND_MAP, encoding="utf-8")
    selected_routines = tuple(name for name in ROUTINES if name not in F2PY_EXPORT_LIMITATIONS)
    return (
        sys.executable,
        "-m",
        "numpy.f2py",
        "-m",
        module_name,
        "-h",
        str(workdir / f"{module_name}.pyf"),
        *(str(source) for source in _f2py_source_plan(workdir)),
        "only:",
        *selected_routines,
        ":",
        "--f2cmap",
        str(f2cmap),
        "--overwrite-signature",
    )


def _f2py_build_command(workdir: Path, native_library: Path) -> tuple[str, ...]:
    """Build only f2py's wrapper and link the precompiled LAPACK implementation."""
    module_name = "f2py_reference_lapack_example"
    return (
        sys.executable,
        "-m",
        "numpy.f2py",
        "-c",
        str(workdir / f"{module_name}.pyf"),
        f"-L{native_library.parent}",
        f"-l{linker_name(native_library)}",
        "--f2cmap",
        str(workdir / ".f2py_f2cmap"),
        "--build-dir",
        str(workdir / "generated"),
        f"--f77flags={BUILD_FLAGS}",
        f"--f90flags={BUILD_FLAGS}",
        f"--opt={BUILD_FLAGS}",
    )


def _contract_command(workdir: Path) -> tuple[str, ...]:
    """Generate the complete LAPACK semantic contract through the public CLI."""
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
        str(workdir / "contracts" / "lapack"),
    )


def _prik_build_command(
    runtime_entry: Path,
    native_library: Path,
    workdir: Path,
    compiler: str,
) -> tuple[str, ...]:
    """Build the projected complete-library contract through PRIK's public CLI."""
    jobs = max(1, min(os.cpu_count() or 1, 8))
    joined_wrapper_flags = " ".join(PRIK_WRAPPER_FLAGS)
    return (
        sys.executable,
        "-m",
        "prik",
        str(runtime_entry),
        "--out",
        "prik_reference_lapack_example",
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


@pytest.fixture(scope="session")
def native_build(tmp_path_factory: pytest.TempPathFactory) -> NativeLibrary:
    """Compile complete LAPACK plus its BLAS dependencies once for both wrappers."""
    compiler = _compiler()
    cache_root = (
        native_cache_root()
        if os.environ.get("PRIK_REAL_LIBRARY_NATIVE_CACHE_DIR")
        else tmp_path_factory.mktemp("reference-lapack-native")
    )
    try:
        return build_reference_library("lapack", cache_root=cache_root, compiler=compiler)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        pytest.fail(f"Reference LAPACK native build failed with {compiler_identity(compiler)}\n{error}")


@pytest.fixture(scope="session")
def prik_build(tmp_path_factory: pytest.TempPathFactory, native_build: NativeLibrary) -> BuiltLapack:
    """Build the complete LAPACK wrapper through PRIK's public CLI once."""
    compiler = native_build.compiler
    workdir = tmp_path_factory.mktemp("prik-reference-lapack-example")
    _run_build(_contract_command(workdir), workdir, compiler)
    entry = workdir / "contracts" / "lapack" / "__init__.pyi"
    runtime_entry = remove_internal_root_imports(entry)
    module_name = "prik_reference_lapack_example"
    command = _prik_build_command(runtime_entry, native_build.shared_library, workdir, compiler)
    result = _run_build(command, workdir, compiler)
    return BuiltLapack(
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
def prik_lapack(prik_build: BuiltLapack):
    """Return the complete session-scoped PRIK LAPACK module."""
    return prik_build.module


@pytest.fixture(scope="session")
def f2py_build(tmp_path_factory: pytest.TempPathFactory, native_build: NativeLibrary) -> BuiltLapack:
    """Build f2py against the same complete native LAPACK library."""
    compiler = native_build.compiler
    workdir = tmp_path_factory.mktemp("f2py-reference-lapack-example")
    _run_build(_f2py_signature_command(workdir), workdir, compiler)
    module_name = "f2py_reference_lapack_example"
    command = _f2py_build_command(workdir, native_build.shared_library)
    result = _run_build(command, workdir, compiler, native_build.shared_library)
    return BuiltLapack(
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
def f2py_lapack(f2py_build: BuiltLapack):
    """Return the session-scoped f2py comparison module."""
    return f2py_build.module


@pytest.fixture(scope="session")
def scipy_lapack():
    """Return the pinned SciPy low-level LAPACK module."""
    scipy = pytest.importorskip("scipy")
    if scipy.__version__ != SCIPY_VERSION:
        pytest.fail(f"expected SciPy {SCIPY_VERSION}, found {scipy.__version__}")
    return importlib.import_module("scipy.linalg.lapack")
