"""Module source resolution follows `use` from entry sources to the files that define each module."""

from __future__ import annotations

from pathlib import Path

import pytest

from prik.parsers.fortran import FortranParseError
from prik.parsers.fortran.module_sources import resolve_fortran_module_sources


def _write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _resolve(entries, search):
    return resolve_fortran_module_sources(entries, search, lambda path: path.read_text(encoding="utf-8"))


def test_used_modules_resolve_transitively_dependencies_first(tmp_path: Path):
    """File names and directories are irrelevant; intrinsic modules need no source."""
    base = _write(tmp_path, "lib/deep/b-defs.f90", "module base\nuse, intrinsic :: iso_c_binding\nend module base\n")
    middle = _write(tmp_path, "lib/middle.F90", "module middle\nuse base\nend module middle\n")
    entry = _write(tmp_path, "app/entry.f90", "module app\nuse middle\nuse iso_fortran_env\nend module app\n")

    assert _resolve([entry], [tmp_path / "lib"]) == (base.resolve(), middle.resolve(), entry)


def test_a_module_an_entry_defines_is_not_searched_for(tmp_path: Path):
    """A second definition under a search directory does not compete with an entry's own."""
    _write(tmp_path, "search/copy.f90", "module shared\nend module shared\n")
    shared = _write(tmp_path, "shared.f90", "module shared\nend module shared\n")
    user = _write(tmp_path, "user.f90", "module user\nuse shared\nend module user\n")

    assert _resolve([user, shared], [tmp_path / "search"]) == (shared, user)


@pytest.mark.parametrize(
    ("definitions", "code"),
    [
        pytest.param((), "PARSE_MODULE_SOURCE_NOT_FOUND", id="missing"),
        pytest.param(("one.f90", "two.f90"), "PARSE_AMBIGUOUS_MODULE_SOURCE", id="ambiguous"),
    ],
)
def test_a_used_module_needs_exactly_one_defining_source(tmp_path: Path, definitions, code: str):
    for name in definitions:
        _write(tmp_path, f"search/{name}", "module needed\nend module needed\n")
    (tmp_path / "search").mkdir(exist_ok=True)
    entry = _write(tmp_path, "entry.f90", "module entry\nuse needed\nend module entry\n")

    with pytest.raises(FortranParseError, match="needed") as error:
        _resolve([entry], [tmp_path / "search"])

    assert error.value.code == code
