"""Public reference and contributor-map contracts."""

import re
from pathlib import Path

import pytest

import prik
from tests.docs._structure_support import (
    CLI_HELP_GROUP_HEADINGS,
    CLI_REFERENCE_OPTIONS,
    CLI_REFERENCE_PATH,
    CLI_VISIBLE_HELP_OPTIONS,
    DOCS_ROOT,
    FEATURE_MATRIX_PATH,
    FEATURE_MATRIX_ROWS,
    FEATURE_MATRIX_STATUSES,
    MARKDOWN_LINK,
    PYTHON_API_REFERENCE_PATH,
    ROOT,
    _front_matter,
    _prik_cli_help,
)


DOCUMENTATION_PATH_REFERENCE = re.compile(r"`(docs/[^`]+\.md)`")


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


def test_feature_matrix_has_rows() -> None:
    assert FEATURE_MATRIX_ROWS


@pytest.mark.parametrize("row", FEATURE_MATRIX_ROWS, ids=lambda row: row["Feature"])
def test_feature_matrix_support_claim_is_complete(row: dict[str, str]) -> None:
    assert row["Status"] in FEATURE_MATRIX_STATUSES
    for column in ["Feature", "Status", "User docs", "Evidence", "Limitations"]:
        assert row[column]
    for column in ["User docs", "Evidence"]:
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
    for column in ["User docs", "Evidence"]:
        for target in MARKDOWN_LINK.findall(row[column]):
            if target.startswith(("http://", "https://")):
                continue
            resolved_target = (FEATURE_MATRIX_PATH.parent / target).resolve()
            assert resolved_target.exists(), f"{row['Feature']}: {column} link target does not exist: {target}"


REVIEWED_CONTRIBUTOR_MAPS = [
    path
    for path in sorted((DOCS_ROOT / "developer").glob("*.md"))
    if _front_matter(path)[0]["publication"] == "reviewed"
]


@pytest.mark.parametrize("source", REVIEWED_CONTRIBUTOR_MAPS, ids=lambda path: path.name)
def test_reviewed_contributor_maps_do_not_require_unpublished_user_docs(source: Path) -> None:
    metadata, body = _front_matter(source)
    targets = [*metadata["related"].split(","), *MARKDOWN_LINK.findall(body)]

    for target in targets:
        target = target.strip().split("#", maxsplit=1)[0]
        if not target.endswith(".md"):
            continue
        destination = (source.parent / target).resolve()
        target_metadata, _ = _front_matter(destination)
        assert target_metadata["publication"] == "reviewed" or destination.is_relative_to(DOCS_ROOT / "developer"), (
            f"{source.relative_to(DOCS_ROOT)}: unpublished documentation target outside docs/developer/: {target}"
        )

    for target in DOCUMENTATION_PATH_REFERENCE.findall(body):
        destination = ROOT / target
        assert destination.is_file(), f"{source.relative_to(DOCS_ROOT)}: missing documentation path: {target}"
        target_metadata, _ = _front_matter(destination)
        assert target_metadata["publication"] == "reviewed" or destination.is_relative_to(DOCS_ROOT / "developer"), (
            f"{source.relative_to(DOCS_ROOT)}: unpublished documentation path outside docs/developer/: {target}"
        )
