"""Import fixture for the wrapper produced by ``build_all.sh``."""

import ast
import importlib
import os
from pathlib import Path

import numpy as np
import pytest
from numpy import float64

float128 = np.longdouble

_PUBLIC_REAL_TYPES = {
    "Float64": float64,
    "Float128": float128,
}


@pytest.fixture(scope="session")
def libm():
    """Return the already-built PRIK libm module."""
    return importlib.import_module("prik_reference_libm")


@pytest.fixture(scope="session")
def public_long_double_type():
    """Return the public scalar type generated for libm ``long double`` calls."""
    contract = Path(os.environ["LIBM_BUILD_ROOT"]) / "prik/contract/libm_api.pyi"
    tree = ast.parse(contract.read_text(encoding="utf-8"), filename=str(contract))
    sinl = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "sinl")
    annotation = sinl.args.args[0].annotation

    assert isinstance(annotation, ast.Name)
    assert annotation.id in _PUBLIC_REAL_TYPES
    return _PUBLIC_REAL_TYPES[annotation.id]
