"""C enum declaration parser tests."""


def test_enum_constants_preserve_explicit_implicit_and_symbolic_values():
    from prik.parsers.c import parse_c_file

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
    from prik.parsers.c import CEnum, CStruct, parse_c_file

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
