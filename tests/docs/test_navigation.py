"""Published documentation-lane contracts."""

from tests.docs._structure_support import ROOT


def test_site_navigation_exposes_user_and_contributor_indexes() -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "user/index.md" in site_configuration
    assert "developer/index.md" in site_configuration
