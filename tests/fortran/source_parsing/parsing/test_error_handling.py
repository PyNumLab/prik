import pytest

from x2py import FortranParseError, parse_fortran_file


# ---------------------------------------------------------------------------
# FortranParseError attributes
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Duplicate declaration errors
# ---------------------------------------------------------------------------


def test_duplicate_declaration_raises_parse_error():
    code = """
subroutine dup(x)
  real :: x
  integer :: x
end subroutine dup
"""
    with pytest.raises(FortranParseError, match="Duplicate declaration"):
        parse_fortran_file(code, filename="dup.f90")


def test_duplicate_function_result_raises_parse_error():
    code = """
real function f(x)
  real :: x
  real :: f
end function f
"""
    with pytest.raises(FortranParseError, match="Duplicate declaration"):
        parse_fortran_file(code, filename="dup_result.f90")


def test_duplicate_function_result_with_result_keyword_raises_parse_error():
    code = """
real function f(x) result(res)
  real :: x
  real :: res
end function f
"""
    with pytest.raises(FortranParseError, match="Duplicate declaration"):
        parse_fortran_file(code, filename="dup_result_kw.f90")


def test_duplicate_initialized_declaration_raises_parse_error():
    code = """
subroutine dup_init()
  integer :: x = 1
  integer :: x = 2
end subroutine dup_init
"""
    with pytest.raises(FortranParseError, match="Duplicate declaration"):
        parse_fortran_file(code, filename="dup_init.f90")


# ---------------------------------------------------------------------------
# Duplicate procedure name errors
# ---------------------------------------------------------------------------


def test_duplicate_procedure_name_global_scope_raises_parse_error():
    code = """
subroutine work(n)
  integer, intent(in) :: n
end subroutine work

function work(n) result(out)
  integer, intent(in) :: n
  integer :: out
end function work
"""
    with pytest.raises(FortranParseError, match="Duplicate procedure name"):
        parse_fortran_file(code, filename="dup_proc.f90")


def test_duplicate_procedure_name_in_module_raises_parse_error():
    code = """
module m
contains
  subroutine work(n)
    integer, intent(in) :: n
  end subroutine work
  function work(n) result(out)
    integer, intent(in) :: n
    integer :: out
  end function work
end module m
"""
    with pytest.raises(FortranParseError, match="Duplicate procedure name"):
        parse_fortran_file(code, filename="dup_mod_proc.f90")


def test_contained_procedures_with_same_name_in_different_hosts_are_allowed():
    code = """
module m
contains
  subroutine host_a()
  contains
    subroutine swap_order()
    end subroutine swap_order
  end subroutine host_a

  subroutine host_b()
  contains
    subroutine swap_order()
    end subroutine swap_order
  end subroutine host_b
end module m
"""
    parsed = parse_fortran_file(code, filename="contained_scope_ok.f90")
    assert [sig.name.lower() for sig in parsed.modules[0].procedures] == ["host_a", "host_b"]


def test_duplicate_procedure_name_error_carries_location():
    code = """
subroutine work(n)
  integer, intent(in) :: n
end subroutine work

subroutine work(n)
  integer, intent(in) :: n
end subroutine work
"""
    with pytest.raises(FortranParseError) as exc_info:
        parse_fortran_file(code, filename="dup.f90")
    err = exc_info.value
    assert err.filename == "dup.f90"
    assert err.line_number is not None


# ---------------------------------------------------------------------------
# Star-kind declarations
# ---------------------------------------------------------------------------


def test_star_kind_in_modern_source_is_parsed():
    code = """
subroutine bad(x)
  real*8 :: x
end subroutine bad
"""
    proc = parse_fortran_file(code, filename="bad.f90").procedures[0]
    assert proc.arguments[0].base_type == "real"
    assert proc.arguments[0].kind == "8"


def test_star_kind_in_module_variable_is_parsed():
    code = """
module m
  real*8 :: x
end module m
"""
    var = parse_fortran_file(code, filename="bad.f90").modules[0].variables[0]
    assert var.base_type == "real"
    assert var.kind == "8"


# ---------------------------------------------------------------------------
# Unknown/unsupported type declaration errors
# ---------------------------------------------------------------------------


def test_unknown_type_in_subroutine_raises_parse_error():
    code = """
subroutine bad(x)
  weirdtype :: x
end subroutine bad
"""
    with pytest.raises(FortranParseError, match="Unknown or unsupported datatype"):
        parse_fortran_file(code, filename="bad.f90")


def test_unknown_type_in_module_variable_raises_parse_error():
    code = """
module m
  weirdtype :: x
end module m
"""
    with pytest.raises(FortranParseError, match="Unknown or unsupported datatype"):
        parse_fortran_file(code, filename="bad.f90")


def test_unknown_type_in_interface_raises_parse_error():
    code = """
module m
  interface foo
    subroutine bar(x)
      weirdtype :: x
    end subroutine bar
  end interface
end module m
"""
    with pytest.raises(FortranParseError, match="Unknown or unsupported datatype"):
        parse_fortran_file(code, filename="bad.f90")


# ---------------------------------------------------------------------------
# Module variable type validation
# ---------------------------------------------------------------------------


def test_module_variable_with_unknown_type_raises_parse_error():
    code = """
module m
  integer :: n
end module m
"""
    parsed = parse_fortran_file(code)
    assert parsed.modules[0].variables[0].base_type == "integer"


def test_module_variable_parsed_correctly_no_error():
    code = """
module cfg
  real(kind=8) :: tolerance
  integer :: max_iter
  logical :: verbose
end module cfg
"""
    parsed = parse_fortran_file(code)
    assert len(parsed.modules[0].variables) == 3
    assert parsed.modules[0].variables[0].base_type == "real"
    assert parsed.modules[0].variables[1].base_type == "integer"
    assert parsed.modules[0].variables[2].base_type == "logical"


# ---------------------------------------------------------------------------
# Derived type field type validation
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Parameter symbol errors
# ---------------------------------------------------------------------------


def test_parameter_without_type_in_implicit_none_scope_raises_parse_error():
    code = """
      subroutine cst(a)
      implicit none
      real a
      parameter ( zero = 0.0e+0 )
      end
"""
    with pytest.raises(FortranParseError, match="Unknown datatype for PARAMETER symbol"):
        parse_fortran_file(code, filename="legacy.f")


def test_duplicate_parameter_declaration_raises_parse_error():
    code = """
subroutine dup_param()
  integer, parameter :: n = 5
  integer, parameter :: n = 10
end subroutine dup_param
"""
    with pytest.raises(FortranParseError, match="Duplicate PARAMETER declaration"):
        parse_fortran_file(code, filename="dup_param.f90")


# ---------------------------------------------------------------------------
# Mixed-era source forms
# ---------------------------------------------------------------------------


def test_f77_source_with_module_keyword_is_parsed():
    code = """
      module bad_module
      end module bad_module
"""
    parsed = parse_fortran_file(code, filename="legacy.f77")
    assert parsed.format == "f77"
    assert parsed.modules[0].name == "bad_module"


def test_f77_source_file_metadata_is_preserved():
    code = """
      module bad_module
      end module bad_module
"""
    parsed = parse_fortran_file(code, filename="legacy.f77")
    assert parsed.filename == "legacy.f77"


# ---------------------------------------------------------------------------
# Function result type errors
# ---------------------------------------------------------------------------


def test_function_with_implicit_none_and_missing_result_type_raises():
    code = """
function f(x) result(res)
  implicit none
  real :: x
end function f
"""
    with pytest.raises(FortranParseError, match=r"has no type declaration|Unknown datatype for function result"):
        parse_fortran_file(code, filename="bad.f90")


# ---------------------------------------------------------------------------
# Error location accuracy
# ---------------------------------------------------------------------------


def test_error_reports_correct_line_number():
    code = "subroutine foo(x)\n  integer :: x\n  weirdtype :: y\nend subroutine foo\n"
    with pytest.raises(FortranParseError) as exc_info:
        parse_fortran_file(code, filename="foo.f90")
    err = exc_info.value
    assert err.line_number == 3


def test_error_reports_source_line_content():
    code = "subroutine foo(x)\n  integer :: x\n  weirdtype :: y\nend subroutine foo\n"
    with pytest.raises(FortranParseError) as exc_info:
        parse_fortran_file(code, filename="foo.f90")
    err = exc_info.value
    assert "weirdtype" in (err.source_line or "")


# ---------------------------------------------------------------------------
# Duplicate argument name errors
# ---------------------------------------------------------------------------


def test_duplicate_argument_name_in_subroutine_raises_parse_error():
    code = """
subroutine dup(x, y, x)
  integer, intent(in) :: x
  real, intent(in) :: y
end subroutine dup
"""
    with pytest.raises(FortranParseError, match="Duplicate argument name"):
        parse_fortran_file(code, filename="dup_arg.f90")


def test_duplicate_argument_name_in_function_raises_parse_error():
    code = """
function f(a, b, a) result(res)
  integer, intent(in) :: a
  real, intent(in) :: b
  integer :: res
end function f
"""
    with pytest.raises(FortranParseError, match="Duplicate argument name"):
        parse_fortran_file(code, filename="dup_arg_func.f90")


# ---------------------------------------------------------------------------
# Implicit none: undeclared arguments
# ---------------------------------------------------------------------------


def test_implicit_none_undeclared_arg_raises_parse_error():
    code = """
subroutine foo(x, y)
  implicit none
  integer, intent(in) :: x
end subroutine foo
"""
    with pytest.raises(FortranParseError, match="has no type declaration"):
        parse_fortran_file(code, filename="implicit_none.f90")


def test_implicit_none_all_args_declared_no_error():
    code = """
subroutine foo(x, y)
  implicit none
  integer, intent(in) :: x
  real, intent(out) :: y
end subroutine foo
"""
    parsed = parse_fortran_file(code, filename="ok.f90")
    assert len(parsed.procedures) == 1
    assert all(a.base_type != "unknown" for a in parsed.procedures[0].arguments)


def test_implicit_none_undeclared_function_result_raises_parse_error():
    code = """
function f(x)
  implicit none
  integer, intent(in) :: x
end function f
"""
    with pytest.raises(FortranParseError, match=r"has no type declaration|Unknown datatype for function result"):
        parse_fortran_file(code, filename="implicit_none_func.f90")


# ---------------------------------------------------------------------------
# Function result validation
# ---------------------------------------------------------------------------


def test_function_result_shadowing_arg_name_raises_parse_error():
    code = """
function f(res) result(res)
  integer, intent(in) :: res
end function f
"""
    with pytest.raises(FortranParseError, match="shadows an argument name"):
        parse_fortran_file(code, filename="shadow.f90")


def test_function_with_explicit_result_clause_no_error():
    code = """
function f(x) result(out)
  implicit none
  integer, intent(in) :: x
  integer :: out
end function f
"""
    parsed = parse_fortran_file(code, filename="ok.f90")
    assert len(parsed.procedures) == 1
    assert parsed.procedures[0].result is not None
    assert parsed.procedures[0].result.name == "out"
    assert parsed.procedures[0].result.base_type == "integer"


# ---------------------------------------------------------------------------
# Derived type duplicate field names
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Module duplicate variable names
# ---------------------------------------------------------------------------


def test_duplicate_variable_in_module_raises_parse_error():
    code = """
module m
  integer :: n
  real :: n
end module m
"""
    with pytest.raises(FortranParseError, match="Duplicate variable"):
        parse_fortran_file(code, filename="dup_var.f90")


def test_module_unique_variables_no_error():
    code = """
module m
  integer :: n
  real :: x
  logical :: flag
end module m
"""
    parsed = parse_fortran_file(code, filename="ok.f90")
    assert len(parsed.modules[0].variables) == 3


def test_duplicate_variable_in_program_raises_parse_error():
    code = """
program main
  integer n
  real n
end program main
"""
    with pytest.raises(FortranParseError, match=r"Duplicate variable.*program"):
        parse_fortran_file(code, filename="dup_program_var.f90")


def test_duplicate_variable_in_block_data_raises_parse_error():
    code = """
      block data init_data
      integer n
      real n
      end
"""
    with pytest.raises(FortranParseError, match=r"Duplicate variable.*block data"):
        parse_fortran_file(code, filename="dup_block_data_var.f")


def test_same_level_duplicate_modules_raise_parse_error():
    code = """
module same_name
end module same_name

module same_name
end module same_name
"""
    with pytest.raises(FortranParseError, match="Duplicate module name 'same_name' in file scope"):
        parse_fortran_file(code, filename="dup_modules.f90")


def test_slicer_reports_mismatched_end_unit_name():
    code = """
module expected_name
end module wrong_name
"""
    with pytest.raises(FortranParseError, match="Mismatched end module name 'wrong_name' for module 'expected_name'"):
        parse_fortran_file(code, filename="mismatch_module.f90")


def test_slicer_accepts_mismatched_procedure_end_name_without_preferred_alternative():
    parsed = parse_fortran_file(
        """
subroutine expected_name()
end subroutine alternate_name
""",
        filename="mismatch_procedure_raw_alternative.f90",
    )

    assert parsed.procedures[0].name == "expected_name"


def test_slicer_reports_missing_end_unit():
    code = """
module missing_end
  integer :: n
"""
    with pytest.raises(FortranParseError, match="Missing end module for module 'missing_end'"):
        parse_fortran_file(code, filename="missing_end_module.f90")


@pytest.mark.parametrize(
    "code",
    [
        "int add(int a, int b);\n",
        "api_size count(void);\n",
        """
subroutine mixed_spec()
  api_size count(void);
end subroutine mixed_spec
""",
    ],
)
def test_fortran_parser_rejects_invalid_non_fortran_syntax_outside_execution_bodies(code):
    with pytest.raises(
        FortranParseError,
        match=r"Invalid Fortran syntax|Unknown or unsupported datatype declaration",
    ) as exc_info:
        parse_fortran_file(code, filename="mixed.f90")

    assert exc_info.value.code in {"PARSE_INVALID_SYNTAX", "PARSE_UNSUPPORTED_DECLARATION"}


def test_fortran_parser_ignores_non_fortran_syntax_after_execution_boundary():
    parsed = parse_fortran_file(
        """
subroutine mixed_body()
  call noop()
  api_size count(void);
end subroutine mixed_body
""",
        filename="mixed_body.f90",
    )

    assert parsed.procedures[0].name == "mixed_body"


@pytest.mark.parametrize(
    "code",
    [
        "@@@\n",
        """
module bad_spec
  @@@
end module bad_spec
""",
        """
subroutine bad_spec()
  @@@
end subroutine bad_spec
""",
    ],
)
def test_fortran_parser_rejects_invalid_syntax_outside_execution_bodies(code):
    with pytest.raises(FortranParseError, match="Invalid Fortran syntax") as exc_info:
        parse_fortran_file(code, filename="invalid_syntax.f90")

    assert exc_info.value.code == "PARSE_INVALID_SYNTAX"


def test_fortran_parser_ignores_invalid_syntax_after_execution_boundary():
    parsed = parse_fortran_file(
        """
subroutine ignored_body()
  call noop()
  @@@
end subroutine ignored_body
""",
        filename="invalid_body.f90",
    )

    assert parsed.procedures[0].name == "ignored_body"


def test_fortran_parser_skips_standalone_include_fragment_after_execution_boundary():
    parsed = parse_fortran_file(
        """
include 'fragment.inc'
if (enabled) then
  @@@
else
  @@@
endif
""",
        filename="fragment.inc",
    )

    assert parsed.procedures == []


def test_fortran_parser_skips_balanced_internal_procedure_contents():
    parsed = parse_fortran_file(
        """
subroutine host()
contains
  subroutine nested()
    @@@
  end subroutine nested
end subroutine host
""",
        filename="ignored_internal_body.f90",
    )

    assert parsed.procedures[0].name == "host"


def test_fortran_parser_rejects_unterminated_internal_procedure_unit():
    with pytest.raises(FortranParseError, match="Missing end procedure"):
        parse_fortran_file(
            """
subroutine host()
contains
  subroutine nested()
end subroutine host
""",
            filename="unterminated_internal_unit.f90",
        )


def test_fortran_parser_skips_nested_unit_like_lines_after_execution_boundary():
    parsed = parse_fortran_file(
        """
subroutine host()
  call begin_work()
  interface
    subroutine ignored()
      @@@
    end subroutine ignored
  end interface
end subroutine host
""",
        filename="ignored_nested_execution.f90",
    )

    assert parsed.procedures[0].name == "host"


def test_fortran_parser_skips_unterminated_unit_like_lines_after_execution_boundary():
    parsed = parse_fortran_file(
        """
subroutine host()
  call begin_work()
  subroutine ignored()
end subroutine host
""",
        filename="ignored_unterminated_nested_execution.f90",
    )

    assert parsed.procedures[0].name == "host"


def test_fortran_parser_rejects_subunit_inside_block_data():
    with pytest.raises(FortranParseError, match="Invalid Fortran syntax") as exc_info:
        parse_fortran_file(
            """
block data invalid_block
  interface
  end interface
end block data invalid_block
""",
            filename="invalid_block_data.f90",
        )

    assert exc_info.value.code == "PARSE_INVALID_SYNTAX"


def test_invalid_syntax_guard_preserves_valid_semicolon_separated_fortran_statements():
    parsed = parse_fortran_file(
        """
subroutine valid_body(x)
  real :: x
  call update(x); write(*,*) x
end subroutine valid_body
""",
        filename="valid_body.f90",
    )

    assert parsed.procedures[0].name == "valid_body"
