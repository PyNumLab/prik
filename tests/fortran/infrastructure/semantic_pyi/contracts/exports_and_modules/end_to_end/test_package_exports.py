"""Editable package-entry contracts shape module namespaces."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
)
from prik import build_pyi_extension

MODULE_FIXTURES = Path(__file__).parents[5] / "modules" / "end_to_end" / "fixtures"
EDITED_ENTRIES = Path(__file__).parent / "fixtures" / "edited_contracts" / "module_exports"
SOURCE = MODULE_FIXTURES / "module_exports.f90"
BASE_CONTRACT = MODULE_FIXTURES / "contracts" / "module_exports"
UPDATE_DECLARATION = "\ndef update() -> Int32: ...\n"
pytestmark = pytest.mark.fortran_end_to_end


def _editable_package(
    tmp_path: Path,
    name: str,
    entry_fixture: str | None = None,
    module1_fixture: str | None = None,
    facade_fixture: str | None = None,
) -> Path:
    package = tmp_path / name
    shutil.copytree(BASE_CONTRACT, package)
    if entry_fixture is not None:
        package.joinpath("__init__.pyi").write_text(
            EDITED_ENTRIES.joinpath(entry_fixture).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    if module1_fixture is not None:
        shutil.copyfile(EDITED_ENTRIES / module1_fixture, package / "module1.pyi")
    if facade_fixture is not None:
        shutil.copyfile(EDITED_ENTRIES / facade_fixture, package / "facade.pyi")
    return package


def _build(package: Path, native_object: Path):
    result = build_pyi_extension(
        package / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=package.parent / f"{package.name}_build",
    )
    return _import_from_build_dir(result.module_name, result.output_dir)


def test_entry_contract_selects_child_flattened_aliased_and_bound_exports(tmp_path: Path):
    native_object = _compile_native_object(SOURCE, tmp_path / "native")

    child = _build(_editable_package(tmp_path, "child_api"), native_object)
    assert child.module1.func1() == np.int32(1)
    assert child.module2.func2() == np.int32(2)
    assert child.standalone() == np.int32(3)
    assert not hasattr(child, "func1")

    flattened_package = _editable_package(tmp_path, "flattened_api", "flatten.pyi")
    for leaf_name in ("module1.pyi", "module2.pyi"):
        leaf = flattened_package / leaf_name
        leaf.write_text(
            leaf.read_text(encoding="utf-8").replace(UPDATE_DECLARATION, "\n"),
            encoding="utf-8",
        )
    flattened = _build(flattened_package, native_object)
    assert flattened.func1() == np.int32(1)
    assert flattened.func2() == np.int32(2)
    assert flattened.standalone() == np.int32(3)
    assert not hasattr(flattened, "module1")
    assert not hasattr(flattened, "module2")

    aliased = _build(
        _editable_package(
            tmp_path,
            "aliased_api",
            "aliases.pyi",
            "module1_added_binding.pyi",
            "facade.pyi",
        ),
        native_object,
    )
    assert aliased.solve() == np.int32(1)
    assert aliased.update_module1() == np.int32(11)
    assert aliased.update_module2() == np.int32(22)
    assert aliased.renamed_standalone() == np.int32(3)
    assert aliased.m2.branch.func2() == np.int32(2)
    assert not hasattr(aliased, "Int32")
    assert not hasattr(aliased, "bind")
    assert not hasattr(aliased, "facade")
    assert not hasattr(aliased, "func1")
    assert not hasattr(aliased, "standalone")
    assert not hasattr(aliased, "update")
    assert not hasattr(aliased, "module1")
    assert not hasattr(aliased, "module2")


def test_entry_contract_rejects_colliding_wildcard_exports(tmp_path: Path):
    package = _editable_package(tmp_path, "colliding_api", "collision.pyi")

    with pytest.raises(ValueError, match=r"Conflicting \.pyi exports for 'update'"):
        build_pyi_extension(
            package / "__init__.pyi",
            native_objects=[tmp_path / "unused.o"],
        )
