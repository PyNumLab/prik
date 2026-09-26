"""Every entry point names the same Fortran sources and reads them in the same form.

Source suffixes, the fixed or free form of a file, and the sources a list of
files and directories names have one owner, so discovery, project parsing,
the CLIs, and a build agree on a path.
"""

from __future__ import annotations

from pathlib import Path

from prik import cli as prik_cli
from prik.parsers.fortran import parse_fortran_project
from prik.parsers.fortran import cli as fortran_parser_cli
from prik.parsers.fortran.module_sources import _searched_files
from prik.preprocessing.languages import FORTRAN_SOURCE_SUFFIXES, fortran_source_form, validated_source_paths


def test_every_entry_point_names_the_same_sources_under_a_directory(tmp_path: Path):
    """A ``.fpp`` file is a Fortran source everywhere; a text file is one nowhere."""
    root = tmp_path / "src"
    (root / "nested").mkdir(parents=True)
    free = root / "b.f90"
    free.write_text("module b\nend module b\n", encoding="utf-8")
    fixed = root / "nested" / "a.fpp"
    fixed.write_text("      module a\n      end module a\n", encoding="utf-8")
    (root / "notes.txt").write_text("not a source\n", encoding="utf-8")
    expected = {free, fixed}

    assert set(prik_cli._expand_paths([str(root)])) == expected
    assert {Path(name) for name in fortran_parser_cli._parse_paths([str(root)])} == expected
    assert {Path(parsed.filename) for parsed in parse_fortran_project(root).files} == expected
    assert set(_searched_files([root])) == {path.resolve() for path in expected}
    assert set(validated_source_paths([root], FORTRAN_SOURCE_SUFFIXES, label="Fortran")) == expected


def test_a_parsed_file_records_the_form_its_lexer_read():
    """``.fpp`` is fixed form; an unknown suffix is decided by column 6."""
    parsed = parse_fortran_project({"a.fpp": "      module a\n     &\n      end module a\n"}).files[0]

    assert parsed.format == fortran_source_form(parsed.source, "a.fpp") == "fixed"
    assert fortran_source_form("      x = 1\n     &  + 2\n", "legacy.src") == "fixed"
    assert fortran_source_form("x = 1\n", "modern.src") == "free"
