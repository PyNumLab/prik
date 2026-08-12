"""Semantic contracts for module state and common blocks."""

from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


def test_module_common_block_storage_stays_internal():
    source = """
module common_mod
  public :: value, read_value
  real :: value
  common /shared/ value
contains
  real function read_value()
    read_value = value
  end function read_value
end module common_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))

    assert module.variables == []
    assert [function.name for function in module.functions] == ["read_value"]


def test_procedure_common_block_storage_is_allowed():
    source = """
module procedure_common_mod
contains
  subroutine work()
    real :: value
    common /shared/ value
  end subroutine work
end module procedure_common_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))

    assert [function.name for function in module.functions] == ["work"]
