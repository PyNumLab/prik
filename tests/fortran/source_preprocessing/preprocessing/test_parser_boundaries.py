"""Preprocessor selection and declaration/execution boundary handling."""

import ast
from dataclasses import replace
import re

import pytest

from x2py import FortranParseError, parse_fortran_file


def test_fortran_lexer_strip_comment_preserves_directives_and_quoted_bangs():
    from x2py.parsers.fortran.lexer import strip_comment

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
    from x2py.parsers.fortran.lexer import preprocess_lines

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


def collect_signature_shape_symbols(signature):
    symbols = set()
    for arg in signature.arguments:
        for dim in arg.shape:
            symbols.update(re.findall(r"[A-Za-z_]\w*", dim))
    return symbols


def evaluate_signature_shapes(signature, symbol_values=None):
    symbol_values = symbol_values or {}
    out = replace(signature)
    out.arguments = [replace(a) for a in signature.arguments]

    def fold_integer_expr(text):
        try:
            tree = ast.parse(text, mode="eval")
        except SyntaxError:
            return text
        allowed = (
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Constant,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.Pow,
            ast.USub,
            ast.UAdd,
        )
        if any(not isinstance(node, allowed) for node in ast.walk(tree)):
            return text
        value = eval(compile(tree, "<shape>", "eval"), {"__builtins__": {}}, {})
        return str(int(value)) if isinstance(value, int | float) and value == int(value) else text

    for arg in out.arguments:
        arg.shape = list(arg.shape)
        for index, dim in enumerate(arg.shape):
            for key, value in symbol_values.items():
                dim = re.sub(rf"\b{re.escape(str(key))}\b", str(value), dim, flags=re.IGNORECASE)
            if ":" in dim:
                dim = ":".join(fold_integer_expr(part) if part.strip() else part for part in dim.split(":"))
            else:
                dim = fold_integer_expr(dim)
            arg.shape[index] = dim
    return out


def test_signature_shape_helpers_evaluate_publicly_parsed_signature():
    code = """
subroutine fill(a)
  real, intent(inout) :: a(0:nx-1, 1:ny)
end subroutine fill
"""

    sig = parse_fortran_file(code).procedures[0]

    assert collect_signature_shape_symbols(sig) == {"nx", "ny"}
    evaluated = evaluate_signature_shapes(sig, {"NX": 4, "ny": 3})
    assert evaluated.arguments[0].shape == ["0:3", "1:3"]
    assert sig.arguments[0].shape == ["0:nx-1", "1:ny"]


@pytest.mark.parametrize("directive", ["#if USE_FAST", "#ifdef USE_FAST", "#define USE_FAST 1", '#include "api.inc"'])
def test_cpp_directives_require_compiler_preprocessing(directive):
    code = f"{directive}\nsubroutine selected()\nend subroutine selected\n"

    with pytest.raises(FortranParseError, match="require compiler preprocessing") as exc_info:
        parse_fortran_file(code, filename="raw_cpp.F90")

    assert exc_info.value.code == "PARSE_PREPROCESSING_REQUIRED"
    assert exc_info.value.line_number == 1


def test_compiler_linemarkers_remain_parseable_for_provenance():
    code = '# 40 "include/api.inc" 1\nsubroutine selected()\nend subroutine selected\n'

    parsed = parse_fortran_file(code, filename="preprocessed.F90")

    assert [procedure.name for procedure in parsed.procedures] == ["selected"]


def test_fixed_form_cpp_directives_are_rejected_before_comment_handling():
    code = "#ifdef USE_FAST\n      subroutine selected()\n      end\n#endif\n"

    with pytest.raises(FortranParseError, match="require compiler preprocessing") as exc_info:
        parse_fortran_file(code, filename="raw_cpp.F")

    assert exc_info.value.code == "PARSE_PREPROCESSING_REQUIRED"
    assert exc_info.value.line_number == 1


def test_fixed_form_compiler_linemarkers_are_removed_before_lexing():
    code = '# 1 "api.F"\n      subroutine selected()\n      end\n'

    parsed = parse_fortran_file(code, filename="preprocessed.F")

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


def test_executable_statement_in_module_spec_part_raises():
    code = """
module bad_exec_mod
  write(*,*) "not allowed"
end module bad_exec_mod
"""

    with pytest.raises(FortranParseError, match="Executable statement is not allowed"):
        parse_fortran_file(code, filename="bad_exec_mod.f90")


def test_openmp_declarative_directives_raise_but_executable_directives_are_body_lines():
    declarative = """
module omp_mod
  integer :: state
!$omp threadprivate(state)
end module omp_mod
"""
    executable = """
subroutine omp_body(x)
  integer, intent(inout) :: x
!$omp parallel do
  do i = 1, x
    x = x + i
  end do
end subroutine omp_body
"""
    proc_declarative = """
subroutine omp_decl(x)
!$omp declare simd
  integer, intent(inout) :: x
end subroutine omp_decl
"""
    type_declarative = """
module omp_type_mod
  type :: state
!$omp declare target
    integer :: value
  end type state
end module omp_type_mod
"""
    module_executable = """
module bad_omp_mod
!$omp parallel
end module bad_omp_mod
"""
    fixed_form_executable = """
      subroutine fixed_omp(n)
      integer n
C$OMP PARALLEL DO
      do 10 i = 1, n
10    continue
      end
"""

    with pytest.raises(FortranParseError, match="Unsupported OpenMP declarative directive"):
        parse_fortran_file(declarative, filename="omp_mod.f90")
    with pytest.raises(FortranParseError, match="Unsupported OpenMP declarative directive"):
        parse_fortran_file(proc_declarative, filename="omp_decl.f90")
    with pytest.raises(FortranParseError, match="Unsupported OpenMP declarative directive"):
        parse_fortran_file(type_declarative, filename="omp_type.f90")
    with pytest.raises(FortranParseError, match="Executable statement is not allowed"):
        parse_fortran_file(module_executable, filename="bad_omp_mod.f90")
    assert parse_fortran_file(executable, filename="omp_body.f90").procedures[0].name == "omp_body"
    assert parse_fortran_file(fixed_form_executable, filename="fixed_omp.f").procedures[0].name == "fixed_omp"


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


def test_stray_end_unit_lines_are_rejected_by_public_file_parse():
    with pytest.raises(FortranParseError, match="Invalid Fortran syntax") as exc_info:
        parse_fortran_file(
            """
end module stray_mod
end submodule stray_submod
end program stray_program
end interface

subroutine kept()
end subroutine kept
""",
            filename="stray_ends.f90",
        )

    assert exc_info.value.code == "PARSE_INVALID_SYNTAX"
