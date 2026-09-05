"""End-to-end Boolean array conversion across supported native storage widths."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from prik import contracts
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

  subroutine replace_c_bool(values)
    logical(kind=c_bool), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_c_bool

  subroutine replace_8(values)
    logical(kind=1), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_8

  subroutine replace_16(values)
    logical(kind=2), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_16

  subroutine replace_32(values)
    logical(kind=4), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_32

  subroutine replace_64(values)
    logical(kind=8), allocatable, intent(inout) :: values(:)
    if (allocated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_64

end module logical_kind_arrays
"""


_LOGICAL_POINTER_SOURCE = """
module logical_pointer_arrays
  implicit none
contains
  subroutine replace_pointer_32(values)
    logical(kind=4), pointer, intent(inout) :: values(:)
    if (associated(values)) deallocate(values)
    allocate(values(3))
    values = .false.
    values(1) = .true.
    values(3) = .true.
  end subroutine replace_pointer_32
end module logical_pointer_arrays
"""


_LOGICAL_KIND_DTYPES = {
    "c_bool": np.bool_,
    "8": np.bool_,
    "16": np.int16,
    "32": np.int32,
    "64": np.int64,
}


def test_boolean_arrays_are_aliased_at_their_own_width_without_any_copy(tmp_path: Path):
    """Every logical kind is passed as the caller's own buffer, whatever its width.

    NumPy has no Boolean wider than one byte, so a logical array is described by
    the integer of matching width. The widths then agree by construction and the
    buffer is aliased directly: no native-kind temporary is declared, nothing is
    widened on the way in, and nothing is narrowed on the way out.
    """
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
    assert "call native_exercise_c_bool(n, input_values, output_values, inout_values)" in bridge_source

    for suffix, dtype in _LOGICAL_KIND_DTYPES.items():
        input_values = np.array([1, 0, 1, 0], dtype=dtype)
        initial_inout = np.array([0, 0, 1, 1], dtype=dtype)
        output_values = np.empty(input_values.shape, dtype=dtype)
        inout_values = initial_inout.copy()

        result = getattr(module, f"exercise_{suffix}")(
            np.int32(input_values.size),
            input_values,
            output_values,
            inout_values,
        )

        assert result is None
        assert output_values.dtype == inout_values.dtype == np.dtype(dtype), suffix
        # The values are Fortran logicals, so they are read back as truth
        # rather than compared against any one integer the compiler chose.
        np.testing.assert_array_equal(
            output_values.astype(bool), np.logical_not(input_values.astype(bool)), err_msg=suffix
        )
        np.testing.assert_array_equal(
            inout_values.astype(bool),
            np.logical_xor(input_values.astype(bool), initial_inout.astype(bool)),
            err_msg=suffix,
        )


def test_numbered_boolean_pyi_contracts_probe_and_call_every_supported_width(tmp_path: Path):
    contract = """
from prik.contracts import Allocatable, Bool8, Bool16, Bool32, Bool64, Int32

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

def replace_c_bool(values: Allocatable[Bool8[:]]) -> None: ...
def replace_8(values: Allocatable[Bool8[:]]) -> None: ...
def replace_16(values: Allocatable[Bool16[:]]) -> None: ...
def replace_32(values: Allocatable[Bool32[:]]) -> None: ...
def replace_64(values: Allocatable[Bool64[:]]) -> None: ...
"""
    module, result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="logical_kind_arrays",
        source_text=_LOGICAL_KIND_ARRAY_SOURCE,
        contract_text=contract,
    )
    bridge_source = next(path for path in result.generated_sources if path.suffix == ".f90").read_text(encoding="utf-8")
    assert "call native_exercise_8(n, input_values, output_values, inout_values)" in bridge_source
    # Each numbered contract width aliases a buffer of its own size.
    for kind in ("logical(c_bool)", "logical(2)", "logical(4)", "logical(8)"):
        assert f"{kind}, pointer, contiguous, dimension(:) :: input_values" in bridge_source, kind

    for suffix, dtype in _LOGICAL_KIND_DTYPES.items():
        input_values = np.array([1, 0, 1, 0], dtype=dtype)
        initial_inout = np.array([0, 0, 1, 1], dtype=dtype)
        output_values = np.empty(input_values.shape, dtype=dtype)
        inout_values = initial_inout.copy()

        getattr(module, f"exercise_{suffix}")(
            np.int32(input_values.size),
            input_values,
            output_values,
            inout_values,
        )

        np.testing.assert_array_equal(
            output_values.astype(bool), np.logical_not(input_values.astype(bool)), err_msg=suffix
        )
        np.testing.assert_array_equal(
            inout_values.astype(bool),
            np.logical_xor(input_values.astype(bool), initial_inout.astype(bool)),
            err_msg=suffix,
        )

    handle_contracts = {
        "c_bool": contracts.Bool8,
        "8": contracts.Bool8,
        "16": contracts.Bool16,
        "32": contracts.Bool32,
        "64": contracts.Bool64,
    }
    for suffix, dtype in _LOGICAL_KIND_DTYPES.items():
        handle = contracts.Allocatable[handle_contracts[suffix][:]]()
        try:
            assert getattr(module, f"replace_{suffix}")(handle) is None
            assert handle.dtype == np.dtype(dtype)
            assert handle.shape == (3,)
            np.testing.assert_array_equal(handle.to_numpy().astype(bool), [True, False, True])
        finally:
            handle.close()


def test_caller_created_wide_logical_pointer_uses_its_native_width(tmp_path: Path):
    contract = """
from prik.contracts import Annotated, Bool32, Pointer, PointerPolicy

def replace_pointer_32(
    values: Annotated[
        Pointer[Bool32[:]],
        PointerPolicy(
            nullable=True,
            transfer="call_local",
            target_owner="caller",
            lifetime="call",
            deallocation="deallocate_resize",
            shape_source="pointer_bounds",
            contiguity="contiguous",
            reassociation="allocate_resize",
            aliasing="descriptor",
            mutability="mutable",
        ),
    ],
) -> None: ...
"""
    module, _result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="logical_pointer_arrays",
        source_text=_LOGICAL_POINTER_SOURCE,
        contract_text=contract,
    )
    pointer = contracts.Pointer[contracts.Bool32[:]]()
    try:
        assert module.replace_pointer_32(pointer) is None
        assert pointer.dtype == np.dtype(np.int32)
        assert pointer.shape == (3,)
        np.testing.assert_array_equal(pointer.to_numpy().astype(bool), [True, False, True])
        pointer.deallocate()
    finally:
        pointer.close()
