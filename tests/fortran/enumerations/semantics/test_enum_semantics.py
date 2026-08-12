"""Fortran enum values and generated semantic-contract behavior."""

from pathlib import Path


from prik import parse_fortran_file as parse_fortran_source
from prik.printers import emit_module
from prik.semantics.fortran2ir import fortran_module_to_semantic_module

ENUM_SOURCE = Path(__file__).parents[1] / "end_to_end" / "fixtures" / "fenums_f90.f90"


def test_fortran_enums_preserve_values_in_generated_pyi_contract():
    parsed = parse_fortran_source(ENUM_SOURCE.read_text(encoding="utf-8"))
    semantic = fortran_module_to_semantic_module(parsed)
    constants = {variable.name: variable for variable in semantic.variables}

    assert [(name, constants[name].default_value) for name in ("red", "blue", "green", "yellow")] == [
        ("red", "-1"),
        ("blue", "0"),
        ("green", "10"),
        ("yellow", "11"),
    ]
    assert constants["red"].semantic_type.metadata["fortran_bind_c"] is True
    stub = emit_module(semantic)
    assert "color: Int32 = red" not in stub
    assert "color: Int32 = ..." in stub
    assert "color: Int32\n" in stub
    assert "red: Final[Int32] = -1" in stub
    assert "yellow: Final[Int32] = 11" in stub
    assert "class Enum" not in stub
    assert "class IntEnum" not in stub
