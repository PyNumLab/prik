"""Fail-closed page publication for the prik MkDocs website."""

from __future__ import annotations

import os
import posixpath
import re
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit


_PUBLICATION_KEY = "publication"
_REVIEWED = "reviewed"
_TRUE_VALUES = {"1", "true", "yes", "on"}
_MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown", ".mkdn", ".mkd"}
_LANE_INDEXES = {
    "user": "user/index.md",
    "developer": "developer/index.md",
}
_MARKDOWN_LINK = re.compile(r"(?<!!)\[([^]]+)]\(([^)]+)\)")

_include_drafts = False
_known_document_paths: set[str] = set()
_published_paths: set[str] = set()
_docs_dir = Path()
_repository_url = ""


def _front_matter_value(path: Path, key: str) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return None

    try:
        end = lines.index("---", 1)
    except ValueError:
        return None

    for line in lines[1:end]:
        name, separator, value = line.partition(":")
        if separator and name.strip() == key:
            return value.strip()
    return None


def _publication_states(docs_dir: Path) -> tuple[dict[str, str | None], set[str]]:
    states: dict[str, str | None] = {}
    known_paths: set[str] = set()
    for path in docs_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _MARKDOWN_SUFFIXES:
            continue
        relative_path = path.relative_to(docs_dir).as_posix()
        known_paths.add(relative_path)
        if relative_path.startswith("old_docs/"):
            continue
        states[relative_path] = _front_matter_value(path, _PUBLICATION_KEY)
    return states, known_paths


def _reviewed_paths(states: dict[str, str | None]) -> set[str]:
    if states.get("index.md") != _REVIEWED:
        return set()

    reviewed = {"index.md"}
    for lane, lane_index in _LANE_INDEXES.items():
        if states.get(lane_index) != _REVIEWED:
            continue
        reviewed.update(
            path
            for path, state in states.items()
            if (path == lane_index or path.startswith(f"{lane}/")) and state == _REVIEWED
        )
    return reviewed


def _filter_navigation(value, published_paths: set[str]):
    if isinstance(value, str):
        if PurePosixPath(value).suffix.lower() not in _MARKDOWN_SUFFIXES:
            return value
        return value if value in published_paths else None

    if isinstance(value, list):
        filtered = []
        for item in value:
            kept = _filter_navigation(item, published_paths)
            if kept is not None:
                filtered.append(kept)
        return filtered or None

    if isinstance(value, dict):
        filtered = {}
        for title, item in value.items():
            kept = _filter_navigation(item, published_paths)
            if kept is not None:
                filtered[title] = kept
        return filtered or None

    return value


def _relative_document_target(source_uri: str, raw_target: str) -> str | None:
    target = raw_target.strip().split(maxsplit=1)[0]
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
        return None
    if PurePosixPath(parsed.path).suffix.lower() not in _MARKDOWN_SUFFIXES:
        return None
    source_parent = PurePosixPath(source_uri).parent.as_posix()
    return posixpath.normpath(posixpath.join(source_parent, unquote(parsed.path)))


def _document_route(markdown_uri: str) -> str:
    path = PurePosixPath(markdown_uri)
    route = path.parent.as_posix() if path.name == "index.md" else path.with_suffix("").as_posix()
    return "" if route == "." else route


def _unpublished_document_site_target(source_uri: str, raw_target: str, resolved_target: str) -> str:
    target_parts = raw_target.strip().split(maxsplit=1)
    parsed = urlsplit(target_parts[0])
    source_route = _document_route(source_uri)
    target_route = _document_route(resolved_target)
    rewritten = posixpath.relpath(target_route or ".", start=source_route or ".")
    if rewritten == ".":
        rewritten = ""
    elif not rewritten.endswith("/"):
        rewritten += "/"
    if parsed.query:
        rewritten += f"?{parsed.query}"
    if parsed.fragment:
        rewritten += f"#{parsed.fragment}"
    if len(target_parts) == 2:
        rewritten += f" {target_parts[1]}"
    return rewritten


def _rewrite_unpublished_document_targets(markdown: str, source_uri: str) -> str:
    def replace_link(match: re.Match[str]) -> str:
        label, target = match.groups()
        resolved = _relative_document_target(source_uri, target)
        if resolved in _known_document_paths and resolved not in _published_paths:
            return f"[{label}]({_unpublished_document_site_target(source_uri, target, resolved)})"
        return match.group(0)

    return _MARKDOWN_LINK.sub(replace_link, markdown)


def _repository_target(source_uri: str, raw_target: str) -> str | None:
    target_parts = raw_target.strip().split(maxsplit=1)
    parsed = urlsplit(target_parts[0])
    if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
        return None

    source_path = _docs_dir / source_uri
    resolved = (source_path.parent / unquote(parsed.path)).resolve()
    repository_root = _docs_dir.parent.resolve()
    if not resolved.is_relative_to(repository_root) or not resolved.exists():
        return None
    if resolved.is_relative_to(_docs_dir.resolve()):
        return None

    route = "tree" if resolved.is_dir() else "blob"
    relative_path = resolved.relative_to(repository_root).as_posix()
    rewritten = f"{_repository_url}/{route}/main/{quote(relative_path)}"
    if parsed.query:
        rewritten += f"?{parsed.query}"
    if parsed.fragment:
        rewritten += f"#{parsed.fragment}"
    if len(target_parts) == 2:
        rewritten += f" {target_parts[1]}"
    return rewritten


def _rewrite_repository_targets(markdown: str, source_uri: str) -> str:
    def replace_link(match: re.Match[str]) -> str:
        label, target = match.groups()
        rewritten = _repository_target(source_uri, target)
        if rewritten is None:
            return match.group(0)
        return f"[{label}]({rewritten})"

    return _MARKDOWN_LINK.sub(replace_link, markdown)


def on_config(config, **_kwargs):
    """Load publication state and filter production navigation."""
    global _docs_dir, _include_drafts, _known_document_paths, _published_paths, _repository_url

    _include_drafts = os.getenv("PRIK_DOCS_INCLUDE_DRAFTS", "").strip().lower() in _TRUE_VALUES
    _docs_dir = Path(config["docs_dir"])
    _repository_url = str(config["repo_url"]).rstrip("/")
    states, _known_document_paths = _publication_states(_docs_dir)
    _published_paths = _reviewed_paths(states)

    if not _include_drafts:
        config["nav"] = _filter_navigation(config["nav"], _published_paths) or []
    return config


def on_files(files, **_kwargs):
    """Remove unpublished Markdown files from production output and search."""
    if _include_drafts:
        return files

    for file in list(files):
        if PurePosixPath(file.src_uri).suffix.lower() in _MARKDOWN_SUFFIXES and file.src_uri not in _published_paths:
            files.remove(file)
    return files


def on_page_markdown(markdown: str, page, **_kwargs) -> str:
    """Label local drafts and preserve production links to unpublished pages."""
    source_uri = page.file.src_uri
    markdown = _rewrite_repository_targets(markdown, source_uri)
    if _include_drafts:
        if source_uri not in _published_paths:
            warning = (
                '!!! warning "Unpublished documentation draft"\n'
                "    This page is available only in the local draft preview.\n\n"
            )
            return warning + markdown
        return markdown
    return _rewrite_unpublished_document_targets(markdown, source_uri)
