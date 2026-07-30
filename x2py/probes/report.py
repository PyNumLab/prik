"""Generate target-specific native-to-semantic-to-NumPy mapping examples."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import platform

from x2py.parsers.c.models import (
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
from x2py.parsers.fortran.models import FortranVariable
from x2py.semantics.c2ir import CToIRConverter
from x2py.semantics.fortran2ir import FortranToIRConverter, fortran_type_storage_expression

from x2py.pipeline.preprocessing import PreprocessingConfig
from x2py.probes.c_types import probe_c_standard_types_cached
from x2py.probes.fortran_types import evaluate_fortran_type_facts, probe_fortran_type_expressions_cached
from x2py.types.numpy import numpy_dtype_expression


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


def _fortran_type(
    spelling: str,
    base_type: str,
    kind: str | None = None,
    *,
    target_kind_expression: str | None = None,
    character_length_syntax: bool = False,
    declared_storage_bits: int | None = None,
) -> tuple[str, FortranVariable]:
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
    """Return a stable platform label used by architecture-specific docs."""
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
    """Generate the modeled C arithmetic mapping table for one compiler target."""
    report = probe_c_standard_types_cached(
        PreprocessingConfig(mode="compiler", compiler=compiler, compiler_args=list(compiler_args)),
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )
    converter = CToIRConverter(standard_type_report=report)
    rows = []
    for spelling, ctype in _C_TYPES:
        semantic_type = converter.visit(ctype, as_type=True)
        fact = report.types[spelling]
        rows.append((spelling, _c_fact_text(fact), _semantic_text(semantic_type), _numpy_dtype(semantic_type.dtype)))
    return _markdown_table("C type", rows)


def fortran_type_mapping_markdown(
    *,
    compiler: str = "gfortran",
    compiler_args: Sequence[str] = (),
    runner: Sequence[str] | None = None,
    cache_dir: str | None = None,
    refresh: bool = False,
) -> str:
    """Generate the supported Fortran intrinsic mapping table for one target."""
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
    expressions = [expression for _spelling, _variable, _key, expression in entries if expression is not None]
    config = PreprocessingConfig(mode="compiler", compiler=compiler, compiler_args=list(compiler_args))
    report = probe_fortran_type_expressions_cached(
        config,
        expressions,
        runner=runner,
        cache_dir=cache_dir,
        refresh=refresh,
    )
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
    rows = []
    for spelling, variable, _key, _expression in entries:
        semantic_type = converter.visit(variable)
        fact = semantic_type.metadata["fortran_type_fact"]
        rows.append(
            (
                spelling,
                f"{fact['bits']}-bit storage",
                _semantic_text(semantic_type),
                _numpy_dtype(semantic_type.dtype),
            )
        )
    return _markdown_table("Fortran type", rows)


def _c_fact_text(fact: dict[str, object]) -> str:
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
    if semantic_type.name != semantic_type.dtype:
        return f"{semantic_type.name} ({semantic_type.dtype} storage)"
    return str(semantic_type.dtype)


def _numpy_dtype(semantic_dtype: str | None) -> str:
    try:
        expression = numpy_dtype_expression(semantic_dtype)
    except KeyError:
        return "unsupported"
    if semantic_dtype == "String":
        return f"{expression} / ABI bytes"
    return expression


def _markdown_table(native_header: str, rows: list[tuple[str, str, str, str]]) -> str:
    lines = [
        f"Target profile: `{target_profile()}`",
        "",
        f"| {native_header} | Native target fact | Semantic dtype | NumPy dtype |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(f"| `{native}` | {fact} | `{semantic}` | `{numpy}` |" for native, fact, semantic, numpy in rows)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Print one compiler-generated datatype mapping table."""
    parser = argparse.ArgumentParser(description="Generate a target-specific x2py datatype mapping table.")
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


if __name__ == "__main__":  # pragma: no cover - exercised through executable documentation.
    raise SystemExit(main())


__all__ = (
    "c_type_mapping_markdown",
    "fortran_type_mapping_markdown",
    "target_profile",
)
