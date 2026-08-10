"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

from prik import parse_fortran_file


def test_subroutine_derived_type_arguments_are_parsed():
    code = """
subroutine step(state)
  type(sim_state), intent(inout) :: state
end subroutine step
"""
    sig = parse_fortran_file(code).procedures[0]
    arg = sig.arguments[0]
    assert arg.base_type == "derived"
    assert arg.kind == "sim_state"


def test_derived_type_extends_external_parent_stays_symbolic():
    code = """
module m
  type, extends(external_base_t) :: child_t
  end type child_t
end module m
"""
    dt = parse_fortran_file(code).modules[0].derived_types[0]
    assert dt.extends == "external_base_t"


def test_derived_type_procedure_and_generic_bindings():
    code = """
module m
  type :: t
  contains
    procedure, pass(self) :: init => t_init
    procedure, nopass :: clear
    generic :: assignment(=) => init
    generic, public :: setup => init, clear
  end type t
end module m
"""
    dt = parse_fortran_file(code).modules[0].derived_types[0]
    assert {"name": "init => t_init", "attrs": ["pass(self)"]} in dt.procedure_bindings
    assert {"name": "clear", "attrs": ["nopass"]} in dt.procedure_bindings
    assert {"name": "assignment(=)", "targets": ["init"], "attrs": []} in dt.generic_bindings
    assert {"name": "setup", "targets": ["init", "clear"], "attrs": ["public"]} in dt.generic_bindings
