import pytest

from prik.parsers.fortran.models import FortranParseError
from prik import parse_fortran_file


def test_same_argument_name_in_different_procedures_is_allowed():
    code = """
subroutine a(x)
  implicit none
  integer :: x
end subroutine a

subroutine b(x)
  implicit none
  real(8) :: x
end subroutine b
"""
    parsed = parse_fortran_file(code, filename="scope_args_ok.f90")
    assert [s.name for s in parsed.procedures] == ["a", "b"]


def test_interface_argument_names_do_not_conflict_with_host_locals():
    code = """
subroutine host(func, x)
  implicit none
  interface
     function func(x)
       real(8) :: x
       real(8) :: func
     end function func
  end interface
  real(8) :: x
end subroutine host
"""
    parsed = parse_fortran_file(code, filename="scope_interface_ok.f90")
    assert len(parsed.procedures) == 1
    assert parsed.procedures[0].name == "host"


def test_same_contained_procedure_name_in_different_hosts_is_allowed():
    code = """
module m
contains
  subroutine host_a()
  contains
    subroutine helper(y)
      integer :: y
    end subroutine helper
  end subroutine host_a

  subroutine host_b()
  contains
    subroutine helper(y)
      real(8) :: y
    end subroutine helper
  end subroutine host_b
end module m
"""
    parsed = parse_fortran_file(code, filename="scope_contains_ok.f90")
    module = parsed.modules[0]
    assert [s.name.lower() for s in module.procedures] == ["host_a", "host_b"]


def test_duplicate_procedure_name_in_same_scope_still_errors():
    code = """
module m
contains
  subroutine work(n)
    integer :: n
  end subroutine work
  function work(n) result(out)
    integer :: n
    integer :: out
  end function work
end module m
"""
    with pytest.raises(FortranParseError, match="Duplicate procedure name"):
        parse_fortran_file(code, filename="scope_dup_err.f90")


def test_type_components_do_not_conflict_with_host_procedure_locals():
    code = """
module component_vs_local
  implicit none
  type :: box_t
     integer :: n
  end type box_t
contains
  subroutine touch()
    implicit none
    integer :: n
  end subroutine touch
end module component_vs_local
"""
    parsed = parse_fortran_file(code, filename="scope_component_local_ok.f90")
    module = parsed.modules[0]
    assert [s.name for s in module.procedures] == ["touch"]


def test_module_variable_and_type_component_same_name_is_allowed():
    code = """
module module_vs_component
  implicit none
  integer :: vals
  type :: payload
     integer :: vals
  end type payload
end module module_vs_component
"""
    parsed = parse_fortran_file(code, filename="scope_module_component_same_name_ok.f90")
    module = parsed.modules[0]

    assert {v.name for v in module.variables} == {"vals"}
    assert [t.name for t in module.derived_types] == ["payload"]
    assert {f.name for f in module.derived_types[0].fields} == {"vals"}


def test_type_component_names_do_not_leak_between_different_modules():
    code = """
module a_mod
  type :: t
     integer :: vals
  end type t
end module a_mod

module b_mod
  type :: t
     real(8) :: vals
  end type t
end module b_mod
"""
    parsed = parse_fortran_file(code, filename="scope_cross_module_components_ok.f90")
    assert [m.name for m in parsed.modules] == ["a_mod", "b_mod"]
    assert {f.name for f in parsed.modules[0].derived_types[0].fields} == {"vals"}
    assert {f.name for f in parsed.modules[1].derived_types[0].fields} == {"vals"}


def test_duplicate_type_component_name_still_errors_inside_single_type_scope():
    code = """
module dup_component_mod
  implicit none
  type :: thing
    integer :: vals
    real(8) :: vals
  end type thing
end module dup_component_mod
"""
    with pytest.raises(FortranParseError, match="Duplicate field 'vals' in derived type 'thing'"):
        parse_fortran_file(code, filename="scope_component_dup_err.f90")


def test_module_parameter_shape_is_visible_to_contained_function_scope():
    code = """
module dims_mod
  implicit none
  integer, parameter :: n = 8
contains
  function total(values) result(out)
    implicit none
    real, intent(in) :: values(n)
    real :: out
  end function total
end module dims_mod
"""
    parsed = parse_fortran_file(code, filename="scope_module_shape_param_ok.f90")
    module = parsed.modules[0]
    proc = module.procedures[0]

    assert module.variables[0].name == "n"
    assert module.variables[0].value == "8"
    assert module.variables[0].symbolic_value == "8"
    assert proc.name == "total"
    assert proc.arguments[0].shape == ["n"]
    assert proc.arguments[0].base_type == "real"
    assert proc.result.base_type == "real"
    assert proc.variables == {}


def test_fortran_parser_class_entrypoint():
    source = """
subroutine touch(x)
    integer, intent(inout) :: x
end subroutine
"""

    signatures = parse_fortran_file(source).procedures

    assert len(signatures) == 1
    assert signatures[0].name == "touch"
