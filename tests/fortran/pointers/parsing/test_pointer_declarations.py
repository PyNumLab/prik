"""Fortran pointer declaration parsing."""

from prik import parse_fortran_file


def test_scalar_array_and_optional_pointer_attributes_are_parsed():
    source = """
module pointer_declarations
  real(8), target :: storage(4)
  real(8), pointer :: module_values(:) => null()
contains
  subroutine select_values(scalar, values, maybe_values)
    real(8), pointer, intent(in) :: scalar
    real(8), pointer, contiguous, intent(inout) :: values(:)
    real(8), pointer, optional, intent(out) :: maybe_values(:)
  end subroutine select_values
end module pointer_declarations
"""

    module = parse_fortran_file(source).modules[0]
    module_values = module.variables[1]
    arguments = {argument.name: argument for argument in module.procedures[0].arguments}

    assert module_values.pointer is True
    assert module_values.shape == [":"]
    assert arguments["scalar"].pointer is True
    assert arguments["scalar"].shape == []
    assert arguments["values"].pointer is True
    assert arguments["values"].contiguous is True
    assert arguments["values"].intent == "inout"
    assert arguments["maybe_values"].pointer is True
    assert arguments["maybe_values"].optional is True
    assert arguments["maybe_values"].intent == "out"
