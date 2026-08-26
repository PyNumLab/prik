"""Fortran enum runtime behavior from source and generated contracts."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_or_generated_pyi_and_import

FIXTURES = Path(__file__).parent / "fixtures"
ENUM_SOURCE = FIXTURES / "native" / "fenums_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_fortran_enums_preserve_integer_runtime_surface(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        ENUM_SOURCE,
        tmp_path,
        {
            "bind_c_fenums_f90_wrapper.f90",
            "fenums_f90_wrapper.c",
            "fenums_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fenums_f90",
        pyi_parity_build_mode,
    )

    assert module.red == np.int32(-1)
    assert module.blue == np.int32(0)
    assert module.green == np.int32(10)
    assert module.yellow == np.int32(11)
    assert module.round_trip_color(np.int32(module.green)) == np.int32(10)
    assert module.round_trip_color(np.int32(123)) == np.int32(123)
    assert all(isinstance(value, np.int32) for value in (module.red, module.blue, module.green, module.yellow))
    assert not hasattr(module, "Enum")
    assert not hasattr(module, "IntEnum")

    sample = module.paint()
    assert sample.color == np.int32(-1)
    sample.color = np.int32(module.yellow)
    assert sample.color == np.int32(11)
