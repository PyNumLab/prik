"""Compiler-derived Fortran kind expression facts.

Fortran kind values and intrinsics such as ``selected_real_kind`` are
processor/compiler facts.  This module evaluates the exact initialization
expressions requested by the semantic layer through the user-selected Fortran
compiler and flags, then returns values suitable for
``FortranToIRConverter(..., compile_time_values=...)``.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
from typing import Any

from prik.pipeline.preprocessing import PreprocessingConfig, PreprocessingError, validate_macro_name


class FortranTypeProbeError(ValueError):
    """Raised when a compiler-derived Fortran type probe cannot run."""


@dataclass(frozen=True)
class FortranTypeProbeRecipe:
    """Commands and input flags needed to reproduce one probe result."""

    compiler: str
    compile_argv: list[str]
    run_argv: list[str]
    expressions: list[str]
    requested_standard: str | None = None
    include_dirs: list[str] | None = None
    defines: list[str] | None = None
    undefs: list[str] | None = None
    compiler_args: list[str] | None = None


@dataclass(frozen=True)
class FortranTypeProbeReport:
    """JSON-stable Fortran kind expression values for semantic conversion."""

    values: dict[str, int]
    recipe: FortranTypeProbeRecipe
    source_text: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible report."""
        return asdict(self)

    def to_compile_time_values(
        self,
        requirements: Iterable[Mapping[str, object]] | None = None,
    ) -> dict[str, int]:
        """Return values keyed for semantic compile-time substitution.

        Exact expression keys are always included.  When semantic requirement
        records are supplied, parameter requirements also add ``symbol -> value``
        mappings, so a parameter such as ``rk = selected_real_kind(12)`` resolves
        both ``selected_real_kind(12)`` and later uses of ``rk``.
        """
        values = dict(self.values)
        if requirements is None:
            return values
        for item in requirements:
            expression = str(item.get("expression") or "").strip()
            symbol = str(item.get("symbol") or "").strip()
            if item.get("code") != "parameter_value" or not expression or not symbol:
                continue
            value = _value_for_expression(self.values, expression)
            if value is not None:
                values[symbol] = value
        return values


_PROBE_CACHE_SCHEMA_VERSION = 1
_PROBE_ENVIRONMENT_VARIABLES = (
    "COMPILER_PATH",
    "CPATH",
    "GFORTRAN_UNBUFFERED_ALL",
    "GFORTRAN_UNBUFFERED_PRECONNECTED",
    "GFORTRAN_CONVERT_UNIT",
    "GCC_EXEC_PREFIX",
    "LIB",
    "LIBRARY_PATH",
    "QEMU_LD_PREFIX",
    "SDKROOT",
    "SYSROOT",
)
_MEMORY_CACHE: dict[str, FortranTypeProbeReport] = {}


_SAFE_EXPRESSION_RE = re.compile(r"^[A-Za-z0-9_+\-*/().,= :]+$")
_TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")

_ISO_FORTRAN_ENV_NAMES = {
    "int8",
    "int16",
    "int32",
    "int64",
    "real32",
    "real64",
    "real128",
}
_ISO_C_BINDING_NAMES = {
    "c_bool",
    "c_char",
    "c_double",
    "c_double_complex",
    "c_float",
    "c_float_complex",
    "c_int",
    "c_int16_t",
    "c_int32_t",
    "c_int64_t",
    "c_int8_t",
    "c_long",
    "c_long_double",
    "c_long_double_complex",
    "c_long_long",
    "c_short",
    "c_signed_char",
    "c_size_t",
}


def fortran_type_probe_expressions(
    requirements: Iterable[Mapping[str, object]],
) -> list[str]:
    """Return unique semantic requirement expressions that need probing."""
    expressions: list[str] = []
    seen: set[str] = set()
    for item in requirements:
        expression = str(item.get("expression") or "").strip()
        if not expression:
            continue
        key = expression.lower()
        if key in seen:
            continue
        seen.add(key)
        expressions.append(expression)
    return expressions


def build_fortran_type_probe_source(expressions: Sequence[str]) -> str:
    """Return free-form Fortran source that evaluates integer expressions."""
    unique_expressions = _normalize_expressions(expressions)
    imports = _probe_import_lines(unique_expressions)
    declarations = [
        f"  integer, parameter :: prik_value_{index} = {expression}"
        for index, expression in enumerate(unique_expressions)
    ]

    lines = [
        "program prik_fortran_type_probe",
        *imports,
        "  implicit none",
        *declarations,
        "  write(*,'(A)', advance='no') '{\"values\":['",
    ]
    for index, _expression in enumerate(unique_expressions):
        if index:
            lines.append("  write(*,'(A)', advance='no') ','")
        lines.append(f"  write(*,'(I0)', advance='no') prik_value_{index}")
    lines.extend(
        [
            "  write(*,'(A)') ']}'",
            "end program prik_fortran_type_probe",
            "",
        ]
    )
    return "\n".join(lines)


def probe_fortran_type_expressions(
    config: PreprocessingConfig,
    expressions: Sequence[str],
    *,
    runner: Sequence[str] | None = None,
) -> FortranTypeProbeReport:
    """Compile and execute a Fortran expression probe for one compiler target.

    The default runner executes the produced binary directly, which matches the
    current native-target assumption.  Cross targets can pass an emulator/runner
    command; the command is recorded in the result.
    """
    _validate_probe_config(config)

    unique_expressions = _normalize_expressions(expressions)
    source_text = build_fortran_type_probe_source(unique_expressions)

    with tempfile.TemporaryDirectory(prefix="prik-fortran-type-probe-") as temp_dir:
        source_path = Path(temp_dir) / "fortran_type_probe.F90"
        executable_path = Path(temp_dir) / ("fortran_type_probe.exe" if os.name == "nt" else "fortran_type_probe")
        source_path.write_text(source_text, encoding="utf-8")

        compile_argv = [
            config.compiler,
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
            raise FortranTypeProbeError(
                f"failed to run Fortran type probe compiler {config.compiler!r}: {exc}"
            ) from exc
        if compiled.returncode != 0:
            command = " ".join(shlex.quote(arg) for arg in compile_argv)
            detail = f": {compiled.stderr.strip()}" if compiled.stderr.strip() else ""
            raise FortranTypeProbeError(f"Fortran type probe compilation failed with `{command}`{detail}")

        run_argv = [*(runner or ()), str(executable_path)]
        try:
            completed = subprocess.run(
                run_argv,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise FortranTypeProbeError(
                f"failed to execute Fortran type probe; provide a compatible runner for cross-compiled targets: {exc}"
            ) from exc
        if completed.returncode != 0:
            command = " ".join(shlex.quote(arg) for arg in run_argv)
            detail = f": {completed.stderr.strip()}" if completed.stderr.strip() else ""
            raise FortranTypeProbeError(f"Fortran type probe execution failed with `{command}`{detail}")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise FortranTypeProbeError(f"Fortran type probe produced invalid JSON: {exc}") from exc

    raw_values = payload.get("values")
    if not isinstance(raw_values, list):
        raise FortranTypeProbeError("Fortran type probe output is missing 'values'")
    if len(raw_values) != len(unique_expressions):
        raise FortranTypeProbeError("Fortran type probe output count does not match input expressions")

    values: dict[str, int] = {}
    for expression, value in zip(unique_expressions, raw_values, strict=False):
        if not isinstance(value, int):
            raise FortranTypeProbeError(f"Fortran type probe value for {expression!r} is not an integer")
        values[expression] = value

    return FortranTypeProbeReport(
        values=values,
        recipe=FortranTypeProbeRecipe(
            compiler=config.compiler,
            compile_argv=compile_argv,
            run_argv=run_argv,
            expressions=list(unique_expressions),
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
        raise FortranTypeProbeError("Fortran type probing requires an exact compiler executable")
    if config.compile_commands:
        raise FortranTypeProbeError(
            "Fortran type probing does not consume compile_commands directly; "
            "pass the selected target/include/compiler flags explicitly"
        )
    if config.command_template:
        raise FortranTypeProbeError(
            "Fortran type probing does not consume custom preprocessing templates; "
            "pass the selected compiler and target flags explicitly"
        )


def load_fortran_type_probe_report(path: str | Path) -> FortranTypeProbeReport:
    """Load and validate a reusable compiler-derived Fortran type report."""
    report_path = Path(path)
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FortranTypeProbeError(f"failed to read Fortran type probe report {report_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FortranTypeProbeError(f"Fortran type probe report {report_path} contains invalid JSON: {exc}") from exc
    return _report_from_payload(payload, source=str(report_path))


def fortran_type_probe_cache_key(
    config: PreprocessingConfig,
    expressions: Sequence[str],
    *,
    runner: Sequence[str] | None = None,
) -> str:
    """Return the cache key for one exact compiler target and expression set."""
    normalized = _normalize_expressions(expressions)
    source_digest = hashlib.sha256(build_fortran_type_probe_source(normalized).encode()).hexdigest()
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


def probe_fortran_type_expressions_cached(
    config: PreprocessingConfig,
    expressions: Sequence[str],
    *,
    runner: Sequence[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> FortranTypeProbeReport:
    """Return compiler facts, reusing memory and persistent cache entries."""
    _validate_probe_config(config)
    cache_key = fortran_type_probe_cache_key(config, expressions, runner=runner)
    if not refresh and cache_key in _MEMORY_CACHE:
        return _MEMORY_CACHE[cache_key]

    cache_path = _probe_cache_dir(cache_dir) / f"{cache_key}.json"
    if not refresh:
        try:
            report = load_fortran_type_probe_report(cache_path)
        except FortranTypeProbeError:
            pass
        else:
            _MEMORY_CACHE[cache_key] = report
            return report

    report = probe_fortran_type_expressions(config, expressions, runner=runner)
    _MEMORY_CACHE[cache_key] = report
    _write_cached_report(cache_path, report)
    return report


def _report_for_expressions(
    config: PreprocessingConfig,
    expressions: Sequence[str],
    *,
    report: FortranTypeProbeReport | None = None,
    runner: Sequence[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> FortranTypeProbeReport:
    normalized = _normalize_expressions(expressions)
    if report is not None:
        missing = [expression for expression in normalized if _value_for_expression(report.values, expression) is None]
        if missing:
            raise FortranTypeProbeError(
                "Fortran type probe report is missing required expressions: "
                + ", ".join(repr(item) for item in missing)
            )
        return report
    return probe_fortran_type_expressions_cached(
        config,
        normalized,
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )


def evaluate_fortran_type_requirements(
    config: PreprocessingConfig,
    requirements: Iterable[Mapping[str, object]],
    *,
    report: FortranTypeProbeReport | None = None,
    runner: Sequence[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> dict[str, int]:
    """Evaluate collected semantic requirements into compile-time values."""
    requirement_list = list(requirements)
    expressions = fortran_type_probe_expressions(requirement_list)
    if not expressions:
        return {}
    active_report = _report_for_expressions(
        config,
        expressions,
        report=report,
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )
    return active_report.to_compile_time_values(requirement_list)


def evaluate_fortran_type_facts(
    config: PreprocessingConfig,
    requirements: Iterable[Mapping[str, object]],
    *,
    report: FortranTypeProbeReport | None = None,
    runner: Sequence[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> dict[tuple[str, str | None], dict[str, object]]:
    """Measure storage facts for collected intrinsic Fortran type requirements."""
    requirement_list = list(requirements)
    expressions = [str(item.get("expression") or "").strip() for item in requirement_list]
    expressions = [expression for expression in expressions if expression]
    if not expressions:
        return {}
    active_report = _report_for_expressions(
        config,
        expressions,
        report=report,
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )
    facts: dict[tuple[str, str | None], dict[str, object]] = {}
    for item in requirement_list:
        expression = str(item.get("expression") or "").strip()
        if not expression:
            continue
        value = _value_for_expression(active_report.values, expression)
        if value is None:  # pragma: no cover - guarded by _report_for_expressions.
            raise FortranTypeProbeError(f"Fortran type probe report is missing required expression {expression!r}")
        base_type = str(item.get("base_type") or "").lower()
        raw_kind = item.get("kind")
        kind = None if raw_kind is None else str(raw_kind).lower()
        facts[(base_type, kind)] = {
            "base_type": base_type,
            "kind": kind,
            "bits": value,
            "expression": expression,
        }
    return facts


def _report_from_payload(payload: Any, *, source: str) -> FortranTypeProbeReport:
    if not isinstance(payload, dict):
        raise FortranTypeProbeError(f"Fortran type probe report {source} must contain a JSON object")
    values = payload.get("values")
    recipe = payload.get("recipe")
    source_text = payload.get("source_text")
    if not isinstance(values, dict) or not all(
        isinstance(key, str) and isinstance(value, int) for key, value in values.items()
    ):
        raise FortranTypeProbeError(f"Fortran type probe report {source} is missing valid 'values'")
    if not isinstance(recipe, dict) or not isinstance(recipe.get("compiler"), str):
        raise FortranTypeProbeError(f"Fortran type probe report {source} is missing a valid 'recipe'")
    if not isinstance(source_text, str):
        raise FortranTypeProbeError(f"Fortran type probe report {source} is missing valid 'source_text'")
    return FortranTypeProbeReport(
        values=values,
        recipe=FortranTypeProbeRecipe(
            compiler=recipe["compiler"],
            compile_argv=list(recipe.get("compile_argv") or []),
            run_argv=list(recipe.get("run_argv") or []),
            expressions=list(recipe.get("expressions") or []),
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
        return Path(root) / "fortran_type_probe"
    if root := os.getenv("XDG_CACHE_HOME"):
        return Path(root) / "prik" / "fortran_type_probe"
    return Path.home() / ".cache" / "prik" / "fortran_type_probe"


def _write_cached_report(path: Path, report: FortranTypeProbeReport) -> None:
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


def _normalize_expressions(expressions: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for expression in expressions:
        text = str(expression).strip()
        if not text:
            continue
        _validate_expression(text)
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(text)
    return normalized


def _validate_expression(expression: str) -> None:
    if "\n" in expression or "\r" in expression or ";" in expression:
        raise FortranTypeProbeError(
            f"Fortran type probe expression is not a single initialization expression: {expression!r}"
        )
    if _SAFE_EXPRESSION_RE.fullmatch(expression) is None:
        raise FortranTypeProbeError(f"Fortran type probe expression contains unsupported characters: {expression!r}")


def _probe_import_lines(expressions: Sequence[str]) -> list[str]:
    tokens = {token.lower() for expression in expressions for token in _TOKEN_RE.findall(expression)}
    lines: list[str] = []
    env_names = sorted(tokens & _ISO_FORTRAN_ENV_NAMES)
    c_names = sorted(tokens & _ISO_C_BINDING_NAMES)
    if env_names:
        lines.extend(_probe_import_statement("iso_fortran_env", env_names))
    if c_names:
        lines.extend(_probe_import_statement("iso_c_binding", c_names))
    return lines


def _probe_import_statement(module: str, names: Sequence[str]) -> list[str]:
    single_line = f"  use, intrinsic :: {module}, only: {', '.join(names)}"
    if len(single_line) <= 120:
        return [single_line]
    lines = [f"  use, intrinsic :: {module}, only: &"]
    lines.extend(f"    {name}{', &' if index < len(names) - 1 else ''}" for index, name in enumerate(names))
    return lines


def _probe_compile_flags(config: PreprocessingConfig) -> list[str]:
    """Carry target-relevant compiler flags into the generated probe."""
    flags = ["-cpp"]
    flags.extend(f"-I{path}" for path in config.include_dirs)
    flags.extend(f"-D{define}" for define in config.defines)
    flags.extend(f"-U{undef}" for undef in config.undefs)
    if config.std:
        flags.append(f"-std={config.std}")
    flags.extend(config.compiler_args)
    return flags


def _value_for_expression(values: Mapping[str, int], expression: str) -> int | None:
    exact = values.get(expression)
    if exact is not None:
        return exact
    target = expression.strip().lower()
    for key, value in values.items():
        if key.strip().lower() == target:
            return value
    return None


def main(argv: list[str] | None = None) -> int:
    """Run a compiler-derived Fortran type probe and write JSON."""
    parser = argparse.ArgumentParser(
        description="Probe Fortran kind/compile-time expressions through an exact compiler."
    )
    parser.add_argument("--compiler", required=True, help="Exact native or cross Fortran compiler executable.")
    parser.add_argument(
        "--expr",
        "--expression",
        dest="expressions",
        action="append",
        default=[],
        help="Integer initialization expression to evaluate; repeat for multiple expressions.",
    )
    parser.add_argument("-I", "--include-dir", dest="include_dirs", action="append", default=[])
    parser.add_argument("-D", "--define", dest="defines", action="append", default=[])
    parser.add_argument("-U", "--undef", dest="undefs", action="append", default=[])
    parser.add_argument("--std", help="Project Fortran standard passed to the probe compiler.")
    parser.add_argument("--compiler-arg", dest="compiler_args", action="append", default=[])
    parser.add_argument(
        "--runner",
        dest="runner",
        action="append",
        default=[],
        help="Runner command item for cross targets; repeat for arguments.",
    )
    parser.add_argument("--cache-dir", help="Directory for reusable compiler-derived Fortran type results.")
    parser.add_argument("--refresh", action="store_true", help="Ignore a reusable Fortran type result and probe again.")
    args = parser.parse_args(argv)
    try:
        for define in args.defines:
            validate_macro_name(define, "--define/-D")
        for undef in args.undefs:
            validate_macro_name(undef, "--undef/-U")
        report = probe_fortran_type_expressions_cached(
            PreprocessingConfig(
                mode="compiler",
                compiler=args.compiler,
                include_dirs=args.include_dirs,
                defines=args.defines,
                undefs=args.undefs,
                std=args.std,
                compiler_args=args.compiler_args,
            ),
            args.expressions,
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
    "FortranTypeProbeError",
    "FortranTypeProbeRecipe",
    "FortranTypeProbeReport",
    "build_fortran_type_probe_source",
    "evaluate_fortran_type_facts",
    "evaluate_fortran_type_requirements",
    "fortran_type_probe_cache_key",
    "fortran_type_probe_expressions",
    "load_fortran_type_probe_report",
    "probe_fortran_type_expressions",
    "probe_fortran_type_expressions_cached",
)
