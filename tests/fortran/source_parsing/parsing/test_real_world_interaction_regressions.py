"""Minimized parser regressions extracted from former third-party sources."""

from prik import parse_fortran_file
from prik.parsers.fortran.lexer import preprocess_lines, strip_comment
from prik.parsers.fortran.models import FortranProcedureSignature
from prik.parsers.fortran.parser import FortranParser, _SourceUnitScanner
from prik.parsers.fortran.utils import split_csv


def test_free_form_lexing_preserves_mixed_quotes_and_folds_leading_ampersands():
    assert strip_comment('print *, "don\'t remove ! here" ! remove me', "free") == ('print *, "don\'t remove ! here" ')
    assert preprocess_lines(
        "value = first &\n  & + second &\n  & + third\n",
        filename="continuation.f90",
    ) == [("value = first+ second+ third", 1, "value = first &")]
    assert split_csv("left,") == ["left"]


def test_legacy_and_extended_types_keep_initializers_and_declaration_attributes():
    parsed = parse_fortran_file(
        """
module declaration_interactions
  implicit none
  type legacy_state
    integer :: enabled = 1 < 2
  end type legacy_state
  type :: parent_state
  end type parent_state
  type, extends(parent_state) :: child_state
  end type child_state
  type, extends(remote_state) :: external_child_state
  end type external_child_state
  integer, target :: selected
  integer, public :: exposed
  integer, parameter :: truth = 1 < 2
  real, parameter :: scale = 1.25d0
  character(len=*), parameter :: label = "timer"
  character*1, parameter :: prefix = 'D'
  complex, parameter :: imaginary = (0.d0, 1.d0)
end module declaration_interactions
""",
        filename="declaration_interactions.f90",
    )
    module = parsed.modules[0]
    types = {dtype.name: dtype for dtype in module.derived_types}
    variables = {variable.name: variable for variable in module.variables}

    assert types["legacy_state"].fields[0].value == "1"
    assert types["legacy_state"].fields[0].symbolic_value == "1 < 2"
    assert types["child_state"].extends is types["parent_state"]
    assert types["external_child_state"].extends == "remote_state"
    assert variables["selected"].target is True
    assert variables["exposed"].visibility == "public"
    assert variables["truth"].value == "1"
    assert variables["scale"].value == "1.25d0"
    assert variables["label"].value == '"timer"'
    assert variables["prefix"].is_parameter is True
    assert variables["prefix"].value == "'D'"
    assert variables["prefix"].symbolic_value == "'D'"
    assert variables["imaginary"].value == "(0.d0, 1.d0)"


def test_polymorphic_class_declarations_work_in_each_metadata_scope():
    module = parse_fortran_file(
        """
module polymorphic_declarations
  type :: base_state
  end type base_state
  class(base_state), allocatable :: current
  type :: holder
    class(base_state), pointer :: item
  end type holder
contains
  subroutine consume(value)
    class(base_state), intent(in) :: value
  end subroutine consume
end module polymorphic_declarations
""",
        filename="polymorphic_declarations.f90",
    ).modules[0]

    assert module.variables[0].base_type == "derived"
    assert module.variables[0].kind == "base_state"
    assert module.variables[0].allocatable is True
    assert module.derived_types[1].fields[0].base_type == "derived"
    assert module.derived_types[1].fields[0].kind == "base_state"
    assert module.derived_types[1].fields[0].pointer is True
    assert module.procedures[0].arguments[0].base_type == "derived"
    assert module.procedures[0].arguments[0].kind == "base_state"


def test_legacy_procedure_specifications_preserve_wrapper_relevant_facts():
    parsed = parse_fortran_file(
        """
function evaluate(callback, x) result(out)
  implicit none
  real :: callback
  external :: callback
  real, intent(in) :: x
  integer, parameter :: rk = selected_real_kind(12)
  real(kind=rk) :: out
  real :: cache
  common /workspace/ cache, /scratch/ cache
  save cache
  data cache / 0.0 /
  include 'constants.inc'
  square(value) = value * value
  out = callback(x) + square(x)
end function evaluate
""",
        filename="procedure_interactions.f90",
    )
    signature = parsed.procedures[0]
    arguments = {argument.name: argument for argument in signature.arguments}

    assert arguments["callback"].base_type == "real"
    assert signature.result is not None
    assert signature.result.kind == "selected_real_kind(12)"
    assert signature.common_variables == ["cache"]
    assert _SourceUnitScanner.is_executable_statement_start("square(value) = value * value") is False


def test_procedure_include_is_recorded_before_signature_finalization():
    parser = FortranParser()
    state = parser._new_procedure_scope_state(
        FortranProcedureSignature("include_contract", "subroutine"),
        symbols={},
    )

    assert parser._handle_proc_include_or_import_line("include 'constants.inc'", state) is True
    assert state.includes == ["'constants.inc'"]
