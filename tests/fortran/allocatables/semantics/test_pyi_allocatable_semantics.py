"""Semantic `.pyi` spelling and projection rules for allocatables."""

import re

import pytest

from tests.fortran._support.semantic_conversion import parse_pyi_text
from prik.semantics.metadata import PROJECTED_OUTPUT_METADATA
from prik.semantics.native_array_handles import native_array_descriptor_kind


def test_persistent_allocatable_descriptors_preserve_scalar_and_array_kinds():
    module = parse_pyi_text(
        """
from prik.contracts import Aliased, Allocatable, Annotated, Float64

scratch: Allocatable[Float64]
values: Annotated[Allocatable[Float64[:]], Aliased]

class buffer:
    field: Allocatable[Float64[:, :]]
""",
        module_name="persistent_allocatables",
    )

    scratch, values = module.variables
    field = module.classes[0].fields[0]

    assert scratch.semantic_type.name == "Float64"
    assert scratch.semantic_type.rank == 0
    assert scratch.semantic_type.storage is None
    assert scratch.semantic_type.metadata["fortran_allocatable"] is True

    assert native_array_descriptor_kind(values.semantic_type) == "allocatable"
    assert values.semantic_type.rank == 1
    assert values.semantic_type.metadata["aliased"] is True
    assert native_array_descriptor_kind(field.semantic_type) == "allocatable"
    assert field.semantic_type.rank == 2
    assert "aliased" not in field.semantic_type.metadata


def test_scalar_allocatable_calls_use_nullable_values_and_explicit_descriptor_projections():
    module = parse_pyi_text(
        """
from prik.contracts import Allocatable, Arg, Float64, Return, Returns, native_call

@native_call([Allocatable(Arg(0)), Allocatable(Return("created", 1))])
def update(
    value: Float64 | None,
) -> tuple[
    Returns["value", Float64] | None,
    Returns["created", Float64] | None,
]: ...
""",
        module_name="scalar_allocatable_calls",
    )

    function = module.functions[0]
    value, created = function.arguments
    assert value.semantic_type.metadata["fortran_allocatable"] is True
    assert value.metadata[PROJECTED_OUTPUT_METADATA] is True
    assert created.semantic_type.metadata["fortran_allocatable"] is True
    assert created.metadata[PROJECTED_OUTPUT_METADATA] is True
    assert [mapping.value_kind for mapping in function.projection] == ["allocatable", "allocatable"]


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            "from prik.contracts import Allocatable, Float64\ndef consume(value: Allocatable[Float64]) -> None: ...\n",
            "Procedure scalar descriptors use nullable value annotations",
        ),
        (
            "from prik.contracts import Allocatable, Float64\ndef produce() -> Allocatable[Float64]: ...\n",
            "Procedure scalar descriptor results use a nullable value annotation",
        ),
        (
            "from prik.contracts import Allocatable, Arg, Float64, native_call\n"
            "@native_call([Allocatable(Arg(0))])\n"
            "def consume(value: Float64) -> None: ...\n",
            "must use a nullable annotation",
        ),
        (
            "from prik.contracts import Allocatable, Arg, Float64, native_call\n"
            "@native_call([], result=Allocatable(Arg(0)))\n"
            "def produce() -> Float64 | None: ...\n",
            "must reference Return(i), not Arg(i)",
        ),
    ],
)
def test_scalar_allocatable_calls_reject_descriptor_wrappers_as_python_values(
    source: str,
    message: str,
):
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_pyi_text(source, module_name="invalid_scalar_allocatable")


def test_plain_nullable_scalar_is_not_an_allocatable_descriptor():
    module = parse_pyi_text(
        "from prik.contracts import Float64\nmaybe_value: Float64 | None\n",
        module_name="nullable_value",
    )

    semantic_type = module.variables[0].semantic_type
    assert semantic_type.name == "Float64 | None"
    assert "fortran_allocatable" not in semantic_type.metadata


def test_legacy_annotated_allocatable_array_spelling_is_rejected():
    with pytest.raises(ValueError, match="use Allocatable"):
        parse_pyi_text(
            """
from prik.contracts import Allocatable, Annotated, Float64
values: Annotated[Float64[:], Allocatable]
""",
            module_name="legacy_allocatable_array",
        )
