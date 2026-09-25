"""Module source resolution follows `use` from entry sources to the files that define each module."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from prik.parsers.fortran import FortranParseError
from prik.parsers.fortran.module_sources import resolve_fortran_module_sources
from prik.preprocessing import PreprocessingConfig, preprocess_source


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


@pytest.mark.parametrize(
    ("statement", "user_source", "found"),
    [
        pytest.param("use, intrinsic :: iso_fortran_env", True, False, id="intrinsic-never-searched"),
        pytest.param("use, intrinsic :: vendor_runtime", False, False, id="unlisted-intrinsic-not-searched"),
        pytest.param("use, non_intrinsic :: iso_fortran_env", True, True, id="non-intrinsic-uses-the-source"),
        pytest.param("use iso_fortran_env", True, True, id="unstated-prefers-a-source"),
        pytest.param("use iso_fortran_env", False, False, id="unstated-falls-back-to-the-processor"),
        pytest.param("use ieee_arithmetic", False, False, id="unstated-ieee-module-falls-back-to-the-processor"),
    ],
)
def test_use_nature_decides_whether_a_module_source_is_needed(tmp_path: Path, statement, user_source, found):
    user_module = "module iso_fortran_env\nend module iso_fortran_env\n"
    definition = _write(tmp_path, "search/iso_fortran_env.f90", user_module) if user_source else None
    (tmp_path / "search").mkdir(exist_ok=True)
    entry = _write(tmp_path, "entry.f90", f"module entry\n  {statement}\nend module entry\n")

    resolved = _resolve([entry], [tmp_path / "search"])

    assert resolved == ((definition.resolve(), entry) if found else (entry,))


def test_explicit_non_intrinsic_module_without_a_source_is_not_found(tmp_path: Path):
    (tmp_path / "search").mkdir()
    entry = _write(tmp_path, "entry.f90", "module entry\n  use, non_intrinsic :: iso_fortran_env\nend module entry\n")

    with pytest.raises(FortranParseError) as error:
        _resolve([entry], [tmp_path / "search"])

    assert error.value.code == "PARSE_MODULE_SOURCE_NOT_FOUND"


def test_nested_submodule_resolves_its_direct_parent_before_the_ancestor_module(tmp_path: Path):
    """``submodule (base:middle) leaf`` needs the ``middle`` submodule, which needs ``base``."""
    base = _write(
        tmp_path,
        "src/base.f90",
        "module base\n  interface\n    module subroutine run()\n    end subroutine run\n  end interface\nend module base\n",
    )
    middle = _write(tmp_path, "src/impl/middle.f90", "submodule (base) middle\nend submodule middle\n")
    leaf = _write(
        tmp_path,
        "leaf.f90",
        "submodule (base:middle) leaf\ncontains\n  module subroutine run()\n  end subroutine run\nend submodule leaf\n",
    )

    assert _resolve([leaf], [tmp_path / "src"]) == (base.resolve(), middle.resolve(), leaf)


@pytest.mark.skipif(shutil.which("gfortran") is None, reason="requires gfortran preprocessing")
def test_a_module_named_through_a_macro_is_found_by_parsing_the_searched_sources(tmp_path: Path):
    """A ``module`` line the raw index cannot read is found once the preprocessed sources are parsed."""
    config = PreprocessingConfig(mode="compiler", compiler="gfortran")
    generated = _write(
        tmp_path,
        "lib/gen.F90",
        "#define MODNAME generated_mod\nmodule MODNAME\n  integer, parameter :: answer = 42\nend module MODNAME\n",
    )
    _write(tmp_path, "lib/broken.F90", '#include "missing_header.h"\nmodule broken\nend module broken\n')
    entry = _write(tmp_path, "app.f90", "module app\n  use generated_mod, only: answer\nend module app\n")

    resolved = resolve_fortran_module_sources(
        [entry],
        [tmp_path / "lib"],
        lambda path: preprocess_source(path, language="fortran", config=config).source,
    )

    assert resolved == (generated.resolve(), entry)
