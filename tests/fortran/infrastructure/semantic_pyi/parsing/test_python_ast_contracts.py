"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

import ast
import pytest
from prik.printers import emit_module
from prik.semantics.models import (
    SemanticConstraint,
    SemanticModule,
)
from prik.semantics.pyi2ir import (
    convert_pyi_to_ir,
)
from tests.fortran._support.pyi_conversion import (
    CONTRACT_IMPORT,
    parse_pyi_text,
)
from prik.parsers.pyi import parse_pyi_text as parse_pyi_ast_text


def test_pyi_parser_returns_python_ast_only():
    """The parser owns syntax only; semantic conversion accepts nothing but its AST."""
    source = f"{CONTRACT_IMPORT}def scale(value: Float64) -> Float64: ...\n"
    tree = parse_pyi_ast_text(source, filename="scale.pyi")

    assert isinstance(tree, ast.Module)
    assert isinstance(tree.body[-1], ast.FunctionDef)
    assert convert_pyi_to_ir(tree, module_name="parsed", source=source).functions[0].name == "scale"
    with pytest.raises(TypeError, match=r"expects a Python ast\.Module"):
        convert_pyi_to_ir(source)


def test_module_scalar_storage_round_trips():
    """A contract retains which module scalars expose native storage."""
    source = """from prik.contracts import Int32

live: Int32[()]
plain: Int32
"""
    module = parse_pyi_text(source, module_name="owner")
    emitted = emit_module(module)

    assert "live: Int32[()]" in emitted
    assert "plain: Int32" in emitted
    replay = parse_pyi_text(emitted, module_name="owner")
    assert replay.variables[0].semantic_type.metadata["native_storage"] is True
    assert "native_storage" not in replay.variables[1].semantic_type.metadata


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
    assert module.variables[1].name == "alias"
    assert module.variables[1].origin.native_name == "native_alias"
    assert module.variables[1].semantic_type.constraints == [SemanticConstraint("Finite")]
    emitted = emit_module(SemanticModule(name="constraints", variables=[module.variables[0]]))
    assert "value: Annotated[Int32, Bounded(1, 8), Finite]" in emitted
    assert parse_pyi_text(emitted, module_name="constraints").variables[0] == module.variables[0]
