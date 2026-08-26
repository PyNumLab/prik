"""A positional-only binding parses its call tuple and installs no keyword table."""

from prik.parsers.c import parse_c_file
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.semantics.c2ir import c_file_to_semantic_module

# Reserved parameter spellings are exactly what a real system header supplies.
_SOURCE = "double blend(double __x, double __y) { return __x + __y; }\n"


def _binding(**options) -> str:
    module = c_file_to_semantic_module(parse_c_file(_SOURCE, filename="surface.c"))
    complete_semantic_policies(module, **options)
    generated = WrapperGenerator().generate(WrapperPlanner().build(module))
    return next(source.text for source in generated.sources if source.path.suffix == ".c")


def test_a_positional_only_binding_takes_no_keyword_dictionary():
    binding = _binding(positional_only=True)

    assert "static PyObject * wrap_blend(PyObject * self, PyObject * args) {" in binding
    assert 'if (!PyArg_ParseTuple(args, "OO", &bound_arg0_obj, &bound_arg1_obj)) return NULL' in binding
    assert "kwlist" not in binding
    assert "METH_KEYWORDS" not in binding

    # The native declaration keeps the header's spelling; the Python surface does not.
    assert "double blend(double __x, double __y);" in binding
    assert "blend(arg0, arg1) -> float64" in binding
    assert "for argument arg0." in binding
    assert "__x" not in binding.split("static PyObject * wrap_blend")[1]


def test_the_default_binding_still_accepts_keywords_under_the_declared_names():
    binding = _binding()

    assert "static PyObject * wrap_blend(PyObject * self, PyObject * args, PyObject * kwargs) {" in binding
    assert 'static char * kwlist[] = {"__x", "__y", NULL};' in binding
    assert "METH_VARARGS | METH_KEYWORDS" in binding
