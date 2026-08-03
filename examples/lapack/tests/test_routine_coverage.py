"""Fail-closed audit for the reviewed SciPy float64 LAPACK surface."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from ..routine_inventory import (
    EXPLICIT_TEST_NAMES,
    EXPECTED_LAPACK_PROCEDURES,
    EXPECTED_LAPACK_SOURCE_FILES,
    F2PY_EXPORT_LIMITATIONS,
    F2PY_FUNCTION_RESULTS,
    F2PY_SCALAR_WRITEBACK_ROUTINES,
    PRIK_ABI_ADAPTERS,
    ROUTINE_FAMILIES,
    ROUTINE_GROUPS,
    ROUTINE_SPECS,
    ROUTINES,
    SCIPY_VERSION,
)


TEST_ROOT = Path(__file__).resolve().parent
EXAMPLE_ROOT = TEST_ROOT.parent
NATIVE_ROOT = EXAMPLE_ROOT / "native"
LAPACK_PYF = EXAMPLE_ROOT / "lapack.pyf"
LAPACK_F2CMAP = EXAMPLE_ROOT / "lapack.f2cmap"
FORTRAN_SUFFIXES = {".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"}
F2PY_INOUT_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "dlarfg": ("alpha", "tau"),
    "dlartg": ("c", "s", "r"),
    "dgbcon": ("rcond", "info"),
    "dgecon": ("rcond", "info"),
    "dgtcon": ("rcond", "info"),
    "dpocon": ("rcond", "info"),
    "dppcon": ("rcond", "info"),
    "dsycon": ("rcond", "info"),
    "dtrcon": ("rcond", "info"),
}
PYF_PROCEDURE = re.compile(
    r"^\s*(subroutine|function)\s+([a-z]\w*)\s*\(.*?^\s*end\s+\1\s+\2\s*$",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def _pyf_procedures() -> dict[str, str]:
    text = LAPACK_PYF.read_text(encoding="utf-8")
    return {match.group(2).lower(): match.group(0) for match in PYF_PROCEDURE.finditer(text)}


def _inout_arguments(block: str) -> set[str]:
    return {
        argument.strip().lower()
        for line in block.splitlines()
        if "intent(inout)" in line.lower() and "::" in line
        for argument in line.split("::", 1)[1].split(",")
    }


def _explicit_test_owners() -> dict[str, list[tuple[str, Path]]]:
    owners: dict[str, list[tuple[str, Path]]] = {}
    for path in sorted(TEST_ROOT.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            matches = [routine for routine, test_name in EXPLICIT_TEST_NAMES.items() if node.name == test_name]
            assert len(matches) <= 1, f"{node.name} ambiguously owns {matches}"
            if matches:
                owners.setdefault(matches[0], []).append((node.name, path))
    return owners


def _visible_wrapper_calls(path: Path, test_name: str, routine: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    test_node = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == test_name
    )
    return {
        call.func.value.id
        for call in ast.walk(test_node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == routine
        and isinstance(call.func.value, ast.Name)
    }


def test_inventory_is_unique_and_matches_pinned_scipy_surface(scipy_lapack):
    """The reviewed inventory exactly matches SciPy's native d* surface."""
    observed = tuple(
        sorted(
            name
            for name in dir(scipy_lapack)
            if name.startswith("d") and callable(getattr(scipy_lapack, name)) and not name.endswith("_lwork")
        )
    )
    assert len(ROUTINES) == 127
    assert len(set(ROUTINES)) == len(ROUTINES)
    assert tuple(sorted(ROUTINES)) == observed, f"inventory drifted from SciPy {SCIPY_VERSION}"


def test_inventory_groups_form_one_complete_partition():
    """Every selected routine has exactly one LAPACK family owner."""
    grouped = tuple(name for names in ROUTINE_GROUPS.values() for name in names)
    assert grouped == ROUTINES
    assert len(set(grouped)) == len(grouped)
    assert set(ROUTINE_FAMILIES) == set(ROUTINES)
    assert set(ROUTINE_SPECS) == set(ROUTINES)
    assert set(F2PY_INOUT_ARGUMENTS) == F2PY_SCALAR_WRITEBACK_ROUTINES
    for routine, spec in ROUTINE_SPECS.items():
        assert spec.native_name == routine
        assert spec.family == ROUTINE_FAMILIES[routine]
        assert spec.test_name == EXPLICIT_TEST_NAMES[routine]
        assert all(
            (
                spec.source_file,
                spec.scipy_name,
                spec.prik_export,
                spec.prik_adapter,
                spec.f2py_export,
                spec.f2py_behavior,
                spec.mutation,
                spec.returns,
                spec.workspace,
                spec.index_convention,
                spec.oracle,
            )
        )
    assert set(ROUTINES) >= F2PY_FUNCTION_RESULTS
    assert set(F2PY_EXPORT_LIMITATIONS) <= set(ROUTINES)
    assert set(PRIK_ABI_ADAPTERS) <= set(ROUTINES)


def test_committed_f2py_signature_matches_selected_surface():
    """The reviewed signature exposes exactly the supported comparison surface."""
    procedures = _pyf_procedures()
    expected = set(ROUTINES) - set(F2PY_EXPORT_LIMITATIONS)
    assert len(procedures) == len(expected) == 125
    assert set(procedures) == expected
    assert re.search(r"^\s*module\s+la_constants\s*$", LAPACK_PYF.read_text(encoding="utf-8"), re.MULTILINE)
    assert LAPACK_F2CMAP.read_text(encoding="utf-8") == "{'real': {'wp': 'double'}}\n"


def test_committed_f2py_signature_records_scalar_writebacks():
    observed = {
        routine: arguments for routine, block in _pyf_procedures().items() if (arguments := _inout_arguments(block))
    }
    assert observed == {routine: set(arguments) for routine, arguments in F2PY_INOUT_ARGUMENTS.items()}


def test_f2py_script_compiles_the_signature_and_reuses_the_native_library():
    script = (EXAMPLE_ROOT / "build_f2py.sh").read_text(encoding="utf-8")
    assert 'python -m numpy.f2py -c \\\n  "$EXAMPLE_WORKSPACE/examples/lapack/lapack.pyf"' in script
    assert '"-L$(dirname "$LAPACK_SHARED_LIBRARY")"' in script
    assert "-lprik_full_lapack" in script
    assert '--f2cmap "$EXAMPLE_WORKSPACE/examples/lapack/lapack.f2cmap"' in script
    assert '--f90flags="-O0 -I$LAPACK_MODULE_DIR"' in script
    assert "examples/lapack/native" not in script


def test_documented_scripts_place_both_wrappers_under_one_build_root(prik_lapack, f2py_lapack):
    prik_root = Path(prik_lapack.__file__).resolve().parent.parent
    f2py_root = Path(f2py_lapack.__file__).resolve().parent.parent
    assert prik_root == f2py_root


def test_authoritative_native_source_boundary_is_complete_and_unique():
    """The maintained source owner contains the complete library corpus once."""
    sources = tuple(
        sorted(path for path in NATIVE_ROOT.iterdir() if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES)
    )
    stems = {path.stem.lower() for path in sources}
    assert len(sources) == EXPECTED_LAPACK_SOURCE_FILES
    assert EXPECTED_LAPACK_PROCEDURES == EXPECTED_LAPACK_SOURCE_FILES + 4
    assert set(ROUTINES) <= stems
    for routine, spec in ROUTINE_SPECS.items():
        assert (NATIVE_ROOT / spec.source_file).is_file(), routine
    assert {"la_constants", "la_xisnan"} <= stems


def test_selected_routines_have_one_explicit_named_test():
    """Static AST ownership prevents generated or silently missing tests."""
    owners = _explicit_test_owners()
    assert set(owners) == set(ROUTINES)
    duplicates = {routine: tests for routine, tests in owners.items() if len(tests) != 1}
    assert duplicates == {}


def test_selected_tests_keep_all_wrapper_calls_visible():
    """Named tests invoke every available surface without hiding calls."""
    owners = _explicit_test_owners()
    missing = {}
    for routine, [(test_name, path)] in owners.items():
        expected_surfaces = {"prik_lapack", "scipy_lapack"}
        if routine not in F2PY_EXPORT_LIMITATIONS:
            expected_surfaces.add("f2py_lapack")
        visible = _visible_wrapper_calls(path, test_name, routine)
        if visible != expected_surfaces:
            missing[routine] = sorted(expected_surfaces - visible)
    assert missing == {}


def test_documented_coverage_claims_match_inventory():
    """Published claims are derived from the reviewed inventory."""
    readme = " ".join((EXAMPLE_ROOT / "README.md").read_text(encoding="utf-8").split())
    assert len(EXPLICIT_TEST_NAMES) == len(ROUTINES)
    assert f"PRIK wraps all {EXPECTED_LAPACK_PROCEDURES:,} discovered procedures" in readme
    assert f"the {len(ROUTINES)} `float64` routines" in readme
    assert f"raw f2py supports {len(ROUTINES) - len(F2PY_EXPORT_LIMITATIONS)}" in readme
    assert f"All {len(EXPLICIT_TEST_NAMES)} selected routines have explicit correctness tests" in readme
    assert f"The {len(F2PY_INOUT_ARGUMENTS)} scalar-writeback routines" in readme
    assert f"owns {EXPECTED_LAPACK_SOURCE_FILES:,} LAPACK implementation sources" in readme
    assert "no unsupported or skipped routines" in readme


def test_selected_routines_are_exported_by_prik(prik_lapack):
    """The complete PRIK wrapper must export every selected routine."""
    missing = [name for name in ROUTINES if not hasattr(prik_lapack, name)]
    assert missing == []


def test_expected_f2py_routines_are_exported(f2py_lapack):
    """Only reproduced and documented f2py limitations may lack an export."""
    assert getattr(f2py_lapack, "la_constants", None) is not None
    expected = [name for name in ROUTINES if name not in F2PY_EXPORT_LIMITATIONS]
    missing = [name for name in expected if not hasattr(f2py_lapack, name)]
    assert missing == []
    unexpected = [name for name in F2PY_EXPORT_LIMITATIONS if hasattr(f2py_lapack, name)]
    assert unexpected == []
