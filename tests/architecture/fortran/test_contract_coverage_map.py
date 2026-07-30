"""Validate the permanent Fortran contract ledger."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).parents[3]
LEDGER = REPO_ROOT / "tests/fortran/CONTRACT_COVERAGE.md"
CONTRACT_HEADER = (
    "Documentation contract",
    "Status",
    "Dimensions",
    "Stage evidence",
    "Runtime evidence",
    "Negative evidence",
    "CI lane",
)
AUTHORITATIVE_SOURCES = (
    "docs/user/guide/",
    "docs/user/reference/pyi-contracts/",
    "docs/user/examples/recipes/inspect-fortran-api.md",
    "docs/user/examples/recipes/compiler-preprocessing.md",
    "docs/user/reference/cli-commands.md",
    "docs/user/reference/semantic-ir.md",
    "docs/user/reference/semantic-pyi-format.md",
    "docs/user/reference/fortran-wrapper.md",
    "docs/user/language-support/feature-matrix.md",
)
TERMINAL_STAGES = {
    "parsing",
    "probes",
    "preprocessing",
    "semantics",
    "policy",
    "wrapper_codegen",
    "compiling",
    "pipeline",
    "import",
    "runtime",
}
DOCUMENTATION_LINK = re.compile(r"^\[[^]]+\]\((?P<path>[^)#]+)#(?P<anchor>[^)]+)\)$")
NODE = re.compile(r"^`(?P<node>tests/fortran/[^`]+::[^`]+)`$")
NEGATIVE_NODE = re.compile(r"^`(?P<node>tests/fortran/[^`]+::[^`]+)` \(`(?P<stage>[a-z_]+)`\)$")


def _split_table_row(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _contract_rows() -> list[tuple[str, ...]]:
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    header_index = lines.index("| " + " | ".join(CONTRACT_HEADER) + " |")
    rows = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        row = _split_table_row(line)
        assert len(row) == len(CONTRACT_HEADER)
        rows.append(row)
    return rows


def _heading_slug(heading: str) -> str:
    heading = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", heading)
    heading = heading.replace("`", "").replace("*", "").replace("_", "")
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[^\w\s-]", "", heading.casefold())
    return re.sub(r"-+", "-", re.sub(r"\s+", "-", heading)).strip("-")


def _document_anchors(path: Path) -> set[str]:
    anchors = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            anchors.add(_heading_slug(match.group(1)))
    return anchors


def _evidence_nodes(cell: str, *, negative: bool = False) -> list[str]:
    if cell == "—":
        return []
    pattern = NEGATIVE_NODE if negative else NODE
    nodes = []
    for entry in cell.split("<br>"):
        match = pattern.fullmatch(entry.strip())
        assert match is not None, entry
        if negative:
            assert match.group("stage") in TERMINAL_STAGES
        nodes.append(match.group("node"))
    return nodes


def _collected_nodes(*paths: str) -> set[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *paths],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return {line.strip() for line in result.stdout.splitlines() if line.startswith("tests/") and "::" in line}


def test_contract_ledger_declares_the_complete_schema_and_sources() -> None:
    text = LEDGER.read_text(encoding="utf-8")
    assert "| " + " | ".join(CONTRACT_HEADER) + " |" in text
    for source in AUTHORITATIVE_SOURCES:
        assert source in text


def test_contract_documentation_links_resolve_to_stable_headings() -> None:
    for row in _contract_rows():
        match = DOCUMENTATION_LINK.fullmatch(row[0])
        assert match is not None, row[0]
        path = (LEDGER.parent / match.group("path")).resolve()
        assert path.is_file()
        assert path.is_relative_to(REPO_ROOT / "docs/user")
        assert match.group("anchor") in _document_anchors(path)


def test_every_contract_row_retains_evidence_and_blocked_rows_name_the_terminal_stage() -> None:
    for row in _contract_rows():
        stage_nodes = _evidence_nodes(row[3])
        runtime_nodes = _evidence_nodes(row[4])
        negative_nodes = _evidence_nodes(row[5], negative=True)

        assert stage_nodes or runtime_nodes or negative_nodes, row[0]
        if row[1] == "Blocked":
            assert negative_nodes, row[0]


def test_contract_evidence_uses_exact_final_nodes_that_collect() -> None:
    requested = set()
    for row in _contract_rows():
        assert row[1] in {"Supported", "Partially supported", "Blocked"}
        requested.update(_evidence_nodes(row[3]))
        requested.update(_evidence_nodes(row[4]))
        requested.update(_evidence_nodes(row[5], negative=True))

    if not requested:
        return

    paths = sorted({node.split("::", maxsplit=1)[0] for node in requested})
    for relative in paths:
        assert (REPO_ROOT / relative).is_file()
        assert "/architecture/" not in relative

    collected = _collected_nodes(*paths)
    assert requested <= collected
