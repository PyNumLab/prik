"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

from pathlib import Path
import subprocess
import sys

from tests.fortran._support.pyi_conversion import (
    CONTRACT_IMPORT,
    CONTRACT_SYMBOLS,
    ProjectionMapping,
    SemanticArgument,
    SemanticConstraint,
    SemanticModule,
    SemanticType,
    _PyiAstParser,
    ast,
    convert_pyi_to_ir,
    emit_module,
    parse_pyi_ast_text,
    parse_pyi_text,
    pytest,
)


def test_pyi_parser_returns_python_ast_only():
    tree = parse_pyi_ast_text("def scale(value: Float64) -> Float64: ...\n", filename="scale.pyi")

    assert isinstance(tree, ast.Module)
    assert isinstance(tree.body[0], ast.FunctionDef)
    assert tree.body[0].name == "scale"


def test_convert_pyi_to_ir_accepts_parsed_pyi_ast_only():
    source = f"{CONTRACT_IMPORT}value: Int32\n"
    tree = parse_pyi_ast_text(source, filename="contract.pyi")

    module = convert_pyi_to_ir(tree, module_name="parsed", source=source)

    assert module.name == "parsed"
    assert module.variables[0].name == "value"
    with pytest.raises(TypeError, match=r"expects a Python ast\.Module"):
        convert_pyi_to_ir(source)


def test_pyi2ir_direct_example_is_runnable():
    repository_root = Path(__file__).resolve().parents[4]

    result = subprocess.run(
        [sys.executable, "prik/semantics/pyi2ir.py"],
        cwd=repository_root,
        capture_output=True,
        check=True,
        text=True,
    )

    assert result.stdout == "math.scale(value): Float64 -> Float64\n"


def test_pyi_parser_reports_unsupported_lines_and_invalid_helpers():
    with pytest.raises(ValueError, match=r"Unsupported .pyi node"):
        parse_pyi_text("bare_name\n", module_name="edited")

    with pytest.raises(ValueError, match="Unsupported class body node"):
        parse_pyi_text("class C:\n    bare_name\n", module_name="edited")

    with pytest.raises(ValueError, match="Expected typed argument"):
        parse_pyi_text("def f(x) -> None: ...\n", module_name="edited")

    with pytest.raises(ValueError, match="expects positional arguments only"):
        parse_pyi_text("@native_call([Arg(0, name='x')])\ndef f(x: Int32) -> None: ...\n", module_name="edited")

    with pytest.raises(ValueError, match="Expected imported prik contract helper"):
        parse_pyi_text("@native_call([Unknown(0)])\ndef f(x: Int32) -> None: ...\n", module_name="edited")

    with pytest.raises(ValueError, match="Expected imported prik contract helper"):
        parse_pyi_text("@native_call([Len(Unknown(0))])\ndef f(x: Int32) -> None: ...\n", module_name="edited")

    with pytest.raises(ValueError, match="Unknown semantic type is not allowed"):
        parse_pyi_text("x: Unknown\n", module_name="edited")


def test_pyi_parser_preserves_generic_constraints_as_annotation_metadata():
    module = parse_pyi_text(
        """
value: Annotated[Int32, Bounded(1, 8), Finite]
alias: Annotated[Int32, SourceName("native_alias"), Finite]
""",
        module_name="edited",
    )

    assert module.variables[0].name == "value"
    assert module.variables[0].semantic_type.constraints == [
        SemanticConstraint("Bounded", [1, 8]),
        SemanticConstraint("Finite"),
    ]
    assert module.variables[1].name == "native_alias"
    assert module.variables[1].semantic_type.constraints == [SemanticConstraint("Finite")]
    emitted = emit_module(SemanticModule(name="constraints", variables=[module.variables[0]]))
    assert "value: Annotated[Int32, Bounded(1, 8), Finite]" in emitted
    assert parse_pyi_text(emitted, module_name="constraints").variables[0] == module.variables[0]


def test_pyi_parser_internal_projection_helpers_preserve_native_names():
    parser = _PyiAstParser(module_name="internal")
    parser._contract_bindings.update({name: name for name in CONTRACT_SYMBOLS})
    return_type, returned_values = parser.return_projection(
        ast.parse("tuple[Float64, Returns['extra', Int32] | None, Returns['other', Float64]]", mode="eval").body
    )
    pointer = parser.semantic_type(ast.parse("Addr(Float64)", mode="eval").body)
    returned = SemanticArgument("result", SemanticType("Float64"), metadata={"return_position": 1})
    mapping = ProjectionMapping(native_name="native_result", result_position=1)
    _, values = parser._apply_native_call_returns(None, [returned], [mapping])
    native_arg = SemanticArgument("python_name", SemanticType("Int32"))
    arg_mapping = ProjectionMapping(native_name="native_name", python_position=0)
    parser._apply_native_call_argument_names([native_arg], {}, [arg_mapping])

    assert return_type.name == "Float64"
    assert returned_values[0].name == "extra"
    assert returned_values[0].optional is True
    assert returned_values[0].metadata == {"return_position": 1}
    assert returned_values[0].semantic_type.ownership.mutable is True
    assert returned_values[1].name == "other"
    assert returned_values[1].metadata == {"return_position": 2}
    assert pointer.storage.mutable is True
    assert pointer.ownership.mutable is True
    assert values[0].name == "native_result"
    assert arg_mapping.native_name == "native_name"
