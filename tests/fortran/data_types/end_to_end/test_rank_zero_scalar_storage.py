"""End-to-end scalar values and rank-zero NumPy storage."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_inline_pyi_contract_module


pytestmark = pytest.mark.fortran_end_to_end


def test_scalar_values_and_rank_zero_storage_cross_the_native_boundary(tmp_path: Path):
    module, _result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="scalar_storage_contract",
        source_text="""
module scalar_storage_contract
  use iso_c_binding, only: c_double, c_int32_t
  integer(c_int32_t) :: counter = 3
  integer(c_int32_t), parameter :: answer = 42
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

  subroutine bump_storage_float(value)
    real(c_double), intent(inout) :: value
    value = value * 2.0_c_double
  end subroutine bump_storage_float

  subroutine make_value(value)
    integer(c_int32_t), intent(out) :: value
    value = 41
  end subroutine make_value

  subroutine make_storage(value)
    integer(c_int32_t), intent(out) :: value
    value = 42
  end subroutine make_storage

  function direct_storage_result() result(value)
    integer(c_int32_t) :: value
    value = 44
  end function direct_storage_result

  subroutine hidden_storage_result(value)
    integer(c_int32_t), intent(out) :: value
    value = 45
  end subroutine hidden_storage_result
end module scalar_storage_contract
""",
        contract_text="""
from prik.contracts import Annotated, Final, Immutable, Int32, Float64, Return, Returns, native_call

counter: Int32
answer: Final[Int32] = 42

def value_input(value: Int32) -> Int32: ...

def bump_value(
    value: Annotated[Int32, Immutable]
) -> Returns["value", Int32]: ...

def bump_storage(value: Int32[()]) -> None: ...

def bump_storage_float(value: Float64[()]) -> None: ...

@native_call([Return("value", 0)])
def make_value() -> Int32: ...

def make_storage(value: Int32[()]) -> None: ...

def direct_storage_result() -> Int32[()]: ...

@native_call([Return("value", 0)])
def hidden_storage_result() -> Int32[()]: ...
""",
    )

    assert module.value_input(np.int32(5)) == np.int32(7)
    assert module.counter == np.int32(3)
    module.counter = np.int32(9)
    assert module.counter == np.int32(9)
    assert module.answer == np.int32(42)

    original = np.int32(4)
    assert module.bump_value(original) == np.int32(5)
    assert original == np.int32(4)

    storage = np.array(6, dtype=np.int32)
    assert module.bump_storage(storage) is None
    assert storage[()] == np.int32(7)

    float_storage = np.array(3.5, dtype=np.float64)
    assert module.bump_storage_float(float_storage) is None
    assert float_storage[()] == np.float64(7.0)

    assert module.make_value() == np.int32(41)
    output_storage = np.empty((), dtype=np.int32)
    assert module.make_storage(output_storage) is None
    assert output_storage[()] == np.int32(42)

    for result, expected in (
        (module.direct_storage_result(), np.int32(44)),
        (module.hidden_storage_result(), np.int32(45)),
    ):
        assert isinstance(result, np.ndarray)
        assert result.shape == ()
        assert result.dtype == np.dtype(np.int32)
        assert result[()] == expected

    with pytest.raises(TypeError):
        module.bump_storage(np.int32(6))
    with pytest.raises(TypeError):
        module.bump_storage(np.array(6, dtype=np.int64))
    read_only = np.array(6, dtype=np.int32)
    read_only.flags.writeable = False
    with pytest.raises(TypeError, match="writeable"):
        module.bump_storage(read_only)
