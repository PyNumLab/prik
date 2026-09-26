"""Public reference and contributor-map contracts."""

import re
from pathlib import Path

import pytest

import prik
from tests.docs._structure_support import (
    CLI_REFERENCE_OPTIONS,
    CLI_REFERENCE_PATH,
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


def test_cli_reference_and_help_expose_every_public_option() -> None:
    reference = CLI_REFERENCE_PATH.read_text(encoding="utf-8")
    help_text = _prik_cli_help()

    undocumented = [option for option in CLI_REFERENCE_OPTIONS if option not in reference]
    hidden = [option for option in CLI_REFERENCE_OPTIONS if option not in help_text]
    assert not undocumented, f"{CLI_REFERENCE_PATH.relative_to(ROOT)} does not document: {undocumented}"
    assert not hidden, f"`python -m prik --help` output does not show: {hidden}"


def test_python_api_reference_documents_every_public_export() -> None:
    content = PYTHON_API_REFERENCE_PATH.read_text(encoding="utf-8")
    missing = [name for name in sorted(prik.__all__) if f"`{name}`" not in content]
    assert not missing, f"{PYTHON_API_REFERENCE_PATH.relative_to(ROOT)} does not document: {missing}"


def _feature_matrix_row_problems(row: dict[str, str]) -> list[str]:
    feature = row["Feature"] or "<unnamed row>"
    problems = [f"{feature}: {column} is empty" for column in row if not row[column]]
    if row["Status"] not in FEATURE_MATRIX_STATUSES:
        problems.append(f"{feature}: unknown status {row['Status']!r}")
    for column in ["User docs", "Evidence"]:
        targets = MARKDOWN_LINK.findall(row[column])
        if not targets:
            problems.append(f"{feature}: {column} must contain a Markdown link")
        for target in targets:
            if target.startswith(("http://", "https://")):
                continue
            if not (FEATURE_MATRIX_PATH.parent / target).resolve().exists():
                problems.append(f"{feature}: {column} link target does not exist: {target}")
    if row["Status"] in {"Supported", "Partially supported"}:
        evidence_targets = [
            (FEATURE_MATRIX_PATH.parent / target).resolve() for target in MARKDOWN_LINK.findall(row["Evidence"])
        ]
        if not any(target.is_relative_to(ROOT / "tests") for target in evidence_targets):
            problems.append(f"{feature}: support claims need direct test evidence")
    return problems


def test_feature_matrix_support_claims_are_complete_and_linked() -> None:
    assert FEATURE_MATRIX_ROWS, f"{FEATURE_MATRIX_PATH.relative_to(ROOT)}: feature matrix table has no rows"
    problems = [problem for row in FEATURE_MATRIX_ROWS for problem in _feature_matrix_row_problems(row)]
    assert not problems, "\n".join(problems)


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
