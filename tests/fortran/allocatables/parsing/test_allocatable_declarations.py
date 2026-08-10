"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

from tests.fortran._support.parser_procedures import parse_fortran_module


def test_module_allocatable_target_attribute_is_preserved():
    module = parse_fortran_module(
        """
module alloc_target_mod
  real(8), allocatable, target :: values(:)
end module alloc_target_mod
"""
    )

    values = module.variables[0]
    assert values.name == "values"
    assert values.allocatable is True
    assert values.target is True
