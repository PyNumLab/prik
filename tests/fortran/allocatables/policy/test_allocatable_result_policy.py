"""Allocatable result forms that policy must block before codegen."""

from prik.policy.completion import complete_semantic_policies
from prik.policy.models import FunctionWrapperPolicy
from prik.semantics.models import RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA
from tests.fortran._support.ownership_policy import parse_pyi_text


def test_direct_allocatable_scalar_function_result_is_blocked_before_codegen():
    module = parse_pyi_text(
        """
@native_call([Arg(0)], result=Allocatable(Return(0)))
def maybe_allocatable(flag: Int32) -> Float64 | None: ...
""",
        module_name="direct_descriptor_result",
    )

    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is False
    assert (
        "direct allocatable scalar function results cannot preserve unallocated state; "
        "use an allocatable hidden output projection"
    ) in policy.blockers
