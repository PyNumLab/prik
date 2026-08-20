"""Tests split by stable ownership concept from `test_c_conversion_properties.py`."""

import pytest
from dataclasses import asdict
from hypothesis import (
    given,
    strategies as st,
)
from prik.parsers.fortran import parse_fortran_file
from prik.semantics.fortran2ir import (
    fortran_file_to_semantic_modules,
    resolve_semantic_compile_time_values,
)
from prik.semantics.models import (
    SemanticArgument,
    SemanticArrayContract,
    SemanticConstraint,
    SemanticModule,
    SemanticStorageContract,
    SemanticType,
)
from tests.fortran._support.semantic_properties import _FORTRAN_VALUE_TYPES


@pytest.mark.property
@given(_FORTRAN_VALUE_TYPES)
def test_generated_fortran_value_arguments_have_the_expected_semantic_contract(case):
    fortran_type, semantic_type = case
    fortran_module = fortran_file_to_semantic_modules(
        parse_fortran_file(
            f"subroutine consume(value)\n  {fortran_type}, intent(in), value :: value\nend subroutine consume\n",
            filename="generated.f90",
        ),
        standalone_module_name="generated",
    )[0]

    fortran_argument = fortran_module.functions[0].arguments[0]
    assert fortran_argument.semantic_type.name == semantic_type
    assert fortran_argument.semantic_type.origin.source_language == "fortran"


@pytest.mark.property
@given(n=st.integers(min_value=1, max_value=999), m=st.integers(min_value=1, max_value=999))
def test_generated_semantic_specialization_is_non_mutating_and_idempotent(n, m):
    module = SemanticModule(
        name="generated",
        variables=[
            SemanticArgument(
                name="values",
                semantic_type=SemanticType(
                    name="Float64",
                    dtype="Float64",
                    rank=2,
                    shape=["1:n", "m + 1"],
                    constraints=[SemanticConstraint("Extent", ["n", {"upper": "m"}])],
                    metadata={"bounds": ("n", ["m"])},
                    storage=SemanticStorageContract(
                        kind="array",
                        metadata={"extent": "n"},
                        array=SemanticArrayContract(
                            rank=2,
                            shape=["1:n", "m + 1"],
                            lower_bounds=["1", "0"],
                            upper_bounds=["n", "m"],
                            source_shape=["1:n", "0:m"],
                            metadata={"extent": {"first": "n", "second": "m"}},
                        ),
                    ),
                ),
            )
        ],
        metadata={"shape": ["n", "m"]},
    )
    original = asdict(module)

    resolved = resolve_semantic_compile_time_values(module, {"n": n, "m": m})

    assert asdict(module) == original
    semantic_type = resolved.variables[0].semantic_type
    assert semantic_type.shape == [f"1:{n}", f"{m} + 1"]
    assert semantic_type.constraints[0].arguments == [str(n), {"upper": str(m)}]
    assert semantic_type.metadata == {"bounds": (str(n), [str(m)])}
    assert semantic_type.storage is not None
    assert semantic_type.storage.metadata == {"extent": str(n)}
    assert semantic_type.storage.array is not None
    assert semantic_type.storage.array.shape == [f"1:{n}", f"{m} + 1"]
    assert semantic_type.storage.array.lower_bounds == ["1", "0"]
    assert semantic_type.storage.array.upper_bounds == [str(n), str(m)]
    assert semantic_type.storage.array.source_shape == [f"1:{n}", f"0:{m}"]
    assert semantic_type.storage.array.metadata == {"extent": {"first": str(n), "second": str(m)}}
    assert asdict(resolve_semantic_compile_time_values(resolved, {"n": n, "m": m})) == asdict(resolved)
