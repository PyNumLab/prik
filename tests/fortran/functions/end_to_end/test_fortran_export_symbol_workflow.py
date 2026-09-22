"""Generated contracts and runtime builds share Fortran export selection."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import shutil

import numpy as np
import pytest

from prik import build_fortran_extension, build_pyi_extension
from tests.fortran._support.wrapper_build import _import_from_build_dir


FIXTURES = Path(__file__).parent / "fixtures"
NATIVE = FIXTURES / "native" / "export_selection"
SOURCES = tuple(NATIVE / name for name in ("kinds.f90", "callbacks.f90", "selected.f90", "unrelated.f90"))
EXPORTS = ("selected_solver_mod::solve",)
pytestmark = pytest.mark.fortran_end_to_end


def _generate_contract(tmp_path: Path) -> Path:
    contract = tmp_path / "contract"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            *map(str, SOURCES),
            "--export-symbols",
            str(FIXTURES / "export_symbols.txt"),
            "--out",
            str(contract),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return contract


def test_generate_pyi_emits_only_the_selected_module_and_callback_dependency(tmp_path: Path):
    contract = _generate_contract(tmp_path)

    assert {path.name for path in contract.iterdir()} == {
        "__init__.pyi",
        "export_callbacks_mod.pyi",
        "selected_solver_mod.pyi",
    }
    selected = (contract / "selected_solver_mod.pyi").read_text(encoding="utf-8")
    assert "def solve(" in selected
    assert "hidden_solver" not in selected
    assert "from .export_callbacks_mod import report" in selected
    assert '__all__ = ["solve"]' in selected
    assert '__all__ = ["selected_solver_mod"]' in (contract / "__init__.pyi").read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("gfortran") is None, reason="requires gfortran")
def test_source_and_generated_contract_builds_publish_and_run_the_same_callback(tmp_path: Path):
    source_result = build_fortran_extension(
        SOURCES,
        output_dir=tmp_path / "source_build",
        output_name="selected_exports",
        export_symbols=EXPORTS,
        jobs=2,
    )
    contract = _generate_contract(tmp_path)
    contract_result = build_pyi_extension(
        contract / "__init__.pyi",
        native_fortran_sources=SOURCES,
        output_dir=tmp_path / "contract_build",
        output_name="selected_contract",
        jobs=2,
    )
    for result in (source_result, contract_result):
        root = _import_from_build_dir(result.module_name, result.output_dir)
        assert {name for name in dir(root) if not name.startswith("_")} == {"selected_solver_mod"}
        module = root.selected_solver_mod
        assert {name for name in dir(module) if not name.startswith("_")} == {"solve"}
        seen = []

        def callback(value, status, *, observed=seen):
            observed.append((value, status))

        assert module.solve(np.int32(4), callback) == np.int32(5)
        assert seen == [(np.int32(5), None)]
