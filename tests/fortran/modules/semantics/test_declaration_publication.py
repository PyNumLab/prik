"""A module publishes the declarations its own accessibility makes reachable.

A prototype or a generic follows the same rule every other declaration does:
the contract may need to name it for typing or dispatch, but only what the
module makes public becomes part of its Python surface. A block written inside
a contained procedure is reachable in that procedure alone, so it is never a
module publication at all.
"""

from pathlib import Path

from prik.parsers.fortran import parse_fortran_file, parse_fortran_project
from prik.printers.pyi import PyiPrinter
from prik.policy.exports import complete_python_export_policy
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules, fortran_project_to_semantic_modules

PRIVATE_SOURCE = """\
module m
  implicit none
  private

  abstract interface
    subroutine cb()
    end subroutine
  end interface

  interface hidden_generic
    module procedure hidden_one
  end interface

  public :: run
contains
  subroutine run(f)
    procedure(cb) :: f
    call f()
  end subroutine run

  subroutine hidden_one(a)
    integer, intent(in) :: a
    print *, a
  end subroutine hidden_one
end module m
"""

LOCAL_INTERFACE_SOURCE = """\
module m
  implicit none
contains
  subroutine first(f)
    abstract interface
      subroutine cb(x)
        integer :: x
      end subroutine
    end interface
    procedure(cb) :: f
    call f(1)
  end subroutine first

  subroutine second(f)
    abstract interface
      subroutine cb(x)
        real :: x
      end subroutine
    end interface
    procedure(cb) :: f
    call f(1.0)
  end subroutine second
end module m
"""


def _module(source: str, tmp_path: Path):
    """Convert one source to its policy-complete semantic module."""
    path = tmp_path / "m.f90"
    path.write_text(source, encoding="utf-8")
    module = fortran_file_to_semantic_modules(parse_fortran_file(source, filename=str(path)))[0]
    complete_python_export_policy(module)
    return module


def test_a_private_prototype_and_generic_state_their_accessibility(tmp_path: Path):
    """Semantics records what the module's `private` default says about each."""
    module = _module(PRIVATE_SOURCE, tmp_path)

    assert [(item.name, item.visibility) for item in module.prototypes] == [("cb", "private")]
    assert [(item.name, item.visibility) for item in module.overload_sets] == [("hidden_generic", "private")]


def test_a_private_prototype_and_generic_are_written_but_not_published(tmp_path: Path):
    """The contract names both for typing and dispatch, and publishes neither."""
    module = _module(PRIVATE_SOURCE, tmp_path)
    contract = PyiPrinter().emit(module)

    # `run` annotates its callback with the prototype, so the name must exist.
    assert "def cb() -> None: ..." in contract
    assert "def hidden_generic(" in contract
    assert '__all__ = ["run"]' in contract


def test_two_procedures_may_name_different_interfaces_the_same_way(tmp_path: Path):
    """A block inside a procedure is that procedure's, so each keeps its own."""
    module = _module(LOCAL_INTERFACE_SOURCE, tmp_path)

    assert [(item.name, item.native_name, item.visibility) for item in module.prototypes] == [
        ("first_cb", "cb", "private"),
        ("second_cb", "cb", "private"),
    ]
    # Each procedure's callback keeps the signature its own block declares.
    signatures = {
        function.name: [argument.semantic_type.metadata["arguments"][0].name for argument in function.arguments]
        for function in module.functions
    }
    assert signatures == {"first": ["Int32"], "second": ["Float32"]}


def test_a_procedure_local_interface_is_never_a_module_publication(tmp_path: Path):
    """A `use` of the module cannot reach it, so the contract does not publish it."""
    module = _module(LOCAL_INTERFACE_SOURCE, tmp_path)
    contract = PyiPrinter().emit(module)

    assert "def first_cb(" in contract
    assert "def second_cb(" in contract
    assert "f: first_cb" in contract
    assert "f: second_cb" in contract
    assert '__all__ = ["first", "second"]' in contract


MODULE_AND_LOCAL_SOURCE = """\
module m
  implicit none
  abstract interface
    subroutine first_cb(x)
      integer :: x
    end subroutine
  end interface
contains
  subroutine first(f)
    abstract interface
      subroutine cb(x)
        real :: x
      end subroutine
    end interface
    procedure(cb) :: f
    call f(1.0)
  end subroutine first

  subroutine uses_module_one(g)
    procedure(first_cb) :: g
    call g(1)
  end subroutine uses_module_one
end module m
"""

JOINED_COLLISION_SOURCE = """\
module m
  implicit none
contains
  subroutine a_b(f)
    abstract interface
      subroutine c(x)
        integer :: x
      end subroutine
    end interface
    procedure(c) :: f
    call f(1)
  end subroutine a_b

  subroutine a(f)
    abstract interface
      subroutine b_c(x)
        real :: x
      end subroutine
    end interface
    procedure(b_c) :: f
    call f(1.0)
  end subroutine a
end module m
"""


def _callback_annotations(module) -> dict[str, tuple[str, str]]:
    """Return each callback argument's contract name and first argument type."""
    return {
        f"{function.name}.{argument.name}": (
            argument.semantic_type.name,
            argument.semantic_type.metadata["arguments"][0].name,
        )
        for function in module.functions
        for argument in function.arguments
        if argument.semantic_type.storage is not None and argument.semantic_type.storage.kind == "callback"
    }


def test_a_prototype_is_identified_by_its_scope_rather_than_its_spelling(tmp_path: Path):
    """A module block and a procedure block are different declarations.

    Naming the procedure-local one by joining its scope to its name produces
    the module block's own spelling, so the two would be one prototype and one
    of the callbacks would be given the other's signature.
    """
    module = _module(MODULE_AND_LOCAL_SOURCE, tmp_path)

    identities = [(item.native_name, item.declaring_scope, item.visibility) for item in module.prototypes]
    assert identities == [("first_cb", (), "public"), ("cb", ("first",), "private")]

    # The module's own block keeps the spelling another module imports it by.
    names = [item.name for item in module.prototypes]
    assert names[0] == "first_cb"
    assert names[1] != "first_cb"

    annotations = _callback_annotations(module)
    assert annotations["uses_module_one.g"] == ("first_cb", "Int32")
    assert annotations["first.f"] == (names[1], "Float32")


def test_scopes_whose_joined_spellings_collide_keep_distinct_contract_names(tmp_path: Path):
    """`a_b` declaring `c` and `a` declaring `b_c` are different prototypes."""
    module = _module(JOINED_COLLISION_SOURCE, tmp_path)

    names = [item.name for item in module.prototypes]
    assert len(set(names)) == 2

    annotations = _callback_annotations(module)
    assert annotations["a_b.f"] == (names[0], "Int32")
    assert annotations["a.f"] == (names[1], "Float32")


def test_a_contract_writes_one_prototype_for_each_scope(tmp_path: Path):
    """Both prototypes are written, and only the module's own is published."""
    module = _module(MODULE_AND_LOCAL_SOURCE, tmp_path)
    contract = PyiPrinter().emit(module)
    local_name = module.prototypes[1].name

    assert "def first_cb(\n    x: Int32[()]\n) -> None: ..." in contract
    assert f"def {local_name}(\n    x: Float32[()]\n) -> None: ..." in contract
    assert f"f: {local_name}" in contract
    assert "g: first_cb" in contract
    assert '__all__ = ["first_cb", "first", "uses_module_one"]' in contract


IMPORT_COLLISION_SOURCE = """\
module helper_mod
  implicit none
  integer :: first_cb = 7
end module helper_mod

module m_mod
  use helper_mod, only : first_cb
  implicit none
contains
  subroutine first(f)
    abstract interface
      subroutine cb(x)
        real :: x
      end subroutine
    end interface
    procedure(cb) :: f
    call f(1.0)
  end subroutine first
end module m_mod
"""


def test_a_prototype_does_not_take_a_name_the_module_imports(tmp_path: Path):
    """A use-associated name binds here too, so a prototype cannot be given it.

    `m_mod` imports `first_cb`, and its contained procedure declares `cb`,
    whose suggested spelling is the same. Allocating against the declared names
    alone let the prototype shadow the import the contract writes.
    """
    (tmp_path / "project.f90").write_text(IMPORT_COLLISION_SOURCE, encoding="utf-8")
    modules = {
        module.name: module for module in fortran_project_to_semantic_modules(parse_fortran_project(str(tmp_path)))
    }
    module = modules["m_mod"]
    complete_python_export_policy(module)

    assert [(item.native_name, item.declaring_scope) for item in module.prototypes] == [("cb", ("first",))]
    assert module.prototypes[0].name != "first_cb"

    contract = PyiPrinter(normalize_public_names=True).emit(module)
    assert "from .helper_mod import first_cb" in contract
    assert f"def {module.prototypes[0].name}(" in contract
    assert f"f: {module.prototypes[0].name}" in contract
