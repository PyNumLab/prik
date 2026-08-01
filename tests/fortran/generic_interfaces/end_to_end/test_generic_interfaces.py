"""Generic procedure interface runtime wrapper tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
OVERLOAD_F90_SOURCE = FIXTURES / "foverloads_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


@pytest.fixture
def compiled_generic_module(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    return _build_source_or_generated_pyi_and_import(
        OVERLOAD_F90_SOURCE,
        tmp_path,
        {
            "bind_c_foverloads_f90_wrapper.f90",
            "foverloads_f90_wrapper.c",
            "foverloads_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "foverloads_f90",
        pyi_parity_build_mode,
    )


def test_fortran_generic_interfaces_dispatch_in_generated_c_extension(
    compiled_generic_module,
):
    module = compiled_generic_module

    assert "Module Attributes" not in module.__doc__
    assert "convert(*args, **kwargs)" in module.__doc__
    assert "_prik_overload_" not in module.__doc__
    assert "convert_integer" not in module.__doc__
    assert "convert(value: int32) -> int32" in module.convert.__doc__
    assert "convert(value: float64) -> float64" in module.convert.__doc__
    assert "convert(value: complex128) -> complex128" in module.convert.__doc__
    assert "convert_integer" not in module.convert.__doc__
    assert "convert_real" not in module.convert.__doc__
    assert "convert_complex" not in module.convert.__doc__

    assert module.convert(np.int32(4)) == np.int32(14)
    assert module.convert(np.float64(4.0)) == np.float64(4.5)
    assert module.convert(np.complex128(2.0 + 3.0j)) == np.complex128(3.0 + 2.0j)
    assert module.summarize(np.float64(2.5)) == np.float64(2.5)
    assert module.summarize(np.array([1.0, 2.0, 3.0], dtype=np.float64)) == np.float64(6.0)

    value = module.accumulator()
    value.add(np.int32(2))
    value.add(np.float64(0.5))
    assert value.total == np.float64(2.5)
    assert module.inspect(value) == np.float64(2.5)

    sample = module.sample()
    sample.value = np.float64(7.25)
    assert module.inspect(sample) == np.float64(7.25)

    with pytest.raises(TypeError):
        module.convert("not numeric")
    with pytest.raises(TypeError):
        value.add(np.complex128(1.0 + 0.0j))
