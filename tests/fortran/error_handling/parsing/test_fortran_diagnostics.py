import pytest

from prik.parsers.fortran import FortranParseError, parse_fortran_file


# ---------------------------------------------------------------------------
# FortranParseError attributes
# ---------------------------------------------------------------------------


def test_parse_error_carries_filename():
    code = """
subroutine bad(x)
  weirdtype :: x
end subroutine bad
"""
    with pytest.raises(FortranParseError) as exc_info:
        parse_fortran_file(code, filename="bad.f90")
    err = exc_info.value
    assert err.filename == "bad.f90"
    assert err.line_number is not None
    assert err.source_line is not None


def test_parse_error_message_includes_filename_and_lineno():
    code = """
subroutine bad(x)
  weirdtype :: x
end subroutine bad
"""
    with pytest.raises(FortranParseError) as exc_info:
        parse_fortran_file(code, filename="myfile.f90")
    msg = str(exc_info.value)
    assert "myfile.f90:3:1" in msg
    assert "error[PARSE_UNSUPPORTED_DECLARATION]" in msg


def test_parse_error_message_includes_source_line():
    code = """
subroutine bad(x)
  weirdtype :: x
end subroutine bad
"""
    with pytest.raises(FortranParseError) as exc_info:
        parse_fortran_file(code, filename="myfile.f90")
    msg = str(exc_info.value)
    assert "weirdtype" in msg


def test_parse_error_without_filename_has_no_location_prefix():
    code = """
subroutine bad(x)
  weirdtype :: x
end subroutine bad
"""
    with pytest.raises(FortranParseError) as exc_info:
        parse_fortran_file(code)
    msg = str(exc_info.value)
    assert "Unknown or unsupported datatype" in msg


def test_parse_error_formats_compiler_style_diagnostic():
    code = """
subroutine bad(x)
  weirdtype :: x
end subroutine bad
"""
    with pytest.raises(FortranParseError) as exc_info:
        parse_fortran_file(code, filename="myfile.f90")

    diagnostic = exc_info.value.format_diagnostic(color=False)
    assert "myfile.f90:3:1: error[PARSE_UNSUPPORTED_DECLARATION]:" in diagnostic
    assert "Unknown or unsupported datatype" in diagnostic
    assert "3 |   weirdtype :: x" in diagnostic
    assert "| ^" in diagnostic


def test_parse_error_formats_color_diagnostic():
    err = FortranParseError("bad token", filename="bad.f90", line_number=7, source_line="  bad token")

    diagnostic = err.format_diagnostic(color=True)

    assert "\033[" in diagnostic
    assert "bad.f90:7:1" in diagnostic
    assert "error" in diagnostic


def test_parse_error_debug_mode_includes_internal_parser_location(monkeypatch):
    err = FortranParseError("bad token", filename="bad.f90", line_number=7, source_line="  bad token")

    diagnostic = err.format_diagnostic(color=False, debug=True)

    assert "note: parser raised at" in diagnostic
    assert "test_parse_error_debug_mode_includes_internal_parser_location" in diagnostic

    monkeypatch.setenv("FORTRAN_PARSER_DEBUG", "1")
    assert "note: parser raised at" in err.format_diagnostic(color=False)


def test_duplicate_argument_error_includes_procedure_header_context():
    code = """subroutine dup(x, y, x)
  integer, intent(in) :: x
  real, intent(in) :: y
end subroutine dup
"""
    with pytest.raises(FortranParseError) as exc_info:
        parse_fortran_file(code, filename="dup_arg.f90")

    diagnostic = exc_info.value.format_diagnostic(color=False)
    assert "dup_arg.f90:1:1" in diagnostic
    assert "1 | subroutine dup(x, y, x)" in diagnostic


def test_parse_error_is_subclass_of_value_error():
    code = """
subroutine bad(x)
  weirdtype :: x
end subroutine bad
"""
    with pytest.raises(ValueError):
        parse_fortran_file(code, filename="bad.f90")
