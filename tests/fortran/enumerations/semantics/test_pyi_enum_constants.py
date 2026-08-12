"""Tests split by stable ownership concept from `test_python_ast_contracts.py`."""

from prik.printers import emit_module
from tests.fortran._support.pyi_conversion import parse_pyi_text


def test_convert_pyi_to_ir_round_trips_enum_like_integer_constants():
    source = """STATUS_OK: Final[Int] = 0
STATUS_NEXT: Final[Int] = STATUS_OK + 1

def set_status(
    value: Int
) -> None: ...
"""

    module = parse_pyi_text(source, module_name="status_api")

    assert module.classes == []
    assert [item.name for item in module.variables] == ["STATUS_OK", "STATUS_NEXT"]
    assert module.variables[1].default_value == "STATUS_OK + 1"
    assert module.functions[0].arguments[0].semantic_type.name == "Int"
    emitted = emit_module(module)
    assert "STATUS_NEXT: Final[Int] = STATUS_OK + 1" in emitted
    assert parse_pyi_text(emitted, module_name="status_api") == module
