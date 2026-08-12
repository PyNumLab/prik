"""Verify fail-closed MkDocs publication filtering."""

from __future__ import annotations

from pathlib import Path

from tools import mkdocs_publication


def test_root_and_lane_indexes_gate_reviewed_pages() -> None:
    states = {
        "index.md": "reviewed",
        "user/index.md": "reviewed",
        "user/ready.md": "reviewed",
        "user/draft.md": "draft",
        "developer/index.md": "draft",
        "developer/ready.md": "reviewed",
    }

    assert mkdocs_publication._reviewed_paths(states) == {
        "index.md",
        "user/index.md",
        "user/ready.md",
    }
    assert mkdocs_publication._reviewed_paths({**states, "index.md": "draft"}) == set()


def test_navigation_drops_drafts_and_empty_sections() -> None:
    navigation = [
        {"Home": "index.md"},
        {"User": [{"Overview": "user/index.md"}, {"Draft": "user/draft.md"}]},
        {"Developer": [{"Draft": "developer/draft.md"}]},
    ]

    assert mkdocs_publication._filter_navigation(navigation, {"index.md", "user/index.md"}) == [
        {"Home": "index.md"},
        {"User": [{"Overview": "user/index.md"}]},
    ]


def test_production_links_to_unpublished_pages_point_to_draft_site_route(monkeypatch) -> None:
    monkeypatch.setattr(
        mkdocs_publication,
        "_known_document_paths",
        {"index.md", "user/index.md", "user/draft.md"},
    )
    monkeypatch.setattr(mkdocs_publication, "_published_paths", {"index.md", "user/index.md"})
    markdown = "[User](user/index.md) [Draft](user/draft.md) [Source](../README.md) [External](https://example.com)"

    assert mkdocs_publication._rewrite_unpublished_document_targets(markdown, "index.md") == (
        "[User](user/index.md) [Draft](user/draft/) [Source](../README.md) [External](https://example.com)"
    )


def test_repository_evidence_links_are_rewritten_to_github(tmp_path: Path, monkeypatch) -> None:
    docs_dir = tmp_path / "docs"
    page_dir = docs_dir / "user"
    page_dir.mkdir(parents=True)
    (page_dir / "index.md").write_text("# User\n", encoding="utf-8")
    documentation_section = page_dir / "guide"
    documentation_section.mkdir()
    source_file = tmp_path / "tests" / "evidence.py"
    source_file.parent.mkdir()
    source_file.write_text("# evidence\n", encoding="utf-8")
    monkeypatch.setattr(mkdocs_publication, "_docs_dir", docs_dir)
    monkeypatch.setattr(mkdocs_publication, "_repository_url", "https://github.com/PyNumLab/prik")

    markdown = (
        "[Page](index.md) [Section](guide/) [Evidence](../../tests/evidence.py#proof) [Missing](../../missing.py)"
    )

    assert mkdocs_publication._rewrite_repository_targets(markdown, "user/index.md") == (
        "[Page](index.md) [Section](guide/) "
        "[Evidence](https://github.com/PyNumLab/prik/blob/main/tests/evidence.py#proof) "
        "[Missing](../../missing.py)"
    )
