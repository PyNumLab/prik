"""Orchestrate target-specific native-to-semantic-to-NumPy reports.

The public functions combine compiler probes, the normal semantic converters,
and codegen's NumPy projection catalogue before rendering Markdown.  This is a
cross-stage inspection pipeline, not a probe implementation or an alternative
datatype conversion path. ``c_type_mapping_markdown()`` and
``fortran_type_mapping_markdown()`` are the report boundaries; ``main()`` is
their standalone command-line adapter.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
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
from prik.preprocessing.probes.fortran_types import evaluate_fortran_type_facts, probe_fortran_type_expressions_cached


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


def c_type_mapping_markdown(
    *,
    compiler: str = "cc",
    compiler_args: Sequence[str] = (),
    runner: Sequence[str] | None = None,
    cache_dir: str | None = None,
    refresh: bool = False,
) -> str:
    """Render the modeled C native-to-semantic-to-NumPy mapping for one target.

    Use this inspection report when documenting or checking how the selected
    compiler represents the supported C primitive and standard-library types.
    Compiler arguments and an optional runner select a native or cross target;
    cache options are forwarded to the existing C ABI probe. The returned
    Markdown contains the target profile and one row per supported C spelling.
    Probe and semantic-conversion failures propagate to the caller.
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
    rows = []
    for spelling, ctype in _C_TYPES:
        semantic_type = converter.visit(ctype, as_type=True)
        fact = report.types[spelling]
        rows.append((spelling, _c_fact_text(fact), _semantic_text(semantic_type), _numpy_dtype(semantic_type.dtype)))

    # Render the stable documentation table after all target conversion is complete.
    return _markdown_table("C type", rows)


def fortran_type_mapping_markdown(
    *,
    compiler: str = "gfortran",
    compiler_args: Sequence[str] = (),
    runner: Sequence[str] | None = None,
    cache_dir: str | None = None,
    refresh: bool = False,
) -> str:
    """Render the supported Fortran native-to-semantic-to-NumPy mapping for one target.

    Use this inspection report to show how the selected compiler and flags map
    the maintained modern and legacy intrinsic spellings. It probes only
    compiler-dependent storage expressions, models fixed legacy storage and
    character code units directly, then returns a Markdown table. Compiler,
    runner, and cache options use the existing Fortran probe path; its failures
    and semantic-conversion failures propagate to the caller.
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

    # Convert every displayed spelling with the shared target facts, then render it.
    rows = []
    for spelling, variable, key, _expression in entries:
        semantic_type = converter.visit(variable)
        rows.append(
            (
                spelling,
                _fortran_fact_text(semantic_type, key),
                _semantic_text(semantic_type),
                _numpy_dtype(semantic_type.dtype),
            )
        )
    return _markdown_table("Fortran type", rows)


def _fortran_fact_text(semantic_type, key: tuple[str, str | None]) -> str:
    """Format one Fortran row's target-storage description.

    Character entries intentionally bypass compiler metadata because the report
    models their eight-bit code unit directly. Every other entry consumes the
    converter metadata populated from the shared Fortran probe facts.
    """
    if key[0] == "character":
        return "8-bit storage"
    fact = semantic_type.metadata["fortran_type_fact"]
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


def _markdown_table(native_header: str, rows: list[tuple[str, str, str, str]]) -> str:
    """Render ordered native, target, semantic, and NumPy rows as Markdown.

    Native rows must already be in their supported-display order. The helper
    adds the local target-profile heading and does not escape or reorder row
    content, preserving the generated documentation snapshot format.
    """
    lines = [
        f"Target profile: `{target_profile()}`",
        "",
        f"| {native_header} | Native target fact | Semantic dtype | NumPy dtype |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(f"| `{native}` | {fact} | `{semantic}` | `{numpy}` |" for native, fact, semantic, numpy in rows)
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
        print(c_type_mapping_markdown(compiler=args.compiler or "cc", **options))
    else:
        print(fortran_type_mapping_markdown(compiler=args.compiler or "gfortran", **options))
    return 0


__all__ = (
    "c_type_mapping_markdown",
    "fortran_type_mapping_markdown",
    "target_profile",
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
            markdown = c_type_mapping_markdown(compiler=compiler, cache_dir=cache_dir, refresh=True)
        print(next(line for line in markdown.splitlines() if line.startswith("| `int` |")))
    else:
        raise SystemExit(main())
