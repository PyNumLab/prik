"""Source and generated-contract runtime parity for primitive scalar kinds."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
SCALAR_KINDS_F90_SOURCE = FIXTURES / "fscalar_kinds_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


@pytest.fixture
def compiled_scalar_kind_module(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    return _build_source_or_generated_pyi_and_import(
        SCALAR_KINDS_F90_SOURCE,
        tmp_path,
        {
            "bind_c_fscalar_kinds_f90_wrapper.f90",
            "fscalar_kinds_f90_wrapper.c",
            "fscalar_kinds_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fscalar_kinds_f90",
        pyi_parity_build_mode,
    )


def test_scalar_kind_coverage_uses_compiler_probed_wrapper_types(
    compiled_scalar_kind_module,
):
    module = compiled_scalar_kind_module

    assert module.id_i8(np.int8(np.iinfo(np.int8).min)) == np.iinfo(np.int8).min
    assert module.id_i16(np.int16(np.iinfo(np.int16).max)) == np.iinfo(np.int16).max
    assert module.id_i32(np.int32(np.iinfo(np.int32).min)) == np.iinfo(np.int32).min
    assert module.id_i32_value(np.int32(17)) == np.int32(17)
    assert module.id_i64(np.int64(2**40)) == 2**40
    assert module.id_c_i32(np.int32(123456)) == 123456

    values_i16 = np.array([np.iinfo(np.int16).min, -1, np.iinfo(np.int16).max], dtype=np.int16)
    out_i16 = np.empty_like(values_i16)
    module.copy_i16(np.int32(values_i16.size), values_i16, out_i16)
    np.testing.assert_array_equal(out_i16, values_i16)

    assert bool(module.not_flag(True)) is False
    flags = np.array([True, False, True], dtype=np.bool_)
    inverted = np.empty_like(flags)
    module.invert_flags(np.int32(flags.size), flags, inverted)
    np.testing.assert_array_equal(inverted, np.logical_not(flags))

    assert np.isnan(module.id_r32(np.float32(np.nan)))
    assert np.isposinf(module.id_r64(np.float64(np.inf)))
    assert module.id_c_float(np.float32(1.25)) == np.float32(1.25)
    assert module.id_c_double(np.float64(-2.5)) == np.float64(-2.5)

    values_r64 = np.array([np.finfo(np.float64).min, np.inf, np.nan], dtype=np.float64)
    out_r64 = np.empty_like(values_r64)
    module.copy_r64(np.int32(values_r64.size), values_r64, out_r64)
    np.testing.assert_allclose(out_r64, values_r64, equal_nan=True)

    np.testing.assert_allclose(module.conj_c64(np.complex64(1 + 2j)), np.complex64(1 - 2j))
    np.testing.assert_allclose(module.shift_c128(np.complex128(2 + 3j)), np.complex128(3 + 1j))
    np.testing.assert_allclose(module.conj_c_float_complex(np.complex64(-1 + 4j)), np.complex64(-1 - 4j))
    np.testing.assert_allclose(
        module.conj_c_double_complex(np.complex128(-2 - 5j)),
        np.complex128(-2 + 5j),
    )

    with pytest.raises(TypeError):
        module.id_i32(4)
    with pytest.raises(TypeError):
        module.id_i32(np.int64(4))
    with pytest.raises(TypeError):
        module.id_r64(1.5)

    values_c128 = np.array([1 + 2j, np.inf - 3j, np.nan + 4j], dtype=np.complex128)
    out_c128 = np.empty_like(values_c128)
    module.copy_c128(np.int32(values_c128.size), values_c128, out_c128)
    np.testing.assert_allclose(out_c128, values_c128, equal_nan=True)
