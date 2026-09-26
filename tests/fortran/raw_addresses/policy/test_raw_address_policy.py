"""Raw address forms that policy must block before codegen."""

import pytest

from prik.policy.completion import complete_semantic_policies
from prik.semantics.models import RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA
from tests.fortran._support.ownership_policy import parse_pyi_text


@pytest.mark.parametrize(
    ("contract", "blocker"),
    [
        pytest.param(
            "def optional_raw(n: Int32, values: Addr(Float64[n]) = ...) -> None: ...",
            "argument 'values' optional raw array addresses are not supported",
            id="optional",
        ),
        pytest.param(
            'def projected_raw(n: Int32, values: Addr(Float64[n])) -> Returns["values", Float64[n]]: ...',
            "argument 'values' raw array address cannot project a Python result",
            id="projected-result",
        ),
    ],
)
def test_wrapper_policy_blocks_raw_array_addresses_it_cannot_prove(contract: str, blocker: str):
    module = parse_pyi_text(contract, module_name="blocked_raw_array")
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert blocker in policy.blockers
