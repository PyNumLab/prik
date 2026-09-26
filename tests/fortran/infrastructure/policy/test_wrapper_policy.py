from pathlib import Path

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.wrapper_build import wrapper_source
from prik.planning import WrapperPlanner
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.preprocessing import PreprocessingConfig, read_fortran_source
from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
    RESOLVED_RUNTIME_STATUS_ERROR_POLICY_METADATA,
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
    BridgeDataAction,
    ExternalDeclarationMode,
    NativeStatusErrorPolicy,
    OptionalMode,
    PythonExceptionKind,
)
from prik.policy.construction import completed_function_wrapper_policy

FMATH_CONTRACT = Path("tests/fortran/data_types/end_to_end/fixtures/contracts/fmath/__init__.pyi")


def _source_semantic_module(filename: str, *, module_name: str):
    source = wrapper_source(filename)
    parsed = parse_fortran_project({str(source): read_fortran_source(source, PreprocessingConfig()).source})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


@pytest.mark.parametrize(
    ("lane", "native_name", "slot_value_kind"),
    [
        pytest.param("source", "ADD_R8", "arg", id="fortran_source"),
        # The contract states no separate native name: `add_r8` reaches
        # Fortran's `ADD_R8`, which is named without regard to case.
        pytest.param("contract", "add_r8", "addr", id="pyi_contract"),
    ],
)
def test_fmath_scalar_replacements_complete_one_policy_from_source_and_contract(lane, native_name, slot_value_kind):
    if lane == "source":
        module = _source_semantic_module("fmath.f", module_name="fmath")
    else:
        module = pyi_file_to_semantic_module(FMATH_CONTRACT, module_name="fmath")
        complete_semantic_policies(module)
    policies = {function.name.casefold(): completed_function_wrapper_policy(function) for function in module.functions}

    # Every conservative scalar replacement is supported and needs no cleanup.
    for policy in policies.values():
        assert policy.supported is True
        assert policy.blockers == ()
        assert policy.writeback_actions
        assert policy.cleanup_actions == ()
        assert policy.release_actions == ()
        assert all(argument.conversion_phase is ArgumentConversionPhase.IMMEDIATE for argument in policy.arguments)

    policy = policies["add_r8"]
    assert policy.owner_path.casefold() == "fmath.add_r8"
    assert [(export.namespace, export.name) for export in policy.python_exports] == [((), "add_r8")]
    assert policy.native_name == native_name
    assert policy.standalone is True
    assert [
        (
            argument.name,
            argument.python_position,
            argument.native_position,
            argument.codegen_action,
            argument.python_barrier_action,
            argument.native_barrier_action,
            argument.storage_mode,
        )
        for argument in policy.arguments
    ] == [
        (
            name,
            position,
            position,
            CodegenAction.COPY_IN_OUT,
            PythonBarrierAction.SCALAR_VALUE,
            NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
            StorageMode.STACK,
        )
        for position, name in enumerate(("X", "Y"))
    ]
    assert [
        (
            slot.source_kind,
            slot.value_kind,
            slot.native_position,
            slot.python_position,
            slot.native_barrier_action,
            slot.codegen_action,
        )
        for slot in policy.native_call_slots
    ] == [
        (
            "projection",
            slot_value_kind,
            position,
            position,
            NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS,
            CodegenAction.COPY_IN_OUT,
        )
        for position in (0, 1)
    ]
    [result] = policy.results
    assert result.codegen_action is CodegenAction.DIRECT_VALUE
    assert result.storage_mode is StorageMode.STACK


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


def test_wrapper_policy_records_runtime_and_native_order_metadata():
    module = parse_pyi_text(
        """
@nogil
@bind("SWAP_ARGS")
@standalone
@native_call([Addr(Arg(1)), Addr(Arg(0))])
def swap_args(x: Float64, y: Float64) -> Float64: ...

def add(x: Float64, y: Float64) -> Float64: ...
""",
        module_name="runtime_policy",
    )
    complete_semantic_policies(module)

    policy, implicit = (completed_function_wrapper_policy(function) for function in module.functions)

    assert policy.release_gil is True
    assert policy.standalone is True
    assert [argument.python_position for argument in policy.arguments] == [0, 1]
    assert [argument.native_position for argument in policy.arguments] == [1, 0]
    assert [(slot.native_position, slot.python_position, slot.value_kind) for slot in policy.native_call_slots] == [
        (0, 1, "addr"),
        (1, 0, "addr"),
    ]
    # Without a native_call, Python order is the native order.
    assert implicit.release_gil is False
    assert [argument.native_position for argument in implicit.arguments] == [0, 1]
    assert [(slot.source_kind, slot.native_position, slot.python_position) for slot in implicit.native_call_slots] == [
        ("implicit", 0, 0),
        ("implicit", 1, 1),
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


@pytest.mark.parametrize(
    ("slot_spelling", "slot_type", "blocker"),
    [
        pytest.param("Int32(Arg(0).shape[0])", "Int32", None, id="stated_integer_type"),
        pytest.param("Arg(0).shape[0]", "SizeT", None, id="unstated_type_defaults_to_size_t"),
        pytest.param("Float64(Arg(0).shape[0])", None, "cannot be materialized as 'Float64'", id="non_integer_type"),
        pytest.param("Int(Arg(0).shape[0])", None, "cannot be materialized as 'Int'", id="unresolved_int"),
        pytest.param("UInt(Arg(0).shape[0])", None, "cannot be materialized as 'UInt'", id="unresolved_uint"),
    ],
)
def test_wrapper_policy_types_or_blocks_a_computed_shape_projection(slot_spelling, slot_type, blocker):
    module = parse_pyi_text(
        f"""
@native_call([{slot_spelling}, Arg(0)])
def scale(values: Float64[:]) -> None: ...
""",
        module_name="computed_extent",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    if blocker is None:
        assert policy.supported is True
        assert policy.native_call_slots[0].semantic_type_name == slot_type
    else:
        assert policy.supported is False
        assert f"native-call shape slot 0 {blocker}" in policy.blockers


def test_wrapper_policy_completes_a_one_character_hidden_literal():
    module = parse_pyi_text(
        """
@native_call([Arg(0), String[1]("N")])
def tagged(x: Float64) -> Float64: ...
""",
        module_name="hidden_string_literal",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is True
    slot = policy.native_call_slots[1]
    assert (slot.literal_type, slot.literal_value) == ("String[1]", "N")
    assert (slot.semantic_type_name, slot.character_length) == ("String", 1)
    assert slot.object_kind is None


@pytest.mark.parametrize(
    ("literal", "blocker"),
    [
        pytest.param('String[4]("NOPE")', "uses unsupported first-lane literal type 'String[4]'", id="multi_character"),
        pytest.param(
            'String[1]("")', "declares String[1] but its value must contain exactly one character", id="empty"
        ),
        pytest.param(
            'String[1]("NO")', "declares String[1] but its value must contain exactly one character", id="two"
        ),
        pytest.param("String[1](1)", "declares String[1] but its value is not a string", id="not_a_string"),
        pytest.param(
            'String[1]("🎉")', "declares String[1] but its value is not representable as one C char byte", id="non_byte"
        ),
    ],
)
def test_wrapper_policy_blocks_an_invalid_character_hidden_literal(literal, blocker):
    module = parse_pyi_text(
        f"""
@native_call([Arg(0), {literal}])
def tagged(x: Float64) -> Float64: ...
""",
        module_name="invalid_character_literal",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]

    assert policy.supported is False
    assert f"native-call literal slot 1 {blocker}" in policy.blockers


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


def test_completed_function_policy_rejects_unimplemented_runtime_constraints():
    module = parse_pyi_text(
        "def solve(value: Annotated[Int32, Bounded(1, 8), Finite]) -> Int32: ...\n",
        module_name="constrained",
    )
    complete_semantic_policies(module)

    with pytest.raises(ValueError, match="no runtime validators for semantic constraints"):
        WrapperPlanner().build(module)
