from pathlib import Path

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.wrapper_build import wrapper_source
from prik.planning import WrapperPlanner
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from prik.preprocessing import PreprocessingConfig
from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
    RESOLVED_RUNTIME_STATUS_ERROR_POLICY_METADATA,
    SemanticFunction,
    SemanticType,
)
from prik.policy.ownership import (
    CodegenAction,
    NativeBarrierAction,
    ObjectKind,
    PythonBarrierAction,
    StorageMode,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    ArgumentConversionPhase,
    ArgumentHandoffMode,
    BridgeDataAction,
    ExternalDeclarationMode,
    FunctionWrapperPolicy,
    NativeStatusErrorPolicy,
    OptionalMode,
    PythonExceptionKind,
)
from prik.policy.construction import build_function_wrapper_policy, completed_function_wrapper_policy

FMATH_CONTRACT = Path("tests/fortran/data_types/end_to_end/fixtures/baseline/contracts/fmath/__init__.pyi")


def _source_semantic_module(filename: str, *, module_name: str):
    source = wrapper_source(filename)
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


def test_fmath_fixture_gets_completed_function_wrapper_policy():
    module = pyi_file_to_semantic_module(FMATH_CONTRACT, module_name="fmath")

    complete_semantic_policies(module)

    policies = [function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA] for function in module.functions]
    assert policies
    assert all(isinstance(policy, FunctionWrapperPolicy) for policy in policies)
    assert all(policy.supported for policy in policies)
    assert all(policy.blockers == () for policy in policies)
    assert all(policy.writeback_actions for policy in policies)
    assert all(
        argument.conversion_phase is ArgumentConversionPhase.IMMEDIATE
        for policy in policies
        for argument in policy.arguments
    )
    assert all(policy.cleanup_actions == () for policy in policies)
    assert all(policy.release_actions == () for policy in policies)


def test_rank_zero_scalar_storage_results_complete_as_numpy_array_policies():
    module = parse_pyi_text(
        """
def direct_storage_result() -> Float64[()]: ...

@native_call([Return("out", 0)])
def hidden_storage_result() -> Float64[()]: ...
""",
        module_name="rank_zero_storage_results",
    )
    complete_semantic_policies(module)

    policies = {function.name: completed_function_wrapper_policy(function) for function in module.functions}
    direct_policy = policies["direct_storage_result"]
    hidden_policy = policies["hidden_storage_result"]
    direct = direct_policy.results[0]
    hidden = hidden_policy.results[0]

    assert direct_policy.supported is True
    assert hidden_policy.supported is True
    assert direct.ownership.kind is ObjectKind.NUMPY_ARRAY
    assert direct.array.rank == 0
    assert direct.array.category == "scalar_storage"
    assert direct.codegen_action is CodegenAction.COPY_OUT
    assert direct.native_barrier_action is NativeBarrierAction.NONE
    assert direct.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert hidden.ownership.kind is ObjectKind.NUMPY_ARRAY
    assert hidden.array.rank == 0
    assert hidden.array.category == "scalar_storage"
    assert hidden.codegen_action is CodegenAction.COPY_OUT
    assert hidden.native_barrier_action is NativeBarrierAction.PASS_STORAGE_ADDRESS
    assert hidden.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert hidden_policy.native_call_slots[0].result_position == hidden.result_position
    assert hidden_policy.native_call_slots[0].native_barrier_action is hidden.native_barrier_action


def test_hidden_result_policy_reports_a_missing_return_projection_after_selection():
    module = parse_pyi_text(
        """
@native_call([Return("status", 0)])
def hidden_status() -> Int32: ...
""",
        module_name="missing_hidden_projection",
    )
    complete_semantic_policies(module)
    function = module.functions[0]

    # Preserve the completed hidden-output ownership decision while removing
    # its result mapping to characterize the candidate builder's fail-closed path.
    function.projection = []
    policy = build_function_wrapper_policy(
        function,
        owner_path="missing_hidden_projection.hidden_status",
    )

    assert policy.results == ()
    assert "hidden result 'status' has no completed return projection" in policy.blockers


def test_hidden_result_policy_keeps_blocked_bridge_action_on_the_candidate():
    module = parse_pyi_text(
        """
@native_call([Return("message", 0)])
def hidden_message() -> String: ...
""",
        module_name="blocked_hidden_bridge",
    )
    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.results[0].bridge_data_action is BridgeDataAction.BLOCKED
    assert "hidden result 'message' has no completed bridge data action" in policy.blockers


def test_external_declaration_mode_is_completed_from_native_abi_requirements():
    module = parse_pyi_text(
        """
@standalone
def classic(n: Int32, values: Float64[n]) -> Float64: ...

@standalone
def optional(value: Annotated[Float64, Immutable] | None = ...) -> None: ...
""",
        module_name="external_modes",
    )
    complete_semantic_policies(module)

    classic = completed_function_wrapper_policy(module.functions[0])
    optional = completed_function_wrapper_policy(module.functions[1])
    assert classic.external_declaration is ExternalDeclarationMode.IMPLICIT_EXTERNAL
    assert optional.external_declaration is ExternalDeclarationMode.EXPLICIT_INTERFACE


def test_source_fmath_scalar_policy_projects_conservative_replacements():
    module = _source_semantic_module("fmath.f", module_name="fmath")
    function = next(item for item in module.functions if item.name == "ADD_R8")
    policies = [item.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA] for item in module.functions]

    policy = function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is True
    assert policy.blockers == ()
    assert [(export.namespace, export.name) for export in policy.python_exports] == [((), "add_r8")]
    assert policy.native_name == "ADD_R8"
    assert policy.standalone is True
    assert [argument.name for argument in policy.arguments] == ["X", "Y"]
    assert [argument.codegen_action for argument in policy.arguments] == [
        CodegenAction.COPY_IN_OUT,
        CodegenAction.COPY_IN_OUT,
    ]
    assert all(argument.conversion_phase is ArgumentConversionPhase.IMMEDIATE for argument in policy.arguments)
    assert [argument.python_barrier_action for argument in policy.arguments] == [
        PythonBarrierAction.SCALAR_VALUE,
        PythonBarrierAction.SCALAR_VALUE,
    ]
    assert [argument.native_barrier_action for argument in policy.arguments] == [
        NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
        NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
    ]
    assert [argument.storage_mode for argument in policy.arguments] == [StorageMode.STACK, StorageMode.STACK]
    assert all(policy.writeback_actions for policy in policies)
    assert all(policy.cleanup_actions == () for policy in policies)
    assert all(policy.release_actions == () for policy in policies)
    assert [
        (slot.source_kind, slot.value_kind, slot.native_barrier_action, slot.codegen_action)
        for slot in policy.native_call_slots
    ] == [
        (
            "projection",
            "arg",
            NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
            CodegenAction.COPY_IN_OUT,
        ),
        (
            "projection",
            "arg",
            NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
            CodegenAction.COPY_IN_OUT,
        ),
    ]


def test_source_export_policy_resolves_names_inside_each_namespace():
    module = _source_semantic_module("fnaming_f90.f90", module_name="fnaming_f90")
    policies = {
        function.name: function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
        for function in module.functions
        if function.visibility == "public"
    }

    assert [(export.namespace, export.name) for export in policies["lambda"].python_exports] == [
        (("fnaming_f90",), "lambda_")
    ]
    assert [(export.namespace, export.name) for export in policies["lambda_"].python_exports] == [
        (("fnaming_f90",), "lambda__2")
    ]
    assert all(
        function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA].python_exports == ()
        for function in module.functions
        if function.visibility == "private"
    )


def test_fmath_scalar_policy_records_address_projected_call_slots():
    module = pyi_file_to_semantic_module(FMATH_CONTRACT, module_name="fmath")
    complete_semantic_policies(module)
    function = next(item for item in module.functions if item.name == "add_r8")

    policy = completed_function_wrapper_policy(function)

    assert policy.owner_path == "fmath.add_r8"
    assert [(export.namespace, export.name) for export in policy.python_exports] == [((), "add_r8")]
    assert policy.native_name == "ADD_R8"
    assert policy.standalone is True

    assert [argument.name for argument in policy.arguments] == ["X", "Y"]
    assert [argument.python_position for argument in policy.arguments] == [0, 1]
    assert [argument.native_position for argument in policy.arguments] == [0, 1]
    for argument in policy.arguments:
        assert argument.semantic_type_name == "Float64"
        assert argument.rank == 0
        assert argument.optional is False
        assert argument.ownership.kind is ObjectKind.SCALAR
        assert argument.codegen_action is CodegenAction.COPY_IN_OUT
        assert argument.conversion_phase is ArgumentConversionPhase.IMMEDIATE
        assert argument.python_barrier_action is PythonBarrierAction.SCALAR_VALUE
        assert argument.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
        assert argument.storage_mode is StorageMode.STACK
        assert argument.boundary_storage_mode is StorageMode.STACK
        assert argument.projects_result is True
        assert argument.python_visible is True

    assert [(slot.native_position, slot.python_position) for slot in policy.native_call_slots] == [
        (0, 0),
        (1, 1),
    ]
    assert [slot.source_kind for slot in policy.native_call_slots] == ["projection", "projection"]
    assert [slot.value_kind for slot in policy.native_call_slots] == ["addr", "addr"]
    assert [slot.native_name for slot in policy.native_call_slots] == ["X", "Y"]
    assert all(
        slot.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS for slot in policy.native_call_slots
    )

    assert len(policy.results) == 1
    result = policy.results[0]
    assert result.owner_path == "fmath.add_r8.return"
    assert result.semantic_type_name == "Float64"
    assert result.rank == 0
    assert result.ownership.kind is ObjectKind.SCALAR
    assert result.codegen_action is CodegenAction.DIRECT_VALUE
    assert result.python_barrier_action is PythonBarrierAction.NONE
    assert result.native_barrier_action is NativeBarrierAction.NONE
    assert result.storage_mode is StorageMode.STACK
    assert result.boundary_storage_mode is StorageMode.STACK


def test_wrapper_policy_records_runtime_and_native_order_metadata():
    module = parse_pyi_text(
        """
@nogil
@bind("SWAP_ARGS")
@standalone
@native_call([Addr(Arg(1)), Addr(Arg(0))])
def swap_args(x: Float64, y: Float64) -> Float64: ...
""",
        module_name="runtime_policy",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])

    assert policy.release_gil is True
    assert policy.standalone is True
    assert [argument.python_position for argument in policy.arguments] == [0, 1]
    assert [argument.native_position for argument in policy.arguments] == [1, 0]
    assert [(slot.native_position, slot.python_position, slot.value_kind) for slot in policy.native_call_slots] == [
        (0, 1, "addr"),
        (1, 0, "addr"),
    ]


def test_runtime_status_policy_is_completed_before_wrapper_planning():
    module = parse_pyi_text(
        """
@raises(status="status", message="message", success=0)
@native_call([Addr(Arg(0)), Hidden("status", Int32), Hidden("message", String[32])])
def solve(value: Int32) -> None: ...
""",
        module_name="runtime_status",
    )

    complete_semantic_policies(module)

    function = module.functions[0]
    status_error = function.metadata[RESOLVED_RUNTIME_STATUS_ERROR_POLICY_METADATA]
    policy = completed_function_wrapper_policy(function)
    assert isinstance(status_error, NativeStatusErrorPolicy)
    assert policy.status_error is status_error
    assert status_error.success == 0
    assert status_error.exception_kind is PythonExceptionKind.RUNTIME_ERROR
    assert status_error.status.owner_path == "runtime_status.solve.status"
    assert status_error.status.native_position == 1
    assert status_error.status.semantic_type_name == "Int32"
    assert status_error.message is not None
    assert status_error.message.owner_path == "runtime_status.solve.message"
    assert status_error.message.native_position == 2
    assert status_error.message.semantic_type_name == "String"
    assert status_error.message.character_length == 32
    assert policy.results == ()
    assert [slot.semantic_type_name for slot in policy.native_call_slots] == ["Int32", "Int32", "String"]
    assert [slot.character_length for slot in policy.native_call_slots] == [None, None, 32]


def test_wrapper_policy_records_implicit_native_order():
    module = parse_pyi_text(
        """
def add(x: Float64, y: Float64) -> Float64: ...
""",
        module_name="implicit_order",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])

    assert policy.release_gil is False
    assert [argument.native_position for argument in policy.arguments] == [0, 1]
    assert [(slot.source_kind, slot.native_position, slot.python_position) for slot in policy.native_call_slots] == [
        ("implicit", 0, 0),
        ("implicit", 1, 1),
    ]


def test_wrapper_policy_records_primitive_hidden_literals():
    module = parse_pyi_text(
        """
@native_call([Arg(0), Int32(1), Float64(0.5), Bool(False)])
def scale(x: Float64) -> Float64: ...
""",
        module_name="hidden_literals",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])

    assert [argument.native_position for argument in policy.arguments] == [0]
    assert [
        (
            slot.owner_path,
            slot.native_position,
            slot.source_kind,
            slot.python_position,
            slot.value_kind,
            slot.literal_type,
            slot.literal_value,
            slot.native_barrier_action,
            slot.codegen_action,
        )
        for slot in policy.native_call_slots
    ] == [
        (
            "hidden_literals.scale.x",
            0,
            "projection",
            0,
            "arg",
            None,
            None,
            NativeBarrierAction.PASS_VALUE,
            CodegenAction.CALL_LOCAL_INPUT,
        ),
        (
            "hidden_literals.scale.native_slot_1",
            1,
            "literal",
            None,
            "literal",
            "Int32",
            1,
            NativeBarrierAction.PASS_VALUE,
            CodegenAction.DIRECT_VALUE,
        ),
        (
            "hidden_literals.scale.native_slot_2",
            2,
            "literal",
            None,
            "literal",
            "Float64",
            0.5,
            NativeBarrierAction.PASS_VALUE,
            CodegenAction.DIRECT_VALUE,
        ),
        (
            "hidden_literals.scale.native_slot_3",
            3,
            "literal",
            None,
            "literal",
            "Bool",
            False,
            NativeBarrierAction.PASS_VALUE,
            CodegenAction.DIRECT_VALUE,
        ),
    ]


def test_wrapper_policy_blocks_non_primitive_hidden_literals():
    module = parse_pyi_text(
        """
@native_call([Arg(0), String[1]("N")])
def tagged(x: Float64) -> Float64: ...
""",
        module_name="hidden_string_literal",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert "native-call literal slot 1 uses unsupported first-lane literal type 'String[1]'" in policy.blockers


def test_wrapper_policy_completes_required_rank_one_array_buffer_handoff():
    module = parse_pyi_text(
        """
def sum_values(values: Float64[:]) -> Float64: ...
""",
        module_name="array_argument",
    )
    complete_semantic_policies(module)
    function = module.functions[0]
    policy = function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is True
    assert policy.blockers == ()
    argument = policy.arguments[0]
    assert argument.ownership.kind is ObjectKind.NUMPY_ARRAY
    assert argument.python_barrier_action is PythonBarrierAction.ARRAY_STORAGE
    assert argument.native_barrier_action is NativeBarrierAction.PASS_ARRAY_BUFFER
    assert argument.bridge_data_action is BridgeDataAction.ASSOCIATE_VIEW
    assert argument.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER
    assert argument.array is not None
    assert argument.array.rank == 1
    assert argument.array.shape == (":",)
    assert argument.array.axes == ("dense",)
    assert argument.array.contiguous is True
    assert policy.native_call_slots[0].array == argument.array


def test_wrapper_policy_flattens_python_rank_for_rank_one_assumed_size_storage():
    module = parse_pyi_text(
        """
def sum_flat(n: Int32, values: Float64[Flat]) -> Float64: ...
""",
        module_name="flat_array_argument",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    argument = policy.arguments[1]
    assert argument.array is not None
    assert argument.array.rank == 1
    assert argument.array.shape == (":",)
    assert argument.array.category == "assumed_size"
    assert argument.array.flatten_python_storage is True
    assert argument.array.flat_axis == 0
    assert argument.native_array_actual is not None
    assert argument.native_array_actual.rank == 1
    assert argument.native_array_actual.shape == (":",)
    assert argument.native_array_actual.flatten_storage is True
    assert argument.native_array_actual.flat_axis == 0
    assert policy.native_call_slots[1].array == argument.array


def test_wrapper_policy_flattens_remaining_axes_for_multidimensional_assumed_size_storage():
    module = parse_pyi_text(
        """
from prik.contracts import Annotated, Flat, Float64, Int32, ORDER_C

def sum_fortran(rows: Int32, values: Float64[rows, Flat]) -> Float64: ...
def sum_c(columns: Int32, values: Annotated[Float64[Flat, columns], ORDER_C]) -> Float64: ...
""",
        module_name="flat_matrix_argument",
    )
    complete_semantic_policies(module)
    policies = {
        function.name: function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA] for function in module.functions
    }

    fortran_argument = policies["sum_fortran"].arguments[1]
    assert fortran_argument.array is not None
    assert fortran_argument.array.rank == 2
    assert fortran_argument.array.shape == ("rows", ":")
    assert fortran_argument.array.order == "ORDER_F"
    assert fortran_argument.array.category == "assumed_size"
    assert fortran_argument.array.flatten_python_storage is True
    assert fortran_argument.array.flat_axis == 1
    assert fortran_argument.native_array_actual is not None
    assert fortran_argument.native_array_actual.rank == 2
    assert fortran_argument.native_array_actual.shape == ("rows", ":")
    assert fortran_argument.native_array_actual.flatten_storage is True
    assert fortran_argument.native_array_actual.flat_axis == 1

    c_argument = policies["sum_c"].arguments[1]
    assert c_argument.array is not None
    assert c_argument.array.rank == 2
    assert c_argument.array.shape == (":", "columns")
    assert c_argument.array.order == "ORDER_C"
    assert c_argument.array.category == "assumed_size"
    assert c_argument.array.flatten_python_storage is True
    assert c_argument.array.flat_axis == 0
    assert c_argument.native_array_actual is not None
    assert c_argument.native_array_actual.rank == 2
    assert c_argument.native_array_actual.shape == (":", "columns")
    assert c_argument.native_array_actual.flatten_storage is True
    assert c_argument.native_array_actual.flat_axis == 0


def test_wrapper_policy_completes_assumed_optional_replacements_and_blocks_unreleased_status_cleanup():
    module = parse_pyi_text(
        """
def assumed(name: String) -> Returns["name", String]: ...
def optional(label: String = ...) -> Returns["label", String] | None: ...
def optional_fixed(label: String[8] = ...) -> Returns["label", String[8]] | None: ...
def optional_identity(label: String = ...) -> None: ...

@raises(status="status", success=0)
@native_call([Arg(0), Hidden("status", Int32)])
def with_status(
    name: String[8]
) -> Returns["name", String[8]]: ...
""",
        module_name="blocked_string_writeback",
    )
    complete_semantic_policies(module)
    assumed = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    optional = module.functions[1].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    optional_fixed = module.functions[2].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    optional_identity = module.functions[3].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    with_status = module.functions[4].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert assumed.supported is True
    assert assumed.arguments[0].character_length is None
    assert assumed.arguments[0].codegen_action is CodegenAction.COPY_IN_OUT
    assert optional.supported is True
    assert optional.arguments[0].optional_mode is OptionalMode.NULLABLE_VALUE
    assert optional.arguments[0].nullable is True
    assert optional.arguments[0].character_length is None
    assert optional_fixed.supported is True
    assert optional_fixed.arguments[0].character_length == 8
    assert optional_identity.supported is True
    assert optional_identity.arguments[0].optional_mode is OptionalMode.NULLABLE_VALUE
    assert optional_identity.arguments[0].codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert optional_identity.writeback_actions == ()
    assert with_status.supported is False
    assert "string replacement with native status error requires planned failure-path cleanup" in (with_status.blockers)


def test_wrapper_policy_blocks_optional_or_projected_string_address_forms():
    module = parse_pyi_text(
        """
def optional_storage(label: String[8][()] = ...) -> None: ...
def optional_raw(label: Addr(String[8]) = ...) -> None: ...
def projected_storage(label: String[8][()]) -> Returns["label", String[8][()]]: ...
def projected_raw(label: Addr(String[8])) -> Returns["label", String[8]]: ...
""",
        module_name="blocked_string_addresses",
    )
    complete_semantic_policies(module)
    policies = [function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA] for function in module.functions]

    assert all(policy.supported is False for policy in policies)
    assert "optional string storage is unsupported" in "; ".join(policies[0].blockers)
    assert "optional raw string address is unsupported" in "; ".join(policies[1].blockers)
    assert "string storage unexpectedly projects a result" in "; ".join(policies[2].blockers)
    assert "raw string address unexpectedly projects a result" in "; ".join(policies[3].blockers)


def test_missing_wrapper_policy_fails_before_planning():
    function = SemanticFunction(
        name="add",
        arguments=[],
        return_type=SemanticType(name="Float64", dtype="Float64"),
    )

    with pytest.raises(ValueError, match="missing completed wrapper policy"):
        completed_function_wrapper_policy(function)


def test_completed_function_policy_rejects_unimplemented_runtime_constraints():
    module = parse_pyi_text(
        "def solve(value: Annotated[Int32, Bounded(1, 8), Finite]) -> Int32: ...\n",
        module_name="constrained",
    )
    complete_semantic_policies(module)

    with pytest.raises(ValueError, match="no runtime validators for semantic constraints"):
        WrapperPlanner().build(module)
