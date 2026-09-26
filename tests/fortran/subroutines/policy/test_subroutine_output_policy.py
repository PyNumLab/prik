from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.construction import completed_function_wrapper_policy


def test_native_call_policy_maps_visible_positions_when_hidden_output_precedes_input():
    module = parse_pyi_text(
        """
@native_call([Return("status", 0), Addr(Arg(0))])
def mapped_status(base: Int32) -> Int32: ...
""",
        module_name="scalar_native_order",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])

    assert [(argument.name, argument.python_position, argument.native_position) for argument in policy.arguments] == [
        ("base", 0, 1)
    ]
    assert [(slot.owner_path, slot.source_kind, slot.native_position) for slot in policy.native_call_slots] == [
        ("scalar_native_order.mapped_status.status", "result", 0),
        ("scalar_native_order.mapped_status.base", "projection", 1),
    ]
