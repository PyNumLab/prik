"""Rank-zero callback storage: an edited contract writes through native memory."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_inline_pyi_contract_module,
    _build_source_and_import,
)

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = """
module fcallback_scalar_storage_f90
  implicit none

  abstract interface
    subroutine directions_callback(read_value, update_value, write_value)
      real(8), intent(in) :: read_value
      real(8), intent(inout) :: update_value
      real(8), intent(out) :: write_value
    end subroutine directions_callback
  end interface

contains
  subroutine apply_directions(callback, read_value, update_value, write_value)
    procedure(directions_callback) :: callback
    real(8), intent(in) :: read_value
    real(8), intent(inout) :: update_value
    real(8), intent(out) :: write_value

    call callback(read_value, update_value, write_value)
  end subroutine apply_directions
end module fcallback_scalar_storage_f90
"""

CONTRACT = """
from prik.contracts import Addr, Arg, Float64, In, InOut, Out, Return, Returns, native_call, prototype

@prototype
def directions_callback(
    read_value: In(Float64[()]),
    update_value: InOut(Float64[()]),
    write_value: Out(Float64[()])
) -> None: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Return('write_value', 1)])
def apply_directions(
    callback: directions_callback,
    read_value: Float64,
    update_value: Float64
) -> tuple[Returns["update_value", Float64], Float64]: ...
"""


def test_rank_zero_callback_storage_writes_through_to_the_native_caller(tmp_path: Path):
    """A rank-zero storage dummy exposes native memory with direction-correct access.

    The default `Addr(T)` spelling hands Python an independent value, so a
    contract that needs an `out` or `inout` callback dummy to reach the native
    caller asks for storage instead.
    """
    module, _result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="fcallback_scalar_storage_f90",
        source_text=SOURCE,
        contract_text=CONTRACT,
    )
    observed = {}

    def callback(read_value, update_value, write_value):
        observed["read_writeable"] = read_value.flags.writeable
        observed["update_writeable"] = update_value.flags.writeable
        observed["write_writeable"] = write_value.flags.writeable
        observed["read"] = float(read_value)
        observed["update_in"] = float(update_value)
        update_value[...] = float(update_value) * 10.0
        write_value[...] = float(read_value) + float(update_value)

    updated, written = module.apply_directions(callback, np.float64(3.0), np.float64(4.0))

    assert observed == {
        "read_writeable": False,
        "update_writeable": True,
        "write_writeable": True,
        "read": 3.0,
        "update_in": 4.0,
    }
    assert updated == np.float64(40.0)
    assert written == np.float64(43.0)


SOURCE_DEFAULT = """
module fcallback_default_storage_f90
  implicit none

  abstract interface
    subroutine objective_callback(x, f)
      real(8), intent(in) :: x(:)
      real(8), intent(out) :: f
    end subroutine objective_callback
  end interface

contains
  subroutine evaluate(calfun, x, total)
    procedure(objective_callback) :: calfun
    real(8), intent(in) :: x(:)
    real(8), intent(out) :: total

    call calfun(x, total)
  end subroutine evaluate
end module fcallback_default_storage_f90
"""


def test_out_scalar_callback_writes_back_without_editing_the_contract(tmp_path: Path):
    """Wrapping Fortran source directly produces a callback that can answer.

    The generated default must be the spelling that works: an `intent(out)`
    scalar reaches Python as writable storage, so the value the callable
    computes reaches the native caller with no contract edit.
    """
    source = tmp_path / "fcallback_default_storage_f90.f90"
    source.write_text(SOURCE_DEFAULT, encoding="utf-8")
    module = _build_source_and_import(
        source,
        tmp_path / "build",
        {
            "bind_c_fcallback_default_storage_f90_wrapper.f90",
            "fcallback_default_storage_f90_wrapper.c",
            "fcallback_default_storage_f90_wrapper.h",
        },
    )

    def objective(x):
        return float(np.sum(x * x))

    def objective_prik(x, f):
        f[...] = objective(x)

    assert module.evaluate(objective_prik, np.array([1.0, 2.0, 3.0])) == np.float64(14.0)


def test_callback_docstring_states_the_callable_signature_and_write_through(tmp_path: Path):
    """The docstring is the only callback description in the source-only workflow.

    Guessing a callback signature wrong is fatal at the callback boundary, so
    `help()` must state the arity, direction, and how an output is delivered.
    """
    source = tmp_path / "fcallback_default_storage_f90.f90"
    source.write_text(SOURCE_DEFAULT, encoding="utf-8")
    module = _build_source_and_import(
        source,
        tmp_path / "build",
        {
            "bind_c_fcallback_default_storage_f90_wrapper.f90",
            "fcallback_default_storage_f90_wrapper.c",
            "fcallback_default_storage_f90_wrapper.h",
        },
    )
    documentation = module.evaluate.__doc__

    assert "Called as: calfun(x, f) -> None" in documentation
    assert "x : ndarray[float64], intent(in)" in documentation
    assert "f : ndarray[float64], intent(out); assign through it (f[...] = value)" in documentation
    assert "An exception or an invalid return value terminates the process." in documentation
