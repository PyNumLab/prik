"""Positive-strided ordinary array view lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


def _strided_plan():
    module = parse_pyi_text(
        """
from x2py.contracts import Float64

def strided(values: Float64[::, ::]) -> None: ...
""",
        module_name="strided_arrays",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_strided_array_plan_names_bounds_and_element_strides_explicitly():
    argument = _strided_plan().namespaces[0].functions[0].arguments[0]
    array = argument.array

    assert array is not None
    assert array.rank == 2
    assert array.axes == ("strided", "strided")
    assert array.contiguous is False
    assert array.upper_bound_roles == (
        f"{argument.owner_path}:upper-bound:0",
        f"{argument.owner_path}:upper-bound:1",
    )
    assert array.stride_roles == (
        f"{argument.owner_path}:stride:0",
        f"{argument.owner_path}:stride:1",
    )


def test_strided_array_lowering_validates_and_passes_one_explicit_bridge_slice():
    artifacts = WrapperCodeGenerator().generate(_strided_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert '_native_array_actual_argument_for_binding_positional"' in c_source
    assert 'PyUnicode_FromString("F")' in c_source
    assert "bound_values_upper_bound_0" in c_source
    assert "bound_values_stride_1" in c_source
    assert "real(c_double), pointer, dimension(:, :) :: values_base" in bridge_source
    assert (
        "values_base(1:values_upper_bound_0 + 1:values_stride_0, 1:values_upper_bound_1 + 1:values_stride_1)"
    ) in bridge_source
    assert max(map(len, bridge_source.splitlines())) <= 132


def test_strided_role_edit_fails_before_backend_lowering():
    plan = _strided_plan()
    array = plan.namespaces[0].functions[0].arguments[0].array
    assert array is not None
    array.stride_roles = array.stride_roles[:1]

    with pytest.raises(ValueError, match="invalid-array-stride-roles"):
        WrapperCodeGenerator().generate(plan)
