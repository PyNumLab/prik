"""End-to-end Boolean array conversion across supported native storage widths."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_inline_pyi_contract_module, _build_text_and_import


pytestmark = pytest.mark.fortran_end_to_end


_LOGICAL_KIND_ARRAY_SOURCE = """
module logical_kind_arrays
  use, intrinsic :: iso_c_binding, only: c_bool, c_int32_t
  implicit none
contains

  subroutine exercise_c_bool(n, input_values, output_values, inout_values)
    integer(c_int32_t), intent(in) :: n
    logical(kind=c_bool), intent(in) :: input_values(n)
    logical(kind=c_bool), intent(out) :: output_values(n)
    logical(kind=c_bool), intent(inout) :: inout_values(n)
    output_values = .not. input_values
    inout_values = input_values .neqv. inout_values
  end subroutine exercise_c_bool

  subroutine exercise_8(n, input_values, output_values, inout_values)
    integer(c_int32_t), intent(in) :: n
    logical(kind=1), intent(in) :: input_values(n)
    logical(kind=1), intent(out) :: output_values(n)
    logical(kind=1), intent(inout) :: inout_values(n)
    output_values = .not. input_values
    inout_values = input_values .neqv. inout_values
  end subroutine exercise_8

  subroutine exercise_16(n, input_values, output_values, inout_values)
    integer(c_int32_t), intent(in) :: n
    logical(kind=2), intent(in) :: input_values(n)
    logical(kind=2), intent(out) :: output_values(n)
    logical(kind=2), intent(inout) :: inout_values(n)
    output_values = .not. input_values
    inout_values = input_values .neqv. inout_values
  end subroutine exercise_16

  subroutine exercise_32(n, input_values, output_values, inout_values)
    integer(c_int32_t), intent(in) :: n
    logical(kind=4), intent(in) :: input_values(n)
    logical(kind=4), intent(out) :: output_values(n)
    logical(kind=4), intent(inout) :: inout_values(n)
    output_values = .not. input_values
    inout_values = input_values .neqv. inout_values
  end subroutine exercise_32

  subroutine exercise_64(n, input_values, output_values, inout_values)
    integer(c_int32_t), intent(in) :: n
    logical(kind=8), intent(in) :: input_values(n)
    logical(kind=8), intent(out) :: output_values(n)
    logical(kind=8), intent(inout) :: inout_values(n)
    output_values = .not. input_values
    inout_values = input_values .neqv. inout_values
  end subroutine exercise_64

end module logical_kind_arrays
"""


def test_boolean_arrays_copy_only_in_required_directions_for_every_supported_width(tmp_path: Path):
    module = _build_text_and_import(
        _LOGICAL_KIND_ARRAY_SOURCE,
        "logical_kind_arrays.f90",
        tmp_path,
        {
            "bind_c_logical_kind_arrays_wrapper.f90",
            "logical_kind_arrays_wrapper.c",
            "logical_kind_arrays_wrapper.h",
        },
    )
    bridge_source = (tmp_path / "bind_c_logical_kind_arrays_wrapper.f90").read_text(encoding="utf-8")
    assert bridge_source.count("input_values_native = input_values") == 4
    assert bridge_source.count("inout_values_native = inout_values") == 4
    assert "output_values_native = output_values" not in bridge_source
    assert bridge_source.count("output_values = merge(.true._c_bool, .false._c_bool, output_values_native)") == 4
    assert bridge_source.count("inout_values = merge(.true._c_bool, .false._c_bool, inout_values_native)") == 4
    assert "call native_exercise_c_bool(n, input_values, output_values, inout_values)" in bridge_source
    input_values = np.array([True, False, True, False], dtype=np.bool_)
    initial_inout = np.array([False, False, True, True], dtype=np.bool_)
    expected_output = np.logical_not(input_values)
    expected_inout = np.logical_xor(input_values, initial_inout)

    for suffix in ("c_bool", "8", "16", "32", "64"):
        output_values = np.empty(input_values.shape, dtype=np.bool_)
        inout_values = initial_inout.copy()

        result = getattr(module, f"exercise_{suffix}")(
            np.int32(input_values.size),
            input_values,
            output_values,
            inout_values,
        )

        assert result is None
        assert input_values.dtype == output_values.dtype == inout_values.dtype == np.dtype(np.bool_)
        np.testing.assert_array_equal(output_values, expected_output)
        np.testing.assert_array_equal(inout_values, expected_inout)


def test_numbered_boolean_pyi_contracts_probe_and_call_every_supported_width(tmp_path: Path):
    contract = """
from prik.contracts import Bool8, Bool16, Bool32, Bool64, Int32

def exercise_c_bool(
    n: Int32,
    input_values: Bool8[n],
    output_values: Bool8[n],
    inout_values: Bool8[n],
) -> None: ...

def exercise_8(
    n: Int32,
    input_values: Bool8[n],
    output_values: Bool8[n],
    inout_values: Bool8[n],
) -> None: ...

def exercise_16(
    n: Int32,
    input_values: Bool16[n],
    output_values: Bool16[n],
    inout_values: Bool16[n],
) -> None: ...

def exercise_32(
    n: Int32,
    input_values: Bool32[n],
    output_values: Bool32[n],
    inout_values: Bool32[n],
) -> None: ...

def exercise_64(
    n: Int32,
    input_values: Bool64[n],
    output_values: Bool64[n],
    inout_values: Bool64[n],
) -> None: ...
"""
    module, result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="logical_kind_arrays",
        source_text=_LOGICAL_KIND_ARRAY_SOURCE,
        contract_text=contract,
    )
    bridge_source = next(path for path in result.generated_sources if path.suffix == ".f90").read_text(encoding="utf-8")
    assert "call native_exercise_8(n, input_values, output_values, inout_values)" in bridge_source
    assert "logical(kind=2), dimension(input_values_extent_0) :: input_values_native" in bridge_source
    assert "logical(kind=4), dimension(input_values_extent_0) :: input_values_native" in bridge_source
    assert "logical(kind=8), dimension(input_values_extent_0) :: input_values_native" in bridge_source

    input_values = np.array([True, False, True, False], dtype=np.bool_)
    initial_inout = np.array([False, False, True, True], dtype=np.bool_)
    for suffix in ("c_bool", "8", "16", "32", "64"):
        output_values = np.empty(input_values.shape, dtype=np.bool_)
        inout_values = initial_inout.copy()

        getattr(module, f"exercise_{suffix}")(
            np.int32(input_values.size),
            input_values,
            output_values,
            inout_values,
        )

        np.testing.assert_array_equal(output_values, np.logical_not(input_values))
        np.testing.assert_array_equal(inout_values, np.logical_xor(input_values, initial_inout))
