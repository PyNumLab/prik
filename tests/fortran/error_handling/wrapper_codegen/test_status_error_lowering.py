"""Native-call runtime-envelope and status-error lowering tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from x2py.pipeline.pyi import pyi_file_to_semantic_module
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.semantics.wrapper_policy import BridgeDataAction, PythonExceptionKind
from x2py.wrapper_codegen import DatatypeFamily, WrapperCodeGenerator, WrapperPlanner


RUNTIME_POLICY_CONTRACT = (
    Path(__file__).resolve().parents[1] / "end_to_end" / "fixtures" / "edited_contract" / "fruntime_policy_f90.pyi"
)


def _runtime_plan():
    module = pyi_file_to_semantic_module(RUNTIME_POLICY_CONTRACT, module_name="fruntime_policy_f90")
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _rendered_source(artifacts, suffix: str) -> str:
    return next(source.text for source in artifacts.sources if source.path.name.endswith(suffix))


def _function_source(source: str, function_name: str, next_name: str | None = None) -> str:
    start = source.index(f"static PyObject * wrap_{function_name}")
    if next_name is None:
        return source[start : source.index("PyMODINIT_FUNC", start)]
    return source[start : source.index(f"static PyObject * wrap_{next_name}", start)]


def _edit_function(plan, function_name: str, edit):
    root = plan.namespaces[0]
    functions = tuple(
        edit(function) if function.binding.python_name == function_name else function for function in root.functions
    )
    return replace(plan, namespaces=(replace(root, functions=functions), *plan.namespaces[1:]))


def test_planner_records_editable_native_runtime_and_status_error_facts():
    plan = _runtime_plan()
    functions = {function.binding.python_name: function for function in plan.namespaces[0].functions}
    solve = functions["solve"]

    assert functions["pause_for_one_second"].binding.hold_gil is False
    assert functions["pause_with_gil"].binding.hold_gil is True
    assert solve.binding.hold_gil is False
    assert solve.binding.status_error is not None
    assert solve.binding.status_error.success == 0
    assert solve.binding.status_error.exception_kind is PythonExceptionKind.RUNTIME_ERROR
    assert solve.binding.status_error.status_role == solve.native_call_slots[1].symbolic_role
    assert solve.binding.status_error.message_role == solve.native_call_slots[2].symbolic_role
    assert "Raises\n------" in solve.binding.docstring
    assert solve.binding.docstring.count("RuntimeError\n") == 1
    assert "If native status differs from the success value 0." in solve.binding.docstring
    assert solve.native_call_slots[1].semantic_type_name == "Int32"
    assert solve.native_call_slots[1].datatype_family is DatatypeFamily.INTEGER
    assert solve.native_call_slots[1].bridge_data_action is BridgeDataAction.DIRECT_TRANSFER
    assert solve.native_call_slots[1].bridge_copy_reason is None
    assert solve.native_call_slots[2].semantic_type_name == "String"
    assert solve.native_call_slots[2].datatype_family is DatatypeFamily.STRING
    assert solve.native_call_slots[2].character_length == 32
    assert solve.native_call_slots[2].bridge_data_action is BridgeDataAction.COPY_REPRESENTATION
    assert solve.native_call_slots[2].bridge_copy_reason == (
        "copy fixed-length Fortran character output into C-owned null-terminated storage"
    )


def test_direct_binding_lowering_places_only_native_call_outside_the_gil():
    artifacts = WrapperCodeGenerator().generate(_runtime_plan())
    c_source = _rendered_source(artifacts, ".c")
    released = _function_source(c_source, "pause_for_one_second", "pause_with_gil")
    held = _function_source(c_source, "pause_with_gil", "solve")
    solve = _function_source(c_source, "solve")

    assert released.index("Py_BEGIN_ALLOW_THREADS") < released.index("bind_c_pause_for_one_second()")
    assert released.index("bind_c_pause_for_one_second()") < released.index("Py_END_ALLOW_THREADS")
    assert "Py_BEGIN_ALLOW_THREADS" not in held
    assert "Py_END_ALLOW_THREADS" not in held
    assert solve.index("Py_BEGIN_ALLOW_THREADS") < solve.index("bind_c_solve(&bound_value, &status, &message)")
    assert solve.index("bind_c_solve(&bound_value, &status, &message)") < solve.index("Py_END_ALLOW_THREADS")
    assert solve.index("Py_END_ALLOW_THREADS") < solve.index("PyUnicode_FromString")
    assert solve.index("PyUnicode_FromString") < solve.index("status != 0")
    assert "PyErr_SetObject(PyExc_RuntimeError, message_obj)" in solve
    assert "free(message)" in solve


def test_direct_bridge_lowering_projects_status_and_copies_fixed_message():
    artifacts = WrapperCodeGenerator().generate(_runtime_plan())
    fortran_source = _rendered_source(artifacts, ".f90")

    assert "subroutine bind_c_solve(value, status, message)" in fortran_source
    assert "integer(c_int32_t) :: status" in fortran_source
    assert "type(c_ptr) :: message" in fortran_source
    assert "character(kind=c_char, len=32) :: message_value" in fortran_source
    assert "call native_solve(value, status, message_value)" in fortran_source
    assert "message = c_malloc(33_c_size_t)" in fortran_source
    assert "message_copy(33) = c_null_char" in fortran_source


def test_fixed_message_bridge_copy_requires_its_completed_reason():
    plan = _runtime_plan()
    invalid = _edit_function(
        plan,
        "solve",
        lambda function: replace(
            function,
            native_call_slots=tuple(
                replace(slot, bridge_copy_reason=None) if slot.datatype_family is DatatypeFamily.STRING else slot
                for slot in function.native_call_slots
            ),
        ),
    )

    with pytest.raises(ValueError, match="missing-bridge-copy-reason"):
        WrapperCodeGenerator().generate(invalid)


def test_runtime_plan_edits_dispatch_to_named_lowering_and_validate_roles():
    plan = _runtime_plan()
    held = _edit_function(
        plan,
        "pause_for_one_second",
        lambda function: replace(function, binding=replace(function.binding, hold_gil=True)),
    )
    c_source = _rendered_source(WrapperCodeGenerator().generate(held), ".c")
    released = _function_source(c_source, "pause_for_one_second", "pause_with_gil")
    assert "Py_BEGIN_ALLOW_THREADS" not in released
    assert "Py_END_ALLOW_THREADS" not in released

    invalid = _edit_function(
        plan,
        "solve",
        lambda function: replace(
            function,
            binding=replace(
                function.binding,
                status_error=replace(function.binding.status_error, status_role="missing:status"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="missing-status-result-role"):
        WrapperCodeGenerator().generate(invalid)
