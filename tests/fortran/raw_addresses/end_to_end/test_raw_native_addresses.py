"""Primitive, array, and fixed-string raw address runtime boundaries."""

import ctypes
from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import (
    _compile_native_object,
    _import_from_build_dir,
    _sole_native_module,
)
from prik import build_pyi_extension

NATIVE_CALL_EXAMPLES_F90_SOURCE = (
    Path(__file__).parents[2]
    / "infrastructure"
    / "semantic_pyi"
    / "contracts"
    / "calls_and_results"
    / "end_to_end"
    / "fixtures"
    / "native"
    / "fnative_call_examples_f90.f90"
)
RAW_CONTRACT = Path(__file__).parent / "fixtures" / "edited_contracts" / "raw_native_order" / "__init__.pyi"
pytestmark = pytest.mark.fortran_end_to_end


def test_primitive_array_and_fixed_string_raw_addresses_share_one_native_build(tmp_path: Path):
    native_object = _compile_native_object(NATIVE_CALL_EXAMPLES_F90_SOURCE, tmp_path / "native")
    result = build_pyi_extension(
        RAW_CONTRACT,
        native_objects=[native_object],
        native_include_dirs=[native_object.parent],
        output_dir=tmp_path / "build",
    )
    package = _import_from_build_dir(result.module_name, result.output_dir)
    module = package if hasattr(package, "fill_vector_raw") else _sole_native_module(package)

    base = np.array(4, dtype=np.int32)
    status = np.empty((), dtype=np.int32)
    assert module.scalar_status_raw(base.ctypes.data, status.ctypes.data) is None
    assert status[()] == np.int32(15)
    with pytest.raises(TypeError):
        module.scalar_status_raw(base, status.ctypes.data)
    with pytest.raises(OverflowError):
        module.scalar_status_raw(1 << 100, status.ctypes.data)

    vector_size = np.array(4, dtype=np.int32)
    raw_vector = np.empty(4, dtype=np.float64)
    assert module.fill_vector_raw(vector_size, raw_vector.ctypes.data) is None
    np.testing.assert_allclose(raw_vector, np.array([1.5, 3.0, 4.5, 6.0], dtype=np.float64))

    with pytest.raises(TypeError):
        module.fill_vector_raw(vector_size, raw_vector)
    with pytest.raises(TypeError):
        module.fill_vector_raw(vector_size, "not an address")

    rows = np.array(2, dtype=np.int32)
    cols = np.array(3, dtype=np.int32)
    for order, function_name in (("C", "shift_matrix_raw_c"), ("F", "shift_matrix_raw_f")):
        matrix = np.array([[1.0, 3.0, 5.0], [2.0, 4.0, 6.0]], dtype=np.float64, order=order)
        shifted = np.empty((2, 3), dtype=np.float64, order=order)
        function = getattr(module, function_name)
        assert function(rows, cols, matrix.ctypes.data, shifted.ctypes.data) is None
        np.testing.assert_allclose(shifted, matrix + 10.0)

    raw_label = ctypes.create_string_buffer(8)
    raw_label.raw = b"abc     "
    assert module.fixed_inout_raw(ctypes.addressof(raw_label)) is None
    assert raw_label.raw == b"Xbc    !"

    storage_label = np.array("abc     ", dtype="S8")
    assert module.fixed_inout_storage(storage_label) is None
    assert storage_label[()] == b"Xbc    !"

    with pytest.raises(TypeError):
        module.fixed_inout_raw("abc     ")
    with pytest.raises(TypeError, match="itemsize 8"):
        module.fixed_inout_storage(np.array("abc", dtype="S3"))
    with pytest.raises(TypeError):
        module.fixed_inout_storage(np.array([b"abc     "], dtype="S8"))
    with pytest.raises(TypeError):
        module.fixed_inout_storage(np.array("abc     ", dtype="U8"))
    read_only = np.array("abc     ", dtype="S8")
    read_only.flags.writeable = False
    with pytest.raises(TypeError, match="writeable"):
        module.fixed_inout_storage(read_only)
