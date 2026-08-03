"""Positive ownership and navigation contracts for the pytest tree."""

from __future__ import annotations

import ast
import re
from pathlib import Path


REPO_ROOT = Path(__file__).parents[3]
TEST_ROOT = REPO_ROOT / "tests"
EXAMPLES_ROOT = REPO_ROOT / "examples"
TEST_INDEX = TEST_ROOT / "README.md"
WORKFLOW_ROOT = REPO_ROOT / ".github/workflows"
BLAS_LAPACK_WORKFLOW = REPO_ROOT / ".github/workflows/blas-lapack.yml"
CLAUDE_WORKFLOW = REPO_ROOT / ".github/workflows/claude.yml"
COVERAGE_WORKFLOW = REPO_ROOT / ".github/workflows/coverage.yml"
CODECOV_CONFIG = REPO_ROOT / "codecov.yml"
DOCS_WORKFLOW = REPO_ROOT / ".github/workflows/docs.yml"
FORTRAN_SMOKE_WORKFLOW = REPO_ROOT / ".github/workflows/fortran-toolchain-smoke.yml"
MERGE_VALIDATION_WORKFLOW = REPO_ROOT / ".github/workflows/merge-validation.yml"
PUBLISH_WORKFLOW = REPO_ROOT / ".github/workflows/publish-to-pypi.yml"
STATIC_ANALYSIS_WORKFLOW = REPO_ROOT / ".github/workflows/static-analysis.yml"
TESTS_WORKFLOW = REPO_ROOT / ".github/workflows/tests.yml"
QUALITY_ASSURANCE_DOC = REPO_ROOT / "docs/developer/quality-assurance.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
MANIFEST = REPO_ROOT / "MANIFEST.in"
FULL_REAL_LIBRARY_TEST = "tests/fortran/building_shared_library/end_to_end/real_libraries/test_full_libraries.py"
BLAS_CI_FULL_SURFACE = "examples/blas/ci_full_surface.py"
LAPACK_CI_FULL_SURFACE = "examples/lapack/ci_full_surface.py"

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


def _github_action_job_display_names(workflow: Path) -> dict[str, str]:
    names: dict[str, str] = {}
    current_job: str | None = None
    in_jobs = False
    for line in workflow.read_text(encoding="utf-8").splitlines():
        if line == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue
        job_match = re.fullmatch(r"  ([a-z0-9-]+):", line)
        if job_match:
            current_job = job_match.group(1)
            continue
        if current_job is not None and line.startswith("    name: "):
            names[current_job] = line.removeprefix("    name: ")
    return names


def _github_action_workflow_name(workflow: Path) -> str:
    first_line = workflow.read_text(encoding="utf-8").splitlines()[0]
    assert first_line.startswith("name: ")
    return first_line.removeprefix("name: ")


def _github_matrix_display_names(workflow: Path) -> tuple[str, ...]:
    prefix = "display_name: "
    return tuple(
        line.strip().removeprefix(prefix)
        for line in workflow.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith(prefix)
    )


def _github_action_job_block(workflow: Path, job_id: str) -> str:
    remainder = workflow.read_text(encoding="utf-8").split(f"  {job_id}:\n", maxsplit=1)[1]
    next_job = re.search(r"\n  [a-z0-9-]+:\n", remainder)
    return remainder if next_job is None else remainder[: next_job.start()]


def _github_action_job_steps(workflow: Path, job_id: str) -> tuple[str, ...]:
    block = _github_action_job_block(workflow, job_id)
    steps = block.split("    steps:\n", maxsplit=1)[1]
    return tuple(line for line in steps.splitlines() if line.strip())


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


def test_native_library_examples_are_copyable_without_the_repository_test_package() -> None:
    assert (EXAMPLES_ROOT / "__init__.py").is_file()
    assert (EXAMPLES_ROOT / "conftest.py").is_file()
    assert (EXAMPLES_ROOT / "blas" / "__init__.py").is_file()
    assert (EXAMPLES_ROOT / "lapack" / "__init__.py").is_file()

    repository_test_imports = []
    for path in sorted(EXAMPLES_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None and node.module.startswith("tests"):
                repository_test_imports.append(f"{path.relative_to(REPO_ROOT)}: {node.module}")
            if isinstance(node, ast.Import):
                repository_test_imports.extend(
                    f"{path.relative_to(REPO_ROOT)}: {alias.name}"
                    for alias in node.names
                    if alias.name.startswith("tests")
                )
    assert repository_test_imports == []


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


def test_real_library_examples_have_one_dedicated_workflow() -> None:
    ordinary_jobs = TESTS_WORKFLOW.read_text(encoding="utf-8")
    dedicated_job = BLAS_LAPACK_WORKFLOW.read_text(encoding="utf-8")

    assert '-m "not real_library and not toolchain_smoke"' in ordinary_jobs
    assert ordinary_jobs.count('-m "not real_library and not toolchain_smoke"') == 2
    assert FULL_REAL_LIBRARY_TEST not in ordinary_jobs
    assert "examples/blas" not in ordinary_jobs
    assert "examples/lapack" not in ordinary_jobs
    assert 'python -m pytest -q -o "python_files=test_*.py ci_full_surface.py"' in dedicated_job
    assert dedicated_job.count("python_files=test_*.py ci_full_surface.py") == 2
    assert f"examples/blas {BLAS_CI_FULL_SURFACE}" in dedicated_job
    assert f"examples/lapack {LAPACK_CI_FULL_SURFACE}" in dedicated_job
    assert BLAS_CI_FULL_SURFACE in dedicated_job
    assert LAPACK_CI_FULL_SURFACE in dedicated_job
    assert FULL_REAL_LIBRARY_TEST not in dedicated_job
    assert '"meson==1.11.2"' in dedicated_job
    assert '"ninja==1.13.0"' in dedicated_job
    assert '"scipy==1.18.0"' in dedicated_job
    assert "libblas-dev" in dedicated_job
    assert "liblapack-dev" in dedicated_job
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


def test_active_github_action_checks_use_distinct_workflow_scopes_and_job_names() -> None:
    workflow_names = {
        BLAS_LAPACK_WORKFLOW: "Native Libraries",
        CLAUDE_WORKFLOW: "Repository Automation",
        COVERAGE_WORKFLOW: "Quality Metrics",
        DOCS_WORKFLOW: "Documentation",
        FORTRAN_SMOKE_WORKFLOW: "Compiler Compatibility",
        MERGE_VALIDATION_WORKFLOW: "Pull Request",
        PUBLISH_WORKFLOW: "Release Automation",
        STATIC_ANALYSIS_WORKFLOW: "Code Quality",
        TESTS_WORKFLOW: "Test Matrix",
    }
    expected = {
        BLAS_LAPACK_WORKFLOW: {"real-library-wrappers": "BLAS + LAPACK · Ubuntu 24.04 · Python 3.12"},
        CLAUDE_WORKFLOW: {"claude": "Claude Code response to mention"},
        COVERAGE_WORKFLOW: {"coverage": "Project coverage · Ubuntu 24.04 · Python 3.12"},
        DOCS_WORKFLOW: {
            "benchmark": "Documentation performance benchmark · Ubuntu 24.04 ARM64 · Python 3.12",
            "build": "Documentation site build · Ubuntu 24.04 · Python 3.12",
            "deploy": "Documentation deployment · GitHub Pages",
        },
        FORTRAN_SMOKE_WORKFLOW: {
            "toolchain-smoke": "Compiler smoke · ${{ matrix.display_name }}",
            "macos-flang-smoke": "Compiler smoke · macOS 15 ARM64 · LLVM Flang · Python 3.12",
        },
        MERGE_VALIDATION_WORKFLOW: {
            "static-analysis": "Static analysis · Ubuntu 24.04 · Python 3.12",
            "parser-reference-guard": "Parser reference guard · Ubuntu 24.04",
            "compiler-smoke": "Compiler smoke · ${{ matrix.display_name }}",
            "compiler-smoke-macos": "Compiler smoke · macOS 15 ARM64 · LLVM Flang · Python 3.12",
            "unit-tests": "${{ matrix.display_name }}",
            "unit-tests-macos": "Unit tests · macOS 15 ARM64 · Python 3.12",
            "native-libraries": "BLAS + LAPACK · Ubuntu 24.04 · Python 3.12",
            "documentation-benchmark": "Documentation performance benchmark · Ubuntu 24.04 ARM64 · Python 3.12",
            "documentation-build": "Documentation site build · Ubuntu 24.04 · Python 3.12",
            "merge-gate": "Validation · all required checks",
        },
        PUBLISH_WORKFLOW: {
            "build": "PyPI distribution build · Ubuntu 24.04 · Python 3.12",
            "publish": "PyPI trusted publishing · pypi",
        },
        STATIC_ANALYSIS_WORKFLOW: {"static-analysis": "Static analysis · Ubuntu 24.04 · Python 3.12"},
        TESTS_WORKFLOW: {
            "test": "Unit tests · Ubuntu 24.04 · Python ${{ matrix.python-version }}",
            "macos": "Unit tests · macOS 15 ARM64 · Python 3.12",
        },
    }

    assert set(workflow_names) == set(expected) == set(WORKFLOW_ROOT.glob("*.yml"))
    assert {workflow: _github_action_workflow_name(workflow) for workflow in workflow_names} == workflow_names
    assert len(workflow_names.values()) == len(set(workflow_names.values()))
    assert {workflow: _github_action_job_display_names(workflow) for workflow in expected} == expected

    display_names = [name for jobs in expected.values() for name in jobs.values()]
    check_contexts = [
        f"{workflow_names[workflow]} / {job_name}" for workflow, jobs in expected.items() for job_name in jobs.values()
    ]
    assert len(check_contexts) == len(set(check_contexts))
    assert all(not re.fullmatch(r"Python(?:\s+.*)?", name) for name in display_names)

    smoke_matrix_names = _github_matrix_display_names(FORTRAN_SMOKE_WORKFLOW)
    assert smoke_matrix_names == (
        "Ubuntu 24.04 · Intel IFX 2026.1.1 · Python 3.12",
        "Ubuntu 24.04 · LLVM Flang 22.1.8 · Python 3.12",
    )
    assert 'python-version: ["3.10", "3.11", "3.12"]' in TESTS_WORKFLOW.read_text(encoding="utf-8")
    documented_contexts = ("Pull Request / Validation · all required checks",)
    quality_assurance = QUALITY_ASSURANCE_DOC.read_text(encoding="utf-8")
    assert len(documented_contexts) == len(set(documented_contexts))
    for context in documented_contexts:
        assert f"`{context}`" in quality_assurance


def test_pull_request_declares_direct_staged_jobs_and_always_reports_the_gate() -> None:
    workflow = MERGE_VALIDATION_WORKFLOW.read_text(encoding="utf-8")

    assert workflow.startswith("name: Pull Request\n")
    assert "  pull_request:\n    types: [opened, synchronize, reopened, labeled, unlabeled]" in workflow
    assert "group: pull-request-${{ github.ref }}" in workflow
    assert "cancel-in-progress: true" in workflow
    assert "uses: ./.github/workflows/" not in workflow

    for job_id in ("static-analysis", "parser-reference-guard"):
        block = _github_action_job_block(MERGE_VALIDATION_WORKFLOW, job_id)
        assert "needs:" not in block
        assert "runs-on:" in block

    for job_id in ("compiler-smoke", "compiler-smoke-macos"):
        block = _github_action_job_block(MERGE_VALIDATION_WORKFLOW, job_id)
        assert "needs: [static-analysis, parser-reference-guard]" in block
        assert "runs-on:" in block

    for job_id in ("unit-tests", "unit-tests-macos"):
        block = _github_action_job_block(MERGE_VALIDATION_WORKFLOW, job_id)
        assert "needs: [compiler-smoke, compiler-smoke-macos]" in block
        assert "runs-on:" in block

    unit_tests = _github_action_job_block(MERGE_VALIDATION_WORKFLOW, "unit-tests")
    assert "Unit tests + project coverage · Ubuntu 24.04 · Python 3.12" in unit_tests
    assert "python -m coverage combine" in unit_tests
    assert "python -m coverage report" in unit_tests
    assert "uses: codecov/codecov-action@v6" in unit_tests
    assert "id-token: write" in unit_tests

    native_libraries = _github_action_job_block(MERGE_VALIDATION_WORKFLOW, "native-libraries")
    assert "needs: [unit-tests, unit-tests-macos]" in native_libraries
    assert "ignore-real-library-wrappers" in native_libraries
    assert 'python -m pytest -q -o "python_files=test_*.py ci_full_surface.py"' in native_libraries
    assert native_libraries.count("python_files=test_*.py ci_full_surface.py") == 2
    assert f"examples/blas {BLAS_CI_FULL_SURFACE}" in native_libraries
    assert f"examples/lapack {LAPACK_CI_FULL_SURFACE}" in native_libraries
    assert BLAS_CI_FULL_SURFACE in native_libraries
    assert LAPACK_CI_FULL_SURFACE in native_libraries
    assert FULL_REAL_LIBRARY_TEST not in native_libraries

    benchmark = _github_action_job_block(MERGE_VALIDATION_WORKFLOW, "documentation-benchmark")
    assert "needs: native-libraries" in benchmark
    assert "always()" in benchmark
    assert "bash benchmarks/run.sh" in benchmark

    documentation = _github_action_job_block(MERGE_VALIDATION_WORKFLOW, "documentation-build")
    assert "needs: documentation-benchmark" in documentation
    assert "python -m pytest -q tests/shared/docs" in documentation
    assert "python -m mkdocs build --strict" in documentation

    gate = _github_action_job_block(MERGE_VALIDATION_WORKFLOW, "merge-gate")
    assert "if: ${{ always() }}" in gate
    for dependency in (
        "static-analysis",
        "parser-reference-guard",
        "compiler-smoke",
        "compiler-smoke-macos",
        "unit-tests",
        "unit-tests-macos",
        "native-libraries",
        "documentation-benchmark",
        "documentation-build",
    ):
        assert f"      - {dependency}" in gate
        assert f"needs.{dependency}.result" in gate
    assert 'if [[ "$result" != "success" ]]' in gate
    assert 'exit "$failed"' in gate


def test_purpose_specific_workflows_do_not_create_duplicate_pull_request_runs() -> None:
    for workflow in (
        TESTS_WORKFLOW,
        STATIC_ANALYSIS_WORKFLOW,
        BLAS_LAPACK_WORKFLOW,
        FORTRAN_SMOKE_WORKFLOW,
        COVERAGE_WORKFLOW,
        DOCS_WORKFLOW,
    ):
        text = workflow.read_text(encoding="utf-8")
        assert "  workflow_call:" not in text
        assert "  pull_request:" not in text

    assert "run-coverage" not in COVERAGE_WORKFLOW.read_text(encoding="utf-8")


def test_pull_request_jobs_share_the_reviewed_component_workflow_steps() -> None:
    for pull_request_job, component_workflow, component_job in (
        ("static-analysis", STATIC_ANALYSIS_WORKFLOW, "static-analysis"),
        ("compiler-smoke", FORTRAN_SMOKE_WORKFLOW, "toolchain-smoke"),
        ("compiler-smoke-macos", FORTRAN_SMOKE_WORKFLOW, "macos-flang-smoke"),
        ("unit-tests-macos", TESTS_WORKFLOW, "macos"),
        ("native-libraries", BLAS_LAPACK_WORKFLOW, "real-library-wrappers"),
        ("documentation-benchmark", DOCS_WORKFLOW, "benchmark"),
    ):
        assert _github_action_job_steps(MERGE_VALIDATION_WORKFLOW, pull_request_job) == _github_action_job_steps(
            component_workflow, component_job
        )

    pull_request_build = _github_action_job_steps(MERGE_VALIDATION_WORKFLOW, "documentation-build")
    main_build = _github_action_job_steps(DOCS_WORKFLOW, "build")
    configure_pages = main_build.index("      - name: Configure GitHub Pages")
    assert pull_request_build == main_build[:configure_pages]


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


def test_pull_request_and_main_generate_equivalent_documentation_performance_snapshots() -> None:
    pull_request = MERGE_VALIDATION_WORKFLOW.read_text(encoding="utf-8")
    main = DOCS_WORKFLOW.read_text(encoding="utf-8")

    assert "group: documentation-${{ github.ref }}" in main
    assert "cancel-in-progress: true" in main
    assert "  workflow_call:" not in main
    for declaration in (
        "runs-on: ubuntu-24.04-arm",
        "python tools/benchmark_host.py",
        "--require-machine aarch64",
        "--require-arm-part 0xd49",
        '--github-env "$GITHUB_ENV"',
        "bash benchmarks/run.sh",
        "python tools/generate_performance_docs.py",
        "name: performance-snapshot",
        "benchmarks/results/f2py.json",
        "benchmarks/results/prik.json",
        "benchmarks/results/f2py-build.json",
        "benchmarks/results/prik-build.json",
        "uses: actions/download-artifact@v4",
        "python -m pytest -q tests/shared/docs",
        "python -m mkdocs build --strict",
    ):
        assert declaration in pull_request
        assert declaration in main

    assert main.count("github.ref == 'refs/heads/main' && github.event_name != 'pull_request'") == 3
