"""C declaration-specifier and composed-type parser tests."""

import pytest


def test_primitive_specifiers_create_concrete_primitive_types():
    from x2py.parsers.c import CBool, CShort, CUnsignedLongLong, parse_c_file

    parsed = parse_c_file(
        """
unsigned long long next_id(void);
signed short clamp_short(signed short value);
_Bool enabled(void);
""",
        filename="primitives.h",
    )

    functions = {function.name: function for function in parsed.functions}
    assert isinstance(functions["next_id"].result_type, CUnsignedLongLong)
    assert isinstance(functions["clamp_short"].parameters[0].type, CShort)
    assert isinstance(functions["enabled"].result_type, CBool)


@pytest.mark.parametrize(
    ("spelling", "expected_name"),
    [
        ("void", "CVoid"),
        ("_Bool", "CBool"),
        ("char", "CChar"),
        ("signed char", "CSignedChar"),
        ("unsigned char", "CUnsignedChar"),
        ("short", "CShort"),
        ("short int", "CShort"),
        ("signed short", "CShort"),
        ("signed short int", "CShort"),
        ("unsigned short", "CUnsignedShort"),
        ("unsigned short int", "CUnsignedShort"),
        ("int", "CInt"),
        ("signed", "CInt"),
        ("signed int", "CInt"),
        ("unsigned", "CUnsignedInt"),
        ("unsigned int", "CUnsignedInt"),
        ("long", "CLong"),
        ("long int", "CLong"),
        ("signed long", "CLong"),
        ("signed long int", "CLong"),
        ("unsigned long", "CUnsignedLong"),
        ("unsigned long int", "CUnsignedLong"),
        ("long long", "CLongLong"),
        ("long long int", "CLongLong"),
        ("signed long long", "CLongLong"),
        ("signed long long int", "CLongLong"),
        ("unsigned long long", "CUnsignedLongLong"),
        ("unsigned long long int", "CUnsignedLongLong"),
        ("float", "CFloat"),
        ("double", "CDouble"),
        ("long double", "CLongDouble"),
        ("float _Complex", "CFloatComplex"),
        ("_Complex", "CDoubleComplex"),
        ("double _Complex", "CDoubleComplex"),
        ("long double _Complex", "CLongDoubleComplex"),
    ],
)
def test_every_supported_primitive_spelling_creates_a_concrete_ctype(spelling, expected_name):
    import x2py.parsers.c as c_parser
    from x2py.parsers.c import CType, parse_c_file

    function = parse_c_file(f"{spelling} primitive(void);\n", filename="primitive_table.h").functions[0]
    expected = getattr(c_parser, expected_name)

    assert isinstance(function.result_type, expected)
    assert isinstance(function.result_type, CType)


@pytest.mark.parametrize(
    ("spelling", "expected_name"),
    [
        ("int unsigned", "CUnsignedInt"),
        ("int long unsigned", "CUnsignedLong"),
        ("double long", "CLongDouble"),
        ("_Complex float", "CFloatComplex"),
    ],
)
def test_valid_reordered_primitive_specifiers_are_normalized(spelling, expected_name):
    import x2py.parsers.c as c_parser
    from x2py.parsers.c import parse_c_file

    function = parse_c_file(f"{spelling} primitive(void);\n", filename="reordered_primitives.h").functions[0]

    assert isinstance(function.result_type, getattr(c_parser, expected_name))
    assert function.result_type.source_text == spelling


@pytest.mark.parametrize(
    ("source", "expected_column"),
    [
        ("unsigned float value;\n", 1),
        ("void bad(long char value);\n", 1),
        ("struct bad { signed unsigned value; };\n", 14),
        ("unsigned float bad(void) { return 0; }\n", 1),
    ],
)
def test_invalid_primitive_specifier_sequences_raise_parse_errors(source, expected_column):
    from x2py.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match="Invalid type specifier sequence") as error:
        parse_c_file(source, filename="invalid_specifiers.h")

    assert error.value.code == "CPARSE_INVALID_SPECIFIER_SEQUENCE"
    assert (
        f"invalid_specifiers.h:1:{expected_column}: error[CPARSE_INVALID_SPECIFIER_SEQUENCE]"
        in error.value.format_diagnostic(color=False)
    )


def test_unresolved_single_typedef_name_is_preserved_until_resolution():
    from x2py.parsers.c import CTypedef, parse_c_file

    parsed = parse_c_file("external_type value;\n", filename="deferred_typedef.h")

    assert isinstance(parsed.variables[0].type, CTypedef)
    assert parsed.variables[0].type.name == "external_type"
    assert parsed.diagnostics == []


def test_pointer_qualifiers_belong_to_the_component_they_qualify():
    from x2py.parsers.c import CComposedType, CConst, CDouble, CPointer, CRestrict, parse_c_file

    parsed = parse_c_file(
        "void copy(const double * restrict src, double * restrict dst);\n",
        filename="qualifiers.h",
    )

    params = {parameter.name: parameter for parameter in parsed.functions[0].parameters}
    src = params["src"].type
    dst = params["dst"].type
    assert isinstance(src, CComposedType)
    assert isinstance(src.components[0], CPointer)
    assert src.components[0].qualifiers == [CRestrict()]
    assert isinstance(src.components[1], CDouble)
    assert src.components[1].qualifiers == [CConst()]
    assert dst.components[0].qualifiers == [CRestrict()]


def test_multi_level_qualifiers_stay_on_their_exact_type_components():
    from x2py.parsers.c import CComposedType, CConst, CInt, CPointer, CVolatile, parse_c_file

    parsed = parse_c_file(
        "const int * const * volatile chain;\n",
        filename="multi_level_qualifiers.h",
    )

    chain = parsed.variables[0].type
    assert isinstance(chain, CComposedType)
    assert [type(component) for component in chain.components] == [CPointer, CPointer, CInt]
    assert chain.components[0].qualifiers == [CVolatile()]
    assert chain.components[1].qualifiers == [CConst()]
    assert chain.components[2].qualifiers == [CConst()]


def test_array_parameters_preserve_declarations_and_expose_adjusted_pointer_types():
    from x2py.parsers.c import CArray, CComposedType, CConst, CDouble, CInt, CPointer, parse_c_file

    parsed = parse_c_file(
        "void solve(size_t n, double a[static 4], const int shape[2], int work[const *], int matrix[3][4]);\n",
        filename="arrays.h",
    )

    params = {parameter.name: parameter for parameter in parsed.functions[0].parameters}
    a_declared = params["a"].declared_type
    assert isinstance(a_declared, CComposedType)
    assert [type(component) for component in a_declared.components] == [CArray, CDouble]
    assert a_declared.components[0].bound == "4"
    assert a_declared.components[0].is_static_minimum is True
    assert [type(component) for component in params["a"].type.components] == [CPointer, CDouble]

    shape_declared = params["shape"].declared_type
    assert shape_declared.components[0].bound == "2"
    assert shape_declared.components[-1].qualifiers == [CConst()]
    assert [type(component) for component in params["shape"].type.components] == [CPointer, CInt]
    assert params["shape"].type.components[-1].qualifiers == [CConst()]

    work_declared = params["work"].declared_type
    assert work_declared.components[0].qualifiers == [CConst()]
    assert work_declared.components[0].is_variable_length is True
    assert params["work"].type.components[0].qualifiers == [CConst()]

    matrix_declared = params["matrix"].declared_type
    assert [type(component) for component in matrix_declared.components] == [CArray, CArray, CInt]
    assert [component.bound for component in matrix_declared.components[:2]] == ["3", "4"]
    assert [type(component) for component in params["matrix"].type.components] == [CPointer, CArray, CInt]
    assert params["matrix"].type.components[1].bound == "4"


def test_multiple_declarators_share_specifiers_but_have_distinct_compositions():
    from x2py.parsers.c import CArray, CComposedType, CConst, CInt, CPointer, parse_c_file

    parsed = parse_c_file("extern const int *left, right[4];\n", filename="variables.h")

    variables = {variable.name: variable for variable in parsed.variables}
    assert variables["left"].storage == ["extern"]
    assert isinstance(variables["left"].type, CComposedType)
    assert [type(component) for component in variables["left"].type.components] == [CPointer, CInt]
    assert [type(component) for component in variables["right"].type.components] == [CArray, CInt]
    assert variables["right"].type.components[0].bound == "4"
    assert variables["right"].type.components[-1].qualifiers == [CConst()]


def test_typedefs_and_typedef_references_are_concrete_types():
    from x2py.parsers.c import CArray, CComposedType, CDouble, CPointer, CStruct, CTypedef, CUnsignedLong, parse_c_file

    parsed = parse_c_file(
        """
struct state;
typedef unsigned long api_size;
typedef const struct state *state_ref;
typedef double vector3[3];
typedef vector3 basis3[3];
state_ref current_state(void);
void set_basis(basis3 basis);
""",
        filename="typedef_layers.h",
    )

    typedefs = {typedef.name: typedef for typedef in parsed.typedefs}
    assert isinstance(typedefs["api_size"].type, CUnsignedLong)
    state_ref = typedefs["state_ref"].type
    assert isinstance(state_ref, CComposedType)
    assert [type(component) for component in state_ref.components] == [CPointer, CStruct]
    assert state_ref.components[-1].name == "state"
    assert isinstance(typedefs["vector3"].type.components[0], CArray)
    assert isinstance(typedefs["vector3"].type.components[-1], CDouble)
    assert isinstance(typedefs["basis3"].type.components[-1], CTypedef)
    assert typedefs["basis3"].type.components[-1].name == "vector3"
    assert isinstance(parsed.functions[1].parameters[0].type, CTypedef)


def test_repeated_file_scope_tentative_variable_declarations_merge():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file("int i;\nint i;\n", filename="tentative.c")

    assert [variable.name for variable in parsed.variables] == ["i"]
    assert parsed.variables[0].initializer is None
    assert [location.line for location in parsed.variables[0].declaration_locations] == [2]
    assert parsed.diagnostics == []


def test_tentative_variable_declaration_followed_by_definition_prefers_definition():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file("int i;\nint i = 1;\n", filename="definition.c")

    assert [variable.name for variable in parsed.variables] == ["i"]
    assert parsed.variables[0].initializer.source_text == "1"
    assert parsed.variables[0].source_location.line == 2
    assert [location.line for location in parsed.variables[0].declaration_locations] == [1]
    assert parsed.diagnostics == []


def test_duplicate_initialized_file_scope_variables_report_diagnostic():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file("int i = 1;\nint i = 2;\n", filename="duplicate_variables.c")

    assert [variable.name for variable in parsed.variables] == ["i"]
    assert parsed.variables[0].initializer.source_text == "1"
    assert any(diag.code == "C_DUPLICATE_VARIABLE_DEFINITION" for diag in parsed.diagnostics)


def test_conflicting_file_scope_variable_declarations_report_diagnostic():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file("int i;\ndouble i;\n", filename="conflicting_variables.c")

    assert [variable.name for variable in parsed.variables] == ["i"]
    assert any(diag.code == "C_CONFLICTING_VARIABLE_DECLARATION" for diag in parsed.diagnostics)


def test_type_key_preserves_seen_state_for_recursive_composed_types():
    from x2py.parsers.c import CComposedType, CParser, CPointer, CTypedef

    typedef = CTypedef(name="node")
    recursive = CComposedType(components=[CPointer(), typedef])
    typedef.type = recursive

    assert CParser()._type_key(recursive) == (
        "CComposedType",
        (
            ("CPointer", ()),
            ("CTypedef", ("cycle", "CComposedType", None), ()),
        ),
        (),
    )


def test_compatible_repeated_typedefs_merge_but_conflicting_typedefs_diagnose():
    from x2py.parsers.c import parse_c_file

    compatible = parse_c_file("typedef int count_t;\ntypedef int count_t;\n", filename="typedefs.h")
    conflicting = parse_c_file("typedef int count_t;\ntypedef double count_t;\n", filename="bad_typedefs.h")

    assert [typedef.name for typedef in compatible.typedefs] == ["count_t"]
    assert [location.line for location in compatible.typedefs[0].declaration_locations] == [2]
    assert compatible.diagnostics == []
    assert any(diag.code == "C_CONFLICTING_TYPEDEF" for diag in conflicting.diagnostics)


def test_variables_preserve_initializer_text_arrays_and_concrete_tag_types():
    from x2py.parsers.c import CArray, CEnum, CInt, CStruct, CUnion, parse_c_file

    parsed = parse_c_file(
        """
const struct state *global_state = 0;
volatile union scalar *global_scalar;
const enum status last_status = STATUS_OK;
double matrix[3][4];
int answer = 42;
""",
        filename="variables_richer.h",
    )

    variables = {variable.name: variable for variable in parsed.variables}
    assert isinstance(variables["global_state"].type.components[-1], CStruct)
    assert variables["global_state"].type.components[-1].name == "state"
    assert variables["global_state"].initializer.source_text == "0"
    assert isinstance(variables["global_scalar"].type.components[-1], CUnion)
    assert isinstance(variables["last_status"].type, CEnum)
    assert variables["last_status"].initializer.source_text == "STATUS_OK"
    assert [component.bound for component in variables["matrix"].type.components[:2]] == ["3", "4"]
    assert all(isinstance(component, CArray) for component in variables["matrix"].type.components[:2])
    assert isinstance(variables["answer"].type, CInt)
    assert variables["answer"].initializer.source_text == "42"


def test_parameters_preserve_concrete_struct_union_and_enum_uses():
    from x2py.parsers.c import CEnum, CStruct, CUnion, parse_c_file

    parsed = parse_c_file(
        "void consume(const struct state *s, union scalar *u, enum status status);\n",
        filename="tag_params.h",
    )

    params = {parameter.name: parameter for parameter in parsed.functions[0].parameters}
    assert isinstance(params["s"].type.components[-1], CStruct)
    assert params["s"].type.components[-1].name == "state"
    assert isinstance(params["u"].type.components[-1], CUnion)
    assert isinstance(params["status"].type, CEnum)


def test_incomplete_structs_and_pointer_uses_are_concrete_objects():
    from x2py.parsers.c import CComposedType, CPointer, CStruct, parse_c_file

    parsed = parse_c_file(
        """
struct handle;
struct handle *open_handle(void);
void close_handle(struct handle *handle);
""",
        filename="opaque.h",
    )

    handle = parsed.structs[0]
    assert isinstance(handle, CStruct)
    assert handle.name == "handle"
    assert handle.is_incomplete is True
    assert handle.members == []

    functions = {function.name: function for function in parsed.functions}
    result = functions["open_handle"].result_type
    assert isinstance(result, CComposedType)
    assert isinstance(result.components[0], CPointer)
    assert isinstance(result.components[1], CStruct)
    assert result.components[1].name == "handle"


def test_storage_is_declaration_metadata_and_qualifiers_are_type_metadata():
    from x2py.parsers.c import CAtomic, CConst, CUnsignedLong, CVolatile, parse_c_file

    parsed = parse_c_file(
        """
extern int api_errno;
static const double scale_factor = 1.0;
_Thread_local unsigned long tls_counter;
register volatile int scratch;
_Atomic int atomic_counter;
""",
        filename="storage_variables.h",
    )

    variables = {variable.name: variable for variable in parsed.variables}
    assert variables["api_errno"].storage == ["extern"]
    assert variables["scale_factor"].storage == ["static"]
    assert variables["scale_factor"].type.qualifiers == [CConst()]
    assert variables["tls_counter"].storage == ["_Thread_local"]
    assert isinstance(variables["tls_counter"].type, CUnsignedLong)
    assert variables["scratch"].storage == ["register"]
    assert variables["scratch"].type.qualifiers == [CVolatile()]
    assert variables["atomic_counter"].type.qualifiers == [CAtomic()]


def test_atomic_type_specifier_qualifies_the_declared_outermost_type():
    from x2py.parsers.c import CAtomic, CComposedType, CInt, CPointer, parse_c_file

    parsed = parse_c_file(
        """
_Atomic(int) atomic_value;
_Atomic(int *) atomic_pointer;
_Atomic(int) *pointer_to_atomic;
""",
        filename="atomic_types.h",
    )

    variables = {variable.name: variable for variable in parsed.variables}
    assert isinstance(variables["atomic_value"].type, CInt)
    assert variables["atomic_value"].type.qualifiers == [CAtomic()]

    atomic_pointer = variables["atomic_pointer"].type
    assert isinstance(atomic_pointer, CComposedType)
    assert isinstance(atomic_pointer.components[0], CPointer)
    assert atomic_pointer.components[0].qualifiers == [CAtomic()]
    assert atomic_pointer.components[1].qualifiers == []

    pointer_to_atomic = variables["pointer_to_atomic"].type
    assert isinstance(pointer_to_atomic.components[0], CPointer)
    assert pointer_to_atomic.components[0].qualifiers == []
    assert pointer_to_atomic.components[1].qualifiers == [CAtomic()]
    assert parsed.diagnostics == []


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("_Atomic(int) long value;\n", "Invalid type specifier sequence"),
        ("_Atomic() value;\n", "Invalid _Atomic type-name"),
        ("_Atomic(int named) value;\n", "Invalid _Atomic type-name"),
    ],
)
def test_invalid_atomic_type_specifiers_raise_focused_errors(source, message):
    from x2py.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match=message) as exc_info:
        parse_c_file(source, filename="invalid_atomic.h")

    assert exc_info.value.code == "CPARSE_INVALID_SPECIFIER_SEQUENCE"


def test_function_bodies_do_not_contribute_local_variables():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int compute(int x) { int local_value = x + 1; return local_value; }
extern int exported_value;
""",
        filename="locals.c",
    )

    assert [variable.name for variable in parsed.variables] == ["exported_value"]


def test_declarations_return_concrete_objects_instead_of_kind_fields():
    from x2py.parsers.c import (
        CArray,
        CFunction,
        CFunctionType,
        CInt,
        CPointer,
        CStruct,
        CTypedef,
        CVariable,
        parse_c_file,
    )

    parsed = parse_c_file(
        """
struct handle;
typedef int (*compare_fn)(const void *, const void *);
extern int *values[4];
extern int (*matrix)[4];
int add(int a, int b);
void sort_items(int (*fallback)(const void *, const void *));
""",
        filename="declaration_matrix.h",
    )

    assert isinstance(parsed.structs[0], CStruct)
    assert all(isinstance(typedef, CTypedef) for typedef in parsed.typedefs)
    assert all(isinstance(variable, CVariable) for variable in parsed.variables)
    assert all(isinstance(function, CFunction) for function in parsed.functions)

    compare = parsed.typedefs[0].type
    assert [type(component) for component in compare.components] == [CPointer, CFunctionType]
    values, matrix = parsed.variables
    assert [type(component) for component in values.type.components] == [CArray, CPointer, CInt]
    assert [type(component) for component in matrix.type.components] == [CPointer, CArray, CInt]
    assert parsed.functions[1].parameters[0].callback_candidate is True


def test_composite_definitions_are_concrete_objects_and_static_assert_is_diagnostic():
    from x2py.parsers.c import CEnum, CStruct, CUnion, CVariable, parse_c_file

    parsed = parse_c_file(
        """
struct point { double x; double y; };
union value { int i; double d; };
enum status { STATUS_OK = 0 };
_Static_assert(sizeof(int) == 4, "expected int width");
""",
        filename="composites.h",
    )

    assert isinstance(parsed.structs[0], CStruct)
    assert all(isinstance(member, CVariable) for member in parsed.structs[0].members)
    assert [member.name for member in parsed.structs[0].members] == ["x", "y"]
    assert isinstance(parsed.unions[0], CUnion)
    assert isinstance(parsed.enums[0], CEnum)
    assert [diagnostic.unit_kind for diagnostic in parsed.diagnostics] == ["static_assert"]


def test_parenthesized_declarators_preserve_pointer_array_order():
    from x2py.parsers.c import CArray, CInt, CPointer, parse_c_file

    parsed = parse_c_file("extern int *values[4];\nextern int (*matrix)[4];\n", filename="paren_decl.h")
    variables = {variable.name: variable for variable in parsed.variables}

    assert [type(component) for component in variables["values"].type.components] == [CArray, CPointer, CInt]
    assert [type(component) for component in variables["matrix"].type.components] == [CPointer, CArray, CInt]


def test_function_type_discards_placeholder_parameter_names():
    from x2py.parsers.c import CFunctionType, CPointer, parse_c_file

    parsed = parse_c_file(
        "typedef int (*compare_fn)(const void *left, const void *right);\n",
        filename="callback_typedef.h",
    )

    type_ = parsed.typedefs[0].type
    assert isinstance(type_.components[0], CPointer)
    signature = type_.components[1]
    assert isinstance(signature, CFunctionType)
    assert len(signature.parameter_types) == 2


def test_conflicting_function_pointer_typedefs_report_diagnostic():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "typedef int (*callback_fn)(int);\ntypedef double (*callback_fn)(double);\n",
        filename="callback_typedef_conflict.h",
    )

    assert [typedef.name for typedef in parsed.typedefs] == ["callback_fn"]
    assert [(diagnostic.code, diagnostic.unit_kind, diagnostic.unit_name) for diagnostic in parsed.diagnostics] == [
        ("C_CONFLICTING_TYPEDEF", "typedef", "callback_fn")
    ]


def test_recursive_compositions_cover_tables_callback_arrays_and_function_results():
    from x2py.parsers.c import CArray, CFunctionType, CInt, CPointer, parse_c_file

    parsed = parse_c_file(
        """
extern int *(*table)[4];
typedef int (*callback_table[8])(int);
int (*factory(void))(int);
int direct(void), *value;
""",
        filename="recursive_declarators.h",
    )

    variables = {variable.name: variable for variable in parsed.variables}
    assert [type(component) for component in variables["table"].type.components] == [
        CPointer,
        CArray,
        CPointer,
        CInt,
    ]
    assert [type(component) for component in variables["value"].type.components] == [CPointer, CInt]
    callbacks = parsed.typedefs[0].type
    assert [type(component) for component in callbacks.components] == [CArray, CPointer, CFunctionType]
    functions = {function.name: function for function in parsed.functions}
    assert set(functions) == {"factory", "direct"}
    assert [type(component) for component in functions["factory"].result_type.components] == [
        CPointer,
        CFunctionType,
    ]


def test_declaration_attributes_are_tolerated_and_layout_omissions_are_diagnosed():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int visible __attribute__((visibility("default")));
int outdated [[deprecated]];
_Alignas(16) int aligned_value;
        """,
        filename="extensions.h",
        preprocessing="compiler",
    )

    assert [variable.name for variable in parsed.variables] == ["visible", "outdated", "aligned_value"]
    assert [(diagnostic.code, diagnostic.unit_kind, diagnostic.unit_name) for diagnostic in parsed.diagnostics] == [
        ("C_UNMODELED_COMPILER_EXTENSION", "alignment_specifier", "_Alignas"),
    ]


def test_unsupported_top_level_declarator_is_reported_with_source_location():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file("int value @@;\nint kept;\n", filename="bad_declarator.h")

    assert [variable.name for variable in parsed.variables] == ["kept"]
    assert len(parsed.diagnostics) == 1
    diagnostic = parsed.diagnostics[0]
    assert diagnostic.code == "C_UNSUPPORTED_DECLARATOR"
    assert diagnostic.severity == "warning"
    assert diagnostic.unit_kind == "declarator"
    assert diagnostic.unit_name is None
    assert diagnostic.message == "Unsupported declarator syntax after parsed type layers: '@@'."
    assert diagnostic.location is not None
    assert diagnostic.location.filename == "bad_declarator.h"
    assert diagnostic.location.line == 1
    assert diagnostic.location.column == 1
    assert diagnostic.location.source_line == "int value @@;"


@pytest.mark.parametrize(
    ("text", "unit_kind", "message"),
    [
        ("struct pending { int value; }", "struct_definition", "Struct definitions are not supported yet."),
        ("union pending { int value; }", "union_definition", "Union definitions are not supported yet."),
        ("enum pending { value }", "enum_definition", "Enum definitions are not supported yet."),
        ("_Static_assert(sizeof(int) == 4)", "static_assert", "Static assertions are recorded but not evaluated."),
        ("int value __attribute__((used))", "attribute_declaration", "Compiler-specific declaration attributes"),
        ("int value __declspec(dllexport)", "attribute_declaration", "Compiler-specific declaration attributes"),
        ("int value [[deprecated]]", "attribute_declaration", "Compiler-specific declaration attributes"),
        ("_Alignas(16) int value", "alignment_declaration", "Declaration alignment specifiers"),
        ("alignas(16) int value", "alignment_declaration", "Declaration alignment specifiers"),
        ("int values[] = {1, 2, 3}", "brace_declaration", "Unsupported declaration containing braces."),
    ],
)
def test_unsupported_declaration_diagnostic_classifies_known_shapes(text, unit_kind, message):
    from x2py.parsers.c import CParser
    from x2py.parsers.c.lexer import CTopLevelSegment

    segment = CTopLevelSegment(
        text=text,
        terminator=";",
        filename="unsupported.h",
        original_start_line=7,
        original_start_column=3,
        original_source_line=f"  {text};",
    )

    diagnostic = CParser()._unsupported_declaration_diagnostic(segment)

    assert diagnostic is not None
    assert diagnostic.code == "C_UNSUPPORTED_DECLARATION"
    assert diagnostic.severity == "warning"
    assert diagnostic.unit_kind == unit_kind
    assert diagnostic.unit_name is None
    assert message in diagnostic.message
    assert diagnostic.location is not None
    assert diagnostic.location.filename == "unsupported.h"
    assert diagnostic.location.line == 7
    assert diagnostic.location.column == 3
    assert diagnostic.location.source_line == f"  {text};"


def test_unsupported_declaration_diagnostic_ignores_empty_and_plain_declarations():
    from x2py.parsers.c import CParser
    from x2py.parsers.c.lexer import CTopLevelSegment

    parser = CParser()

    assert parser._unsupported_declaration_diagnostic(CTopLevelSegment(text="", terminator=";")) is None
    assert parser._unsupported_declaration_diagnostic(CTopLevelSegment(text="int value", terminator=";")) is None


@pytest.mark.parametrize(
    "source",
    [
        "int;\n",
        "namespace api { int run(void); }\n",
        "public:\n",
    ],
)
def test_non_c_top_level_grammar_is_rejected_without_language_guessing(source):
    from x2py.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match="Invalid C syntax") as exc_info:
        parse_c_file(source, filename="invalid_top_level.h")

    assert exc_info.value.code == "CPARSE_INVALID_SYNTAX"


@pytest.mark.parametrize(
    ("source", "name", "type_name"),
    [
        ("class widget;\n", "widget", "class"),
        ("namespace api = other;\n", "api", "namespace"),
        ("using size_type = value;\n", "size_type", "using"),
    ],
)
def test_identifier_spelling_does_not_trigger_foreign_language_detection(source, name, type_name):
    from x2py.parsers.c import CTypedef, parse_c_file

    parsed = parse_c_file(source, filename="identifier_spelling.h")

    assert [variable.name for variable in parsed.variables] == [name]
    assert isinstance(parsed.variables[0].type, CTypedef)
    assert parsed.variables[0].type.name == type_name


def test_braced_and_designated_initializer_declarations_preserve_source_text():
    from x2py.parsers.c import CArray, CComposedType, parse_c_file

    parsed = parse_c_file(
        "struct config;\nint values[3] = {1, 2, 3};\nstruct config cfg = {.enabled = 1};\nint scalar = 1;\n",
        filename="braced_initializers.h",
    )

    variables = {variable.name: variable for variable in parsed.variables}
    assert set(variables) == {"values", "cfg", "scalar"}
    assert isinstance(variables["values"].type, CComposedType)
    assert isinstance(variables["values"].type.components[0], CArray)
    assert variables["values"].initializer.source_text == "{1, 2, 3}"
    assert variables["cfg"].initializer.source_text == "{.enabled = 1}"
    assert variables["scalar"].initializer.source_text == "1"
    assert parsed.diagnostics == []


def test_asm_declarator_suffixes_are_tolerated_with_symbol_identity_diagnostics():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        'extern int retained, pinned asm("r0");\nint run(int value asm("r0"));\n',
        filename="declarator_extensions.h",
        preprocessing="compiler",
    )

    assert [variable.name for variable in parsed.variables] == ["retained", "pinned"]
    assert [function.name for function in parsed.functions] == ["run"]
    assert [(diagnostic.code, diagnostic.unit_kind) for diagnostic in parsed.diagnostics] == [
        ("C_UNMODELED_COMPILER_EXTENSION", "asm_label"),
        ("C_UNMODELED_COMPILER_EXTENSION", "asm_label"),
    ]


def test_storage_class_and_inline_specifiers_are_recorded_on_functions():
    from x2py.parsers.c import parse_c_file

    parsed = parse_c_file(
        "static inline int local_add(int a, int b) { return a + b; }\nextern int exported_add(int a, int b);\n",
        filename="storage.c",
    )

    functions = {function.name: function for function in parsed.functions}
    assert functions["local_add"].storage == ["static"]
    assert "inline" in functions["local_add"].specifiers
    assert functions["exported_add"].storage == ["extern"]
