"""Tests for the repository-owned alternate-compiler lane runner."""

from pathlib import Path

from tools.run_fortran_toolchain_lane import (
    FOCUSED_FORTRAN_CLI_NODES,
    PROFILE_TEST_PATHS,
    lane_commands,
    main,
)


def test_lane_commands_run_profile_and_cli_evidence_before_strict_smoke(tmp_path: Path):
    profile, smoke = lane_commands(
        "/opt/toolchains/bin/ifx",
        python_executable="/opt/python",
        junit_dir=tmp_path,
    )

    assert profile[:3] == ("/opt/python", "-m", "pytest")
    assert set(PROFILE_TEST_PATHS) < set(profile)
    assert set(FOCUSED_FORTRAN_CLI_NODES) < set(profile)
    assert f"--junitxml={tmp_path / 'pytest-toolchain-profile-results.xml'}" in profile
    assert smoke[-5:] == (
        "tests/fortran",
        "-m",
        "toolchain_smoke",
        "--require-toolchain-smoke",
        "--x2py-fortran-compiler=/opt/toolchains/bin/ifx",
    )
    assert f"--junitxml={tmp_path / 'pytest-toolchain-smoke-results.xml'}" in smoke


def test_plan_prints_both_commands_without_resolving_the_compiler(capsys):
    assert main(["--compiler=/missing/flang", "--plan"]) == 0

    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("profile-and-cli: ")
    assert lines[1].startswith("strict-smoke: ")
    assert "--x2py-fortran-compiler=/missing/flang" in lines[1]
