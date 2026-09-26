"""Direct-plan immutable string replacement and identity lowering."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    OptionalMode,
    PythonExceptionKind,
    WritebackPhase,
)
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.planning.models import BindingStatusErrorPlan


def _fixed_writeback_module():
    module = parse_pyi_text(
        """
def replace_name(name: String[8]) -> Returns["name", String[8]]: ...
def discard_name(name: String[8]) -> None: ...
""",
        module_name="fixed_string_writeback",
    )
    complete_semantic_policies(module)
    return module


def _fixed_writeback_plan():
    return WrapperPlanner().build(_fixed_writeback_module())


def _functions(plan):
    return {function.binding.python_name: function for function in plan.namespaces[0].functions}


def test_fixed_string_replacements_validate_first_and_cleanup_every_live_buffer():
    module = parse_pyi_text(
        """
def replace_names(
    first: String[8], second: String[8], count: Int32
) -> tuple[Returns["first", String[8]], Returns["second", String[8]], Int32]: ...
""",
        module_name="fixed_string_cleanup_order",
    )
    complete_semantic_policies(module)
    artifacts = WrapperGenerator().generate(WrapperPlanner().build(module))
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    first_allocation = "bound_first = (char *)prik_malloc((size_t)bound_first_length + 1);"
    second_allocation = "bound_second = (char *)prik_malloc((size_t)bound_second_length + 1);"
    assert c_source.index("prik_int32_or_storage(bound_count_obj, ") < c_source.index(first_allocation)
    assert c_source.index("prik_character_input(bound_second_obj, ") < c_source.index(first_allocation)
    assert c_source.index(first_allocation) < c_source.index(second_allocation)

    second_failure = c_source[c_source.index("if (bound_second == NULL)") : c_source.index(second_allocation) + 900]
    assert "free(bound_first); bound_first = NULL;" in second_failure
    assert "free(bound_second); bound_second = NULL;" in second_failure

    # Converting the first string also releases its buffer, before the scalar result is read.
    first_conversion = "result_0_obj = prik_character_result(bound_first_obj, &bound_first, "
    scalar_conversion = "prik_int32_to_numpy(&__return_0)"
    assert c_source.index(first_conversion) < c_source.index(scalar_conversion)


def test_string_writeback_conversion_failure_releases_unpublished_native_results():
    module = parse_pyi_text(
        """
def replace_and_return(
    name: String[8]
) -> tuple[Returns["name", String[8]], String[8]]: ...
""",
        module_name="string_writeback_with_result",
    )
    complete_semantic_policies(module)
    artifacts = WrapperGenerator().generate(WrapperPlanner().build(module))
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    writeback_failure = c_source[
        c_source.index("if (result_0_obj == NULL)") : c_source.index("if (__return_0 == NULL)")
    ]
    assert "if (__return_0 != NULL) { free(__return_0); __return_0 = NULL; }" in writeback_failure


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("missing-cleanup", "missing-writeback-phase"),
        ("lifecycle-type-drift", "inconsistent-lifecycle-type"),
        ("descriptor-presence", "invalid-string-optional-mode"),
        ("status-error", "string-writeback-with-status-error"),
    ],
)
def test_fixed_string_writeback_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _fixed_writeback_plan()
    function = _functions(plan)["replace_name"]
    argument = function.arguments[0]
    if edit == "missing-cleanup":
        function.writeback_actions = tuple(
            action for action in function.writeback_actions if action.phase is not WritebackPhase.CLEANUP
        )
    elif edit == "lifecycle-type-drift":
        copy_out = next(action for action in function.writeback_actions if action.phase is WritebackPhase.COPY_OUT)
        copy_out.semantic_type_name = "Int32"
    elif edit == "descriptor-presence":
        argument.binding.optional_mode = OptionalMode.DESCRIPTOR
        argument.entrypoint.optional_mode = OptionalMode.DESCRIPTOR
    else:
        function.binding = replace(
            function.binding,
            status_error=BindingStatusErrorPlan(
                status_role="missing:status",
                message_role=None,
                success=0,
                exception_kind=PythonExceptionKind.RUNTIME_ERROR,
            ),
        )

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)
