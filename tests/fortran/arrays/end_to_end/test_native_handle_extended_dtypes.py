"""Native handles preserve the NumPy dtype for target-dependent primitives."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_inline_pyi_contract_module, _build_text_and_import, _compiler

pytestmark = pytest.mark.fortran_end_to_end


SOURCE = r"""\
module fextended_handle_dtypes
  use iso_c_binding, only: c_long_double, c_long_double_complex
  implicit none

  real(c_long_double), allocatable :: real_values(:)
  complex(c_long_double_complex), pointer :: complex_values(:) => null()

contains

  subroutine setup()
    integer :: i

    if (allocated(real_values)) deallocate(real_values)
    allocate(real_values(2))
    real_values = [1.0_c_long_double, 2.0_c_long_double]

    if (associated(complex_values)) deallocate(complex_values)
    allocate(complex_values(2))
    complex_values = [(cmplx(i, -i, kind=c_long_double_complex), i = 1, 2)]

  end subroutine setup

  function sum_real(values) result(total)
    real(c_long_double), intent(in) :: values(:)
    real(c_long_double) :: total
    total = sum(values)
  end function sum_real

  function sum_complex(values) result(total)
    complex(c_long_double_complex), intent(in) :: values(:)
    complex(c_long_double_complex) :: total
    total = sum(values)
  end function sum_complex

end module fextended_handle_dtypes
"""

SIZE_SOURCE = r"""\
module fsize_handle
  use iso_c_binding, only: c_size_t
  implicit none
  integer(c_size_t), allocatable :: values(:)
contains
  subroutine setup()
    if (allocated(values)) deallocate(values)
    allocate(values(2))
    values = [4_c_size_t, 8_c_size_t]
  end subroutine setup

  function total() result(value)
    integer(c_size_t) :: value
    value = sum(values)
  end function total
end module fsize_handle
"""

SIZE_CONTRACT = """\
from prik.contracts import Allocatable, SizeT

values: Allocatable[SizeT[:]]

def setup() -> None: ...

def total() -> SizeT: ...
"""


def _build_module(tmp_path: Path):
    return _build_text_and_import(
        SOURCE,
        "fextended_handle_dtypes.f90",
        tmp_path,
        {
            "bind_c_fextended_handle_dtypes_wrapper.f90",
            "fextended_handle_dtypes_wrapper.c",
            "fextended_handle_dtypes_wrapper.h",
        },
    )


def test_native_handles_support_long_double_and_complex(tmp_path: Path):
    if Path(_compiler()).name.lower() == "ifx":
        pytest.skip("ifx long double is wider than the host NumPy longdouble")
    module = _build_module(tmp_path)
    module.setup()

    real_values = module.real_values
    assert real_values.to_numpy().dtype == np.dtype(np.longdouble)
    assert module.sum_real(real_values) == np.longdouble(3)

    complex_values = module.complex_values
    assert complex_values.associated is True
    assert complex_values.shape == (2,)
    assert module.sum_complex(complex_values) == np.clongdouble(3 - 3j)


def test_size_t_contract_handles_use_numpy_uintp(tmp_path: Path):
    module, _ = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="fsize_handle",
        source_text=SIZE_SOURCE,
        contract_text=SIZE_CONTRACT,
    )
    module.setup()

    values = module.values
    assert values.to_numpy().dtype == np.dtype(np.uintp)
    assert module.total() == np.uintp(12)
