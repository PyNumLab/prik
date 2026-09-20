"""Optional callback presence across source and generated-contract builds."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_or_generated_pyi_and_import


pytestmark = pytest.mark.fortran_end_to_end


SOURCE = """
module fcallback_optional_f90
  use iso_c_binding
  implicit none

  abstract interface
    subroutine report(value, status, values, terminate)
      integer, intent(in) :: value
      integer, intent(in), optional :: status
      real(8), intent(in), optional :: values(:)
      logical, intent(out), optional :: terminate
    end subroutine report

    subroutine c_report(value, status) bind(C)
      import c_int
      integer(c_int), value, intent(in) :: value
      integer(c_int), intent(in), optional :: status
    end subroutine c_report
  end interface

contains

  integer function run(mode, callback) result(output)
    integer, intent(in) :: mode
    procedure(report), optional :: callback
    integer :: status
    real(8) :: values(2)
    logical :: terminate

    output = -1
    if (.not. present(callback)) return
    output = mode
    select case (mode)
    case (0)
      call callback(4)
    case (1)
      status = 9
      call callback(4, status)
    case (2)
      status = 9
      values = [1.5d0, 2.5d0]
      call callback(4, status, values)
    case (3)
      terminate = .false.
      call callback(4, terminate=terminate)
      if (terminate) output = 99
    end select
  end function run

  integer(c_int) function direct_run(mode, callback) bind(C) result(output)
    integer(c_int), value, intent(in) :: mode
    procedure(c_report), optional :: callback
    integer(c_int) :: status

    output = -1_c_int
    if (.not. present(callback)) return
    output = mode
    if (mode == 0_c_int) then
      call callback(4_c_int)
    else
      status = 9_c_int
      call callback(4_c_int, status)
    end if
  end function direct_run
end module fcallback_optional_f90
"""


@pytest.fixture
def optional_callback_module(pyi_parity_build_mode: str, tmp_path: Path):
    source = tmp_path / "fcallback_optional_f90.f90"
    source.write_text(SOURCE, encoding="utf-8")
    module = _build_source_or_generated_pyi_and_import(
        source,
        tmp_path,
        {
            "bind_c_fcallback_optional_f90_wrapper.f90",
            "fcallback_optional_f90_wrapper.c",
            "fcallback_optional_f90_wrapper.h",
        },
        None,
        pyi_parity_build_mode,
    )
    build_dir = (
        tmp_path / "source_build"
        if pyi_parity_build_mode == "source"
        else tmp_path / "generated_pyi_build" / "pyi_build"
    )
    return module, build_dir, pyi_parity_build_mode


def test_optional_callback_and_optional_dummies_preserve_each_presence_state(optional_callback_module):
    module, _build_dir, _build_mode = optional_callback_module

    assert module.run(np.int32(0)) == np.int32(-1)
    assert module.run(np.int32(0), None) == np.int32(-1)

    observed = []

    def report(value, status, values, terminate):
        observed.append((value, status, None if values is None else np.array(values), terminate))
        if terminate is not None:
            terminate[...] = True

    assert module.run(np.int32(0), report) == np.int32(0)
    assert observed[-1] == (np.int32(4), None, None, None)

    assert module.run(np.int32(1), report) == np.int32(1)
    assert observed[-1] == (np.int32(4), np.int32(9), None, None)

    assert module.run(np.int32(2), report) == np.int32(2)
    value, status, values, terminate = observed[-1]
    assert (value, status, terminate) == (np.int32(4), np.int32(9), None)
    np.testing.assert_array_equal(values, np.array([1.5, 2.5], dtype=np.float64))

    assert module.run(np.int32(3), report) == np.int32(99)
    assert observed[-1][1:3] == (None, None)
    assert isinstance(observed[-1][3], np.ndarray)
    assert observed[-1][3].shape == ()


def test_optional_bind_c_callback_remains_direct_and_preserves_inner_presence(optional_callback_module):
    module, build_dir, build_mode = optional_callback_module

    assert module.direct_run(np.int32(0)) == np.int32(-1)
    assert module.direct_run(np.int32(0), None) == np.int32(-1)
    seen = []
    assert module.direct_run(np.int32(0), lambda value, status: seen.append((value, status))) == np.int32(0)
    assert module.direct_run(np.int32(1), lambda value, status: seen.append((value, status))) == np.int32(1)
    assert seen == [(np.int32(4), None), (np.int32(4), np.int32(9))]

    if build_mode == "source":
        binding = (build_dir / "fcallback_optional_f90_wrapper.c").read_text(encoding="utf-8")
        bridge = (build_dir / "bind_c_fcallback_optional_f90_wrapper.f90").read_text(encoding="utf-8")
        assert "direct_run(int32_t mode, void (*callback)(int32_t, void *));" in binding
        assert "direct_run(bound_mode, bound_callback_obj != Py_None ? prik_callback_trampoline_" in binding
        assert "function bind_c_direct_run" not in bridge.casefold()


def test_exception_propagation_is_unchanged_for_a_supplied_optional_callback(optional_callback_module):
    _module, build_dir, _build_mode = optional_callback_module
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import numpy as np; import fcallback_optional_f90 as root; "
                "module = root.fcallback_optional_f90; "
                "module.run(np.int32(0), lambda *args: (_ for _ in ()).throw(ValueError('optional exploded')))"
            ),
        ],
        cwd=build_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "ValueError: optional exploded" in result.stderr
