"""A callback name reached by several `use` routes has to name one interface.

Callback resolution answers which native declaration a `procedure(...)` names.
Routes are compared by the declaration they reach, so repeating a route is
harmless while two different ones, or one this project never read, leave the
name meaning nothing here.
"""

from pathlib import Path

from prik.parsers.fortran import parse_fortran_project
from prik.semantics.fortran2ir import FortranToIRConverter

HOME = """\
module known_callbacks
  implicit none
  abstract interface
    subroutine cb(x)
      integer, intent(in) :: x
    end subroutine cb
  end interface
end module known_callbacks

module relay_mod
  use known_callbacks, only : cb
  implicit none
end module relay_mod
"""


def _visible_callbacks(tmp_path: Path, importer: str, *, module_name: str) -> dict[str, str | None]:
    """Return the callback interfaces one module resolves, by declaring module."""
    source = tmp_path / "callbacks.f90"
    source.write_text(f"{HOME}\n{importer}", encoding="utf-8")
    project = parse_fortran_project([source])
    modules = [module for parsed in (getattr(project, "files", None) or [project]) for module in parsed.modules]
    index = FortranToIRConverter._callback_module_index(modules)
    importing = next(module for module in modules if module.name == module_name)
    resolved = FortranToIRConverter._module_callback_interfaces(index, importing)
    return {name: (item.module.name if item.module is not None else None) for name, item in resolved.items()}


def test_one_route_resolves_the_callback_it_names(tmp_path: Path):
    """A single `use` names one interface, which is what the dummy declares."""
    assert _visible_callbacks(
        tmp_path,
        """\
module single_mod
  use known_callbacks, only : cb
  implicit none
contains
  subroutine go(f)
    procedure(cb) :: f
  end subroutine go
end module single_mod
""",
        module_name="single_mod",
    ) == {"cb": "known_callbacks"}


def test_routes_reaching_one_declaration_resolve_it(tmp_path: Path):
    """Importing the same interface twice, directly and through a relay, is one entity."""
    assert _visible_callbacks(
        tmp_path,
        """\
module agreeing_mod
  use known_callbacks, only : cb
  use relay_mod,       only : cb
  implicit none
contains
  subroutine go(f)
    procedure(cb) :: f
  end subroutine go
end module agreeing_mod
""",
        module_name="agreeing_mod",
    ) == {"cb": "known_callbacks"}


def test_a_readable_route_beside_an_unreadable_one_resolves_nothing(tmp_path: Path):
    """An unread module offers whatever it names, which nothing here can compare.

    The re-export graph already refuses to name an entity here, so resolving
    the dummy against the readable route would answer a question the rest of
    the conversion declined.
    """
    assert (
        _visible_callbacks(
            tmp_path,
            """\
module competing_mod
  use known_callbacks,    only : cb
  use external_callbacks, only : cb
  implicit none
contains
  subroutine go(f)
    procedure(cb) :: f
  end subroutine go
end module competing_mod
""",
            module_name="competing_mod",
        )
        == {}
    )


def test_a_module_keeps_its_own_declaration_over_a_competing_import(tmp_path: Path):
    """A module's own interface is what its declarations name, imports aside."""
    assert _visible_callbacks(
        tmp_path,
        """\
module owning_mod
  use known_callbacks,    only : cb
  use external_callbacks, only : cb
  implicit none
  abstract interface
    subroutine cb(x)
      integer, intent(in) :: x
    end subroutine cb
  end interface
end module owning_mod
""",
        module_name="owning_mod",
    ) == {"cb": "owning_mod"}


LOCAL_CALLBACKS = """\
module local_mod
  implicit none
contains
  subroutine first(f)
    abstract interface
      subroutine cb(x)
        integer, intent(in) :: x
      end subroutine cb
    end interface
    procedure(cb) :: f
    call f(1)
  end subroutine first

  subroutine second(f)
    abstract interface
      subroutine cb(x)
        real(8), intent(in) :: x
      end subroutine cb
    end interface
    procedure(cb) :: f
    call f(1.0d0)
  end subroutine second
end module local_mod
"""


def test_each_procedure_resolves_the_callback_it_declares(tmp_path: Path):
    """Two procedures may name different interfaces the same way.

    A block written inside a procedure belongs to it, and the parser stores
    those beside the module's own, so indexing the module's blocks without
    regard to scope lets whichever came first answer for both.
    """
    source = tmp_path / "local_callbacks.f90"
    source.write_text(LOCAL_CALLBACKS, encoding="utf-8")
    project = parse_fortran_project([source])
    modules = [module for parsed in (getattr(project, "files", None) or [project]) for module in parsed.modules]
    index = FortranToIRConverter._callback_module_index(modules)
    owner = next(module for module in modules if module.name == "local_mod")

    # The module declares no interface of its own; both belong to a procedure.
    assert FortranToIRConverter._declared_callback_interfaces(owner) == {}

    seen = {}
    for procedure in owner.procedures:
        scope = FortranToIRConverter._scope_callback_interfaces(
            index,
            procedure.uses,
            base={},
            owner=owner,
            scope_name=procedure.name,
        )
        seen[procedure.name] = [argument.base_type for argument in scope["cb"].signature.arguments]

    assert seen == {"first": ["integer"], "second": ["real"]}
