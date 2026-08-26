"""Scalar derived-type arguments, results, fields, and lifetime evidence."""

import gc
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
DERIVED_BOUNDARY_F90_SOURCE = FIXTURES / "native" / "fderived_boundary_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_scalar_derived_types_cross_procedure_boundaries(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        DERIVED_BOUNDARY_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fderived_boundary_f90_wrapper.f90",
            "fderived_boundary_f90_wrapper.c",
            "fderived_boundary_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fderived_boundary_f90",
        pyi_parity_build_mode,
    )

    point = module.point()
    point.x = np.float64(1.0)
    point.y = np.float64(2.0)
    assert not hasattr(point, "hidden")
    assert module.point_sum(point) == np.float64(3.0)

    identity = id(point)
    assert module.move_point(point, np.float64(4.0), np.float64(5.0)) is None
    assert id(point) == identity
    assert point.x == np.float64(5.0)
    assert point.y == np.float64(7.0)

    out_point = module.point()
    assert module.make_point_out(out_point, np.float64(8.0), np.float64(9.0)) is None
    assert out_point.x == np.float64(8.0)
    assert out_point.y == np.float64(9.0)

    result_point = module.make_point(np.float64(10.0), np.float64(11.0))
    assert isinstance(result_point, module.point)
    assert result_point.x == np.float64(10.0)
    assert result_point.y == np.float64(11.0)

    holder = module.holder()
    holder.scale = np.float64(2.5)
    assert module.set_holder_origin(holder, result_point) is None
    origin = holder.origin
    assert isinstance(origin, module.point)
    assert origin.x == np.float64(10.0)
    origin.x = np.float64(12.0)
    assert module.holder_origin_x(holder) == np.float64(12.0)

    del holder
    gc.collect()
    assert origin.x == np.float64(12.0)
