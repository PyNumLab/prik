"""Native compile flags that change the wrapper's measured runtime ABI."""

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _sole_native_module

RUNTIME_ABI_SOURCE = Path(__file__).parent / "fixtures" / "native" / "fruntime_abi_f90.f90"
pytestmark = pytest.mark.fortran_end_to_end


def test_top_level_native_kind_flags_drive_internal_type_measurement(tmp_path: Path):
    source = tmp_path / RUNTIME_ABI_SOURCE.name
    shutil.copyfile(RUNTIME_ABI_SOURCE, source)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            str(source),
            "--native-compile-flags=-fdefault-real-8",
            "--out-dir",
            str(tmp_path / "build"),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )
    module_name = json.loads(completed.stdout)["module_name"]

    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(tmp_path))
    try:
        module = _sole_native_module(importlib.import_module(module_name))
        assert module.scale(np.float64(4.0), np.float64(1.25)) == np.float64(5.0)
    finally:
        sys.path.remove(str(tmp_path))
