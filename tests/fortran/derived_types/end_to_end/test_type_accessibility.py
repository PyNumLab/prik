"""Generated class surface for Fortran accessibility statements."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fortran._support.wrapper_build import _build_source_and_import

pytestmark = pytest.mark.fortran_end_to_end

SOURCE = Path(__file__).parent / "fixtures" / "type_accessibility.f90"
GENERATED = {
    "bind_c_type_accessibility_wrapper.f90",
    "type_accessibility_wrapper.c",
    "type_accessibility_wrapper.h",
}


def test_accessibility_statements_shape_the_generated_class(tmp_path: Path):
    """Only components and bindings the type publishes reach Python.

    A `type, public ::` declaration is exported even though the module defaults
    to `private`, while the type's own `private` statements keep its internal
    component and binding off the generated surface.
    """
    module = _build_source_and_import(SOURCE, tmp_path, GENERATED)

    assert hasattr(module, "gated")
    members = {name for name in dir(module.gated) if not name.startswith("_")}
    assert members == {"shown", "step", "peek"}

    instance = module.gated(shown=np.int32(5))
    assert instance.shown == np.int32(5)
    assert instance.peek() == np.int32(7)
    instance.step()
    assert instance.peek() == np.int32(8)
