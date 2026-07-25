from pathlib import Path

import pytest

from tests._shared.ownership_policy_support import parse_pyi_text
from tests.wrapper.fortran._support import wrapper_source
from x2py.parsers.fortran.parser import parse_fortran_project
from x2py.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from x2py.pipeline.preprocessing import PreprocessingConfig
from x2py.pipeline.pyi import pyi_file_to_semantic_module
from x2py.semantics.fortran2ir import fortran_project_to_semantic_modules
from x2py.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
    RESOLVED_MODULE_VARIABLE_POLICY_METADATA,
    RESOLVED_OWNERSHIP_POLICY_METADATA,
    RESOLVED_RUNTIME_STATUS_ERROR_POLICY_METADATA,
    SemanticFunction,
    SemanticType,
)
from x2py.semantics.ownership import (
    AssignmentMode,
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    ObjectKind,
    OwnershipOwner,
    PythonBarrierAction,
    SetterAction,
    StorageMode,
    TransferMode,
)
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import (
    RAW_STRING_ADDRESS_COPY_REASON,
    STRING_STORAGE_COPY_REASON,
    ArgumentHandoffMode,
    BridgeDataAction,
    CallbackABIKind,
    CallbackTransferAction,
    ExternalDeclarationMode,
    FunctionWrapperPolicy,
    ModuleGetterAction,
    ModuleVariablePolicy,
    NativeArrayDescriptorKind,
    NativeDescriptorHandoffABI,
    NativeStatusErrorPolicy,
    OptionalMode,
    PythonExceptionKind,
    WritebackPhase,
    completed_function_wrapper_policy,
)

FMATH_CONTRACT = Path("tests/wrapper/fortran/scalars/contracts/fmath/__init__.pyi")


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
    assert all(policy.writeback_actions == () for policy in policies)
    assert all(policy.cleanup_actions == () for policy in policies)
    assert all(policy.release_actions == () for policy in policies)


def test_optional_scalar_policy_completes_nullable_value_presence_before_planning():
    module = pyi_file_to_semantic_module(
        Path("tests/wrapper/fortran/function_calls/contracts/foptional_fixed/__init__.pyi"),
        module_name="foptional_fixed",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])

    assert policy.supported is True
    assert [argument.optional_mode for argument in policy.arguments] == [
        OptionalMode.REQUIRED,
        OptionalMode.NULLABLE_VALUE,
    ]
    assert policy.native_module is None
    assert policy.native_is_subroutine is False


def test_optional_descriptor_policy_completes_three_state_boundary_before_planning():
    module = parse_pyi_text(
        """
@native_call([Allocatable(Arg(0))])
def alloc_state(value: Annotated[Float64, Immutable] | None = ...) -> Int32: ...
""",
        module_name="scalar_optional_descriptors",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])
    value = policy.arguments[0]

    assert policy.supported is True
    assert value.optional_mode is OptionalMode.DESCRIPTOR
    assert value.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert value.bridge_copy_reason == "materialize owned Fortran allocatable scalar storage from the binding value"
    assert value.nullable is True
    assert value.descriptor_boundary is True
    assert policy.native_module == "scalar_optional_descriptors"


def test_optional_projected_array_keeps_nullable_value_separate_from_descriptor_storage():
    module = parse_pyi_text(
        """
@native_call([Addr(Arg(0)), Arg(1)])
def fill_optional(
    n: Int32,
    values: Float64[::] = ...,
) -> Returns["values", Float64[::]] | None: ...
""",
        module_name="optional_array_storage",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])
    values = policy.arguments[1]

    assert policy.supported is True
    assert values.optional_mode is OptionalMode.NULLABLE_VALUE
    assert values.nullable is True
    assert values.descriptor_boundary is False
    assert values.handoff_mode is ArgumentHandoffMode.ARRAY_BUFFER


def test_required_descriptor_policy_keeps_required_python_argument_nullable_at_native_boundary():
    module = parse_pyi_text(
        """
@native_call([Allocatable(Arg(0))])
def alloc_state(value: Float64 | None) -> Int32: ...
""",
        module_name="scalar_required_descriptors",
    )
    complete_semantic_policies(module)

    value = completed_function_wrapper_policy(module.functions[0]).arguments[0]

    assert value.optional is False
    assert value.optional_mode is OptionalMode.REQUIRED_DESCRIPTOR
    assert value.nullable is True
    assert value.descriptor_boundary is True
    assert value.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION


def test_scalar_copy_in_out_policy_completes_writeback_before_planning():
    module = parse_pyi_text(
        'def bump(value: Annotated[Int32, Immutable]) -> Returns["value", Int32]: ...',
        module_name="scalar_writeback",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])

    assert policy.supported is True
    assert policy.results == ()
    assert policy.native_is_subroutine is True
    assert tuple(action.phase for action in policy.writeback_actions) == tuple(WritebackPhase)
    assert {action.source_role for action in policy.writeback_actions} == {"scalar_writeback.bump.value:value"}
    assert {action.result_position for action in policy.writeback_actions} == {0}


def test_native_call_policy_maps_visible_positions_when_hidden_output_precedes_input():
    module = parse_pyi_text(
        """
@native_call([Return("status", 0), Addr(Arg(0))])
def mapped_status(base: Int32) -> Int32: ...
""",
        module_name="scalar_native_order",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])

    assert [(argument.name, argument.python_position, argument.native_position) for argument in policy.arguments] == [
        ("base", 0, 1)
    ]
    assert [(slot.owner_path, slot.source_kind, slot.native_position) for slot in policy.native_call_slots] == [
        ("scalar_native_order.mapped_status.status", "result", 0),
        ("scalar_native_order.mapped_status.base", "projection", 1),
    ]


def test_multiple_scalar_result_policy_completes_order_and_hidden_address_before_planning():
    module = parse_pyi_text(
        """
@native_call([Addr(Arg(0)), Return("status", 1)])
def with_scalar(n: Int32) -> tuple[Int32, Int32]: ...
""",
        module_name="multiple_scalar_results",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])

    assert policy.supported is True
    assert [(result.source_kind, result.result_position) for result in policy.results] == [
        ("direct_return", 0),
        ("hidden_output", 1),
    ]
    hidden = policy.results[1]
    assert hidden.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert policy.native_call_slots[1].owner_path == hidden.owner_path


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


def test_source_hidden_scalar_output_completes_call_local_address_before_planning():
    module = _source_semantic_module("foutputs_f90.f90", module_name="foutputs_f90")
    function = next(function for function in module.functions if function.name == "scalar_status")
    policy = completed_function_wrapper_policy(function)

    hidden = policy.results[0]
    assert hidden.source_kind == "hidden_output"
    assert hidden.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert policy.native_call_slots[1].native_barrier_action is hidden.native_barrier_action


def test_source_callback_value_default_and_explicit_reference_are_completed():
    module = _source_semantic_module("fcallback_all_f90.f90", module_name="fcallback_all_f90")
    function = next(item for item in module.functions if item.name == "apply_value_callback")
    policy = completed_function_wrapper_policy(function)
    transfer = policy.arguments[0].callback.arguments[0]

    assert transfer.abi is CallbackABIKind.VALUE
    assert transfer.passed_by_value is True
    assert transfer.adapter_action is CallbackTransferAction.COPY_IN

    array_function = next(item for item in module.functions if item.name == "apply_array_storage_callback")
    array_policy = completed_function_wrapper_policy(array_function)
    extent = array_policy.arguments[0].callback.arguments[0]
    assert extent.abi is CallbackABIKind.REFERENCE
    assert extent.passed_by_value is False
    assert extent.adapter_action is CallbackTransferAction.COPY_IN


@pytest.mark.parametrize(
    ("prototype", "blocker"),
    [
        (
            "def callback_shape(value: Allocatable[Float64]) -> None: ...",
            "callback argument 'value' uses unsupported allocatable, pointer, polymorphic, or assumed-type storage",
        ),
        (
            "def callback_shape(value: Float64 = ...) -> None: ...",
            "callback argument 'value' cannot be optional",
        ),
        (
            "def callback_shape() -> Pointer[Float64]: ...",
            "callback result uses unsupported allocatable, pointer, polymorphic, or assumed-type storage",
        ),
    ],
)
def test_callback_descriptor_and_optional_forms_are_blocked_before_codegen(prototype: str, blocker: str):
    module = parse_pyi_text(
        f"""
@prototype
{prototype}

def apply(callback: callback_shape) -> None: ...
""",
        module_name="unsupported_callback_shape",
    )

    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is False
    assert blocker in policy.blockers


def test_external_declaration_mode_is_completed_from_native_abi_requirements():
    module = parse_pyi_text(
        """
@external
def classic(n: Int32, values: Float64[n]) -> Float64: ...

@external
def optional(value: Annotated[Float64, Immutable] | None = ...) -> None: ...
""",
        module_name="external_modes",
    )
    complete_semantic_policies(module)

    classic = completed_function_wrapper_policy(module.functions[0])
    optional = completed_function_wrapper_policy(module.functions[1])
    assert classic.external_declaration is ExternalDeclarationMode.IMPLICIT_EXTERNAL
    assert optional.external_declaration is ExternalDeclarationMode.EXPLICIT_INTERFACE


def test_hidden_scalar_descriptor_result_keeps_descriptor_policy_instead_of_plain_address_storage():
    module = parse_pyi_text(
        """
@native_call([Allocatable(Return("value", 0))])
def create_allocatable() -> Float64 | None: ...
""",
        module_name="descriptor_result",
    )
    function = module.functions[0]
    result_argument = function.arguments[0]

    complete_semantic_policies(module)

    decision = result_argument.metadata[RESOLVED_OWNERSHIP_POLICY_METADATA]
    assert function.projection[0].value_kind == "allocatable"
    assert result_argument.semantic_type.storage is None
    assert decision.descriptor_boundary is True
    assert decision.native_barrier_action is NativeBarrierAction.PASS_VALUE


def test_direct_allocatable_scalar_function_result_is_blocked_before_codegen():
    module = parse_pyi_text(
        """
@native_call([Arg(0)], result=Allocatable(Return(0)))
def maybe_allocatable(flag: Int32) -> Float64 | None: ...
""",
        module_name="direct_descriptor_result",
    )

    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is False
    assert (
        "direct allocatable scalar function results cannot preserve unallocated state; "
        "use an allocatable hidden output projection"
    ) in policy.blockers


def test_direct_high_rank_allocatable_function_result_is_supported_before_codegen():
    module = parse_pyi_text(
        """
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def make_matrix(n: Int32, m: Int32) -> Allocatable[Float64[:, :]]: ...
""",
        module_name="direct_allocatable_matrix_result",
    )

    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is True
    assert policy.blockers == ()
    result = policy.results[0]
    assert result.rank == 2
    assert result.native_array_handle is not None
    assert result.native_array_handle.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
    assert result.native_array_handle.handoff.abi is NativeDescriptorHandoffABI.OWNED_RESULT_STORAGE


def test_source_fmath_scalar_policy_accepts_storage_address_native_action():
    module = _source_semantic_module("fmath.f", module_name="fmath")
    function = next(item for item in module.functions if item.name == "ADD_R8")
    policies = [item.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA] for item in module.functions]

    policy = function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is True
    assert policy.blockers == ()
    assert [(export.namespace, export.name) for export in policy.python_exports] == [((), "add_r8")]
    assert policy.native_name == "ADD_R8"
    assert policy.external is True
    assert [argument.name for argument in policy.arguments] == ["X", "Y"]
    assert [argument.codegen_action for argument in policy.arguments] == [
        CodegenAction.IN_PLACE_ARGUMENT,
        CodegenAction.IN_PLACE_ARGUMENT,
    ]
    assert [argument.python_barrier_action for argument in policy.arguments] == [
        PythonBarrierAction.SCALAR_VALUE,
        PythonBarrierAction.SCALAR_VALUE,
    ]
    assert [argument.native_barrier_action for argument in policy.arguments] == [
        NativeBarrierAction.PASS_STORAGE_ADDRESS,
        NativeBarrierAction.PASS_STORAGE_ADDRESS,
    ]
    assert [argument.storage_mode for argument in policy.arguments] == [StorageMode.STACK, StorageMode.STACK]
    assert all(policy.writeback_actions == () for policy in policies)
    assert all(policy.cleanup_actions == () for policy in policies)
    assert all(policy.release_actions == () for policy in policies)
    assert [
        (slot.source_kind, slot.value_kind, slot.native_barrier_action, slot.codegen_action)
        for slot in policy.native_call_slots
    ] == [
        (
            "projection",
            "arg",
            NativeBarrierAction.PASS_STORAGE_ADDRESS,
            CodegenAction.IN_PLACE_ARGUMENT,
        ),
        (
            "projection",
            "arg",
            NativeBarrierAction.PASS_STORAGE_ADDRESS,
            CodegenAction.IN_PLACE_ARGUMENT,
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
    assert policy.external is True

    assert [argument.name for argument in policy.arguments] == ["X", "Y"]
    assert [argument.python_position for argument in policy.arguments] == [0, 1]
    assert [argument.native_position for argument in policy.arguments] == [0, 1]
    for argument in policy.arguments:
        assert argument.semantic_type_name == "Float64"
        assert argument.rank == 0
        assert argument.optional is False
        assert argument.ownership.kind is ObjectKind.SCALAR
        assert argument.codegen_action is CodegenAction.CALL_LOCAL_INPUT
        assert argument.python_barrier_action is PythonBarrierAction.SCALAR_VALUE
        assert argument.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
        assert argument.storage_mode is StorageMode.ALIAS
        assert argument.boundary_storage_mode is StorageMode.ALIAS
        assert argument.projects_result is False
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
@hold_gil
@bind("SWAP_ARGS")
@external
@native_call([Addr(Arg(1)), Addr(Arg(0))])
def swap_args(x: Float64, y: Float64) -> Float64: ...
""",
        module_name="runtime_policy",
    )
    complete_semantic_policies(module)

    policy = completed_function_wrapper_policy(module.functions[0])

    assert policy.hold_gil is True
    assert policy.external is True
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
@native_call([Addr(Arg(0)), Return("status", 0), Return("message", 1)])
def solve(value: Int32) -> tuple[Int32, String[32]]: ...
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

    assert policy.hold_gil is False
    assert [argument.native_position for argument in policy.arguments] == [0, 1]
    assert [(slot.source_kind, slot.native_position, slot.python_position) for slot in policy.native_call_slots] == [
        ("implicit", 0, 0),
        ("implicit", 1, 1),
    ]


def test_scalar_module_variable_policy_completes_access_and_storage_before_planning():
    module = parse_pyi_text(
        """
limit: Final[Int32] = 12
counter: Int32 = 3
target_scale: Annotated[Float64, Aliased]
optional_scale: Allocatable[Float64]
selected_scale: Pointer[Float64]
""",
        module_name="scalar_state",
    )
    complete_semantic_policies(module)

    policies = {
        variable.name: variable.metadata[RESOLVED_MODULE_VARIABLE_POLICY_METADATA] for variable in module.variables
    }

    assert all(isinstance(policy, ModuleVariablePolicy) for policy in policies.values())
    assert all(policy.supported for policy in policies.values())
    assert policies["limit"].getter_action is ModuleGetterAction.CONSTANT_VALUE
    assert policies["limit"].setter_action is SetterAction.OMIT
    assert policies["limit"].native_assignment is AssignmentMode.NONE
    assert policies["limit"].constant_value == 12
    assert policies["counter"].getter_action is ModuleGetterAction.DIRECT_VALUE
    assert policies["counter"].setter_action is SetterAction.WRITE_THROUGH
    assert policies["counter"].native_assignment is AssignmentMode.VALUE_COPY
    assert policies["counter"].initializer == 3
    assert policies["target_scale"].getter_action is ModuleGetterAction.DIRECT_VALUE
    assert policies["target_scale"].setter_action is SetterAction.WRITE_THROUGH
    assert policies["target_scale"].native_assignment is AssignmentMode.VALUE_COPY
    assert policies["optional_scale"].getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT
    assert policies["optional_scale"].descriptor_kind == "allocatable"
    assert policies["optional_scale"].setter_action is SetterAction.REJECT_REPLACEMENT
    assert policies["optional_scale"].native_assignment is AssignmentMode.NONE
    assert policies["selected_scale"].getter_action is ModuleGetterAction.NULLABLE_SNAPSHOT
    assert policies["selected_scale"].descriptor_kind == "pointer"
    assert policies["selected_scale"].setter_action is SetterAction.REJECT_REPLACEMENT
    assert policies["selected_scale"].native_assignment is AssignmentMode.NONE


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
from x2py.contracts import Annotated, Flat, Float64, Int32, ORDER_C

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


def test_wrapper_policy_completes_required_raw_array_address_handoff():
    module = parse_pyi_text(
        """
def raw_values(n: Int32[()], values: Addr(Float64[n])) -> None: ...
def raw_matrix(n: Int32, m: Int32, values: Addr(Float64[n, m])) -> None: ...
def raw_labels(n: Int32, labels: Addr(String[8][n])) -> None: ...
""",
        module_name="raw_array_arguments",
    )
    complete_semantic_policies(module)
    policies = {
        function.name: function.metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA] for function in module.functions
    }

    assert all(policy.supported for policy in policies.values())
    values = policies["raw_values"].arguments[1]
    assert values.ownership.kind is ObjectKind.NUMPY_ARRAY
    assert values.python_barrier_action is PythonBarrierAction.RAW_ADDRESS
    assert values.native_barrier_action is NativeBarrierAction.PASS_RAW_ADDRESS
    assert values.handoff_mode is ArgumentHandoffMode.OPAQUE_ADDRESS
    assert values.bridge_data_action is BridgeDataAction.ASSOCIATE_VIEW
    assert values.bridge_copy_reason is None
    assert values.array is not None
    assert values.array.rank == 1
    assert values.array.shape == ("n",)
    assert values.array.axes == ("dense",)
    assert values.array.category == "raw_address"
    assert values.array.contiguous is True
    assert values.array.extent_references == (("n",),)
    assert policies["raw_values"].native_call_slots[1].array == values.array

    matrix = policies["raw_matrix"].arguments[2]
    assert matrix.array is not None
    assert matrix.array.order == "ORDER_F"
    assert matrix.array.shape == ("n", "m")

    labels = policies["raw_labels"].arguments[1]
    assert labels.ownership.kind is ObjectKind.NUMPY_ARRAY
    assert labels.character_length == 8
    assert labels.array is not None
    assert labels.array.itemsize == 8


def test_wrapper_policy_keeps_optional_raw_array_addresses_blocked():
    module = parse_pyi_text(
        "def optional_raw(n: Int32, values: Addr(Float64[n]) = ...) -> None: ...",
        module_name="optional_raw_array",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert "argument 'values' optional raw array addresses are not supported" in policy.blockers


def test_wrapper_policy_keeps_projected_raw_array_addresses_blocked():
    module = parse_pyi_text(
        'def projected_raw(n: Int32, values: Addr(Float64[n])) -> Returns["values", Float64[n]]: ...',
        module_name="projected_raw_array",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert "argument 'values' raw array address cannot project a Python result" in policy.blockers


def test_wrapper_policy_completes_required_read_only_string_value_handoff():
    module = parse_pyi_text(
        "def consume(value: String) -> None: ...",
        module_name="string_argument",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is True
    assert policy.blockers == ()
    argument = policy.arguments[0]
    assert argument.python_barrier_action is PythonBarrierAction.STRING_VALUE
    assert argument.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert argument.codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert argument.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER
    assert argument.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert argument.bridge_copy_reason == ("materialize Fortran character storage from the binding UTF-8 byte buffer")


def test_wrapper_policy_completes_fixed_string_direct_and_hidden_copy_results():
    module = parse_pyi_text(
        """
def direct_label() -> String[8]: ...

@native_call([Return("label", 0)])
def hidden_label() -> String[8]: ...
""",
        module_name="fixed_string_results",
    )
    complete_semantic_policies(module)
    direct_policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    hidden_policy = module.functions[1].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert direct_policy.supported is True
    direct = direct_policy.results[0]
    assert direct.ownership.kind is ObjectKind.STRING
    assert direct.codegen_action is CodegenAction.COPY_OUT
    assert direct.native_barrier_action is NativeBarrierAction.NONE
    assert direct.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert direct.character_length == 8

    assert hidden_policy.supported is True
    hidden = hidden_policy.results[0]
    assert hidden.ownership.kind is ObjectKind.STRING
    assert hidden.codegen_action is CodegenAction.COPY_OUT
    assert hidden.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert hidden.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert hidden.character_length == 8
    assert hidden_policy.native_call_slots[0].character_length == hidden.character_length


def test_wrapper_policy_completes_fixed_string_replacement_and_discarded_identity():
    module = parse_pyi_text(
        """
def replace_name(name: String[8]) -> Returns["name", String[8]]: ...
def discard_name(name: String[8]) -> None: ...
""",
        module_name="fixed_string_writeback",
    )
    complete_semantic_policies(module)
    replacement = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    identity = module.functions[1].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert replacement.supported is True
    argument = replacement.arguments[0]
    assert argument.ownership.kind is ObjectKind.STRING
    assert argument.ownership.owner is OwnershipOwner.PYTHON
    assert argument.ownership.transfer is TransferMode.COPY_RETURN
    assert argument.ownership.destruction is DestructionPolicy.PYTHON_REFCOUNT
    assert argument.codegen_action is CodegenAction.COPY_IN_OUT
    assert argument.character_length == 8
    assert argument.projects_result is True
    # The native call mutates a binding-owned replacement, not the immutable
    # Python string supplied at the public boundary.
    assert argument.writable is False
    assert tuple(action.phase for action in replacement.writeback_actions) == tuple(WritebackPhase)

    assert identity.supported is True
    assert identity.arguments[0].codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert identity.arguments[0].projects_result is False
    assert identity.writeback_actions == ()


def test_wrapper_policy_completes_assumed_optional_replacements_and_blocks_unreleased_status_cleanup():
    module = parse_pyi_text(
        """
def assumed(name: String) -> Returns["name", String]: ...
def optional(label: String = ...) -> Returns["label", String] | None: ...
def optional_fixed(label: String[8] = ...) -> Returns["label", String[8]] | None: ...
def optional_identity(label: String = ...) -> None: ...

@raises(status="status", success=0)
@native_call([Arg(0), Return("status", 1)])
def with_status(
    name: String[8]
) -> tuple[Returns["name", String[8]], Returns["status", Int32]]: ...
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


def test_wrapper_policy_completes_fixed_string_storage_and_raw_address_ownership():
    module = parse_pyi_text(
        """
def storage(label: String[8][()]) -> None: ...
def raw(label: Addr(String[8])) -> None: ...
""",
        module_name="fixed_string_addresses",
    )
    complete_semantic_policies(module)
    storage = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    raw = module.functions[1].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert storage.supported is True
    storage_argument = storage.arguments[0]
    assert storage_argument.ownership.kind is ObjectKind.STRING
    assert storage_argument.ownership.owner is OwnershipOwner.CALLER
    assert storage_argument.ownership.transfer is TransferMode.IN_PLACE
    assert storage_argument.ownership.destruction is DestructionPolicy.CALLER
    assert storage_argument.storage_mode is StorageMode.ALIAS
    assert storage_argument.boundary_storage_mode is StorageMode.ALIAS
    assert storage_argument.codegen_action is CodegenAction.IN_PLACE_ARGUMENT
    assert storage_argument.python_barrier_action is PythonBarrierAction.STRING_STORAGE
    assert storage_argument.native_barrier_action is NativeBarrierAction.PASS_STORAGE_ADDRESS
    assert storage_argument.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert storage_argument.bridge_copy_reason == STRING_STORAGE_COPY_REASON
    assert storage_argument.character_length == 8
    assert storage.writeback_actions == ()

    assert raw.supported is True
    raw_argument = raw.arguments[0]
    assert raw_argument.ownership.kind is ObjectKind.STRING
    assert raw_argument.ownership.owner is OwnershipOwner.CALLER
    assert raw_argument.ownership.transfer is TransferMode.IN_PLACE
    assert raw_argument.ownership.destruction is DestructionPolicy.CALLER
    assert raw_argument.storage_mode is StorageMode.STACK
    assert raw_argument.boundary_storage_mode is StorageMode.STACK
    assert raw_argument.codegen_action is CodegenAction.IN_PLACE_ARGUMENT
    assert raw_argument.python_barrier_action is PythonBarrierAction.RAW_ADDRESS
    assert raw_argument.native_barrier_action is NativeBarrierAction.PASS_RAW_ADDRESS
    assert raw_argument.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert raw_argument.bridge_copy_reason == RAW_STRING_ADDRESS_COPY_REASON
    assert raw_argument.character_length == 8
    assert raw.writeback_actions == ()


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
