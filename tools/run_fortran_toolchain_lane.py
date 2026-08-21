#!/usr/bin/env python3
"""Run the focused profile checks and strict Fortran toolchain smoke lane."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_TEST_PATHS = (
    "tests/fortran/infrastructure/building/compiling/test_compiler_verbose.py",
    "tests/fortran/infrastructure/preprocessing/test_configuration_and_adapters.py",
)
FOCUSED_FORTRAN_CLI_NODES = (
    "tests/fortran/infrastructure/preprocessing/test_cli.py::"
    "test_cli_fortran_compiler_mode_runs_exact_compiler_and_parses_stdout",
)


def lane_commands(
    compiler: str,
    *,
    python_executable: str = sys.executable,
    junit_dir: Path | None = None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return the profile/CLI and strict-smoke pytest commands."""
    common = (
        python_executable,
        "-m",
        "pytest",
        "-q",
        "--randomly-seed=1",
        "-o",
        "junit_family=legacy",
    )
    profile_report = (
        (f"--junitxml={junit_dir / 'pytest-toolchain-profile-results.xml'}",) if junit_dir is not None else ()
    )
    smoke_report = (f"--junitxml={junit_dir / 'pytest-toolchain-smoke-results.xml'}",) if junit_dir is not None else ()
    profile = (
        *common,
        *profile_report,
        *PROFILE_TEST_PATHS,
        *FOCUSED_FORTRAN_CLI_NODES,
    )
    smoke = (
        *common,
        *smoke_report,
        "tests/fortran",
        "-m",
        "toolchain_smoke",
        "--require-toolchain-smoke",
        f"--prik-fortran-compiler={compiler}",
    )
    return profile, smoke


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", required=True, help="Fortran compiler executable for strict smoke.")
    parser.add_argument(
        "--junit-dir",
        type=Path,
        default=None,
        help="Optional directory for separate profile and smoke JUnit reports.",
    )
    parser.add_argument("--plan", action="store_true", help="Print commands without resolving or running the compiler.")
    return parser


def _resolved_compiler(parser: argparse.ArgumentParser, requested: str) -> str:
    compiler = shutil.which(requested)
    if compiler is None:
        parser.error(f"Fortran compiler is unavailable: {requested}")
    return str(Path(compiler).resolve())


def main(argv: Sequence[str] | None = None) -> int:
    """Run or print the maintained alternate-toolchain lane."""
    parser = _parser()
    args = parser.parse_args(argv)
    compiler = args.compiler if args.plan else _resolved_compiler(parser, args.compiler)
    commands = lane_commands(compiler, junit_dir=args.junit_dir)

    if args.plan:
        for label, command in zip(("profile-and-cli", "strict-smoke"), commands, strict=True):
            print(f"{label}: {shlex.join(command)}")
        return 0

    if args.junit_dir is not None:
        args.junit_dir.mkdir(parents=True, exist_ok=True)
    for command in commands:
        completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
        if completed.returncode:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
