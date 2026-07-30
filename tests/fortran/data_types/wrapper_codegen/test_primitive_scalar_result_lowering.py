"""Typed direct primitive-scalar result lowering through the public generator."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


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

    assert f"PyObject * result_obj = x2py_scalar_to_{result_kind}({numpy_type}, &result);" in c_source
    assert "return result_obj;" in c_source
