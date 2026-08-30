"""Completed-policy evidence for runtime-rank C pointer storage."""

from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import ArrayPythonLayout, EntrypointPassingConvention, EntrypointProjectionAction
from prik.semantics.native_contract import validate_pyi_native_contract


def test_c_runtime_rank_and_total_size_are_complete_before_planning():
    module = pyi_text_to_semantic_module(
        """from prik.contracts import Arg, Float64, native_call
@native_call([Arg(0).size, Arg(0)])
def scale(values: Float64[...]) -> None: ...
""",
        module_name="runtime_rank",
        native_language="c",
    )
    validate_pyi_native_contract([module])
    complete_semantic_policies(module)

    policy = module.functions[0].metadata["resolved_function_wrapper_policy"]
    array = policy.arguments[0].array
    size_slot = policy.native_call_slots[0]

    assert array.rank is None
    assert (array.minimum_rank, array.maximum_rank) == (0, 15)
    assert array.order == "ORDER_C"
    assert array.native_order == "ORDER_C"
    assert array.contiguous is None
    assert array.python_layout is ArrayPythonLayout.ANY_STRIDED
    assert size_slot.semantic_type_name == "SizeT"
    assert size_slot.projection_action is EntrypointProjectionAction.COMPUTED_SIZE
    assert size_slot.entrypoint_passing is EntrypointPassingConvention.C_VALUE


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
