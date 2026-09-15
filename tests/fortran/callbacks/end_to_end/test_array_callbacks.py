"""Array callback argument and result conversion tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_and_import,
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
CALLBACK_ARRAY_F90_SOURCE = FIXTURES / "native" / "fcallback_array_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_immediate_dummy_procedure_converts_array_arguments_and_results(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        CALLBACK_ARRAY_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fcallback_array_f90_wrapper.f90",
            "fcallback_array_f90_wrapper.c",
            "fcallback_array_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fcallback_array_f90",
        pyi_parity_build_mode,
    )
    values = np.asfortranarray(np.array([1.0, 2.0, 3.0], dtype=np.float64))

    assert module.apply_reduce(lambda count, data: data[:count].sum(), np.int32(3), values) == np.float64(6.0)
    transformed = np.empty_like(values)
    result = module.apply_transform(
        lambda count, data: np.asfortranarray(data[:count] * 2.0),
        np.int32(3),
        values,
        transformed,
    )
    assert result is None
    np.testing.assert_array_equal(transformed, np.array([2.0, 4.0, 6.0], dtype=np.float64))


def test_assumed_shape_callback_arrays_cross_the_boundary_as_contiguous_copies(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    """An assumed-shape callback dummy carries its extent from the native descriptor."""
    module = _build_source_or_generated_pyi_and_import(
        CALLBACK_ARRAY_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fcallback_array_f90_wrapper.f90",
            "fcallback_array_f90_wrapper.c",
            "fcallback_array_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fcallback_array_f90",
        pyi_parity_build_mode,
    )
    values = np.asfortranarray(np.array([1.5, 2.5, 3.5, 4.5], dtype=np.float64))
    doubled = np.zeros(4, dtype=np.float64)
    seen = []

    def double(data, output):
        seen.append(np.array(data))
        output[...] = data * 2.0

    assert module.apply_assumed_shape(double, values, doubled) is None
    np.testing.assert_array_equal(seen[0], values)
    np.testing.assert_array_equal(doubled, values * 2.0)


MATRIX_SOURCE = """
module fcallback_matrix_f90
  implicit none

  abstract interface
    subroutine matrix_callback(input, output)
      real(8), intent(in) :: input(:,:)
      real(8), intent(out) :: output(:,:)
    end subroutine matrix_callback
  end interface

contains
  subroutine apply_matrix(callback, input, output)
    procedure(matrix_callback) :: callback
    real(8), intent(in) :: input(:,:)
    real(8), intent(out) :: output(:,:)

    call callback(input, output)
  end subroutine apply_matrix
end module fcallback_matrix_f90
"""


def test_rank_two_assumed_shape_callback_arrays_cross_both_directions(tmp_path: Path):
    """Every axis of a multidimensional assumed-shape dummy must survive.

    A rank-one lowering can look correct while dropping later axes, so this
    checks the extents the callable observes and the data written back.
    """
    source = tmp_path / "fcallback_matrix_f90.f90"
    source.write_text(MATRIX_SOURCE, encoding="utf-8")
    module = _build_source_and_import(
        source,
        tmp_path / "build",
        {
            "bind_c_fcallback_matrix_f90_wrapper.f90",
            "fcallback_matrix_f90_wrapper.c",
            "fcallback_matrix_f90_wrapper.h",
        },
    )
    incoming = np.asfortranarray(np.arange(6, dtype=np.float64).reshape(2, 3))
    written = np.asfortranarray(np.zeros((2, 3), dtype=np.float64))
    observed = {}

    def double(input_values, output_values):
        observed["shape"] = input_values.shape
        observed["values"] = np.array(input_values)
        output_values[...] = input_values * 2.0

    assert module.apply_matrix(double, incoming, written) is None
    assert observed["shape"] == (2, 3)
    np.testing.assert_array_equal(observed["values"], incoming)
    np.testing.assert_array_equal(written, incoming * 2.0)
