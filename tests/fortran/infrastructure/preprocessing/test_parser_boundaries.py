"""Preprocessor selection and declaration/execution boundary handling."""

import pytest

from prik.parsers.fortran import FortranParseError, parse_fortran_file


def test_fortran_lexer_strip_comment_preserves_directives_and_quoted_bangs():
    from prik.parsers.fortran.lexer import strip_comment

    assert strip_comment("  !$OMP parallel do", "free") == "!$OMP parallel do"
    assert strip_comment("C$OMP PARALLEL DO", "fixed") == "!$omp PARALLEL DO"
    assert strip_comment("*$omp end parallel do", "fixed") == "!$omp end parallel do"
    assert strip_comment("#ifdef USE_FAST", "fixed") == "#ifdef USE_FAST"
    assert strip_comment("   #ifdef USE_FAST", "fixed") == "   #ifdef USE_FAST"
    assert strip_comment("   #define BANG !", "fixed") == "   #define BANG !"
    assert strip_comment("c ordinary comment", "fixed") == ""
    assert strip_comment("C ordinary comment", "fixed") == ""
    assert strip_comment("* ordinary comment", "fixed") == ""
    assert strip_comment("! ordinary comment", "fixed") == ""
    assert strip_comment("print *, 'kept ! text' ! removed", "free") == "print *, 'kept ! text' "
    assert strip_comment('print *, "kept ! text" ! removed', "free") == 'print *, "kept ! text" '
    assert strip_comment("""print *, 'kept " ! text' ! removed""", "free") == """print *, 'kept " ! text' """


def test_fortran_lexer_preprocess_lines_folds_free_and_fixed_continuations():
    from prik.parsers.fortran.lexer import preprocess_lines

    free = "alpha = one &\n  & + two ! removed\n\nbeta = 3\n! removed\n"
    assert preprocess_lines(free, filename="free.f90") == [
        ("alpha = one+ two", 1, "alpha = one &"),
        ("beta = 3", 4, "beta = 3"),
    ]
    assert preprocess_lines("alpha = one&\n&two\n", filename="free.f90") == [
        ("alpha = onetwo", 1, "alpha = one&"),
    ]
    assert preprocess_lines("alpha = X\nbeta = 1  \n", filename="free.f90") == [
        ("alpha = X", 1, "alpha = X"),
        ("beta = 1", 2, "beta = 1  "),
    ]

    fixed = "      alpha = one\n     1 + two\nC comment\n      beta = 3\n"
    assert preprocess_lines(fixed, filename="fixed.f") == [
        ("alpha = one + two", 1, "      alpha = one"),
        ("beta = 3", 4, "      beta = 3"),
    ]
    assert preprocess_lines("      alpha = one\n\n     1x\n\n     1y\n", filename="fixed.f") == [
        ("alpha = one x y", 1, "      alpha = one"),
    ]
    assert preprocess_lines("      alpha = one\n!$omp parallel do\n      beta = 3\n", filename="fixed.f") == [
        ("alpha = one", 1, "      alpha = one"),
        ("!$omp parallel do", 2, "!$omp parallel do"),
        ("beta = 3", 3, "      beta = 3"),
    ]


@pytest.mark.parametrize(
    ("filename", "code"),
    [
        pytest.param("raw_cpp.F90", "#if USE_FAST\nsubroutine selected()\nend subroutine selected\n", id="if"),
        pytest.param("raw_cpp.F90", "#ifdef USE_FAST\nsubroutine selected()\nend subroutine selected\n", id="ifdef"),
        pytest.param(
            "raw_cpp.F90", "#define USE_FAST 1\nsubroutine selected()\nend subroutine selected\n", id="define"
        ),
        pytest.param(
            "raw_cpp.F90", '#include "api.inc"\nsubroutine selected()\nend subroutine selected\n', id="include"
        ),
        pytest.param(
            "raw_cpp.F",
            "#ifdef USE_FAST\n      subroutine selected()\n      end\n#endif\n",
            id="fixed-form-before-comment-handling",
        ),
    ],
)
def test_cpp_directives_require_compiler_preprocessing(filename, code):
    with pytest.raises(FortranParseError, match="require compiler preprocessing") as exc_info:
        parse_fortran_file(code, filename=filename)

    assert exc_info.value.code == "PARSE_PREPROCESSING_REQUIRED"
    assert exc_info.value.line_number == 1


@pytest.mark.parametrize(
    ("filename", "code"),
    [
        pytest.param(
            "preprocessed.F90",
            '# 40 "include/api.inc" 1\nsubroutine selected()\nend subroutine selected\n',
            id="free-form",
        ),
        pytest.param("preprocessed.F", '# 1 "api.F"\n      subroutine selected()\n      end\n', id="fixed-form"),
    ],
)
def test_compiler_linemarkers_remain_parseable_for_provenance(filename, code):
    parsed = parse_fortran_file(code, filename=filename)

    assert [procedure.name for procedure in parsed.procedures] == ["selected"]


def test_include_and_ignored_spec_lines_do_not_change_public_signature():
    code = """
subroutine legacy_specs(x)
  include 'params.inc'
  intrinsic abs
  save
  common /blk/ tmp
  data tmp /0.0/
  equivalence (tmp, x)
  format(1x, f8.3)
  real, intent(inout) :: x
  real :: tmp
end subroutine legacy_specs
"""

    sig = parse_fortran_file(code, filename="legacy_specs.f90").procedures[0]

    assert [arg.name for arg in sig.arguments] == ["x"]
    assert sig.arguments[0].base_type == "real"
    assert sig.common_variables == ["tmp"]


@pytest.mark.parametrize(
    ("code", "unit_kind", "expected"),
    [
        (
            """
module common_mod
  real :: value, values(4)
  logical :: flag
  common /shared/ value, values /other/ flag
end module common_mod
""",
            "module",
            ["value", "values", "flag"],
        ),
        (
            """
subroutine common_proc()
  real :: value, values(4)
  logical :: flag
  common /shared/ value, values /other/ flag
end subroutine common_proc
""",
            "procedure",
            ["value", "values", "flag"],
        ),
    ],
)
def test_common_block_members_are_recorded_for_non_export(code, unit_kind, expected):
    parsed = parse_fortran_file(code, filename="common_block.f90")
    unit = parsed.modules[0] if unit_kind == "module" else parsed.procedures[0]

    assert unit.common_variables == expected


def test_execution_part_boundaries_and_local_types_are_not_misread_as_declarations():
    code = """
subroutine exec_edges(x)
  real, intent(inout) :: x
  integer :: i
  type scratch_t
    integer :: id
  end type scratch_t
  x = x + 1.0
  go to 10
10 continue
  call noop()
end subroutine exec_edges
"""

    sig = parse_fortran_file(code).procedures[0]

    assert [arg.name for arg in sig.arguments] == ["x"]
    assert sig.arguments[0].base_type == "real"
    assert "i" not in sig.variables


def test_program_execution_part_is_ignored_after_first_executable_statement():
    code = """
program driver
  use iso_fortran_env
  integer :: ierr
  write(*,*) "running"
  maybe_decl looking_body_statement
contains
  subroutine inner()
  end subroutine inner
end program driver
"""

    program = parse_fortran_file(code, filename="driver.f90").programs[0]

    assert [var.name for var in program.variables] == ["ierr"]


def test_statement_function_and_numeric_label_before_execution_part():
    code = """
subroutine old_style(x)
  real x
  real f
10 continue
  f(x) = x + 1.0
end subroutine old_style
"""

    sig = parse_fortran_file(code, filename="old_style.f90").procedures[0]

    assert sig.arguments[0].base_type == "real"


def test_implicit_mapping_parameter_noise_and_assignment_lines_do_not_break_procedure_parse():
    code = """
subroutine declaration_noise(x)
  implicit real(a-h,o-z)
  integer, parameter :: n = 3, ignored_token
  parameter (m = 4, malformed_token)
  x = 1.0
  real x
end subroutine declaration_noise
"""

    sig = parse_fortran_file(code, filename="declaration_noise.f90").procedures[0]

    assert sig.arguments[0].name == "x"
    assert sig.arguments[0].base_type == "real"
