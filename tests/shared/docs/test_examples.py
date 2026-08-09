"""Execute explicitly marked examples embedded in Markdown documentation."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import os
import platform
from pathlib import Path
import re
import shlex
import subprocess
import sys

import pytest

from prik import pyi_text_to_semantic_module


ROOT = Path(__file__).parents[3]
DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "examples/blas/README.md",
    ROOT / "examples/fftpack/README.md",
    ROOT / "examples/lapack/README.md",
    ROOT / "examples/minpack/README.md",
    *sorted(path for path in (ROOT / "docs").rglob("*.md") if "old_docs" not in path.parts),
]
AUDITED_PYTHON_DOC_PATHS = [
    ROOT / "README.md",
    *sorted((ROOT / "docs/user/getting-started").glob("*.md")),
    *sorted((ROOT / "docs/user/guide").glob("*.md")),
]
TEST_MARKER = re.compile(r"^\s*<!--\s*prik-doc-test:\s*(run|exact)(?:\s+([a-z0-9_-]+))?\s*-->\s*$")
OUTPUT_MARKER = re.compile(r"^\s*<!--\s*prik-doc-test-output\s*-->\s*$")
SOURCE_MARKER = re.compile(r"^\s*<!--\s*prik-doc-source:\s*(.+?)\s*-->\s*$")
FENCE_MARKER = re.compile(r"^\s*(`{3,}|~{3,})")
SHELL_OPERATORS = {"&&", "||", ";", "|", ">", ">>", "<", "2>", "2>>"}
DISALLOWED_OPTIONS = {
    "--compile-commands",
    "--compiler",
    "--compiler-arg",
    "--out",
    "--preprocess-template",
}
C_DOCS_START = "<!-- PRIK_C_DOCS_START"
C_DOCS_END = "PRIK_C_DOCS_END -->"
C_DOCS_DISABLED = "<!-- PRIK_C_DOCS_DISABLED:"


@dataclass(frozen=True)
class DocumentationExample:
    path: Path
    line: int
    mode: str
    language: str
    command: str
    expected_output: str | None = None
    platform: str | None = None

    @property
    def test_id(self) -> str:
        return f"{self.path.relative_to(ROOT)}:{self.line}"


@dataclass(frozen=True)
class DocumentedSource:
    path: Path
    line: int
    source_path: Path
    selector: str | None
    source_text: str

    @property
    def test_id(self) -> str:
        return f"{self.path.relative_to(ROOT)}:{self.line}"


@dataclass(frozen=True)
class DocumentedPythonBlock:
    path: Path
    line: int
    source: str

    @property
    def test_id(self) -> str:
        return f"{self.path.relative_to(ROOT)}:{self.line}"


def _platform_id() -> str:
    machine = platform.machine().lower()
    machine = {"amd64": "x86_64", "arm64": "aarch64"}.get(machine, machine)
    return f"{platform.system().lower()}-{machine}"


def _next_nonempty_line(lines: list[str], start: int) -> int:
    index = start
    while index < len(lines) and not lines[index].strip():
        index += 1
    return index


def _fenced_block(lines: list[str], start: int, *, language: str | None = None) -> tuple[str, int, str]:
    start = _next_nonempty_line(lines, start)
    if start >= len(lines) or not lines[start].startswith("```"):
        raise AssertionError(f"expected a fenced block at line {start + 1}")
    actual_language = lines[start][3:].strip()
    if language is not None and actual_language != language:
        raise AssertionError(f"expected a {language!r} fenced block at line {start + 1}, got {actual_language!r}")

    end = start + 1
    while end < len(lines) and lines[end].strip() != "```":
        end += 1
    if end >= len(lines):
        raise AssertionError(f"unclosed fenced block at line {start + 1}")
    return "\n".join(lines[start + 1 : end]), end + 1, actual_language


def _logical_command(command_block: str, *, location: str) -> str:
    command = re.sub(r"\\\n\s*", " ", command_block).strip()
    if "\n" in command:
        raise AssertionError(f"{location}: documentation tests must contain exactly one shell command")
    return command


def _visible_documentation_lines(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    visible: list[str] = []
    hidden = False
    for line in lines:
        if line.strip() == C_DOCS_START:
            hidden = True
            visible.append("")
        elif line.strip() == C_DOCS_END:
            hidden = False
            visible.append("")
        elif hidden or line.lstrip().startswith(C_DOCS_DISABLED):
            visible.append("")
        else:
            visible.append(line)
    assert not hidden, f"{path.relative_to(ROOT)}: unclosed deferred documentation comment"
    return visible


def _documented_content_from_path(path: Path) -> tuple[list[DocumentationExample], list[DocumentedSource]]:
    lines = _visible_documentation_lines(path)
    examples: list[DocumentationExample] = []
    sources: list[DocumentedSource] = []
    index = 0

    while index < len(lines):
        source_marker = SOURCE_MARKER.match(lines[index])
        if source_marker is not None:
            marker_line = index + 1
            source_text, index, _language = _fenced_block(lines, index + 1)
            source_reference = source_marker.group(1)
            source_path, separator, selector = source_reference.partition("::")
            sources.append(
                DocumentedSource(
                    path=path,
                    line=marker_line,
                    source_path=ROOT / source_path,
                    selector=selector if separator else None,
                    source_text=source_text,
                )
            )
            continue

        marker = TEST_MARKER.match(lines[index])
        if marker is None:
            if OUTPUT_MARKER.match(lines[index]):
                raise AssertionError(f"{path.relative_to(ROOT)}:{index + 1}: output marker has no exact test")
            fence = FENCE_MARKER.match(lines[index])
            if fence is not None:
                token = fence.group(1)
                index += 1
                while index < len(lines) and lines[index].strip() != token:
                    index += 1
            index += 1
            continue

        mode = marker.group(1)
        marker_line = index + 1
        command_block, after_command, language = _fenced_block(lines, index + 1)
        if language not in {"bash", "python"}:
            raise AssertionError(
                f"{path.relative_to(ROOT)}:{marker_line}: documentation tests require a bash or python fenced block"
            )
        command = (
            _logical_command(command_block, location=f"{path.relative_to(ROOT)}:{marker_line}")
            if language == "bash"
            else command_block
        )
        expected_output = None
        index = after_command

        if mode == "exact":
            while index < len(lines) and not OUTPUT_MARKER.match(lines[index]):
                if TEST_MARKER.match(lines[index]):
                    raise AssertionError(
                        f"{path.relative_to(ROOT)}:{marker_line}: exact test is missing an output marker"
                    )
                index += 1
            if index >= len(lines):
                raise AssertionError(f"{path.relative_to(ROOT)}:{marker_line}: exact test is missing an output marker")
            expected_output, index, _output_language = _fenced_block(lines, index + 1)

        examples.append(
            DocumentationExample(
                path=path,
                line=marker_line,
                mode=mode,
                language=language,
                command=command,
                expected_output=expected_output,
                platform=marker.group(2),
            )
        )

    return examples, sources


DOCUMENTATION_CONTENT = [_documented_content_from_path(path) for path in DOC_PATHS]
DOCUMENTATION_EXAMPLES = [example for examples, _sources in DOCUMENTATION_CONTENT for example in examples]
DOCUMENTED_SOURCES = [source for _examples, sources in DOCUMENTATION_CONTENT for source in sources]


def _documented_python_blocks(path: Path) -> list[DocumentedPythonBlock]:
    """Collect every visible Python fence for syntax and contract validation."""
    lines = _visible_documentation_lines(path)
    blocks = []
    index = 0
    while index < len(lines):
        if lines[index].strip() != "```python":
            index += 1
            continue
        source, after_block, _language = _fenced_block(lines, index, language="python")
        blocks.append(DocumentedPythonBlock(path=path, line=index + 1, source=source))
        index = after_block
    return blocks


DOCUMENTED_PYTHON_BLOCKS = [block for path in AUDITED_PYTHON_DOC_PATHS for block in _documented_python_blocks(path)]


def _command_argv(example: DocumentationExample) -> list[str]:
    if example.language == "python":
        return [sys.executable, "-c", example.command]

    argv = shlex.split(example.command)
    allowed_modules = {("python", "-m", "prik")}
    normalized_command = ("python", *argv[1:3]) if argv and argv[0] in {"python", "python3"} else ()
    if normalized_command not in allowed_modules:
        raise AssertionError(f"{example.test_id}: unsupported documentation command")
    if any(argument in SHELL_OPERATORS for argument in argv):
        raise AssertionError(f"{example.test_id}: shell operators are not supported")
    if any(
        argument == option or argument.startswith(f"{option}=") for argument in argv for option in DISALLOWED_OPTIONS
    ):
        raise AssertionError(f"{example.test_id}: output-writing and custom-executable options are not supported")
    argv[0] = sys.executable
    return argv


def test_documentation_has_automatically_verified_examples():
    assert DOCUMENTATION_EXAMPLES, "mark at least one Markdown example with prik-doc-test"
    assert any(example.mode == "exact" for example in DOCUMENTATION_EXAMPLES)
    assert DOCUMENTED_SOURCES, "mark displayed fixture inputs with prik-doc-source"


@pytest.mark.parametrize("source", DOCUMENTED_SOURCES, ids=lambda source: source.test_id)
def test_documented_source_input(source: DocumentedSource):
    assert source.source_path.is_file(), f"{source.test_id}: documented source does not exist: {source.source_path}"
    file_text = source.source_path.read_text(encoding="utf-8")
    expected_text = file_text
    if source.selector is not None:
        tree = ast.parse(file_text, filename=str(source.source_path))
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == source.selector]
        assert len(selected) == 1, f"{source.test_id}: source selector {source.selector!r} did not name one function"
        expected_text = ast.get_source_segment(file_text, selected[0]) or ""
    assert source.source_text.rstrip("\n") == expected_text.rstrip("\n")


@pytest.mark.parametrize("block", DOCUMENTED_PYTHON_BLOCKS, ids=lambda block: block.test_id)
def test_documented_python_block_is_valid(block: DocumentedPythonBlock):
    """Keep Python examples parseable and semantic contract examples loadable."""
    ast.parse(block.source, filename=block.test_id)
    if "from prik.contracts import" in block.source:
        pyi_text_to_semantic_module(block.source, module_name="documentation_example")


@pytest.mark.parametrize("path", DOC_PATHS, ids=lambda path: str(path.relative_to(ROOT)))
def test_documented_expected_output_labels_are_automatically_verified(path: Path):
    lines = _visible_documentation_lines(path)
    for index, line in enumerate(lines):
        if line.strip() not in {"Expected output:", "Output:"}:
            continue
        marker_index = _next_nonempty_line(lines, index + 1)
        assert marker_index < len(lines) and OUTPUT_MARKER.match(lines[marker_index]), (
            f"{path.relative_to(ROOT)}:{index + 1}: documented output must use prik-doc-test-output"
        )


@pytest.mark.parametrize("example", DOCUMENTATION_EXAMPLES, ids=lambda example: example.test_id)
def test_documentation_example(example: DocumentationExample):
    if example.platform is not None and example.platform != _platform_id():
        pytest.skip(f"example targets {example.platform}, running on {_platform_id()}")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT), env.get("PYTHONPATH")]))
    result = subprocess.run(
        _command_argv(example),
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, (
        f"{example.test_id}: command failed with status {result.returncode}\n"
        f"command: {example.command}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert result.stderr == "", f"{example.test_id}: command wrote to stderr:\n{result.stderr}"
    if example.mode == "exact":
        assert result.stdout.rstrip("\n") == (example.expected_output or "").rstrip("\n")
