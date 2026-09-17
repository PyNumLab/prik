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


CALLBACK_HOME = """\
module callback_types
  implicit none
  abstract interface
    integer function unary(x)
      integer, intent(in) :: x
    end function unary
  end interface
end module callback_types
"""


def _callback_reexports(tmp_path: Path, importer: str, *, module_name: str) -> list[tuple[str, str, str]]:
    """Return one module's public use associations over an abstract-interface home."""
    source = tmp_path / "callbacks.f90"
    source.write_text(f"{CALLBACK_HOME}\n{importer}", encoding="utf-8")
    modules = fortran_project_to_semantic_modules(parse_fortran_project([source]))
    importing = next(module for module in modules if module.name == module_name)
    return [(item.local_name, item.source_name, item.origin_module) for item in importing.reexports]


def test_a_plain_use_carries_an_abstract_interface_procedure(tmp_path: Path):
    """An abstract block names no generic; what it declares are its procedures."""
    assert _callback_reexports(
        tmp_path,
        """\
module middle_mod
  use callback_types
  implicit none
end module middle_mod
""",
        module_name="middle_mod",
    ) == [("unary", "unary", "callback_types")]


def test_an_abstract_interface_procedure_survives_a_further_hop(tmp_path: Path):
    """Carrying it once makes it importable by name from the carrying module."""
    assert _callback_reexports(
        tmp_path,
        """\
module middle_mod
  use callback_types
  implicit none
end module middle_mod

module user_mod
  use middle_mod, only : unary
  implicit none
end module user_mod
""",
        module_name="user_mod",
    ) == [("unary", "unary", "callback_types")]


def test_a_callback_reached_through_a_public_route_stays_public(tmp_path: Path):
    """Callback accessibility is the module's accessibility, routes included.

    A bare `private` would hide the name were the used module not named public,
    so judging it by the symbol statements alone reaches the wrong answer.
    """
    assert _callback_reexports(
        tmp_path,
        """\
module facade_mod
  use callback_types
  implicit none
  private
  public :: callback_types
end module facade_mod
""",
        module_name="facade_mod",
    ) == [("unary", "unary", "callback_types")]


def test_a_callback_reached_through_a_private_route_is_withheld(tmp_path: Path):
    """Naming the used module private withholds what it carried, default aside."""
    assert (
        _callback_reexports(
            tmp_path,
            """\
module facade_mod
  use callback_types
  implicit none
  private :: callback_types
end module facade_mod
""",
            module_name="facade_mod",
        )
        == []
    )


def test_routes_that_agree_on_one_entity_publish_it(tmp_path: Path):
    """Two `use` statements naming the same declaration name one entity."""
    assert _reexports(
        tmp_path,
        """\
module middle_mod
  use a_mod, only : x
  implicit none
end module middle_mod

module b_mod
  use a_mod, only : x
  use middle_mod, only : x
  implicit none
end module b_mod
""",
    ) == [("x", "x", "a_mod")]


def test_a_readable_route_beside_an_unreadable_one_is_not_guessed(tmp_path: Path):
    """An unparsed module may carry the same entity or another one.

    Choosing the readable route would be a guess about the one this project
    cannot read, so the name is left out rather than resolved to either.
    """
    assert (
        _reexports(
            tmp_path,
            """\
module b_mod
  use a_mod, only : x
  use external_mod, only : x
  implicit none
end module b_mod
""",
        )
        == []
    )


def test_a_single_unreadable_route_still_names_what_it_reached(tmp_path: Path):
    """One route names one entity, whether or not this project can read it."""
    assert _reexports(
        tmp_path,
        """\
module b_mod
  use external_mod, only : y
  implicit none
end module b_mod
""",
    ) == [("y", "y", "external_mod")]


def test_a_procedure_local_abstract_interface_stays_inside_its_procedure(tmp_path: Path):
    """A block written inside a contained procedure declares a name only there.

    Those blocks are stored beside the module's own, so nothing but the
    declaring scope distinguishes them.
    """
    assert _reexports(
        tmp_path,
        """\
module local_home
  implicit none
contains
  subroutine work()
    abstract interface
      subroutine local_callback()
      end subroutine local_callback
    end interface
  end subroutine work
end module local_home

module b_mod
  use local_home
  implicit none
end module b_mod
""",
    ) == [("work", "work", "local_home")]


def test_a_procedure_local_generic_stays_inside_its_procedure(tmp_path: Path):
    """A named generic declared inside a procedure is that procedure's, too."""
    carried = _reexports(
        tmp_path,
        """\
module local_home
  implicit none
contains
  subroutine work()
    interface local_generic
      module procedure work
    end interface local_generic
  end subroutine work
end module local_home

module b_mod
  use local_home
  implicit none
end module b_mod
""",
    )

    assert [local for local, _source, _origin in carried] == ["work"]


def test_a_wildcard_route_beside_an_unreadable_one_is_not_guessed(tmp_path: Path):
    """A plain `use` compares routes the way a named import does.

    Discarding the unreadable route would leave the readable one standing
    alone and answer for a module this project never read.
    """
    assert (
        _reexports(
            tmp_path,
            """\
module left_mod
  use a_mod, only : x
  implicit none
end module left_mod

module right_mod
  use external_mod, only : x
  implicit none
end module right_mod

module b_mod
  use left_mod
  use right_mod
  implicit none
end module b_mod
""",
        )
        == []
    )


def test_wildcard_routes_that_agree_on_one_entity_publish_it(tmp_path: Path):
    """Repeating a route to the same declaration names one entity."""
    assert _reexports(
        tmp_path,
        """\
module left_mod
  use a_mod, only : x
  implicit none
end module left_mod

module b_mod
  use left_mod
  use a_mod, only : x
  implicit none
end module b_mod
""",
    ) == [("x", "x", "a_mod")]


def test_a_name_spelled_inside_a_character_literal_is_not_a_dependency(tmp_path: Path):
    """A literal's contents are its value, not a reference to what they spell."""
    source = tmp_path / "project.f90"
    source.write_text(
        f"""{DECLARING}
module b_mod
  use a_mod, only : box
  implicit none
  character(len=3), parameter :: label = "box"
end module b_mod
""",
        encoding="utf-8",
    )
    modules = fortran_project_to_semantic_modules(parse_fortran_project([source]))
    importing = next(module for module in modules if module.name == "b_mod")

    assert [(item.local_name, item.declaration_dependency) for item in importing.reexports] == [("box", False)]


def test_a_type_a_declaration_names_is_a_dependency(tmp_path: Path):
    """Declaring with an imported type is what makes it a dependency."""
    source = tmp_path / "project.f90"
    source.write_text(
        f"""{DECLARING}
module b_mod
  use a_mod, only : box
  implicit none
  type(box) :: item
end module b_mod
""",
        encoding="utf-8",
    )
    modules = fortran_project_to_semantic_modules(parse_fortran_project([source]))
    importing = next(module for module in modules if module.name == "b_mod")

    assert [(item.local_name, item.declaration_dependency) for item in importing.reexports] == [("box", True)]


def test_a_compile_time_symbol_is_not_substituted_inside_a_character_literal():
    """A literal's contents are data, so a symbol spelled there is not a reference."""
    from prik.semantics.fortran2ir import _resolve_compile_time_text

    values = {"runtime": "4"}

    assert _resolve_compile_time_text('len("runtime")', values) == 'len("runtime")'
    # A reference outside the literal is still resolved.
    assert _resolve_compile_time_text("runtime + 1", values) == "4 + 1"
    assert _resolve_compile_time_text('len("runtime") + runtime', values) == 'len("runtime") + 4'
