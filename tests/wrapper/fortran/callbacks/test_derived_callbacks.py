"""Derived-type callback argument and result conversion tests."""

from pathlib import Path

import numpy as np

from tests.wrapper.fortran._support import _build_source_or_generated_pyi_and_import, wrapper_source

CALLBACK_DERIVED_F90_SOURCE = wrapper_source("fcallback_derived_f90.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "contracts"


def test_immediate_dummy_procedure_converts_derived_arguments_and_results(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        CALLBACK_DERIVED_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fcallback_derived_f90_wrapper.f90",
            "fcallback_derived_f90_wrapper.c",
            "fcallback_derived_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fcallback_derived_f90",
        pyi_parity_build_mode,
    )
    point = module.point_t(x=np.float64(2.0), y=np.float64(5.0))
    output = module.point_t()

    result = module.apply_point(
        lambda value: module.point_t(x=value.x + 1.0, y=value.y * 2.0),
        point,
        output,
    )
    assert result is None
    assert output.x == np.float64(3.0)
    assert output.y == np.float64(10.0)
