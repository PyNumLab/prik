"""Multi-file `generate --pyi`: imported interfaces reach a buildable contract."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _compiler, _import_from_build_dir
from prik import build_pyi_extension
from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.semantics.native_contract import native_contract_issues

pytestmark = pytest.mark.fortran_end_to_end

PINTRF_SOURCE = """
module pintrf_mod
  implicit none
  private
  public :: OBJ

  abstract interface
    subroutine OBJ(x, f)
      implicit none
      real(8), intent(in) :: x
      real(8), intent(out) :: f
    end subroutine OBJ
  end interface
end module pintrf_mod
"""

SOLVER_SOURCE = """
module solver_mod
  use, non_intrinsic :: pintrf_mod, only : OBJ
  implicit none
contains
  subroutine minimize(calfun, x, f)
    procedure(OBJ) :: calfun
    real(8), intent(in) :: x
    real(8), intent(out) :: f

    call calfun(x, f)
  end subroutine minimize
end module solver_mod
"""

RENAMED_SOURCE = """
module renamed_mod
  use, non_intrinsic :: pintrf_mod, only : LOCAL_OBJ => OBJ
  implicit none
contains
  subroutine minimize_renamed(calfun, x, f)
    procedure(LOCAL_OBJ) :: calfun
    real(8), intent(in) :: x
    real(8), intent(out) :: f

    call calfun(x, f)
  end subroutine minimize_renamed
end module renamed_mod
"""


def _generate_contracts(tmp_path: Path) -> tuple[Path, list[Path]]:
    sources = []
    for name, text in (
        ("pintrf.f90", PINTRF_SOURCE),
        ("solver.f90", SOLVER_SOURCE),
        ("renamed.f90", RENAMED_SOURCE),
    ):
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        sources.append(path)
    contracts = tmp_path / "contracts"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            *[str(path) for path in sources],
            "--out",
            str(contracts),
            "--compiler",
            _compiler(),
        ],
        check=True,
        capture_output=True,
    )
    return contracts, sources


def test_multi_file_generation_places_the_prototype_with_its_declaring_module(tmp_path: Path):
    """Each module's contract records what that module declares or imports.

    The per-file CLI conversion path is where an imported interface previously
    degraded to an opaque placeholder, so this exercises that workflow rather
    than whole-project conversion.
    """
    contracts, _sources = _generate_contracts(tmp_path)

    declaring = (contracts / "pintrf_mod.pyi").read_text(encoding="utf-8")
    assert "@prototype\ndef OBJ(" in declaring

    consuming = (contracts / "solver_mod.pyi").read_text(encoding="utf-8")
    assert "from pintrf_mod import OBJ" in consuming
    assert "calfun: OBJ" in consuming

    renamed = (contracts / "renamed_mod.pyi").read_text(encoding="utf-8")
    assert "from pintrf_mod import OBJ as LOCAL_OBJ" in renamed
    assert "calfun: LOCAL_OBJ" in renamed


def test_generated_multi_file_contracts_parse_without_native_contract_issues(tmp_path: Path):
    """PRIK must be able to read back every contract it just wrote."""
    contracts, _sources = _generate_contracts(tmp_path)

    for contract in sorted(contracts.glob("*.pyi")):
        if contract.name == "__init__.pyi":
            continue
        module = pyi_text_to_semantic_module(contract.read_text(encoding="utf-8"), module_name=contract.stem)
        assert native_contract_issues(module) == [], contract.name


def test_building_from_generated_multi_file_contracts_runs_the_callback(tmp_path: Path):
    """The whole route must survive: source, contract, parse, build, call."""
    contracts, sources = _generate_contracts(tmp_path)
    result = build_pyi_extension(
        contracts / "__init__.pyi",
        input_compiler=_compiler(),
        native_fortran_sources=[str(path) for path in sources],
        output_dir=tmp_path / "build",
        output_name="multi_file_callbacks",
    )
    module = _import_from_build_dir(result.module_name, result.output_dir)

    def objective(x, f):
        f[...] = float(x) ** 2

    assert module.solver_mod.minimize(objective, np.float64(3.0)) == np.float64(9.0)
    assert module.renamed_mod.minimize_renamed(objective, np.float64(4.0)) == np.float64(16.0)
