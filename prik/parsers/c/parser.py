"""Partial C parser for wrapper-oriented declaration extraction.

Parsing sketch
==============

The public wrappers call the same orchestration object:

    parse_c_file(...) -> CParser.parse_file(...) -> CFile
    parse_c_project(...) -> CParser.parse_project(...) -> CProject

Recommended reading order for maintainers:

1. Start from the module-level wrappers: `parse_c_file` and `parse_c_project`.
2. Read `CParser.parse_file`, `parse_project`, and `_assemble_project`.
3. Follow `_parse_translation_unit`, which dispatches one top-level C segment.
4. Read the declaration/declarator helpers used by each dispatched segment.
5. Finish with `_build_project` and the index helpers.

`CParser` is organized in that same order:

- public parse entrypoints;
- source locations, diagnostics, macro provenance, and redeclaration merging;
- declaration-specifier and compiler-extension lexical helpers;
- recursive declarator grammar and parameter helpers;
- function and aggregate parsers;
- translation-unit dispatch and project assembly;
- thin module-level wrappers backed by `_DEFAULT_PARSER`.

One source file follows this path:

    source text/path
      -> raw include/pragma metadata, or compiler/preprocessed line mappings
      -> split_top_level_c_source(...) -> CTopLevelSegment objects
      -> _parse_translation_unit(...)
           -> _parse_tag_definition(...) -> _parse_fields(...)
           -> _parse_function(...)
           -> _parse_declaration(...)
      -> _normalize_redeclarations(...)
      -> typed CFile declarations and diagnostics

Declarations share one type-construction path. For example:

    const int *values[4]
      -> _split_declaration_specifiers: ("const int", "*values[4]")
      -> _parse_specifiers: CInt qualified with CConst
      -> _parse_declarator: name "values", array and pointer operations
      -> _apply_declarator_operations: CArray -> CPointer -> CInt

This is why typedefs, variables, function parameters, and aggregate members
obtain types with the same declarator rules. Raw preprocessing accepts include
and pragma metadata only; macro-shaped source requires compiler preprocessing.
Compiler/preprocessed input is parsed by the same route after linemarkers are
mapped back to original source locations.

Executable walkthroughs live in
``tests/c/parsing/test_c_parser_developer_tutorial.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import pairwise
import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

from .lexer import (
    CLogicalRecord,
    CTopLevelSegment,
    lex_c_source,
    line_mappings_for_source,
    normalize_c_source,
    split_top_level_c_source,
    strip_c_comments,
    top_level_partition,
    top_level_split,
    top_level_split_with_offsets,
)
from .models import (
    CArray,
    CAtomic,
    CBool,
    CChar,
    CComposedType,
    CConst,
    CDouble,
    CDoubleComplex,
    CDiagnostic,
    CEnum,
    CEnumerator,
    CFile,
    CFloat,
    CFloatComplex,
    CFunction,
    CFunctionType,
    CParameter,
    CParseError,
    CPointer,
    CProject,
    CRestrict,
    CSourceLocation,
    CShort,
    CSignedChar,
    CStruct,
    CType,
    CTypedef,
    CUnion,
    CUnknownType,
    CUnsignedChar,
    CUnsignedInt,
    CUnsignedLong,
    CUnsignedLongLong,
    CUnsignedShort,
    CVariable,
    CVoid,
    CVolatile,
    CInt,
    CInitializer,
    CLong,
    CLongDouble,
    CLongDoubleComplex,
    CLongLong,
)
from .preprocessor import collect_preprocessor_metadata
from .type_resolver import resolve_project_types

_C_SOURCE_SUFFIXES = {".c", ".h", ".i"}
_IDENTIFIER_RE = re.compile(r"[A-Za-z_]\w*")
_STORAGE_CLASSES = {"typedef", "extern", "static", "register", "_Thread_local"}
_TYPE_QUALIFIERS = {"const", "restrict", "volatile", "_Atomic"}
_FUNCTION_SPECIFIERS = {"inline", "_Noreturn"}
_STORAGE_CLASS_ALIASES = {"_tls": "_Thread_local"}
_COMPILER_KEYWORD_NORMALIZATIONS = {
    "__thread": "_tls",
    "__const": "const",
    "__const__": "const",
    "__restrict": "restrict",
    "__restrict__": "restrict",
    "__volatile": "volatile",
    "__volatile__": "volatile",
    "__inline": "inline",
    "__inline__": "inline",
    "__forceinline": "inline",
    "__signed": "signed",
    "__signed__": "signed",
}
_EXTENDED_SCALAR_NORMALIZATIONS = {
    "__int8": "_xi8",
    "__int16": "_xi16",
    "__int32": "_xi32",
    "__int64": "_xi64",
    "__int128": "_xi128",
    "__int128_t": "_xi128t",
    "__uint128_t": "_xu128t",
    "__fp16": "_xhf16",
    "_Float16": "_xf16",
    "_Float32": "_xf32",
    "_Float32x": "_xf32x",
    "_Float64": "_xf64",
    "_Float64x": "_xf64x",
    "_Float128": "_xf128",
    "_Decimal32": "_xd32",
    "_Decimal64": "_xd64",
    "_Decimal128": "_xd128",
}
_COMPILER_KEYWORD_NORMALIZATIONS.update(_EXTENDED_SCALAR_NORMALIZATIONS)
_EXTENDED_SCALAR_SPELLINGS = {normalized: spelling for spelling, normalized in _EXTENDED_SCALAR_NORMALIZATIONS.items()}
_EXTENDED_SCALAR_WORDS = set(_EXTENDED_SCALAR_SPELLINGS)
_TAG_KINDS = {"struct", "union", "enum"}
_UNSUPPORTED_DECLARATION_MARKERS = (
    "__attribute__",
    "__declspec",
    "[[",
    "_Alignas",
    "alignas",
)
_ALLOWED_RAW_DIRECTIVE_RE = re.compile(r'^\s*#\s*(?:include\s*(?:"[^"]+"|<[^>]+>)|pragma\b)', re.IGNORECASE)
_GNU_ATTRIBUTE_KEYWORDS = {"__attribute", "__attribute__"}
_DECLSPEC_KEYWORDS = {"__declspec", "__declspec__"}
_ASM_KEYWORDS = {"asm", "__asm", "__asm__"}
_TYPEOF_KEYWORDS = {"typeof", "__typeof", "__typeof__"}
_ALIGNMENT_KEYWORDS = {"_Alignas", "alignas"}
_IGNORABLE_EXTENSION_KEYWORDS = {"__extension__"}
_CALLING_CONVENTION_KEYWORDS = {
    "__cdecl",
    "__fastcall",
    "__regcall",
    "__stdcall",
    "__thiscall",
    "__vectorcall",
}
_IGNORABLE_DECLARATION_KEYWORDS = {
    "__w64",
}
_ABI_DECLARATION_KEYWORDS = {
    "__ptr32",
    "__ptr64",
    "__unaligned",
}
_ABI_SIGNIFICANT_ATTRIBUTE_NAMES = {
    "alias",
    "align",
    "aligned",
    "cdecl",
    "fastcall",
    "ifunc",
    "mode",
    "ms_abi",
    "packed",
    "regcall",
    "stdcall",
    "sysv_abi",
    "thiscall",
    "thread",
    "transparent_union",
    "vector_size",
    "vectorcall",
}
_ATTRIBUTE_NAME_RE = re.compile(r"[A-Za-z_]\w*")
_PRIMITIVE_WORDS = {
    "void",
    "char",
    "short",
    "int",
    "long",
    "float",
    "double",
    "signed",
    "unsigned",
    "_Bool",
    "_Complex",
}
_QUALIFIER_CLASSES = {
    "const": CConst,
    "volatile": CVolatile,
    "restrict": CRestrict,
    "_Atomic": CAtomic,
}
_PRIMITIVE_TYPES = {
    "void": CVoid,
    "_Bool": CBool,
    "char": CChar,
    "signed char": CSignedChar,
    "unsigned char": CUnsignedChar,
    "short": CShort,
    "short int": CShort,
    "signed short": CShort,
    "signed short int": CShort,
    "unsigned short": CUnsignedShort,
    "unsigned short int": CUnsignedShort,
    "int": CInt,
    "signed": CInt,
    "signed int": CInt,
    "unsigned": CUnsignedInt,
    "unsigned int": CUnsignedInt,
    "long": CLong,
    "long int": CLong,
    "signed long": CLong,
    "signed long int": CLong,
    "unsigned long": CUnsignedLong,
    "unsigned long int": CUnsignedLong,
    "long long": CLongLong,
    "long long int": CLongLong,
    "signed long long": CLongLong,
    "signed long long int": CLongLong,
    "unsigned long long": CUnsignedLongLong,
    "unsigned long long int": CUnsignedLongLong,
    "float": CFloat,
    "double": CDouble,
    "long double": CLongDouble,
    "float _Complex": CFloatComplex,
    "_Complex": CDoubleComplex,
    "double _Complex": CDoubleComplex,
    "long double _Complex": CLongDoubleComplex,
}
_PRIMITIVE_TYPE_SIGNATURES = {
    tuple(sorted(spelling.split())): type_class for spelling, type_class in _PRIMITIVE_TYPES.items()
}


@dataclass
class _PointerOp:
    """Declarator operation representing one pointer layer."""

    qualifiers: list[str]


@dataclass
class _ArrayOp:
    """Declarator operation representing one array suffix."""

    size: str | None = None
    static: bool = False
    qualifiers: list[str] | None = None
    variable_length: bool = False


@dataclass
class _FunctionOp:
    """Declarator operation representing one function suffix."""

    parameters: list[CParameter]
    variadic: bool = False
    prototype_style: str | None = None


@dataclass
class _ParsedDeclarator:
    """Name plus type-construction operations parsed from a declarator."""

    name: str | None
    operations: list[_PointerOp | _ArrayOp | _FunctionOp]
    source_text: str = ""


@dataclass(frozen=True)
class _UnmodeledCompilerExtension:
    """Ignored compiler syntax whose semantics can matter to generated wrappers."""

    kind: str
    name: str
    offset: int
    message: str


class _UnsupportedDeclaratorSyntax(ValueError):
    """Raised internally when a declarator has unconsumed syntax."""

    pass


class _InvalidSpecifierSequence(ValueError):
    """Raised internally when declaration specifiers are not valid C."""

    pass


class _InvalidCGrammarSyntax(ValueError):
    """Raised internally when a nested C grammar region is malformed."""

    pass


def _looks_like_existing_source_path(value: object) -> bool:
    """Return whether `value` can safely be treated as an existing source path."""
    if isinstance(value, Path):
        return value.is_file()
    if not isinstance(value, str) or not value or "\n" in value:
        return False
    try:
        return Path(value).is_file()
    except OSError:
        return False


def _collect_c_paths(path: Path) -> list[Path]:
    """Collect C source/header files below a directory in stable order."""
    return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in _C_SOURCE_SUFFIXES)


def _posix_key(path: str | Path | PurePosixPath) -> str:
    """Normalize a filesystem-ish path to the project JSON key spelling."""
    return PurePosixPath(str(path)).as_posix()


def _include_key_from_current(current_key: str, target: str) -> str:
    """Resolve an include target key relative to the current file key."""
    current_parent = PurePosixPath(current_key).parent
    if str(current_parent) == ".":
        return _posix_key(target)
    return _posix_key(current_parent / target)


def _is_header_key(key: str) -> bool:
    """Return whether a project key names a C header."""
    return PurePosixPath(key).suffix.lower() == ".h"


def _is_source_key(key: str) -> bool:
    """Return whether a project key names a C source file."""
    return PurePosixPath(key).suffix.lower() == ".c"


class CParser:
    """Parser orchestration object for the partial typed C model.

    The instance carries no parse stack; per-call input and preprocessing
    configuration flow explicitly through `parse_file` and `parse_project`.
    See the module sketch and developer tutorial tests for the helper path.

    Class section map:
    - public file/project parse entrypoints;
    - source-location, diagnostic, macro, and redeclaration helpers;
    - declaration-specifier and compiler-extension helpers;
    - recursive declarator and parameter grammar helpers;
    - function and aggregate parsers;
    - translation-unit dispatch and project assembly.
    """

    # ------------------------------------------------------------------
    # Public parse entrypoints
    # ------------------------------------------------------------------

    def parse_file(
        self,
        source_or_path: str | Path,
        filename: str | None = None,
        *,
        include_dirs: Sequence[str | Path] | None = None,
        preprocessing: str = "raw",
        encoding: str = "utf-8",
    ) -> CFile:
        """Parse one source string/path into a `CFile` parser model.

        The current implementation supports raw preprocessing metadata,
        compiler-fed preprocessed text, and the partial grammar subset
        documented in `docs/c_parser.md`.
        """
        source_path: Path | None = None
        if _looks_like_existing_source_path(source_or_path):
            path = Path(source_or_path)
            source_path = path
            if filename is None:
                filename = str(path)
            source = path.read_text(encoding=encoding)
        else:
            source = str(source_or_path)

        inferred_preprocessed_path = (
            filename if filename is not None and PurePosixPath(filename).suffix.lower() == ".i" else None
        )
        if preprocessing == "raw" and inferred_preprocessed_path is not None:
            preprocessing = "preprocessed"

        parsed = CFile(filename=filename, preprocessing=preprocessing)
        if preprocessing == "raw":
            self._raise_for_raw_preprocessing_directives(source, filename)
            effective_include_dirs = list(include_dirs or ())
            if source_path is not None:
                effective_include_dirs.insert(0, source_path.parent)
            metadata = collect_preprocessor_metadata(
                source,
                filename=filename,
                include_dirs=effective_include_dirs,
            )
            parsed.includes = metadata.includes
            parsed.macros = metadata.macros
            parsed.raw_directives = metadata.raw_directives
            parsed.diagnostics = metadata.diagnostics
            functions, structs, unions, enums, typedefs, variables, parser_diagnostics = self._parse_translation_unit(
                source,
                filename,
                use_linemarkers=False,
                normalize_compiler_extensions=False,
            )
            parsed.functions = functions
            parsed.structs = structs
            parsed.unions = unions
            parsed.enums = enums
            parsed.typedefs = typedefs
            parsed.variables = variables
            parsed.diagnostics.extend(parser_diagnostics)
            self._normalize_redeclarations(parsed)
        elif preprocessing in {"compiler", "preprocessed"}:
            parsed.preprocessed_source_path = inferred_preprocessed_path
            functions, structs, unions, enums, typedefs, variables, parser_diagnostics = self._parse_translation_unit(
                source,
                filename,
                use_linemarkers=True,
                normalize_compiler_extensions=True,
            )
            parsed.functions = functions
            parsed.structs = structs
            parsed.unions = unions
            parsed.enums = enums
            parsed.typedefs = typedefs
            parsed.variables = variables
            parsed.diagnostics.extend(parser_diagnostics)
            self._normalize_redeclarations(parsed)
            self._mark_preprocessed_declarations(parsed)
            parsed.original_source_paths = self._original_source_paths(
                source,
                filename,
                preprocessed_source_path=parsed.preprocessed_source_path,
            )
        else:
            raise ValueError("C preprocessing mode must be 'raw', 'compiler', or 'preprocessed'.")
        return parsed

    @staticmethod
    def _raise_for_raw_preprocessing_directives(source: str, filename: str | None) -> None:
        """Reject raw directives that require a real C preprocessor."""
        normalized = normalize_c_source(source, filename=filename)
        include_guard_lines = CParser._trivial_include_guard_lines(normalized.records)
        for record in normalized.records:
            stripped = record.text.strip()
            if not stripped.startswith("#") or _ALLOWED_RAW_DIRECTIVE_RE.match(stripped):
                continue
            if record.original_start_line in include_guard_lines:
                continue
            source_line = record.source_line
            column = source_line.find("#") + 1 if source_line and "#" in source_line else 1
            raise CParseError(
                "C preprocessing directives require compiler preprocessing before parsing.",
                filename=record.filename,
                line_number=record.original_start_line,
                column=column,
                source_line=source_line,
                code="CPARSE_PREPROCESSING_REQUIRED",
            )

    @staticmethod
    def _trivial_include_guard_lines(records: Sequence[CLogicalRecord]) -> set[int]:
        """Return directive lines for a simple whole-file include guard."""
        directive_records: list[tuple[CLogicalRecord, str, str]] = []
        for record in records:
            stripped = record.text.strip()
            if not stripped.startswith("#"):
                continue
            match = re.match(r"^\s*#\s*(ifndef|define|endif)\b(.*)$", stripped)
            if match is None:
                continue
            directive, argument = match.groups()
            directive_records.append((record, directive.lower(), argument.strip()))

        if len(directive_records) != 3:
            return set()

        (
            (ifndef_record, ifndef_directive, ifndef_name),
            (
                define_record,
                define_directive,
                define_name,
            ),
            (endif_record, endif_directive, endif_argument),
        ) = directive_records
        if ifndef_directive != "ifndef" or define_directive != "define" or endif_directive != "endif":
            return set()
        if not ifndef_name or ifndef_name != define_name or endif_argument:
            return set()
        if ifndef_record.original_start_line > define_record.original_start_line:
            return set()
        if define_record.original_start_line > endif_record.original_start_line:
            return set()
        return {
            ifndef_record.original_start_line,
            define_record.original_start_line,
            endif_record.original_start_line,
        }

    def parse_project(
        self,
        files: Mapping[str, str] | Sequence[str | Path] | str | Path,
        *,
        include_dirs: Sequence[str | Path] | None = None,
        preprocessing: str = "raw",
        encoding: str = "utf-8",
    ) -> CProject:
        """Parse explicit project inputs without recursively parsing includes.

        A directory input explicitly supplies all supported source files below
        that directory. Include directives are recorded and resolved as graph
        facts where possible, but they never cause another file to be opened.
        """
        if isinstance(files, Mapping):
            parsed_files = {
                name: self.parse_file(
                    source,
                    filename=name,
                    include_dirs=include_dirs,
                    preprocessing=preprocessing,
                    encoding=encoding,
                )
                for name, source in files.items()
            }
            return self._assemble_project(parsed_files)

        paths: list[Path] = []
        root: Path | None = None
        if isinstance(files, str | Path):
            path = Path(files)
            if path.is_dir():
                root = path
                paths = _collect_c_paths(path)
            else:
                paths = [path]
        else:
            paths = [Path(p) for p in files]

        parsed_files: dict[str, CFile] = {}
        for path in sorted(paths):
            key = path.name if root is not None else str(path)
            if root is not None:
                key = str(path.relative_to(root))
            parsed_files[key] = self.parse_file(
                path,
                filename=key,
                include_dirs=include_dirs,
                preprocessing=preprocessing,
                encoding=encoding,
            )
        return self._assemble_project(parsed_files)

    def _assemble_project(self, files: Mapping[str, CFile]) -> CProject:
        """Assemble already parsed translation units into one `CProject`.

        This helper is useful when an orchestration layer preprocesses each
        source first and attaches recipe metadata before project resolution.

        Example:
            >>> parser = CParser()
            >>> parsed = parser.parse_file("int answer(void);", filename="api.h")
            >>> project = parser._assemble_project({"api.h": parsed})
            >>> sorted(project.functions)
            ['answer']
        """
        return self._build_project(dict(files))

    # ------------------------------------------------------------------
    # Source locations, diagnostics, and macro provenance
    # ------------------------------------------------------------------

    @staticmethod
    def _mark_preprocessed_declarations(parsed: CFile) -> None:
        """Mark declarations extracted from an externally preprocessed stream."""
        seen_types: set[int] = set()

        def mark_type(type_: CType | None) -> None:
            """Mark one reachable type graph as originating in preprocessed text."""
            if type_ is None:
                return
            if isinstance(type_, CComposedType):
                for component in type_.components:
                    mark_type(component)
                return
            if isinstance(type_, CFunctionType):
                mark_type(type_.result_type)
                for parameter_type in type_.parameter_types:
                    mark_type(parameter_type)
                return
            if isinstance(type_, CStruct | CUnion):
                if id(type_) in seen_types:
                    return
                seen_types.add(id(type_))
                type_.origin = "preprocessed"
                for member in type_.members:
                    mark_variable(member)
                return
            if isinstance(type_, CEnum):
                if id(type_) in seen_types:
                    return
                seen_types.add(id(type_))
                type_.origin = "preprocessed"
                for constant in type_.constants:
                    constant.origin = "preprocessed"
                return
            if isinstance(type_, CTypedef):
                if id(type_) in seen_types:
                    return
                seen_types.add(id(type_))
                type_.origin = "preprocessed"
                mark_type(type_.type)

        def mark_variable(variable: CVariable) -> None:
            """Mark a variable and recursively mark its declared type."""
            variable.origin = "preprocessed"
            mark_type(variable.type)

        for function in parsed.functions:
            function.origin = "preprocessed"
            mark_type(function.result_type)
            for parameter in function.parameters:
                parameter.origin = "preprocessed"
                mark_type(parameter.type)
                mark_type(parameter.declared_type)
        for aggregate in [*parsed.structs, *parsed.unions]:
            mark_type(aggregate)
        for enum in parsed.enums:
            mark_type(enum)
        for typedef in parsed.typedefs:
            typedef.origin = "preprocessed"
            mark_type(typedef.type)
        for variable in parsed.variables:
            mark_variable(variable)

    @staticmethod
    def _original_source_paths(
        source: str,
        filename: str | None,
        *,
        preprocessed_source_path: str | None,
    ) -> list[str]:
        """Collect non-generated source identities referenced by linemarkers."""
        paths: list[str] = []
        for mapping in line_mappings_for_source(source, filename=filename, use_linemarkers=True):
            path = mapping.filename
            if (
                path is None
                or path == preprocessed_source_path
                or (path.startswith("<") and path.endswith(">"))
                or path in paths
            ):
                continue
            paths.append(path)
        return paths

    def _source_location_at(self, segment: CTopLevelSegment, offset: int) -> CSourceLocation:
        """Return the original source location for `offset` inside a segment."""
        prefix = segment.text[:offset]
        line_offset = prefix.count("\n")
        line = segment.original_start_line + line_offset
        filename = segment.filename
        column = len(prefix.rsplit("\n", 1)[-1]) + 1 if line_offset else segment.original_start_column + len(prefix)
        source_line = segment.original_source_line
        if line_offset < len(segment.original_line_numbers):
            line = segment.original_line_numbers[line_offset]
        if line_offset < len(segment.original_filenames):
            filename = segment.original_filenames[line_offset]
        if line_offset and line_offset < len(segment.original_source_lines):
            source_line = segment.original_source_lines[line_offset]
        return CSourceLocation(
            filename=filename,
            line=line,
            column=column,
            source_line=source_line,
        )

    def _source_location(self, segment: CTopLevelSegment) -> CSourceLocation:
        """Return the original start location for a top-level segment."""
        return self._source_location_at(segment, 0)

    @staticmethod
    def _could_start_c_external_declaration(text: str) -> bool:
        """Return whether `text` begins like a C external declaration."""
        stripped = text.lstrip()
        return bool(stripped) and (stripped[0].isalpha() or stripped[0] == "_")

    @staticmethod
    def _raise_for_invalid_top_level_syntax(segment: CTopLevelSegment) -> None:
        """Raise a focused syntax error for a segment that cannot begin C."""
        text = segment.text.strip()
        if not text:
            return
        tokens = lex_c_source(text)
        has_scope_operator = any(left.text == ":" and right.text == ":" for left, right in pairwise(tokens))
        if segment.terminator != "eof" and not has_scope_operator and CParser._could_start_c_external_declaration(text):
            return
        raise CParseError(
            f"Invalid C syntax at top level: {text}",
            filename=segment.filename,
            line_number=segment.original_start_line,
            column=segment.original_start_column,
            source_line=segment.original_source_line,
            code="CPARSE_INVALID_SYNTAX",
        )

    def _invalid_syntax_error(
        self,
        segment: CTopLevelSegment,
        text: str,
        *,
        context: str,
        offset: int = 0,
    ) -> CParseError:
        """Build the fatal diagnostic used when a C grammar region is invalid."""
        location = self._source_location_at(segment, offset)
        return CParseError(
            f"Invalid C syntax in {context}: {text.strip()}",
            filename=location.filename,
            line_number=location.line,
            column=location.column,
            source_line=location.source_line,
            code="CPARSE_INVALID_SYNTAX",
        )

    def _has_unsupported_declaration_marker(self, text: str) -> bool:
        """Return whether `text` contains a known unsupported declaration marker."""
        return any(marker in text for marker in _UNSUPPORTED_DECLARATION_MARKERS)

    def _redeclaration_diagnostic(
        self,
        code: str,
        message: str,
        location: CSourceLocation | None,
        unit_kind: str,
        unit_name: str | None,
    ) -> CDiagnostic:
        """Build a normalized redeclaration/conflict diagnostic."""
        return CDiagnostic(
            code=code,
            message=message,
            severity="error",
            location=location,
            unit_kind=unit_kind,
            unit_name=unit_name,
        )

    def _append_declaration_location(
        self,
        locations: list[CSourceLocation],
        location: CSourceLocation | None,
    ) -> None:
        """Append a declaration location once, preserving encounter order."""
        if location is not None and location not in locations:
            locations.append(location)

    # ------------------------------------------------------------------
    # Redeclaration compatibility and normalization
    # ------------------------------------------------------------------

    def _type_key(self, type_: CType, seen: set[int] | None = None) -> tuple:
        """Return a cycle-safe structural key used for type compatibility."""
        if seen is None:
            seen = set()
        object_id = id(type_)
        if object_id in seen:
            return ("cycle", type(type_).__name__, getattr(type_, "reference_name", None))
        seen.add(object_id)

        qualifiers = tuple(qualifier.spelling for qualifier in type_.qualifiers)
        if isinstance(type_, CComposedType):
            return (
                "CComposedType",
                tuple(self._type_key(component, seen) for component in type_.components),
                qualifiers,
            )
        if isinstance(type_, CFunctionType):
            return (
                "CFunctionType",
                self._type_key(type_.result_type, seen),
                tuple(self._type_key(parameter_type, seen) for parameter_type in type_.parameter_types),
                type_.is_variadic,
                qualifiers,
            )
        if isinstance(type_, CPointer):
            return ("CPointer", qualifiers)
        if isinstance(type_, CArray):
            return (
                "CArray",
                type_.bound,
                type_.is_static_minimum,
                type_.is_variable_length,
                type_.is_flexible,
                qualifiers,
            )
        if isinstance(type_, CTypedef):
            if type_.type is not None:
                return ("CTypedef", self._type_key(type_.type, seen), qualifiers)
            return ("CTypedef", type_.name, qualifiers)
        if isinstance(type_, CStruct):
            return ("CStruct", type_.name, type_.anonymous_id, qualifiers)
        if isinstance(type_, CUnion):
            return ("CUnion", type_.name, type_.anonymous_id, qualifiers)
        if isinstance(type_, CEnum):
            return ("CEnum", type_.name, type_.anonymous_id, qualifiers)
        return (type(type_).__name__, qualifiers)

    def _types_compatible(self, left: CType, right: CType) -> bool:
        """Return whether two parser type models are structurally compatible."""
        return self._type_key(left) == self._type_key(right)

    def _unspecified_function_declaration(self, function: CFunction) -> bool:
        """Return whether `function` is an old C empty-parameter declaration."""
        return function.prototype_style == "unspecified" and not function.parameters

    def _functions_compatible(self, left: CFunction, right: CFunction) -> bool:
        """Return whether two function declarations can denote one function."""
        if not self._types_compatible(left.result_type, right.result_type):
            return False
        if self._unspecified_function_declaration(left) or self._unspecified_function_declaration(right):
            return True
        if left.is_variadic != right.is_variadic or len(left.parameters) != len(right.parameters):
            return False
        return all(
            self._types_compatible(left_param.type, right_param.type)
            for left_param, right_param in zip(left.parameters, right.parameters, strict=False)
        )

    def _merge_function_declaration(
        self,
        existing: CFunction,
        incoming: CFunction,
    ) -> CFunction:
        """Merge compatible function declarations, preferring definitions."""
        if incoming.is_definition and not existing.is_definition:
            merged = incoming
            for location in existing.declaration_locations:
                self._append_declaration_location(merged.declaration_locations, location)
            self._append_declaration_location(merged.declaration_locations, existing.source_location)
            return merged

        for location in incoming.declaration_locations:
            self._append_declaration_location(existing.declaration_locations, location)
        self._append_declaration_location(existing.declaration_locations, incoming.source_location)
        return existing

    def _deduplicate_functions(
        self,
        functions: list[CFunction],
        diagnostics: list[CDiagnostic],
    ) -> list[CFunction]:
        """Merge compatible functions and report duplicate/conflicting ones."""
        normalized: list[CFunction] = []

        for function in functions:
            overlapping = [index for index, existing in enumerate(normalized) if existing.name == function.name]
            if not overlapping:
                normalized.append(function)
                continue

            for index in overlapping:
                existing = normalized[index]
                if not self._functions_compatible(existing, function):
                    diagnostics.append(
                        self._redeclaration_diagnostic(
                            "C_CONFLICTING_FUNCTION_DECLARATION",
                            f"Conflicting declarations for function {function.name!r}.",
                            function.source_location,
                            "function",
                            function.name,
                        )
                    )
                    continue

                if existing.is_definition and function.is_definition:
                    diagnostics.append(
                        self._redeclaration_diagnostic(
                            "C_DUPLICATE_FUNCTION_DEFINITION",
                            f"Duplicate definition for function {function.name!r}.",
                            function.source_location,
                            "function",
                            function.name,
                        )
                    )
                    continue

                normalized[index] = self._merge_function_declaration(existing, function)

        return normalized

    def _is_variable_definition(self, variable: CVariable) -> bool:
        """Return whether a file-scope variable has an initializer."""
        return variable.initializer is not None

    def _merge_variable_declaration(
        self,
        existing: CVariable,
        incoming: CVariable,
    ) -> CVariable:
        """Merge compatible file-scope variable declarations."""
        if self._is_variable_definition(incoming) and not self._is_variable_definition(existing):
            merged = incoming
            for location in existing.declaration_locations:
                self._append_declaration_location(merged.declaration_locations, location)
            self._append_declaration_location(merged.declaration_locations, existing.source_location)
            return merged

        for location in incoming.declaration_locations:
            self._append_declaration_location(existing.declaration_locations, location)
        self._append_declaration_location(existing.declaration_locations, incoming.source_location)
        return existing

    def _deduplicate_variables(
        self,
        variables: list[CVariable],
        diagnostics: list[CDiagnostic],
    ) -> list[CVariable]:
        """Merge tentative variables and report duplicate/conflicting definitions."""
        by_name: dict[str, CVariable] = {}
        order: list[str] = []

        for variable in variables:
            if variable.name is None:
                continue
            existing = by_name.get(variable.name)
            if existing is None:
                by_name[variable.name] = variable
                order.append(variable.name)
                continue

            if not self._types_compatible(existing.type, variable.type):
                diagnostics.append(
                    self._redeclaration_diagnostic(
                        "C_CONFLICTING_VARIABLE_DECLARATION",
                        f"Conflicting declarations for variable {variable.name!r}.",
                        variable.source_location,
                        "variable",
                        variable.name,
                    )
                )
                continue

            if self._is_variable_definition(existing) and self._is_variable_definition(variable):
                diagnostics.append(
                    self._redeclaration_diagnostic(
                        "C_DUPLICATE_VARIABLE_DEFINITION",
                        f"Duplicate definition for variable {variable.name!r}.",
                        variable.source_location,
                        "variable",
                        variable.name,
                    )
                )
                continue

            by_name[variable.name] = self._merge_variable_declaration(existing, variable)

        return [by_name[name] for name in order]

    def _deduplicate_typedefs(
        self,
        typedefs: list[CTypedef],
        diagnostics: list[CDiagnostic],
    ) -> list[CTypedef]:
        """Merge repeated compatible typedefs and report conflicts."""
        by_name: dict[str, CTypedef] = {}
        order: list[str] = []

        for typedef in typedefs:
            existing = by_name.get(typedef.name)
            if existing is None:
                by_name[typedef.name] = typedef
                order.append(typedef.name)
                continue

            if existing.type is None or typedef.type is None or not self._types_compatible(existing.type, typedef.type):
                diagnostics.append(
                    self._redeclaration_diagnostic(
                        "C_CONFLICTING_TYPEDEF",
                        f"Conflicting typedef declarations for {typedef.name!r}.",
                        typedef.source_location,
                        "typedef",
                        typedef.name,
                    )
                )
                continue

            for location in typedef.declaration_locations:
                self._append_declaration_location(existing.declaration_locations, location)
            self._append_declaration_location(existing.declaration_locations, typedef.source_location)

        return [by_name[name] for name in order]

    def _deduplicate_structs(
        self,
        structs: list[CStruct],
        diagnostics: list[CDiagnostic],
    ) -> list[CStruct]:
        """Merge incomplete/complete struct tags and report duplicate definitions."""
        by_name: dict[str, CStruct] = {}
        ordered: list[CStruct] = []

        for struct in structs:
            if struct.name is None:
                ordered.append(struct)
                continue
            existing = by_name.get(struct.name)
            if existing is None:
                by_name[struct.name] = struct
                ordered.append(struct)
                continue
            if existing.is_incomplete and not struct.is_incomplete:
                index = ordered.index(existing)
                ordered[index] = struct
                by_name[struct.name] = struct
                continue
            if not existing.is_incomplete and not struct.is_incomplete:
                diagnostics.append(
                    self._redeclaration_diagnostic(
                        "C_DUPLICATE_TAG_DEFINITION",
                        f"Duplicate definition for struct tag {struct.name!r}.",
                        struct.source_location,
                        "struct",
                        struct.name,
                    )
                )
        return ordered

    def _deduplicate_unions(
        self,
        unions: list[CUnion],
        diagnostics: list[CDiagnostic],
    ) -> list[CUnion]:
        """Merge incomplete/complete union tags and report duplicate definitions."""
        by_name: dict[str, CUnion] = {}
        ordered: list[CUnion] = []

        for union in unions:
            if union.name is None:
                ordered.append(union)
                continue
            existing = by_name.get(union.name)
            if existing is None:
                by_name[union.name] = union
                ordered.append(union)
                continue
            if existing.is_incomplete and not union.is_incomplete:
                index = ordered.index(existing)
                ordered[index] = union
                by_name[union.name] = union
                continue
            if not existing.is_incomplete and not union.is_incomplete:
                diagnostics.append(
                    self._redeclaration_diagnostic(
                        "C_DUPLICATE_TAG_DEFINITION",
                        f"Duplicate definition for union tag {union.name!r}.",
                        union.source_location,
                        "union",
                        union.name,
                    )
                )
        return ordered

    def _deduplicate_enums(
        self,
        enums: list[CEnum],
        diagnostics: list[CDiagnostic],
    ) -> list[CEnum]:
        """Report duplicate enum definitions while preserving first definitions."""
        by_name: dict[str, CEnum] = {}
        ordered: list[CEnum] = []

        for enum in enums:
            if enum.name is None:
                ordered.append(enum)
                continue
            existing = by_name.get(enum.name)
            if existing is None:
                by_name[enum.name] = enum
                ordered.append(enum)
                continue
            diagnostics.append(
                self._redeclaration_diagnostic(
                    "C_DUPLICATE_TAG_DEFINITION",
                    f"Duplicate definition for enum tag {enum.name!r}.",
                    enum.source_location,
                    "enum",
                    enum.name,
                )
            )
        return ordered

    def _normalize_redeclarations(self, parsed: CFile) -> None:
        """Normalize top-level redeclarations in one parsed file in place."""
        parsed.structs = self._deduplicate_structs(parsed.structs, parsed.diagnostics)
        parsed.unions = self._deduplicate_unions(parsed.unions, parsed.diagnostics)
        parsed.enums = self._deduplicate_enums(parsed.enums, parsed.diagnostics)
        parsed.typedefs = self._deduplicate_typedefs(parsed.typedefs, parsed.diagnostics)
        parsed.variables = self._deduplicate_variables(parsed.variables, parsed.diagnostics)
        parsed.functions = self._deduplicate_functions(parsed.functions, parsed.diagnostics)

    def _end_location(self, segment: CTopLevelSegment) -> CSourceLocation:
        """Return the original end location for a top-level segment."""
        filename = segment.original_filenames[-1] if segment.original_filenames else segment.filename
        return CSourceLocation(
            filename=filename,
            line=segment.original_end_line,
            column=segment.original_end_column,
            source_line=segment.original_end_source_line,
        )

    # ------------------------------------------------------------------
    # Declaration specifiers and lexical helper primitives
    # ------------------------------------------------------------------

    def _last_identifier(self, text: str) -> re.Match[str] | None:
        """Return the last identifier in `text`, ignoring bracket contents."""
        bracket_depth = 0
        allowed_spans: list[tuple[int, int]] = []
        span_start = 0
        for index, char in enumerate(text):
            if char == "[":
                if bracket_depth == 0 and span_start < index:
                    allowed_spans.append((span_start, index))
                bracket_depth += 1
            elif char == "]" and bracket_depth:
                bracket_depth -= 1
                if bracket_depth == 0:
                    span_start = index + 1
        if bracket_depth == 0 and span_start < len(text):
            allowed_spans.append((span_start, len(text)))

        matches: list[re.Match[str]] = []
        for start, end in allowed_spans:
            matches.extend(_IDENTIFIER_RE.finditer(text, start, end))
        return matches[-1] if matches else None

    def _specifier_words(self, spec_text: str) -> list[str]:
        """Extract identifier-like words from a declaration-specifier prefix."""
        return _IDENTIFIER_RE.findall(spec_text)

    def _qualifiers(self, spellings: list[str]) -> list:
        """Instantiate qualifier model objects from qualifier spellings."""
        return [_QUALIFIER_CLASSES[spelling]() for spelling in spellings]

    def _invalid_specifier_error(
        self,
        segment: CTopLevelSegment,
        message: str,
        *,
        offset: int = 0,
    ) -> CParseError:
        """Build the fatal diagnostic used for invalid specifier sequences."""
        location = self._source_location_at(segment, offset)
        return CParseError(
            message,
            filename=location.filename,
            line_number=location.line,
            column=location.column,
            source_line=location.source_line,
            code="CPARSE_INVALID_SPECIFIER_SEQUENCE",
        )

    def _atomic_type_specifier_parts(self, spec_text: str) -> tuple[str, str] | None:
        """Return surrounding specifiers and the type-name inside `_Atomic(...)`."""
        for match in _IDENTIFIER_RE.finditer(spec_text):
            if match.group(0) != "_Atomic":
                continue
            open_index = self._skip_whitespace(spec_text, match.end())
            if open_index >= len(spec_text) or spec_text[open_index] != "(":
                continue
            close_index = self._find_matching_delimiter(spec_text, open_index, "(", ")")
            if close_index is None:
                return None
            surrounding = " ".join(
                part
                for part in (
                    spec_text[: match.start()].strip(),
                    spec_text[close_index + 1 :].strip(),
                )
                if part
            )
            return surrounding, spec_text[open_index + 1 : close_index].strip()
        return None

    def _add_outermost_qualifiers(self, type_: CType, qualifiers: list) -> None:
        """Attach qualifiers to the object denoted by an assembled type."""
        if isinstance(type_, CComposedType) and type_.components:
            type_.components[0].qualifiers.extend(qualifiers)
        else:
            type_.qualifiers.extend(qualifiers)

    def _parse_specifiers(self, spec_text: str) -> tuple[CType, list[str], list[str]]:
        """Parse C declaration specifiers into base type and specifier lists."""
        atomic_specifier = self._atomic_type_specifier_parts(spec_text)
        outer_spec_text = atomic_specifier[0] if atomic_specifier is not None else spec_text
        words = self._specifier_words(outer_spec_text)
        storage: list[str] = []
        qualifiers: list[str] = []
        function_specifiers: list[str] = []
        type_words: list[str] = []

        for raw_word in words:
            word = self._canonical_primitive_word(raw_word)
            storage_class = self._canonical_storage_class(word)
            qualifier = self._canonical_type_qualifier(word)
            function_specifier = self._canonical_function_specifier(word)
            if storage_class is not None:
                storage.append(storage_class)
            elif qualifier is not None:
                qualifiers.append(qualifier)
            elif function_specifier is not None:
                function_specifiers.append(function_specifier)
            else:
                type_words.append(word)

        if atomic_specifier is not None:
            if type_words:
                raise _InvalidSpecifierSequence(f"Invalid type specifier sequence {spec_text.strip()!r}.")
            inner_text = atomic_specifier[1]
            inner_spec_text, inner_declarator = self._split_declaration_specifiers(inner_text)
            if not inner_spec_text:
                raise _InvalidSpecifierSequence(f"Invalid _Atomic type-name {inner_text!r}.")
            name, type_, inner_storage, inner_function_specifiers, _direct_function = self._build_declared_type(
                inner_spec_text, inner_declarator
            )
            if name is not None or inner_storage or inner_function_specifiers:
                raise _InvalidSpecifierSequence(f"Invalid _Atomic type-name {inner_text!r}.")
            self._add_outermost_qualifiers(
                type_,
                [CAtomic(), *self._qualifiers(qualifiers)],
            )
        elif type_words and type_words[0] in _TAG_KINDS:
            tag_name = type_words[1] if len(type_words) > 1 else None
            tag_type = {"struct": CStruct, "union": CUnion, "enum": CEnum}[type_words[0]]
            tag_kwargs = {
                "name": tag_name,
                "qualifiers": self._qualifiers(qualifiers),
                "source_text": " ".join([*qualifiers, *type_words]),
            }
            if tag_type in {CStruct, CUnion}:
                tag_kwargs["is_incomplete"] = True
            type_: CType = tag_type(**tag_kwargs)
        elif type_words:
            displayed_type_words = [_EXTENDED_SCALAR_SPELLINGS.get(word, word) for word in type_words]
            spelling = " ".join(displayed_type_words)
            primitive = _PRIMITIVE_TYPE_SIGNATURES.get(tuple(sorted(type_words)))
            if primitive is not None:
                type_ = primitive(
                    qualifiers=self._qualifiers(qualifiers),
                    source_text=" ".join([*qualifiers, *type_words]),
                )
            elif sum(word in _EXTENDED_SCALAR_WORDS for word in type_words) == 1 and all(
                word in _EXTENDED_SCALAR_WORDS | {"signed", "unsigned", "_Complex"} for word in type_words
            ):
                type_ = CUnknownType(
                    spelling=spelling,
                    qualifiers=self._qualifiers(qualifiers),
                    source_text=" ".join([*qualifiers, *displayed_type_words]),
                )
            elif len(type_words) == 1 and type_words[0] not in _PRIMITIVE_WORDS:
                type_ = CTypedef(
                    name=type_words[0],
                    qualifiers=self._qualifiers(qualifiers),
                    source_text=" ".join([*qualifiers, *type_words]),
                )
            else:
                raise _InvalidSpecifierSequence(f"Invalid type specifier sequence {spelling!r}.")
        else:
            type_ = CUnknownType(
                qualifiers=self._qualifiers(qualifiers),
                source_text=spec_text.strip(),
            )

        return type_, storage, function_specifiers

    def _skip_whitespace(self, text: str, index: int) -> int:
        """Advance `index` past ASCII/Unicode whitespace."""
        while index < len(text) and text[index].isspace():
            index += 1
        return index

    def _read_identifier(self, text: str, index: int) -> tuple[str, int] | None:
        """Read one C identifier at `index` and return `(name, end)`."""
        if index >= len(text):
            return None
        first = text[index]
        if not (first == "_" or first.isalpha()):
            return None
        end = index + 1
        while end < len(text) and (text[end] == "_" or text[end].isalnum()):
            end += 1
        return text[index:end], end

    @staticmethod
    def _canonical_storage_class(word: str) -> str | None:
        """Return the standard spelling for a recognized storage class."""
        if word in _STORAGE_CLASSES:
            return word
        return _STORAGE_CLASS_ALIASES.get(word)

    @staticmethod
    def _canonical_type_qualifier(word: str) -> str | None:
        """Return the standard spelling for a recognized type qualifier."""
        return word if word in _TYPE_QUALIFIERS else None

    @staticmethod
    def _canonical_function_specifier(word: str) -> str | None:
        """Return the standard spelling for a recognized function specifier."""
        return word if word in _FUNCTION_SPECIFIERS else None

    @staticmethod
    def _canonical_primitive_word(word: str) -> str:
        """Normalize alternate compiler spellings for primitive type words."""
        return word

    @staticmethod
    def _blank_span(characters: list[str], start: int, end: int) -> None:
        """Blank one syntax span while retaining line and column accounting."""
        for index in range(start, end):
            if characters[index] != "\n":
                characters[index] = " "

    @staticmethod
    def _replace_span(characters: list[str], start: int, end: int, replacement: str) -> None:
        """Replace a syntax span with a short token and pad the remaining width."""
        writable = [index for index in range(start, end) if characters[index] != "\n"]
        if len(replacement) > len(writable):
            replacement = "_T"
        for index, char in zip(writable, replacement, strict=False):
            characters[index] = char
        for index in writable[len(replacement) :]:
            characters[index] = " "

    @staticmethod
    def _significant_attribute_names(payload: str) -> list[str]:
        """Return ABI- or linkage-relevant attribute names from one payload."""
        names: list[str] = []
        for raw_name in _ATTRIBUTE_NAME_RE.findall(payload):
            name = raw_name.strip("_")
            if name in _ABI_SIGNIFICANT_ATTRIBUTE_NAMES and name not in names:
                names.append(name)
        return names

    def _attribute_extension_facts(
        self,
        payload: str,
        *,
        offset: int,
    ) -> list[_UnmodeledCompilerExtension]:
        """Describe ignored attributes whose semantics remain wrapper-relevant."""
        return [
            _UnmodeledCompilerExtension(
                kind="compiler_attribute",
                name=name,
                offset=offset,
                message=(
                    f"Compiler attribute {name!r} was accepted for parsing but "
                    "its ABI or linkage semantics are not modeled."
                ),
            )
            for name in self._significant_attribute_names(payload)
        ]

    @staticmethod
    def _find_double_bracket_end(text: str, start: int) -> int | None:
        """Return the end offset after one C23/C++-style `[[...]]` attribute."""
        index = start + 2
        quote = ""
        escaped = False
        while index < len(text) - 1:
            char = text[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = ""
                index += 1
                continue
            if char in {'"', "'"}:
                quote = char
                index += 1
                continue
            if text[index : index + 2] == "]]":
                return index + 2
            index += 1
        return None

    def _compiler_extension_invocation_end(self, text: str, start: int) -> int:
        """Return the end of a keyword's optional balanced parenthesized payload."""
        open_index = self._skip_whitespace(text, start)
        if open_index >= len(text) or text[open_index] != "(":
            return start
        close_index = self._find_matching_delimiter(text, open_index, "(", ")")
        return close_index + 1 if close_index is not None else start

    def _normalize_compiler_extensions(
        self,
        text: str,
    ) -> tuple[str, list[_UnmodeledCompilerExtension]]:
        """Remove tolerated compiler syntax while retaining source coordinates.

        The parser extracts wrapper-facing C types, not compiler attribute
        semantics. Harmless syntax is blanked before grammar parsing. Extensions
        that can affect ABI, layout, or symbol identity also produce warnings.
        """
        characters = list(text)
        extensions: list[_UnmodeledCompilerExtension] = []
        index = 0
        state = "normal"
        quote = ""

        while index < len(text):
            char = text[index]
            nxt = text[index + 1] if index + 1 < len(text) else ""
            if state == "line_comment":
                if char == "\n":
                    state = "normal"
                index += 1
                continue
            if state == "block_comment":
                if char == "*" and nxt == "/":
                    state = "normal"
                    index += 2
                else:
                    index += 1
                continue
            if state in {"string", "char"}:
                if char == "\\" and nxt:
                    index += 2
                    continue
                if char == quote:
                    state = "normal"
                    quote = ""
                index += 1
                continue
            if char == "/" and nxt == "/":
                state = "line_comment"
                index += 2
                continue
            if char == "/" and nxt == "*":
                state = "block_comment"
                index += 2
                continue
            if char in {'"', "'"}:
                state = "string" if char == '"' else "char"
                quote = char
                index += 1
                continue

            if text[index : index + 2] == "[[":
                span_end = self._find_double_bracket_end(text, index)
                if span_end is not None:
                    extensions.extend(
                        self._attribute_extension_facts(
                            text[index + 2 : span_end - 2],
                            offset=index,
                        )
                    )
                    self._blank_span(characters, index, span_end)
                    index = span_end
                    continue

            identifier = self._read_identifier(text, index)
            if identifier is None:
                index += 1
                continue
            word, word_end = identifier

            if word in _COMPILER_KEYWORD_NORMALIZATIONS:
                self._replace_span(
                    characters,
                    index,
                    word_end,
                    _COMPILER_KEYWORD_NORMALIZATIONS[word],
                )
                index = word_end
                continue

            if word in _GNU_ATTRIBUTE_KEYWORDS | _DECLSPEC_KEYWORDS:
                span_end = self._compiler_extension_invocation_end(text, word_end)
                if span_end > word_end:
                    extensions.extend(
                        self._attribute_extension_facts(
                            text[word_end:span_end],
                            offset=index,
                        )
                    )
                else:
                    span_end = word_end
                self._blank_span(characters, index, span_end)
                index = span_end
                continue

            if word in _ALIGNMENT_KEYWORDS:
                span_end = self._compiler_extension_invocation_end(text, word_end)
                if span_end <= word_end:
                    span_end = word_end
                extensions.append(
                    _UnmodeledCompilerExtension(
                        kind="alignment_specifier",
                        name=word,
                        offset=index,
                        message=(
                            f"Alignment specifier {word!r} was accepted for parsing "
                            "but its layout semantics are not modeled."
                        ),
                    )
                )
                self._blank_span(characters, index, span_end)
                index = span_end
                continue

            if word in _ASM_KEYWORDS:
                payload_start = self._skip_whitespace(text, word_end)
                while True:
                    qualifier = self._read_identifier(text, payload_start)
                    if qualifier is None or qualifier[0] not in {"goto", "volatile", "__volatile", "__volatile__"}:
                        break
                    payload_start = self._skip_whitespace(text, qualifier[1])
                span_end = self._compiler_extension_invocation_end(text, payload_start)
                if span_end <= payload_start:
                    span_end = word_end
                extensions.append(
                    _UnmodeledCompilerExtension(
                        kind="asm_label",
                        name=word,
                        offset=index,
                        message=(
                            "Assembler label syntax was accepted for parsing but "
                            "the alternate native symbol identity is not modeled."
                        ),
                    )
                )
                self._blank_span(characters, index, span_end)
                index = span_end
                continue

            if word in _TYPEOF_KEYWORDS or word == "_BitInt":
                span_end = self._compiler_extension_invocation_end(text, word_end)
                if span_end > word_end:
                    placeholder = "_typeof" if word in _TYPEOF_KEYWORDS else "_bitint"
                    extensions.append(
                        _UnmodeledCompilerExtension(
                            kind="compiler_type",
                            name=word,
                            offset=index,
                            message=(f"Compiler type expression {word!r} was accepted as an opaque type placeholder."),
                        )
                    )
                    self._replace_span(characters, index, span_end, placeholder)
                    index = span_end
                    continue

            if word in _CALLING_CONVENTION_KEYWORDS:
                extensions.append(
                    _UnmodeledCompilerExtension(
                        kind="calling_convention",
                        name=word,
                        offset=index,
                        message=(
                            f"Calling convention {word!r} was accepted for parsing "
                            "but its ABI semantics are not modeled."
                        ),
                    )
                )
                self._blank_span(characters, index, word_end)
                index = word_end
                continue

            if word in _ABI_DECLARATION_KEYWORDS:
                extensions.append(
                    _UnmodeledCompilerExtension(
                        kind="compiler_qualifier",
                        name=word,
                        offset=index,
                        message=(
                            f"Compiler qualifier {word!r} was accepted for parsing "
                            "but its ABI semantics are not modeled."
                        ),
                    )
                )
                self._blank_span(characters, index, word_end)
                index = word_end
                continue

            if word in _IGNORABLE_EXTENSION_KEYWORDS | _IGNORABLE_DECLARATION_KEYWORDS:
                self._blank_span(characters, index, word_end)
                index = word_end
                continue

            index = word_end

        return "".join(characters), extensions

    def _normalized_extension_segment(
        self,
        segment: CTopLevelSegment,
    ) -> tuple[CTopLevelSegment, list[CDiagnostic]]:
        """Normalize one segment and report semantically significant omissions."""
        normalized, extensions = self._normalize_compiler_extensions(segment.text)
        diagnostics = [
            CDiagnostic(
                code="C_UNMODELED_COMPILER_EXTENSION",
                message=extension.message,
                severity="warning",
                location=self._source_location_at(segment, extension.offset),
                unit_kind=extension.kind,
                unit_name=extension.name,
            )
            for extension in extensions
        ]
        return replace(segment, text=normalized), diagnostics

    def _find_matching_delimiter(
        self,
        text: str,
        open_index: int,
        open_char: str,
        close_char: str,
    ) -> int | None:
        """Find the matching delimiter while respecting strings and chars."""
        depth = 0
        state = "normal"
        quote = ""
        escaped = False
        for index in range(open_index, len(text)):
            char = text[index]
            if state in {"string", "char"}:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    state = "normal"
                    quote = ""
                continue
            if char in {'"', "'"}:
                state = "string" if char == '"' else "char"
                quote = char
                escaped = False
                continue
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    return index
        return None

    def _split_declaration_specifiers(self, text: str) -> tuple[str, str]:
        """Split a declaration into specifier prefix and declarator tail.

        This is the declaration grammar gateway. It consumes storage classes,
        qualifiers, function specifiers, primitive words, tag references, and at
        most one typedef-name placeholder before leaving the declarator text for
        the recursive declarator parser.
        """
        index = 0
        spec_end = 0
        consumed_type = False
        consumed_typedef_name = False

        while True:
            index = self._skip_whitespace(text, index)
            identifier = self._read_identifier(text, index)
            if identifier is None:
                break
            word, end = identifier

            if word == "_Atomic":
                open_index = self._skip_whitespace(text, end)
                if open_index < len(text) and text[open_index] == "(":
                    if consumed_type:
                        break
                    close_index = self._find_matching_delimiter(text, open_index, "(", ")")
                    if close_index is None:
                        break
                    consumed_type = True
                    index = close_index + 1
                    spec_end = index
                    continue

            if (
                self._canonical_storage_class(word) is not None
                or self._canonical_type_qualifier(word) is not None
                or self._canonical_function_specifier(word) is not None
            ):
                index = end
                spec_end = end
                continue

            if self._canonical_primitive_word(word) in _PRIMITIVE_WORDS or word in _EXTENDED_SCALAR_WORDS:
                consumed_type = True
                index = end
                spec_end = end
                continue

            if word in _TAG_KINDS:
                consumed_type = True
                index = self._skip_whitespace(text, end)
                tag_identifier = self._read_identifier(text, index)
                if tag_identifier is not None:
                    _tag_name, index = tag_identifier
                spec_end = index
                continue

            if not consumed_type and not consumed_typedef_name:
                consumed_type = True
                consumed_typedef_name = True
                index = end
                spec_end = end
                continue

            break

        return text[:spec_end].strip(), text[spec_end:].strip()

    # ------------------------------------------------------------------
    # Recursive declarator grammar
    # ------------------------------------------------------------------

    def _parse_pointer_ops(
        self,
        text: str,
        index: int,
    ) -> tuple[list[_PointerOp], int]:
        """Parse leading pointer operators from a declarator fragment."""
        pointers: list[_PointerOp] = []
        index = self._skip_whitespace(text, index)
        while index < len(text) and text[index] == "*":
            index += 1
            qualifiers: list[str] = []
            while True:
                index = self._skip_whitespace(text, index)
                identifier = self._read_identifier(text, index)
                if identifier is None:
                    break
                word, end = identifier
                qualifier = self._canonical_type_qualifier(word)
                if qualifier is None:
                    break
                qualifiers.append(qualifier)
                index = end
            pointers.append(_PointerOp(qualifiers=qualifiers))
            index = self._skip_whitespace(text, index)
        return pointers, index

    def _parse_array_op(self, content: str) -> _ArrayOp:
        """Parse the contents of one array declarator suffix."""
        words = content.strip().split()
        qualifiers: list[str] = []
        is_static = False
        remaining: list[str] = []
        for word in words:
            if word == "static":
                is_static = True
            elif self._canonical_type_qualifier(word) is not None:
                qualifiers.append(self._canonical_type_qualifier(word))
            else:
                remaining.append(word)
        normalized = " ".join(remaining)
        variable_length = normalized == "*"
        return _ArrayOp(
            size=None if variable_length else normalized or None,
            static=is_static,
            qualifiers=qualifiers,
            variable_length=variable_length,
        )

    def _parse_declarator_suffixes(
        self,
        text: str,
        index: int,
    ) -> tuple[list[_ArrayOp | _FunctionOp], int]:
        """Parse direct-declarator array/function suffixes."""
        operations: list[_ArrayOp | _FunctionOp] = []
        while True:
            index = self._skip_whitespace(text, index)
            if index >= len(text):
                return operations, index

            if text[index] == "[":
                close_index = self._find_matching_delimiter(text, index, "[", "]")
                if close_index is None:
                    return operations, index
                operations.append(self._parse_array_op(text[index + 1 : close_index]))
                index = close_index + 1
                continue

            if text[index] == "(":
                close_index = self._find_matching_delimiter(text, index, "(", ")")
                if close_index is None:
                    return operations, index
                parameters_text = text[index + 1 : close_index]
                parameters, variadic = self._parse_parameters(parameters_text)
                operations.append(
                    _FunctionOp(
                        parameters=parameters,
                        variadic=variadic,
                        prototype_style=self._prototype_style(parameters_text),
                    )
                )
                index = close_index + 1
                continue

            return operations, index

    def _parse_direct_declarator_at(
        self,
        text: str,
        index: int,
    ) -> tuple[str | None, list[_PointerOp | _ArrayOp | _FunctionOp], int]:
        """Parse a direct declarator at `index`.

        Direct declarators contain the identifier, parenthesized declarator, and
        suffix chain. Parenthesized declarators recurse back into
        `_parse_declarator` so pointer/function/array precedence follows C's
        grammar instead of a flat string split.
        """
        index = self._skip_whitespace(text, index)
        if index < len(text) and text[index] == "(":
            close_index = self._find_matching_delimiter(text, index, "(", ")")
            if close_index is None:
                return None, [], index
            inner = self._parse_declarator(text[index + 1 : close_index])
            suffixes, index = self._parse_declarator_suffixes(text, close_index + 1)
            return inner.name, [*reversed(suffixes), *inner.operations], index

        identifier = self._read_identifier(text, index)
        if identifier is None:
            suffixes, index = self._parse_declarator_suffixes(text, index)
            return None, list(reversed(suffixes)), index

        name, index = identifier
        suffixes, index = self._parse_declarator_suffixes(text, index)
        return name, list(reversed(suffixes)), index

    def _parse_declarator_at(
        self,
        text: str,
        index: int,
    ) -> tuple[str | None, list[_PointerOp | _ArrayOp | _FunctionOp], int]:
        """Parse one full declarator at `index` into name and operations."""
        pointers, index = self._parse_pointer_ops(text, index)
        name, direct_operations, index = self._parse_direct_declarator_at(text, index)
        return name, [*pointers, *direct_operations], index

    def _parse_declarator(self, text: str) -> _ParsedDeclarator:
        """Parse a complete declarator fragment and reject unconsumed syntax."""
        stripped = text.strip()
        if not stripped:
            return _ParsedDeclarator(name=None, operations=[], source_text="")
        name, operations, index = self._parse_declarator_at(stripped, 0)
        remainder = stripped[self._skip_whitespace(stripped, index) :].strip()
        if remainder:
            raise _UnsupportedDeclaratorSyntax(
                f"Unsupported declarator syntax after parsed type layers: {remainder!r}."
            )
        return _ParsedDeclarator(name=name, operations=operations, source_text=stripped)

    def _prepend_component(self, component: CType, current: CType) -> CComposedType:
        """Prepend one derived type component to an existing parser type."""
        if isinstance(current, CComposedType):
            return CComposedType(
                components=[component, *current.components],
                source_text=current.source_text,
            )
        return CComposedType(components=[component, current], source_text=current.source_text)

    def _apply_pointer_operation(self, current: CType, operation: _PointerOp) -> CType:
        """Apply one parsed pointer operation to the current type."""
        return self._prepend_component(
            CPointer(qualifiers=self._qualifiers(operation.qualifiers)),
            current,
        )

    def _apply_array_operation(self, current: CType, operation: _ArrayOp) -> CType:
        """Apply one parsed array operation to the current type."""
        array = CArray(
            bound=operation.size,
            is_static_minimum=operation.static,
            qualifiers=self._qualifiers(operation.qualifiers or []),
            is_variable_length=operation.variable_length,
        )
        return self._prepend_component(array, current)

    def _apply_function_operation(self, current: CType, operation: _FunctionOp) -> CType:
        """Apply one parsed function operation to the current type."""
        return CFunctionType(
            result_type=current,
            parameter_types=[parameter.type for parameter in operation.parameters],
            is_variadic=operation.variadic,
            prototype_style=operation.prototype_style,
            source_text=current.source_text,
        )

    def _apply_declarator_operations(
        self,
        base_type: CType,
        operations: list[_PointerOp | _ArrayOp | _FunctionOp],
    ) -> CType:
        """Apply parsed declarator operations to a declaration base type."""
        current = base_type
        for operation in operations:
            if isinstance(operation, _PointerOp):
                current = self._apply_pointer_operation(current, operation)
            elif isinstance(operation, _ArrayOp):
                current = self._apply_array_operation(current, operation)
            else:
                current = self._apply_function_operation(current, operation)
        return current

    def _build_declared_type(
        self,
        spec_text: str,
        declarator_fragment: str = "",
    ) -> tuple[str | None, CType, list[str], list[str], _FunctionOp | None]:
        """Build the declared entity name, type, and declaration metadata."""
        base_type, storage, function_specifiers = self._parse_specifiers(spec_text)
        parsed = self._parse_declarator(declarator_fragment)
        type_ = self._apply_declarator_operations(base_type, parsed.operations)
        source_parts = [spec_text.strip(), declarator_fragment.strip()]
        type_.source_text = " ".join(part for part in source_parts if part).strip()
        direct_function = (
            parsed.operations[-1] if parsed.operations and isinstance(parsed.operations[-1], _FunctionOp) else None
        )
        return parsed.name, type_, storage, function_specifiers, direct_function

    def _adjust_parameter_type(self, declared_type: CType) -> CType:
        """Apply C parameter adjustment while preserving the written type."""
        if isinstance(declared_type, CFunctionType):
            return CComposedType(
                components=[CPointer(), declared_type],
                source_text=declared_type.source_text,
            )
        if (
            isinstance(declared_type, CComposedType)
            and declared_type.components
            and isinstance(declared_type.components[0], CArray)
        ):
            outer_array = declared_type.components[0]
            return CComposedType(
                components=[
                    CPointer(qualifiers=list(outer_array.qualifiers)),
                    *declared_type.components[1:],
                ],
                source_text=declared_type.source_text,
            )
        return declared_type

    # ------------------------------------------------------------------
    # Parameter and function grammar
    # ------------------------------------------------------------------

    def _parse_parameter(self, text: str) -> CParameter | None:
        """Parse one function parameter declaration through the shared backend."""
        stripped = text.strip()
        if not stripped or stripped == "void":
            return None
        spec_text, declarator = self._split_declaration_specifiers(stripped)
        if not spec_text:
            raise _InvalidCGrammarSyntax(f"Invalid parameter declaration: {stripped}")
        name, type_, _storage, _function_specifiers, _direct_function = self._build_declared_type(
            spec_text,
            declarator,
        )
        return CParameter(
            name=name,
            type=self._adjust_parameter_type(type_),
            declared_type=type_,
        )

    def _find_parameter_list(self, text: str) -> tuple[int, int] | None:
        """Return the bounds of a trailing parameter list in declaration text."""
        close_index = len(text) - 1
        while close_index >= 0 and text[close_index].isspace():
            close_index -= 1
        if close_index < 0 or text[close_index] != ")":
            return None

        depth = 0
        state = "normal"
        quote = ""
        escaped = False
        for index in range(close_index, -1, -1):
            char = text[index]
            if state in {"string", "char"}:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    state = "normal"
                    quote = ""
                continue
            if char in {'"', "'"}:
                state = "string" if char == '"' else "char"
                quote = char
                escaped = False
                continue
            if char == ")":
                depth += 1
            elif char == "(":
                depth -= 1
                if depth == 0:
                    return index, close_index
        return None

    def _parse_parameters(self, parameters_text: str) -> tuple[list[CParameter], bool]:
        """Parse a comma-separated parameter list and variadic marker."""
        stripped = parameters_text.strip()
        if not stripped or stripped == "void":
            return [], False

        parameters: list[CParameter] = []
        variadic = False
        items = top_level_split(stripped, ",")
        for index, item in enumerate(items):
            if item == "...":
                if variadic or index != len(items) - 1:
                    raise _InvalidCGrammarSyntax("The variadic marker must be the final function parameter.")
                variadic = True
                continue
            parameter = self._parse_parameter(item)
            if parameter is None:
                raise _InvalidCGrammarSyntax(f"Invalid parameter declaration: {item}")
            parameters.append(parameter)
        return parameters, variadic

    def _is_knr_definition(self, segment: CTopLevelSegment, parameters_text: str) -> bool:
        """Return whether a function-looking block is a K&R-style definition."""
        if segment.terminator != "block":
            return False
        stripped = parameters_text.strip()
        if not stripped or stripped == "void" or "..." in stripped:
            return False
        return all(re.fullmatch(r"[A-Za-z_]\w*", item.strip()) for item in top_level_split(stripped, ","))

    def _raise_for_unsupported_old_style_definitions(
        self,
        source: str,
        filename: str | None,
        *,
        use_linemarkers: bool,
        normalize_compiler_extensions: bool,
    ) -> None:
        """Raise before top-level splitting hides unsupported K&R declarations."""
        normalized_source = source
        if normalize_compiler_extensions:
            normalized_source, _extensions = self._normalize_compiler_extensions(source)
        stripped_lines = strip_c_comments(normalized_source).splitlines()
        line_mappings = line_mappings_for_source(
            source,
            filename=filename,
            use_linemarkers=use_linemarkers,
        )

        for index, line in enumerate(stripped_lines):
            text = line.strip()
            if text.startswith("#"):
                continue
            parameter_bounds = self._find_parameter_list(text)
            if parameter_bounds is None:
                continue
            open_index, close_index = parameter_bounds
            before_parameters = text[:open_index].strip()
            name_match = self._last_identifier(before_parameters)
            if name_match is None:
                continue
            if name_match.group(0) in {"if", "for", "while", "switch"}:
                continue
            return_spec = before_parameters[: name_match.start()].strip()
            if not return_spec or "(" in return_spec or ")" in return_spec:
                continue

            parameters_text = text[open_index + 1 : close_index].strip()
            if not parameters_text or parameters_text == "void":
                continue

            parameters = [part.strip() for part in parameters_text.split(",")]
            if not parameters or not all(re.fullmatch(r"[A-Za-z_]\w*", part) for part in parameters):
                continue

            saw_old_style_declaration = False
            for follow in stripped_lines[index + 1 :]:
                stripped = follow.strip()
                if not stripped:
                    continue
                if stripped.startswith("{"):
                    mapping = line_mappings[index] if index < len(line_mappings) else None
                    source_line = (
                        mapping.source_line if mapping is not None and mapping.source_line is not None else line
                    )
                    raise CParseError(
                        "K&R style function definitions are not supported",
                        filename=mapping.filename if mapping is not None else filename,
                        line_number=mapping.line if mapping is not None else index + 1,
                        column=max(line.find(name_match.group(0)) + 1, 1),
                        source_line=source_line,
                        code="CPARSE_UNSUPPORTED_KNR_DEFINITION",
                    )
                if stripped.endswith(";"):
                    saw_old_style_declaration = True
                    continue
                break

            if saw_old_style_declaration:
                mapping = line_mappings[index] if index < len(line_mappings) else None
                source_line = mapping.source_line if mapping is not None and mapping.source_line is not None else line
                raise CParseError(
                    "K&R style function definitions are not supported",
                    filename=mapping.filename if mapping is not None else filename,
                    line_number=mapping.line if mapping is not None else index + 1,
                    column=max(line.find(name_match.group(0)) + 1, 1),
                    source_line=source_line,
                    code="CPARSE_UNSUPPORTED_KNR_DEFINITION",
                )

    def _prototype_style(self, parameters_text: str) -> str:
        """Classify empty `()` versus prototype-style parameter lists."""
        return "unspecified" if not parameters_text.strip() else "prototype"

    def _parse_function(self, segment: CTopLevelSegment) -> CFunction | None:
        """Parse a function prototype or definition segment, if it is one."""
        text = segment.text.strip()
        if text.startswith(("typedef ", "_Static_assert")) or self._has_unsupported_declaration_marker(text):
            return None

        spec_text, declarator = self._split_declaration_specifiers(text)
        if not spec_text or not declarator:
            return None
        try:
            name, function_type, storage, function_specifiers, direct_function = self._build_declared_type(
                spec_text,
                declarator,
            )
        except _InvalidSpecifierSequence as error:
            raise self._invalid_specifier_error(segment, str(error)) from None
        if name is None or not isinstance(function_type, CFunctionType) or direct_function is None:
            return None
        parameter_bounds = self._find_parameter_list(text)
        if parameter_bounds is not None:
            open_index, close_index = parameter_bounds
            parameters_text = text[open_index + 1 : close_index]
            if "(" not in text[:open_index] and self._is_knr_definition(segment, parameters_text):
                raise CParseError(
                    "K&R style function definitions are not supported",
                    filename=segment.filename,
                    line_number=segment.original_start_line,
                    column=segment.original_start_column,
                    source_line=segment.original_source_line,
                    code="CPARSE_UNSUPPORTED_KNR_DEFINITION",
                )
        return self._function_from_type(
            name,
            function_type,
            direct_function.parameters,
            storage,
            function_specifiers,
            segment,
        )

    def _function_from_type(
        self,
        name: str,
        function_type: CFunctionType,
        parameters: list[CParameter],
        storage: list[str],
        function_specifiers: list[str],
        segment: CTopLevelSegment,
    ) -> CFunction:
        """Assemble a `CFunction` model from a parsed function declarator."""
        return CFunction(
            name=name,
            result_type=function_type.result_type,
            parameters=list(parameters),
            storage=list(storage),
            specifiers=function_specifiers,
            is_variadic=function_type.is_variadic,
            is_definition=segment.terminator == "block",
            prototype_style=function_type.prototype_style,
            source_location=self._source_location(segment),
            start=self._source_location(segment),
            end=self._end_location(segment) if segment.terminator == "block" else None,
        )

    # ------------------------------------------------------------------
    # Aggregate, field, enum, and declaration parsing
    # ------------------------------------------------------------------

    def _anonymous_tag_id(self, kind: str, segment: CTopLevelSegment) -> str:
        """Create a stable anonymous aggregate id from source location."""
        filename = segment.filename or "<source>"
        return f"{kind}@{filename}:{segment.original_start_line}:{segment.original_start_column}"

    def _tag_definition_header(self, text: str) -> tuple[str, list[str], str | None] | None:
        """Parse the prefix before an aggregate definition body."""
        words = self._specifier_words(text)
        for index, word in enumerate(words):
            if word not in _TAG_KINDS:
                continue
            prefix: list[str] = []
            for prefix_word in words[:index]:
                normalized = self._canonical_storage_class(prefix_word) or self._canonical_type_qualifier(prefix_word)
                if normalized is None:
                    return None
                prefix.append(normalized)
            suffix = words[index + 1 :]
            if len(suffix) > 1:
                return None
            return word, prefix, suffix[0] if suffix else None
        return None

    def _forward_tag(self, segment: CTopLevelSegment) -> CStruct | CUnion | None:
        """Parse `struct tag;` or `union tag;` forward declarations."""
        words = self._specifier_words(segment.text.strip())
        if len(words) != 2 or words[0] not in {"struct", "union"}:
            return None
        if words[0] == "struct":
            return CStruct(
                name=words[1],
                is_incomplete=True,
                source_location=self._source_location(segment),
            )
        return CUnion(
            name=words[1],
            is_incomplete=True,
            source_location=self._source_location(segment),
        )

    def _use_aggregate_definition(
        self,
        type_: CType,
        aggregate: CStruct | CUnion | CEnum,
    ) -> CType:
        """Replace a matching tag reference with the parsed aggregate object."""
        if isinstance(type_, CComposedType):
            terminal = type_.components[-1]
            if isinstance(terminal, CStruct | CUnion | CEnum) and not terminal.qualifiers:
                type_.components[-1] = aggregate
            return type_
        if isinstance(type_, CStruct | CUnion | CEnum) and not type_.qualifiers:
            return aggregate
        return type_

    def _declarations_from_declarators(
        self,
        spec_text: str,
        declarator_list: str,
        segment: CTopLevelSegment,
        *,
        resolved: CStruct | CUnion | CEnum | None = None,
    ) -> tuple[list[CFunction], list[CTypedef], list[CVariable], list[CDiagnostic]]:
        """Parse all declarators after a shared declaration-specifier prefix.

        This is the common declaration backend for top-level functions,
        variables, typedefs, and aggregate declarators that follow inline
        `struct`/`union`/`enum` definitions.
        """
        functions: list[CFunction] = []
        typedefs: list[CTypedef] = []
        variables: list[CVariable] = []
        diagnostics: list[CDiagnostic] = []

        for declarator in top_level_split(declarator_list, ","):
            declaration, initializer = top_level_partition(declarator, "=")
            try:
                name, type_, storage, function_specifiers, direct_function = self._build_declared_type(
                    spec_text,
                    declaration,
                )
            except _InvalidSpecifierSequence as error:
                raise self._invalid_specifier_error(segment, str(error)) from None
            except _UnsupportedDeclaratorSyntax as error:
                diagnostics.append(self._declarator_diagnostic(segment, str(error)))
                continue
            if not name:
                continue
            if resolved is not None:
                type_ = self._use_aggregate_definition(type_, resolved)
            location = self._source_location(segment)
            if "typedef" in storage:
                typedefs.append(
                    CTypedef(
                        name=name,
                        type=type_,
                        source_location=location,
                        source_text=name,
                    )
                )
            elif isinstance(type_, CFunctionType) and direct_function is not None:
                functions.append(
                    self._function_from_type(
                        name,
                        type_,
                        direct_function.parameters,
                        storage,
                        function_specifiers,
                        segment,
                    )
                )
            else:
                variables.append(
                    CVariable(
                        name=name,
                        type=type_,
                        storage=storage,
                        initializer=CInitializer(initializer) if initializer is not None else None,
                        source_location=location,
                    )
                )

        return functions, typedefs, variables, diagnostics

    def _declarator_diagnostic(self, segment: CTopLevelSegment, message: str) -> CDiagnostic:
        """Build a warning for a declarator rejected by the grammar subset."""
        return CDiagnostic(
            code="C_UNSUPPORTED_DECLARATOR",
            message=message,
            severity="warning",
            location=self._source_location(segment),
            unit_kind="declarator",
            unit_name=None,
        )

    def _union_by_value_names(self, type_: CType, seen: set[int] | None = None) -> set[str]:
        """Return union type names that appear without pointer/array indirection."""
        if seen is None:
            seen = set()
        type_id = id(type_)
        if type_id in seen:
            return set()
        seen.add(type_id)
        if isinstance(type_, CUnion):
            return {type_.reference_name}
        if isinstance(type_, CTypedef) and type_.type is not None:
            return self._union_by_value_names(type_.type, seen)
        if isinstance(type_, CFunctionType):
            names = set()
            names.update(self._union_by_value_names(type_.result_type, seen))
            for parameter_type in type_.parameter_types:
                names.update(self._union_by_value_names(parameter_type, seen))
            return names
        if isinstance(type_, CComposedType):
            names = set()
            protected_by_indirection = False
            for component in type_.components:
                if isinstance(component, CPointer | CArray):
                    protected_by_indirection = True
                    continue
                if isinstance(component, CFunctionType):
                    names.update(self._union_by_value_names(component, seen))
                    protected_by_indirection = False
                    continue
                if isinstance(component, CUnion) and not protected_by_indirection:
                    names.add(component.reference_name)
                protected_by_indirection = False
            return names
        return set()

    def _union_by_value_diagnostics(self, function: CFunction) -> list[CDiagnostic]:
        """Build conservative diagnostics for functions using unions by value."""
        union_names = self._union_by_value_names(function.result_type)
        for parameter in function.parameters:
            union_names.update(self._union_by_value_names(parameter.type))
        if not union_names:
            return []

        formatted = ", ".join(sorted(union_names))
        return [
            CDiagnostic(
                code="C_UNION_BY_VALUE",
                message=(
                    f"Function {function.name!r} uses union type(s) by value: {formatted}. "
                    "Use an explicit pointer or defer wrapper policy to the semantic layer."
                ),
                severity="warning",
                location=function.source_location,
                unit_kind="function",
                unit_name=function.name,
            )
        ]

    def _append_union_by_value_diagnostics(
        self,
        function: CFunction,
        diagnostics: list[CDiagnostic],
    ) -> None:
        """Append union-by-value diagnostics without duplicating messages."""
        for diagnostic in self._union_by_value_diagnostics(function):
            already_present = any(
                existing.code == diagnostic.code
                and existing.unit_kind == diagnostic.unit_kind
                and existing.unit_name == diagnostic.unit_name
                and existing.location == diagnostic.location
                for existing in diagnostics
            )
            if not already_present:
                diagnostics.append(diagnostic)

    def _field_diagnostic(
        self,
        segment: CTopLevelSegment,
        owner_kind: str,
        message: str,
        *,
        offset: int,
    ) -> CDiagnostic:
        """Build a field-level warning at a precise member offset."""
        return CDiagnostic(
            code="C_UNSUPPORTED_FIELD_DECLARATION",
            message=message,
            severity="warning",
            location=self._source_location_at(segment, offset),
            unit_kind=f"{owner_kind}_field",
            unit_name=None,
        )

    def _incomplete_array_component(self, type_: CType) -> CArray | None:
        """Return the outer incomplete array component, if present."""
        components = type_.components if isinstance(type_, CComposedType) else [type_]
        if not components or not isinstance(components[0], CArray):
            return None
        array = components[0]
        if array.bound is None and not array.is_variable_length:
            return array
        return None

    def _validate_flexible_members(
        self,
        members: list[CVariable],
        owner_kind: str,
    ) -> list[CDiagnostic]:
        """Validate C flexible array member placement rules for this subset."""
        diagnostics: list[CDiagnostic] = []
        named_members = sum(member.name is not None for member in members)
        for index, member in enumerate(members):
            array = self._incomplete_array_component(member.type)
            if array is None:
                continue
            if owner_kind == "struct" and index == len(members) - 1 and named_members > 1:
                array.is_flexible = True
                continue
            if owner_kind == "union":
                message = "A union member cannot be a flexible array member."
            elif index != len(members) - 1:
                message = "A flexible array member must be the final member of a struct."
            else:
                message = "A flexible array member requires a preceding named struct member."
            diagnostics.append(
                CDiagnostic(
                    code="C_INVALID_FLEXIBLE_ARRAY_MEMBER",
                    message=message,
                    severity="error",
                    location=member.source_location,
                    unit_kind=f"{owner_kind}_field",
                    unit_name=member.name,
                )
            )
        return diagnostics

    def _nested_field_segment(
        self,
        segment: CTopLevelSegment,
        text: str,
        offset: int,
    ) -> CTopLevelSegment:
        """Create a location-preserving segment for a nested field definition."""
        start = self._source_location_at(segment, offset)
        end = self._source_location_at(segment, offset + max(len(text) - 1, 0))
        line_offset = segment.text[:offset].count("\n")
        line_count = text.count("\n") + 1
        line_slice = slice(line_offset, line_offset + line_count)
        return CTopLevelSegment(
            text=text,
            terminator=";",
            filename=start.filename,
            original_start_line=start.line or segment.original_start_line,
            original_end_line=end.line or segment.original_end_line,
            original_start_column=start.column or segment.original_start_column,
            original_end_column=end.column or segment.original_end_column,
            original_source_line=start.source_line,
            original_end_source_line=end.source_line,
            original_source_lines=segment.original_source_lines[line_slice],
            original_filenames=segment.original_filenames[line_slice],
            original_line_numbers=segment.original_line_numbers[line_slice],
        )

    def _parse_fields(
        self,
        body: str,
        segment: CTopLevelSegment,
        owner_kind: str,
        *,
        body_offset: int,
    ) -> tuple[list[CVariable], list[CDiagnostic]]:
        """Parse struct/union member declarations through the shared backend."""
        members: list[CVariable] = []
        diagnostics: list[CDiagnostic] = []
        if body.strip() and not body.rstrip().endswith(";"):
            raise self._invalid_syntax_error(
                segment,
                body,
                context=f"{owner_kind} field declaration",
                offset=body_offset,
            )
        for text, field_offset in top_level_split_with_offsets(body, ";"):
            member_offset = body_offset + field_offset
            member_location = self._source_location_at(segment, member_offset)
            if "{" in text or "}" in text:
                nested = self._parse_tag_definition(self._nested_field_segment(segment, text, member_offset))
                if nested is not None:
                    aggregate, functions, typedefs, variables, nested_diagnostics = nested
                    if not functions and not typedefs:
                        if variables:
                            members.extend(variables)
                            diagnostics.extend(nested_diagnostics)
                            continue
                        if isinstance(aggregate, CStruct | CUnion) and aggregate.name is None:
                            members.append(
                                CVariable(
                                    name=None,
                                    type=aggregate,
                                    source_location=member_location,
                                )
                            )
                            diagnostics.extend(nested_diagnostics)
                            continue
                diagnostics.append(
                    self._field_diagnostic(
                        segment,
                        owner_kind,
                        "Unsupported nested aggregate field declaration.",
                        offset=member_offset,
                    )
                )
                continue
            if "::" in text:
                raise self._invalid_syntax_error(
                    segment,
                    text,
                    context=f"{owner_kind} field declaration",
                    offset=member_offset,
                )
            spec_text, declarator_list = self._split_declaration_specifiers(text)
            if not spec_text or not declarator_list:
                raise self._invalid_syntax_error(
                    segment,
                    text,
                    context=f"{owner_kind} field declaration",
                    offset=member_offset,
                )
            for declarator in top_level_split(declarator_list, ","):
                declaration, _initializer = top_level_partition(declarator, "=")
                declaration, bit_width = top_level_partition(declaration, ":")
                try:
                    name, type_, _storage, _function_specifiers, _direct_function = self._build_declared_type(
                        spec_text,
                        declaration,
                    )
                except _InvalidSpecifierSequence as error:
                    raise self._invalid_specifier_error(segment, str(error), offset=member_offset) from None
                except _UnsupportedDeclaratorSyntax as error:
                    diagnostics.append(self._field_diagnostic(segment, owner_kind, str(error), offset=member_offset))
                    continue
                if name is None and bit_width is None:
                    diagnostics.append(
                        self._field_diagnostic(
                            segment,
                            owner_kind,
                            "Unnamed field type is not supported.",
                            offset=member_offset,
                        )
                    )
                    continue
                members.append(
                    CVariable(
                        name=name,
                        type=type_,
                        source_location=member_location,
                        bit_width=bit_width,
                    )
                )
        diagnostics.extend(self._validate_flexible_members(members, owner_kind))
        return members, diagnostics

    def _parse_enumerators(self, body: str, segment: CTopLevelSegment) -> list[CEnumerator]:
        """Parse enum constants while preserving explicit expression text."""
        constants: list[CEnumerator] = []
        for item in top_level_split(body, ","):
            name_text, value = top_level_partition(item, "=")
            identifier = self._read_identifier(name_text.strip(), 0)
            if identifier is None:
                raise self._invalid_syntax_error(segment, item, context="enum member")
            name, end = identifier
            if name_text[end:].strip():
                raise self._invalid_syntax_error(segment, item, context="enum member")
            constants.append(
                CEnumerator(
                    name=name,
                    value=value,
                    source_location=self._source_location(segment),
                )
            )
        return constants

    def _parse_tag_definition(
        self,
        segment: CTopLevelSegment,
    ) -> (
        tuple[
            CStruct | CUnion | CEnum,
            list[CFunction],
            list[CTypedef],
            list[CVariable],
            list[CDiagnostic],
        ]
        | None
    ):
        """Parse a top-level struct, union, or enum definition segment."""
        text = segment.text.strip()
        if self._has_unsupported_declaration_marker(text):
            return None
        open_index = text.find("{")
        if open_index < 0:
            return None
        close_index = self._find_matching_delimiter(text, open_index, "{", "}")
        if close_index is None:
            return None

        header = self._tag_definition_header(text[:open_index].strip())
        if header is None:
            return None
        kind, prefix, tag_name = header
        body = text[open_index + 1 : close_index]
        declarators = text[close_index + 1 :].strip()
        location = self._source_location(segment)
        anonymous_id = None if tag_name else self._anonymous_tag_id(kind, segment)
        diagnostics: list[CDiagnostic] = []

        if kind == "enum":
            aggregate: CStruct | CUnion | CEnum = CEnum(
                name=tag_name,
                constants=self._parse_enumerators(body, segment),
                anonymous_id=anonymous_id,
                source_location=location,
            )
        else:
            members, diagnostics = self._parse_fields(
                body,
                segment,
                kind,
                body_offset=open_index + 1,
            )
            if kind == "struct":
                aggregate = CStruct(
                    name=tag_name,
                    members=members,
                    anonymous_id=anonymous_id,
                    source_location=location,
                )
            else:
                aggregate = CUnion(
                    name=tag_name,
                    members=members,
                    anonymous_id=anonymous_id,
                    source_location=location,
                )

        functions: list[CFunction] = []
        typedefs: list[CTypedef] = []
        variables: list[CVariable] = []
        if declarators:
            spec_text = " ".join([*prefix, kind, *([tag_name] if tag_name else [])])
            functions, typedefs, variables, declarator_diagnostics = self._declarations_from_declarators(
                spec_text,
                declarators,
                segment,
                resolved=aggregate,
            )
            diagnostics.extend(declarator_diagnostics)
        elif "typedef" in prefix:
            diagnostics.append(
                CDiagnostic(
                    code="C_UNSUPPORTED_DECLARATION",
                    message="Typedef aggregate definition has no alias declarator.",
                    severity="warning",
                    location=location,
                    unit_kind=f"{kind}_typedef",
                    unit_name=tag_name,
                )
            )

        return aggregate, functions, typedefs, variables, diagnostics

    def _parse_declaration(
        self,
        segment: CTopLevelSegment,
    ) -> tuple[list[CFunction], list[CTypedef], list[CVariable], list[CDiagnostic]]:
        """Parse an ordinary top-level declaration segment."""
        text = segment.text.strip()
        if not text or text.startswith("_Static_assert") or self._has_unsupported_declaration_marker(text):
            return [], [], [], []

        spec_text, declarator_list = self._split_declaration_specifiers(text)
        if not spec_text or not declarator_list:
            return [], [], [], []

        return self._declarations_from_declarators(spec_text, declarator_list, segment)

    def _unsupported_declaration_diagnostic(self, segment: CTopLevelSegment) -> CDiagnostic | None:
        """Classify an unsupported declaration-shaped segment for diagnostics."""
        text = segment.text.strip()
        if not text:
            return None

        kind = ""
        message = ""

        if text.startswith("struct "):
            kind = "struct_definition"
            message = "Struct definitions are not supported yet."
        elif text.startswith("union "):
            kind = "union_definition"
            message = "Union definitions are not supported yet."
        elif text.startswith("enum "):
            kind = "enum_definition"
            message = "Enum definitions are not supported yet."
        elif text.startswith("_Static_assert"):
            kind = "static_assert"
            message = "Static assertions are recorded but not evaluated."
        elif "__attribute__" in text or "__declspec" in text or "[[" in text:
            kind = "attribute_declaration"
            message = "Compiler-specific declaration attributes are not supported yet."
        elif "_Alignas" in text or "alignas" in text:
            kind = "alignment_declaration"
            message = "Declaration alignment specifiers are not supported yet."
        elif "{" in text or "}" in text:
            kind = "brace_declaration"
            message = "Unsupported declaration containing braces."
        else:
            return None

        return CDiagnostic(
            code="C_UNSUPPORTED_DECLARATION",
            message=message,
            severity="warning",
            location=self._source_location(segment),
            unit_kind=kind,
            unit_name=None,
        )

    # ------------------------------------------------------------------
    # Translation-unit dispatch and project assembly
    # ------------------------------------------------------------------

    def _parse_translation_unit(
        self,
        source: str,
        filename: str | None,
        *,
        use_linemarkers: bool,
        normalize_compiler_extensions: bool,
    ) -> tuple[
        list[CFunction],
        list[CStruct],
        list[CUnion],
        list[CEnum],
        list[CTypedef],
        list[CVariable],
        list[CDiagnostic],
    ]:
        """Dispatch top-level C external declarations by grammar role.

        The ordering here is intentional: aggregate definitions are parsed
        before function/declaration fallback, and ordinary `;` declarations
        all flow through the shared declaration backend.
        """
        self._raise_for_unsupported_old_style_definitions(
            source,
            filename,
            use_linemarkers=use_linemarkers,
            normalize_compiler_extensions=normalize_compiler_extensions,
        )

        functions: list[CFunction] = []
        structs: list[CStruct] = []
        unions: list[CUnion] = []
        enums: list[CEnum] = []
        typedefs: list[CTypedef] = []
        variables: list[CVariable] = []
        diagnostics: list[CDiagnostic] = []

        for segment in split_top_level_c_source(
            source,
            filename=filename,
            use_linemarkers=use_linemarkers,
            tolerate_compiler_extensions=normalize_compiler_extensions,
        ):
            if normalize_compiler_extensions:
                segment, extension_diagnostics = self._normalized_extension_segment(segment)
                diagnostics.extend(extension_diagnostics)
                if not segment.text.strip():
                    continue
            self._raise_for_invalid_top_level_syntax(segment)
            try:
                tag_definition = self._parse_tag_definition(segment)
            except _InvalidCGrammarSyntax as error:
                raise self._invalid_syntax_error(segment, str(error), context="nested declaration") from None
            if tag_definition is not None:
                aggregate, parsed_functions, parsed_typedefs, parsed_variables, parsed_diagnostics = tag_definition
                if isinstance(aggregate, CStruct):
                    structs.append(aggregate)
                elif isinstance(aggregate, CUnion):
                    unions.append(aggregate)
                else:
                    enums.append(aggregate)
                functions.extend(parsed_functions)
                typedefs.extend(parsed_typedefs)
                variables.extend(parsed_variables)
                diagnostics.extend(parsed_diagnostics)
                continue
            if segment.terminator != ";":
                try:
                    function = self._parse_function(segment)
                except _UnsupportedDeclaratorSyntax as error:
                    diagnostics.append(self._declarator_diagnostic(segment, str(error)))
                    continue
                except _InvalidCGrammarSyntax as error:
                    raise self._invalid_syntax_error(segment, str(error), context="function declaration") from None
                if function is not None:
                    functions.append(function)
                    self._append_union_by_value_diagnostics(function, diagnostics)
                    continue
                unsupported = self._unsupported_declaration_diagnostic(segment)
                if unsupported is not None:
                    diagnostics.append(unsupported)
                    continue
                raise self._invalid_syntax_error(segment, segment.text, context="top level")
            forward_tag = self._forward_tag(segment)
            if isinstance(forward_tag, CStruct):
                structs.append(forward_tag)
                continue
            if isinstance(forward_tag, CUnion):
                unions.append(forward_tag)
                continue
            try:
                parsed_functions, parsed_typedefs, parsed_variables, declarator_diagnostics = self._parse_declaration(
                    segment
                )
            except _InvalidCGrammarSyntax as error:
                raise self._invalid_syntax_error(segment, str(error), context="declaration") from None
            functions.extend(parsed_functions)
            typedefs.extend(parsed_typedefs)
            variables.extend(parsed_variables)
            for function in parsed_functions:
                self._append_union_by_value_diagnostics(function, diagnostics)
            diagnostics.extend(declarator_diagnostics)
            if not parsed_functions and not parsed_typedefs and not parsed_variables and not declarator_diagnostics:
                unsupported = self._unsupported_declaration_diagnostic(segment)
                if unsupported is not None:
                    diagnostics.append(unsupported)
                else:
                    raise self._invalid_syntax_error(segment, segment.text, context="top level")

        return functions, structs, unions, enums, typedefs, variables, diagnostics

    def _build_project(self, parsed_files: dict[str, CFile]) -> CProject:
        """Build project indexes, include graph facts, and resolved type links."""
        project = CProject(files=parsed_files)
        all_functions: list[CFunction] = []
        for filename, file in parsed_files.items():
            project.functions_by_file[filename] = [function.name for function in file.functions]
            all_functions.extend(file.functions)
            for struct in file.structs:
                if struct.name is not None:
                    self._index_struct(project, struct, project.diagnostics)
            for union in file.unions:
                if union.name is not None:
                    self._index_union(project, union, project.diagnostics)
            for enum in file.enums:
                if enum.name is not None:
                    self._index_enum(project, enum, project.diagnostics)
                for constant in enum.constants:
                    project.enum_constants[constant.name] = constant
            for typedef in file.typedefs:
                project.typedefs[typedef.name] = typedef
            for variable in file.variables:
                if variable.name is not None:
                    project.variables[variable.name] = variable
            for macro in file.macros:
                project.macros[macro.name] = macro
            for include in file.includes:
                project.includes[f"{filename}:{include.target}"] = include
            project.diagnostics.extend(file.diagnostics)
            self._index_file_includes(project, filename, file)
        self._index_header_source_pairs(project)
        resolve_project_types(project)
        normalized_functions = self._deduplicate_functions(all_functions, project.diagnostics)
        for function in normalized_functions:
            project.functions[function.name] = function
        for function in project.functions.values():
            self._append_union_by_value_diagnostics(function, project.diagnostics)
        return project

    def _index_struct(
        self,
        project: CProject,
        struct: CStruct,
        diagnostics: list[CDiagnostic],
    ) -> None:
        """Index a named struct tag, completing an earlier incomplete tag."""
        if struct.name is None:
            return
        existing = project.structs.get(struct.name)
        if existing is None or (existing.is_incomplete and not struct.is_incomplete):
            project.structs[struct.name] = struct
        elif not existing.is_incomplete and not struct.is_incomplete:
            diagnostics.append(
                self._redeclaration_diagnostic(
                    "C_DUPLICATE_TAG_DEFINITION",
                    f"Duplicate definition for struct tag {struct.name!r}.",
                    struct.source_location,
                    "struct",
                    struct.name,
                )
            )

    def _index_union(
        self,
        project: CProject,
        union: CUnion,
        diagnostics: list[CDiagnostic],
    ) -> None:
        """Index a named union tag, completing an earlier incomplete tag."""
        if union.name is None:
            return
        existing = project.unions.get(union.name)
        if existing is None or (existing.is_incomplete and not union.is_incomplete):
            project.unions[union.name] = union
        elif not existing.is_incomplete and not union.is_incomplete:
            diagnostics.append(
                self._redeclaration_diagnostic(
                    "C_DUPLICATE_TAG_DEFINITION",
                    f"Duplicate definition for union tag {union.name!r}.",
                    union.source_location,
                    "union",
                    union.name,
                )
            )

    def _index_enum(
        self,
        project: CProject,
        enum: CEnum,
        diagnostics: list[CDiagnostic],
    ) -> None:
        """Index a named enum tag and report duplicate definitions."""
        if enum.name is None:
            return
        existing = project.enums.get(enum.name)
        if existing is None:
            project.enums[enum.name] = enum
        else:
            diagnostics.append(
                self._redeclaration_diagnostic(
                    "C_DUPLICATE_TAG_DEFINITION",
                    f"Duplicate definition for enum tag {enum.name!r}.",
                    enum.source_location,
                    "enum",
                    enum.name,
                )
            )

    def _include_graph_target(
        self,
        parsed_files: dict[str, CFile],
        filename: str,
        target: str,
        resolved_path: str | None,
    ) -> str:
        """Choose the project include-graph key for an include target."""
        local_key = _include_key_from_current(filename, target)
        if local_key in parsed_files:
            return local_key

        basename_matches = [key for key in parsed_files if PurePosixPath(key).name == target]
        if len(basename_matches) == 1:
            return basename_matches[0]

        if resolved_path:
            resolved_name = Path(resolved_path).name
            resolved_matches = [key for key in parsed_files if PurePosixPath(key).name == resolved_name]
            if len(resolved_matches) == 1:
                return resolved_matches[0]
            return str(Path(resolved_path))

        return local_key

    def _index_file_includes(
        self,
        project: CProject,
        filename: str,
        file: CFile,
    ) -> None:
        """Populate include facts without extending the parsed input set."""
        local_targets: set[str] = set()
        system_targets: set[str] = set()
        unresolved_targets: set[str] = set()

        for include in file.includes:
            if include.kind == "system":
                system_targets.add(include.target)
                continue

            target = self._include_graph_target(
                project.files,
                filename,
                include.target,
                include.resolved_path,
            )
            local_targets.add(target)
            if include.resolved_path is None and target not in project.files:
                unresolved_targets.add(include.target)

        project.include_graph[filename] = local_targets
        project.system_includes[filename] = system_targets
        project.unresolved_includes[filename] = unresolved_targets

    def _index_header_source_pairs(self, project: CProject) -> None:
        """Populate reporting-only header/source relationships."""
        headers = [key for key in project.files if _is_header_key(key)]
        sources = [key for key in project.files if _is_source_key(key)]

        for header in headers:
            project.header_source_pairs.setdefault(header, set())

        for header in headers:
            header_path = PurePosixPath(header)
            header_stem = header_path.with_suffix("")
            for source in sources:
                source_path = PurePosixPath(source)
                if source_path.with_suffix("") == header_stem:
                    project.header_source_pairs[header].add(source)

        for source in sources:
            for included in project.include_graph.get(source, set()):
                if included in project.files and _is_header_key(included):
                    project.header_source_pairs.setdefault(included, set()).add(source)


_DEFAULT_PARSER = CParser()


# -----------------------------------------------------------------------------
# Module-level convenience wrappers
# -----------------------------------------------------------------------------


def parse_c_file(
    source_or_path: str | Path,
    filename: str | None = None,
    *,
    include_dirs: Sequence[str | Path] | None = None,
    preprocessing: str = "raw",
    encoding: str = "utf-8",
) -> CFile:
    """Parse one C source string/path using the default parser instance.

    Example:
        >>> parse_c_file("int answer(void);", filename="api.h").functions[0].name
        'answer'
    """
    return _DEFAULT_PARSER.parse_file(
        source_or_path,
        filename=filename,
        include_dirs=include_dirs,
        preprocessing=preprocessing,
        encoding=encoding,
    )


def parse_c_project(
    files: Mapping[str, str] | Sequence[str | Path] | str | Path,
    *,
    include_dirs: Sequence[str | Path] | None = None,
    preprocessing: str = "raw",
    encoding: str = "utf-8",
) -> CProject:
    """Parse multiple C files or a directory using the default parser instance.

    Example:
        >>> project = parse_c_project({"api.h": "int answer(void);"})
        >>> sorted(project.functions)
        ['answer']
    """
    return _DEFAULT_PARSER.parse_project(
        files,
        include_dirs=include_dirs,
        preprocessing=preprocessing,
        encoding=encoding,
    )
