"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

import pytest
from prik.parsers.fortran import FortranParseError, parse_fortran_file, parse_fortran_project
from tests.fortran._support.parser_procedures import (
    parse_fortran_block_data_unit,
    parse_fortran_module,
    parse_fortran_modules,
    parse_fortran_program,
    parse_fortran_submodule,
)


def test_duplicate_symbols_are_reported_from_inline_fortran():
    with pytest.raises(FortranParseError, match="Duplicate variable 'x' in module 'dup_mod'"):
        parse_fortran_file(
            """
module dup_mod
  integer :: x
  real :: x
end module dup_mod
"""
        )

    with pytest.raises(FortranParseError, match="Duplicate field 'id' in derived type 'particle'"):
        parse_fortran_file(
            """
module dup_type_mod
  type :: particle
    integer :: id
    real :: id
  end type particle
end module dup_type_mod
"""
        )

    with pytest.raises(FortranParseError, match="Duplicate argument name 'x' in procedure 'dup_arg'"):
        parse_fortran_file(
            """
subroutine dup_arg(x, x)
  integer, intent(in) :: x
end subroutine dup_arg
"""
        )


def test_fixed_form_fortran77_continuation():
    code = """
      subroutine saxpy(n,x,y,a)
      integer n
      real x(n),y(n),a
      do 10 i=1,n
     1y(i)=y(i)+a*x(i)
 10   continue
      end
"""
    sigs = parse_fortran_file(code, filename="legacy.f").procedures
    assert len(sigs) == 1
    assert sigs[0].name == "saxpy"
    assert sigs[0].arguments[0].base_type == "integer"
    assert sigs[0].arguments[1].base_type == "real"
    assert sigs[0].arguments[1].rank == 1


def test_unknown_datatype_for_argument_crashes_parser():
    code = """
subroutine bad(x)
  weirdtype :: x
end subroutine bad
"""
    with pytest.raises(ValueError, match="Unknown or unsupported datatype"):
        _ = parse_fortran_file(code, filename="bad.f90").procedures


def test_parse_fortran_file_returns_file_model_for_source_string():
    code = """
module file_mod
contains
subroutine ping(x)
  integer, intent(in) :: x
end subroutine ping
end module file_mod
"""
    parsed = parse_fortran_file(code)
    assert parsed.filename is None
    assert [m.name for m in parsed.modules] == ["file_mod"]
    assert [p.name for p in parsed.modules[0].procedures] == ["ping"]


def test_parse_fortran_project_returns_project_registry():
    project = parse_fortran_project(
        {
            "a.f90": """
module a_mod
contains
subroutine step(x)
  integer, intent(in) :: x
end subroutine step
end module a_mod
""",
            "b.f90": """
subroutine free_proc(y)
  real, intent(in) :: y
end subroutine free_proc
""",
        }
    )
    assert [f.filename for f in project.files] == ["a.f90", "b.f90"]
    assert "a_mod" in project.modules
    assert "a_mod.step" in project.procedures
    assert "free_proc" in project.procedures


def test_parse_fortran_project_accepts_directory_and_orders_dependencies(tmp_path):
    (tmp_path / "10_solver.f90").write_text(
        """
module solver_mod
  use kinds_mod, only: rk
contains
  subroutine step(x)
    real(kind=rk), intent(inout) :: x(:)
  end subroutine step
end module solver_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "00_kinds.f90").write_text(
        """
module kinds_mod
  integer, parameter :: rk = selected_real_kind(15, 307)
end module kinds_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "20_driver.f90").write_text(
        """
program driver
  use solver_mod
  real :: x(4)
end program driver
""",
        encoding="utf-8",
    )
    (tmp_path / "30_init.f90").write_text(
        """
block data init_data
  integer :: seed
end block data init_data
""",
        encoding="utf-8",
    )

    project = parse_fortran_project(tmp_path)

    assert len(project.files) == 4
    assert "kinds_mod" in project.modules
    assert "solver_mod" in project.modules
    assert "driver" in project.programs
    assert "solver_mod.step" in project.procedures
    solver = project.procedures["solver_mod.step"]
    assert solver.arguments[0].kind == "selected_real_kind(15, 307)"


def test_singular_parse_entrypoints_return_single_models():
    assert (
        parse_fortran_file("""
subroutine one(x)
  integer, intent(in) :: x
end subroutine one
""")
        .procedures[0]
        .name
        == "one"
    )

    assert (
        parse_fortran_module("""
module single_mod
end module single_mod
""").name
        == "single_mod"
    )

    assert (
        parse_fortran_file("""
module type_mod
  type :: particle
    integer :: id
  end type particle
end module type_mod
""")
        .modules[0]
        .derived_types[0]
        .name
        == "particle"
    )

    assert (
        parse_fortran_file("""
module iface_mod
  interface apply
    subroutine do_apply(x)
      integer, intent(in) :: x
    end subroutine do_apply
  end interface
end module iface_mod
""")
        .modules[0]
        .interfaces[0]
        .name
        == "apply"
    )

    assert (
        parse_fortran_program("""
program driver
  integer :: ierr
end program driver
""").name
        == "driver"
    )

    assert (
        parse_fortran_block_data_unit("""
block data init_data
  integer :: seed
end block data init_data
""").name
        == "init_data"
    )

    assert (
        parse_fortran_submodule("""
submodule (parent_mod) child_impl
end submodule child_impl
""").name
        == "child_impl"
    )


def test_singular_parse_entrypoint_rejects_ambiguous_sources():
    assert (
        len(
            parse_fortran_modules("""
module first_mod
end module first_mod
module second_mod
end module second_mod
""")
        )
        == 2
    )

    parsed = parse_fortran_file("""
subroutine first()
end subroutine first
subroutine second()
end subroutine second
""")
    assert len(parsed.procedures) == 2


def test_type_accessibility_statements_set_component_and_binding_defaults():
    """A type's `private` statement is a default, not an unsupported declaration.

    The statement before `contains` sets component accessibility; the statement
    after it sets type-bound accessibility. Each declaration that states its own
    accessibility keeps it.
    """
    module = parse_fortran_module(
        """
module access_mod
  implicit none
  type,public :: t
    private
    integer :: hidden = 0
    integer,public :: shown = 0
  contains
    private
    procedure :: internal_step
    procedure,public :: step => internal_step
  end type t
contains
  subroutine internal_step(self)
    class(t),intent(inout) :: self
  end subroutine internal_step
end module access_mod
"""
    )

    dtype = module.derived_types[0]
    assert dtype.component_visibility == "private"
    assert dtype.binding_visibility == "private"
    assert {field.name: field.visibility for field in dtype.fields} == {
        "hidden": "private",
        "shown": "public",
    }
    assert [(binding["name"], binding["visibility"]) for binding in dtype.procedure_bindings] == [
        ("internal_step", "private"),
        ("step => internal_step", "public"),
    ]


def test_deferred_type_bound_binding_records_its_declaring_interface():
    """A deferred binding parses; whether it can be wrapped belongs to policy."""
    module = parse_fortran_module(
        """
module deferred_mod
  implicit none
  type,public,abstract :: base
  contains
    procedure(size_func),deferred,public :: size_of
  end type base
  abstract interface
    pure function size_func(self) result(s)
      import :: base
      class(base),intent(in) :: self
      integer :: s
    end function size_func
  end interface
end module deferred_mod
"""
    )

    binding = module.derived_types[0].procedure_bindings[0]
    assert binding["name"] == "size_of"
    assert binding["interface"] == "size_func"
    assert "deferred" in binding["attrs"]


def test_named_block_construct_starts_the_execution_part():
    """`name: block` is an executable construct, not a declaration."""
    module = parse_fortran_module(
        """
module block_mod
  implicit none
contains
  subroutine scale_value(x)
    real(8),intent(inout) :: x
    main: block
      real(8) :: factor
      factor = 2.0d0
      x = x * factor
    end block main
  end subroutine scale_value
end module block_mod
"""
    )

    assert [procedure.name for procedure in module.procedures] == ["scale_value"]
