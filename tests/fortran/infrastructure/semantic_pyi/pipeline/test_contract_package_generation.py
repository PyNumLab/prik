"""Explicit Fortran `--pyi --out` contract package generation tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tests.fortran._support.pyi_fixtures import assert_generated_pyi_package_matches_fixture

FIXTURES = Path(__file__).parent / "fixtures"
NATIVE_FIXTURES = FIXTURES / "native"
CONTRACT_FIXTURES = FIXTURES / "contracts"
SOURCE_NAMESPACE = NATIVE_FIXTURES / "contract_mixed_module_external.f90"
STANDALONE_ONLY = NATIVE_FIXTURES / "contract_standalone_only.f90"
SAME_NAME_MIXED = NATIVE_FIXTURES / "contract_same_name.f90"
TRANSITIVE_NATIVE = NATIVE_FIXTURES / "contract_import_graph.f90"
MULTI_MODULE = NATIVE_FIXTURES / "contract_multi_module.f90"


@pytest.mark.parametrize(
    "source",
    [STANDALONE_ONLY, SOURCE_NAMESPACE, SAME_NAME_MIXED, TRANSITIVE_NATIVE],
    ids=lambda path: path.stem,
)
def test_generated_contract_package_matches_reviewed_layout(source: Path, tmp_path: Path):
    """The CLI writes an explicit `__init__.pyi` entry plus one leaf per native module, as reviewed."""
    package = tmp_path / "contracts" / source.stem
    subprocess.run(
        [sys.executable, "-m", "prik", "generate", "--pyi", str(source), "--out", str(package)],
        capture_output=True,
        text=True,
        check=True,
    )

    assert_generated_pyi_package_matches_fixture(package, CONTRACT_FIXTURES / source.stem / "generated")


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
        "from . import contract_left_mod\nfrom . import contract_right_mod\n\n"
        '__all__ = ["contract_left_mod", "contract_right_mod"]\n'
    )
