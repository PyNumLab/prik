"""Parser diagnostics and the boundary where the parser stops reading a unit.

Every rejected source reports a stable error code, a message naming the owning
scope, and, when the parser knows it, the line the user wrote. Content the
parser does not model (execution parts, internal procedure bodies) is skipped
rather than validated.
"""

import pytest

from prik.parsers.fortran import FortranParseError, parse_fortran_file


def _error(filename, source, code, message, line):
    return pytest.param(filename, source, code, message, line)


_DIAGNOSTICS = {
    # Duplicate names, compared case-insensitively within one scope.
    "duplicate-declaration-in-procedure": _error(
        "dup.f90",
        "subroutine dup(x)\n  real :: x\n  integer :: x\nend subroutine dup\n",
        "PARSE_DUPLICATE_DECLARATION",
        "Duplicate declaration of symbol 'x' in procedure 'dup'.",
        3,
    ),
    "duplicate-function-name-result": _error(
        "dup_result.f90",
        "real function f(x)\n  real :: x\n  real :: f\nend function f\n",
        "PARSE_DUPLICATE_DECLARATION",
        "Duplicate declaration of symbol 'f' in procedure 'f'.",
        3,
    ),
    "duplicate-result-clause-variable": _error(
        "dup_result_kw.f90",
        "real function f(x) result(res)\n  real :: x\n  real :: res\nend function f\n",
        "PARSE_DUPLICATE_DECLARATION",
        "Duplicate declaration of symbol 'res' in procedure 'f'.",
        3,
    ),
    "procedure-dummy-retyped": _error(
        "declarations.f90",
        "subroutine apply(callback)\n"
        "  procedure(callback_iface), external :: callback\n"
        "  integer :: callback\n"
        "end subroutine apply\n",
        "PARSE_DUPLICATE_DECLARATION",
        "Duplicate declaration of symbol 'callback' in procedure 'apply'.",
        3,
    ),
    "duplicate-parameter": _error(
        "parameters.f90",
        "subroutine shape()\n  integer, parameter :: n = 4, m = n + 2\n  integer, parameter :: n = 8\nend subroutine shape\n",
        "PARSE_DUPLICATE_PARAMETER",
        "Duplicate PARAMETER declaration of symbol 'n' in procedure 'shape'.",
        3,
    ),
    "duplicate-argument-case-insensitive": _error(
        "dup_arg.f90",
        "subroutine step(value, VALUE)\nend subroutine step\n",
        "PARSE_DUPLICATE_ARGUMENT",
        "Duplicate argument name 'VALUE' in procedure 'step'.",
        1,
    ),
    "duplicate-procedure-global-scope": _error(
        "dup_proc.f90",
        "subroutine work(n)\n  integer, intent(in) :: n\nend subroutine work\n\n"
        "function work(n) result(out)\n  integer, intent(in) :: n\n  integer :: out\nend function work\n",
        "PARSE_DUPLICATE_PROCEDURE",
        "Duplicate procedure name 'work' in global scope.",
        5,
    ),
    "duplicate-procedure-in-module-case-insensitive": _error(
        "dup_mod_proc.f90",
        "module m\ncontains\n  subroutine step()\n  end subroutine step\n"
        "  subroutine STEP()\n  end subroutine STEP\nend module m\n",
        "PARSE_DUPLICATE_PROCEDURE",
        "Duplicate procedure name 'STEP' in module 'm'.",
        5,
    ),
    "duplicate-module-in-file-case-insensitive": _error(
        "dup_modules.f90",
        "module same_name\nend module same_name\n\nmodule Same_Name\nend module Same_Name\n",
        "PARSE_DUPLICATE_UNIT",
        "Duplicate module name 'Same_Name' in file scope.",
        4,
    ),
    "duplicate-field-case-insensitive": _error(
        "dup_field.f90",
        "module m\n  type :: state_t\n    integer, pointer :: ids(:), IDs(:)\n  end type state_t\nend module m\n",
        "PARSE_DUPLICATE_FIELD",
        "Duplicate field 'IDs' in derived type 'state_t'.",
        None,
    ),
    "duplicate-module-variable": _error(
        "dup_var.f90",
        "module m\n  integer :: n\n  real :: n\nend module m\n",
        "PARSE_DUPLICATE_VARIABLE",
        "Duplicate variable 'n' in module 'm'.",
        None,
    ),
    "duplicate-program-variable": _error(
        "dup_program_var.f90",
        "program main\n  integer n\n  real n\nend program main\n",
        "PARSE_DUPLICATE_VARIABLE",
        "Duplicate variable 'n' in program 'main'.",
        None,
    ),
    "duplicate-block-data-variable-fixed-form": _error(
        "dup_block_data_var.f",
        "      block data init_data\n      integer n\n      real n\n      end\n",
        "PARSE_DUPLICATE_VARIABLE",
        "Duplicate variable 'n' in block data 'init_data'.",
        None,
    ),
    # Unknown datatypes in every metadata scope.
    "unknown-type-with-kind-in-procedure": _error(
        "procedure_contract.f90",
        "subroutine work()\n  vector(kind=4) :: value\nend subroutine work\n",
        "PARSE_UNSUPPORTED_DECLARATION",
        "Unknown or unsupported datatype declaration for procedure 'work': vector(kind=4) :: value",
        2,
    ),
    "unknown-type-in-interface-body": _error(
        "bad_iface.f90",
        "module m\n  interface foo\n    subroutine bar(x)\n      weirdtype :: x\n"
        "    end subroutine bar\n  end interface\nend module m\n",
        "PARSE_UNSUPPORTED_DECLARATION",
        "Unknown or unsupported datatype declaration for procedure 'bar': weirdtype :: x",
        4,
    ),
    "unknown-type-in-module": _error(
        "bad_mod.f90",
        "module m\n  weirdtype :: x\nend module m\n",
        "PARSE_UNSUPPORTED_DECLARATION",
        "Unknown or unsupported datatype declaration in module 'm': weirdtype :: x",
        2,
    ),
    "unknown-type-in-module-without-double-colon": _error(
        "bad_mod.f90",
        "module owner_mod\n  weirdtype value\nend module owner_mod\n",
        "PARSE_UNSUPPORTED_DECLARATION",
        "Unknown or unsupported datatype declaration in module 'owner_mod': weirdtype value",
        2,
    ),
    "unknown-type-in-derived-type-without-double-colon": _error(
        "bad_type.f90",
        "module m\n  type :: state_t\n    weirdtype value\n  end type state_t\nend module m\n",
        "PARSE_UNSUPPORTED_DECLARATION",
        "Unknown or unsupported datatype declaration in type 'state_t': weirdtype value",
        3,
    ),
    "c-prototype-in-procedure-specification": _error(
        "mixed.f90",
        "subroutine mixed_spec()\n  api_size count(void);\nend subroutine mixed_spec\n",
        "PARSE_UNSUPPORTED_DECLARATION",
        "Unknown or unsupported datatype declaration for procedure 'mixed_spec': api_size count(void);",
        2,
    ),
    # Implicit typing and function results.
    "implicit-none-undeclared-argument": _error(
        "implicit_none.f90",
        "subroutine foo(x, y)\n  implicit none\n  integer, intent(in) :: x\nend subroutine foo\n",
        "PARSE_IMPLICIT_NONE_UNDECLARED_SYMBOL",
        "Argument 'y' in procedure 'foo' has no type declaration (implicit none is active).",
        None,
    ),
    "implicit-none-undeclared-function-name-result": _error(
        "implicit_none_func.f90",
        "function f(x)\n  implicit none\n  integer, intent(in) :: x\nend function f\n",
        "PARSE_IMPLICIT_NONE_UNDECLARED_SYMBOL",
        "Function result 'f' in procedure 'f' has no type declaration (implicit none is active).",
        None,
    ),
    "implicit-none-undeclared-result-clause": _error(
        "bad_result.f90",
        "function f(x) result(res)\n  implicit none\n  real :: x\nend function f\n",
        "PARSE_UNKNOWN_FUNCTION_RESULT_TYPE",
        "Unknown datatype for function result 'res' in procedure 'f'.",
        None,
    ),
    "legacy-parameter-without-type-under-implicit-none": _error(
        "legacy.f",
        "      subroutine cst(a)\n      implicit none\n      real a\n      parameter ( zero = 0.0e+0 )\n      end\n",
        "PARSE_UNKNOWN_PARAMETER_TYPE",
        "Unknown datatype for PARAMETER symbol 'zero' in procedure 'cst'.",
        4,
    ),
    "result-shadows-argument": _error(
        "shadow.f90",
        "function f(res) result(res)\n  integer, intent(in) :: res\nend function f\n",
        "PARSE_RESULT_SHADOWS_ARGUMENT",
        "Function result variable 'res' in function 'f' shadows an argument name.",
        None,
    ),
    # Unit boundaries and headers.
    "mismatched-end-module-name": _error(
        "mismatch_module.f90",
        "module expected_name\nend module wrong_name\n",
        "PARSE_MISMATCHED_UNIT_END",
        "Mismatched end module name 'wrong_name' for module 'expected_name'.",
        2,
    ),
    "missing-end-module": _error(
        "missing_end_module.f90",
        "module missing_end\n  integer :: n\n",
        "PARSE_MISSING_UNIT_END",
        "Missing end module for module 'missing_end'.",
        1,
    ),
    "unterminated-internal-procedure": _error(
        "unterminated_internal_unit.f90",
        "subroutine host()\ncontains\n  subroutine nested()\nend subroutine host\n",
        "PARSE_MISSING_UNIT_END",
        "Missing end procedure for procedure 'host'.",
        1,
    ),
    "missing-end-derived-type": _error(
        "module_contract.f90",
        "module owner_mod\n  type :: missing_end\nend module owner_mod\n",
        "PARSE_MISSING_DERIVED_TYPE_END",
        "Missing end derived type for derived type 'missing_end'.",
        2,
    ),
    "missing-end-type-nested-in-derived-type": _error(
        "type_field_invalid.f90",
        "module m\n  type :: state\n    type :: nested_marker\n  end type state\nend module m\n",
        "PARSE_MISSING_DERIVED_TYPE_END",
        "Missing end derived type for derived type 'nested_marker'.",
        3,
    ),
    "malformed-module-header": _error(
        "headers.f90",
        "module bad-name\nend module bad-name\n",
        "PARSE_MALFORMED_HEADER",
        "Unsupported or malformed module header: module bad-name",
        1,
    ),
    "malformed-separate-module-procedure-header": _error(
        "headers.f90",
        "submodule (p) c\ncontains\n  module procedure bad(x)\n  end procedure bad\nend submodule c\n",
        "PARSE_MALFORMED_HEADER",
        "Unsupported or malformed module procedure header: module procedure bad(x)",
        3,
    ),
    "stray-end-statement-in-file-scope": _error(
        "stray_ends.f90",
        "end module stray_mod\nsubroutine kept()\nend subroutine kept\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in file scope: end module stray_mod",
        1,
    ),
    # Invalid syntax, reported by the scope that owns the line.
    "invalid-syntax-in-file-scope": _error(
        "invalid_syntax.f90",
        "@@@\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in file scope: @@@",
        1,
    ),
    "c-prototype-in-file-scope": _error(
        "mixed.f90",
        "int add(int a, int b);\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in file scope: int add(int a, int b);",
        1,
    ),
    "invalid-syntax-in-module-specification": _error(
        "invalid_syntax.f90",
        "module bad_spec\n  @@@\nend module bad_spec\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in module 'bad_spec' specification part: @@@",
        2,
    ),
    "invalid-syntax-in-procedure-specification": _error(
        "invalid_syntax.f90",
        "subroutine work()\n  @@@\nend subroutine work\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in procedure 'work' specification part: @@@",
        2,
    ),
    "invalid-syntax-in-derived-type-specification": _error(
        "type_contract.f90",
        "module m\n  type :: state_t\n    call invalid_in_type_spec()\n  end type state_t\nend module m\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in type 'state_t' specification part: call invalid_in_type_spec()",
        3,
    ),
    "invalid-syntax-in-module-contains-part": _error(
        "contains_contract.f90",
        "module owner_mod\ncontains\n  @@@\nend module owner_mod\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in module 'owner_mod' contains part: @@@",
        3,
    ),
    "invalid-syntax-in-interface-after-valid-lines": _error(
        "interface_contract.f90",
        "module m\n  interface Callbacks\n    MODULE PROCEDURE :: First, Second\n"
        "    PROCEDURE(Callback) :: Handler\n    @@@\n  end interface Callbacks\nend module m\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in interface 'Callbacks': @@@",
        5,
    ),
    "nested-type-in-interface": _error(
        "nested_contract.f90",
        "interface callbacks\n  type :: nested\n  end type nested\nend interface\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in interface 'callbacks': type :: nested",
        2,
    ),
    "nested-type-in-derived-type": _error(
        "nested_contract.f90",
        "type :: outer\n  type :: nested\n  end type nested\nend type outer\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in derived type 'outer' specification part: type :: nested",
        2,
    ),
    "nested-type-in-block-data": _error(
        "nested_contract.f90",
        "block data init_data\n  type :: nested\n  end type nested\nend block data init_data\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in block data 'init_data' specification part: type :: nested",
        2,
    ),
    "interface-in-block-data": _error(
        "invalid_block_data.f90",
        "block data invalid_block\n  interface\n  end interface\nend block data invalid_block\n",
        "PARSE_INVALID_SYNTAX",
        "Invalid Fortran syntax in block data 'invalid_block' specification part: interface",
        2,
    ),
    "malformed-type-bound-declaration": _error(
        "type_contains_bad.f90",
        "module m\n  type :: state\n  contains\n    integer, public :: bad_binding\n  end type state\nend module m\n",
        "PARSE_UNSUPPORTED_TYPE_BOUND_DECLARATION",
        "Unsupported or malformed type-bound declaration in type 'state': integer, public :: bad_binding",
        4,
    ),
    # Executable statements and OpenMP directives outside an execution part.
    "executable-statement-in-module-specification": _error(
        "module_contract.f90",
        "module owner_mod\n  call work()\nend module owner_mod\n",
        "PARSE_EXECUTABLE_IN_SPECIFICATION",
        "Executable statement is not allowed in module specification part 'owner_mod': call work()",
        2,
    ),
    "openmp-executable-directive-in-module": _error(
        "bad_omp_mod.f90",
        "module bad_omp_mod\n!$omp parallel\nend module bad_omp_mod\n",
        "PARSE_EXECUTABLE_IN_SPECIFICATION",
        "Executable statement is not allowed in module specification part 'bad_omp_mod': !$omp parallel",
        2,
    ),
    "openmp-declarative-directive-in-module": _error(
        "omp_mod.f90",
        "module owner_mod\n  !$omp threadprivate(counter)\nend module owner_mod\n",
        "PARSE_UNSUPPORTED_OPENMP_DIRECTIVE",
        "Unsupported OpenMP declarative directive in module 'owner_mod': !$omp threadprivate(counter)",
        2,
    ),
    "openmp-declarative-directive-in-procedure": _error(
        "omp_decl.f90",
        "subroutine omp_decl(x)\n!$omp declare simd\n  integer, intent(inout) :: x\nend subroutine omp_decl\n",
        "PARSE_UNSUPPORTED_OPENMP_DIRECTIVE",
        "Unsupported OpenMP declarative directive in procedure 'omp_decl': !$omp declare simd",
        2,
    ),
    "openmp-declarative-directive-in-derived-type": _error(
        "omp_type.f90",
        "module m\n  type :: state\n!$omp declare target\n    integer :: value\n  end type state\nend module m\n",
        "PARSE_UNSUPPORTED_OPENMP_DIRECTIVE",
        "Unsupported OpenMP declarative directive in type 'state': !$omp declare target",
        3,
    ),
}


@pytest.mark.parametrize(
    ("filename", "source", "code", "message", "line"),
    list(_DIAGNOSTICS.values()),
    ids=list(_DIAGNOSTICS),
)
def test_parse_error_reports_code_message_and_location(filename, source, code, message, line):
    with pytest.raises(FortranParseError) as exc_info:
        parse_fortran_file(source, filename=filename)

    error = exc_info.value
    assert isinstance(error, ValueError)
    assert (error.code, error.base_message, error.filename, error.line_number) == (code, message, filename, line)
    if line is not None:
        assert error.source_line.strip() == source.splitlines()[line - 1].strip()
    diagnostic = error.format_diagnostic(color=False)
    assert f"error[{code}]" in diagnostic
    assert message in diagnostic


_ACCEPTED = {
    "non-fortran-after-execution-boundary": (
        "mixed_body.f90",
        "subroutine mixed_body()\n  call noop()\n  api_size count(void);\nend subroutine mixed_body\n",
        ["mixed_body"],
    ),
    "invalid-syntax-after-execution-boundary": (
        "accepted.f90",
        "subroutine ignored_body()\n  call noop()\n  @@@\nend subroutine ignored_body\n",
        ["ignored_body"],
    ),
    "semicolon-separated-statements": (
        "accepted.f90",
        "subroutine valid_body(x)\n  real :: x\n  call update(x); write(*,*) x\nend subroutine valid_body\n",
        ["valid_body"],
    ),
    "nested-unit-lines-after-execution-boundary": (
        "accepted.f90",
        "subroutine host()\n  call begin_work()\n  interface\n    subroutine ignored()\n      @@@\n"
        "    end subroutine ignored\n  end interface\nend subroutine host\n",
        ["host"],
    ),
    "unterminated-unit-line-after-execution-boundary": (
        "accepted.f90",
        "subroutine host()\n  call begin_work()\n  subroutine ignored()\nend subroutine host\n",
        ["host"],
    ),
    "internal-procedure-body-is-not-validated": (
        "accepted.f90",
        "subroutine host()\ncontains\n  subroutine nested()\n    @@@\n  end subroutine nested\nend subroutine host\n",
        ["host"],
    ),
    "same-internal-procedure-name-in-different-hosts": (
        "accepted.f90",
        "module m\ncontains\n  subroutine host_a()\n  contains\n    subroutine swap_order()\n"
        "    end subroutine swap_order\n  end subroutine host_a\n\n  subroutine host_b()\n  contains\n"
        "    subroutine swap_order()\n    end subroutine swap_order\n  end subroutine host_b\nend module m\n",
        ["host_a", "host_b"],
    ),
    "procedure-end-name-mismatch-is-tolerated": (
        "accepted.f90",
        "subroutine expected_name()\nend subroutine alternate_name\n",
        ["expected_name"],
    ),
    "named-block-construct-starts-execution": (
        "accepted.f90",
        "module block_mod\n  implicit none\ncontains\n  subroutine scale_value(x)\n    real(8),intent(inout) :: x\n"
        "    main: block\n      real(8) :: factor\n      factor = 2.0d0\n      x = x * factor\n"
        "    end block main\n  end subroutine scale_value\nend module block_mod\n",
        ["scale_value"],
    ),
    "openmp-executable-directive-in-body": (
        "accepted.f90",
        "subroutine omp_body(x)\n  integer, intent(inout) :: x\n!$omp parallel do\n  do i = 1, x\n"
        "    x = x + i\n  end do\nend subroutine omp_body\n",
        ["omp_body"],
    ),
    "fixed-form-openmp-sentinel-in-body": (
        "fixed_omp.f",
        "      subroutine fixed_omp(n)\n      integer n\nC$OMP PARALLEL DO\n      do 10 i = 1, n\n10    continue\n      end\n",
        ["fixed_omp"],
    ),
    "include-and-declaration-in-module-contains-part": (
        "accepted.f90",
        "module owner_mod\ncontains\n  include 'shape.inc'\n  integer :: macro_decl\n"
        "  subroutine s()\n  end subroutine s\nend module owner_mod\n",
        ["s"],
    ),
    "standalone-include-fragment": (
        "fragment.inc",
        "include 'fragment.inc'\nif (enabled) then\n  @@@\nelse\n  @@@\nendif\n",
        [],
    ),
}


@pytest.mark.parametrize(("filename", "source", "procedures"), list(_ACCEPTED.values()), ids=list(_ACCEPTED))
def test_parser_skips_content_it_does_not_model(filename, source, procedures):
    parsed = parse_fortran_file(source, filename=filename)

    names = [procedure.name for procedure in parsed.procedures]
    names += [procedure.name for module in parsed.modules for procedure in module.procedures]
    assert names == procedures
