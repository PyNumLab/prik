"""Runtime contract for immutable snapshots of Fortran parameter arrays."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_wrapper_plan_and_import, _sole_native_module

pytestmark = pytest.mark.fortran_end_to_end

PARAMETER_ARRAY_SOURCE = """\
module parameter_array_constants_f90
  use iso_fortran_env, only: real64
  implicit none
  real(real64), parameter :: dpmpar(3) = [epsilon(1.0_real64), tiny(1.0_real64), huge(1.0_real64)]
contains
  function parameter_sum() result(value)
    real(real64) :: value

    value = sum(dpmpar)
  end function parameter_sum
end module parameter_array_constants_f90
"""


def _write_source(root: Path) -> Path:
    root.mkdir(parents=True)
    source = root / "parameter_array_constants_f90.f90"
    source.write_text(PARAMETER_ARRAY_SOURCE, encoding="utf-8")
    return source


def test_fortran_parameter_array_is_a_read_only_python_owned_import_snapshot(tmp_path: Path):
    source = _write_source(tmp_path / "fixture")
    module, result = _build_source_wrapper_plan_and_import(source, tmp_path / "build")

    values = module.dpmpar
    expected = np.array(
        [np.finfo(np.float64).eps, np.finfo(np.float64).tiny, np.finfo(np.float64).max],
        dtype=np.float64,
    )
    assert isinstance(values, np.ndarray)
    assert values.dtype == np.dtype(np.float64)
    assert values.shape == (3,)
    assert values.flags.f_contiguous
    assert values.flags.writeable is False
    np.testing.assert_array_equal(values, expected)
    with pytest.raises(ValueError, match="read-only"):
        values[0] = 1.0
    assert module.parameter_sum() == np.float64(expected.sum())

    module.dpmpar = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    assert module.parameter_sum() == np.float64(expected.sum())

    sys.modules.pop("parameter_array_constants_f90", None)
    sys.path.insert(0, str(result.output_dir))
    try:
        reloaded = _sole_native_module(importlib.import_module("parameter_array_constants_f90"))
    finally:
        sys.path.remove(str(result.output_dir))
    np.testing.assert_array_equal(reloaded.dpmpar, expected)
    assert reloaded.dpmpar.flags.writeable is False
