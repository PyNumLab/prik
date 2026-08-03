"""Maintainer-only complete-surface checks that reuse the LAPACK example build."""

from __future__ import annotations

import pytest

from .contracts import root_function_names
from .helpers import assert_runtime_smoke
from .routine_inventory import EXPECTED_LAPACK_ROOT_PROCEDURES


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_ci_complete_prik_surface_reuses_example_extension(prik_build):
    runtime_package = prik_build.workdir / "contracts" / "lapack"
    expected = root_function_names(runtime_package)
    assert len(expected) == EXPECTED_LAPACK_ROOT_PROCEDURES

    missing = sorted(name for name in expected if not callable(getattr(prik_build.module, name, None)))
    assert missing == []
    assert_runtime_smoke(prik_build.module)
