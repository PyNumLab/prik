"""An accessible generic is assembled from every interface that contributes to it.

An ordinary entity has one declaration, so two routes naming different ones
leave a local name ambiguous. A generic is the exception the language makes:
accessible generic interfaces sharing an identifier all contribute their
specific procedures to one generic, so every contributing route is read rather
than the first that matches.
"""

from pathlib import Path

from prik.parsers.fortran import parse_fortran_project
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules

CONTRIBUTORS = """\
module ints_mod
  implicit none
  interface convert
    module procedure convert_i
  end interface
contains
  integer function convert_i(x)
    integer, intent(in) :: x
    convert_i = x
  end function convert_i
end module ints_mod

module reals_mod
  implicit none
  interface convert
    module procedure convert_r
  end interface
contains
  real function convert_r(x)
    real, intent(in) :: x
    convert_r = x
  end function convert_r
end module reals_mod
"""

LOCAL_EXTENSION = """\
  interface convert
    module procedure convert_l
  end interface

contains
  logical function convert_l(x)
    logical, intent(in) :: x
    convert_l = x
  end function convert_l
end module facade_mod
"""


def _modules(tmp_path: Path, *sources: str):
    """Parse one throwaway project and return its semantic modules by name."""
    (tmp_path / "project.f90").write_text("\n".join(sources), encoding="utf-8")
    return {module.name: module for module in fortran_project_to_semantic_modules(parse_fortran_project(str(tmp_path)))}


def _specifics(module, generic_name: str) -> list[str]:
    """Return the specific procedures one module's generic dispatches over."""
    return [
        procedure.name
        for overload_set in module.overload_sets
        if overload_set.name == generic_name
        for procedure in overload_set.procedures
    ]


def test_two_imported_generics_both_contribute_their_specifics(tmp_path: Path):
    """Neither import replaces the other, so the generic dispatches over both."""
    modules = _modules(
        tmp_path,
        CONTRIBUTORS,
        """\
module facade_mod
  use ints_mod,  only : convert
  use reals_mod, only : convert
  implicit none
"""
        + LOCAL_EXTENSION,
    )

    assert _specifics(modules["facade_mod"], "convert") == ["convert_i", "convert_r", "convert_l"]


def test_an_imported_generic_reached_twice_contributes_once(tmp_path: Path):
    """One declaration is one contributor however many routes reach it."""
    modules = _modules(
        tmp_path,
        CONTRIBUTORS,
        """\
module hop_mod
  use ints_mod, only : convert
  implicit none
end module hop_mod

module facade_mod
  use ints_mod, only : convert
  use hop_mod,  only : convert
  implicit none
"""
        + LOCAL_EXTENSION,
    )

    assert _specifics(modules["facade_mod"], "convert") == ["convert_i", "convert_l"]


def test_a_private_generic_route_contributes_nothing(tmp_path: Path):
    """Accessibility applies to a generic route as it does to any other."""
    modules = _modules(
        tmp_path,
        CONTRIBUTORS,
        """\
module hop_mod
  use reals_mod, only : convert
  implicit none
  private :: convert
end module hop_mod

module facade_mod
  use ints_mod, only : convert
  use hop_mod,  only : convert
  implicit none
"""
        + LOCAL_EXTENSION,
    )

    assert _specifics(modules["facade_mod"], "convert") == ["convert_i", "convert_l"]


def test_generic_contributors_survive_a_transitive_chain(tmp_path: Path):
    """A module extending a merged generic inherits everything it reaches."""
    modules = _modules(
        tmp_path,
        CONTRIBUTORS,
        """\
module middle_mod
  use ints_mod,  only : convert
  use reals_mod, only : convert
  implicit none
  interface convert
    module procedure convert_m
  end interface
contains
  double precision function convert_m(x)
    double precision, intent(in) :: x
    convert_m = x
  end function convert_m
end module middle_mod

module facade_mod
  use middle_mod, only : convert
  implicit none
"""
        + LOCAL_EXTENSION,
    )

    assert _specifics(modules["middle_mod"], "convert") == ["convert_i", "convert_r", "convert_m"]
    assert sorted(_specifics(modules["facade_mod"], "convert")) == [
        "convert_i",
        "convert_l",
        "convert_m",
        "convert_r",
    ]


def test_two_imported_generics_remain_one_accessible_name(tmp_path: Path):
    """Generic routes are contributors, so they do not cancel each other out."""
    modules = _modules(
        tmp_path,
        CONTRIBUTORS,
        """\
module facade_mod
  use ints_mod,  only : convert
  use reals_mod, only : convert
  implicit none
end module facade_mod
""",
    )

    reexports = {item.local_name: item for item in modules["facade_mod"].reexports}
    assert reexports["convert"].entity_kind == "generic"


def test_a_generic_and_a_variable_of_one_name_are_not_merged(tmp_path: Path):
    """Different kinds of entity are a genuine ambiguity, not a contribution."""
    modules = _modules(
        tmp_path,
        CONTRIBUTORS,
        """\
module holder_mod
  implicit none
  integer :: convert = 3
end module holder_mod

module facade_mod
  use ints_mod,   only : convert
  use holder_mod, only : convert
  implicit none
end module facade_mod
""",
    )

    assert [item.local_name for item in modules["facade_mod"].reexports] == []


def test_a_procedure_local_generic_stays_inside_its_procedure(tmp_path: Path):
    """A block written inside a procedure is not part of the module's interface."""
    modules = _modules(
        tmp_path,
        """\
module owner_mod
  implicit none
contains
  subroutine run()
    interface convert
      module procedure convert_p
    end interface
  end subroutine run

  integer function convert_p(x)
    integer, intent(in) :: x
    convert_p = x
  end function convert_p
end module owner_mod

module facade_mod
  use owner_mod, only : convert
  implicit none
end module facade_mod
""",
    )

    assert [item.entity_kind for item in modules["facade_mod"].reexports if item.local_name == "convert"] == ["unknown"]
