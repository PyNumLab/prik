"""Declared extents, flat storage, dense rank, and order lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import (
    TransformationAction,
    TransformationLayer,
    WritebackPhase,
)
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


def _dense_plan():
    module = parse_pyi_text(
        """
from x2py.contracts import Annotated, Flat, Float64, Int32, ORDER_C, external

def dense_f(rows: Int32, cols: Int32, values: Float64[rows, cols]) -> None: ...
def dense_c(rows: Int32, cols: Int32, values: Annotated[Float64[rows, cols], ORDER_C]) -> None: ...
def flat(n: Int32, values: Float64[Flat]) -> None: ...

@external
def flat_rank2_runtime(values: Float64[:, Flat]) -> None: ...

@external
def flat_rank2_fixed(values: Float64[3, Flat]) -> None: ...

@external
def c_flat_rank2_runtime(values: Annotated[Float64[Flat, :], ORDER_C]) -> None: ...

@external
def c_flat_rank2_fixed(values: Annotated[Float64[Flat, 3], ORDER_C]) -> None: ...

@external
def bounded_flat(
    ldb: Int32,
    values: Float64[ldb, Flat],
) -> None: ...
""",
        module_name="dense_array_shapes",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _copy_f_plan():
    module = parse_pyi_text(
        """
from x2py.contracts import Annotated, COPY_F, Float64, ORDER_C

def transform(values: Annotated[Float64[2, 3], ORDER_C, COPY_F]) -> None: ...
""",
        module_name="copy_f_arrays",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _copy_f_lifecycle_plan():
    module = parse_pyi_text(
        """
from x2py.contracts import Annotated, COPY_F, Float64, ORDER_C, Returns

def native_input(values: Annotated[Float64[2, 3], ORDER_C, COPY_F]) -> None: ...

def projected(
    values: Annotated[Float64[2, 3], ORDER_C, COPY_F]
) -> Returns["values", Float64[2, 3]]: ...
""",
        module_name="copy_f_lifecycle",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _late_extent_external_plan():
    module = parse_pyi_text(
        """
from x2py.contracts import Annotated, Float64, Immutable, Int32, external

@external
def late_extent(values: Float64[n], n: Annotated[Int32, Immutable] | None = ...) -> None: ...
""",
        module_name="late_extent_external",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def test_dense_array_plan_records_extent_dependencies_flat_storage_and_order():
    functions = {function.binding.python_name: function for function in _dense_plan().namespaces[0].functions}
    dense_f = functions["dense_f"].arguments[-1].array
    dense_c = functions["dense_c"].arguments[-1].array
    flat = functions["flat"].arguments[-1].array
    flat_rank2_runtime = functions["flat_rank2_runtime"].arguments[-1].array
    flat_rank2_fixed = functions["flat_rank2_fixed"].arguments[-1].array
    c_flat_rank2_runtime = functions["c_flat_rank2_runtime"].arguments[-1].array
    c_flat_rank2_fixed = functions["c_flat_rank2_fixed"].arguments[-1].array
    bounded_flat = functions["bounded_flat"].arguments[-1].array

    assert dense_f is not None
    assert dense_f.rank == 2
    assert dense_f.shape == ("rows", "cols")
    assert dense_f.order == "ORDER_F"
    assert dense_f.extent_reference_roles == (
        ("dense_array_shapes.dense_f.rows:value",),
        ("dense_array_shapes.dense_f.cols:value",),
    )
    assert dense_c is not None
    assert dense_c.order == "ORDER_C"
    assert flat is not None
    assert flat.rank == 1
    assert flat.shape == (":",)
    assert flat.category == "assumed_size"
    assert flat.flatten_python_storage is True
    assert flat.flat_axis == 0
    assert flat_rank2_runtime is not None
    assert flat_rank2_runtime.rank == 2
    assert flat_rank2_runtime.shape == (":", ":")
    assert flat_rank2_runtime.order == "ORDER_F"
    assert flat_rank2_runtime.category == "assumed_size"
    assert flat_rank2_runtime.flatten_python_storage is True
    assert flat_rank2_runtime.flat_axis == 1
    assert flat_rank2_fixed is not None
    assert flat_rank2_fixed.rank == 2
    assert flat_rank2_fixed.shape == ("3", ":")
    assert flat_rank2_fixed.order == "ORDER_F"
    assert flat_rank2_fixed.flatten_python_storage is True
    assert flat_rank2_fixed.flat_axis == 1
    assert c_flat_rank2_runtime is not None
    assert c_flat_rank2_runtime.rank == 2
    assert c_flat_rank2_runtime.shape == (":", ":")
    assert c_flat_rank2_runtime.order == "ORDER_C"
    assert c_flat_rank2_runtime.category == "assumed_size"
    assert c_flat_rank2_runtime.flatten_python_storage is True
    assert c_flat_rank2_runtime.flat_axis == 0
    assert c_flat_rank2_fixed is not None
    assert c_flat_rank2_fixed.rank == 2
    assert c_flat_rank2_fixed.shape == (":", "3")
    assert c_flat_rank2_fixed.order == "ORDER_C"
    assert c_flat_rank2_fixed.flatten_python_storage is True
    assert c_flat_rank2_fixed.flat_axis == 0
    assert bounded_flat is not None
    assert bounded_flat.shape == ("ldb", ":")
    assert bounded_flat.flatten_python_storage is True
    assert bounded_flat.flat_axis == 1
    assert bounded_flat.extent_reference_roles == (("dense_array_shapes.bounded_flat.ldb:value",), ())


def test_dense_array_lowering_uses_planned_shape_checks_and_bridge_orientation():
    artifacts = WrapperCodeGenerator().generate(_dense_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "PyTuple_SET_ITEM(bound_values_shape, 0, PyLong_FromLongLong((long long)(bound_rows)))" in c_source
    assert "PyTuple_SET_ITEM(bound_values_shape, 1, PyLong_FromLongLong((long long)(bound_cols)))" in c_source
    assert 'bound_values_layout = PyUnicode_FromString("F")' in c_source
    assert 'bound_values_layout = PyUnicode_FromString("C")' in c_source
    assert '"_native_array_actual_argument_for_binding_positional"' in c_source
    assert "bound_values_shape = PyTuple_New(1)" in c_source
    assert "PyTuple_SET_ITEM(bound_values_shape, 0, Py_None)" in c_source
    assert (
        'PyObject_CallFunction(bound_values_helper, "OsiOOiiiiiiiii", bound_values_obj, "float64", 1, '
        "bound_values_shape, bound_values_layout, 1, 1, 1, 0, 0, 0, 1, 1, 0)"
    ) in c_source
    assert (
        'PyObject_CallFunction(bound_values_helper, "OsiOOiiiiiiiii", bound_values_obj, "float64", 2, '
        "bound_values_shape, bound_values_layout, 1, 1, 1, 0, 0, 0, 1, 1, 1)"
    ) in c_source
    assert "call c_f_pointer(bound_values, values, [values_extent_0, values_extent_1])" in bridge_source
    assert "call c_f_pointer(bound_values, values, [values_extent_1, values_extent_0])" in bridge_source
    assert "subroutine bind_c_flat(n, bound_values, values_extent_0)" in bridge_source
    assert "subroutine bind_c_flat_rank2_runtime(" in bridge_source
    assert "subroutine bind_c_c_flat_rank2_runtime(" in bridge_source
    assert "external :: flat_rank2_runtime" in bridge_source
    assert "external :: c_flat_rank2_fixed" in bridge_source
    assert "real(c_double), pointer, dimension(:, :) :: values" in bridge_source


def test_external_interface_declares_late_extent_before_dependent_array():
    artifacts = WrapperCodeGenerator().generate(_late_extent_external_plan())
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    signature = "subroutine late_extent(values, n)"
    interface = bridge_source.split(signature, maxsplit=1)[1].split("end subroutine late_extent", maxsplit=1)[0]
    assert interface.index("integer(c_int32_t), optional :: n") < interface.index(
        "real(c_double), dimension(n) :: values"
    )


def test_unavailable_dense_extent_role_fails_before_backend_lowering():
    plan = _dense_plan()
    array = plan.namespaces[0].functions[0].arguments[-1].array
    assert array is not None
    array.extent_reference_roles = (("edited.missing:value",), array.extent_reference_roles[1])

    with pytest.raises(ValueError, match="unavailable-array-extent-reference"):
        WrapperCodeGenerator().generate(plan)


def test_copy_f_is_one_binding_owned_transformation_lifecycle():
    argument = _copy_f_plan().namespaces[0].functions[0].arguments[0]

    assert argument.array is not None
    assert argument.array.order == "ORDER_C"
    assert argument.array.native_order == "ORDER_F"
    assert tuple(item.phase for item in argument.transformations) == (
        WritebackPhase.COPY_IN,
        WritebackPhase.COPY_OUT,
        WritebackPhase.CLEANUP,
    )
    assert {item.layer for item in argument.transformations} == {TransformationLayer.BINDING}
    assert tuple(item.action for item in argument.transformations) == (
        TransformationAction.COPY_ARRAY_REPRESENTATION,
        TransformationAction.COPY_ARRAY_REPRESENTATION,
        TransformationAction.RELEASE_TEMPORARY,
    )


def test_copy_f_lowering_keeps_numpy_copy_in_and_copy_out_out_of_the_bridge():
    artifacts = WrapperCodeGenerator().generate(_copy_f_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "!PyArray_IS_C_CONTIGUOUS((PyArrayObject *)bound_values_obj)" in c_source
    assert (
        "bound_values_representation = PyArray_NewCopy((PyArrayObject *)bound_values_obj, NPY_FORTRANORDER)" in c_source
    )
    assert "bound_values = PyArray_DATA((PyArrayObject *)bound_values_representation)" in c_source
    assert (
        "PyArray_CopyInto((PyArrayObject *)bound_values_obj, (PyArrayObject *)bound_values_representation) < 0"
        in c_source
    )
    assert "Py_XDECREF(bound_values_representation)" in c_source
    assert "call c_f_pointer(bound_values, values, [values_extent_0, values_extent_1])" in bridge_source
    assert "COPY_F" not in bridge_source


def test_copy_f_native_input_and_projected_identity_share_the_same_lifecycle_algorithm():
    functions = {
        function.binding.python_name: function for function in _copy_f_lifecycle_plan().namespaces[0].functions
    }
    native_input = functions["native_input"].arguments[0]
    projected = functions["projected"].arguments[0]

    assert tuple(item.phase for item in native_input.transformations) == (
        WritebackPhase.COPY_IN,
        WritebackPhase.COPY_OUT,
        WritebackPhase.CLEANUP,
    )
    assert tuple(item.phase for item in projected.transformations) == (
        WritebackPhase.COPY_IN,
        WritebackPhase.COPY_OUT,
        WritebackPhase.CLEANUP,
    )
    assert projected.projects_result is True

    artifacts = WrapperCodeGenerator().generate(_copy_f_lifecycle_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    native_input_body, projected_body = c_source.split("static PyObject * wrap_projected", maxsplit=1)
    assert "PyArray_NewCopy((PyArrayObject *)bound_values_obj, NPY_FORTRANORDER)" in native_input_body
    assert "PyArray_CopyInto((PyArrayObject *)bound_values_obj" in native_input_body
    assert "PyArray_CopyInto((PyArrayObject *)bound_values_obj" in projected_body
    assert "PyObject * result_obj = bound_values_obj" in projected_body
    assert "Py_INCREF(result_obj)" in projected_body
    assert "COPY_F" not in bridge_source


def test_copy_f_layer_edit_fails_central_validation():
    plan = _copy_f_plan()
    argument = plan.namespaces[0].functions[0].arguments[0]
    argument.transformations[0].layer = TransformationLayer.BRIDGE

    with pytest.raises(ValueError, match="invalid-transformation-layer"):
        WrapperCodeGenerator().generate(plan)
