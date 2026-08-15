"""Tests split by stable ownership concept from `test_functions_and_callbacks.py`."""

from dataclasses import asdict

from prik.pipeline.pyi import emit_module_stubs
from prik.printers import emit_module
from prik.parsers.c import parse_c_file, parse_c_project
from prik.parsers.c.models import (
    CArray,
    CComposedType,
    CDouble,
    CFile,
    CFunction,
    CInitializer,
    CInt,
    CMacro,
    CParameter,
    CPointer,
    CSourceLocation,
    CStruct,
    CTypedef,
    CUnion,
    CUnknownType,
    CVariable,
)
from prik.pipeline.pyi import pyi_text_to_semantic_module as parse_pyi_text
from prik.semantics.c2ir import (
    CToIRConverter,
    c_file_to_semantic_module,
    c_file_to_semantic_modules,
    c_project_to_semantic_module,
    c_project_to_semantic_modules,
)
from prik.semantics.models import (
    SemanticArgument,
    SemanticClass,
    SemanticField,
    SemanticModule,
    SemanticOrigin,
    SemanticType,
    SemanticVariable,
)
from tests.c.semantics.conversion._support import (
    _assert_c_origin,
    _function,
)


def test_c2ir_converts_structs_and_opaque_struct_pointers():
    parsed = parse_c_file(
        """
struct point { double x; double y; };
struct context;
struct point scale_point(struct point p, double factor);
struct context *context_create(void);
void context_destroy(struct context *ctx);
""",
        filename="structs.h",
    )
    module = c_file_to_semantic_modules(parsed)[0]

    point = next(cls for cls in module.classes if cls.name == "point")
    context = next(cls for cls in module.classes if cls.name == "context")
    scale_point = _function(module, "scale_point")
    context_create = _function(module, "context_create")

    assert [field.name for field in point.fields] == ["x", "y"]
    assert all(isinstance(field, SemanticField) for field in point.fields)
    assert [field.semantic_type.name for field in point.fields] == ["Float64", "Float64"]
    assert point.native_name == "struct point"
    assert point.metadata == {"c_kind": "struct", "incomplete": False}
    assert point.origin.source_language == "c"
    assert point.origin.native_name == "struct point"
    assert point.origin.source_kind == "struct"
    assert point.origin.source_type == "struct point"
    assert context.base_classes == ["CStruct", "Opaque"]
    assert context.metadata == {"c_kind": "struct", "incomplete": True}
    assert scale_point.arguments[0].semantic_type.name == "point"
    assert context_create.return_type.name == "context"
    assert context_create.return_type.storage.kind == "reference"
    assert "class context(CStruct, Opaque):" in emit_module(module)


def test_c2ir_private_include_types_remain_available_as_opaque_handles():
    parsed = parse_c_file(
        """
# 1 "private.h" 1
struct private_context { int internal; };
void internal_only(void);
int hidden_value;
# 1 "api.h" 2
struct private_context *make_context(void);
void use_context(struct private_context *ctx);
""",
        filename="api.h",
        preprocessing="compiler",
    )
    parsed.preprocessing_recipe = {
        "included_files": [
            {"path": "api.h", "dependency_kind": "root", "exposure": "public"},
            {"path": "private.h", "dependency_kind": "project", "exposure": "private"},
        ]
    }

    module = c_file_to_semantic_modules(parsed)[0]
    make_context = _function(module, "make_context")
    use_context = _function(module, "use_context")
    stubs = emit_module_stubs(module)

    assert all(cls.name != "private_context" for cls in module.classes)
    assert _function(module, "internal_only").visibility == "private"
    assert next(variable for variable in module.variables if variable.name == "hidden_value").visibility == "private"
    assert make_context.return_type.name == "private_context"
    assert use_context.arguments[0].semantic_type.name == "private_context"
    assert make_context.return_type.metadata["external_type_ref"] == {
        "name": "private_context",
        "local_name": "private_context",
        "origin_module": "private",
        "wrapped": False,
        "representation": "opaque",
    }
    assert "from private import private_context" in stubs["api"]
    assert (
        stubs["private"]
        == "from prik.contracts import CStruct, Opaque\n\nclass private_context(CStruct, Opaque):\n    pass"
    )


def test_c2ir_preserves_anonymous_aggregate_members_as_nested_c_classes():
    parsed = parse_c_file(
        "struct flags { union { int integer; float real; }; struct { int code; } meta; int tag; };\n",
        filename="flags.h",
    )

    module = c_file_to_semantic_module(parsed)
    flags = module.classes[0]
    anonymous_union, meta = flags.classes
    anonymous_field, meta_field, tag = flags.fields
    code = emit_module(module)
    reparsed = parse_pyi_text(code, module_name="flags")
    reparsed_flags = reparsed.classes[0]

    assert flags.base_classes == ["CStruct"]
    assert flags.metadata == {"c_kind": "struct", "incomplete": False}
    assert anonymous_union.base_classes == ["CUnion", "CAnonymous"]
    assert anonymous_union.metadata == {"c_kind": "union", "incomplete": False, "c_anonymous": True}
    assert [field.name for field in anonymous_union.fields] == ["integer", "real"]
    assert meta.base_classes == ["CStruct", "CAnonymous"]
    assert [field.name for field in meta.fields] == ["code"]
    assert anonymous_field.name == "_anonymous_union_0"
    assert anonymous_field.semantic_type.name == "anonymous_union_0_type"
    assert [constraint.name for constraint in anonymous_field.semantic_type.constraints] == ["CAnonymousMember"]
    assert anonymous_field.semantic_type.metadata["c_kind"] == "union"
    assert meta_field.name == "meta"
    assert meta_field.semantic_type.name == "meta_type"
    assert tag.name == "tag"
    assert "class flags(CStruct):" in code
    assert "class anonymous_union_0_type(CUnion, CAnonymous):" in code
    assert "_anonymous_union_0: Annotated[anonymous_union_0_type, CAnonymousMember]" in code
    assert [(cls.name, cls.base_classes) for cls in reparsed_flags.classes] == [
        ("anonymous_union_0_type", ["CUnion", "CAnonymous"]),
        ("meta_type", ["CStruct", "CAnonymous"]),
    ]
    assert reparsed_flags.metadata == {"c_kind": "struct"}
    assert reparsed_flags.classes[0].metadata == {"c_kind": "union", "c_anonymous": True}
    assert [constraint.name for constraint in reparsed_flags.fields[0].semantic_type.constraints] == [
        "CAnonymousMember"
    ]


def test_c2ir_private_include_opaque_struct_by_value_preserves_the_external_reference():
    parsed = parse_c_file(
        """
# 1 "private.h" 1
struct private_context { int internal; };
# 1 "api.h" 2
void use_context(struct private_context ctx);
""",
        filename="api.h",
        preprocessing="compiler",
    )
    parsed.preprocessing_recipe = {
        "included_files": [
            {"path": "api.h", "dependency_kind": "root", "exposure": "public"},
            {"path": "private.h", "dependency_kind": "project", "exposure": "private"},
        ]
    }

    module = c_file_to_semantic_modules(parsed)[0]
    semantic_type = _function(module, "use_context").arguments[0].semantic_type
    assert semantic_type.metadata["external_type_ref"]["representation"] == "opaque"


def test_c2ir_externalizes_only_private_opaque_classes_with_external_origins():
    converter = CToIRConverter()
    public = SemanticClass(name="public", origin=SemanticOrigin(source_location={"filename": "api.h"}))
    private_plain = SemanticClass(
        name="private_plain",
        visibility="private",
        origin=SemanticOrigin(source_location={"filename": "private.h"}),
    )
    private_without_location = SemanticClass(
        name="private_without_location", visibility="private", base_classes=["Opaque"]
    )
    private_external = SemanticClass(
        name="private_external",
        visibility="private",
        base_classes=["Opaque"],
        origin=SemanticOrigin(source_location={"filename": "private.h"}),
    )
    reference = SemanticArgument(name="value", semantic_type=SemanticType(name="private_external"))
    module = SemanticModule(
        name="api",
        classes=[public, private_plain, private_without_location, private_external],
        variables=[reference],
    )

    converter._externalize_private_classes(module)

    assert [cls.name for cls in module.classes] == ["public", "private_plain", "private_without_location"]
    assert reference.semantic_type.metadata["external_type_ref"] == {
        "name": "private_external",
        "local_name": "private_external",
        "origin_module": "private",
        "wrapped": False,
        "representation": "opaque",
    }


def test_c2ir_converts_enum_constants_and_simple_macro_constants():
    parsed = parse_c_file(
        """
enum status { STATUS_OK = 0, STATUS_WARN, STATUS_ERROR = 10 };
""",
        filename="constants.h",
    )
    parsed.macros = [CMacro(name="API_VERSION", value="3")]
    module = c_file_to_semantic_modules(parsed)[0]

    constants = {var.name: var for var in module.variables}
    assert constants["API_VERSION"].default_value == "3"
    assert constants["API_VERSION"].semantic_type.constraints[0].name == "Constant"
    assert constants["STATUS_WARN"].default_value == "1"
    assert constants["STATUS_ERROR"].default_value == "10"
    api_version = constants["API_VERSION"]
    assert isinstance(api_version, SemanticVariable)
    assert api_version.semantic_type.name == "Int32"
    assert api_version.semantic_type.dtype == "Int32"
    assert [asdict(constraint) for constraint in api_version.semantic_type.constraints] == [
        {"name": "Constant", "arguments": []}
    ]
    _assert_c_origin(
        api_version.origin,
        native_name="API_VERSION",
        source_kind="macro",
    )
    status_ok = constants["STATUS_OK"]
    assert module.classes == []
    assert status_ok.semantic_type.name == "Int"
    assert status_ok.semantic_type.dtype == "Int32"
    assert status_ok.semantic_type.metadata["enum_name"] == "status"
    assert status_ok.semantic_type.metadata["c_kind"] == "enum"
    assert status_ok.semantic_type.metadata["c_enum"] == "enum status"
    assert status_ok.semantic_type.metadata["c_underlying_type"] == "Int"
    assert status_ok.semantic_type.coercions == []
    _assert_c_origin(
        status_ok.origin,
        native_name="STATUS_OK",
        native_scope="enum status",
        source_kind="enum_constant",
        source_location={
            "filename": "constants.h",
            "line": 2,
            "column": 1,
            "source_line": "enum status { STATUS_OK = 0, STATUS_WARN, STATUS_ERROR = 10 };",
        },
    )


def test_c2ir_names_anonymous_typedef_enums_and_keeps_enumerators_unscoped():
    source = "typedef enum { FLAG_NONE = 0, FLAG_READ = 1 } flag_t; flag_t get_flags(void);"
    parsed = parse_c_file(source, filename="flags.h")

    module = c_file_to_semantic_module(parsed)
    project_module = c_project_to_semantic_module(parse_c_project({"flags.h": source}), name="flags")

    assert module.classes == []
    assert project_module.classes == []
    assert [variable.name for variable in module.variables] == ["FLAG_NONE", "FLAG_READ"]
    assert [variable.name for variable in project_module.variables] == ["FLAG_NONE", "FLAG_READ"]
    assert [variable.semantic_type.name for variable in module.variables] == ["Int", "Int"]
    assert module.variables[0].semantic_type.metadata["enum_name"] == "flag_t"
    assert _function(module, "get_flags").return_type.name == "Int"
    assert _function(project_module, "get_flags").return_type.name == "Int"


def test_c2ir_enum_values_emit_only_python_compatible_expressions():
    parsed = parse_c_file(
        "enum flags { FLAG_ONE = 1U, FLAG_OCTAL = 010, FLAG_SHIFT = FLAG_ONE << 1, FLAG_CHAR = 'A' };",
        filename="flags.h",
    )
    module = c_file_to_semantic_module(parsed)

    code = emit_module(module)

    assert "FLAG_ONE: Final[Int] = 1" in code
    assert "FLAG_OCTAL: Final[Int] = 8" in code
    assert "FLAG_SHIFT: Final[Int] = FLAG_ONE << 1" in code
    assert "FLAG_CHAR: Final[Int]" in code
    assert {variable.name: variable.default_value for variable in module.variables} == {
        "FLAG_ONE": "1U",
        "FLAG_OCTAL": "010",
        "FLAG_SHIFT": "FLAG_ONE << 1",
        "FLAG_CHAR": "'A'",
    }
    assert [variable.name for variable in parse_pyi_text(code, module_name="flags").variables] == [
        "FLAG_ONE",
        "FLAG_OCTAL",
        "FLAG_SHIFT",
        "FLAG_CHAR",
    ]


def test_c2ir_cross_header_enum_references_import_the_owner_enum():
    project = parse_c_project(
        {
            "types.h": "enum status { STATUS_OK = 0 };",
            "api.h": "enum status get_status(void);",
        }
    )

    modules = {module.name: module for module in c_project_to_semantic_modules(project)}

    assert modules["api"].classes == []
    assert modules["types"].classes == []
    assert _function(modules["api"], "get_status").return_type.name == "Int"
    assert _function(modules["api"], "get_status").return_type.metadata["c_enum"] == "enum status"

    anonymous_project = parse_c_project(
        {
            "types.h": "typedef enum { FLAG_NONE = 0 } flag_t;",
            "api.h": "flag_t get_flags(void);",
        }
    )
    anonymous_modules = {module.name: module for module in c_project_to_semantic_modules(anonymous_project)}
    assert _function(anonymous_modules["api"], "get_flags").return_type.name == "Int"


def test_c2ir_uses_enum_specific_underlying_type_facts_when_supplied():
    parsed = parse_c_file(
        "enum status { STATUS_OK = 0, STATUS_ERROR = 255 }; enum status get_status(void);",
        filename="status.h",
    )
    module = CToIRConverter(
        standard_type_report={
            "types": {
                "enum status": {
                    "available": True,
                    "kind": "integer",
                    "signed": False,
                    "bits": 8,
                    "underlying_c_type": "unsigned char",
                }
            }
        }
    ).visit(parsed)

    return_type = _function(module, "get_status").return_type
    assert module.classes == []
    assert return_type.name == "UInt8"
    assert return_type.dtype == "UInt8"
    assert return_type.metadata["c_kind"] == "enum"
    assert return_type.metadata["c_enum_type_fact_source"] == "compiler_probe"


def test_c2ir_uses_standard_type_probe_opaque_handle_facts():
    parsed = parse_c_file("void close_file(FILE *stream);\n", filename="stdio_api.h")
    converter = CToIRConverter(
        standard_type_report={
            "types": {
                "FILE": {
                    "available": True,
                    "kind": "opaque_handle",
                    "pointer_bits": 64,
                }
            }
        }
    )

    module = converter.visit(parsed)
    close_file = _function(module, "close_file")

    assert [(cls.name, cls.base_classes) for cls in module.classes] == [("FILE", ["Opaque"])]
    assert close_file.arguments[0].semantic_type.name == "FILE"
    assert close_file.arguments[0].semantic_type.dtype == "FILE"
    assert close_file.arguments[0].semantic_type.storage.kind == "reference"
    assert close_file.arguments[0].semantic_type.metadata == {
        "c_standard_type": "FILE",
        "c_standard_type_fact": {
            "available": True,
            "kind": "opaque_handle",
            "pointer_bits": 64,
        },
        "c_opaque_handle": True,
        "c_typedefs": ["FILE"],
    }
    opaque = module.classes[0]
    assert opaque.native_name == "FILE"
    assert opaque.metadata == {"c_kind": "opaque_standard_type"}
    _assert_c_origin(
        opaque.origin,
        native_name="FILE",
        source_kind="standard_type",
        source_type="FILE",
    )


def test_c2ir_models_pointer_to_arrays_unknown_extents_unions_and_anonymous_aliases():
    converter = CToIRConverter()
    direct_array = converter.visit(
        CComposedType(components=[CArray(bound="2"), CInt()], source_text="int values[2]"),
        owner="values",
    )
    ownerless_array = converter.visit(
        CComposedType(components=[CArray(bound=None), CInt()], source_text="int values[]")
    )
    named_unknown_array = converter.visit(
        CComposedType(components=[CArray(bound=None), CInt()], source_text="int named_values[]"),
        owner="named_values",
    )
    pointer_array = converter.visit(
        CComposedType(components=[CPointer(), CArray(bound=None), CDouble()], source_text="double (*)[]"),
        owner="matrix",
    )
    pointer_matrix = converter.visit(
        CComposedType(
            components=[CPointer(), CArray(bound="2"), CArray(bound="3"), CInt()],
            source_text="int (*)[2][3]",
        ),
        owner="matrix",
    )
    choice = CUnion(
        name="choice",
        members=[CVariable(name="integer", type=CInt())],
        source_location=CSourceLocation(filename="choice.h", line=1, column=1, source_line="union choice;"),
    )
    converter.unions = {"choice": choice}
    union_type = converter.visit(CUnion(name="choice"), owner="selected", as_type=True)
    anon_struct = CStruct(anonymous_id="anon_struct_1")
    anon_union = CUnion(anonymous_id="anon_union_1")
    converter.typedefs = {
        "record_t": CTypedef(name="record_t", type=anon_struct),
        "variant_t": CTypedef(name="variant_t", type=anon_union),
    }

    assert direct_array.name == "Int"
    assert direct_array.rank == 1
    assert direct_array.shape == ["2"]
    assert direct_array.storage.array.shape == ["2"]
    assert ownerless_array.shape == [":"]
    assert named_unknown_array.shape == [":"]
    assert pointer_array.storage.pointer_depth == 1
    assert pointer_array.storage.array.source_shape == [":"]
    assert pointer_array.storage.metadata["c_pointer_to_array"] is True
    assert pointer_matrix.name == "Int"
    assert pointer_matrix.shape == ["2", "3"]
    assert union_type.name == "choice"
    assert union_type.dtype == "choice"
    assert union_type.metadata == {"c_kind": "union", "incomplete": False}
    _assert_c_origin(
        union_type.origin,
        native_name="union choice",
        source_kind="type",
        source_type="union choice",
        metadata={"c_type": "CUnion"},
    )
    semantic_union = converter.visit(choice)
    assert semantic_union.name == "choice"
    assert semantic_union.native_name == "union choice"
    assert [field.name for field in semantic_union.fields] == ["integer"]
    assert semantic_union.metadata == {"c_kind": "union", "incomplete": False}
    _assert_c_origin(
        semantic_union.origin,
        native_name="union choice",
        source_kind="union",
        source_type="union choice",
        source_location={"filename": "choice.h", "line": 1, "column": 1, "source_line": "union choice;"},
    )
    assert converter.visit(anon_struct).name == "record_t"
    assert converter.visit(anon_union).name == "variant_t"
    assert converter.visit(CStruct()).name == "anonymous_struct"
    assert converter.visit(CUnion()).name == "anonymous_union"
    assert CToIRConverter().visit(CUnion(name="fresh_union"), as_type=True).name == "fresh_union"


def test_c2ir_preserves_nested_unresolved_owners_and_private_opaque_bases():
    converter = CToIRConverter()
    nested_array = converter.visit(
        CComposedType(
            components=[CArray(bound="2"), CUnknownType(spelling="missing_t", source_text="missing_t")],
            source_text="missing_t values[2]",
        ),
        owner="values",
    )
    nested_pointer = converter.visit(
        CComposedType(
            components=[CPointer(), CUnknownType(spelling="missing_t", source_text="missing_t")],
            source_text="missing_t *value",
        ),
        owner="value",
    )
    nested_pointer_array = converter.visit(
        CComposedType(
            components=[CPointer(), CArray(bound="2"), CUnknownType(spelling="missing_t", source_text="missing_t")],
            source_text="missing_t (*)[2]",
        ),
        owner="matrix",
    )
    singleton = converter.visit(
        CComposedType(components=[CUnknownType(spelling="missing_t", source_text="missing_t")]),
        owner="singleton",
    )
    private_class = SemanticClass(
        name="private_handle",
        base_classes=["Opaque"],
        origin=SemanticOrigin(source_language="c", source_location={"filename": "private.h"}),
    )
    private_module = SemanticModule(name="api", classes=[private_class])
    private_file = CFile(
        filename="api.h",
        preprocessing_recipe={"included_files": [{"path": "private.h", "exposure": "private"}]},
    )
    converter._apply_include_exposure(private_module, private_file)

    assert nested_array.name == "missing_t"
    assert nested_pointer.name == "missing_t"
    assert nested_pointer_array.name == "missing_t"
    assert singleton.name == "missing_t"
    assert private_class.visibility == "private"
    assert private_class.base_classes == ["Opaque"]


def test_c2ir_marks_incomplete_by_value_structs_and_preserves_initializer_locations():
    incomplete = CStruct(name="handle", is_incomplete=True)
    converter = CToIRConverter()
    converter.structs = {"handle": incomplete}
    parameter = converter.visit(CParameter(name="handle", type=incomplete), owner="open")
    pointer_parameter = converter.visit(
        CParameter(
            name="handle",
            type=CComposedType(
                components=[CPointer(), CPointer(), incomplete],
                source_text="struct handle **",
            ),
        ),
        owner="open",
    )
    array_parameter = converter.visit(
        CParameter(
            name="handles",
            type=CComposedType(
                components=[CArray(bound="2"), incomplete],
                source_text="struct handle handles[2]",
            ),
        ),
        owner="open",
    )
    variable = converter.visit(
        CVariable(
            name=None,
            type=incomplete,
            initializer=CInitializer("factory()"),
            source_location=CSourceLocation(filename="api.h", line=2, column=4, source_line="struct handle h;"),
        )
    )
    named_variable = converter.visit(CVariable(name="handle", type=incomplete))
    return_type = converter.visit(CFunction(name="open_handle", result_type=incomplete)).return_type

    assert parameter.semantic_type.metadata["incomplete"] is True
    assert pointer_parameter.semantic_type.storage.kind == "pointer"
    assert array_parameter.semantic_type.storage.kind == "array"
    assert named_variable.semantic_type.metadata["incomplete"] is True
    assert return_type.metadata["incomplete"] is True
    assert variable.name == "<anonymous>"
    assert variable.default_value == "factory()"
    assert variable.origin.source_location["filename"] == "api.h"
