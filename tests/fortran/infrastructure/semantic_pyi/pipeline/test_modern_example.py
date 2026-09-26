from pathlib import Path

from prik.parsers.fortran import parse_fortran_file
from prik.semantics.fortran2ir import fortran_module_to_semantic_module
from prik.printers import emit_module
from tests.fortran._support.paths import GENERAL_FORTRAN_DIR

NATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "native"


def test_modern_fortran_example_pyi_snapshot():
    fixture = GENERAL_FORTRAN_DIR / "modern_pyi_example.f90"
    expected_fixture = Path(__file__).parent / "fixtures" / "modern_math_physics.pyi"
    source = fixture.read_text(encoding="utf-8")

    parsed = parse_fortran_file(source, filename=str(fixture.name))
    modules = [fortran_module_to_semantic_module(m) for m in parsed.modules]
    pyi = "\n\n".join(emit_module(m) for m in modules).strip()

    assert pyi == expected_fixture.read_text(encoding="utf-8").strip()
