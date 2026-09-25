"""Project-level registries, dependencies, and scope model behavior."""

from pathlib import Path

import pytest

from prik.parsers.fortran import FortranParseError, parse_fortran_file, parse_fortran_project
from prik.parsers.fortran.scope import ScopeUses
from prik.parsers.fortran.parser import FortranParser
from prik.semantics.fortran2ir import fortran_module_to_semantic_module


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


def test_declaration_level_private_attribute_overrides_public_module_default():
    parsed = parse_fortran_file(
        """
module constants
  real, parameter, private :: epsilon = 1.0
  real, parameter :: visible = 2.0
end module constants
"""
    )

    module = parsed.modules[0]

    assert {variable.name: variable.visibility for variable in module.variables} == {
        "epsilon": "private",
        "visible": "public",
    }
    assert module.private_symbols == ["epsilon"]


def test_separate_parameter_statement_and_bind_c_module_storage_are_preserved():
    module = parse_fortran_file(
        """
module native_constants
  integer :: limit
  parameter (limit = 4)
  integer, bind(c) :: addressable
end module native_constants
"""
    ).modules[0]

    variables = {variable.name: variable for variable in module.variables}
    assert variables["limit"].is_parameter
    assert variables["limit"].value == "4"
    assert not variables["addressable"].is_parameter
    assert variables["addressable"]._fortran_bind_c


@pytest.mark.parametrize(
    ("implicit", "expected"),
    [
        pytest.param("", {"pi": "Float32", "n": "Int32"}, id="default-letter-rules"),
        pytest.param(
            "implicit double precision (a-h,o-z), integer(kind=8) (n)",
            {"pi": "Float64", "n": "Int64"},
            id="implicit-statement-mapping",
        ),
    ],
)
def test_separate_parameter_statement_types_an_undeclared_name_by_module_implicit_rules(implicit, expected):
    module = parse_fortran_file(
        f"""
module legacy_constants
  {implicit}
  parameter (pi = 3.14159265358979d0, n = 4)
end module legacy_constants
"""
    ).modules[0]

    semantic = fortran_module_to_semantic_module(module)
    assert {variable.name: variable.semantic_type.name for variable in semantic.variables} == expected
    assert all(variable.is_parameter for variable in module.variables)


@pytest.mark.parametrize("statement", ["implicit none", "implicit none (type)", "implicit none (type, external)"])
def test_separate_parameter_statement_under_implicit_none_requires_a_declaration(statement: str):
    with pytest.raises(FortranParseError, match="implicit none is active") as error:
        parse_fortran_file(
            f"""
module strict_constants
  {statement}
  parameter (undeclared = 3)
end module strict_constants
"""
        )

    assert error.value.code == "PARSE_UNKNOWN_PARAMETER_TYPE"


def test_implicit_none_external_keeps_implicit_typing_for_a_separate_parameter():
    module = parse_fortran_file(
        """
module external_only
  implicit none (external)
  parameter (n = 4)
end module external_only
"""
    ).modules[0]

    assert fortran_module_to_semantic_module(module).variables[0].semantic_type.name == "Int32"


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

    # A nested submodule depends on its direct parent, identified through its ancestor.
    project = parse_fortran_project({"child.f90": code})
    assert project.dependencies["ancestor_mod:child_mod"] == {"ancestor_mod:parent_mod"}
    assert "ancestor_mod:child_mod.reset" in project.procedures


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


def test_project_directory_orders_ancestor_submodule_dependencies(tmp_path):
    (tmp_path / "ancestor.f90").write_text(
        """
module ancestor_mod
end module ancestor_mod
""",
        encoding="utf-8",
    )
    (tmp_path / "parent.f90").write_text(
        """
submodule (ancestor_mod) parent_mod
end submodule parent_mod
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
    assert {"ancestor_mod:parent_mod", "ancestor_mod:child_mod"} <= set(project.submodules)
    assert project.dependencies["ancestor_mod:child_mod"] == {"ancestor_mod:parent_mod", "helper_mod"}
    ordered = [Path(parsed.filename).name for parsed in project.files]
    assert ordered.index("ancestor.f90") < ordered.index("parent.f90") < ordered.index("child.f90")


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

    assert ScopeUses(parsed.programs[0].uses).imports_all("callback_mod") is True
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
    assert [(mapping.source, mapping.target) for mapping in ScopeUses(proc.uses).mappings("precision_mod")] == [
        ("wp", "local_wp"),
        ("stride", None),
        ("wide", "local_wide"),
    ]
    assert project.dependencies["solver_mod"] == {"precision_mod"}


def test_project_compile_time_resolution_uses_models_is_idempotent_and_preserves_symbolic_shapes():
    parser = FortranParser()
    kinds_file = parser.parse_file(
        """
module kinds
  integer, parameter :: word = 4
  integer, parameter :: rk = word * 2
  integer, parameter :: n = 3
end module kinds
""",
        filename="kinds.f90",
    )
    consumer_file = parser.parse_file(
        """
module records
  use kinds, only: wp => rk, n
  type :: sample
    real(kind=wp) :: values(0:n)
  end type sample
contains
  subroutine consume(values)
    real(kind=wp), intent(in) :: values(1:n)
  end subroutine consume
end module records
""",
        filename="records.f90",
    )
    kinds_file.source = None
    consumer_file.source = None

    parser._resolve_project_compile_time_facts([kinds_file, consumer_file])
    field = consumer_file.modules[0].derived_types[0].fields[0]
    argument = consumer_file.modules[0].procedures[0].arguments[0]
    first_result = (field.kind, list(field.shape), argument.kind, list(argument.shape))

    parser._resolve_project_compile_time_facts([kinds_file, consumer_file])

    assert first_result == ("8", ["0:3"], "8", ["1:n"])
    assert (field.kind, field.shape, argument.kind, argument.shape) == first_result


def test_project_resolves_reexported_intrinsic_kind_renames():
    project = parse_fortran_project(
        {
            "consumer.f90": """
subroutine consume(x)
  use fftpack_kind, only: dp => rk
  real(dp), intent(inout) :: x
end subroutine consume
""",
            "kind.f90": """
module fftpack_kind
  use, intrinsic :: iso_fortran_env, only: rk => real64
end module fftpack_kind
""",
        }
    )

    assert project.procedures["consume"].arguments[0].kind == "real64"


def test_single_file_project_resolves_intrinsic_kind_rename_for_module_variables():
    project = parse_fortran_project(
        {
            "minpack.f90": """
module minpack_module
  use iso_fortran_env, only: wp => real64
  real(wp), parameter :: dpmpar(3) = 0.0_wp
contains
  real(wp) function enorm(value) result(output)
    real(wp), intent(in) :: value
    output = value
  end function enorm
end module minpack_module
"""
        }
    )

    module = project.modules["minpack_module"]
    assert module.variables[0].kind == "real64"
    assert module.procedures[0].arguments[0].kind == "real64"
    assert module.procedures[0].result.kind == "real64"


def test_project_resolves_submodule_host_associated_kind():
    project = parse_fortran_project(
        {
            "implementation.f90": """
submodule(transform_api) transform_impl
contains
  module function twice(value) result(output)
    real(rk), intent(in) :: value
    real(rk) :: output
  end function twice
end submodule transform_impl
""",
            "parent.f90": """
module transform_api
  use precision
  interface
    module function twice(value) result(output)
      real(rk), intent(in) :: value
      real(rk) :: output
    end function twice
  end interface
end module transform_api
""",
            "kind.f90": """
module precision
  use, intrinsic :: iso_fortran_env, only: rk => real64
end module precision
""",
        }
    )

    procedure = project.submodules["transform_api:transform_impl"].procedures[0]
    assert procedure.arguments[0].kind == "real64"
    assert procedure.result.kind == "real64"
    prototype = project.modules["transform_api"].interfaces[0].procedures[0]
    assert prototype.arguments[0].kind == "real64"
    assert prototype.result.kind == "real64"


def test_directory_project_records_missing_and_parent_only_submodule_dependencies(tmp_path):
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

    assert project.dependencies["parent_mod:child_mod"] == {"parent_mod", "missing_mod"}


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


def test_project_resolution_folds_fortran_real_literal_integer_parameters():
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

    assert proc.arguments[0].shape == ["1:7"]


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
    assert [mapping.local_name for mapping in ScopeUses(proc.uses).mappings("public_params_mod")] == [
        "rk",
        "n",
    ]


@pytest.mark.parametrize(
    ("nature", "kind"),
    [
        pytest.param("non_intrinsic", "3", id="user-module-value"),
        pytest.param("intrinsic", "real64", id="processor-spelling"),
    ],
)
def test_an_imported_kind_constant_follows_the_use_nature(nature: str, kind: str):
    """A kind named through ``use, intrinsic`` is the processor's, even beside a same-named user module."""
    project = parse_fortran_project(
        {
            "user.f90": "module iso_fortran_env\n  integer, parameter :: real64 = 3\nend module iso_fortran_env\n",
            "consumer.f90": (
                f"module consumer\n  use, {nature} :: iso_fortran_env, only: wp => real64\n"
                "  real(kind=wp) :: v\nend module consumer\n"
            ),
        }
    )

    assert project.modules["consumer"].variables[0].kind == kind


def test_same_named_submodules_of_different_ancestors_are_separate_project_scopes():
    """A submodule name is local to its ancestor, so ``a:impl`` and ``b:impl`` coexist.

    Each is keyed by its identity, depends on its own parent, and resolves
    kinds through its own ancestor's parameters. A nested child of each does
    the same through its direct parent.
    """
    sources = {}
    for ancestor, kind in (("a", 4), ("b", 8)):
        sources[f"{ancestor}.f90"] = f"""
module {ancestor}
  integer, parameter :: wp = {kind}
  interface
    module subroutine run(x)
      real(wp), intent(inout) :: x
    end subroutine run
  end interface
end module {ancestor}
"""
        sources[f"{ancestor}_impl.f90"] = f"""
submodule ({ancestor}) impl
contains
  module subroutine run(x)
    real(wp), intent(inout) :: x
  end subroutine run
end submodule impl
"""
        sources[f"{ancestor}_leaf.f90"] = f"""
submodule ({ancestor}:impl) leaf
  real(wp) :: scale
end submodule leaf
"""

    project = parse_fortran_project(sources)

    assert set(project.submodules) == {"a:impl", "b:impl", "a:leaf", "b:leaf"}
    assert project.dependencies["a:leaf"] == {"a:impl"}
    assert project.dependencies["b:impl"] == {"b"}
    assert project.submodules["a:impl"].procedures[0].arguments[0].kind == "4"
    assert project.submodules["b:impl"].procedures[0].arguments[0].kind == "8"
    assert project.submodules["a:leaf"].variables[0].kind == "4"
    assert project.submodules["b:leaf"].variables[0].kind == "8"
