"""Module-array plan validation and character descriptor lowering."""

from __future__ import annotations

from dataclasses import replace

import pytest

from prik.codegen.fortran.bridge import FortranBridgeGenerator
from prik.parsers.fortran.parser import parse_fortran_project
from prik.pipeline.build import _apply_source_python_exports, _merge_wrapper_modules
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.printers.fortran import FortranSourcePrinter
from prik.semantics.fortran2ir import fortran_project_to_semantic_modules
from tests.fortran._support.ownership_policy import parse_pyi_text


DESCRIPTOR_CHARACTER_SOURCE = """
module char_state
  implicit none
  character(len=5), allocatable :: fixed_alloc(:)
  character(len=5), pointer :: fixed_ptr(:) => null()
  character(len=:), allocatable :: deferred_alloc(:)
  real(8), allocatable :: numbers(:)
end module char_state
"""


def _undecided_plan():
    """Return a module-array plan whose address mechanism policy never selected."""
    module = parse_pyi_text("plain: Float64[3]\n", module_name="array_state")
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    variable = plan.variables[0]
    return plan, variable, replace(variable, storage_address=None)


def test_module_array_view_plan_rejects_a_missing_address_mechanism():
    """The plan boundary reports the gap rather than letting lowering guess."""
    plan, _variable, undecided = _undecided_plan()
    plan.variables = (undecided,)

    diagnostics = WrapperGenerator()._plan_diagnostics(plan)

    assert any(diagnostic.code == "missing-module-array-address-mechanism" for diagnostic in diagnostics)


def test_module_array_view_lowering_requires_a_completed_address_mechanism():
    """Lowering refuses to invent an address route policy did not select."""
    plan, _variable, undecided = _undecided_plan()
    bridge = FortranBridgeGenerator()
    bridge.visit(plan)

    with pytest.raises(ValueError, match="no completed address mechanism"):
        bridge.visit(undecided)


def _character_bridge_source():
    parsed = parse_fortran_project({"char_state.f90": DESCRIPTOR_CHARACTER_SOURCE})
    modules = fortran_project_to_semantic_modules(parsed)
    _apply_source_python_exports(modules)
    module = _merge_wrapper_modules(modules, name="char_state")
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    return FortranSourcePrinter().visit(FortranBridgeGenerator().visit(plan))


def test_fixed_character_callbacks_use_an_ordinary_descriptor_projection():
    """The callback declaration matches the descriptor attribute policy selected upstream."""
    source = _character_bridge_source()

    assert source.count("character(kind=c_char, len=*), dimension(:), intent(inout) :: value") == 2
    assert "character(kind=c_char, len=:), allocatable, dimension(:), intent(inout) :: value" in source
    assert "real(c_double), allocatable, dimension(:), intent(inout) :: value" in source
    assert "if (allocated(native_fixed_alloc)) then" in source
    assert "if (associated(native_fixed_ptr)) then" in source
    assert "call callback(native_deferred_alloc, context)" in source
