"""C parser diagnostic rendering, including color and source locations."""

import prik.parsers.c.models as models


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
