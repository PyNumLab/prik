"""Documentation metadata and visibility contracts."""

from pathlib import Path

import pytest

from tests.docs._structure_support import (
    ALLOWED_PUBLICATION_STATES,
    ALLOWED_STATUSES,
    DEFERRED_C_PAGE_PATHS,
    DOC_PATHS,
    REQUIRED_METADATA,
    ROOT,
    _front_matter,
    _visible_documentation_source,
)


@pytest.mark.parametrize("path", DOC_PATHS, ids=lambda path: str(path.relative_to(ROOT)))
def test_documentation_page_metadata(path: Path) -> None:
    metadata, _ = _front_matter(path)
    missing = REQUIRED_METADATA - metadata.keys()
    assert not missing, f"{path.relative_to(ROOT)}: missing metadata fields: {sorted(missing)}"

    for key in REQUIRED_METADATA:
        assert metadata[key], f"{path.relative_to(ROOT)}: metadata field {key!r} is empty"

    assert metadata["status"] in ALLOWED_STATUSES, f"{path.relative_to(ROOT)}: unknown status {metadata['status']!r}"
    assert metadata["publication"] in ALLOWED_PUBLICATION_STATES, (
        f"{path.relative_to(ROOT)}: unknown publication state {metadata['publication']!r}"
    )


@pytest.mark.parametrize("path", DEFERRED_C_PAGE_PATHS, ids=lambda path: str(path.relative_to(ROOT)))
def test_dedicated_deferred_c_pages_have_no_visible_body(path: Path) -> None:
    assert _visible_documentation_source(path).strip() == ""


def test_deferred_c_pages_are_not_in_site_navigation() -> None:
    lines = (ROOT / "mkdocs.yml").read_text(encoding="utf-8").splitlines()
    active_navigation = "\n".join(line for line in lines if not line.lstrip().startswith("#"))
    assert "Inspect a C API" not in active_navigation
    assert "C Parser Reference" not in active_navigation
    assert any("PRIK_C_DOCS" in line and "inspect-c-api.md" in line for line in lines)
    assert any("PRIK_C_DOCS" in line and "deferred/c-parser.md" in line for line in lines)
