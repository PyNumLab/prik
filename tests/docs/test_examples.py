"""Execute verified examples embedded in Markdown documentation."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import os
import platform
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

import pytest

from prik.pipeline.pyi import pyi_text_to_semantic_module


ROOT = Path(__file__).parents[2]
DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "examples/blas/README.md",
    ROOT / "examples/bspline/README.md",
    ROOT / "examples/fftpack/README.md",
    ROOT / "examples/lapack/README.md",
    ROOT / "examples/libm/README.md",
    ROOT / "examples/minpack/README.md",
    *sorted((ROOT / "docs").rglob("*.md")),
]
AUDITED_PYTHON_DOC_PATHS = [
    ROOT / "README.md",
    *sorted((ROOT / "docs").rglob("*.md")),
]
DEVELOPER_PACKAGE_DOC_PATHS = sorted((ROOT / "docs/developer/packages").rglob("*.md"))
TEST_MARKER = re.compile(r"^\s*<!--\s*prik-doc-test:\s*(run|exact)(?:\s+([a-z0-9_-]+))?\s*-->\s*$")
OUTPUT_MARKER = re.compile(r"^\s*<!--\s*prik-doc-test-output\s*-->\s*$")
INVALID_CONTRACT_MARKER = re.compile(r"^\s*<!--\s*prik-doc-contract:\s*invalid\s*-->\s*$")
SOURCE_MARKER = re.compile(r"^\s*<!--\s*prik-doc-source:\s*(.+?)\s*-->\s*$")
FENCE_MARKER = re.compile(r"^\s*(`{3,}|~{3,})")
DIRECT_PRODUCTION_COMMAND = re.compile(r"^python3 (?P<path>prik/(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_]+\.py)$")
SHELL_OPERATORS = {"&&", "||", ";", "|", ">", ">>", "<", "2>", "2>>"}
DISALLOWED_OPTIONS = {
    "--compile-commands",
    "--compiler",
    "--compiler-arg",
    "--out",
    "--preprocess-template",
}
TARGET_DEPENDENT_EXAMPLES = {
    "prik/pipeline/type_mapping_report.py",
    "prik/preprocessing/probes/fortran_types.py",
}
EXAMPLE_TOOL_REQUIREMENTS = {
    "prik/pipeline/build.py": (("gfortran",), ("gcc",)),
    "prik/pipeline/type_mapping_report.py": (("cc",),),
    "prik/preprocessing/probes/fortran_types.py": (("gfortran", "f95"),),
    "prik/preprocessing/source.py": (("cc",),),
}


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
    expects_contract_error: bool = False

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


def _previous_nonempty_line(lines: list[str], start: int) -> int:
    index = start
    while index >= 0 and not lines[index].strip():
        index -= 1
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


def _documented_content_from_path(path: Path) -> tuple[list[DocumentationExample], list[DocumentedSource]]:
    lines = path.read_text(encoding="utf-8").splitlines()
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


def _developer_package_examples(path: Path) -> list[DocumentationExample]:
    """Discover production-file command/result pairs from one package guide."""
    lines = path.read_text(encoding="utf-8").splitlines()
    examples: list[DocumentationExample] = []
    index = 0

    while index < len(lines):
        if lines[index].strip() != "```bash":
            index += 1
            continue

        command_block, after_command, _language = _fenced_block(lines, index, language="bash")
        command = _logical_command(command_block, location=f"{path.relative_to(ROOT)}:{index + 1}")
        command_match = DIRECT_PRODUCTION_COMMAND.fullmatch(command)
        if command_match is None:
            index = after_command
            continue

        result_index = after_command
        while result_index < len(lines):
            stripped = lines[result_index].strip()
            if stripped == "```text":
                break
            if stripped == "```bash" or stripped.startswith("## "):
                raise AssertionError(
                    f"{path.relative_to(ROOT)}:{index + 1}: production command is missing a displayed result"
                )
            result_index += 1
        if result_index >= len(lines):
            raise AssertionError(
                f"{path.relative_to(ROOT)}:{index + 1}: production command is missing a displayed result"
            )

        expected_output, after_result, _output_language = _fenced_block(
            lines,
            result_index,
            language="text",
        )
        script_path = command_match.group("path")
        if script_path in TARGET_DEPENDENT_EXAMPLES:
            mode = "invariant"
        elif any(line.strip() == "..." for line in expected_output.splitlines()):
            mode = "excerpt"
        else:
            mode = "exact"
        examples.append(
            DocumentationExample(
                path=path,
                line=index + 2,
                mode=mode,
                language="bash",
                command=command,
                expected_output=expected_output,
            )
        )
        index = after_result

    return examples


DOCUMENTATION_CONTENT = [_documented_content_from_path(path) for path in DOC_PATHS]
MARKED_DOCUMENTATION_EXAMPLES = [example for examples, _sources in DOCUMENTATION_CONTENT for example in examples]
DEVELOPER_PACKAGE_EXAMPLES = [
    example for path in DEVELOPER_PACKAGE_DOC_PATHS for example in _developer_package_examples(path)
]
DOCUMENTATION_EXAMPLES = [*MARKED_DOCUMENTATION_EXAMPLES, *DEVELOPER_PACKAGE_EXAMPLES]
DOCUMENTED_SOURCES = [source for _examples, sources in DOCUMENTATION_CONTENT for source in sources]


def _documented_python_blocks(path: Path) -> list[DocumentedPythonBlock]:
    """Collect every visible Python fence for syntax and contract validation.

    A fence introduced by ``prik-doc-test-output`` holds captured command
    output rather than Python source, so it is skipped.  One introduced by
    ``prik-doc-contract: invalid`` is a negative example whose documented
    behavior is that loading it fails.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks = []
    index = 0
    while index < len(lines):
        if lines[index].strip() != "```python":
            index += 1
            continue
        source, after_block, _language = _fenced_block(lines, index, language="python")
        marker_index = _previous_nonempty_line(lines, index - 1)
        marker = lines[marker_index] if marker_index >= 0 else ""
        if not OUTPUT_MARKER.match(marker):
            blocks.append(
                DocumentedPythonBlock(
                    path=path,
                    line=index + 1,
                    source=source,
                    expects_contract_error=bool(INVALID_CONTRACT_MARKER.match(marker)),
                )
            )
        index = after_block
    return blocks


DOCUMENTED_PYTHON_BLOCKS = [block for path in AUDITED_PYTHON_DOC_PATHS for block in _documented_python_blocks(path)]


def _command_argv(example: DocumentationExample) -> list[str]:
    if example.language == "python":
        return [sys.executable, "-c", example.command]

    argv = shlex.split(example.command)
    allowed_modules = {("python", "-m", "prik")}
    normalized_command = ("python", *argv[1:3]) if argv and argv[0] in {"python", "python3"} else ()
    direct_command = DIRECT_PRODUCTION_COMMAND.fullmatch(example.command)
    if normalized_command not in allowed_modules and direct_command is None:
        raise AssertionError(f"{example.test_id}: unsupported documentation command")
    if any(argument in SHELL_OPERATORS for argument in argv):
        raise AssertionError(f"{example.test_id}: shell operators are not supported")
    if any(
        argument == option or argument.startswith(f"{option}=") for argument in argv for option in DISALLOWED_OPTIONS
    ):
        raise AssertionError(f"{example.test_id}: output-writing and custom-executable options are not supported")
    if direct_command is not None:
        script_path = (ROOT / direct_command.group("path")).resolve()
        try:
            script_path.relative_to((ROOT / "prik").resolve())
        except ValueError as exc:
            raise AssertionError(f"{example.test_id}: production command escapes the prik package") from exc
        if not script_path.is_file():
            raise AssertionError(f"{example.test_id}: production command target does not exist")
    argv[0] = sys.executable
    return argv


def _direct_script_path(example: DocumentationExample) -> str | None:
    command_match = DIRECT_PRODUCTION_COMMAND.fullmatch(example.command)
    return command_match.group("path") if command_match is not None else None


def _missing_example_tool(example: DocumentationExample) -> str | None:
    script_path = _direct_script_path(example)
    for alternatives in EXAMPLE_TOOL_REQUIREMENTS.get(script_path or "", ()):
        if not any(shutil.which(executable) for executable in alternatives):
            return " or ".join(alternatives)
    return None


def _assert_excerpt_output(actual: str, expected: str, *, test_id: str) -> None:
    """Match documented chunks in order, treating a line containing ``...`` as omitted output."""
    chunks: list[str] = []
    current_lines: list[str] = []
    for line in expected.splitlines():
        if line.strip() == "...":
            if current_lines:
                chunks.append("\n".join(current_lines))
                current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        chunks.append("\n".join(current_lines))

    cursor = 0
    for chunk in chunks:
        position = actual.find(chunk, cursor)
        assert position >= 0, f"{test_id}: documented output excerpt was not found in order:\n{chunk}"
        cursor = position + len(chunk)


def _assert_target_dependent_output(example: DocumentationExample, output: str) -> None:
    script_path = _direct_script_path(example)
    if script_path == "prik/pipeline/type_mapping_report.py":
        row = output.strip()
        assert row.startswith("| `int` | ")
        assert "signed" in row
        assert "numpy." in row
        return
    if script_path == "prik/preprocessing/probes/fortran_types.py":
        label, separator, raw_value = output.strip().partition(" = ")
        assert label == "selected_int_kind(9)"
        assert separator == " = "
        assert int(raw_value) > 0
        return
    raise AssertionError(f"{example.test_id}: no invariant validator exists for {script_path}")


def test_documentation_has_automatically_verified_examples():
    assert DOCUMENTATION_EXAMPLES, "mark at least one Markdown example with prik-doc-test"
    assert any(example.mode == "exact" for example in DOCUMENTATION_EXAMPLES)
    assert DEVELOPER_PACKAGE_EXAMPLES, "document at least one package-guide production example"
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
    if "from prik.contracts import" not in block.source:
        assert not block.expects_contract_error, (
            f"{block.test_id}: prik-doc-contract: invalid marks a block that loads no contract"
        )
        return
    if block.expects_contract_error:
        with pytest.raises(ValueError):
            pyi_text_to_semantic_module(block.source, module_name="documentation_example")
        return
    pyi_text_to_semantic_module(block.source, module_name="documentation_example")


@pytest.mark.parametrize("path", DOC_PATHS, ids=lambda path: str(path.relative_to(ROOT)))
def test_documented_expected_output_labels_are_automatically_verified(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
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
    missing_tool = _missing_example_tool(example)
    if missing_tool is not None:
        pytest.skip(f"{missing_tool} is required for {example.command}")
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
    elif example.mode == "excerpt":
        _assert_excerpt_output(result.stdout.rstrip("\n"), example.expected_output or "", test_id=example.test_id)
    elif example.mode == "invariant":
        _assert_target_dependent_output(example, result.stdout)
