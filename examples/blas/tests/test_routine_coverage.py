"""Fail closed when the reference source set, inventory, exports, or tests drift."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from prik.parsers.fortran.parser import parse_fortran_file

from ..f2py_build import (
    BLAS_SOURCES,
    F2PY_INOUT_ARGUMENTS,
    f2py_build_command,
    f2py_signature_command,
)
from ..routine_inventory import (
    ALL_ROUTINES,
    DIFFERENTIALLY_TESTED_ROUTINES,
    EXPLICIT_TEST_NAMES,
    PERMANENTLY_SKIPPED_ROUTINES,
    PRIK_TESTED_ROUTINES,
    ROUTINE_GROUPS,
    UNSUPPORTED_ROUTINES,
)


pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]
TEST_ROOT = Path(__file__).resolve().parent
EXAMPLE_ROOT = TEST_ROOT.parent

TEST_MODULES = (
    "test_level1_real.py",
    "test_level1_complex.py",
    "test_level2_general.py",
    "test_level2_symmetric.py",
    "test_level2_hermitian.py",
    "test_level2_triangular.py",
    "test_level2_packed.py",
    "test_level2_banded.py",
    "test_level3_general.py",
    "test_level3_symmetric.py",
    "test_level3_hermitian.py",
    "test_level3_triangular.py",
    "test_auxiliary.py",
)


def test_f2py_commands_generate_signatures_and_reuse_the_native_library(tmp_path: Path):
    native_library = tmp_path / "native" / "libprik_full_blas.so"
    signature_command = f2py_signature_command(tmp_path / "f2py")
    f2py_command = f2py_build_command(tmp_path / "f2py", native_library)

    assert signature_command[:5] == (sys.executable, "-m", "numpy.f2py", "-m", "f2py_reference_blas")
    assert f2py_command[:4] == (sys.executable, "-m", "numpy.f2py", "-c")
    assert f"-L{native_library.parent}" in f2py_command
    assert "-lprik_full_blas" in f2py_command
    for source in BLAS_SOURCES:
        expected_f2py_source = (
            tmp_path / "f2py" / "f2py-intent-sources" / source.name if source.stem in F2PY_INOUT_ARGUMENTS else source
        )
        assert str(expected_f2py_source) in signature_command
        assert str(source) not in f2py_command


def test_f2py_scalar_writeback_overlays_are_explicit(tmp_path: Path):
    command = f2py_signature_command(tmp_path)

    for routine, arguments in F2PY_INOUT_ARGUMENTS.items():
        source = next(source for source in BLAS_SOURCES if source.stem == routine)
        overlay = tmp_path / "f2py-intent-sources" / source.name
        prefix = "Cf2py" if source.suffix == ".f" else "!f2py"
        assert str(overlay) in command
        assert f"{prefix} intent(inout) {', '.join(arguments)}" in overlay.read_text(encoding="utf-8")


def _source_routines() -> tuple[str, ...]:
    routines: list[str] = []
    for source in BLAS_SOURCES:
        parsed = parse_fortran_file(source.read_text(encoding="utf-8"), filename=source.name)
        routines.extend(procedure.name.lower() for procedure in parsed.procedures)
    return tuple(routines)


def _explicit_test_functions() -> dict[str, tuple[Path, ast.FunctionDef]]:
    functions: dict[str, tuple[Path, ast.FunctionDef]] = {}
    for filename in TEST_MODULES:
        path = TEST_ROOT / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                assert node.name not in functions, f"duplicate explicitly named test: {node.name}"
                functions[node.name] = (path, node)
    return functions


def test_source_routines_match_the_classified_inventory():
    source_routines = _source_routines()
    assert len(BLAS_SOURCES) == 155
    assert len(source_routines) == 155
    assert len(source_routines) == len(set(source_routines)), "source routine names must be unique"
    assert len(ALL_ROUTINES) == len(set(ALL_ROUTINES)), "each routine must have exactly one classification"
    assert set(source_routines) == set(ALL_ROUTINES)
    assert sum(len(routines) for routines in ROUTINE_GROUPS.values()) == 155


def test_f2py_exports_every_expected_routine(f2py_blas):
    missing = sorted(routine for routine in ALL_ROUTINES if not callable(getattr(f2py_blas, routine, None)))
    assert missing == []


def test_documented_scripts_place_both_wrappers_under_one_build_root(prik_blas, f2py_blas):
    prik_root = Path(prik_blas.__file__).resolve().parent.parent
    f2py_root = Path(f2py_blas.__file__).resolve().parent.parent
    assert prik_root == f2py_root


def test_every_routine_has_one_visible_explicit_test():
    functions = _explicit_test_functions()
    expected_names = set(EXPLICIT_TEST_NAMES.values())
    missing = sorted(expected_names - functions.keys())
    assert missing == []

    for routine, test_name in EXPLICIT_TEST_NAMES.items():
        path, node = functions[test_name]
        segment = ast.get_source_segment(path.read_text(encoding="utf-8"), node)
        assert segment is not None
        assert routine in segment, f"{test_name} does not visibly exercise {routine}"
        assert "prik" in segment, f"{test_name} does not visibly invoke or validate PRIK"
        assert "f2py" in segment, f"{test_name} does not visibly invoke or document f2py"
        assert "pytest.skip" not in segment, f"{test_name} silently skips {routine}"
        decorator_names = {ast.unparse(decorator) for decorator in node.decorator_list}
        assert not any("skip" in decorator for decorator in decorator_names), f"{test_name} skips {routine}"


def test_every_routine_has_exactly_one_audited_outcome():
    outcomes = {
        "differential success": set(DIFFERENTIALLY_TESTED_ROUTINES),
        "unsupported": set(UNSUPPORTED_ROUTINES),
        "environmental skip": set(PERMANENTLY_SKIPPED_ROUTINES),
    }
    for routine in ALL_ROUTINES:
        states = [state for state, routines in outcomes.items() if routine in routines]
        assert len(states) == 1, f"{routine} has outcome states {states}"

    classified = set().union(*outcomes.values())
    assert classified == set(ALL_ROUTINES)
    assert set(ALL_ROUTINES) == PRIK_TESTED_ROUTINES
    assert UNSUPPORTED_ROUTINES == {}
    assert PERMANENTLY_SKIPPED_ROUTINES == {}


def test_documented_coverage_totals_match_inventory():
    readme = (EXAMPLE_ROOT / "README.md").read_text(encoding="utf-8")
    expected_rows = {
        "Native source files": len(BLAS_SOURCES),
        "Discovered callable routines": len(ALL_ROUTINES),
        "PRIK exports and independently validated routines": len(PRIK_TESTED_ROUTINES),
        "f2py exports": len(ALL_ROUTINES),
        "Full independent plus differential success": len(DIFFERENTIALLY_TESTED_ROUTINES),
        "f2py scalar-writeback intent overlays": len(F2PY_INOUT_ARGUMENTS),
        "Unsupported routines": len(UNSUPPORTED_ROUTINES),
        "Environmentally skipped routines": len(PERMANENTLY_SKIPPED_ROUTINES),
    }
    for label, count in expected_rows.items():
        assert f"| {label} | {count:,} |" in readme
