"""Semantic-to-NumPy dtype mapping tests."""

import pytest

from x2py.semantics.models import SemanticType
from x2py.types.numpy import (
    SEMANTIC_DTYPE_TO_NUMPY_DTYPE,
    numpy_dtype_expression,
    semantic_dtype_to_numpy_dtype,
    semantic_dtype_to_numpy_dtype_map,
    semantic_type_to_numpy_dtype,
)


def test_semantic_dtype_to_numpy_dtype_dictionary_uses_resolved_widths():
    assert SEMANTIC_DTYPE_TO_NUMPY_DTYPE == {
        "Bool": "numpy.bool_",
        "Int8": "numpy.int8",
        "Int16": "numpy.int16",
        "Int32": "numpy.int32",
        "Int64": "numpy.int64",
        "UInt8": "numpy.uint8",
        "UInt16": "numpy.uint16",
        "UInt32": "numpy.uint32",
        "UInt64": "numpy.uint64",
        "Float16": "numpy.float16",
        "Float32": "numpy.float32",
        "Float64": "numpy.float64",
        "Float128": "numpy.longdouble",
        "Complex64": "numpy.complex64",
        "Complex128": "numpy.complex128",
        "Complex256": "numpy.clongdouble",
        "String": "numpy.str_",
        "SizeT": "numpy.uintp",
    }
    assert "Int" not in SEMANTIC_DTYPE_TO_NUMPY_DTYPE


def test_numpy_dtype_expression_rejects_unresolved_or_unknown_semantic_dtypes():
    with pytest.raises(KeyError, match="Semantic dtype is not resolved"):
        numpy_dtype_expression(None)

    with pytest.raises(KeyError, match="No NumPy dtype mapping for semantic dtype 'Int'"):
        numpy_dtype_expression("Int")


def test_semantic_type_to_numpy_dtype_uses_dtype_not_name():
    numpy = pytest.importorskip("numpy")
    semantic_type = SemanticType("Int", dtype="Int64")

    assert semantic_type_to_numpy_dtype(semantic_type) == numpy.dtype(numpy.int64)
    assert semantic_dtype_to_numpy_dtype("Float16") == numpy.dtype(numpy.float16)
    assert semantic_dtype_to_numpy_dtype("Float64") == numpy.dtype(numpy.float64)
    dtype_map = semantic_dtype_to_numpy_dtype_map()
    assert dtype_map["Int32"] == numpy.dtype(numpy.int32)
    assert set(dtype_map) == set(SEMANTIC_DTYPE_TO_NUMPY_DTYPE)
