from __future__ import annotations

import inspect
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any


_ANSI = {
    "bold": "\033[1m",
    "red": "\033[31m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
    "reset": "\033[0m",
}
_TRUE_VALUES = {"1", "true", "yes", "on"}


def _parse_shape_dim(dim: str) -> dict[str, str | None]:
    token = (dim or "").strip()
    if not token:
        return {"raw": "", "lower": None, "upper": None}
    if ":" not in token:
        return {"raw": token, "lower": "1", "upper": token}
    lo, hi = token.split(":", 1)
    lo = lo.strip() or None
    hi = hi.strip() or None
    return {"raw": token, "lower": lo, "upper": hi}


def _split_top_level(text: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
        if char == delimiter and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    parts.append("".join(current).strip())
    return parts


def _split_top_level_csv(text: str) -> list[str]:
    return [part for part in _split_top_level(text, ",") if part]


def _parse_fortran_expression(text: str | None) -> Any:
    token = (text or "").strip()
    if not token:
        return None

    slice_parts = _split_top_level(token, ":")
    if len(slice_parts) > 1:
        while len(slice_parts) < 3:
            slice_parts.append("")
        return FortranSlice(
            lower=_parse_fortran_expression(slice_parts[0]),
            upper=_parse_fortran_expression(slice_parts[1]),
            stride=_parse_fortran_expression(slice_parts[2]),
            raw=token,
        )

    match = re.fullmatch(r"(?P<name>[A-Za-z_]\w*)\s*\((?P<args>.*)\)", token)
    if match:
        return FortranFunctionCall(
            name=match.group("name"),
            arguments=[_parse_fortran_expression(arg) for arg in _split_top_level_csv(match.group("args"))],
            raw=token,
        )

    return token


@dataclass
class FortranSlice:
    lower: Any = None
    upper: Any = None
    stride: Any = None
    raw: str = ""


@dataclass
class FortranFunctionCall:
    name: str
    arguments: list[Any] = field(default_factory=list)
    raw: str = ""


@dataclass
class FortranShape:
    dimensions: list[Any] = field(default_factory=list)
    raw: list[str] = field(default_factory=list)


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUE_VALUES


def _apply_color(text: str, *styles: str, enabled: bool) -> str:
    if not enabled:
        return text
    prefix = "".join(_ANSI[style] for style in styles)
    return f"{prefix}{text}{_ANSI['reset']}"


def _enable_windows_ansi() -> None:  # pragma: no cover - Windows-only console setup.
    """Enable ANSI escape sequence handling on Windows terminals when possible."""
    if os.name != "nt":
        return

    if sys.modules.get("colorama") is not None:
        sys.modules["colorama"].just_fix_windows_console()
        return

    import importlib.util

    if importlib.util.find_spec("colorama") is not None:
        import importlib

        colorama = importlib.import_module("colorama")
        colorama.just_fix_windows_console()


class FortranParseError(ValueError):
    """Parser error with compiler-style diagnostic rendering support."""

    default_code = "PARSE_ERROR"

    def __init__(
        self,
        message: str,
        filename: str | None = None,
        line_number: int | None = None,
        source_line: str | None = None,
        *,
        code: str | None = None,
    ):
        self.filename = filename
        self.line_number = line_number
        self.source_line = source_line
        self.base_message = message
        self.code = code or self.default_code
        frame = inspect.stack()[1]
        self.parser_file = frame.filename
        self.parser_line_number = frame.lineno
        self.parser_function = frame.function
        super().__init__(self.format_diagnostic(color=False))

    def format_diagnostic(self, *, color: bool = False, debug: bool | None = None) -> str:
        """Return a Fortran/compiler-style diagnostic for this parse error."""
        if color:
            _enable_windows_ansi()
        if debug is None:
            debug = _env_flag("FORTRAN_PARSER_DEBUG")

        location = self.filename or "<unknown>"
        if self.line_number is not None:
            location = f"{location}:{self.line_number}:1"

        severity = _apply_color("error", "red", "bold", enabled=color)
        code = _apply_color(f"[{self.code}]", "cyan", enabled=color)
        lines = [f"{_apply_color(location, 'bold', enabled=color)}: {severity}{code}: {self.base_message}"]

        if self.source_line is not None:
            line_no = str(self.line_number) if self.line_number is not None else "?"
            gutter_width = max(len(line_no), 1)
            source = self.source_line.rstrip("\n")
            marker = "^" if source.strip() else ""
            lines.extend(
                [
                    f"{' ' * gutter_width} {_apply_color('|', 'blue', enabled=color)}",
                    f"{_apply_color(line_no.rjust(gutter_width), 'blue', enabled=color)} {_apply_color('|', 'blue', enabled=color)} {source}",
                    f"{' ' * gutter_width} {_apply_color('|', 'blue', enabled=color)} {_apply_color(marker, 'red', 'bold', enabled=color)}",
                ]
            )

        if debug:
            lines.append(
                _apply_color(
                    f"note: parser raised at {self.parser_file}:{self.parser_line_number} in {self.parser_function}()",
                    "cyan",
                    enabled=color,
                )
            )

        return "\n".join(lines)


@dataclass
class FortranVariable:
    name: str
    base_type: str = "unknown"
    kind: str = ""
    rank: int = 0
    shape: list[str] = field(default_factory=list)
    lbound: list[str | None] = field(default_factory=list)
    ubound: list[str | None] = field(default_factory=list)
    value: str | None = None
    symbolic_value: str | None = None
    value_type: str = "unknown"
    is_parameter: bool = False
    target: bool = False
    dimensions: list[int] = field(default_factory=list)
    visibility: str = "public"

    def __post_init__(self) -> None:
        if self.kind is None:
            self.kind = ""

    @property
    def shape_info(self) -> list[dict[str, str | None]]:
        """Structured per-dimension shape metadata derived from `shape` tokens."""
        return [_parse_shape_dim(dim) for dim in self.shape]

    @property
    def structured_shape(self) -> FortranShape:
        """Typed representation of shape tokens.

        The serialized `shape` field remains the compatibility source of truth.
        This helper exposes slices and function-call dimensions without
        changing existing JSON output.
        """
        return FortranShape(
            dimensions=[_parse_fortran_expression(dim) for dim in self.shape],
            raw=list(self.shape),
        )

    @property
    def lower_bounds(self) -> list[str | None]:
        return [d["lower"] for d in self.shape_info]

    @property
    def upper_bounds(self) -> list[str | None]:
        return [d["upper"] for d in self.shape_info]

    @property
    def kind_expression(self) -> Any:
        return _parse_fortran_expression(self.kind)

    @property
    def value_expression(self) -> Any:
        return _parse_fortran_expression(self.value)

    @property
    def target_kind_expression(self) -> str:
        """Compiler kind expression preserved without changing parser JSON."""
        return str(getattr(self, "_target_kind_expression", ""))

    @property
    def character_length_syntax(self) -> bool:
        """Whether the stored character ``kind`` text is actually a length."""
        return bool(getattr(self, "_character_length_syntax", False))

    @property
    def polymorphic(self) -> bool:
        """Whether this variable was declared with Fortran ``class(...)``."""
        return bool(getattr(self, "_fortran_polymorphic", False))

    @property
    def declared_storage_bits(self) -> int | None:
        """Fixed storage width carried by a legacy numeric ``type*N`` form."""
        bits = getattr(self, "_declared_storage_bits", None)
        return int(bits) if bits is not None else None


@dataclass
class FortranArgument(FortranVariable):
    procedure: str | None = None
    optional: bool = False
    pass_by_value: bool = False
    allocatable: bool = False
    pointer: bool = False
    target: bool = False

    @property
    def contiguous(self) -> bool:
        return bool(getattr(self, "_contiguous", False))

    @contiguous.setter
    def contiguous(self, value: bool) -> None:
        self._contiguous = bool(value)

    @property
    def intent(self) -> str | None:
        """Exact Fortran INTENT attribute on this dummy argument, when present."""
        value = getattr(self, "_intent", None)
        return None if value is None else str(value)

    @intent.setter
    def intent(self, value: str | None) -> None:
        self._intent = None if value is None else re.sub(r"\s+", "", str(value).lower())

    @property
    def reads_argument(self) -> bool | None:
        value = getattr(self, "_reads_argument", None)
        return None if value is None else bool(value)

    @reads_argument.setter
    def reads_argument(self, value: bool | None) -> None:
        self._reads_argument = None if value is None else bool(value)

    @property
    def writes_argument(self) -> bool | None:
        value = getattr(self, "_writes_argument", None)
        return None if value is None else bool(value)

    @writes_argument.setter
    def writes_argument(self, value: bool | None) -> None:
        self._writes_argument = None if value is None else bool(value)


@dataclass(eq=False)
class FortranUseMapping:
    source: str
    target: str | None = None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.local_name == other
        if not isinstance(other, FortranUseMapping):
            return False
        return (self.source, self.target) == (other.source, other.target)

    @property
    def local_name(self) -> str:
        return self.target or self.source


@dataclass
class FortranProcedureSignature:
    name: str
    kind: str
    module: str | None = None
    arguments: list[FortranArgument] = field(default_factory=list)
    result: FortranArgument | None = None
    attributes: list[str] = field(default_factory=list)
    bind_name: str | None = None
    uses: dict[str, list[FortranUseMapping]] = field(default_factory=dict)
    in_interface: bool = False
    variables: dict[str, FortranVariable] = field(default_factory=dict)
    common_variables: list[str] = field(default_factory=list)


@dataclass
class FortranDerivedType:
    name: str
    module: str | None = None
    fields: list[FortranArgument] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    final_procedures: list[str] = field(default_factory=list)
    extends: FortranDerivedType | str | None = None
    attributes: list[str] = field(default_factory=list)
    procedure_bindings: list[dict] = field(default_factory=list)
    generic_bindings: list[dict] = field(default_factory=list)


@dataclass
class FortranInterface:
    name: str | None = None
    module: str | None = None
    procedures: list[FortranProcedureSignature] = field(default_factory=list)
    specific_procedures: list[str] = field(default_factory=list)
    abstract: bool = False


@dataclass
class FortranEnumerator:
    name: str
    value: str | None = None
    symbolic_value: str | None = None
    visibility: str = "public"


@dataclass
class FortranEnum:
    name: str | None = None
    module: str | None = None
    bind_c: bool = False
    enumerators: list[FortranEnumerator] = field(default_factory=list)
    visibility: str = "public"


@dataclass
class FortranModule:
    name: str
    filename: str | None = None
    uses: dict[str, list[FortranUseMapping]] = field(default_factory=dict)
    variables: list[FortranVariable] = field(default_factory=list)
    procedures: list[FortranProcedureSignature] = field(default_factory=list)
    derived_types: list[FortranDerivedType] = field(default_factory=list)
    interfaces: list[FortranInterface] = field(default_factory=list)
    enums: list[FortranEnum] = field(default_factory=list)
    default_visibility: str = "public"
    public_symbols: list[str] = field(default_factory=list)
    private_symbols: list[str] = field(default_factory=list)
    common_variables: list[str] = field(default_factory=list)


@dataclass
class FortranSubmodule:
    name: str
    parent: str
    ancestor: str | None = None
    filename: str | None = None
    uses: dict[str, list[FortranUseMapping]] = field(default_factory=dict)
    variables: list[FortranVariable] = field(default_factory=list)
    procedures: list[FortranProcedureSignature] = field(default_factory=list)
    derived_types: list[FortranDerivedType] = field(default_factory=list)
    interfaces: list[FortranInterface] = field(default_factory=list)
    enums: list[FortranEnum] = field(default_factory=list)
    common_variables: list[str] = field(default_factory=list)


@dataclass
class FortranProgram:
    name: str | None = None
    filename: str | None = None
    uses: dict[str, list[FortranUseMapping]] = field(default_factory=dict)
    variables: list[FortranVariable] = field(default_factory=list)
    procedures: list[FortranProcedureSignature] = field(default_factory=list)
    enums: list[FortranEnum] = field(default_factory=list)
    common_variables: list[str] = field(default_factory=list)


@dataclass
class FortranBlockData:
    name: str | None = None
    filename: str | None = None
    variables: list[FortranVariable] = field(default_factory=list)
    common_variables: list[str] = field(default_factory=list)


@dataclass
class FortranFile:
    # --------------------------------------------------------
    # File metadata
    # --------------------------------------------------------

    filename: str | None = None

    source: str | None = None

    encoding: str = "utf-8"

    format: str = "free"
    # "free" | "fixed"

    # --------------------------------------------------------
    # Top-level program units
    # --------------------------------------------------------

    modules: list[FortranModule] = field(default_factory=list)

    submodules: list[FortranSubmodule] = field(default_factory=list)

    programs: list[FortranProgram] = field(default_factory=list)

    block_data_units: list[FortranBlockData] = field(default_factory=list)

    procedures: list[FortranProcedureSignature] = field(default_factory=list)
    # standalone procedures outside modules

    interfaces: list[FortranInterface] = field(default_factory=list)

    derived_types: list[FortranDerivedType] = field(default_factory=list)
    # standalone derived types if ever encountered

    variables: list[FortranVariable] = field(default_factory=list)
    # file-scope declarations if relevant

    # --------------------------------------------------------
    # Include information
    # --------------------------------------------------------

    includes: list[str] = field(default_factory=list)

    # --------------------------------------------------------
    # Diagnostics
    # --------------------------------------------------------

    diagnostics: list[str] = field(default_factory=list)

    # --------------------------------------------------------
    # Symbol table (optional later)
    # --------------------------------------------------------

    symbols: dict[str, object] = field(default_factory=dict)


@dataclass
class FortranProject:
    # --------------------------------------------------------
    # Physical files
    # --------------------------------------------------------

    files: list[FortranFile] = field(default_factory=list)

    # --------------------------------------------------------
    # Global symbol registries
    # --------------------------------------------------------

    modules: dict[str, FortranModule] = field(default_factory=dict)

    submodules: dict[str, FortranSubmodule] = field(default_factory=dict)

    programs: dict[str, FortranProgram] = field(default_factory=dict)

    procedures: dict[str, FortranProcedureSignature] = field(default_factory=dict)

    derived_types: dict[str, FortranDerivedType] = field(default_factory=dict)

    interfaces: dict[str, FortranInterface] = field(default_factory=dict)

    # --------------------------------------------------------
    # Dependency graph
    # --------------------------------------------------------

    dependencies: dict[str, set[str]] = field(default_factory=dict)

    # --------------------------------------------------------
    # Include resolution
    # --------------------------------------------------------

    include_dirs: list[str] = field(default_factory=list)

    # --------------------------------------------------------
    # Diagnostics
    # --------------------------------------------------------

    diagnostics: list[str] = field(default_factory=list)
