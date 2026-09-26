"""A collision-adapted symbol is reached from a unit that excludes Python.h."""

import pytest

from prik.parsers.c import parse_c_file
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.semantics.c2ir import c_file_to_semantic_module
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules

_SOURCE = """long long native_round(double value) { return (long long)value; }
double native_add(double left, double right) { return left + right; }
"""


def _generated(**planner_options):
    module = c_file_to_semantic_module(parse_c_file(_SOURCE, filename="collide.c"))
    complete_semantic_policies(module)
    return WrapperGenerator().generate(WrapperPlanner(**planner_options).build(module))


def _sources_by_name(generated):
    return {source.path.name: source.text for source in generated.sources if source.path.suffix == ".c"}


_DECLARATIONS = {
    "native_round": ("long long native_round(double value);", "return (native_round)(value);"),
    "native_add": ("double native_add(double left, double right);", "return (native_add)(left, right);"),
}


@pytest.mark.parametrize(
    ("planner_options", "adapted"),
    [
        pytest.param({}, set(), id="unselected"),
        pytest.param({"collision_adapters": ("native_round",)}, {"native_round"}, id="one-selected-symbol"),
        pytest.param({"collision_adapter_all": True}, {"native_round", "native_add"}, id="all-direct-symbols"),
    ],
)
def test_a_selected_symbol_moves_its_native_declaration_into_the_adapter_unit(planner_options, adapted):
    sources = _sources_by_name(_generated(**planner_options))
    binding = sources["collide_wrapper.c"]
    adapters = sources.get("collide_adapters.c")

    assert (adapters is not None) == bool(adapted)
    if adapters is not None:
        # The adapter unit reaches the user symbol from a unit without Python.h.
        assert "Python.h" not in adapters
    for symbol, (declaration, forward) in _DECLARATIONS.items():
        if symbol in adapted:
            # The binding never declares the colliding identifier itself.
            assert declaration not in binding
            assert f"prik_collision_adapter_{symbol}(" in binding
            assert declaration in adapters
            assert forward in adapters
        else:
            assert declaration in binding
            assert f"prik_collision_adapter_{symbol}" not in binding


def test_collision_adapter_all_leaves_a_fortran_bind_c_entrypoint_alone():
    """A bind(C) procedure reaches a direct entrypoint but carries no exact C declaration."""
    module = fortran_file_to_semantic_modules(
        parse_fortran_source(
            """module m
  use iso_c_binding
  implicit none
contains
  real(c_double) function scaled(x) bind(c, name="scaled")
    real(c_double), value :: x
    scaled = 2.0_c_double * x
  end function scaled
end module m
"""
        )
    )[0]
    complete_semantic_policies(module)
    generated = WrapperGenerator().generate(WrapperPlanner(collision_adapter_all=True).build(module))

    assert "m_adapters.c" not in _sources_by_name(generated)
