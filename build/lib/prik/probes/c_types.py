"""Compiler-derived ABI facts for modeled C arithmetic primitives and standard types.

This module deliberately runs a generated C executable instead of hard-coding
primitive widths or typedef spellings. Those are target/compiler facts, while
``FILE`` is an opaque library handle for wrapper purposes.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from contextlib import suppress
from typing import Any

from prik.pipeline.preprocessing import PreprocessingConfig, PreprocessingError, validate_macro_name


class CStandardTypeProbeError(ValueError):
    """Raised when a compiler-derived C standard type probe cannot run."""


@dataclass(frozen=True)
class CStandardTypeProbeRecipe:
    """Commands and input flags needed to reproduce one probe result."""

    compiler: str
    compile_argv: list[str]
    run_argv: list[str]
    probe_standard: str = "c11"
    requested_standard: str | None = None
    include_dirs: list[str] | None = None
    defines: list[str] | None = None
    undefs: list[str] | None = None
    compiler_args: list[str] | None = None


@dataclass(frozen=True)
class CStandardTypeProbeReport:
    """JSON-stable ABI facts suitable as input to later C semantic mapping."""

    types: dict[str, dict[str, object]]
    recipe: CStandardTypeProbeRecipe
    source_text: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible report."""
        return asdict(self)


_SIGNED_INTEGER_TYPES = {
    "signed char",
    "short",
    "int",
    "long",
    "long long",
}
_UNSIGNED_INTEGER_TYPES = {
    "unsigned char",
    "unsigned short",
    "unsigned int",
    "unsigned long",
    "unsigned long long",
}
_REAL_TYPES = {"float", "double", "long double"}
_COMPLEX_TYPES = {"float _Complex", "double _Complex", "long double _Complex"}
# Increment when report classification changes without changing the generated C source.
_PROBE_CACHE_SCHEMA_VERSION = 1
_PROBE_ENVIRONMENT_VARIABLES = (
    "COMPILER_PATH",
    "CPATH",
    "C_INCLUDE_PATH",
    "GCC_EXEC_PREFIX",
    "INCLUDE",
    "LIB",
    "LIBRARY_PATH",
    "MACOSX_DEPLOYMENT_TARGET",
    "QEMU_LD_PREFIX",
    "SDKROOT",
    "SYSROOT",
)
_MEMORY_CACHE: dict[str, CStandardTypeProbeReport] = {}


def build_c_standard_type_probe_source() -> str:
    """Return the C11 source compiled by :func:`probe_c_standard_types`."""
    return r"""#include <complex.h>
#include <float.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <time.h>

#define PRIK_BASE_TYPE(value) _Generic((value), \
    _Bool: "_Bool", \
    char: "char", \
    signed char: "signed char", \
    unsigned char: "unsigned char", \
    short: "short", \
    unsigned short: "unsigned short", \
    int: "int", \
    unsigned int: "unsigned int", \
    long: "long", \
    unsigned long: "unsigned long", \
    long long: "long long", \
    unsigned long long: "unsigned long long", \
    float: "float", \
    double: "double", \
    long double: "long double", \
    float _Complex: "float _Complex", \
    double _Complex: "double _Complex", \
    long double _Complex: "long double _Complex", \
    default: "other")

#define PRIK_PRINT_ARITHMETIC(name, header, type) \
    printf("\"" name "\":{\"header\":\"" header "\",\"available\":true," \
           "\"kind\":\"arithmetic\",\"underlying_c_type\":\"%s\"," \
           "\"bits\":%zu,\"alignment_bits\":%zu}", \
           PRIK_BASE_TYPE((type)0), \
           sizeof(type) * (size_t)CHAR_BIT, \
           _Alignof(type) * (size_t)CHAR_BIT)

#define PRIK_PRINT_CHAR() \
    printf("\"char\":{\"header\":\"<builtin>\",\"available\":true," \
           "\"kind\":\"arithmetic\",\"underlying_c_type\":\"char\"," \
           "\"signed\":%s,\"bits\":%zu,\"alignment_bits\":%zu}", \
           CHAR_MIN < 0 ? "true" : "false", \
           sizeof(char) * (size_t)CHAR_BIT, \
           _Alignof(char) * (size_t)CHAR_BIT)

#define PRIK_PRINT_REAL(name, type, precision, max_exp) \
    printf("\"" name "\":{\"header\":\"<builtin>\",\"available\":true," \
           "\"kind\":\"arithmetic\",\"underlying_c_type\":\"%s\"," \
           "\"bits\":%zu,\"alignment_bits\":%zu,\"precision_bits\":%d," \
           "\"max_binary_exponent\":%d}", \
           PRIK_BASE_TYPE((type)0), \
           sizeof(type) * (size_t)CHAR_BIT, \
           _Alignof(type) * (size_t)CHAR_BIT, \
           precision, max_exp)

int main(void) {
    printf("{\"types\":{");
    PRIK_PRINT_ARITHMETIC("_Bool", "<builtin>", _Bool);
    printf(",");
    PRIK_PRINT_CHAR();
    printf(",");
    PRIK_PRINT_ARITHMETIC("signed char", "<builtin>", signed char);
    printf(",");
    PRIK_PRINT_ARITHMETIC("unsigned char", "<builtin>", unsigned char);
    printf(",");
    PRIK_PRINT_ARITHMETIC("short", "<builtin>", short);
    printf(",");
    PRIK_PRINT_ARITHMETIC("unsigned short", "<builtin>", unsigned short);
    printf(",");
    PRIK_PRINT_ARITHMETIC("int", "<builtin>", int);
    printf(",");
    PRIK_PRINT_ARITHMETIC("unsigned int", "<builtin>", unsigned int);
    printf(",");
    PRIK_PRINT_ARITHMETIC("long", "<builtin>", long);
    printf(",");
    PRIK_PRINT_ARITHMETIC("unsigned long", "<builtin>", unsigned long);
    printf(",");
    PRIK_PRINT_ARITHMETIC("long long", "<builtin>", long long);
    printf(",");
    PRIK_PRINT_ARITHMETIC("unsigned long long", "<builtin>", unsigned long long);
    printf(",");
    PRIK_PRINT_REAL("float", float, FLT_MANT_DIG, FLT_MAX_EXP);
    printf(",");
    PRIK_PRINT_REAL("double", double, DBL_MANT_DIG, DBL_MAX_EXP);
    printf(",");
    PRIK_PRINT_REAL("long double", long double, LDBL_MANT_DIG, LDBL_MAX_EXP);
    printf(",");
    PRIK_PRINT_ARITHMETIC("float _Complex", "<builtin>", float _Complex);
    printf(",");
    PRIK_PRINT_ARITHMETIC("double _Complex", "<builtin>", double _Complex);
    printf(",");
    PRIK_PRINT_ARITHMETIC("long double _Complex", "<builtin>", long double _Complex);
    printf(",");
    PRIK_PRINT_ARITHMETIC("size_t", "stddef.h", size_t);
    printf(",");
#ifdef UINT32_MAX
    PRIK_PRINT_ARITHMETIC("uint32_t", "stdint.h", uint32_t);
#else
    printf("\"uint32_t\":{\"header\":\"stdint.h\",\"available\":false}");
#endif
    printf(",");
    PRIK_PRINT_ARITHMETIC("time_t", "time.h", time_t);
    printf(",\"FILE\":{\"header\":\"stdio.h\",\"available\":true,"
           "\"kind\":\"opaque_handle\",\"pointer_bits\":%zu,"
           "\"pointer_alignment_bits\":%zu}",
           sizeof(FILE *) * (size_t)CHAR_BIT,
           _Alignof(FILE *) * (size_t)CHAR_BIT);
    printf("}}\n");
    return 0;
}
"""


def _probe_compile_flags(config: PreprocessingConfig) -> list[str]:
    """Carry target-relevant compiler flags into the generated C11 probe."""
    flags = [f"-I{path}" for path in config.include_dirs]
    flags.extend(f"-D{define}" for define in config.defines)
    flags.extend(f"-U{undef}" for undef in config.undefs)
    flags.append("-std=c11")
    flags.extend(config.compiler_args)
    return flags


def _semantic_type_facts(types: dict[str, dict[str, object]]) -> None:
    """Classify arithmetic results for later semantic type conversion."""
    for fact in types.values():
        if not fact.get("available") or fact.get("kind") != "arithmetic":
            continue
        underlying = fact.get("underlying_c_type")
        if underlying in _SIGNED_INTEGER_TYPES:
            fact["kind"] = "integer"
            fact["signed"] = True
            fact["semantic_category"] = "signed_integer"
        elif underlying in _UNSIGNED_INTEGER_TYPES:
            fact["kind"] = "integer"
            fact["signed"] = False
            fact["semantic_category"] = "unsigned_integer"
        elif underlying in _REAL_TYPES:
            fact["kind"] = "real"
            fact["semantic_category"] = "real"
        elif underlying in _COMPLEX_TYPES:
            fact["kind"] = "complex"
            fact["semantic_category"] = "complex"
        elif underlying == "_Bool":
            fact["kind"] = "bool"
            fact["semantic_category"] = "bool"
        elif underlying == "char":
            fact["kind"] = "integer"
            if isinstance(fact.get("signed"), bool):
                fact["semantic_category"] = "signed_integer" if fact["signed"] else "unsigned_integer"
            else:
                fact["semantic_category"] = "integer_implementation_signedness"
        else:
            fact["semantic_category"] = "implementation_defined"


def probe_c_standard_types(
    config: PreprocessingConfig,
    *,
    runner: Sequence[str] | None = None,
) -> CStandardTypeProbeReport:
    """Compile and execute the standard-type probe for one compiler target.

    The default runner executes the produced binary directly, which is
    appropriate for native builds. Cross-compiled targets must provide a
    runner such as an emulator; the command is recorded in the result.
    """
    _validate_probe_config(config)

    with tempfile.TemporaryDirectory(prefix="prik-c-type-probe-") as temp_dir:
        source_path = Path(temp_dir) / "c_standard_type_probe.c"
        executable_path = Path(temp_dir) / ("c_standard_type_probe.exe" if os.name == "nt" else "c_standard_type_probe")
        source_text = build_c_standard_type_probe_source()
        source_path.write_text(source_text, encoding="utf-8")

        compile_argv = [
            config.compiler,
            "-x",
            "c",
            *_probe_compile_flags(config),
            str(source_path),
            "-o",
            str(executable_path),
        ]
        try:
            compiled = subprocess.run(
                compile_argv,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise CStandardTypeProbeError(f"failed to run C type probe compiler {config.compiler!r}: {exc}") from exc
        if compiled.returncode != 0:
            command = " ".join(shlex.quote(arg) for arg in compile_argv)
            detail = f": {compiled.stderr.strip()}" if compiled.stderr.strip() else ""
            raise CStandardTypeProbeError(f"C standard type probe compilation failed with `{command}`{detail}")

        run_argv = [*(runner or ()), str(executable_path)]
        try:
            completed = subprocess.run(
                run_argv,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise CStandardTypeProbeError(
                "failed to execute C standard type probe; provide a compatible "
                f"runner for cross-compiled targets: {exc}"
            ) from exc
        if completed.returncode != 0:
            command = " ".join(shlex.quote(arg) for arg in run_argv)
            detail = f": {completed.stderr.strip()}" if completed.stderr.strip() else ""
            raise CStandardTypeProbeError(f"C standard type probe execution failed with `{command}`{detail}")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise CStandardTypeProbeError(f"C standard type probe produced invalid JSON: {exc}") from exc

    types = payload.get("types")
    if not isinstance(types, dict):
        raise CStandardTypeProbeError("C standard type probe output is missing 'types'")
    _semantic_type_facts(types)
    return CStandardTypeProbeReport(
        types=types,
        recipe=CStandardTypeProbeRecipe(
            compiler=config.compiler,
            compile_argv=compile_argv,
            run_argv=run_argv,
            requested_standard=config.std,
            include_dirs=list(config.include_dirs),
            defines=list(config.defines),
            undefs=list(config.undefs),
            compiler_args=list(config.compiler_args),
        ),
        source_text=source_text,
    )


def _validate_probe_config(config: PreprocessingConfig) -> None:
    if not config.compiler:
        raise CStandardTypeProbeError("C standard type probing requires an exact compiler executable")
    if config.compile_commands:
        raise CStandardTypeProbeError(
            "C standard type probing does not consume compile_commands directly; "
            "pass the selected target/include/compiler flags explicitly"
        )
    if config.command_template:
        raise CStandardTypeProbeError(
            "C standard type probing does not consume custom preprocessing templates; "
            "pass the selected compiler and target flags explicitly"
        )


def load_c_standard_type_probe_report(path: str | Path) -> CStandardTypeProbeReport:
    """Load and validate a previously generated C ABI probe report."""
    report_path = Path(path)
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CStandardTypeProbeError(f"failed to read C type probe report {report_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CStandardTypeProbeError(f"C type probe report {report_path} contains invalid JSON: {exc}") from exc
    return _report_from_payload(payload, source=str(report_path))


def c_standard_type_probe_cache_key(
    config: PreprocessingConfig,
    *,
    runner: Sequence[str] | None = None,
) -> str:
    """Return the cache key for one exact compiler target and probe schema."""
    source_digest = hashlib.sha256(build_c_standard_type_probe_source().encode()).hexdigest()
    payload = {
        "schema_version": _PROBE_CACHE_SCHEMA_VERSION,
        "source_digest": source_digest,
        "compiler": _compiler_identity(config.compiler),
        "cwd": str(Path.cwd().resolve()),
        "requested_standard": config.std,
        "include_dirs": list(config.include_dirs),
        "defines": list(config.defines),
        "undefs": list(config.undefs),
        "compiler_args": list(config.compiler_args),
        "runner": {
            "argv": list(runner or ()),
            "executable": _compiler_identity(runner[0]) if runner else None,
        },
        "environment": {name: os.environ.get(name) for name in _PROBE_ENVIRONMENT_VARIABLES},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def probe_c_standard_types_cached(
    config: PreprocessingConfig,
    *,
    runner: Sequence[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> CStandardTypeProbeReport:
    """Return compiler ABI facts, reusing memory and persistent cache entries."""
    _validate_probe_config(config)
    cache_key = c_standard_type_probe_cache_key(config, runner=runner)
    if not refresh and cache_key in _MEMORY_CACHE:
        return _MEMORY_CACHE[cache_key]

    cache_path = _probe_cache_dir(cache_dir) / f"{cache_key}.json"
    if not refresh:
        try:
            report = load_c_standard_type_probe_report(cache_path)
        except CStandardTypeProbeError:
            pass
        else:
            _MEMORY_CACHE[cache_key] = report
            return report

    report = probe_c_standard_types(config, runner=runner)
    _MEMORY_CACHE[cache_key] = report
    _write_cached_report(cache_path, report)
    return report


def _report_from_payload(payload: Any, *, source: str) -> CStandardTypeProbeReport:
    if not isinstance(payload, dict):
        raise CStandardTypeProbeError(f"C type probe report {source} must contain a JSON object")
    types = payload.get("types")
    recipe = payload.get("recipe")
    source_text = payload.get("source_text")
    if not isinstance(types, dict) or not all(
        isinstance(name, str) and isinstance(fact, dict) for name, fact in types.items()
    ):
        raise CStandardTypeProbeError(f"C type probe report {source} is missing valid 'types'")
    if not isinstance(recipe, dict) or not isinstance(recipe.get("compiler"), str):
        raise CStandardTypeProbeError(f"C type probe report {source} is missing a valid 'recipe'")
    if not isinstance(source_text, str):
        raise CStandardTypeProbeError(f"C type probe report {source} is missing valid 'source_text'")
    return CStandardTypeProbeReport(
        types=types,
        recipe=CStandardTypeProbeRecipe(
            compiler=recipe["compiler"],
            compile_argv=list(recipe.get("compile_argv") or []),
            run_argv=list(recipe.get("run_argv") or []),
            probe_standard=str(recipe.get("probe_standard") or "c11"),
            requested_standard=recipe.get("requested_standard"),
            include_dirs=list(recipe.get("include_dirs") or []),
            defines=list(recipe.get("defines") or []),
            undefs=list(recipe.get("undefs") or []),
            compiler_args=list(recipe.get("compiler_args") or []),
        ),
        source_text=source_text,
    )


def _compiler_identity(compiler: str | None) -> dict[str, object]:
    if compiler is None:
        return {"command": None}
    resolved = shutil.which(compiler) or compiler
    path = Path(resolved).expanduser().resolve()
    identity: dict[str, object] = {"command": compiler, "path": str(path)}
    try:
        stat = path.stat()
    except OSError:
        return identity
    identity.update({"size": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    return identity


def _probe_cache_dir(cache_dir: str | Path | None) -> Path:
    if cache_dir is not None:
        return Path(cache_dir)
    if root := os.getenv("PRIK_CACHE_DIR"):
        return Path(root) / "c_type_probe"
    if root := os.getenv("XDG_CACHE_HOME"):
        return Path(root) / "prik" / "c_type_probe"
    return Path.home() / ".cache" / "prik" / "c_type_probe"


def _write_cached_report(path: Path, report: CStandardTypeProbeReport) -> None:
    temporary_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        os.replace(temporary_path, path)
    except OSError:
        # A read-only home/cache directory must not make semantic conversion fail.
        pass
    finally:
        with suppress(OSError):
            temporary_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    """Run a compiler-derived C standard type probe and write JSON."""
    parser = argparse.ArgumentParser(
        description="Probe modeled C arithmetic-primitive and standard-type ABI facts through an exact compiler."
    )
    parser.add_argument("--compiler", required=True, help="Exact native or cross C compiler executable.")
    parser.add_argument("-I", "--include-dir", dest="include_dirs", action="append", default=[])
    parser.add_argument("-D", "--define", dest="defines", action="append", default=[])
    parser.add_argument("-U", "--undef", dest="undefs", action="append", default=[])
    parser.add_argument("--std", help="Original project standard recorded as provenance; the probe itself uses C11.")
    parser.add_argument("--compiler-arg", dest="compiler_args", action="append", default=[])
    parser.add_argument(
        "--runner",
        dest="runner",
        action="append",
        default=[],
        help="Runner command item for cross targets; repeat for arguments.",
    )
    parser.add_argument("--cache-dir", help="Directory for reusable compiler ABI probe results.")
    parser.add_argument("--refresh", action="store_true", help="Ignore a reusable ABI probe result and probe again.")
    args = parser.parse_args(argv)
    try:
        for define in args.defines:
            validate_macro_name(define, "--define/-D")
        for undef in args.undefs:
            validate_macro_name(undef, "--undef/-U")
        report = probe_c_standard_types_cached(
            PreprocessingConfig(
                mode="compiler",
                compiler=args.compiler,
                include_dirs=args.include_dirs,
                defines=args.defines,
                undefs=args.undefs,
                std=args.std,
                compiler_args=args.compiler_args,
            ),
            runner=args.runner or None,
            cache_dir=args.cache_dir,
            refresh=args.refresh,
        )
    except (PreprocessingError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report.to_dict(), indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through CLI tests.
    raise SystemExit(main())


__all__ = (
    "CStandardTypeProbeError",
    "CStandardTypeProbeRecipe",
    "CStandardTypeProbeReport",
    "build_c_standard_type_probe_source",
    "c_standard_type_probe_cache_key",
    "load_c_standard_type_probe_report",
    "probe_c_standard_types",
    "probe_c_standard_types_cached",
)
