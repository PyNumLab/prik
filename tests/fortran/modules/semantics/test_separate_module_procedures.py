"""A separate module procedure is one of its module's procedures wherever those are read.

An interface body with the ``module`` prefix declares a procedure the module
owns and a submodule implements. Name resolution, the project registry, and
generic inheritance read it exactly as they read a procedure the module
contains.
"""

from __future__ import annotations

import pytest

from prik.parsers.fortran import parse_fortran_file, parse_fortran_project
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules, fortran_project_to_semantic_modules

SIZES = """
module sizes
  implicit none
  interface
    pure module function extent(n) result(m)
      integer, intent(in) :: n
      integer :: m
    end function extent
  end interface
end module sizes

submodule (sizes) sizes_impl
  implicit none
contains
  module procedure extent
    m = 2 * n
  end procedure extent
end submodule sizes_impl

module user
  use sizes
  implicit none
contains
  subroutine fill(n, x)
    integer, intent(in) :: n
    real(8), intent(out) :: x(extent(n))
    x = real(n, 8)
  end subroutine fill
end module user
"""


def test_a_separate_function_a_plain_use_reaches_sizes_a_declaration():
    """``x(extent(n))`` calls ``sizes.extent``, which only an interface body declares.

    A plain ``use`` offers the names its module declares, so leaving separate
    procedures out made the call an unresolved reference with no native scope.
    """
    project = parse_fortran_project({"sizes.f90": SIZES})
    modules = {module.name: module for module in fortran_project_to_semantic_modules(project)}
    x = modules["user"].functions[0].arguments[1]

    callables = [
        (item.name, item.native_scope, item.placement)
        for axis in x.semantic_type.storage.array.expression_callables
        for item in axis
    ]

    assert callables == [("extent", "sizes", "module")]
    assert project.procedures["sizes.extent"].name == "extent"


HOSTED_KIND = """
module m
  implicit none
  integer, parameter :: wp = 8
  interface
    module function twice(x) result(y)
      real(wp), intent(in) :: x
      real(wp) :: y
    end function twice
  end interface
end module m
"""


@pytest.mark.parametrize("route", ["file", "project"])
def test_a_separate_interface_body_resolves_kinds_through_its_module(route: str):
    """The body is host associated with its module, so ``real(wp)`` is ``real(8)`` however it is parsed."""
    if route == "file":
        module = parse_fortran_file(HOSTED_KIND, filename="m.f90").modules[0]
    else:
        module = parse_fortran_project({"m.f90": HOSTED_KIND}).modules["m"]
    signature = module.separate_procedures[0]

    assert (signature.arguments[0].kind, signature.result.kind) == ("8", "8")


def test_a_file_converted_with_its_siblings_resolves_their_procedures_as_a_project_does():
    """The context sibling modules supply is the same one project conversion builds.

    A single file converted with its siblings knew their module names but not
    what they declared, so a sibling's procedure a plain ``use`` reaches stayed
    unresolved there while the project route resolved it.
    """
    sizes_source, _header, user_body = SIZES.partition("\nmodule user\n")
    project = parse_fortran_project({"sizes.f90": sizes_source, "user.f90": "module user\n" + user_body})
    sizes_file, user_file = project.files
    alone = fortran_file_to_semantic_modules(user_file, sibling_modules=sizes_file.modules)
    within = [module for module in fortran_project_to_semantic_modules(project) if module.name == "user"]

    def callables(modules):
        x = modules[0].functions[0].arguments[1]
        return [
            (item.native_scope, item.placement)
            for axis in x.semantic_type.storage.array.expression_callables
            for item in axis
        ]

    assert callables(alone) == callables(within) == [("sizes", "module")]
