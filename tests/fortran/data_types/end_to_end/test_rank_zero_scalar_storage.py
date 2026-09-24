"""End-to-end scalar values and rank-zero NumPy storage."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_inline_pyi_contract_module


pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


def test_scalar_values_and_rank_zero_storage_cross_the_native_boundary(tmp_path: Path):
    module, _result = _build_inline_pyi_contract_module(
        tmp_path,
        module_name="scalar_storage_contract",
        source_text=(NATIVE_FIXTURES / "scalar_storage_contract.f90").read_text(encoding="utf-8"),
        contract_text="""
from prik.contracts import Annotated, Final, Immutable, Int32, Float64, Return, Returns, native_call

counter: Int32[()]
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
    assert module.value_input(np.array(5, dtype=np.int32)) == np.int32(7)
    with pytest.raises(TypeError):
        module.value_input(np.array(5, dtype=np.int64))
    native_counter = module.counter
    assert native_counter.shape == ()
    assert native_counter[()] == np.int32(3)
    assert module.bump_value(native_counter) == np.int32(4)
    assert module.counter[()] == np.int32(4)
    module.counter = np.int32(9)
    assert native_counter[()] == np.int32(9)
    assert module.answer == np.int32(42)

    original = np.int32(4)
    assert module.bump_value(original) == np.int32(5)
    assert original == np.int32(4)
    borrowed = np.array(4, dtype=np.int32)
    assert module.bump_value(borrowed) == np.int32(5)
    assert borrowed[()] == np.int32(5)
    borrowed.flags.writeable = False
    with pytest.raises(TypeError, match="writeable"):
        module.bump_value(borrowed)

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
