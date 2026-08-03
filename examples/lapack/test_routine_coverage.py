"""Fail-closed audit for the reviewed SciPy float64 LAPACK surface."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from .conftest import (
    F2PY_BUILD_DEPENDENCIES,
    F2PY_KIND_MAP,
    F2PY_LINK_DEPENDENCIES,
    PRIK_WRAPPER_FLAGS,
    _f2py_build_command,
    _f2py_source_plan,
    _prik_build_command,
)
from .f2py_contract import F2PY_INOUT_ARGUMENTS
from .routine_inventory import (
    EXPLICIT_TEST_NAMES,
    EXPECTED_LAPACK_ROOT_PROCEDURES,
    EXPECTED_LAPACK_SOURCE_FILES,
    F2PY_EXPORT_LIMITATIONS,
    F2PY_FUNCTION_RESULTS,
    PRIK_ABI_ADAPTERS,
    ROUTINE_FAMILIES,
    ROUTINE_GROUPS,
    ROUTINE_SPECS,
    ROUTINES,
    SCIPY_VERSION,
)


EXAMPLE_ROOT = Path(__file__).resolve().parent
NATIVE_ROOT = EXAMPLE_ROOT / "native"
OLD_NATIVE_ROOT = (
    EXAMPLE_ROOT.parents[1]
    / "tests"
    / "fortran"
    / "building_shared_library"
    / "end_to_end"
    / "real_libraries"
    / "lapack"
    / "native"
)
FORTRAN_SUFFIXES = {".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77", ".ftn"}
pytestmark = [pytest.mark.fortran_end_to_end, pytest.mark.real_library]


def _explicit_test_owners() -> dict[str, list[tuple[str, Path]]]:
    owners: dict[str, list[tuple[str, Path]]] = {}
    for path in sorted(EXAMPLE_ROOT.glob("test_*.py")):
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


def test_f2py_source_plan_includes_required_kind_module(tmp_path: Path):
    """The selected build closes dependencies without consuming PRIK's library."""
    plan = _f2py_source_plan(tmp_path)
    dependency_count = len(F2PY_BUILD_DEPENDENCIES)
    assert tuple(path.name for path in plan[:dependency_count]) == F2PY_BUILD_DEPENDENCIES
    assert {path.stem for path in plan[dependency_count:]} == set(ROUTINES) - set(F2PY_EXPORT_LIMITATIONS)
    assert len(plan) == dependency_count + len(ROUTINES) - len(F2PY_EXPORT_LIMITATIONS)
    assert F2PY_KIND_MAP == "{'real': {'wp': 'double'}}\n"

    for routine, arguments in F2PY_INOUT_ARGUMENTS.items():
        source = next(path for path in plan if path.stem == routine)
        prefix = "Cf2py" if source.suffix == ".f" else "!f2py"
        assert source.parent == tmp_path / "f2py-intent-sources"
        assert f"{prefix} intent(inout) {', '.join(arguments)}" in source.read_text(encoding="utf-8")

    command = _f2py_build_command(tmp_path)
    dependency_values = tuple(command[index + 1] for index, value in enumerate(command) if value == "--dep")
    assert dependency_values == F2PY_LINK_DEPENDENCIES
    assert "only:" in command
    assert ":" in command
    assert not any("libprik_full_lapack" in value for value in command)
    assert (tmp_path / ".f2py_f2cmap").read_text(encoding="utf-8") == F2PY_KIND_MAP


def test_prik_build_command_uses_the_public_cli(tmp_path: Path):
    """The documented LAPACK wrapper build is a real PRIK CLI invocation."""
    runtime_entry = tmp_path / "runtime" / "__init__.pyi"
    native_library = tmp_path / "libprik_full_lapack.so"
    command = _prik_build_command(runtime_entry, native_library, tmp_path, "/usr/bin/gfortran")

    assert command[:4] == (sys.executable, "-m", "prik", str(runtime_entry))
    assert command[command.index("--native-objects") + 1] == str(native_library)
    assert "--native-shared-library" not in command
    joined_flags = " ".join(PRIK_WRAPPER_FLAGS)
    assert f"--wrapper-fortran-flags={joined_flags}" in command
    assert f"--wrapper-c-flags={joined_flags}" in command


def test_authoritative_native_source_boundary_is_complete_and_unique():
    """The maintained source owner contains the complete library corpus once."""
    sources = tuple(
        sorted(path for path in NATIVE_ROOT.iterdir() if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES)
    )
    stems = {path.stem.lower() for path in sources}
    assert len(sources) == EXPECTED_LAPACK_SOURCE_FILES
    assert EXPECTED_LAPACK_ROOT_PROCEDURES == EXPECTED_LAPACK_SOURCE_FILES - 2 + 4
    assert set(ROUTINES) <= stems
    for routine, spec in ROUTINE_SPECS.items():
        assert (NATIVE_ROOT / spec.source_file).is_file(), routine
    assert {"la_constants", "la_xisnan"} <= stems
    assert not OLD_NATIVE_ROOT.exists()


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


def test_documented_coverage_totals_match_inventory():
    """Published totals are derived from the reviewed inventory, not hand-waved."""
    readme = (EXAMPLE_ROOT / "README.md").read_text(encoding="utf-8")
    expected_rows = {
        "Authoritative LAPACK implementation sources": EXPECTED_LAPACK_SOURCE_FILES,
        "Discovered root LAPACK procedures": EXPECTED_LAPACK_ROOT_PROCEDURES,
        "Selected SciPy-backed float64 routines": len(ROUTINES),
        "Explicit correctness tests": len(EXPLICIT_TEST_NAMES),
        "PRIK root exports required in CI": EXPECTED_LAPACK_ROOT_PROCEDURES,
        "Selected PRIK routines independently validated": len(ROUTINES),
        "SciPy exports used": len(ROUTINES),
        "f2py exports required in CI": len(ROUTINES) - len(F2PY_EXPORT_LIMITATIONS),
        "Routines satisfying the independent oracle through f2py": len(ROUTINES) - len(F2PY_EXPORT_LIMITATIONS),
        "Documented f2py source-parser export limitations": len(F2PY_EXPORT_LIMITATIONS),
        "f2py scalar-writeback intent overlays": len(F2PY_INOUT_ARGUMENTS),
        "Documented PRIK default-LOGICAL ABI adapters": len(PRIK_ABI_ADAPTERS),
        "Documented unsupported/skipped routines": 0,
    }
    for label, count in expected_rows.items():
        assert f"| {label} | {count:,} |" in readme


def test_selected_routines_are_exported_by_prik(prik_lapack):
    """The complete PRIK wrapper must export every selected routine."""
    missing = [name for name in ROUTINES if not hasattr(prik_lapack, name)]
    assert missing == []


def test_expected_f2py_routines_are_exported(f2py_lapack):
    """Only reproduced and documented f2py limitations may lack an export."""
    expected = [name for name in ROUTINES if name not in F2PY_EXPORT_LIMITATIONS]
    missing = [name for name in expected if not hasattr(f2py_lapack, name)]
    assert missing == []
    unexpected = [name for name in F2PY_EXPORT_LIMITATIONS if hasattr(f2py_lapack, name)]
    assert unexpected == []
