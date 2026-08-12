"""Public parser entrypoints and source/path input contracts."""

import pytest

from prik.parsers.fortran import FortranParseError, FortranParser, parse_fortran_file, parse_fortran_project
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules


def test_parser_public_entrypoint_aliases_and_singular_contracts_use_inline_sources():
    parser = FortranParser()
    module_code = """
module alias_mod
contains
  subroutine ping(x)
    integer, intent(in) :: x
  end subroutine ping
end module alias_mod
"""

    assert parser.parse_file(module_code).modules[0].name == "alias_mod"
    assert parser.parse_file(module_code).modules[0].procedures[0].name == "ping"
    assert "alias_mod" in parser.parse_project({"alias.f90": module_code}).modules
    assert "alias_mod.ping" in parser.parse_project({"alias.f90": module_code}).procedures

    assert parser.parse_module("module single_mod\nend module single_mod\n").name == "single_mod"
    assert parser.parse_program("program driver\nend program driver\n").name == "driver"
    assert parser.parse_derived_type("type :: state_t\nend type state_t\n").name == "state_t"
    assert (
        parser.parse_interface(
            """
interface callback
  subroutine cb()
  end subroutine cb
end interface callback
"""
        ).name
        == "callback"
    )
    assert parser.parse_submodule("submodule (parent_mod) child_mod\nend submodule child_mod\n").name == "child_mod"
    assert (
        parser.parse_block_data("block data init_data\n  integer seed\nend block data init_data\n").name == "init_data"
    )

    with pytest.raises(FortranParseError, match="none were found"):
        parser.parse_module("program not_a_module\nend program not_a_module\n")

    with pytest.raises(FortranParseError, match="found 2"):
        parser.parse_module(
            """
module first_mod
end module first_mod
module second_mod
end module second_mod
"""
        )


def test_fortran_parser_package_exports_the_supported_parser_api():
    parsed_fortran = FortranParser().parse_file(
        """
subroutine work(n)
  integer, intent(in) :: n
end subroutine work
"""
    )

    assert fortran_file_to_semantic_modules(parsed_fortran)[0].functions[0].name == "work"


def test_file_path_and_unknown_filename_public_parse_paths(tmp_path):
    source_path = tmp_path / "path_input.f90"
    source_path.write_text(
        """
subroutine from_path(i)
  integer, intent(in) :: i
end subroutine from_path
""",
        encoding="utf-8",
    )

    parsed_from_path = parse_fortran_file(source_path)
    parsed_unknown_suffix = parse_fortran_file(
        """
subroutine from_unknown(i)
  integer, intent(in) :: i
end subroutine from_unknown
""",
        filename="from_unknown.src",
    )
    with pytest.raises(FortranParseError, match="Invalid Fortran syntax"):
        parse_fortran_file(12345)

    assert parsed_from_path.filename == str(source_path)
    assert parsed_from_path.format == "modern"
    assert parsed_from_path.procedures[0].name == "from_path"
    assert parsed_unknown_suffix.format == "unknown"


def test_public_instance_visitor_entrypoints_use_source_strings():
    parser = FortranParser()

    assert (
        parser.parse_file(
            """
subroutine alias_proc()
end subroutine alias_proc
"""
        )
        .procedures[0]
        .name
        == "alias_proc"
    )
    assert (
        "alias_mod"
        in parser.parse_project(
            {
                "alias_mod.f90": """
module alias_mod
end module alias_mod
"""
            }
        ).modules
    )

    with pytest.raises(FortranParseError, match="only standalone procedures were found"):
        parser.parse_module(
            """
subroutine lone_proc()
end subroutine lone_proc
"""
        )


@pytest.mark.parametrize(
    ("source", "expected_module"),
    [
        ("type :: file_state\nend type file_state\n", None),
        ("module owner_mod\n  type :: file_state\n  end type file_state\nend module owner_mod\n", "owner_mod"),
        (
            "submodule (parent_mod) owner_submod\n"
            "  type :: file_state\n"
            "  end type file_state\n"
            "end submodule owner_submod\n",
            "owner_submod",
        ),
        ("program driver\n  type :: file_state\n  end type file_state\nend program driver\n", None),
        (
            "subroutine work()\n  type :: file_state\n  end type file_state\nend subroutine work\n",
            None,
        ),
        (
            "module owner_mod\n"
            "contains\n"
            "  subroutine work()\n"
            "    type :: file_state\n"
            "    end type file_state\n"
            "  end subroutine work\n"
            "end module owner_mod\n",
            "owner_mod",
        ),
    ],
)
def test_public_derived_type_visitor_collects_nested_scope_sources(source, expected_module):
    dtype = FortranParser().parse_derived_type(source, filename="nested_type.f90")

    assert dtype.name == "file_state"
    assert dtype.module == expected_module


def test_public_project_parse_from_path_sequence(tmp_path):
    source_path = tmp_path / "listed_project.f90"
    source_path.write_text(
        """
module listed_project_mod
contains
  subroutine work()
  end subroutine work
end module listed_project_mod
""",
        encoding="utf-8",
    )

    project = parse_fortran_project([source_path])

    assert "listed_project_mod" in project.modules
    assert "listed_project_mod.work" in project.procedures
