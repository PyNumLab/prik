"""Strict lowering ownership for ordinary and generated support procedures."""

from __future__ import annotations

import ast
from inspect import getsource
from textwrap import dedent

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.codegen.c.binding import CBindingGenerator
from prik.codegen.fortran.bridge import FortranBridgeGenerator
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import GeneratedSupportProcedureImplementationOwner, WrapperPlanner
from prik.policy.completion import complete_semantic_policies


def _plan(source: str, *, module_name: str):
    module = parse_pyi_text(source, module_name=module_name)
    complete_semantic_policies(module)
    return WrapperPlanner().build(module)


def _rendered(plan, suffix: str) -> str:
    generated = WrapperGenerator().generate(plan)
    return next(source.text for source in generated.sources if source.path.suffix == suffix)


def _attribute_reads(generator_type: type) -> set[str]:
    tree = ast.parse(dedent(getsource(generator_type)))
    return {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}


def test_backend_lowerers_cannot_read_the_opposite_plan_facet():
    binding_reads = _attribute_reads(CBindingGenerator)
    assert "bridge" not in binding_reads
    assert "adapter" not in binding_reads
    assert "binding" not in _attribute_reads(FortranBridgeGenerator)


def test_ordinary_function_facets_change_only_their_own_consumers():
    source = "def scale(value: Float64) -> Float64: ...\n"
    original = _plan(source, module_name="ordinary_facet_boundary")
    binding_edit = _plan(source, module_name="ordinary_facet_boundary")
    bridge_edit = _plan(source, module_name="ordinary_facet_boundary")
    entrypoint_edit = _plan(source, module_name="ordinary_facet_boundary")

    binding_edit.namespaces[0].functions[0].binding.release_gil = True
    bridge_edit.namespaces[0].functions[0].bridge.native_name = "renamed_native_scale"
    entrypoint_edit.namespaces[0].functions[0].entrypoint.symbol_name = "shared_scale_entrypoint"

    original_c = _rendered(original, ".c")
    original_fortran = _rendered(_plan(source, module_name="ordinary_facet_boundary"), ".f90")

    assert _rendered(binding_edit, ".f90") == original_fortran
    assert _rendered(bridge_edit, ".c") == original_c
    assert "shared_scale_entrypoint" in _rendered(entrypoint_edit, ".c")
    assert "shared_scale_entrypoint" in _rendered(
        _plan_with_entrypoint_symbol(source, "ordinary_facet_boundary", "shared_scale_entrypoint"),
        ".f90",
    )


def _plan_with_entrypoint_symbol(source: str, module_name: str, symbol: str):
    plan = _plan(source, module_name=module_name)
    plan.namespaces[0].functions[0].entrypoint.symbol_name = symbol
    return plan


def test_fortran_owned_support_procedure_uses_one_shared_entrypoint():
    source = "counter: Int32\n"
    plan = _plan(source, module_name="fortran_support_boundary")
    procedure = next(item for item in plan.entrypoint.support_procedures if item.role == "module:get")

    assert procedure.implementation_owner is GeneratedSupportProcedureImplementationOwner.FORTRAN
    procedure.symbol_name = "shared_counter_getter"

    assert "shared_counter_getter" in _rendered(plan, ".c")
    assert "shared_counter_getter" in _rendered(
        _edited_support_symbol(source, "fortran_support_boundary", "module:get", "shared_counter_getter"),
        ".f90",
    )


def _edited_support_symbol(source: str, module_name: str, role: str, symbol: str):
    plan = _plan(source, module_name=module_name)
    next(item for item in plan.entrypoint.support_procedures if item.role == role).symbol_name = symbol
    return plan


def test_binding_owned_callback_support_procedure_uses_one_shared_entrypoint():
    source = """
@prototype
def callback(value: Int32) -> Int32: ...

def apply(callback: callback, value: Int32) -> Int32: ...
"""
    plan = _plan(source, module_name="binding_support_boundary")
    callback = plan.namespaces[0].functions[0].arguments[0].callback
    procedure = callback.entrypoint.support_procedure

    assert procedure.implementation_owner is GeneratedSupportProcedureImplementationOwner.BINDING
    procedure.symbol_name = "shared_callback_trampoline"

    assert "shared_callback_trampoline" in _rendered(plan, ".c")
    assert "shared_callback_trampoline" in _rendered(
        _edited_callback_symbol(source, "shared_callback_trampoline"),
        ".f90",
    )


def _edited_callback_symbol(source: str, symbol: str):
    plan = _plan(source, module_name="binding_support_boundary")
    plan.namespaces[0].functions[0].arguments[0].callback.entrypoint.support_procedure.symbol_name = symbol
    return plan
