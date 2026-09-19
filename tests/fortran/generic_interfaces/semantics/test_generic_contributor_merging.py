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


SAME_NAMED_SPECIFICS = """\
module ints_mod
  implicit none
  interface convert
    module procedure to_value
  end interface
contains
  integer function to_value(x)
    integer, intent(in) :: x
    to_value = x
  end function to_value
end module ints_mod

module reals_mod
  implicit none
  interface convert
    module procedure to_value
  end interface
contains
  real function to_value(x)
    real, intent(in) :: x
    to_value = x
  end function to_value
end module reals_mod

module facade_mod
  use ints_mod,  only : convert
  use reals_mod, only : convert
  implicit none
  interface convert
    module procedure to_value_l
  end interface
contains
  logical function to_value_l(x)
    logical, intent(in) :: x
    to_value_l = x
  end function to_value_l
end module facade_mod
"""


def test_contributors_spelling_a_specific_alike_stay_two_procedures(tmp_path: Path):
    """A specific is identified by the module declaring it, not by its spelling.

    Two contributors each declare `to_value`. Keying them by name alone made
    the second look like the first and dropped it, so the merged generic lost a
    signature it must dispatch over.
    """
    modules = _modules(tmp_path, SAME_NAMED_SPECIFICS)
    overload_set = next(item for item in modules["facade_mod"].overload_sets if item.name == "convert")

    identities = [
        (procedure.origin.native_scope, procedure.arguments[0].semantic_type.name)
        for procedure in overload_set.procedures
    ]
    assert identities == [("ints_mod", "Int32"), ("reals_mod", "Float32"), ("facade_mod", "Bool")]


def test_a_contract_names_each_merged_specific_distinctly(tmp_path: Path):
    """Two specifics spelled alike need two Python names and two targets."""
    from prik.policy.exports import complete_python_export_policy
    from prik.printers.pyi import PyiPrinter

    modules = _modules(tmp_path, SAME_NAMED_SPECIFICS)
    facade = modules["facade_mod"]
    complete_python_export_policy(facade)
    contract = PyiPrinter(normalize_public_names=True).emit(facade)

    assert contract.count("def to_value(") == 1
    assert contract.count("def to_value_2(") == 1
    # Each dispatcher names the declaration this contract actually writes.
    assert '@overload("to_value")' in contract
    assert '@overload("to_value_2")' in contract


def test_a_type_bound_assignment_reaches_the_method_it_projects(tmp_path: Path):
    """The generic's candidate and the method it names are one declaration.

    A defined assignment projects its bound object as the result. The original
    method has to carry that projection too, so both the generic call and a
    direct call behave the same way.
    """
    modules = _modules(
        tmp_path,
        """\
module asg_mod
  implicit none
  type :: box_t
    integer :: value = 0
  contains
    procedure :: assign_value
    generic :: assignment(=) => assign_value
  end type box_t
contains
  subroutine assign_value(self, other)
    class(box_t), intent(inout) :: self
    integer, intent(in) :: other
    self%value = other
  end subroutine assign_value
end module asg_mod
""",
    )
    declared = modules["asg_mod"].classes[0]
    method = next(item for item in declared.methods if item.name == "assign_value")

    assert [(item.python_name, item.result_position) for item in method.projection] == [
        ("self", 0),
        ("other", None),
    ]


def test_a_contract_binds_a_merged_generic_only_by_declaring_it(tmp_path: Path):
    """The facade writes the merged generic, so no `use` of a contributor is imported.

    Mirroring each `use` bound `convert` once per contributor as well as by the
    facade's own declaration, and a package binding one name three ways cannot
    be read back.
    """
    from prik.pipeline.pyi import emit_module_stubs

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
    contract = emit_module_stubs(list(modules.values()), normalize_public_names=True)["facade_mod"]

    assert [line for line in contract.splitlines() if line.startswith("from .")] == []
    assert contract.count("def convert(") == 3
