"""A collision-adapted symbol is reached from a unit that excludes Python.h."""

from prik.parsers.c import parse_c_file
from prik.parsers.fortran import parse_fortran_file as parse_fortran_source
from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.semantics.c2ir import c_file_to_semantic_module
from prik.semantics.fortran2ir import fortran_file_to_semantic_modules
from prik.semantics.native_contract import validate_pyi_native_contract

_SOURCE = """long long native_round(double value) { return (long long)value; }
double native_add(double left, double right) { return left + right; }
"""


def _generated(**planner_options):
    module = c_file_to_semantic_module(parse_c_file(_SOURCE, filename="collide.c"))
    complete_semantic_policies(module)
    return WrapperGenerator().generate(WrapperPlanner(**planner_options).build(module))


def _sources_by_name(generated):
    return {source.path.name: source.text for source in generated.sources if source.path.suffix == ".c"}


def test_unselected_symbols_keep_the_direct_declaration_and_emit_no_adapter_unit():
    sources = _sources_by_name(_generated())

    assert "collide_adapters.c" not in sources
    assert "long long native_round(double value);" in sources["collide_wrapper.c"]


def test_a_selected_symbol_moves_its_native_declaration_into_the_adapter_unit():
    sources = _sources_by_name(_generated(collision_adapters=("native_round",)))
    binding = sources["collide_wrapper.c"]
    adapters = sources["collide_adapters.c"]

    # The binding never declares the colliding identifier itself.
    assert "long long native_round(double value);" not in binding
    assert "long long prik_collision_adapter_native_round(double value);" in binding
    assert "prik_collision_adapter_native_round(" in binding

    # The adapter unit declares it, forwards to it, and includes no Python header.
    assert "long long native_round(double value);" in adapters
    assert "return (native_round)(value);" in adapters
    assert "Python.h" not in adapters

    # An unselected symbol in the same module keeps its direct declaration.
    assert "double native_add(double left, double right);" in binding


def test_collision_adapter_all_selects_every_direct_c_symbol():
    sources = _sources_by_name(_generated(collision_adapter_all=True))
    binding = sources["collide_wrapper.c"]
    adapters = sources["collide_adapters.c"]

    assert "prik_collision_adapter_native_round(" in binding
    assert "prik_collision_adapter_native_add(" in binding
    assert "return (native_add)(left, right);" in adapters


def test_two_callables_naming_one_symbol_define_the_forwarder_once():
    """Several Python names may bind one native symbol; the forwarder is one definition."""
    module = pyi_text_to_semantic_module(
        """from prik.contracts import Float64, bind

def native_add(left: Float64, right: Float64) -> Float64: ...

@bind("native_add")
def add_alias(left: Float64, right: Float64) -> Float64: ...
""",
        module_name="collide",
        native_language="c",
    )
    validate_pyi_native_contract([module])
    complete_semantic_policies(module)
    generated = WrapperGenerator().generate(WrapperPlanner(collision_adapter_all=True).build(module))
    adapters = _sources_by_name(generated)["collide_adapters.c"]

    assert adapters.count("prik_collision_adapter_native_add(double left, double right) {") == 1
    assert adapters.count("double native_add(double left, double right);") == 1


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
