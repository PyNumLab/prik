"""Compiler-backed preprocessing support for prik wrapper pipelines.

The parser frontends intentionally parse one source stream. This module owns the
compiler/preprocessor invocation, side-channel metadata, source provenance, and
the native Fortran INCLUDE expansion that GNU Fortran CPP leaves unresolved.
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

from prik.compiling.compiler_profiles import fortran_compiler_family


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


class PreprocessingError(Exception):
    """Raised when preprocessing configuration or execution fails."""

    def __init__(
        self,
        message: str,
        *,
        category: PreprocessingCategory = "PREPROCESSOR_FAILED",
        diagnostics: Sequence[PreprocessingDiagnostic] | None = None,
    ) -> None:
        self.category = category
        self.diagnostics = list(diagnostics or [])
        super().__init__(message)


@dataclass
class Invocation:
    """Concrete command line used to obtain preprocessed source."""

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
    category: PreprocessingCategory
    message: str
    severity: Literal["error", "warning", "note"] = "error"
    path: str | None = None
    line: int | None = None
    command: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
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
    path: str
    included_by: str | None = None
    include_line: int | None = None
    mechanism: IncludeMechanism = "cpp_include"
    dependency_kind: DependencyKind = "project"
    exposure: Exposure = "public"

    def to_dict(self) -> dict[str, object]:
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
    generated_line: int
    original_path: str
    original_line: int
    include_stack: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_line": self.generated_line,
            "original_path": self.original_path,
            "original_line": self.original_line,
            "include_stack": list(self.include_stack),
        }


@dataclass
class MacroDefinition:
    name: str
    value: str | None = None
    function_like: bool = False
    parameters: list[str] | None = None
    path: str | None = None
    line: int | None = None
    builtin: bool = False

    def to_dict(self) -> dict[str, object]:
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
    source: str
    recipe: dict[str, object]
    included_files: list[IncludedFile] = field(default_factory=list)
    source_mappings: list[SourceMapping] = field(default_factory=list)
    macros: list[MacroDefinition] = field(default_factory=list)
    diagnostics: list[PreprocessingDiagnostic] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
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
    """JSON-compatible metadata about one preprocessing operation."""

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
        """Backward-compatible alias for older callers."""
        return self.standard

    def to_dict(self) -> dict[str, object]:
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
    """Configuration for compiler-backed preprocessing operations."""

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
        return self.mode == "compiler"

    def fortran_internal_recipe(self, path: Path) -> dict[str, object] | None:
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
    name: str
    capabilities: dict[str, bool]

    def build_preprocess_invocation(
        self,
        source_path: Path,
        *,
        language: str,
        config: PreprocessingConfig,
    ) -> Invocation: ...

    def collect_dependencies(self, result: PreprocessResult) -> list[IncludedFile]: ...

    def collect_macros(self, result: PreprocessResult) -> list[MacroDefinition]: ...

    def parse_linemarkers(self, source: str, filename: str | None = None) -> list[SourceMapping]: ...


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
_FORTRAN_INCLUDE_RE = re.compile(r"^\s*include\s*(?P<quote>['\"])(?P<path>[^'\"]+)(?P=quote)\s*$", re.IGNORECASE)


def validate_macro_name(macro_str: str, context: str) -> None:
    """Validate that a command-line macro definition has a usable name."""

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
    if language not in _VALID_LANGUAGES:
        raise PreprocessingError(
            f"compiler preprocessing is not supported for language {language!r}",
            category="INVALID_COMPILER_ARGUMENTS",
        )


def _compiler_required(config: PreprocessingConfig, language: str) -> str:
    if not config.compiler:
        raise PreprocessingError(
            f"{language} compiler preprocessing requires --compiler with an exact executable",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    return config.compiler


def _fortran_preprocessor_profile(compiler: str) -> tuple[str, tuple[str, ...], dict[str, bool]]:
    """Return vendor-specific preprocessing arguments and advertised facts."""
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


def _preprocessor_options(
    config: PreprocessingConfig,
    *,
    language: str,
    include_language_flag: bool,
    compiler: str,
) -> list[str]:
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
    if source.suffix.lower() in _FORTRAN_SOURCE_SUFFIXES:
        return []
    return ["-x", "f95-cpp-input"]


class GCCCompatibleCAdapter:
    name = "gcc-compatible-c"
    capabilities: ClassVar[dict[str, bool]] = {"dependency_output": True, "macro_dump": True, "linemarkers": True}

    def build_preprocess_invocation(
        self,
        source_path: Path,
        *,
        language: str,
        config: PreprocessingConfig,
    ) -> Invocation:
        return build_direct_preprocess_invocation(source_path, language=language, config=config)

    def collect_dependencies(self, result: PreprocessResult) -> list[IncludedFile]:
        return list(result.included_files)

    def collect_macros(self, result: PreprocessResult) -> list[MacroDefinition]:
        return list(result.macros)

    def parse_linemarkers(self, source: str, filename: str | None = None) -> list[SourceMapping]:
        return parse_linemarker_mappings(source, filename=filename)


class GNUFortranAdapter(GCCCompatibleCAdapter):
    name = "gnu-fortran"


class CommandTemplateAdapter(GCCCompatibleCAdapter):
    name = "command-template"
    capabilities: ClassVar[dict[str, bool]] = {"dependency_output": False, "macro_dump": False, "linemarkers": False}

    def build_preprocess_invocation(
        self,
        source_path: Path,
        *,
        language: str,
        config: PreprocessingConfig,
    ) -> Invocation:
        return build_template_preprocess_invocation(source_path, language=language, config=config)


def build_direct_preprocess_invocation(
    source_path: Path | str,
    *,
    language: str,
    config: PreprocessingConfig,
) -> Invocation:
    """Build an exact direct compiler invocation for preprocessing."""

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
    if language == "fortran":
        adapter, _vendor_args, capabilities = _fortran_preprocessor_profile(compiler)
    else:
        adapter = "gcc-compatible-c"
        capabilities = {"dependency_output": True, "macro_dump": True, "linemarkers": True}
    return Invocation(
        argv=argv,
        cwd=None,
        adapter=adapter,
        language=language,
        compiler=compiler,
        capabilities=capabilities,
    )


def _load_compile_commands(path: str | os.PathLike[str] | None) -> list[dict[str, object]]:
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
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left.absolute() == right.absolute()


def _compile_command_argv(entry: dict[str, object]) -> list[str]:
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
    path = Path(arg)
    if not path.suffix:
        return False
    candidate = path if path.is_absolute() else cwd / path
    return _same_source(candidate, source)


def _filter_compile_only_args(args: list[str], source: Path, cwd: Path) -> list[str]:
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
    """Build a preprocessing invocation from a compile_commands.json entry."""

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
    if language == "fortran":
        adapter, _vendor_args, capabilities = _fortran_preprocessor_profile(compiler)
    else:
        adapter = "gcc-compatible-c"
        capabilities = {"dependency_output": True, "macro_dump": True, "linemarkers": True}
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
    """Build the selected compiler adapter invocation."""

    _require_language(language)
    if config.adapter == "command-template" or config.command_template:
        return build_template_preprocess_invocation(source_path, language=language, config=config)
    if config.compile_commands:
        return build_compile_commands_invocation(source_path, language=language, config=config)
    return build_direct_preprocess_invocation(source_path, language=language, config=config)


def _unescape_linemarker_filename(text: str) -> str:
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
    if 3 in flags:
        return "system"
    if path.startswith("<") and path.endswith(">"):
        return "system"
    return "project"


def _exposure_for(path: str, kind: DependencyKind, config: PreprocessingConfig) -> Exposure:
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


def _mapping_for_generated_line(
    mappings: Sequence[SourceMapping], generated_line: int, fallback: Path
) -> SourceMapping:
    for mapping in mappings:
        if mapping.generated_line == generated_line:
            return mapping
    return SourceMapping(
        generated_line=generated_line,
        original_path=str(fallback),
        original_line=generated_line,
        include_stack=[str(fallback)],
    )


def _resolve_fortran_include(target: str, including_file: str, include_dirs: Sequence[str]) -> Path | None:
    candidates = [Path(including_file).parent / target]
    candidates.extend(Path(include_dir) / target for include_dir in include_dirs)
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def _line_marker(line: int, path: str, flag: int | None = None) -> str:
    escaped = path.replace("\\", "\\\\").replace('"', '\\"')
    suffix = f" {flag}" if flag is not None else ""
    return f'# {line} "{escaped}"{suffix}'


def expand_native_fortran_includes(
    source: str,
    *,
    root_path: Path,
    include_dirs: Sequence[str],
    config: PreprocessingConfig | None = None,
) -> tuple[str, list[IncludedFile], list[SourceMapping], list[PreprocessingDiagnostic]]:
    """Resolve native Fortran INCLUDE statements by textual insertion."""

    config = config or PreprocessingConfig()
    diagnostics: list[PreprocessingDiagnostic] = []
    included_files: list[IncludedFile] = []
    generated_mappings: list[SourceMapping] = []
    line_counter = 0

    def emit_line(line: str, mapping: SourceMapping, out: list[str]) -> None:
        nonlocal line_counter
        out.append(line)
        line_counter += 1
        generated_mappings.append(
            SourceMapping(
                generated_line=line_counter,
                original_path=mapping.original_path,
                original_line=mapping.original_line,
                include_stack=list(mapping.include_stack),
            )
        )

    def expand_text(text: str, current_file: Path, stack: list[Path]) -> list[str]:
        out: list[str] = []
        mappings = parse_linemarker_mappings(text, filename=str(current_file))
        mapping_by_line = {mapping.generated_line: mapping for mapping in mappings}
        for generated_line, line in enumerate(text.splitlines(), start=1):
            marker = _parse_linemarker(line)
            if marker is not None:
                mapping = _mapping_for_generated_line(mappings, generated_line, current_file)
                emit_line(line, mapping, out)
                continue
            mapping = mapping_by_line.get(generated_line) or SourceMapping(
                generated_line=generated_line,
                original_path=str(current_file),
                original_line=generated_line,
                include_stack=[str(path) for path in stack],
            )
            match = _FORTRAN_INCLUDE_RE.match(line)
            if match is None:
                emit_line(line, mapping, out)
                continue

            target = match.group("path")
            resolved = _resolve_fortran_include(target, mapping.original_path, include_dirs)
            if resolved is None:
                diagnostics.append(
                    PreprocessingDiagnostic(
                        category="INCLUDE_NOT_FOUND",
                        message=f'Fortran INCLUDE file "{target}" was not found',
                        path=mapping.original_path,
                        line=mapping.original_line,
                    )
                )
                continue
            try:
                resolved_abs = resolved.resolve()
            except OSError:
                resolved_abs = resolved.absolute()
            if resolved_abs in stack:
                cycle = " -> ".join(str(path) for path in [*stack, resolved_abs])
                diagnostics.append(
                    PreprocessingDiagnostic(
                        category="INCLUDE_CYCLE",
                        message=f"Fortran INCLUDE cycle detected: {cycle}",
                        path=mapping.original_path,
                        line=mapping.original_line,
                    )
                )
                continue

            kind: DependencyKind = "project"
            included_files.append(
                IncludedFile(
                    path=str(resolved_abs),
                    included_by=mapping.original_path,
                    include_line=mapping.original_line,
                    mechanism="fortran_include",
                    dependency_kind=kind,
                    exposure=_exposure_for(str(resolved_abs), kind, config),
                )
            )
            emit_line(_line_marker(1, str(resolved_abs), 1), mapping, out)
            try:
                include_text = resolved.read_text(encoding="utf-8")
            except OSError as exc:
                diagnostics.append(
                    PreprocessingDiagnostic(
                        category="INCLUDE_NOT_FOUND",
                        message=f'Fortran INCLUDE file "{target}" could not be read: {exc}',
                        path=mapping.original_path,
                        line=mapping.original_line,
                    )
                )
                continue
            out.extend(expand_text(include_text, resolved_abs, [*stack, resolved_abs]))
            emit_line(_line_marker(mapping.original_line + 1, mapping.original_path, 2), mapping, out)
        return out

    root_abs = root_path.resolve() if root_path.exists() else root_path.absolute()
    expanded_lines = expand_text(source, root_abs, [root_abs])
    return (
        "\n".join(expanded_lines) + ("\n" if source.endswith("\n") else ""),
        included_files,
        generated_mappings,
        diagnostics,
    )


def _recipe_from_invocation(
    source_path: Path,
    language: str,
    config: PreprocessingConfig,
    invocation: Invocation,
    result: PreprocessResult | None = None,
) -> PreprocessingRecipe:
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


def preprocess_source(
    source_path: Path | str,
    *,
    language: str,
    config: PreprocessingConfig,
) -> PreprocessResult:
    """Run compiler preprocessing and return expanded source plus provenance."""

    if not config.uses_compiler:
        raise PreprocessingError(
            "Compiler preprocessing not configured",
            category="INVALID_COMPILER_ARGUMENTS",
        )
    source = Path(source_path)
    invocation = build_preprocess_invocation(source, language=language, config=config)
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

    expanded_source = completed.stdout
    mappings = parse_linemarker_mappings(expanded_source, filename=str(source))
    included_files = _included_files_from_linemarkers(
        expanded_source,
        root_path=source,
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
    macros = _parse_macro_definitions(expanded_source, mappings)

    if language == "fortran":
        expanded_source, native_includes, native_mappings, native_diagnostics = expand_native_fortran_includes(
            expanded_source,
            root_path=source,
            include_dirs=config.include_dirs,
            config=config,
        )
        included_files.extend(native_includes)
        mappings = native_mappings or parse_linemarker_mappings(expanded_source, filename=str(source))
        diagnostics.extend(native_diagnostics)

    result = PreprocessResult(
        source=expanded_source,
        recipe={},
        included_files=included_files,
        source_mappings=mappings,
        macros=macros,
        diagnostics=diagnostics,
    )
    result.recipe = _recipe_from_invocation(source, language, config, invocation, result).to_dict()
    if any(diagnostic.severity == "error" for diagnostic in diagnostics):
        first = next(diagnostic for diagnostic in diagnostics if diagnostic.severity == "error")
        raise PreprocessingError(
            first.message,
            category=first.category,
            diagnostics=diagnostics,
        )
    return result


def run_compiler_preprocessor_with_recipe(
    source_path: Path | str,
    language: str,
    config: PreprocessingConfig,
) -> tuple[str, PreprocessingRecipe]:
    """Run compiler preprocessing and return expanded source plus recipe."""

    result = preprocess_source(source_path, language=language, config=config)
    recipe = PreprocessingRecipe(
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
    return result.source, recipe


def run_compiler_preprocessor(
    source_path: Path | str,
    language: str,
    config: PreprocessingConfig,
) -> str:
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
    "expand_native_fortran_includes",
    "parse_linemarker_mappings",
    "preprocess_source",
    "run_compiler_preprocessor",
    "run_compiler_preprocessor_with_recipe",
    "validate_macro_name",
)
