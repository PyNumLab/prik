"""Build the reviewed f2py LAPACK wrapper against one native shared library."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from examples.f2py_intents import prepare_f2py_intent_sources
from examples.native_library import linker_name, require_tool

from .routine_inventory import F2PY_EXPORT_LIMITATIONS, ROUTINES


EXAMPLE_ROOT = Path(__file__).resolve().parent
NATIVE_ROOT = EXAMPLE_ROOT / "native"
BUILD_FLAGS = "-O0"
FORTRAN_SUFFIXES = (".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn")
F2PY_BUILD_DEPENDENCIES = ("la_constants.f90",)
F2PY_KIND_MAP = "{'real': {'wp': 'double'}}\n"
F2PY_INOUT_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "dlarfg": ("alpha", "tau"),
    "dlartg": ("c", "s", "r"),
    "dgbcon": ("rcond", "info"),
    "dgecon": ("rcond", "info"),
    "dgtcon": ("rcond", "info"),
    "dpocon": ("rcond", "info"),
    "dppcon": ("rcond", "info"),
    "dsycon": ("rcond", "info"),
    "dtrcon": ("rcond", "info"),
}


def build_environment(compiler: str, native_library: Path) -> dict[str, str]:
    """Return the compiler and runtime-link environment for f2py."""
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
    rpath_flag = f"-Wl,-rpath,{native_library.parent}"
    environment["LDFLAGS"] = " ".join(filter(None, (environment.get("LDFLAGS"), rpath_flag)))
    return environment


def _selected_source(routine: str) -> Path:
    matches = tuple(path for suffix in FORTRAN_SUFFIXES if (path := NATIVE_ROOT / f"{routine}{suffix}").is_file())
    if len(matches) != 1:
        raise FileNotFoundError(
            f"expected exactly one authoritative source for {routine}, found {[str(path) for path in matches]}"
        )
    return matches[0]


def f2py_source_plan(workdir: Path) -> tuple[Path, ...]:
    """Return reviewed signatures with intent overlays and their kind dependency."""
    dependencies = tuple(NATIVE_ROOT / name for name in F2PY_BUILD_DEPENDENCIES)
    missing_dependencies = [str(path) for path in dependencies if not path.is_file()]
    if missing_dependencies:
        raise FileNotFoundError(f"missing f2py signature dependencies: {missing_dependencies}")
    selected = tuple(_selected_source(name) for name in ROUTINES if name not in F2PY_EXPORT_LIMITATIONS)
    return prepare_f2py_intent_sources(dependencies + selected, workdir, F2PY_INOUT_ARGUMENTS)


def f2py_signature_command(workdir: Path) -> tuple[str, ...]:
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
        *(str(source) for source in f2py_source_plan(workdir)),
        "only:",
        *selected_routines,
        ":",
        "--f2cmap",
        str(f2cmap),
        "--overwrite-signature",
    )


def f2py_build_command(workdir: Path, native_library: Path) -> tuple[str, ...]:
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


def build_f2py_wrapper(workdir: Path, native_library: Path, compiler: str) -> None:
    """Generate and compile the f2py wrapper in one user-facing build directory."""
    workdir.mkdir(parents=True, exist_ok=True)
    environment = build_environment(compiler, native_library)
    for command in (f2py_signature_command(workdir), f2py_build_command(workdir, native_library)):
        subprocess.run(  # nosec B603 - explicit Python/f2py commands and copied example inputs
            command,
            cwd=workdir,
            env=environment,
            check=True,
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Build the documented f2py comparison wrapper."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workdir", type=Path)
    parser.add_argument("native_library", type=Path)
    parser.add_argument("--compiler", default=None)
    args = parser.parse_args(argv)
    compiler = args.compiler or require_tool("gfortran")
    build_f2py_wrapper(args.workdir.resolve(), args.native_library.resolve(), compiler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
