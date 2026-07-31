"""Validate the declared alternate-compiler GitHub Actions lanes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.run_fortran_toolchain_lane import FOCUSED_FORTRAN_CLI_NODES, PROFILE_TEST_PATHS, lane_commands


REPO_ROOT = Path(__file__).parents[3]
WORKFLOW = REPO_ROOT / ".github/workflows/fortran-toolchain-smoke.yml"
TESTS_WORKFLOW = REPO_ROOT / ".github/workflows/tests.yml"


def test_workflow_declares_pinned_ifx_and_flang_pairs_on_ubuntu_2404() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert text.startswith("name: Smoke Tests\n")
    assert "runs-on: ubuntu-24.04" in text
    assert 'X2PY_IFX_VERSION: "2026.1.1"' in text
    assert 'X2PY_FLANG_VERSION: "22.1.8"' in text
    assert 'X2PY_FLANG_RUNTIME_VERSION: "22.1.7"' in text
    for snippet in (
        "- toolchain: ifx",
        "display_name: Linux · Intel IFX 2026.1.1 · Python 3.12",
        "fortran_compiler: ifx",
        "c_compiler: icx",
        "- toolchain: flang",
        "display_name: Linux · LLVM Flang 22.1.8 · Python 3.12",
        "fortran_compiler: flang",
        "c_compiler: clang",
    ):
        assert snippet in text


def test_workflow_installs_pinned_compilers_and_exports_their_runtime() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    for snippet in (
        "https://software.repos.intel.com/python/conda/",
        '"ifx_linux-64=$X2PY_IFX_VERSION"',
        '"dpcpp_linux-64=$X2PY_IFX_VERSION"',
        '"flang=$X2PY_FLANG_VERSION"',
        '"clang=$X2PY_FLANG_VERSION"',
        '"libflang-rt=$X2PY_FLANG_RUNTIME_VERSION"',
        'echo "$toolchain_prefix/bin" >> "$GITHUB_PATH"',
        'echo "LD_LIBRARY_PATH=$toolchain_prefix/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" >> "$GITHUB_ENV"',
    ):
        assert snippet in text

    assert 'cache_version: "2026.1.1-v2"' in text


def test_every_workflow_lane_delegates_to_the_repository_owned_runner() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "Show repository-owned lane plan" in text
    assert "Run profile checks and strict smoke" in text
    assert text.count("python tools/run_fortran_toolchain_lane.py") == 4
    assert '--compiler "$RUNNER_TEMP/${{ matrix.environment }}/bin/${{ matrix.fortran_compiler }}"' in text


def test_macos_flang_lane_installs_a_coherent_pair_and_runs_strict_smoke() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    macos_job = text.split("  macos-flang-smoke:\n", maxsplit=1)[1]

    for snippet in (
        "name: macOS 15 ARM64 · LLVM Flang · Python 3.12",
        "runs-on: macos-15",
        "brew install flang",
        'flang_prefix="$(brew --prefix flang)"',
        'llvm_prefix="$(brew --prefix llvm)"',
        'ln -sf "$flang_prefix/bin/flang" "$toolchain_prefix/bin/flang"',
        'ln -sf "$llvm_prefix/bin/clang" "$toolchain_prefix/bin/clang"',
        "DYLD_LIBRARY_PATH=",
        "ImageVersion",
        "sw_vers",
        "uname -m",
        "--compiler flang",
    ):
        assert snippet in macos_job

    assert macos_job.count("python tools/run_fortran_toolchain_lane.py") == 2


def test_macos_lane_runs_strict_smoke_and_the_full_ordinary_suite() -> None:
    text = TESTS_WORKFLOW.read_text(encoding="utf-8")
    macos_job = text.split("  macos:\n", maxsplit=1)[1]

    for snippet in (
        "name: macOS 15 ARM64 · Python 3.12",
        "runs-on: macos-15",
        "X2PY_GFORTRAN_BINARY: gfortran-13",
        "X2PY_GCC_BINARY: gcc-13",
        'ln -sf "$(command -v "$X2PY_GFORTRAN_BINARY")" "$compiler_dir/gfortran"',
        'ln -sf "$(command -v "$X2PY_GCC_BINARY")" "$compiler_dir/gcc"',
        "ImageVersion",
        "sw_vers",
        "uname -m",
        "python tools/run_fortran_toolchain_lane.py",
        "--compiler gfortran",
        '-m "not real_library and not toolchain_smoke"',
        "tests/architecture",
        "tests/c",
        "tests/fortran",
        "tests/shared",
    ):
        assert snippet in macos_job

    assert macos_job.count("python tools/run_fortran_toolchain_lane.py") == 2


def test_lane_runner_contains_profile_cli_and_strict_smoke_commands() -> None:
    profile, smoke = lane_commands("/opt/toolchain/bin/flang", python_executable="python")

    assert set(PROFILE_TEST_PATHS) < set(profile)
    assert set(FOCUSED_FORTRAN_CLI_NODES) < set(profile)
    assert smoke[-5:] == (
        "tests/fortran",
        "-m",
        "toolchain_smoke",
        "--require-toolchain-smoke",
        "--x2py-fortran-compiler=/opt/toolchain/bin/flang",
    )


def test_every_profile_and_cli_reference_collects() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            *PROFILE_TEST_PATHS,
            *FOCUSED_FORTRAN_CLI_NODES,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    for reference in (*PROFILE_TEST_PATHS, *FOCUSED_FORTRAN_CLI_NODES):
        path = reference.partition("::")[0]
        assert path in completed.stdout
