"""Fortran accessibility decides which use-associated entities a module publishes.

Accessibility is settled by precedence: an access statement naming the entity
decides it, otherwise the module's bare `public`/`private` default does, and
that default is itself `public`. Those rules cover a use-associated entity, so
an ordinary module publishes what it imports without naming it anywhere.
"""

from pathlib import Path

import pytest

from prik.parsers.fortran import parse_fortran_project
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules

DECLARING = """\
module a_mod
  implicit none
  integer :: x = 7
  integer :: y = 9
  type :: box
    integer :: value
  end type box
contains
  integer function scale_value(v)
    integer, intent(in) :: v
    scale_value = v * 2
  end function scale_value
end module a_mod
"""


def _reexports(
    tmp_path: Path,
    importer: str,
    *,
    module_name: str = "b_mod",
) -> list[tuple[str, str, str]]:
    """Return one module's public use associations as (local, source, origin)."""
    source = tmp_path / "project.f90"
    source.write_text(f"{DECLARING}\n{importer}", encoding="utf-8")
    modules = fortran_project_to_semantic_modules(parse_fortran_project([source]))
    importing = next(module for module in modules if module.name == module_name)
    return [(item.local_name, item.source_name, item.origin_module) for item in importing.reexports]


def test_a_default_public_module_publishes_what_it_imports(tmp_path: Path):
    """No access statement is needed: the module default is public."""
    assert _reexports(
        tmp_path,
        """\
module b_mod
  use a_mod, only : x
  implicit none
end module b_mod
""",
    ) == [("x", "x", "a_mod")]


def test_a_declaration_dependency_remains_a_public_use_association(tmp_path: Path):
    """Using an import in a declaration does not change its accessibility."""
    assert _reexports(
        tmp_path,
        """\
module b_mod
  use a_mod, only : crate => box
  implicit none
contains
  integer function crate_value(item) result(out)
    type(crate), intent(in) :: item
    out = item%value
  end function crate_value
end module b_mod
""",
    ) == [("crate", "box", "a_mod")]


def test_a_third_module_resolves_a_declaration_dependency_through_its_importer(tmp_path: Path):
    """A public use association remains available to another Fortran module."""
    assert _reexports(
        tmp_path,
        """\
module b_mod
  use a_mod, only : box
  implicit none
  type(box) :: stored
end module b_mod

module c_mod
  use b_mod, only : box
  implicit none
  type(box) :: another
end module c_mod
""",
        module_name="c_mod",
    ) == [("box", "box", "a_mod")]


def test_explicit_public_still_publishes_a_declaration_dependency(tmp_path: Path):
    """A named public statement is an explicit publication request."""
    assert _reexports(
        tmp_path,
        """\
module b_mod
  use a_mod, only : crate => box
  implicit none
  public :: crate
contains
  integer function crate_value(item) result(out)
    type(crate), intent(in) :: item
    out = item%value
  end function crate_value
end module b_mod
""",
    ) == [("crate", "box", "a_mod")]


def test_a_bare_private_default_publishes_nothing_it_imports(tmp_path: Path):
    """A bare `private` sets the default, which then covers the import."""
    assert (
        _reexports(
            tmp_path,
            """\
module b_mod
  use a_mod, only : x
  implicit none
  private
end module b_mod
""",
        )
        == []
    )


def test_an_access_statement_outranks_a_private_default(tmp_path: Path):
    """Naming the entity decides it, whichever way the default points."""
    assert _reexports(
        tmp_path,
        """\
module b_mod
  use a_mod, only : x
  implicit none
  private
  public :: x
end module b_mod
""",
    ) == [("x", "x", "a_mod")]


def test_an_access_statement_outranks_a_public_default(tmp_path: Path):
    """`private :: x` decides it even though the default is public."""
    assert (
        _reexports(
            tmp_path,
            """\
module b_mod
  use a_mod, only : x
  implicit none
  private :: x
end module b_mod
""",
        )
        == []
    )


def test_a_private_used_module_route_withholds_its_entities(tmp_path: Path):
    """Naming the only used-module route private makes its entities private."""
    assert (
        _reexports(
            tmp_path,
            """\
module b_mod
  use a_mod
  implicit none
  private :: a_mod
end module b_mod
""",
        )
        == []
    )


def test_a_public_used_module_route_outranks_the_private_default(tmp_path: Path):
    """A public route exposes its entities despite the module's bare default."""
    published = _reexports(
        tmp_path,
        """\
module b_mod
  use a_mod
  implicit none
  private
  public :: a_mod
end module b_mod
""",
    )

    assert sorted(local for local, _source, _origin in published) == ["box", "scale_value", "x", "y"]


def test_any_public_route_keeps_a_multiply_accessible_entity_public(tmp_path: Path):
    """One public route wins when another route to the same entity is private."""
    assert _reexports(
        tmp_path,
        """\
module left_mod
  use a_mod, only : x
end module left_mod

module right_mod
  use a_mod, only : x
end module right_mod

module b_mod
  use left_mod
  use right_mod
  implicit none
  private :: left_mod
  public :: right_mod
end module b_mod
""",
    ) == [("x", "x", "a_mod")]


def test_a_renamed_default_public_import_publishes_the_local_name(tmp_path: Path):
    """A rename changes the name this module publishes, never the declaration."""
    assert _reexports(
        tmp_path,
        """\
module b_mod
  use a_mod, only : renamed => y
  implicit none
end module b_mod
""",
    ) == [("renamed", "y", "a_mod")]


def test_a_plain_use_carries_the_public_names_of_what_it_reads(tmp_path: Path):
    """A `use` naming no list carries every public name, default rules applying."""
    carried = _reexports(
        tmp_path,
        """\
module b_mod
  use a_mod
  implicit none
end module b_mod
""",
    )

    assert sorted(local for local, _source, _origin in carried) == ["box", "scale_value", "x", "y"]


def test_a_plain_use_carries_a_named_generic_interface(tmp_path: Path):
    """The offered-name inventory includes named interface declarations."""
    carried = _reexports(
        tmp_path,
        """\
module generic_home
  implicit none
  interface convert
    module procedure convert_i
    module procedure convert_r
  end interface convert
contains
  integer function convert_i(value)
    integer, intent(in) :: value
    convert_i = value
  end function convert_i
  real function convert_r(value)
    real, intent(in) :: value
    convert_r = value
  end function convert_r
end module generic_home

module b_mod
  use generic_home
  implicit none
end module b_mod
""",
    )

    assert ("convert", "convert", "generic_home") in carried


def test_a_plain_use_under_a_private_default_carries_nothing(tmp_path: Path):
    """The importing module's default decides what it publishes in turn."""
    assert (
        _reexports(
            tmp_path,
            """\
module b_mod
  use a_mod
  implicit none
  private
end module b_mod
""",
        )
        == []
    )


@pytest.mark.parametrize("kind", ["variable", "procedure"])
def test_accessibility_decides_every_re_exportable_kind(kind: str, tmp_path: Path):
    """The rule is about accessibility, so it does not single out one kind."""
    name = "x" if kind == "variable" else "scale_value"
    published = _reexports(
        tmp_path,
        f"""\
module b_mod
  use a_mod, only : {name}
  implicit none
end module b_mod
""",
    )

    assert published == [(name, name, "a_mod")]
