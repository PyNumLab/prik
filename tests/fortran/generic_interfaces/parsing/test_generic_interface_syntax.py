"""Generic interface parser evidence for free- and fixed-form sources."""

from pathlib import Path

import pytest

from prik.parsers.fortran import parse_fortran_file
from tests.fortran._support.parser_procedures import (
    parse_fortran_interfaces,
    parse_fortran_module,
    parse_fortran_modules,
)
from prik.parsers.fortran.models import FortranParseError

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

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


def test_generic_interface_declared_in_several_blocks_becomes_one_generic():
    """Fortran builds one generic from as many blocks as a scope declares.

    Real sources split a generic across preprocessor-guarded blocks, adding
    specifics only for the kinds a build supports, so repeated blocks name one
    generic rather than redeclaring it.
    """
    source = (NATIVE_FIXTURES / "generic_interface_declared_in_several_blocks_becomes_one_generic.f90").read_text(
        encoding="utf-8"
    )

    module = parse_fortran_module(source)

    generics = [interface for interface in module.interfaces if interface.name]
    assert len(generics) == 1
    assert generics[0].name == "huge_value"
    assert generics[0].specific_procedures == ["huge_value_sp", "huge_value_dp", "huge_value_qp"]


def test_repeated_generic_names_stay_separate_per_module():
    """Two modules in one file each own their generic of the same name."""
    source = (NATIVE_FIXTURES / "repeated_generic_names_stay_separate_per_module.f90").read_text(encoding="utf-8")

    modules = {module.name: module for module in parse_fortran_modules(source)}

    assert [item.specific_procedures for item in modules["first_mod"].interfaces if item.name] == [["report_first"]]
    assert [item.specific_procedures for item in modules["second_mod"].interfaces if item.name] == [["report_second"]]


def test_type_bound_generic_declared_in_several_statements_becomes_one_binding():
    """A type-bound generic collects specifics from as many statements as it takes.

    A derived type may name one generic binding over several ``generic ::``
    statements, and every statement contributes specifics to that one binding
    rather than declaring another of the same name.
    """
    source = (NATIVE_FIXTURES / "type_bound_generic_declared_in_several_statements_becomes_one_binding.f90").read_text(
        encoding="utf-8"
    )

    module = parse_fortran_module(source)

    assert [binding["name"] for binding in module.derived_types[0].generic_bindings] == ["area"]
    assert module.derived_types[0].generic_bindings[0]["targets"] == ["area_int", "area_real"]


def test_type_bound_operator_generic_merges_across_statements_and_spacing():
    """One defined operator binding survives being split across statements."""
    source = (NATIVE_FIXTURES / "type_bound_operator_generic_merges_across_statements_and_spacing.f90").read_text(
        encoding="utf-8"
    )

    module = parse_fortran_module(source)

    assert [binding["name"] for binding in module.derived_types[0].generic_bindings] == ["operator(+)"]
    assert module.derived_types[0].generic_bindings[0]["targets"] == ["add_int", "add_real"]


def test_same_generic_name_in_two_procedures_declares_two_generics():
    """A generic belongs to the scope declaring it, and procedures are scopes.

    Two procedures of one module may each declare an interface of the same
    name, and they name different generics. Merging them on the module they
    share would let one procedure's specifics answer the other's calls.
    """
    source = (NATIVE_FIXTURES / "same_generic_name_in_two_procedures_declares_two_generics.f90").read_text(
        encoding="utf-8"
    )

    module = parse_fortran_module(source)

    assert [
        (interface.name, [signature.name for signature in interface.procedures])
        for interface in module.interfaces
        if interface.name
    ] == [
        ("local_generic", ["first_impl"]),
        ("local_generic", ["second_impl"]),
    ]
