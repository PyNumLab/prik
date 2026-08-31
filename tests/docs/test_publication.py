"""Verify fail-closed MkDocs publication filtering."""

from __future__ import annotations

from pathlib import Path

import pytest

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


def test_package_command_expands_its_main_example_source(tmp_path: Path, monkeypatch) -> None:
    docs_dir = tmp_path / "docs"
    source_path = tmp_path / "prik" / "component.py"
    docs_dir.mkdir()
    source_path.parent.mkdir()
    source_path.write_text(
        'def component():\n    return "library code"\n\nif __name__ == "__main__":\n    print(component())\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(mkdocs_publication, "_docs_dir", docs_dir)

    expanded = mkdocs_publication._expand_package_main_examples(
        "```bash\npython3 prik/component.py\n```",
        "developer/packages/component.md",
    )

    assert "<summary>Example source: <code>prik/component.py</code></summary>" in expanded
    assert 'if __name__ == "__main__":\n    print(component())' in expanded


def test_package_command_rejects_a_module_without_one_main_example(tmp_path: Path, monkeypatch) -> None:
    docs_dir = tmp_path / "docs"
    source_path = tmp_path / "prik" / "component.py"
    docs_dir.mkdir()
    source_path.parent.mkdir()
    source_path.write_text("def component():\n    return None\n", encoding="utf-8")
    monkeypatch.setattr(mkdocs_publication, "_docs_dir", docs_dir)

    with pytest.raises(ValueError, match="one top-level __main__ block"):
        mkdocs_publication._expand_package_main_examples(
            "```bash\npython3 prik/component.py\n```",
            "developer/packages/component.md",
        )


def test_example_notebooks_are_served_from_the_site(tmp_path: Path) -> None:
    """A download button needs the notebook same-origin, not on GitHub.

    The browser honours ``download`` only for a same-origin file, so the site
    serves a copy while the repository keeps the single source of truth.
    """
    docs_dir = tmp_path / "docs"
    notebook_dir = tmp_path / mkdocs_publication._EXAMPLE_NOTEBOOK_DIR
    docs_dir.mkdir()
    notebook_dir.mkdir(parents=True)
    (notebook_dir / "quickstart.ipynb").write_text("{}", encoding="utf-8")
    (notebook_dir / "notes.txt").write_text("not a notebook", encoding="utf-8")
    files: list[object] = []

    mkdocs_publication._publish_example_notebooks(
        files,
        {"docs_dir": str(docs_dir), "site_dir": str(tmp_path / "site")},
    )

    assert [file.src_uri for file in files] == ["quickstart.ipynb"]
    assert Path(files[0].abs_dest_path).name == "quickstart.ipynb"


def test_publishing_example_notebooks_tolerates_a_missing_directory(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    files: list[object] = []

    mkdocs_publication._publish_example_notebooks(
        files,
        {"docs_dir": str(docs_dir), "site_dir": str(tmp_path / "site")},
    )

    assert files == []
