from pathlib import Path


from tests.fortran._support.ownership_policy import parse_pyi_text
from tests.fortran._support.wrapper_build import wrapper_source
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from prik.pipeline.preprocessing import PreprocessingConfig
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.semantics.ownership import (
    NativeBarrierAction,
)
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy import (
    ArgumentConversionPhase,
    WritebackPhase,
    completed_function_wrapper_policy,
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
    assert policy.arguments[0].conversion_phase is ArgumentConversionPhase.IMMEDIATE
    assert tuple(action.phase for action in policy.writeback_actions) == tuple(WritebackPhase)
    assert {action.source_role for action in policy.writeback_actions} == {"scalar_writeback.bump.value:value"}
    assert {action.result_position for action in policy.writeback_actions} == {0}


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
