"""Explicit Fortran `--pyi --out` contract package generation tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tests.fortran._support.pyi_fixtures import assert_generated_pyi_package_matches_fixture

FIXTURES = Path(__file__).parent / "fixtures"
NATIVE_FIXTURES = FIXTURES / "native"
CONTRACT_FIXTURES = FIXTURES / "contracts"
SOURCE_NAMESPACE = NATIVE_FIXTURES / "contract_mixed_module_external.f90"
STANDALONE_ONLY = NATIVE_FIXTURES / "contract_standalone_only.f90"
SAME_NAME_MIXED = NATIVE_FIXTURES / "contract_same_name.f90"
TRANSITIVE_NATIVE = NATIVE_FIXTURES / "contract_import_graph.f90"
MULTI_MODULE = NATIVE_FIXTURES / "contract_multi_module.f90"


def _generate_contract_package(source: Path, package: Path) -> Path:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(source),
            "--out",
            str(package),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert_generated_pyi_package_matches_fixture(
        package,
        CONTRACT_FIXTURES / source.stem / "generated",
    )
    return package / "__init__.pyi"


def test_standalone_generation_writes_explicit_package_entry(tmp_path: Path):
    entry = _generate_contract_package(
        STANDALONE_ONLY,
        tmp_path / "contracts" / "contract_standalone_only",
    )

    assert entry == tmp_path / "contracts" / "contract_standalone_only" / "__init__.pyi"
    assert {path.name for path in entry.parent.iterdir()} == {"__init__.pyi"}
    text = entry.read_text(encoding="utf-8")
    assert text.count("@external") == 2
    assert "def standalone_ping() -> None: ..." in text
    assert "def standalone_double(" in text


def test_module_generation_writes_explicit_package_entry_and_native_leaf(tmp_path: Path):
    entry = _generate_contract_package(
        SOURCE_NAMESPACE,
        tmp_path / "contracts" / "contract_mixed_module_external",
    )

    assert entry == tmp_path / "contracts" / "contract_mixed_module_external" / "__init__.pyi"
    assert {path.name for path in entry.parent.iterdir()} == {
        "__init__.pyi",
        "contract_math_mod.pyi",
    }
    assert entry.read_text(encoding="utf-8").startswith(
        "from prik.contracts import Addr, Arg, Int32, external, native_call\n"
        "from . import contract_math_mod\n\n"
        "@external\n"
    )


def test_same_named_module_uses_init_entry_and_keeps_externals_at_root(tmp_path: Path):
    entry = _generate_contract_package(
        SAME_NAME_MIXED,
        tmp_path / "contracts" / "contract_same_name",
    )

    assert entry == tmp_path / "contracts" / "contract_same_name" / "__init__.pyi"
    assert {path.name for path in entry.parent.iterdir()} == {"__init__.pyi", "contract_same_name.pyi"}
    assert entry.read_text(encoding="utf-8") == (
        "from prik.contracts import external\n"
        "from . import contract_same_name\n\n"
        "@external\n"
        "def external_ping() -> None: ...\n"
    )
    assert "def module_ping() -> None: ..." in (entry.parent / "contract_same_name.pyi").read_text(encoding="utf-8")


def test_import_graph_generation_writes_entry_and_native_leaves(tmp_path: Path):
    entry = _generate_contract_package(
        TRANSITIVE_NATIVE,
        tmp_path / "contracts" / "contract_import_graph",
    )

    assert entry == tmp_path / "contracts" / "contract_import_graph" / "__init__.pyi"
    assert {path.name for path in entry.parent.iterdir()} == {"__init__.pyi", "deep.pyi", "m1.pyi"}
    assert entry.read_text(encoding="utf-8") == "from . import m1\nfrom . import deep\n"


def test_multi_module_generation_keeps_each_native_namespace(tmp_path: Path):
    package = tmp_path / "contracts" / "contract_multi_module"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(MULTI_MODULE),
            "--out",
            str(package),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert {path.name for path in package.iterdir()} == {
        "__init__.pyi",
        "contract_left_mod.pyi",
        "contract_right_mod.pyi",
    }
    assert (package / "__init__.pyi").read_text(encoding="utf-8") == (
        "from . import contract_left_mod\nfrom . import contract_right_mod\n"
    )
