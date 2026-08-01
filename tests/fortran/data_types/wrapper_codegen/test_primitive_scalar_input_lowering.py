"""Typed scalar input lowering through the public generator."""

from __future__ import annotations

import pytest

from tests.fortran._support.ownership_policy import parse_pyi_text
from x2py.semantics.policy_completion import complete_semantic_policies
from x2py.wrapper_codegen import WrapperCodeGenerator, WrapperPlanner


@pytest.mark.parametrize(
    ("type_name", "c_type", "helper_suffix"),
    [
        ("Bool", "bool", "NPY_BOOL"),
        ("Int8", "int8_t", "NPY_INT8"),
        ("Int16", "int16_t", "NPY_INT16"),
        ("Int32", "int32_t", "NPY_INT32"),
        ("Int64", "int64_t", "NPY_INT64"),
        ("Float32", "float", "NPY_FLOAT32"),
        ("Float64", "double", "NPY_FLOAT64"),
        ("Complex64", "float complex", "NPY_COMPLEX64"),
        ("Complex128", "double complex", "NPY_COMPLEX128"),
    ],
)
def test_scalar_input_registry_lowers_completed_type_into_the_native_support_api(type_name, c_type, helper_suffix):
    module = parse_pyi_text(f"def identity(x: {type_name}) -> {type_name}: ...", module_name="scalar_input")
    complete_semantic_policies(module)
    plan = WrapperPlanner().build(module)

    artifacts = WrapperCodeGenerator().generate(plan)
    c_source = next(source.text for source in artifacts.sources if source.path.suffix == ".c")

    assert f"{c_type} bound_x;" in c_source
    assert (
        f"if (x2py_{helper_suffix.casefold().removeprefix('npy_')}_unpack_exact(bound_x_obj, &bound_x) < 0)" in c_source
    )
    assert "if (!PyErr_Occurred())" in c_source


def test_binding_locals_are_isolated_from_identifiers_imported_by_c_headers():
    module = parse_pyi_text("def identity(complex: Float64) -> Float64: ...", module_name="header_names")
    complete_semantic_policies(module)

    c_source = next(
        source.text
        for source in WrapperCodeGenerator().generate(WrapperPlanner().build(module)).sources
        if source.path.suffix == ".c"
    )

    assert '#include "binding_support/x2py_binding.h"' in c_source
    assert "double bound_complex;" in c_source
    assert "x2py_float64_unpack_exact(bound_complex_obj, &bound_complex)" in c_source
    assert "double complex;" not in c_source
