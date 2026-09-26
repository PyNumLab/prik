"""Project assembly: file discovery, dependency order, registries, and scope rules."""

from pathlib import Path

import pytest

from prik.parsers.fortran import FortranParseError, FortranParser, parse_fortran_file, parse_fortran_project


def test_directory_project_parses_once_and_assembles_dependency_ordered_models(tmp_path: Path, monkeypatch):
    sources = {
        "ancestor.f90": "module Ancestor_Mod\nend module Ancestor_Mod\n",
        "parent.f90": "module Parent_Mod\n  use Ancestor_Mod\n  type :: Parent_State\n  end type Parent_State\nend module Parent_Mod\n",
        "helper.f90": "module Helper_Mod\nend module Helper_Mod\n",
        "child.f90": (
            "submodule (Parent_Mod) Child_Mod\n"
            "  use Helper_Mod\n"
            "  type :: Child_State\n"
            "  end type Child_State\n"
            "end submodule Child_Mod\n"
        ),
        "grandchild.f90": "submodule (Parent_Mod:Child_Mod) Grandchild_Mod\nend submodule Grandchild_Mod\n",
        "units.f90": (
            "type :: File_State\n"
            "end type File_State\n"
            "program Driver\n"
            "  use Parent_Mod\n"
            "end program Driver\n"
            "block data Init_Data\n"
            "  integer :: seed\n"
            "end block data Init_Data\n"
        ),
    }
    for filename, source in sources.items():
        (tmp_path / filename).write_text(source, encoding="utf-8")

    read_paths: list[Path] = []
    encodings: list[str | None] = []
    original_read_text = Path.read_text

    def read_text(path, *args, **kwargs):
        read_paths.append(path)
        encodings.append(kwargs.get("encoding"))
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)

    project = parse_fortran_project(tmp_path)

    ancestor = str(tmp_path / "ancestor.f90")
    parent = str(tmp_path / "parent.f90")
    helper = str(tmp_path / "helper.f90")
    child = str(tmp_path / "child.f90")
    grandchild = str(tmp_path / "grandchild.f90")
    units = str(tmp_path / "units.f90")

    assert len(read_paths) == len(sources)
    assert set(read_paths) == {tmp_path / filename for filename in sources}
    assert set(encodings) == {"utf-8"}

    ordered_files = [parsed_file.filename for parsed_file in project.files]
    assert ordered_files.index(ancestor) < ordered_files.index(parent)
    assert ordered_files.index(parent) < ordered_files.index(child)
    assert ordered_files.index(helper) < ordered_files.index(child)
    assert ordered_files.index(child) < ordered_files.index(grandchild)
    assert units in ordered_files

    assert {module.name for module in project.modules.values()} == {
        "Ancestor_Mod",
        "Helper_Mod",
        "Parent_Mod",
    }
    assert {submodule.name for submodule in project.submodules.values()} == {
        "Child_Mod",
        "Grandchild_Mod",
    }
    assert [program.name for program in project.programs.values()] == ["Driver"]
    assert [block.name for parsed_file in project.files for block in parsed_file.block_data_units] == ["Init_Data"]
    assert {dtype.name for dtype in project.derived_types.values()} == {
        "Parent_State",
        "Child_State",
        "File_State",
    }
    assert {module.name: module.filename for module in project.modules.values()} == {
        "Ancestor_Mod": ancestor,
        "Helper_Mod": helper,
        "Parent_Mod": parent,
    }
    assert {submodule.name: submodule.filename for submodule in project.submodules.values()} == {
        "Child_Mod": child,
        "Grandchild_Mod": grandchild,
    }
    # A submodule is keyed ``ancestor:name`` and depends on its direct parent.
    assert project.dependencies["parent_mod"] == {"ancestor_mod"}
    assert project.dependencies["parent_mod:child_mod"] == {"parent_mod", "helper_mod"}
    assert project.dependencies["parent_mod:grandchild_mod"] == {"parent_mod:child_mod"}


def test_project_registries_preserve_qualified_aliases_values_and_dependencies():
    project = parse_fortran_project(
        {
            "api.f90": """
module api_mod
  type :: state_t
    integer :: id
  end type state_t
  interface callback
    subroutine on_step(x)
      integer, intent(in) :: x
    end subroutine on_step
  end interface callback
contains
  subroutine step(x)
    real, intent(in) :: x
  end subroutine step
end module api_mod
""",
            "child.f90": """
submodule (api_mod) child_mod
  type :: child_state_t
    integer :: id
  end type child_state_t
  interface child_callback
    subroutine child_step(x)
      integer, intent(in) :: x
    end subroutine child_step
  end interface child_callback
contains
  module procedure reset
  end procedure reset
end submodule child_mod
""",
            "units.f90": """
type :: global_state_t
  integer :: id
end type global_state_t
interface global_callback
  subroutine global_step()
  end subroutine global_step
end interface global_callback
program driver
  use api_mod
end program driver
""",
        }
    )

    module = project.modules["api_mod"]
    submodule = project.submodules["api_mod:child_mod"]

    assert set(project.modules) == {"api_mod"}
    assert set(project.submodules) == {"api_mod:child_mod"}
    assert set(project.programs) == {"driver"}
    assert project.dependencies == {
        "api_mod": set(),
        "api_mod:child_mod": {"api_mod"},
        "driver": {"api_mod"},
    }
    assert set(project.procedures) == {"api_mod.step", "step", "api_mod:child_mod.reset", "reset"}
    assert project.procedures["api_mod.step"] is project.procedures["step"] is module.procedures[0]
    assert project.procedures["api_mod:child_mod.reset"] is project.procedures["reset"] is submodule.procedures[0]
    assert set(project.derived_types) == {
        "api_mod.state_t",
        "state_t",
        "api_mod:child_mod.child_state_t",
        "child_state_t",
        "global_state_t",
    }
    assert project.derived_types["api_mod.state_t"] is project.derived_types["state_t"]
    assert project.derived_types["api_mod:child_mod.child_state_t"] is project.derived_types["child_state_t"]
    assert set(project.interfaces) == {
        "api_mod.callback",
        "callback",
        "api_mod:child_mod.child_callback",
        "child_callback",
        "global_callback",
    }
    assert project.interfaces["api_mod.callback"] is project.interfaces["callback"]
    assert project.interfaces["api_mod:child_mod.child_callback"] is project.interfaces["child_callback"]


@pytest.mark.parametrize("standalone_first", [False, True])
def test_standalone_procedure_owns_unqualified_name_shared_with_module_member(standalone_first):
    module_source = """
module nan_mod
contains
  logical function sisnan(value)
    real, intent(in) :: value
  end function sisnan
end module nan_mod
"""
    standalone_source = """
logical function sisnan(value)
  real, intent(in) :: value
end function sisnan
"""
    sources = [("standalone.f90", standalone_source), ("module.f90", module_source)]
    if not standalone_first:
        sources.reverse()

    project = parse_fortran_project(dict(sources))
    module_procedure = project.modules["nan_mod"].procedures[0]
    standalone_procedure = next(procedure for parsed_file in project.files for procedure in parsed_file.procedures)

    assert project.procedures["nan_mod.sisnan"] is module_procedure
    assert project.procedures["sisnan"] is standalone_procedure


def test_parse_file_preserves_top_level_models_but_limits_file_symbol_registry():
    parsed = FortranParser().parse_file(
        """
type :: file_state_t
end type file_state_t
interface file_callback
  subroutine on_file()
  end subroutine on_file
end interface file_callback
subroutine global_step()
end subroutine global_step
module api_mod
contains
  subroutine module_step()
  end subroutine module_step
end module api_mod
""",
        filename="parse_file_contract.f90",
    )

    assert [dtype.name for dtype in parsed.derived_types] == ["file_state_t"]
    assert [interface.name for interface in parsed.interfaces] == ["file_callback"]
    assert [procedure.name for procedure in parsed.procedures] == ["global_step"]
    assert [module.name for module in parsed.modules] == ["api_mod"]
    assert set(parsed.symbols) == {"api_mod", "global_step"}
    assert parsed.symbols["api_mod"] is parsed.modules[0]
    assert parsed.symbols["global_step"] is parsed.procedures[0]


@pytest.mark.parametrize(
    ("unit", "scope"),
    [
        pytest.param("module shared\nend module shared\n", "module", id="module"),
        pytest.param("subroutine shared()\nend subroutine shared\n", "procedure", id="procedure"),
        pytest.param("program shared\nend program shared\n", "program", id="program"),
    ],
)
def test_parse_project_rejects_duplicate_units_across_files_with_project_scope_metadata(unit, scope):
    with pytest.raises(FortranParseError) as duplicate:
        parse_fortran_project({"first.f90": unit, "second.f90": unit})

    assert duplicate.value.base_message == f"Duplicate symbol 'shared' in project {scope} scope."
    assert (duplicate.value.filename, duplicate.value.line_number, duplicate.value.source_line) == (None, None, None)
    assert duplicate.value.code == "PARSE_DUPLICATE_SYMBOL"


def test_project_with_cyclic_module_uses_still_parses_every_file():
    project = parse_fortran_project(
        {
            "left.f90": "module left_mod\n  use right_mod\nend module left_mod\n",
            "right.f90": "module right_mod\n  use left_mod\nend module right_mod\n",
        }
    )

    assert [parsed.filename for parsed in project.files] == ["left.f90", "right.f90"]
    assert project.dependencies == {"left_mod": {"right_mod"}, "right_mod": {"left_mod"}}


@pytest.mark.parametrize("as_directory", [False, True], ids=["path-list", "directory"])
def test_project_encoding_is_forwarded_to_file_parsing(tmp_path: Path, as_directory: bool):
    source = tmp_path / "latin1.f90"
    source.write_bytes("! caf\xe9\nmodule encoded_mod\nend module encoded_mod\n".encode("latin-1"))

    project = parse_fortran_project(tmp_path if as_directory else [source], encoding="latin-1")

    assert set(project.modules) == {"encoded_mod"}
    assert project.files[0].encoding == "latin-1"
    assert project.files[0].source.startswith("! caf\xe9")


@pytest.mark.parametrize(
    ("statement", "forbids_typing"),
    [
        pytest.param("implicit none", True, id="plain"),
        pytest.param("implicit none (type)", True, id="type"),
        pytest.param("implicit none (type, external)", True, id="type-and-external"),
        pytest.param("implicit none (external)", False, id="external-only"),
    ],
)
def test_implicit_none_specifiers_decide_whether_undeclared_dummies_are_typed(statement: str, forbids_typing: bool):
    """Only NONE or NONE(TYPE) forbids implicit typing; NONE(EXTERNAL) keeps it."""
    source = f"""
subroutine scale(n)
  {statement}
end subroutine scale
"""
    if forbids_typing:
        with pytest.raises(FortranParseError, match="implicit none is active"):
            parse_fortran_file(source)
        return
    (argument,) = parse_fortran_file(source).procedures[0].arguments
    assert argument.base_type == "integer"
