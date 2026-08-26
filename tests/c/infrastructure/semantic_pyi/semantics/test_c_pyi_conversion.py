"""C-native semantic `.pyi` conversion contracts."""

import pytest

from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text


def test_convert_pyi_to_ir_uses_c_native_array_defaults():
    module = parse_pyi_text(
        """
from prik.contracts import Annotated, Float64, ORDER_ANY, ORDER_F

def consume(
    a: Float64[:, :],
    f: Annotated[Float64[:, :], ORDER_F],
    any_order: Annotated[Float64[:, :], ORDER_ANY]
) -> None: ...
""",
        module_name="c_contract",
        native_language="c",
    )

    arrays = [arg.semantic_type.storage.array for arg in module.functions[0].arguments]
    assert [array.order for array in arrays] == ["ORDER_C", "ORDER_F", "ORDER_ANY"]
    assert arrays[1].source_shape == []


def test_convert_pyi_to_ir_rejects_redundant_c_default_array_order():
    with pytest.raises(ValueError, match="ORDER_C is implicit for c"):
        parse_pyi_text(
            """
from prik.contracts import Annotated, Float64, ORDER_C

value: Annotated[Float64[:, :], ORDER_C]
""",
            module_name="redundant_order",
            native_language="c",
        )
