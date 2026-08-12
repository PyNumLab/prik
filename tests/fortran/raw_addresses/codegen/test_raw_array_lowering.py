"""Direct-plan raw array address policy, validation, and lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.ownership import (
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    ObjectKind,
    OwnershipOwner,
    PythonBarrierAction,
    StorageMode,
    TransferMode,
)
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy_models import ArgumentHandoffMode, BridgeDataAction
from prik.codegen import WrapperCodeGenerator, WrapperPlanner
from prik.codegen.plan import DatatypeFamily


def _raw_array_module():
    module = parse_pyi_text(
        """
def raw_vector(n: Int32[()], values: Addr(Float64[n])) -> None: ...
def raw_matrix_c(n: Int32, m: Int32, values: Annotated[Addr(Float64[n, m]), ORDER_C]) -> None: ...
def raw_matrix_f(
    n: Int32,
    m: Int32,
    values: Addr(Float64[n, m])
) -> None: ...
def raw_labels(n: Int32, labels: Addr(String[8][n])) -> None: ...
def raw_literal(values: Addr(Float64[4])) -> None: ...
def raw_expression(n: Int32, values: Addr(Float64[n + 1])) -> None: ...
def raw_zero_extent(values: Addr(Float64[0])) -> None: ...
def raw_negative_extent(values: Addr(Float64[-1])) -> None: ...
@native_call([Addr(Arg(1)), Arg(0)])
def raw_reordered(values: Addr(Float64[4]), n: Int32) -> None: ...
""",
        module_name="raw_array_addresses",
    )
    complete_semantic_policies(module)
    return module


def _raw_array_plan():
    return WrapperPlanner().build(_raw_array_module())


def _functions(plan):
    return {function.binding.python_name: function for function in plan.namespaces[0].functions}


def test_raw_array_addresses_use_one_shared_transfer_and_shape_plan():
    module = _raw_array_module()
    function = _functions(WrapperPlanner().build(module))["raw_vector"]
    argument = function.arguments[1]
    assert argument.native_call_slot is function.native_call_slots[argument.native_position]
    assert argument.array is argument.native_call_slot.array
    assert argument.object_kind is ObjectKind.NUMPY_ARRAY
    assert argument.ownership_owner is OwnershipOwner.CALLER
    assert argument.transfer_mode is TransferMode.IN_PLACE
    assert argument.destruction_policy is DestructionPolicy.CALLER
    assert argument.storage_mode is StorageMode.STACK
    assert argument.boundary_storage_mode is StorageMode.STACK
    assert argument.datatype_family is DatatypeFamily.REAL
    assert argument.binding.python_action is PythonBarrierAction.RAW_ADDRESS
    assert argument.binding.codegen_action is CodegenAction.IN_PLACE_ARGUMENT
    assert argument.bridge.native_action is NativeBarrierAction.PASS_RAW_ADDRESS
    assert argument.bridge.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
    assert argument.bridge.data_action is BridgeDataAction.ASSOCIATE_VIEW
    assert argument.bridge.copy_reason is None

    assert argument.array is not None
    assert argument.array.rank == 1
    assert argument.array.shape == ("n",)
    assert argument.array.axes == ("dense",)
    assert argument.array.contiguous is True
    assert argument.array.category == "raw_address"
    assert argument.array.data_role == argument.binding.handoff_role
    assert argument.array.extent_reference_roles == (("raw_array_addresses.raw_vector.n:value",),)
    assert argument.array.extent_roles == ()
    assert argument.array.upper_bound_roles == ()
    assert argument.array.stride_roles == ()
    assert argument.array.runtime_rank_role is None
    assert argument.array.itemsize_role is None


def test_raw_array_addresses_reuse_integer_extraction_and_named_array_bridge_association():
    artifacts = WrapperCodeGenerator().generate(_raw_array_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "void bind_c_raw_vector(void * n, void * values);" in c_source
    assert "if (!PyLong_Check(bound_values_obj))" in c_source
    assert "bound_values = PyLong_AsVoidPtr(bound_values_obj);" in c_source
    assert "if (bound_values == NULL && PyErr_Occurred()) return NULL;" in c_source
    assert "bind_c_raw_vector(bound_n, bound_values);" in c_source
    assert "bound_values_extent" not in c_source
    assert "PyArray_Check(bound_values_obj)" not in c_source

    assert "real(c_double), pointer, dimension(:) :: values" in bridge_source
    assert "call c_f_pointer(bound_values, values, [n])" in bridge_source
    assert "call native_raw_vector(n, values)" in bridge_source
    assert "call c_f_pointer(bound_values, values, [m, n])" in bridge_source
    assert "call c_f_pointer(bound_values, values, [n, m])" in bridge_source
    assert "character(kind=c_char, len=8), pointer, dimension(:) :: labels" in bridge_source
    assert "call c_f_pointer(bound_labels, labels, [n])" in bridge_source
    assert "call c_f_pointer(bound_values, values, [4])" in bridge_source
    assert "call c_f_pointer(bound_values, values, [n + 1])" in bridge_source
    assert "call c_f_pointer(bound_values, values, [0])" in bridge_source
    assert "call c_f_pointer(bound_values, values, [-1])" in bridge_source
    assert "call native_raw_reordered(n, values)" in bridge_source
    assert "values_extent_0" not in bridge_source


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("object-kind", "unexpected-scalar-array-handoff"),
        ("python-action", "invalid-array-python-action"),
        ("native-action", "invalid-raw-array-native-action"),
        ("handoff", "invalid-raw-array-handoff-mode"),
        ("data-action", "invalid-raw-array-data-action"),
        ("rank", "invalid-raw-array-rank"),
        ("shape", "inconsistent-raw-array-rank"),
        ("category", "invalid-raw-array-category"),
        ("orientation", "invalid-raw-array-order"),
        ("buffer-role", "unexpected-raw-array-buffer-roles"),
        ("shape-role", "unavailable-array-extent-reference"),
        ("element-family", "Unsupported first-lane scalar type"),
        ("character-length", "invalid-raw-character-array-itemsize"),
        ("slot-identity", "inconsistent-function-native-slot"),
    ],
)
def test_raw_array_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _raw_array_plan()
    function = _functions(plan)["raw_vector"]
    argument = function.arguments[1]
    if edit == "character-length":
        function = _functions(plan)["raw_labels"]
        argument = function.arguments[1]
    assert argument.array is not None
    if edit == "object-kind":
        argument.object_kind = ObjectKind.SCALAR
    elif edit == "python-action":
        argument.binding.python_action = PythonBarrierAction.STRING_VALUE
    elif edit == "native-action":
        argument.bridge.native_action = NativeBarrierAction.PASS_ARRAY_BUFFER
        argument.native_call_slot.native_action = NativeBarrierAction.PASS_ARRAY_BUFFER
    elif edit == "handoff":
        argument.bridge.handoff_mode = ArgumentHandoffMode.ARRAY_BUFFER
    elif edit == "data-action":
        argument.bridge.data_action = BridgeDataAction.DIRECT_TRANSFER
        argument.native_call_slot.bridge_data_action = BridgeDataAction.DIRECT_TRANSFER
    elif edit == "rank":
        argument.array.rank = 0
    elif edit == "shape":
        argument.array.shape = ()
    elif edit == "category":
        argument.array.category = "explicit"
    elif edit == "orientation":
        argument.array.order = "ORDER_X"
    elif edit == "buffer-role":
        argument.array.extent_roles = ("edited:extent:0",)
    elif edit == "shape-role":
        argument.array.extent_reference_roles = (("edited.missing:value",),)
    elif edit == "element-family":
        argument.semantic_type_name = "UInt8"
    elif edit == "character-length":
        argument.array.itemsize = None
    else:
        argument.native_call_slot = function.native_call_slots[0]

    with pytest.raises(ValueError, match=diagnostic):
        WrapperCodeGenerator().generate(plan)
