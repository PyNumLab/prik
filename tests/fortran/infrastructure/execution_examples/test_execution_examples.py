"""Output contracts for the contributor guide's executable modules.

Each test owns one production file's ``if __name__ == "__main__"`` example.
Feature tests exercise the underlying behavior separately; this module keeps
the executable architecture inventory visible and auditable in one place.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def _run_example(relative_path: str, *arguments: str) -> str:
    completed = subprocess.run(
        [sys.executable, relative_path, *arguments],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout


def test_fortran_root_cli_execution_example():
    assert _run_example("prik/cli.py", "--version") == "prik 0.2.1\n"


def test_fortran_utilities_stage_values_execution_example():
    assert _run_example("prik/utilities/stage_values.py") == (
        "Editable parser output: geometry -> ['scale', 'norm']\n"
        "Frozen consumer input: geometry -> ('scale', 'norm')\n"
        "Mutation rejected: ParserOutput is frozen by its consuming stage\n"
    )


def test_fortran_contracts_init_execution_example():
    assert _run_example("prik/contracts/__init__.py") == (
        "Float64() -> np.float64(0.0) (float64)\n"
        "Float64[:, :] -> element=Float64, rank=2, "
        "shape=(slice(None, None, None), slice(None, None, None))\n"
    )


def test_fortran_compiler_compiler_profiles_execution_example():
    assert _run_example("prik/compiler/compiler_profiles.py") == (
        "Selected family: gfortran\nCompiler profile: GNU\nMatching C executable: gcc\nFortran module-output flag: -J\n"
    )


def test_fortran_compiler_objects_execution_example():
    assert _run_example("prik/compiler/objects.py") == (
        "Compile input: generated/bridge.f90 -> build/bridge.o\n"
        "Language: fortran\n"
        "Flags: ('-O2',)\n"
        "Include directories: build/modules\n"
    )


def test_fortran_compiler_compilers_execution_example():
    assert _run_example("prik/compiler/compilers.py") == (
        "Compiler profile: GNU\n"
        "Compile input: demo.c -> demo.o\n"
        "Recorded without execution: True\n"
        "Contains compile switch: True\n"
        "Contains requested flag: True\n"
        "Commands recorded: 1\n"
    )


def test_fortran_compiler_native_support_execution_example():
    assert _run_example("prik/compiler/native_support.py") == (
        "Installed directory: binding_support\nBinding header present: True\nNumPy version header present: True\n"
    )


def test_fortran_preprocessing_source_execution_example():
    assert _run_example("prik/preprocessing/source.py") == (
        "Before Fortran include expansion:\n"
        "module greeting\n"
        "include 'constants.inc'\n"
        "contains\n"
        "subroutine show_answer()\n"
        "print *, answer\n"
        "end subroutine show_answer\n"
        "end module greeting\n"
        "\n"
        "After Fortran include expansion:\n"
        "module greeting\n"
        "integer, parameter :: answer = 42\n"
        "contains\n"
        "subroutine show_answer()\n"
        "print *, answer\n"
        "end subroutine show_answer\n"
        "end module greeting\n"
        "Native includes: 1; diagnostics: 0\n"
        "\n"
        "Before C compiler preprocessing:\n"
        '#include "state.h"\n'
        "int state_id = STATE_ID;\n"
        "\n"
        "After C compiler preprocessing:\n"
        "int state_id = 42;\n"
    )


def test_fortran_preprocessing_c_execution_example():
    assert _run_example("prik/preprocessing/c.py") == (
        "Raw directive: #pragma once\n"
        "Includes: local state.h, system stddef.h\n"
        "Diagnostic: C_UNRESOLVED_INCLUDE\n"
        "Resolved include: state.h (diagnostics: 0)\n"
    )


def test_fortran_preprocessing_fortran_execution_example():
    assert _run_example("prik/preprocessing/fortran.py") == (
        "Expanded parser input:\n"
        "module geometry\n"
        "integer, parameter :: dimensions = 3\n"
        "end module geometry\n"
        "Native include dependencies: 1\n"
        "Generated source mappings: 5\n"
        "Diagnostics: 0\n"
    )


def test_fortran_preprocessing_probes_c_types_execution_example():
    output = _run_example("prik/preprocessing/probes/c_types.py").strip()
    label, separator, raw_value = output.partition(": ")

    assert label == "int"
    assert separator == ": "
    assert raw_value.endswith("-bit signed")
    assert int(raw_value.removesuffix("-bit signed")) >= 16


def test_fortran_preprocessing_probes_fortran_types_execution_example():
    output = _run_example("prik/preprocessing/probes/fortran_types.py").strip()
    label, separator, raw_value = output.partition(" = ")

    assert label == "selected_int_kind(9)"
    assert separator == " = "
    assert int(raw_value) > 0


def test_fortran_parsers_c_lexer_execution_example():
    assert _run_example("prik/parsers/c/lexer.py") == (
        "Identifier tokens: struct point double x double y double norm struct point value\n"
        "Segment at line 2: struct point { double x; double y; } [;]\n"
        "Segment at line 3: double norm(struct point value) [;]\n"
    )


def test_fortran_parsers_c_parser_execution_example():
    assert _run_example("prik/parsers/c/parser.py") == (
        "Parsed: state_api.h\n"
        "Typedef: api_size -> unsigned long\n"
        "Struct: state (id)\n"
        "Function: count() -> api_size\n"
        "Function: step(value) -> pointer to struct state\n"
    )


def test_fortran_parsers_c_type_resolver_execution_example():
    assert _run_example("prik/parsers/c/type_resolver.py") == (
        "Tag reference:\nstate_handle -> struct state\nTypedef chain:\nstate_alias -> raw_state -> struct state\n"
    )


def test_fortran_parsers_c_cli_execution_example():
    assert _run_example("prik/parsers/c/cli.py") == (
        "File: geometry.h\n"
        "  Language: c\n"
        "  Functions: 1\n"
        "    - norm\n"
        "  Structs: 1\n"
        "    - point\n"
        "  Unions: 0\n"
        "  Enums: 0\n"
        "  Typedefs: 0\n"
        "  Variables: 0\n"
        "  Macros: 0\n"
        "  Includes: 0\n"
        "  Diagnostics: 0\n"
    )


def test_fortran_parsers_fortran_lexer_execution_example():
    assert _run_example("prik/parsers/fortran/lexer.py") == (
        "Detected source form: free\n"
        "line 1: subroutine shift(value,offset)\n"
        "line 3:   real, intent(inout) :: value\n"
        "line 4:   real, intent(in) :: offset\n"
        "line 5: end subroutine shift\n"
    )


def test_fortran_parsers_fortran_parser_execution_example():
    assert _run_example("prik/parsers/fortran/parser.py") == (
        "Module: metrics\nParameter: n = 4\nProcedure: scale(values: real[1])\n"
    )


def test_fortran_parsers_fortran_type_resolver_execution_example():
    assert _run_example("prik/parsers/fortran/type_resolver.py") == (
        "integer(4) -> 4\n"
        "real(kind=selected_real_kind(15, 307)) -> selected_real_kind(15, 307)\n"
        "character(len=16, kind=c_char) -> len=16, kind=c_char\n"
    )


def test_fortran_parsers_fortran_cli_execution_example():
    assert _run_example("prik/parsers/fortran/cli.py") == (
        "File: geometry.f90\n"
        "  Modules: 1\n"
        "    - module geometry (vars=0, uses=0)\n"
        "      Procedures: 1\n"
        "        - function norm(value:real[0]) -> real[0]\n"
    )


def test_fortran_parsers_pyi_parser_execution_example():
    assert _run_example("prik/parsers/pyi/parser.py") == (
        "Parsed AST: Module\nFunction node: scale\nArgument annotation: Float64\nSemantic conversion performed: False\n"
    )


def test_fortran_semantics_models_execution_example():
    assert _run_example("prik/semantics/models.py") == (
        "Semantic module: geometry\n"
        "Function: scale -> native SCALE\n"
        "Argument: values: Float64, rank=1, shape=('n',), order=F\n"
        "Source provenance: fortran real\n"
    )


def test_fortran_semantics_scalar_types_execution_example():
    assert _run_example("prik/semantics/scalar_types.py") == (
        "Float64: family=real, storage=64 bits\n"
        "Int: family=signed_integer, storage=target-dependent\n"
        "Backend spelling stored here: False\n"
    )


def test_fortran_semantics_c2ir_execution_example():
    assert _run_example("prik/semantics/c2ir.py") == "math.scale(value): Int <- Int\n"


def test_fortran_semantics_fortran2ir_execution_example():
    assert _run_example("prik/semantics/fortran2ir.py") == ("math.scale(value): Float64 via reference storage\n")


def test_fortran_semantics_pyi2ir_execution_example():
    assert _run_example("prik/semantics/pyi2ir.py") == "math.scale(value): Float64 -> Float64\n"


def test_fortran_semantics_ownership_metadata_execution_example():
    assert _run_example("prik/semantics/ownership_metadata.py") == (
        "Raw ownership request: owner=caller, transfer=in_place, destruction=caller\n"
        "Pointer contract: nullable=True, lifetime=owner, reassociation=forbidden\n"
        "Completed lowering action present: False\n"
    )


def test_fortran_semantics_native_array_handles_execution_example():
    assert _run_example("prik/semantics/native_array_handles.py") == (
        "Descriptor kind: allocatable\n"
        "Data facet: Float64, rank=2, shape=('rows', 'columns')\n"
        "Element facet: Float64, rank=0\n"
        "Handle marker retained by data facet: False\n"
    )


def test_fortran_semantics_native_contract_execution_example():
    assert _run_example("prik/semantics/native_contract.py") == (
        "Prepared origin: fortran module math\n"
        "Valid contract issues: 0\n"
        "Invalid contract issue: pyi_native_type_missing at math.broken.value\n"
    )


def test_fortran_policy_models_execution_example():
    assert _run_example("prik/policy/models.py") == (
        "Array policy: rank=2, shape=('rows', 'columns'), order=F\n"
        "Lifecycle policy: copy_out writeback via copy_in_out\n"
        "Completed record mutation rejected: True\n"
    )


def test_fortran_policy_ownership_execution_example():
    assert _run_example("prik/policy/ownership.py") == (
        "before: math.scale(value): Float64 semantic IR\nafter: scalar/caller/call_local; scalar_value -> pass_value\n"
    )


def test_fortran_policy_construction_execution_example():
    assert _run_example("prik/policy/construction.py") == (
        "before: math.scale(value): Float64 semantic IR\n"
        "after: direct_transfer; result=native_scalar; native=pass_value\n"
    )


def test_fortran_policy_completion_execution_example():
    assert _run_example("prik/policy/completion.py") == (
        "before: math.scale(value): Float64 semantic IR\nafter: math.scale(value): scalar_value -> pass_value\n"
    )


def test_fortran_policy_exports_execution_example():
    assert _run_example("prik/policy/exports.py") == (
        "Native semantic owner: math.SCALE_VALUE\n"
        "Python export: linear_algebra.scale_value\n"
        "Completed policy type: PythonExportPolicy\n"
    )


def test_fortran_policy_native_array_handles_execution_example():
    assert _run_example("prik/policy/native_array_handles.py") == (
        "Handle policy: pointer/pointer, storage=alias\n"
        "Allowed operations: to_numpy, nullify\n"
        "Array ABI: descriptor\n"
        "Selected build header: ISO_Fortran_binding.h\n"
    )


def test_fortran_planning_models_execution_example():
    assert _run_example("prik/planning/models.py") == (
        "Plan owner: demo\nPython export: ping\nNative procedure: PING\nNative slots: 0\n"
    )


def test_fortran_planning_planner_execution_example():
    assert _run_example("prik/planning/planner.py") == (
        "Plan owner: planner_demo\n"
        "Python export: double_value\n"
        "Native target: DOUBLE_VALUE\n"
        "Conversion order: ('planner_demo.double_value.value',)\n"
    )


def test_fortran_codegen_nodes_execution_example():
    assert _run_example("prik/codegen/nodes.py") == (
        "C node tree: CModule -> wrap_ping -> CReturn\n"
        "Fortran node tree: FortranModule -> bind_c_ping -> FortranCall\n"
        "Source text rendered: False\n"
    )


def test_fortran_codegen_primitive_scalar_types_execution_example():
    assert _run_example("prik/codegen/primitive_scalar_types.py") == (
        "Float64: C=double; Fortran=real(c_double); NumPy=numpy.float64\n"
        "NumPy C macro: NPY_FLOAT64\n"
        "Fresh editable node per lookup: True\n"
    )


def test_fortran_codegen_docstrings_execution_example():
    assert _run_example("prik/codegen/docstrings.py") == (
        "double_value(value) -> float64\n"
        "\n"
        "Parameters\n"
        "----------\n"
        "value : float64\n"
        "\n"
        "Returns\n"
        "-------\n"
        "result : float64\n"
        "\n"
        "Raises\n"
        "------\n"
        "TypeError\n"
        "    If an argument has an incompatible Python type or dtype.\n"
    )


def test_fortran_codegen_c_binding_execution_example():
    output = _run_example("prik/codegen/c/binding.py")

    assert output.startswith(
        "Native procedure: DOUBLE_VALUE\nNative call slots: implicit:value\nC module: binding_demo_wrapper\n"
    )
    assert "Binding wrapper: wrap_double_value\n" in output
    assert "result = bind_c_double_value(bound_value)" in output
    assert output.endswith("  CReturn(expression=CodeExpression(text='result_obj'))\n")


def test_fortran_codegen_c_python_surface_execution_example():
    assert _run_example("prik/codegen/c/python_surface.py") == (
        "Rendered Python facade:\n"
        "_prik_unset = object()\n"
        "\n"
        "_prik_ops_state = {}\n"
        "class State:\n"
        "    'Opaque native state.'\n"
        "    __slots__ = ('_prik_capsule', '_prik_owner', '_prik_ops', '_prik_origin')\n"
        "    def __new__(cls, *args, **kwargs):\n"
        "        'Construction is disabled.'\n"
        "        raise TypeError('State objects come from native code.')\n"
        "def _prik_wrap_State(capsule, owner=None, ops=None, origin='direct'):\n"
        "    value = object.__new__(State)\n"
        "    value._prik_capsule = capsule\n"
        "    value._prik_owner = owner\n"
        "    value._prik_ops = _prik_ops_state if ops is None else ops\n"
        "    value._prik_origin = origin\n"
        "    return value\n"
    )


def test_fortran_codegen_fortran_bridge_execution_example():
    output = _run_example("prik/codegen/fortran/bridge.py")

    assert output.startswith(
        "Native procedure: DOUBLE_VALUE\nNative call slots: implicit:value\nBridge module: bind_c_bridge_demo_wrapper\n"
    )
    assert "Bridge procedure: bind_c_double_value\n" in output
    assert "Result: result :: real(c_double)\n" in output
    assert output.endswith(
        "  FortranAssignment(target='result', expression=CodeExpression(text='native_double_value(value)'))\n"
        "Internal procedures: (none)\n"
    )


def test_fortran_printers_c_execution_example():
    assert _run_example("prik/printers/c.py") == (
        "Rendered C binding source:\n"
        "#include <Python.h>\n"
        "\n"
        "static PyObject * wrap_ping(PyObject * self) {\n"
        "    Py_INCREF(Py_None);\n"
        "    return Py_None;\n"
        "}\n"
    )


def test_fortran_printers_pyi_execution_example():
    assert _run_example("prik/printers/pyi.py") == (
        "Semantic module: printer_demo\n"
        "from prik.contracts import Float64, bind\n"
        "\n"
        '@bind("DOUBLE_VALUE")\n'
        "def double_value(\n"
        "    value: Float64\n"
        ") -> Float64: ...\n"
    )


def test_fortran_printers_fortran_execution_example():
    assert _run_example("prik/printers/fortran.py") == (
        "Rendered Fortran bridge source:\n"
        "module bind_c_printer_demo_wrapper\n"
        "  use iso_c_binding, only: c_double\n"
        "  use printer_demo, only: native_double_value => DOUBLE_VALUE\n"
        "  implicit none\n"
        "contains\n"
        '  function bind_c_double_value(value) result(result) bind(c, name="DOUBLE_VALUE")\n'
        "    real(c_double), value :: value\n"
        "    real(c_double) :: result\n"
        "    result = native_double_value(value)\n"
        "  end function bind_c_double_value\n"
        "end module bind_c_printer_demo_wrapper\n"
    )


def test_fortran_pipeline_pyi_execution_example():
    assert _run_example("prik/pipeline/pyi.py") == (
        "Loaded semantic module: math\n"
        "Loaded contract marker: True\n"
        "Functions: scale\n"
        "Re-emitted module:\n"
        "from prik.contracts import Float64\n"
        "\n"
        "def scale(\n"
        "    value: Float64\n"
        ") -> Float64: ...\n"
    )


def test_fortran_pipeline_wrapper_execution_example():
    assert _run_example("prik/pipeline/wrapper.py") == (
        "Extension initializer: PyInit_generator_demo\n"
        "Rendered sources: bind_c_generator_demo_wrapper.f90, "
        "generator_demo_wrapper.c, generator_demo_wrapper.h\n"
        "Native support: binding_support\n"
    )


def test_fortran_pipeline_type_mapping_report_execution_example():
    if shutil.which("cc") is None:
        pytest.skip("cc is required for the direct type-mapping example")

    row = _run_example("prik/pipeline/type_mapping_report.py").strip()

    assert row.startswith("| `int` | ")
    assert "signed" in row
    assert "numpy." in row


@pytest.mark.fortran_end_to_end
def test_fortran_pipeline_build_execution_example():
    assert _run_example("prik/pipeline/build.py") == "scale(3.0, 2.5) = 7.5\n"


def test_fortran_runtime_handles_execution_example():
    assert _run_example("prik/runtime/handles.py") == (
        "Runtime handle: AllocatableArray\n"
        "Descriptor kind: allocatable\n"
        "Initial view: [1.0, 2.0, 3.0]\n"
        "Resized shape: (4,)\n"
        "Generated resize received NumPy extents: True\n"
    )


def test_fortran_naming_policy_execution_example():
    assert _run_example("prik/naming/policy.py") == (
        "Normalized public name: render_value\n"
        "Collision-safe public name: render_value_2\n"
        "C destructor symbol: state_drop\n"
    )


def test_fortran_naming_native_symbols_execution_example():
    assert _run_example("prik/naming/native_symbols.py") == (
        "Owner identity: geometry.point.coordinates\n"
        "Stable native symbol: point_coordinate_d_c2fc5940\n"
        "Within 27-character limit: True\n"
    )


def test_fortran_utilities_strings_execution_example():
    assert _run_example("prik/utilities/strings.py") == ("First available name: temporary_4\nNext counter: 5\n")


def test_fortran_utilities_visitor_execution_example():
    assert _run_example("prik/utilities/visitor.py") == (
        "Exact handler: literal:42\nMRO fallback: expression:Expression\n"
    )


def test_fortran_utilities_declaration_expressions_execution_example():
    assert _run_example("prik/utilities/declaration_expressions.py") == (
        "Fortran extent: ubound(source, 1) - lbound(source, 1) + 1\n"
        "Public expression: source.shape[0]\n"
        "Role-bound expression: __prik_extent_source_0\n"
        "Fortran rendering: native_source_extent_0\n"
        "Compile-time product: 6\n"
    )
