"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

import pytest
import re
from prik.semantics.native_array_handles import native_array_descriptor_kind
from tests.fortran._support.pyi_conversion import parse_pyi_text


def test_convert_pyi_to_ir_accepts_defaulted_scalar_descriptor_optional_dummies():
    module = parse_pyi_text(
        """
@native_call([Allocatable(Arg(0)), Pointer(Arg(1))])
def update(scale: Float64 | None = ..., current: Float64 | None = ...) -> None: ...
""",
        module_name="optional_scalar_descriptors",
    )

    scale, current = module.functions[0].arguments
    assert scale.optional is True
    assert scale.semantic_type.metadata["fortran_allocatable"] is True
    assert current.optional is True
    assert current.semantic_type.metadata["fortran_pointer"] is True
    assert native_array_descriptor_kind(scale.semantic_type) is None
    assert native_array_descriptor_kind(current.semantic_type) is None


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            "values: Allocatable[Float64[:]] | None = ...\n",
            "only valid for optional callable arguments",
        ),
        (
            "def make_values() -> Allocatable[Float64[:]] | None: ...\n",
            "only valid for optional callable arguments",
        ),
        (
            "def consume(values: Allocatable[Float64[:]] | None) -> None: ...\n",
            "must use '= ...' or '= None'",
        ),
        (
            "def consume(values: Pointer[Float64[:]] = ...) -> None: ...\n",
            "must use Pointer[T[...]] | None = ...",
        ),
    ],
)
def test_convert_pyi_to_ir_rejects_misplaced_optional_array_handle_none(source, message):
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_pyi_text(source, module_name="invalid_optional_array_handle")
