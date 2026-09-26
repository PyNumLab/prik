"""Semantic contracts for module state and common blocks."""

from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


def test_module_common_block_storage_stays_internal():
    """Common-block storage is never a module variable, in the module or in a procedure."""
    source = """
module common_mod
  public :: value, read_value
  real :: value
  common /shared/ value
contains
  real function read_value()
    read_value = value
  end function read_value

  subroutine work()
    real :: local
    common /procedure_shared/ local
  end subroutine work
end module common_mod
"""

    module = fortran_module_to_semantic_module(parse_fortran_source(source))

    assert module.variables == []
    assert [function.name for function in module.functions] == ["read_value", "work"]
