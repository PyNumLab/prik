"""Typed scalar input lowering through the public generator."""

from __future__ import annotations

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def test_binding_locals_are_isolated_from_identifiers_imported_by_c_headers():
    module = parse_pyi_text("def identity(complex: Float64) -> Float64: ...", module_name="header_names")
    complete_semantic_policies(module)

    c_source = next(
        source.text
        for source in WrapperGenerator().generate(WrapperPlanner().build(module)).sources
        if source.path.suffix == ".c"
    )

    assert '#include "binding_support/prik_binding.h"' in c_source
    assert "double bound_complex;" in c_source
    assert "prik_float64_or_storage(bound_complex_obj, NPY_FLOAT64, " in c_source
    assert "&bound_complex, " in c_source
    assert "double complex;" not in c_source
