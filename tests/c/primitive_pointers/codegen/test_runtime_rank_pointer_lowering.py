"""Direct C pointer lowering consumes completed runtime-rank policy."""

from prik.parsers.c import parse_c_file
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.policy.models import ArrayPythonLayout
from prik.semantics.c2ir import c_file_to_semantic_module


def test_direct_c_binding_keeps_pointer_abi_and_uses_completed_runtime_rank_bounds():
    module = c_file_to_semantic_module(
        parse_c_file("double native_read(const double *input) { return *input; }", filename="read.c")
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    generated = WrapperGenerator().generate(plan)
    binding = next(source.text for source in generated.sources if source.path.suffix == ".c")
    function = plan.namespaces[0].functions[0]
    array = function.arguments[0].array

    assert plan.bridge is None
    assert plan.entrypoint.native_languages == ("c",)
    assert array.rank is None
    assert (array.minimum_rank, array.maximum_rank) == (0, 15)
    assert "double native_read(const double * input);" in binding
    assert array.python_layout is ArrayPythonLayout.ANY_STRIDED
    assert ("prik_array_validate(bound_input_obj, NPY_FLOAT64, 0, 15, PRIK_ARRAY_LAYOUT_ANY_STRIDED, 0, 0") in binding
    assert "result = native_read(bound_input);" in binding
    assert "bind_c_read_wrapper" not in binding
