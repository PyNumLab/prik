"""Generic interface parser evidence for free- and fixed-form sources."""

from pathlib import Path

import pytest

from prik.parsers.fortran import parse_fortran_file
from tests.fortran._support.parser_procedures import (
    parse_fortran_interfaces,
    parse_fortran_module,
)
from prik.parsers.fortran.models import FortranParseError

FIXTURES = Path(__file__).parents[1] / "end_to_end" / "fixtures"


def test_named_generic_interface_procedures_are_tagged_with_interface_name():
    code = """
interface foo
  integer function foo_i(x)
    integer, intent(in) :: x
  end function foo_i

  real function foo_r(x)
    real, intent(in) :: x
  end function foo_r
end interface foo
"""
    interfaces = parse_fortran_interfaces(code, filename="iface_generic.f90")
    assert len(interfaces) == 1
    assert interfaces[0].name == "foo"
    assert [p.name for p in interfaces[0].procedures] == ["foo_i", "foo_r"]
    assert all(p.in_interface for p in interfaces[0].procedures)


def test_named_generic_interface_preserves_specific_procedure_references():
    code = """
module generic_mod
  interface convert
    module procedure convert_integer, convert_real
  end interface convert
contains
  integer function convert_integer(value)
    integer :: value
    convert_integer = value
  end function convert_integer
  real function convert_real(value)
    real :: value
    convert_real = value
  end function convert_real
end module generic_mod
"""
    interface = parse_fortran_module(code).interfaces[0]
    assert interface.name == "convert"
    assert interface.specific_procedures == ["convert_integer", "convert_real"]
    assert interface.procedures == []
    assert interface.abstract is False


def test_defined_operator_and_assignment_interfaces_preserve_generic_names_and_targets():
    code = """
module defined_generics
  interface operator(+)
    module procedure add_values
  end interface operator(+)
  interface operator(.cross.)
    module procedure cross_values
  end interface operator(.cross.)
  interface assignment(=)
    module procedure assign_value
  end interface assignment(=)
end module defined_generics
"""
    interfaces = parse_fortran_module(code).interfaces

    assert [(interface.name, interface.specific_procedures) for interface in interfaces] == [
        ("operator(+)", ["add_values"]),
        ("operator(.cross.)", ["cross_values"]),
        ("assignment(=)", ["assign_value"]),
    ]


def test_fixed_form_generic_interface_preserves_specific_procedures():
    parsed = parse_fortran_file(FIXTURES / "native" / "foverloads_fixed.f")
    interface = parsed.modules[0].interfaces[0]

    assert interface.name == "convert"
    assert interface.specific_procedures == ["convert_integer", "convert_real"]


def test_assumed_type_generic_candidate_is_rejected_at_parsing():
    source = """
module unsupported_generic
  interface inspect
    module procedure inspect_any
  end interface
contains
  subroutine inspect_any(value)
    class(*), intent(in) :: value
  end subroutine inspect_any
end module unsupported_generic
"""

    with pytest.raises(FortranParseError, match=r"Unsupported assumed-type CLASS\(\*\) declaration") as exc_info:
        parse_fortran_file(source, filename="unsupported_generic.f90")

    assert exc_info.value.code == "PARSE_UNSUPPORTED_DECLARATION"
