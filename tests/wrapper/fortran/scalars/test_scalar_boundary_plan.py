"""Isolated compiled parity for primitive scalar boundary representations."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.wrapper.fortran._support import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from x2py import build_pyi_extension


def _build_contract_module(
    tmp_path: Path,
    *,
    module_name: str,
    source_text: str,
    contract_text: str,
):
    source = tmp_path / f"{module_name}.f90"
    source.write_text(source_text, encoding="utf-8")
    contract = tmp_path / f"{module_name}.pyi"
    contract.write_text(contract_text, encoding="utf-8")
    native_object = _compile_native_object(source, tmp_path / "native")

    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    generated_c = (result.output_dir / f"{module_name}_wrapper.c").read_text(encoding="utf-8")
    assert "static PyObject * wrap_" in generated_c
    return _sole_native_module(_import_from_build_dir(result.module_name, result.output_dir))


def _build_scalar_boundary_modules(tmp_path: Path):
    return (
        _build_contract_module(
            tmp_path,
            module_name="scalar_boundary_plan",
            source_text="""
module scalar_boundary_plan
  use iso_c_binding, only: c_double, c_int32_t
contains
  function value_input(value) result(output)
    integer(c_int32_t), intent(in) :: value
    integer(c_int32_t) :: output
    output = value + 2
  end function value_input

  subroutine bump_value(value)
    integer(c_int32_t), intent(inout) :: value
    value = value + 1
  end subroutine bump_value

  subroutine bump_storage(value)
    integer(c_int32_t), intent(inout) :: value
    value = value + 1
  end subroutine bump_storage

  subroutine bump_raw(value)
    integer(c_int32_t), intent(inout) :: value
    value = value + 1
  end subroutine bump_raw

  subroutine bump_storage_float(value)
    real(c_double), intent(inout) :: value
    value = value * 2.0_c_double
  end subroutine bump_storage_float

  subroutine bump_raw_float(value)
    real(c_double), intent(inout) :: value
    value = value * 2.0_c_double
  end subroutine bump_raw_float

  subroutine make_value(value)
    integer(c_int32_t), intent(out) :: value
    value = 41
  end subroutine make_value

  subroutine make_storage(value)
    integer(c_int32_t), intent(out) :: value
    value = 42
  end subroutine make_storage

  subroutine make_raw(value)
    integer(c_int32_t), intent(out) :: value
    value = 43
  end subroutine make_raw

  function direct_storage_result() result(value)
    integer(c_int32_t) :: value
    value = 44
  end function direct_storage_result

  subroutine hidden_storage_result(value)
    integer(c_int32_t), intent(out) :: value
    value = 45
  end subroutine hidden_storage_result

  subroutine mapped_status(status, base)
    integer(c_int32_t), intent(out) :: status
    integer(c_int32_t), intent(in) :: base
    status = base + 11
  end subroutine mapped_status
end module scalar_boundary_plan
""",
            contract_text="""
from x2py.contracts import Addr, Annotated, Arg, Float64, Immutable, Int32, Return, Returns, native_call

def value_input(value: Int32) -> Int32: ...

def bump_value(
    value: Annotated[Int32, Immutable]
) -> Returns["value", Int32]: ...

def bump_storage(value: Int32[()]) -> None: ...

def bump_raw(value: Addr(Int32)) -> None: ...

def bump_storage_float(value: Float64[()]) -> None: ...

def bump_raw_float(value: Addr(Float64)) -> None: ...

@native_call([Return("value", 0)])
def make_value() -> Int32: ...

def make_storage(value: Int32[()]) -> None: ...

def make_raw(value: Addr(Int32)) -> None: ...

def direct_storage_result() -> Int32[()]: ...

@native_call([Return("value", 0)])
def hidden_storage_result() -> Int32[()]: ...

@native_call([Return("status", 0), Addr(Arg(0))])
def mapped_status(base: Int32) -> Int32: ...
""",
        ),
    )


def _build_scalar_kind_modules(tmp_path: Path):
    return (
        _build_contract_module(
            tmp_path,
            module_name="scalar_kind_plan",
            source_text="""
module scalar_kind_plan
  use iso_c_binding, only: c_bool, c_double, c_double_complex, c_float, &
    c_float_complex, c_int8_t, c_int16_t, c_int32_t, c_int64_t
contains
  function id_i8(value) result(output)
    integer(c_int8_t), intent(in) :: value
    integer(c_int8_t) :: output
    output = value
  end function id_i8

  function id_i16(value) result(output)
    integer(c_int16_t), intent(in) :: value
    integer(c_int16_t) :: output
    output = value
  end function id_i16

  function id_i32(value) result(output)
    integer(c_int32_t), intent(in) :: value
    integer(c_int32_t) :: output
    output = value
  end function id_i32

  function id_i64(value) result(output)
    integer(c_int64_t), intent(in) :: value
    integer(c_int64_t) :: output
    output = value
  end function id_i64

  function id_bool(value) result(output)
    logical(c_bool), intent(in) :: value
    logical(c_bool) :: output
    output = value
  end function id_bool

  function id_r32(value) result(output)
    real(c_float), intent(in) :: value
    real(c_float) :: output
    output = value
  end function id_r32

  function id_r64(value) result(output)
    real(c_double), intent(in) :: value
    real(c_double) :: output
    output = value
  end function id_r64

  function conj_c64(value) result(output)
    complex(c_float_complex), intent(in) :: value
    complex(c_float_complex) :: output
    output = conjg(value)
  end function conj_c64

  function conj_c128(value) result(output)
    complex(c_double_complex), intent(in) :: value
    complex(c_double_complex) :: output
    output = conjg(value)
  end function conj_c128
end module scalar_kind_plan
""",
            contract_text="""
from x2py.contracts import Addr, Arg, Bool, Complex128, Complex64, Float32, Float64, Int16, Int32, Int64, Int8, native_call

@native_call([Addr(Arg(0))])
def id_i8(value: Int8) -> Int8: ...

@native_call([Addr(Arg(0))])
def id_i16(value: Int16) -> Int16: ...

@native_call([Addr(Arg(0))])
def id_i32(value: Int32) -> Int32: ...

@native_call([Addr(Arg(0))])
def id_i64(value: Int64) -> Int64: ...

@native_call([Addr(Arg(0))])
def id_bool(value: Bool) -> Bool: ...

@native_call([Addr(Arg(0))])
def id_r32(value: Float32) -> Float32: ...

@native_call([Addr(Arg(0))])
def id_r64(value: Float64) -> Float64: ...

@native_call([Addr(Arg(0))])
def conj_c64(value: Complex64) -> Complex64: ...

@native_call([Addr(Arg(0))])
def conj_c128(value: Complex128) -> Complex128: ...
""",
        ),
    )


def _build_multiple_scalar_result_modules(tmp_path: Path):
    return (
        _build_contract_module(
            tmp_path,
            module_name="multiple_scalar_results_plan",
            source_text="""
module multiple_scalar_results_plan
  use iso_c_binding, only: c_int32_t
contains
  function with_scalar(n, status) result(value)
    integer(c_int32_t), intent(in) :: n
    integer(c_int32_t), intent(out) :: status
    integer(c_int32_t) :: value
    value = n * 2
    status = n + 3
  end function with_scalar
end module multiple_scalar_results_plan
""",
            contract_text="""
from x2py.contracts import Addr, Arg, Int32, Return, native_call

@native_call([Addr(Arg(0)), Return("status", 1)])
def with_scalar(n: Int32) -> tuple[Int32, Int32]: ...
""",
        ),
    )


def _build_scalar_descriptor_result_modules(tmp_path: Path):
    module_name = "scalar_descriptor_results_plan"
    source = tmp_path / f"{module_name}.f90"
    source.write_text(
        """
module scalar_descriptor_results_plan
  use iso_c_binding, only: c_double, c_int32_t
  real(c_double), target, save :: pointer_value = 7.5_c_double
contains
  subroutine maybe_allocatable(flag, value)
    integer(c_int32_t), intent(in) :: flag
    real(c_double), allocatable, intent(out) :: value
    if (flag > 0) then
      allocate(value)
      value = 2.5_c_double
    end if
  end subroutine maybe_allocatable

  subroutine maybe_pointer(flag, value)
    integer(c_int32_t), intent(in) :: flag
    real(c_double), pointer, intent(out) :: value
    if (flag > 0) then
      value => pointer_value
    else
      nullify(value)
    end if
  end subroutine maybe_pointer
end module scalar_descriptor_results_plan
""",
        encoding="utf-8",
    )
    contract = tmp_path / f"{module_name}.pyi"
    contract.write_text(
        """
from x2py.contracts import Allocatable, Arg, Float64, Int32, Pointer, Return, native_call

@native_call([Arg(0), Allocatable(Return("value", 0))])
def maybe_allocatable(flag: Int32) -> Float64 | None: ...

@native_call([Arg(0), Pointer(Return("value", 0))])
def maybe_pointer(flag: Int32) -> Float64 | None: ...
""",
        encoding="utf-8",
    )
    native_object = _compile_native_object(source, tmp_path / "native_scalar_descriptors")
    result = build_pyi_extension(
        contract,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "wrapper_plan_scalar_descriptors",
    )
    return (_sole_native_module(_import_from_build_dir(result.module_name, result.output_dir)),)


def test_scalar_value_storage_raw_address_out_and_inout_use_canonical_plan(tmp_path: Path):
    modules = _build_scalar_boundary_modules(tmp_path)

    for module in modules:
        assert module.value_input(np.int32(5)) == np.int32(7)

        original = np.int32(4)
        replacement = module.bump_value(original)
        assert original == np.int32(4)
        assert replacement == np.int32(5)

        storage = np.array(6, dtype=np.int32)
        assert module.bump_storage(storage) is None
        assert storage[()] == np.int32(7)

        raw = np.array(8, dtype=np.int32)
        assert module.bump_raw(raw.ctypes.data) is None
        assert raw[()] == np.int32(9)

        float_storage = np.array(3.5, dtype=np.float64)
        assert module.bump_storage_float(float_storage) is None
        assert float_storage[()] == np.float64(7.0)

        float_raw = np.array(4.5, dtype=np.float64)
        assert module.bump_raw_float(float_raw.ctypes.data) is None
        assert float_raw[()] == np.float64(9.0)

        assert module.make_value() == np.int32(41)

        output_storage = np.empty((), dtype=np.int32)
        assert module.make_storage(output_storage) is None
        assert output_storage[()] == np.int32(42)

        output_raw = np.empty((), dtype=np.int32)
        assert module.make_raw(output_raw.ctypes.data) is None
        assert output_raw[()] == np.int32(43)

        direct_storage = module.direct_storage_result()
        assert isinstance(direct_storage, np.ndarray)
        assert direct_storage.shape == ()
        assert direct_storage.dtype == np.dtype(np.int32)
        assert direct_storage[()] == np.int32(44)

        hidden_storage = module.hidden_storage_result()
        assert isinstance(hidden_storage, np.ndarray)
        assert hidden_storage.shape == ()
        assert hidden_storage.dtype == np.dtype(np.int32)
        assert hidden_storage[()] == np.int32(45)

        assert module.mapped_status(np.int32(4)) == np.int32(15)

        with pytest.raises(TypeError):
            module.bump_storage(np.int32(6))
        with pytest.raises(TypeError):
            module.bump_storage(np.array(6, dtype=np.int64))
        read_only = np.array(6, dtype=np.int32)
        read_only.flags.writeable = False
        with pytest.raises(TypeError, match="writeable"):
            module.bump_storage(read_only)
        with pytest.raises(TypeError):
            module.bump_raw(raw)


def test_multiple_scalar_results_use_canonical_plan_without_array_blockers(tmp_path: Path):
    modules = _build_multiple_scalar_result_modules(tmp_path)

    for module in modules:
        assert module.with_scalar(np.int32(4)) == (np.int32(8), np.int32(7))


def test_scalar_descriptor_results_copy_values_or_none_through_wrapper_plan_route(tmp_path: Path):
    modules = _build_scalar_descriptor_result_modules(tmp_path)

    for module in modules:
        assert module.maybe_allocatable(np.int32(1)) == np.float64(2.5)
        assert module.maybe_allocatable(np.int32(0)) is None
        assert module.maybe_pointer(np.int32(1)) == np.float64(7.5)
        assert module.maybe_pointer(np.int32(0)) is None


def test_scalar_primitive_kinds_use_canonical_plan_without_array_blockers(tmp_path: Path):
    modules = _build_scalar_kind_modules(tmp_path)

    for module in modules:
        assert module.id_i8(np.int8(np.iinfo(np.int8).min)) == np.int8(np.iinfo(np.int8).min)
        assert module.id_i16(np.int16(np.iinfo(np.int16).max)) == np.int16(np.iinfo(np.int16).max)
        assert module.id_i32(np.int32(np.iinfo(np.int32).min)) == np.int32(np.iinfo(np.int32).min)
        assert module.id_i64(np.int64(2**40)) == np.int64(2**40)
        assert bool(module.id_bool(True)) is True
        assert module.id_r32(np.float32(1.25)) == np.float32(1.25)
        assert module.id_r64(np.float64(-2.5)) == np.float64(-2.5)
        assert module.conj_c64(np.complex64(1 + 2j)) == np.complex64(1 - 2j)
        assert module.conj_c128(np.complex128(2 + 3j)) == np.complex128(2 - 3j)
