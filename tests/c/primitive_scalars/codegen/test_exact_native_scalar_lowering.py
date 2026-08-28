"""Binding lowering consumes exact scalar types completed before planning."""

import pytest

from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner
from prik.policy.completion import complete_semantic_policies
from prik.semantics.native_contract import validate_pyi_native_contract


def _binding(text: str) -> str:
    module = pyi_text_to_semantic_module(text, module_name="exact", native_language="c")
    validate_pyi_native_contract([module])
    complete_semantic_policies(module)
    generated = WrapperGenerator().generate(WrapperPlanner().build(module))
    return next(source.text for source in generated.sources if source.path.suffix == ".c")


def _plan_and_binding(text: str):
    module = pyi_text_to_semantic_module(text, module_name="exact", native_language="c")
    validate_pyi_native_contract([module])
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    generated = WrapperGenerator().generate(plan)
    binding = next(source.text for source in generated.sources if source.path.suffix == ".c")
    return plan, binding


def test_exact_value_argument_and_result_use_native_prototype_and_directional_casts():
    binding = _binding(
        """from prik.contracts import Arg, CLongLong, Int64, Return, native_call
@native_call([CLongLong(Arg(0))], result=CLongLong(Return(0)))
def convert(value: Int64) -> Int64: ...
"""
    )

    assert "long long convert(long long value);" in binding
    assert "result = (int64_t)convert((long long)bound_value);" in binding


def test_exact_address_argument_materializes_native_storage_before_taking_its_address():
    binding = _binding(
        """from prik.contracts import Addr, Arg, CLongLong, Int64, Returns, native_call
@native_call([Addr(CLongLong(Arg(0)))])
def update(value: Int64) -> Returns["value", Int64]: ...
"""
    )

    assert "void update(long long * value);" in binding
    assert "long long bound_value;" in binding
    assert "bound_value = (long long)bound_value_converted;" in binding
    assert "update(&bound_value);" in binding
    assert "int64_t bound_value_contract = (int64_t)bound_value;" in binding
    assert "prik_int64_to_numpy(&bound_value_contract)" in binding


def test_exact_output_parameter_uses_native_storage_then_converts_the_python_result():
    binding = _binding(
        """from prik.contracts import CLongLong, Int64, Return, native_call
@native_call([CLongLong(Return("out", 0))])
def read() -> Int64: ...
"""
    )

    assert "void read(long long * out);" in binding
    assert "long long out;" in binding
    assert "read(&out);" in binding
    assert "int64_t out_contract = (int64_t)out;" in binding


@pytest.mark.parametrize(
    ("native_type", "annotation", "c_type", "numpy_macro", "numpy_name"),
    [
        ("CChar", "Int8", "char", "NPY_BYTE", "numpy.byte"),
        ("CSignedChar", "Int8", "signed char", "NPY_BYTE", "numpy.byte"),
        ("CUnsignedChar", "UInt8", "unsigned char", "NPY_UBYTE", "numpy.ubyte"),
        ("CShort", "Int16", "short", "NPY_SHORT", "numpy.short"),
        ("CUnsignedShort", "UInt16", "unsigned short", "NPY_USHORT", "numpy.ushort"),
        ("CInt", "Int32", "int", "NPY_INT", "numpy.intc"),
        ("CUnsignedInt", "UInt32", "unsigned int", "NPY_UINT", "numpy.uintc"),
        ("CLong", "Int64", "long", "NPY_LONG", "numpy.long"),
        ("CUnsignedLong", "UInt64", "unsigned long", "NPY_ULONG", "numpy.ulong"),
        ("CLongLong", "Int64", "long long", "NPY_LONGLONG", "numpy.longlong"),
        (
            "CUnsignedLongLong",
            "UInt64",
            "unsigned long long",
            "NPY_ULONGLONG",
            "numpy.ulonglong",
        ),
        ("CFloat", "Float32", "float", "NPY_FLOAT", "numpy.single"),
        ("CDouble", "Float64", "double", "NPY_DOUBLE", "numpy.double"),
        ("CLongDouble", "Float128", "long double", "NPY_LONGDOUBLE", "numpy.longdouble"),
        ("CFloatComplex", "Complex64", "float _Complex", "NPY_CFLOAT", "numpy.csingle"),
        ("CDoubleComplex", "Complex128", "double _Complex", "NPY_CDOUBLE", "numpy.cdouble"),
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
    assert '"values", NULL,' in binding
