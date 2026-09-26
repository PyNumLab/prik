"""Semantic `.pyi` spelling and projection rules for allocatables."""

import re

import pytest

from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text


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
