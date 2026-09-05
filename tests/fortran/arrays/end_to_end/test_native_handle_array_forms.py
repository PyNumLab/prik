"""Generated handles used as every supported ordinary Fortran array form."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from prik.runtime.handles import AllocatableArray, PointerArray
from tests.fortran._support.wrapper_build import _build_text_and_import


pytestmark = pytest.mark.fortran_end_to_end


NATIVE_HANDLE_ARRAY_FORMS_SOURCE = """\
module fhandle_array_forms_f90
  implicit none
  real(8), allocatable :: values(:)
  real(8), allocatable :: matrix(:, :)
  real(8), allocatable :: hyper(:, :, :, :, :, :, :, :, :, :, :, :, :, :, :)
  real(8), target :: backing(8)
  real(8), pointer :: strided_values(:)
  character(len=:), allocatable :: words(:)
contains
  subroutine setup()
    integer :: i

    allocate(values(4))
    values = [1.0_8, 2.0_8, 3.0_8, 4.0_8]
    allocate(matrix(2, 3))
    matrix = reshape([(1.0_8 * i, i = 1, 6)], [2, 3])
    allocate(hyper(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1))
    hyper = 1.0_8
    backing = [(1.0_8 * i, i = 1, 8)]
    strided_values => backing(1:8:2)
    allocate(character(len=5) :: words(2))
    words = [character(len=5) :: "alpha", "bravo"]
  end subroutine setup

  function explicit_total(actual, n) result(total)
    integer(4), intent(in) :: n
    real(8), intent(in) :: actual(n)
    real(8) :: total

    total = sum(actual)
  end function explicit_total

  function assumed_total(actual) result(total)
    real(8), intent(in) :: actual(:)
    real(8) :: total

    total = sum(actual)
  end function assumed_total

  function flat_total(actual, n) result(total)
    integer(4), intent(in) :: n
    real(8), intent(in) :: actual(*)
    real(8) :: total

    total = sum(actual(:n))
  end function flat_total

  function optional_total(actual) result(total)
    real(8), intent(in), optional :: actual(:)
    real(8) :: total

    if (present(actual)) then
      total = sum(actual)
    else
      total = -1.0_8
    end if
  end function optional_total

  function rank_score(actual) result(score)
    real(8), intent(in) :: actual(..)
    integer(4) :: score

    select rank (actual)
    rank (1)
      score = 100 + size(actual)
    rank (2)
      score = 200 + size(actual)
    rank (15)
      score = 1500 + size(actual)
    rank default
      score = -1
    end select
  end function rank_score

  function element_width(actual) result(width)
    character(len=*), intent(in) :: actual(:)
    integer(4) :: width

    width = len(actual)
  end function element_width
end module fhandle_array_forms_f90
"""


def test_generated_handles_cover_supported_ordinary_array_forms(tmp_path: Path):
    module = _build_text_and_import(
        NATIVE_HANDLE_ARRAY_FORMS_SOURCE,
        "fhandle_array_forms_f90.f90",
        tmp_path,
        {
            "bind_c_fhandle_array_forms_f90_wrapper.f90",
            "fhandle_array_forms_f90_wrapper.c",
            "fhandle_array_forms_f90_wrapper.h",
        },
    )

    values = module.values
    strided = module.strided_values
    assert isinstance(values, AllocatableArray)
    assert isinstance(strided, PointerArray)
    with pytest.raises(ValueError, match="unallocated"):
        module.assumed_total(values)
    with pytest.raises(ValueError, match="unassociated"):
        module.assumed_total(strided)

    module.setup()

    assert module.explicit_total(values, np.int32(4)) == np.float64(10.0)
    assert module.assumed_total(values) == np.float64(10.0)
    assert module.flat_total(values, np.int32(4)) == np.float64(10.0)
    assert module.optional_total() == np.float64(-1.0)
    assert module.optional_total(None) == np.float64(-1.0)
    assert module.optional_total(values) == np.float64(10.0)
    assert module.rank_score(values) == np.int32(104)
    assert module.rank_score(module.matrix) == np.int32(206)
    assert module.rank_score(module.hyper) == np.int32(1501)
    assert module.assumed_total(strided) == np.float64(16.0)
    assert module.element_width(module.words) == np.int32(5)

    with pytest.raises(TypeError, match="incompatible shape at axis 0"):
        module.explicit_total(values, np.int32(3))
    with pytest.raises(TypeError, match="does not match expected dtype"):
        module.assumed_total(module.words)
