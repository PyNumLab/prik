"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

from prik.codegen.printers import emit_module
from tests.fortran._support.pyi_conversion import parse_pyi_text


def test_convert_pyi_to_ir_applies_decorators_after_native_call():
    module = parse_pyi_text(
        """
@native_call([])
@private
def hidden() -> None: ...
""",
        module_name="edited",
    )

    assert module.functions[0].visibility == "private"


def test_identity_returns_reconstruct_native_projection_without_decorator():
    source = """
def fill(values: Float64[3]) -> Returns["values", Float64[3]]: ...
"""
    module = parse_pyi_text(source, module_name="identity_returns")
    function = module.functions[0]

    assert len(function.projection) == 1
    assert function.projection[0].native_position == 0
    assert function.projection[0].python_position == 0
    assert function.projection[0].result_position == 0
    assert (
        emit_module(module)
        .strip()
        .endswith('def fill(\n    values: Float64[3]\n) -> Returns["values", Float64[3]]: ...')
    )


def test_convert_pyi_to_ir_accepts_multiline_native_call_decorator():
    module = parse_pyi_text(
        """
@native_call([
    Arg(0),
    Return(0),
])
def wrapper(
    x: Int32
) -> Float64: ...
""",
        module_name="edited",
    )

    func = module.functions[0]
    assert func.name == "wrapper"
    assert func.projection[0].python_position == 0
    assert func.projection[1].result_position == 0
