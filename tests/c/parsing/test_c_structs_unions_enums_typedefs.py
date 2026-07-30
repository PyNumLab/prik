"""C aggregate type, enum, and typedef parser tests."""

import pytest


def test_named_struct_members_are_variables_in_source_order():
    from x2py.parsers.c import CArray, CComposedType, CVariable, parse_c_file

    parsed = parse_c_file(
        "struct point { double x; double y; double coordinates[2]; };\n",
        filename="structs.h",
    )

    point = parsed.structs[0]
    assert [member.name for member in point.members] == ["x", "y", "coordinates"]
    assert all(isinstance(member, CVariable) for member in point.members)
    assert isinstance(point.members[2].type, CComposedType)
    assert isinstance(point.members[2].type.components[0], CArray)
    assert point.members[2].type.components[0].bound == "2"


def test_typedef_struct_alias_refers_to_the_concrete_struct_object():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "typedef struct point { double x; double y; } point_t;\n",
        filename="typedef_struct.h",
    )

    assert parsed.structs[0].name == "point"
    assert parsed.typedefs[0].name == "point_t"
    assert parsed.typedefs[0].type is parsed.structs[0]


def test_forward_struct_declaration_is_completed_by_later_definition():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "struct state;\nstruct state { int id; };\n",
        filename="complete_struct.h",
    )

    assert [struct.name for struct in parsed.structs] == ["state"]
    assert parsed.structs[0].is_incomplete is False
    assert parsed.structs[0].members[0].name == "id"
    assert parsed.diagnostics == []


def test_duplicate_complete_tag_definitions_report_diagnostics():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "struct state { int id; };\nstruct state { int id; };\n",
        filename="duplicate_struct.h",
    )

    assert [struct.name for struct in parsed.structs] == ["state"]
    assert any(diag.code == "C_DUPLICATE_TAG_DEFINITION" for diag in parsed.diagnostics)


def test_anonymous_struct_typedef_gets_stable_anonymous_id():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file("typedef struct { int code; } result_t;\n", filename="anon_struct.h")

    assert parsed.structs[0].name is None
    assert parsed.structs[0].anonymous_id
    assert parsed.typedefs[0].type is parsed.structs[0]


def test_union_members_are_variables_without_struct_field_class():
    from x2py.parsers.c import CUnion, CVariable, parse_c_file

    parsed = parse_c_file("union value { int i; double d; };\n", filename="union.h")

    value = parsed.unions[0]
    assert isinstance(value, CUnion)
    assert [member.name for member in value.members] == ["i", "d"]
    assert all(isinstance(member, CVariable) for member in value.members)


def test_anonymous_union_typedef_refers_to_the_concrete_union_object():
    from x2py.parsers.c import CUnion, parse_c_file

    parsed = parse_c_file("typedef union { int i; double d; } value_t;\n", filename="anon_union.h")

    assert isinstance(parsed.unions[0], CUnion)
    assert parsed.unions[0].anonymous_id
    assert parsed.typedefs[0].type is parsed.unions[0]


def test_function_signatures_using_unions_by_value_report_diagnostics():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
union value { int i; double d; };
int consume(union value value);
union value make_value(void);
void consume_pointer(union value *value);
""",
        filename="union_by_value.h",
    )

    assert [function.name for function in parsed.functions] == [
        "consume",
        "make_value",
        "consume_pointer",
    ]
    assert [
        (diagnostic.code, diagnostic.unit_kind, diagnostic.unit_name, diagnostic.location.line)
        for diagnostic in parsed.diagnostics
    ] == [
        ("C_UNION_BY_VALUE", "function", "consume", 3),
        ("C_UNION_BY_VALUE", "function", "make_value", 4),
    ]


def test_project_reports_union_by_value_through_resolved_typedefs():
    from x2py.parsers.c import parse_c_project

    project = parse_c_project(
        {
            "value.h": "typedef union value { int i; } value_t;\n",
            "api.h": "value_t consume_alias(value_t value);\nvoid consume_alias_pointer(value_t *value);\n",
        }
    )

    assert set(project.functions) == {"consume_alias", "consume_alias_pointer"}
    assert [
        (diagnostic.code, diagnostic.unit_kind, diagnostic.unit_name, diagnostic.location.line)
        for diagnostic in project.diagnostics
        if diagnostic.code == "C_UNION_BY_VALUE"
    ] == [("C_UNION_BY_VALUE", "function", "consume_alias", 1)]


def test_incomplete_union_and_tag_typedef_aliases_use_concrete_tag_classes():
    from x2py.parsers.c import CStruct, CUnion, parse_c_file

    parsed = parse_c_file(
        "struct handle;\nunion payload;\ntypedef struct handle handle_t;\ntypedef union payload payload_t;\n",
        filename="tag_aliases.h",
    )

    assert parsed.structs[0].is_incomplete is True
    assert parsed.unions[0].is_incomplete is True
    typedefs = {typedef.name: typedef for typedef in parsed.typedefs}
    assert isinstance(typedefs["handle_t"].type, CStruct)
    assert typedefs["handle_t"].type.name == "handle"
    assert isinstance(typedefs["payload_t"].type, CUnion)
    assert typedefs["payload_t"].type.name == "payload"


def test_repeated_union_and_enum_tags_normalize_with_duplicate_diagnostics():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
union value;
union value { int integer; };
union value { double real; };
enum status { STATUS_OK };
enum status { STATUS_ERROR };
""",
        filename="duplicate_tags.h",
    )

    assert [member.name for member in parsed.unions[0].members] == ["integer"]
    assert [constant.name for constant in parsed.enums[0].constants] == ["STATUS_OK"]
    assert [(diagnostic.code, diagnostic.unit_kind) for diagnostic in parsed.diagnostics] == [
        ("C_DUPLICATE_TAG_DEFINITION", "union"),
        ("C_DUPLICATE_TAG_DEFINITION", "enum"),
    ]


def test_enum_constants_preserve_explicit_implicit_and_symbolic_values():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
enum status {
    STATUS_OK = 0,
    STATUS_WARN,
    STATUS_ERROR = 10,
    STATUS_NEXT = STATUS_ERROR + 1
};
""",
        filename="enum.h",
    )

    assert [(item.name, item.value) for item in parsed.enums[0].constants] == [
        ("STATUS_OK", "0"),
        ("STATUS_WARN", None),
        ("STATUS_ERROR", "10"),
        ("STATUS_NEXT", "STATUS_ERROR + 1"),
    ]


def test_typedef_enum_and_trailing_tag_variable_are_separate_objects():
    from x2py.parsers.c import CEnum, CStruct, parse_c_file

    parsed = parse_c_file(
        "typedef enum { FLAG_NONE = 0, FLAG_READ = 1 } flag_t;\nstruct point { int x; } origin;\n",
        filename="tag_declarators.h",
    )

    assert parsed.enums[0].anonymous_id
    assert isinstance(parsed.typedefs[0].type, CEnum)
    assert parsed.typedefs[0].type is parsed.enums[0]
    assert parsed.variables[0].name == "origin"
    assert isinstance(parsed.variables[0].type, CStruct)
    assert parsed.variables[0].type is parsed.structs[0]


def test_recursive_struct_pointer_uses_an_incomplete_struct_component_without_cycles():
    from x2py.parsers.c import CComposedType, CPointer, CStruct, parse_c_file

    parsed = parse_c_file(
        "typedef struct node { int value; struct node *next; } node_t;\n",
        filename="recursive_struct.h",
    )

    node = parsed.structs[0]
    next_type = node.members[1].type
    assert isinstance(next_type, CComposedType)
    assert isinstance(next_type.components[0], CPointer)
    assert isinstance(next_type.components[1], CStruct)
    assert next_type.components[1].name == "node"
    assert next_type.components[1].is_incomplete is True


def test_typedef_chains_preserve_typedef_objects_before_resolution():
    from x2py.parsers.c import CTypedef, CUnsignedLong, parse_c_file

    parsed = parse_c_file(
        "typedef unsigned long size_type;\ntypedef size_type api_size;\napi_size count(void);\n",
        filename="typedef_chain.h",
    )

    typedefs = {typedef.name: typedef for typedef in parsed.typedefs}
    assert isinstance(typedefs["size_type"].type, CUnsignedLong)
    assert isinstance(typedefs["api_size"].type, CTypedef)
    assert typedefs["api_size"].type.name == "size_type"
    assert isinstance(parsed.functions[0].result_type, CTypedef)


def test_struct_members_use_same_components_for_callbacks_arrays_and_bitfields():
    from x2py.parsers.c import CArray, CFunctionType, CPointer, parse_c_file

    parsed = parse_c_file(
        "struct hooks { int (*compare)(const void *, const void *); unsigned enabled : 1; int values[4]; };\n",
        filename="members.h",
    )

    compare, enabled, values = parsed.structs[0].members
    assert [type(component) for component in compare.type.components] == [CPointer, CFunctionType]
    assert compare.callback_candidate is True
    assert enabled.bit_width == "1"
    assert isinstance(values.type.components[0], CArray)
    assert values.type.components[0].bound == "4"


def test_struct_members_preserve_precise_locations_and_legal_flexible_array_metadata():
    from x2py.parsers.c import CArray, parse_c_file

    parsed = parse_c_file(
        """struct packet {
    unsigned size;
    unsigned char data[];
};
""",
        filename="packet.h",
    )

    size, data = parsed.structs[0].members
    assert [(member.source_location.line, member.source_location.column) for member in (size, data)] == [
        (2, 5),
        (3, 5),
    ]
    assert data.source_location.source_line == "    unsigned char data[];"
    assert isinstance(data.type.components[0], CArray)
    assert data.type.components[0].is_flexible is True
    assert parsed.diagnostics == []


@pytest.mark.parametrize(
    ("source", "owner_name", "message"),
    [
        (
            """struct bad {
    unsigned char data[];
    int tail;
};
""",
            "structs",
            "must be the final member",
        ),
        (
            """struct bad {
    unsigned char data[];
};
""",
            "structs",
            "requires a preceding named struct member",
        ),
        (
            """union bad {
    unsigned char data[];
    int code;
};
""",
            "unions",
            "cannot be a flexible array member",
        ),
    ],
)
def test_invalid_flexible_array_members_are_diagnosed(source, owner_name, message):
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(source, filename="invalid_flexible.h")
    aggregate = getattr(parsed, owner_name)[0]
    data = aggregate.members[0]

    assert data.type.components[0].is_flexible is False
    assert [(diagnostic.code, diagnostic.severity) for diagnostic in parsed.diagnostics] == [
        ("C_INVALID_FLEXIBLE_ARRAY_MEMBER", "error"),
    ]
    assert message in parsed.diagnostics[0].message
    assert parsed.diagnostics[0].location.line == 2
    assert parsed.diagnostics[0].unit_name == "data"


def test_unnamed_and_zero_width_bitfields_preserve_source_facts_and_locations():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """struct flags {
    unsigned : 0;
    unsigned mode : 3;
};
""",
        filename="bitfields.h",
    )

    zero_width, mode = parsed.structs[0].members
    assert [(member.name, member.bit_width) for member in (zero_width, mode)] == [
        (None, "0"),
        ("mode", "3"),
    ]
    assert [member.source_location.line for member in (zero_width, mode)] == [2, 3]
    assert parsed.diagnostics == []


def test_nested_aggregate_member_definition_builds_the_nested_type():
    from x2py.parsers.c import CStruct, CUnion, parse_c_file

    parsed = parse_c_file(
        """struct outer {
    struct { int nested; } inner;
    union { int integer; double real; } value;
    int kept;
};
""",
        filename="nested_member.h",
    )

    outer = parsed.structs[0]
    assert [member.name for member in outer.members] == ["inner", "value", "kept"]
    assert isinstance(outer.members[0].type, CStruct)
    assert [member.name for member in outer.members[0].type.members] == ["nested"]
    assert outer.members[0].source_location.line == 2
    assert outer.members[0].type.members[0].source_location.line == 2
    assert isinstance(outer.members[1].type, CUnion)
    assert [member.name for member in outer.members[1].type.members] == ["integer", "real"]
    assert parsed.diagnostics == []


def test_anonymous_aggregate_member_without_a_declarator_is_retained():
    from x2py.parsers.c import CUnion, parse_c_file

    parsed = parse_c_file(
        "struct flags { union { int integer; float real; }; int tag; };\n",
        filename="anonymous_member.h",
    )

    anonymous, tag = parsed.structs[0].members
    assert anonymous.name is None
    assert isinstance(anonymous.type, CUnion)
    assert [member.name for member in anonymous.type.members] == ["integer", "real"]
    assert tag.name == "tag"
    assert parsed.diagnostics == []


def test_struct_field_missing_semicolon_reports_syntax_location():
    from x2py.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError) as exc_info:
        parse_c_file(
            """struct broken {
    int value
};
""",
            filename="bad_field_syntax.h",
        )

    error = exc_info.value
    assert error.code == "CPARSE_INVALID_SYNTAX"
    assert error.filename == "bad_field_syntax.h"
    assert error.line_number == 1
    assert error.column == 16
    assert error.source_line == "struct broken {"


def test_nested_aggregate_field_with_function_declarator_is_rejected():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """struct outer {
    struct inner { int x; } field, make(void);
    int kept;
};
""",
        filename="nested_bad_field.h",
    )

    assert [member.name for member in parsed.structs[0].members] == ["kept"]
    assert len(parsed.diagnostics) == 1
    diagnostic = parsed.diagnostics[0]
    assert diagnostic.code == "C_UNSUPPORTED_FIELD_DECLARATION"
    assert diagnostic.message == "Unsupported nested aggregate field declaration."
    assert diagnostic.location is not None
    assert diagnostic.location.line == 2
    assert diagnostic.location.column == 5


def test_bad_field_declarator_does_not_stop_later_declarators():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """struct bad {
    int broken @@, kept;
};
""",
        filename="bad_field_multi.h",
    )

    assert [member.name for member in parsed.structs[0].members] == ["kept"]
    assert len(parsed.diagnostics) == 1
    assert parsed.diagnostics[0].code == "C_UNSUPPORTED_FIELD_DECLARATION"


def test_unnamed_field_type_without_bit_width_reports_diagnostic():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """struct bad {
    int *;
    int kept;
};
""",
        filename="unnamed_field.h",
    )

    assert [member.name for member in parsed.structs[0].members] == ["kept"]
    assert len(parsed.diagnostics) == 1
    diagnostic = parsed.diagnostics[0]
    assert diagnostic.code == "C_UNSUPPORTED_FIELD_DECLARATION"
    assert diagnostic.message == "Unnamed field type is not supported."
    assert diagnostic.location is not None
    assert diagnostic.location.line == 2
    assert diagnostic.location.column == 5


def test_unsupported_field_declarator_is_reported_at_member_location():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """struct bad {
    int broken @@;
    int kept;
};
""",
        filename="bad_field.h",
    )

    assert [member.name for member in parsed.structs[0].members] == ["kept"]
    assert len(parsed.diagnostics) == 1
    diagnostic = parsed.diagnostics[0]
    assert diagnostic.code == "C_UNSUPPORTED_FIELD_DECLARATION"
    assert diagnostic.severity == "warning"
    assert diagnostic.unit_kind == "struct_field"
    assert diagnostic.unit_name is None
    assert diagnostic.message == "Unsupported declarator syntax after parsed type layers: '@@'."
    assert diagnostic.location is not None
    assert diagnostic.location.filename == "bad_field.h"
    assert diagnostic.location.line == 2
    assert diagnostic.location.column == 5
    assert diagnostic.location.source_line == "    int broken @@;"
