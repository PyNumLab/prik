"""Build actual MINPACK sources and verify representative numerical answers."""

from __future__ import annotations

import numpy as np
import pytest

from tests.fortran.infrastructure.building.end_to_end.real_libraries._support import (
    build_real_fortran_library,
    real_library_source_dir,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


@pytest.fixture(scope="module")
def minpack(tmp_path_factory: pytest.TempPathFactory):
    source_dir = real_library_source_dir("minpack")
    extension = build_real_fortran_library(
        "minpack",
        [source_dir / "minpack.f90"],
        tmp_path_factory.mktemp("minpack-showcase"),
    )
    return extension.minpack_module


def test_enorm_returns_the_known_euclidean_norm(minpack):
    values = np.array([3.0, 4.0, 12.0], dtype=np.float64)

    assert minpack.enorm(np.int32(values.size), values) == pytest.approx(13.0)


def test_qrfac_returns_known_column_norms_and_r_diagonal(minpack):
    matrix = np.asfortranarray([[3.0, 0.0], [4.0, 5.0]], dtype=np.float64)
    pivots = np.zeros(2, dtype=np.int32)
    diagonal = np.zeros(2, dtype=np.float64)
    column_norms = np.zeros(2, dtype=np.float64)
    workspace = np.zeros(2, dtype=np.float64)

    minpack.qrfac(
        np.int32(2),
        np.int32(2),
        matrix,
        np.int32(2),
        True,
        pivots,
        np.int32(2),
        diagonal,
        column_norms,
        workspace,
    )

    np.testing.assert_array_equal(pivots, np.array([1, 2], dtype=np.int32))
    np.testing.assert_allclose(column_norms, np.array([5.0, 5.0]))
    np.testing.assert_allclose(diagonal, np.array([-5.0, -3.0]), atol=1.0e-12)
