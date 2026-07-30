"""Portable runtime matrix for primitive Fortran arrays."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_text_and_import
from tests.fortran.arrays.end_to_end.fixtures.primitive_dtype_rank_matrix import (
    PRIMITIVE_ARRAY_CASES,
    primitive_dtype_rank_source,
)

pytestmark = pytest.mark.fortran_end_to_end


def test_every_primitive_dtype_at_every_concrete_rank_mutates_exact_storage(tmp_path: Path):
    module = _build_text_and_import(
        primitive_dtype_rank_source(),
        "farray_dtype_rank_matrix.f90",
        tmp_path,
        {
            "bind_c_farray_dtype_rank_matrix_wrapper.f90",
            "farray_dtype_rank_matrix_wrapper.c",
            "farray_dtype_rank_matrix_wrapper.h",
        },
    )

    for case in PRIMITIVE_ARRAY_CASES:
        for rank in range(1, 16):
            shape = (2, *([1] * (rank - 1)))
            values = np.asfortranarray(np.asarray(case.values, dtype=case.dtype).reshape(shape, order="F"))

            result = getattr(module, f"bump_{case.name}_r{rank}")(values)

            assert result is None
            assert values.dtype == np.dtype(case.dtype)
            assert values.shape == shape
            assert values.flags.f_contiguous
            np.testing.assert_array_equal(
                values,
                np.asarray(case.expected, dtype=case.dtype).reshape(shape, order="F"),
            )
