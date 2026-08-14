"""Prepare C and Fortran source for the parser frontends.

The parsers intentionally consume one expanded source stream. This module
therefore owns compiler/preprocessor invocation plus shared provenance and
dependency metadata. The Fortran-specific textual ``INCLUDE`` pass lives in
``prik.preprocessing.fortran`` and is coordinated here. Neither module parses
declarations or makes semantic policy decisions; callers pass
:class:`PreprocessResult.source` to the appropriate parser after this stage
completes.

The public route is :func:`preprocess_source`. ``PreprocessingConfig`` selects
a direct compiler, compile database, or command template; ``PreprocessResult``
returns the prepared stream with its recipe, mappings, dependencies, macros,
and diagnostics. ``PreprocessingPlan`` and ``Invocation`` describe a request
before execution. Read the module in its phase order: configuration and
validation, adapter facades, command construction, provenance recovery, then
execution and result assembly.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Literal, Protocol

from prik.compiler.compiler_profiles import fortran_compiler_family


PreprocessingCategory = Literal[
    "PREPROCESSOR_NOT_FOUND",
    "PREPROCESSOR_FAILED",
    "INVALID_COMPILER_ARGUMENTS",
    "UNSUPPORTED_COMPILER_CAPABILITY",
    "PROVENANCE_UNAVAILABLE",
    "INCLUDE_NOT_FOUND",
    "INCLUDE_CYCLE",
]

IncludeMechanism = Literal["c_include", "cpp_include", "fortran_include"]
DependencyKind = Literal["root", "project", "system"]
Exposure = Literal["public", "private"]


# Compiler output syntax and supported source forms.
_VALID_LANGUAGES = {"c", "fortran"}
_C_SOURCE_SUFFIXES = {".c", ".h", ".i"}
_FORTRAN_SOURCE_SUFFIXES = {".f", ".for", ".ftn", ".f77", ".f90", ".f95", ".f03", ".f08"}
_DEFINE_RE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)(\(([^)]*)\))?(?:\s+(.*))?$")
_LINEMARKER_RE = re.compile(
    r'^\s*#\s+(?P<line>\d+)\s+(?:"(?P<quoted>(?:[^"\\]|\\.)*)"|(?P<bare>\S+))(?P<flags>(?:\s+\d+)*)\s*$'
)
_LINE_DIRECTIVE_RE = re.compile(
    r'^\s*#\s*line\s+(?P<line>\d+)(?:\s+(?:"(?P<quoted>(?:[^"\\]|\\.)*)"|(?P<bare>\S+)))?\s*$'
)


class PreprocessingError(Exception):
    """Report a preprocessing configuration, compiler, or include failure.

    Callers normally surface ``category`` and ``diagnostics`` through the CLI
    or parser payload.  The exception message remains the concise
    user-facing summary.
    """

    def __init__(
        self,
        message: str,
        *,
        category: PreprocessingCategory = "PREPROCESSOR_FAILED",
        diagnostics: Sequence[PreprocessingDiagnostic] | None = None,
    ) -> None:
        """Initialize a failure with its stable category and diagnostic details.

        Args:
            message: Concise explanation presented to callers.
            category: Stable machine-readable failure classification.
            diagnostics: Optional detailed diagnostics to retain with the error.
        """
        self.category = category
        self.diagnostics = list(diagnostics or [])
        super().__init__(message)


@dataclass
class Invocation:
    """Describe one concrete compiler command used to expand source.

    Invocation builders return this record when a caller needs to inspect the
    exact argv and working directory before execution.  ``preprocess_source``
    consumes it internally and records the same facts in its result recipe.
    """

    argv: list[str]
    cwd: str | None = None
    adapter: str = "direct"
    language: str | None = None
    compiler: str | None = None
    compile_commands: str | None = None
    compile_commands_entry: dict[str, object] | None = None
    capabilities: dict[str, bool] = field(default_factory=dict)


@dataclass
class PreprocessingDiagnostic:
    """Store one preprocessing diagnostic with optional source provenance.

    Results and errors retain these records so CLI and API callers can report
    stable categories without reparsing compiler stderr.
    """

    category: PreprocessingCategory
    message: str
    severity: Literal["error", "warning", "note"] = "error"
    path: str | None = None
    line: int | None = None
    command: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Return a detached JSON-compatible representation of this diagnostic."""
        return {
            "category": self.category,
            "message": self.message,
            "severity": self.severity,
            "path": self.path,
            "line": self.line,
            "command": list(self.command),
        }


@dataclass
class PreprocessingPlan:
    """Represent the requested preprocessing inputs before command selection.

    This JSON-compatible value is useful to callers that need to display or
    persist a requested operation rather than execute it immediately.
    """

    language: str
    source_path: str
    adapter: str
    compiler: str | None = None
    cwd: str | None = None
    include_dirs: list[str] = field(default_factory=list)
    defines: list[str] = field(default_factory=list)
    undefs: list[str] = field(default_factory=list)
    standard: str | None = None
    compiler_args: list[str] = field(default_factory=list)
    compile_commands: str | None = None
    command_template: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a detached JSON-compatible representation of the requested plan."""
        return {
            "language": self.language,
            "source_path": self.source_path,
            "adapter": self.adapter,
            "compiler": self.compiler,
            "cwd": self.cwd,
            "include_dirs": list(self.include_dirs),
            "defines": list(self.defines),
            "undefs": list(self.undefs),
            "standard": self.standard,
            "compiler_args": list(self.compiler_args),
            "compile_commands": self.compile_commands,
            "command_template": self.command_template,
        }


@dataclass
class IncludedFile:
    """Describe one root or include edge discovered during preprocessing.

    ``mechanism`` identifies whether compiler markers or native Fortran
    expansion found the edge.  Downstream parsers consume these records as
    dependency and public-exposure facts.
    """

    path: str
    included_by: str | None = None
    include_line: int | None = None
    mechanism: IncludeMechanism = "cpp_include"
    dependency_kind: DependencyKind = "project"
    exposure: Exposure = "public"

    def to_dict(self) -> dict[str, object]:
        """Return a detached JSON-compatible representation of this include edge."""
        return {
            "path": self.path,
            "included_by": self.included_by,
            "include_line": self.include_line,
            "mechanism": self.mechanism,
            "dependency_kind": self.dependency_kind,
            "exposure": self.exposure,
        }


@dataclass
class SourceMapping:
    """Map one generated source line back to its original source location.

    ``include_stack`` preserves the active inclusion chain for provenance-aware
    parsers and diagnostics.
    """

    generated_line: int
    original_path: str
    original_line: int
    include_stack: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Return a detached JSON-compatible representation of this mapping."""
        return {
            "generated_line": self.generated_line,
            "original_path": self.original_path,
            "original_line": self.original_line,
            "include_stack": list(self.include_stack),
        }


@dataclass
class MacroDefinition:
    """Record an active macro when compiler output exposes its definition.

    Macro metadata is descriptive rather than executable: semantic conversion
    may consume supported object-like values, while callers retain function-like
    definitions as provenance only.
    """

    name: str
    value: str | None = None
    function_like: bool = False
    parameters: list[str] | None = None
    path: str | None = None
    line: int | None = None
    builtin: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return a detached JSON-compatible representation of this macro."""
        return {
            "name": self.name,
            "value": self.value,
            "function_like": self.function_like,
            "parameters": list(self.parameters) if self.parameters is not None else None,
            "path": self.path,
            "line": self.line,
            "builtin": self.builtin,
        }


@dataclass
class PreprocessResult:
    """Return expanded source together with all preprocessing side-channel data.

    Pass ``source`` to a C or Fortran parser.  ``recipe`` and the metadata
    collections are normally attached to the parser or build report so later
    stages can preserve compiler provenance.
    """

    source: str
    recipe: dict[str, object]
    included_files: list[IncludedFile] = field(default_factory=list)
    source_mappings: list[SourceMapping] = field(default_factory=list)
    macros: list[MacroDefinition] = field(default_factory=list)
    diagnostics: list[PreprocessingDiagnostic] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Return a detached JSON-compatible representation of this result."""
        return {
            "source": self.source,
            "recipe": dict(self.recipe),
            "included_files": [item.to_dict() for item in self.included_files],
            "source_mappings": [item.to_dict() for item in self.source_mappings],
            "macros": [item.to_dict() for item in self.macros],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


@dataclass
class PreprocessingRecipe:
    """Store JSON-compatible provenance for one completed preprocessing operation.

    Use this record when a caller wants expanded source and a typed recipe from
    :func:`run_compiler_preprocessor_with_recipe`.  ``to_dict`` is the payload
    shape stored alongside parser results.
    """

    language: str
    compiler: str | None
    mode: str = "compiler"
    adapter: str = "direct"
    argv: list[str] = field(default_factory=list)
    cwd: str | None = None
    include_dirs: list[str] = field(default_factory=list)
    defines: list[str] = field(default_factory=list)
    undefs: list[str] = field(default_factory=list)
    standard: str | None = None
    compiler_args: list[str] = field(default_factory=list)
    source_path: str | None = None
    compile_commands: str | None = None
    compile_commands_entry: dict[str, object] | None = None
    command_template: str | None = None
    included_files: list[dict[str, object]] = field(default_factory=list)
    source_mappings: list[dict[str, object]] = field(default_factory=list)
    macros: list[dict[str, object]] = field(default_factory=list)
    diagnostics: list[dict[str, object]] = field(default_factory=list)
    capabilities: dict[str, bool] = field(default_factory=dict)

    @property
    def std(self) -> str | None:
        """Return the configured language standard under its historical name."""
        return self.standard

    def to_dict(self) -> dict[str, object]:
        """Return a detached JSON-compatible representation of this recipe."""
        return {
            "language": self.language,
            "compiler": self.compiler,
            "mode": self.mode,
            "adapter": self.adapter,
            "argv": list(self.argv),
            "cwd": self.cwd,
            "include_dirs": list(self.include_dirs),
            "defines": list(self.defines),
            "undefs": list(self.undefs),
            "standard": self.standard,
            "std": self.standard,
            "compiler_args": list(self.compiler_args),
            "source_path": self.source_path,
            "source_file": self.source_path,
            "compile_commands": self.compile_commands,
            "compile_commands_entry": self.compile_commands_entry,
            "command_template": self.command_template,
            "included_files": list(self.included_files),
            "source_mappings": list(self.source_mappings),
            "macros": list(self.macros),
            "diagnostics": list(self.diagnostics),
            "capabilities": dict(self.capabilities),
        }


@dataclass
class PreprocessingConfig:
    """Configure compiler-backed source expansion and dependency exposure.

    Use ``mode="compiler"`` with ``preprocess_source`` or either convenience
    runner.  Select a direct compiler, compile database, or command template;
    include paths and macro options apply to the selected invocation and to
    native Fortran ``INCLUDE`` expansion.
    """

    mode: str = "internal"
    compiler: str | None = None
    compile_commands: str | None = None
    adapter: str = "auto"
    command_template: str | None = None
    include_dirs: list[str] = field(default_factory=list)
    defines: list[str] = field(default_factory=list)
    undefs: list[str] = field(default_factory=list)
    std: str | None = None
    compiler_args: list[str] = field(default_factory=list)
    include_exposure: Literal["reachable-project", "roots-only"] = "reachable-project"
    public_includes: list[str] = field(default_factory=list)
    private_includes: list[str] = field(default_factory=list)
    collect_macro_metadata: bool = False

    @property
    def uses_compiler(self) -> bool:
        """Whether this configuration authorizes compiler-backed preprocessing."""
        return self.mode == "compiler"

    def fortran_internal_recipe(self, path: Path) -> dict[str, object] | None:
        """Return parser-test macro metadata when compiler invocation is absent.

        ``None`` means no internal recipe is needed.  The method does not read
        ``path`` or execute a compiler; it only records the macros supplied to
        the internal Fortran parser-test path.
        """
        if self.uses_compiler or not (self.defines or self.undefs):
            return None
        return PreprocessingRecipe(
            language="fortran",
            compiler=None,
            mode="internal",
            adapter="parser-test",
            argv=[],
            defines=list(self.defines),
            undefs=list(self.undefs),
            source_path=str(path),
        ).to_dict()


class CompilerAdapter(Protocol):
    """Describe the adapter façade used by callers with custom compiler families.

    Implementations build an invocation and expose metadata already present in
    a :class:`PreprocessResult`; they do not run the compiler themselves.
    """

    name: str
    capabilities: dict[str, bool]

    def build_preprocess_invocation(
        self,
        source_path: Path,
        *,
        language: str,
        config: PreprocessingConfig,
    ) -> Invocation:
        """Build the adapter-specific command for ``source_path`` and ``language``."""
        ...

    def collect_dependencies(self, result: PreprocessResult) -> list[IncludedFile]:
        """Return the dependency records already collected in ``result``."""
        ...

    def collect_macros(self, result: PreprocessResult) -> list[MacroDefinition]:
        """Return the macro records already collected in ``result``."""
        ...

    def parse_linemarkers(self, source: str, filename: str | None = None) -> list[SourceMapping]:
        """Map non-marker lines in compiler output back to their source locations."""
        ...


# Configuration validation and command option normalization.


def validate_macro_name(macro_str: str, context: str) -> None:
    """Validate one ``-D`` or ``-U`` style macro argument before invocation.

    Use this at a configuration boundary when accepting macro text from a user.
    The macro value, if any, is left untouched; only the identifier before the
    first ``=`` is validated.

    Raises:
        PreprocessingError: If the macro text has no valid identifier.
    """

    if not macro_str:
        raise PreprocessingError(
            f"{context} requires a macro name",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    name = macro_str.split("=", 1)[0]
    if not name:
        raise PreprocessingError(
            f"{context} requires a macro name before '='",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        raise PreprocessingError(
            f"{context}: invalid macro name '{name}'; must be a valid identifier",
            category="INVALID_COMPILER_ARGUMENTS",
        )


def _require_language(language: str) -> None:
    """Reject languages without a compiler-preprocessing adapter.

    The helper consumes the user-facing language selector and raises the stable
    invalid-argument error before any command or filesystem work occurs.
    """
    if language not in _VALID_LANGUAGES:
        raise PreprocessingError(
            f"compiler preprocessing is not supported for language {language!r}",
            category="INVALID_COMPILER_ARGUMENTS",
        )


def _compiler_required(config: PreprocessingConfig, language: str) -> str:
    """Return the explicit compiler required by a direct invocation.

    Direct mode intentionally requires an exact configured executable, while
    compile-database and command-template modes obtain their command elsewhere.
    """
    if not config.compiler:
        raise PreprocessingError(
            f"{language} compiler preprocessing requires --compiler with an exact executable",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    return config.compiler


def _fortran_preprocessor_profile(compiler: str) -> tuple[str, tuple[str, ...], dict[str, bool]]:
    """Return the Fortran adapter name, extra flags, and provenance capabilities.

    Unknown compilers retain the GNU-compatible profile.  LLVM Flang suppresses
    line markers, so its capability record explicitly reports that limitation.
    """
    try:
        token, _vendor, _c_compiler = fortran_compiler_family(compiler)
    except ValueError:
        token = ""
    if token == "flang":
        return (
            "llvm-flang",
            ("-P",),
            {"dependency_output": False, "macro_dump": False, "linemarkers": False},
        )
    return (
        "gnu-fortran",
        (),
        {"dependency_output": True, "macro_dump": True, "linemarkers": True},
    )


def _invocation_adapter_profile(language: str, compiler: str) -> tuple[str, dict[str, bool]]:
    """Return the selected adapter label and a fresh capability mapping.

    Both direct and compile-database invocation builders use this shared
    profile so their recorded adapter facts stay identical for the same
    language/compiler pair.
    """
    if language == "fortran":
        adapter, _vendor_args, capabilities = _fortran_preprocessor_profile(compiler)
        return adapter, capabilities
    return "gcc-compatible-c", {"dependency_output": True, "macro_dump": True, "linemarkers": True}


def _preprocessor_options(
    config: PreprocessingConfig,
    *,
    language: str,
    include_language_flag: bool,
    compiler: str,
) -> list[str]:
    """Build common compiler flags in their established invocation order.

    The returned flags begin with compiler preprocessing mode, followed by the
    language mode, include directories, macro controls, standard, and raw
    compiler arguments.  The caller decides where source and compile-database
    arguments are placed around this sequence.
    """
    args: list[str] = ["-E"]
    if include_language_flag and language == "c":
        args.extend(["-x", "c"])
    if language == "fortran":
        args.append("-cpp")
        _adapter, vendor_args, _capabilities = _fortran_preprocessor_profile(compiler)
        args.extend(vendor_args)
    for include_dir in config.include_dirs:
        args.append(f"-I{include_dir}")
    for define in config.defines:
        args.append(f"-D{define}")
    for undef in config.undefs:
        args.append(f"-U{undef}")
    if config.std:
        args.append(f"-std={config.std}")
    args.extend(config.compiler_args)
    return args


def _fortran_source_language_hint(source: Path) -> list[str]:
    """Return a source-form hint only for Fortran paths with unknown suffixes."""
    if source.suffix.lower() in _FORTRAN_SOURCE_SUFFIXES:
        return []
    return ["-x", "f95-cpp-input"]


# Adapter facades for callers that need the protocol rather than direct execution.


class GCCCompatibleCAdapter:
    """Provide the GCC/Clang-compatible C adapter contract.

    Use this façade when a caller needs direct-command construction and
    metadata access through the :class:`CompilerAdapter` protocol.  Execution
    remains owned by :func:`preprocess_source`.
    """

    name = "gcc-compatible-c"
    capabilities: ClassVar[dict[str, bool]] = {"dependency_output": True, "macro_dump": True, "linemarkers": True}

    def build_preprocess_invocation(
        self,
        source_path: Path,
        *,
        language: str,
        config: PreprocessingConfig,
    ) -> Invocation:
        """Build this adapter's direct compiler command for one C source path."""
        return build_direct_preprocess_invocation(source_path, language=language, config=config)

    def collect_dependencies(self, result: PreprocessResult) -> list[IncludedFile]:
        """Return a shallow copy of the include records stored in ``result``."""
        return list(result.included_files)

    def collect_macros(self, result: PreprocessResult) -> list[MacroDefinition]:
        """Return a shallow copy of the macro records stored in ``result``."""
        return list(result.macros)

    def parse_linemarkers(self, source: str, filename: str | None = None) -> list[SourceMapping]:
        """Return source mappings parsed from this adapter's compiler output."""
        return parse_linemarker_mappings(source, filename=filename)


class GNUFortranAdapter(GCCCompatibleCAdapter):
    """Expose GNU-compatible Fortran preprocessing through the shared façade."""

    name = "gnu-fortran"


class CommandTemplateAdapter(GCCCompatibleCAdapter):
    """Build custom-template commands while retaining shared metadata helpers."""

    name = "command-template"
    capabilities: ClassVar[dict[str, bool]] = {"dependency_output": False, "macro_dump": False, "linemarkers": False}

    def build_preprocess_invocation(
        self,
        source_path: Path,
        *,
        language: str,
        config: PreprocessingConfig,
    ) -> Invocation:
        """Expand this configuration's custom template for the selected source."""
        return build_template_preprocess_invocation(source_path, language=language, config=config)


# Compiler command construction.


def build_direct_preprocess_invocation(
    source_path: Path | str,
    *,
    language: str,
    config: PreprocessingConfig,
) -> Invocation:
    """Build the exact direct compiler command used to expand one source file.

    Use this for inspection or tests when the caller has an explicit compiler.
    It validates the language and compiler setting but neither reads the source
    nor executes the returned command.

    Raises:
        PreprocessingError: If the language is unsupported or no compiler was configured.
    """

    _require_language(language)
    compiler = _compiler_required(config, language)
    source = Path(source_path)
    argv = [
        compiler,
        *_preprocessor_options(
            config,
            language=language,
            include_language_flag=language == "c",
            compiler=compiler,
        ),
        *(_fortran_source_language_hint(source) if language == "fortran" else []),
        str(source),
    ]
    adapter, capabilities = _invocation_adapter_profile(language, compiler)
    return Invocation(
        argv=argv,
        cwd=None,
        adapter=adapter,
        language=language,
        compiler=compiler,
        capabilities=capabilities,
    )


def _load_compile_commands(path: str | os.PathLike[str] | None) -> list[dict[str, object]]:
    """Load and validate the top-level list in a compile-commands database.

    The helper reads UTF-8 JSON only and intentionally preserves each entry's
    raw fields for recipe provenance.  Entry-level validation happens when the
    selected source is resolved.
    """
    if not path:
        raise PreprocessingError(
            "compile_commands database path is missing",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    database_path = Path(path)
    try:
        raw = database_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PreprocessingError(
            f"cannot read compile commands file {database_path}: {exc}",
            category="INVALID_COMPILER_ARGUMENTS",
        ) from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PreprocessingError(
            f"invalid compile commands JSON: {exc}",
            category="INVALID_COMPILER_ARGUMENTS",
        ) from exc
    if not isinstance(payload, list):
        raise PreprocessingError(
            "compile_commands.json must contain a list",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    return payload


def _entry_file_path(entry: dict[str, object]) -> Path:
    """Resolve one compile-database entry's source path against its directory.

    The returned path may remain relative when the entry omits ``directory``;
    that preserves compile-database working-directory semantics for later
    source matching.
    """
    if "file" not in entry:
        raise PreprocessingError(
            "compile_commands entry is missing 'file'",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    directory = Path(str(entry.get("directory") or "."))
    file_path = Path(str(entry["file"]))
    if not file_path.is_absolute():
        file_path = directory / file_path
    return file_path


def _same_source(left: Path, right: Path) -> bool:
    """Compare source paths while tolerating filesystem resolution failures."""
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left.absolute() == right.absolute()


def _compile_command_argv(entry: dict[str, object]) -> list[str]:
    """Extract one non-empty compiler argv from a compile-database entry.

    ``arguments`` is already tokenized; ``command`` is tokenized with shell
    quoting rules.  Invalid entry shapes raise the stable configuration error.
    """
    if "arguments" in entry:
        arguments = entry["arguments"]
        if not isinstance(arguments, list):
            raise PreprocessingError(
                "compile_commands entry 'arguments' must contain a list",
                category="INVALID_COMPILER_ARGUMENTS",
            )
        argv = [str(arg) for arg in arguments]
    elif "command" in entry:
        command = entry["command"]
        if not isinstance(command, str):
            raise PreprocessingError(
                "compile_commands entry 'command' must contain a string",
                category="INVALID_COMPILER_ARGUMENTS",
            )
        argv = shlex.split(command)
    else:
        raise PreprocessingError(
            "compile_commands entry must contain 'arguments' or 'command'",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    if not argv:
        raise PreprocessingError(
            "compile_commands entry has an empty command",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    return argv


def _is_source_arg(arg: str, source: Path, cwd: Path) -> bool:
    """Return whether one compile argument names the selected source file."""
    path = Path(arg)
    if not path.suffix:
        return False
    candidate = path if path.is_absolute() else cwd / path
    return _same_source(candidate, source)


def _filter_compile_only_args(args: list[str], source: Path, cwd: Path) -> list[str]:
    """Remove compile-only output, dependency, and source arguments from ``args``.

    The remaining order is preserved because compiler target and include flags
    can be significant.  The helper deliberately does not normalize any other
    argument text from the database.
    """
    filtered: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in {"-c", "/c"}:
            index += 1
            continue
        if arg == "-o":
            index += 2
            continue
        if arg.startswith("-o") and arg != "-o":
            index += 1
            continue
        if arg.startswith("/Fo"):
            index += 1
            continue
        if arg in {"-MF", "-MT", "-MQ"}:
            index += 2
            continue
        if arg.startswith(("-MF", "-MT", "-MQ")):
            index += 1
            continue
        if _is_source_arg(arg, source, cwd):
            index += 1
            continue
        filtered.append(arg)
        index += 1
    return filtered


def _compile_commands_entry(source_path: Path, database: list[dict[str, object]]) -> dict[str, object]:
    """Select the sole compile-database entry that matches ``source_path``.

    Missing and ambiguous matches are configuration errors rather than an
    arbitrary selection, so the recipe always identifies one exact command.
    """
    matches: list[dict[str, object]] = []
    for entry in database:
        if not isinstance(entry, dict):
            raise PreprocessingError(
                "compile_commands entries must be objects",
                category="INVALID_COMPILER_ARGUMENTS",
            )
        entry_path = _entry_file_path(entry)
        if _same_source(entry_path, source_path):
            matches.append(entry)
    if not matches:
        raise PreprocessingError(
            f"no compile_commands entry found for {source_path}",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    if len(matches) > 1:
        raise PreprocessingError(
            f"multiple compile_commands entries found for {source_path}",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    return matches[0]


def build_compile_commands_invocation(
    source_path: Path | str,
    *,
    config: PreprocessingConfig,
    language: str = "c",
) -> Invocation:
    """Build one preprocessing command from a matching ``compile_commands`` entry.

    Use this when the project build command, rather than a standalone compiler
    setting, is authoritative.  Compile-only arguments are removed, then the
    normal preprocessing flags are inserted ahead of retained build flags.

    Raises:
        PreprocessingError: If the database cannot provide one valid matching entry.
    """

    _require_language(language)
    source = Path(source_path)
    database = _load_compile_commands(config.compile_commands)
    entry = _compile_commands_entry(source, database)
    cwd = Path(str(entry.get("directory") or "."))
    compile_argv = _compile_command_argv(entry)
    compiler = config.compiler or compile_argv[0]
    compile_args = _filter_compile_only_args(compile_argv[1:], source, cwd)
    argv = [
        compiler,
        *_preprocessor_options(
            config,
            language=language,
            include_language_flag=False,
            compiler=compiler,
        ),
        *compile_args,
        str(source),
    ]
    adapter, capabilities = _invocation_adapter_profile(language, compiler)
    return Invocation(
        argv=argv,
        cwd=str(cwd),
        adapter=adapter,
        language=language,
        compiler=compiler,
        compile_commands=str(config.compile_commands) if config.compile_commands else None,
        compile_commands_entry=dict(entry),
        capabilities=capabilities,
    )


def _template_token_value(token: str, source: Path, language: str, config: PreprocessingConfig) -> list[str]:
    """Expand one command-template token into zero or more argv elements.

    Collection placeholders retain the configured order, while ordinary tokens
    use the scalar placeholders accepted by ``str.format``.  Unknown format
    fields intentionally propagate their ``KeyError`` to preserve template
    validation behavior.
    """
    if token == "{source}":
        return [str(source)]
    if token == "{compiler}":
        return [config.compiler or ""]
    if token == "{language}":
        return [language]
    if token == "{include_dirs}":
        return [f"-I{item}" for item in config.include_dirs]
    if token == "{defines}":
        return [f"-D{item}" for item in config.defines]
    if token == "{undefs}":
        return [f"-U{item}" for item in config.undefs]
    if token == "{standard}":
        return [f"-std={config.std}"] if config.std else []
    if token == "{compiler_args}":
        return list(config.compiler_args)
    return [
        token.format(
            source=str(source),
            compiler=config.compiler or "",
            language=language,
            standard=config.std or "",
        )
    ]


def build_template_preprocess_invocation(
    source_path: Path | str,
    *,
    language: str,
    config: PreprocessingConfig,
) -> Invocation:
    """Build a custom-template preprocessing command without executing it.

    A template must expand to a non-empty command that writes preprocessed
    source to stdout.  Use the documented placeholders for source, compiler,
    language, include paths, macro controls, standard, and compiler arguments.

    Raises:
        PreprocessingError: If no template is configured or expansion is empty.
    """
    _require_language(language)
    if not config.command_template:
        raise PreprocessingError(
            "custom command-template adapter requires --preprocess-template",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    source = Path(source_path)
    argv: list[str] = []
    for token in shlex.split(config.command_template):
        argv.extend(item for item in _template_token_value(token, source, language, config) if item)
    if not argv:
        raise PreprocessingError(
            "custom command-template adapter expanded to an empty command",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    return Invocation(
        argv=argv,
        adapter="command-template",
        language=language,
        compiler=config.compiler or argv[0],
        capabilities={"dependency_output": False, "macro_dump": False, "linemarkers": False},
    )


def build_preprocess_invocation(
    source_path: Path | str,
    *,
    language: str,
    config: PreprocessingConfig,
) -> Invocation:
    """Build the command selected by one preprocessing configuration.

    Command templates take precedence when configured, followed by compile
    databases and then direct compiler mode.  This function only selects and
    builds the command; use :func:`preprocess_source` to execute it.
    """

    _require_language(language)
    if config.adapter == "command-template" or config.command_template:
        return build_template_preprocess_invocation(source_path, language=language, config=config)
    if config.compile_commands:
        return build_compile_commands_invocation(source_path, language=language, config=config)
    return build_direct_preprocess_invocation(source_path, language=language, config=config)


# Compiler provenance: line markers, dependency edges, and macro metadata.


def _unescape_linemarker_filename(text: str) -> str:
    """Decode the limited C-preprocessor escapes used in quoted marker paths.

    Unknown escape sequences intentionally lose only their escape marker,
    matching compiler marker interpretation used by existing provenance tests.
    """
    out: list[str] = []
    escaped = False
    for char in text:
        if escaped:
            out.append({"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"'}.get(char, char))
            escaped = False
        elif char == "\\":
            escaped = True
        else:
            out.append(char)
    if escaped:
        out.append("\\")
    return "".join(out)


def _parse_linemarker(line: str) -> tuple[int, str | None, list[int]] | None:
    """Parse one GCC-style marker or ``#line`` directive, if present.

    The result is ``(original_line, path, flags)``.  Non-marker source lines
    return ``None`` so callers can retain their generated-line accounting.
    """
    match = _LINE_DIRECTIVE_RE.match(line.strip())
    if match is not None:
        filename = match.group("quoted") or match.group("bare")
        return int(match.group("line")), _unescape_linemarker_filename(filename) if filename else None, []
    match = _LINEMARKER_RE.match(line.strip())
    if match is None:
        return None
    filename = match.group("quoted") or match.group("bare")
    flags = [int(flag) for flag in (match.group("flags") or "").split()]
    return int(match.group("line")), _unescape_linemarker_filename(filename) if filename else None, flags


def _dependency_kind(path: str, flags: Sequence[int] = ()) -> DependencyKind:
    """Classify a marker path as a project or system dependency.

    Marker flag ``3`` and fully bracketed pseudo paths represent system inputs;
    all other paths remain project dependencies until a caller marks the root.
    """
    if 3 in flags:
        return "system"
    if path.startswith("<") and path.endswith(">"):
        return "system"
    return "project"


def _exposure_for(path: str, kind: DependencyKind, config: PreprocessingConfig) -> Exposure:
    """Choose public or private dependency exposure in precedence order.

    Explicit private patterns win, explicit public patterns come next, and the
    remaining decision follows system/private and roots-only policy.
    """
    if any(Path(path).match(pattern) or pattern in path for pattern in config.private_includes):
        return "private"
    if any(Path(path).match(pattern) or pattern in path for pattern in config.public_includes):
        return "public"
    if kind == "system":
        return "private"
    if config.include_exposure == "roots-only" and kind != "root":
        return "private"
    return "public"


def parse_linemarker_mappings(source: str, filename: str | None = None) -> list[SourceMapping]:
    """Map each non-marker output line to original compiler-source provenance.

    Use this for GCC-style output or native Fortran expansion when downstream
    parser diagnostics need original paths, lines, and nested include stacks.
    Marker lines themselves have no mapping because they are directives rather
    than parser input.
    """
    mappings: list[SourceMapping] = []
    current_path = filename or "<preprocessed>"
    current_line = 1
    include_stack: list[str] = [current_path] if current_path else []
    for generated_line, line in enumerate(source.splitlines(), start=1):
        marker = _parse_linemarker(line)
        if marker is not None:
            marker_line, marker_path, flags = marker
            if marker_path is not None:
                if 1 in flags:
                    if not include_stack or include_stack[-1] != marker_path:
                        include_stack.append(marker_path)
                elif 2 in flags:
                    if marker_path in include_stack:
                        include_stack = include_stack[: include_stack.index(marker_path) + 1]
                    else:
                        include_stack = [marker_path]
                elif include_stack:
                    include_stack[-1] = marker_path
                else:
                    include_stack = [marker_path]
                current_path = marker_path
            current_line = marker_line
            continue
        mappings.append(
            SourceMapping(
                generated_line=generated_line,
                original_path=current_path,
                original_line=current_line,
                include_stack=list(include_stack),
            )
        )
        current_line += 1
    return mappings


def _included_files_from_linemarkers(
    source: str,
    *,
    root_path: Path,
    language: str,
    config: PreprocessingConfig,
) -> list[IncludedFile]:
    """Derive root and compiler-include edges from line-marker transitions.

    The returned list keeps first-seen compiler includes in output order while
    always retaining the root as its first public dependency.  Native Fortran
    include edges are added separately by :func:`expand_native_fortran_includes`.
    """
    files: list[IncludedFile] = [
        IncludedFile(
            path=str(root_path),
            included_by=None,
            include_line=None,
            mechanism="cpp_include" if language == "fortran" else "c_include",
            dependency_kind="root",
            exposure="public",
        )
    ]
    seen = {str(root_path)}
    current_path = str(root_path)
    current_line = 1
    stack: list[str] = [str(root_path)]
    for line in source.splitlines():
        marker = _parse_linemarker(line)
        if marker is None:
            current_line += 1
            continue
        marker_line, marker_path, flags = marker
        if marker_path is not None:
            if 1 in flags and marker_path not in seen:
                kind = _dependency_kind(marker_path, flags)
                files.append(
                    IncludedFile(
                        path=marker_path,
                        included_by=stack[-1] if stack else current_path,
                        include_line=current_line,
                        mechanism="cpp_include" if language == "fortran" else "c_include",
                        dependency_kind=kind,
                        exposure=_exposure_for(marker_path, kind, config),
                    )
                )
                seen.add(marker_path)
            if 1 in flags:
                stack.append(marker_path)
            elif 2 in flags:
                stack = stack[: stack.index(marker_path) + 1] if marker_path in stack else [marker_path]
            elif stack:
                stack[-1] = marker_path
            current_path = marker_path
        current_line = marker_line
    return files


def _parse_macro_definitions(source: str, mappings: Sequence[SourceMapping]) -> list[MacroDefinition]:
    """Extract ``#define`` records and attach available line-marker provenance.

    The helper only describes definitions present in the supplied source; it
    does not evaluate macros or synthesize definitions absent from compiler
    output.
    """
    macros: list[MacroDefinition] = []
    mapping_by_generated = {mapping.generated_line: mapping for mapping in mappings}
    for generated_line, line in enumerate(source.splitlines(), start=1):
        match = _DEFINE_RE.match(line)
        if match is None:
            continue
        name, params_text, params, value = match.groups()
        mapping = mapping_by_generated.get(generated_line)
        macros.append(
            MacroDefinition(
                name=name,
                value=value.strip() if value else None,
                function_like=params_text is not None,
                parameters=[item.strip() for item in params.split(",")]
                if params is not None and params.strip()
                else ([] if params_text else None),
                path=mapping.original_path if mapping else None,
                line=mapping.original_line if mapping else None,
                builtin=(mapping.original_path.startswith("<") if mapping else False),
            )
        )
    return macros


# Result recipe construction and compiler execution.


def _recipe_from_invocation(
    source_path: Path,
    language: str,
    config: PreprocessingConfig,
    invocation: Invocation,
    result: PreprocessResult | None = None,
) -> PreprocessingRecipe:
    """Project an invocation and collected result metadata into a typed recipe.

    The function copies every mutable collection so the resulting recipe is a
    stable snapshot of this operation rather than an alias of caller-owned
    configuration or result records.
    """
    return PreprocessingRecipe(
        language=language,
        compiler=invocation.compiler,
        mode="compiler",
        adapter=invocation.adapter,
        argv=list(invocation.argv),
        cwd=invocation.cwd,
        include_dirs=list(config.include_dirs),
        defines=list(config.defines),
        undefs=list(config.undefs),
        standard=config.std,
        compiler_args=list(config.compiler_args),
        source_path=str(source_path),
        compile_commands=invocation.compile_commands,
        compile_commands_entry=invocation.compile_commands_entry,
        command_template=config.command_template,
        included_files=[item.to_dict() for item in result.included_files] if result else [],
        source_mappings=[item.to_dict() for item in result.source_mappings] if result else [],
        macros=[item.to_dict() for item in result.macros] if result else [],
        diagnostics=[item.to_dict() for item in result.diagnostics] if result else [],
        capabilities=dict(invocation.capabilities),
    )


def _recipe_from_result(result: PreprocessResult) -> PreprocessingRecipe:
    """Restore the typed recipe record from a result's JSON-compatible payload.

    ``PreprocessResult.recipe`` is intentionally a dictionary for parser
    payload compatibility.  This helper supplies the historic sparse-payload
    defaults used by :func:`run_compiler_preprocessor_with_recipe`.
    """
    return PreprocessingRecipe(
        language=str(result.recipe.get("language")),
        compiler=result.recipe.get("compiler") if isinstance(result.recipe.get("compiler"), str) else None,
        mode=str(result.recipe.get("mode") or "compiler"),
        adapter=str(result.recipe.get("adapter") or "direct"),
        argv=list(result.recipe.get("argv") or []),
        cwd=result.recipe.get("cwd") if isinstance(result.recipe.get("cwd"), str) else None,
        include_dirs=list(result.recipe.get("include_dirs") or []),
        defines=list(result.recipe.get("defines") or []),
        undefs=list(result.recipe.get("undefs") or []),
        standard=result.recipe.get("standard") if isinstance(result.recipe.get("standard"), str) else None,
        compiler_args=list(result.recipe.get("compiler_args") or []),
        source_path=result.recipe.get("source_path") if isinstance(result.recipe.get("source_path"), str) else None,
        compile_commands=result.recipe.get("compile_commands")
        if isinstance(result.recipe.get("compile_commands"), str)
        else None,
        compile_commands_entry=result.recipe.get("compile_commands_entry")
        if isinstance(result.recipe.get("compile_commands_entry"), dict)
        else None,
        command_template=result.recipe.get("command_template")
        if isinstance(result.recipe.get("command_template"), str)
        else None,
        included_files=list(result.recipe.get("included_files") or []),
        source_mappings=list(result.recipe.get("source_mappings") or []),
        macros=list(result.recipe.get("macros") or []),
        diagnostics=list(result.recipe.get("diagnostics") or []),
        capabilities=dict(result.recipe.get("capabilities") or {}),
    )


def _run_preprocess_invocation(invocation: Invocation) -> str:
    """Execute one prepared compiler command and normalize execution failures.

    The helper performs the existing bare-executable availability check before
    running the process.  It returns stdout only after a zero exit status and
    raises :class:`PreprocessingError` with the exact invocation attached to
    each execution failure.
    """
    executable = invocation.argv[0] if invocation.argv else ""
    if executable and os.sep not in executable and shutil.which(executable) is None:
        raise PreprocessingError(
            f"preprocessor not found: {executable}",
            category="PREPROCESSOR_NOT_FOUND",
            diagnostics=[
                PreprocessingDiagnostic(
                    category="PREPROCESSOR_NOT_FOUND",
                    message=f"preprocessor not found: {executable}",
                    command=list(invocation.argv),
                )
            ],
        )
    try:
        completed = subprocess.run(
            invocation.argv,
            cwd=invocation.cwd,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except FileNotFoundError as exc:
        raise PreprocessingError(
            f"preprocessor not found: {invocation.argv[0]}",
            category="PREPROCESSOR_NOT_FOUND",
            diagnostics=[
                PreprocessingDiagnostic(
                    category="PREPROCESSOR_NOT_FOUND",
                    message=f"preprocessor not found: {invocation.argv[0]}",
                    command=list(invocation.argv),
                )
            ],
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise PreprocessingError(
            "compiler preprocessing failed: timed out after 60 seconds",
            category="PREPROCESSOR_FAILED",
            diagnostics=[
                PreprocessingDiagnostic(
                    category="PREPROCESSOR_FAILED",
                    message="compiler preprocessing timed out after 60 seconds",
                    command=list(invocation.argv),
                )
            ],
        ) from exc
    except OSError as exc:
        raise PreprocessingError(
            f"failed to run compiler preprocessor: {exc}",
            category="PREPROCESSOR_FAILED",
            diagnostics=[
                PreprocessingDiagnostic(
                    category="PREPROCESSOR_FAILED",
                    message=f"failed to run compiler preprocessor: {exc}",
                    command=list(invocation.argv),
                )
            ],
        ) from exc

    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        message = f"compiler preprocessing failed with exit code {completed.returncode}"
        if stderr:
            message = f"{message}\n{stderr}"
        raise PreprocessingError(
            message,
            category="PREPROCESSOR_FAILED",
            diagnostics=[
                PreprocessingDiagnostic(
                    category="PREPROCESSOR_FAILED",
                    message=stderr or message,
                    command=list(invocation.argv),
                )
            ],
        )
    return completed.stdout


def _collect_compiler_metadata(
    expanded_source: str,
    *,
    source_path: Path,
    language: str,
    config: PreprocessingConfig,
    invocation: Invocation,
) -> tuple[list[SourceMapping], list[IncludedFile], list[MacroDefinition], list[PreprocessingDiagnostic]]:
    """Collect compiler-output provenance without changing the expanded source.

    The returned collections retain compiler output order.  A no-linemarker
    capability records the existing warning only when no source mappings can be
    recovered from the output.
    """
    mappings = parse_linemarker_mappings(expanded_source, filename=str(source_path))
    included_files = _included_files_from_linemarkers(
        expanded_source,
        root_path=source_path,
        language=language,
        config=config,
    )
    diagnostics: list[PreprocessingDiagnostic] = []
    if invocation.capabilities.get("linemarkers") is False and not mappings:
        diagnostics.append(
            PreprocessingDiagnostic(
                category="PROVENANCE_UNAVAILABLE",
                message="selected compiler adapter did not provide source linemarkers",
                severity="warning",
                command=list(invocation.argv),
            )
        )
    return mappings, included_files, _parse_macro_definitions(expanded_source, mappings), diagnostics


def _raise_for_error_diagnostics(diagnostics: Sequence[PreprocessingDiagnostic]) -> None:
    """Raise the first error diagnostic after all preprocessing facts are collected.

    Warnings return normally.  Passing every diagnostic into the error preserves
    sibling include failures and their original discovery order for callers.
    """
    first_error = next((diagnostic for diagnostic in diagnostics if diagnostic.severity == "error"), None)
    if first_error is not None:
        raise PreprocessingError(
            first_error.message,
            category=first_error.category,
            diagnostics=diagnostics,
        )


def preprocess_source(
    source_path: Path | str,
    *,
    language: str,
    config: PreprocessingConfig,
) -> PreprocessResult:
    """Expand one C or Fortran source path and collect its preprocessing facts.

    Use this as the primary API before passing ``result.source`` to the
    language parser.  It validates compiler mode, selects and executes the
    configured adapter, collects compiler provenance, then expands remaining
    native Fortran includes.  The returned recipe is ready to attach to parser
    or build output.

    Raises:
        PreprocessingError: If configuration, execution, or native include
            expansion produces an error diagnostic.
    """

    # Stage 1: validate the requested compiler route and build its exact command.
    if not config.uses_compiler:
        raise PreprocessingError(
            "Compiler preprocessing not configured",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    source = Path(source_path)
    invocation = build_preprocess_invocation(source, language=language, config=config)

    # Stage 2: execute the compiler and normalize process failures.
    expanded_source = _run_preprocess_invocation(invocation)

    # Stage 3: collect compiler-provided source, dependency, and macro metadata.
    mappings, included_files, macros, diagnostics = _collect_compiler_metadata(
        expanded_source,
        source_path=source,
        language=language,
        config=config,
        invocation=invocation,
    )

    # Stage 4: resolve native Fortran includes that compiler CPP does not expand.
    if language == "fortran":
        from prik.preprocessing.fortran import expand_native_fortran_includes

        expanded_source, native_includes, native_mappings, native_diagnostics = expand_native_fortran_includes(
            expanded_source,
            root_path=source,
            include_dirs=config.include_dirs,
            config=config,
        )
        included_files.extend(native_includes)
        mappings = native_mappings or parse_linemarker_mappings(expanded_source, filename=str(source))
        diagnostics.extend(native_diagnostics)

    # Stage 5: snapshot all facts into the result and recipe payload.
    result = PreprocessResult(
        source=expanded_source,
        recipe={},
        included_files=included_files,
        source_mappings=mappings,
        macros=macros,
        diagnostics=diagnostics,
    )
    result.recipe = _recipe_from_invocation(source, language, config, invocation, result).to_dict()
    _raise_for_error_diagnostics(diagnostics)
    return result


def run_compiler_preprocessor_with_recipe(
    source_path: Path | str,
    language: str,
    config: PreprocessingConfig,
) -> tuple[str, PreprocessingRecipe]:
    """Return expanded parser input and a typed provenance recipe.

    Use this compatibility-shaped convenience API when a caller needs a tuple
    rather than :class:`PreprocessResult`.  It executes the same full workflow
    as :func:`preprocess_source` and preserves sparse-recipe defaults.
    """

    result = preprocess_source(source_path, language=language, config=config)
    return result.source, _recipe_from_result(result)


def run_compiler_preprocessor(
    source_path: Path | str,
    language: str,
    config: PreprocessingConfig,
) -> str:
    """Return only compiler-expanded parser input for one configured source path.

    Use :func:`run_compiler_preprocessor_with_recipe` or
    :func:`preprocess_source` instead when recipe or provenance metadata is
    needed by the next pipeline stage.
    """
    source, _recipe = run_compiler_preprocessor_with_recipe(source_path, language, config)
    return source


__all__ = (
    "CommandTemplateAdapter",
    "CompilerAdapter",
    "GCCCompatibleCAdapter",
    "GNUFortranAdapter",
    "IncludedFile",
    "Invocation",
    "MacroDefinition",
    "PreprocessResult",
    "PreprocessingConfig",
    "PreprocessingDiagnostic",
    "PreprocessingError",
    "PreprocessingPlan",
    "PreprocessingRecipe",
    "SourceMapping",
    "build_compile_commands_invocation",
    "build_direct_preprocess_invocation",
    "build_preprocess_invocation",
    "build_template_preprocess_invocation",
    "parse_linemarker_mappings",
    "preprocess_source",
    "run_compiler_preprocessor",
    "run_compiler_preprocessor_with_recipe",
    "validate_macro_name",
)


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    from prik.preprocessing.fortran import expand_native_fortran_includes

    with TemporaryDirectory() as directory:
        example_directory = Path(directory)
        root_path = example_directory / "greeting.F90"
        include_path = example_directory / "constants.inc"
        fortran_source = (
            "module greeting\n"
            "include 'constants.inc'\n"
            "contains\n"
            "subroutine show_answer()\n"
            "print *, answer\n"
            "end subroutine show_answer\n"
            "end module greeting\n"
        )
        root_path.write_text(fortran_source, encoding="utf-8")
        include_path.write_text("integer, parameter :: answer = 42\n", encoding="utf-8")

        # Native Fortran INCLUDE expansion after compiler CPP output.
        print("Before Fortran include expansion:")
        print(fortran_source, end="")
        print()
        expanded_source, included_files, _mappings, diagnostics = expand_native_fortran_includes(
            fortran_source,
            root_path=root_path,
            include_dirs=[],
        )
        parser_input = [line for line in expanded_source.splitlines() if not line.lstrip().startswith("#")]

        print("After Fortran include expansion:")
        print("\n".join(parser_input))
        print(f"Native includes: {len(included_files)}; diagnostics: {len(diagnostics)}")
        print()

        # Compiler-backed C include and macro expansion.
        c_source_path = example_directory / "state.c"
        c_header_path = example_directory / "state.h"
        c_source = '#include "state.h"\nint state_id = STATE_ID;\n'
        c_header_path.write_text("#define STATE_ID 42\n", encoding="utf-8")
        c_source_path.write_text(c_source, encoding="utf-8")

        print("Before C compiler preprocessing:")
        print(c_source, end="")
        print()
        c_result = preprocess_source(
            c_source_path,
            language="c",
            config=PreprocessingConfig(mode="compiler", compiler="cc"),
        )
        c_parser_input = [
            line.strip() for line in c_result.source.splitlines() if line.strip() and not line.lstrip().startswith("#")
        ]

        print("After C compiler preprocessing:")
        print("\n".join(c_parser_input))
