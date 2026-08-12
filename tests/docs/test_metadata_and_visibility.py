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
    TODO_STATUSES,
    VISIBLE_C_DOCUMENTATION,
    VISIBLE_C_DOCUMENTATION_EXCEPTIONS,
    WEBSITE_DOCUMENTATION_PATHS,
    _front_matter,
    _visible_documentation_source,
)


@pytest.mark.parametrize("path", DOC_PATHS, ids=lambda path: str(path.relative_to(ROOT)))
def test_documentation_page_metadata(path: Path) -> None:
    metadata, body = _front_matter(path)
    missing = REQUIRED_METADATA - metadata.keys()
    assert not missing, f"{path.relative_to(ROOT)}: missing metadata fields: {sorted(missing)}"

    for key in REQUIRED_METADATA:
        assert metadata[key], f"{path.relative_to(ROOT)}: metadata field {key!r} is empty"

    assert metadata["status"] in ALLOWED_STATUSES, f"{path.relative_to(ROOT)}: unknown status {metadata['status']!r}"
    assert metadata["publication"] in ALLOWED_PUBLICATION_STATES, (
        f"{path.relative_to(ROOT)}: unknown publication state {metadata['publication']!r}"
    )
    if metadata["status"] in TODO_STATUSES:
        assert "## TODO" in body, f"{path.relative_to(ROOT)}: unfinished pages must include a TODO section"
        assert "TODO:" in body, f"{path.relative_to(ROOT)}: TODO section must contain explicit TODO markers"


@pytest.mark.parametrize(
    "path",
    [
        ROOT / "README.md",
        *(path for path in WEBSITE_DOCUMENTATION_PATHS if _front_matter(path)[0].get("publication") == "reviewed"),
    ],
    ids=lambda path: str(path.relative_to(ROOT)),
)
def test_deferred_c_documentation_is_not_visible(path: Path) -> None:
    visible = _visible_documentation_source(path)
    for allowed_text in VISIBLE_C_DOCUMENTATION_EXCEPTIONS.get(str(path.relative_to(ROOT)), ()):
        visible = visible.replace(allowed_text, "")
    match = VISIBLE_C_DOCUMENTATION.search(visible)
    assert match is None, f"{path.relative_to(ROOT)}: visible deferred documentation: {match.group(0)!r}"


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


def test_contributor_maps_defer_only_the_c_input_frontend() -> None:
    source_map = _visible_documentation_source(ROOT / "docs/developer/source-map.md")
    feature_map = _visible_documentation_source(ROOT / "docs/developer/feature-to-code-map.md")
    visible = f"{source_map}\n{feature_map}"

    for deferred_owner in (
        "prik/parsers/c/",
        "prik/semantics/c2ir.py",
        "prik/preprocessing/c.py",
        "prik/preprocessing/probes/c_types.py",
        "tests/c/",
    ):
        assert deferred_owner not in visible

    for generated_backend_owner in (
        "prik/codegen/c/binding.py",
        "prik/codegen/c/python_surface.py",
        "prik/printers/c.py",
        "prik/codegen/fortran/bridge.py",
        "prik/printers/fortran.py",
    ):
        assert generated_backend_owner in visible
