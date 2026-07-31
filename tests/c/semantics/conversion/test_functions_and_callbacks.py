"""Tests split by stable ownership concept from `test_functions_and_callbacks.py`."""

from tests.c.semantics.conversion._support import (
    CAtomic,
    CChar,
    CComposedType,
    CConst,
    CFunction,
    CFunctionType,
    CInt,
    CParameter,
    CPointer,
    CSourceLocation,
    CStruct,
    CToIRConverter,
    CTypedef,
    CUnknownType,
    CVariable,
    CVoid,
    CVolatile,
    _c_origin,
    _function,
    asdict,
    c_file_to_semantic_modules,
    c_function_to_semantic_function,
    parse_c_file,
)


def test_c2ir_converts_scalar_function_signatures_and_preserves_native_order():
    parsed = parse_c_file("int add(int a, int b);\ndouble scale(double x);\n", filename="api.h")
    module = c_file_to_semantic_modules(parsed)[0]

    add = _function(module, "add")
    scale = _function(module, "scale")

    assert module.name == "api"
    assert [arg.name for arg in add.arguments] == ["a", "b"]
    assert [arg.semantic_type.name for arg in add.arguments] == ["Int", "Int"]
    assert [arg.semantic_type.dtype for arg in add.arguments] == ["Int32", "Int32"]
    assert [arg.metadata for arg in add.arguments] == [{"native_position": 0}, {"native_position": 1}]
    assert add.native_name == "add"
    assert add.visibility == "public"
    assert add.return_type.name == "Int"
    assert add.return_type.dtype == "Int32"
    assert [mapping.native_position for mapping in add.projection] == [0, 1]
    assert scale.return_type.name == "Float64"
    assert scale.arguments[0].semantic_type.metadata == {}
    assert scale.arguments[0].semantic_type.origin.metadata["c_type"] == "CDouble"
    assert module.metadata == {
        "source_language": "c",
        "counts": {
            "functions": 2,
            "structs": 0,
            "unions": 0,
            "enums": 0,
            "typedefs": 0,
            "macros": 0,
            "includes": 0,
            "diagnostics": 0,
        },
        "preprocessing": "raw",
    }
    assert add.metadata == {
        "storage": [],
        "specifiers": [],
        "prototype_style": "prototype",
        "is_definition": False,
    }
    assert [asdict(mapping) for mapping in add.projection] == [
        {
            "python_name": "a",
            "native_name": "a",
            "native_position": 0,
            "python_position": 0,
            "result_position": None,
            "value_kind": "",
            "value": None,
        },
        {
            "python_name": "b",
            "native_name": "b",
            "native_position": 1,
            "python_position": 1,
            "result_position": None,
            "value_kind": "",
            "value": None,
        },
    ]
    assert asdict(add.arguments[0].origin) == _c_origin(
        native_name="a",
        native_scope="add",
        source_kind="parameter",
        source_type="int a",
    )
    assert asdict(add.origin) == _c_origin(
        native_name="add",
        source_kind="function",
        source_type="CFunctionType",
        source_location={
            "filename": "api.h",
            "line": 1,
            "column": 1,
            "source_line": "int add(int a, int b);",
        },
    )
    assert asdict(module.origin) == _c_origin(
        native_name="api.h",
        native_scope="api.h",
        source_kind="translation_unit",
        metadata={"preprocessing": "raw"},
    )


def test_c_function_compatibility_helper_accepts_parser_function():
    parsed = parse_c_file("float half(float value);\n", filename="helpers.h")

    function = c_function_to_semantic_function(parsed.functions[0])

    assert function.name == "half"
    assert function.arguments[0].semantic_type.name == "Float32"
    assert function.return_type.name == "Float32"


def test_c2ir_converts_qualifiers_callbacks_bitfields_and_unspecified_functions():
    callback = CComposedType(
        components=[
            CPointer(),
            CFunctionType(result_type=CVoid(), parameter_types=[CInt()]),
        ],
        source_text="void (*)(int)",
    )
    converter = CToIRConverter()
    variable = converter.visit(CVariable(name="handler", type=callback, storage=["static"]))
    field = converter.visit(CVariable(name="bits", type=CInt(), bit_width="3"))
    unresolved_variable = converter.visit(
        CVariable(name="missing_value", type=CUnknownType(spelling="missing_t", source_text="missing_t"))
    )
    function = converter.visit(parse_c_file("static int legacy();\n", filename="legacy.h").functions[0])
    qualified = converter.visit(
        CChar(qualifiers=[CConst(), CVolatile(), CAtomic()], source_text="const volatile _Atomic char")
    )
    unnamed = converter.visit(CParameter(name=None, type=CInt()))
    located_parameter = converter.visit(
        CParameter(
            name="located",
            type=CInt(),
            source_location=CSourceLocation(filename="api.h", line=3, column=5, source_line="int located"),
        )
    )
    ownerless_missing_parameter = converter.visit(
        CParameter(name="missing", type=CUnknownType(spelling="missing_t", source_text="missing_t"))
    )
    callback_parameter = converter.visit(CParameter(name="callback", type=callback))
    variadic = converter.visit(parse_c_file("int log_value(const char *fmt, ...);\n").functions[0])
    direct_callback = converter.visit(callback)
    direct_function_type = converter.visit(CFunctionType(result_type=CVoid(), parameter_types=[CInt()]))
    void_type = converter.visit(CVoid())
    missing_parameter = converter.visit(
        CParameter(name="missing", type=CUnknownType(spelling="missing_t", source_text="missing_t")),
        owner="load",
    )
    loose_struct = converter.visit(CStruct(name="loose"), as_type=True)
    missing_return = converter.visit(
        CFunction(name="missing_return", result_type=CUnknownType(spelling="missing_t", source_text="missing_t"))
    )
    unnamed_function = converter.visit(CFunction(name="unnamed", parameters=[CParameter(name=None, type=CInt())]))

    assert variable.visibility == "private"
    assert variable.semantic_type.name == "CFunctionPointer"
    assert variable.semantic_type.dtype == "CFunctionPointer"
    assert variable.semantic_type.metadata == {"source_type": "void (*)(int)"}
    assert asdict(variable.semantic_type.origin) == _c_origin(
        source_kind="function_pointer",
        source_type="void (*)(int)",
    )
    assert field.semantic_type.metadata["c_primitive"] == "int"
    assert field.semantic_type.metadata["c_type_fact"]["bits"] == 32
    assert field.visibility == "public"
    assert unresolved_variable.semantic_type.name == "missing_t"
    assert asdict(field.origin) == _c_origin(
        native_name="bits",
        source_kind="variable",
        source_type="CInt",
        metadata={"storage": [], "bit_width": "3"},
    )
    assert function.visibility == "private"
    assert function.metadata == {
        "storage": ["static"],
        "specifiers": [],
        "prototype_style": "unspecified",
        "is_definition": False,
    }
    assert qualified.name == "Int8"
    assert qualified.metadata["c_char_policy"] == "implementation-defined signed 8-bit code unit"
    assert qualified.origin.metadata["c_type"] == "CChar"
    assert qualified.origin.metadata["qualifiers"] == ["const", "volatile", "_Atomic"]
    assert unnamed.name == "arg0"
    assert unnamed.metadata == {"native_position": 0}
    assert located_parameter.origin.source_location == {
        "filename": "api.h",
        "line": 3,
        "column": 5,
        "source_line": "int located",
    }
    assert ownerless_missing_parameter.semantic_type.name == "missing_t"
    assert callback_parameter.semantic_type.metadata == {"source_type": "void (*)(int)"}
    assert unnamed_function.projection[0].native_name == "arg0"
    assert variadic.metadata["prototype_style"] == "prototype"
    assert direct_callback.metadata == {"source_type": "void (*)(int)"}
    assert asdict(direct_callback.origin) == _c_origin(
        source_kind="function_pointer",
        source_type="void (*)(int)",
    )
    assert direct_function_type.metadata == {"source_type": "CFunctionType"}
    assert void_type.name == "Any"
    assert void_type.dtype == "Any"
    assert void_type.metadata == {"c_void_pointer_pointee": True}
    assert asdict(void_type.origin) == _c_origin(
        source_kind="type",
        source_type="CVoid",
        metadata={"c_type": "CVoid"},
    )
    assert missing_parameter.semantic_type.name == "missing_t"
    assert loose_struct.name == "loose"
    assert loose_struct.dtype == "loose"
    assert loose_struct.metadata == {"c_kind": "struct", "incomplete": False}
    assert asdict(loose_struct.origin) == _c_origin(
        native_name="struct loose",
        source_kind="type",
        source_type="struct loose",
        metadata={"c_type": "CStruct"},
    )
    assert missing_return.return_type.name == "missing_t"
    assert converter._return_type(CVoid(), owner="nothing") is None
    assert CToIRConverter().visit(CTypedef(name="absent_t")).name == "absent_t"
