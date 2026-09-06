"""Signed-stride ordinary array view lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import ArrayEntrypointABI, EntrypointPassingConvention
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _strided_plan(rank: int = 2):
    dimensions = ", ".join("::" for _ in range(rank))
    module = parse_pyi_text(
        f"""
from prik.contracts import Float64

def strided(values: Float64[{dimensions}]) -> None: ...
""",
        module_name="strided_arrays",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_strided_array_plan_selects_one_descriptor_without_parallel_stride_roles():
    argument = _strided_plan().namespaces[0].functions[0].arguments[0]
    array = argument.array

    assert array is not None
    assert array.rank == 2
    assert array.axes == ("strided", "strided")
    assert array.contiguous is False
    assert array.entrypoint_abi is ArrayEntrypointABI.C_DESCRIPTOR
    assert array.signed_strides is True
    assert argument.entrypoint.passing is EntrypointPassingConvention.C_DESCRIPTOR_POINTER
    assert argument.entrypoint.pass_array_metadata is False
    assert array.upper_bound_roles == ()
    assert array.stride_roles == ()
    assert array.dense_actual_role is None


def test_strided_array_lowering_hands_over_one_descriptor_from_either_source():
    """A strided dummy is reached by a descriptor, whoever supplied the array.

    This is the direct-entrypoint answer for an assumed-shape dummy: a bind(C)
    procedure with no bridge receives a ``CFI_cdesc_t *``, and the extents and
    signed strides travel inside it. So the generated C describes a NumPy array
    into one and enters a handle's own, and the bridge dummy is the array
    itself -- there is nothing left to reconstruct on the Fortran side.
    """
    artifacts = WrapperGenerator().generate(_strided_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    # A handle is entered through its own descriptor entry point.
    assert (
        "prik_native_array_backend_for_actual(bound_values_capsule, 2, 2, "
        'CFI_type_double, sizeof(double), "float64", "values")'
    ) in c_source
    # A NumPy array has none, so one is built over its storage as it stands.
    assert "prik_describe_numpy_array((CFI_cdesc_t *)&bound_values_parent" in c_source
    assert "CFI_section(section, parent, lower, upper, step)" in c_source
    # Signed strides are what this layout accepts now.
    assert "NPY_FLOAT64, 2, 2, PRIK_ARRAY_LAYOUT_SIGNED_STRIDED_F, 0, 1" in c_source
    # One descriptor crosses, not an address with extents beside it.
    assert "double bind_c_strided(CFI_cdesc_t * values)" in c_source or (
        "void bind_c_strided(CFI_cdesc_t * values)" in c_source
    )
    assert "bound_values_dense_actual" not in c_source
    assert "bound_values_upper_bound_0" not in c_source

    assert "real(c_double), dimension(:, :) :: values" in bridge_source
    assert "call native_strided(values)" in bridge_source
    # Nothing is rebuilt from an address any more.
    assert "call c_f_pointer(" not in bridge_source
    assert "values_base" not in bridge_source
    assert "values_dense_actual" not in bridge_source
    assert max(map(len, bridge_source.splitlines())) <= 132


def test_descriptor_array_stride_role_edit_fails_before_backend_lowering():
    plan = _strided_plan()
    array = plan.namespaces[0].functions[0].arguments[0].array
    assert array is not None
    array.stride_roles = (f"{array.data_role}:stride:0",)

    with pytest.raises(ValueError, match="unexpected-array-descriptor-roles"):
        WrapperGenerator().generate(plan)


def test_descriptor_array_dense_actual_role_edit_fails_before_backend_lowering():
    plan = _strided_plan()
    array = plan.namespaces[0].functions[0].arguments[0].array
    assert array is not None
    array.dense_actual_role = f"{array.data_role}:dense-actual"

    with pytest.raises(ValueError, match="unexpected-array-descriptor-roles"):
        WrapperGenerator().generate(plan)
