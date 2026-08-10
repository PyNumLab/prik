"""Internal CPython binding lowering contracts."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from prik.codegen import (
    BackendScalarType,
)
from prik.codegen.c.binding import CBindingGenerator


def test_c_binding_rejects_an_unprefixed_numpy_scalar_macro():
    scalar = BackendScalarType(
        semantic_name="Invalid",
        c_spelling="double",
        fortran_spelling="real(c_double)",
        numpy_type_macro="FLOAT64",
    )

    with pytest.raises(ValueError, match="Unsupported NumPy scalar type macro 'FLOAT64'"):
        CBindingGenerator()._scalar_helper_suffix(scalar)


def test_binding_direct_example_is_runnable():
    repository_root = Path(__file__).resolve().parents[4]
    result = subprocess.run(
        [sys.executable, str(repository_root / "prik/codegen/c/binding.py")],
        cwd=repository_root,
        capture_output=True,
        check=True,
        text=True,
    )

    assert "Native procedure: DOUBLE_VALUE" in result.stdout
