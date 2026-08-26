from pathlib import Path


from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.wrapper_build import wrapper_source
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from prik.preprocessing import PreprocessingConfig
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.models import (
    RESOLVED_FUNCTION_WRAPPER_POLICY_METADATA,
    RESOLVED_OWNERSHIP_POLICY_METADATA,
)
from prik.policy.ownership import (
    NativeBarrierAction,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    FunctionWrapperPolicy,
    NativeArrayDescriptorKind,
    NativeDescriptorHandoffABI,
)

FMATH_CONTRACT = Path("tests/fortran/data_types/end_to_end/fixtures/contracts/fmath/__init__.pyi")


def _source_semantic_module(filename: str, *, module_name: str):
    source = wrapper_source(filename)
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


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
