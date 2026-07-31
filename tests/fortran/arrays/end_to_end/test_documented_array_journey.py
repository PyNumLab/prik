"""The complete public array journey documented in the User Guide."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "array_ops.f90"


def test_documented_array_source_build_validates_layout_flat_strides_mutation_and_results(
    tmp_path: Path,
):
    module = _build_source_and_import(
        SOURCE,
        tmp_path,
        {
            "array_ops_wrapper.c",
            "array_ops_wrapper.h",
            "bind_c_array_ops_wrapper.f90",
        },
    )

    matrix = np.ones((2, 3), dtype=np.float64, order="F")
    assert module.scale_matrix(np.int32(2), np.int32(3), matrix) is None
    np.testing.assert_array_equal(matrix, np.full((2, 3), 2.0, order="F"))

    shifted = np.zeros(4, dtype=np.float64)
    assert module.shift(np.int32(4), shifted) is None
    np.testing.assert_array_equal(shifted, np.ones(4))

    flat_matrix = np.array(
        [[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]],
        dtype=np.float64,
        order="F",
    )
    assert module.sum_flat(np.int32(flat_matrix.size), flat_matrix) == np.float64(66.0)
    with pytest.raises(TypeError, match="contiguous"):
        module.sum_flat(np.int32(flat_matrix[:, ::2].size), flat_matrix[:, ::2])

    panels = np.asfortranarray(np.arange(1, 25, dtype=np.float64).reshape((2, 3, 4), order="F"))
    assert module.sum_flat_columns(np.int32(2), np.int32(12), panels) == np.float64(300.0)

    base = np.asfortranarray(np.arange(1, 25, dtype=np.float64).reshape((8, 3), order="F"))
    visible_rows = base[::2, :]
    output_storage = np.zeros((8, 3), dtype=np.float64, order="F")
    output = output_storage[::2, :]
    assert module.scale_visible_rows(visible_rows, output) is None
    np.testing.assert_array_equal(output, 3.0 * visible_rows)

    no_intent = np.array([2.0, 5.0, 7.0], dtype=np.float64)
    assert module.scale_without_intent(no_intent) is None
    np.testing.assert_array_equal(no_intent, np.array([4.0, 10.0, 14.0]))

    optional_values = np.array([1.0, 2.0], dtype=np.float64)
    assert module.mutate_optional() is None
    assert module.mutate_optional(None, np.float64(2.0)) is None
    assert module.mutate_optional(optional_values, np.float64(2.5)) is None
    np.testing.assert_array_equal(optional_values, np.array([3.5, 4.5]))
    optional_output = np.empty(3, dtype=np.float64)
    assert module.fill_optional(np.int32(3), optional_output) is None
    np.testing.assert_array_equal(optional_output, np.array([11.0, 12.0, 13.0]))
    assert module.fill_optional(np.int32(3)) is None
    assert module.fill_optional(np.int32(3), None) is None

    vector = module.automatic_vector(np.int32(4))
    np.testing.assert_array_equal(vector, np.array([2.0, 4.0, 6.0, 8.0]))

    with pytest.raises(TypeError, match="dtype"):
        module.scale_matrix(np.int32(2), np.int32(3), np.ones((2, 3), dtype=np.float32, order="F"))
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale_matrix(np.int32(2), np.int32(3), np.ones((2, 3), dtype=np.float64, order="C"))
    with pytest.raises(TypeError, match="incompatible shape"):
        module.scale_matrix(np.int32(3), np.int32(2), matrix)

    read_only = np.ones((2, 3), dtype=np.float64, order="F")
    read_only.flags.writeable = False
    with pytest.raises(TypeError, match="writeable"):
        module.scale_matrix(np.int32(2), np.int32(3), read_only)
