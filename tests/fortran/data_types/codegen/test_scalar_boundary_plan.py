"""Isolated compiled parity for primitive scalar boundary representations."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension


def _build_contract_module(
    tmp_path: Path,
    *,
    module_name: str,
    source_text: str,
    contract_text: str,
):
    source = tmp_path / f"{module_name}.f90"
    source.write_text(source_text, encoding="utf-8")
    contract = tmp_path / f"{module_name}.pyi"
    contract.write_text(contract_text, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native")

    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    generated_c = (result.output_dir / f"{module_name}_wrapper.c").read_text(encoding="utf-8")
    assert "static PyObject * wrap_" in generated_c
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def _build_multiple_scalar_result_modules(tmp_path: Path):
    return (
        _build_contract_module(
            tmp_path,
            module_name="multiple_scalar_results_plan",
            source_text="""
module multiple_scalar_results_plan
  use iso_c_binding, only: c_int32_t
contains
  function with_scalar(n, status) result(value)
    integer(c_int32_t), intent(in) :: n
    integer(c_int32_t), intent(out) :: status
    integer(c_int32_t) :: value
    value = n * 2
    status = n + 3
  end function with_scalar
end module multiple_scalar_results_plan
""",
            contract_text="""
from prik.contracts import Addr, Arg, Int32, Return, native_call

@native_call([Addr(Arg(0)), Return("status", 1)])
def with_scalar(n: Int32) -> tuple[Int32, Int32]: ...
""",
        ),
    )


def test_multiple_scalar_results_use_canonical_plan_without_array_blockers(tmp_path: Path):
    modules = _build_multiple_scalar_result_modules(tmp_path)

    for module in modules:
        result = module.with_scalar(np.int32(4))

        assert result == (np.int32(8), np.int32(7))
        assert tuple(type(value) for value in result) == (np.int32, np.int32)
