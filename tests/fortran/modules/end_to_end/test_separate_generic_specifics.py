"""A separate module procedure is a generic specific a later module inherits.

``module function`` and ``module subroutine`` interface bodies declare
procedures the module owns and a submodule implements, so a module extending
a generic built from them dispatches over them too.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from prik import build_fortran_extension
from tests.fortran._support.wrapper_build import (
    _build_generated_pyi_and_import,
    _import_from_build_dir,
    _sole_native_module,
)

pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


def _package(source: Path, tmp_path: Path, lane: str):
    """Build one fixture from source or through its generated contract and import it."""
    if lane == "source":
        result = build_fortran_extension(source, output_dir=tmp_path / "source", output_name=source.stem)
        return _import_from_build_dir(result.module_name, result.output_dir)
    return _build_generated_pyi_and_import(source, tmp_path / "pyi")


def _namespace(package, name: str):
    return getattr(package, name) if hasattr(package, name) else getattr(_sole_native_module(package), name)


@pytest.mark.parametrize("lane", ["source", "generated_pyi"])
def test_a_generic_of_separate_specifics_dispatches_through_an_importing_module(tmp_path: Path, lane: str):
    """``facade`` extends ``convert``, so it inherits the specifics only interface bodies declare."""
    package = _package(NATIVE_FIXTURES / "separate_generic_specific.f90", tmp_path, lane)
    facade = _namespace(package, "facade")

    assert facade.convert(np.int32(3)) == np.int32(4)
    assert facade.convert(np.float64(1.5)) == np.float64(3.0)
    assert facade.convert(np.int64(2)) == np.int64(20)
