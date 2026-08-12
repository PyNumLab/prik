"""Readable NumPy projection and primitive backend catalogue invariants."""

import pytest

from prik.codegen.primitive_scalar_types import (
    NumpyDtypeRegistry,
    PrimitiveScalarTypeRegistry,
)


def test_numpy_projection_catalogue_uses_resolved_semantic_names():
    assert NumpyDtypeRegistry.TYPES["Bool64"] == "numpy.bool_"
    assert NumpyDtypeRegistry.TYPES["Int32"] == "numpy.int32"
    assert NumpyDtypeRegistry.TYPES["Float128"] == "numpy.longdouble"
    assert NumpyDtypeRegistry.TYPES["Complex256"] == "numpy.clongdouble"
    assert NumpyDtypeRegistry.TYPES["SizeT"] == "numpy.uintp"
    assert "Int" not in NumpyDtypeRegistry.TYPES


def test_numpy_projection_rejects_unresolved_and_unknown_semantic_dtypes():
    with pytest.raises(KeyError, match="Semantic dtype is not resolved"):
        NumpyDtypeRegistry.expression_for(None)

    with pytest.raises(KeyError, match="No NumPy dtype mapping for semantic dtype 'Int'"):
        NumpyDtypeRegistry.expression_for("Int")


def test_backend_catalogue_makes_each_emitted_representation_explicit():
    scalar = PrimitiveScalarTypeRegistry.type_for("Float64")

    assert scalar.semantic_name == "Float64"
    assert scalar.c_spelling == "double"
    assert scalar.fortran_spelling == "real(c_double)"
    assert scalar.numpy_type_macro == "NPY_FLOAT64"
    assert scalar.python_type_name == NumpyDtypeRegistry.TYPES["Float64"]
    assert scalar.cfi_type_spelling == "CFI_type_double"


def test_backend_catalogue_returns_detached_records():
    scalar = PrimitiveScalarTypeRegistry.type_for("Int32")
    scalar.c_spelling = "changed"

    assert PrimitiveScalarTypeRegistry.type_for("Int32").c_spelling == "int32_t"
