"""Reusable fake-compiler and error assertions for preprocessing tests."""

import os
import sys
from pathlib import Path

import pytest

from prik.pipeline.preprocessing import PreprocessingError


def _fake_compiler(tmp_path: Path, output: str) -> tuple[Path, Path, dict[str, str]]:
    script = tmp_path / "fake-cc"
    args_file = tmp_path / "compiler-args.txt"
    script.write_text(
        f"""#!{sys.executable}
import os
import pathlib
import sys

pathlib.Path(os.environ["PRIK_FAKE_COMPILER_ARGS"]).write_text("\\n".join(sys.argv[1:]), encoding="utf-8")
sys.stdout.write(os.environ["PRIK_FAKE_COMPILER_OUTPUT"])
""",
        encoding="utf-8",
    )
    script.chmod(0o755)
    env = {
        **os.environ,
        "PRIK_FAKE_COMPILER_ARGS": str(args_file),
        "PRIK_FAKE_COMPILER_OUTPUT": output,
    }
    return script, args_file, env


def _failing_compiler(tmp_path: Path, stderr: str) -> Path:
    script = tmp_path / "failing-cc"
    script.write_text(
        f"""#!{sys.executable}
import sys

sys.stderr.write({stderr!r})
sys.exit(1)
""",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def _assert_preprocessing_error(
    exc_info: pytest.ExceptionInfo[PreprocessingError],
    *,
    message: str,
    category: str = "INVALID_COMPILER_ARGUMENTS",
) -> None:
    assert str(exc_info.value) == message
    assert exc_info.value.category == category
    assert exc_info.value.diagnostics == []
