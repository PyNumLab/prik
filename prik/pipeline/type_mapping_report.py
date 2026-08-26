"""Orchestrate target-specific native-to-semantic-to-NumPy reports.

The public functions combine compiler probes, the normal semantic converters,
and codegen's NumPy projection catalogue into one measured record.  This is a
cross-stage inspection pipeline, not a probe implementation or an alternative
datatype conversion path. ``c_type_mapping_report()`` and
``fortran_type_mapping_report()`` are the report boundaries, and every text
format converts one of their records: ``type_mapping_markdown()`` renders the
mapping table and ``expression_probe_markdown()`` renders a measured ``--expr``
probe. Both output formats therefore describe identical measurements.
``main()`` is their standalone command-line adapter.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import asdict
import platform

from prik.codegen.primitive_scalar_types import NumpyDtypeRegistry
from prik.parsers.c.models import (
    CBool,
    CChar,
    CDouble,
    CDoubleComplex,
    CFloat,
    CFloatComplex,
    CInt,
    CLong,
    CLongDouble,
    CLongDoubleComplex,
    CLongLong,
    CShort,
    CSignedChar,
    CTypedef,
    CUnsignedChar,
    CUnsignedInt,
    CUnsignedLong,
    CUnsignedLongLong,
    CUnsignedShort,
)
from prik.parsers.fortran.models import FortranVariable
from prik.semantics.c2ir import CToIRConverter
from prik.semantics.fortran2ir import FortranToIRConverter, fortran_type_storage_expression

from prik.preprocessing import PreprocessingConfig
from prik.preprocessing.probes.c_types import probe_c_standard_types_cached
from prik.preprocessing.probes.fortran_types import (
    FortranTypeProbeReport,
    evaluate_fortran_type_facts,
    probe_fortran_type_expressions_cached,
)


# C report inventory.
_C_TYPES = (
    ("_Bool", CBool()),
    ("char", CChar()),
    ("signed char", CSignedChar()),
    ("unsigned char", CUnsignedChar()),
    ("short", CShort()),
    ("unsigned short", CUnsignedShort()),
    ("int", CInt()),
    ("unsigned int", CUnsignedInt()),
    ("long", CLong()),
    ("unsigned long", CUnsignedLong()),
    ("long long", CLongLong()),
    ("unsigned long long", CUnsignedLongLong()),
    ("float", CFloat()),
    ("double", CDouble()),
    ("long double", CLongDouble()),
    ("float _Complex", CFloatComplex()),
    ("double _Complex", CDoubleComplex()),
    ("long double _Complex", CLongDoubleComplex()),
    ("size_t", CTypedef(name="size_t")),
)


# Fortran report inventory.
def _fortran_type(
    spelling: str,
    base_type: str,
    kind: str | None = None,
    *,
    target_kind_expression: str | None = None,
    character_length_syntax: bool = False,
    declared_storage_bits: int | None = None,
) -> tuple[str, FortranVariable]:
    """Build one report-only Fortran variable and its displayed spelling.

    The helper records metadata that the existing Fortran converter consumes
    when deriving a target type key. It returns the spelling and configured
    variable without mutating any caller-owned object; the private attributes
    intentionally distinguish legacy storage and character-length forms.
    """
    variable = FortranVariable(name="value", base_type=base_type, kind=kind or "")
    if target_kind_expression:
        variable._target_kind_expression = target_kind_expression
    if character_length_syntax:
        variable._character_length_syntax = True
    if declared_storage_bits is not None:
        variable._declared_storage_bits = declared_storage_bits
    return spelling, variable


_FORTRAN_MODERN_TYPES = (
    _fortran_type("integer", "integer"),
    *(_fortran_type(f"integer(kind={kind})", "integer", kind) for kind in ("1", "2", "4", "8")),
    *(_fortran_type(f"integer({kind})", "integer", kind) for kind in ("int8", "int16", "int32", "int64")),
    *(
        _fortran_type(f"integer({kind})", "integer", kind)
        for kind in (
            "c_signed_char",
            "c_short",
            "c_int",
            "c_long",
            "c_long_long",
            "c_size_t",
            "c_int8_t",
            "c_int16_t",
            "c_int32_t",
            "c_int64_t",
        )
    ),
    _fortran_type("real", "real"),
    *(_fortran_type(f"real(kind={kind})", "real", kind) for kind in ("4", "8", "16")),
    *(_fortran_type(f"real({kind})", "real", kind) for kind in ("real32", "real64", "real128")),
    *(_fortran_type(f"real({kind})", "real", kind) for kind in ("c_float", "c_double", "c_long_double")),
    *(_fortran_type(f"real({kind})", "real", kind) for kind in ("kind(1.0e0)", "kind(1.0d0)", "kind(1.0q0)")),
    _fortran_type("complex", "complex"),
    *(_fortran_type(f"complex(kind={kind})", "complex", kind) for kind in ("4", "8", "16")),
    *(_fortran_type(f"complex({kind})", "complex", kind) for kind in ("real32", "real64", "real128")),
    *(
        _fortran_type(f"complex({kind})", "complex", kind)
        for kind in ("c_float_complex", "c_double_complex", "c_long_double_complex")
    ),
    *(
        _fortran_type(f"complex(kind={kind})", "complex", kind)
        for kind in ("kind(1.0e0)", "kind(1.0d0)", "kind(1.0q0)")
    ),
    _fortran_type("logical", "logical"),
    *(_fortran_type(f"logical(kind={kind})", "logical", kind) for kind in ("1", "2", "4", "8")),
    _fortran_type("logical(c_bool)", "logical", "c_bool"),
    _fortran_type("character", "character"),
    _fortran_type("character(len=n)", "character", "n", character_length_syntax=True),
    _fortran_type("character(kind=1)", "character", "kind=1"),
    _fortran_type("character(kind=c_char)", "character", "kind=c_char"),
)

_FORTRAN_LEGACY_TYPES = (
    *(
        _fortran_type(f"integer*{width}", "integer", width, declared_storage_bits=int(width) * 8)
        for width in ("1", "2", "4", "8")
    ),
    *(
        _fortran_type(f"real*{width}", "real", width, declared_storage_bits=int(width) * 8)
        for width in ("4", "8", "16")
    ),
    _fortran_type("double precision", "real", target_kind_expression="kind(1.0d0)"),
    *(
        _fortran_type(f"complex*{width}", "complex", width, declared_storage_bits=int(width) * 8)
        for width in ("8", "16", "32")
    ),
    _fortran_type("double complex", "complex", target_kind_expression="kind(1.0d0)"),
    *(
        _fortran_type(f"logical*{width}", "logical", width, declared_storage_bits=int(width) * 8)
        for width in ("1", "2", "4", "8")
    ),
    _fortran_type("character*1", "character", "1", character_length_syntax=True),
    _fortran_type("character*8", "character", "8", character_length_syntax=True),
    _fortran_type("character*(*)", "character", "*", character_length_syntax=True),
)

_FORTRAN_TYPES = (*_FORTRAN_MODERN_TYPES, *_FORTRAN_LEGACY_TYPES)


def target_profile() -> str:
    """Return the normalized platform label shown at the top of each report.

    Use this value to identify the local Python host named in a rendered table.
    Common AMD64 and ARM64 machine aliases normalize to their conventional
    architecture names; the result is not a compiler target triple and does
    not alter probing.
    """
    machine = platform.machine().lower()
    machine = {"amd64": "x86_64", "arm64": "aarch64"}.get(machine, machine)
    return f"{platform.system().lower()}-{machine}"


def c_type_mapping_report(
    *,
    compiler: str = "cc",
    compiler_args: Sequence[str] = (),
    runner: Sequence[str] | None = None,
    cache_dir: str | None = None,
    refresh: bool = False,
) -> dict[str, object]:
    """Measure the modeled C native-to-semantic-to-NumPy mapping for one target.

    Use this inspection report when documenting or checking how the selected
    compiler represents the supported C primitive and standard-library types.
    Compiler arguments and an optional runner select a native or cross target;
    cache options are forwarded to the existing C ABI probe. The returned
    record contains the target profile and one entry per supported C spelling;
    pass it to :func:`type_mapping_markdown` for the table. Probe and
    semantic-conversion failures propagate to the caller.
    """
    # Measure target ABI facts once for every C spelling in this fixed report.
    report = probe_c_standard_types_cached(
        PreprocessingConfig(mode="compiler", compiler=compiler, compiler_args=list(compiler_args)),
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )

    # Reuse the C semantic converter to project each measured native type.
    converter = CToIRConverter(standard_type_report=report)
    mapping_entries = []
    for spelling, ctype in _C_TYPES:
        semantic_type = converter.visit(ctype, as_type=True)
        fact = report.types[spelling]
        mapping_entries.append(_mapping_entry(spelling, fact, _c_fact_text(fact), semantic_type))

    # Return the measured record; text formats convert it afterwards.
    return _mapping_report("c", mapping_entries, report)


def fortran_type_mapping_report(
    *,
    compiler: str = "gfortran",
    compiler_args: Sequence[str] = (),
    runner: Sequence[str] | None = None,
    cache_dir: str | None = None,
    refresh: bool = False,
) -> dict[str, object]:
    """Measure the supported Fortran native-to-semantic-to-NumPy mapping for one target.

    Use this inspection report to show how the selected compiler and flags map
    the maintained modern and legacy intrinsic spellings. It probes only
    compiler-dependent storage expressions, models fixed legacy storage and
    character code units directly, then returns a measured record for
    :func:`type_mapping_markdown`. Compiler, runner, and cache options use the
    existing Fortran probe path; its failures and semantic-conversion failures
    propagate to the caller.
    """
    # Associate every maintained spelling with its converter key and probe expression.
    key_converter = FortranToIRConverter()
    entries = [
        (
            spelling,
            variable,
            key,
            (
                None
                if variable.declared_storage_bits is not None or key[0] == "character"
                else fortran_type_storage_expression(*key)
            ),
        )
        for spelling, variable in _FORTRAN_TYPES
        for key in [key_converter._target_type_key(variable)]
    ]

    # Measure all compiler-dependent storage expressions in one cached probe.
    expressions = [expression for _spelling, _variable, _key, expression in entries if expression is not None]
    config = PreprocessingConfig(mode="compiler", compiler=compiler, compiler_args=list(compiler_args))
    report = probe_fortran_type_expressions_cached(
        config,
        expressions,
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )

    # Convert probe entries into the storage-fact records accepted by semantic IR.
    requirements = [
        {
            "base_type": key[0],
            "kind": key[1],
            "expression": expression,
        }
        for _spelling, _variable, key, expression in entries
        if expression is not None
    ]
    converter = FortranToIRConverter(type_facts=evaluate_fortran_type_facts(config, requirements, report=report))

    # Convert every displayed spelling with the shared target facts, then record it.
    mapping_entries = []
    for spelling, variable, key, _expression in entries:
        semantic_type = converter.visit(variable)
        fact = _fortran_target_fact(semantic_type, key)
        mapping_entries.append(_mapping_entry(spelling, fact, _fortran_fact_text(fact), semantic_type))
    return _mapping_report("fortran", mapping_entries, report)


def _fortran_target_fact(semantic_type, key: tuple[str, str | None]) -> dict[str, object]:
    """Return one Fortran spelling's measured target-storage record.

    Character entries intentionally bypass compiler metadata because the report
    models their eight-bit code unit directly. Every other entry consumes the
    converter metadata populated from the shared Fortran probe facts.
    """
    if key[0] == "character":
        return {"bits": 8}
    return dict(semantic_type.metadata["fortran_type_fact"])


def _fortran_fact_text(fact: Mapping[str, object]) -> str:
    """Format one measured Fortran storage record for a Markdown table cell."""
    return f"{fact['bits']}-bit storage"


def _c_fact_text(fact: dict[str, object]) -> str:
    """Format one classified C probe fact for a Markdown table cell.

    The helper reads the existing measured and semantic-category fields without
    changing them. Unknown or non-arithmetic fact kinds remain visible instead
    of receiving a report-only fallback classification.
    """
    bits = int(fact.get("bits") or 0)
    if fact.get("kind") == "integer":
        signedness = "signed" if fact.get("signed") else "unsigned"
        return f"{signedness} {bits}-bit"
    if fact.get("kind") == "bool":
        return f"{bits}-bit bool"
    if fact.get("kind") == "real":
        return f"{bits}-bit storage, {fact.get('precision_bits')}-bit precision"
    if fact.get("kind") == "complex":
        return f"{bits}-bit storage"
    return str(fact.get("kind") or "unknown")


def _semantic_text(semantic_type) -> str:
    """Format semantic identity and concrete storage for a report cell.

    Stable semantic names that differ from their target dtype retain both
    pieces of information; matching names render only once. The semantic value
    is read-only and may originate from either language converter.
    """
    if semantic_type.name != semantic_type.dtype:
        return f"{semantic_type.name} ({semantic_type.dtype} storage)"
    return str(semantic_type.dtype)


def _numpy_dtype(semantic_dtype: str | None) -> str:
    """Return the NumPy expression displayed for one semantic dtype.

    Unsupported semantic dtypes render as a stable marker rather than raising
    during documentation generation. String rows retain the distinct ABI-byte
    note because the NumPy string type is not the native character layout.
    """
    try:
        expression = NumpyDtypeRegistry.expression_for(semantic_dtype)
    except KeyError:
        return "unsupported"
    if semantic_dtype == "String":
        return f"{expression} / ABI bytes"
    return expression


def _mapping_entry(
    native: str,
    target_fact: Mapping[str, object],
    native_fact_text: str,
    semantic_type,
) -> dict[str, object]:
    """Build one serializable native-to-semantic-to-NumPy mapping entry.

    ``target_fact`` keeps the structured measurement so JSON consumers read
    numbers rather than parsing prose, while the display fields carry the exact
    strings the Markdown table renders. Semantic identity and NumPy projection
    are read from the converted type so both formats agree by construction.
    """
    return {
        "native": native,
        "target_fact": dict(target_fact),
        "native_fact": native_fact_text,
        "semantic_dtype": _semantic_text(semantic_type),
        "numpy_dtype": _numpy_dtype(semantic_type.dtype),
    }


def _mapping_report(language: str, entries: list[dict[str, object]], probe) -> dict[str, object]:
    """Wrap ordered mapping entries in the serializable report envelope.

    Entries stay in their supported-display order, and ``report`` names the
    record shape so machine consumers can tell a mapping table from a measured
    expression probe without inspecting the payload. The originating probe's
    recipe and generated source travel with the report so a JSON reader can
    reproduce the measurement.
    """
    return {
        "report": "type_mapping",
        "language": language,
        "target_profile": target_profile(),
        "types": entries,
        "recipe": asdict(probe.recipe),
        "source_text": probe.source_text,
    }


_NATIVE_HEADER = {"c": "C type", "fortran": "Fortran type"}


def type_mapping_markdown(report: Mapping[str, object]) -> str:
    """Render one measured type-mapping report as its Markdown table.

    This is the only Markdown path for the mapping report: callers measure with
    :func:`c_type_mapping_report` or :func:`fortran_type_mapping_report` and
    convert the same record here, so the table can never drift from the JSON
    form. Entries render in report order without escaping or reordering.
    """
    native_header = _NATIVE_HEADER[str(report["language"])]
    lines = [
        f"Target profile: `{report['target_profile']}`",
        "",
        f"| {native_header} | Native target fact | Semantic dtype | NumPy dtype |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| `{entry['native']}` | {entry['native_fact']} | `{entry['semantic_dtype']}` | `{entry['numpy_dtype']}` |"
        for entry in report["types"]
    )
    return "\n".join(lines)


def expression_probe_markdown(report: FortranTypeProbeReport) -> str:
    """Render one measured Fortran expression probe as a Markdown table.

    Use this to read a ``--expr`` probe in the same shape as the mapping table.
    Values render in measurement order; the compiler recipe and generated
    program stay in the JSON form, which remains the complete record.
    """
    lines = [
        f"Compiler: `{report.recipe.compiler}`",
        "",
        "| Fortran expression | Measured value |",
        "| --- | --- |",
    ]
    lines.extend(f"| `{expression}` | {value} |" for expression, value in report.values.items())
    return "\n".join(lines)


# Standalone CLI.
def main(argv: list[str] | None = None) -> int:
    """Print one compiler-generated C or Fortran datatype mapping table.

    Use this entrypoint from ``python -m prik.pipeline.type_mapping_report`` with a required
    language and optional compiler, target, runner, and cache settings. Argv is
    accepted for embedding and tests; on success the chosen report is written
    to standard output and zero is returned. Compiler probe and conversion
    failures are intentionally allowed to reach the caller.
    """
    parser = argparse.ArgumentParser(description="Generate a target-specific prik datatype mapping table.")
    parser.add_argument("--language", choices=("c", "fortran"), required=True)
    parser.add_argument("--compiler", help="Exact compiler executable; defaults to cc or gfortran.")
    parser.add_argument("--compiler-arg", dest="compiler_args", action="append", default=[])
    parser.add_argument("--runner", action="append", default=[], help="Runner command item for a cross target.")
    parser.add_argument("--cache-dir", help="Directory for reusable compiler type probe results.")
    parser.add_argument("--refresh", action="store_true", help="Ignore reusable type probe results and probe again.")
    args = parser.parse_args(argv)
    options = {
        "compiler_args": args.compiler_args,
        "runner": args.runner or None,
        "cache_dir": args.cache_dir,
        "refresh": args.refresh,
    }
    if args.language == "c":
        print(type_mapping_markdown(c_type_mapping_report(compiler=args.compiler or "cc", **options)))
    else:
        print(type_mapping_markdown(fortran_type_mapping_report(compiler=args.compiler or "gfortran", **options)))
    return 0


__all__ = (
    "c_type_mapping_report",
    "expression_probe_markdown",
    "fortran_type_mapping_report",
    "target_profile",
    "type_mapping_markdown",
)


if __name__ == "__main__":  # pragma: no cover - exercised through executable documentation.
    import shutil
    import sys
    import tempfile

    if __spec__ is None and len(sys.argv) == 1:
        compiler = shutil.which("cc")
        if compiler is None:
            raise SystemExit("The direct type-mapping example requires cc on PATH.")
        with tempfile.TemporaryDirectory(prefix="prik-type-mapping-example-") as cache_dir:
            markdown = type_mapping_markdown(
                c_type_mapping_report(compiler=compiler, cache_dir=cache_dir, refresh=True)
            )
        print(next(line for line in markdown.splitlines() if line.startswith("| `int` |")))
    else:
        raise SystemExit(main())
