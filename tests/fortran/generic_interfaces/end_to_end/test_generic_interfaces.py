"""Generic procedure interface runtime wrapper tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
    _build_sources_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
OVERLOAD_F90_SOURCE = FIXTURES / "foverloads_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end

PRIVATE_INLINE_GENERIC_MODULE = """\
module private_inline_generic
  implicit none
  private
  public :: shift

  interface shift
    module function shift_integer(value) result(output)
      integer, intent(in) :: value
      integer :: output
    end function shift_integer
    module function shift_real(value) result(output)
      real(8), intent(in) :: value
      real(8) :: output
    end function shift_real
  end interface shift
end module private_inline_generic
"""

PRIVATE_INLINE_GENERIC_SUBMODULE = """\
submodule(private_inline_generic) private_inline_generic_impl
contains
  module procedure shift_integer
    output = value + 1
  end procedure shift_integer

  module procedure shift_real
    output = value + 0.5_8
  end procedure shift_real
end submodule private_inline_generic_impl
"""


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


def test_public_generic_dispatches_to_private_inline_submodule_specifics(tmp_path: Path):
    module, _payload = _build_sources_and_import(
        [
            ("private_inline_generic.f90", PRIVATE_INLINE_GENERIC_MODULE),
            ("private_inline_generic_impl.f90", PRIVATE_INLINE_GENERIC_SUBMODULE),
        ],
        tmp_path,
    )

    assert module.private_inline_generic.shift(np.int32(4)) == np.int32(5)
    assert module.private_inline_generic.shift(np.float64(4.0)) == np.float64(4.5)
    bridge = (tmp_path / "bind_c_private_inline_generic_wrapper.f90").read_text(encoding="utf-8").lower()
    assert "native__prik_overload_shift_0 => shift" in bridge
    assert "native__prik_overload_shift_1 => shift" in bridge
    assert "=> shift_integer" not in bridge
    assert "=> shift_real" not in bridge
