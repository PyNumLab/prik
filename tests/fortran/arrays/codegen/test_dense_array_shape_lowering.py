"""Declared extents, flat storage, dense rank, and order lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    TransformationLayer,
)
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


def _dense_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Annotated, Flat, Float64, Int32, ORDER_C, standalone

def dense_f(rows: Int32, cols: Int32, values: Float64[rows, cols]) -> None: ...
def dense_c(rows: Int32, cols: Int32, values: Annotated[Float64[rows, cols], ORDER_C]) -> None: ...
def flat(n: Int32, values: Float64[Flat]) -> None: ...

@standalone
def flat_rank2_runtime(values: Float64[:, Flat]) -> None: ...

@standalone
def flat_rank2_fixed(values: Float64[3, Flat]) -> None: ...

@standalone
def c_flat_rank2_runtime(values: Annotated[Float64[Flat, :], ORDER_C]) -> None: ...

@standalone
def c_flat_rank2_fixed(values: Annotated[Float64[Flat, 3], ORDER_C]) -> None: ...

@standalone
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
from prik.contracts import Annotated, COPY_F, Float64, ORDER_C

def transform(values: Annotated[Float64[2, 3], ORDER_C, COPY_F]) -> None: ...
""",
        module_name="copy_f_arrays",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _copy_f_status_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Annotated, Arg, COPY_F, Float64, Hidden, Int32, ORDER_C, Returns, native_call, raises

@raises(status="status", success=0)
@native_call([Arg(0), Hidden("status", Int32)])
def transform_status(
    values: Annotated[Float64[2, 3], ORDER_C, COPY_F]
) -> Returns["status", Int32]: ...
""",
        module_name="copy_f_status",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _late_extent_external_plan():
    module = parse_pyi_text(
        """
from prik.contracts import Annotated, Float64, Immutable, Int32, standalone

@standalone
def late_extent(values: Float64[n], n: Annotated[Int32, Immutable] | None = ...) -> None: ...
""",
        module_name="late_extent_external",
    )
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


@pytest.mark.parametrize(
    ("name", "shape", "order", "flat_axis"),
    [
        pytest.param("flat_rank2_runtime", (":", ":"), "ORDER_F", 1, id="fortran-flat-last-axis-open-prefix"),
        pytest.param("flat_rank2_fixed", ("3", ":"), "ORDER_F", 1, id="fortran-flat-last-axis-fixed-prefix"),
        pytest.param("c_flat_rank2_runtime", (":", ":"), "ORDER_C", 0, id="c-flat-first-axis-open-suffix"),
        pytest.param("c_flat_rank2_fixed", (":", "3"), "ORDER_C", 0, id="c-flat-first-axis-fixed-suffix"),
    ],
)
def test_dense_array_plan_places_flat_storage_by_order(name, shape, order, flat_axis):
    """The flat axis is the slowest-varying one for the declared order.

    Runtime tests cover rank-one and argument-sized Fortran-order flat storage;
    the C-order placements and fixed-extent neighbours are only decided here.
    """
    functions = {function.binding.python_name: function for function in _dense_plan().namespaces[0].functions}
    array = functions[name].arguments[-1].array

    assert array.shape == shape
    assert array.order == order
    assert array.category == "assumed_size"
    assert array.flatten_python_storage is True
    assert array.flat_axis == flat_axis


def test_external_interface_declares_late_extent_before_dependent_array():
    plan = _late_extent_external_plan()
    function = plan.namespaces[0].functions[0]
    artifacts = WrapperGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert function.binding.argument_conversion_order == (
        "late_extent_external.late_extent.n",
        "late_extent_external.late_extent.values",
    )
    assert c_source.index("prik_int32_or_storage(bound_n_obj, ") < c_source.index(
        "bound_values_bind_fixed[0] = (long long)(bound_n);"
    )
    signature = "subroutine late_extent(values, n)"
    interface = bridge_source.split(signature, maxsplit=1)[1].split("end subroutine late_extent", maxsplit=1)[0]
    assert interface.index("integer(c_int32_t), optional :: n") < interface.index(
        "real(c_double), dimension(n) :: values"
    )


def test_edited_binding_conversion_order_cannot_read_an_extent_late():
    plan = _late_extent_external_plan()
    function = plan.namespaces[0].functions[0]
    function.binding.argument_conversion_order = tuple(reversed(function.binding.argument_conversion_order))

    with pytest.raises(ValueError, match="late-binding-extent-conversion"):
        WrapperGenerator().generate(plan)


def test_unavailable_dense_extent_role_fails_before_backend_lowering():
    plan = _dense_plan()
    array = plan.namespaces[0].functions[0].arguments[-1].array
    assert array is not None
    array.extent_reference_roles = (("edited.missing:value",), array.extent_reference_roles[1])

    with pytest.raises(ValueError, match="unavailable-array-extent-reference"):
        WrapperGenerator().generate(plan)


def test_copy_f_status_cleanup_clears_the_released_temporary_before_error_cleanup():
    artifacts = WrapperGenerator().generate(_copy_f_status_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    function_body = c_source[c_source.index("static PyObject * wrap_transform_status") :]

    copyback = function_body.index("PyArray_CopyInto")
    success_release = function_body.index("Py_CLEAR(bound_values_representation)", copyback)
    status_check = function_body.index("if (status != 0)", success_release)
    error_release = function_body.index("Py_CLEAR(bound_values_representation)", status_check)
    assert copyback < success_release < status_check < error_release


def test_copy_f_layer_edit_fails_central_validation():
    plan = _copy_f_plan()
    argument = plan.namespaces[0].functions[0].arguments[0]
    argument.transformations[0].layer = TransformationLayer.BRIDGE

    with pytest.raises(ValueError, match="invalid-transformation-layer"):
        WrapperGenerator().generate(plan)
