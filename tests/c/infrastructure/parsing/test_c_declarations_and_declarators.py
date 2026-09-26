"""C declaration-specifier and composed-type parser tests."""

import pytest


def test_pointer_qualifiers_belong_to_the_component_they_qualify():
    from prik.parsers.c import CComposedType, CConst, CDouble, CPointer, CRestrict, parse_c_file

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
    from prik.parsers.c import CComposedType, CConst, CInt, CPointer, CVolatile, parse_c_file

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
    from prik.parsers.c import CArray, CComposedType, CConst, CDouble, CInt, CPointer, parse_c_file

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
    from prik.parsers.c import CArray, CComposedType, CConst, CInt, CPointer, parse_c_file

    parsed = parse_c_file("extern const int *left, right[4];\n", filename="variables.h")

    variables = {variable.name: variable for variable in parsed.variables}
    assert variables["left"].storage == ["extern"]
    assert isinstance(variables["left"].type, CComposedType)
    assert [type(component) for component in variables["left"].type.components] == [CPointer, CInt]
    assert [type(component) for component in variables["right"].type.components] == [CArray, CInt]
    assert variables["right"].type.components[0].bound == "4"
    assert variables["right"].type.components[-1].qualifiers == [CConst()]


def test_typedefs_and_typedef_references_are_concrete_types():
    from prik.parsers.c import CArray, CComposedType, CDouble, CPointer, CStruct, CTypedef, CUnsignedLong, parse_c_file

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


def test_variables_preserve_initializer_text_arrays_and_concrete_tag_types():
    from prik.parsers.c import CArray, CEnum, CInt, CStruct, CUnion, parse_c_file

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


def test_storage_is_declaration_metadata_and_qualifiers_are_type_metadata():
    from prik.parsers.c import CAtomic, CConst, CUnsignedLong, CVolatile, parse_c_file

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
    from prik.parsers.c import CAtomic, CComposedType, CInt, CPointer, parse_c_file

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


def test_function_bodies_do_not_contribute_local_variables():
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(
        """
int compute(int x) { int local_value = x + 1; return local_value; }
extern int exported_value;
""",
        filename="locals.c",
    )

    assert [variable.name for variable in parsed.variables] == ["exported_value"]


def test_declaration_attributes_are_tolerated_and_layout_omissions_are_diagnosed():
    from prik.parsers.c import parse_c_file

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
    from prik.parsers.c import parse_c_file

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
    "source",
    [
        "int;\n",
        "namespace api { int run(void); }\n",
        "public:\n",
    ],
)
def test_non_c_top_level_grammar_is_rejected_without_language_guessing(source):
    from prik.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match="Invalid C syntax") as exc_info:
        parse_c_file(source, filename="invalid_top_level.h")

    assert exc_info.value.code == "CPARSE_INVALID_SYNTAX"


def test_braced_and_designated_initializer_declarations_preserve_source_text():
    from prik.parsers.c import CArray, CComposedType, parse_c_file

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
    from prik.parsers.c import parse_c_file

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
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(
        "static inline int local_add(int a, int b) { return a + b; }\nextern int exported_add(int a, int b);\n",
        filename="storage.c",
    )

    functions = {function.name: function for function in parsed.functions}
    assert functions["local_add"].storage == ["static"]
    assert "inline" in functions["local_add"].specifiers
    assert functions["exported_add"].storage == ["extern"]


@pytest.mark.parametrize(
    ("spelling", "expected_name"),
    [
        pytest.param("void", "CVoid", id="void"),
        pytest.param("_Bool", "CBool", id="bool"),
        pytest.param("char", "CChar", id="plain-char"),
        pytest.param("signed char", "CSignedChar", id="signed-char-is-distinct"),
        pytest.param("unsigned char", "CUnsignedChar", id="unsigned-char"),
        pytest.param("signed short int", "CShort", id="short-with-sign-and-int"),
        pytest.param("unsigned short", "CUnsignedShort", id="unsigned-short"),
        pytest.param("signed", "CInt", id="bare-signed-is-int"),
        pytest.param("unsigned", "CUnsignedInt", id="bare-unsigned-is-unsigned-int"),
        pytest.param("long int", "CLong", id="long-int"),
        pytest.param("unsigned long", "CUnsignedLong", id="unsigned-long"),
        pytest.param("signed long long int", "CLongLong", id="long-long-counts-two-longs"),
        pytest.param("unsigned long long", "CUnsignedLongLong", id="unsigned-long-long"),
        pytest.param("float", "CFloat", id="float"),
        pytest.param("double", "CDouble", id="double"),
        pytest.param("long double", "CLongDouble", id="long-double"),
        pytest.param("float _Complex", "CFloatComplex", id="float-complex"),
        pytest.param("_Complex", "CDoubleComplex", id="bare-complex-is-double"),
        pytest.param("long double _Complex", "CLongDoubleComplex", id="long-double-complex"),
        pytest.param("int unsigned", "CUnsignedInt", id="reordered-int-unsigned"),
        pytest.param("int long unsigned", "CUnsignedLong", id="reordered-int-long-unsigned"),
        pytest.param("double long", "CLongDouble", id="reordered-double-long"),
        pytest.param("_Complex float", "CFloatComplex", id="reordered-complex-float"),
    ],
)
def test_primitive_specifier_spellings_create_one_concrete_ctype(spelling, expected_name):
    import prik.parsers.c as c_parser
    from prik.parsers.c import parse_c_file

    function = parse_c_file(f"{spelling} primitive(void);\n", filename="primitive_table.h").functions[0]

    assert isinstance(function.result_type, getattr(c_parser, expected_name))
    # The source spelling survives normalization, whatever the specifier order.
    assert function.result_type.source_text == spelling


@pytest.mark.parametrize(
    ("source", "message", "expected_column"),
    [
        pytest.param("unsigned float value;\n", "Invalid type specifier sequence", 1, id="variable"),
        pytest.param("void bad(long char value);\n", "Invalid type specifier sequence", 1, id="parameter"),
        pytest.param(
            "struct bad { signed unsigned value; };\n", "Invalid type specifier sequence", 14, id="struct-member"
        ),
        pytest.param("unsigned float bad(void) { return 0; }\n", "Invalid type specifier sequence", 1, id="definition"),
        pytest.param("_Atomic(int) long value;\n", "Invalid type specifier sequence", None, id="atomic-plus-long"),
        pytest.param("_Atomic() value;\n", "Invalid _Atomic type-name", None, id="empty-atomic"),
        pytest.param("_Atomic(int named) value;\n", "Invalid _Atomic type-name", None, id="atomic-with-declarator"),
    ],
)
def test_invalid_type_specifier_sequences_raise_located_parse_errors(source, message, expected_column):
    from prik.parsers.c import CParseError, parse_c_file

    with pytest.raises(CParseError, match=message) as error:
        parse_c_file(source, filename="invalid_specifiers.h")

    assert error.value.code == "CPARSE_INVALID_SPECIFIER_SEQUENCE"
    if expected_column is not None:
        assert (
            f"invalid_specifiers.h:1:{expected_column}: error[CPARSE_INVALID_SPECIFIER_SEQUENCE]"
            in error.value.format_diagnostic(color=False)
        )


def test_declarators_compose_pointer_array_and_function_layers_in_c_binding_order():
    from prik.parsers.c import CArray, CFunctionType, CInt, CPointer, parse_c_file

    parsed = parse_c_file(
        """
extern int *values[4];
extern int (*matrix)[4];
extern int *(*table)[4];
typedef int (*compare_fn)(const void *left, const void *right);
typedef int (*callback_table[8])(int);
int (*factory(void))(int);
int direct(void), *value;
void sort_items(int (*fallback)(const void *, const void *));
""",
        filename="recursive_declarators.h",
    )

    def layers(type_):
        return [type(component) for component in type_.components]

    variables = {variable.name: variable for variable in parsed.variables}
    assert layers(variables["values"].type) == [CArray, CPointer, CInt]
    assert layers(variables["matrix"].type) == [CPointer, CArray, CInt]
    assert layers(variables["table"].type) == [CPointer, CArray, CPointer, CInt]
    assert layers(variables["value"].type) == [CPointer, CInt]
    typedefs = {typedef.name: typedef for typedef in parsed.typedefs}
    assert layers(typedefs["compare_fn"].type) == [CPointer, CFunctionType]
    # Placeholder parameter names do not become part of a function type.
    assert len(typedefs["compare_fn"].type.components[1].parameter_types) == 2
    assert layers(typedefs["callback_table"].type) == [CArray, CPointer, CFunctionType]
    functions = {function.name: function for function in parsed.functions}
    assert set(functions) == {"factory", "direct", "sort_items"}
    assert layers(functions["factory"].result_type) == [CPointer, CFunctionType]
    assert functions["sort_items"].parameters[0].callback_candidate is True


@pytest.mark.parametrize(
    ("source", "section", "kept_lines", "initializer", "codes"),
    [
        pytest.param("int i;\nint i;\n", "variables", [2], None, [], id="repeated-tentative-variable-merges"),
        pytest.param(
            "int i;\nint i = 1;\n", "variables", [1], "1", [], id="tentative-then-definition-keeps-definition"
        ),
        pytest.param(
            "int i = 1;\nint i = 2;\n",
            "variables",
            None,
            "1",
            ["C_DUPLICATE_VARIABLE_DEFINITION"],
            id="duplicate-definition",
        ),
        pytest.param(
            "int i;\ndouble i;\n",
            "variables",
            None,
            None,
            ["C_CONFLICTING_VARIABLE_DECLARATION"],
            id="conflicting-types",
        ),
        pytest.param("typedef int i;\ntypedef int i;\n", "typedefs", [2], None, [], id="compatible-typedef-merges"),
        pytest.param(
            "typedef int i;\ntypedef double i;\n",
            "typedefs",
            None,
            None,
            ["C_CONFLICTING_TYPEDEF"],
            id="typedef-conflict",
        ),
        pytest.param(
            "typedef int (*i)(int);\ntypedef double (*i)(double);\n",
            "typedefs",
            None,
            None,
            ["C_CONFLICTING_TYPEDEF"],
            id="function-pointer-typedef-conflict",
        ),
    ],
)
def test_file_scope_redeclarations_merge_or_diagnose(source, section, kept_lines, initializer, codes):
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(source, filename="redeclarations.c")

    declarations = getattr(parsed, section)
    assert [declaration.name for declaration in declarations] == ["i"]
    assert [diagnostic.code for diagnostic in parsed.diagnostics] == codes
    if kept_lines is not None:
        assert [location.line for location in declarations[0].declaration_locations] == kept_lines
    if section == "variables":
        kept = declarations[0].initializer
        assert (kept.source_text if kept is not None else None) == initializer


@pytest.mark.parametrize(
    ("text", "unit_kind", "message"),
    [
        pytest.param(
            "_Static_assert(sizeof(int) == 4)",
            "static_assert",
            "Static assertions are recorded but not evaluated.",
            id="static-assert",
        ),
        pytest.param(
            "int value __attribute__((used))",
            "attribute_declaration",
            "Compiler-specific declaration attributes",
            id="gnu-attribute",
        ),
        pytest.param(
            "int value __declspec(dllexport)",
            "attribute_declaration",
            "Compiler-specific declaration attributes",
            id="declspec",
        ),
        pytest.param(
            "int value [[deprecated]]",
            "attribute_declaration",
            "Compiler-specific declaration attributes",
            id="standard-attribute",
        ),
        pytest.param(
            "_Alignas(16) int value", "alignment_declaration", "Declaration alignment specifiers", id="alignas-keyword"
        ),
        pytest.param(
            "alignas(16) int value", "alignment_declaration", "Declaration alignment specifiers", id="alignas-macro"
        ),
        pytest.param(
            "struct packed { int a; } __attribute__((packed)) value",
            "struct_definition",
            "Struct definitions are not supported yet.",
            id="attributed-struct-definition",
        ),
    ],
)
def test_raw_unsupported_declarations_warn_with_their_location_and_later_declarations_continue(
    text, unit_kind, message
):
    from prik.parsers.c import parse_c_file

    parsed = parse_c_file(f"int kept;\n  {text};\nint later;\n", filename="unsupported.h")

    assert [variable.name for variable in parsed.variables] == ["kept", "later"]
    assert len(parsed.diagnostics) == 1
    diagnostic = parsed.diagnostics[0]
    assert diagnostic.code == "C_UNSUPPORTED_DECLARATION"
    assert diagnostic.severity == "warning"
    assert diagnostic.unit_kind == unit_kind
    assert diagnostic.unit_name is None
    assert message in diagnostic.message
    assert diagnostic.location.filename == "unsupported.h"
    assert diagnostic.location.line == 2
    assert diagnostic.location.column == 3
    assert diagnostic.location.source_line == f"  {text};"


@pytest.mark.parametrize(
    ("source", "name", "type_name"),
    [
        pytest.param("external_type value;\n", "value", "external_type", id="unresolved-typedef-name"),
        pytest.param("class widget;\n", "widget", "class", id="cpp-class-keyword"),
        pytest.param("namespace api = other;\n", "api", "namespace", id="cpp-namespace-keyword"),
        pytest.param("using size_type = value;\n", "size_type", "using", id="cpp-using-keyword"),
    ],
)
def test_identifier_spelling_is_a_deferred_typedef_not_foreign_language_detection(source, name, type_name):
    from prik.parsers.c import CTypedef, parse_c_file

    parsed = parse_c_file(source, filename="identifier_spelling.h")

    assert [variable.name for variable in parsed.variables] == [name]
    assert isinstance(parsed.variables[0].type, CTypedef)
    assert parsed.variables[0].type.name == type_name
    assert parsed.variables[0].type.type is None
    assert parsed.diagnostics == []
