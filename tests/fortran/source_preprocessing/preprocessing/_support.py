"""Shared preprocessing CLI and compiler-command contract tests."""

import json

import os

import subprocess

import sys

from pathlib import Path

import pytest

import x2py.pipeline.preprocessing as preprocessing

from x2py.pipeline.preprocessing import (
    PreprocessingError,
    PreprocessingConfig,
    build_compile_commands_invocation,
    build_direct_preprocess_invocation,
    build_preprocess_invocation,
    build_template_preprocess_invocation,
    expand_native_fortran_includes,
    run_compiler_preprocessor,
    run_compiler_preprocessor_with_recipe,
    validate_macro_name,
)


def _fake_compiler(tmp_path: Path, output: str) -> tuple[Path, Path, dict[str, str]]:
    script = tmp_path / "fake-cc"
    args_file = tmp_path / "compiler-args.txt"
    script.write_text(
        f"""#!{sys.executable}
import os
import pathlib
import sys

pathlib.Path(os.environ["X2PY_FAKE_COMPILER_ARGS"]).write_text("\\n".join(sys.argv[1:]), encoding="utf-8")
sys.stdout.write(os.environ["X2PY_FAKE_COMPILER_OUTPUT"])
""",
        encoding="utf-8",
    )
    script.chmod(0o755)
    env = {
        **os.environ,
        "X2PY_FAKE_COMPILER_ARGS": str(args_file),
        "X2PY_FAKE_COMPILER_OUTPUT": output,
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


__all__ = (
    "Path",
    "PreprocessingConfig",
    "PreprocessingError",
    "_assert_preprocessing_error",
    "_failing_compiler",
    "_fake_compiler",
    "build_compile_commands_invocation",
    "build_direct_preprocess_invocation",
    "build_preprocess_invocation",
    "build_template_preprocess_invocation",
    "expand_native_fortran_includes",
    "json",
    "preprocessing",
    "pytest",
    "run_compiler_preprocessor",
    "run_compiler_preprocessor_with_recipe",
    "subprocess",
    "sys",
    "validate_macro_name",
)
