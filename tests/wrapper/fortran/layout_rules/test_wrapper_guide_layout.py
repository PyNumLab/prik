"""Structural checks for the wrapper guide and subject-oriented test layout."""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys

from tests.wrapper.fortran._support import REPO_ROOT, WRAPPER_FORTRAN_DATA, WRAPPER_TEST_ROOT

WRAPPER_ROOT = WRAPPER_TEST_ROOT
WRAPPER_SUITE_ROOT = WRAPPER_ROOT.parent
DOCS_ROOT = REPO_ROOT / "docs"
CHECKLIST_COVERAGE = WRAPPER_SUITE_ROOT / "CHECKLIST_COVERAGE.md"
WRAPPER_PLAN_MIGRATION_CHECKLIST = DOCS_ROOT / "maintainer" / "roadmap" / "wrapper-plan-migration-checklist.md"
FORTRAN_SUFFIXES = {".f", ".f90", ".f95", ".for"}
ROOT_FILES = {
    "README.md",
    "_generated_contracts.py",
    "_support.py",
    "conftest.py",
    "fmath_cases.py",
    "valgrind.supp",
}
CONTRACT_FIXTURE_ROOTS = {"contracts", "modified_contracts", "handwritten_contracts", "invalid_contracts"}
CONTRACT_VARIANT_DIRS = {"generated", "modified", "handwritten", "invalid"}
SUBJECT_TEST_MODULES = {
    "build_from_source": (
        "test_build_modes.py",
        "test_compiler_verbose.py",
        "test_source_generated_pyi_contracts.py",
        "test_runtime_abi.py",
    ),
    "build_from_pyi": (
        "test_contract_package_runtime.py",
        "test_pyi_wrapper_builds.py",
    ),
    "multiple_files": ("test_multi_source_builds.py",),
    "external_routines": ("test_external_procedures.py",),
    "real_libraries": ("test_real_blas_lapack.py", "test_stage7_native_bundles.py"),
    "edit_pyi_contracts": (
        "test_native_order_contracts.py",
        "test_ownership_contracts.py",
        "test_policy_dispatch_contracts.py",
        "test_surface_edit_contracts.py",
        "test_visibility_contracts.py",
    ),
    "arrays": (
        "test_array_contracts.py",
        "test_array_results.py",
        "test_assumed_rank_arrays.py",
        "test_array_generated_pyi_contracts.py",
        "test_multidimensional_arrays.py",
    ),
    "scalars": (
        "test_fortran_enums.py",
        "test_scalar_boundary_plan.py",
        "test_scalar_generated_pyi_contracts.py",
        "test_scalar_kinds.py",
        "test_value_and_bind_c.py",
        "test_verified_baseline.py",
    ),
    "function_calls": (
        "test_function_call_generated_pyi_contracts.py",
        "test_native_call_examples.py",
        "test_optional_arguments.py",
        "test_output_arguments.py",
        "test_scalar_writeback_plan.py",
    ),
    "strings": (
        "test_character_arguments.py",
        "test_character_edge_cases.py",
        "test_string_generated_pyi_contracts.py",
    ),
    "derived_types": (
        "test_borrowed_finalizers.py",
        "test_constructors_and_finalizers.py",
        "test_derived_layout.py",
        "test_derived_type_boundaries.py",
        "test_derived_type_generated_pyi_contracts.py",
        "test_derived_type_methods.py",
        "test_phase8_derived_plan.py",
        "test_phase9_bound_constructors.py",
        "test_scalar_derived_actual_dummy_matrix.py",
        "test_inheritance.py",
        "test_pointers.py",
    ),
    "callbacks": (
        "test_all_callback_shapes.py",
        "test_array_callbacks.py",
        "test_callback_generated_pyi_contracts.py",
        "test_derived_callbacks.py",
        "test_scalar_callbacks.py",
    ),
    "module_state": (
        "test_allocatable_replacement.py",
        "test_allocatable_views.py",
        "test_common_blocks.py",
        "test_module_state_generated_pyi_contracts.py",
        "test_module_state.py",
        "test_scalar_module_variable_plan.py",
    ),
    "runtime_behavior": (
        "test_openmp_runtime.py",
        "test_runtime_behavior_generated_pyi_contracts.py",
        "test_runtime_policies.py",
        "test_runtime_recursion.py",
    ),
    "naming": (
        "test_defined_operators.py",
        "test_generic_interfaces.py",
        "test_naming_generated_pyi_contracts.py",
        "test_phase9_class_overloads.py",
        "test_visibility_naming.py",
    ),
    "layout_rules": ("test_wrapper_guide_layout.py",),
}
ALLOWED_SUBJECTS = tuple(SUBJECT_TEST_MODULES)
SUBJECT_TEST_PATHS = tuple(
    f"{subject}/{filename}" for subject, filenames in SUBJECT_TEST_MODULES.items() for filename in filenames
)
MIGRATION_MATRIX_STATUS_VALUES = {
    "not-applicable",
    "deferred-real-library",
    "legacy",
    "dual-route",
    "wrapper-plan",
}
MIGRATION_MATRIX_ROW_RE = re.compile(
    r"^\| `(?P<selector>tests/wrapper/[^`]+)` \| (?P<unit>[^|]+) "
    r"\| (?P<lanes>[^|]+) \| `(?P<status>[^`]+)` \|$"
)
MIGRATION_SUMMARY_ROW_RE = re.compile(r"^\| `(?P<status>[^`]+)` \| (?P<count>[0-9]+) \|$")


def _is_meaningful(path: Path) -> bool:
    return "__pycache__" not in path.parts and path.suffix != ".pyc"


def _meaningful_files(path: Path) -> list[Path]:
    return [child for child in path.rglob("*") if child.is_file() and _is_meaningful(child)]


def _wrapper_fixture_paths() -> list[Path]:
    return sorted(
        path for path in WRAPPER_FORTRAN_DATA.glob("*") if path.is_file() and path.suffix.lower() in FORTRAN_SUFFIXES
    )


def _subject_test_text() -> str:
    return "\n".join((WRAPPER_ROOT / relative_path).read_text(encoding="utf-8") for relative_path in SUBJECT_TEST_PATHS)


def _docs_and_test_text_paths() -> list[Path]:
    roots = (DOCS_ROOT, WRAPPER_SUITE_ROOT, REPO_ROOT / "README.md")
    return sorted(
        path
        for root in roots
        for path in ([root] if root.is_file() else root.rglob("*"))
        if path.is_file()
        and path.suffix in {".md", ".py"}
        and path != Path(__file__)
        and "docs/old_docs" not in path.as_posix()
    )


def _collected_wrapper_test_nodes() -> list[str]:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "tests/wrapper",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(line for line in result.stdout.splitlines() if line.startswith("tests/wrapper/") and "::" in line)


def _wrapper_plan_migration_matrix_rows() -> dict[str, dict[str, str]]:
    rows = {}
    for line in WRAPPER_PLAN_MIGRATION_CHECKLIST.read_text(encoding="utf-8").splitlines():
        match = MIGRATION_MATRIX_ROW_RE.match(line)
        if match is None:
            continue
        selector = match.group("selector")
        rows[selector] = {
            "unit": match.group("unit").strip(),
            "lanes": match.group("lanes").strip(),
            "status": match.group("status"),
        }
    return rows


def _wrapper_plan_migration_summary_counts() -> dict[str, int]:
    counts = {}
    for line in WRAPPER_PLAN_MIGRATION_CHECKLIST.read_text(encoding="utf-8").splitlines():
        match = MIGRATION_SUMMARY_ROW_RE.match(line)
        if match is None or match.group("status") not in MIGRATION_MATRIX_STATUS_VALUES:
            continue
        status = match.group("status")
        assert status not in counts, f"duplicate migration summary row: {status}"
        counts[status] = int(match.group("count"))
    return counts


def _migration_selector_matches(selector: str, nodeid: str) -> bool:
    if selector.endswith("::*"):
        return nodeid.startswith(f"{selector[:-3]}::")
    if selector.endswith("[*]"):
        return nodeid.startswith(f"{selector[:-3]}[")
    return nodeid == selector


def test_fortran_wrapper_tree_uses_only_allowed_subjects():
    missing_subjects = [subject for subject in ALLOWED_SUBJECTS if not (WRAPPER_ROOT / subject).is_dir()]
    assert missing_subjects == []

    unexpected_root_files = sorted(
        path.name
        for path in WRAPPER_ROOT.iterdir()
        if path.is_file() and _is_meaningful(path) and path.name not in ROOT_FILES
    )
    assert unexpected_root_files == []

    unexpected_directories = sorted(
        path.name
        for path in WRAPPER_ROOT.iterdir()
        if path.is_dir()
        and path.name not in ALLOWED_SUBJECTS
        and path.name != "__pycache__"
        and _meaningful_files(path)
    )
    assert unexpected_directories == []


def test_subject_test_modules_match_the_layout_contract():
    expected = set(SUBJECT_TEST_PATHS)
    actual = {
        path.relative_to(WRAPPER_ROOT).as_posix() for path in WRAPPER_ROOT.rglob("test_*.py") if _is_meaningful(path)
    }

    assert actual == expected
    assert not list(WRAPPER_ROOT.glob("test_*.py"))
    assert not any(WRAPPER_ROOT.glob("section_*"))


def test_native_wrapper_sources_live_only_in_the_shared_corpus():
    nested_fixture_dirs = sorted(
        path.relative_to(WRAPPER_FORTRAN_DATA).as_posix() for path in WRAPPER_FORTRAN_DATA.rglob("*") if path.is_dir()
    )
    assert nested_fixture_dirs == []

    in_wrapper_tree = sorted(
        path.relative_to(WRAPPER_ROOT).as_posix()
        for path in WRAPPER_ROOT.rglob("*")
        if path.is_file() and _is_meaningful(path) and path.suffix.lower() in FORTRAN_SUFFIXES
    )
    assert in_wrapper_tree == []

    fixture_paths = _wrapper_fixture_paths()
    assert len(fixture_paths) >= 40

    fixture_name_counts = Counter(path.name for path in fixture_paths)
    duplicate_names = sorted(name for name, count in fixture_name_counts.items() if count > 1)
    assert duplicate_names == []

    test_text = _subject_test_text()
    unreferenced = sorted(path.name for path in fixture_paths if path.name not in test_text)
    assert unreferenced == []


def test_runtime_contract_fixtures_stay_under_consuming_subjects():
    generated_variant_dirs = sorted(
        path.relative_to(WRAPPER_ROOT).as_posix()
        for path in WRAPPER_ROOT.glob("*/contracts/**/generated")
        if path.is_dir()
    )
    assert generated_variant_dirs == []

    contract_files = sorted(
        path.relative_to(WRAPPER_ROOT).as_posix()
        for root_name in CONTRACT_FIXTURE_ROOTS
        for path in WRAPPER_ROOT.glob(f"*/{root_name}/**/*")
        if path.is_file() and _is_meaningful(path)
    )
    assert contract_files
    assert all(path.endswith(".pyi") for path in contract_files)

    bad_locations = []
    for relative_path in contract_files:
        parts = relative_path.split("/")
        if len(parts) < 3 or parts[0] not in ALLOWED_SUBJECTS or parts[1] not in CONTRACT_FIXTURE_ROOTS:
            bad_locations.append(relative_path)
            continue
        if parts[1] == "contracts" and any(part in CONTRACT_VARIANT_DIRS for part in parts[2:-1]):
            bad_locations.append(relative_path)
    assert bad_locations == []

    undocumented_modified = [
        relative_path
        for relative_path in contract_files
        if "/modified_contracts/" in relative_path
        and not (WRAPPER_ROOT / relative_path).read_text(encoding="utf-8").startswith("# Intentional difference:")
    ]
    assert undocumented_modified == []


def test_subject_readmes_and_checklist_coverage_index_the_layout():
    for subject, test_modules in SUBJECT_TEST_MODULES.items():
        readme = WRAPPER_ROOT / subject / "README.md"
        assert readme.is_file(), subject
        text = readme.read_text(encoding="utf-8")
        for required in ("Focused pytest command:", "Native data path:", "Contract fixtures:", "Roadmap items:"):
            assert required in text, f"{subject} README missing {required}"
        for test_module in test_modules:
            assert test_module in text, f"{subject} README missing {test_module}"

    coverage_text = CHECKLIST_COVERAGE.read_text(encoding="utf-8")
    missing_subjects = [f"fortran/{subject}/README.md" for subject in ALLOWED_SUBJECTS if subject not in coverage_text]
    missing_tests = [test_path for test_path in SUBJECT_TEST_PATHS if test_path not in coverage_text]
    assert missing_subjects == []
    assert missing_tests == []


def test_wrapper_checklist_python_evidence_references_existing_test_nodes():
    coverage_text = CHECKLIST_COVERAGE.read_text(encoding="utf-8")
    references = set(re.findall(r"`([^`]+\.py(?:::[A-Za-z0-9_]+)?)`", coverage_text))
    assert references

    missing = []
    for reference in sorted(references):
        path_text, _, node_name = reference.partition("::")
        if path_text.startswith("tests/"):
            path = REPO_ROOT / path_text
        elif path_text.split("/", 1)[0] in ALLOWED_SUBJECTS:
            path = WRAPPER_ROOT / path_text
        else:
            continue
        if not path.is_file():
            missing.append(reference)
            continue
        if node_name:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            function_names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
            if node_name not in function_names:
                missing.append(reference)
    assert missing == []


def test_wrapper_plan_migration_matrix_tracks_collected_wrapper_nodes():
    matrix_rows = _wrapper_plan_migration_matrix_rows()
    assert matrix_rows

    invalid_status_rows = sorted(
        selector for selector, row in matrix_rows.items() if row["status"] not in MIGRATION_MATRIX_STATUS_VALUES
    )
    assert invalid_status_rows == []

    incomplete_rows = sorted(selector for selector, row in matrix_rows.items() if not row["unit"] or not row["lanes"])
    assert incomplete_rows == []

    collected_nodes = _collected_wrapper_test_nodes()
    assert collected_nodes

    unmatched_nodes = []
    multiply_matched_nodes = []
    statuses_by_node = {}
    for nodeid in collected_nodes:
        matches = [selector for selector in matrix_rows if _migration_selector_matches(selector, nodeid)]
        if not matches:
            unmatched_nodes.append(nodeid)
        elif len(matches) > 1:
            multiply_matched_nodes.append((nodeid, matches))
        else:
            statuses_by_node[nodeid] = matrix_rows[matches[0]]["status"]

    stale_selectors = sorted(
        selector
        for selector in matrix_rows
        if not any(_migration_selector_matches(selector, nodeid) for nodeid in collected_nodes)
    )

    assert unmatched_nodes == []
    assert multiply_matched_nodes == []
    assert stale_selectors == []

    collected_status_counts = Counter(statuses_by_node.values())
    expected_summary = {status: collected_status_counts.get(status, 0) for status in MIGRATION_MATRIX_STATUS_VALUES}
    assert _wrapper_plan_migration_summary_counts() == expected_summary


def test_wrapper_language_suite_and_reference_link_current_subject_paths():
    root_test_modules = sorted(path.name for path in WRAPPER_SUITE_ROOT.glob("test_*.py"))
    assert root_test_modules == []
    assert (WRAPPER_SUITE_ROOT / "README.md").is_file()
    assert "fortran/README.md" in (WRAPPER_SUITE_ROOT / "README.md").read_text(encoding="utf-8")

    reference = (DOCS_ROOT / "user/reference/fortran-wrapper.md").read_text(encoding="utf-8")
    runtime_paths = [test_path for test_path in SUBJECT_TEST_PATHS if not test_path.startswith("layout_rules/")]
    missing = [test_path for test_path in runtime_paths if test_path not in reference]
    assert missing == []
    assert "- [x]" not in reference
    assert "- [ ]" not in reference


def test_stale_wrapper_paths_are_rejected_after_stage_one_moves():
    fixture_names = [path.name for path in _wrapper_fixture_paths()]
    stale_fragments = [
        "tests/wrapper/fortran/" + "test_",
        "tests/wrapper/fortran/" + "multi_source" + "_builds",
        "tests/wrapper/fortran/" + "pyi/",
        "tests/wrapper/fortran/pyi_contracts/",
        "tests/wrapper/fortran/native_build/",
        "tests/wrapper/fortran/multi_source/",
        "tests/wrapper/fortran/standalone/",
        "tests/wrapper/fortran/feature_parity/",
        "tests/wrapper/fortran/editable_contracts/",
        "tests/wrapper/fortran/parity_policy/",
        "tests/wrapper/fortran/library_scale/",
        "tests/data/fortran/wrapper/feature_parity/",
        "tests/data/fortran/wrapper/library_scale/",
        "tests/data/fortran/wrapper/multi_source/",
        "tests/data/fortran/wrapper/native_build/",
        "tests/data/fortran/wrapper/standalone/",
        *(f"tests/wrapper/fortran/{fixture_name}" for fixture_name in fixture_names),
    ]
    offenders = []
    for path in _docs_and_test_text_paths():
        text = path.read_text(encoding="utf-8")
        for fragment in stale_fragments:
            if fragment in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {fragment}")
    assert offenders == []


def test_obsolete_policy_files_and_monolithic_wrapper_test_are_removed():
    obsolete_docs = (
        "fortran_wrapper_checklist.md",
        "fortran_wrapper_ownership_policy.md",
        "fortran_wrapper_naming_policy.md",
    )

    assert not any((DOCS_ROOT / filename).exists() for filename in obsolete_docs)
    assert not (WRAPPER_ROOT / "test_wrapper.py").exists()
    assert not any(WRAPPER_ROOT.glob("section_*"))
