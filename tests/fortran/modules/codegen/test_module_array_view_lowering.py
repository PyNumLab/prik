"""Bridge lowering for the two fixed module-array address mechanisms."""

from __future__ import annotations

from dataclasses import replace

import pytest

from prik.codegen.c.binding import CBindingGenerator
from prik.codegen.fortran.bridge import FortranBridgeGenerator
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.printers.fortran import FortranSourcePrinter
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from tests.fortran._support.ownership_policy import parse_pyi_text


MODULE_ARRAY_SOURCE = """
module array_state
  use iso_fortran_env, only: int32, real64
  implicit none
  real(real64) :: plain(2, 3)
  integer(int32) :: counts(3)
  character(len=5) :: labels(2)
  real(real64), target :: addressable(4)
end module array_state
"""


def _plan():
    parsed = parse_fortran_project({"array_state.f90": MODULE_ARRAY_SOURCE})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="array_state")
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _bridge_module():
    return FortranBridgeGenerator().visit(_plan())


def _lowered_getters():
    plan = _plan()
    bridge = FortranBridgeGenerator()
    bridge.visit(plan)
    printer = FortranSourcePrinter()
    return {
        variable.binding.python_names[0]: printer.visit(bridge.visit(variable)[0])
        for namespace in plan.namespaces
        for variable in namespace.variables
    }


def test_addressable_module_array_takes_its_address_directly():
    """A `target` declaration lets `c_loc` name the array, so nothing else is emitted."""
    getter = _lowered_getters()["addressable"]

    assert "c_loc(native_addressable)" in getter
    assert "capture_array_address" not in getter


@pytest.mark.parametrize("python_name", ["plain", "counts", "labels"])
def test_ordinary_module_array_captures_its_address_in_c(python_name):
    """Without `target`, the address is taken on the C side, never by `c_loc`.

    `c_loc` requires the variable it names to be a target, so an ordinary
    declaration has no Fortran route to its own address. The getter hands the
    whole array to a `bind(C)` procedure instead: an assumed-type assumed-size
    dummy is passed as the bare base address, so C receives where the module
    variable lives. The bridge forms no pointer and claims no target, and one
    interface covers every element type including character.
    """
    getter = _lowered_getters()[python_name]

    assert f"prik_capture_address(native_{python_name})" in getter
    assert "c_loc" not in getter
    assert "target" not in getter


def test_captured_address_declares_one_typeless_c_interface():
    """One assumed-type interface serves every captured element type."""
    module = _bridge_module()

    interfaces = [procedure for interface in module.interfaces for procedure in interface.procedures]
    captures = [procedure for procedure in interfaces if procedure.name == "prik_capture_address"]
    assert len(captures) == 1
    assert captures[0].bind_name == "prik_capture_address"
    assert captures[0].parameters[0].type_name == "type(*)"
    assert captures[0].parameters[0].attributes == ("dimension(*)",)


def test_capture_helper_is_declared_only_where_an_array_needs_it():
    """A module whose arrays are all addressable declares no capture interface."""
    module = parse_pyi_text(
        "addressable: Annotated[Float64[4], Aliased]\n",
        module_name="array_state",
    )
    complete_semantic_policies(module)
    bridge = FortranBridgeGenerator()
    emitted = bridge.visit(WrapperPlanner().build(module))

    names = [procedure.name for interface in emitted.interfaces for procedure in interface.procedures]
    assert "prik_capture_address" not in names


def test_binding_opts_into_the_bundled_capture_primitive():
    """The C side selects the runtime definition of the symbol the bridge calls.

    The helper lives in the bundled support header rather than in emitted code,
    because it is a fixed ABI primitive rather than something a plan describes.
    It needs external linkage for the bridge to call it, so the binding opts in
    once per extension and the header defines it in that translation unit alone.
    """
    binding = CBindingGenerator().binding_module(_plan())

    assert any(define.name == "PRIK_BINDING_CAPTURE_ADDRESS" for define in binding.defines)
    assert not any(function.name == "prik_capture_address" for function in binding.functions)


def test_binding_omits_the_capture_primitive_when_no_array_needs_it():
    """An extension whose arrays are all addressable pulls in no capture symbol."""
    module = parse_pyi_text(
        "addressable: Annotated[Float64[4], Aliased]\n",
        module_name="array_state",
    )
    complete_semantic_policies(module)
    binding = CBindingGenerator().binding_module(WrapperPlanner().build(module))

    assert not any(define.name == "PRIK_BINDING_CAPTURE_ADDRESS" for define in binding.defines)


def _undecided_plan():
    """Return a module-array plan whose address mechanism policy never selected."""
    module = parse_pyi_text("plain: Float64[3]\n", module_name="array_state")
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    variable = plan.namespaces[0].variables[0]
    return plan, variable, replace(variable, array_address=None)


def test_module_array_view_plan_rejects_a_missing_address_mechanism():
    """The plan boundary reports the gap rather than letting lowering guess."""
    plan, _variable, undecided = _undecided_plan()
    namespace = plan.namespaces[0]
    namespace.variables = (undecided,)

    diagnostics = WrapperGenerator()._plan_diagnostics(plan)

    assert any(diagnostic.code == "missing-module-array-address-mechanism" for diagnostic in diagnostics)


def test_module_array_view_lowering_requires_a_completed_address_mechanism():
    """Lowering refuses to invent an address route policy did not select."""
    plan, _variable, undecided = _undecided_plan()
    bridge = FortranBridgeGenerator()
    bridge.visit(plan)

    with pytest.raises(ValueError, match="no completed address mechanism"):
        bridge.visit(undecided)
