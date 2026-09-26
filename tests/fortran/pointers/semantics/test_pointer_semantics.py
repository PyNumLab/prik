"""Edited-`.pyi` pointer contract diagnostics."""

import re

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            "def produce() -> Pointer[Float64]: ...\n",
            "Procedure scalar descriptor results use a nullable value annotation",
        ),
        (
            "@native_call([], result=Pointer(Return(0)))\ndef produce() -> Float64: ...\n",
            "must use a nullable T | None annotation",
        ),
    ],
)
def test_scalar_pointer_results_require_a_nullable_value_annotation(source: str, message: str):
    with pytest.raises(ValueError, match=re.escape(message)):
        parse_pyi_text(source, module_name="invalid_pointer_projection")
