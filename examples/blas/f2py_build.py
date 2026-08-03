"""Build the reviewed f2py BLAS wrapper against one native shared library."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from examples.f2py_intents import prepare_f2py_intent_sources
from examples.native_library import linker_name, require_tool


EXAMPLE_ROOT = Path(__file__).resolve().parent
NATIVE_ROOT = EXAMPLE_ROOT / "native"
FORTRAN_SUFFIXES = frozenset({".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"})
BLAS_SOURCES = tuple(
    sorted(path for path in NATIVE_ROOT.iterdir() if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES)
)
BUILD_FLAGS = "-O0"
F2PY_INOUT_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "srotg": ("a", "b", "c", "s"),
    "drotg": ("a", "b", "c", "s"),
    "crotg": ("a", "c", "s"),
    "zrotg": ("a", "c", "s"),
    "srotmg": ("sd1", "sd2", "sx1", "sparam"),
    "drotmg": ("dd1", "dd2", "dx1", "dparam"),
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


def f2py_signature_command(workdir: Path) -> tuple[str, ...]:
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


def f2py_build_command(workdir: Path, native_library: Path) -> tuple[str, ...]:
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
