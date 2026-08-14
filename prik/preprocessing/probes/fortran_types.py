"""Compiler-derived Fortran kind and storage facts.

Fortran kind values and intrinsic expressions such as ``selected_real_kind``
are compiler facts, not parser or semantic-policy decisions. This module
evaluates the exact expressions requested by the semantic layer with the
selected compiler and flags, caches the resulting facts, and returns values
suitable for ``FortranToIRConverter(..., compile_time_values=...)``.

``FortranTypeProbeReport`` is the reusable measurement record.
``evaluate_fortran_type_requirements`` and ``evaluate_fortran_type_facts`` are
the semantic-facing routes; ``probe_fortran_type_expressions_cached`` is the
general cached measurement route. The module proceeds from generated source
and validation through execution, report loading and caching, then semantic
consumer helpers.
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

from prik.preprocessing import PreprocessingConfig, PreprocessingError, validate_macro_name


# Cache identity and generated-source configuration.
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
_SAFE_EXPRESSION_RE = re.compile(r"^[A-Za-z0-9_+\-*/().,= :]+$")
_TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")

_ISO_FORTRAN_ENV_NAMES = {
    "int8",
    "int16",
    "int32",
    "int64",
    "logical_kinds",
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


# Public result records.
class FortranTypeProbeError(ValueError):
    """Report that a compiler-derived Fortran type probe could not complete.

    Callers normally surface this error when the configured compiler cannot
    run, an expression is unsafe to embed in generated source, or a reusable
    report does not contain the facts required for semantic conversion.
    """


@dataclass(frozen=True)
class FortranTypeProbeRecipe:
    """Record the commands and flags that reproduce one probe result.

    Each :class:`FortranTypeProbeReport` includes this record so callers can
    inspect or serialize the exact compiler invocation, runner, expressions,
    and target-relevant preprocessing inputs that produced its values.
    """

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
    """Store JSON-stable compiler facts for semantic conversion or inspection.

    ``values`` maps the exact requested expressions to integer results.
    ``recipe`` captures how those facts were measured, and ``source_text`` is
    the generated program used for the measurement. Pass this report to the
    evaluation functions to reuse already measured expressions.
    """

    values: dict[str, int]
    recipe: FortranTypeProbeRecipe
    source_text: str

    def to_dict(self) -> dict[str, object]:
        """Return a detached JSON-compatible representation of this report.

        Use the returned mapping with :func:`json.dumps` when persisting or
        displaying compiler facts. Nested recipe lists are copied by
        :func:`dataclasses.asdict`.
        """
        return asdict(self)

    def to_compile_time_values(
        self,
        requirements: Iterable[Mapping[str, object]] | None = None,
    ) -> dict[str, int]:
        """Return values in the form consumed by semantic compile-time lookup.

        Exact expression keys are always included. When semantic requirement
        records are supplied, ``parameter_value`` entries also add
        ``symbol -> value`` mappings. Thus ``rk = selected_real_kind(12)``
        resolves both the expression and later uses of ``rk``. The returned
        dictionary is independent of the report.
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


_MEMORY_CACHE: dict[str, FortranTypeProbeReport] = {}


# Requirement collection and generated source.
def fortran_type_probe_expressions(
    requirements: Iterable[Mapping[str, object]],
) -> list[str]:
    """Return ordered, case-insensitively unique expressions from requirements.

    Use this when semantic requirement records need to become probe input. It
    ignores records without an expression and preserves the first spelling of
    each expression so that reports remain readable and deterministic.
    """
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
    """Build free-form Fortran source that prints integer expression results.

    Callers may inspect the returned source or pass it to a compiler. Blank and
    duplicate expressions are removed case-insensitively, and recognized
    ``iso_fortran_env`` and ``iso_c_binding`` names receive the imports needed
    by the standalone generated program. Unsafe expressions raise
    :class:`FortranTypeProbeError` before source is returned.
    """
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


def _normalize_expressions(expressions: Sequence[str]) -> list[str]:
    """Validate, trim, and deduplicate generated-source expressions.

    The input sequence may contain empty strings or equivalent Fortran names
    with different case. The returned list preserves the first non-empty
    spelling of each case-insensitive expression; invalid text raises before
    any source is generated.
    """
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
    """Reject text that cannot safely occupy one parameter declaration.

    ``expression`` is already trimmed by the caller. The probe accepts only a
    single initialization expression from a conservative character set, so it
    cannot introduce another Fortran statement; failures raise
    :class:`FortranTypeProbeError` without mutating state.
    """
    if "\n" in expression or "\r" in expression or ";" in expression:
        raise FortranTypeProbeError(
            f"Fortran type probe expression is not a single initialization expression: {expression!r}"
        )
    if _SAFE_EXPRESSION_RE.fullmatch(expression) is None:
        raise FortranTypeProbeError(f"Fortran type probe expression contains unsupported characters: {expression!r}")


def _probe_import_lines(expressions: Sequence[str]) -> list[str]:
    """Return intrinsic module imports required by the generated expressions.

    The helper scans the normalized expression tokens and emits at most one
    import for each supported intrinsic module. Names are sorted so generated
    source and cache keys stay deterministic.
    """
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
    """Format one intrinsic ``use`` statement within the source line limit.

    ``module`` and the ordered imported ``names`` become either one line or a
    continuation block. The returned lines preserve name order and never alter
    the calling source builder's expression list.
    """
    single_line = f"  use, intrinsic :: {module}, only: {', '.join(names)}"
    if len(single_line) <= 120:
        return [single_line]
    lines = [f"  use, intrinsic :: {module}, only: &"]
    lines.extend(f"    {name}{', &' if index < len(names) - 1 else ''}" for index, name in enumerate(names))
    return lines


# Compiler execution.
def probe_fortran_type_expressions(
    config: PreprocessingConfig,
    expressions: Sequence[str],
    *,
    runner: Sequence[str] | None = None,
) -> FortranTypeProbeReport:
    """Compile and execute a Fortran probe for one compiler target.

    Supply the selected compiler and target-relevant flags in ``config``, plus
    the integer initialization ``expressions`` needed by semantic conversion.
    The default directly executes the generated binary; cross targets pass an
    emulator command through ``runner``. The returned report records the
    generated source and both commands. Compilation, execution, malformed
    output, and unsupported configuration failures raise
    :class:`FortranTypeProbeError`.
    """
    # Prepare validated source before creating any temporary compiler inputs.
    _validate_probe_config(config)
    unique_expressions = _normalize_expressions(expressions)
    source_text = build_fortran_type_probe_source(unique_expressions)

    # Compile and run in an isolated directory that is removed before return.
    with tempfile.TemporaryDirectory(prefix="prik-fortran-type-probe-") as temp_dir:
        source_path = Path(temp_dir) / "fortran_type_probe.F90"
        executable_name = "fortran_type_probe.exe" if os.name == "nt" else "fortran_type_probe"
        executable_path = Path(temp_dir) / executable_name
        source_path.write_text(source_text, encoding="utf-8")
        compile_argv = _compile_fortran_type_probe(config, source_path, executable_path)
        run_argv, output = _run_fortran_type_probe(executable_path, runner)

    # Validate compiler output before exposing it as semantic input.
    values = _probe_values_from_output(output, unique_expressions)
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
    """Ensure ``config`` can describe one standalone compiler probe.

    The probe requires an exact compiler command and reuses only explicit
    target flags. Compile databases and custom preprocessing templates belong
    to source preprocessing, so this helper rejects them with a stable probe
    error and otherwise leaves ``config`` unchanged.
    """
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


def _compile_fortran_type_probe(
    config: PreprocessingConfig,
    source_path: Path,
    executable_path: Path,
) -> list[str]:
    """Compile the generated source and return its exact command.

    ``source_path`` and ``executable_path`` must be inside the active temporary
    directory. The helper carries target-relevant flags from ``config`` into
    the compiler command, raises :class:`FortranTypeProbeError` on launch or
    nonzero-exit failures, and does not retain compiler output on success.
    """
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
        raise FortranTypeProbeError(f"failed to run Fortran type probe compiler {config.compiler!r}: {exc}") from exc
    if compiled.returncode != 0:
        command = " ".join(shlex.quote(arg) for arg in compile_argv)
        detail = f": {compiled.stderr.strip()}" if compiled.stderr.strip() else ""
        raise FortranTypeProbeError(f"Fortran type probe compilation failed with `{command}`{detail}")
    return compile_argv


def _probe_compile_flags(config: PreprocessingConfig) -> list[str]:
    """Return target-relevant compiler flags for the generated probe source.

    The result deliberately mirrors the selected preprocessing inputs without
    attempting source preprocessing itself. It is a new list, leaving the
    configuration lists unmodified for callers and cache-key construction.
    """
    flags = ["-cpp"]
    flags.extend(f"-I{path}" for path in config.include_dirs)
    flags.extend(f"-D{define}" for define in config.defines)
    flags.extend(f"-U{undef}" for undef in config.undefs)
    if config.std:
        flags.append(f"-std={config.std}")
    flags.extend(config.compiler_args)
    return flags


def _run_fortran_type_probe(executable_path: Path, runner: Sequence[str] | None) -> tuple[list[str], str]:
    """Execute one compiled probe and return its command plus standard output.

    ``runner`` prefixes the executable path for cross-compiled targets. On a
    missing runner or executable, or a nonzero program exit, this helper raises
    :class:`FortranTypeProbeError`; on success it preserves the compiler
    program's stdout unchanged for the JSON-validation stage.
    """
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
    return run_argv, completed.stdout


def _probe_values_from_output(output: str, expressions: Sequence[str]) -> dict[str, int]:
    """Parse and validate the generated probe's JSON values.

    ``output`` must encode the list emitted by the generated Fortran program,
    ordered to match normalized ``expressions``. The returned mapping retains
    that expression spelling and order; malformed JSON, count mismatches, and
    non-integer values raise :class:`FortranTypeProbeError`.
    """
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise FortranTypeProbeError(f"Fortran type probe produced invalid JSON: {exc}") from exc

    raw_values = payload.get("values")
    if not isinstance(raw_values, list):
        raise FortranTypeProbeError("Fortran type probe output is missing 'values'")
    if len(raw_values) != len(expressions):
        raise FortranTypeProbeError("Fortran type probe output count does not match input expressions")

    values: dict[str, int] = {}
    for expression, value in zip(expressions, raw_values, strict=False):
        if not isinstance(value, int):
            raise FortranTypeProbeError(f"Fortran type probe value for {expression!r} is not an integer")
        values[expression] = value
    return values


# Report loading and cache management.
def load_fortran_type_probe_report(path: str | Path) -> FortranTypeProbeReport:
    """Load and validate a reusable compiler-derived type report from JSON.

    Pass a report written from :meth:`FortranTypeProbeReport.to_dict` when
    semantic inspection needs an already measured target. Invalid or unreadable
    files raise :class:`FortranTypeProbeError`; successful loads return the
    typed report without probing or changing the cache.
    """
    report_path = Path(path)
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FortranTypeProbeError(f"failed to read Fortran type probe report {report_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise FortranTypeProbeError(f"Fortran type probe report {report_path} contains invalid JSON: {exc}") from exc
    return _report_from_payload(payload, source=str(report_path))


def _report_from_payload(payload: Any, *, source: str) -> FortranTypeProbeReport:
    """Construct a report only from a complete serialized report payload.

    ``source`` labels validation failures for the caller. This helper verifies
    the top-level values, recipe compiler, and generated source, then restores
    optional recipe lists with their existing empty-list defaults.
    """
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


def fortran_type_probe_cache_key(
    config: PreprocessingConfig,
    expressions: Sequence[str],
    *,
    runner: Sequence[str] | None = None,
) -> str:
    """Return the cache key for one exact compiler target and expression set.

    The digest covers normalized generated source, compiler identity,
    target-relevant flags, working directory, selected environment, and runner.
    Use it only to inspect cache identity; callers normally use
    :func:`probe_fortran_type_expressions_cached` to retrieve a report.
    """
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


def _compiler_identity(compiler: str | None) -> dict[str, object]:
    """Describe a compiler or runner command for cache invalidation.

    A configured command resolves through ``PATH`` when possible and records
    its path, size, and modification time if stat succeeds. Missing commands
    remain representable so callers can still form a deterministic key before
    a later probe reports the launch failure.
    """
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


def probe_fortran_type_expressions_cached(
    config: PreprocessingConfig,
    expressions: Sequence[str],
    *,
    runner: Sequence[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> FortranTypeProbeReport:
    """Return compiler facts, reusing matching memory and persistent reports.

    Call this instead of the uncached probe for normal semantic conversion.
    Matching reports are first reused from process memory, then the selected
    cache directory; a miss runs a new probe and writes it back. ``refresh``
    skips both read layers. A read-only cache never prevents a successful probe,
    but invalid cached reports are ignored and measured again.
    """
    _validate_probe_config(config)
    cache_key = fortran_type_probe_cache_key(config, expressions, runner=runner)

    # Reuse the fastest trustworthy result first.
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

    # A cache miss or refresh measures and then offers the new report for reuse.
    report = probe_fortran_type_expressions(config, expressions, runner=runner)
    _MEMORY_CACHE[cache_key] = report
    _write_cached_report(cache_path, report)
    return report


def _probe_cache_dir(cache_dir: str | Path | None) -> Path:
    """Select the persistent cache directory without creating it.

    An explicit ``cache_dir`` wins, followed by ``PRIK_CACHE_DIR`` and
    ``XDG_CACHE_HOME``. The platform-default cache location is returned only
    when no override is present; directory creation is intentionally deferred
    to the write path.
    """
    if cache_dir is not None:
        return Path(cache_dir)
    if root := os.getenv("PRIK_CACHE_DIR"):
        return Path(root) / "fortran_type_probe"
    if root := os.getenv("XDG_CACHE_HOME"):
        return Path(root) / "prik" / "fortran_type_probe"
    return Path.home() / ".cache" / "prik" / "fortran_type_probe"


def _write_cached_report(path: Path, report: FortranTypeProbeReport) -> None:
    """Atomically offer ``report`` to the persistent cache at ``path``.

    The helper creates the parent directory and replaces the final JSON only
    after writing a sibling temporary file. Cache-write failures are suppressed
    so unavailable or read-only cache storage cannot fail semantic conversion;
    a leftover temporary file is removed when possible.
    """
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


# Semantic consumers of measured facts.
def evaluate_fortran_type_requirements(
    config: PreprocessingConfig,
    requirements: Iterable[Mapping[str, object]],
    *,
    report: FortranTypeProbeReport | None = None,
    runner: Sequence[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> dict[str, int]:
    """Resolve semantic compile-time requirements into substitution values.

    Pass semantic requirement records collected from parsed Fortran. If a
    matching ``report`` is supplied it is validated and reused; otherwise this
    function obtains a cached compiler measurement using ``config``. The result
    maps both expressions and eligible parameter symbols to integers, or is
    empty when no expression needs probing.
    """
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
    """Resolve intrinsic storage requirements into semantic type facts.

    Supply the semantic type requirement records that contain a base type,
    optional kind, and storage-size expression. This function reuses a supplied
    report or cached measurement, then returns facts keyed by ``(base_type,
    kind)`` for the Fortran semantic converter. It returns an empty mapping when
    requirements contain no expressions and raises if a supplied report is
    incomplete.
    """
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


def resolve_fortran_logical_storage_types(
    config: PreprocessingConfig,
    storage_bits: Iterable[int],
    *,
    runner: Sequence[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> dict[int, str]:
    """Resolve Boolean storage widths to exact Fortran logical declarations.

    Use this when a language-neutral semantic ``.pyi`` contains ``Bool`` or a
    numbered Boolean contract but no source-language kind spelling.  The
    selected compiler is queried for ``logical_kinds`` and ``c_bool``.  The
    result maps each requested bit width to ``logical(kind=...)``; eight-bit
    ``c_bool`` storage is preferred when it matches.  Unsupported or ambiguous
    widths raise :class:`FortranTypeProbeError` rather than guessing an ABI.

    The probe uses the normal reusable cache and leaves ``config`` and the
    caller's iterable unchanged.
    """
    requested = tuple(sorted({int(bits) for bits in storage_bits}))
    if not requested:
        return {}
    if any(bits <= 0 for bits in requested):
        raise FortranTypeProbeError("Fortran logical storage widths must be positive integers")

    summary = probe_fortran_type_expressions_cached(
        config,
        [
            "size(logical_kinds)",
            "c_bool",
            "storage_size(logical(.false., kind=c_bool))",
        ],
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )
    kind_count = summary.values["size(logical_kinds)"]
    c_bool_kind = summary.values["c_bool"]
    c_bool_bits = summary.values["storage_size(logical(.false., kind=c_bool))"]
    if kind_count <= 0:
        raise FortranTypeProbeError("Fortran compiler reported no supported logical kinds")

    expressions = [
        expression
        for index in range(1, kind_count + 1)
        for expression in (
            f"logical_kinds({index})",
            f"storage_size(logical(.false., kind=logical_kinds({index})))",
        )
    ]
    details = probe_fortran_type_expressions_cached(
        config,
        expressions,
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )
    kinds_by_bits: dict[int, list[int]] = {}
    for index in range(1, kind_count + 1):
        kind = details.values[f"logical_kinds({index})"]
        bits = details.values[f"storage_size(logical(.false., kind=logical_kinds({index})))"]
        kinds_by_bits.setdefault(bits, []).append(kind)

    resolved: dict[int, str] = {}
    for bits in requested:
        candidates = list(dict.fromkeys(kinds_by_bits.get(bits, ())))
        if bits == c_bool_bits and c_bool_kind in candidates:
            resolved[bits] = "logical(kind=c_bool)"
        elif len(candidates) == 1:
            resolved[bits] = f"logical(kind={candidates[0]})"
        elif not candidates:
            raise FortranTypeProbeError(f"Fortran compiler has no logical kind with {bits}-bit storage")
        else:
            candidate_text = ", ".join(str(kind) for kind in candidates)
            raise FortranTypeProbeError(
                f"Fortran compiler has ambiguous logical kinds for {bits}-bit storage: {candidate_text}"
            )
    return resolved


def _report_for_expressions(
    config: PreprocessingConfig,
    expressions: Sequence[str],
    *,
    report: FortranTypeProbeReport | None = None,
    runner: Sequence[str] | None = None,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> FortranTypeProbeReport:
    """Return a report proven to contain every requested expression.

    A caller-supplied ``report`` is checked case-insensitively against the
    normalized expressions and returned unchanged when complete. Without one,
    the helper delegates to the normal cached probe path, preserving its cache
    and refresh behavior. Missing supplied values raise before semantic facts
    are constructed.
    """
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


def _value_for_expression(values: Mapping[str, int], expression: str) -> int | None:
    """Look up an expression value, accepting Fortran's case insensitivity.

    The exact dictionary key is checked first to keep the common path fast.
    Otherwise the helper compares trimmed, lower-cased keys and returns the
    first matching value; it returns ``None`` rather than raising when no fact
    is available.
    """
    exact = values.get(expression)
    if exact is not None:
        return exact
    target = expression.strip().lower()
    for key, value in values.items():
        if key.strip().lower() == target:
            return value
    return None


# Standalone CLI.
def main(argv: list[str] | None = None) -> int:
    """Run the probe CLI and print one report as indented JSON.

    Use this entrypoint from ``python -m prik.preprocessing.probes.fortran_types`` with an
    explicit ``--compiler`` and one or more ``--expr`` arguments. ``argv`` is
    accepted for embedding and tests; otherwise command-line arguments are
    parsed. Invalid macro definitions and probe failures are reported through
    argparse, while success writes the report to standard output and returns
    zero.
    """
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
    "resolve_fortran_logical_storage_types",
)


if __name__ == "__main__":  # pragma: no cover - exercised through CLI tests.
    import sys

    if __spec__ is None and len(sys.argv) == 1:
        compiler = shutil.which("gfortran") or shutil.which("f95")
        if compiler is None:
            raise SystemExit("The direct type-probe example requires gfortran or f95 on PATH.")
        report = probe_fortran_type_expressions(
            PreprocessingConfig(mode="compiler", compiler=compiler),
            ["selected_int_kind(9)"],
        )
        print(f"selected_int_kind(9) = {report.values['selected_int_kind(9)']}")
    else:
        raise SystemExit(main())
