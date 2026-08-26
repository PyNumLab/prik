"""Semantic `.pyi` rules for editable module initializers."""

import ast

import pytest
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text


def test_mutable_module_literal_defaults_are_preserved():
    source = """from prik.contracts import Float64, Int32, String

counter: Int32 = 41
scale: Float64 = 2.5
label: String[8] = "ready"
"""

    module = parse_pyi_text(source, module_name="runtime_state")

    assert [variable.default_value for variable in module.variables[:2]] == ["41", "2.5"]
    assert ast.literal_eval(module.variables[2].default_value) == "ready"


@pytest.mark.parametrize(
    "source",
    [
        "from prik.contracts import Int32\ncounter: Int32 = f(42)\n",
        "from prik.contracts import Int32\ncounter: Int32 = x + 1\n",
        "from prik.contracts import Int32\ncounter: Int32 = SOME_NAME\n",
    ],
)
def test_mutable_module_expression_defaults_are_rejected(source):
    with pytest.raises(ValueError, match="Mutable defaults must be literal values"):
        parse_pyi_text(source, module_name="runtime_state")
