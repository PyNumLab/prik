"""Array shape, rank, mutability, dtype, alignment, and byte-order tests."""

from pathlib import Path

import numpy as np
import pytest
from numpy.lib.stride_tricks import as_strided

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)

FIXTURES = Path(__file__).parent / "fixtures"
ARRAY_CONTRACTS_F90_SOURCE = FIXTURES / "native" / "farray_contracts_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
_MAX_WRAPPER_TEST_RANK = 15

pytestmark = pytest.mark.fortran_end_to_end


def test_remaining_array_contracts_are_validated_before_fortran_calls(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        ARRAY_CONTRACTS_F90_SOURCE,
        tmp_path,
        {
            "bind_c_farray_contracts_f90_wrapper.f90",
            "farray_contracts_f90_wrapper.c",
            "farray_contracts_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "farray_contracts_f90",
        pyi_parity_build_mode,
    )

    readonly = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
    readonly.setflags(write=False)
    if pyi_parity_build_mode == "source":
        assert module.sum_assumed_size(np.int32(4), readonly) == np.float64(10.0)
        assert module.sum_in(readonly) == np.float64(10.0)
    else:
        with pytest.raises(TypeError, match="writeable"):
            module.sum_assumed_size(np.int32(4), readonly)
        with pytest.raises(TypeError, match="writeable"):
            module.sum_in(readonly)

    fortran_storage = np.asfortranarray(np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]], dtype=np.float64))
    c_storage = np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]], dtype=np.float64, order="C")
    assert module.sum_assumed_size(np.int32(fortran_storage.size), fortran_storage) == np.float64(66.0)
    assert module.sum_assumed_size(np.int32(c_storage.size), c_storage) == np.float64(66.0)
    assert module.sum_assumed_size(np.int32(3), fortran_storage) == np.float64(13.0)
    assert module.sum_assumed_size(np.int32(3), c_storage) == np.float64(6.0)

    noncontiguous_flat = fortran_storage[:, ::2]
    with pytest.raises(TypeError, match="contiguous"):
        module.sum_assumed_size(np.int32(noncontiguous_flat.size), noncontiguous_flat)

    lower_bound_values = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
    assert module.scale_lower(np.int32(4), lower_bound_values) is None
    np.testing.assert_allclose(lower_bound_values, np.array([2.0, 4.0, 6.0, 8.0], dtype=np.float64))
    with pytest.raises(TypeError, match="incompatible shape at axis 0"):
        module.scale_lower(np.int32(4), np.ones(3, dtype=np.float64))

    with pytest.raises(TypeError, match="writeable"):
        module.bump_inout(readonly)
    readonly_out = np.empty(4, dtype=np.float64)
    readonly_out.setflags(write=False)
    with pytest.raises(TypeError, match="writeable"):
        module.fill_out(readonly_out)

    swapped_dtype = np.dtype(np.float64).newbyteorder("S")
    swapped = np.array([1.0, 2.0], dtype=swapped_dtype)
    with pytest.raises(TypeError, match="native byte order"):
        module.sum_in(swapped)

    storage = np.zeros(8 * 4 + 1, dtype=np.uint8)
    misaligned = storage[1:].view(np.float64)
    assert not misaligned.flags.aligned
    with pytest.raises(TypeError, match="aligned"):
        module.sum_in(misaligned)

    with pytest.raises(TypeError, match="dtype"):
        module.sum_in(np.array([1.0, 2.0], dtype=np.float32))

    empty_rank4 = np.empty((0, 1, 1, 1), dtype=np.float64, order="F")
    empty_rank4_out = np.empty_like(empty_rank4, order="F")
    assert module.shift4(empty_rank4, empty_rank4_out) is None
    assert empty_rank4_out.shape == empty_rank4.shape

    zero_stride_empty = as_strided(
        np.empty(1, dtype=np.float64),
        shape=empty_rank4.shape,
        strides=(0, 0, 0, 0),
    )
    zero_stride_empty_out = as_strided(
        np.empty(1, dtype=np.float64),
        shape=empty_rank4.shape,
        strides=(0, 0, 0, 0),
    )
    assert zero_stride_empty.flags.f_contiguous
    assert zero_stride_empty_out.flags.f_contiguous
    assert module.shift4(zero_stride_empty, zero_stride_empty_out) is None

    for rank in range(1, _MAX_WRAPPER_TEST_RANK + 1):
        shape = (2, *([1] * (rank - 1)))
        source = np.asfortranarray(np.arange(np.prod(shape), dtype=np.float64).reshape(shape, order="F"))
        out = np.empty(shape, dtype=np.float64, order="F")

        assert getattr(module, f"shift{rank}")(source, out) is None
        np.testing.assert_allclose(out, source + rank)
