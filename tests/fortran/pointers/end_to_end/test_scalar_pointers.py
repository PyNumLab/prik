"""Scalar pointer values across module, argument, output, and result boundaries."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_text_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from x2py import build_pyi_extension

pytestmark = pytest.mark.fortran_end_to_end

SCALAR_POINTER_SOURCE = """\
module fscalar_pointers_f90
  implicit none
  real(8), target :: target_scale
  real(8), pointer :: selected_scale => null()
contains
  subroutine clear_pointer()
    nullify(selected_scale)
  end subroutine clear_pointer

  subroutine point_to_target(value)
    real(8), intent(in) :: value
    target_scale = value
    selected_scale => target_scale
  end subroutine point_to_target

  subroutine bump_native()
    if (associated(selected_scale)) selected_scale = selected_scale + 20.0_8
  end subroutine bump_native

  function echo_pointer(value) result(out)
    real(8), pointer, intent(in) :: value
    real(8) :: out
    if (associated(value)) then
      out = value + 2.0_8
    else
      out = -2.0_8
    end if
  end function echo_pointer

  subroutine update_pointer(value)
    real(8), pointer, intent(inout) :: value
    if (associated(value)) then
      value = value + 20.0_8
    else
      target_scale = 20.0_8
      value => target_scale
    end if
  end subroutine update_pointer

  subroutine clear_pointer_value(value)
    real(8), pointer, intent(inout) :: value
    nullify(value)
  end subroutine clear_pointer_value

  subroutine create_pointer(value)
    real(8), pointer, intent(out) :: value
    target_scale = 40.0_8
    value => target_scale
  end subroutine create_pointer

  function maybe_pointer(flag) result(value)
    integer(4), intent(in) :: flag
    real(8), pointer :: value
    if (flag /= 0) then
      target_scale = 4.5_8
      value => target_scale
    else
      nullify(value)
    end if
  end function maybe_pointer
end module fscalar_pointers_f90
"""


def _scalar_pointer_module(build_mode: str, tmp_path: Path):
    filename = "fscalar_pointers_f90.f90"
    expected_sources = {
        "bind_c_fscalar_pointers_f90_wrapper.f90",
        "fscalar_pointers_f90_wrapper.c",
        "fscalar_pointers_f90_wrapper.h",
    }
    if build_mode == "source":
        source_build_dir = tmp_path / "source_build"
        source_build_dir.mkdir(parents=True)
        return _build_text_and_import(
            SCALAR_POINTER_SOURCE,
            filename,
            source_build_dir,
            expected_sources,
        )

    source_dir = tmp_path / "source"
    source_dir.mkdir(parents=True)
    source = source_dir / filename
    source.write_text(SCALAR_POINTER_SOURCE, encoding="utf-8")
    contract_dir = tmp_path / "contracts" / source.stem
    subprocess.run(
        [sys.executable, "-m", "x2py", "generate", "--pyi", str(source), "--out", str(contract_dir)],
        capture_output=True,
        text=True,
        check=True,
    )
    native_object = _compile_native_object(source, tmp_path / "native")
    result = build_pyi_extension(
        contract_dir / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "pyi_build",
    )
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def test_scalar_pointers_project_nullable_copied_values(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _scalar_pointer_module(pyi_parity_build_mode, tmp_path)

    module.clear_pointer()
    assert module.selected_scale is None
    with pytest.raises(AttributeError):
        module.selected_scale = np.float64(9.0)

    module.point_to_target(np.float64(2.5))
    snapshot = module.selected_scale
    assert snapshot == np.float64(2.5)
    module.bump_native()
    assert snapshot == np.float64(2.5)
    assert module.selected_scale == np.float64(22.5)

    assert module.echo_pointer(np.float64(3.0)) == np.float64(5.0)
    assert module.echo_pointer(None) == np.float64(-2.0)
    assert module.update_pointer(np.float64(3.0)) == np.float64(23.0)
    assert module.update_pointer(None) == np.float64(20.0)
    assert module.clear_pointer_value(np.float64(3.0)) is None
    assert module.create_pointer() == np.float64(40.0)
    assert module.maybe_pointer(np.int32(1)) == np.float64(4.5)
    assert module.maybe_pointer(np.int32(0)) is None

    module.clear_pointer()
    assert module.selected_scale is None
