"""Project kind aliases resolve to intrinsics before any compiler probe runs."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import, _compiler, _import_from_build_dir
from prik import build_pyi_extension
from prik.parsers.fortran import parse_fortran_file
from prik.semantics.fortran2ir import collect_fortran_type_storage_requirements

pytestmark = pytest.mark.fortran_end_to_end

KIND_ALIAS_SOURCE = """
module consts_mod
  use iso_fortran_env, only : REAL64
  use iso_fortran_env, only : INT32
  implicit none

  integer, parameter :: DP = REAL64
  integer, parameter :: IK_DFT = INT32
  integer, parameter :: RP = DP
  integer, parameter :: IK = IK_DFT
end module consts_mod

module consumer_mod
  use consts_mod, only : RP, IK
  implicit none
contains
  subroutine work(x, n)
    real(RP), intent(inout) :: x
    integer(IK), intent(in) :: n
    x = x * real(n, RP)
  end subroutine work
end module consumer_mod
"""


def test_kind_alias_chain_reaches_the_probe_as_intrinsic_expressions(tmp_path: Path):
    """A project names its kinds through its own parameters, and they resolve.

    Each `use` of one module adds to what the scope imported, and a parameter
    may name another, so `RP` reaches `REAL64` through `DP`. The probe measures
    target storage and is given expressions a compiler understands, never a
    project name it has no way to evaluate.
    """
    source = tmp_path / "kinds.f90"
    source.write_text(KIND_ALIAS_SOURCE, encoding="utf-8")

    parsed = parse_fortran_file(source)
    consumer = next(module for module in parsed.modules if module.name == "consumer_mod")
    assert [(argument.name, argument.kind) for argument in consumer.procedures[0].arguments] == [
        ("x", "REAL64"),
        ("n", "INT32"),
    ]
    assert all(
        "RP" not in str(requirement["expression"]) and "IK" not in str(requirement["expression"])
        for requirement in collect_fortran_type_storage_requirements(parsed)
    )

    module = _build_source_and_import(
        source,
        tmp_path / "source_build",
        {"bind_c_kinds_wrapper.f90", "kinds_wrapper.c", "kinds_wrapper.h"},
    )
    assert module.consumer_mod.work(np.float64(2.5), np.int32(4)) == pytest.approx(10.0)


def test_kind_alias_chain_survives_its_generated_contract(tmp_path: Path):
    """The contract states resolved types, and rebuilding keeps the behavior."""
    source = tmp_path / "kinds.f90"
    source.write_text(KIND_ALIAS_SOURCE, encoding="utf-8")
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

    contract = (contracts / "consumer_mod.pyi").read_text(encoding="utf-8")
    assert "x: Float64" in contract
    assert "n: Int32" in contract

    result = build_pyi_extension(
        contracts / "__init__.pyi",
        input_compiler=_compiler(),
        native_fortran_sources=[str(source)],
        output_dir=tmp_path / "contract_build",
        output_name="kinds_contract",
    )
    rebuilt = _import_from_build_dir(result.module_name, result.output_dir)
    assert rebuilt.consumer_mod.work(np.float64(2.5), np.int32(4)) == pytest.approx(10.0)
