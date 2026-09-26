"""A generic merged from several modules builds the same from source and from its contracts."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from prik import build_fortran_extension, build_pyi_extension
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


PURE_FACADE = NATIVE_FIXTURES / "pure_facade_generic.f90"


@pytest.mark.parametrize("selected", [False, True], ids=["whole-project", "selected"])
def test_a_pure_facade_dispatches_every_generic_it_merges(tmp_path: Path, selected: bool):
    """A facade declaring nothing still owns the generic its two imports merge into.

    Both contributors keep their specifics private, so neither is reachable by
    name. Built from source and replayed from its generated contracts, the
    facade dispatches over both, and selecting ``facade_mod::convert`` selects
    the merged generic rather than one contributor.
    """
    exports = ("facade_mod::convert",) if selected else None
    source = build_fortran_extension(
        PURE_FACADE, output_dir=tmp_path / "source", output_name="pure_facade_source", export_symbols=exports
    )
    command = [sys.executable, "-m", "prik", "generate", "--pyi", str(PURE_FACADE), "--out", str(tmp_path / "pyi")]
    if exports:
        symbols = tmp_path / "exports.txt"
        symbols.write_text("\n".join(exports) + "\n", encoding="utf-8")
        command += ["--export-symbols", str(symbols)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    replay = build_pyi_extension(
        tmp_path / "pyi" / "__init__.pyi",
        native_fortran_sources=(PURE_FACADE,),
        output_dir=tmp_path / "replay",
        output_name="pure_facade_replay",
    )

    for result in (source, replay):
        facade = _import_from_build_dir(result.module_name, result.output_dir).facade_mod
        assert facade.convert(np.int32(3)) == np.int32(4)
        assert facade.convert(np.float64(1.5)) == np.float64(3.0)
