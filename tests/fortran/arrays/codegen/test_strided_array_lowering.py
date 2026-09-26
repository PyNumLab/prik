"""Descriptor array dummies: contiguity and plan validation."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _plan(annotation: str):
    module = parse_pyi_text(
        f"""
from prik.contracts import Float64

def call(values: {annotation}) -> None: ...
""",
        module_name="descriptor_arrays",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_contiguous_descriptor_dummy_preserves_contiguity_for_native_call():
    """A contiguous descriptor dummy must not make a compiler temporary.

    A temporary still computes the right values, so runtime tests cannot see it.
    """
    artifacts = WrapperGenerator().generate(_plan("Float64[:]"))
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "real(c_double), dimension(:), contiguous :: values" in bridge_source


@pytest.mark.parametrize("roles", ["stride_roles", "lower_bound_roles"])
def test_descriptor_array_parallel_role_edit_fails_before_backend_lowering(roles: str):
    """Strides and bounds travel inside the descriptor, never beside it."""
    plan = _plan("Float64[::, ::]")
    array = plan.namespaces[0].functions[0].arguments[0].array
    assert array is not None
    setattr(array, roles, (f"{array.data_role}:{roles}:0",))

    with pytest.raises(ValueError, match="unexpected-array-descriptor-roles"):
        WrapperGenerator().generate(plan)
