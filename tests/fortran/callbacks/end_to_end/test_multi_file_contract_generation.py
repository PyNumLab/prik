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

module scoped_rename_mod
  implicit none
contains
  subroutine minimize_scoped(calfun, x, f)
    use, non_intrinsic :: pintrf_mod, only : SCOPED_OBJ => OBJ
    implicit none
    procedure(SCOPED_OBJ) :: calfun
    real(8), intent(in) :: x
    real(8), intent(out) :: f

    call calfun(x, f)
  end subroutine minimize_scoped
end module scoped_rename_mod
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
    assert "from .pintrf_mod import OBJ" in consuming
    assert "calfun: OBJ" in consuming

    renamed = (contracts / "renamed_mod.pyi").read_text(encoding="utf-8")
    assert "from .pintrf_mod import OBJ as LOCAL_OBJ" in renamed
    assert "calfun: LOCAL_OBJ" in renamed

    # A procedure-local rename reaches the contract through the synthetic
    # prototype import rather than the module's own import list.
    scoped = (contracts / "scoped_rename_mod.pyi").read_text(encoding="utf-8")
    assert "from .pintrf_mod import OBJ as SCOPED_OBJ" in scoped
    assert "calfun: SCOPED_OBJ" in scoped
    assert "import SCOPED_OBJ" not in scoped.replace("OBJ as SCOPED_OBJ", "")


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
    assert module.scoped_rename_mod.minimize_scoped(objective, np.float64(5.0)) == np.float64(25.0)


CALLBACK_RESULT_TYPES_SOURCE = """
module cbresult_types
  implicit none
  type :: point_t
    real(8) :: x
  end type point_t

  abstract interface
    function make_point(x) result(p)
      import :: point_t
      implicit none
      real(8), intent(in) :: x
      type(point_t) :: p
    end function make_point
  end interface
end module cbresult_types
"""

CALLBACK_RESULT_CONSUMER_SOURCE = """
module cbresult_consumer
  use, non_intrinsic :: cbresult_types, only : make_point, point_t
  implicit none
contains
  subroutine run(f, seed, out_x)
    procedure(make_point) :: f
    real(8), intent(in) :: seed
    real(8), intent(out) :: out_x
    type(point_t) :: made

    made = f(seed)
    out_x = made%x
  end subroutine run
end module cbresult_consumer
"""


def test_imported_callback_returning_a_module_owned_type_builds(tmp_path: Path):
    """A callback result type belongs to the module that declares the interface.

    Attributing it to the consuming module produced an identity no wrapper
    definition could satisfy, so the build failed outright.  The generated
    contract must name the declaring module and the extension must build.

    The built extension is not called here: resolving a cross-module derived
    type through the runtime namespace is a separate, pre-existing gap that
    also affects ordinary functions returning an imported type.
    """
    sources = []
    for name, text in (
        ("cbresult_types.f90", CALLBACK_RESULT_TYPES_SOURCE),
        ("cbresult_consumer.f90", CALLBACK_RESULT_CONSUMER_SOURCE),
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

    declaring = (contracts / "cbresult_types.pyi").read_text(encoding="utf-8")
    assert "def make_point(" in declaring
    assert "-> point_t: ..." in declaring

    result = build_pyi_extension(
        contracts / "__init__.pyi",
        input_compiler=_compiler(),
        native_fortran_sources=[str(path) for path in sources],
        output_dir=tmp_path / "build",
        output_name="callback_result_types",
    )
    assert result.shared_library.exists()


RENAMED_CHAIN_SOURCE = """
module chain_declares_mod
  implicit none
  abstract interface
    subroutine OBJ(x, f)
      implicit none
      real(8), intent(in) :: x
      real(8), intent(out) :: f
    end subroutine OBJ
  end interface
end module chain_declares_mod

module chain_middle_mod
  use, non_intrinsic :: chain_declares_mod, only : MID => OBJ
  implicit none
  public :: MID
end module chain_middle_mod

module chain_consumer_mod
  use, non_intrinsic :: chain_middle_mod, only : LOCAL => MID
  implicit none
contains
  subroutine run_chain(calfun, x, f)
    procedure(LOCAL) :: calfun
    real(8), intent(in) :: x
    real(8), intent(out) :: f

    call calfun(x, f)
  end subroutine run_chain
end module chain_consumer_mod
"""


def test_renamed_reexport_chain_builds_through_its_generated_contracts(tmp_path: Path):
    """Each hop renames the interface, so only the declaring module names it.

    A rename and a re-export are covered separately elsewhere; combining them
    is what exposes a reference that followed the module back to the declaration
    while keeping an alias from somewhere along the way.
    """
    source = tmp_path / "chain.f90"
    source.write_text(RENAMED_CHAIN_SOURCE, encoding="utf-8")
    contracts = tmp_path / "contracts"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(source),
            "--out",
            str(contracts),
            "--compiler",
            _compiler(),
        ],
        check=True,
        capture_output=True,
    )

    # Each contract mirrors the `use` its own module wrote.
    assert "from .chain_declares_mod import OBJ as MID" in (contracts / "chain_middle_mod.pyi").read_text(
        encoding="utf-8"
    )
    consuming = (contracts / "chain_consumer_mod.pyi").read_text(encoding="utf-8")
    assert "from .chain_middle_mod import MID as LOCAL" in consuming
    assert "calfun: LOCAL" in consuming

    result = build_pyi_extension(
        contracts / "__init__.pyi",
        input_compiler=_compiler(),
        native_fortran_sources=[str(source)],
        output_dir=tmp_path / "build",
        output_name="renamed_chain_callbacks",
    )
    module = _import_from_build_dir(result.module_name, result.output_dir)

    def objective(x, f):
        f[...] = float(x) * 7.0

    assert module.chain_consumer_mod.run_chain(objective, np.float64(6.0)) == np.float64(42.0)
