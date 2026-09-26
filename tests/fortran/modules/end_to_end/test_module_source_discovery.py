"""An entry source is enough: the modules it uses are found under search directories."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from prik import build_fortran_extension, build_pyi_extension
from tests.fortran._support.wrapper_build import _import_from_build_dir

pytestmark = pytest.mark.fortran_end_to_end

PROJECT = Path(__file__).parent / "fixtures" / "native" / "module_discovery"
ENTRY = PROJECT / "api" / "api_entry.f90"


def test_entry_source_discovers_used_modules_for_contract_and_build(tmp_path: Path):
    """Modules named by `use`, in any file and directory, reach both the contract and the build."""
    contract = tmp_path / "contract"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(ENTRY),
            "--module-source-dir",
            str(PROJECT),
            "--out",
            str(contract),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "class Handle_T:" in (contract / "base_types.pyi").read_text(encoding="utf-8")

    result = build_fortran_extension(
        ENTRY,
        module_source_dirs=[PROJECT],
        output_name="discovered_api",
        output_dir=tmp_path / "build",
    )
    root = _import_from_build_dir(result.module_name, result.output_dir)
    handle = root.base_types.Handle_T()
    root.api.touch(handle)
    assert handle.val == np.int32(1)


def test_a_separate_module_procedure_is_wrapped_and_its_submodule_discovered(tmp_path: Path):
    """A ``module function`` declared in an interface block is the module's own procedure.

    Its body lives in a submodule that no ``use`` names; discovery still
    brings that submodule in, so the contract publishes the function and both
    the source build and a replay of the contract link its implementation.
    """
    library = tmp_path / "lib"
    library.mkdir()
    (library / "shapes.f90").write_text(
        """module shapes
  implicit none
  interface
    module function area(side) result(value)
      real(8), intent(in) :: side
      real(8) :: value
    end function area
  end interface
end module shapes
""",
        encoding="utf-8",
    )
    (library / "shapes_impl.f90").write_text(
        """submodule (shapes) shapes_impl
contains
  module procedure area
    value = side * side
  end procedure area
end submodule shapes_impl
""",
        encoding="utf-8",
    )
    entry = tmp_path / "app.f90"
    entry.write_text("module app\n  use shapes, only: area\n  implicit none\nend module app\n", encoding="utf-8")
    contract = tmp_path / "contract"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(entry),
            "--module-source-dir",
            str(library),
            "--out",
            str(contract),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "def area(" in (contract / "shapes.pyi").read_text(encoding="utf-8")

    source = build_fortran_extension(
        entry, module_source_dirs=[library], output_name="separate_source", output_dir=tmp_path / "source"
    )
    replay = build_pyi_extension(
        contract / "__init__.pyi",
        native_fortran_sources=(library / "shapes.f90", library / "shapes_impl.f90"),
        output_name="separate_replay",
        output_dir=tmp_path / "replay",
    )
    for result in (source, replay):
        root = _import_from_build_dir(result.module_name, result.output_dir)
        assert root.shapes.area(np.float64(3.0)) == np.float64(9.0)
