"""C function declarations and their semantic projection."""

from prik.parsers.c import parse_c_file
from prik.parsers.c.models import (
    CAtomic,
    CChar,
    CComposedType,
    CConst,
    CFunction,
    CFunctionType,
    CInt,
    CParameter,
    CPointer,
    CUnknownType,
    CVariable,
    CVolatile,
    CVoid,
)
from prik.semantics.c2ir import CToIRConverter, c_file_to_semantic_modules
from tests.c._support.semantic_conversion import (
    _assert_c_origin,
    _function,
)


def test_c2ir_converts_scalar_function_signatures_and_preserves_native_order():
    parsed = parse_c_file("int add(int a, int b);\ndouble scale(double x);\n", filename="api.h")
    module = c_file_to_semantic_modules(parsed)[0]

    add = _function(module, "add")
    scale = _function(module, "scale")

    assert module.name == "api"
    assert module.metadata["source_language"] == "c"
    assert [(arg.name, arg.semantic_type.name, arg.semantic_type.dtype) for arg in add.arguments] == [
        ("a", "Int", "Int32"),
        ("b", "Int", "Int32"),
    ]
    assert add.native_name == "add"
    assert add.visibility == "public"
    assert (add.return_type.name, add.return_type.dtype) == ("Int", "Int32")
    assert scale.return_type.name == "Float64"
    assert [
        (mapping.python_name, mapping.native_name, mapping.native_position, mapping.python_position)
        for mapping in add.projection
    ] == [("a", "a", 0, 0), ("b", "b", 1, 1)]
    # The exact C ABI spelling is recorded for direct-C policy to consume.
    c_abi = add.metadata["c_abi"]
    assert c_abi["variadic"] is False
    assert c_abi["result"]["source_spelling"] == "int"
    assert [parameter["source_spelling"] for parameter in c_abi["parameters"]] == ["int", "int"]
    assert add.metadata["prototype_style"] == "prototype"
    _assert_c_origin(
        add.origin,
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
    function = converter.visit(parse_c_file("static int legacy();\n", filename="legacy.h").functions[0])
    qualified = converter.visit(
        CChar(qualifiers=[CConst(), CVolatile(), CAtomic()], source_text="const volatile _Atomic char")
    )
    callback_parameter = converter.visit(CParameter(name="callback", type=callback))
    variadic = converter.visit(parse_c_file("int log_value(const char *fmt, ...);\n").functions[0])
    void_type = converter.visit(CVoid())
    missing_return = converter.visit(
        CFunction(name="missing_return", result_type=CUnknownType(spelling="missing_t", source_text="missing_t"))
    )
    unnamed_function = converter.visit(CFunction(name="unnamed", parameters=[CParameter(name=None, type=CInt())]))

    # ``static`` storage is translation-unit local, so it is never published.
    assert variable.visibility == "private"
    assert function.visibility == "private"
    assert function.metadata["prototype_style"] == "unspecified"
    assert function.metadata["c_abi"]["parameters"] == []
    assert variable.semantic_type.name == "CFunctionPointer"
    assert callback_parameter.semantic_type.metadata == {"source_type": "void (*)(int)"}
    assert field.semantic_type.metadata["c_primitive"] == "int"
    assert field.origin.metadata["bit_width"] == "3"
    assert qualified.name == "Int8"
    assert qualified.metadata["c_char_policy"] == "implementation-defined signed 8-bit code unit"
    assert qualified.origin.metadata["qualifiers"] == ["const", "volatile", "_Atomic"]
    assert variadic.metadata["prototype_style"] == "prototype"
    assert variadic.metadata["c_abi"]["variadic"] is True
    assert (void_type.name, void_type.metadata) == ("Any", {"c_void_pointer_pointee": True})
    assert missing_return.return_type.name == "missing_t"
    assert unnamed_function.projection[0].native_name == "arg0"
