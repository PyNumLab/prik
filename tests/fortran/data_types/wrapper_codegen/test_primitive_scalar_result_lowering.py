"""Typed direct primitive-scalar result lowering through the public generator."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from prik.semantics.policy_completion import complete_semantic_policies
from prik.semantics.wrapper_policy import DirectResultABI
from prik.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


@pytest.mark.parametrize(
    ("type_name", "numpy_type", "result_kind"),
    [
        ("Bool", "NPY_BOOL", "python"),
        ("Int32", "NPY_INT32", "python"),
        ("Float32", "NPY_FLOAT32", "numpy"),
        ("Float64", "NPY_FLOAT64", "python"),
        ("Complex64", "NPY_COMPLEX64", "numpy"),
        ("Complex128", "NPY_COMPLEX128", "python"),
    ],
)
def test_direct_scalar_result_registry_projects_supported_type_facts(type_name, numpy_type, result_kind):
    module = parse_pyi_text(f"def identity(x: {type_name}) -> {type_name}: ...", module_name="scalar_result")
    complete_semantic_policies(module)
    artifacts = WrapperCodeGenerator().generate(WrapperPlanner().build(module))
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    helper_suffix = numpy_type.casefold().removeprefix("npy_")
    assert f"PyObject * result_obj = prik_{helper_suffix}_to_{result_kind}(&result);" in c_source
    assert "return result_obj;" in c_source


def test_direct_bool_result_normalizes_the_fortran_truth_bit_before_c_conversion():
    module = parse_pyi_text(
        "def not_flag(value: Bool) -> Bool: ...",
        module_name="logical_result",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    result = plan.namespaces[0].functions[0].results[0]

    assert result.direct_result_abi is DirectResultABI.LOGICAL_LOW_BIT_INT8

    artifacts = WrapperCodeGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")
    fortran_source = next(source.text for source in artifacts.sources if source.path.suffix == ".f90")

    assert "int8_t bind_c_not_flag(bool value);" in c_source
    assert "result = (bool)bind_c_not_flag(bound_value);" in c_source
    assert "integer(c_int8_t) :: result" in fortran_source
    assert "logical(c_bool) :: c_result" in fortran_source
    assert "c_result = native_not_flag(value)" in fortran_source
    assert "result = iand(transfer(c_result, 0_c_int8_t), 1_c_int8_t)" in fortran_source


def test_generator_rejects_a_non_normalized_direct_bool_result_abi():
    module = parse_pyi_text(
        "def not_flag(value: Bool) -> Bool: ...",
        module_name="logical_result",
    )
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)
    plan.namespaces[0].functions[0].results[0].direct_result_abi = DirectResultABI.NATIVE_SCALAR

    with pytest.raises(ValueError, match="invalid-direct-result-abi"):
        WrapperCodeGenerator().generate(plan)
