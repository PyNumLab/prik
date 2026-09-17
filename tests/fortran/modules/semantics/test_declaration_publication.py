"""A module publishes the declarations its own accessibility makes reachable.

A prototype or a generic follows the same rule every other declaration does:
the contract may need to name it for typing or dispatch, but only what the
module makes public becomes part of its Python surface. A block written inside
a contained procedure is reachable in that procedure alone, so it is never a
module publication at all.
"""

from pathlib import Path

from prik.parsers.fortran import parse_fortran_file
from prik.printers.pyi import PyiPrinter
from prik.policy.exports import complete_python_export_policy
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules

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
    assert "cb" not in PyiPrinter().published_names(module)


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
