"""Import fixture for the wrapper produced by ``build_all.sh``."""

import ast
import importlib
import os
from pathlib import Path

import numpy as np
import pytest


_REAL_DTYPES = {
    "Float64": np.float64,
    "Float128": np.longdouble,
}


@pytest.fixture(scope="session")
def libm():
    """Return the already-built PRIK libm module."""
    return importlib.import_module("prik_reference_libm")


@pytest.fixture(scope="session")
def public_long_double_dtype():
    """Return the public dtype generated for the libm ``long double`` calls."""
    contract = Path(os.environ["LIBM_BUILD_ROOT"]) / "prik/contract/libm_api.pyi"
    tree = ast.parse(contract.read_text(encoding="utf-8"), filename=str(contract))
    sinl = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "sinl")
    annotation = sinl.args.args[0].annotation

    assert isinstance(annotation, ast.Name)
    assert annotation.id in _REAL_DTYPES
    return np.dtype(_REAL_DTYPES[annotation.id])
