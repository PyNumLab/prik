from pathlib import Path


from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _fortran_source_for_pipeline, _merge_wrapper_modules
from prik.preprocessing import PreprocessingConfig
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from prik.policy.ownership import (
    NativeBarrierAction,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.construction import (
    completed_function_wrapper_policy,
)

FMATH_CONTRACT = Path("tests/fortran/data_types/end_to_end/fixtures/baseline/contracts/fmath/__init__.pyi")


CALLS_NATIVE = Path(__file__).parents[2] / "pyi_contracts" / "calls_and_results" / "end_to_end" / "fixtures" / "native"


def _source_semantic_module(filename: str, *, module_name: str):
    source = CALLS_NATIVE / filename
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return module


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


def test_source_hidden_scalar_output_completes_call_local_address_before_planning():
    module = _source_semantic_module("foutputs_f90.f90", module_name="foutputs_f90")
    function = next(function for function in module.functions if function.name == "scalar_status")
    policy = completed_function_wrapper_policy(function)

    hidden = policy.results[0]
    assert hidden.source_kind == "hidden_output"
    assert hidden.native_barrier_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
    assert policy.native_call_slots[1].native_barrier_action is hidden.native_barrier_action
