"""Array callback argument and result conversion tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_or_generated_pyi_and_import

FIXTURES = Path(__file__).parent / "fixtures"
CALLBACK_ARRAY_F90_SOURCE = FIXTURES / "fcallback_array_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_immediate_dummy_procedure_converts_array_arguments_and_results(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        CALLBACK_ARRAY_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fcallback_array_f90_wrapper.f90",
            "fcallback_array_f90_wrapper.c",
            "fcallback_array_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fcallback_array_f90",
        pyi_parity_build_mode,
    )
    values = np.asfortranarray(np.array([1.0, 2.0, 3.0], dtype=np.float64))

    assert module.apply_reduce(lambda count, data: data[:count].sum(), np.int32(3), values) == np.float64(6.0)
    transformed = np.empty_like(values)
    result = module.apply_transform(
        lambda count, data: np.asfortranarray(data[:count] * 2.0),
        np.int32(3),
        values,
        transformed,
    )
    assert result is None
    np.testing.assert_array_equal(transformed, np.array([2.0, 4.0, 6.0], dtype=np.float64))
