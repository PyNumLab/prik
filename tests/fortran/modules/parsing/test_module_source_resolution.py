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


requires_gfortran = pytest.mark.skipif(shutil.which("gfortran") is None, reason="requires gfortran preprocessing")


def _preprocessed_resolve(entries, search):
    config = PreprocessingConfig(mode="compiler", compiler="gfortran")
    return resolve_fortran_module_sources(
        entries,
        search,
        lambda path: preprocess_source(path, language="fortran", config=config).source,
        command_line_macros=False,
    )


MACRO_NAMED = "#define MODNAME {name}\nmodule MODNAME\n  integer, parameter :: answer = 42\nend module MODNAME\n"


@requires_gfortran
def test_a_module_named_through_a_macro_is_found_by_its_preprocessed_text(tmp_path: Path):
    """A module a macro names is located, and a source that cannot be preprocessed defines nothing."""
    generated = _write(tmp_path, "lib/gen.F90", MACRO_NAMED.format(name="generated_mod"))
    _write(tmp_path, "lib/broken.F90", '#include "missing_header.h"\nmodule broken\nend module broken\n')
    entry = _write(tmp_path, "app.f90", "module app\n  use generated_mod, only: answer\nend module app\n")

    assert _preprocessed_resolve([entry], [tmp_path / "lib"]) == (generated.resolve(), entry)


@requires_gfortran
def test_a_macro_named_user_module_shadows_the_processor_module_it_is_named_after(tmp_path: Path):
    """A ``use`` stating no nature falls back to the processor only when no source defines the module."""
    user_module = _write(tmp_path, "lib/ieee.F90", MACRO_NAMED.format(name="ieee_arithmetic"))
    entry = _write(tmp_path, "app.f90", "module app\n  use ieee_arithmetic, only: answer\nend module app\n")

    assert _preprocessed_resolve([entry], [tmp_path / "lib"]) == (user_module.resolve(), entry)


@requires_gfortran
def test_a_macro_named_second_definition_makes_a_module_ambiguous(tmp_path: Path):
    """One definition visible in the raw text does not hide another that only preprocessing reveals."""
    _write(tmp_path, "lib/plain.f90", "module shared_mod\nend module shared_mod\n")
    _write(tmp_path, "lib/generated.F90", MACRO_NAMED.format(name="shared_mod"))
    entry = _write(tmp_path, "app.f90", "module app\n  use shared_mod\nend module app\n")

    with pytest.raises(FortranParseError, match="shared_mod") as error:
        _preprocessed_resolve([entry], [tmp_path / "lib"])

    assert error.value.code == "PARSE_AMBIGUOUS_MODULE_SOURCE"


@requires_gfortran
def test_reading_every_source_for_one_module_selects_none_of_the_others(tmp_path: Path):
    """Locating a macro-named module reads every source, but a later module is still checked for uniqueness."""
    _write(tmp_path, "lib/gen.F90", MACRO_NAMED.format(name="aa_generated"))
    _write(tmp_path, "lib/one.f90", "module zz_dup\nend module zz_dup\n")
    _write(tmp_path, "lib/two.f90", "module zz_dup\nend module zz_dup\n")
    entry = _write(tmp_path, "app.f90", "module app\n  use aa_generated\n  use zz_dup\nend module app\n")

    with pytest.raises(FortranParseError, match="zz_dup") as error:
        _preprocessed_resolve([entry], [tmp_path / "lib"])

    assert error.value.code == "PARSE_AMBIGUOUS_MODULE_SOURCE"


@pytest.mark.parametrize("non_intrinsic_first", [False, True])
def test_scopes_in_one_file_that_name_a_module_differently_are_each_honored(tmp_path: Path, non_intrinsic_first: bool):
    """One scope's ``intrinsic`` use never cancels another scope's need for the module's source."""
    user_module = _write(
        tmp_path, "lib/ieee.f90", "module ieee_arithmetic\n  integer :: mine\nend module ieee_arithmetic\n"
    )
    processor = "module a\n  use, intrinsic :: ieee_arithmetic\nend module a\n"
    source = "module b\n  use, non_intrinsic :: ieee_arithmetic, only: mine\nend module b\n"
    entry = _write(tmp_path, "app.f90", source + processor if non_intrinsic_first else processor + source)

    assert _resolve([entry], [tmp_path / "lib"]) == (user_module.resolve(), entry)


def test_uses_inside_internal_procedures_and_block_constructs_are_followed(tmp_path: Path):
    """A nested scope's ``use`` is a dependency of the file even though its host cannot see it."""
    inner = _write(tmp_path, "lib/inner.f90", "module inner_mod\nend module inner_mod\n")
    block = _write(tmp_path, "lib/block.f90", "module block_mod\nend module block_mod\n")
    entry = _write(
        tmp_path,
        "app.f90",
        """module app
contains
  subroutine run()
    block
      use block_mod
    end block
  contains
    subroutine helper()
      use inner_mod
    end subroutine helper
  end subroutine run
end module app
""",
    )

    assert set(_resolve([entry], [tmp_path / "lib"])) == {inner.resolve(), block.resolve(), entry}


def test_same_named_submodules_of_different_ancestors_are_separate_units(tmp_path: Path):
    """``a:impl`` and ``b:impl`` are two submodules, and each nested child finds its own parent."""
    units = {}
    for ancestor in ("a", "b"):
        units[ancestor] = _write(tmp_path, f"lib/{ancestor}.f90", f"module {ancestor}\nend module {ancestor}\n")
        units[f"{ancestor}:impl"] = _write(
            tmp_path, f"lib/{ancestor}_impl.f90", f"submodule ({ancestor}) impl\nend submodule impl\n"
        )
    leaves = [
        _write(tmp_path, f"{ancestor}_leaf.f90", f"submodule ({ancestor}:impl) leaf\nend submodule leaf\n")
        for ancestor in ("a", "b")
    ]

    resolved = _resolve(leaves, [tmp_path / "lib"])

    assert set(resolved) == {path.resolve() for path in units.values()} | set(leaves)
    for ancestor, leaf in zip(("a", "b"), leaves, strict=True):
        order = resolved.index
        assert order(units[ancestor].resolve()) < order(units[f"{ancestor}:impl"].resolve()) < order(leaf)


def test_submodules_implementing_a_used_module_are_selected_with_it(tmp_path: Path):
    """No ``use`` names a submodule, yet the module's separate procedures are implemented there."""
    api = _write(
        tmp_path,
        "lib/api.f90",
        "module api\n  interface\n    module subroutine run()\n    end subroutine run\n  end interface\nend module api\n",
    )
    impl = _write(tmp_path, "lib/impl/api_impl.f90", "submodule (api) impl\nend submodule impl\n")
    leaf = _write(
        tmp_path,
        "lib/impl/api_leaf.f90",
        "submodule (api:impl) leaf\ncontains\n  module subroutine run()\n  end subroutine run\nend submodule leaf\n",
    )
    _write(tmp_path, "lib/other.f90", "module other\nend module other\nsubmodule (other) impl\nend submodule impl\n")
    entry = _write(tmp_path, "app.f90", "module app\n  use api\nend module app\n")

    resolved = _resolve([entry], [tmp_path / "lib"])

    assert set(resolved) == {api.resolve(), impl.resolve(), leaf.resolve(), entry}
    assert resolved.index(api.resolve()) < resolved.index(impl.resolve()) < resolved.index(leaf.resolve())
