"""An entry source is enough: the modules it uses are found under search directories."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from prik import build_fortran_extension
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
