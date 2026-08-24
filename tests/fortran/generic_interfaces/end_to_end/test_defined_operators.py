"""Defined operator and assignment runtime wrapper tests."""

import gc
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
OPERATOR_F90_SOURCE = FIXTURES / "native" / "foperators_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
pytestmark = pytest.mark.fortran_end_to_end


def test_fortran_defined_operators_and_assignment_dispatch_in_generated_c_extension(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        OPERATOR_F90_SOURCE,
        tmp_path,
        {
            "bind_c_foperators_f90_wrapper.f90",
            "foperators_f90_wrapper.c",
            "foperators_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "foperators_f90",
        pyi_parity_build_mode,
    )

    def vector(value):
        result = module.vector()
        result.value = np.float64(value)
        return result

    def offset(value):
        result = module.offset()
        result.value = np.float64(value)
        return result

    left = vector(5.0)
    right = vector(2.0)

    assert "__add__(*args, **kwargs)" in module.vector.__doc__
    assert "__add__(right: vector) -> vector" in module.vector.__add__.__doc__
    assert "add_vectors" not in module.vector.__add__.__doc__

    assert module.convert(np.int32(2)) == np.int32(12)
    assert module.convert(np.float64(2.0)) == np.float64(2.5)
    assert (left + right).value == np.float64(7.0)
    assert (left + np.int32(3)).value == np.float64(8.0)
    assert (left + np.float64(0.5)).value == np.float64(5.5)
    assert (np.float64(1.5) + left).value == np.float64(106.5)
    assert (left + np.array([1.0, 2.0], dtype=np.float64)).value == np.float64(8.0)
    assert (left + offset(4.0)).value == np.float64(9.0)
    temporary_result = vector(1.0) + vector(2.0)
    gc.collect()
    assert temporary_result.value == np.float64(3.0)
    assert (+left).value == np.float64(5.0)
    assert (left - np.float64(1.5)).value == np.float64(3.5)
    assert (np.float64(9.0) - left).value == np.float64(4.0)
    assert (-left).value == np.float64(-5.0)
    assert (left * np.float64(2.0)).value == np.float64(10.0)
    assert (left / np.float64(2.0)).value == np.float64(2.5)
    assert (left ** np.int32(2)).value == np.float64(25.0)
    with pytest.raises(TypeError, match="modulus is not supported"):
        pow(left, np.int32(2), np.int32(3))

    assert left == vector(5.0)
    assert left != right
    assert right < left
    assert left < np.float64(6.0)
    assert np.float64(1.0) < left
    assert right <= left
    assert left > right
    assert left >= right
    assert bool(left & right) is True
    assert bool(vector(0.0) | right) is True
    assert bool(~vector(0.0)) is True
    assert left == offset(1.0)
    assert left != np.int32(0)
    assert left.operator_dot(right) == np.float64(10.0)
    assert left.r_operator_shift(np.float64(2.0)).value == np.float64(207.0)

    assigned = vector(1.0)
    assigned_identity = id(assigned)
    assert assigned.assign(np.int32(7)) is assigned
    assert id(assigned) == assigned_identity
    assert assigned.value == np.float64(7.0)
    assert assigned.assign(np.float64(3.5)) is assigned
    assert assigned.value == np.float64(3.5)
    assert assigned.assign(assigned) is assigned
    assert assigned.value == np.float64(3.5)

    counter = module.counter()
    counter.value = np.int32(4)
    assert (counter + np.int32(3)).value == np.int32(7)

    with pytest.raises(TypeError):
        left + np.complex128(1.0 + 0.0j)
    with pytest.raises(TypeError):
        assigned.assign(np.complex128(1.0 + 0.0j))
