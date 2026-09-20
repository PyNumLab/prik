"""Generated class surface for Fortran accessibility statements."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from prik.parsers.fortran import parse_fortran_project
from prik.pipeline.pyi import emit_module_stubs
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from tests.fortran._support.wrapper_build import _build_source_and_import, _build_text_and_import

pytestmark = pytest.mark.fortran_end_to_end

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"

SOURCE = Path(__file__).parent / "fixtures" / "native" / "type_accessibility.f90"
GENERATED = {
    "bind_c_type_accessibility_wrapper.f90",
    "type_accessibility_wrapper.c",
    "type_accessibility_wrapper.h",
}

DEPENDENCY_SOURCE = (NATIVE_FIXTURES / "type_accessibility_dependency.f90").read_text(encoding="utf-8")


def test_accessibility_statements_shape_the_generated_class(tmp_path: Path):
    """Only components and bindings the type publishes reach Python.

    A `type, public ::` declaration is exported even though the module defaults
    to `private`, while the type's own `private` statements keep its internal
    component and binding off the generated surface.
    """
    module = _build_source_and_import(SOURCE, tmp_path, GENERATED)

    assert hasattr(module, "Gated")
    members = {name for name in dir(module.Gated) if not name.startswith("_")}
    assert members == {"shown", "step", "peek"}

    instance = module.Gated(shown=np.int32(5))
    assert instance.shown == np.int32(5)
    assert instance.peek() == np.int32(7)
    instance.step()
    assert instance.peek() == np.int32(8)


def test_declaration_dependency_accessibility_and_python_publication_are_separate(tmp_path: Path):
    """The semantic route remains valid while runtime and contract omit its alias."""
    source = tmp_path / "dependency_accessibility.f90"
    module = _build_text_and_import(
        DEPENDENCY_SOURCE,
        source.name,
        tmp_path,
        {
            "bind_c_dependency_accessibility_wrapper.f90",
            "dependency_accessibility_wrapper.c",
            "dependency_accessibility_wrapper.h",
        },
    )
    stubs = emit_module_stubs(
        fortran_project_to_semantic_modules(parse_fortran_project([source])),
        normalize_public_names=True,
    )

    consumer_contract = stubs["dependency_consumer"]
    # A renamed type is still a class, spelled as one wherever the contract
    # writes it: in its import and in the annotations naming it.
    assert "from .dependency_home import Box as Crate" in consumer_contract
    assert "item: Crate" in consumer_contract
    assert consumer_contract.rstrip().endswith('__all__ = ["crate_value"]')
    assert not any(name.casefold() == "crate" for name in vars(module.dependency_consumer))

    item = module.dependency_home.Box(value=np.int32(7))
    assert module.dependency_consumer.crate_value(item) == np.int32(7)
