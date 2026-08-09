"""Positive-strided ordinary array view lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.policy_completion import complete_semantic_policies
from prik.codegen import WrapperCodeGenerator, WrapperPlanner


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
    assert array.dense_actual_role == f"{argument.owner_path}:dense-actual"


def test_strided_array_lowering_validates_and_passes_one_explicit_bridge_slice():
    artifacts = WrapperCodeGenerator().generate(_strided_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert 'prik_array_actual_unpack(bound_values_obj, "float64", 2, bound_values_shape, "F"' in c_source
    assert "NPY_FLOAT64, 2, 2, PRIK_ARRAY_LAYOUT_POSITIVE_STRIDED_F, 0, 1" in c_source
    assert "bound_values_upper_bound_0 = bound_values_actual.upper_bounds[0]" in c_source
    assert "bound_values_stride_1 = bound_values_actual.strides[1]" in c_source
    assert "bound_values_upper_bound_0" in c_source
    assert "bound_values_stride_1" in c_source
    assert "int bound_values_dense_actual = 0;" in c_source
    assert "bound_values_dense_actual = PyArray_IS_F_CONTIGUOUS" in c_source
    assert "if (!bound_values_dense_actual) {" in c_source
    assert (
        "bind_c_strided(bound_values, bound_values_dense_actual, bound_values_extent_0, bound_values_extent_1,"
        in c_source
    )
    assert "integer(c_int), value :: values_dense_actual" in bridge_source
    assert "real(c_double), pointer, dimension(:, :) :: values_base" in bridge_source
    assert "real(c_double), pointer, dimension(:, :) :: values" in bridge_source
    assert "if (values_dense_actual /= 0_c_int) then" in bridge_source
    assert "values => values_base" in bridge_source
    assert (
        "values => values_base(1:values_upper_bound_0 + 1:values_stride_0, 1:values_upper_bound_1 + 1:values_stride_1)"
    ) in bridge_source
    assert "call native_strided(values)" in bridge_source
    assert max(map(len, bridge_source.splitlines())) <= 132


def test_rank3_strided_array_pointer_sections_respect_free_form_line_limit():
    artifacts = WrapperCodeGenerator().generate(_strided_plan(rank=3))
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "values => values_base(&" in bridge_source
    assert "& 1:values_upper_bound_2 + 1:values_stride_2)" in bridge_source
    assert max(map(len, bridge_source.splitlines())) <= 132


def test_strided_role_edit_fails_before_backend_lowering():
    plan = _strided_plan()
    array = plan.namespaces[0].functions[0].arguments[0].array
    assert array is not None
    array.stride_roles = array.stride_roles[:1]

    with pytest.raises(ValueError, match="invalid-array-stride-roles"):
        WrapperCodeGenerator().generate(plan)


def test_strided_dense_actual_role_edit_fails_before_backend_lowering():
    plan = _strided_plan()
    array = plan.namespaces[0].functions[0].arguments[0].array
    assert array is not None
    array.dense_actual_role = None

    with pytest.raises(ValueError, match="invalid-array-dense-actual-role"):
        WrapperCodeGenerator().generate(plan)
