"""Assumed-rank array dispatch and supported-rank boundary tests."""

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _build_source_or_generated_pyi_and_import,
)
from x2py.runtime.handles import _NativeArrayHandoff, AllocatableArray, PointerArray

FIXTURES = Path(__file__).parent / "fixtures"
ASSUMED_RANK_F90_SOURCE = FIXTURES / "fassumed_rank_f90.f90"
CONTRACT_FIXTURES = FIXTURES / "contracts"
_MAX_WRAPPER_TEST_RANK = 15

pytestmark = pytest.mark.fortran_end_to_end


@pytest.fixture(scope="module", params=("source", "generated-pyi"))
def assumed_rank_module(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory):
    return _build_source_or_generated_pyi_and_import(
        ASSUMED_RANK_F90_SOURCE,
        tmp_path_factory.mktemp(f"assumed-rank-{request.param}"),
        {
            "bind_c_fassumed_rank_f90_wrapper.f90",
            "fassumed_rank_f90_wrapper.c",
            "fassumed_rank_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "fassumed_rank_f90",
        request.param,
    )


def _allocated_handle_for_rejected_assumed_rank(value):
    return AllocatableArray(
        dtype=value.dtype,
        rank=value.ndim,
        ops={
            "array_actual": lambda _handle: pytest.fail("assumed-rank path must reject handles before handoff"),
            "descriptor": lambda _handle: _NativeArrayHandoff(401),
            "shape": lambda _handle: value.shape,
            "layout": lambda _handle: "F" if value.flags.f_contiguous else "C",
            "writeable": lambda _handle: value.flags.writeable,
            "native_byte_order": lambda _handle: value.dtype.isnative,
            "aligned": lambda _handle: value.flags.aligned,
            "to_numpy": lambda _handle: value,
            "allocated": lambda _handle: True,
            "deallocate": lambda _handle: None,
            "resize": lambda _handle, _shape: None,
        },
    )


def _unassociated_handle_for_rejected_assumed_rank():
    return PointerArray(
        dtype=np.dtype(np.float64),
        rank=1,
        ops={
            "array_actual": lambda _handle: pytest.fail("assumed-rank path must reject handles before handoff"),
            "descriptor": lambda _handle: _NativeArrayHandoff(402),
            "shape": lambda _handle: None,
            "to_numpy": lambda _handle: None,
            "associated": lambda _handle: False,
            "nullify": lambda _handle: None,
        },
    )


def test_assumed_rank_arguments_dispatch_to_runtime_rank(
    assumed_rank_module,
):
    module = assumed_rank_module

    assert "Rank: 1..15" in module.rank_weighted_sum.__doc__
    assert "Rank: 1..15" in module.bump_assumed_rank.__doc__

    for rank in range(1, _MAX_WRAPPER_TEST_RANK + 1):
        shape = (2, *([1] * (rank - 1)))
        values = np.asfortranarray(np.arange(np.prod(shape), dtype=np.float64).reshape(shape, order="F"))
        expected_sum = np.float64(rank + values.sum())

        assert module.rank_weighted_sum(values) == expected_sum
        assert module.bump_assumed_rank(values) is None
        np.testing.assert_allclose(values, np.arange(np.prod(shape), dtype=np.float64).reshape(shape, order="F") + rank)

    with pytest.raises(TypeError):
        module.rank_weighted_sum(np.float64(1.0))

    rank16 = np.empty((1,) * (_MAX_WRAPPER_TEST_RANK + 1), dtype=np.float64, order="F")
    with pytest.raises(TypeError):
        module.rank_weighted_sum(rank16)

    handle_values = np.asfortranarray(np.array([1.0, 2.0], dtype=np.float64))
    with pytest.raises(TypeError):
        module.rank_weighted_sum(_allocated_handle_for_rejected_assumed_rank(handle_values))
    with pytest.raises(TypeError):
        module.rank_weighted_sum(_unassociated_handle_for_rejected_assumed_rank())


def test_assumed_rank_bridge_dispatches_each_runtime_rank_argument(
    assumed_rank_module,
):
    module = assumed_rank_module

    for left_rank in range(1, _MAX_WRAPPER_TEST_RANK + 1):
        right_rank = _MAX_WRAPPER_TEST_RANK + 1 - left_rank
        left_shape = (2, *([1] * (left_rank - 1)))
        right_shape = (2, *([1] * (right_rank - 1)))
        left = np.ones(left_shape, dtype=np.float64, order="F")
        right = np.ones(right_shape, dtype=np.float64, order="F")

        assert module.rank_pair_score(left, right) == 100 * left_rank + right_rank + 4
