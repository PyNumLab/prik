"""Runtime constructors for concrete primitive semantic contracts."""

import numpy as np
import pytest

import x2py.contracts as contracts


def test_concrete_primitive_default_constructors_return_zero_numpy_scalars():
    cases = (
        (contracts.Bool, np.bool_),
        (contracts.Int8, np.int8),
        (contracts.Int16, np.int16),
        (contracts.Int32, np.int32),
        (contracts.Int64, np.int64),
        (contracts.UInt8, np.uint8),
        (contracts.UInt16, np.uint16),
        (contracts.UInt32, np.uint32),
        (contracts.UInt64, np.uint64),
        (contracts.Float16, np.float16),
        (contracts.Float32, np.float32),
        (contracts.Float64, np.float64),
        (contracts.Float128, np.longdouble),
        (contracts.Complex64, np.complex64),
        (contracts.Complex128, np.complex128),
        (contracts.Complex256, np.clongdouble),
        (contracts.SizeT, np.uintp),
    )

    for contract, scalar_type in cases:
        value = contract()
        assert isinstance(value, scalar_type), contract
        assert value == scalar_type(0), contract


def test_primitive_contract_constructors_reject_values_and_array_annotations():
    with pytest.raises(TypeError, match="ordinary array contract annotations"):
        contracts.Float64[:]()
    with pytest.raises(TypeError, match="default constructor takes no arguments"):
        contracts.Int32(3)
