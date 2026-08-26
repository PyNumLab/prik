"""Direct-plan immutable string replacement and identity lowering."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.ownership import (
    CodegenAction,
    DestructionPolicy,
    ObjectKind,
    OwnershipOwner,
    StorageMode,
    TransferMode,
)
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    BridgeDataAction,
    OptionalMode,
    PythonExceptionKind,
    STRING_REPLACEMENT_COPY_REASON,
    WritebackPhase,
)
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.planning.models import BindingStatusErrorPlan, DatatypeFamily


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


def test_fixed_replacement_projects_completed_argument_and_lifecycle_facts():
    module = _fixed_writeback_module()
    functions = _functions(WrapperPlanner().build(module))
    replacement = functions["replace_name"]
    argument = replacement.arguments[0]
    assert argument.character_length == 8
    assert argument.object_kind is ObjectKind.STRING
    assert argument.ownership_owner is OwnershipOwner.PYTHON
    assert argument.transfer_mode is TransferMode.COPY_RETURN
    assert argument.destruction_policy is DestructionPolicy.PYTHON_REFCOUNT
    assert argument.storage_mode is StorageMode.STACK
    assert argument.boundary_storage_mode is StorageMode.STACK
    assert argument.nullable is False
    assert argument.mutates_native is False
    assert argument.projects_result is True
    assert argument.result_position == 0
    assert argument.binding.codegen_action is CodegenAction.COPY_IN_OUT
    assert argument.bridge.codegen_action is CodegenAction.COPY_IN_OUT
    assert argument.projected_call_slot.adapter.codegen_action is CodegenAction.COPY_IN_OUT
    assert argument.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION
    assert argument.bridge.copy_reason == STRING_REPLACEMENT_COPY_REASON
    assert tuple(action.phase for action in replacement.writeback_actions) == tuple(WritebackPhase)
    assert all(action.semantic_type_name == "String" for action in replacement.writeback_actions)
    assert all(action.datatype_family is DatatypeFamily.STRING for action in replacement.writeback_actions)

    identity = functions["discard_name"]
    assert identity.arguments[0].binding.codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert identity.arguments[0].bridge.codegen_action is CodegenAction.CALL_LOCAL_INPUT
    assert identity.arguments[0].projects_result is False
    assert identity.writeback_actions == ()


def test_fixed_string_writeback_dispatches_to_named_binding_and_bridge_lowering():
    artifacts = WrapperGenerator().generate(_fixed_writeback_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "void bind_c_replace_name(char * name, int64_t name_length);" in c_source
    assert "const char * bound_name_source = NULL;" in c_source
    assert "char * bound_name = NULL;" in c_source
    assert "bound_name = (char *)prik_malloc((size_t)bound_name_length + 1);" in c_source
    assert 'PyExc_MemoryError, "Unable to allocate mutable string buffer for argument name."' in c_source
    assert "memcpy(bound_name, bound_name_source, (size_t)bound_name_length);" in c_source
    assert "bound_name[bound_name_length] = '\\0';" in c_source
    assert "bind_c_replace_name(bound_name, (int64_t)bound_name_length);" in c_source
    assert 'Py_BuildValue("s", (const char *)bound_name)' in c_source
    conversion = c_source.index('Py_BuildValue("s", (const char *)bound_name)')
    release = c_source.index("free(bound_name);", conversion)
    assert conversion < release
    assert release < c_source.index("if (result_obj == NULL)", conversion)
    assert "void bind_c_discard_name(const char * name, int64_t name_length);" in c_source
    assert "bind_c_discard_name(bound_name, (int64_t)bound_name_length);" in c_source

    assert "call c_f_pointer(bound_name, name_bytes, [name_length + 1])" in bridge_source
    assert "name = transfer(name_bytes(1:name_length), name)" in bridge_source
    assert "call native_replace_name(name)" in bridge_source
    assert "name_bytes(1:name_length) = transfer(name, name_bytes(1:name_length))" in bridge_source
    assert "name_bytes(name_length + 1) = c_null_char" in bridge_source
    assert "call c_f_pointer(bound_name, name_bytes, [name_length])" in bridge_source
    assert "call native_discard_name(name)" in bridge_source


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
    assert c_source.index("prik_int32_unpack_exact(bound_count_obj, &bound_count)") < c_source.index(first_allocation)
    assert c_source.index("bound_second_source = PyUnicode_AsUTF8AndSize") < c_source.index(first_allocation)
    assert c_source.index(first_allocation) < c_source.index(second_allocation)

    second_failure = c_source[c_source.index("if (bound_second == NULL)") : c_source.index(second_allocation) + 900]
    assert "free(bound_first); bound_first = NULL;" in second_failure
    assert "free(bound_second); bound_second = NULL;" in second_failure

    first_conversion = 'result_0_obj = Py_BuildValue("s", (const char *)bound_first);'
    scalar_conversion = "prik_int32_to_numpy(&__return_0)"
    assert c_source.index(first_conversion) < c_source.index(scalar_conversion)
    assert c_source.index("free(bound_first);", c_source.index(first_conversion)) < c_source.index(scalar_conversion)


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


def test_assumed_and_optional_string_replacements_reuse_runtime_length_and_presence_facts():
    module = parse_pyi_text(
        """
def assumed(name: String) -> Returns["name", String]: ...
def optional(label: String = ...) -> Returns["label", String] | None: ...
def optional_identity(label: String = ...) -> None: ...
""",
        module_name="assumed_optional_string_writeback",
    )
    complete_semantic_policies(module)
    functions = _functions(WrapperPlanner().build(module))
    for name in ("assumed", "optional", "optional_identity"):
        argument = functions[name].arguments[0]
        assert argument.character_length is None
        assert argument.projected_call_slot.character_length is None
    assert functions["assumed"].arguments[0].binding.optional_mode is OptionalMode.REQUIRED
    assert functions["optional"].arguments[0].binding.optional_mode is OptionalMode.NULLABLE_VALUE
    assert functions["optional"].arguments[0].nullable is True
    assert functions["optional_identity"].arguments[0].binding.codegen_action is CodegenAction.CALL_LOCAL_INPUT


def test_assumed_and_optional_string_lowering_guards_presence_copyback_and_cleanup():
    module = parse_pyi_text(
        """
def assumed(name: String) -> Returns["name", String]: ...
def optional(label: String = ...) -> Returns["label", String] | None: ...
def optional_identity(label: String = ...) -> None: ...
""",
        module_name="assumed_optional_string_writeback",
    )
    complete_semantic_policies(module)
    artifacts = WrapperGenerator().generate(WrapperPlanner().build(module))
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "void bind_c_assumed(char * name, int64_t name_length);" in c_source
    assert "void bind_c_optional(char * label, int64_t label_length);" in c_source
    assert "PyObject * bound_label_obj = Py_None;" in c_source
    assert "if (bound_label_obj != Py_None)" in c_source
    assert "bind_c_optional(bound_label, (int64_t)bound_label_length);" in c_source
    assert "if (bound_label == NULL)" in c_source
    assert "Py_INCREF(Py_None);" in c_source
    assert 'result_obj = Py_BuildValue("s", (const char *)bound_label);' in c_source
    assert "void bind_c_optional_identity(const char * label, int64_t label_length);" in c_source

    assert "character(kind=c_char, len=name_length) :: name" in bridge_source
    assert "if (c_associated(bound_label)) then" in bridge_source
    assert "call native_optional(label=label)" in bridge_source
    assert "call native_optional()" in bridge_source
    assert "label_bytes(1:label_length) = transfer(label, label_bytes(1:label_length))" in bridge_source
    assert "label_bytes(label_length + 1) = c_null_char" in bridge_source


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("wrong-owner", "invalid-string-replacement-owner"),
        ("wrong-copy-reason", "invalid-string-copy-reason"),
        ("missing-cleanup", "missing-writeback-phase"),
        ("lifecycle-type-drift", "inconsistent-lifecycle-type"),
        ("descriptor-presence", "invalid-string-optional-mode"),
    ],
)
def test_fixed_string_writeback_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _fixed_writeback_plan()
    function = _functions(plan)["replace_name"]
    argument = function.arguments[0]
    if edit == "wrong-owner":
        argument.ownership_owner = OwnershipOwner.NATIVE
    elif edit == "wrong-copy-reason":
        argument.bridge.copy_reason = "an edited copy reason"
        argument.projected_call_slot.adapter.bridge_copy_reason = "an edited copy reason"
    elif edit == "missing-cleanup":
        function.writeback_actions = tuple(
            action for action in function.writeback_actions if action.phase is not WritebackPhase.CLEANUP
        )
    elif edit == "lifecycle-type-drift":
        copy_out = next(action for action in function.writeback_actions if action.phase is WritebackPhase.COPY_OUT)
        copy_out.semantic_type_name = "Int32"
    else:
        argument.binding.optional_mode = OptionalMode.DESCRIPTOR
        argument.entrypoint.optional_mode = OptionalMode.DESCRIPTOR

    with pytest.raises(ValueError, match=diagnostic):
        WrapperGenerator().generate(plan)


def test_fixed_string_writeback_status_edit_fails_at_generator_validation():
    plan = _fixed_writeback_plan()
    function = _functions(plan)["replace_name"]
    function.binding = replace(
        function.binding,
        status_error=BindingStatusErrorPlan(
            status_role="missing:status",
            message_role=None,
            success=0,
            exception_kind=PythonExceptionKind.RUNTIME_ERROR,
        ),
    )

    with pytest.raises(ValueError, match="string-writeback-with-status-error"):
        WrapperGenerator().generate(plan)
