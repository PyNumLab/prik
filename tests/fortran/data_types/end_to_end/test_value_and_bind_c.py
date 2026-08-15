"""Fortran value and existing bind(C) ABI runtime wrapper tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
    wrapper_source,
)

BIND_VALUE_F90_SOURCE = wrapper_source("fbind_value_f90.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "fixtures" / "baseline" / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_value_and_existing_bind_c_renamed_symbol_use_correct_abi(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        BIND_VALUE_F90_SOURCE,
        tmp_path,
        {
            "fbind_value_f90_wrapper.c",
            "fbind_value_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fbind_value_f90",
        pyi_parity_build_mode,
    )

    assert module.plus_value(np.int32(5)) == np.int32(12)
    assert module.double_value(np.int32(6)) == np.int32(12)
    assert module.plus_reference(np.int32(5)) == np.int32(16)
    assert module.scale_real(np.float64(4.0)) == np.float64(10.0)
    assert module.conjugate_value(np.complex128(2.0 + 3.0j)) == np.complex128(2.0 - 3.0j)
    assert bool(module.invert_flag(True)) is False
    assert module.char_code("A") == np.int32(65)

    if pyi_parity_build_mode == "source":
        binding_source = (tmp_path / "source_build" / "fbind_value_f90_wrapper.c").read_text(encoding="utf-8")
        for native_name in (
            "prik_plus_value",
            "double_value",
            "plus_reference",
            "prik_scale_real",
            "prik_conjugate_value",
            "prik_invert_flag",
            "char_code",
        ):
            assert f"{native_name}(" in binding_source
