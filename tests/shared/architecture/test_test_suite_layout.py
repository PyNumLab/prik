"""Positive ownership and navigation contracts for the pytest tree."""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).parents[3]
TEST_ROOT = REPO_ROOT / "tests"
TEST_INDEX = TEST_ROOT / "README.md"
BLAS_LAPACK_WORKFLOW = REPO_ROOT / ".github/workflows/blas-lapack.yml"
CLAUDE_WORKFLOW = REPO_ROOT / ".github/workflows/claude.yml"
COVERAGE_WORKFLOW = REPO_ROOT / ".github/workflows/coverage.yml"
CODECOV_CONFIG = REPO_ROOT / "codecov.yml"
DOCS_WORKFLOW = REPO_ROOT / ".github/workflows/docs.yml"
PARSER_REFERENCE_WORKFLOW = REPO_ROOT / ".github/workflows/parser-reference-guard.yml"
PUBLISH_WORKFLOW = REPO_ROOT / ".github/workflows/publish-to-pypi.yml"
STATIC_ANALYSIS_WORKFLOW = REPO_ROOT / ".github/workflows/static-analysis.yml"
TESTS_WORKFLOW = REPO_ROOT / ".github/workflows/tests.yml"
PYPROJECT = REPO_ROOT / "pyproject.toml"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
MANIFEST = REPO_ROOT / "MANIFEST.in"
FULL_REAL_LIBRARY_TEST = "tests/fortran/building_shared_library/end_to_end/real_libraries/test_full_libraries.py"

LEGACY_TEST_ROOTS = {
    "benchmarks",
    "cli",
    "data",
    "docs",
    "naming",
    "parser",
    "parsing",
    "pipeline",
    "probes",
    "pyi",
    "runtime",
    "semantics",
    "tools",
    "types",
    "utilities",
    "wrapper",
    "wrapper_codegen",
}
LANGUAGE_DIRECTORIES = {"c", "fortran", "shared"}
PRIMARY_OWNER_DIRECTORIES = {"architecture", *LANGUAGE_DIRECTORIES}
ARCHITECTURE_OWNER_DIRECTORIES = {"c", "fortran"}
FORTRAN_OWNER_DIRECTORIES = {
    "allocatables",
    "arrays",
    "building_shared_library",
    "callbacks",
    "command_line_interface",
    "data_types",
    "derived_types",
    "enumerations",
    "error_handling",
    "functions",
    "generic_interfaces",
    "infrastructure",
    "memory_management",
    "modules",
    "optional_arguments",
    "pointers",
    "pyi_contracts",
    "raw_addresses",
    "semantic_pyi_format",
    "semantic_ir",
    "source_parsing",
    "source_preprocessing",
    "strings",
    "subroutines",
}
SHARED_OWNER_DIRECTORIES = {"architecture", "docs", "naming", "tools", "types", "utilities"}
TOOLS_TEST_MODULES = {
    "test_benchmark_host.py",
    "test_build_time_benchmark.py",
    "test_check_benchmark_regression.py",
    "test_check_radon_policy.py",
    "test_check_static_analysis_versions.py",
    "test_generate_performance_docs.py",
    "test_print_pytest_failures.py",
    "test_runtime_benchmark.py",
    "test_run_fortran_toolchain_lane.py",
    "test_warm_real_library_native_cache.py",
}
DOCS_TEST_MODULES = {"test_examples.py", "test_publication.py", "test_structure.py"}
ARCHITECTURE_TEST_MODULES = {
    "test_dependency_boundaries.py",
    "test_package_structure.py",
    "test_test_suite_layout.py",
    "test_visitor_protocol.py",
}
STALE_PYTEST_PATH_PATTERNS = (
    *(re.compile(rf"\btests/{re.escape(root)}(?=/|\b)") for root in sorted(LEGACY_TEST_ROOTS)),
    re.compile(r"\btests/_shared(?=/|\b)"),
)


def _pytest_modules() -> list[Path]:
    return sorted(TEST_ROOT.rglob("test_*.py"))


def _maintained_path_reference_files() -> list[Path]:
    candidates = [REPO_ROOT / "README.md", *REPO_ROOT.glob(".github/workflows/*"), *REPO_ROOT.rglob("*.md")]
    return sorted(
        path
        for path in candidates
        if path.is_file()
        and path.name != "AGENTS.md"
        and "old_docs" not in path.parts
        and "_migration" not in path.parts
        and "docs/maintainer/roadmap" not in path.as_posix()
        and ".git" not in path.parts
    )


def test_pytest_modules_have_one_allowed_primary_owner() -> None:
    root_modules = sorted(path.name for path in TEST_ROOT.glob("test_*.py"))
    assert root_modules == []

    assert {
        path.name for path in TEST_ROOT.iterdir() if path.is_dir() and path.name != "__pycache__"
    } == PRIMARY_OWNER_DIRECTORIES
    assert all(path.relative_to(TEST_ROOT).parts[0] in PRIMARY_OWNER_DIRECTORIES for path in _pytest_modules())


def test_primary_roots_use_only_documented_owner_directories() -> None:
    for root, expected in (
        (TEST_ROOT / "architecture", ARCHITECTURE_OWNER_DIRECTORIES),
        (TEST_ROOT / "fortran", FORTRAN_OWNER_DIRECTORIES),
        (TEST_ROOT / "shared", SHARED_OWNER_DIRECTORIES),
    ):
        actual = {
            path.name for path in root.iterdir() if path.is_dir() and path.name not in {"__pycache__", "_support"}
        }
        assert actual == expected


def test_stage_modules_have_unique_basenames_for_default_pytest_import_mode() -> None:
    by_name: dict[str, list[str]] = {}
    for path in _pytest_modules():
        by_name.setdefault(path.name, []).append(path.relative_to(TEST_ROOT).as_posix())
    duplicates = {name: paths for name, paths in by_name.items() if len(paths) > 1}
    assert duplicates == {}


def test_language_first_roots_have_documented_existing_owners() -> None:
    text = TEST_INDEX.read_text(encoding="utf-8")
    for language in LANGUAGE_DIRECTORIES:
        test_directory = f"tests/{language}/"
        assert test_directory in text
        assert (REPO_ROOT / test_directory).is_dir()


def test_specialized_test_lanes_contain_only_owned_modules() -> None:
    assert {path.name for path in (TEST_ROOT / "shared" / "tools").glob("test_*.py")} == TOOLS_TEST_MODULES
    assert {path.name for path in (TEST_ROOT / "shared" / "docs").glob("test_*.py")} == DOCS_TEST_MODULES
    assert {
        path.name for path in (TEST_ROOT / "shared" / "architecture").glob("test_*.py")
    } == ARCHITECTURE_TEST_MODULES


def test_fortran_support_directory_contains_no_pytest_modules() -> None:
    assert sorted((TEST_ROOT / "fortran" / "_support").rglob("test_*.py")) == []


def test_test_index_links_and_language_directories_exist() -> None:
    text = TEST_INDEX.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^]]+\]\(([^)#]+)", text):
        assert (TEST_INDEX.parent / target).resolve().exists(), target

    assert all((TEST_ROOT / language).is_dir() for language in LANGUAGE_DIRECTORIES)


def test_maintained_docs_do_not_name_deprecated_pytest_locations() -> None:
    stale = []
    for path in _maintained_path_reference_files():
        text = path.read_text(encoding="utf-8")
        for pattern in STALE_PYTEST_PATH_PATTERNS:
            if pattern.search(text):
                stale.append(f"{path.relative_to(REPO_ROOT)}: {pattern.pattern}")
    assert stale == []


def test_full_real_library_nodes_have_one_dedicated_workflow() -> None:
    ordinary_jobs = TESTS_WORKFLOW.read_text(encoding="utf-8")
    dedicated_job = BLAS_LAPACK_WORKFLOW.read_text(encoding="utf-8")

    assert '-m "not real_library and not toolchain_smoke"' in ordinary_jobs
    assert ordinary_jobs.count('-m "not real_library and not toolchain_smoke"') == 2
    assert FULL_REAL_LIBRARY_TEST not in ordinary_jobs
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


def test_coverage_workflow_reuses_the_canonical_test_selections() -> None:
    ordinary = TESTS_WORKFLOW.read_text(encoding="utf-8")
    coverage = COVERAGE_WORKFLOW.read_text(encoding="utf-8")

    for snippet in (
        "tests/architecture",
        "tests/c",
        "tests/fortran",
        "tests/shared",
        "-m toolchain_smoke",
        '-m "not real_library and not toolchain_smoke"',
        "--require-toolchain-smoke",
        "--prik-fortran-compiler=gfortran",
    ):
        assert snippet in ordinary
        assert snippet in coverage
    assert coverage.count("python -m coverage run -m pytest") == 2
    assert "python -m coverage combine" in coverage
    assert "python -m coverage report" in coverage


def test_codecov_keeps_project_coverage_blocking_and_patch_coverage_informational() -> None:
    assert CODECOV_CONFIG.read_text(encoding="utf-8") == (
        "coverage:\n"
        "  status:\n"
        "    project:\n"
        "      default:\n"
        "        target: 90%\n"
        "    patch:\n"
        "      default:\n"
        "        target: 90%\n"
        "        informational: true\n"
    )


def test_active_github_action_jobs_use_purpose_first_display_names() -> None:
    expected = {
        DOCS_WORKFLOW: (
            "name: Documentation",
            "    name: Benchmark",
            "    name: Build",
            "    name: Deploy",
        ),
        PARSER_REFERENCE_WORKFLOW: (
            "name: Parser Reference",
            "    name: Guard",
        ),
        STATIC_ANALYSIS_WORKFLOW: (
            "name: Static Analysis",
            "    name: Python 3.12",
        ),
        TESTS_WORKFLOW: (
            "name: Tests",
            "    name: Python ${{ matrix.python-version }}",
            "    name: macOS 15 ARM64 · Python 3.12",
        ),
        BLAS_LAPACK_WORKFLOW: (
            "name: BLAS + LAPACK",
            "    name: Python 3.12",
        ),
        COVERAGE_WORKFLOW: (
            "name: Coverage",
            "    name: Python 3.12",
        ),
        PUBLISH_WORKFLOW: (
            "name: Publish to PyPI",
            "    name: Build and validate distributions",
            "    name: Publish distributions",
        ),
        CLAUDE_WORKFLOW: (
            "name: Claude Code",
            "    name: Respond",
        ),
    }

    for workflow, names in expected.items():
        text = workflow.read_text(encoding="utf-8")
        for name in names:
            assert name in text


def test_pypi_package_identity_is_complete_and_consistent() -> None:
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")

    for declaration in (
        'name = "prik"',
        'version = "0.1.0"',
        'prik = "prik.cli:main"',
        'Homepage = "https://pynumlab.github.io/prik/"',
        'Repository = "https://github.com/PyNumLab/prik"',
        'Issues = "https://github.com/PyNumLab/prik/issues"',
        'Changelog = "https://github.com/PyNumLab/prik/blob/main/CHANGELOG.md"',
    ):
        assert declaration in pyproject
    assert "## 0.1.0 — 2026-08-01" in changelog
    assert "`prik --version`" in changelog
    assert "`prik.__version__`" in changelog
    assert MANIFEST.read_text(encoding="utf-8") == "include CHANGELOG.md\n"


def test_pypi_publication_uses_a_protected_token_free_release_job() -> None:
    workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    build_job, publish_job = workflow.split("  publish:\n", maxsplit=1)

    for declaration in (
        "  release:\n    types: [published]",
        "persist-credentials: false",
        "release tag {release_tag!r} must be {expected_tag!r}",
        "python -m build",
        "python -m twine check dist/*",
        'compgen -G "dist/prik-*-py3-none-any.whl"',
        'bin/prik" --version',
        "prik.__version__ == m.version",
        "uses: actions/upload-artifact@v4",
    ):
        assert declaration in build_job

    assert "id-token: write" not in build_job
    assert "needs: build" in publish_job
    assert "name: pypi" in publish_job
    assert "id-token: write" in publish_job
    assert "uses: actions/download-artifact@v4" in publish_job
    assert "uses: pypa/gh-action-pypi-publish@release/v1" in publish_job
    assert "secrets." not in workflow
    assert "password:" not in workflow
    assert "workflow_dispatch:" not in workflow


def test_static_analysis_targets_the_renamed_package_tree() -> None:
    workflow = STATIC_ANALYSIS_WORKFLOW.read_text(encoding="utf-8")

    assert "python -m bandit -c pyproject.toml -r prik" in workflow
    assert "python -m radon cc prik" in workflow
    assert "python -m radon mi prik" in workflow
    for removed_root in ("c_parser", "fortran_parser", "semantics"):
        assert removed_root not in workflow


def test_documentation_workflow_generates_main_only_performance_snapshot() -> None:
    workflow = DOCS_WORKFLOW.read_text(encoding="utf-8")

    assert "group: documentation-${{ github.ref }}" in workflow
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in workflow
    assert "runs-on: ubuntu-24.04-arm" in workflow
    assert "if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'" in workflow
    assert "python tools/benchmark_host.py" in workflow
    assert "--require-machine aarch64" in workflow
    assert "--require-arm-part 0xd49" in workflow
    assert '--github-env "$GITHUB_ENV"' in workflow
    assert "bash benchmarks/run.sh" in workflow
    assert "python tools/generate_performance_docs.py" in workflow
    assert "name: performance-snapshot" in workflow
    assert "benchmarks/results/f2py.json" in workflow
    assert "benchmarks/results/prik.json" in workflow
    assert "benchmarks/results/f2py-build.json" in workflow
    assert "benchmarks/results/prik-build.json" in workflow
    assert "uses: actions/download-artifact@v4" in workflow
