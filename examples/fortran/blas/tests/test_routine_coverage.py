"""Fail closed when the reference source set, inventory, exports, or tests drift."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from prik.parsers.fortran.parser import parse_fortran_file

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
NATIVE_ROOT = EXAMPLE_ROOT / "native"
BLAS_PYF = EXAMPLE_ROOT / "blas.pyf"
FORTRAN_SUFFIXES = frozenset({".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"})
BLAS_SOURCES = tuple(
    sorted(path for path in NATIVE_ROOT.iterdir() if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES)
)
F2PY_INOUT_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "srotg": ("a", "b", "c", "s"),
    "drotg": ("a", "b", "c", "s"),
    "crotg": ("a", "c", "s"),
    "zrotg": ("a", "c", "s"),
    "srotmg": ("sd1", "sd2", "sx1", "sparam"),
    "drotmg": ("dd1", "dd2", "dx1", "dparam"),
}
PYF_PROCEDURE = re.compile(
    r"^\s*(subroutine|function)\s+([a-z]\w*)\s*\(.*?^\s*end\s+\1\s+\2\s*$",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)

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


def _pyf_procedures() -> dict[str, str]:
    text = BLAS_PYF.read_text(encoding="utf-8")
    return {match.group(2).lower(): match.group(0) for match in PYF_PROCEDURE.finditer(text)}


def _inout_arguments(block: str) -> set[str]:
    return {
        argument.strip().lower()
        for line in block.splitlines()
        if "intent(inout)" in line.lower() and "::" in line
        for argument in line.split("::", 1)[1].split(",")
    }


def test_committed_f2py_signature_matches_source_inventory():
    procedures = _pyf_procedures()
    assert len(procedures) == len(BLAS_SOURCES) == 155
    assert set(procedures) == set(_source_routines())


def test_committed_f2py_signature_records_scalar_writebacks():
    observed = {
        routine: arguments for routine, block in _pyf_procedures().items() if (arguments := _inout_arguments(block))
    }
    assert observed == {routine: set(arguments) for routine, arguments in F2PY_INOUT_ARGUMENTS.items()}


def test_f2py_script_compiles_the_signature_and_reuses_the_native_library():
    script = (EXAMPLE_ROOT / "build_f2py.sh").read_text(encoding="utf-8")
    assert 'python -m numpy.f2py -c \\\n  "$EXAMPLE_WORKSPACE/examples/fortran/blas/blas.pyf"' in script
    assert '"-L$(dirname "$BLAS_SHARED_LIBRARY")"' in script
    assert "-lprik_full_blas" in script
    assert "examples/fortran/blas/native" not in script


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


def _visible_wrapper_calls(node: ast.FunctionDef, routine: str) -> set[str]:
    return {
        call.func.value.id
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == routine
        and isinstance(call.func.value, ast.Name)
    }


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
        if routine in {"xerbla", "xerbla_array"}:
            assert segment.count(f"blas.{routine}(") == 2, f"{test_name} must invoke both subprocess wrappers"
            assert "prik_reference_blas" in segment
            assert "f2py_reference_blas" in segment
        else:
            visible = _visible_wrapper_calls(node, routine)
            assert visible == {"prik_blas", "f2py_blas"}, f"{test_name} exposes {routine} through {sorted(visible)}"
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


def test_documented_coverage_claims_match_inventory():
    readme = " ".join((EXAMPLE_ROOT / "README.md").read_text(encoding="utf-8").split())
    assert len(BLAS_SOURCES) == len(ALL_ROUTINES) == len(PRIK_TESTED_ROUTINES)
    assert len(ALL_ROUTINES) == len(DIFFERENTIALLY_TESTED_ROUTINES)
    assert f"All {len(ALL_ROUTINES):,} routines are exported and validated through both wrappers" in readme
    assert f"The {len(F2PY_INOUT_ARGUMENTS)} rotation routines" in readme
    assert f"contains the {len(BLAS_SOURCES):,} files" in readme
    assert UNSUPPORTED_ROUTINES == {}
    assert PERMANENTLY_SKIPPED_ROUTINES == {}
    assert "no unsupported or skipped routines" in readme
