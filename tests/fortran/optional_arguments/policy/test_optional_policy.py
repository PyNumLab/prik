"""Optional presence completes one three-state boundary decision before planning."""

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.models import RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import ArgumentHandoffMode, FunctionWrapperPolicy, OptionalMode
from prik.policy.construction import completed_function_wrapper_policy


@pytest.mark.parametrize(
    ("contract", "position", "optional_mode", "nullable", "descriptor_boundary", "handoff_mode"),
    [
        (
            "def scale(base: Float64, factor: Float64 = ...) -> Float64: ...",
            1,
            OptionalMode.NULLABLE_VALUE,
            False,
            False,
            None,
        ),
        (
            "@native_call([Allocatable(Arg(0))])\n"
            "def alloc_state(value: Annotated[Float64, Immutable] | None = ...) -> Int32: ...",
            0,
            OptionalMode.DESCRIPTOR,
            True,
            True,
            None,
        ),
        (
            "@native_call([Allocatable(Arg(0))])\ndef alloc_state(value: Float64 | None) -> Int32: ...",
            0,
            OptionalMode.REQUIRED_DESCRIPTOR,
            True,
            True,
            None,
        ),
        (
            "@native_call([Addr(Arg(0)), Arg(1)])\n"
            'def fill_optional(n: Int32, values: Float64[::] = ...) -> Returns["values", Float64[::]] | None: ...',
            1,
            OptionalMode.NULLABLE_VALUE,
            True,
            False,
            ArgumentHandoffMode.ARRAY_BUFFER,
        ),
    ],
    ids=[
        "optional-scalar-nullable-value",
        "optional-descriptor-three-state",
        "required-descriptor-nullable-at-native-boundary",
        "optional-array-buffer-separate-from-descriptor-storage",
    ],
)
def test_optional_policy_completes_presence_mode_before_planning(
    contract, position, optional_mode, nullable, descriptor_boundary, handoff_mode
):
    """Omitted, ``None``, and a value are three states; policy says which ones the ABI carries.

    A plain optional passes a null pointer for omitted or ``None``. A
    descriptor dummy also distinguishes a present-but-unallocated descriptor,
    and a required descriptor argument still accepts ``None`` for that state.
    """
    module = parse_pyi_text(contract, module_name="optional_policy")
    complete_semantic_policies(module)
    policy = completed_function_wrapper_policy(module.functions[0])
    argument = policy.arguments[position]

    assert policy.supported is True
    assert argument.optional_mode is optional_mode
    assert argument.nullable is nullable
    assert argument.descriptor_boundary is descriptor_boundary
    if handoff_mode is not None:
        assert argument.handoff_mode is handoff_mode


def test_optional_value_callback_dummy_is_blocked_before_codegen():
    module = parse_pyi_text(
        """
@prototype
def callback_shape(value: Float64 = ...) -> None: ...

def apply(callback: callback_shape) -> None: ...
""",
        module_name="unsupported_optional_callback",
    )

    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is False
    assert (
        "callback argument 'value' cannot be both optional and passed by value; "
        "use a reference dummy so absence has a null-pointer ABI"
    ) in policy.blockers
