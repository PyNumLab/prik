"""Maintainer-only complete-surface checks that reuse the LAPACK example build."""

from __future__ import annotations

from pathlib import Path

import pytest

from ..routine_inventory import EXPECTED_LAPACK_ROOT_PROCEDURES
from examples.lapack.tests.helpers import assert_runtime_smoke
from prik.pipeline.pyi import pyi_paths_to_semantic_modules


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def test_ci_complete_prik_surface_reuses_example_extension(prik_lapack):
    build_root = Path(prik_lapack.__file__).resolve().parent.parent
    runtime_package = build_root / "contracts" / "lapack"
    modules = pyi_paths_to_semantic_modules([runtime_package])
    root = next(module for module in modules if module.name == "__init__")
    expected = {function.name for function in root.functions}
    assert len(expected) == EXPECTED_LAPACK_ROOT_PROCEDURES

    missing = sorted(name for name in expected if not callable(getattr(prik_lapack, name, None)))
    assert missing == []
    assert_runtime_smoke(prik_lapack)
