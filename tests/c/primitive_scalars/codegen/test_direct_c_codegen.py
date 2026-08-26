"""C declaration provenance is consumed by direct binding generation."""

from prik.parsers.c import parse_c_file
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.semantics.c2ir import c_file_to_semantic_module


def test_direct_c_binding_keeps_qualifiers_pointer_depth_and_user_symbol():
    module = c_file_to_semantic_module(
        parse_c_file("double native_read(const double *input) { return *input; }", filename="read.c")
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    generated = WrapperGenerator().generate(plan)
    binding = next(source.text for source in generated.sources if source.path.suffix == ".c")

    assert plan.bridge is None
    assert plan.entrypoint.native_languages == ("c",)
    assert "double native_read(const double * input);" in binding
    assert "native_read(&bound_input)" in binding
    assert "bind_c_read_wrapper" not in binding
