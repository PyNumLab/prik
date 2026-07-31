"""Minimal JSON-shape coverage for C parser model dataclasses."""

from dataclasses import is_dataclass
import importlib
import inspect
from types import SimpleNamespace

import x2py.parsers.c.models as models


def _type_payload(model: str, **extra):
    payload = {"model": model, "qualifiers": [], "source_text": ""}
    payload.update(extra)
    return payload


def test_each_c_model_has_minimal_json_shape():
    cases = {
        "CSourceLocation": (
            models.CSourceLocation(),
            {"filename": None, "line": None, "column": None, "source_line": None},
        ),
        "CDiagnostic": (
            models.CDiagnostic(code="C_TEST", message="test message"),
            {
                "code": "C_TEST",
                "message": "test message",
                "severity": "warning",
                "location": None,
                "unit_kind": None,
                "unit_name": None,
            },
        ),
        "CQualifier": (models.CQualifier("const"), "const"),
        "CConst": (models.CConst(), "const"),
        "CVolatile": (models.CVolatile(), "volatile"),
        "CRestrict": (models.CRestrict(), "restrict"),
        "CAtomic": (models.CAtomic(), "_Atomic"),
        "CType": (models.CType(), _type_payload("CType")),
        "CUnknownType": (models.CUnknownType(), _type_payload("CUnknownType", spelling="unknown")),
        "CVoid": (models.CVoid(), _type_payload("CVoid")),
        "CBool": (models.CBool(), _type_payload("CBool")),
        "CChar": (models.CChar(), _type_payload("CChar")),
        "CSignedChar": (models.CSignedChar(), _type_payload("CSignedChar")),
        "CUnsignedChar": (models.CUnsignedChar(), _type_payload("CUnsignedChar")),
        "CShort": (models.CShort(), _type_payload("CShort")),
        "CUnsignedShort": (models.CUnsignedShort(), _type_payload("CUnsignedShort")),
        "CInt": (models.CInt(), _type_payload("CInt")),
        "CUnsignedInt": (models.CUnsignedInt(), _type_payload("CUnsignedInt")),
        "CLong": (models.CLong(), _type_payload("CLong")),
        "CUnsignedLong": (models.CUnsignedLong(), _type_payload("CUnsignedLong")),
        "CLongLong": (models.CLongLong(), _type_payload("CLongLong")),
        "CUnsignedLongLong": (models.CUnsignedLongLong(), _type_payload("CUnsignedLongLong")),
        "CFloat": (models.CFloat(), _type_payload("CFloat")),
        "CDouble": (models.CDouble(), _type_payload("CDouble")),
        "CLongDouble": (models.CLongDouble(), _type_payload("CLongDouble")),
        "CFloatComplex": (models.CFloatComplex(), _type_payload("CFloatComplex")),
        "CDoubleComplex": (models.CDoubleComplex(), _type_payload("CDoubleComplex")),
        "CLongDoubleComplex": (models.CLongDoubleComplex(), _type_payload("CLongDoubleComplex")),
        "CPointer": (models.CPointer(), _type_payload("CPointer")),
        "CArray": (
            models.CArray(),
            _type_payload(
                "CArray",
                bound=None,
                is_static_minimum=False,
                is_variable_length=False,
                is_flexible=False,
            ),
        ),
        "CFunctionType": (
            models.CFunctionType(),
            _type_payload(
                "CFunctionType",
                result_type=_type_payload("CVoid"),
                parameter_types=[],
                is_variadic=False,
                prototype_style=None,
            ),
        ),
        "CComposedType": (
            models.CComposedType(),
            _type_payload("CComposedType", components=[]),
        ),
        "CParameter": (
            models.CParameter(),
            {
                "name": None,
                "type": _type_payload("CVoid"),
                "declared_type": None,
                "source_location": None,
                "callback_policy": None,
            },
        ),
        "CFunction": (
            models.CFunction(name="run"),
            {
                "name": "run",
                "result_type": _type_payload("CVoid"),
                "parameters": [],
                "storage": [],
                "specifiers": [],
                "is_variadic": False,
                "is_definition": False,
                "prototype_style": None,
                "source_location": None,
                "start": None,
                "end": None,
                "declaration_locations": [],
            },
        ),
        "CStruct": (
            models.CStruct(),
            _type_payload(
                "CStruct",
                name=None,
                members=[],
                anonymous_id=None,
                is_incomplete=False,
                source_location=None,
            ),
        ),
        "CUnion": (
            models.CUnion(),
            _type_payload(
                "CUnion",
                name=None,
                members=[],
                anonymous_id=None,
                is_incomplete=False,
                source_location=None,
            ),
        ),
        "CEnumerator": (
            models.CEnumerator(name="STATUS_OK"),
            {"name": "STATUS_OK", "value": None, "source_location": None},
        ),
        "CEnum": (
            models.CEnum(),
            _type_payload("CEnum", name=None, constants=[], anonymous_id=None, source_location=None),
        ),
        "CTypedef": (
            models.CTypedef(name="api_int"),
            _type_payload(
                "CTypedef",
                name="api_int",
                type=None,
                source_location=None,
                declaration_locations=[],
            ),
        ),
        "CInitializer": (models.CInitializer(source_text="42"), {"source_text": "42"}),
        "CVariable": (
            models.CVariable(name="value"),
            {
                "name": "value",
                "type": _type_payload("CVoid"),
                "storage": [],
                "initializer": None,
                "bit_width": None,
                "source_location": None,
                "callback_policy": None,
                "declaration_locations": [],
            },
        ),
        "CMacro": (
            models.CMacro(name="API"),
            {
                "name": "API",
                "value": None,
                "function_like": False,
                "directive": "define",
                "source_location": None,
            },
        ),
        "CRawDirective": (
            models.CRawDirective(directive="include"),
            {"directive": "include", "argument": None, "source_location": None},
        ),
        "CMacroDependency": (
            models.CMacroDependency(name="API"),
            {
                "name": "API",
                "context": "declaration",
                "source_location": None,
                "source_text": "",
            },
        ),
        "CInclude": (
            models.CInclude(target="api.h"),
            {"target": "api.h", "kind": "local", "resolved_path": None, "source_location": None},
        ),
        "CFile": (
            models.CFile(filename="api.h"),
            {
                "filename": "api.h",
                "language": "c",
                "preprocessing": "raw",
                "functions": [],
                "structs": [],
                "unions": [],
                "enums": [],
                "typedefs": [],
                "variables": [],
                "macros": [],
                "includes": [],
                "raw_directives": [],
                "macro_dependencies": [],
                "diagnostics": [],
            },
        ),
        "CProject": (
            models.CProject(),
            {
                "files": {},
                "functions": {},
                "structs": {},
                "unions": {},
                "enums": {},
                "typedefs": {},
                "variables": {},
                "macros": {},
                "includes": {},
                "functions_by_file": {},
                "enum_constants": {},
                "include_graph": {},
                "system_includes": {},
                "unresolved_includes": {},
                "header_source_pairs": {},
                "diagnostics": [],
            },
        ),
    }

    model_dataclasses = {
        name
        for name, obj in inspect.getmembers(models, inspect.isclass)
        if obj.__module__ == models.__name__ and is_dataclass(obj)
    }
    assert set(cases) == model_dataclasses

    for model_name, (model, expected) in cases.items():
        assert models.c_model_to_dict(model) == expected, model_name


def test_c_model_helpers_cover_environment_color_and_windows_setup(monkeypatch):
    monkeypatch.setenv("C_PARSER_DEBUG", " YES ")
    assert models._env_flag("C_PARSER_DEBUG")
    monkeypatch.delenv("C_PARSER_DEBUG")
    assert not models._env_flag("C_PARSER_DEBUG")

    assert models._apply_color("value", "red", "bold", enabled=False) == "value"
    assert models._apply_color("value", "red", "bold", enabled=True) == "\x1b[31m\x1b[1mvalue\x1b[0m"

    calls = []
    colorama = SimpleNamespace(just_fix_windows_console=lambda: calls.append("fixed"))
    original_os_name = models.os.name
    monkeypatch.setattr(models.os, "name", "nt")
    try:
        monkeypatch.setitem(models.sys.modules, "colorama", colorama)
        models._enable_windows_ansi()
        assert calls == ["fixed"]

        monkeypatch.delitem(models.sys.modules, "colorama")
        monkeypatch.setattr(importlib.util, "find_spec", lambda name: object() if name == "colorama" else None)
        monkeypatch.setattr(importlib, "import_module", lambda name: colorama if name == "colorama" else None)
        models._enable_windows_ansi()
        assert calls == ["fixed", "fixed"]
    finally:
        monkeypatch.setattr(models.os, "name", original_os_name)


def _make_parse_error(**kwargs):
    return models.CParseError("unexpected token", **kwargs)


def test_c_parse_error_diagnostic_rendering_contract(monkeypatch):
    error = _make_parse_error(filename="bad.h", line_number=2, column=5, source_line="int broken(;\n")
    plain = "bad.h:2:5: error[CPARSE_ERROR]: unexpected token\n  |\n2 | int broken(;\n  |     ^"
    colored = (
        "\x1b[1mbad.h:2:5\x1b[0m: \x1b[31m\x1b[1merror\x1b[0m"
        "\x1b[36m[CPARSE_ERROR]\x1b[0m: unexpected token\n"
        "  \x1b[34m|\x1b[0m\n"
        "\x1b[34m2\x1b[0m \x1b[34m|\x1b[0m int broken(;\n"
        "  \x1b[34m|\x1b[0m \x1b[31m\x1b[1m    ^\x1b[0m"
    )

    assert str(error) == plain
    assert error.format_diagnostic(color=False, debug=False) == plain
    assert error.format_diagnostic(color=True, debug=False) == colored
    assert error.parser_file is not None
    assert error.parser_line_number > 0
    assert error.parser_function is not None

    monkeypatch.setenv("C_PARSER_DEBUG", "yes")
    assert "note: parser raised at" in error.format_diagnostic(color=False)
    colored_debug = error.format_diagnostic(color=True, debug=True)
    assert "\x1b[36mnote: parser raised at " in colored_debug
    assert colored_debug.endswith("()\x1b[0m")

    default_column = _make_parse_error(filename="bad.h", line_number=4, source_line="x")
    assert default_column.format_diagnostic(debug=False).startswith("bad.h:4:1:")

    unknown = _make_parse_error(source_line="value X\n")
    assert unknown.format_diagnostic(debug=False) == (
        "<unknown>: error[CPARSE_ERROR]: unexpected token\n  |\n? | value X\n  | ^"
    )

    blank = _make_parse_error(source_line="   ")
    assert blank.format_diagnostic(debug=False) == (
        "<unknown>: error[CPARSE_ERROR]: unexpected token\n  |\n? |    \n  | "
    )


def test_c_model_to_dict_preserves_seen_aggregates_through_dicts():
    node = models.CStruct(name="node")

    assert models.c_model_to_dict({"first": node, "again": node})["again"] == {"reference": "struct node"}


def test_c_parse_error_uses_immediate_stack_frame(monkeypatch):
    frames = [
        None,
        SimpleNamespace(filename="parser.py", lineno=7, function="raise_here"),
        SimpleNamespace(filename="caller.py", lineno=9, function="caller"),
    ]
    monkeypatch.setattr(models.inspect, "stack", lambda: frames)

    error = models.CParseError("invalid")

    assert (error.parser_file, error.parser_line_number, error.parser_function) == ("parser.py", 7, "raise_here")


def test_callback_candidate_requires_function_type_after_pointer():
    callback_before_pointer = models.CComposedType(components=[models.CFunctionType(), models.CPointer()])

    assert not models.CVariable(name="value", type=callback_before_pointer).callback_candidate
    assert not models.CParameter(name="value", type=callback_before_pointer).callback_candidate
