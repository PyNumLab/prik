"""Binding lowering consumes exact array element types completed before planning.

The rows are identities whose NumPy storage is not implied by width alone:
plain ``char``, ``int`` versus ``long`` versus ``long long``, and the
extended-precision real and complex types.
"""

import pytest

from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.semantics.native_contract import validate_pyi_native_contract


def _plan_and_binding(text: str):
    module = pyi_text_to_semantic_module(text, module_name="exact", native_language="c")
    validate_pyi_native_contract([module])
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    generated = WrapperGenerator().generate(plan)
    binding = next(source.text for source in generated.sources if source.path.suffix == ".c")
    return plan, binding


@pytest.mark.parametrize(
    ("native_type", "annotation", "c_type", "numpy_macro", "numpy_name"),
    [
        ("CChar", "Int8", "char", "NPY_BYTE", "numpy.byte"),
        ("CInt", "Int32", "int", "NPY_INT", "numpy.intc"),
        ("CLong", "Int64", "long", "NPY_LONG", "numpy.long"),
        ("CLongLong", "Int64", "long long", "NPY_LONGLONG", "numpy.longlong"),
        (
            "CUnsignedLongLong",
            "UInt64",
            "unsigned long long",
            "NPY_ULONGLONG",
            "numpy.ulonglong",
        ),
        ("CLongDouble", "Float128", "long double", "NPY_LONGDOUBLE", "numpy.longdouble"),
        (
            "CLongDoubleComplex",
            "Complex256",
            "long double _Complex",
            "NPY_CLONGDOUBLE",
            "numpy.clongdouble",
        ),
    ],
)
def test_exact_native_array_types_require_the_corresponding_numpy_c_storage(
    native_type,
    annotation,
    c_type,
    numpy_macro,
    numpy_name,
):
    plan, binding = _plan_and_binding(
        f"""from prik.contracts import Arg, {native_type}, {annotation}, native_call
@native_call([{native_type}(Arg(0))])
def update(values: {annotation}[:]) -> None: ...
"""
    )
    function = plan.namespaces[0].functions[0]

    assert function.binding.docstring is not None
    assert f"Accepts exact {numpy_name} element storage" in function.binding.docstring
    assert f"void update({c_type} * values);" in binding
    assert f"prik_bind_array(bound_values_obj, {numpy_macro}," in binding
    assert f'"{numpy_name}", ' in binding
    assert '"values", ' in binding
