"""Project-level registries, dependencies, and scope model behavior."""

import pytest

from x2py import FortranParseError, parse_fortran_file, parse_fortran_project


def test_module_visibility_public_and_private_spec_lines_are_applied():
    code = """
module visibility_mod
  private
  public :: exported
  private :: hidden
  integer :: exported, hidden, inherited
end module visibility_mod

module public_mod
  public
  real :: visible
end module public_mod
"""

    modules = {module.name: module for module in parse_fortran_file(code).modules}
    visibility = {var.name: var.visibility for var in modules["visibility_mod"].variables}

    assert modules["visibility_mod"].default_visibility == "private"
    assert visibility == {
        "exported": "public",
        "hidden": "private",
        "inherited": "private",
    }
    assert modules["public_mod"].variables[0].visibility == "public"


def test_submodule_types_interfaces_and_project_dependencies_attach_to_public_models():
    code = """
submodule (ancestor_mod:parent_mod) child_mod
  type :: child_state
    integer :: id
  end type child_state

  interface callbacks
    subroutine on_step(x)
      integer, intent(in) :: x
    end subroutine on_step
  end interface callbacks
contains
  module procedure reset
  end procedure reset
end submodule child_mod
"""

    parsed = parse_fortran_file(code)
    submodule = parsed.submodules[0]

    assert submodule.parent == "parent_mod"
    assert submodule.ancestor == "ancestor_mod"
    assert [dtype.name for dtype in submodule.derived_types] == ["child_state"]
    assert [iface.name for iface in submodule.interfaces] == ["callbacks"]
    assert [proc.name for proc in submodule.procedures] == ["reset"]

    project = parse_fortran_project({"child.f90": code})
    assert project.dependencies["child_mod"] == {"ancestor_mod", "parent_mod"}
    assert "child_mod.reset" in project.procedures


def test_project_registry_includes_module_types_interfaces_and_program_dependencies():
    project = parse_fortran_project(
        {
            "api.f90": """
module api_mod
  type :: state_t
    integer :: id
  end type state_t

  interface apply
    subroutine apply_i(x)
      integer, intent(in) :: x
    end subroutine apply_i
  end interface apply
contains
  subroutine step(state)
    type(state_t), intent(inout) :: state
  end subroutine step
end module api_mod
""",
            "driver.f90": """
program driver
  use api_mod
  integer :: ierr
end program driver
""",
        }
    )

    assert "api_mod.state_t" in project.derived_types
    assert "state_t" in project.derived_types
    assert "api_mod.apply" in project.interfaces
    assert "apply" in project.interfaces
    assert project.dependencies["driver"] == {"api_mod"}


def test_duplicate_project_scope_names_raise_public_parse_errors():
    with pytest.raises(FortranParseError, match="Duplicate symbol 'dup_mod' in project module scope"):
        parse_fortran_project(
            {
                "a.f90": "module dup_mod\nend module dup_mod\n",
                "b.f90": "module dup_mod\nend module dup_mod\n",
            }
        )


def test_project_directory_namespace_orders_ancestor_submodule_dependencies(tmp_path):
    (tmp_path / "ancestor.f90").write_text(
        """
module ancestor_mod
end module ancestor_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "parent.f90").write_text(
        """
module parent_mod
  use ancestor_mod
end module parent_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "child.f90").write_text(
        """
submodule (ancestor_mod:parent_mod) child_mod
  use helper_mod
contains
  module procedure reset
  end procedure reset
end submodule child_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "helper.f90").write_text(
        """
module helper_mod
end module helper_mod
""",
        encoding="utf-8",
    )

    project = parse_fortran_project(tmp_path)

    assert "ancestor_mod" in project.modules
    assert "parent_mod" in project.modules
    assert "child_mod" in project.submodules
    assert project.dependencies["child_mod"] == {"ancestor_mod", "parent_mod", "helper_mod"}


def test_program_contains_and_unnamed_block_data_public_models():
    code = """
program main
  use callback_mod
  integer :: ierr
contains
  subroutine internal()
  end subroutine internal
end program main

block data
  integer seed
end
"""

    parsed = parse_fortran_file(code, filename="units.f90")

    assert parsed.programs[0].uses["callback_mod"] == []
    assert [var.name for var in parsed.programs[0].variables] == ["ierr"]
    assert parsed.block_data_units[0].name is None
    assert [var.name for var in parsed.block_data_units[0].variables] == ["seed"]


def test_public_models_finalize_program_block_data_and_file_level_types_interfaces():
    project = parse_fortran_project(
        {
            "units_a.f90": """
type :: file_state
  integer :: id
end type file_state

interface file_callback
  subroutine cb()
  end subroutine cb
end interface file_callback

program driver
  integer :: status
end program driver

block data init_data
  integer seed
end block data init_data
""",
            "units_b.f90": """
program worker
  integer :: status
end program worker
""",
        }
    )

    assert "file_state" in project.derived_types
    assert "file_callback" in project.interfaces
    assert "driver" in project.programs
    assert "worker" in project.programs


def test_duplicate_program_and_block_data_variables_report_scope_labels():
    with pytest.raises(FortranParseError, match="Duplicate variable 'status' in program 'driver'"):
        parse_fortran_file(
            """
program driver
  integer :: status
  real :: status
end program driver
""",
            filename="dup_program_var.f90",
        )

    with pytest.raises(FortranParseError, match="Duplicate variable 'seed' in block data 'init_data'"):
        parse_fortran_file(
            """
block data init_data
  integer seed
  real seed
end block data init_data
""",
            filename="dup_block_var.f90",
        )


def test_directory_project_resolves_module_kinds_and_orders_dependencies(tmp_path):
    (tmp_path / "kinds.f90").write_text(
        """
module kinds_mod
  integer, parameter :: rk = 8
end module kinds_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "solver.f90").write_text(
        """
module solver_mod
  use kinds_mod, only: rk
contains
  function make_value(x) result(value)
    real(kind=rk), intent(in) :: x(1:rk)
    real(kind=rk) :: value
  end function make_value
end module solver_mod
""",
        encoding="utf-8",
    )

    project = parse_fortran_project(tmp_path)
    proc = project.procedures["solver_mod.make_value"]

    assert proc.arguments[0].kind == "8"
    assert proc.arguments[0].shape == ["1:rk"]
    assert proc.result.kind == "8"
    assert project.dependencies["solver_mod"] == {"kinds_mod"}


def test_directory_project_tracks_renamed_kind_imports_from_other_files(tmp_path):
    (tmp_path / "precision.f90").write_text(
        """
module precision_mod
  integer, parameter :: word = 4
  integer, parameter :: stride = 2
  integer, parameter :: wp = word * stride
  integer, parameter :: wide = wp * stride
end module precision_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "solver.f90").write_text(
        """
module solver_mod
  use precision_mod, only: local_wp => wp, stride, local_wide => wide
contains
  subroutine consume(x, y)
    real(kind=local_wp), intent(in) :: x(1:stride)
    complex(kind=local_wide), intent(out) :: y
  end subroutine consume
end module solver_mod
""",
        encoding="utf-8",
    )

    project = parse_fortran_project(tmp_path)
    proc = project.procedures["solver_mod.consume"]
    args = {arg.name: arg for arg in proc.arguments}

    assert args["x"].kind == "8"
    assert args["x"].shape == ["1:stride"]
    assert args["y"].kind == "16"
    assert [(mapping.source, mapping.target) for mapping in proc.uses["precision_mod"]] == [
        ("wp", "local_wp"),
        ("stride", None),
        ("wide", "local_wide"),
    ]
    assert project.dependencies["solver_mod"] == {"precision_mod"}


def test_directory_namespace_records_missing_and_parent_only_submodule_dependencies(tmp_path):
    (tmp_path / "parent.f90").write_text(
        """
module parent_mod
end module parent_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "child.f90").write_text(
        """
submodule (parent_mod) child_mod
  use missing_mod
contains
  module procedure reset
  end procedure reset
end submodule child_mod
""",
        encoding="utf-8",
    )

    project = parse_fortran_project(tmp_path)

    assert project.dependencies["child_mod"] == {"parent_mod", "missing_mod"}


def test_program_and_block_data_scope_errors_use_public_parse_paths():
    with pytest.raises(FortranParseError, match="Unsupported OpenMP declarative directive in program 'driver'"):
        parse_fortran_file(
            """
program driver
!$omp threadprivate(counter)
end program driver
""",
            filename="program_omp_decl.f90",
        )

    with pytest.raises(FortranParseError, match="Unsupported OpenMP declarative directive in block data 'init_data'"):
        parse_fortran_file(
            """
block data init_data
!$omp threadprivate(seed)
end block data init_data
""",
            filename="block_omp_decl.f90",
        )

    with pytest.raises(FortranParseError, match="Unknown or unsupported datatype declaration in program 'driver'"):
        parse_fortran_file(
            """
program driver
  weirdtype state
end program driver
""",
            filename="program_unknown_decl.f90",
        )

    with pytest.raises(
        FortranParseError, match="Unknown or unsupported datatype declaration in block data 'init_data'"
    ):
        parse_fortran_file(
            """
block data init_data
  weirdtype seed
end block data init_data
""",
            filename="block_unknown_decl.f90",
        )


def test_project_resolution_keeps_relevant_local_parameter_variables():
    project = parse_fortran_project(
        {
            "local_params.f90": """
subroutine use_relevant_local_param(e)
  integer, parameter :: n = 8
  integer, parameter :: one = 1.0d+0
  real, intent(inout) :: e(1:+n-one)
end subroutine use_relevant_local_param
"""
        }
    )

    proc = project.procedures["use_relevant_local_param"]

    assert proc.arguments[0].shape == ["1:+(8)-one"]
    assert proc.variables["one"].value == "1"


def test_project_resolution_uses_file_level_use_only_and_local_parameters(tmp_path):
    (tmp_path / "params.f90").write_text(
        """
module public_params_mod
  integer, parameter :: rk = selected_real_kind(12)
  integer, parameter :: n = 4
end module public_params_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "worker.f90").write_text(
        """
subroutine file_level_worker(x, y)
  use public_params_mod, only: rk, , n
  integer, parameter :: local_rk = selected_real_kind(6)
  real(kind=rk), intent(inout) :: x(1:n)
  real(kind=local_rk), intent(out) :: y
end subroutine file_level_worker
""",
        encoding="utf-8",
    )
    project = parse_fortran_project(tmp_path)

    proc = project.procedures["file_level_worker"]
    args = {arg.name: arg for arg in proc.arguments}

    assert args["x"].kind == "selected_real_kind(12)"
    assert args["x"].shape == ["1:n"]
    assert args["y"].kind == "selected_real_kind(6)"
    assert [mapping.local_name for mapping in proc.uses["public_params_mod"]] == ["rk", "n"]
