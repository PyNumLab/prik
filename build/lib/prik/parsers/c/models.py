from __future__ import annotations

import inspect
import os
import sys
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any


_ANSI = {
    "bold": "\033[1m",
    "red": "\033[31m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
    "reset": "\033[0m",
}
_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUE_VALUES


def _apply_color(text: str, *styles: str, enabled: bool) -> str:
    if not enabled:
        return text
    prefix = "".join(_ANSI[style] for style in styles)
    return f"{prefix}{text}{_ANSI['reset']}"


def _enable_windows_ansi() -> None:  # pragma: no cover - Windows-only console setup.
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


def c_model_to_dict(obj: Any, _seen: set[int] | None = None) -> Any:
    """Convert C parser dataclasses into stable JSON-compatible values."""
    if _seen is None:
        _seen = set()
    if isinstance(obj, CQualifier):
        return obj.spelling
    if isinstance(obj, CType):
        if isinstance(obj, CStruct | CUnion | CEnum | CTypedef) and id(obj) in _seen:
            return {"reference": obj.reference_name}
        if isinstance(obj, CStruct | CUnion | CEnum | CTypedef):
            _seen.add(id(obj))
        payload = {"model": type(obj).__name__}
        payload.update(
            {f.name: c_model_to_dict(getattr(obj, f.name), _seen) for f in fields(obj) if f.name != "origin"}
        )
        return payload
    if is_dataclass(obj):
        return {
            f.name: c_model_to_dict(getattr(obj, f.name), _seen)
            for f in fields(obj)
            if not (
                f.name == "origin"
                or (
                    isinstance(obj, CFile)
                    and f.name in {"preprocessing_recipe", "preprocessed_source_path"}
                    and getattr(obj, f.name) is None
                )
                or (isinstance(obj, CFile) and f.name == "original_source_paths" and not getattr(obj, f.name))
                or (isinstance(obj, CFunction) and f.name == "condition_set" and not getattr(obj, f.name))
                or (
                    isinstance(obj, CProject) and f.name == "conditional_function_variants" and not getattr(obj, f.name)
                )
            )
        }
    if isinstance(obj, list):
        return [c_model_to_dict(v, _seen) for v in obj]
    if isinstance(obj, dict):
        return {k: c_model_to_dict(v, _seen) for k, v in obj.items()}
    if isinstance(obj, set | frozenset):
        return sorted(c_model_to_dict(v, _seen) for v in obj)
    return obj


class CParseError(ValueError):
    """C parser error with compiler-style diagnostic rendering support."""

    default_code = "CPARSE_ERROR"

    def __init__(
        self,
        message: str,
        filename: str | None = None,
        line_number: int | None = None,
        column: int | None = None,
        source_line: str | None = None,
        *,
        code: str | None = None,
    ):
        self.filename = filename
        self.line_number = line_number
        self.column = column
        self.source_line = source_line
        self.base_message = message
        self.code = code or self.default_code
        frame = inspect.stack()[1]
        self.parser_file = frame.filename
        self.parser_line_number = frame.lineno
        self.parser_function = frame.function
        super().__init__(self.format_diagnostic(color=False))

    def format_diagnostic(self, *, color: bool = False, debug: bool | None = None) -> str:
        if color:
            _enable_windows_ansi()
        if debug is None:
            debug = _env_flag("C_PARSER_DEBUG")

        location = self.filename or "<unknown>"
        if self.line_number is not None:
            column = self.column if self.column is not None else 1
            location = f"{location}:{self.line_number}:{column}"

        severity = _apply_color("error", "red", "bold", enabled=color)
        code = _apply_color(f"[{self.code}]", "cyan", enabled=color)
        lines = [f"{_apply_color(location, 'bold', enabled=color)}: {severity}{code}: {self.base_message}"]

        if self.source_line is not None:
            line_no = str(self.line_number) if self.line_number is not None else "?"
            gutter_width = max(len(line_no), 1)
            source = self.source_line.rstrip("\n")
            marker_column = max((self.column or 1) - 1, 0)
            marker = " " * marker_column + "^" if source.strip() else ""
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
class CSourceLocation:
    filename: str | None = None
    line: int | None = None
    column: int | None = None
    source_line: str | None = None

    @property
    def display(self) -> str:
        location = self.filename or "<unknown>"
        if self.line is not None:
            column = self.column if self.column is not None else 1
            location = f"{location}:{self.line}:{column}"
        return location


@dataclass
class CDiagnostic:
    code: str
    message: str
    severity: str = "warning"
    location: CSourceLocation | None = None
    unit_kind: str | None = None
    unit_name: str | None = None


@dataclass(frozen=True)
class CQualifier:
    spelling: str


@dataclass(frozen=True)
class CConst(CQualifier):
    spelling: str = "const"


@dataclass(frozen=True)
class CVolatile(CQualifier):
    spelling: str = "volatile"


@dataclass(frozen=True)
class CRestrict(CQualifier):
    spelling: str = "restrict"


@dataclass(frozen=True)
class CAtomic(CQualifier):
    spelling: str = "_Atomic"


@dataclass(kw_only=True)
class CType:
    qualifiers: list[CQualifier] = field(default_factory=list)
    source_text: str = ""


@dataclass
class CUnknownType(CType):
    spelling: str = "unknown"


@dataclass
class CVoid(CType):
    pass


@dataclass
class CBool(CType):
    pass


@dataclass
class CChar(CType):
    pass


@dataclass
class CSignedChar(CType):
    pass


@dataclass
class CUnsignedChar(CType):
    pass


@dataclass
class CShort(CType):
    pass


@dataclass
class CUnsignedShort(CType):
    pass


@dataclass
class CInt(CType):
    pass


@dataclass
class CUnsignedInt(CType):
    pass


@dataclass
class CLong(CType):
    pass


@dataclass
class CUnsignedLong(CType):
    pass


@dataclass
class CLongLong(CType):
    pass


@dataclass
class CUnsignedLongLong(CType):
    pass


@dataclass
class CFloat(CType):
    pass


@dataclass
class CDouble(CType):
    pass


@dataclass
class CLongDouble(CType):
    pass


@dataclass
class CFloatComplex(CType):
    pass


@dataclass
class CDoubleComplex(CType):
    pass


@dataclass
class CLongDoubleComplex(CType):
    pass


@dataclass
class CPointer(CType):
    pass


@dataclass
class CArray(CType):
    bound: str | None = None
    is_static_minimum: bool = False
    is_variable_length: bool = False
    is_flexible: bool = False


@dataclass
class CFunctionType(CType):
    result_type: CType = field(default_factory=CVoid)
    parameter_types: list[CType] = field(default_factory=list)
    is_variadic: bool = False
    prototype_style: str | None = None


@dataclass
class CComposedType(CType):
    components: list[CType] = field(default_factory=list)

    @property
    def pointer_depth(self) -> int:
        return sum(isinstance(component, CPointer) for component in self.components)

    @property
    def array_rank(self) -> int:
        return sum(isinstance(component, CArray) for component in self.components)


def _contains_function_pointer(type_: CType) -> bool:
    if not isinstance(type_, CComposedType):
        return False
    for index, component in enumerate(type_.components):
        if isinstance(component, CPointer) and any(
            isinstance(later, CFunctionType) for later in type_.components[index + 1 :]
        ):
            return True
    return False


@dataclass
class CParameter:
    name: str | None = None
    type: CType = field(default_factory=CVoid)
    declared_type: CType | None = None
    source_location: CSourceLocation | None = None
    callback_policy: Any = None
    origin: str | None = None

    @property
    def callback_candidate(self) -> bool:
        return _contains_function_pointer(self.type)


@dataclass
class CFunction:
    name: str
    result_type: CType = field(default_factory=CVoid)
    parameters: list[CParameter] = field(default_factory=list)
    storage: list[str] = field(default_factory=list)
    specifiers: list[str] = field(default_factory=list)
    is_variadic: bool = False
    is_definition: bool = False
    prototype_style: str | None = None
    source_location: CSourceLocation | None = None
    start: CSourceLocation | None = None
    end: CSourceLocation | None = None
    declaration_locations: list[CSourceLocation] = field(default_factory=list)
    condition_set: frozenset[str] = field(default_factory=frozenset)
    origin: str | None = None

    @property
    def type(self) -> CFunctionType:
        return CFunctionType(
            result_type=self.result_type,
            parameter_types=[parameter.type for parameter in self.parameters],
            is_variadic=self.is_variadic,
            prototype_style=self.prototype_style,
        )


@dataclass
class CStruct(CType):
    name: str | None = None
    members: list[CVariable] = field(default_factory=list)
    anonymous_id: str | None = None
    is_incomplete: bool = False
    source_location: CSourceLocation | None = None
    origin: str | None = None

    @property
    def reference_name(self) -> str:
        return f"struct {self.name}" if self.name else self.anonymous_id or "anonymous struct"


@dataclass
class CUnion(CType):
    name: str | None = None
    members: list[CVariable] = field(default_factory=list)
    anonymous_id: str | None = None
    is_incomplete: bool = False
    source_location: CSourceLocation | None = None
    origin: str | None = None

    @property
    def reference_name(self) -> str:
        return f"union {self.name}" if self.name else self.anonymous_id or "anonymous union"


@dataclass
class CEnumerator:
    name: str
    value: str | None = None
    source_location: CSourceLocation | None = None
    origin: str | None = None


@dataclass
class CEnum(CType):
    name: str | None = None
    constants: list[CEnumerator] = field(default_factory=list)
    anonymous_id: str | None = None
    source_location: CSourceLocation | None = None
    origin: str | None = None

    @property
    def reference_name(self) -> str:
        return f"enum {self.name}" if self.name else self.anonymous_id or "anonymous enum"


@dataclass
class CTypedef(CType):
    name: str
    type: CType | None = None
    source_location: CSourceLocation | None = None
    declaration_locations: list[CSourceLocation] = field(default_factory=list)
    origin: str | None = None

    @property
    def reference_name(self) -> str:
        return self.name


@dataclass
class CInitializer:
    source_text: str


@dataclass
class CVariable:
    name: str | None
    type: CType = field(default_factory=CVoid)
    storage: list[str] = field(default_factory=list)
    initializer: CInitializer | None = None
    bit_width: str | None = None
    source_location: CSourceLocation | None = None
    callback_policy: Any = None
    declaration_locations: list[CSourceLocation] = field(default_factory=list)
    origin: str | None = None

    @property
    def callback_candidate(self) -> bool:
        return _contains_function_pointer(self.type)


@dataclass
class CMacro:
    name: str
    value: str | None = None
    function_like: bool = False
    directive: str = "define"
    source_location: CSourceLocation | None = None


@dataclass
class CRawDirective:
    directive: str
    argument: str | None = None
    source_location: CSourceLocation | None = None


@dataclass
class CMacroDependency:
    name: str
    context: str = "declaration"
    source_location: CSourceLocation | None = None
    source_text: str = ""


@dataclass
class CInclude:
    target: str
    kind: str = "local"
    resolved_path: str | None = None
    source_location: CSourceLocation | None = None


@dataclass
class CFile:
    filename: str | None = None
    language: str = "c"
    preprocessing: str = "raw"
    preprocessing_recipe: dict[str, Any] | None = None
    preprocessed_source_path: str | None = None
    original_source_paths: list[str] = field(default_factory=list)
    functions: list[CFunction] = field(default_factory=list)
    structs: list[CStruct] = field(default_factory=list)
    unions: list[CUnion] = field(default_factory=list)
    enums: list[CEnum] = field(default_factory=list)
    typedefs: list[CTypedef] = field(default_factory=list)
    variables: list[CVariable] = field(default_factory=list)
    macros: list[CMacro] = field(default_factory=list)
    includes: list[CInclude] = field(default_factory=list)
    raw_directives: list[CRawDirective] = field(default_factory=list)
    macro_dependencies: list[CMacroDependency] = field(default_factory=list)
    diagnostics: list[CDiagnostic] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return c_model_to_dict(self)


@dataclass
class CProject:
    files: dict[str, CFile] = field(default_factory=dict)
    functions: dict[str, CFunction] = field(default_factory=dict)
    structs: dict[str, CStruct] = field(default_factory=dict)
    unions: dict[str, CUnion] = field(default_factory=dict)
    enums: dict[str, CEnum] = field(default_factory=dict)
    typedefs: dict[str, CTypedef] = field(default_factory=dict)
    variables: dict[str, CVariable] = field(default_factory=dict)
    macros: dict[str, CMacro] = field(default_factory=dict)
    includes: dict[str, CInclude] = field(default_factory=dict)
    functions_by_file: dict[str, list[str]] = field(default_factory=dict)
    enum_constants: dict[str, CEnumerator] = field(default_factory=dict)
    include_graph: dict[str, set[str]] = field(default_factory=dict)
    system_includes: dict[str, set[str]] = field(default_factory=dict)
    unresolved_includes: dict[str, set[str]] = field(default_factory=dict)
    header_source_pairs: dict[str, set[str]] = field(default_factory=dict)
    conditional_function_variants: dict[str, list[CFunction]] = field(default_factory=dict)
    diagnostics: list[CDiagnostic] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return c_model_to_dict(self)
