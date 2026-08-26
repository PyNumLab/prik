"""Shared facts and parsers for documentation contract tests."""

from __future__ import annotations

from functools import cache
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).parents[2]
DOCS_ROOT = ROOT / "docs"
FEATURE_MATRIX_PATH = DOCS_ROOT / "user/language-support/feature-matrix.md"
CLI_REFERENCE_PATH = DOCS_ROOT / "user/reference/cli-commands.md"
PYTHON_API_REFERENCE_PATH = DOCS_ROOT / "user/reference/python-api.md"
DOC_PATHS = sorted(DOCS_ROOT.rglob("*.md"))
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
REQUIRED_METADATA = {"title", "audience", "prerequisites", "related", "status", "publication"}
ALLOWED_PUBLICATION_STATES = {"draft", "reviewed"}
ALLOWED_STATUSES = {
    "active-roadmap",
    "design",
    "draft",
    "maintained",
    "not-yet-implemented",
    "planned-documentation",
}
CLI_HELP_GROUP_HEADINGS = [
    "commands:",
    "positional arguments:",
    "input selection:",
    "input options:",
    "generation modes:",
    "compiler and preprocessing options:",
    "preprocessing options:",
    "C include options:",
    "report options:",
    "compiler options:",
    "wrapper options:",
    "native options:",
    "probe options:",
    "execution options:",
    "output options:",
    "diagnostic options:",
]
CLI_REFERENCE_OPTIONS = [
    "paths",
    "--help-build",
    "--version",
    "--language",
    "--pyi",
    "--sources",
    "--preprocessor-adapter",
    "--compiler",
    "--preprocess-template",
    "-I",
    "--include-dir",
    "-D",
    "--define",
    "-U",
    "--undef",
    "--std",
    "--compiler-arg",
    "--show-vars",
    "--print-limit",
    "--makefile",
    "--strict-wrapper-names",
    "--build-manifest",
    "--native-fortran-sources",
    "--native-compile-flags",
    "--jobs",
    "--native-objects",
    "--native-library",
    "--native-link-item",
    "--native-library-dir",
    "--expr",
    "--runner",
    "--cache-dir",
    "--refresh",
    "--json",
    "--out",
    "--out-dir",
    "--verbose",
    "--no-color",
    "--debug",
]
CLI_VISIBLE_HELP_OPTIONS = CLI_REFERENCE_OPTIONS
FEATURE_MATRIX_STATUSES = {
    "Supported",
    "Partially supported",
    "Unsupported",
}


def _front_matter(path: Path) -> tuple[dict[str, str], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0] == "---", f"{path.relative_to(ROOT)}: missing front matter"

    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise AssertionError(f"{path.relative_to(ROOT)}: unclosed front matter") from error

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        assert separator, f"{path.relative_to(ROOT)}: invalid front matter line: {line!r}"
        metadata[key.strip()] = value.strip()

    return metadata, "\n".join(lines[end + 1 :])


def _visible_documentation_source(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if path != ROOT / "README.md" and lines and lines[0] == "---":
        lines = lines[lines.index("---", 1) + 1 :]

    visible: list[str] = []
    hidden = False
    for line in lines:
        stripped = line.strip()
        if stripped == "<!--":
            assert not hidden, f"{path.relative_to(ROOT)}: nested documentation comment"
            hidden = True
        elif stripped == "-->" and hidden:
            hidden = False
        elif hidden:
            continue
        else:
            visible.append(line)
    assert not hidden, f"{path.relative_to(ROOT)}: unclosed documentation comment"
    return "\n".join(visible)


@cache
def _prik_cli_help() -> str:
    commands = [
        ["--help"],
        ["input.f90", "--help"],
        ["parse", "--help"],
        ["semantics", "--help"],
        ["generate", "--help"],
        ["probe", "--help"],
    ]
    outputs = []
    for command in commands:
        result = subprocess.run(
            [sys.executable, "-m", "prik", *command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        outputs.append(result.stdout)
    return "\n".join(outputs)


def _feature_matrix_rows() -> list[dict[str, str]]:
    header = "| Feature | Status | User docs | Evidence | Limitations |"
    columns = ["Feature", "Status", "User docs", "Evidence", "Limitations"]
    rows: list[dict[str, str]] = []
    in_table = False

    for line in FEATURE_MATRIX_PATH.read_text(encoding="utf-8").splitlines():
        if line == header:
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("| ---"):
            continue
        if not line.startswith("|"):
            in_table = False
            continue

        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == len(columns), f"invalid feature matrix row: {line!r}"
        rows.append(dict(zip(columns, cells, strict=True)))

    return rows


FEATURE_MATRIX_ROWS = _feature_matrix_rows()
