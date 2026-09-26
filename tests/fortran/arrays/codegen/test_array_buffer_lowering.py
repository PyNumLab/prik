"""Array handoff plans are validated before lowering, and lower to legal Fortran."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import BridgeDataAction
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _array_plan():
    module = parse_pyi_text(
        "def sum_values(values: Float64[:]) -> Float64: ...\n",
        module_name="array_buffers",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("rank", "inconsistent-array-rank"),
        ("axis", "invalid-array-axis-modes"),
        ("role", "inconsistent-array-data-role"),
        ("action", "invalid-array-data-action"),
    ],
)
def test_array_handoff_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _array_plan()
    argument = plan.namespaces[0].functions[0].arguments[0]
    if edit == "rank":
        argument.array.rank = 2
    elif edit == "axis":
        argument.array.axes = ("strided",)
    elif edit == "role":
        argument.array.data_role = "edited:data-role"
    else:
        argument.bridge.data_action = BridgeDataAction.DIRECT_TRANSFER

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)


def test_high_rank_bool_array_bridge_stays_inside_the_fortran_line_limit():
    """Free-form Fortran caps a line at 132 columns, whatever the rank.

    A rank-15 logical descriptor dummy is the longest ordinary array
    declaration PRIK emits and is where continuation would first be missed.
    Not every compiler rejects a longer line, so this is checked on the text.
    """
    shape = ", ".join(":" for _ in range(15))
    module = parse_pyi_text(
        f"""
from prik.contracts import Bool

def normalize(values: Bool[{shape}]) -> None: ...
""",
        module_name="high_rank_logical_array",
    )
    complete_semantic_policies(module)
    artifacts = WrapperGenerator().generate(WrapperPlanner().build(module))
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "dimension(:, :, :, :, :, :, :, :, :, :, :, :, :, :, :), contiguous :: values" in bridge_source
    assert max(map(len, bridge_source.splitlines())) <= 132
