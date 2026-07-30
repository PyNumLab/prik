from pathlib import Path


from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.wrapper_build import wrapper_source
from x2py.parsers.fortran.parser import parse_fortran_project
from x2py.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from x2py.pipeline.preprocessing import PreprocessingConfig
from x2py.semantics.fortran2ir import fortran_project_to_semantic_modules
from x2py.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
)
from x2py.semantics.ownership import (
    CodegenAction,
    DestructionPolicy,
    NativeBarrierAction,
    ObjectKind,
    OwnershipOwner,
    PythonBarrierAction,
    StorageMode,
    TransferMode,
)
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import (
    RAW_STRING_ADDRESS_COPY_REASON,
    STRING_STORAGE_COPY_REASON,
    ArgumentHandoffMode,
    BridgeDataAction,
)

FMATH_CONTRACT = Path("tests/fortran/data_types/end_to_end/fixtures/baseline/contracts/fmath/__init__.pyi")


def _source_semantic_module(filename: str, *, module_name: str):
    source = wrapper_source(filename)
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


def test_wrapper_policy_completes_primitive_raw_address_handoff():
    module = parse_pyi_text(
        "def update(value: Addr(Float64)) -> None: ...",
        module_name="primitive_raw_address",
    )
    complete_semantic_policies(module)
    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    argument = policy.arguments[0]

    assert argument.python_barrier_action is PythonBarrierAction.RAW_ADDRESS
    assert argument.native_barrier_action is NativeBarrierAction.PASS_RAW_ADDRESS
    assert argument.ownership.owner is OwnershipOwner.CALLER
    assert argument.ownership.transfer is TransferMode.IN_PLACE
    assert argument.ownership.destruction is DestructionPolicy.CALLER


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
