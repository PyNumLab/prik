"""Maintainer-only complete-surface checks that reuse the BLAS example build."""

from __future__ import annotations

import pytest

from examples.blas.routine_inventory import ALL_ROUTINES
from tests.fortran.building_shared_library.end_to_end.real_libraries import test_full_libraries as full


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_ci_complete_prik_surface_reuses_example_extension(prik_blas):
    missing = sorted(routine for routine in ALL_ROUTINES if not callable(getattr(prik_blas, routine, None)))
    assert missing == []
    full._assert_blas_runtime_smoke(prik_blas)
