"""Writable scalar callback storage on the bridge-free direct `bind(C)` route."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = """
module fcallback_direct_storage_f90
  use iso_c_binding
  implicit none

  abstract interface
    subroutine update_callback(value) bind(C)
      import :: c_double
      real(c_double), intent(inout) :: value
    end subroutine update_callback

    subroutine emit_callback(value) bind(C)
      import :: c_double
      real(c_double), intent(out) :: value
    end subroutine emit_callback
  end interface

contains
  real(c_double) function drive_update(callback, seed) bind(C) result(output)
    procedure(update_callback) :: callback
    real(c_double), value, intent(in) :: seed

    output = seed
    call callback(output)
  end function drive_update

  real(c_double) function drive_emit(callback) bind(C) result(output)
    procedure(emit_callback) :: callback

    call callback(output)
  end function drive_emit
end module fcallback_direct_storage_f90
"""


def _direct_module(tmp_path: Path):
    source = tmp_path / "fcallback_direct_storage_f90.f90"
    source.write_text(SOURCE, encoding="utf-8")
    # A bind(C) entry point needs no generated Fortran adapter, so the expected
    # source set is exactly the binding pair.
    return _build_source_and_import(
        source,
        tmp_path / "build",
        {
            "fcallback_direct_storage_f90_wrapper.c",
            "fcallback_direct_storage_f90_wrapper.h",
        },
    )


def test_direct_bind_c_callbacks_receive_writable_rank_zero_storage(tmp_path: Path):
    """The projection must work where no Fortran bridge exists at all.

    A direct entry point calls the trampoline as a plain C function pointer, so
    writable storage has to be the binding's doing rather than an adapter's.
    """
    module = _direct_module(tmp_path)
    observed = {}

    def update(value):
        observed["writeable"] = value.flags.writeable
        observed["incoming"] = float(value)
        value[...] *= 2

    def emit(value):
        observed["emit_writeable"] = value.flags.writeable
        value[...] = 42.0

    assert module.drive_update(update, np.float64(5.0)) == np.float64(10.0)
    assert module.drive_emit(emit) == np.float64(42.0)
    assert observed == {"writeable": True, "incoming": 5.0, "emit_writeable": True}


def test_direct_bind_c_callback_storage_adds_no_fortran_bridge(tmp_path: Path):
    """Scalar callback storage must not drag a bridge onto the direct route."""
    _direct_module(tmp_path)
    generated = {path.name for path in (tmp_path / "build").glob("*_wrapper.f90")}

    assert generated == set()
