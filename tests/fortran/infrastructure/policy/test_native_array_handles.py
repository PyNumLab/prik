"""Internal native-array handle policy dispatch contracts."""

from prik.policy.native_array_handles import (
    ArrayInteropPolicy,
    ArrayInteropPolicyDispatcher,
)


def test_array_interop_dispatcher_routes_completed_abi_selector_to_named_method():
    class Subject:
        name = "values"

    class Target:
        def data_buffer(self, subject, policy, marker):
            return marker, subject.name, policy.abi

        def descriptor(self, subject, policy, marker):
            return marker, subject.name, policy.abi, policy.descriptor_kind

    dispatcher = ArrayInteropPolicyDispatcher(
        {
            ("argument", "data_buffer"): "data_buffer",
            ("argument", "descriptor"): "descriptor",
        },
    )

    assert dispatcher.dispatch(
        Target(),
        Subject(),
        ArrayInteropPolicy(abi="data_buffer", owner="argument values"),
        "argument",
        "seen",
    ) == ("seen", "values", "data_buffer")
    assert dispatcher.dispatch(
        Target(),
        Subject(),
        ArrayInteropPolicy(
            abi="descriptor",
            owner="argument values",
            descriptor_kind="allocatable",
            handle_kind="argument_descriptor",
        ),
        "argument",
        "seen",
    ) == ("seen", "values", "descriptor", "allocatable")
