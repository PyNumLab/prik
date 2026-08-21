"""Select coherent vendor profiles for explicit native wrapper builds.

``available_compilers`` supplies separate C and Fortran settings for every
supported vendor, including the active Python and NumPy extension inputs.
``fortran_compiler_family()`` classifies a selected Fortran executable and
names its matching C driver; executable lookup and command execution belong to
``Compiler`` in :mod:`prik.compiler.compilers`.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
import sys
import sysconfig

from numpy import get_include as numpy_include


def _words(value: object) -> tuple[str, ...]:
    """Return a configuration variable as command-line words."""
    return tuple(str(value or "").split())


def _python_library_candidates(config: dict[str, object]) -> tuple[Path, ...]:
    """Find Python library files advertised by the active interpreter."""
    libdir = config.get("LIBDIR")
    version = config.get("VERSION")
    if not isinstance(libdir, str) or not libdir or not isinstance(version, str) or not version:
        return ()
    directory = Path(libdir)
    if not directory.is_dir():
        return ()
    return tuple(sorted(directory.glob(f"libpython{version}*")))


def _python_library_name(config: dict[str, object]) -> str | None:
    """Return the fallback ``-l`` name when no interpreter file is available."""
    library = str(config.get("LDLIBRARY") or config.get("LIBRARY") or "")
    if library.startswith("lib"):
        return Path(library).stem.removeprefix("lib")
    return None


def _python_include_directories(config: dict[str, object]) -> tuple[str, ...]:
    """Return Python header roots, including a delegated multiarch root."""
    include_dirs = [numpy_include()]
    include = config.get("INCLUDEPY")
    if not isinstance(include, str) or not include:
        return tuple(include_dirs)

    include_path = Path(include)
    include_dirs.append(include)
    multiarch = config.get("MULTIARCH")
    if isinstance(multiarch, str) and multiarch:
        multiarch_root = include_path.parent / multiarch
        delegated = multiarch_root / include_path.name / "pyconfig.h"
        if delegated.is_file():
            include_dirs.extend((str(include_path.parent), str(multiarch_root)))
    return tuple(dict.fromkeys(include_dirs))


def _python_build_settings() -> dict[str, object]:
    """Collect the active interpreter's headers, extension suffix, and link input."""
    config = dict(sysconfig.get_config_vars())

    python_settings: dict[str, object] = {
        "flags": (*_words(config.get("CFLAGS")), *_words(config.get("CC"))[1:]),
        "include": _python_include_directories(config),
        "shared_suffix": str(config.get("EXT_SUFFIX") or ".so"),
    }
    settings: dict[str, object] = {"libs": _words(config.get("LIBM")), "python": python_settings}
    candidates = _python_library_candidates(config)
    shared_suffixes = (".dylib", ".dll") if sys.platform in {"darwin", "win32"} else (".so",)
    shared = tuple(path for path in candidates if any(suffix in path.name for suffix in shared_suffixes))
    static = tuple(path for path in candidates if path.suffix == ".a")
    preferred = shared or static
    if preferred:
        exact = tuple(path for path in preferred if path.suffix in shared_suffixes or path.suffix == ".a")
        library = exact[0] if exact else preferred[0]
        python_settings["dependencies"] = (str(library),)
        python_settings["libdir"] = (str(library.parent),)
        return settings

    name = _python_library_name(config)
    if name:
        python_settings["libs"] = (name,)
    libdir = config.get("LIBDIR")
    if isinstance(libdir, str) and libdir:
        python_settings["libdir"] = (libdir,)
    return settings


def _language(
    executable: str,
    mpi_executable: str,
    *,
    debug_flags: tuple[str, ...],
    release_flags: tuple[str, ...],
    general_flags: tuple[str, ...],
    optional_general_flags: tuple[str, ...] = (),
    standard_flags: tuple[str, ...],
    module_output_flag: str | None = None,
    openmp: dict[str, tuple[str, ...]] | None = None,
    openacc: dict[str, tuple[str, ...]] | None = None,
) -> dict[str, object]:
    """Create one language entry without mixing it with build orchestration."""
    entry: dict[str, object] = {
        "exec": executable,
        "mpi_exec": mpi_executable,
        "debug_flags": debug_flags,
        "release_flags": release_flags,
        "general_flags": general_flags,
        "optional_general_flags": optional_general_flags,
        "standard_flags": standard_flags,
        "mpi": {},
        "openmp": openmp or {},
        "openacc": openacc or {},
    }
    if module_output_flag is not None:
        entry["module_output_flag"] = module_output_flag
    return entry


_GNU_C = _language(
    "gcc",
    "mpicc",
    debug_flags=("-g", "-O0"),
    release_flags=("-O3", "-funroll-loops", "-DNDEBUG"),
    general_flags=("-fPIC",),
    standard_flags=("-std=c99",),
    openmp={"flags": ("-fopenmp",), "libs": ("gomp",)},
    openacc={"flags": ("-ta=multicore", "-Minfo=accel")},
)
_GNU_CXX = _language(
    "g++",
    "mpic++",
    debug_flags=("-g", "-O0"),
    release_flags=("-O3", "-funroll-loops"),
    general_flags=("-fPIC",),
    standard_flags=("--std=c++20",),
    openmp={"flags": ("-fopenmp",), "libs": ("gomp",)},
    openacc={"flags": ("-ta=multicore", "-Minfo=accel")},
)
_GNU_FORTRAN = _language(
    "gfortran",
    "mpif90",
    debug_flags=("-fcheck=bounds", "-g", "-O0"),
    release_flags=("-O3", "-funroll-loops", "-DNDEBUG"),
    general_flags=("-fPIC", "-cpp"),
    optional_general_flags=("-ftrampoline-impl=heap",),
    standard_flags=("-std=f2003",),
    module_output_flag="-J",
    openmp={"flags": ("-fopenmp",), "libs": ("gomp",)},
    openacc={"flags": ("-ta=multicore", "-Minfo=accel")},
)

_INTEL_C = _language(
    "icx",
    "mpiicx",
    debug_flags=("-g", "-O0"),
    release_flags=("-O3", "-funroll-loops", "-DNDEBUG"),
    general_flags=("-fPIC",),
    standard_flags=("-std=c99",),
    openmp={"flags": ("-qopenmp",)},
    openacc={"flags": ("-ta=multicore", "-Minfo=accel")},
)
_INTEL_CXX = _language(
    "icpx",
    "mpiicpx",
    debug_flags=("-g", "-O0"),
    release_flags=("-O3", "-funroll-loops"),
    general_flags=("-fPIC",),
    standard_flags=("--std=c++20",),
    openmp={"flags": ("-qopenmp",)},
    openacc={"flags": ("-ta=multicore", "-Minfo=accel")},
)
_INTEL_FORTRAN = _language(
    "ifx",
    "mpiifx",
    debug_flags=("-check", "bounds", "-g", "-O0"),
    release_flags=("-O3", "-funroll-loops", "-DNDEBUG"),
    general_flags=("-fPIC", "-fpp"),
    standard_flags=("-std=f2003",),
    module_output_flag="-module",
    openmp={"flags": ("-qopenmp", "-nostandard-realloc-lhs"), "libs": ("iomp5",)},
    openacc={"flags": ("-ta=multicore", "-Minfo=accel")},
)

_PGI_C = _language(
    "pgcc",
    "pgcc",
    debug_flags=("-g", "-O0"),
    release_flags=("-O3", "-Munroll", "-DNDEBUG"),
    general_flags=("-fPIC",),
    standard_flags=("-std=c99",),
    openmp={"flags": ("-mp",)},
    openacc={"flags": ("-acc",)},
)
_PGI_FORTRAN = _language(
    "pgfortran",
    "pgfortran",
    debug_flags=("-Mbounds", "-g", "-O0"),
    release_flags=("-O3", "-Munroll", "-DNDEBUG"),
    general_flags=("-fPIC", "-cpp"),
    standard_flags=("-Mstandard",),
    module_output_flag="-module",
    openmp={"flags": ("-mp",)},
    openacc={"flags": ("-acc",)},
)

_NVIDIA_C = _language(
    "nvc",
    "mpicc",
    debug_flags=("-g", "-O0"),
    release_flags=("-O3", "-Munroll", "-DNDEBUG"),
    general_flags=("-fPIC",),
    standard_flags=("-std=c99",),
    openmp={"flags": ("-mp",)},
    openacc={"flags": ("-acc",)},
)
_NVIDIA_CXX = _language(
    "nvc++",
    "mpic++",
    debug_flags=("-g", "-O0"),
    release_flags=("-O3", "-Munroll"),
    general_flags=("-fPIC",),
    standard_flags=("--std=c++20",),
    openmp={"flags": ("-mp",)},
    openacc={"flags": ("-acc",)},
)
_NVIDIA_FORTRAN = _language(
    "nvfortran",
    "mpifort",
    debug_flags=("-Mbounds", "-g", "-O0"),
    release_flags=("-O3", "-Munroll", "-DNDEBUG"),
    general_flags=("-fPIC", "-cpp"),
    standard_flags=("-Mstandard",),
    module_output_flag="-module",
    openmp={"flags": ("-mp",)},
    openacc={"flags": ("-acc",)},
)

_CLANG_OPENMP = {"flags": ("-fopenmp",)}
if sys.platform == "darwin":
    _CLANG_OPENMP = {"flags": ("-Xpreprocessor", "-fopenmp"), "libs": ("omp",)}
_LLVM_C = _language(
    "clang",
    "mpicc",
    debug_flags=("-g", "-O0"),
    release_flags=("-O3", "-funroll-loops", "-DNDEBUG"),
    general_flags=("-fPIC",),
    standard_flags=("-std=c99",),
    openmp=_CLANG_OPENMP,
    openacc={"flags": ("-fopenacc",)},
)
_LLVM_CXX = _language(
    "clang++",
    "mpic++",
    debug_flags=("-g", "-O0"),
    release_flags=("-O3", "-funroll-loops"),
    general_flags=("-fPIC",),
    standard_flags=("--std=c++20",),
    openmp=_CLANG_OPENMP,
    openacc={"flags": ("-fopenacc",)},
)
_LLVM_FORTRAN = _language(
    "flang",
    "mpifort",
    debug_flags=("-g", "-O0"),
    release_flags=("-O3", "-DNDEBUG"),
    general_flags=("-fPIC", "-cpp"),
    standard_flags=("-std=f2003",),
    module_output_flag="-J",
    openmp=_CLANG_OPENMP,
    openacc={"flags": ("-fopenacc",)},
)


def _toolchain(**languages: dict[str, object]) -> dict[str, dict[str, object]]:
    """Attach active-Python build settings to independent language entries."""
    python_settings = _python_build_settings()
    return {name: {**deepcopy(language), **deepcopy(python_settings)} for name, language in languages.items()}


available_compilers = {
    "GNU": _toolchain(c=_GNU_C, **{"c++": _GNU_CXX}, fortran=_GNU_FORTRAN),
    "intel": _toolchain(c=_INTEL_C, **{"c++": _INTEL_CXX}, fortran=_INTEL_FORTRAN),
    "PGI": _toolchain(c=_PGI_C, fortran=_PGI_FORTRAN),
    "nvidia": _toolchain(c=_NVIDIA_C, **{"c++": _NVIDIA_CXX}, fortran=_NVIDIA_FORTRAN),
    "LLVM": _toolchain(c=_LLVM_C, **{"c++": _LLVM_CXX}, fortran=_LLVM_FORTRAN),
}

vendors = tuple(available_compilers)

_FORTRAN_COMPILER_FAMILIES = (
    ("nvfortran", "nvidia", "nvc"),
    ("pgfortran", "PGI", "pgcc"),
    ("gfortran", "GNU", "gcc"),
    ("flang", "LLVM", "clang"),
    ("ifort", "intel", "icx"),
    ("ifx", "intel", "icx"),
)

_C_COMPILER_FAMILIES = (
    ("nvc", "nvidia"),
    ("pgcc", "PGI"),
    ("gcc", "GNU"),
    ("clang", "LLVM"),
    ("icx", "intel"),
    ("icc", "intel"),
)


def fortran_compiler_family(executable: str) -> tuple[str, str, str]:
    """Return the compiler token, profile, and matching C executable name."""
    name = Path(executable).name
    for token, vendor, c_executable in _FORTRAN_COMPILER_FAMILIES:
        if re.search(rf"(?:^|-){re.escape(token)}(?:-|$)", name):
            return token, vendor, c_executable
    supported = ", ".join(token for token, _vendor, _c_executable in _FORTRAN_COMPILER_FAMILIES)
    raise ValueError(f"Unknown Fortran compiler family for {executable!r}; expected one of: {supported}")


def c_compiler_family(executable: str) -> tuple[str, str]:
    """Return the C-driver token and compiler profile for ``executable``.

    C-only extension builds deliberately choose this route instead of treating
    a C executable as a misspelled Fortran driver.  Mixed-language builds keep
    using :func:`fortran_compiler_family`, because the Fortran runtime then
    owns the final link driver.
    """
    name = Path(executable).name
    for token, vendor in _C_COMPILER_FAMILIES:
        if re.search(rf"(?:^|-){re.escape(token)}(?:-|$)", name):
            return token, vendor
    supported = ", ".join(token for token, _vendor in _C_COMPILER_FAMILIES)
    raise ValueError(f"Unknown C compiler family for {executable!r}; expected one of: {supported}")


if __name__ == "__main__":
    token, vendor, c_executable = fortran_compiler_family("/opt/toolchain/bin/gfortran-13")
    fortran_profile = available_compilers[vendor]["fortran"]

    print(f"Selected family: {token}")
    print(f"Compiler profile: {vendor}")
    print(f"Matching C executable: {c_executable}")
    print(f"Fortran module-output flag: {fortran_profile['module_output_flag']}")
