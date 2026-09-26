"""Readable NumPy projection for resolved primitive semantic types."""

import pytest

from prik.codegen.primitive_scalar_types import NumpyDtypeRegistry


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
