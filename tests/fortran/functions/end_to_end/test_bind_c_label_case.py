"""A `bind(C)` label is an external symbol, not a Fortran identifier."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import, _compiler, _import_from_build_dir
from prik import build_pyi_extension

pytestmark = pytest.mark.fortran_end_to_end

BIND_C_LABEL_SOURCE = """
module label_mod
  use iso_c_binding, only : c_int
  implicit none
contains
  subroutine scale(x) bind(C, name="SCALE")
    integer(c_int), intent(inout) :: x
    x = x * 3
  end subroutine scale
end module label_mod
"""


def test_bind_c_label_keeps_its_exact_spelling_through_a_generated_contract(tmp_path: Path):
    """A C binding label differing only in case from its procedure survives.

    Fortran names `scale` without regard to case, so nothing about that name
    needs recording. The label `SCALE` is a C external symbol instead, which is
    spelled exactly, and the wrapper links against it rather than the Fortran
    identifier it happens to resemble.
    """
    source = tmp_path / "label.f90"
    source.write_text(BIND_C_LABEL_SOURCE, encoding="utf-8")

    source_module = _build_source_and_import(
        source,
        tmp_path / "source_build",
        {"label_wrapper.c", "label_wrapper.h"},
    )
    assert source_module.scale(np.int32(5)) == np.int32(15)

    contracts = tmp_path / "contracts"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prik",
            "generate",
            "--pyi",
            str(source),
            "--out",
            str(contracts),
            "--compiler",
            _compiler(),
        ],
        check=True,
        capture_output=True,
    )
    contract = (contracts / "label_mod.pyi").read_text(encoding="utf-8")
    assert '@bind("SCALE")' in contract
    assert "def scale(" in contract

    result = build_pyi_extension(
        contracts / "__init__.pyi",
        input_compiler=_compiler(),
        native_fortran_sources=[str(source)],
        output_dir=tmp_path / "contract_build",
        output_name="label_contract",
    )
    rebuilt = _import_from_build_dir(result.module_name, result.output_dir)
    assert rebuilt.label_mod.scale(np.int32(5)) == np.int32(15)
