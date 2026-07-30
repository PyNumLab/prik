"""Tests split by stable ownership concept from `test_compile_time_values.py`."""

from tests.fortran._support.semantic_conversion import (
    SemanticModule,
    SemanticType,
    SemanticVariable,
    resolve_semantic_compile_time_values,
)


def test_resolve_semantic_compile_time_values_handles_enum_like_constants():
    enumerator = SemanticVariable(
        name="STATUS_LIMIT",
        semantic_type=SemanticType("Int32", metadata={"enum_name": "status"}),
        default_value="n",
    )
    module = SemanticModule(
        name="status_mod",
        variables=[enumerator],
    )

    resolved = resolve_semantic_compile_time_values(module, {"n": 16})

    assert resolved.variables[0].semantic_type.metadata == {"enum_name": "status"}
    assert resolved.variables[0].default_value == "16"
