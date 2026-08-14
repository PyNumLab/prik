"""Published documentation-lane contracts."""

import pytest

from tests.docs._structure_support import DOCS_ROOT, ROOT, _front_matter


@pytest.mark.parametrize(
    ("lane", "audience_terms"),
    [
        ("user", ("users",)),
        ("developer", ("developers", "maintainers", "contributors")),
    ],
)
def test_documentation_lane_has_consistent_audience(lane: str, audience_terms: tuple[str, ...]) -> None:
    for path in (DOCS_ROOT / lane).rglob("*.md"):
        metadata, _ = _front_matter(path)
        assert any(term in metadata["audience"] for term in audience_terms)
        if lane == "user":
            assert "maintainers" not in metadata["audience"]


def test_site_navigation_exposes_user_and_contributor_indexes() -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "user/index.md" in site_configuration
    assert "developer/index.md" in site_configuration
