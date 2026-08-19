"""Direct-plan required scalar string-value input lowering."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.policy.ownership import CodegenAction, NativeBarrierAction, PythonBarrierAction
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import (
    ArgumentHandoffMode,
    BridgeDataAction,
    NativeArrayDescriptorKind,
    OptionalMode,
)
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.planning.models import DatatypeFamily


def _string_input_module():
    module = parse_pyi_text(
        """
def fixed(text: String[8]) -> Int32: ...
def assumed(text: String) -> Int32: ...
""",
        module_name="string_inputs",
    )
    complete_semantic_policies(module)
    return module


def _string_input_plan():
    return WrapperPlanner().build(_string_input_module())


def test_required_string_values_reuse_argument_plan_with_character_handoff_facts():
    module = _string_input_module()
    plan = WrapperPlanner().build(module)
    functions = {function.binding.python_name: function for function in plan.namespaces[0].functions}
    fixed = functions["fixed"].arguments[0]
    assumed = functions["assumed"].arguments[0]

    for function_name, argument in (("fixed", fixed), ("assumed", assumed)):
        assert argument.datatype_family is DatatypeFamily.STRING
        assert argument.binding.python_action is PythonBarrierAction.STRING_VALUE
        assert argument.bridge.native_action is NativeBarrierAction.PASS_CALL_LOCAL_ADDRESS
        assert argument.entrypoint.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER
        assert argument.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION
        assert argument.bridge.copy_reason == (
            "materialize Fortran character storage from the binding UTF-8 byte buffer"
        )
        assert argument.projected_call_slot.adapter.bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
        assert argument.entrypoint.length_handoff_role == f"{argument.owner_path}:length"
        assert argument.projected_call_slot is functions[function_name].entrypoint.projected_slots[0]
        assert argument.projected_call_slot.adapter.codegen_action is CodegenAction.CALL_LOCAL_INPUT

    assert fixed.projected_call_slot.character_length == 8
    assert assumed.projected_call_slot.character_length is None


def test_required_string_values_dispatch_to_named_binding_and_bridge_lowering():
    artifacts = WrapperGenerator().generate(_string_input_plan())
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "#include <string.h>" in c_source
    assert "const char * bound_text = NULL;" in c_source
    assert "bound_text = PyUnicode_AsUTF8AndSize(bound_text_obj, &bound_text_length);" in c_source
    assert "strlen(bound_text) != bound_text_length" in c_source
    assert "bound_text_length != 8" in c_source
    assert "must encode to exactly 8 bytes" in c_source
    assert "bind_c_fixed(bound_text, (int64_t)bound_text_length)" in c_source
    assert "bind_c_assumed(bound_text, (int64_t)bound_text_length)" in c_source

    assert "type(c_ptr), value :: bound_text" in bridge_source
    assert "integer(c_int64_t), value :: text_length" in bridge_source
    assert "character(kind=c_char), pointer, dimension(:) :: text_bytes" in bridge_source
    assert "character(kind=c_char, len=text_length) :: text" in bridge_source
    assert "call c_f_pointer(bound_text, text_bytes, [text_length])" in bridge_source
    assert "text = transfer(text_bytes, text)" in bridge_source
    assert "native_fixed(text)" in bridge_source
    assert "native_assumed(text)" in bridge_source


@pytest.mark.parametrize(
    ("edit", "diagnostic"),
    [
        ("missing-length", "missing-string-length-handoff"),
        ("wrong-handoff", "invalid-string-handoff"),
        ("wrong-copy", "invalid-string-data-action"),
    ],
)
def test_string_handoff_plan_edits_fail_before_backend_lowering(edit: str, diagnostic: str):
    plan = _string_input_plan()
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


DEFERRED_INPUT_SOURCE = """
module deferred_input
  implicit none
contains
  subroutine measure(value, length)
    character(len=:), allocatable, intent(in) :: value
    integer(4), intent(out) :: length
    length = len(value)
  end subroutine measure
end module deferred_input
"""


def _source_route_plan(tmp_path, text: str, module_name: str):
    from prik.parsers.fortran.parser import parse_fortran_project
    from prik.pipeline.build import (
        _apply_source_python_exports,
        _fortran_source_for_pipeline,
        _merge_wrapper_modules,
    )
    from prik.preprocessing import PreprocessingConfig
    from prik.semantics.fortran2ir import fortran_project_to_semantic_modules

    source = tmp_path / f"{module_name}.f90"
    source.write_text(text, encoding="utf-8")
    parsed = parse_fortran_project({str(source): _fortran_source_for_pipeline(source, PreprocessingConfig())})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name=module_name)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _deferred_input_plan(tmp_path):
    return _source_route_plan(tmp_path, DEFERRED_INPUT_SOURCE, "deferred_input")


def _deferred_update_plan(tmp_path):
    return _source_route_plan(tmp_path, DEFERRED_UPDATE_SOURCE, "deferred_update")


def test_deferred_length_string_input_plans_an_allocatable_adapter_local(tmp_path):
    """The bridge facet carries the deferred fact; the shared entrypoint does not.

    A deferred-length dummy cannot appear in a ``bind(C)`` interface, so the
    adapter local is adapter-local conversion rather than part of the C ABI.
    """
    plan = _deferred_input_plan(tmp_path)
    function = next(
        function
        for namespace in plan.namespaces
        for function in namespace.functions
        if function.binding.python_name == "measure"
    )
    argument = function.arguments[0]

    assert argument.bridge.character_local is not None
    assert argument.bridge.character_local.deferred_length is True
    assert argument.bridge.character_local.descriptor_kind is NativeArrayDescriptorKind.ALLOCATABLE
    assert argument.entrypoint.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER
    assert argument.bridge.data_action is BridgeDataAction.COPY_REPRESENTATION


def test_deferred_length_string_input_lowers_to_allocatable_local_without_changing_the_binding(tmp_path):
    """The adapter allocates on assignment; the C binding keeps the byte buffer."""
    artifacts = WrapperGenerator().generate(_deferred_input_plan(tmp_path))
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    assert "character(kind=c_char, len=:), allocatable :: value" in bridge_source
    assert "transfer(value_bytes, repeat(' ', value_length))" in bridge_source
    assert "character(kind=c_char, len=value_length)" not in bridge_source
    # The shared C ABI is unchanged: the binding still hands over bytes plus a length.
    assert "bind_c_measure" in c_source


def test_deferred_length_string_update_plans_one_input_and_one_output_group(tmp_path):
    """The update adds an output group beside its input, not a descriptor argument.

    The Python-visible argument keeps the plain character-buffer handoff, so the
    C ABI gains only the descriptor output group the reallocated value needs.
    """
    plan = _deferred_update_plan(tmp_path)
    function = next(
        function
        for namespace in plan.namespaces
        for function in namespace.functions
        if function.binding.python_name == "grow"
    )
    argument = function.arguments[0]
    result = function.results[0]

    assert argument.entrypoint.handoff_mode is ArgumentHandoffMode.CHARACTER_BUFFER
    assert argument.binding.optional_mode is OptionalMode.REQUIRED
    assert argument.binding.descriptor_boundary is False
    assert argument.entrypoint.descriptor_output_role is None
    assert argument.projects_character_descriptor_update is True

    assert result.updates_argument is True
    assert result.owner_path == argument.owner_path
    assert result.projected_call_slot is argument.projected_call_slot
    assert result.scalar_descriptor is not None
    assert result.entrypoint.parameter_name == "value_output"
    assert tuple(
        (parameter.owner_path, parameter.source_kind)
        for parameter in sorted(function.entrypoint.parameters, key=lambda item: item.position)
    ) == ((argument.owner_path, "argument"), (result.owner_path, "hidden_result"))


def test_deferred_length_string_update_copies_the_reallocated_local_into_c_storage(tmp_path):
    """The adapter reads back the same local the native procedure may reallocate.

    Reading a separate output local would return the value the caller passed in,
    which compiles and imports but silently discards the update.
    """
    artifacts = WrapperGenerator().generate(_deferred_update_plan(tmp_path))
    bridge_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    assert "character(kind=c_char, len=:), allocatable :: value" in bridge_source
    assert "call native_grow(value)" in bridge_source
    assert "if (allocated(value)) then" in bridge_source
    assert "value_output_length = len(value, kind=c_int64_t)" in bridge_source
    assert "transfer(value, value_output_copy(1:value_output_length))" in bridge_source
    # No separate output local exists to read the pre-call value from.
    assert "value_output_value" not in bridge_source
    assert "bind_c_grow(bound_value, (int64_t)bound_value_length, &value_output, " in c_source


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


DESCRIPTOR_LOCAL_SOURCE = """
module descriptor_locals
  implicit none
contains
  subroutine fixed_allocatable(value, length)
    character(len=4), allocatable, intent(in) :: value
    integer(4), intent(out) :: length
    length = len(value)
  end subroutine fixed_allocatable
  subroutine deferred_pointer(value, length)
    character(len=:), pointer, intent(in) :: value
    integer(4), intent(out) :: length
    length = len(value)
  end subroutine deferred_pointer
  subroutine fixed_pointer(value, length)
    character(len=4), pointer, intent(in) :: value
    integer(4), intent(out) :: length
    length = len(value)
  end subroutine fixed_pointer
  subroutine pointer_update(value)
    character(len=:), pointer, intent(inout) :: value
    if (associated(value)) value = 'z'
  end subroutine pointer_update
end module descriptor_locals
"""


def _descriptor_local_source(tmp_path) -> str:
    artifacts = WrapperGenerator().generate(_source_route_plan(tmp_path, DESCRIPTOR_LOCAL_SOURCE, "descriptor_locals"))
    return next(source.text for source in artifacts.sources if source.path.suffix == ".f90")


def test_descriptor_character_locals_carry_the_attribute_the_native_dummy_declares(tmp_path):
    """An allocatable or pointer dummy rejects a plain local as its actual argument.

    The local is the only thing that changes: each of these arguments still
    crosses the C ABI as a byte buffer and a length.
    """
    bridge_source = _descriptor_local_source(tmp_path)

    assert "character(kind=c_char, len=4), allocatable :: value" in bridge_source
    assert "character(kind=c_char, len=:), pointer :: value" in bridge_source
    assert "character(kind=c_char, len=4), pointer :: value" in bridge_source


def test_descriptor_character_locals_are_allocated_before_the_copy_that_needs_them(tmp_path):
    """Only a deferred-length allocatable is established by assignment alone.

    A pointer has no storage until it is allocated, and a fixed-length
    allocatable would otherwise be moulded from storage that does not exist.
    """
    bridge_source = _descriptor_local_source(tmp_path)

    assert "allocate(character(kind=c_char, len=value_length) :: value)" in bridge_source
    assert "allocate(value)" in bridge_source


def test_pointer_character_locals_release_the_storage_the_adapter_allocated(tmp_path):
    """A read-only pointer dummy cannot reassociate, so its allocation is always still ours.

    An update dummy may be reassociated or deallocated by the native procedure,
    so the adapter compares against the seed it recorded and leaves native-owned
    storage alone.
    """
    bridge_source = _descriptor_local_source(tmp_path)

    assert "value => null()" in bridge_source
    assert "if (associated(value)) then" in bridge_source
    assert "deallocate(value)" in bridge_source
    assert "value_seed => value" in bridge_source
    assert "if (associated(value, value_seed)) then" in bridge_source
