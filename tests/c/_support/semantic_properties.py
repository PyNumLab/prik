"""Property-based invariants for C-to-semantic-IR conversion."""

from __future__ import annotations

import pytest


pytest.importorskip("hypothesis")

from hypothesis import strategies as st


_C_SCALAR_TYPES = st.sampled_from(
    [
        ("_Bool", "Bool"),
        ("double", "Float64"),
        ("float", "Float32"),
        ("int", "Int"),
    ]
)
_C_VALUE_TYPES = st.sampled_from(
    [
        ("_Bool", "Bool"),
        ("double", "Float64"),
        ("float", "Float32"),
    ]
)


@st.composite
def c_scalar_prototypes(draw):
    source_result, semantic_result = draw(_C_SCALAR_TYPES)
    parameter_ids = draw(st.lists(st.integers(min_value=0, max_value=99), max_size=6, unique=True))
    parameter_types = draw(st.lists(_C_SCALAR_TYPES, min_size=len(parameter_ids), max_size=len(parameter_ids)))
    parameters = [
        f"{source_type} p_{parameter_id}"
        for parameter_id, (source_type, _semantic_type) in zip(parameter_ids, parameter_types, strict=True)
    ]
    parameter_text = ", ".join(parameters) if parameters else "void"
    source = f"{source_result} transform({parameter_text});\n"
    expected_parameters = [
        (f"p_{parameter_id}", semantic_type)
        for parameter_id, (_source_type, semantic_type) in zip(parameter_ids, parameter_types, strict=True)
    ]
    return source, semantic_result, expected_parameters
