"""Positive ownership and navigation contracts for the pytest tree."""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]
TEST_ROOT = REPO_ROOT / "tests"
TEST_INDEX = TEST_ROOT / "README.md"
MIGRATION_CHECKLIST = REPO_ROOT / "docs/maintainer/roadmap/test-suite-organization-checklist.md"
QUALITY_WORKFLOW = REPO_ROOT / ".github/workflows/quality.yml"
FULL_REAL_LIBRARY_TEST = "tests/wrapper/fortran/real_libraries/test_real_blas_lapack.py"

STAGE_DIRECTORIES = {
    "architecture",
    "benchmarks",
    "cli",
    "docs",
    "naming",
    "parsing",
    "pipeline",
    "probes",
    "runtime",
    "semantics",
    "tools",
    "types",
    "utilities",
    "wrapper_codegen",
}
NON_STAGE_DIRECTORIES = {"wrapper"}
DOCUMENTED_SOURCE_OWNERS = {
    "x2py.parsers.c": "tests/parsing/c/",
    "x2py.parsers.fortran": "tests/parsing/fortran/",
    "x2py.parsers.pyi": "tests/parsing/pyi/",
    "x2py.probes": "tests/probes/",
    "x2py.pipeline": "tests/pipeline/",
    "x2py.wrapper_codegen": "tests/wrapper_codegen/",
    "x2py.naming": "tests/naming/",
    "x2py.utilities": "tests/utilities/",
    "x2py.types": "tests/types/",
    "x2py.runtime.handles": "tests/runtime/handles/",
    "x2py.cli": "tests/cli/",
}
TOOLS_TEST_MODULES = {
    "test_check_benchmark_regression.py",
    "test_check_radon_policy.py",
    "test_check_static_analysis_versions.py",
    "test_print_pytest_failures.py",
    "test_warm_real_library_native_cache.py",
}
DOCS_TEST_MODULES = {"test_examples.py", "test_publication.py", "test_structure.py"}
ARCHITECTURE_TEST_MODULES = {
    "test_dependency_boundaries.py",
    "test_package_structure.py",
    "test_test_suite_layout.py",
    "test_visitor_protocol.py",
}
DEPRECATED_PYTEST_ROOTS = {
    TEST_ROOT / "parser",
    TEST_ROOT / "property",
    TEST_ROOT / "pyi",
}
STALE_PYTEST_PATH_PATTERNS = (
    "tests/parser/test_",
    "tests/parser/c/test_",
    "tests/property/test_",
    "tests/pyi/test_",
    "tests/semantics/test_",
    "tests/test_naming_policy.py",
    "tests/test_runtime_handles.py",
    "tests/tools/test_documentation_",
    "tests/tools/test_numpy_types.py",
    "tests/tools/test_package_structure.py",
    "tests/tools/test_type_mapping_report.py",
)


def _pytest_modules() -> list[Path]:
    return sorted(TEST_ROOT.rglob("test_*.py"))


def _maintained_path_reference_files() -> list[Path]:
    candidates = [REPO_ROOT / "README.md", *REPO_ROOT.glob(".github/workflows/*"), *REPO_ROOT.rglob("*.md")]
    return sorted(
        path
        for path in candidates
        if path.is_file() and "old_docs" not in path.parts and path != MIGRATION_CHECKLIST and ".git" not in path.parts
    )


def test_pytest_modules_have_one_allowed_primary_owner() -> None:
    root_modules = sorted(path.name for path in TEST_ROOT.glob("test_*.py"))
    assert root_modules == []

    unexpected = []
    for path in _pytest_modules():
        relative = path.relative_to(TEST_ROOT)
        if relative.parts[0] not in STAGE_DIRECTORIES | NON_STAGE_DIRECTORIES:
            unexpected.append(relative.as_posix())
    assert unexpected == []


def test_deprecated_pytest_roots_cannot_regain_test_modules() -> None:
    unexpected = sorted(
        path.relative_to(TEST_ROOT).as_posix() for root in DEPRECATED_PYTEST_ROOTS for path in root.glob("test_*.py")
    )
    assert unexpected == []


def test_stage_modules_have_unique_basenames_for_default_pytest_import_mode() -> None:
    by_name: dict[str, list[str]] = {}
    for path in _pytest_modules():
        by_name.setdefault(path.name, []).append(path.relative_to(TEST_ROOT).as_posix())
    duplicates = {name: paths for name, paths in by_name.items() if len(paths) > 1}
    assert duplicates == {}


def test_major_source_packages_have_documented_existing_test_owners() -> None:
    text = TEST_INDEX.read_text(encoding="utf-8")
    for source_package, test_directory in DOCUMENTED_SOURCE_OWNERS.items():
        assert source_package in text
        assert test_directory in text
        assert (REPO_ROOT / test_directory).is_dir()


def test_specialized_test_lanes_contain_only_owned_modules() -> None:
    assert {path.name for path in (TEST_ROOT / "tools").glob("test_*.py")} == TOOLS_TEST_MODULES
    assert {path.name for path in (TEST_ROOT / "docs").glob("test_*.py")} == DOCS_TEST_MODULES
    assert {path.name for path in (TEST_ROOT / "architecture").glob("test_*.py")} == ARCHITECTURE_TEST_MODULES


def test_wrapper_runtime_modules_stay_in_the_fortran_feature_tree() -> None:
    wrapper_modules = sorted((TEST_ROOT / "wrapper").rglob("test_*.py"))
    assert wrapper_modules
    assert all(path.is_relative_to(TEST_ROOT / "wrapper" / "fortran") for path in wrapper_modules)


def test_test_index_links_and_stage_directories_exist() -> None:
    text = TEST_INDEX.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^]]+\]\(([^)#]+)", text):
        assert (TEST_INDEX.parent / target).resolve().exists(), target

    documented_stage_dirs = set(re.findall(r"`tests/([^/`]+)/[^`]*`", text))
    assert STAGE_DIRECTORIES - {"benchmarks"} <= documented_stage_dirs | {
        "architecture",
        "cli",
        "docs",
        "naming",
        "probes",
        "tools",
        "types",
    }


def test_maintained_docs_do_not_name_deprecated_pytest_locations() -> None:
    stale = []
    for path in _maintained_path_reference_files():
        text = path.read_text(encoding="utf-8")
        for pattern in STALE_PYTEST_PATH_PATTERNS:
            if pattern in text:
                stale.append(f"{path.relative_to(REPO_ROOT)}: {pattern}")
    assert stale == []


def test_full_real_library_nodes_have_one_dedicated_quality_job() -> None:
    text = QUALITY_WORKFLOW.read_text(encoding="utf-8")
    ordinary_jobs, dedicated_and_later = text.split("  real-library-wrappers:", maxsplit=1)
    dedicated_job, _later_jobs = dedicated_and_later.split("\n  coverage-report:", maxsplit=1)

    assert f"--ignore={FULL_REAL_LIBRARY_TEST}" in ordinary_jobs
    assert (
        f'"{FULL_REAL_LIBRARY_TEST}::test_full_library_wrapper_imports_every_root_procedure_from_cached_shared_library[blas]"'
        in dedicated_job
    )
    assert (
        f'"{FULL_REAL_LIBRARY_TEST}::test_full_library_wrapper_imports_every_root_procedure_from_cached_shared_library[lapack]"'
        in dedicated_job
    )
    assert "ignore-real-library-wrappers" in dedicated_job
    assert "matrix.library" not in dedicated_job
