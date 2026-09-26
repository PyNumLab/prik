"""Plan validation for scalar string-value handoffs and deferred-length updates.

Runtime behavior of every lane is proved end to end in
``tests/fortran/strings/end_to_end/``; these checks keep the validator that
stops an incomplete plan before lowering.
"""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import ArgumentHandoffMode, BridgeDataAction
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("missing-length", "missing-string-length-handoff"),
        ("wrong-handoff", "invalid-string-handoff"),
        ("wrong-copy", "invalid-string-data-action"),
    ],
)
def test_string_handoff_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    module = parse_pyi_text("def fixed(text: String[8]) -> Int32: ...", module_name="string_inputs")
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    argument = plan.namespaces[0].functions[0].arguments[0]
    if edit == "missing-length":
        argument.entrypoint.length_handoff_role = None
    elif edit == "wrong-handoff":
        argument.entrypoint.handoff_mode = ArgumentHandoffMode.TYPED_REFERENCE
    else:
        argument.bridge.data_action = BridgeDataAction.DIRECT_TRANSFER
        argument.projected_call_slot.adapter.bridge_data_action = BridgeDataAction.DIRECT_TRANSFER
        argument.bridge.copy_reason = None
        argument.projected_call_slot.adapter.bridge_copy_reason = None

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)


DEFERRED_UPDATE_SOURCE = """
module deferred_update
  implicit none
contains
  subroutine grow(value)
    character(len=:), allocatable, intent(inout) :: value
    if (allocated(value)) value = value // '!'
  end subroutine grow
end module deferred_update
"""


def _source_route_plan(tmp_path, text: str, module_name: str):
    from prik.parsers.fortran.parser import parse_fortran_project
    from prik.pipeline.build import (
        _apply_source_python_exports,
        _merge_wrapper_modules,
    )
    from prik.preprocessing import PreprocessingConfig, read_fortran_source
    from prik.semantics.fortran2ir import fortran_project_to_semantic_modules

    source = tmp_path / f"{module_name}.f90"
    source.write_text(text, encoding="utf-8")
    parsed = parse_fortran_project({str(source): read_fortran_source(source, PreprocessingConfig()).source})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _deferred_update_plan(tmp_path):
    return _source_route_plan(tmp_path, DEFERRED_UPDATE_SOURCE, "deferred_update")


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("drop-descriptor", "missing-update-result-descriptor"),
        ("drop-slot", "missing-update-result-native-slot"),
        ("drop-deferred-input", "invalid-update-result-argument"),
    ],
)
def test_deferred_length_string_update_plan_edits_fail_before_backend_lowering(
    edit: str,
    diagnostic: str,
    tmp_path,
):
    """The update lane's producer facts are validated, not assumed.

    Each edit leaves a plan that still lowers to compilable code while losing
    the reason the reallocated value reaches Python, so validation has to reject
    it rather than emit a wrapper that returns the caller's own value.
    """
    plan = _deferred_update_plan(tmp_path)
    function = next(
        item for namespace in plan.namespaces for item in namespace.functions if item.binding.python_name == "grow"
    )
    result = function.results[0]
    if edit == "drop-descriptor":
        result.scalar_descriptor = None
    elif edit == "drop-slot":
        result.projected_call_slot = None
    else:
        function.arguments[0].bridge.character_local = None

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)
