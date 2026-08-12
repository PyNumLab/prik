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
