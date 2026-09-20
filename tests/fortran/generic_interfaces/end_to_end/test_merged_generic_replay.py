"""A generic merged from several modules builds the same from source and from its contracts."""

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

MERGED_SOURCE = (NATIVE_FIXTURES / "merged_generic.f90").read_text(encoding="utf-8")


def _source_build(source: Path, build_dir: Path):
    result = build_fortran_extension(source, output_dir=build_dir, output_name="merged_generic")
    return _import_from_build_dir(result.module_name, result.output_dir)


@pytest.mark.parametrize("lane", ["source", "generated_pyi"])
def test_merged_generic_dispatches_every_contributor(tmp_path: Path, lane: str):
    source = tmp_path / "merged_generic.f90"
    source.write_text(MERGED_SOURCE, encoding="utf-8")
    if lane == "source":
        package = _source_build(source, tmp_path / "source_build")
    else:
        package = _build_generated_pyi_and_import(source, tmp_path / "pyi_build")
    facade = _sole_native_module(package).facade_mod if not hasattr(package, "facade_mod") else package.facade_mod

    assert facade.convert(np.int32(3)) == np.int32(3)
    assert facade.convert(np.float32(2.5)) == np.float32(2.5)
    assert facade.convert(np.bool_(True))
