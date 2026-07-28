from pathlib import Path
import shutil

import numpy as np
import pytest

from x2py import build_pyi_extension
from tests.wrapper.fortran._support import (
    _build_source_or_generated_pyi_and_import,
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
    wrapper_source,
)


SOURCE = wrapper_source("multid_arrays.f90")
CONTRACT_FIXTURES = Path(__file__).parent / "contracts"
EXPECTED_GENERATED_SOURCES = {
    "bind_c_multid_arrays_wrapper.f90",
    "multid_arrays_wrapper.c",
    "multid_arrays_wrapper.h",
}


@pytest.fixture
def module(pyi_parity_build_mode: str, tmp_path: Path):
    return _build_source_or_generated_pyi_and_import(
        SOURCE,
        tmp_path,
        EXPECTED_GENERATED_SOURCES,
        CONTRACT_FIXTURES / "multid_arrays",
        pyi_parity_build_mode,
    )


def _matrix(rows=4, cols=3):
    data = np.arange(1, rows * cols + 1, dtype=np.float64)
    return np.asfortranarray(data.reshape((rows, cols), order="F"))


def _strided_matrix(rows=4, cols=3):
    base = _matrix(rows * 2, cols)
    return base[::2, :]


def _strided_matrix_output(shape):
    base = np.zeros((shape[0] * 2, shape[1]), dtype=np.float64, order="F")
    return base[::2, :]


def _checksum2(array):
    total = 0.0
    for i, j in np.ndindex(array.shape):
        total += array[i, j] * (1000.0 * (i + 1) + 10.0 * (j + 1))
    return total


def _c_ordered_strided_matrix(rows=4, cols=3):
    data = np.arange(1, rows * cols * 2 + 1, dtype=np.float64)
    base = np.array(data.reshape((rows, cols * 2), order="C"), order="C")
    return base[:, ::2]


def _reversed_fortran_matrix(rows=4, cols=3):
    base = _matrix(rows * 2, cols)
    return base[::-2, :]


def _broadcast_fortran_like_matrix(rows=4, cols=3):
    row = np.asfortranarray(np.arange(1, cols + 1, dtype=np.float64)[None, :])
    return np.broadcast_to(row, (rows, cols))


def _rank3(shape=(4, 3, 2)):
    data = np.arange(1, np.prod(shape) + 1, dtype=np.float64)
    return np.asfortranarray(data.reshape(shape, order="F"))


def _strided_rank3(shape=(4, 3, 2)):
    base = _rank3((shape[0] * 2, shape[1], shape[2]))
    return base[::2, :, :]


def _strided_rank3_output(shape):
    base = np.zeros((shape[0] * 2, shape[1], shape[2]), dtype=np.float64, order="F")
    return base[::2, :, :]


def _checksum3(array):
    total = 0.0
    for i, j, k in np.ndindex(array.shape):
        total += array[i, j, k] * (10000.0 * (i + 1) + 100.0 * (j + 1) + (k + 1))
    return total


def _c_ordered_strided_rank3(shape=(4, 3, 2)):
    base_shape = (shape[0], shape[1], shape[2] * 2)
    data = np.arange(1, np.prod(base_shape) + 1, dtype=np.float64)
    base = np.array(data.reshape(base_shape, order="C"), order="C")
    return base[:, :, ::2]


def test_rank2_contiguous_contract_requires_fortran_contiguous(module):
    source = _matrix()
    out = np.zeros_like(source, order="F")

    module.scale2_contiguous(source, out)

    np.testing.assert_allclose(out, 2.0 * source)

    c_order_source = np.array(source, order="C", copy=True)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_contiguous(c_order_source, out)

    c_order_out = np.zeros_like(source, order="C")
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_contiguous(source, c_order_out)

    strided_source = _strided_matrix()
    strided_out = np.zeros_like(strided_source, order="F")
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_contiguous(strided_source, strided_out)


def test_rank2_assumed_shape_accepts_fortran_ordered_strided_views(module):
    contiguous_source = _matrix()
    contiguous_out = np.zeros_like(contiguous_source, order="F")

    module.scale2_strided(contiguous_source, contiguous_out)

    np.testing.assert_allclose(contiguous_out, 3.0 * contiguous_source)

    contiguous_checksum = np.zeros(1, dtype=np.float64)
    module.checksum2_strided(contiguous_source, contiguous_checksum)
    np.testing.assert_allclose(contiguous_checksum[0], _checksum2(contiguous_source))

    strided_source = _strided_matrix()
    strided_out = _strided_matrix_output(strided_source.shape)

    module.scale2_strided(strided_source, strided_out)

    np.testing.assert_allclose(strided_out, 3.0 * strided_source)

    strided_checksum = np.zeros(1, dtype=np.float64)
    module.checksum2_strided(strided_source, strided_checksum)
    np.testing.assert_allclose(strided_checksum[0], _checksum2(strided_source))

    c_order_source = np.array(contiguous_source, order="C", copy=True)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_strided(c_order_source, contiguous_out)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.checksum2_strided(c_order_source, contiguous_checksum)

    c_ordered_strided_source = _c_ordered_strided_matrix()
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_strided(c_ordered_strided_source, contiguous_out)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.checksum2_strided(c_ordered_strided_source, contiguous_checksum)

    c_order_out = np.zeros_like(contiguous_source, order="C")
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_strided(contiguous_source, c_order_out)


def test_rank2_assumed_shape_rejects_non_positive_strides(module):
    source = _matrix()
    out = np.zeros_like(source, order="F")
    checksum = np.zeros(1, dtype=np.float64)

    reversed_source = _reversed_fortran_matrix()
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_strided(reversed_source, out)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.checksum2_strided(reversed_source, checksum)

    broadcast_source = _broadcast_fortran_like_matrix()
    assert broadcast_source.strides[0] == 0
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_strided(broadcast_source, out)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.checksum2_strided(broadcast_source, checksum)

    reversed_out = _reversed_fortran_matrix()
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_strided(source, reversed_out)


def test_rank2_explicit_shape_requires_fortran_contiguous(module):
    source = _matrix()
    rows, cols = source.shape
    out = np.zeros_like(source, order="F")

    module.scale2_explicit(np.int32(rows), np.int32(cols), source, out)

    np.testing.assert_allclose(out, 4.0 * source)

    c_order_source = np.array(source, order="C", copy=True)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_explicit(np.int32(rows), np.int32(cols), c_order_source, out)

    strided_source = _strided_matrix(rows, cols)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.scale2_explicit(np.int32(rows), np.int32(cols), strided_source, out)


def test_rank3_contiguous_contract_requires_fortran_contiguous(module):
    source = _rank3()
    out = np.zeros_like(source, order="F")

    module.shift3_contiguous(source, out)

    np.testing.assert_allclose(out, source + 10.0)

    c_order_source = np.array(source, order="C", copy=True)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.shift3_contiguous(c_order_source, out)

    strided_source = _strided_rank3()
    strided_out = np.zeros_like(strided_source, order="F")
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.shift3_contiguous(strided_source, strided_out)


def test_rank3_assumed_shape_accepts_fortran_ordered_strided_views(module):
    contiguous_source = _rank3()
    contiguous_out = np.zeros_like(contiguous_source, order="F")

    module.shift3_strided(contiguous_source, contiguous_out)

    np.testing.assert_allclose(contiguous_out, contiguous_source + 20.0)

    contiguous_checksum = np.zeros(1, dtype=np.float64)
    module.checksum3_strided(contiguous_source, contiguous_checksum)
    np.testing.assert_allclose(contiguous_checksum[0], _checksum3(contiguous_source))

    strided_source = _strided_rank3()
    strided_out = _strided_rank3_output(strided_source.shape)

    module.shift3_strided(strided_source, strided_out)

    np.testing.assert_allclose(strided_out, strided_source + 20.0)

    strided_checksum = np.zeros(1, dtype=np.float64)
    module.checksum3_strided(strided_source, strided_checksum)
    np.testing.assert_allclose(strided_checksum[0], _checksum3(strided_source))

    c_order_source = np.array(contiguous_source, order="C", copy=True)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.shift3_strided(c_order_source, contiguous_out)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.checksum3_strided(c_order_source, contiguous_checksum)

    c_ordered_strided_source = _c_ordered_strided_rank3()
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.shift3_strided(c_ordered_strided_source, contiguous_out)
    with pytest.raises(TypeError, match=r"expected ordering \(F\)"):
        module.checksum3_strided(c_ordered_strided_source, contiguous_checksum)


def test_dense_strided_and_projected_arrays_use_canonical_plan(tmp_path: Path):
    """Replay dense extents, positive strides, and returned storage identity."""
    native_object = _compile_native_object(SOURCE, tmp_path / "native")
    selected = ("scale2_contiguous", "scale2_strided", "scale2_explicit", "shift3_strided")
    contract_package = tmp_path / "multid_arrays_contract"
    shutil.copytree(CONTRACT_FIXTURES / "multid_arrays", contract_package)
    (contract_package / "__init__.pyi").write_text(
        "".join(f"from .multid_arrays import {name}\n" for name in selected),
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract_package / "__init__.pyi",
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    imported = _import_from_build_dir(result.module_name, result.output_dir)
    module = imported if hasattr(imported, "scale2_contiguous") else _sole_native_module(imported)

    dense = _matrix()
    dense_out = np.zeros_like(dense, order="F")
    assert module.scale2_contiguous(dense, dense_out) is None
    np.testing.assert_allclose(dense_out, 2.0 * dense)

    explicit_out = np.zeros_like(dense, order="F")
    assert module.scale2_explicit(np.int32(4), np.int32(3), dense, explicit_out) is None
    np.testing.assert_allclose(explicit_out, 4.0 * dense)

    strided = _strided_matrix()
    strided_out = _strided_matrix_output(strided.shape)
    assert module.scale2_strided(strided, strided_out) is None
    np.testing.assert_allclose(strided_out, 3.0 * strided)

    empty = _strided_matrix(0, 3)
    empty_out = _strided_matrix_output(empty.shape)
    assert module.scale2_strided(empty, empty_out) is None
    assert empty_out.shape == (0, 3)

    dense = _matrix()
    output = np.zeros_like(dense, order="F")
    with pytest.raises(TypeError):
        module.scale2_strided(_reversed_fortran_matrix(), output)
    with pytest.raises(TypeError):
        module.scale2_strided(_broadcast_fortran_like_matrix(), output)
    with pytest.raises(TypeError):
        module.scale2_contiguous(np.array(dense, order="C"), output)
