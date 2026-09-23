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


def test_module_identity_ignores_same_named_external_root(tmp_path: Path):
    source = tmp_path / "foo.f90"
    source.write_text(
        """module foo
contains
  subroutine chosen()
  end subroutine chosen
end module foo

subroutine external()
end subroutine external
""",
        encoding="utf-8",
    )
    exports = tmp_path / "exports.txt"
    exports.write_text("foo::chosen\n", encoding="utf-8")
    contract = tmp_path / "contract"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(source),
            "--export-symbols",
            str(exports),
            "--out",
            str(contract),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert {path.name for path in contract.iterdir()} == {"__init__.pyi", "foo.pyi"}
    assert "def chosen(" in (contract / "foo.pyi").read_text(encoding="utf-8")
    assert "external" not in (contract / "foo.pyi").read_text(encoding="utf-8")


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


@pytest.mark.skipif(shutil.which("gfortran") is None, reason="requires gfortran")
def test_facade_selection_and_contract_replay_share_generic_and_native_variable(tmp_path: Path):
    """A selected facade binds one generic and one live native scalar in both lanes."""
    sources = tuple((NATIVE.parent / "export_selection_facade" / name) for name in ("owner.f90", "facade.f90"))
    exports = tmp_path / "exports.txt"
    exports.write_text("facade::run\nfacade::marker\n", encoding="utf-8")
    contract = tmp_path / "contract"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            *map(str, sources),
            "--export-symbols",
            str(exports),
            "--out",
            str(contract),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    facade_contract = (contract / "facade.pyi").read_text(encoding="utf-8")
    owner_contract = (contract / "owner.pyi").read_text(encoding="utf-8")
    assert "from .owner import" in facade_contract
    assert '"run"' in facade_contract and '"marker"' in facade_contract
    assert '@native_module("facade")' in owner_contract
    assert "marker: Annotated[Int32, NativeStorage]" in owner_contract

    source = build_fortran_extension(
        sources,
        output_name="facade_source",
        output_dir=tmp_path / "source",
        export_symbols=("facade::run", "facade::marker"),
        jobs=2,
    )
    replay = build_pyi_extension(
        contract / "__init__.pyi",
        native_fortran_sources=sources,
        output_name="facade_replay",
        output_dir=tmp_path / "replay",
        jobs=2,
    )
    for result in (source, replay):
        module = _import_from_build_dir(result.module_name, result.output_dir).facade
        assert module.run() == np.int32(7)
        assert isinstance(module.marker, np.ndarray) and module.marker.shape == ()
        module.marker[()] = np.int32(11)
        assert module.run() == np.int32(11)
