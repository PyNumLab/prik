"""Array-valued function result runtime wrapper tests."""

import gc
import shutil
from pathlib import Path

import numpy as np
import pytest

from tests.wrapper.fortran._support import (
    _build_source_or_generated_pyi_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _require_maybe_unallocated_function_result_support,
    _sole_native_module,
    wrapper_source,
)
from x2py import build_pyi_extension
from x2py.runtime.handles import AllocatableArray

ARRAY_RESULTS_F90_SOURCE = wrapper_source("farray_results_f90.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "contracts"
_MAX_WRAPPER_TEST_RANK = 15


def test_array_results_follow_data_buffer_and_descriptor_handle_contracts(
    pyi_parity_build_mode: str,
    tmp_path: Path,
):
    module = _build_source_or_generated_pyi_and_import(
        ARRAY_RESULTS_F90_SOURCE,
        tmp_path,
        {
            "bind_c_farray_results_f90_wrapper.f90",
            "farray_results_f90_wrapper.c",
            "farray_results_f90_wrapper.h",
        },
        CONTRACT_FIXTURES / "farray_results_f90",
        pyi_parity_build_mode,
    )

    fixed = module.fixed_vector()
    np.testing.assert_allclose(fixed, np.array([1.0, 2.0, 3.0], dtype=np.float64))
    assert fixed.base is not None

    automatic = module.automatic_vector(np.int32(4))
    np.testing.assert_allclose(automatic, np.array([2.0, 4.0, 6.0, 8.0], dtype=np.float64))
    assert automatic.base is not None

    matrix = module.automatic_matrix(np.int32(2), np.int32(3))
    np.testing.assert_allclose(
        matrix,
        np.array([[12.0, 13.0, 14.0], [22.0, 23.0, 24.0]], dtype=np.float64),
    )
    assert matrix.flags.f_contiguous
    assert matrix.base is not None

    cube = module.rank3_cube(np.int32(2), np.int32(2), np.int32(2))
    expected_cube = np.empty((2, 2, 2), dtype=np.float64, order="F")
    for i, j, k in np.ndindex(expected_cube.shape):
        expected_cube[i, j, k] = 100.0 * (i + 1) + 10.0 * (j + 1) + (k + 1)
    np.testing.assert_allclose(cube, expected_cube)
    assert cube.flags.f_contiguous

    rank_results = []
    for rank in range(1, _MAX_WRAPPER_TEST_RANK + 1):
        result = getattr(module, f"rank{rank}_result")()
        shape = (2, *([1] * (rank - 1)))
        expected = np.full(shape, float(rank), dtype=np.float64, order="F")
        expected[(1, *([0] * (rank - 1)))] = float(rank) + 0.5

        assert result.shape == shape
        assert result.flags.f_contiguous
        assert result.base is not None
        np.testing.assert_allclose(result, expected)
        rank_results.append((result, expected))

    zero = module.zero_vector()
    assert zero.shape == (0,)
    assert zero.dtype == np.dtype(np.float64)
    assert zero.base is not None

    zero_alloc = module.zero_alloc_vector()
    assert isinstance(zero_alloc, AllocatableArray)
    assert zero_alloc.allocated is True
    assert zero_alloc.shape == (0,)
    assert zero_alloc.to_numpy().shape == (0,)

    allocated = module.maybe_alloc_vector(np.int32(3))
    assert isinstance(allocated, AllocatableArray)
    np.testing.assert_allclose(allocated.to_numpy(), np.array([5.0, 10.0, 15.0], dtype=np.float64))

    allocated_matrix = module.maybe_alloc_matrix(np.int32(2), np.int32(3))
    assert isinstance(allocated_matrix, AllocatableArray)
    assert allocated_matrix.allocated is True
    np.testing.assert_allclose(
        allocated_matrix.to_numpy(),
        np.array([[110.0, 120.0, 130.0], [210.0, 220.0, 230.0]], dtype=np.float64),
    )

    zero_alloc_matrix = module.zero_alloc_matrix(np.int32(2))
    assert isinstance(zero_alloc_matrix, AllocatableArray)
    assert zero_alloc_matrix.allocated is True
    assert zero_alloc_matrix.shape == (0, 2)
    assert zero_alloc_matrix.to_numpy().shape == (0, 2)

    del module
    gc.collect()
    np.testing.assert_allclose(matrix, np.array([[12.0, 13.0, 14.0], [22.0, 23.0, 24.0]], dtype=np.float64))
    np.testing.assert_allclose(cube, expected_cube)
    for result, expected in rank_results:
        np.testing.assert_allclose(result, expected)


def test_ordinary_array_results_use_canonical_plan(tmp_path: Path, monkeypatch):
    """Replay fixed-shape direct results without descriptor-backed neighbors."""
    native_object = _compile_native_object(ARRAY_RESULTS_F90_SOURCE, tmp_path / "native")
    selected = (
        "fixed_vector",
        "automatic_vector",
        "automatic_matrix",
        "rank3_cube",
        "rank15_result",
        "zero_vector",
    )
    contract_package = tmp_path / "ordinary_array_results"
    shutil.copytree(CONTRACT_FIXTURES / "farray_results_f90", contract_package)
    (contract_package / "__init__.pyi").write_text(
        "".join(f"from .farray_results_f90 import {name}\n" for name in selected),
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract_package / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    imported = _import_from_build_dir(result.module_name, result.output_dir)
    module = imported if hasattr(imported, "fixed_vector") else _sole_native_module(imported)

    np.testing.assert_array_equal(module.fixed_vector(), np.array([1.0, 2.0, 3.0]))
    np.testing.assert_array_equal(module.automatic_vector(np.int32(3)), np.array([2.0, 4.0, 6.0]))
    matrix = module.automatic_matrix(np.int32(2), np.int32(3))
    np.testing.assert_array_equal(matrix, np.array([[12.0, 13.0, 14.0], [22.0, 23.0, 24.0]]))
    assert matrix.flags.f_contiguous
    assert module.rank3_cube(np.int32(0), np.int32(2), np.int32(3)).shape == (0, 2, 3)
    assert module.rank15_result().shape == (2, *([1] * 14))
    assert module.zero_vector().shape == (0,)

    monkeypatch.setenv("X2PY_WRAPPER_FAIL_ALLOC", "1")
    with pytest.raises(MemoryError, match="Unable to allocate copy-return output array"):
        module.fixed_vector()


def test_owned_allocatable_results_preserve_handle_state(tmp_path: Path):
    """Replay valid allocated and zero-sized allocatable function results."""
    native_object = _compile_native_object(ARRAY_RESULTS_F90_SOURCE, tmp_path / "native")
    contract_package = tmp_path / "allocatable_results"
    shutil.copytree(CONTRACT_FIXTURES / "farray_results_f90", contract_package)
    (contract_package / "__init__.pyi").write_text(
        "from .farray_results_f90 import maybe_alloc_matrix, maybe_alloc_vector, zero_alloc_matrix, zero_alloc_vector\n",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract_package / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    imported = _import_from_build_dir(result.module_name, result.output_dir)
    module = imported if hasattr(imported, "maybe_alloc_vector") else _sole_native_module(imported)

    allocated = module.maybe_alloc_vector(np.int32(3))
    assert isinstance(allocated, AllocatableArray)
    assert allocated.allocated is True
    np.testing.assert_allclose(allocated.to_numpy(), np.array([5.0, 10.0, 15.0]))

    zero_sized = module.zero_alloc_vector()
    assert isinstance(zero_sized, AllocatableArray)
    assert zero_sized.allocated is True
    assert zero_sized.shape == (0,)
    assert zero_sized.to_numpy().shape == (0,)

    allocated_matrix = module.maybe_alloc_matrix(np.int32(2), np.int32(3))
    assert isinstance(allocated_matrix, AllocatableArray)
    assert allocated_matrix.allocated is True
    np.testing.assert_allclose(
        allocated_matrix.to_numpy(),
        np.array([[110.0, 120.0, 130.0], [210.0, 220.0, 230.0]]),
    )

    zero_sized_matrix = module.zero_alloc_matrix(np.int32(2))
    assert isinstance(zero_sized_matrix, AllocatableArray)
    assert zero_sized_matrix.allocated is True
    assert zero_sized_matrix.shape == (0, 2)
    assert zero_sized_matrix.to_numpy().shape == (0, 2)

    allocated.close()
    zero_sized.close()
    allocated_matrix.close()
    zero_sized_matrix.close()


def test_maybe_unallocated_allocatable_result_preserves_absent_state(tmp_path: Path):
    """Use an edited contract for direct allocatable results that may be unallocated."""
    _require_maybe_unallocated_function_result_support()
    native_object = _compile_native_object(ARRAY_RESULTS_F90_SOURCE, tmp_path / "native")
    contract_package = tmp_path / "maybe_unallocated_results"
    shutil.copytree(CONTRACT_FIXTURES / "farray_results_f90", contract_package)
    pyi_path = contract_package / "farray_results_f90.pyi"
    contract_text = pyi_path.read_text(encoding="utf-8")
    contract_text = contract_text.replace(
        "Addr, Allocatable, Arg, Float64, Int32, native_call",
        "Addr, Allocatable, Annotated, Arg, Float64, Int32, MaybeUnallocated, native_call",
        1,
    )
    contract_text = contract_text.replace(
        "def maybe_alloc_vector(\n    n: Int32\n) -> Allocatable[Float64[:]]: ...",
        "def maybe_alloc_vector(\n    n: Int32\n) -> Annotated[Allocatable[Float64[:]], MaybeUnallocated]: ...",
        1,
    )
    contract_text = contract_text.replace(
        "def maybe_alloc_matrix(\n    rows: Int32,\n    cols: Int32\n) -> Allocatable[Float64[:, :]]: ...",
        "def maybe_alloc_matrix(\n"
        "    rows: Int32,\n"
        "    cols: Int32\n"
        ") -> Annotated[Allocatable[Float64[:, :]], MaybeUnallocated]: ...",
        1,
    )
    pyi_path.write_text(contract_text, encoding="utf-8")
    (contract_package / "__init__.pyi").write_text(
        "from .farray_results_f90 import maybe_alloc_matrix, maybe_alloc_vector\n",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract_package / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    imported = _import_from_build_dir(result.module_name, result.output_dir)
    module = imported if hasattr(imported, "maybe_alloc_vector") else _sole_native_module(imported)

    allocated_vector = module.maybe_alloc_vector(np.int32(3))
    assert isinstance(allocated_vector, AllocatableArray)
    assert allocated_vector.allocated is True
    np.testing.assert_allclose(allocated_vector.to_numpy(), np.array([5.0, 10.0, 15.0]))

    unallocated_matrix = module.maybe_alloc_matrix(np.int32(0), np.int32(3))
    assert isinstance(unallocated_matrix, AllocatableArray)
    assert unallocated_matrix.allocated is False
    assert unallocated_matrix.shape is None
    assert unallocated_matrix.to_numpy() is None

    allocated_vector.close()
    unallocated_matrix.close()
