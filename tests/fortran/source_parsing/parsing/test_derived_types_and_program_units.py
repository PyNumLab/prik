"""Tests split by stable ownership concept from `test_procedures_and_interfaces.py`."""

from tests.fortran._support.parser_procedures import (
    FortranParseError,
    parse_fortran_block_data_unit,
    parse_fortran_file,
    parse_fortran_module,
    parse_fortran_modules,
    parse_fortran_program,
    parse_fortran_project,
    parse_fortran_submodule,
    pytest,
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
