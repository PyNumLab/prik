"""Callback declaration parsing."""

from prik.parsers.fortran import parse_fortran_file


def test_nested_interface_marks_dummy_as_procedure():
    code = """
module callback_mod
contains
  subroutine caller(cb)
    interface
      subroutine cb(x)
        integer, intent(in) :: x
      end subroutine cb
    end interface
  end subroutine caller
end module callback_mod
"""

    parsed = parse_fortran_file(code)
    procedures = {proc.name: proc for proc in parsed.modules[0].procedures}

    assert procedures["caller"].arguments[0].base_type == "procedure"
