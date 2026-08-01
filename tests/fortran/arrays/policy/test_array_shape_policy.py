"""Completed array extent-reference policy."""

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.models import RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA
from prik.semantics.policy_completion import complete_semantic_policies


def test_array_extent_reference_requires_a_visible_scalar_argument():
    module = parse_pyi_text(
        """
from prik.contracts import Float64

def values() -> Float64[missing]: ...
""",
        module_name="missing_extent",
    )
    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert policy.supported is False
    assert (
        "array owner 'missing_extent.values.return' extent axis 0 has unavailable scalar references ('missing',)"
        in policy.blockers
    )
