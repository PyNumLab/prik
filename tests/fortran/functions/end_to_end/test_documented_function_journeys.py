"""End-to-end journeys for the Wrapping Functions guide."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import

pytestmark = pytest.mark.fortran_end_to_end

FIXTURES = Path(__file__).parent / "fixtures"
FUNCTIONS_SOURCE = FIXTURES / "documented_functions.f90"


def test_function_results_outputs_arrays_and_no_intent_replacements_follow_documented_order(
    tmp_path: Path,
):
    module = _build_source_and_import(
        FUNCTIONS_SOURCE,
        tmp_path,
        {
            "bind_c_documented_functions_wrapper.f90",
            "documented_functions_wrapper.c",
            "documented_functions_wrapper.h",
        },
    )

    assert module.scale(np.float64(3.0), np.float64(2.5)) == np.float64(7.5)
    with pytest.raises(TypeError):
        module.scale(3.0, np.float64(2.5))

    values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    assert module.sum_with_count(values) == (np.float64(6.0), np.int32(3))

    output = np.empty(4, dtype=np.float64)
    assert module.fill_and_sum(np.int32(4), output) == np.float64(10.0)
    np.testing.assert_array_equal(output, np.array([1.0, 2.0, 3.0, 4.0]))

    original = np.float64(3.0)
    assert module.square_no_intent(original) == (np.float64(16.0), np.float64(4.0))
    assert original == np.float64(3.0)

    automatic = module.automatic_vector(np.int32(4))
    assert automatic.flags.f_contiguous
    np.testing.assert_array_equal(automatic, np.array([1.0, 4.0, 9.0, 16.0]))
