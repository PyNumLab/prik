"""Wrapper lowering selected by completed module initializer policy."""

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


def test_module_variable_literal_families_select_their_c_spelling():
    module = parse_pyi_text(
        """
enabled: Bool = True
count: Int32 = 3
scale: Float64 = 1.5
phase: Complex128 = 1 + 2j
""",
        module_name="literal_state",
    )
    complete_semantic_policies(module)

    artifacts = WrapperCodeGenerator().generate(WrapperPlanner().build(module))
    c_source = next(item.text for item in artifacts.sources if item.path.name.endswith(".c"))

    assert "bind_c_set_enabled(true);" in c_source
    assert "bind_c_set_count(3);" in c_source
    assert "bind_c_set_scale(1.5);" in c_source
    assert "bind_c_set_phase((1.0 + 2.0 * I));" in c_source
