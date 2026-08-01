"""GNU OpenMP build flags, execution, and default GIL-policy tests."""

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _sole_native_module, wrapper_source

OPENMP_SOURCE = wrapper_source("fopenmp_runtime_f90.f90")
pytestmark = pytest.mark.fortran_end_to_end


@pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("make") is None or shutil.which("gfortran") is None,
    reason="OpenMP wrapper smoke test requires GNU Make and GNU Fortran",
)
def test_openmp_enabled_procedure_builds_with_explicit_gnu_flags(tmp_path: Path):
    source = tmp_path / "fopenmp_runtime_f90.f90"
    shutil.copyfile(OPENMP_SOURCE, source)

    generated = subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--makefile",
            str(source),
            "--out-dir",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(generated.stdout)
    makefile = Path(payload["build_makefile"])

    subprocess.run(
        [
            "make",
            "-j4",
            "-f",
            str(makefile),
            "all",
            "PRIK_FFLAGS=-fopenmp",
            "PRIK_LDFLAGS=-fopenmp",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    c_wrapper = (tmp_path / "fopenmp_runtime_f90_wrapper.c").read_text(encoding="utf-8")
    assert "Py_BEGIN_ALLOW_THREADS" not in c_wrapper
    assert "Py_END_ALLOW_THREADS" not in c_wrapper

    sys.modules.pop("fopenmp_runtime_f90", None)
    sys.path.insert(0, str(tmp_path))
    try:
        module = _sole_native_module(importlib.import_module("fopenmp_runtime_f90"))
        values = np.arange(1, 33, dtype=np.float64)
        assert module.parallel_sum(values) == np.sum(values)
    finally:
        sys.path.remove(str(tmp_path))
