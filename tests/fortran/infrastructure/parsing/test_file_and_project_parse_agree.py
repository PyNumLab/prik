"""One file parsed alone and within a project resolves what it declares the same way.

``parse_file`` resolves kinds, values, and shapes with the same pass project
assembly runs, visiting the same declarations, so parsing a self-contained
source alone never leaves a name unresolved that a project parse resolves.
"""

from __future__ import annotations

from prik.parsers.fortran import parse_fortran_file, parse_fortran_project

SELF_CONTAINED = """
module m
  implicit none
  integer, parameter :: wp = 8
  interface
    subroutine callback(x)
      import :: wp
      real(wp) :: x
    end subroutine callback
    module function twice(x) result(y)
      real(wp), intent(in) :: x
      real(wp) :: y
    end function twice
  end interface
contains
  subroutine run(y)
    real(wp) :: y
  end subroutine run
end module m

submodule (m) impl
  implicit none
  interface
    subroutine hook(z)
      import :: wp
      real(wp) :: z
    end subroutine hook
  end interface
end submodule impl
"""


def _kinds(parsed_file) -> dict[str, str | None]:
    """Return every argument kind the file declares, keyed by owner and name."""
    owners = (*parsed_file.modules, *parsed_file.submodules)
    signatures = [
        *(procedure for owner in owners for procedure in owner.procedures),
        *(procedure for owner in owners for interface in owner.interfaces for procedure in interface.procedures),
    ]
    return {
        f"{signature.module}.{signature.name}.{argument.name}": argument.kind
        for signature in signatures
        for argument in signature.arguments
    }


def test_a_file_resolves_every_kind_it_declares_as_a_project_of_it_does():
    alone = _kinds(parse_fortran_file(SELF_CONTAINED, filename="m.f90"))
    in_project = _kinds(parse_fortran_project({"m.f90": SELF_CONTAINED}).files[0])

    assert alone == in_project
    assert set(alone.values()) == {"8"}
