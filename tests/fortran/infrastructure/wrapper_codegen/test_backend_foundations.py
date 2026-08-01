"""Tests for isolated primitive backend foundations."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.fortran._support.wrapper_build import REPO_ROOT
from x2py.wrapper_codegen import (
    BackendScalarType,
    BindingModulePlan,
    BridgeModulePlan,
    CDeclaration,
    CExpressionStatement,
    CFunction,
    CFunctionPrototype,
    CHeader,
    CInclude,
    CModule,
    CParameter,
    CReturn,
    CSourcePrinter,
    CodeExpression,
    FortranAssignment,
    FortranCall,
    FortranFunction,
    FortranIf,
    FortranModule,
    FortranParameter,
    FortranPointerAssignment,
    FortranSourcePrinter,
    FortranUse,
    ModulePlan,
    NamespacePlan,
    UnsupportedWrapperCodegenNodeError,
)


def test_source_printers_render_complete_c_header_and_fortran_modules():
    float64 = BackendScalarType(
        semantic_name="Float64",
        c_spelling="double",
        fortran_spelling="real(c_double)",
        python_parse_unit="d",
        numpy_type_macro="NPY_FLOAT64",
    )
    parameters = (CParameter("self", "PyObject *"), CParameter("args", "PyObject *"))
    c_function = CFunction(
        name="wrap_add_r8",
        return_type="PyObject *",
        parameters=parameters,
        storage="static",
        body=(
            CDeclaration("x", float64.c_spelling, CodeExpression("0.0")),
            CExpressionStatement(CodeExpression("import_array()")),
            CReturn(CodeExpression("NULL")),
        ),
    )
    c_header = CHeader(
        guard="FMATH_WRAPPER_H",
        includes=(CInclude("Python.h"),),
        prototypes=(CFunctionPrototype("wrap_add_r8", "PyObject *", parameters),),
    )
    c_module = CModule(
        name="fmath_wrapper",
        includes=(
            CInclude("Python.h"),
            CInclude("numpy/arrayobject.h"),
            CInclude("fmath_wrapper.h", system=False),
        ),
        functions=(c_function,),
    )
    fortran_module = FortranModule(
        name="bind_c_fmath_wrapper",
        uses=(FortranUse("iso_c_binding", ("c_double",)),),
        procedures=(
            FortranFunction(
                name="bind_c_add_r8",
                parameters=(FortranParameter("x", float64.fortran_spelling, ("value",)),),
                result_name="result",
                result_type=float64.fortran_spelling,
                bind_name="ADD_R8",
                body=(FortranAssignment("result", CodeExpression("x")),),
            ),
        ),
    )
    c_header_source = CSourcePrinter().doprint(c_header)
    c_source = CSourcePrinter().doprint(c_module)
    fortran_source = FortranSourcePrinter().doprint(fortran_module)

    assert "#ifndef FMATH_WRAPPER_H" in c_header_source
    assert "PyObject * wrap_add_r8(PyObject * self, PyObject * args);" in c_header_source
    assert '#include "fmath_wrapper.h"' in c_source
    assert "static PyObject * wrap_add_r8(PyObject * self, PyObject * args)" in c_source
    assert "double x = 0.0;" in c_source
    assert "import_array();" in c_source
    assert "use iso_c_binding, only: c_double" in fortran_source
    assert 'function bind_c_add_r8(x) result(result) bind(c, name="ADD_R8")' in fortran_source
    assert "real(c_double), value :: x" in fortran_source


def test_source_printers_reject_wrapper_plan_models():
    plan = ModulePlan(
        owner_path="demo",
        binding=BindingModulePlan("demo"),
        bridge=BridgeModulePlan("demo"),
        namespaces=(NamespacePlan(owner_path="demo", python_path=()),),
    )

    with pytest.raises(UnsupportedWrapperCodegenNodeError):
        CSourcePrinter().doprint(plan)
    with pytest.raises(UnsupportedWrapperCodegenNodeError):
        FortranSourcePrinter().doprint(plan)


def test_fortran_source_printer_wraps_long_parenthesized_call_arguments():
    slices = ", ".join(f"1:values_upper_bound_{axis} + 1:values_stride_{axis}" for axis in range(4))
    source = FortranSourcePrinter().doprint(
        FortranCall(
            "native_scale",
            (
                CodeExpression(f"values_base({slices})"),
                CodeExpression(f"out_base({slices})"),
            ),
        )
    )

    assert "& values_base(&" in source
    assert "&   1:values_upper_bound_3 + 1:values_stride_3), &" in source
    assert "& out_base(&" in source
    assert max(map(len, source.splitlines())) <= 124


def test_fortran_source_printer_wraps_long_pointer_array_sections():
    slices = ", ".join(f"1:values_upper_bound_{axis} + 1:values_stride_{axis}" for axis in range(4))

    source = FortranSourcePrinter().doprint(
        FortranPointerAssignment("values", CodeExpression(f"values_base({slices})"))
    )

    assert source.startswith("values => values_base(&")
    assert "& 1:values_upper_bound_3 + 1:values_stride_3)" in source
    assert max(map(len, source.splitlines())) <= 132


def test_fortran_source_printer_formats_unstructured_long_statements_automatically():
    expression = " + ".join(f"value_{index}" for index in range(20))

    source = FortranSourcePrinter().doprint(FortranAssignment("result", CodeExpression(expression)))

    assert " &\n  & " in source
    assert max(map(len, source.splitlines())) <= 132


def test_fortran_source_printer_formats_after_nested_indentation_is_complete():
    expression = " + ".join(f"value_{index}" for index in range(20))
    source = FortranSourcePrinter().doprint(
        FortranModule(
            "nested_lines",
            procedures=(
                FortranFunction(
                    "nested",
                    body=(
                        FortranIf(
                            CodeExpression("outer"),
                            body=(
                                FortranIf(
                                    CodeExpression("inner"),
                                    body=(FortranAssignment("result", CodeExpression(expression)),),
                                ),
                            ),
                        ),
                    ),
                    is_subroutine=True,
                ),
            ),
        )
    )

    assert "       & " in source
    assert max(map(len, source.splitlines())) <= 132


def test_fortran_source_printer_rejects_an_overlong_token_without_a_safe_break():
    with pytest.raises(ValueError, match=r"free-form limit is 132"):
        FortranSourcePrinter().doprint(FortranAssignment("result", CodeExpression("x" * 134)))


def test_source_printers_do_not_import_wrapper_plan_models():
    path = REPO_ROOT / "x2py" / "wrapper_codegen" / "printers" / "source_printers.py"
    imports = {
        node.module
        for node in ast.walk(ast.parse(Path(path).read_text(encoding="utf-8")))
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert "x2py.wrapper_codegen.plan" not in imports
