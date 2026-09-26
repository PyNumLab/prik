"""Completed-policy evidence for runtime-rank C pointer storage."""

from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import ArrayPythonLayout
from prik.semantics.native_contract import validate_pyi_native_contract


def test_contiguous_narrows_runtime_rank_storage_to_the_c_order_layout():
    """``T[...]`` states no layout, so ``Contiguous`` is what asserts one."""
    module = pyi_text_to_semantic_module(
        """from prik.contracts import Annotated, Contiguous, Float64
def scale(values: Annotated[Float64[...], Contiguous]) -> None: ...
""",
        module_name="contiguous_rank",
        native_language="c",
    )
    validate_pyi_native_contract([module])
    complete_semantic_policies(module)

    array = module.functions[0].metadata["resolved_function_wrapper_policy"].arguments[0].array

    assert array.rank is None
    assert (array.minimum_rank, array.maximum_rank) == (0, 15)
    assert array.contiguous is True
    assert array.python_layout is ArrayPythonLayout.C_CONTIGUOUS
