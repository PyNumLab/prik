"""Documentation link-integrity contracts."""

import re

from tests.docs._structure_support import (
    DOC_PATHS,
    DOCS_ROOT,
    MARKDOWN_LINK,
    ROOT,
    _visible_documentation_source,
)


def test_documentation_links_use_published_pages_or_repository_evidence() -> None:
    github_documentation_prefixes = (
        "https://github.com/PyNumLab/prik/blob/main/docs/",
        "https://github.com/PyNumLab/prik/tree/main/docs/",
    )

    for path in DOC_PATHS:
        prose_lines: list[str] = []
        fence: str | None = None
        for line in _visible_documentation_source(path).splitlines():
            marker = re.match(r"^\s*(`{3,}|~{3,})", line)
            if fence is not None:
                if line.strip() == fence:
                    fence = None
                continue
            if marker is not None:
                fence = marker.group(1)
                continue
            prose_lines.append(line)

        for target in MARKDOWN_LINK.findall("\n".join(prose_lines)):
            if "/" not in target and "." not in target:
                continue
            assert not target.startswith(github_documentation_prefixes), (
                f"{path.relative_to(ROOT)}: documentation link points to GitHub: {target}"
            )
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            assert resolved != (ROOT / "README.md").resolve(), (
                f"{path.relative_to(ROOT)}: documentation workflow points to the repository README"
            )
            if resolved.is_relative_to(DOCS_ROOT.resolve()):
                assert resolved.is_file(), (
                    f"{path.relative_to(ROOT)}: documentation link must target a website page or asset: {target}"
                )


def test_readme_uses_absolute_targets_outside_document_anchors() -> None:
    source = _visible_documentation_source(ROOT / "README.md")
    markdown_targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", source)
    html_targets = re.findall(r"\b(?:href|src)=[\"']([^\"']+)[\"']", source)

    for target in [*markdown_targets, *html_targets]:
        if target.startswith("#"):
            continue
        assert target.startswith(("https://", "mailto:")), f"README.md: relative PyPI target: {target}"
