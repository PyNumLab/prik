"""Fetch, verify, build, and cache the pinned TA-Lib native library."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys


TA_LIB_VERSION = "0.7.1"
TA_LIB_TAG = f"v{TA_LIB_VERSION}"
TA_LIB_COMMIT = "2247d599bddf37ed37e3a709371517e46efc66f6"
TA_LIB_REPOSITORY = "https://github.com/TA-Lib/ta-lib.git"
DEFAULT_JOB_LIMIT = 8


def _require_tool(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} is required to build the TA-Lib example")
    return executable


def _run(*command: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    output_options = {"capture_output": True} if capture_output else {"stdout": sys.stderr}
    return subprocess.run(  # nosec B603 - fixed tools and pinned public source
        command,
        check=True,
        text=True,
        **output_options,
    )


def _cache_root() -> Path:
    configured = os.environ.get("PRIK_TALIB_CACHE_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg_cache).expanduser() if xdg_cache else Path.home() / ".cache"
    return base / "prik" / "examples" / "ta-lib"


def _compiler_key(compiler: str) -> str:
    identity = _run(compiler, "--version", capture_output=True).stdout.splitlines()[0]
    digest = hashlib.sha256(f"{Path(compiler).resolve()}:{identity}".encode()).hexdigest()[:12]
    target = f"{platform.system().lower()}-{platform.machine().lower()}"
    return f"{target}-{digest}"


def _jobs() -> int:
    configured = os.environ.get("PRIK_TALIB_JOBS") or os.environ.get("PRIK_REAL_LIBRARY_NATIVE_JOBS")
    if configured is not None:
        jobs = int(configured)
        if jobs < 1:
            raise ValueError("PRIK_TALIB_JOBS must be a positive integer")
        return jobs
    return max(1, min(os.cpu_count() or 1, DEFAULT_JOB_LIMIT))


def _verified_source(cache_root: Path, git: str) -> Path:
    source = cache_root / f"source-{TA_LIB_TAG}"
    if not source.is_dir():
        cache_root.mkdir(parents=True, exist_ok=True)
        _run(git, "clone", "--depth", "1", "--branch", TA_LIB_TAG, TA_LIB_REPOSITORY, str(source))
    actual = _run(git, "-C", str(source), "rev-parse", "HEAD", capture_output=True).stdout.strip()
    if actual != TA_LIB_COMMIT:
        raise RuntimeError(
            f"cached TA-Lib {TA_LIB_TAG} resolved to {actual}, expected {TA_LIB_COMMIT}; remove {source} and retry"
        )
    return source


def _installed_library(prefix: Path) -> bool:
    include = prefix / "include" / "ta-lib" / "ta_libc.h"
    libraries = tuple((prefix / "lib").glob("libta-lib.*"))
    return include.is_file() and bool(libraries)


def _shared_library(prefix: Path) -> Path:
    """Return the installed shared library used for reference-test settings."""
    library_dir = prefix / "lib"
    preferred = (library_dir / "libta-lib.so", library_dir / "libta-lib.dylib")
    for path in preferred:
        if path.is_file():
            return path.resolve()
    candidates = sorted((*library_dir.glob("libta-lib.so.*"), *library_dir.glob("libta-lib.*.dylib")))
    if not candidates:
        raise RuntimeError(f"TA-Lib installation has no shared library under {library_dir}")
    return candidates[-1].resolve()


def _reference_paths(build: Path) -> tuple[Path, Path]:
    return build / "bin" / "ta_regtest", build / "bin" / "ta_ref_serve"


def _reference_tools_built(build: Path) -> bool:
    return all(path.is_file() for path in _reference_paths(build))


def _build_reference_server(compiler: str, source: Path, build: Path) -> Path:
    """Build the pinned library's JSON oracle used by its own test runner."""
    generated = source / "ta_codegen" / "output" / "c"
    template = generated / "ta_codegen_serve.c"
    static_library = build / "libta-lib.a"
    output = build / "bin" / "ta_ref_serve"
    if output.is_file() and output.stat().st_mtime >= max(template.stat().st_mtime, static_library.stat().st_mtime):
        return output

    text = template.read_text(encoding="utf-8")
    text = re.sub(r'#include "ta_func/[^"]*\.c"\n', "", text)
    text = re.sub(r'#include "ta_common/[^"]*\.c"\n', "", text)
    text = text.replace(
        "#include <stdio.h>",
        '#include <stdio.h>\n#include "ta_func.h"\n#include "ta_memory.h"\n#include "ta_utility.h"',
    )
    text = text.replace(
        "int main(void) {",
        "int main(void) { TA_Initialize(); TA_RestoreCandleDefaultSettings(TA_AllCandleSettings);",
    )
    oracle_source = build / "_ta_ref_serve.c"
    oracle_source.write_text(text, encoding="utf-8")
    include_dirs = (
        generated,
        source / "include",
        generated / "ta_common",
        generated / "ta_abstract",
        generated / "ta_abstract" / "frames",
        source / "ta_codegen" / "input" / "lib" / "c",
        source / "src" / "ta_common",
        source / "src" / "ta_func",
        source / "src",
        source / "src" / "ta_abstract",
        source / "src" / "ta_abstract" / "frames",
    )
    try:
        _run(
            compiler,
            "-O3",
            "-DNDEBUG",
            "-DTA_REF_SERVE",
            *(f"-I{path}" for path in include_dirs),
            "-o",
            str(output),
            str(oracle_source),
            str(static_library),
            "-lm",
        )
    finally:
        oracle_source.unlink(missing_ok=True)
    return output


def build_ta_lib(compiler: str) -> tuple[Path, Path, Path, Path]:
    """Return the install prefix, runner, oracle, and shared library."""
    override = os.environ.get("PRIK_TALIB_PREFIX")
    if override:
        prefix = Path(override).expanduser().resolve()
        if not _installed_library(prefix):
            raise RuntimeError(f"PRIK_TALIB_PREFIX is not a complete TA-Lib install: {prefix}")
        runner_value = os.environ.get("PRIK_TALIB_REGTEST")
        oracle_value = os.environ.get("PRIK_TALIB_REFERENCE_SERVER")
        if not runner_value or not oracle_value:
            raise RuntimeError(
                "PRIK_TALIB_PREFIX requires PRIK_TALIB_REGTEST and PRIK_TALIB_REFERENCE_SERVER "
                "for full reference verification"
            )
        runner = Path(runner_value).expanduser().resolve()
        oracle = Path(oracle_value).expanduser().resolve()
        if not runner.is_file() or not oracle.is_file():
            raise RuntimeError("configured TA-Lib regression runner or reference server does not exist")
        return prefix, runner, oracle, _shared_library(prefix)

    compiler = str(Path(compiler).resolve())
    cache_root = _cache_root()
    source = _verified_source(cache_root, _require_tool("git"))
    key = _compiler_key(compiler)
    build = cache_root / f"build-{TA_LIB_TAG}-{key}"
    prefix = cache_root / f"install-{TA_LIB_TAG}-{key}"
    complete = prefix / ".prik-ta-lib-complete"
    runner, oracle = _reference_paths(build)
    if complete.is_file() and _installed_library(prefix) and _reference_tools_built(build):
        return prefix, runner, oracle, _shared_library(prefix)

    cmake = _require_tool("cmake")
    _run(
        cmake,
        "-S",
        str(source),
        "-B",
        str(build),
        "-DBUILD_DEV_TOOLS=ON",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_C_COMPILER={compiler}",
        f"-DCMAKE_INSTALL_PREFIX={prefix}",
    )
    _run(cmake, "--build", str(build), "--parallel", str(_jobs()))
    _run(cmake, "--install", str(build))
    if not _installed_library(prefix):
        raise RuntimeError(f"TA-Lib installation did not produce headers and a library under {prefix}")
    oracle = _build_reference_server(compiler, source, build)
    if not runner.is_file():
        raise RuntimeError(f"TA-Lib build did not produce its regression runner at {runner}")
    complete.write_text(f"{TA_LIB_TAG}\n{TA_LIB_COMMIT}\n", encoding="utf-8")
    return prefix, runner, oracle, _shared_library(prefix)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default="cc")
    names = ("prefix", "regtest", "reference", "library")
    parser.add_argument("--artifact", choices=names, default="prefix")
    args = parser.parse_args()
    compiler = _require_tool(args.compiler)
    artifacts = dict(zip(names, build_ta_lib(compiler), strict=True))
    print(artifacts[args.artifact])


if __name__ == "__main__":
    main()
