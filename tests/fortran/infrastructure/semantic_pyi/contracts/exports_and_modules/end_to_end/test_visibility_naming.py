"""Visibility, naming, and Python API surface runtime wrapper tests."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
    wrapper_source,
)

NAMING_F90_SOURCE = wrapper_source("fnaming_f90.f90")
NAMING_F90_TEXT = NAMING_F90_SOURCE.read_text(encoding="utf-8")
CONTRACT_FIXTURES = Path(__file__).parent / "fixtures" / "visibility" / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_visibility_and_default_python_name_fixing_policy(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        NAMING_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fnaming_f90_wrapper.f90",
            "fnaming_f90_wrapper.c",
            "fnaming_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fnaming_f90",
        pyi_parity_build_mode,
    )

    assert module.lambda_(np.int32(3)) == 4
    assert module.lambda__2(np.int32(3)) == 5
    assert module.get_value() == 100
    assert module.value == 7
    module.value = np.int32(11)
    assert module.value == 11
    assert not hasattr(module, "get_value_2")
    assert not hasattr(module, "set_value")

    assert not hasattr(module, "hidden_t")
    assert not hasattr(module, "hidden_proc")

    item = module.visible_t(lambda_=np.int32(5), lambda__2=np.int32(6))
    assert item.lambda_ == 5
    assert item.lambda__2 == 6
    assert item.from_() == 11
    assert not hasattr(item, "hidden")


def test_strict_wrapper_names_reject_python_name_fixes(tmp_path: Path):
    source = tmp_path / "fnaming_f90.f90"
    source.write_text(NAMING_F90_TEXT, encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "prik",
        str(source),
        "--out-dir",
        str(tmp_path),
        "--json",
        "--strict-wrapper-names",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    assert result.returncode != 0
    assert "strict wrapper naming" in result.stderr
