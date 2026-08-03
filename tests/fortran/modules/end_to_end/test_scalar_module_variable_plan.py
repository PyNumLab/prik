"""Whole-module parity for scalar native module state."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_wrapper_plan_and_import,
    _sole_native_module,
)
from prik.runtime.handles import AllocatableArray

pytestmark = pytest.mark.fortran_end_to_end

SCALAR_MODULE_SOURCE = """\
module fscalar_module_state_f90
  implicit none
  integer(4), parameter :: nmax = 12
  integer(4), parameter :: computed_limit = kind(1.0) * 2
  character*1, parameter :: prefix = 'D'
  integer(4) :: counter = 3
  real(8), target :: target_scale = 1.5_8
  real(8), allocatable :: optional_scale
  real(8), pointer :: selected_scale => null()
  real(8), allocatable :: values(:)
contains
  function summarize() result(value)
    integer(4) :: value

    value = counter + nmax
  end function summarize

  function set_allocatable(value) result(current)
    real(8), intent(in) :: value
    real(8) :: current

    if (allocated(optional_scale)) deallocate(optional_scale)
    allocate(optional_scale)
    optional_scale = value
    current = optional_scale
  end function set_allocatable

  function point_to_target(value) result(current)
    real(8), intent(in) :: value
    real(8) :: current

    target_scale = value
    selected_scale => target_scale
    current = selected_scale
  end function point_to_target

  function bump_native() result(total)
    real(8) :: total

    if (allocated(optional_scale)) optional_scale = optional_scale + 10.0_8
    if (associated(selected_scale)) selected_scale = selected_scale + 20.0_8
    total = 0.0_8
    if (allocated(optional_scale)) total = total + optional_scale
    if (associated(selected_scale)) total = total + selected_scale
  end function bump_native

  function clear_all() result(status)
    integer(4) :: status

    if (allocated(optional_scale)) deallocate(optional_scale)
    nullify(selected_scale)
    status = 0
  end function clear_all

  subroutine allocate_values(n)
    integer(4), intent(in) :: n
    integer(4) :: i

    if (allocated(values)) deallocate(values)
    allocate(values(n))
    values = [(real(i, 8), i = 1, n)]
  end subroutine allocate_values

  subroutine scale_values(factor)
    real(8), intent(in) :: factor

    values = factor * values
  end subroutine scale_values

  subroutine deallocate_values()
    if (allocated(values)) deallocate(values)
  end subroutine deallocate_values
end module fscalar_module_state_f90
"""


def _write_whole_scalar_module(root: Path) -> Path:
    root.mkdir(parents=True)
    source = root / "fscalar_module_state_f90.f90"
    source.write_text(SCALAR_MODULE_SOURCE, encoding="utf-8")
    return source


def _reload_native_module(build_dir: Path):
    sys.modules.pop("fscalar_module_state_f90", None)
    sys.path.insert(0, str(build_dir))
    try:
        return _sole_native_module(importlib.import_module("fscalar_module_state_f90"))
    finally:
        sys.path.remove(str(build_dir))


def test_whole_scalar_module_variable_behavior_uses_canonical_plan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    source = _write_whole_scalar_module(tmp_path / "fixture")
    expected_sources = {
        "bind_c_fscalar_module_state_f90_wrapper.f90",
        "fscalar_module_state_f90_wrapper.c",
        "fscalar_module_state_f90_wrapper.h",
    }
    module, result = _build_source_wrapper_plan_and_import(source, tmp_path / "build")
    build_dir = result.output_dir
    assert {path.name for path in result.generated_sources} == expected_sources

    assert module.nmax == np.int32(12)
    assert module.computed_limit == np.int32(8)
    assert module.prefix == "D"
    assert module.counter == np.int32(3)
    assert module.target_scale == np.float64(1.5)
    assert module.optional_scale is None
    assert module.selected_scale is None
    values = module.values
    assert isinstance(values, AllocatableArray)
    assert values.allocated is False
    assert values.to_numpy() is None
    assert module.summarize() == np.int32(15)

    module.counter = np.int32(9)
    assert module.counter == np.int32(9)
    assert module.summarize() == np.int32(21)
    with pytest.raises(TypeError):
        module.counter = np.float64(4.0)
    with pytest.raises(AttributeError):
        del module.counter
    with pytest.raises(AttributeError):
        module.optional_scale = np.float64(9.0)
    with pytest.raises(AttributeError):
        module.selected_scale = np.float64(9.0)

    assert module.set_allocatable(np.float64(1.5)) == np.float64(1.5)
    allocatable_snapshot = module.optional_scale
    assert module.point_to_target(np.float64(2.5)) == np.float64(2.5)
    pointer_snapshot = module.selected_scale
    assert module.bump_native() == np.float64(34.0)
    assert allocatable_snapshot == np.float64(1.5)
    assert pointer_snapshot == np.float64(2.5)
    assert module.optional_scale == np.float64(11.5)
    assert module.selected_scale == np.float64(22.5)

    module.allocate_values(np.int32(3))
    assert module.values is values
    live_values = values.to_numpy()
    np.testing.assert_array_equal(live_values, np.array([1.0, 2.0, 3.0], dtype=np.float64))
    live_values[0] = np.float64(9.0)
    module.scale_values(np.float64(2.0))
    np.testing.assert_array_equal(live_values, np.array([18.0, 4.0, 6.0], dtype=np.float64))
    module.deallocate_values()
    assert values.allocated is False
    assert values.to_numpy() is None

    monkeypatch.setenv("PRIK_WRAPPER_FAIL_ALLOC", "1")
    assert module.optional_scale is None
    assert module.selected_scale is None
    monkeypatch.delenv("PRIK_WRAPPER_FAIL_ALLOC")
    assert module.optional_scale == np.float64(11.5)
    assert module.selected_scale == np.float64(22.5)

    module.nmax = np.int32(99)
    assert module.nmax == np.int32(99)
    assert module.summarize() == np.int32(21)
    reloaded = _reload_native_module(build_dir)
    assert reloaded.nmax == np.int32(12)
    assert reloaded.counter == np.int32(9)
    assert reloaded.summarize() == np.int32(21)

    c_source = (build_dir / "fscalar_module_state_f90_wrapper.c").read_text(encoding="utf-8")
    fortran_source = (build_dir / "bind_c_fscalar_module_state_f90_wrapper.f90").read_text(encoding="utf-8")
    assert "bind_c_get_counter" in c_source
    assert "bind_c_get_computed_limit" in c_source
    assert 'PyUnicode_FromString("D")' in c_source
    assert "bind_c_set_counter" in c_source
    assert "bind_c_get_optional_scale" in c_source
    assert "bind_c_get_selected_scale" in c_source
    assert "function bind_c_get_counter()" in fortran_source
    assert "function bind_c_get_computed_limit()" in fortran_source
    assert "subroutine bind_c_set_counter(" in fortran_source
    assert "function bind_c_get_optional_scale()" in fortran_source
    assert "function bind_c_get_selected_scale()" in fortran_source
    assert "bind(c" in fortran_source
