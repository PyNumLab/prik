"""Public reference and source-navigation synchronization contracts."""

import re

import pytest

import prik
from tests.docs._structure_support import (
    ARCHIVED_OLD_DOCS,
    CLI_HELP_GROUP_HEADINGS,
    CLI_REFERENCE_OPTIONS,
    CLI_REFERENCE_PATH,
    CLI_VISIBLE_HELP_OPTIONS,
    DOCS_ROOT,
    FEATURE_MATRIX_PATH,
    FEATURE_MATRIX_REQUIRED_FEATURES,
    FEATURE_MATRIX_ROWS,
    FEATURE_MATRIX_STATUSES,
    LEGACY_ACTIVE_DOC_REFERENCES,
    MAJOR_SOURCE_PACKAGES,
    MARKDOWN_LINK,
    PACKAGE_READMES,
    PACKAGE_README_NAVIGATION_REFERENCES,
    PYTHON_API_REFERENCE_PATH,
    REQUIRED_EXAMPLE_RECIPE_PAGES,
    REQUIRED_SOURCE_NAVIGATION_PAGES,
    ROOT,
    SOURCE_NAVIGATION_CORPUS,
    SOURCE_NAVIGATION_HOTSPOTS,
    SOURCE_NAVIGATION_PUBLIC_DOCS,
    SOURCE_NAVIGATION_TEST_TARGETS,
    _combined_text,
    _prik_cli_help,
)


PYTHON_SOURCE_REFERENCE = re.compile(
    r"`((?:(?:\.\./|[A-Za-z0-9_]+/)*[A-Za-z0-9_]+\.py))`",
)


@pytest.mark.parametrize("heading", CLI_HELP_GROUP_HEADINGS)
def test_cli_help_uses_documented_option_groups(heading: str) -> None:
    assert heading in _prik_cli_help()


@pytest.mark.parametrize("option", CLI_REFERENCE_OPTIONS)
def test_cli_reference_documents_public_option(option: str) -> None:
    content = CLI_REFERENCE_PATH.read_text(encoding="utf-8")
    assert option in content


@pytest.mark.parametrize("option", CLI_VISIBLE_HELP_OPTIONS)
def test_cli_help_exposes_documented_public_option(option: str) -> None:
    assert option in _prik_cli_help()


@pytest.mark.parametrize("name", sorted(prik.__all__))
def test_python_api_reference_documents_public_export(name: str) -> None:
    content = PYTHON_API_REFERENCE_PATH.read_text(encoding="utf-8")
    assert f"`{name}`" in content


@pytest.mark.parametrize("relative_path", REQUIRED_SOURCE_NAVIGATION_PAGES)
def test_required_source_navigation_page_exists(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", REQUIRED_SOURCE_NAVIGATION_PAGES)
def test_source_navigation_page_is_in_site_navigation(relative_path: str) -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert relative_path in site_configuration


@pytest.mark.parametrize("relative_path", REQUIRED_EXAMPLE_RECIPE_PAGES)
def test_required_example_recipe_exists(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", REQUIRED_EXAMPLE_RECIPE_PAGES)
def test_example_recipe_is_in_site_navigation(relative_path: str) -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert relative_path in site_configuration


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_HOTSPOTS)
def test_source_navigation_hotspot_exists(relative_path: str) -> None:
    assert (ROOT / relative_path).exists()


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_HOTSPOTS)
def test_source_navigation_mentions_hotspot(relative_path: str) -> None:
    assert relative_path in _combined_text(SOURCE_NAVIGATION_CORPUS)


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_PUBLIC_DOCS)
def test_source_navigation_public_doc_exists(relative_path: str) -> None:
    assert (ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_PUBLIC_DOCS)
def test_source_navigation_mentions_public_doc(relative_path: str) -> None:
    assert relative_path in _combined_text(SOURCE_NAVIGATION_CORPUS)


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_TEST_TARGETS)
def test_source_navigation_test_target_exists(relative_path: str) -> None:
    assert (ROOT / relative_path).exists()


@pytest.mark.parametrize("relative_path", SOURCE_NAVIGATION_TEST_TARGETS)
def test_source_navigation_mentions_test_target(relative_path: str) -> None:
    assert relative_path in _combined_text(SOURCE_NAVIGATION_CORPUS)


@pytest.mark.parametrize("relative_path", PACKAGE_READMES)
def test_package_readme_links_to_source_navigation(relative_path: str) -> None:
    content = (ROOT / relative_path).read_text(encoding="utf-8")
    for reference in PACKAGE_README_NAVIGATION_REFERENCES:
        assert reference in content


@pytest.mark.parametrize("relative_path", PACKAGE_READMES)
def test_package_readme_python_source_references_exist(relative_path: str) -> None:
    readme = ROOT / relative_path
    references = PYTHON_SOURCE_REFERENCE.findall(readme.read_text(encoding="utf-8"))

    for reference in references:
        if reference.startswith(("docs/", "examples/", "prik/", "tests/", "tools/")):
            target = ROOT / reference
        else:
            target = readme.parent / reference
        assert target.resolve().is_file(), f"{relative_path}: missing Python source reference {reference}"


@pytest.mark.parametrize("relative_path", PACKAGE_READMES)
def test_package_readme_does_not_use_legacy_active_doc_paths(relative_path: str) -> None:
    content = (ROOT / relative_path).read_text(encoding="utf-8")
    for reference in LEGACY_ACTIVE_DOC_REFERENCES:
        assert reference not in content


def test_feature_matrix_has_rows_and_status_groups() -> None:
    assert FEATURE_MATRIX_ROWS
    statuses = {row["Status"] for row in FEATURE_MATRIX_ROWS}
    assert {"Supported", "Partially supported", "Unsupported", "Planned", "Not implemented"} <= statuses


@pytest.mark.parametrize("feature", FEATURE_MATRIX_REQUIRED_FEATURES)
def test_feature_matrix_includes_required_feature(feature: str) -> None:
    matrix_features = {row["Feature"] for row in FEATURE_MATRIX_ROWS}
    assert feature in matrix_features


@pytest.mark.parametrize("row", FEATURE_MATRIX_ROWS, ids=lambda row: row["Feature"])
def test_feature_matrix_row_is_complete(row: dict[str, str]) -> None:
    assert row["Status"] in FEATURE_MATRIX_STATUSES
    assert "TODO" not in " ".join(row.values())
    for column in ["Feature", "Status", "User docs", "Source owner", "Evidence", "Limitations"]:
        assert row[column]
    for column in ["User docs", "Source owner", "Evidence"]:
        assert MARKDOWN_LINK.search(row[column]), f"{row['Feature']}: {column} must contain a Markdown link"
    if row["Status"] in {"Supported", "Partially supported"}:
        evidence_targets = [
            (FEATURE_MATRIX_PATH.parent / target).resolve() for target in MARKDOWN_LINK.findall(row["Evidence"])
        ]
        assert any(target.is_relative_to(ROOT / "tests") for target in evidence_targets), (
            f"{row['Feature']}: support claims need direct test evidence"
        )


@pytest.mark.parametrize("row", FEATURE_MATRIX_ROWS, ids=lambda row: row["Feature"])
def test_feature_matrix_links_point_to_existing_files(row: dict[str, str]) -> None:
    for column in ["User docs", "Source owner", "Evidence"]:
        for target in MARKDOWN_LINK.findall(row[column]):
            if target.startswith(("http://", "https://")):
                continue
            resolved_target = (FEATURE_MATRIX_PATH.parent / target).resolve()
            assert resolved_target.exists(), f"{row['Feature']}: {column} link target does not exist: {target}"


@pytest.mark.parametrize("package", MAJOR_SOURCE_PACKAGES)
def test_source_map_covers_major_source_packages(package: str) -> None:
    source_map = (DOCS_ROOT / "developer/source-map.md").read_text(encoding="utf-8")
    assert package in source_map


@pytest.mark.parametrize("relative_path", PACKAGE_READMES)
def test_major_source_package_has_local_readme(relative_path: str) -> None:
    assert (ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", ARCHIVED_OLD_DOCS)
def test_old_documentation_is_archived(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


def test_static_site_seed_configuration_exists() -> None:
    assert (ROOT / "mkdocs.yml").is_file()


def test_contributor_architecture_stays_shallow_and_routes_to_package_guides() -> None:
    architecture = (DOCS_ROOT / "developer/architecture.md").read_text(encoding="utf-8")
    overview_start = architecture.index("## Repository Structure")
    overview_end = architecture.index("## Package-Root Entry Points")
    overview = architecture[overview_start:overview_end]

    for direct_child in (
        "├── prik/",
        "├── tests/",
        "├── docs/",
        "├── examples/",
        "├── tools/",
        "├── compiler/",
        "├── preprocessing/",
        "├── parsers/",
        "├── semantics/",
        "├── policy/",
        "├── planning/",
        "├── codegen/",
        "├── printers/",
        "├── pipeline/",
        "├── runtime/",
        "├── naming/",
        "└── utilities/",
    ):
        assert direct_child in overview
    assert "│   ├──" not in overview
    assert "    ├──" not in overview

    for heading in (
        "Package-Root Entry Points",
        "End-To-End Workflow",
        "Stage Handoffs",
        "Authority And Dependency Rules",
        "Package Guide Map",
        "Tests And Evidence",
        "Where A Change Begins",
        "Contributor Documentation Structure",
    ):
        assert f"## {heading}" in architecture

    package_guides = (
        "contracts",
        "compiler",
        "preprocessing",
        "parsers",
        "semantics",
        "policy",
        "planning",
        "codegen",
        "printers",
        "pipeline",
        "runtime",
        "naming",
        "utilities",
    )
    for package in package_guides:
        assert f"packages/{package}.md" in architecture


def test_every_top_level_source_package_has_one_canonical_guide() -> None:
    expected_packages = {
        "contracts",
        "compiler",
        "preprocessing",
        "parsers",
        "semantics",
        "policy",
        "planning",
        "codegen",
        "printers",
        "pipeline",
        "runtime",
        "naming",
        "utilities",
    }
    source_packages = {
        path.name for path in (ROOT / "prik").iterdir() if path.is_dir() and not path.name.startswith("_")
    }
    guide_paths = {path.stem for path in (DOCS_ROOT / "developer/packages").glob("*.md") if path.name != "index.md"}

    assert source_packages == expected_packages
    assert guide_paths == expected_packages


@pytest.mark.parametrize(
    "package",
    (
        "contracts",
        "compiler",
        "preprocessing",
        "parsers",
        "semantics",
        "policy",
        "planning",
        "codegen",
        "printers",
        "pipeline",
        "runtime",
        "naming",
        "utilities",
    ),
)
def test_package_guide_has_structure_examples_tests_and_change_routes(package: str) -> None:
    path = DOCS_ROOT / f"developer/packages/{package}.md"
    content = path.read_text(encoding="utf-8")

    assert "../architecture.md" in content
    assert "## Purpose And Boundaries" in content
    assert "## Local Structure" in content
    assert "## What This Stage Receives And Produces" in content
    assert "## Directory Tour" in content
    assert "## Execution Example" in content
    assert "## Tests And What They Prove" in content
    assert "## Change Routes" in content
    assert "../../../tests/" in content
    assert "python3 prik/" in content

    for target in MARKDOWN_LINK.findall(content):
        if target.startswith(("http://", "https://")):
            continue
        assert (path.parent / target).resolve().exists(), f"{package}: missing linked owner {target}"


def test_package_guides_cover_every_supported_python_module() -> None:
    deferred_c_input_modules = {
        path.relative_to(ROOT).as_posix()
        for root in (
            ROOT / "prik/parsers/c",
            ROOT / "prik/preprocessing/c.py",
            ROOT / "prik/preprocessing/probes/c_types.py",
            ROOT / "prik/semantics/c2ir.py",
        )
        for path in (root.rglob("*.py") if root.is_dir() else (root,))
    }

    package_guides = {
        path.stem: path for path in (DOCS_ROOT / "developer/packages").glob("*.md") if path.name != "index.md"
    }
    for package, guide_path in package_guides.items():
        documented = guide_path.read_text(encoding="utf-8")
        source_modules = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "prik" / package).rglob("*.py")
            if path.relative_to(ROOT).as_posix() not in deferred_c_input_modules
        }
        missing = sorted(path for path in source_modules if path not in documented)
        assert not missing, f"{guide_path.name}: undocumented supported modules: {missing}"


def test_superseded_contributor_pages_and_completed_roadmaps_are_removed() -> None:
    removed_paths = (
        "adding-a-feature.md",
        "adding-a-fortran-construct.md",
        "adding-a-code-generation-backend.md",
        "build-system.md",
        "coding-standards.md",
        "development-workflow.md",
        "repository-structure.md",
        "roadmap/native-array-handle-checklist.md",
        "roadmap/wrapper-plan-migration-checklist.md",
    )
    for relative_path in removed_paths:
        assert not (DOCS_ROOT / "developer" / relative_path).exists()


def test_contributor_documentation_uses_only_canonical_areas_and_active_roadmaps() -> None:
    contributor_root = DOCS_ROOT / "developer"
    assert {path.name for path in contributor_root.iterdir() if path.is_dir()} == {
        "concepts",
        "deferred",
        "design",
        "packages",
        "roadmap",
        "workflows",
    }
    assert {path.name for path in contributor_root.glob("*.md")} == {
        "architecture.md",
        "feature-to-code-map.md",
        "index.md",
        "source-map.md",
        "testing-strategy.md",
    }

    roadmap_root = contributor_root / "roadmap"
    roadmap_paths = {path.name for path in roadmap_root.glob("*.md")}
    assert roadmap_paths == {
        "documentation-content-checklist.md",
        "fortran-test-suite-cleanup-checklist.md",
        "index.md",
        "semantic-pyi-wrapper-checklist.md",
    }
    for path in roadmap_root.glob("*-checklist.md"):
        assert re.search(r"^\s*- \[ \]", path.read_text(encoding="utf-8"), re.MULTILINE), (
            f"{path.relative_to(ROOT)} is complete and belongs in Git history, not active roadmaps"
        )


def test_package_guide_execution_commands_have_centralized_contract_tests() -> None:
    test_inventory = (ROOT / "tests/fortran/infrastructure/execution_examples/test_execution_examples.py").read_text(
        encoding="utf-8"
    )

    for path in sorted((DOCS_ROOT / "developer/packages").glob("*.md")):
        if path.name == "index.md":
            continue
        content = path.read_text(encoding="utf-8")
        commands = re.findall(r"^python3 (prik/[A-Za-z0-9_/]+\.py)(?:\s.*)?$", content, re.MULTILINE)
        assert commands, f"{path.name}: no direct production-file example"
        for command_path in commands:
            components = [component.removesuffix(".py").strip("_") for component in command_path.split("/")[1:]]
            test_name = f"test_fortran_{'_'.join(components)}_execution_example"
            assert f"def {test_name}(" in test_inventory, f"{path.name}: {command_path} lacks {test_name}"


def test_generated_site_and_distribution_outputs_share_hidden_root() -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    release_workflow = (ROOT / ".github/workflows/publish-to-pypi.yml").read_text(encoding="utf-8")
    docs_workflow = (ROOT / ".github/workflows/docs.yml").read_text(encoding="utf-8")
    setup_configuration = (ROOT / "setup.cfg").read_text(encoding="utf-8")
    artifact_ignores = (ROOT / ".artifacts/.gitignore").read_text(encoding="utf-8").splitlines()
    source_manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")

    assert "site_dir: .artifacts/site" in site_configuration
    assert "python -m build --outdir .artifacts/dist" in release_workflow
    assert "path: .artifacts/dist/" in release_workflow
    assert "packages-dir: .artifacts/dist/" in release_workflow
    assert "path: .artifacts/site" in docs_workflow
    assert "egg_base = .artifacts" in setup_configuration
    assert artifact_ignores == ["*", "!.gitignore"]
    assert "include .artifacts/.gitignore" in source_manifest


def test_site_theme_keeps_sidebar_open_and_code_blocks_copyable() -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "name: readthedocs" in site_configuration
    assert "collapse_navigation: false" in site_configuration
    assert "navigation_depth: 4" in site_configuration
    assert "stylesheets/site.css" in site_configuration
    assert "stylesheets/code-copy.css" in site_configuration
    assert "javascripts/code-copy.js" in site_configuration

    script = (DOCS_ROOT / "javascripts" / "code-copy.js").read_text(encoding="utf-8")
    layout_stylesheet = (DOCS_ROOT / "stylesheets" / "site.css").read_text(encoding="utf-8")
    stylesheet = (DOCS_ROOT / "stylesheets" / "code-copy.css").read_text(encoding="utf-8")
    assert ".wy-nav-content" in layout_stylesheet
    assert "max-width: 1200px" in layout_stylesheet
    assert "margin: 0" in layout_stylesheet
    assert ".wy-nav-side" in layout_stylesheet
    assert "padding-bottom: 0" in layout_stylesheet
    assert ".wy-side-scroll" in layout_stylesheet
    assert "overflow-y: auto" in layout_stylesheet
    assert "scrollbar-width: thin" in layout_stylesheet
    assert ".wy-side-scroll::-webkit-scrollbar-thumb" in layout_stylesheet
    assert ".rst-versions" in layout_stylesheet
    assert "display: none" in layout_stylesheet
    assert ".rst-content pre" in layout_stylesheet
    assert "width: 100%" in layout_stylesheet
    assert "max-width: 56rem" in layout_stylesheet
    assert "padding-right: 3.25rem" in layout_stylesheet
    assert 'document.querySelectorAll("pre code")' in script
    assert "navigator.clipboard.writeText" in script
    assert 'button.setAttribute("aria-label", "Copy code to clipboard")' in script
    assert ".prik-code-copy" in stylesheet
