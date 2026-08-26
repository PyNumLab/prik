"""Tests split by stable ownership concept from `test_functions_and_callbacks.py`."""

from dataclasses import asdict
from typing import ClassVar

import pytest

from prik.parsers.c import parse_c_file
from prik.parsers.c.models import (
    CArray,
    CBool,
    CChar,
    CComposedType,
    CDouble,
    CDoubleComplex,
    CFile,
    CFloat,
    CFloatComplex,
    CFunction,
    CInt,
    CLong,
    CLongDouble,
    CLongDoubleComplex,
    CLongLong,
    CMacro,
    CParameter,
    CPointer,
    CProject,
    CRestrict,
    CShort,
    CSignedChar,
    CSourceLocation,
    CStruct,
    CTypedef,
    CUnknownType,
    CUnsignedChar,
    CUnsignedInt,
    CUnsignedLong,
    CUnsignedLongLong,
    CUnsignedShort,
    CVariable,
)
from prik.semantics.c2ir import (
    CToIRConverter,
    c_file_to_semantic_module,
    c_file_to_semantic_modules,
    c_function_to_semantic_function,
    c_parameter_to_semantic_argument,
    c_project_to_semantic_module,
    c_project_to_semantic_modules,
    c_struct_to_semantic_class,
    c_type_to_semantic_type,
)
from tests.c._support.semantic_conversion import (
    _assert_c_origin,
    _assert_unsupported_type,
    _function,
)


def test_c2ir_maps_const_and_mutable_pointers_to_storage_contracts():
    parsed = parse_c_file(
        "void copy(const double *src, double *dst);\n",
        filename="copy.h",
    )
    module = c_file_to_semantic_modules(parsed)[0]
    copy = _function(module, "copy")
    src, dst = copy.arguments

    assert src.semantic_type.name == "Float64"
    assert src.semantic_type.storage.kind == "reference"
    assert src.semantic_type.storage.read_only is True

    assert dst.semantic_type.name == "Float64"
    assert dst.semantic_type.storage.kind == "reference"
    assert dst.semantic_type.storage.read_only is False
    assert asdict(src.semantic_type.ownership) == {"ownership": "borrowed", "mutable": False, "aliasing": True}
    assert asdict(dst.semantic_type.ownership) == {"ownership": "borrowed", "mutable": True, "aliasing": True}
    assert asdict(src.semantic_type.storage) == {
        "kind": "reference",
        "read_only": True,
        "mutable": False,
        "pointer_depth": 1,
        "ownership": "borrowed",
        "array": None,
        "calling_convention": None,
        "metadata": {
            "c_pointer_qualifiers": [[]],
            "restrict": False,
            "source_type": "const double *src",
        },
    }
    assert asdict(dst.semantic_type.storage) == {
        "kind": "reference",
        "read_only": False,
        "mutable": True,
        "pointer_depth": 1,
        "ownership": "borrowed",
        "array": None,
        "calling_convention": None,
        "metadata": {
            "c_pointer_qualifiers": [[]],
            "restrict": False,
            "source_type": "double *dst",
        },
    }
    restricted = CToIRConverter().visit(
        CComposedType(
            components=[CPointer(qualifiers=[CRestrict()]), CDouble()],
            source_text="double *restrict",
        )
    )
    assert restricted.storage.metadata["restrict"] is True
    assert restricted.ownership.aliasing is False
    double_pointer = CToIRConverter().visit(
        CComposedType(components=[CPointer(), CPointer(), CDouble()], source_text="double **")
    )
    assert double_pointer.storage.kind == "pointer"
    assert double_pointer.storage.pointer_depth == 2


def test_c2ir_uses_declared_c_array_bounds_before_parameter_adjustment():
    parsed = parse_c_file(
        "void solve(double a[static 4], const int shape[2], int matrix[3][4]);\n",
        filename="arrays.h",
    )
    module = c_file_to_semantic_modules(parsed)[0]
    solve = _function(module, "solve")
    a, shape, matrix = solve.arguments

    assert a.semantic_type.storage.kind == "array"
    assert a.semantic_type.storage.array.shape == ["4"]
    assert a.semantic_type.storage.array.metadata["c_static_minimum"] == [True]

    assert shape.semantic_type.storage.read_only is True
    assert shape.semantic_type.storage.array.shape == ["2"]

    assert matrix.semantic_type.rank == 2
    assert matrix.semantic_type.shape == ["3", "4"]
    assert matrix.semantic_type.storage.array.shape == ["3", "4"]
    assert matrix.semantic_type.storage.array.order == "ORDER_C"
    assert asdict(a.semantic_type.storage) == {
        "kind": "array",
        "read_only": False,
        "mutable": True,
        "pointer_depth": 1,
        "ownership": "borrowed",
        "array": {
            "rank": 1,
            "shape": ["4"],
            "lower_bounds": [],
            "upper_bounds": [],
            "source_shape": ["4"],
            "category": "c_array",
            "order": None,
            "copy_order": None,
            "axes": ["dense"],
            "contiguous": True,
            "allocatable": False,
            "pointer": False,
            "metadata": {
                "c_static_minimum": [True],
                "c_variable_length": [False],
                "c_flexible": [False],
            },
        },
        "calling_convention": None,
        "metadata": {"source_type": "double a[static 4]"},
    }
    assert asdict(matrix.semantic_type.storage) == {
        "kind": "array",
        "read_only": False,
        "mutable": True,
        "pointer_depth": 1,
        "ownership": "borrowed",
        "array": {
            "rank": 2,
            "shape": ["3", "4"],
            "lower_bounds": [],
            "upper_bounds": [],
            "source_shape": ["3", "4"],
            "category": "c_array",
            "order": "ORDER_C",
            "copy_order": None,
            "axes": ["dense", "dense"],
            "contiguous": True,
            "allocatable": False,
            "pointer": False,
            "metadata": {
                "c_static_minimum": [False, False],
                "c_variable_length": [False, False],
                "c_flexible": [False, False],
            },
        },
        "calling_convention": None,
        "metadata": {"source_type": "int matrix[3][4]"},
    }


def test_c2ir_converts_integer_expression_macro_constants_when_resolvable():
    parsed = parse_c_file(
        """
void fill(int x[static API_N1]);
""",
        filename="shape_macros.h",
    )
    parsed.macros = [
        CMacro(name="API_N0", value="4"),
        CMacro(name="API_N1", value="(API_N0 + 2)"),
        CMacro(name="API_MASK", value="(1U << API_N1)"),
        CMacro(name="API_TEXT", value='"not a semantic integer constant"'),
        CMacro(name="API_CALL", value="3", function_like=True),
        CMacro(name="API_FIRST", value="1"),
        CMacro(name="API_FORWARD", value="(API_LATE + 1)"),
        CMacro(name="API_FORWARD_CHAIN", value="(API_FORWARD_MIDDLE + 1)"),
        CMacro(name="API_FORWARD_MIDDLE", value="(API_FORWARD_LATE + 1)"),
        CMacro(name="API_FORWARD_LATE", value="2"),
        CMacro(
            name="API_LATE",
            value="4",
            source_location=CSourceLocation(
                filename="shape_macros.h", line=8, column=1, source_line="#define API_LATE 4"
            ),
        ),
    ]
    module = c_file_to_semantic_modules(parsed)[0]

    constants = {var.name: var for var in module.variables}
    assert constants["API_N0"].semantic_type.name == "Int32"
    assert constants["API_N1"].semantic_type.name == "Int32"
    assert constants["API_MASK"].semantic_type.name == "Int32"
    assert constants["API_FORWARD"].semantic_type.name == "Int32"
    assert constants["API_FORWARD_CHAIN"].semantic_type.name == "Int32"
    assert "API_TEXT" not in constants
    assert "API_CALL" not in constants
    _assert_c_origin(
        constants["API_LATE"].origin,
        native_name="API_LATE",
        source_kind="macro",
        source_location={
            "filename": "shape_macros.h",
            "line": 8,
            "column": 1,
            "source_line": "#define API_LATE 4",
        },
    )


def test_c2ir_resolves_local_typedef_chains_and_standard_size_t_fallback():
    parsed = parse_c_file(
        """
typedef unsigned long size_type;
typedef size_type api_size;
api_size count(void);
int read_values(const double *values, size_t n);
""",
        filename="typedefs.h",
    )
    module = c_file_to_semantic_modules(parsed)[0]

    count = _function(module, "count")
    assert count.return_type.name == "UInt64"
    assert count.return_type.metadata == {"c_typedefs": ["size_type", "api_size"]}
    read_values = _function(module, "read_values")
    assert [arg.semantic_type.name for arg in read_values.arguments] == ["Float64", "SizeT"]
    assert read_values.arguments[0].semantic_type.storage.read_only is True
    assert read_values.arguments[1].semantic_type.metadata == {
        "c_standard_type": "size_t",
        "c_standard_type_fallback": True,
        "c_typedefs": ["size_t"],
    }

    converter = CToIRConverter()
    converter.typedefs = {
        "target_t": CTypedef(name="target_t", type=CUnknownType(spelling="missing_t", source_text="missing_t"))
    }
    resolved = converter.visit(CTypedef(name="target_t"), owner="result")
    inline = converter.visit(
        CTypedef(name="inline_t", type=CUnknownType(spelling="inline_missing_t", source_text="inline_missing_t")),
        owner="inline_result",
    )
    unresolved = converter.visit(CTypedef(name="absent_t"), owner="result")
    converter.typedefs["cyclic_t"] = CTypedef(name="cyclic_t")
    cyclic = converter.visit(CTypedef(name="cyclic_t"), owner="cycle")
    assert resolved.metadata == {"c_typedefs": ["target_t"]}
    assert inline.metadata == {"c_typedefs": ["inline_t"]}
    assert unresolved.metadata == {}
    assert cyclic.metadata == {}


def test_c2ir_uses_standard_type_probe_facts_when_supplied():
    parsed = parse_c_file("size_t count(void);\n", filename="probe.h")
    converter = CToIRConverter(
        standard_type_report={
            "types": {
                "size_t": {
                    "available": True,
                    "kind": "integer",
                    "signed": False,
                    "bits": 32,
                }
            }
        }
    )

    module = converter.visit(parsed)

    assert _function(module, "count").return_type.name == "UInt32"


def test_c2ir_preserves_c_int_identity_and_stores_compiler_probed_precision():
    converter = CToIRConverter(
        standard_type_report={
            "types": {
                "int": {
                    "available": True,
                    "kind": "integer",
                    "signed": True,
                    "bits": 16,
                    "underlying_c_type": "int",
                }
            }
        }
    )

    semantic_type = converter.visit(CInt())

    assert semantic_type.name == "Int"
    assert semantic_type.dtype == "Int16"
    assert semantic_type.metadata == {
        "c_primitive": "int",
        "c_type_fact": {
            "available": True,
            "kind": "integer",
            "signed": True,
            "bits": 16,
            "underlying_c_type": "int",
        },
        "c_type_fact_source": "compiler_probe",
    }


@pytest.mark.parametrize(
    ("ctype", "primitive", "fact", "expected"),
    [
        (CChar(), "char", {"kind": "integer", "signed": False, "bits": 8}, "UInt8"),
        (CLong(), "long", {"kind": "integer", "signed": True, "bits": 32}, "Int32"),
        (CUnsignedLong(), "unsigned long", {"kind": "integer", "signed": False, "bits": 32}, "UInt32"),
        (CLongDouble(), "long double", {"kind": "real", "bits": 64}, "Float64"),
        (CLongDoubleComplex(), "long double _Complex", {"kind": "complex", "bits": 128}, "Complex128"),
        (CBool(), "_Bool", {"kind": "bool", "bits": 8}, "Bool8"),
    ],
)
def test_c2ir_uses_compiler_probed_primitive_abi_facts(ctype, primitive, fact, expected):
    semantic_type = CToIRConverter(standard_type_report={"types": {primitive: fact}}).visit(ctype)

    assert semantic_type.name == expected
    assert semantic_type.dtype == expected
    assert semantic_type.metadata["c_primitive"] == primitive
    assert semantic_type.metadata["c_type_fact"] == fact
    assert semantic_type.metadata["c_type_fact_source"] == "compiler_probe"
    if primitive == "char":
        assert semantic_type.metadata["c_char_policy"] == "compiler-probed unsigned 8-bit code unit"


def test_c2ir_blocks_compiler_probed_primitive_abi_without_semantic_dtype():
    fact = {"kind": "integer", "signed": True, "bits": 48}
    semantic_type = CToIRConverter(standard_type_report={"types": {"long": fact}}).visit(CLong())

    assert semantic_type.name == "CUnsupported"
    assert semantic_type.metadata["c_primitive"] == "long"
    assert semantic_type.metadata["c_type_fact"] == fact


def test_c_compatibility_helpers_forward_standard_type_reports():
    report = {
        "types": {
            "measured_t": {
                "available": True,
                "kind": "integer",
                "signed": False,
                "bits": 32,
            }
        }
    }
    measured_type = CTypedef(name="measured_t")
    function = CFunction(name="measure", result_type=measured_type)
    parsed_file = CFile(filename="measure.h", functions=[function])
    project = CProject(files={"measure.h": parsed_file}, functions={"measure": function})

    argument = c_parameter_to_semantic_argument(
        CParameter(name="value", type=measured_type),
        standard_type_report=report,
    )
    converted_type = c_type_to_semantic_type(measured_type, standard_type_report=report)
    converted_function = c_function_to_semantic_function(function, standard_type_report=report)
    cls = c_struct_to_semantic_class(
        CStruct(name="measurement", members=[CVariable(name="value", type=measured_type)]),
        standard_type_report=report,
    )
    assert argument.semantic_type.name == "UInt32"
    assert converted_type.name == "UInt32"
    assert converted_function.return_type.name == "UInt32"
    assert cls.fields[0].semantic_type.name == "UInt32"
    assert _function(
        c_file_to_semantic_module(parsed_file, standard_type_report=report), "measure"
    ).return_type.name == ("UInt32")
    assert _function(
        c_file_to_semantic_modules(parsed_file, standard_type_report=report)[0], "measure"
    ).return_type.name == ("UInt32")
    assert _function(
        c_project_to_semantic_modules(project, standard_type_report=report)[0], "measure"
    ).return_type.name == ("UInt32")
    assert _function(
        c_project_to_semantic_module(project, standard_type_report=report), "measure"
    ).return_type.name == ("UInt32")


@pytest.mark.parametrize(
    ("ctype", "expected_name", "expected_dtype"),
    [
        (CBool(), "Bool", "Bool"),
        (CChar(), "Int8", "Int8"),
        (CSignedChar(), "Int8", "Int8"),
        (CUnsignedChar(), "UInt8", "UInt8"),
        (CShort(), "Int16", "Int16"),
        (CUnsignedShort(), "UInt16", "UInt16"),
        (CInt(), "Int", "Int32"),
        (CUnsignedInt(), "UInt32", "UInt32"),
        (CLong(), "Int64", "Int64"),
        (CUnsignedLong(), "UInt64", "UInt64"),
        (CLongLong(), "Int64", "Int64"),
        (CUnsignedLongLong(), "UInt64", "UInt64"),
        (CFloat(), "Float32", "Float32"),
        (CDouble(), "Float64", "Float64"),
        (CLongDouble(), "Float128", "Float128"),
        (CFloatComplex(), "Complex64", "Complex64"),
        (CDoubleComplex(), "Complex128", "Complex128"),
        (CLongDoubleComplex(), "Complex256", "Complex256"),
    ],
)
def test_c_primitive_precisions_map_to_semantic_types(ctype, expected_name, expected_dtype):
    semantic_type = CToIRConverter().visit(ctype)

    assert semantic_type.name == expected_name
    assert semantic_type.dtype == expected_dtype


@pytest.mark.parametrize(
    ("name", "fact", "expected"),
    [
        ("int8_t", {"available": True, "kind": "integer", "signed": True, "bits": 8}, "Int8"),
        ("int16_t", {"available": True, "kind": "integer", "signed": True, "bits": 16}, "Int16"),
        ("int32_t", {"available": True, "kind": "integer", "signed": True, "bits": 32}, "Int32"),
        ("int64_t", {"available": True, "kind": "integer", "signed": True, "bits": 64}, "Int64"),
        ("uint8_t", {"available": True, "kind": "integer", "signed": False, "bits": 8}, "UInt8"),
        ("uint16_t", {"available": True, "kind": "integer", "signed": False, "bits": 16}, "UInt16"),
        ("uint32_t", {"available": True, "kind": "integer", "signed": False, "bits": 32}, "UInt32"),
        ("uint64_t", {"available": True, "kind": "integer", "signed": False, "bits": 64}, "UInt64"),
    ],
)
def test_c_standard_integer_precision_facts_map_to_semantic_types(name, fact, expected):
    semantic_type = CToIRConverter(standard_type_report={"types": {name: fact}}).visit(CTypedef(name=name))

    assert semantic_type.name == expected
    assert semantic_type.dtype == expected


def test_c2ir_reports_unsupported_type_and_declarator_compositions():
    converter = CToIRConverter(primitive_type_map={CInt: None})

    unresolved = converter.visit(
        CUnknownType(spelling="missing_t", source_text="missing_t"),
        owner="missing_owner",
    )
    unsupported_integer = converter.visit(CInt(source_text="int"), owner="integer_owner")
    empty = converter.visit(CComposedType(components=[], source_text="empty"), owner="empty_owner")
    array_missing_element = converter.visit(
        CComposedType(components=[CArray(bound="4")], source_text="missing element"),
        owner="array_owner",
    )
    array_of_pointer = converter.visit(
        CComposedType(components=[CArray(bound="4"), CPointer(), CDouble()], source_text="double *items[4]"),
        owner="array_pointer_owner",
    )
    pointer_missing_pointee = converter.visit(
        CComposedType(components=[CPointer()], source_text="missing pointee"),
        owner="pointer_owner",
    )
    pointer_composition = converter.visit(
        CComposedType(components=[CPointer(), CInt(), CDouble()], source_text="mixed pointer"),
        owner="pointer_composition_owner",
    )
    other_composition = converter.visit(
        CComposedType(components=[CInt(), CDouble()], source_text="mixed declarator"),
        owner="composition_owner",
    )

    assert unresolved.name == "missing_t"
    assert unresolved.dtype == "missing_t"
    assert unresolved.metadata == {}
    _assert_c_origin(unresolved.origin, source_kind="type", source_type="missing_t")
    _assert_unsupported_type(
        unsupported_integer,
        code="c_unsupported_type",
        message="This C type is not supported by the semantic converter.",
        owner="integer_owner",
        source_type="int",
    )
    _assert_unsupported_type(
        empty,
        code="c_empty_composed_type",
        message="C composed type is missing a base type.",
        owner="empty_owner",
        source_type="empty",
    )
    _assert_unsupported_type(
        array_missing_element,
        code="c_array_missing_element_type",
        message="C array type is missing an element type.",
        owner="array_owner",
        source_type="missing element",
    )
    _assert_unsupported_type(
        array_of_pointer,
        code="c_array_of_pointer_unsupported",
        message="C arrays of pointers need explicit semantic policy.",
        owner="array_pointer_owner",
        source_type="double *items[4]",
    )
    _assert_unsupported_type(
        pointer_missing_pointee,
        code="c_pointer_missing_pointee",
        message="C pointer type is missing a pointee type.",
        owner="pointer_owner",
        source_type="missing pointee",
    )
    _assert_unsupported_type(
        pointer_composition,
        code="c_unsupported_composed_type",
        message="This C pointer composition needs explicit semantic policy.",
        owner="pointer_composition_owner",
        source_type="mixed pointer",
    )
    _assert_unsupported_type(
        other_composition,
        code="c_unsupported_composed_type",
        message="This C declarator composition needs explicit semantic policy.",
        owner="composition_owner",
        source_type="mixed declarator",
    )


def test_c2ir_standard_type_facts_and_numeric_constant_edge_cases():
    class Report:
        types: ClassVar = {
            "signed_size": {"kind": "integer", "signed": True, "bits": 16},
            "real_size": {"kind": "real", "bits": 32},
            "missing": {"available": False, "kind": "integer", "signed": False, "bits": 32},
        }

    converter = CToIRConverter(standard_type_report=Report())
    signed_size = converter._standard_semantic_type("signed_size")
    real_size = converter._standard_semantic_type("real_size")
    assert signed_size.name == "Int16"
    assert signed_size.dtype == "Int16"
    assert signed_size.metadata == {
        "c_standard_type": "signed_size",
        "c_standard_type_fact": {"kind": "integer", "signed": True, "bits": 16},
    }
    assert real_size.name == "Float32"
    assert real_size.dtype == "Float32"
    assert real_size.metadata == {
        "c_standard_type": "real_size",
        "c_standard_type_fact": {"kind": "real", "bits": 32},
    }
    fallback = CToIRConverter()._standard_semantic_type("size_t")
    assert fallback.name == "SizeT"
    assert fallback.dtype == "SizeT"
    assert fallback.metadata == {"c_standard_type": "size_t", "c_standard_type_fallback": True}
    assert converter._standard_semantic_type("missing") is None
    assert converter._standard_semantic_type("not_standard") is None
    opaque_converter = CToIRConverter(
        standard_type_report={
            "implicit_handle": {"kind": "opaque_handle"},
            "missing_handle": {"available": False, "kind": "opaque_handle"},
        }
    )
    assert opaque_converter._standard_semantic_type("implicit_handle").name == "implicit_handle"
    assert opaque_converter._standard_semantic_type("missing_handle") is None
    assert CToIRConverter._standard_type_facts(object()) == {}
    assert CToIRConverter._integer_literal_value(None) is None
    assert CToIRConverter._integer_literal_value("value") is None
    assert CToIRConverter._integer_macro_expression("(MISSING + 1)", {}) is False
    assert CToIRConverter._integer_macro_expression("(1 +)", {}) is False

    parsed = parse_c_file(
        "enum default_status { DEFAULT_OK, DEFAULT_NEXT };\nenum status { STATUS_EXPR = UNKNOWN, STATUS_NEXT };\n",
        filename="edge_constants.h",
    )
    parsed.macros = [
        CMacro(name="RATE", value="1.5"),
        CMacro(name="BAD", value="(MISSING + 1)"),
    ]
    constants = {variable.name: variable for variable in converter.visit(parsed).variables}
    assert constants["RATE"].semantic_type.name == "Float64"
    assert constants["DEFAULT_OK"].default_value == "0"
    assert constants["DEFAULT_NEXT"].default_value == "1"
    assert constants["STATUS_EXPR"].default_value == "UNKNOWN"
    assert constants["STATUS_NEXT"].default_value is None
