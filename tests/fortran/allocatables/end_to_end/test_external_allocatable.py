"""Caller-created allocatable handles passed to standalone externals."""

from pathlib import Path

import numpy as np
import pytest

import prik.contracts as contracts
from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
)
from prik import build_pyi_extension

pytestmark = pytest.mark.fortran_end_to_end


def test_external_allocatable_argument_accepts_a_caller_created_handle(tmp_path: Path):
    source = tmp_path / "external_allocatable.f90"
    source.write_text(
        """
subroutine replace_external(values)
  double precision, allocatable, intent(inout) :: values(:)
  if (allocated(values)) deallocate(values)
  allocate(values(3))
  values = [2.0d0, 4.0d0, 6.0d0]
end subroutine replace_external
""",
        encoding="utf-8",
    )
    contract = tmp_path / "external_allocatable.pyi"
    contract.write_text(
        """from prik.contracts import Allocatable, Float64, Returns, external

@external
def replace_external(
    values: Allocatable[Float64[:]],
) -> Returns["values", Allocatable[Float64[:]]]: ...
""",
        encoding="utf-8",
    )
    native_object = _compile_native_object(source, tmp_path / "native")
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        output_name="external_allocatable_api",
        output_dir=tmp_path / "build",
    )
    module = _import_from_build_dir(result.module_name, result.output_dir)
    handle = contracts.Allocatable[contracts.Float64[:]]()

    returned = module.replace_external(handle)

    assert returned is handle
    assert handle.allocated is True
    np.testing.assert_allclose(handle.to_numpy(), [2.0, 4.0, 6.0])
    handle.close()
