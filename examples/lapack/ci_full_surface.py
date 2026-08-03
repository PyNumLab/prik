"""Maintainer-only complete-surface checks that reuse the LAPACK example build."""

from __future__ import annotations

import pytest

from tests.fortran.building_shared_library.end_to_end.real_libraries import test_full_libraries as full

from .routine_inventory import EXPECTED_LAPACK_ROOT_PROCEDURES


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_ci_complete_prik_surface_reuses_example_extension(prik_build):
    runtime_package = prik_build.workdir / "runtime_contract" / "lapack"
    expected = {function.name for function in full._root_module(runtime_package).functions}
    assert len(expected) == EXPECTED_LAPACK_ROOT_PROCEDURES

    missing = sorted(name for name in expected if not callable(getattr(prik_build.module, name, None)))
    assert missing == []
    full._assert_lapack_runtime_smoke(prik_build.module)
