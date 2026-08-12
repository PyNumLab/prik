from pathlib import Path


from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.wrapper_build import wrapper_source
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from prik.pipeline.preprocessing import PreprocessingConfig
from prik.pipeline.pyi import pyi_file_to_semantic_module
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    ArgumentHandoffMode,
    BridgeDataAction,
    FunctionWrapperPolicy,
    OptionalMode,
)
from prik.policy.construction import completed_function_wrapper_policy

FMATH_CONTRACT = Path("tests/fortran/data_types/end_to_end/fixtures/baseline/contracts/fmath/__init__.pyi")


def _source_semantic_module(filename: str, *, module_name: str):
    source = wrapper_source(filename)
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


def test_optional_scalar_policy_completes_nullable_value_presence_before_planning():
    module = pyi_file_to_semantic_module(
        Path(__file__).parents[1] / "end_to_end" / "fixtures" / "contracts" / "foptional_fixed" / "__init__.pyi",
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


def test_optional_passed_procedure_is_blocked_before_codegen():
    module = parse_pyi_text(
        """
@prototype
def callback_shape(value: Float64 = ...) -> None: ...

def apply(callback: callback_shape) -> None: ...
""",
        module_name="unsupported_optional_callback",
    )

    complete_semantic_policies(module)

    policy = module.functions[0].metadata[RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA]
    assert isinstance(policy, FunctionWrapperPolicy)
    assert policy.supported is False
    assert "callback argument 'value' cannot be optional" in policy.blockers
