"""Wrapper-oriented Fortran parser with class-based grammar-unit visitors.

Read the module-level wrappers at the bottom first, then `FortranParser`
public parse entrypoints, source-unit visitors, `_helper_*` parsing methods, and
finally low-level lexical/static utilities. The detailed maintainer guide
below documents the same file order with a control-flow example.
"""

from __future__ import annotations

import ast
import re
from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path

from prik.utilities.visitor import ClassVisitor

from prik.parsers.fortran.lexer import preprocess_lines
from prik.parsers.fortran.models import (
    FortranArgument,
    FortranBlockData,
    FortranDerivedType,
    FortranEnum,
    FortranEnumerator,
    FortranFile,
    FortranInterface,
    FortranModule,
    FortranParseError,
    FortranProcedureSignature,
    FortranProgram,
    FortranProject,
    FortranSubmodule,
    FortranUseMapping,
    FortranVariable,
)
from prik.parsers.fortran.type_resolver import extract_kind_from_type_spec
from prik.parsers.fortran.utils import split_csv

_PARSER_ARCHITECTURE_GUIDE = """
Parser architecture quick guide
===============================

This module is intentionally centered on two public surfaces:

1) `FortranParser`
   - Stateful orchestration layer that runs block parsers, owns parser helper
     methods, and aggregates file/project models.

2) Module-level wrappers
   - Small convenience entrypoints (`parse_fortran_file`,
     `parse_fortran_project`) backed by one default parser instance.

Recommended reading order for maintainers:
- Start from the module-level public wrappers (`parse_fortran_file`,
  `parse_fortran_project`)
- Then read `FortranParser.parse_file` / `parse_project`
- Then read the high-level `_visit_<ClassName>` methods at the top of the class
- Then drill into `_helper_*` implementations and low-level helpers

`FortranParser` class layout (top -> bottom):
- Public `parse_*` entrypoints.
- One `_visit_<ClassName>` handler per grammar-level source-unit model.
- Source preparation, preprocessor handling, source-unit slicing, and unit
  grammar helpers.
- Header parsers, scope/state helpers, specification visitors, declaration
  parsing, finalization, and kind/shape resolution.
- Project diagnostics and general lexical/static utilities.
- Final module-level convenience wrappers using `_DEFAULT_PARSER`.

The parser flow is intentionally grammar-shaped. Given this source:

    module m
      integer, parameter :: n = 4
    contains
      subroutine scale(x)
        real :: x(n)
      end subroutine scale
    end module m

`parse_file` preprocesses lines, validates obvious malformed headers, and calls
`_helper_slice_child_units` to create one file-level `ModuleUnit`. The
`_visit_ModuleUnit` handler then receives only that substring,
splits it into header/specification/contains with `_helper_split_unit_parts`,
visits the module specification part in a module scope, and recursively slices
its direct children. The contained procedure is dispatched to
`_visit_ProcedureUnit`, which creates a procedure scope and visits only its
specification part; the execution part and internal subprograms are ignored for
wrapper metadata. Internal subprogram boundaries are still sliced so malformed
unit structure is rejected before their contents are skipped.

Scoping follows the same recursion. A helper that parses `integer :: n` or
`real :: x(n)` receives a `_ParserScope` argument. The shared declaration parser
builds the same metadata for variables, procedure arguments/results, and
derived-type fields; `_helper_push_declaration_to_scope` stores the symbol in
the current scope model. This is why the same derived-type name can exist in
two modules, while duplicate names at one sibling level are rejected by the
slicer validation.
"""

_REGEX: dict[str, re.Pattern[str]] = {
    "type": re.compile(
        r"^(integer|real|complex|logical|character|double\s+(?:precision|complex))\b\s*(\([^)]*\))?\s*(.*)$",
        re.IGNORECASE,
    ),
    "char_star": re.compile(r"^character\s*\*\s*(?P<len>\([^)]*\)|\*|[A-Za-z_]\w*|\d+)\s*(?P<rest>.*)$", re.IGNORECASE),
    "procedure": re.compile(
        r"^(?P<prefix>(?:\w+\s+)*)subroutine\s+(?P<name>\w+)(?:\s*\((?P<args>[^)]*)\))?\s*(?P<tail>.*)$", re.IGNORECASE
    ),
    "function": re.compile(
        r"^(?P<prefix>.*?)\b"
        r"function\s+(?P<name>\w+)(?:\s*\((?P<args>[^)]*)\))?\s*(?P<tail>.*)$",
        re.IGNORECASE,
    ),
    "result": re.compile(r"results?\s*\(\s*(?P<name>\w+)\s*\)", re.IGNORECASE),
    "bind_c": re.compile(
        r"bind\s*\(\s*c\s*(?:,\s*name\s*=\s*(?P<quote>['\"])(?P<name>[^'\"]*)(?P=quote))?\s*\)",
        re.IGNORECASE,
    ),
    "use": re.compile(
        r"^use\s*(?:,\s*(?:intrinsic|non_intrinsic)\s*)?(?:::)?\s*(?P<module>\w+)\s*(?P<rest>,\s*.*)?$",
        re.IGNORECASE,
    ),
    "include": re.compile(r"^(?:#\s*)?include\s*(?P<path>['\"][^'\"]+['\"])", re.IGNORECASE),
    "import": re.compile(r"^import\s*(?:::)?\s*(?P<symbols>.*)$", re.IGNORECASE),
    "typed_parameter": re.compile(
        r"^(integer|real|logical|character|complex)\s*(?:\([^)]*\))?\s*,\s*parameter\s*::\s*(?P<body>.*)$",
        re.IGNORECASE,
    ),
    "legacy_parameter": re.compile(r"^parameter\s*\(\s*(?P<body>.*)\s*\)$", re.IGNORECASE),
    "derived_type": re.compile(r"^type\s*(?P<attrs>(?:,\s*[^:]+)?)::\s*(?P<name>\w+)(?:\s*\([^)]*\))?$", re.IGNORECASE),
    "type_field": re.compile(r"^type\s*\(\s*(?P<dtype>\w+(?:\s*\([^)]*\))?)\s*\)\s*(?P<attrs>.*)$", re.IGNORECASE),
    "class_field": re.compile(r"^class\s*\(\s*(?P<dtype>\w+(?:\s*\([^)]*\))?)\s*\)\s*(?P<attrs>.*)$", re.IGNORECASE),
    "procedure_binding": re.compile(r"^procedure\s*(?:,\s*[^:]*)?::\s*(?P<names>.*)$", re.IGNORECASE),
    "procedure_dummy": re.compile(r"^procedure\s*\(\s*(?P<iface>\w+)\s*\)\s*(?P<attrs>.*)$", re.IGNORECASE),
    "module": re.compile(r"^module\s+(?P<name>\w+)\s*$", re.IGNORECASE),
    "submodule": re.compile(r"^submodule\s*\(\s*(?P<parent>[^)]+?)\s*\)\s*(?P<name>\w+)\s*$", re.IGNORECASE),
    "module_procedure_impl": re.compile(r"^module\s+procedure\s+(?P<name>\w+)\s*$", re.IGNORECASE),
    "program": re.compile(r"^program\s+(?P<name>\w+)\s*$", re.IGNORECASE),
    "block_data": re.compile(r"^block\s+data(?:\s+(?P<name>\w+))?\s*$", re.IGNORECASE),
    "unsupported_class_star": re.compile(r"\bclass\s*\(\s*\*\s*\)", re.IGNORECASE),
    "unsupported_select_type": re.compile(r"\bselect\s+type\b", re.IGNORECASE),
    "unsupported_coarray": re.compile(r"\bcoarray\b|\[[^\]]*\]", re.IGNORECASE),
    "unsupported_procedure_pointer": re.compile(r"\bprocedure\s*,\s*pointer\b", re.IGNORECASE),
    "unsupported_c_ptr": re.compile(r"\btype\s*\(\s*c_ptr\s*\)", re.IGNORECASE),
    "identifier": re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b"),
}
_ATTR_PREFIX_WORDS = {"pure", "elemental", "recursive", "impure", "module"}
_UNSUPPORTED_PATTERN_KEYS = (
    "unsupported_class_star",
    "unsupported_select_type",
    "unsupported_coarray",
    "unsupported_procedure_pointer",
    "unsupported_c_ptr",
)
_FORTRAN_LINEMARKER_RE = re.compile(
    r'^\s*#\s*(?:line\s+)?\d+(?:\s+(?:"(?:[^"\\]|\\.)*"|\S+))?(?:\s+\d+)*\s*$',
    re.IGNORECASE,
)
_INTRINSIC_COMPILE_TIME_MODULES = frozenset({"iso_c_binding", "iso_fortran_env"})


_PreprocessedLines = list[tuple[str, int | None, str | None]]
_SourceOrLines = str | _PreprocessedLines


@dataclass(frozen=True)
class SourceUnit:
    """Represent one recursively sliced Fortran grammar unit.

    The slicer retains the unit's normalized lines and original source bounds
    so visitors can parse a local region without losing diagnostic locations.
    Concrete subclasses select the matching ``_visit_*`` handler.
    """

    kind: str
    name: str | None
    lines: _PreprocessedLines
    start_line: int | None
    end_line: int | None


@dataclass(frozen=True)
class ModuleUnit(SourceUnit):
    """A sliced module source unit."""


@dataclass(frozen=True)
class SubmoduleUnit(SourceUnit):
    """A sliced submodule source unit."""


@dataclass(frozen=True)
class ProgramUnit(SourceUnit):
    """A sliced program source unit."""


@dataclass(frozen=True)
class BlockDataUnit(SourceUnit):
    """A sliced block-data source unit."""


@dataclass(frozen=True)
class DerivedTypeUnit(SourceUnit):
    """A sliced derived-type source unit."""


@dataclass(frozen=True)
class InterfaceUnit(SourceUnit):
    """A sliced interface source unit."""


@dataclass(frozen=True)
class ProcedureUnit(SourceUnit):
    """A sliced procedure source unit."""


@dataclass(frozen=True)
class EnumUnit(SourceUnit):
    """A sliced enum source unit."""


_SOURCE_UNIT_TYPES = {
    "module": ModuleUnit,
    "submodule": SubmoduleUnit,
    "program": ProgramUnit,
    "block_data": BlockDataUnit,
    "derived_type": DerivedTypeUnit,
    "interface": InterfaceUnit,
    "procedure": ProcedureUnit,
    "enum": EnumUnit,
}


@dataclass
class _ParserScope:
    """Carry explicit ownership and mutable state while visiting one unit.

    ``model`` receives parsed declarations, ``parent`` preserves lexical
    ownership, and procedure visitors use ``state`` for their temporary symbol
    table.  Helpers receive this record explicitly rather than relying on
    parser-global scope.
    """

    kind: str
    name: str | None
    model: object | None = None
    parent: _ParserScope | None = None
    module_owner: str | None = None
    state: dict | None = None


@dataclass(frozen=True)
class _UnitGrammar:
    """Describe the regions and declaration role allowed by one unit kind."""

    kind: str
    has_execution_part: bool = False
    has_contains_part: bool = False
    ignores_contains_children: bool = False
    declaration_role: str | None = None


@dataclass(frozen=True)
class _UnitParts:
    """Store a sliced unit's header, grammar regions, and optional footer.

    The four regions retain their original line mappings.  Visitors parse only
    the regions supported by their corresponding :class:`_UnitGrammar`.
    """

    header: tuple[str, int | None, str | None] | None
    specification: _PreprocessedLines
    execution: _PreprocessedLines
    contains: _PreprocessedLines
    footer: tuple[str, int | None, str | None] | None


@dataclass
class _ParsedFileUnits:
    """Accumulate visited file-level models before building ``FortranFile``.

    Interface procedures remain attached to their interface rather than the
    standalone-procedure list; all other collections preserve source order.
    """

    modules: list[FortranModule]
    submodules: list[FortranSubmodule]
    programs: list[FortranProgram]
    block_data_units: list[FortranBlockData]
    procedures: list[FortranProcedureSignature]
    interfaces: list[FortranInterface]
    derived_types: list[FortranDerivedType]


# -----------------------------------------------------------------------------
# Compile-time expression and symbol resolution
# -----------------------------------------------------------------------------


class _CompileTimeResolver:
    """Resolve compile-time expressions against one immutable symbol snapshot."""

    def __init__(self, symbols: dict[str, str]):
        """Normalize symbol names and initialize the expression cache."""
        self.symbols = {name.lower(): str(value) for name, value in symbols.items()}
        self.cache: dict[tuple[str, bool], str] = {}

    def resolve(self, expr: str, prefer_symbolic: bool = True, resolving: frozenset[str] = frozenset()) -> str:
        """Resolve symbols in one expression and fold integer-only results."""
        text = expr.strip()
        if not text:
            return expr
        cache_key = (text, prefer_symbolic)
        if cache_key in self.cache:
            return self.cache[cache_key]

        if ":" in text:
            parts = text.split(":")
            resolved = ":".join(self.resolve(p, prefer_symbolic=prefer_symbolic) if p.strip() else p for p in parts)
            self.cache[cache_key] = resolved
            return resolved

        replaced = text
        max_passes = max(8, len(self.symbols) * 2)
        for _ in range(max_passes):
            changed = False

            def replace_symbol(match: re.Match[str]) -> str:
                """Replace one resolvable symbol while detecting cycles."""
                nonlocal changed
                token = match.group(0)
                key = token.lower()
                if key not in self.symbols or key in resolving:
                    return token
                resolved_value = self.resolve(
                    self.symbols[key],
                    prefer_symbolic=False,
                    resolving=resolving | {key},
                )
                if prefer_symbolic and FortranParser._safe_eval_int_expr(resolved_value) is None:
                    return token
                changed = True
                return f"({resolved_value})"

            updated = _REGEX["identifier"].sub(replace_symbol, replaced)
            if not changed or updated == replaced:
                break
            replaced = updated

        evaluated = FortranParser._safe_eval_int_expr(replaced)
        resolved = str(evaluated) if evaluated is not None else (replaced if replaced != text else text)
        self.cache[cache_key] = resolved
        return resolved


class FortranParser(ClassVisitor):
    """Stateful parser entrypoint and orchestration object.

    Raw parser entrypoints preserve all CPP branch alternatives. Branch
    selection belongs to the compiler preprocessing layer.

    Parsing pipeline used by `parse_file`:
    1. Preprocess source into normalized lines (`_preprocessed_lines`).
    2. Slice direct file-level source units (`module`, `submodule`,
       `program`, standalone `procedure`, `block data`, file-level
       `interface`, and file-level derived type).
    3. Dispatch each `SourceUnit` through its `_visit_<ClassName>` handler.
    4. Each unit visitor parses only that unit's own substring, builds its own
       `_ParserScope`, splits the unit into grammar regions, visits the
       specification part, and recursively slices direct children where the
       grammar allows them.
    5. Shared declaration helpers push variables, procedure symbols, and type
       fields into the active scope model.
    6. Build `FortranFile` symbol table and standalone entity lists.

    Class section map:
    - Public parse entrypoints first.
    - Unit visitors next (one `_visit_<ClassName>` method per unit model).
    - Internal `_helper_*` methods after that (reusable scoped parsing logic).
    - Lower-level declaration/header helpers and assembly utilities last.

    Scope behavior summary:
    - `_ParserScope` is passed explicitly into shared helpers; there is no
      ambient `current_module` or interface stack.
    - Module/submodule scopes own contained procedures, interfaces, and derived
      types; program and block-data scopes collect their specification
      variables only.
    - Procedure scopes parse only wrapper-relevant specification declarations;
      execution statements and internal procedures after `contains` are
      ignored, except procedure-local interfaces are revisited to type callback
      dummy arguments.
    - Derived-type scopes parse fields in the specification region and
      type-bound procedure/generic bindings in the `contains` region.
    - Same-level unit names are validated by the slicer, while identical names
      in different scopes remain valid.

    `parse_project` composes multiple `FortranFile` objects into one
    `FortranProject` registry and validates duplicate symbols by scope.
    """

    # ------------------------------------------------------------------
    # Public parse entrypoints
    # ------------------------------------------------------------------

    def parse_file(
        self,
        source_or_path: str | Path,
        filename: str | None = None,
        encoding: str = "utf-8",
    ) -> FortranFile:
        """Parse one source string or path into a ``FortranFile`` model.

        Use this primary entrypoint for one Fortran translation unit.  A path
        is read with ``encoding`` when ``filename`` is omitted; otherwise the
        input is treated as source text and ``filename`` supplies diagnostic
        provenance.  The returned parse-only model feeds project parsing or
        semantic conversion and raises :class:`FortranParseError` for malformed
        or unsupported wrapper-relevant syntax.
        """

        # Stage 1: obtain normalized input and slice direct file-level units.
        code, filename = self._helper_read_source(source_or_path, filename, encoding)
        lines, root_scope, top_units = self._helper_prepare_source_units(code, filename)

        # Stage 2: visit each unit and attach cross-unit parser facts.
        units = self._helper_parse_file_units(top_units, root_scope, filename)
        self._helper_resolve_file_types(units)
        interfaces = self._helper_attach_file_interfaces(lines, filename, units)
        self._helper_resolve_file_kinds(lines, filename, units)

        # Stage 3: assemble the stable file model and its source metadata.
        return self._helper_build_fortran_file(code, filename, encoding, units, interfaces)

    def parse_project(
        self,
        files: dict[str, str] | list[str | Path] | tuple[str | Path, ...] | str | Path,
        *,
        encoding: str = "utf-8",
    ) -> FortranProject:
        """Parse explicit sources or paths into one dependency-aware project.

        Use this after collecting a related set of files, or pass a directory
        for the supported Fortran source forms.  The parser preserves the file
        models while resolving project-level kind references and indexing
        modules, procedures, and types.  Duplicate project symbols and source
        failures raise :class:`FortranParseError`.
        """

        # Stage 1: parse each requested source in dependency-aware order.
        parsed_files = self._helper_parse_project_files(files, encoding)

        # Stage 2: complete cross-file kinds and construct project indexes.
        self._helper_resolve_project_kinds(parsed_files)
        project = FortranProject(files=parsed_files)
        for parsed_file in parsed_files:
            self._helper_index_project_file(project, parsed_file)
        return project

    def parse_module(self, code: _SourceOrLines, filename: str | None = None) -> FortranModule:
        """Parse exactly one module unit from source text or normalized lines.

        Use this narrow entrypoint when the caller expects a single module
        rather than a whole ``FortranFile``.  Its result includes module
        variables, imports, contained procedures, interfaces, and derived
        types.  Inputs with zero or multiple module units raise
        :class:`FortranParseError`.

        Example:
            >>> FortranParser().parse_module("module m\\nend module m\\n").name
            'm'
        """
        _lines, root_scope, all_units = self._helper_prepare_source_units(code, filename)
        module_units = [unit for unit in all_units if unit.kind == "module"]
        if not module_units and any(unit.kind == "procedure" for unit in all_units):
            raise FortranParseError(
                "parse_module() expected a module program unit, but only standalone procedures were found",
                filename=filename,
                code="PARSE_WRONG_ENTRYPOINT",
            )
        unit = self._expect_single_parse_result(
            module_units,
            parser_name="parse_module",
            entity_name="module",
            filename=filename,
        )
        return self._visit(unit, parent_scope=root_scope, filename=filename)

    def parse_submodule(self, code: _SourceOrLines, filename: str | None = None) -> FortranSubmodule:
        """Parse exactly one submodule from source text or normalized lines.

        Use this narrow entrypoint when a caller already knows the input is one
        submodule.  It returns the submodule's parent/ancestor metadata and
        wrapper-relevant specification facts, rejecting zero or multiple
        submodule units with :class:`FortranParseError`.
        """
        _lines, root_scope, all_units = self._helper_prepare_source_units(code, filename)
        unit = self._expect_single_parse_result(
            [unit for unit in all_units if unit.kind == "submodule"],
            parser_name="parse_submodule",
            entity_name="submodule",
            filename=filename,
        )
        return self._visit(unit, parent_scope=root_scope, filename=filename)

    def parse_interface(self, code: _SourceOrLines, filename: str | None = None) -> FortranInterface:
        """Parse exactly one interface block and its procedure declarations.

        Use this for an isolated interface source fragment.  The returned
        model preserves generic specifics and interface-only procedure facts;
        source containing zero or multiple interface blocks raises
        :class:`FortranParseError`.
        """
        unit, scope = self._expect_single_parse_result(
            self._collect_interface_source_units(code, filename),
            parser_name="parse_interface",
            entity_name="interface",
            filename=filename,
        )
        return self._visit(unit, parent_scope=scope, filename=filename)

    def parse_derived_type(self, code: _SourceOrLines, filename: str | None = None) -> FortranDerivedType:
        """Parse exactly one derived type and its wrapper-relevant fields.

        Use this for an isolated ``type`` definition or a containing source
        with one discoverable derived type.  The result includes inheritance,
        fields, and type-bound declarations; ambiguous input raises
        :class:`FortranParseError`.
        """
        unit, scope = self._expect_single_parse_result(
            self._collect_derived_type_source_units(code, filename),
            parser_name="parse_derived_type",
            entity_name="derived type",
            filename=filename,
        )
        return self._visit(unit, parent_scope=scope, filename=filename)

    def parse_program(self, code: _SourceOrLines, filename: str | None = None) -> FortranProgram:
        """Parse exactly one program unit and its specification declarations.

        Use this when inspecting a single main program.  Executable statements
        are intentionally not represented, while declarations, imports, and
        supported enumerations become parser facts.  Ambiguous input raises
        :class:`FortranParseError`.
        """
        _lines, root_scope, all_units = self._helper_prepare_source_units(code, filename)
        unit = self._expect_single_parse_result(
            [unit for unit in all_units if unit.kind == "program"],
            parser_name="parse_program",
            entity_name="program",
            filename=filename,
        )
        return self._visit(unit, parent_scope=root_scope, filename=filename)

    def parse_block_data(self, code: _SourceOrLines, filename: str | None = None) -> FortranBlockData:
        """Parse exactly one block-data unit and its specification declarations.

        Use this narrow entrypoint for a single ``block data`` source unit.
        It returns common-block and variable facts but no execution model, and
        raises :class:`FortranParseError` when the input is not singular.
        """
        _lines, root_scope, all_units = self._helper_prepare_source_units(code, filename)
        unit = self._expect_single_parse_result(
            [unit for unit in all_units if unit.kind == "block_data"],
            parser_name="parse_block_data",
            entity_name="block data unit",
            filename=filename,
        )
        return self._visit(unit, parent_scope=root_scope, filename=filename)

    # ------------------------------------------------------------------
    # Source unit visitors
    # ------------------------------------------------------------------

    def _visit_ModuleUnit(
        self,
        unit: ModuleUnit,
        *,
        parent_scope: _ParserScope,
        filename: str | None,
    ) -> FortranModule:
        """Visit a sliced `module ... end module` unit."""
        header = unit.lines[0]
        module = self._parse_module_header(header[0].strip(), filename, lineno=header[1], source_line=header[2])
        if module is None:  # pragma: no cover - slicer only dispatches module units with module headers.
            raise FortranParseError(
                "Expected module unit.",
                filename=filename,
                line_number=header[1],
                source_line=header[2],
                code="PARSE_EXPECTED_UNIT",
            )
        scope = self._helper_scope_for_model("module", module, parent=parent_scope)
        parts = self._helper_split_unit_parts(unit, self._helper_unit_grammar("module"), filename=filename)
        self._parse_specification_part(scope, parts.specification, filename=filename)

        child_units = self._helper_slice_child_units(unit.lines[1:-1], parent_scope=scope, filename=filename)
        self._helper_validate_child_unit_regions(unit, parts, child_units, filename=filename)
        self._helper_validate_contains_lines(scope, parts.contains, filename=filename)
        self._helper_validate_sibling_units(child_units, parent_scope=scope, filename=filename)
        self._populate_module_like_children(module, child_units, scope=scope, filename=filename)
        self._validate_module_variables(module, filename)
        self._apply_module_visibility(module, filename)
        return module

    def _visit_SubmoduleUnit(
        self,
        unit: SubmoduleUnit,
        *,
        parent_scope: _ParserScope,
        filename: str | None,
    ) -> FortranSubmodule:
        """Visit a sliced `submodule (...) name ... end submodule` unit."""
        header = unit.lines[0]
        submodule = self._parse_submodule_header(header[0].strip(), filename)
        if submodule is None:  # pragma: no cover - slicer only dispatches submodule units with submodule headers.
            raise FortranParseError(
                "Expected submodule unit.",
                filename=filename,
                line_number=header[1],
                source_line=header[2],
                code="PARSE_EXPECTED_UNIT",
            )
        scope = self._helper_scope_for_model("submodule", submodule, parent=parent_scope)
        parts = self._helper_split_unit_parts(unit, self._helper_unit_grammar("submodule"), filename=filename)
        self._parse_specification_part(scope, parts.specification, filename=filename)

        child_units = self._helper_slice_child_units(unit.lines[1:-1], parent_scope=scope, filename=filename)
        self._helper_validate_child_unit_regions(unit, parts, child_units, filename=filename)
        self._helper_validate_contains_lines(scope, parts.contains, filename=filename)
        self._helper_validate_sibling_units(child_units, parent_scope=scope, filename=filename)
        self._populate_module_like_children(submodule, child_units, scope=scope, filename=filename)
        self._validate_module_variables(submodule, filename)
        return submodule

    def _parse_children_of_type(self, child_units, unit_type, *, scope, filename):
        """Visit direct children of one source-unit model class."""
        return [
            self._visit(child, parent_scope=scope, filename=filename)
            for child in child_units
            if isinstance(child, unit_type)
        ]

    @staticmethod
    def _belongs_to_module_like(item, target, *, exclude_interface: bool = False) -> bool:
        """Return whether one visited model belongs to a module-like owner.

        Ownership comparison is case-insensitive, matching Fortran naming.
        ``exclude_interface`` keeps interface procedure signatures attached to
        their interface instead of duplicating them in ``target.procedures``.
        """
        belongs = bool(item.module and item.module.lower() == target.name.lower())
        return belongs and not (exclude_interface and item.in_interface)

    def _populate_module_like_children(self, target, child_units, *, scope, filename) -> None:
        """Visit direct children and append the ones owned by ``target``.

        The method preserves source order within each child category and shares
        the caller's scope/filename for diagnostics.  Interface-contained
        procedure declarations are deliberately excluded from a module's
        standalone procedure collection.
        """
        signatures = self._parse_children_of_type(child_units, ProcedureUnit, scope=scope, filename=filename)
        types = self._parse_children_of_type(child_units, DerivedTypeUnit, scope=scope, filename=filename)
        interfaces = self._parse_children_of_type(child_units, InterfaceUnit, scope=scope, filename=filename)
        enums = self._parse_children_of_type(child_units, EnumUnit, scope=scope, filename=filename)
        target.procedures.extend(
            item for item in signatures if self._belongs_to_module_like(item, target, exclude_interface=True)
        )
        target.derived_types.extend(item for item in types if self._belongs_to_module_like(item, target))
        target.interfaces.extend(item for item in interfaces if self._belongs_to_module_like(item, target))
        target.enums.extend(item for item in enums if self._belongs_to_module_like(item, target))

    def _visit_ProgramUnit(
        self,
        unit: ProgramUnit,
        *,
        parent_scope: _ParserScope,
        filename: str | None,
    ) -> FortranProgram:
        """Visit a sliced `program ... end program` unit."""
        header = unit.lines[0]
        program = self._parse_program_header(header[0].strip(), filename)
        if program is None:  # pragma: no cover - slicer only dispatches program units with program headers.
            raise FortranParseError(
                "Expected program unit.",
                filename=filename,
                line_number=header[1],
                source_line=header[2],
                code="PARSE_EXPECTED_UNIT",
            )
        scope = self._helper_scope_for_model("program", program, parent=parent_scope)
        parts = self._helper_split_unit_parts(unit, self._helper_unit_grammar("program"), filename=filename)
        self._parse_specification_part(scope, parts.specification, filename=filename)
        child_units = self._helper_nonexecution_child_units(unit, parent_scope=scope, filename=filename)
        self._helper_validate_child_unit_regions(unit, parts, child_units, filename=filename)
        self._helper_validate_contains_lines(scope, parts.contains, filename=filename)
        self._helper_validate_ignored_child_units(
            [child for child in child_units if child.kind != "enum"],
            parent_scope=scope,
            filename=filename,
            unit=unit,
            parts=parts,
        )
        program.enums.extend(
            self._visit(child, parent_scope=scope, filename=filename) for child in child_units if child.kind == "enum"
        )
        self._validate_variable_declarations(
            program.variables,
            owner_kind="program",
            owner_name=program.name,
            filename=filename,
        )
        return program

    def _visit_BlockDataUnit(
        self,
        unit: BlockDataUnit,
        *,
        parent_scope: _ParserScope,
        filename: str | None,
    ) -> FortranBlockData:
        """Visit a sliced `block data ... end block data` unit."""
        header = unit.lines[0]
        block_data = self._parse_block_data_header(header[0].strip(), filename)
        if block_data is None:  # pragma: no cover - slicer only dispatches block-data units with block-data headers.
            raise FortranParseError(
                "Expected block data unit.",
                filename=filename,
                line_number=header[1],
                source_line=header[2],
                code="PARSE_EXPECTED_UNIT",
            )
        scope = self._helper_scope_for_model("block_data", block_data, parent=parent_scope)
        parts = self._helper_split_unit_parts(unit, self._helper_unit_grammar("block_data"), filename=filename)
        self._parse_specification_part(scope, parts.specification, filename=filename)
        child_units = self._helper_slice_child_units(unit.lines[1:-1], parent_scope=scope, filename=filename)
        self._helper_validate_child_unit_regions(unit, parts, child_units, filename=filename)
        self._validate_variable_declarations(
            block_data.variables,
            owner_kind="block data",
            owner_name=block_data.name,
            filename=filename,
        )
        return block_data

    def _visit_DerivedTypeUnit(
        self,
        unit: DerivedTypeUnit,
        *,
        parent_scope: _ParserScope,
        filename: str | None,
    ) -> FortranDerivedType:
        """Visit a sliced derived-type definition."""
        header = unit.lines[0]
        dtype = self._init_derived_type(header[0].strip(), current_module=parent_scope.module_owner)
        if dtype is None:  # pragma: no cover - slicer only dispatches derived-type units with type headers.
            raise FortranParseError(
                "Expected derived-type unit.",
                filename=filename,
                line_number=header[1],
                source_line=header[2],
                code="PARSE_EXPECTED_UNIT",
            )
        scope = self._helper_scope_for_model("derived_type", dtype, parent=parent_scope)
        parts = self._helper_split_unit_parts(unit, self._helper_unit_grammar("derived_type"), filename=filename)
        self._parse_specification_part(scope, parts.specification, filename=filename)
        for line, lineno, source_line in parts.contains:
            stripped = line.strip()
            if not stripped:
                continue
            self._parse_derived_type_contains_line(
                stripped,
                dtype,
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )
        child_units = self._helper_slice_child_units(unit.lines[1:-1], parent_scope=scope, filename=filename)
        self._helper_validate_child_unit_regions(unit, parts, child_units, filename=filename)
        self._validate_derived_type_fields(dtype, filename)
        return dtype

    def _visit_EnumUnit(
        self,
        unit: EnumUnit,
        *,
        parent_scope: _ParserScope,
        filename: str | None,
    ) -> FortranEnum:
        """Visit an `enum, bind(C)` unit and preserve enumerator constants."""
        return self._helper_parse_enum_unit(unit, filename=filename, module_owner=parent_scope.module_owner)

    def _visit_InterfaceUnit(
        self,
        unit: InterfaceUnit,
        *,
        parent_scope: _ParserScope,
        filename: str | None,
    ) -> FortranInterface:
        """Visit a sliced interface block."""
        header = unit.lines[0]
        starts_interface, interface_name = self._parse_interface_header(header[0].strip())
        if not starts_interface:  # pragma: no cover - slicer only dispatches interface units with interface headers.
            raise FortranParseError(
                "Expected interface unit.",
                filename=filename,
                line_number=header[1],
                source_line=header[2],
                code="PARSE_EXPECTED_UNIT",
            )
        interface = FortranInterface(
            name=interface_name,
            module=parent_scope.module_owner,
            abstract=header[0].strip().lower().startswith("abstract interface"),
        )
        scope = self._helper_scope_for_model("interface", interface, parent=parent_scope)
        parts = self._helper_split_unit_parts(unit, self._helper_unit_grammar("interface"), filename=filename)
        self._helper_validate_interface_lines(scope, parts.specification, filename=filename)
        interface.specific_procedures.extend(self._interface_specific_procedure_names(parts.specification))
        child_units = self._helper_slice_child_units(
            unit.lines[1:-1],
            parent_scope=scope,
            filename=filename,
        )
        for child in child_units:
            if child.kind != "procedure":
                self._raise_invalid_fortran_syntax_line(
                    child.lines[0][0] if child.lines else child.kind,
                    context=f"interface '{scope.name or '<unnamed>'}'",
                    filename=filename,
                    lineno=child.start_line,
                    source_line=child.lines[0][2] if child.lines else None,
                )
            sig = self._visit(child, parent_scope=scope, filename=filename, in_interface=True)
            self._add_interface_attribute(sig, interface.name)
            interface.procedures.append(sig)
        return interface

    @staticmethod
    def _interface_specific_procedure_names(lines: _PreprocessedLines) -> list[str]:
        """Collect specific procedure names declared by a generic interface."""
        names: list[str] = []
        for line, _, _ in lines:
            stripped = line.strip()
            module_procedure = re.match(
                r"^module\s+procedure\s*(?:::)?\s*(?P<names>.+)$",
                stripped,
                re.IGNORECASE,
            )
            if module_procedure:
                names.extend(name.strip() for name in split_csv(module_procedure.group("names")))
                continue
            procedure = re.match(
                r"^procedure(?:\s*\([^)]*\))?(?:\s*,\s*[^:]*)?\s*::\s*(?P<names>.+)$",
                stripped,
                re.IGNORECASE,
            )
            if procedure:
                names.extend(name.strip() for name in split_csv(procedure.group("names")))
        return names

    def _visit_ProcedureUnit(
        self,
        unit: ProcedureUnit,
        *,
        parent_scope: _ParserScope,
        filename: str | None,
        in_interface: bool = False,
    ) -> FortranProcedureSignature:
        """Visit a sliced procedure body or interface procedure declaration."""
        header = unit.lines[0]
        proc_state = self._parse_procedure_header(
            header[0].strip(),
            parent_scope.module_owner,
            in_interface or parent_scope.kind == "interface",
            filename=filename,
            lineno=header[1],
            source_line=header[2],
        )
        if proc_state is None:
            self._raise_if_unparsed_procedure_header(
                header[0].strip(),
                in_interface=in_interface or parent_scope.kind == "interface",
                filename=filename,
                lineno=header[1],
                source_line=header[2],
            )
            raise FortranParseError(
                "Expected procedure unit.",
                filename=filename,
                line_number=header[1],
                source_line=header[2],
                code="PARSE_EXPECTED_UNIT",
            )
        proc_state["filename"] = filename
        proc_state["header_lineno"] = header[1]
        proc_state["header_source_line"] = header[2]
        proc_state["uses"].update(getattr(parent_scope.model, "uses", {}))
        scope = self._helper_scope_for_model(
            "procedure", proc_state["signature"], parent=parent_scope, state=proc_state
        )
        parts = self._helper_split_unit_parts(unit, self._helper_unit_grammar("procedure"), filename=filename)
        self._parse_specification_part(scope, parts.specification, filename=filename)
        child_units = self._helper_nonexecution_child_units(unit, parent_scope=scope, filename=filename)
        self._helper_validate_child_unit_regions(unit, parts, child_units, filename=filename)
        self._helper_validate_contains_lines(scope, parts.contains, filename=filename)
        self._helper_validate_ignored_child_units(
            [child for child in child_units if child.kind != "interface"],
            parent_scope=scope,
            filename=filename,
            unit=unit,
            parts=parts,
        )
        self._helper_apply_local_interface_declarations(proc_state, unit, parts, scope, filename=filename)
        return self._finalize_proc(proc_state)

    # ------------------------------------------------------------------
    # File and project orchestration
    # ------------------------------------------------------------------

    def _helper_read_source(
        self,
        source_or_path: str | Path,
        filename: str | None,
        encoding: str,
    ) -> tuple[str, str | None]:
        """Read a path-like input or preserve an inline source string."""
        if filename is None and self._looks_like_existing_source_path(source_or_path):
            path = Path(source_or_path)
            return path.read_text(encoding=encoding), str(path)
        return str(source_or_path), filename

    def _helper_parse_file_units(
        self,
        top_units: list[SourceUnit],
        root_scope: _ParserScope,
        filename: str | None,
    ) -> _ParsedFileUnits:
        """Visit and collect each direct file-level source unit."""
        parsed = _ParsedFileUnits([], [], [], [], [], [], [])
        for unit in top_units:
            model = self._visit(unit, parent_scope=root_scope, filename=filename)
            self._helper_append_file_unit(parsed, model)
        return parsed

    @staticmethod
    def _helper_append_file_unit(parsed: _ParsedFileUnits, model: object) -> None:
        """Append one visited model to its file-level collection."""
        if isinstance(model, FortranModule):
            parsed.modules.append(model)
        elif isinstance(model, FortranSubmodule):
            parsed.submodules.append(model)
        elif isinstance(model, FortranProgram):
            parsed.programs.append(model)
        elif isinstance(model, FortranBlockData):
            parsed.block_data_units.append(model)
        elif isinstance(model, FortranProcedureSignature):
            if not model.in_interface:
                parsed.procedures.append(model)
        elif isinstance(model, FortranInterface):
            parsed.interfaces.append(model)
        elif isinstance(model, FortranDerivedType):
            parsed.derived_types.append(model)

    def _helper_resolve_file_types(self, units: _ParsedFileUnits) -> None:
        """Resolve derived-type extension links across file-level owners."""
        all_types = [
            *units.derived_types,
            *(dtype for module in units.modules for dtype in module.derived_types),
            *(dtype for submodule in units.submodules for dtype in submodule.derived_types),
        ]
        self._resolve_derived_type_extensions(all_types)

    def _helper_attach_file_interfaces(
        self,
        lines: _PreprocessedLines,
        filename: str | None,
        units: _ParsedFileUnits,
    ) -> list[FortranInterface]:
        """Collect interfaces and attach module-owned blocks to their owners."""
        interfaces = [
            self._visit(unit, parent_scope=scope, filename=filename)
            for unit, scope in self._collect_interface_source_units(lines, filename)
        ]
        for module in units.modules:
            module.interfaces = [
                iface for iface in interfaces if iface.module and iface.module.lower() == module.name.lower()
            ]
        for submodule in units.submodules:
            submodule.interfaces = [
                iface for iface in interfaces if iface.module and iface.module.lower() == submodule.name.lower()
            ]
        return [iface for iface in interfaces if iface.module is None]

    def _helper_resolve_file_kinds(
        self,
        lines: _PreprocessedLines,
        filename: str | None,
        units: _ParsedFileUnits,
    ) -> None:
        """Resolve variable and procedure kind references within one file."""
        variable_units = [*units.modules, *units.submodules, *units.programs, *units.block_data_units]
        module_params = self._collect_module_parameters(lines, filename)
        if any(
            var.kind or var.value is not None or var.symbolic_value is not None
            for unit in variable_units
            for var in getattr(unit, "variables", [])
        ):
            for unit in variable_units:
                self._resolve_module_variable_kinds(unit, module_params)
        for procedure in self._helper_file_procedures(units):
            self._resolve_signature_kinds(procedure, module_params, resolve_shapes=False)

    @staticmethod
    def _helper_file_procedures(units: _ParsedFileUnits):
        """Yield file procedures in their established resolution order."""
        yield from units.procedures
        for module in units.modules:
            yield from module.procedures
        for submodule in units.submodules:
            yield from submodule.procedures

    def _helper_build_fortran_file(
        self,
        code: str,
        filename: str | None,
        encoding: str,
        units: _ParsedFileUnits,
        interfaces: list[FortranInterface],
    ) -> FortranFile:
        """Build the file aggregate and its direct symbol registry."""
        parsed_file = FortranFile(
            filename=filename,
            source=code,
            encoding=encoding,
            format=self._source_form(filename),
            modules=units.modules,
            submodules=units.submodules,
            programs=units.programs,
            block_data_units=units.block_data_units,
            procedures=units.procedures,
            interfaces=interfaces,
            derived_types=[dtype for dtype in units.derived_types if dtype.module is None],
        )
        for model in [*units.modules, *units.submodules, *units.procedures]:
            self._insert_unique_scope_symbol(
                parsed_file.symbols,
                model.name.lower(),
                model,
                label="file scope",
                filename=filename,
            )
        return parsed_file

    def _helper_parse_project_files(
        self,
        files: dict[str, str] | list[str | Path] | tuple[str | Path, ...] | str | Path,
        encoding: str,
    ) -> list[FortranFile]:
        """Normalize project inputs and parse each source file."""
        if isinstance(files, dict):
            return [self.parse_file(code, filename=fname, encoding=encoding) for fname, code in files.items()]
        if isinstance(files, str | Path):
            namespace = self._helper_collect_namespace(files, encoding=encoding)
            return [self.parse_file(path, encoding=encoding) for path in namespace["files"]]
        return [self.parse_file(path, encoding=encoding) for path in files]

    def _helper_resolve_project_kinds(self, parsed_files: list[FortranFile]) -> None:
        """Resolve project procedure and module-variable kinds from shared symbols."""
        module_params = self._helper_project_module_symbols(parsed_files)

        seen_procedures: set[int] = set()
        for parsed_file in parsed_files:
            for procedure in self._helper_project_file_procedures(parsed_file):
                if id(procedure) not in seen_procedures:
                    self._resolve_signature_kinds(procedure, module_params, resolve_shapes=False)
                    seen_procedures.add(id(procedure))
            for owner in (
                *parsed_file.modules,
                *parsed_file.submodules,
                *parsed_file.programs,
                *parsed_file.block_data_units,
            ):
                self._resolve_module_variable_kinds(owner, module_params)

    def _helper_project_module_symbols(self, parsed_files: list[FortranFile]) -> dict[str, dict[str, str]]:
        """Resolve module symbols and submodule host associations."""
        module_params: dict[str, dict[str, str]] = {}
        owners: dict[str, FortranModule | FortranSubmodule] = {}
        for parsed_file in parsed_files:
            if parsed_file.source is not None:
                module_params.update(self._collect_module_parameters(parsed_file.source, parsed_file.filename))
            owners.update((module.name.lower(), module) for module in parsed_file.modules)
            owners.update((submodule.name.lower(), submodule) for submodule in parsed_file.submodules)

        resolved = self._resolve_module_parameter_values(module_params)
        for _ in range(len(owners) + 1):
            changed = False
            for owner_name, owner in owners.items():
                symbols = dict(resolved.get(owner_name, {}))
                if isinstance(owner, FortranSubmodule):
                    if owner.ancestor:
                        symbols.update(resolved.get(owner.ancestor.lower(), {}))
                    symbols.update(resolved.get(owner.parent.lower(), {}))
                symbols.update(self._helper_owner_imported_symbols(owner, resolved))
                updated = self._resolve_module_parameter_values({owner_name: symbols})[owner_name]
                if updated != resolved.get(owner_name, {}):
                    resolved[owner_name] = updated
                    changed = True
            if not changed:
                break
        return resolved

    @staticmethod
    def _helper_owner_imported_symbols(
        owner: FortranModule | FortranSubmodule,
        resolved_modules: dict[str, dict[str, str]],
    ) -> dict[str, str]:
        """Return explicit compile-time symbols imported into one owner."""
        imported: dict[str, str] = {}
        for dependency, mappings in owner.uses.items():
            dependency_name = dependency.lower()
            dependency_symbols = resolved_modules.get(dependency_name, {})
            if not mappings:
                imported.update(dependency_symbols)
                continue
            for mapping in mappings:
                source_name = mapping.source.lower()
                expression = dependency_symbols.get(source_name)
                if expression is None and dependency_name in _INTRINSIC_COMPILE_TIME_MODULES:
                    expression = mapping.source
                if expression is not None:
                    imported[mapping.local_name.lower()] = expression
        return imported

    @staticmethod
    def _helper_project_file_procedures(parsed_file: FortranFile):
        """Yield direct and interface procedures in project resolution order."""
        yield from parsed_file.procedures
        for interface in parsed_file.interfaces:
            yield from interface.procedures
        for module in parsed_file.modules:
            yield from module.procedures
            for interface in module.interfaces:
                yield from interface.procedures
        for submodule in parsed_file.submodules:
            yield from submodule.procedures
            for interface in submodule.interfaces:
                yield from interface.procedures

    def _helper_index_project_file(self, project: FortranProject, parsed_file: FortranFile) -> None:
        """Add one parsed file's public models to project registries."""
        for module in parsed_file.modules:
            self._helper_index_project_module(project, module)
        for submodule in parsed_file.submodules:
            self._helper_index_project_submodule(project, submodule)
        for program in parsed_file.programs:
            self._helper_index_project_program(project, program)
        for procedure in parsed_file.procedures:
            self._helper_index_project_standalone_procedure(project, procedure)
        for dtype in parsed_file.derived_types:
            self._insert_unique_scope_symbol(
                project.derived_types,
                dtype.name.lower(),
                dtype,
                label="project derived-type scope",
            )
        for interface in parsed_file.interfaces:
            self._helper_index_project_interface(project, interface)

    def _helper_index_project_module(self, project: FortranProject, module: FortranModule) -> None:
        """Index one module and its owned public models."""
        module_key = module.name.lower()
        self._insert_unique_scope_symbol(project.modules, module_key, module, label="project module scope")
        project.dependencies[module_key] = {name.lower() for name in module.uses}
        self._helper_index_project_owner_members(project, module, module_key)

    def _helper_index_project_submodule(self, project: FortranProject, submodule: FortranSubmodule) -> None:
        """Index one submodule, its dependencies, and its public models."""
        submodule_key = submodule.name.lower()
        self._insert_unique_scope_symbol(
            project.submodules,
            submodule_key,
            submodule,
            label="project submodule scope",
        )
        dependencies = {submodule.parent.lower(), *(name.lower() for name in submodule.uses)}
        if submodule.ancestor:
            dependencies.add(submodule.ancestor.lower())
        project.dependencies[submodule_key] = dependencies
        self._helper_index_project_owner_members(project, submodule, submodule_key)

    def _helper_index_project_owner_members(
        self,
        project: FortranProject,
        owner: FortranModule | FortranSubmodule,
        owner_key: str,
    ) -> None:
        """Index qualified and first-seen unqualified owner members."""
        for procedure in owner.procedures:
            qualified_name = f"{owner_key}.{procedure.name.lower()}"
            self._insert_unique_scope_symbol(
                project.procedures,
                qualified_name,
                procedure,
                label="project procedure scope",
            )
            project.procedures.setdefault(procedure.name.lower(), procedure)
        for dtype in owner.derived_types:
            qualified_name = f"{owner_key}.{dtype.name.lower()}"
            self._insert_unique_scope_symbol(
                project.derived_types,
                qualified_name,
                dtype,
                label="project derived-type scope",
            )
            project.derived_types.setdefault(dtype.name.lower(), dtype)
        for interface in owner.interfaces:
            self._helper_index_project_interface(project, interface, owner_key)

    def _helper_index_project_standalone_procedure(
        self,
        project: FortranProject,
        procedure: FortranProcedureSignature,
    ) -> None:
        """Index a standalone procedure ahead of any unqualified owner alias."""
        procedure_key = procedure.name.lower()
        existing = project.procedures.get(procedure_key)
        if existing is not None and existing.module is not None:
            project.procedures[procedure_key] = procedure
            return
        self._insert_unique_scope_symbol(
            project.procedures,
            procedure_key,
            procedure,
            label="project procedure scope",
        )

    def _helper_index_project_program(self, project: FortranProject, program: FortranProgram) -> None:
        """Index one named program and its module dependencies."""
        if not program.name:
            return
        program_key = program.name.lower()
        self._insert_unique_scope_symbol(project.programs, program_key, program, label="project program scope")
        project.dependencies[program_key] = {name.lower() for name in program.uses}

    def _helper_index_project_interface(
        self,
        project: FortranProject,
        interface: FortranInterface,
        owner_key: str | None = None,
    ) -> None:
        """Index one named interface, qualified when it has an owner."""
        if not interface.name:
            return
        interface_name = interface.name.lower()
        registry_key = f"{owner_key}.{interface_name}" if owner_key else interface_name
        self._insert_unique_scope_symbol(
            project.interfaces,
            registry_key,
            interface,
            label="project interface scope",
        )
        if owner_key:
            project.interfaces.setdefault(interface_name, interface)

    # ------------------------------------------------------------------
    # Source preparation and unit slicing
    # ------------------------------------------------------------------

    def _preprocessed_lines(self, source: _SourceOrLines, filename: str | None) -> _PreprocessedLines:
        """Return preprocessed source lines, reusing file-level preprocessing when supplied."""
        if isinstance(source, list):
            lines = source
        else:
            for lineno, source_line in enumerate(source.splitlines(), start=1):
                self._raise_for_raw_cpp_directive(source_line, filename, lineno, source_line)
            source_without_linemarkers = "".join(
                re.sub(r"[^\r\n]", "", line) if _FORTRAN_LINEMARKER_RE.match(line.strip()) else line
                for line in source.splitlines(keepends=True)
            )
            lines = preprocess_lines(source_without_linemarkers, filename)
        for line, lineno, source_line in lines:
            self._raise_for_raw_cpp_directive(line, filename, lineno, source_line)
        return lines

    @staticmethod
    def _raise_for_raw_cpp_directive(
        line: str,
        filename: str | None,
        lineno: int,
        source_line: str,
    ) -> None:
        """Reject raw CPP directives while accepting compiler linemarkers."""
        stripped = line.strip()
        if stripped.startswith("#") and not _FORTRAN_LINEMARKER_RE.match(stripped):
            raise FortranParseError(
                "Fortran CPP directives require compiler preprocessing before parsing.",
                filename=filename,
                line_number=lineno,
                source_line=source_line,
                code="PARSE_PREPROCESSING_REQUIRED",
            )

    def _helper_collect_namespace(
        self,
        root: str | Path,
        extensions: tuple[str, ...] = (".f", ".for", ".ftn", ".f77", ".f90", ".f95", ".f03", ".f08"),
        *,
        encoding: str = "utf-8",
    ) -> dict:
        """Collect parseable source files and dependency-order them.

        Project parsing uses this helper when the caller passes a directory
        instead of an explicit file list. It performs a light first pass to map
        modules/submodules to files, topologically orders files by ``use``
        dependencies, then parses them in that order.

        Example:
            ``parse_project("src")`` calls this helper, receives
            ``{"files": ordered_files, "module_to_file": ...}``, and then
            parses each ordered path through the normal file entrypoint.
        """
        root_path = Path(root)
        files = sorted([p for p in root_path.rglob("*") if p.suffix.lower() in extensions])
        sources = {str(p): p.read_text(encoding=encoding) for p in files}
        file_lines = {fname: preprocess_lines(code, fname) for fname, code in sources.items()}

        module_to_file: dict[str, str] = {}
        submodule_to_file: dict[str, str] = {}
        file_to_uses: dict[str, set[str]] = {fname: set() for fname in sources}
        for fname, _code in sources.items():
            lines = file_lines[fname]
            _lines, root_scope, all_units = self._helper_prepare_source_units(lines, fname)
            modules = [
                self._visit(unit, parent_scope=root_scope, filename=fname)
                for unit in all_units
                if unit.kind == "module"
            ]
            submodules = [
                self._visit(unit, parent_scope=root_scope, filename=fname)
                for unit in all_units
                if unit.kind == "submodule"
            ]
            for m in modules:
                module_to_file[m.name.lower()] = fname
                file_to_uses[fname].update(u.lower() for u in m.uses)
            for sm in submodules:
                submodule_to_file[sm.name.lower()] = fname
                file_to_uses[fname].add(sm.parent.lower())
                if sm.ancestor:
                    file_to_uses[fname].add(sm.ancestor.lower())
                file_to_uses[fname].update(u.lower() for u in sm.uses)

        file_dependencies: dict[str, set[str]] = {}
        for fname, used_modules in file_to_uses.items():
            deps = set()
            for mod in used_modules:
                dep_file = module_to_file.get(mod) or submodule_to_file.get(mod)
                if dep_file and dep_file != fname:
                    deps.add(dep_file)
            file_dependencies[fname] = deps

        ordered_files = self._topological_files(file_dependencies)
        types = []
        modules = []
        submodules = []
        programs = []
        block_data = []
        for f in ordered_files:
            parsed_file = self.parse_file(sources[f], filename=f, encoding=encoding)
            types.extend(parsed_file.derived_types)
            types.extend(dtype for module in parsed_file.modules for dtype in module.derived_types)
            types.extend(dtype for submodule in parsed_file.submodules for dtype in submodule.derived_types)
            modules.extend(parsed_file.modules)
            submodules.extend(parsed_file.submodules)
            programs.extend(parsed_file.programs)
            block_data.extend(parsed_file.block_data_units)

        return {
            "files": ordered_files,
            "file_dependencies": {k: sorted(v) for k, v in file_dependencies.items()},
            "module_to_file": module_to_file,
            "submodule_to_file": submodule_to_file,
            "modules": modules,
            "submodules": submodules,
            "programs": programs,
            "block_data": block_data,
            "types": types,
        }

    def _helper_prepare_source_units(
        self,
        code: _SourceOrLines,
        filename: str | None,
    ) -> tuple[_PreprocessedLines, _ParserScope, list[SourceUnit]]:
        """Preprocess, validate, and slice file-level source units.

        This is the first grammar-shaped step in `parse_file`: raw source is
        normalized into line tuples, obvious malformed headers are rejected,
        and only direct file-scope units are returned.

        Example:
            A file containing ``module constants`` and standalone
            ``subroutine solve`` returns a root file scope plus two
            `SourceUnit` objects, one module unit and one procedure unit, both
            carrying original source line numbers.
        """
        lines = self._preprocessed_lines(code, filename)
        root_scope = _ParserScope(kind="file", name=None)
        units = self._helper_slice_child_units(lines, parent_scope=root_scope, filename=filename)
        self._helper_validate_file_scope_unparsed_lines(lines, filename)
        self._helper_validate_sibling_units(units, parent_scope=root_scope, filename=filename)
        return lines, root_scope, units

    def _collect_interface_source_units(
        self,
        code: _SourceOrLines,
        filename: str | None,
    ) -> list[tuple[SourceUnit, _ParserScope]]:
        """Collect interface units with the parent scope needed to parse them.

        Public plural/singular interface visitors both use this collector so
        singular parsing selects one source unit directly instead of parsing a
        plural result list and checking its length afterward.
        """
        lines, root_scope, _all_units = self._helper_prepare_source_units(code, filename)
        interfaces: list[tuple[SourceUnit, _ParserScope]] = []

        def collect(scope: _ParserScope, child_units: list[SourceUnit]) -> None:
            """Walk non-execution children and retain interface units."""
            for child in child_units:
                if child.kind == "interface":
                    interfaces.append((child, scope))
                    continue
                if child.kind in {"module", "submodule"}:
                    child_scope = _ParserScope(
                        kind=child.kind,
                        name=child.name,
                        parent=scope,
                        module_owner=child.name,
                    )
                    collect(
                        child_scope,
                        self._helper_nonexecution_child_units(child, parent_scope=child_scope, filename=filename),
                    )
                    continue
                if child.kind in {"procedure", "program"}:
                    child_scope = _ParserScope(
                        kind=child.kind,
                        name=child.name,
                        parent=scope,
                        module_owner=scope.module_owner,
                    )
                    collect(
                        child_scope,
                        self._helper_nonexecution_child_units(child, parent_scope=child_scope, filename=filename),
                    )

        collect(root_scope, self._helper_slice_child_units(lines, parent_scope=root_scope, filename=filename))
        return interfaces

    def _collect_derived_type_source_units(
        self,
        code: _SourceOrLines,
        filename: str | None,
    ) -> list[tuple[SourceUnit, _ParserScope]]:
        """Collect derived-type units with their module/program scope context."""
        lines, root_scope, _all_units = self._helper_prepare_source_units(code, filename)
        types: list[tuple[SourceUnit, _ParserScope]] = []

        def collect(scope: _ParserScope, child_units: list[SourceUnit]) -> None:
            """Walk nested grammar units and retain derived-type units."""
            for child in child_units:
                if child.kind == "derived_type":
                    types.append((child, scope))
                    continue
                if child.kind in {"module", "submodule", "program"}:
                    child_scope = _ParserScope(
                        kind=child.kind,
                        name=child.name,
                        parent=scope,
                        module_owner=child.name if child.kind in {"module", "submodule"} else scope.module_owner,
                    )
                    collect(
                        child_scope,
                        self._helper_nonexecution_child_units(child, parent_scope=child_scope, filename=filename),
                    )
                    continue
                if child.kind == "procedure":
                    child_scope = _ParserScope(
                        kind=child.kind,
                        name=child.name,
                        parent=scope,
                        module_owner=scope.module_owner,
                    )
                    collect(
                        child_scope,
                        self._helper_nonexecution_child_units(child, parent_scope=child_scope, filename=filename),
                    )

        collect(root_scope, self._helper_slice_child_units(lines, parent_scope=root_scope, filename=filename))
        return types

    def _helper_validate_possible_unit_header(
        self,
        line: str,
        *,
        filename: str | None,
        lineno: int | None,
        source_line: str | None,
    ) -> None:
        """Validate a line that lexically resembles a source-unit header."""
        stripped = line.strip()
        self._parse_module_header(stripped, filename, lineno=lineno, source_line=source_line)
        if stripped.lower().startswith("end "):
            return
        if re.match(r"^module\s+procedure\s*::", stripped, flags=re.IGNORECASE):
            return
        if not (stripped.lower().startswith("module procedure") or self._looks_like_procedure_header(stripped)):
            return
        if (
            self._parse_procedure_header(
                stripped,
                None,
                False,
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )
            is None
        ):
            self._raise_if_unparsed_procedure_header(
                stripped,
                in_interface=False,
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )

    def _helper_validate_file_scope_unparsed_lines(self, lines: _PreprocessedLines, filename: str | None) -> None:
        """Reject any non-Fortran syntax outside recognized unit bodies.

        This guard is intentionally language-agnostic: lines that are neither
        valid file-scope Fortran constructs nor part of a recognized unit are
        rejected via the generic invalid-syntax diagnostic path.
        """
        index = 0
        while index < len(lines):
            line, lineno, source_line = lines[index]
            stripped = line.strip()
            if not stripped:
                index += 1
                continue

            self._helper_validate_possible_unit_header(
                stripped,
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )
            start = self._helper_classify_unit_start(stripped)
            if start is not None:
                end_index = self._helper_find_unit_end(lines, index, start[0], filename=filename)
                if end_index is not None:
                    index = end_index + 1
                    continue
            if self._is_executable_statement_start(stripped):
                # A standalone include fragment can contain executable lines
                # without an enclosing procedure. Once execution starts, the
                # remaining fragment is intentionally opaque to this parser.
                return
            if self._is_allowed_unparsed_file_scope_line(stripped):
                index += 1
                continue
            self._raise_invalid_fortran_syntax_line(
                stripped,
                context="file scope",
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )

    @staticmethod
    def _is_allowed_unparsed_file_scope_line(line: str) -> bool:
        """Return whether a file-scope line is intentionally metadata-only."""
        stripped = line.strip()
        return (
            stripped.startswith("#")
            or FortranParser._is_openmp_directive(stripped)
            or _REGEX["include"].match(stripped)
        )

    @staticmethod
    def _raise_invalid_fortran_syntax_line(
        line: str,
        *,
        context: str,
        filename: str | None,
        lineno: int | None,
        source_line: str | None,
    ) -> None:
        """Raise the shared invalid-syntax diagnostic for one source line."""
        raise FortranParseError(
            f"Invalid Fortran syntax in {context}: {line.strip()}",
            filename=filename,
            line_number=lineno,
            source_line=source_line,
            code="PARSE_INVALID_SYNTAX",
        )

    def _helper_slice_child_units(
        self,
        lines: _PreprocessedLines,
        *,
        parent_scope: _ParserScope,
        allowed_kinds: set[str] | None = None,
        filename: str | None = None,
        skip_execution_region: bool = False,
    ) -> list[SourceUnit]:
        """Slice direct child units from a parent source substring.

        The name says "child" because this helper is recursive by design:
        `parse_file` calls it for file-level units, `_visit_ModuleUnit` calls it
        for module children, and `_visit_InterfaceUnit` calls it for interface
        procedure declarations. Each returned `SourceUnit.lines` contains only
        that child unit's substring.

        Example:
            In ``module m`` with an ``interface`` block and a contained
            ``subroutine run``, this helper returns two direct children for the
            module scope: one interface unit and one procedure unit. The
            interface's subroutine is not returned at module level; it is
            returned when the interface visitor asks for its own children.
        """
        units: list[SourceUnit] = []
        index = 0
        region = "specification"
        while index < len(lines):
            line, lineno, _ = lines[index]
            stripped = line.strip()
            if stripped.startswith("#"):
                index += 1
                continue
            if skip_execution_region:
                if self._is_contains_transition(stripped):
                    region = "contains"
                    index += 1
                    continue
                if region == "specification" and self._is_executable_statement_start(stripped):
                    region = "execution"
                if region == "execution":
                    index += 1
                    continue
            if parent_scope.kind == "interface" and re.match(r"^module\s+procedure\b", line.strip(), re.IGNORECASE):
                index += 1
                continue
            start = self._helper_classify_unit_start(line)
            if start is None:
                index += 1
                continue
            kind, name = start
            if allowed_kinds is not None and kind not in allowed_kinds:
                index += 1
                continue

            end_index = self._helper_find_unit_end(lines, index, kind, filename=filename)
            if end_index is None:
                if kind == "interface" and (lines[index][2] or "").strip().lower().startswith("end interface"):
                    index += 1
                    continue
                if parent_scope.kind == "interface" and kind == "procedure":
                    # Interface bodies often contain a procedure declaration
                    # that is closed by `end interface`, not by an explicit
                    # `end subroutine`/`end function`. In that grammar context
                    # the whole remaining interface substring belongs to the
                    # declaration.
                    end_index = len(lines) - 1
                else:
                    label = self._helper_unit_label(kind)
                    raise FortranParseError(
                        f"Missing end {label} for {label} '{name or '<unnamed>'}'.",
                        filename=filename,
                        line_number=lineno,
                        source_line=lines[index][2],
                        code="PARSE_MISSING_UNIT_END",
                    )

            end_line = lines[end_index][1]
            units.append(
                _SOURCE_UNIT_TYPES[kind](
                    kind=kind,
                    name=name,
                    lines=lines[index : end_index + 1],
                    start_line=lineno,
                    end_line=end_line,
                )
            )
            index = end_index + 1
        return units

    def _helper_find_unit_end(
        self,
        lines: _PreprocessedLines,
        start_index: int,
        kind: str,
        *,
        filename: str | None = None,
    ) -> int | None:
        """Find the matching end line for a source unit.

        The helper walks nested parseable units with a small stack. It is used
        before building a `SourceUnit`, so every visitor receives only its own
        substring and original line numbers remain attached to each tuple.

        Example:
            Given a module containing an interface containing a subroutine, the
            module end is returned, not the subroutine end, because the nested
            interface/procedure pair is pushed and popped before the module is
            closed.
        """
        start = self._helper_classify_unit_start(lines[start_index][0])
        start_name = start[1] if start is not None else None
        stack: list[tuple[str, str | None, int | None, str | None, str]] = [
            (kind, start_name, lines[start_index][1], lines[start_index][2], "specification")
        ]
        idx = start_index + 1
        while idx < len(lines):
            line, lineno, source_line = lines[idx]
            line = line.strip()
            if not line:
                idx += 1
                continue
            current_kind, current_name, current_line, current_source, current_region = stack[-1]
            if current_kind == "interface" and re.match(r"^module\s+procedure\b", line, re.IGNORECASE):
                idx += 1
                continue

            closes_current, end_name = self._helper_parse_unit_end(current_kind, line)
            if closes_current:
                if end_name and current_name and end_name.lower() != current_name.lower():
                    if current_kind == "procedure" and self._helper_has_preferred_unit_end_ahead(
                        lines,
                        idx,
                        current_kind,
                        current_name,
                    ):
                        idx += 1
                        continue
                    label = self._helper_unit_label(current_kind)
                    if current_kind != "procedure":
                        raise FortranParseError(
                            f"Mismatched end {label} name '{end_name}' for {label} '{current_name}'.",
                            filename=filename,
                            line_number=lineno,
                            source_line=source_line,
                            code="PARSE_MISMATCHED_UNIT_END",
                        )
                stack.pop()
                if not stack:
                    return idx
                idx += 1
                continue

            grammar = self._helper_unit_grammar(current_kind)
            if self._is_contains_transition(line) and grammar.has_contains_part:
                stack[-1] = (current_kind, current_name, current_line, current_source, "contains")
                idx += 1
                continue
            if (
                current_region == "specification"
                and grammar.has_execution_part
                and self._is_executable_statement_start(line)
            ):
                stack[-1] = (current_kind, current_name, current_line, current_source, "execution")
                idx += 1
                continue
            if current_region == "execution":
                idx += 1
                continue

            start = self._helper_classify_unit_start(line)
            if start is not None and self._helper_has_unit_end_ahead(lines, idx, start[0]):
                nested_kind, _ = start
                stack.append((nested_kind, start[1], lineno, source_line, "specification"))
                idx += 1
                continue

            for open_kind, _open_name, _open_line, _open_source, _open_region in reversed(stack):
                closes_open, end_name = self._helper_parse_unit_end(open_kind, line)
                if not closes_open:
                    continue
                label = self._helper_unit_label(current_kind)
                expected = self._helper_unit_label(open_kind)
                raise FortranParseError(
                    f"Unexpected end {expected} while parsing {label} '{current_name or '<unnamed>'}'.",
                    filename=filename,
                    line_number=lineno,
                    source_line=source_line,
                    code="PARSE_UNEXPECTED_UNIT_END",
                )
            idx += 1
        return None

    def _helper_has_unit_end_ahead(self, lines: _PreprocessedLines, start_index: int, kind: str) -> bool:
        """Check whether a candidate unit opener has a later matching end.

        The slicer uses this conservative look-ahead for ambiguous lines such
        as ``type :: state``. With a later ``end type`` it is a derived-type
        unit; without one the existing parser treats it as a declaration-like
        line and continues.

        Example:
            ``type :: particle`` followed by ``end type particle`` returns
            `True`, but a lone ``type :: local_state`` in a program
            specification part returns `False`.
        """
        start = self._helper_classify_unit_start(lines[start_index][0])
        start_name = start[1] if start is not None else None
        if self._helper_has_preferred_unit_end_ahead(lines, start_index, kind, start_name):
            return True
        if kind != "procedure":
            return False
        for idx in range(start_index + 1, len(lines)):
            matched, _end_name = self._helper_parse_unit_end(kind, lines[idx][0])
            if matched:
                return True
        return False

    def _helper_has_preferred_unit_end_ahead(
        self,
        lines: _PreprocessedLines,
        start_index: int,
        kind: str,
        start_name: str | None,
    ) -> bool:
        """Return whether an exact or unnamed terminator exists later."""
        for idx in range(start_index + 1, len(lines)):
            matched, end_name = self._helper_parse_unit_end(kind, lines[idx][0])
            if matched and (not start_name or not end_name or end_name.lower() == start_name.lower()):
                return True
        return False

    def _helper_split_unit_parts(
        self,
        unit: SourceUnit,
        grammar: _UnitGrammar,
        *,
        filename: str | None = None,
    ) -> _UnitParts:
        """Split one unit substring into grammar regions.

        The helper follows the shape you described: every parseable unit has a
        header and a specification part, some have an execution part, and some
        have a contains part. Visitors can then be small and choose which
        region matters for wrapping metadata.

        Example:
            For a procedure, declarations before the first executable
            statement go into `specification`, assignments/calls go into
            `execution`, and internal procedures after `contains` go into
            `contains`. The procedure visitor parses only `specification`.
        """
        header = unit.lines[0] if unit.lines else None
        footer = unit.lines[-1] if unit.lines and self._helper_unit_end_matches(unit.kind, unit.lines[-1][0]) else None
        body = unit.lines[1:-1] if footer is not None else unit.lines[1:]
        specification: _PreprocessedLines = []
        execution: _PreprocessedLines = []
        contains: _PreprocessedLines = []
        region = "specification"
        index = 0

        while index < len(body):
            line, _, _ = body[index]
            stripped = line.strip()
            if not stripped:
                index += 1
                continue
            if self._is_contains_transition(stripped):
                if not grammar.has_contains_part:
                    self._raise_invalid_fortran_syntax_line(
                        stripped,
                        context=f"{self._helper_unit_label(grammar.kind)} '{unit.name or '<unnamed>'}'",
                        filename=filename,
                        lineno=body[index][1],
                        source_line=body[index][2],
                    )
                region = "contains"
                index += 1
                continue

            if grammar.kind == "interface" and re.match(r"^module\s+procedure\b", stripped, re.IGNORECASE):
                specification.append(body[index])
                index += 1
                continue

            start = self._helper_classify_unit_start(stripped)
            if start is not None:
                child_kind, _ = start
                child_end = self._helper_find_unit_end(body, index, child_kind, filename=filename)
                if child_end is not None:
                    index = child_end + 1
                    continue
                if grammar.kind == "interface" and child_kind == "procedure":
                    break

            if (
                region == "specification"
                and grammar.has_execution_part
                and self._is_executable_statement_start(stripped)
            ):
                region = "execution"

            if region == "specification":
                specification.append(body[index])
            elif region == "execution":
                execution.append(body[index])
            else:
                contains.append(body[index])
            index += 1

        return _UnitParts(
            header=header,
            specification=specification,
            execution=execution,
            contains=contains,
            footer=footer,
        )

    def _helper_child_unit_region(
        self,
        unit: SourceUnit,
        parts: _UnitParts,
        child: SourceUnit,
    ) -> str:
        """Return the grammar region containing one direct child unit."""
        child_line = child.start_line
        if child_line is None:
            return "specification"
        contains_line = self._helper_direct_contains_line(unit, filename=None)
        if contains_line is not None and child_line > contains_line:
            return "contains"
        execution_line = next(
            (lineno for _line, lineno, _source_line in parts.execution if lineno is not None),
            None,
        )
        if execution_line is not None and child_line >= execution_line:
            return "execution"
        return "specification"

    def _helper_nonexecution_child_units(
        self,
        unit: SourceUnit,
        *,
        parent_scope: _ParserScope,
        filename: str | None,
    ) -> list[SourceUnit]:
        """Return direct nested units outside an intentionally skipped execution part."""
        grammar = self._helper_unit_grammar(unit.kind)
        child_units = self._helper_slice_child_units(
            unit.lines[1:-1],
            parent_scope=parent_scope,
            filename=filename,
            skip_execution_region=grammar.has_execution_part,
        )
        if not grammar.has_execution_part:
            return child_units
        parts = self._helper_split_unit_parts(unit, grammar, filename=filename)
        return [child for child in child_units if self._helper_child_unit_region(unit, parts, child) != "execution"]

    def _helper_direct_contains_line(
        self,
        unit: SourceUnit,
        *,
        filename: str | None,
    ) -> int | None:
        """Return the direct `contains` transition, skipping nested child units."""
        body = unit.lines[1:-1]
        index = 0
        while index < len(body):
            line, lineno, _source_line = body[index]
            stripped = line.strip()
            if self._is_contains_transition(stripped):
                return lineno
            start = self._helper_classify_unit_start(stripped)
            if start is not None:
                child_end = self._helper_find_unit_end(body, index, start[0], filename=filename)
                if child_end is not None:
                    index = child_end + 1
                    continue
            index += 1
        return None

    def _helper_validate_child_unit_regions(
        self,
        unit: SourceUnit,
        parts: _UnitParts,
        child_units: list[SourceUnit],
        *,
        filename: str | None,
    ) -> None:
        """Reject child units that occur outside their parent's grammar region."""
        allowed = {
            "module": {
                "specification": {"derived_type", "interface", "enum"},
                "contains": {"procedure"},
            },
            "submodule": {
                "specification": {"derived_type", "interface", "enum"},
                "contains": {"procedure"},
            },
            "program": {
                "specification": {"derived_type", "interface", "enum"},
                "contains": {"procedure"},
            },
            "procedure": {
                "specification": {"derived_type", "interface", "enum"},
                "contains": {"procedure"},
            },
            "derived_type": {
                "specification": set(),
                "contains": set(),
            },
            "block_data": {
                "specification": set(),
                "contains": set(),
            },
            "enum": {
                "specification": set(),
                "contains": set(),
            },
        }
        grammar_regions = allowed.get(unit.kind, {})
        for child in child_units:
            region = self._helper_child_unit_region(unit, parts, child)
            if region == "execution":
                continue
            if child.kind in grammar_regions.get(region, set()):
                continue
            self._raise_invalid_fortran_syntax_line(
                child.lines[0][0] if child.lines else child.kind,
                context=(f"{self._helper_unit_label(unit.kind)} '{unit.name or '<unnamed>'}' {region} part"),
                filename=filename,
                lineno=child.start_line,
                source_line=child.lines[0][2] if child.lines else None,
            )

    def _helper_validate_contains_lines(
        self,
        scope: _ParserScope,
        lines: _PreprocessedLines,
        *,
        filename: str | None,
    ) -> None:
        """Validate non-child lines left in a `contains` region."""
        for line, lineno, source_line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or _REGEX["include"].match(stripped):
                continue
            if self._helper_is_valid_contains_alternative_line(scope, stripped):
                continue
            self._helper_validate_possible_unit_header(
                stripped,
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )
            self._raise_invalid_fortran_syntax_line(
                stripped,
                context=f"{self._helper_unit_label(scope.kind)} '{scope.name or '<unnamed>'}' contains part",
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )

    def _helper_is_valid_contains_alternative_line(self, scope: _ParserScope, line: str) -> bool:
        """Accept syntax from an unselected raw-preprocessor specification alternative."""
        scratch_scope = deepcopy(scope)
        try:
            self._parse_specification_part(scratch_scope, [(line, None, None)], filename=None)
        except FortranParseError:
            return False
        return True

    def _helper_validate_interface_lines(
        self,
        scope: _ParserScope,
        lines: _PreprocessedLines,
        *,
        filename: str | None,
    ) -> None:
        """Validate interface statements that are not nested procedure bodies."""
        for line, lineno, source_line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if re.match(
                r"^module\s+procedure\s*(?:::)?\s*[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s*$", stripped, re.IGNORECASE
            ):
                continue
            if re.match(
                r"^procedure(?:\s*\([^)]*\))?(?:\s*,\s*[^:]*)?\s*::\s*[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s*$",
                stripped,
                re.IGNORECASE,
            ):
                continue
            self._helper_validate_possible_unit_header(
                stripped,
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )
            self._raise_invalid_fortran_syntax_line(
                stripped,
                context=f"interface '{scope.name or '<unnamed>'}'",
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )

    def _helper_validate_enum_unit(self, unit: SourceUnit, *, filename: str | None) -> None:
        """Validate an interoperability enum block."""
        self._helper_parse_enum_unit(unit, filename=filename, module_owner=None)

    def _helper_parse_enum_unit(
        self,
        unit: SourceUnit,
        *,
        filename: str | None,
        module_owner: str | None,
    ) -> FortranEnum:
        """Parse an interoperability enum block into enumerator constants."""
        parts = self._helper_split_unit_parts(unit, self._helper_unit_grammar("enum"), filename=filename)
        bind_c = bool(unit.lines and _REGEX["bind_c"].search(unit.lines[0][0]))
        enum = FortranEnum(name=unit.name, module=module_owner, bind_c=bind_c)
        symbols: dict[str, str] = {}
        next_value: int | None = 0
        for line, lineno, source_line in parts.specification:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = re.match(r"^enumerator\s*(?:::)?\s*(?P<items>.+)$", stripped, re.IGNORECASE)
            if match:
                try:
                    for item in split_csv(match.group("items")):
                        enumerator, next_value = self._parse_enum_item(item, symbols, next_value)
                        enum.enumerators.append(enumerator)
                except FortranParseError:
                    self._raise_invalid_fortran_syntax_line(
                        stripped,
                        context="enum specification part",
                        filename=filename,
                        lineno=lineno,
                        source_line=source_line,
                    )
                continue
            self._raise_invalid_fortran_syntax_line(
                stripped,
                context="enum specification part",
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )
        child_units = self._helper_slice_child_units(
            unit.lines[1:-1], parent_scope=_ParserScope(kind="enum", name=unit.name), filename=filename
        )
        self._helper_validate_child_unit_regions(unit, parts, child_units, filename=filename)
        return enum

    @staticmethod
    def _parse_enum_item(
        item: str,
        symbols: dict[str, str],
        next_value: int | None,
    ) -> tuple[FortranEnumerator, int | None]:
        """Parse one enumerator and calculate the following implicit value.

        ``symbols`` is updated only when this item resolves to a value, so later
        explicit expressions can refer to it.  The returned counter is ``None``
        after a non-integer value, preserving the existing no-guessing rule for
        later implicit enumerators.
        """
        stripped = item.strip()
        match = re.fullmatch(r"(?P<name>[A-Za-z_]\w*)(?:\s*=\s*(?P<value>.+))?", stripped)
        if match is None:
            raise FortranParseError(f"Invalid Fortran syntax in enum specification part: {stripped}")

        name = match.group("name")
        source_value = match.group("value")
        if source_value is None:
            value = str(next_value) if next_value is not None else None
            symbolic_value = None
        else:
            symbolic_value = source_value.strip()
            resolved = _CompileTimeResolver(symbols).resolve(symbolic_value, prefer_symbolic=False)
            value = FortranParser._normalize_parameter_value(resolved)

        literal = FortranParser._safe_eval_int_expr(value or "") if value is not None else None
        next_value = literal + 1 if literal is not None else None
        if value is not None:
            symbols[name.lower()] = value
        return FortranEnumerator(name=name, value=value, symbolic_value=symbolic_value), next_value

    def _helper_validate_ignored_child_units(
        self,
        child_units: list[SourceUnit],
        *,
        parent_scope: _ParserScope,
        filename: str | None,
        unit: SourceUnit | None = None,
        parts: _UnitParts | None = None,
    ) -> None:
        """Check or skip nested units that are intentionally omitted from metadata."""
        for child in child_units:
            if (
                unit is not None
                and parts is not None
                and self._helper_child_unit_region(unit, parts, child) == "execution"
            ):
                continue
            if child.kind == "procedure":
                # The slicer has already checked the nested unit boundary and
                # the caller has checked its grammar region. Internal procedure
                # declarations and bodies do not affect wrapper metadata.
                continue
            if isinstance(child, InterfaceUnit | DerivedTypeUnit):
                self._visit(child, parent_scope=parent_scope, filename=filename)
            elif child.kind == "enum":
                self._helper_validate_enum_unit(child, filename=filename)

    def _helper_validate_sibling_units(
        self,
        units: list[SourceUnit],
        *,
        parent_scope: _ParserScope,
        filename: str | None,
    ) -> None:
        """Validate duplicate source-unit names at one scope level.

        The check is scope-local: two modules may each define ``type state``,
        but two direct children with the same relevant kind/name in one scope
        are rejected.

        Example:
            Two ``module mesh`` units at file scope raise a duplicate-module
            error. Two ``subroutine step`` children in one module raise a
            duplicate-procedure error.
        """
        seen: dict[tuple[str, str], list[SourceUnit]] = {}
        for unit in units:
            if not unit.name:
                continue
            if unit.kind == "procedure":
                key = ("procedure", unit.name.lower())
            elif unit.kind in {"module", "submodule", "program", "block_data", "derived_type", "interface"}:
                key = (unit.kind, unit.name.lower())
            else:
                continue
            for _existing in seen.get(key, []):
                if unit.kind == "procedure":
                    scope_label = (
                        f"module '{parent_scope.name}'"
                        if parent_scope.kind in {"module", "submodule"}
                        else "global scope"
                    )
                    raise FortranParseError(
                        f"Duplicate procedure name '{unit.name}' in {scope_label}.",
                        filename=filename,
                        line_number=unit.start_line,
                        source_line=unit.lines[0][2] if unit.lines else None,
                        code="PARSE_DUPLICATE_PROCEDURE",
                    )
                raise FortranParseError(
                    f"Duplicate {unit.kind.replace('_', ' ')} name '{unit.name}' in {parent_scope.kind} scope.",
                    filename=filename,
                    line_number=unit.start_line,
                    source_line=unit.lines[0][2] if unit.lines else None,
                    code="PARSE_DUPLICATE_UNIT",
                )
            seen.setdefault(key, []).append(unit)

    def _helper_unit_grammar(self, kind: str) -> _UnitGrammar:
        """Return the grammar profile used by the source-unit visitor methods.

        The name is intentionally explicit: callers ask for the grammar of a
        source unit before splitting its body into the same high-level regions
        that appear in the Fortran standard: header, specification part,
        execution part, and contains part.

        Example:
            A procedure has a specification part and an execution part, but
            wrapper metadata only needs the specification part::

                grammar = self._helper_unit_grammar("procedure")
                assert grammar.has_execution_part is True
                assert grammar.ignores_contains_children is True
        """
        grammars = {
            "module": _UnitGrammar(
                kind="module",
                has_contains_part=True,
                declaration_role="module_variable",
            ),
            "submodule": _UnitGrammar(
                kind="submodule",
                has_contains_part=True,
                declaration_role="module_variable",
            ),
            "program": _UnitGrammar(
                kind="program",
                has_execution_part=True,
                has_contains_part=True,
                ignores_contains_children=True,
                declaration_role="module_variable",
            ),
            "procedure": _UnitGrammar(
                kind="procedure",
                has_execution_part=True,
                has_contains_part=True,
                ignores_contains_children=True,
                declaration_role="procedure_symbol",
            ),
            "derived_type": _UnitGrammar(
                kind="derived_type",
                has_contains_part=True,
                declaration_role="type_field",
            ),
            "interface": _UnitGrammar(kind="interface"),
            "block_data": _UnitGrammar(kind="block_data", declaration_role="module_variable"),
            "file": _UnitGrammar(kind="file", has_contains_part=True),
        }
        return grammars.get(kind, _UnitGrammar(kind=kind))

    def _helper_classify_unit_start(self, line: str) -> tuple[str, str | None] | None:
        """Classify a line that opens a parseable Fortran source unit.

        The helper name uses "classify" because it does not parse the unit; it
        only recognizes the header enough for the slicer and visitors to agree
        on what visitor should be called next.

        Example:
            ``module mesh`` becomes ``("module", "mesh")`` while
            ``module procedure reset`` becomes ``("procedure", "reset")``.
            That lets a submodule `contains` region reuse the normal procedure
            visitor instead of having a special submodule-only loop.
        """
        stripped = line.strip()
        if not stripped:
            return None
        lower = stripped.lower()
        if lower.startswith("end "):
            return None
        submodule = _REGEX["submodule"].match(stripped)
        if submodule:
            return "submodule", submodule.group("name")
        module = _REGEX["module"].match(stripped)
        if module:
            return "module", module.group("name")
        program = _REGEX["program"].match(stripped)
        if program:
            return "program", program.group("name")
        block_data = _REGEX["block_data"].match(stripped)
        if block_data:
            return "block_data", block_data.group("name")
        if lower == "enum" or lower.startswith("enum,"):
            return "enum", None
        starts_interface, interface_name = self._parse_interface_header(stripped)
        if starts_interface:
            return "interface", interface_name
        module_proc = _REGEX["module_procedure_impl"].match(stripped)
        if module_proc:
            return "procedure", module_proc.group("name")
        if FortranParser._looks_like_procedure_header(stripped):
            proc_match = _REGEX["procedure"].match(stripped) or _REGEX["function"].match(stripped)
            if proc_match:
                return "procedure", proc_match.group("name")
        parsed_type = self._parse_derived_type_start(stripped)
        if parsed_type:
            return "derived_type", parsed_type[0]
        return None

    @staticmethod
    def _helper_parse_unit_end(kind: str, line: str) -> tuple[bool, str | None]:
        """Return whether `line` closes `kind`, plus the optional end name.

        This is the shared closing-token table for the slicer and the unit
        splitter. Keeping it centralized prevents one visitor from accepting a
        different end spelling than another visitor.

        Example:
            ``_helper_parse_unit_end("module", "end module mesh")`` returns
            ``(True, "mesh")``. ``_helper_parse_unit_end("procedure",
            "end function norm")`` returns ``(True, "norm")``.
        """
        stripped = line.strip()
        lower = stripped.lower()
        if kind == "module":
            m = re.match(r"^end\s+module(?:\s+(?P<name>\w+))?\s*$", stripped, re.IGNORECASE)
            return (m is not None, m.group("name") if m else None)
        if kind == "submodule":
            m = re.match(r"^end\s+submodule(?:\s+(?P<name>\w+))?\s*$", stripped, re.IGNORECASE)
            return (m is not None, m.group("name") if m else None)
        if kind == "program":
            m = re.match(r"^end\s+program(?:\s+(?P<name>\w+))?\s*$", stripped, re.IGNORECASE)
            return (m is not None, m.group("name") if m else None)
        if kind == "block_data":
            if lower == "end":
                return True, None
            m = re.match(r"^end\s+block\s+data(?:\s+(?P<name>\w+))?\s*$", stripped, re.IGNORECASE)
            return (m is not None, m.group("name") if m else None)
        if kind == "interface":
            m = re.match(r"^end\s+interface(?:\s+(?P<name>.+?))?\s*$", stripped, re.IGNORECASE)
            return (m is not None, m.group("name") if m else None)
        if kind == "derived_type":
            m = re.match(r"^end\s+type(?:\s+(?P<name>\w+))?\s*$", stripped, re.IGNORECASE)
            return (m is not None, m.group("name") if m else None)
        if kind == "enum":
            m = re.match(r"^end\s+enum\s*$", stripped, re.IGNORECASE)
            return (m is not None, None)
        if kind == "procedure":
            if lower == "end":
                return True, None
            m = re.match(r"^end\s+(?:subroutine|function|procedure)(?:\s+(?P<name>\w+))?\s*$", stripped, re.IGNORECASE)
            return (m is not None, m.group("name") if m else None)
        return False, None

    @staticmethod
    def _helper_unit_label(kind: str) -> str:
        """Return a human-readable unit kind for diagnostics.

        The parser stores normalized kind names such as ``"block_data"`` in
        `SourceUnit`; diagnostics should use Fortran-facing text instead.

        Example:
            ``_helper_unit_label("derived_type")`` returns
            ``"derived type"`` for an error like "Missing end derived type".
        """
        return kind.replace("_", " ")

    @staticmethod
    def _helper_unit_end_matches(kind: str, line: str) -> bool:
        """Return whether `line` closes a unit of `kind`.

        The method isolates all end-token spelling differences so the slicer,
        the body splitter, and unit visitors share one closing-rule table.

        Example:
            The splitter calls ``_helper_unit_end_matches("program", line)``
            on the last line of a sliced unit to decide whether that line is
            the footer or still belongs to the unit body.
        """
        matched, _ = FortranParser._helper_parse_unit_end(kind, line)
        return matched

    @staticmethod
    def _is_contains_transition(line: str) -> bool:
        """Return whether `line` starts a unit's `contains` region."""
        return line.lower() == "contains"

    # ------------------------------------------------------------------
    # Header parsers and source-unit construction
    # ------------------------------------------------------------------

    def _parse_module_header(
        self,
        line: str,
        filename: str | None,
        lineno: int | None = None,
        source_line: str | None = None,
    ) -> FortranModule | None:
        """Parse a module header or reject a malformed module-like line."""
        module_match = _REGEX["module"].match(line)
        if not module_match:
            if line.lower().startswith("module ") and not re.match(
                r"^module\s+(procedure|subroutine|function)\b", line, re.IGNORECASE
            ):
                raise FortranParseError(
                    f"Unsupported or malformed module header: {line.strip()}",
                    filename=filename,
                    line_number=lineno,
                    source_line=source_line,
                    code="PARSE_MALFORMED_HEADER",
                )
            return None
        return FortranModule(name=module_match.group("name"), filename=filename)

    def _parse_submodule_header(self, line: str, filename: str | None) -> FortranSubmodule | None:
        """Parse a submodule header, including parent and optional ancestor."""
        match = _REGEX["submodule"].match(line)
        if not match:
            return None
        parent, ancestor = self._split_submodule_parent(match.group("parent"))
        return FortranSubmodule(
            name=match.group("name"),
            parent=parent,
            ancestor=ancestor,
            filename=filename,
        )

    def _parse_program_header(self, line: str, filename: str | None) -> FortranProgram | None:
        """Parse a program header when `line` starts a program unit."""
        match = _REGEX["program"].match(line)
        if not match:
            return None
        return FortranProgram(name=match.group("name"), filename=filename)

    def _parse_block_data_header(self, line: str, filename: str | None) -> FortranBlockData | None:
        """Parse a named or unnamed block-data header."""
        match = _REGEX["block_data"].match(line)
        if not match:
            return None
        return FortranBlockData(name=match.group("name"), filename=filename)

    def _parse_derived_type_start(self, line: str) -> tuple[str, list[str]] | None:
        """Parse modern or legacy derived-type opening syntax."""
        stripped = line.strip()
        tm = _REGEX["derived_type"].match(stripped)
        if tm:
            attr_txt = (tm.group("attrs") or "").strip().lstrip(",").strip()
            attrs = [a.strip() for a in split_csv(attr_txt)] if attr_txt else []
            return tm.group("name"), attrs
        legacy = re.match(r"^type\s+(?P<name>\w+)\s*$", stripped, re.IGNORECASE)
        if legacy:
            return legacy.group("name"), []
        return None

    def _init_derived_type(
        self,
        line: str,
        *,
        current_module: str | None,
    ) -> FortranDerivedType | None:
        """Build a derived-type model from one recognized opening line."""
        parsed_type = self._parse_derived_type_start(line)
        if not parsed_type:
            return None

        type_name, attrs = parsed_type
        extends = None
        normalized_attrs: list[str] = []
        for attr in attrs:
            lowered = attr.lower()
            if lowered.startswith("extends(") and lowered.endswith(")"):
                extends = attr[attr.find("(") + 1 : -1].strip()
            else:
                normalized_attrs.append(lowered)

        return FortranDerivedType(
            name=type_name,
            module=current_module,
            extends=extends,
            attributes=normalized_attrs,
        )

    @staticmethod
    def _parse_interface_header(line: str) -> tuple[bool, str | None]:
        """Return whether `line` opens an interface and its optional name."""
        lower = line.lower()
        if not (lower.startswith("interface") or lower.startswith("abstract interface")):
            return False, None
        parts = line.split(maxsplit=1)
        name = parts[1].strip() if len(parts) > 1 and not lower.startswith("abstract interface") else None
        return True, name

    def _parse_procedure_header(
        self,
        line: str,
        module: str | None,
        in_interface: bool,
        filename: str | None = None,
        lineno: int | None = None,
        source_line: str | None = None,
    ):
        """Build procedure scope state from a subroutine or function header."""
        module_proc = _REGEX["module_procedure_impl"].match(line)
        if module_proc and not in_interface:
            return self._module_procedure_scope(module_proc, module, in_interface)

        procedure_match = _REGEX["procedure"].match(line)
        if procedure_match:
            return self._subroutine_scope(procedure_match, module, in_interface)
        function_match = _REGEX["function"].match(line)
        if not function_match:
            return None
        return self._function_scope(
            function_match,
            module,
            in_interface,
            filename=filename,
            lineno=lineno,
            source_line=source_line,
        )

    def _module_procedure_scope(self, match, module: str | None, in_interface: bool):
        """Create temporary procedure state for one ``module procedure`` header.

        Such implementation declarations have no explicit dummy list here.
        The returned state owns an empty symbol table and is finalized through
        the same procedure path as regular subroutines and functions.
        """
        sig = FortranProcedureSignature(
            name=match.group("name"),
            kind="module procedure",
            module=module,
            attributes=["module procedure"],
            in_interface=in_interface,
        )
        return self._new_procedure_scope_state(sig, symbols={})

    def _subroutine_scope(self, match, module: str | None, in_interface: bool):
        """Create procedure state from one recognized subroutine header.

        The header match supplies attributes, dummy names, optional ``bind(c)``
        metadata, and interface ownership.  Dummy arguments become the initial
        case-insensitive symbol table for subsequent declarations.
        """
        attributes = self._attrs(match.group("prefix"), match.group("tail"))
        args = [
            FortranArgument(name=name, procedure=match.group("name")) for name in split_csv(match.group("args") or "")
        ]
        sig = FortranProcedureSignature(
            name=match.group("name"),
            kind="subroutine",
            module=module,
            arguments=args,
            attributes=attributes,
            bind_name=self._bind_c_name(match.group("tail")) if "bind(c)" in attributes else None,
            in_interface=in_interface,
        )
        return self._new_procedure_scope_state(sig, symbols={arg.name.lower(): arg for arg in args})

    def _function_scope(
        self,
        match,
        module: str | None,
        in_interface: bool,
        *,
        filename: str | None,
        lineno: int | None,
        source_line: str | None,
    ):
        """Create procedure state from one recognized function header.

        The helper initializes dummy arguments and the result symbol, parses an
        optional result-type prefix, and raises a source-located error for an
        unsupported prefix.  Its result symbol stays in the same scope table as
        arguments so finalization can detect shadowing and missing declarations.
        """
        prefix = (match.group("prefix") or "").strip()
        args = [
            FortranArgument(name=name, procedure=match.group("name")) for name in split_csv(match.group("args") or "")
        ]
        result_match = _REGEX["result"].search(match.group("tail"))
        explicit_result = result_match is not None
        result_name = result_match.group("name") if result_match else match.group("name")
        result = FortranArgument(name=result_name, procedure=match.group("name"))

        type_tokens = [t for t in prefix.split() if t.lower() not in _ATTR_PREFIX_WORDS]
        type_prefix = " ".join(type_tokens)
        parsed_prefix = self._parse_type_prefix(type_prefix)
        if type_prefix and parsed_prefix is None:
            raise FortranParseError(
                f"Unsupported function result type prefix '{type_prefix}' in procedure header.",
                filename=filename,
                line_number=lineno,
                source_line=source_line,
                code="PARSE_UNSUPPORTED_RESULT_TYPE",
            )
        if parsed_prefix:
            result.base_type, result.kind = parsed_prefix
            self._apply_type_spelling_metadata(result, type_prefix)
            if re.match(r"^class\s*\(", type_prefix, re.IGNORECASE):
                result._fortran_polymorphic = True

        attributes = self._attrs(match.group("prefix"), match.group("tail"))
        sig = FortranProcedureSignature(
            name=match.group("name"),
            kind="function",
            module=module,
            arguments=args,
            result=result,
            attributes=attributes,
            bind_name=self._bind_c_name(match.group("tail")) if "bind(c)" in attributes else None,
            in_interface=in_interface,
        )
        return self._new_procedure_scope_state(
            sig,
            symbols={**{a.name.lower(): a for a in args}, result_name.lower(): result},
            typed_symbols={result_name.lower()} if parsed_prefix else set(),
            explicit_result=explicit_result,
        )

    @staticmethod
    def _raise_if_unparsed_procedure_header(
        line: str,
        *,
        in_interface: bool,
        filename: str | None,
        lineno: int | None,
        source_line: str | None,
    ) -> None:
        """Reject malformed lines that still resemble procedure headers."""
        stripped = line.strip()
        if not stripped:
            return
        lowered = stripped.lower()
        if lowered.startswith("module procedure"):
            if in_interface or _REGEX["module_procedure_impl"].match(stripped) or "(" not in stripped:
                return
            raise FortranParseError(
                f"Unsupported or malformed module procedure header: {stripped}",
                filename=filename,
                line_number=lineno,
                source_line=source_line,
                code="PARSE_MALFORMED_HEADER",
            )
        if FortranParser._looks_like_procedure_header(stripped):
            raise FortranParseError(
                f"Unsupported or malformed procedure header: {stripped}",
                filename=filename,
                line_number=lineno,
                source_line=source_line,
                code="PARSE_MALFORMED_HEADER",
            )

    @staticmethod
    def _add_interface_attribute(sig: FortranProcedureSignature, interface_name: str | None) -> None:
        """Attach a stable `interface(name)` marker to a procedure signature."""
        if not interface_name:
            return
        iface_attr = f"interface({interface_name})"
        if iface_attr not in sig.attributes:
            sig.attributes.append(iface_attr)

    @staticmethod
    def _resolve_derived_type_extensions(types: list[FortranDerivedType]) -> None:
        """Link same-file `extends(parent)` names to parsed type models."""
        by_name = {t.name.lower(): t for t in types}
        for dtype in types:
            if isinstance(dtype.extends, str):
                parent = by_name.get(dtype.extends.lower())
                if parent is not None:
                    dtype.extends = parent

    # ------------------------------------------------------------------
    # Scope and procedure state helpers
    # ------------------------------------------------------------------

    def _helper_scope_for_model(
        self,
        kind: str,
        model: object,
        *,
        parent: _ParserScope | None = None,
        module_owner: str | None = None,
        state: dict | None = None,
    ) -> _ParserScope:
        """Build the scope object passed through shared helpers.

        This helper keeps scope construction consistent: every unit visitor
        passes its own model, parent scope, current module owner, and optional
        procedure state through the same small object.

        Example:
            A module procedure receives a procedure scope whose parent is the
            module scope and whose `module_owner` is the module name. The same
            declaration helper can then update procedure arguments while still
            knowing the owner for diagnostics and imports.
        """
        name = getattr(model, "name", None)
        inherited_owner = module_owner if module_owner is not None else (parent.module_owner if parent else None)
        if kind in {"module", "submodule"}:
            inherited_owner = name
        return _ParserScope(
            kind=kind,
            name=name,
            model=model,
            parent=parent,
            module_owner=inherited_owner,
            state=state,
        )

    @staticmethod
    def _scope_key(name: str) -> str:
        """Normalize a case-insensitive Fortran scope key."""
        return name.lower()

    def _new_procedure_scope_state(
        self,
        signature: FortranProcedureSignature,
        *,
        symbols: dict[str, FortranArgument],
        typed_symbols: set[str] | None = None,
        explicit_result: bool = False,
    ) -> dict:
        """Create mutable procedure parsing state shared by spec-line helpers."""
        state = {
            "signature": signature,
            "symbols": symbols,
            "typed_symbols": typed_symbols or set(),
            "uses": {},
            "local_uses": {},
            "in_contains": False,
            "local_params": {},
            "legacy_local_params": set(),
            "implicit_typed_symbols": {},
            "declared_local_types": {},
            "implicit_none": False,
            "imports": set(),
            "external_symbols": set(),
            "includes": [],
            "common_variables": [],
            "filename": None,
            "local_type_depth": 0,
        }
        if explicit_result:
            state["explicit_result"] = True
        return state

    def _proc_scope_get_symbol(self, proc_state: dict, name: str) -> FortranArgument | None:
        """Return one procedure symbol by case-insensitive name."""
        return proc_state["symbols"].get(self._scope_key(name))

    def _proc_scope_symbol_is_declared(self, proc_state: dict, name: str) -> bool:
        """Return whether a procedure symbol already has an explicit type."""
        return self._scope_key(name) in proc_state["typed_symbols"]

    def _proc_scope_mark_declared_symbol(
        self,
        proc_state: dict,
        name: str,
        *,
        filename: str | None = None,
        line_number: int | None = None,
        source_line: str | None = None,
    ) -> str:
        """Record an explicitly typed procedure symbol and reject duplicates."""
        key = self._scope_key(name)
        if key in proc_state["typed_symbols"]:
            raise FortranParseError(
                f"Duplicate declaration of symbol '{name}' in procedure '{proc_state['signature'].name}'.",
                filename=filename,
                line_number=line_number,
                source_line=source_line,
                code="PARSE_DUPLICATE_DECLARATION",
            )
        proc_state["typed_symbols"].add(key)
        return key

    def _proc_scope_add_external_symbol(self, proc_state: dict, name: str) -> str:
        """Record an external procedure symbol and update a matching dummy."""
        key = self._scope_key(name)
        proc_state.setdefault("external_symbols", set()).add(key)
        arg = self._proc_scope_get_symbol(proc_state, key)
        if arg is not None and arg.base_type == "unknown":
            arg.base_type = "procedure"
        return key

    def _proc_scope_add_include(self, proc_state: dict, include_path: str) -> None:
        """Record one procedure-local include path."""
        proc_state.setdefault("includes", []).append(include_path)

    def _proc_scope_add_imports(self, proc_state: dict, names: list[str]) -> None:
        """Record interface imports visible inside a procedure declaration."""
        proc_state.setdefault("imports", set()).update(self._scope_key(n) for n in names if n.strip())

    def _proc_scope_set_declared_local_type(self, proc_state: dict, name: str, meta: dict) -> None:
        """Store type metadata for a declared local symbol."""
        key = self._scope_key(name)
        declared_type = {
            "base_type": meta["base_type"],
            "kind": meta["kind"],
        }
        for metadata_key in (
            "target_kind_expression",
            "character_length_syntax",
            "declared_storage_bits",
            "polymorphic",
        ):
            if metadata_key in meta and (metadata_key != "polymorphic" or meta[metadata_key]):
                declared_type[metadata_key] = meta[metadata_key]
        proc_state["declared_local_types"][key] = declared_type

    def _proc_scope_add_local_parameter(
        self,
        proc_state: dict,
        name: str,
        value: str,
        *,
        filename: str | None = None,
        line_number: int | None = None,
        source_line: str | None = None,
        require_declared: bool = False,
        register_implicit_if_missing: bool = False,
        legacy: bool = False,
    ) -> None:
        """Store one local parameter expression and validate declaration policy."""
        key = self._scope_key(name)
        if require_declared and not self._proc_scope_symbol_is_declared(proc_state, key):
            raise FortranParseError(
                f"Unknown datatype for PARAMETER symbol '{name}' in procedure '{proc_state['signature'].name}'.",
                filename=filename,
                line_number=line_number,
                source_line=source_line,
                code="PARSE_UNKNOWN_PARAMETER_TYPE",
            )
        if key in proc_state["local_params"]:
            raise FortranParseError(
                f"Duplicate PARAMETER declaration of symbol '{name}' in procedure '{proc_state['signature'].name}'.",
                filename=filename,
                line_number=line_number,
                source_line=source_line,
                code="PARSE_DUPLICATE_PARAMETER",
            )
        proc_state["local_params"][key] = value
        if register_implicit_if_missing and not self._proc_scope_symbol_is_declared(proc_state, key):
            proc_state["implicit_typed_symbols"][key] = self._infer_implicit_base_type(name)
        if legacy:
            proc_state["legacy_local_params"].add(key)

    @staticmethod
    def _insert_unique_scope_symbol(
        scope: dict[str, object],
        key: str,
        value: object,
        *,
        label: str,
        filename: str | None = None,
    ) -> None:
        """Insert one scope symbol or raise a duplicate-name diagnostic."""
        if key in scope:
            raise FortranParseError(
                f"Duplicate symbol '{key}' in {label}.",
                filename=filename,
                code="PARSE_DUPLICATE_SYMBOL",
            )
        scope[key] = value

    # ------------------------------------------------------------------
    # Specification-part visitors
    # ------------------------------------------------------------------

    def _parse_specification_part(
        self,
        scope: _ParserScope,
        lines: _PreprocessedLines,
        *,
        filename: str | None,
    ) -> None:
        """Visit declaration/specification lines for a unit scope.

        The helper name mirrors the grammar term "specification part". It is
        called by module, submodule, program, procedure, derived-type, and
        block-data visitors after `_helper_split_unit_parts` has isolated the
        relevant region.

        Example:
            A program and a procedure both have executable statements, but this
            helper only sees their declaration lines before execution begins.
            The visitor decides whether later execution/contains regions are
            ignored or visited separately.
        """
        for line, lineno, source_line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            if scope.kind == "procedure":
                self._parse_procedure_spec_line(
                    stripped,
                    scope.state,
                    filename=filename,
                    lineno=lineno,
                    source_line=source_line,
                )
            elif scope.kind == "derived_type":
                self._parse_type_spec_line(
                    stripped,
                    scope,
                    filename,
                    lineno=lineno,
                    source_line=source_line,
                )
            elif scope.kind in {"module", "submodule", "program", "block_data"}:
                self._parse_module_like_spec_line(
                    scope,
                    stripped,
                    filename=filename,
                    lineno=lineno,
                    source_line=source_line,
                )

    def _parse_module_like_spec_line(
        self,
        scope: _ParserScope,
        line: str,
        *,
        filename: str | None,
        lineno: int | None,
        source_line: str | None,
    ) -> None:
        """Visit one module/submodule/program/block-data specification line.

        These units all expose module-like declarations: ``use`` statements,
        visibility statements where applicable, and variable/parameter
        declarations that land in ``target.variables`` through the common
        declaration backend.

        Example:
            In a program scope, ``integer, parameter :: n = 8`` is parsed by
            `_helper_parse_declaration_line` and pushed to
            `program.variables`. In a module scope, ``private :: work`` updates
            module visibility instead of creating a variable.
        """
        target = scope.model
        if target is None:  # pragma: no cover - internal helper misuse.
            raise FortranParseError(
                "Module-like specification scope is missing a target model.",
                filename=filename,
                code="PARSE_INTERNAL_STATE",
            )
        stripped = line.strip()
        lower = stripped.lower()

        if re.match(r"^common\b", stripped, flags=re.IGNORECASE):
            self._record_common_variables(target.common_variables, stripped)
            return

        if self._is_openmp_declarative_directive(stripped):
            self._raise_unsupported_openmp_declaration(target, stripped, filename, lineno, source_line)

        if self._apply_default_module_visibility(scope, target, lower):
            return

        parsed_use = self._parse_use_statement(stripped)
        if parsed_use and hasattr(target, "uses"):
            module_name, mappings = parsed_use
            target.uses[module_name] = mappings
            return

        if _REGEX["derived_type"].match(stripped):
            parsed_type = self._parse_derived_type_start(stripped)
            raise FortranParseError(
                f"Missing end derived type for derived type '{parsed_type[0] if parsed_type else '<unnamed>'}'.",
                filename=filename,
                line_number=lineno,
                source_line=source_line,
                code="PARSE_MISSING_DERIVED_TYPE_END",
            )

        if "::" in stripped:
            left, right = [x.strip() for x in stripped.split("::", 1)]
            if self._apply_module_attribute_statement(scope, target, left.lower(), right):
                return
        elif self._handle_non_declaration_spec_line(scope, target, stripped, filename, lineno, source_line):
            return

        parsed = self._helper_parse_declaration_line(
            stripped,
            scope,
            role=self._helper_unit_grammar(scope.kind).declaration_role or "module_variable",
            filename=filename,
            lineno=lineno,
            source_line=source_line,
            parse_character_star=scope.kind not in {"module", "submodule"},
        )
        if parsed:
            return
        self._raise_unsupported_module_like_declaration(target, stripped, filename, lineno, source_line)

    def _raise_unsupported_openmp_declaration(self, target, line, filename, lineno, source_line) -> None:
        """Raise the stable diagnostic for an unsupported OpenMP declaration.

        ``target`` determines the parser scope label; the remaining arguments
        preserve the original source location in the emitted error.
        """
        owner_kind, owner_name = self._variable_scope_label(target)
        raise FortranParseError(
            f"Unsupported OpenMP declarative directive in {owner_kind} '{owner_name or '<unnamed>'}': {line}",
            filename=filename,
            line_number=lineno,
            source_line=source_line,
            code="PARSE_UNSUPPORTED_OPENMP_DIRECTIVE",
        )

    @staticmethod
    def _apply_default_module_visibility(scope: _ParserScope, target, line: str) -> bool:
        """Apply a bare module-wide ``public`` or ``private`` statement.

        Returns ``True`` only when it consumed a module visibility statement;
        callers then avoid treating the line as a declaration.  ``target`` is
        mutated in place and all other scope kinds are left untouched.
        """
        if scope.kind != "module" or line not in {"private", "public"}:
            return False
        target.default_visibility = line
        return True

    @staticmethod
    def _apply_module_attribute_statement(scope: _ParserScope, target, attribute: str, value: str) -> bool:
        """Apply a supported module attribute statement and report consumption.

        The helper records named ``public``/``private`` visibility in source
        order or updates the default visibility for an empty list.  It also
        consumes grammar-only ``module procedure`` and ``import`` lines; other
        attributes return ``False`` for normal declaration handling.
        """
        if attribute in {"module procedure", "import"}:
            return True
        if scope.kind != "module" or attribute not in {"public", "private"}:
            return False
        names = [name.strip() for name in split_csv(value) if name.strip()]
        if names:
            getattr(target, f"{attribute}_symbols").extend(names)
        else:
            target.default_visibility = attribute
        return True

    def _handle_non_declaration_spec_line(self, scope, target, line, filename, lineno, source_line) -> bool:
        """Consume ignored specification text or reject illegal executable text.

        Returns ``True`` when the caller should stop processing ``line``.  A
        program may contain execution statements after its declaration region;
        other module-like scopes receive a source-located error instead.
        """
        executable = self._is_executable_statement_start(line)
        if not executable and not self._is_ignored_spec_statement(line):
            return False
        if executable and scope.kind != "program":
            owner_kind, owner_name = self._variable_scope_label(target)
            raise FortranParseError(
                f"Executable statement is not allowed in {owner_kind} specification part "
                f"'{owner_name or '<unnamed>'}': {line}",
                filename=filename,
                line_number=lineno,
                source_line=source_line,
                code="PARSE_EXECUTABLE_IN_SPECIFICATION",
            )
        return True

    def _raise_unsupported_module_like_declaration(self, target, line, filename, lineno, source_line) -> None:
        """Raise the precise unsupported-declaration error for one scope line.

        Clearly non-declarative text is first classified as invalid syntax;
        declaration-like text retains the established unsupported-datatype
        diagnostic.  Both errors preserve the owner label and source location.
        """
        owner_kind, owner_name = self._variable_scope_label(target)
        if "::" not in line and not self._looks_like_declaration_or_spec(line):
            self._raise_invalid_fortran_syntax_line(
                line,
                context=f"{owner_kind} '{owner_name or '<unnamed>'}' specification part",
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )
        raise FortranParseError(
            f"Unknown or unsupported datatype declaration in {owner_kind} '{owner_name or '<unnamed>'}': {line}",
            filename=filename,
            line_number=lineno,
            source_line=source_line,
            code="PARSE_UNSUPPORTED_DECLARATION",
        )

    def _parse_procedure_spec_line(
        self,
        line: str,
        proc_state: dict,
        filename: str | None = None,
        lineno: int | None = None,
        source_line: str | None = None,
    ) -> None:
        """Parse one declaration/specification line inside a procedure scope.

        The method mutates `proc_state` in-place by:
        - registering typed symbols and parameter constants,
        - annotating argument metadata (type/kind/access/rank/shape),
        - recording imports/includes/external callbacks,
        - transitioning unsupported/unknown declarations into explicit errors.

        Example:
            ``real :: x(n)`` goes through
            `_helper_parse_declaration_line` with role ``"procedure_symbol"``
            and updates the existing dummy argument ``x`` in the procedure
            scope.
        """
        stripped = line.strip()
        if re.match(r"^common\b", stripped, flags=re.IGNORECASE):
            self._record_common_variables(proc_state["common_variables"], stripped)
            return
        if self._is_openmp_declarative_directive(stripped):
            raise FortranParseError(
                f"Unsupported OpenMP declarative directive in procedure '{proc_state['signature'].name}': {stripped}",
                filename=filename,
                line_number=lineno,
                source_line=source_line,
                code="PARSE_UNSUPPORTED_OPENMP_DIRECTIVE",
            )
        if self._handle_proc_implicit_line(stripped, proc_state):
            return
        if self._handle_proc_external_line(stripped, proc_state):
            return
        parsed_use = self._parse_use_statement(stripped)
        if parsed_use:
            module_name, mappings = parsed_use
            proc_state["uses"][module_name] = mappings
            proc_state["local_uses"][module_name] = mappings
            return
        # This parser is a subset parser focused on wrapper-relevant metadata.
        # These statements do not affect extracted signature typing/shapes.
        if self._is_ignored_proc_spec_line(stripped):
            return
        if self._handle_proc_include_or_import_line(stripped, proc_state):
            return
        if self._handle_proc_parameter_line(
            stripped,
            proc_state,
            filename=filename,
            lineno=lineno,
            source_line=source_line,
        ):
            return
        if self._is_statement_function_statement(stripped):
            return

        parsed = self._helper_parse_declaration_line(
            stripped,
            _ParserScope(
                kind="procedure",
                name=proc_state["signature"].name,
                model=proc_state["signature"],
                state=proc_state,
                module_owner=proc_state["signature"].module,
            ),
            role="procedure_symbol",
            filename=proc_state.get("filename") or filename,
            lineno=lineno,
            source_line=source_line,
            include_argument_access=True,
        )
        if not parsed:
            self._handle_unknown_proc_declaration(
                line,
                proc_state,
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )
            return

    def _parse_type_spec_line(
        self,
        line: str,
        scope: _ParserScope,
        filename: str | None,
        lineno: int | None = None,
        source_line: str | None = None,
    ) -> None:
        """Visit one derived-type specification-part line.

        Derived types share the common declaration parser for fields, but keep
        their own visitor because the type grammar has type-only statements
        such as ``sequence`` and a later ``contains`` region for bindings.

        Example:
            ``real :: values(n)`` is parsed through
            `_helper_parse_declaration_line` with role ``"type_field"`` and
            appended to `dtype.fields`. ``sequence`` is consumed here without
            creating a field.
        """
        dtype = scope.model
        if dtype is None:  # pragma: no cover - internal helper misuse.
            raise FortranParseError(
                "Derived-type specification scope is missing a target model.",
                filename=filename,
                code="PARSE_INTERNAL_STATE",
            )
        stripped = line.strip()
        if re.match(r"^type\s*::\s*\w+$", stripped, re.IGNORECASE):
            raise FortranParseError(
                f"Missing end derived type for derived type '{stripped.split('::', 1)[1].strip()}'.",
                filename=filename,
                line_number=lineno,
                source_line=source_line,
                code="PARSE_MISSING_DERIVED_TYPE_END",
            )
        if stripped.lower() == "sequence":
            if "sequence" not in dtype.attributes:
                dtype.attributes.append("sequence")
            return
        if stripped.lower() == "private":
            return
        if self._is_openmp_declarative_directive(stripped):
            raise FortranParseError(
                f"Unsupported OpenMP declarative directive in type '{dtype.name}': {stripped}",
                filename=filename,
                line_number=lineno,
                source_line=source_line,
                code="PARSE_UNSUPPORTED_OPENMP_DIRECTIVE",
            )
        parsed = self._helper_parse_declaration_line(
            stripped,
            scope,
            role="type_field",
            filename=filename,
            lineno=lineno,
            source_line=source_line,
            parse_character_star=False,
        )
        if parsed:
            return
        if "::" not in stripped and not self._looks_like_declaration_or_spec(stripped):
            self._raise_invalid_fortran_syntax_line(
                stripped,
                context=f"type '{dtype.name}' specification part",
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )
        raise FortranParseError(
            f"Unknown or unsupported datatype declaration in type '{dtype.name}': {line.strip()}",
            filename=filename,
            line_number=lineno,
            source_line=source_line,
            code="PARSE_UNSUPPORTED_DECLARATION",
        )

    def _parse_derived_type_contains_line(
        self,
        line: str,
        dtype: FortranDerivedType,
        *,
        filename: str | None = None,
        lineno: int | None = None,
        source_line: str | None = None,
    ) -> None:
        """Parse type-bound procedure and generic bindings after `contains`."""
        proc_binding = _REGEX["procedure_binding"].match(line)
        if proc_binding:
            binding_names = split_csv(proc_binding.group("names"))
            dtype.methods.extend(binding_names)
            left = line.split("::", 1)[0]
            attrs = [a.strip().lower() for a in split_csv(left.split(",", 1)[1] if "," in left else "")]
            for name in binding_names:
                dtype.procedure_bindings.append({"name": name, "attrs": attrs})
            return

        if line.lower().startswith("generic") and "::" in line and "=>" in line:
            left, right = [x.strip() for x in line.split("::", 1)]
            attr_txt = left[len("generic") :].strip().lstrip(",").strip()
            attrs = [a.strip().lower() for a in split_csv(attr_txt)] if attr_txt else []
            lhs, rhs_txt = [x.strip() for x in right.split("=>", 1)]
            rhs = [r.strip() for r in split_csv(rhs_txt)]
            dtype.generic_bindings.append({"name": lhs, "targets": rhs, "attrs": attrs})
            return

        if re.match(r"^final\s*::\s*[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s*$", line, re.IGNORECASE):
            dtype.final_procedures.extend(split_csv(line.split("::", 1)[1]))
            return

        raise FortranParseError(
            f"Unsupported or malformed type-bound declaration in type '{dtype.name}': {line.strip()}",
            filename=filename,
            line_number=lineno,
            source_line=source_line,
            code="PARSE_UNSUPPORTED_TYPE_BOUND_DECLARATION",
        )

    def _helper_apply_local_interface_declarations(
        self,
        proc_state: dict,
        unit: SourceUnit,
        parts: _UnitParts,
        scope: _ParserScope,
        *,
        filename: str | None,
    ) -> None:
        """Mark dummy arguments declared by procedure-local interface blocks.

        Interface blocks inside procedures are not wrapper targets themselves,
        but their procedure names can be dummy arguments of the enclosing
        procedure. This helper reuses the source-unit slicer to find those
        local interface declarations and annotate the matching argument as a
        procedure callback.

        Example:
            In ``subroutine apply(cb)`` with a local ``interface`` containing
            ``subroutine cb(x)``, this helper updates the already-known dummy
            argument ``cb`` so its base type becomes ``"procedure"``.
        """
        interface_units = self._helper_slice_child_units(
            unit.lines[1:-1],
            parent_scope=scope,
            allowed_kinds={"interface"},
            filename=filename,
            skip_execution_region=True,
        )
        for interface_unit in interface_units:
            if self._helper_child_unit_region(unit, parts, interface_unit) == "execution":
                continue
            interface = self._visit(interface_unit, parent_scope=scope, filename=filename)
            for signature in interface.procedures:
                name = signature.name
                if self._proc_scope_symbol_is_declared(proc_state, name):
                    key = self._scope_key(name)
                else:
                    key = self._proc_scope_mark_declared_symbol(
                        proc_state,
                        name,
                        filename=filename,
                        line_number=interface_unit.start_line,
                        source_line=interface_unit.lines[0][2] if interface_unit.lines else None,
                    )
                arg = self._proc_scope_get_symbol(proc_state, key)
                if arg is not None and arg.base_type == "unknown":
                    arg.base_type = "procedure"
                    arg.kind = ""

    # ------------------------------------------------------------------
    # Declaration parsing and symbol storage
    # ------------------------------------------------------------------

    def _helper_parse_declaration_line(
        self,
        line: str,
        scope: _ParserScope,
        *,
        role: str,
        filename: str | None,
        lineno: int | None,
        source_line: str | None,
        include_argument_access: bool = False,
        parse_character_star: bool = True,
    ) -> bool:
        """Parse one declaration line and store it in `scope`.

        This is the common declaration backend for module variables, program
        variables, block-data variables, derived-type fields, and procedure
        arguments/results. The `role` argument captures the small differences
        in where the parsed symbol is pushed.

        Example:
            ``real :: x(:)`` with role ``procedure_symbol`` updates
            the active procedure argument. ``real :: x(:)`` with role
            ``module_variable`` appends a `FortranVariable` to the module.
        """
        if "::" in line:
            left, right = [x.strip() for x in line.split("::", 1)]
            has_separator = True
        else:
            left = line.strip()
            right = ""
            has_separator = False

        parsed_decl = self._parse_declaration_left(left, parse_character_star=parse_character_star)
        if parsed_decl is None:
            return False
        meta, attrs = parsed_decl
        if not has_separator:
            legacy_right = self._legacy_declaration_entities(left, meta)
            if legacy_right is not None:
                right = legacy_right
                attrs = []
        self._apply_decl_attrs(meta, attrs, include_argument_access=include_argument_access)
        self._helper_push_declaration_to_scope(
            scope,
            meta=meta,
            right=right,
            role=role,
            filename=filename,
            lineno=lineno,
            source_line=source_line,
        )
        return True

    def _parse_declaration_left(
        self,
        left: str,
        *,
        parse_character_star: bool = True,
    ) -> tuple[dict, list[str]] | None:
        """Parse a declaration prefix into normalized metadata and attributes."""
        star_kind = self._find_legacy_star_kind(left)
        char_star = _REGEX["char_star"].match(left) if parse_character_star else None
        if char_star:
            kind = char_star.group("len").strip()
            if kind.startswith("(") and kind.endswith(")"):
                kind = kind[1:-1].strip()
            trailing = (char_star.group("rest") or "").strip().lstrip(", ")
            meta = self._new_decl_meta("character", kind)
            meta["character_length_syntax"] = True
            return meta, split_csv(trailing)
        if star_kind:
            base, kind = star_kind
            tail = self._strip_legacy_star_kind_prefix(left)
            attrs = split_csv(tail.lstrip(", ")) if tail.startswith(",") else []
            meta = self._new_decl_meta(base.lower(), kind)
            if base.lower() == "character":
                meta["character_length_syntax"] = True
            else:
                meta["declared_storage_bits"] = int(kind) * 8
            return meta, attrs

        intrinsic = self._split_intrinsic_type_spec(left)
        derived = _REGEX["type_field"].match(left)
        class_derived = _REGEX["class_field"].match(left)
        if intrinsic:
            base, type_spec, tail = intrinsic
            meta = self._intrinsic_decl_meta(base, type_spec)
            return meta, split_csv(tail.strip().lstrip(", "))
        if derived or class_derived:
            decl = derived or class_derived
            meta = self._new_decl_meta("derived", decl.group("dtype"))
            meta["polymorphic"] = class_derived is not None
            return meta, split_csv((decl.group("attrs") or "").strip().lstrip(", "))
        if re.match(r"^procedure\s*\(", left, re.IGNORECASE):
            procm = _REGEX["procedure_dummy"].match(left)
            iface = procm.group("iface").lower() if procm else None
            return self._new_decl_meta("procedure", iface), split_csv(
                (procm.group("attrs") if procm else "").strip().lstrip(", ")
            )
        return None

    def _legacy_declaration_entities(self, left: str, meta: dict) -> str | None:
        """Return the entity-list tail from a declaration without `::`."""
        char_star = _REGEX["char_star"].match(left)
        if char_star:
            return (char_star.group("rest") or "").strip().lstrip(", ")

        star_kind = self._find_legacy_star_kind(left)
        if star_kind and meta["base_type"] != "character":
            return self._strip_legacy_star_kind_prefix(left).lstrip(", ")

        intrinsic = self._split_intrinsic_type_spec(left)
        if intrinsic:
            return intrinsic[2].strip().lstrip(", ")

        derived = _REGEX["type_field"].match(left) or _REGEX["class_field"].match(left)
        if derived:
            return (derived.group("attrs") or "").strip().lstrip(", ")

        procm = _REGEX["procedure_dummy"].match(left)
        if procm:
            tail = (procm.group("attrs") or "").strip()
            if tail and not tail.startswith(","):
                return tail
        return None  # pragma: no cover - invalid legacy declaration tails are ignored.

    def _helper_push_declaration_to_scope(
        self,
        scope: _ParserScope,
        *,
        meta: dict,
        right: str,
        role: str,
        filename: str | None,
        lineno: int | None,
        source_line: str | None,
    ) -> None:
        """Push parsed declaration entities into the correct scope model.

        The name says "push" because parsing a declaration is only half of the
        job; the other half is storing the resulting symbol in the active unit
        scope. This helper is the common storage point for variables, fields,
        and procedure arguments/results.

        Example:
            ``integer :: n`` in a module appends `FortranVariable("n")` to
            `module.variables`, while the same declaration inside
            ``subroutine step(n)`` updates the existing `FortranArgument("n")`
            in the procedure signature.
        """
        if role == "procedure_symbol":
            proc_state = scope.state
            if proc_state is None:  # pragma: no cover - internal helper misuse.
                raise FortranParseError(
                    "Procedure declaration scope is missing state.",
                    filename=filename,
                    code="PARSE_INTERNAL_STATE",
                )
            if meta["base_type"] == "procedure" and meta["kind"] in proc_state.get("imports", set()):
                meta["kind"] = None
            for entity in split_csv(right):
                raw_name, shape = self._var(entity)
                if not raw_name:
                    continue
                entity_meta = self._entity_decl_meta(raw_name, meta)
                normalized_name = self._normalize_declared_name(raw_name, entity_meta)
                if not normalized_name:
                    continue
                lowered_name = self._proc_scope_mark_declared_symbol(
                    proc_state,
                    normalized_name,
                    filename=filename,
                    line_number=lineno,
                    source_line=source_line,
                )
                if meta.get("external"):
                    self._proc_scope_add_external_symbol(proc_state, lowered_name)
                arg = self._proc_scope_get_symbol(proc_state, lowered_name)
                if arg is None:
                    self._proc_scope_set_declared_local_type(proc_state, lowered_name, entity_meta)
                    continue
                self._apply(arg, entity_meta, shape)
            return

        target = scope.model
        if target is None:  # pragma: no cover - internal helper misuse.
            raise FortranParseError(
                "Declaration scope is missing a target model.",
                filename=filename,
                code="PARSE_INTERNAL_STATE",
            )

        for entity in split_csv(right):
            initializer = entity.split("=", 1)[1].strip() if "=" in entity else None
            raw_name, shape = self._var(entity)
            if not raw_name:
                continue
            entity_meta = self._entity_decl_meta(raw_name, meta)
            normalized_name = self._normalize_declared_name(raw_name, entity_meta)
            if not normalized_name:
                continue
            if role == "type_field":
                field = FortranArgument(name=normalized_name)
                self._apply(field, entity_meta, shape)
                if initializer is not None:
                    field.value = self._normalize_parameter_value(initializer)
                    field.symbolic_value = initializer
                    field.value_type = "expression"
                target.fields.append(field)
                continue
            var = FortranArgument(name=normalized_name)
            self._apply(var, entity_meta, shape)
            self._record_declaration_visibility(scope, target, var, entity_meta)
            if initializer is not None and meta["parameter"]:
                var.value = self._normalize_parameter_value(initializer)
                var.symbolic_value = initializer
                var.value_type = "expression"
            target.variables.append(var)

    @staticmethod
    def _record_declaration_visibility(scope: _ParserScope, target, var: FortranArgument, meta: dict) -> None:
        """Make declaration-level module visibility survive finalization."""
        visibility = meta.get("explicit_visibility")
        if scope.kind != "module" or visibility not in {"public", "private"}:
            return
        symbols = getattr(target, f"{visibility}_symbols")
        if var.name.casefold() not in {name.casefold() for name in symbols}:
            symbols.append(var.name)

    @staticmethod
    def _entity_decl_meta(raw_name: str, meta: dict) -> dict:
        """Copy character metadata when one entity supplies ``*length`` syntax.

        Non-character entities and declarations without an entity-level star
        return the original ``meta`` mapping unchanged.  For ``character``
        entities, a copied mapping records the length as ``kind`` without
        mutating sibling entities' declaration metadata.
        """
        if meta["base_type"] != "character":
            return meta
        match = re.search(r"\*\s*(\([^)]*\)|\*|[A-Za-z_]\w*|\d+)\s*$", raw_name)
        if match is None:
            return meta
        length = match.group(1).strip()
        if length.startswith("(") and length.endswith(")"):
            length = length[1:-1].strip()
        entity_meta = dict(meta)
        entity_meta["kind"] = length
        entity_meta["character_length_syntax"] = True
        return entity_meta

    @staticmethod
    def _new_decl_meta(base_type: str, kind: str | None) -> dict:
        """Return default declaration metadata for one normalized base type."""
        return {
            "base_type": base_type,
            "kind": kind or "",
            "rank": 0,
            "shape": [],
            "intent": None,
            "reads_argument": None,
            "writes_argument": None,
            "optional": False,
            "value": False,
            "allocatable": False,
            "pointer": False,
            "target": False,
            "contiguous": False,
            "external": False,
            "parameter": False,
            "polymorphic": False,
            "visibility": "public",
            "explicit_visibility": None,
        }

    @staticmethod
    def _intrinsic_decl_meta(base_type: str, type_spec: str) -> dict:
        """Normalize one intrinsic spelling while retaining target-only facts."""
        if base_type in {"double precision", "double complex"}:
            normalized = "real" if base_type == "double precision" else "complex"
            meta = FortranParser._new_decl_meta(normalized, None)
            meta["target_kind_expression"] = "kind(1.0d0)"
            return meta

        meta = FortranParser._new_decl_meta(base_type, extract_kind_from_type_spec(base_type, type_spec))
        if base_type == "character" and type_spec and re.search(r"\bkind\s*=", type_spec, re.IGNORECASE) is None:
            meta["character_length_syntax"] = True
        return meta

    @staticmethod
    def _apply_type_spelling_metadata(var: FortranVariable, spelling: str) -> None:
        """Attach target-only facts from a standalone type prefix."""
        star_kind = FortranParser._find_legacy_star_kind(spelling)
        if star_kind is not None:
            base_type, width = star_kind
            if base_type == "character":
                var._character_length_syntax = True
            else:
                var._declared_storage_bits = int(width) * 8
            return
        if _REGEX["char_star"].match(spelling):
            var._character_length_syntax = True
            return

        intrinsic = FortranParser._split_intrinsic_type_spec(spelling)
        if intrinsic is None:
            return
        base_type, type_spec, _tail = intrinsic
        if base_type in {"double precision", "double complex"}:
            var._target_kind_expression = "kind(1.0d0)"
        elif base_type == "character" and type_spec and re.search(r"\bkind\s*=", type_spec, re.IGNORECASE) is None:
            var._character_length_syntax = True

    @staticmethod
    def _apply_decl_attrs(meta: dict, attrs: list[str], *, include_argument_access: bool = False) -> None:
        """Merge declaration attributes into normalized metadata."""
        for a in attrs:
            la = a.lower()
            if include_argument_access and la.startswith("intent") and "(" in la and ")" in la:
                content = re.sub(r"\s+", "", la.split("(", 1)[1].rsplit(")", 1)[0])
                meta["intent"] = content
                meta["reads_argument"] = content.startswith("in")
                meta["writes_argument"] = content.endswith("out")
            elif la == "optional":
                meta["optional"] = True
            elif la == "value":
                meta["value"] = True
            elif la == "allocatable":
                meta["allocatable"] = True
            elif la == "pointer":
                meta["pointer"] = True
            elif la == "target":
                meta["target"] = True
            elif la == "contiguous":
                meta["contiguous"] = True
            elif la == "external":
                meta["external"] = True
            elif la == "parameter":
                meta["parameter"] = True
            elif la in {"public", "private"}:
                meta["visibility"] = la
                meta["explicit_visibility"] = la
            elif la.startswith("dimension") and "(" in a and ")" in a:
                shape = split_csv(a[a.find("(") + 1 : a.rfind(")")])
                meta["shape"] = shape
                meta["rank"] = len(shape)

    @staticmethod
    def _normalize_declared_name(name: str, meta: dict) -> str:
        """Strip legacy entity-local spelling from a declared symbol name."""
        normalized_name = re.sub(r"^\*\s*[0-9]+\s*", "", name).strip()
        if meta["base_type"] == "character" and "*" in normalized_name:
            # Legacy CHARACTER declarations may carry entity-local length
            # specifiers (e.g. NAME*(*) or SUBNAM*6). Strip the `*len`
            # suffix so symbol lookup matches procedure arguments.
            normalized_name = normalized_name.split("*", 1)[0].strip()
        return normalized_name

    @staticmethod
    def _strip_legacy_star_kind_prefix(left: str) -> str:
        """Remove an intrinsic `type*kind` prefix from a legacy declaration."""
        return re.sub(
            r"^(integer|real|complex|logical|character)\s*\*\s*[0-9]+\s*",
            "",
            left,
            flags=re.IGNORECASE,
        ).strip()

    @staticmethod
    def _var(entry: str):
        """Split one declaration entity into its name and inline dimensions."""
        e = entry.strip()
        if not e:  # pragma: no cover - split_csv omits empty declaration entities for valid declarations.
            return "", []
        if "=" in e:
            # Keep only the declared entity name/shape; drop initializer text.
            e = e.split("=", 1)[0].strip()
        if "(" in e and e.endswith(")"):
            name = e[: e.find("(")].strip()
            return name, split_csv(e[e.find("(") + 1 : -1])
        return e, []

    @staticmethod
    def _apply(arg: FortranArgument, meta: dict, shape: list[str]):
        """Apply normalized declaration metadata to an argument-like model."""
        arg.base_type = meta["base_type"]
        arg.kind = meta["kind"] or ""
        arg.intent = meta["intent"]
        arg.reads_argument = meta["reads_argument"]
        arg.writes_argument = meta["writes_argument"]
        arg.optional = meta["optional"]
        arg.pass_by_value = meta["value"]
        arg.allocatable = meta["allocatable"]
        arg.pointer = meta["pointer"]
        arg.target = meta["target"]
        arg.contiguous = meta["contiguous"]
        arg.is_parameter = meta["parameter"]
        arg.visibility = meta["visibility"]
        FortranParser._apply_internal_type_metadata(arg, meta)
        if shape:
            arg.shape = shape
            arg.rank = len(shape)
        else:
            arg.shape = list(meta["shape"])
            arg.rank = meta["rank"]
        arg.lbound, arg.ubound = FortranParser._extract_bounds(arg.shape)

    @staticmethod
    def _apply_internal_type_metadata(arg: FortranVariable, meta: dict) -> None:
        """Apply compiler-relevant facts that stay outside serialized models."""
        if meta.get("target_kind_expression"):
            arg._target_kind_expression = meta["target_kind_expression"]
        if meta.get("character_length_syntax"):
            arg._character_length_syntax = True
        if meta.get("declared_storage_bits") is not None:
            arg._declared_storage_bits = int(meta["declared_storage_bits"])
        if meta.get("polymorphic"):
            arg._fortran_polymorphic = True

    @staticmethod
    def _split_dim_bounds(dim: str) -> tuple[str | None, str | None]:
        """Normalize one dimension into lower and upper bound text."""
        part = dim.strip()
        if not part:  # pragma: no cover - empty dimensions are invalid Fortran and not emitted by split_csv.
            return None, None
        if ":" not in part:
            return "1", part
        lo, hi = part.split(":", 1)
        lo = lo.strip() or None
        hi = hi.strip() or None
        return lo, hi

    @staticmethod
    def _extract_bounds(shape: list[str]) -> tuple[list[str | None], list[str | None]]:
        """Extract parallel lower/upper bound lists from serialized dimensions."""
        lbounds: list[str | None] = []
        ubounds: list[str | None] = []
        for dim in shape:
            lo, hi = FortranParser._split_dim_bounds(dim)
            lbounds.append(lo)
            ubounds.append(hi)
        return lbounds, ubounds

    # ------------------------------------------------------------------
    # Procedure specification handlers
    # ------------------------------------------------------------------

    def _handle_proc_implicit_line(self, line: str, proc_state: dict) -> bool:
        """Handle a procedure ``implicit`` statement.

        Procedure parsing keeps implicit typing in the procedure state because
        it affects later finalization of undeclared dummy arguments.

        Example:
            ``implicit none`` sets ``proc_state["implicit_none"]`` so
            `_finalize_proc` can require every argument to have an explicit
            declaration.
        """
        if not re.match(r"^implicit\b", line, flags=re.IGNORECASE):
            return False
        if re.match(r"^implicit\s+none\b", line, flags=re.IGNORECASE):
            proc_state["implicit_none"] = True
        return True

    def _handle_proc_external_line(self, line: str, proc_state: dict) -> bool:
        """Handle a procedure ``external`` statement.

        External symbols are stored in the procedure state before declaration
        parsing so a later declaration can mark the corresponding argument as
        a callback-like symbol.

        Example:
            ``external f, g`` records ``f`` and ``g`` in the procedure scope's
            external-symbol set and returns ``True`` to stop further handling
            of the line.
        """
        external_match = re.match(r"^external\b\s*(?:::)?\s*(?P<names>.*)$", line, flags=re.IGNORECASE)
        if not external_match:
            return False
        names = [n.strip().lower() for n in split_csv(external_match.group("names") or "") if n.strip()]
        for name in names:
            self._proc_scope_add_external_symbol(proc_state, name)
        return True

    @staticmethod
    def _is_ignored_proc_spec_line(line: str) -> bool:
        """Return whether a procedure spec line is intentionally metadata-only."""
        ignored_patterns = (
            r"^(function|subroutine)\b",
            r"^intrinsic\b",
            r"^data\b",
            r"^equivalence\b",
            r"^format\s*\(",
            r"^go\s*to\b",
            r"^use\b",
            r"^save\b",
            r"^common\b",
        )
        return any(re.match(pattern, line, flags=re.IGNORECASE) for pattern in ignored_patterns)

    def _handle_proc_include_or_import_line(self, line: str, proc_state: dict) -> bool:
        """Handle procedure-level ``include`` and ``import`` statements.

        These statements are procedure-specific specification-part metadata, so
        they stay outside the common declaration parser while still feeding the
        same procedure state used by argument finalization.

        Example:
            ``import :: c_ptr`` records ``c_ptr`` as an imported symbol, while
            ``include "shape.inc"`` records the include path on the signature.
        """
        include_match = _REGEX["include"].match(line)
        if include_match:
            self._proc_scope_add_include(proc_state, include_match.group("path"))
            return True
        import_match = _REGEX["import"].match(line)
        if import_match:
            symbols = [s.strip().lower() for s in split_csv(import_match.group("symbols") or "") if s.strip()]
            self._proc_scope_add_imports(proc_state, symbols)
            return True
        return False

    def _handle_proc_parameter_line(
        self,
        line: str,
        proc_state: dict,
        *,
        filename: str | None,
        lineno: int | None,
        source_line: str | None,
    ) -> bool:
        """Handle modern and legacy procedure-local parameter statements.

        Parameters are collected into procedure state first, then
        `_finalize_proc` decides which ones are relevant to argument kinds and
        shapes and exposes those as procedure variables.

        Example:
            ``integer, parameter :: n = 2*m`` stores ``n -> "2*m"`` for
            compile-time shape resolution. Legacy ``parameter (n=4)`` is also
            accepted in fixed-form-style sources.
        """
        param_match = _REGEX["typed_parameter"].match(line)
        if param_match:
            for assign in split_csv(param_match.group("body")):
                if "=" not in assign:
                    continue
                name, value = [x.strip() for x in assign.split("=", 1)]
                self._proc_scope_add_local_parameter(
                    proc_state,
                    name,
                    value,
                    filename=filename,
                    line_number=lineno,
                    source_line=source_line,
                )
            return True

        legacy_param_match = _REGEX["legacy_parameter"].match(line)
        if legacy_param_match:
            for assign in split_csv(legacy_param_match.group("body")):
                if "=" not in assign:
                    continue
                name, value = [x.strip() for x in assign.split("=", 1)]
                declared = self._proc_scope_symbol_is_declared(proc_state, name)
                self._proc_scope_add_local_parameter(
                    proc_state,
                    name,
                    value,
                    filename=filename,
                    line_number=lineno,
                    source_line=source_line,
                    require_declared=proc_state.get("implicit_none", False),
                    register_implicit_if_missing=not declared,
                    legacy=declared,
                )
            return True

        return False

    @staticmethod
    def _looks_like_unknown_proc_declaration(line: str) -> bool:
        """Return whether an unparsed procedure line still looks declarative."""
        m_first = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)", line.strip())
        first_word = m_first.group(1).lower() if m_first else ""
        non_decl_starts = {
            "do",
            "if",
            "where",
            "call",
            "select",
            "case",
            "allocate",
            "deallocate",
            "print",
            "write",
            "read",
            "return",
            "stop",
            "cycle",
            "exit",
            "continue",
            "end",
            "else",
            "elseif",
            "contains",
            "goto",
            "go",
            "data",
            "format",
            "use",
            "save",
            "common",
        }
        if "=" in line and "::" not in line:
            return False
        return (
            bool(re.match(r"^[A-Za-z]", line.strip()))
            and first_word not in non_decl_starts
            and ("::" in line or "," in line or " " in line.strip())
        )

    def _handle_unknown_proc_declaration(
        self,
        line: str,
        proc_state: dict,
        *,
        filename: str | None,
        lineno: int | None,
        source_line: str | None,
    ) -> None:
        """Raise for declaration-looking procedure lines the subset cannot parse.

        The procedure visitor ignores executable statements and harmless
        specification noise, but declaration-shaped unknowns should fail early
        so missing type support is visible instead of silently producing
        unknown arguments.

        Example:
            A line such as ``integer(kind=bad :: n`` reaches this helper after
            `_helper_parse_declaration_line` returns ``False`` and is reported
            as an unsupported datatype declaration for the active procedure.
        """
        if not self._looks_like_unknown_proc_declaration(line):
            self._raise_invalid_fortran_syntax_line(
                line,
                context=f"procedure '{proc_state['signature'].name}' specification part",
                filename=filename,
                lineno=lineno,
                source_line=source_line,
            )
        if _REGEX["unsupported_class_star"].search(line):
            raise FortranParseError(
                f"Unsupported assumed-type CLASS(*) declaration for procedure "
                f"'{proc_state['signature'].name}': {line.strip()}",
                filename=filename,
                line_number=lineno,
                source_line=source_line,
                code="PARSE_UNSUPPORTED_DECLARATION",
            )
        if any(_REGEX[pattern_key].search(line) for pattern_key in _UNSUPPORTED_PATTERN_KEYS):
            return
        raise FortranParseError(
            f"Unknown or unsupported datatype declaration for procedure '{proc_state['signature'].name}': {line.strip()}",
            filename=filename,
            line_number=lineno,
            source_line=source_line,
            code="PARSE_UNSUPPORTED_DECLARATION",
        )

    # ------------------------------------------------------------------
    # Finalization and compile-time resolution
    # ------------------------------------------------------------------

    def _finalize_proc(self, state: dict) -> FortranProcedureSignature:
        """Validate and freeze one procedure signature from mutable scope state."""
        sig = state["signature"]
        symbols = state["symbols"]
        local_params = state.get("local_params", {})
        legacy_local_params = state.get("legacy_local_params", set())
        implicit_typed_symbols = state.get("implicit_typed_symbols", {})
        filename = state.get("filename")
        implicit_none = state.get("implicit_none", False)
        sig.variables = {}
        sig.arguments = [symbols.get(a.name.lower(), a) for a in sig.arguments]
        if sig.result:
            sig.result = symbols.get(sig.result.name.lower(), sig.result)

        FortranParser._validate_no_duplicate_arg_names(
            sig.arguments,
            sig.name,
            filename,
            state.get("header_lineno"),
            state.get("header_source_line"),
        )

        # Safety check: if an argument has been explicitly declared in this
        # procedure, it must not remain unknown after declaration parsing.
        # This catches declaration-application regressions (e.g. legacy
        # star-kind list handling) while still allowing truly undeclared
        # arguments to be handled by semantic conversion or wrapper planning.
        declared_symbols = state.get("typed_symbols", set())
        for arg in sig.arguments:
            if (
                arg.name.lower() in declared_symbols and arg.base_type == "unknown"
            ):  # pragma: no cover - defensive parser invariant.
                raise FortranParseError(
                    f"Failed to resolve declared argument '{arg.name}' in procedure '{sig.name}'.",
                    filename=filename,
                    code="PARSE_UNRESOLVED_ARGUMENT_TYPE",
                )
        local_resolver = _CompileTimeResolver(local_params)
        for arg in sig.arguments:
            if arg.kind:
                arg.kind = self._resolve_kind_expression(arg.kind, local_params, resolver=local_resolver)
            if arg.shape:
                arg.shape = [local_resolver.resolve(dim) for dim in arg.shape]
            if arg.base_type == "unknown" and not implicit_none:
                arg.base_type = self._infer_implicit_base_type(arg.name)
        if sig.result and sig.result.kind:
            sig.result.kind = self._resolve_kind_expression(sig.result.kind, local_params, resolver=local_resolver)
        relevant_params = self._collect_relevant_local_params(sig, local_params)
        declared_local_types = state.get("declared_local_types", {})
        # Defensive reconciliation: some legacy declaration forms can be parsed into
        # `declared_local_types` before being matched back to argument symbols.
        # If an argument is still unknown but we have an exact-name local type
        # record, apply it before implicit-none validation to avoid false positives.
        for arg in sig.arguments:
            if arg.base_type != "unknown":
                continue
            inferred = declared_local_types.get(arg.name.lower())
            if not inferred:
                continue
            arg.base_type = inferred.get("base_type", arg.base_type)
            arg.kind = inferred.get("kind", arg.kind)
            self._apply_internal_type_metadata(arg, inferred)

        if implicit_none and not sig.in_interface:
            self._validate_all_args_declared(sig, filename, explicit_result=bool(state.get("explicit_result", False)))

        for name, value in relevant_params.items():
            if name.lower() in legacy_local_params:
                # Legacy PARAMETER (...) constants are declaration artifacts in
                # fixed-form sources; keep them available for compile-time
                # resolution but do not expose them as parsed procedure variables.
                continue
            local_decl = declared_local_types.get(name.lower(), {})
            var = FortranVariable(
                name=name.lower(),
                base_type=local_decl.get("base_type", implicit_typed_symbols.get(name.lower(), "unknown")),
                kind=local_decl.get("kind"),
                value=self._normalize_parameter_value(value),
                value_type="expression",
                is_parameter=True,
            )
            self._apply_internal_type_metadata(var, local_decl)
            var.symbolic_value = value
            sig.variables[name.lower()] = var
        if sig.kind == "function" and sig.result and sig.result.base_type == "unknown":
            if not implicit_none:
                sig.result.base_type = self._infer_implicit_base_type(sig.result.name)
            if (
                sig.result.base_type == "unknown"
            ):  # pragma: no cover - implicit-none result validation handles public cases first.
                raise FortranParseError(
                    f"Unknown datatype for function result '{sig.result.name}' in procedure '{sig.name}'.",
                    filename=filename,
                    code="PARSE_UNKNOWN_FUNCTION_RESULT_TYPE",
                )
        if sig.kind == "function":
            self._validate_function_result(sig, filename)
        for symbol in sorted(state.get("imports", set())):
            attr = f"import({symbol})"
            if attr not in sig.attributes:
                sig.attributes.append(attr)
        sig.uses = dict(state["uses"])
        sig.common_variables = list(state.get("common_variables", ()))
        finalized = replace(sig)
        finalized._local_uses = dict(state.get("local_uses", {}))
        return finalized

    @staticmethod
    def _record_common_variables(output: list[str], statement: str) -> None:
        """Record common-block object names without modeling native storage."""
        body = re.sub(r"^common\b", "", statement, count=1, flags=re.IGNORECASE).strip()
        body = re.sub(r"/[^/]*/", ",", body)
        known = {name.casefold() for name in output}
        for entity in split_csv(body):
            match = re.match(r"\s*([A-Za-z_]\w*)", entity)
            if match is None:
                continue
            name = match.group(1)
            if name.casefold() not in known:
                output.append(name)
                known.add(name.casefold())

    @staticmethod
    def _validate_all_args_declared(
        sig: FortranProcedureSignature, filename: str | None, *, explicit_result: bool
    ) -> None:
        """Require explicit argument/result types when `implicit none` is active."""
        for arg in sig.arguments:
            if arg.base_type == "unknown":
                raise FortranParseError(
                    f"Argument '{arg.name}' in procedure '{sig.name}' has no type declaration (implicit none is active).",
                    filename=filename,
                    code="PARSE_IMPLICIT_NONE_UNDECLARED_SYMBOL",
                )
        if sig.kind == "function" and sig.result and sig.result.base_type == "unknown":
            if explicit_result:
                raise FortranParseError(
                    f"Unknown datatype for function result '{sig.result.name}' in procedure '{sig.name}'.",
                    filename=filename,
                    code="PARSE_UNKNOWN_FUNCTION_RESULT_TYPE",
                )
            raise FortranParseError(
                f"Function result '{sig.result.name}' in procedure '{sig.name}' has no type declaration (implicit none is active).",
                filename=filename,
                code="PARSE_IMPLICIT_NONE_UNDECLARED_SYMBOL",
            )

    @staticmethod
    def _validate_function_result(sig: FortranProcedureSignature, filename: str | None) -> None:
        """Validate function result existence and argument-name separation."""
        if sig.result is None:  # pragma: no cover - function signatures are constructed with result objects.
            raise FortranParseError(
                f"Function '{sig.name}' has no result variable.",
                filename=filename,
                code="PARSE_MISSING_FUNCTION_RESULT",
            )
        result_name = sig.result.name.lower()
        func_name = sig.name.lower()
        for arg in sig.arguments:
            if arg.name.lower() == result_name and result_name != func_name:
                raise FortranParseError(
                    f"Function result variable '{sig.result.name}' in function '{sig.name}' shadows an argument name.",
                    filename=filename,
                    code="PARSE_RESULT_SHADOWS_ARGUMENT",
                )

    @staticmethod
    def _validate_variable_declarations(
        variables: list[FortranVariable],
        *,
        owner_kind: str,
        owner_name: str | None,
        filename: str | None,
    ) -> None:
        """Reject incompatible duplicate variables in one module-like scope."""
        seen: dict[str, FortranArgument] = {}
        display_name = owner_name or "<unnamed>"
        for var in variables:
            key = var.name.lower()
            if not re.match(
                r"^[a-z_]\w*$", key, re.IGNORECASE
            ):  # pragma: no cover - parser normalizes valid Fortran identifiers.
                continue
            prev = seen.get(key)
            if prev is not None:
                if (
                    prev.base_type != var.base_type
                    or prev.kind != var.kind
                    or prev.rank != var.rank
                    or tuple(prev.shape) != tuple(var.shape)
                ):
                    raise FortranParseError(
                        f"Duplicate variable '{var.name}' in {owner_kind} '{display_name}'.",
                        filename=filename,
                        code="PARSE_DUPLICATE_VARIABLE",
                    )
                continue  # pragma: no cover - exact duplicate declarations are invalid Fortran and tolerated defensively.
            seen[key] = var

    @staticmethod
    def _variable_scope_label(scope) -> tuple[str, str | None]:
        """Return the diagnostic owner label for a module-like scope."""
        if isinstance(scope, FortranSubmodule):
            return "submodule", scope.name
        if isinstance(scope, FortranProgram):
            return "program", scope.name
        if isinstance(scope, FortranBlockData):
            return "block data", scope.name
        return "module", scope.name

    @staticmethod
    def _validate_module_variables(module: FortranModule | FortranSubmodule, filename: str | None) -> None:
        """Validate variables declared by a module or submodule."""
        owner_kind, owner_name = FortranParser._variable_scope_label(module)
        FortranParser._validate_variable_declarations(
            module.variables,
            owner_kind=owner_kind,
            owner_name=owner_name,
            filename=filename,
        )

    @staticmethod
    def _apply_module_visibility(module: FortranModule, filename: str | None) -> None:
        """Apply module default and explicit public/private visibility rules."""
        public_set = {s.lower() for s in module.public_symbols}
        private_set = {s.lower() for s in module.private_symbols}
        for var in module.variables:
            name = var.name.lower()
            if name in private_set:
                var.visibility = "private"
            elif name in public_set:
                var.visibility = "public"
            else:
                var.visibility = module.default_visibility
            if var.base_type == "unknown":  # pragma: no cover - unknown module declarations raise before finalization.
                raise FortranParseError(
                    f"Unknown type for variable '{var.name}' in module '{module.name}'.",
                    filename=filename,
                    code="PARSE_UNKNOWN_VARIABLE_TYPE",
                )
        for enum in module.enums:
            enum.visibility = module.default_visibility
            for enumerator in enum.enumerators:
                name = enumerator.name.lower()
                if name in private_set:
                    enumerator.visibility = "private"
                elif name in public_set:
                    enumerator.visibility = "public"
                else:
                    enumerator.visibility = module.default_visibility

    @staticmethod
    def _validate_derived_type_fields(dtype: FortranDerivedType, filename: str | None) -> None:
        """Reject duplicate or unresolved fields in one derived type."""
        seen: set[str] = set()
        for f in dtype.fields:
            if f.name.lower() in seen:
                raise FortranParseError(
                    f"Duplicate field '{f.name}' in derived type '{dtype.name}'.",
                    filename=filename,
                    code="PARSE_DUPLICATE_FIELD",
                )
            seen.add(f.name.lower())
            if f.base_type == "unknown":  # pragma: no cover - unknown type fields raise before finalization.
                raise FortranParseError(
                    f"Unknown type for field '{f.name}' in derived type '{dtype.name}'.",
                    filename=filename,
                    code="PARSE_UNKNOWN_FIELD_TYPE",
                )

    @staticmethod
    def _validate_no_duplicate_arg_names(
        args: list[FortranArgument],
        proc_name: str,
        filename: str | None,
        line_number: int | None = None,
        source_line: str | None = None,
    ) -> None:
        """Reject duplicate dummy argument names in one procedure header."""
        seen: set[str] = set()
        for arg in args:
            key = arg.name.lower()
            if key in seen:
                raise FortranParseError(
                    f"Duplicate argument name '{arg.name}' in procedure '{proc_name}'.",
                    filename=filename,
                    line_number=line_number,
                    source_line=source_line,
                    code="PARSE_DUPLICATE_ARGUMENT",
                )
            seen.add(key)

    def _collect_module_parameters(self, code: _SourceOrLines, filename: str | None) -> dict[str, dict[str, str]]:
        """Collect module specification-part parameter expressions by module."""
        lines = self._preprocessed_lines(code, filename)
        current_module = None
        in_module_spec_part = False
        output: dict[str, dict[str, str]] = {}
        for line, _lineno, _source_line in lines:
            s = line.strip()
            if not s:
                continue
            lowered = s.lower()
            if lowered.startswith("module ") and not re.match(r"^module\s+(procedure|subroutine|function)\b", lowered):
                current_module = s.split()[1].lower()
                in_module_spec_part = True
                output.setdefault(current_module, {})
                continue
            if lowered.startswith("contains") and current_module is not None:
                in_module_spec_part = False
                continue
            if lowered.startswith("end module"):
                current_module = None
                in_module_spec_part = False
                continue
            if current_module is None or not in_module_spec_part:
                continue
            if lowered == "contains":
                in_module_spec_part = False
                continue
            if not in_module_spec_part:
                continue
            pm = _REGEX["typed_parameter"].match(s)
            if not pm:
                continue
            for assign in split_csv(pm.group("body")):
                if "=" not in assign:
                    continue
                k, v = [x.strip() for x in assign.split("=", 1)]
                output[current_module][k.lower()] = v
        return output

    @staticmethod
    def _resolve_module_parameter_values(module_params: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
        """Resolve transitive parameter expressions inside each module."""
        resolved: dict[str, dict[str, str]] = {}
        for module_name, params in module_params.items():
            resolver = _CompileTimeResolver(params)
            resolved[module_name.lower()] = {
                name.lower(): resolver.resolve(FortranParser._resolve_symbol_reference(value, resolver.symbols))
                for name, value in params.items()
            }
        return resolved

    @staticmethod
    def _resolve_signature_kinds(
        sig: FortranProcedureSignature,
        module_params: dict[str, dict[str, str]],
        *,
        resolve_shapes: bool = True,
    ) -> None:
        """Resolve procedure kind and optional shape expressions from scope facts."""
        module_params = FortranParser._resolve_module_parameter_values(module_params)
        symbol_to_value: dict[str, str] = {}
        if sig.module:
            symbol_to_value.update(module_params.get(sig.module.lower(), {}))
        for mod, mappings in sig.uses.items():
            params = module_params.get(mod.lower(), {})
            if not params:
                continue
            if not mappings:
                symbol_to_value.update(params)
                continue
            for mapping in mappings:
                source = mapping.source.lower()
                local = mapping.local_name.lower()
                if source in params:
                    symbol_to_value[local] = params[source]
        for name, var in sig.variables.items():
            if var.value is not None:
                symbol_to_value.setdefault(name.lower(), var.value)
            elif var.symbolic_value is not None:
                symbol_to_value.setdefault(name.lower(), var.symbolic_value)
        variable_base_types = {name.lower(): var.base_type for name, var in sig.variables.items()}
        variable_symbolic_values = {
            name.lower(): var.symbolic_value or var.value for name, var in sig.variables.items()
        }
        resolved_variables = FortranParser._resolve_variables(
            symbol_to_value, variable_base_types, variable_symbolic_values
        )
        for name in list(sig.variables):
            if name.lower() in resolved_variables:
                sig.variables[name] = resolved_variables[name.lower()]
        resolver = _CompileTimeResolver(symbol_to_value)
        for arg in sig.arguments:
            if arg.kind:
                arg.kind = FortranParser._resolve_kind_expression(arg.kind, symbol_to_value, resolver=resolver)
            if resolve_shapes and arg.shape:
                arg.shape = [resolver.resolve(dim) for dim in arg.shape]
        if sig.result and sig.result.kind:
            sig.result.kind = FortranParser._resolve_kind_expression(
                sig.result.kind, symbol_to_value, resolver=resolver
            )

    @staticmethod
    def _resolve_module_variable_kinds(
        module: FortranModule | FortranSubmodule | FortranProgram | FortranBlockData,
        module_params: dict[str, dict[str, str]],
    ) -> None:
        """Resolve kind, value, and shape facts for module-like variables."""
        module_params = FortranParser._resolve_module_parameter_values(module_params)
        symbol_to_value: dict[str, str] = {}
        if getattr(module, "name", None):
            symbol_to_value.update(module_params.get(module.name.lower(), {}))
        for mod, mappings in getattr(module, "uses", {}).items():
            params = module_params.get(mod.lower(), {})
            if not params:
                continue
            if not mappings:
                symbol_to_value.update(params)
                continue
            for mapping in mappings:
                source = mapping.source.lower()
                local = mapping.local_name.lower()
                if source in params:
                    symbol_to_value[local] = params[source]
        for var in getattr(module, "variables", []):
            source_value = var.value if var.value is not None else var.symbolic_value
            if source_value is not None:
                symbol_to_value.setdefault(var.name.lower(), source_value)
        resolver = _CompileTimeResolver(symbol_to_value)
        for var in getattr(module, "variables", []):
            source_value = var.value if var.value is not None else var.symbolic_value
            if source_value is not None:
                resolved_value = resolver.resolve(source_value, prefer_symbolic=False)
                var.value = FortranParser._normalize_parameter_value(resolved_value)
                symbol_to_value[var.name.lower()] = var.value if var.value is not None else source_value
            if var.kind:
                var.kind = FortranParser._resolve_kind_expression(var.kind, symbol_to_value, resolver=resolver)
            if var.shape:
                var.shape = [resolver.resolve(dim) for dim in var.shape]
                var.lbound, var.ubound = FortranParser._extract_bounds(var.shape)

    @staticmethod
    def _resolve_kind_expression(
        expr: str,
        symbols: dict[str, str],
        *,
        resolver: _CompileTimeResolver | None = None,
    ) -> str:
        """Resolve one kind or character-length expression against symbols."""
        active_resolver = resolver or _CompileTimeResolver(symbols)
        text = expr.strip()
        if text.lower().startswith("len="):
            return f"len={active_resolver.resolve(text.split('=', 1)[1].strip())}"
        resolved = FortranParser._resolve_symbol_reference(expr, symbols)
        return active_resolver.resolve(resolved)

    @staticmethod
    def _resolve_symbol_reference(expr: str, symbols: dict[str, str]) -> str:
        """Follow direct symbol aliases until a stable expression is reached."""
        out = expr.strip()
        seen: set[str] = set()
        while out.lower() in symbols and out.lower() not in seen:
            seen.add(out.lower())
            out = symbols[out.lower()].strip()
        return out

    @staticmethod
    def _collect_relevant_local_params(sig: FortranProcedureSignature, local_params: dict[str, str]) -> dict[str, str]:
        """Keep only local parameters reachable from a wrapper signature."""
        if not local_params:
            return {}
        if not sig.arguments and sig.result is None:
            return dict(local_params)
        pending = set()
        for arg in sig.arguments:
            if arg.kind:
                pending.update(FortranParser._extract_symbol_names(arg.kind))
            for dim in arg.shape:
                pending.update(FortranParser._extract_symbol_names(dim))
        if sig.result and sig.result.kind:
            pending.update(FortranParser._extract_symbol_names(sig.result.kind))
        relevant: dict[str, str] = {}
        while pending:
            sym = pending.pop().lower()
            if sym in relevant or sym not in local_params:
                continue
            value = local_params[sym]
            relevant[sym] = value
            pending.update(FortranParser._extract_symbol_names(value))
        return relevant

    @staticmethod
    def _extract_symbol_names(expr: str) -> set[str]:
        """Extract lowercase identifier tokens from one expression."""
        keywords = {"and", "or", "not"}
        return {
            token.lower()
            for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr or "")
            if not token.isdigit() and token.lower() not in keywords
        }

    @staticmethod
    def _normalize_parameter_value(value: str) -> str | None:
        """Return a stable literal value or `None` for unresolved expressions."""
        parsed_int = FortranParser._safe_eval_int_expr(value)
        if parsed_int is not None:
            return str(parsed_int)
        text = value.strip()
        if re.fullmatch(r"[+-]?\d+(?:\.\d*)?(?:[deDE][+-]?\d+)?", text):
            try:
                as_float = float(text.replace("d", "e").replace("D", "E"))
                if as_float.is_integer():
                    return str(int(as_float))
            except ValueError:
                pass
            return text
        if FortranParser._is_literal_parameter_value(text):
            return text
        return None

    @staticmethod
    def _is_literal_parameter_value(value: str) -> bool:
        """Return whether `value` is a supported serialized literal."""
        text = value.strip()
        if not text:
            return False
        if re.fullmatch(r"[+-]?\d+(?:\.\d*)?(?:[deDE][+-]?\d+)?", text):
            return True
        if re.fullmatch(r"\.(?:true|false)\.", text, re.IGNORECASE):
            return True
        if re.fullmatch(r"(['\"]).*\1", text):
            return True
        if text.startswith("[") and text.endswith("]"):
            return all(FortranParser._is_literal_parameter_value(part) for part in split_csv(text[1:-1]))
        if text.startswith("(/") and text.endswith("/)"):
            return all(FortranParser._is_literal_parameter_value(part) for part in split_csv(text[2:-2]))
        if text.startswith("(") and text.endswith(")"):
            parts = split_csv(text[1:-1])
            return len(parts) == 2 and all(FortranParser._is_literal_parameter_value(part) for part in parts)
        return False

    @staticmethod
    def _resolve_variables(
        symbols: dict[str, str],
        base_types: dict[str, str] | None = None,
        symbolic_values: dict[str, str | None] | None = None,
    ) -> dict[str, FortranVariable]:
        """Build resolved parameter variables from a symbol-expression map."""
        base_types = base_types or {}
        symbolic_values = symbolic_values or {}
        valued: dict[str, FortranVariable] = {}
        resolver = _CompileTimeResolver(symbols)
        for name, value in symbols.items():
            var = FortranVariable(
                name=name,
                base_type=base_types.get(name.lower(), "unknown"),
                value=FortranParser._normalize_parameter_value(resolver.resolve(value, prefer_symbolic=False)),
                value_type="expression",
                is_parameter=True,
            )
            var.symbolic_value = symbolic_values.get(name.lower(), value)
            valued[name] = var
        return valued

    @staticmethod
    def _safe_eval_int_expr(expr: str) -> int | None:
        """Safely evaluate a restricted integer-only Python expression.

        Used to fold simple arithmetic after symbol substitution. Only numeric
        constants and basic arithmetic operators are allowed. Any other syntax
        returns None rather than raising.
        """
        normalized = expr.strip()
        normalized = re.sub(r"(?<=\d)_[A-Za-z_][A-Za-z0-9_]*", "", normalized)
        normalized = re.sub(r"\.and\.", " and ", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\.or\.", " or ", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\.not\.", " not ", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\.true\.", "True", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\.false\.", "False", normalized, flags=re.IGNORECASE)

        try:
            node = ast.parse(normalized, mode="eval")
        except SyntaxError:
            return None

        allowed_binops = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
        allowed_unary = (ast.UAdd, ast.USub)

        def _eval(n):
            """Evaluate one allowed AST node, returning None when unsupported."""
            if isinstance(n, ast.Expression):
                return _eval(n.body)
            if isinstance(n, ast.Constant) and isinstance(n.value, int | float | str | bool):
                return n.value
            if isinstance(n, ast.BinOp) and isinstance(n.op, allowed_binops):
                left = _eval(n.left)
                right = _eval(n.right)
                if (
                    left is None
                    or right is None
                    or not isinstance(left, int | float)
                    or not isinstance(right, int | float)
                ):
                    return None
                if isinstance(n.op, ast.Add):
                    return left + right
                if isinstance(n.op, ast.Sub):
                    return left - right
                if isinstance(n.op, ast.Mult):
                    return left * right
                if isinstance(n.op, ast.Div):
                    return left / right
                if isinstance(n.op, ast.FloorDiv):
                    return left // right
                if isinstance(n.op, ast.Mod):
                    return left % right
                if isinstance(n.op, ast.Pow):
                    return left**right
            if isinstance(n, ast.UnaryOp) and isinstance(n.op, allowed_unary):
                v = _eval(n.operand)
                if v is None or not isinstance(v, int | float):
                    return None
                return +v if isinstance(n.op, ast.UAdd) else -v
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                name = n.func.id.lower()
                args = [_eval(arg) for arg in n.args]
                if any(arg is None for arg in args):
                    return None
                try:
                    if name == "abs" and len(args) == 1 and isinstance(args[0], int | float):
                        return abs(args[0])
                    if name == "max" and args and all(isinstance(arg, int | float) for arg in args):
                        return max(args)
                    if name == "min" and args and all(isinstance(arg, int | float) for arg in args):
                        return min(args)
                    if name == "mod" and len(args) == 2 and all(isinstance(arg, int | float) for arg in args):
                        return args[0] % args[1]
                    if name == "int" and args and isinstance(args[0], int | float):
                        return int(args[0])
                    if name == "len" and len(args) == 1 and isinstance(args[0], str):
                        return len(args[0])
                    if name == "len_trim" and len(args) == 1 and isinstance(args[0], str):
                        return len(args[0].rstrip())
                    if name == "iachar" and len(args) == 1 and isinstance(args[0], str) and args[0]:
                        return ord(args[0][0])
                except (OverflowError, ValueError, ZeroDivisionError):
                    return None
            if isinstance(n, ast.BoolOp):
                values = [_eval(value) for value in n.values]
                if any(value is None for value in values):
                    return None
                if isinstance(n.op, ast.And):
                    return all(bool(value) for value in values)
                if isinstance(n.op, ast.Or):
                    return any(bool(value) for value in values)
            if isinstance(n, ast.Compare):
                left = _eval(n.left)
                if left is None:
                    return None
                for op, comparator in zip(n.ops, n.comparators, strict=False):
                    right = _eval(comparator)
                    if right is None:
                        return None
                    if isinstance(op, ast.Gt):
                        ok = left > right
                    elif isinstance(op, ast.GtE):
                        ok = left >= right
                    elif isinstance(op, ast.Lt):
                        ok = left < right
                    elif isinstance(op, ast.LtE):
                        ok = left <= right
                    elif isinstance(op, ast.Eq):
                        ok = left == right
                    elif isinstance(op, ast.NotEq):
                        ok = left != right
                    else:
                        return None
                    if not ok:
                        return False
                    left = right
                return True
            return None

        val = _eval(node)
        if val is None:
            return None
        if isinstance(val, bool):
            return int(val)
        if isinstance(val, float) and val.is_integer():
            return int(val)
        return val if isinstance(val, int) else None

    # ------------------------------------------------------------------
    # Project diagnostics
    # ------------------------------------------------------------------

    @staticmethod
    def _topological_files(file_deps: dict[str, set[str]]) -> list[str]:
        """Return dependency-first file order while tolerating dependency cycles."""
        in_degree = dict.fromkeys(file_deps, 0)
        for f, deps in file_deps.items():
            for d in deps:
                if d in in_degree:
                    in_degree[f] += 1
        ready = sorted([f for f, deg in in_degree.items() if deg == 0])
        ordered: list[str] = []
        deps_copy = {k: set(v) for k, v in file_deps.items()}
        while ready:
            cur = ready.pop(0)
            ordered.append(cur)
            for f, deps in deps_copy.items():
                if cur in deps:
                    deps.remove(cur)
                    if len(deps) == 0 and f not in ordered and f not in ready:
                        ready.append(f)
                        ready.sort()
        remaining = [f for f in file_deps if f not in ordered]
        ordered.extend(sorted(remaining))
        return ordered

    # ------------------------------------------------------------------
    # General lexical utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _split_intrinsic_type_spec(text: str) -> tuple[str, str, str] | None:
        """Split an intrinsic declaration prefix into base, parenthesized spec, and tail."""
        match = re.match(
            r"^(integer|real|complex|logical|character|double\s+(?:precision|complex))\b(?P<rest>.*)$",
            text.strip(),
            re.IGNORECASE,
        )
        if not match:
            return None
        base = match.group(1).lower()
        rest = (match.group("rest") or "").lstrip()
        if not rest.startswith("("):
            return base, "", rest.strip()

        depth = 0
        quote: str | None = None
        for index, char in enumerate(rest):
            if quote:
                if char == quote:
                    quote = None
                continue
            if char in {"'", '"'}:
                quote = char
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return base, rest[: index + 1], rest[index + 1 :].strip()
        return base, rest, ""

    @staticmethod
    def _expect_single_parse_result(
        items: list,
        *,
        parser_name: str,
        entity_name: str,
        filename: str | None,
    ):
        """Return one parsed entity or raise when a singular parser contract is broken."""
        if len(items) == 1:
            return items[0]
        if not items:
            raise FortranParseError(
                f"{parser_name}() expected exactly one {entity_name}, but none were found",
                filename=filename,
                code="PARSE_WRONG_ENTRYPOINT",
            )
        raise FortranParseError(
            f"{parser_name}() expected exactly one {entity_name}, but found {len(items)}",
            filename=filename,
            code="PARSE_AMBIGUOUS_ENTRYPOINT",
        )

    @staticmethod
    def _source_form(filename: str | None) -> str:
        """Infer fixed, modern, or unknown source form from a filename suffix."""
        if not filename:
            return "unknown"
        ext = Path(filename).suffix.lower()
        if ext in {".f", ".for", ".ftn", ".f77"}:
            return "f77"
        if ext in {".f90", ".f95", ".f03", ".f08"}:
            return "modern"
        return "unknown"

    @staticmethod
    def _infer_implicit_base_type(symbol_name: str) -> str:
        """Apply the default Fortran I-N integer implicit typing rule."""
        first = symbol_name.strip()[:1].lower()
        if "i" <= first <= "n":
            return "integer"
        return "real"

    @staticmethod
    def _find_legacy_star_kind(type_left: str) -> tuple[str, str] | None:
        """Return base type and width from a legacy `type*kind` prefix."""
        m = re.match(r"^(integer|real|complex|logical|character)\s*\*\s*([0-9]+)\b", type_left, re.IGNORECASE)
        if not m:
            return None
        return m.group(1).lower(), m.group(2)

    @staticmethod
    def _parse_type_prefix(prefix: str) -> tuple[str, str | None] | None:
        """Parse a standalone intrinsic, derived, or class type prefix."""
        txt = prefix.strip()
        if not txt:
            return None
        star_kind = FortranParser._find_legacy_star_kind(txt)
        if star_kind:
            base, kind = star_kind
            return base, kind
        cm = _REGEX["char_star"].match(txt)
        if cm:
            raw_len = cm.group("len").strip()
            char_kind = raw_len[1:-1].strip() if raw_len.startswith("(") and raw_len.endswith(")") else raw_len
            return "character", char_kind
        intrinsic = FortranParser._split_intrinsic_type_spec(txt)
        if intrinsic:
            base, type_spec, tail = intrinsic
            if tail:
                return None
            if base == "double precision":
                base = "real"
            elif base == "double complex":
                base = "complex"
            kind = extract_kind_from_type_spec(base, type_spec)
            if kind is None and type_spec and base != "character":
                kind = type_spec[1:-1].strip()
            return base, kind or ""
        derived = _REGEX["type_field"].match(txt)
        if derived:
            return "derived", derived.group("dtype")
        class_derived = _REGEX["class_field"].match(txt)
        if class_derived:
            return "derived", class_derived.group("dtype")
        return None  # pragma: no cover - unsupported prefixes are rejected by public grammar.

    @staticmethod
    def _looks_like_existing_source_path(source: str | Path) -> bool:
        """Return True when ``source`` names a readable source file path."""
        if not isinstance(source, str | Path):
            return False
        text = str(source)
        if "\n" in text or "\r" in text:
            return False
        return Path(text).is_file()

    @staticmethod
    def _split_submodule_parent(parent_spec: str) -> tuple[str, str | None]:
        """Split `ancestor:parent` or plain `parent` submodule syntax."""
        parts = [p.strip() for p in parent_spec.split(":", 1)]
        if len(parts) == 2:
            ancestor, parent = parts
            return parent, ancestor
        return parts[0], None

    @staticmethod
    def _attrs(prefix: str, tail: str) -> list[str]:
        """Collect supported procedure header attributes."""
        attrs = [t.lower() for t in prefix.split() if t.lower() in _ATTR_PREFIX_WORDS]
        if _REGEX["bind_c"].search(tail):
            attrs.append("bind(c)")
        return attrs

    @staticmethod
    def _bind_c_name(tail: str) -> str | None:
        """Return the explicit external name from a procedure ``bind(C)`` suffix."""
        match = _REGEX["bind_c"].search(tail)
        if match is None:
            return None
        name = match.groupdict().get("name")
        return name if name else None

    @staticmethod
    def _looks_like_procedure_header(line: str) -> bool:
        """Return whether a line resembles a subroutine or function header."""
        stripped = line.strip()
        if not stripped:
            return False
        lowered = stripped.lower()
        if lowered.startswith(("end ", "call ")):
            return False
        without_strings = re.sub(r"'[^']*'|\"[^\"]*\"", "", stripped)
        return bool(re.search(r"(?:^|[\s,])(?:subroutine|function)\s+[A-Za-z_]\w*", without_strings, re.IGNORECASE))

    @staticmethod
    def _is_openmp_directive(line: str) -> bool:
        """Return whether a line begins an OpenMP sentinel directive."""
        return line.lstrip().lower().startswith("!$omp")

    @staticmethod
    def _is_openmp_declarative_directive(line: str) -> bool:
        """Return whether an OpenMP directive belongs in a specification part."""
        directive = line.lstrip()[5:].strip().lower() if FortranParser._is_openmp_directive(line) else ""
        return directive.startswith(
            (
                "threadprivate",
                "declare simd",
                "declare target",
                "declare reduction",
                "requires",
                "declare mapper",
            )
        )

    @staticmethod
    def _looks_like_declaration_or_spec(line: str) -> bool:
        """Return whether a line resembles a specification-part statement."""
        stripped = line.strip()
        if not stripped:
            return False
        lowered = stripped.lower()
        if FortranParser._is_openmp_directive(stripped):
            return FortranParser._is_openmp_declarative_directive(stripped)
        first_match = re.match(r"([a-z_][a-z0-9_]*)", lowered)
        first = first_match.group(1) if first_match else lowered.split(None, 1)[0].rstrip(",")
        non_decl_starts = {
            "do",
            "if",
            "where",
            "call",
            "select",
            "case",
            "allocate",
            "deallocate",
            "print",
            "write",
            "read",
            "return",
            "stop",
            "cycle",
            "exit",
            "continue",
            "end",
            "else",
            "elseif",
            "contains",
            "goto",
            "go",
            "format",
        }
        if first in non_decl_starts:
            return False
        if "::" in stripped or "," in stripped:
            return True
        return bool(re.match(r"^[A-Za-z_]\w+\s+[A-Za-z_]\w*", stripped))

    @staticmethod
    def _is_statement_function_statement(line: str) -> bool:
        """Return whether a line has legacy statement-function syntax."""
        stripped = line.strip()
        return bool(
            re.match(
                r"^[A-Za-z_]\w*\s*\([^()]*\)\s*=",
                stripped,
                flags=re.IGNORECASE,
            )
        )

    @staticmethod
    def _is_ignored_spec_statement(line: str) -> bool:
        """Return whether a recognized specification statement needs no model."""
        return bool(
            _REGEX["include"].match(line)
            or re.match(
                r"^(implicit|save|common|data|equivalence|external|intrinsic|parameter|namelist|entry)\b",
                line,
                flags=re.IGNORECASE,
            )
        )

    @staticmethod
    def _parse_use_statement(line: str) -> tuple[str, list[FortranUseMapping]] | None:
        """Parse a `use` statement into its module and explicit symbol mappings.

        Example:
            >>> FortranParser._parse_use_statement("use kinds, only: local => remote")
            ('kinds', [FortranUseMapping(source='remote', target='local')])
        """
        match = _REGEX["use"].match(line)
        if not match:
            return None
        rest = (match.group("rest") or "").strip()
        if not rest:
            return match.group("module"), []
        payload = rest.lstrip(",").strip()
        only_match = re.match(r"^only\s*:\s*(?P<symbols>.*)$", payload, re.IGNORECASE)
        if only_match:
            payload = only_match.group("symbols")
        mappings: list[FortranUseMapping] = []
        for item in split_csv(payload):
            token = item.strip()
            if not token:
                continue
            if "=>" in token:
                target, source = [part.strip() for part in token.split("=>", 1)]
            else:
                source = token
                target = None
            mappings.append(FortranUseMapping(source=source, target=target))
        return match.group("module"), mappings

    @staticmethod
    def _is_executable_statement_start(line: str) -> bool:
        """Return whether a line starts execution rather than specification."""
        stripped = line.strip()
        if not stripped:  # pragma: no cover - callers skip blank lines before executable checks.
            return False
        labeled = re.match(r"^\d+\s+(?P<body>.*)$", stripped)
        if labeled:
            stripped = labeled.group("body").strip()
            if not stripped:
                return False
        lowered = stripped.lower()
        if FortranParser._is_openmp_directive(stripped):
            return not FortranParser._is_openmp_declarative_directive(stripped)
        if FortranParser._parse_use_statement(stripped) is not None or FortranParser._is_ignored_spec_statement(
            stripped
        ):
            return False
        first_match = re.match(r"([a-z_][a-z0-9_]*)", lowered)
        first = first_match.group(1) if first_match else lowered.split(None, 1)[0]
        if first.isdigit():
            return False
        executable_starts = {
            "do",
            "if",
            "where",
            "call",
            "select",
            "case",
            "allocate",
            "deallocate",
            "print",
            "write",
            "read",
            "return",
            "stop",
            "cycle",
            "exit",
            "continue",
            "goto",
            "go",
            "open",
            "close",
            "rewind",
            "backspace",
            "inquire",
            "flush",
            "wait",
            "nullify",
            "associate",
            "block",
            "forall",
            "error",
            "pause",
        }
        if first in executable_starts:
            return True
        if _REGEX["legacy_parameter"].match(stripped):
            return False
        if FortranParser._is_statement_function_statement(stripped):
            return False
        if "=" in stripped and "::" not in stripped:
            # Distinguish assignment/statements from declaration lines carrying
            # type specs with named arguments, e.g.:
            #   integer ( kind = 4 ) i
            #   character ( len = * ) s
            # Covers assignment and statement functions in execution part.
            return not (
                _REGEX["char_star"].match(stripped)
                or _REGEX["type"].match(stripped)
                or _REGEX["type_field"].match(stripped)
                or _REGEX["class_field"].match(stripped)
            )
        return False


# -----------------------------------------------------------------------------
# Module-level convenience wrappers
# -----------------------------------------------------------------------------

_DEFAULT_PARSER = FortranParser()

# Module-level parser entrypoints are intentionally limited.


def parse_fortran_file(
    source_or_path: str | Path,
    filename: str | None = None,
    encoding: str = "utf-8",
) -> FortranFile:
    """Parse one source string or path using the shared ``FortranParser``.

    This is the normal public API for parser clients.  Pass inline source with
    an optional ``filename`` for diagnostics, or pass an existing path without
    ``filename`` to read it using ``encoding``.  The returned ``FortranFile``
    is parser-stage data that is normally passed to project aggregation or
    semantic conversion; malformed or unsupported source raises
    :class:`FortranParseError`.

    Example:
        >>> parse_fortran_file("subroutine ping()\\nend subroutine ping\\n").procedures[0].name
        'ping'
    """
    return _DEFAULT_PARSER.parse_file(
        source_or_path,
        filename=filename,
        encoding=encoding,
    )


def parse_fortran_project(files, *, encoding: str = "utf-8") -> FortranProject:
    """Parse explicit Fortran sources or a directory into one project model.

    Use this module-level convenience API for cross-file parsing.  ``files``
    may be a mapping of names to source, explicit paths, or a directory; the
    returned project indexes the parsed files and completed project symbols.
    File and duplicate-symbol errors propagate as :class:`FortranParseError`.

    Example:
        >>> project = parse_fortran_project({"types.f90": "module types\\nend module types\\n"})
        >>> sorted(project.modules)
        ['types']
    """
    return _DEFAULT_PARSER.parse_project(files, encoding=encoding)


if __name__ == "__main__":
    source = """\
module metrics
  integer, parameter :: n = 4
contains
  subroutine scale(values)
    real, intent(inout) :: values(n)
  end subroutine scale
end module metrics
"""

    parsed = parse_fortran_file(source, filename="metrics.f90")
    module = parsed.modules[0]
    procedure = module.procedures[0]
    argument = procedure.arguments[0]

    print(f"Module: {module.name}")
    print(f"Parameter: {module.variables[0].name} = {module.variables[0].value}")
    print(f"Procedure: {procedure.name}({argument.name}: {argument.base_type}[{argument.rank}])")
